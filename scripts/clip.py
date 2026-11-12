#!/usr/bin/env python3
"""Cut a video clip or an animated GIF from the talk.

Usage:
  clip.py <package> --from 16:00 --to 16:08 [--gif] [--width W] [--fps N] [--max 15] [--crop L,T,W,H]
  clip.py <package> --remove clips/clip-1600-1608.gif

--max caps the clip length in seconds (external-publication mode uses 15 by default).
Writes clips/clip-MMSS-MMSS.mp4 (or .gif) and records it in manifest.json["clips"].
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, load_manifest, need, parse_ts, pkg_dir, save_manifest, ts, video_path  # noqa: E402
from grab import crop_filter  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("--from", dest="start")
    ap.add_argument("--to", dest="end")
    ap.add_argument("--remove", help="delete a clip file and its manifest entry")
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--width", type=int, help="default 480 for GIF, 640 for mp4")
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--max", type=float)
    ap.add_argument("--crop")
    ap.add_argument("--alt", default="")
    a = ap.parse_args()
    need("ffmpeg")

    d = pkg_dir(a.package)
    m = load_manifest(d)
    if a.remove:
        name = a.remove if a.remove.startswith("clips/") else f"clips/{a.remove}"
        if os.path.exists(os.path.join(d, name)):
            os.remove(os.path.join(d, name))
        m["clips"] = [c for c in m["clips"] if c["file"] != name]
        save_manifest(d, m)
        print(f"removed {name}")
        return
    if not (a.start and a.end):
        die("--from and --to are required")
    width = a.width or (480 if a.gif else 640)
    start, end = parse_ts(a.start), parse_ts(a.end)
    if end <= start:
        die("--to must be after --from")
    limit = a.max or (15 if m["options"].get("use") == "external" else None)
    if limit and end - start > limit:
        die(f"clip is {end - start:.0f}s; the limit is {limit:.0f}s (external use). Shorten it or pass --max.")

    os.makedirs(os.path.join(d, "clips"), exist_ok=True)
    ext = "gif" if a.gif else "mp4"
    name = f"clips/clip-{ts(start).replace(':', '')}-{ts(end).replace(':', '')}.{ext}"
    out = os.path.join(d, name)
    crop = crop_filter(a.crop.split(",") if a.crop else None)
    base = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", video_path(d)]
    if a.gif:
        vf = (f"{crop},fps={a.fps},scale={width}:-1:flags=lanczos,split[s0][s1];"
              "[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer")
        subprocess.run(base + ["-vf", vf, "-loop", "0", out], check=True)
    else:
        subprocess.run(base + ["-vf", f"{crop},scale={width}:-2", "-c:v", "libx264", "-crf", "23",
                               "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k",
                               "-movflags", "+faststart", out], check=True)

    m["clips"] = [c for c in m["clips"] if c["file"] != name] + [
        {"file": name, "from": ts(start), "to": ts(end), "start": start, "alt": a.alt}]
    save_manifest(d, m)
    mb = os.path.getsize(out) / 1e6
    print(f"{name}  {mb:.1f} MB")
    if a.gif and mb > 5:
        print("WARN: GIF over 5 MB loads slowly in docs. Shorten it, or lower --width (360) / --fps (8), "
              "or --crop to the moving area.")


if __name__ == "__main__":
    main()
