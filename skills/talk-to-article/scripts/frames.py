#!/usr/bin/env python3
"""Find candidate screenshots: one stable frame per visual scene, near-duplicates removed.

Usage:
  frames.py <package> [--threshold 0.25] [--min-scene 1.5] [--every 30] [--dup 12]

How it picks frames:
  - ffmpeg scene detection splits the video into scenes.
  - For each scene it takes a frame ~0.7 s BEFORE the scene ends, so slides with build
    animations are captured complete (a frame at the cut often shows a half-built slide).
  - Scenes shorter than --min-scene are skipped (transitions, flashes).
  - Long scenes (live demos with gradual change) get an extra sample every --every seconds.
  - Consecutive frames whose 16x16 perceptual hash differs by fewer than --dup bits are dropped.

Writes candidates/c_NNN.jpg (480 px), candidates.json and sheets/sheet_NN.jpg (4x4 contact
sheets, read row by row). Prints an index "sheet -> #n mm:ss" because ffmpeg builds without
drawtext cannot label the images themselves.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, load_manifest, need, pkg_dir, ts, video_path  # noqa: E402

PER_SHEET = 16


def scene_starts(video, threshold):
    # showinfo logs at info level: do NOT lower -loglevel or the timestamps disappear.
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-an",
                        "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        die(p.stderr[-1500:])
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", p.stderr)]


def grab_with_hash(video, t, out):
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video,
           "-filter_complex", "[0:v]split[a][b];[a]scale=480:-2[t];[b]scale=16:16,format=gray[h]",
           "-map", "[t]", "-frames:v", "1", "-q:v", "4", out,
           "-map", "[h]", "-frames:v", "1", "-f", "rawvideo", "pipe:1"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0 or len(p.stdout) < 256:
        return None
    px = p.stdout[:256]
    mean = sum(px) / 256
    return [1 if v > mean else 0 for v in px]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("--threshold", type=float, default=0.25)
    ap.add_argument("--min-scene", type=float, default=1.5)
    ap.add_argument("--every", type=float, default=30)
    ap.add_argument("--dup", type=int, default=12)
    a = ap.parse_args()
    need("ffmpeg")

    d = pkg_dir(a.package)
    m = load_manifest(d)
    video = video_path(d)
    duration = float(m["meta"].get("duration") or 0)
    if not duration:
        die("unknown duration in manifest")

    cuts = [0.0] + [c for c in scene_starts(video, a.threshold) if c > 0.5] + [duration]
    times = []  # (time to grab, scene start, scene end)
    for start, end in zip(cuts, cuts[1:]):
        if end - start < a.min_scene:
            continue
        t = start + a.every
        while t < end - a.every / 2:
            times.append((t, start, end))
            t += a.every
        times.append((max(start + 0.2, end - 0.7), start, end))

    cdir, sdir = os.path.join(d, "candidates"), os.path.join(d, "sheets")
    for p in (cdir, sdir):
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p)

    kept, last = [], None
    for t, s0, s1 in times:
        out = os.path.join(cdir, f"c_{len(kept) + 1:03d}.jpg")
        h = grab_with_hash(video, t, out)
        if h is None:
            continue
        if last is not None and sum(x != y for x, y in zip(h, last)) < a.dup:
            os.remove(out)
            continue
        last = h
        kept.append({"n": len(kept) + 1, "t": round(t, 2), "ts": ts(t),
                     "scene": f"{ts(s0)}-{ts(s1)}", "file": f"candidates/{os.path.basename(out)}"})

    json.dump(kept, open(os.path.join(d, "candidates.json"), "w"), indent=1)

    for i in range(0, len(kept), PER_SHEET):
        k = i // PER_SHEET + 1
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-start_number", str(i + 1),
                        "-i", os.path.join(cdir, "c_%03d.jpg"), "-frames:v", "1",
                        "-vf", "scale=320:-2,tile=4x4:padding=4:color=white",
                        os.path.join(sdir, f"sheet_{k:02d}.jpg")], check=True)

    print(f"{len(cuts) - 2} scene cuts -> {len(kept)} candidates after dedupe.")
    print("Each entry: #n frame-time (scene start-end). The frame is grabbed near the END of its scene;")
    print("to show something earlier in that scene, pick your own time inside the range.")
    for i in range(0, len(kept), PER_SHEET):
        chunk = kept[i:i + PER_SHEET]
        print(f"sheets/sheet_{i // PER_SHEET + 1:02d}.jpg (row by row): " +
              "  ".join(f"#{c['n']} {c['ts']} ({c['scene']})" for c in chunk))


if __name__ == "__main__":
    main()
