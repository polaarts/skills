#!/usr/bin/env python3
"""Check (and optionally install) talk-to-article dependencies on macOS, Linux or Windows.

Usage:
  setup.py                 # report what is installed and the install command for what is missing
  setup.py --install       # install the required tools (yt-dlp, ffmpeg)
  setup.py --install --whisper   # also install Whisper (only needed when a video has no subtitles)
  setup.py --install --tesseract # also install Tesseract OCR (Linux native-OCR fallback)
"""
import argparse
import platform
import shutil
import subprocess
import sys

SYSTEM = platform.system()  # Darwin | Linux | Windows

INSTALL = {
    "Darwin": {
        "yt-dlp": ["brew", "install", "yt-dlp"],
        "ffmpeg": ["brew", "install", "ffmpeg"],
        "tesseract": ["brew", "install", "tesseract", "tesseract-lang"],
    },
    "Linux": {
        "yt-dlp": [sys.executable, "-m", "pip", "install", "--user", "-U", "yt-dlp"],
        "ffmpeg": ["sudo", "apt-get", "install", "-y", "ffmpeg"],
        "tesseract": ["sudo", "apt-get", "install", "-y", "tesseract-ocr",
                      "tesseract-ocr-spa", "tesseract-ocr-por", "tesseract-ocr-eng"],
    },
    "Windows": {
        "yt-dlp": ["winget", "install", "--id", "yt-dlp.yt-dlp", "-e"],
        "ffmpeg": ["winget", "install", "--id", "Gyan.FFmpeg", "-e"],
        "tesseract": ["winget", "install", "--id", "UB-Mannheim.TesseractOCR", "-e"],
    },
}
WHISPER = [sys.executable, "-m", "pip", "install", "--user", "-U", "openai-whisper"]


def native_ocr():
    if SYSTEM == "Darwin":
        return "macOS Vision (swift)" if shutil.which("swift") else None
    if SYSTEM == "Windows":
        return "Windows.Media.Ocr (PowerShell)" if shutil.which("powershell") else None
    return "tesseract" if shutil.which("tesseract") else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--whisper", action="store_true")
    ap.add_argument("--tesseract", action="store_true")
    a = ap.parse_args()

    cmds = INSTALL.get(SYSTEM)
    if not cmds:
        print(f"Unsupported OS: {SYSTEM}")
        sys.exit(1)

    wanted = ["yt-dlp", "ffmpeg"] + (["tesseract"] if a.tesseract else [])
    missing = [t for t in wanted if not shutil.which(t)]
    has_whisper = bool(shutil.which("whisper"))

    print(f"OS: {SYSTEM}")
    for t in ["yt-dlp", "ffmpeg"]:
        print(f"  {t:10} {'OK' if shutil.which(t) else 'MISSING'}")
    print(f"  {'whisper':10} {'OK' if has_whisper else 'not installed (only needed for videos without subtitles)'}")
    print(f"  {'OCR':10} {native_ocr() or 'no native OCR (agent vision is the default anyway)'}")

    todo = [cmds[t] for t in missing]
    if a.whisper and not has_whisper:
        todo.append(WHISPER)

    if not todo:
        print("Ready.")
        return
    if not a.install:
        print("\nTo install what is missing, run (or re-run this script with --install):")
        for c in todo:
            print("  " + " ".join(c))
        sys.exit(2)
    for c in todo:
        print("$ " + " ".join(c))
        if subprocess.run(c).returncode != 0:
            print("Install failed; see output above.")
            sys.exit(1)
    print("Ready.")


if __name__ == "__main__":
    main()
