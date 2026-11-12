# Choosing and preparing screenshots

## What earns a screenshot

A screenshot should show something the text describes but can't convey as well: the tool's
interface, a diagram, a before/after, a chart, a code or command slide, the final result.

Good: the app with its control panel while the speaker explains the parameters; the
architecture slide while he walks through it; the command on screen.
Skip: speaker-only shots, audience shots, title/sponsor cards, "Thank you", a slide that
repeats one already used, frames mid-transition.

Aim for 1–3 per H2 section, about one per 45–90 s of talk in a full article (a 20-min talk
≈ 15–25 images). Summary mode: 4–8 total.

## Picking a time

`frames.py` gives the last stable frame of each scene. You may also choose any other second
(`"t": "12:41"`), e.g. the moment the speaker points at the relevant part of a demo, by
reading the transcript around it. When a scene is a live demo, the candidates every 30 s help
you find the best state.

## Crop (picture-in-picture recordings)

Many conference recordings show the slide in a box next to the speaker. Crop to the slide when
the box is clearly smaller than the frame (it reads much better in a doc):

1. Look at the full-resolution frame at that time: `grab.py <pkg> --peek mm:ss` then view
   `peek/<mmss>.jpg` (peeks are not added to the article).
2. Estimate the slide's box as fractions: left, top, width, height (0–1). Add a small margin.
3. Put it in `"crop": [l, t, w, h]` for that selection.
4. Run `grab.py --plan` and **check `images/_preview.jpg`**.

Layouts switch during a talk (PiP ↔ full-screen slide ↔ stage camera), so never copy one crop
to all selections without looking.

## selections.json example

```json
[
  {"t": "0:55",  "alt": "Ejemplos de apps propias", "section": "Introducción"},
  {"t": "3:55",  "alt": "App de gráficos procedurales con su panel", "section": "Caso 1",
   "crop": [0.255, 0.13, 0.73, 0.74]},
  {"t": "15:46", "alt": "Comando para crear una app con Toolcraft", "section": "Cómo empezar"}
]
```
`grab.py --plan` replaces previous grabs, so the file is always the full list in reading order.
Image files are named by timestamp (`images/0055.jpg`, `images/0355.jpg` …), so editing the
plan and re-running it keeps the names the article already references.

## On-screen text

Read slide text with your own vision while choosing — it's free since you are already looking.
Use it to spell names correctly and to capture commands, URLs and numbers exactly.
Fallback: `scripts/ocr.py <images...> --lang en` (macOS Vision, Windows OCR, or tesseract).
OCR text of UI screenshots is noisy; trust it for titles, names and commands, not for prose.
