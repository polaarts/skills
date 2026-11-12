# Batch mode (several talks or a playlist)

1. Ask the menu once.
2. Expand the input: for a playlist, `fetch.py <playlist-url>` prints one URL per line and exits
   with code 3. Show the user the list (title + duration if handy) and confirm before
   processing many hours of video.
3. One package per video. If you can start subagents, give each one video, in parallel
   (about 3–4 at a time; each downloads a video and runs ffmpeg). Each subagent gets:
   - the skill path and the instruction to follow SKILL.md from step 2 (menu already answered),
   - the URL and the exact options as fetch.py flags,
   - "do not ask the user questions; use these options",
   - "use scripts/ocr.py for on-screen text instead of viewing every image" (saves tokens).
   Without subagents, process the videos one after another.
4. Each talk ends as its own folder, `~/talk-articles/<talk-name>-<id>/index.html`.
5. Final report: a table — talk · status · folder path · notes (e.g. "no subtitles → Whisper").
   One failed video never blocks the others; report it and move on.
