# Contributing

Thanks for helping improve talk-to-article.

## Reporting a problem

Open an issue with:
- the agent and OS you used (e.g. Claude Code on macOS 15),
- the script and the command that failed, with its error output,
- for screenshot or layout problems, the timestamp and what you expected.

Please don't attach copyrighted videos or full transcripts. A link to a public video and
the timestamp is enough.

## Changing the code

- Scripts use only the Python standard library (3.9+) plus the `yt-dlp` and `ffmpeg`
  command-line tools. Please don't add Python dependencies.
- Keep mechanical work in `scripts/` (deterministic and testable). Guidance the agent needs
  for judgment calls goes in `SKILL.md` or `references/`.
- Keep `SKILL.md` short. Move details into a reference file and point to it from `SKILL.md`.
- Add or update a test in `tests/` for any change to `check.py`, `build.py` or `common.py`, and
  run:

  ```bash
  python3 -m unittest discover tests
  ```

- Never commit downloaded videos, subtitles, transcripts or articles about real talks. The
  demo in `tests/fixtures/demo/` is fictional on purpose.

## Pull requests

Keep each pull request to a single change, describe how you tested it, and add a line to
`CHANGELOG.md` under "Unreleased".
