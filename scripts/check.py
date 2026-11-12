#!/usr/bin/env python3
"""Validate a package before publishing. Exit 1 if there are errors.

Usage:
  check.py <package>

Checks: article.md exists; every referenced image/clip exists; every H2 section has body text;
each image is followed by a caption with a timestamp; no leftover placeholders; options are set;
external-use rules (attribution block, clip length, no full transcript copied in).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_manifest, parse_ts, pkg_dir  # noqa: E402

# case-sensitive: "todo" is a normal word in Spanish and Portuguese
PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b|(?i:lorem ipsum)|\{\{|\[\[")
TS = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d = pkg_dir(sys.argv[1])
    m = load_manifest(d)
    errors, warns = [], []
    path = os.path.join(d, "article.md")
    if not os.path.isfile(path):
        print("ERROR: article.md missing")
        sys.exit(1)
    md = open(path, encoding="utf-8").read()
    lines = md.splitlines()

    if not re.search(r"^#\s+\S", md, re.M):
        errors.append("no H1 title")
    for k in ("lang", "use", "detail"):
        if not m["options"].get(k):
            errors.append(f"option '{k}' not set in manifest")

    refs = re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", md) + re.findall(r"\]\((clips/[^)\s]+)\)", md)
    for r in refs:
        if not r.startswith("http") and not os.path.isfile(os.path.join(d, r)):
            errors.append(f"missing file: {r}")
    used = set(refs)
    for img in m.get("images", []):
        if img["file"] not in used:
            warns.append(f"grabbed but unused: {img['file']}")

    for i, line in enumerate(lines):
        if re.match(r"\s*!\[", line):
            nxt = next((x for x in lines[i + 1:] if x.strip()), "")
            if not TS.search(nxt):
                errors.append(f"line {i + 1}: image without a timestamped caption right after it")

    sections = re.split(r"^##\s+", md, flags=re.M)[1:]
    for s in sections:
        head, _, body = s.partition("\n")
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body).strip()
        if len(text) < 40:
            errors.append(f"section '{head.strip()}' has almost no text")

    for i, line in enumerate(lines):
        if PLACEHOLDER.search(line):
            errors.append(f"line {i + 1}: placeholder text: {line.strip()[:60]}")

    if m["options"].get("use") == "external":
        head = "\n".join(lines[:12])
        if not (re.search(r"^>", head, re.M) and m["meta"].get("url", "") and (m["meta"]["url"] or "") in head):
            errors.append("external use: attribution block (blockquote with the source URL) must open the article")
        for c in m.get("clips", []):
            if parse_ts(c["to"]) - parse_ts(c["from"]) > 15:
                errors.append(f"external use: clip longer than 15 s: {c['file']}")
        tr = os.path.join(d, "transcript.json")
        if os.path.isfile(tr):
            import json
            words = sum(len(s["text"].split()) for s in json.load(open(tr, encoding="utf-8")))
            if len(md.split()) > 0.8 * words:
                warns.append("external use: article is close to transcript length; summarize more")

    n_img = len(re.findall(r"!\[", md))
    print(f"article.md: {len(md.split())} words, {len(sections)} sections, {n_img} images")
    for w in warns:
        print("WARN:", w)
    for e in errors:
        print("ERROR:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
