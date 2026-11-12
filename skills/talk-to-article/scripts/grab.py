#!/usr/bin/env python3
"""Extract the chosen screenshots at full quality, optionally cropped to the slide area.

Usage:
  grab.py <package> --plan selections.json      # batch (recommended)
  grab.py <package> --at 3:55 [--crop L,T,W,H] [--alt "..."]   # add one image
  grab.py <package> --peek 3:55 [--crop L,T,W,H]                 # just look; nothing added

selections.json is a list of:
  {"t": "3:55", "alt": "short description", "section": "Caso 1", "crop": [0.27, 0.11, 0.70, 0.78]}
crop = left, top, width, height as FRACTIONS of the frame (0-1). Use it when the slide is shown
inside a frame with the speaker (picture-in-picture). Omit it for full-screen slides.

Writes images/<mmss>.jpg (named by time, so names stay stable across re-runs), records them in
manifest.json["images"] (--plan replaces earlier grabs), builds images/_preview.jpg to check every
crop in one look, and prints a ready-to-paste Markdown block (image + caption with deep link).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import deep_link, die, load_manifest, need, parse_ts, pkg_dir, save_manifest, ts, video_path  # noqa: E402


def crop_filter(c):
    if not c:
        return "null"
    l, t, w, h = (float(x) for x in c)
    if not (0 <= l < 1 and 0 <= t < 1 and 0 < w <= 1 - l + 1e-6 and 0 < h <= 1 - t + 1e-6):
        die(f"crop out of range: {c}")
    # even sizes keep encoders happy
    return f"crop=trunc(iw*{w}/2)*2:trunc(ih*{h}/2)*2:iw*{l}:ih*{t}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("--plan")
    ap.add_argument("--at")
    ap.add_argument("--crop")
    ap.add_argument("--alt", default="")
    ap.add_argument("--peek", help="just look: write peek/<mmss>.jpg at full size, not added to the article")
    a = ap.parse_args()
    need("ffmpeg")

    d = pkg_dir(a.package)
    m = load_manifest(d)
    video = video_path(d)

    if a.peek:
        sec = parse_ts(a.peek)
        os.makedirs(os.path.join(d, "peek"), exist_ok=True)
        out = os.path.join(d, "peek", f"{ts(sec).replace(':', '')}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{sec:.2f}", "-i", video, "-frames:v", "1",
                        "-vf", crop_filter(a.crop.split(",") if a.crop else None), "-q:v", "2", out], check=True)
        print(out)
        return

    if a.plan:
        plan = json.load(open(a.plan, encoding="utf-8"))
        idir = os.path.join(d, "images")
        shutil.rmtree(idir, ignore_errors=True)
        m["images"] = []
    elif a.at:
        plan = [{"t": a.at, "alt": a.alt, "crop": a.crop.split(",") if a.crop else None}]
    else:
        die("use --plan or --at")
    os.makedirs(os.path.join(d, "images"), exist_ok=True)

    for item in plan:
        sec = parse_ts(item["t"])
        # named by timestamp, not by position, so re-running a plan never renames images the article uses
        stem = f"images/{ts(sec).replace(':', '')}"
        name, k = f"{stem}.jpg", 2
        while any(i["file"] == name for i in m["images"]):
            name, k = f"{stem}-{k}.jpg", k + 1
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{sec:.2f}", "-i", video,
                        "-frames:v", "1", "-vf", crop_filter(item.get("crop")), "-q:v", "2",
                        os.path.join(d, name)], check=True)
        m["images"].append({"file": name, "t": round(sec, 2), "ts": ts(sec), "alt": item.get("alt", ""),
                            "section": item.get("section"), "crop": item.get("crop")})
    save_manifest(d, m)

    # thumbnails first: tiling images of different sizes in one stream resets the filter graph
    with tempfile.TemporaryDirectory() as tmp:
        for n, i in enumerate(m["images"], 1):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(d, i["file"]), "-vf",
                            "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2:white",
                            os.path.join(tmp, f"t_{n:03d}.jpg")], check=True)
        rows = max(1, -(-len(m["images"]) // 5))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(tmp, "t_%03d.jpg"), "-frames:v", "1",
                        "-vf", f"tile=5x{rows}:padding=4:color=white",
                        os.path.join(d, "images", "_preview.jpg")], check=True)

    label = {"en": "Screenshot"}.get(m["options"].get("lang"), "Captura")
    print(f"preview (row by row, 5 per row): {os.path.join(d, 'images', '_preview.jpg')}\n")
    print("Markdown to paste (edit the descriptions):\n")
    for i in m["images"]:
        link = deep_link(m, i["t"])
        stamp = f"[{i['ts']}]({link})" if link else i["ts"]
        print(f"![{i['alt']}]({i['file']})\n*{label} {stamp} · {i['alt']}*\n")


if __name__ == "__main__":
    main()
