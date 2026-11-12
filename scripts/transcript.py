#!/usr/bin/env python3
"""Turn subtitles (or a Whisper transcription) into a timestamped transcript grouped by chapter.

Usage:
  transcript.py <package> [--bucket 20] [--whisper] [--model small]

Writes transcript.md (for reading) and transcript.json (segments: start, end, text).
"""
import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, load_manifest, pkg_dir, run, save_manifest, ts, video_path  # noqa: E402

NOISE = re.compile(r"\[(music|música|applause|aplausos|laughter|risas|snorts|inaudible)\]|>>", re.I)


def from_json3(path):
    data = json.load(open(path, encoding="utf-8"))
    segs = []
    for e in data.get("events", []):
        text = "".join(s.get("utf8", "") for s in e.get("segs", []) or []).replace("\n", " ").strip()
        if text:
            start = e["tStartMs"] / 1000
            segs.append({"start": start, "end": start + e.get("dDurationMs", 0) / 1000, "text": text})
    return segs


def from_vtt(path):
    segs, cur = [], None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        m = re.match(r"([\d:.]+)\s+-->\s+([\d:.]+)", line)
        if m:
            cur = {"start": _vtt_s(m.group(1)), "end": _vtt_s(m.group(2)), "text": ""}
            segs.append(cur)
        elif line and cur is not None and not line.startswith(("WEBVTT", "NOTE", "Kind:", "Language:")):
            cur["text"] = (cur["text"] + " " + re.sub(r"<[^>]+>", "", line)).strip()
    # auto-VTT repeats rolling lines; drop exact consecutive repeats
    out = []
    for s in segs:
        if s["text"] and (not out or s["text"] != out[-1]["text"]):
            out.append(s)
    return out


def _vtt_s(v):
    parts = [float(p) for p in v.split(":")]
    return sum(p * 60 ** i for i, p in enumerate(reversed(parts)))


def from_whisper(d, model):
    out = os.path.join(d, "whisper.json")
    if not os.path.exists(out):
        if not shutil.which("whisper"):
            die("Whisper is not installed. Run: scripts/setup.py --install --whisper")
        vp = video_path(d)
        run(["whisper", vp, "--model", model, "--output_format", "json", "--output_dir", d])
        os.replace(os.path.join(d, os.path.splitext(os.path.basename(vp))[0] + ".json"), out)
    data = json.load(open(out, encoding="utf-8"))
    return [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in data["segments"]], data.get("language")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("--bucket", type=int, default=20, help="seconds per transcript line")
    ap.add_argument("--whisper", action="store_true", help="transcribe audio when there are no subtitles")
    ap.add_argument("--model", default="small")
    a = ap.parse_args()

    d = pkg_dir(a.package)
    m = load_manifest(d)
    subs = sorted(n for n in os.listdir(d) if n.startswith("subs."))
    if subs and not a.whisper:
        p = os.path.join(d, subs[0])
        segs = from_json3(p) if p.endswith(".json3") else from_vtt(p)
        source = f"subtitles ({subs[0]})"
    else:
        segs, lang = from_whisper(d, a.model)
        source = f"whisper ({a.model})"
        m["meta"]["subtitles"] = {"lang": lang, "automatic": True, "whisper": True}
        save_manifest(d, m)
    if not segs:
        die("transcript is empty")

    for s in segs:
        s["text"] = re.sub(r"\s+", " ", NOISE.sub("", s["text"])).strip()
    segs = [s for s in segs if s["text"]]
    json.dump(segs, open(os.path.join(d, "transcript.json"), "w", encoding="utf-8"), ensure_ascii=False)

    chapters = m["meta"].get("chapters") or [{"start": 0, "title": m["meta"].get("title") or "Talk"}]
    lines = [f"# Transcript: {m['meta'].get('title')}", f"Source: {source}", ""]
    ci, bucket, buf = -1, None, []

    def flush():
        if buf:
            lines.append(f"[{ts(bucket)}] " + " ".join(buf))

    for s in segs:
        while ci + 1 < len(chapters) and s["start"] >= chapters[ci + 1]["start"]:
            flush()
            buf, bucket = [], None
            ci += 1
            lines += ["", f"## [{ts(chapters[ci]['start'])}] {chapters[ci]['title']}", ""]
        b = int(s["start"] // a.bucket * a.bucket)
        if b != bucket:
            flush()
            buf, bucket = [], b
        buf.append(s["text"])
    flush()

    with open(os.path.join(d, "transcript.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    words = sum(len(s["text"].split()) for s in segs)
    print(f"transcript.md written: {words} words, {len(chapters)} chapter(s), source: {source}")


if __name__ == "__main__":
    main()
