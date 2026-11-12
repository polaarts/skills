#!/usr/bin/env python3
"""Copy a finished talk into an Obsidian vault as a note.

    python3 obsidian.py <pkg> [<vault>]

The vault path is remembered (~/.config/talk-to-article/vault), so later runs can omit it.

Writes <vault>/Talks/<folder>/<title>.md with properties (speaker, url, date, duration, tags,
status), the YouTube video embedded at the top, and the first mention of each existing vault
note turned into a [[wikilink]]. images/ and clips/ are copied next to the note. The first run
also creates <vault>/Talks/Talks.base, a table of every talk. A note that already exists is
never overwritten, since it may hold your own notes: delete it to export again.
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import VAULT_FILE, VAULT_FOLDER, die, load_manifest, pkg_dir, saved_vault, ts  # noqa: E402

BASE = """filters:
  and:
    - file.inFolder("Talks")
    - file.hasTag("talk")
views:
  - type: table
    name: Talks
    order:
      - file.name
      - speaker
      - published
      - duration
      - status
    sort:
      - property: published
        direction: DESC
"""
# Spans that must stay as they are: code, wikilinks, markdown links/images, bare URLs.
PROTECTED = re.compile(r"`[^`]*`|\[\[[^\]]*\]\]|!?\[[^\]]*\]\([^)]*\)|https?://\S+")


def note_names(vault, skip):
    """Vault note names worth auto-linking: 4+ chars with an uppercase letter or digit, so
    everyday words that happen to be note names ("inicio", "testing") stay plain text."""
    names = set()
    for root, dirs, files in os.walk(vault):
        dirs[:] = [x for x in dirs if not x.startswith(".") and os.path.join(root, x) != skip]
        names.update(f[:-3] for f in files if f.endswith(".md"))
    return sorted((n for n in names if len(n) >= 4 and re.search(r"[A-Z0-9]", n)), key=len, reverse=True)


def link_mentions(md, names):
    """First plain-text mention of each name becomes [[name]] (case-sensitive, whole words),
    skipping headings, code blocks, tables, and existing links."""
    lines, fence, linked = md.split("\n"), False, []
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
        if fence or line.startswith(("#", "```", "|")):
            continue
        for name in names:
            if name in linked:
                continue
            pat = re.compile(r"(?<![\w\[])" + re.escape(name) + r"(?![\w\]])")
            parts, done = PROTECTED.split(line), False
            keep = PROTECTED.findall(line)
            for k, part in enumerate(parts):
                if not done and pat.search(part):
                    parts[k], done = pat.sub(f"[[{name}]]", part, count=1), True
            if done:
                line = "".join(p + (keep[k] if k < len(keep) else "") for k, p in enumerate(parts))
                linked.append(name)
        lines[i] = line
    return "\n".join(lines), linked


def frontmatter(meta, title, lang):
    date = meta.get("upload_date") or ""
    props = {
        "title": title,
        "speaker": f"[[{meta['speaker_or_channel']}]]" if meta.get("speaker_or_channel") else None,
        "url": meta.get("url"),
        "published": f"{date[:4]}-{date[4:6]}-{date[6:]}" if re.fullmatch(r"\d{8}", date) else None,
        "duration": ts(meta["duration"]) if meta.get("duration") else None,
        "lang": lang,
    }
    # json.dumps gives valid YAML strings; the date stays bare so Obsidian types it as a date.
    rows = [f"{k}: {v if k == 'published' else json.dumps(v, ensure_ascii=False)}" for k, v in props.items() if v]
    return "---\n" + "\n".join(rows) + "\ntags:\n  - talk\nstatus: to-review\n---\n"


def main():
    if len(sys.argv) not in (2, 3):
        die(__doc__.strip().split("\n\n")[1].strip())
    d = pkg_dir(sys.argv[1])
    if len(sys.argv) == 3:
        vault = os.path.abspath(os.path.expanduser(sys.argv[2]))
    else:
        vault = saved_vault() or die("no vault known yet: ask the user for their Obsidian vault path and pass it once")
    if not os.path.isdir(os.path.join(vault, ".obsidian")):
        die(f"{vault} is not an Obsidian vault (no .obsidian folder)")
    saved = os.path.expanduser(VAULT_FILE)
    os.makedirs(os.path.dirname(saved), exist_ok=True)
    open(saved, "w", encoding="utf-8").write(vault)
    src = os.path.join(d, "article.md")
    if not os.path.isfile(src):
        die("article.md not found; write it first")
    m, md = load_manifest(d), open(src, encoding="utf-8").read()
    h1 = re.search(r"^#\s+(.+)\n*", md, re.M)
    title = h1.group(1).strip() if h1 else (m["meta"].get("title") or os.path.basename(d))
    if h1:  # the note's name is the title, so the H1 would repeat it
        md = md[:h1.start()] + md[h1.end():]

    dest = os.path.join(vault, VAULT_FOLDER, os.path.basename(os.path.normpath(d)))
    name = re.sub(r'[\\/*?"<>|#^\[\]]+', " ", re.sub(r"\s*:\s*", " - ", title))  # characters Obsidian forbids
    note = os.path.join(dest, re.sub(r"\s+", " ", name).strip()[:120] + ".md")
    if os.path.exists(note):
        die(f"{note} already exists; not overwritten (delete it to export again)")

    md, linked = link_mentions(md, note_names(vault, dest))
    url = m["meta"].get("url") or ""
    video = f"![]({url})\n\n" if "youtube.com" in url or "youtu.be" in url else ""
    os.makedirs(dest, exist_ok=True)
    for sub in ("images", "clips"):
        if os.path.isdir(os.path.join(d, sub)):
            shutil.copytree(os.path.join(d, sub), os.path.join(dest, sub), dirs_exist_ok=True)
    with open(note, "w", encoding="utf-8") as f:
        f.write(frontmatter(m["meta"], title, m["options"].get("lang", "es")) + "\n" + video + md.lstrip())
    base = os.path.join(vault, VAULT_FOLDER, "Talks.base")
    if not os.path.exists(base):
        open(base, "w", encoding="utf-8").write(BASE)
    print(note)
    print("linked: " + (", ".join(linked) if linked else "none"))


if __name__ == "__main__":
    main()
