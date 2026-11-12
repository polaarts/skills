"""Shared helpers for talk-to-article scripts. Standard library only."""
import glob
import json
import os
import shutil
import re
import subprocess
import sys
import unicodedata

DEFAULT_ROOT = os.path.expanduser("~/talk-articles")
VAULT_FILE = "~/.config/talk-to-article/vault"  # last Obsidian vault obsidian.py exported to
VAULT_FOLDER = "Talks"


def saved_vault():
    try:
        return open(os.path.expanduser(VAULT_FILE), encoding="utf-8").read().strip() or None
    except OSError:
        return None


def vault_note(d):
    """The note obsidian.py exported for package d into the saved vault, if there is one."""
    vault = saved_vault()
    if not vault:
        return None
    folder = os.path.join(vault, VAULT_FOLDER, os.path.basename(os.path.normpath(d)))
    notes = sorted(glob.glob(os.path.join(glob.escape(folder), "*.md")))
    return notes[0] if notes else None


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def need(tool):
    if not shutil.which(tool):
        die(f"'{tool}' not found. Run scripts/setup.py to see how to install it.")


def run(cmd, **kw):
    """Run a command; return CompletedProcess. Raises with stderr on failure."""
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if p.returncode != 0:
        die(f"command failed: {' '.join(cmd)}\n{p.stderr[-2000:]}")
    return p


def ts(seconds):
    """Seconds -> 'mm:ss' (or 'h:mm:ss')."""
    s = int(round(float(seconds)))
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def parse_ts(value):
    """'3:55', '1:02:03', '235', '235.5' -> seconds (float)."""
    parts = str(value).strip().split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        die(f"invalid timestamp: {value!r}")
    total = 0.0
    for n in nums:
        total = total * 60 + n
    return total


def slug(text, limit=60):
    """'Design Will Never Be The Same!' -> 'design-will-never-be-the-same' (ASCII, lowercase)."""
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:limit].rstrip("-")


def find_pkg(root, vid):
    """Existing folder for a video id: '<talk-name>-<id>' (or a legacy '<id>'), else None."""
    if not os.path.isdir(root):
        return None
    for name in sorted(os.listdir(root)):
        if (name == vid or name.endswith(f"-{vid}")) and os.path.isdir(os.path.join(root, name)):
            return os.path.join(root, name)
    return None


def pkg_dir(arg):
    """Accept a package dir path, its folder name, or a bare video id under the default root."""
    path = os.path.expanduser(arg)
    if not os.path.isdir(path):
        path = find_pkg(DEFAULT_ROOT, arg) or os.path.join(DEFAULT_ROOT, arg)
    if not os.path.isfile(os.path.join(path, "manifest.json")):
        die(f"no talk-to-article package at {arg} (missing manifest.json). Run fetch.py first.")
    return path


def load_manifest(d):
    with open(os.path.join(d, "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def save_manifest(d, m):
    tmp = os.path.join(d, "manifest.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    os.replace(tmp, os.path.join(d, "manifest.json"))


def video_path(d):
    for name in sorted(os.listdir(d)):
        if name.startswith("video."):
            return os.path.join(d, name)
    die(f"no video file in {d}. Run fetch.py first.")


def deep_link(manifest, seconds):
    """Link to the exact moment in the source video, when the platform supports it."""
    url = manifest["meta"].get("url") or ""
    if not url.startswith("http"):
        return None
    sep = "&" if "?" in url else "?"
    if "youtube.com" in url or "youtu.be" in url:
        return f"{url}{sep}t={int(seconds)}s"
    if "vimeo.com" in url:
        return f"{url}#t={int(seconds)}s"
    return None
