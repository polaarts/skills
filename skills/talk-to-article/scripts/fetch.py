#!/usr/bin/env python3
"""Download a talk (metadata, chapters, subtitles, video) into a package folder.

Usage:
  fetch.py <url | local-video-file> [--root ~/talk-articles] [--max-height 720]
           [--lang es|en|pt] [--use internal|external] [--detail full|summary]
           [--extras resources,clips,gifs,obsidian]

Creates one folder per talk, <root>/<talk-name>-<id>/, with: manifest.json, info.json, video.<ext>, subs.<lang>.<fmt> (if any).
Re-running on the same source reuses what is already downloaded.
A playlist URL prints its entry URLs (one per line) and exits with code 3 — process each one.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DEFAULT_ROOT, die, find_pkg, need, run, save_manifest, load_manifest, slug  # noqa: E402


def pick_subs(info):
    """Prefer human subtitles, then the auto-captions in the spoken language."""
    lang = (info.get("language") or "").split("-")[0]
    manual = {k: v for k, v in (info.get("subtitles") or {}).items() if k != "live_chat"}
    auto = info.get("automatic_captions") or {}
    if manual:
        for k in manual:
            if lang and k.split("-")[0] == lang:
                return k, False
        return next(iter(manual)), False
    for k in ([f"{lang}-orig"] if lang else []) + [k for k in auto if k.endswith("-orig")] + ([lang] if lang else []):
        if k in auto:
            return k, True
    return None, False


def fetch_remote(url, root, max_h):
    need("yt-dlp")
    need("ffmpeg")
    info = json.loads(run(["yt-dlp", "-J", "--no-warnings", "--flat-playlist", url]).stdout)
    if info.get("_type") == "playlist":
        for e in info.get("entries") or []:
            print(e.get("url") or e.get("webpage_url") or e.get("id"))
        sys.exit(3)

    vid = info["id"] if info.get("extractor_key") == "Youtube" else f"{info.get('extractor_key','web').lower()}-{info['id']}"
    vid = re.sub(r"[^A-Za-z0-9_-]+", "-", vid)
    d = find_pkg(root, vid) or os.path.join(root, "-".join(x for x in (slug(info.get("title")), vid) if x))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f)

    sub_lang, is_auto = pick_subs(info)
    if sub_lang and not any(n.startswith("subs.") for n in os.listdir(d)):
        # YouTube often rate-limits subtitle downloads (HTTP 429). Not fatal: fall back to Whisper.
        p = subprocess.run(["yt-dlp", "--no-warnings", "--skip-download",
                            "--write-auto-subs" if is_auto else "--write-subs",
                            "--sub-langs", sub_lang, "--sub-format", "json3/vtt/best",
                            "-o", os.path.join(d, "subs"), url], capture_output=True, text=True)
        if p.returncode != 0 or not any(n.startswith("subs.") for n in os.listdir(d)):
            print(f"WARN: subtitle download failed ({(p.stderr.strip().splitlines() or ['no file'])[-1][:200]}). "
                  "Use transcript.py --whisper.", file=sys.stderr)
            sub_lang = None

    if not any(n.startswith("video.") for n in os.listdir(d)):
        run(["yt-dlp", "--no-warnings", "-q",
             "-f", f"bv*[height<={max_h}]+ba/b[height<={max_h}]/b",
             "--merge-output-format", "mp4",
             "-o", os.path.join(d, "video.%(ext)s"), url])

    meta = {
        "id": vid,
        "title": info.get("title"),
        "speaker_or_channel": info.get("uploader") or info.get("channel"),
        "url": info.get("webpage_url") or url,
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "spoken_language": info.get("language"),
        "subtitles": {"lang": sub_lang, "automatic": is_auto} if sub_lang else None,
        "chapters": [{"start": c["start_time"], "end": c.get("end_time"), "title": c["title"]}
                     for c in (info.get("chapters") or [])],
        "description": (info.get("description") or "")[:4000],
    }
    return d, meta


def fetch_local(path, root):
    need("ffmpeg")
    path = os.path.abspath(os.path.expanduser(path))
    vid = f"{slug(os.path.splitext(os.path.basename(path))[0]) or 'video'}-{hashlib.sha1(path.encode()).hexdigest()[:6]}"
    d = os.path.join(root, vid)
    os.makedirs(d, exist_ok=True)
    link = os.path.join(d, "video" + os.path.splitext(path)[1].lower())
    if not os.path.exists(link):
        try:
            os.symlink(path, link)
        except OSError:  # Windows without symlink rights
            import shutil
            shutil.copy2(path, link)
    probe = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path]).stdout
    meta = {
        "id": vid, "title": os.path.splitext(os.path.basename(path))[0], "speaker_or_channel": None,
        "url": None, "local_file": path, "duration": float(json.loads(probe)["format"]["duration"]),
        "upload_date": None, "spoken_language": None, "subtitles": None, "chapters": [], "description": "",
    }
    return d, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--max-height", type=int, default=720)
    ap.add_argument("--lang", choices=["es", "en", "pt"])
    ap.add_argument("--use", choices=["internal", "external"])
    ap.add_argument("--detail", choices=["full", "summary"])
    ap.add_argument("--extras", help="comma list: resources,clips,gifs,obsidian")
    a = ap.parse_args()

    root = os.path.expanduser(a.root)
    if os.path.exists(os.path.expanduser(a.source)):
        d, meta = fetch_local(a.source, root)
    elif re.match(r"https?://", a.source):
        d, meta = fetch_remote(a.source, root, a.max_height)
    else:
        die(f"not a URL or an existing file: {a.source}")

    m = load_manifest(d) if os.path.exists(os.path.join(d, "manifest.json")) else {
        "options": {"lang": "es", "use": "internal", "detail": "full", "extras": ["resources"]},
        "images": [], "clips": [], "uploads": {}, "publish": {},
    }
    m["meta"] = meta
    for k in ("lang", "use", "detail"):
        if getattr(a, k):
            m["options"][k] = getattr(a, k)
    if a.extras is not None:
        m["options"]["extras"] = [x for x in a.extras.split(",") if x]
    m["options"].pop("target", None)  # HTML is the only output
    save_manifest(d, m)

    print(json.dumps({
        "package": d, "title": meta["title"], "duration": meta["duration"],
        "subtitles": meta["subtitles"], "chapters": len(meta["chapters"]), "options": m["options"],
    }, ensure_ascii=False, indent=2))
    if not meta["subtitles"]:
        print("NOTE: no subtitles found. Run transcript.py --whisper (needs Whisper; see setup.py).")


if __name__ == "__main__":
    main()
