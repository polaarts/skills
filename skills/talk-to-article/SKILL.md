---
name: talk-to-article
description: Turn a recorded talk, conference session, webinar, keynote or tutorial video (YouTube, Vimeo, conference sites, playlists or a local .mp4) into a technical blog-style article, in Spanish, English or Portuguese, with screenshots of what the speaker shows at each point, plus optional resources table, clips and GIFs. Output is always an HTML page with a fixed, scroll-highlighted table of contents, in one folder per talk (named after the talk + video id) holding the page and its assets. Use this whenever the user shares a talk or video link and wants it documented, summarized as an article, "pasado a documento", turned into notes with captures, or extracted (transcript + images) for their team — even if they don't say "article" — and for batches of talks or a whole playlist.
license: MIT
metadata:
  version: "0.1.0"
  category: Content & Docs
  category-es: Contenido y documentación
  category-pt: Conteúdo e documentação
  platforms: Claude Code, Agent-neutral
  summary: Turns a recorded talk into a technical blog-style article with screenshots, as one HTML page per talk.
  summary-es: Convierte una charla grabada en un artículo técnico de estilo blog con capturas, en una página HTML por charla.
  summary-pt: Transforma uma palestra gravada em um artigo técnico no estilo de blog com capturas, em uma página HTML por palestra.
---

# talk-to-article

Turn a talk into an article a reader can learn from without watching the video: the speaker's
ideas rewritten as a technical blog post, with the slide or demo they were showing placed
right where it is explained.

The work splits in two:
- **Mechanical steps are scripts** (`scripts/`, Python 3 standard library + `yt-dlp` + `ffmpeg`):
  download, transcript, frame candidates, crops, clips, OCR, HTML build, validation. They are
  deterministic and cheap; don't rewrite them inline.
- **Judgment is yours**: the outline, which screenshots matter, the writing, the fidelity check.

One folder per talk, `~/talk-articles/<talk-name>-<id>/` (e.g.
`design-will-never-be-the-same-na1OyJ3E7Kc`; `fetch.py` names it from the title, and a local
file gets `<file-name>-<hash>`). The output is **always HTML**: no other destinations.

The finished folder is the deliverable — open `index.html`, or zip/host the folder as is:
`index.html` (fixed, non-collapsible sidebar card with the talk's title, a search box over
headings and section text — ⌘K on macOS, Ctrl+K elsewhere — and the table of contents, which
highlights the section being read; a light/dark toggle that remembers the choice; for YouTube
talks, the video at the bottom, which screenshot timestamps seek to — it plays only when the
folder is served, e.g. `python3 -m http.server`, not opened from disk) · `images/` · `clips/` · `article.md` (source the page is built from)
· `transcript.md` · `manifest.json`. While working it also holds the video, `candidates/`,
`sheets/` and `peek/`; `build.py --clean` removes them at the end.

Run scripts as `python3 <skill-dir>/scripts/<name>.py ...` (`python` on Windows).
`<pkg>` below is the package path, its folder name, or just the video id.

## 1. Menu

Ask the menu before downloading anything; `references/menu.md` has the exact questions,
options and defaults. One call, four questions: **language** (Español / English / Português) ·
**use** (internal / external publication) · **detail** (full article / executive summary) ·
**extras** (resources table, GIFs, clips, Obsidian note; multi-select). Don't ask for a destination: it is
always the HTML folder.

Use whatever structured-question tool you have (AskUserQuestion, ask_user, request_user_input,
AskQuestion…). Without one, print a numbered text menu and wait. If nobody can answer
(headless/CI) or the user already gave the choices (e.g. `--lang pt --use external`), use them or
the defaults and record them — don't block.

## 2. Prepare

```
python3 scripts/setup.py                 # checks yt-dlp, ffmpeg; prints install commands per OS
python3 scripts/setup.py --install       # installs what's missing (ask the user first)
python3 scripts/fetch.py <url|file> --lang es --use internal --detail full --extras resources,gifs
python3 scripts/transcript.py <pkg>      # add --whisper if fetch said there are no subtitles
python3 scripts/frames.py <pkg>
```
- `fetch.py` exits with code 3 and prints entry URLs for a playlist → batch mode
  (`references/batch.md`). Several URLs from the user → batch mode too.
- Re-running is safe: the package caches downloads.
- Never bypass access controls: if a download is blocked (HTTP 429, a bot check, sign-in or
  private video), don't retry with cookies, other clients or proxies. Use Whisper for
  missing subtitles, or stop and tell the user what failed.
- Whisper is heavy (PyTorch + models). Install it only when a video truly has no subtitles, and
  tell the user before you do.

Metadata titles can carry OCR-like typos from the uploader (e.g. "with Al" for "with AI");
prefer the slide or the obvious reading, and note anything you couldn't confirm.

## 3. Outline

