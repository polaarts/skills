#!/usr/bin/env python3
"""Native OCR fallback: read on-screen text from images without the agent's vision.

Default practice is to read slides with the agent's own vision while choosing screenshots.
Use this in batch mode or when the agent cannot view images.

Usage:
  ocr.py <image> [<image> ...] [--lang es|en|pt]
  ocr.py <package> --all [--lang ...]      # every image in images/ (or candidates/ if none)

Engine by OS: macOS Vision (swift) · Windows.Media.Ocr (PowerShell) · tesseract (Linux/any).
Prints JSON {file: text}.
"""
import argparse
import glob
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

SWIFT = r"""
import Foundation
import Vision
let langs = CommandLine.arguments[1].split(separator: ",").map(String.init)
for path in CommandLine.arguments.dropFirst(2) {
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = langs
    let handler = VNImageRequestHandler(url: URL(fileURLWithPath: path))
    try? handler.perform([req])
    let text = (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
    print("<<<\(path)>>>")
    print(text)
}
"""

PS = r"""
param([string]$Lang, [string[]]$Paths)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
  $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $type) { $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op)); $t.Wait(); $t.Result }
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new($Lang))
if (-not $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
foreach ($p in $Paths) {
  $f = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path $p).Path)) ([Windows.Storage.StorageFile])
  $s = Await ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $d = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $b = Await ($d.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $r = Await ($engine.RecognizeAsync($b)) ([Windows.Media.Ocr.OcrResult])
  Write-Output "<<<$p>>>"
  Write-Output $r.Text
}
"""

LANGS = {"es": ("es-ES", "spa"), "en": ("en-US", "eng"), "pt": ("pt-BR", "por")}


def split_blocks(out):
    res, cur = {}, None
    for line in out.splitlines():
        if line.startswith("<<<") and line.endswith(">>>"):
            cur = line[3:-3]
            res[cur] = []
        elif cur:
            res[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in res.items()}


def ocr(paths, lang):
    bcp, tess = LANGS.get(lang, LANGS["en"])
    system = platform.system()
    if system == "Darwin" and shutil.which("swiftc"):
        # compile once and cache: interpreting the script with `swift` costs ~60 s per run
        cache = os.path.expanduser("~/.cache/talk-to-article")
        binary = os.path.join(cache, "ocr-vision")
        if not os.path.exists(binary):
            os.makedirs(cache, exist_ok=True)
            src = os.path.join(cache, "ocr-vision.swift")
            open(src, "w").write(SWIFT)
            subprocess.run(["swiftc", "-O", src, "-o", binary], capture_output=True)
        if os.path.exists(binary):
            p = subprocess.run([binary, f"{bcp},en-US", *paths], capture_output=True, text=True)
            if p.returncode == 0:
                return split_blocks(p.stdout)
    if system == "Windows" and shutil.which("powershell"):
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False) as f:
            f.write(PS)
        try:
            p = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", f.name,
                                "-Lang", bcp, "-Paths", ",".join(paths)], capture_output=True, text=True)
        finally:
            os.unlink(f.name)
        if p.returncode == 0:
            return split_blocks(p.stdout)
    if shutil.which("tesseract"):
        out = {}
        for path in paths:
            p = subprocess.run(["tesseract", path, "-", "-l", f"{tess}+eng"], capture_output=True, text=True)
            out[path] = p.stdout.strip()
        return out
    sys.exit("No native OCR engine available. Read the images with your own vision instead "
             "(or install tesseract: scripts/setup.py --install --tesseract).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--lang", default="en", help="language of the slides")
    a = ap.parse_args()
    paths = a.inputs
    if a.all:
        d = os.path.expanduser(a.inputs[0])
        paths = sorted(p for p in glob.glob(os.path.join(d, "images", "*.jpg")) if not os.path.basename(p).startswith("_"))
        paths = paths or sorted(glob.glob(os.path.join(d, "candidates", "*.jpg")))
    paths = [os.path.abspath(p) for p in paths]
    print(json.dumps(ocr(paths, a.lang), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