Read `transcript.md` (it is grouped by the video's chapters when there are any) and the
description in `manifest.json`. Plan one H2 section per idea, tool, case study or demo — not
one per chapter by reflex: chapters are often coarse or oddly named. Note each section's time
range; you'll pick its screenshots inside that range.

## 4. Screenshots

Look at every `sheets/sheet_NN.jpg`; `frames.py` printed which `#n mm:ss (scene start-end)` sits
at each position (row by row). Each candidate is grabbed near the END of its scene so slides are
fully built — the slide you see at #n may have been on screen since the scene start; to check
any moment, `grab.py <pkg> --peek mm:ss` (writes `peek/`, adds nothing to the article).

Pick 1–3 per section: what a reader needs to *see* to follow the explanation (the tool's UI,
the diagram, the result, the command). Skip the speaker-only shots, title cards, applause and
near-repeats. Details and crop guidance: `references/frames.md`.

Write the picks to `<pkg>/selections.json` and run `grab.py <pkg> --plan <pkg>/selections.json`.
Images are named by timestamp (`images/0345.jpg`), so re-running the plan never renames what the
article already uses, and the script prints a ready-to-paste image + caption block.
Then **look at `images/_preview.jpg`** — layouts change mid-talk, so a crop that fit one slide
can cut the next; fix and re-run.

While viewing the chosen images, read their on-screen text with your own vision and keep a
small glossary of proper names (tools, libraries, companies, commands). Auto-captions mangle
names ("Tweek Pane" → Tweakpane); the slide is the authority. If you can't view images, or in
batch mode, use `scripts/ocr.py` (native OCR per OS) instead.

## 5. Write `article.md`

Follow `references/style.md` (structure, voice, captions, per-language labels). Essentials:
- A technical blog post, not a script: no fillers, no "so, uh", no narration of the talk
  ("then he says…"); state the ideas directly and attribute claims and numbers to the speaker
  where it matters.
- Every image is followed by its caption line: label, timestamp deep-linked to that second of
  the video, and what it shows.
- Only what the talk says. Don't add facts from memory; if something is unclear in the audio,
  say so or leave it out.
- `detail: summary` → a lead, 4–7 key ideas with their best screenshot each, and resources.
- `use: external` → the rules in `references/legal.md` (attribution block first, condensed,
  limited screenshots and clips). Default to internal when unsure.

Extras:
- **resources** → a table of tools, libraries, commands, repos and links mentioned (names
  spelled as on the slides; link only URLs that appear in the talk/description or that you
  opened).
- **gifs / clips** → for moments where motion is the point (a live demo, an animation):
  `clip.py <pkg> --from 16:20 --to 16:28 --gif` (480 px, 10 fps by default; warns over 5 MB).
  Keep GIFs ≤ 10 s; external use caps clips at 15 s. Discard one with `clip.py <pkg> --remove <file>`.

## 6. Verify

1. **Fidelity review** — a fresh reader compares `article.md` with `transcript.md` and lists
   claims not supported by the talk, wrong numbers or names, and important points missed.
   Use a subagent if you can (prompt in `references/review.md`); otherwise do it yourself as
   a deliberate second pass. Fix what it finds.
2. `python3 scripts/check.py <pkg>` must print OK (files exist, every image has a timestamped
   caption, no empty sections, no placeholders, external-use rules).

## 7. Build the page

```
python3 scripts/build.py <pkg>            # writes <pkg>/index.html (H2/H3 become the table of contents)
python3 scripts/build.py <pkg> --clean    # last run: also deletes video, candidates, sheets, peeks
```
Headings are the table of contents, so keep them short and meaningful. Open `index.html`
(e.g. `open` on macOS) and check it, then rebuild with `--clean` as the final step. Images and
clips are referenced from the folder, not embedded: share the whole folder (zip it), never
the HTML alone. If the user later wants more screenshots, `fetch.py` re-downloads the video
into the same folder.

**Obsidian (when extras include `obsidian`, or the user asks):** before the final
`build.py --clean`, run `python3 scripts/obsidian.py <pkg>`, so the page gets an "Open in
Obsidian" button (internal use only: it holds a local path). The vault path is remembered from the last run; if the
script says no vault is known yet, ask the user for it and pass it as a second argument. It copies the article into `<vault>/Talks/<folder>/` as a note with properties, the video embedded,
and the first mention of each existing vault note linked; the first run also creates
`Talks/Talks.base`. It never overwrites an existing note (the user may have written in it).

## 8. Report

Tell the user, briefly: the folder and its `index.html`, what it covers (sections, screenshots,
extras), and anything you could not do or verify (e.g. names you couldn't confirm, a section
whose audio was unclear). For external use, remind them that
asking the speaker's permission or tagging them is good practice.

## Gotchas learned the hard way

- `ffmpeg -loglevel error` hides `showinfo` timestamps; `frames.py` handles it — don't
  "optimize" its log level.
- The frame exactly at a scene cut is often a half-built slide; that's why candidates come
  from the end of each scene.
- Crop only after viewing that exact frame; check `_preview.jpg`.
- macOS OCR compiles a small Swift helper on first use (~6 s), then it's instant.
