# Changelog

All notable changes are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added
- Skill workflow (`SKILL.md`): menu, download, transcript, outline, screenshots, writing,
  fidelity review, validation and build.
- Menu with four questions: language (es / en / pt), internal or external use, full article or
  executive summary, and extras (resources table, GIFs, clips).
- Scripts (standard library only): `setup.py`, `fetch.py`, `transcript.py`, `frames.py`,
  `grab.py`, `clip.py`, `ocr.py`, `check.py`, `build.py`.
- HTML output: one folder per talk, named `<talk-name>-<id>`, with `index.html` and its assets.
- Sidebar with search (⌘K / Ctrl+K), a table of contents that highlights the current section,
  and a light/dark theme toggle.
- External-use rules (attribution, condensed content, short clips) checked by `check.py`.
- Batch mode for playlists and lists of URLs.
- Offline tests and a demo fixture.
- Monochrome page design shared with the project site (`site/index.html`): hairline borders,
  square corners, Geist and Geist Mono embedded from `assets/fonts/` (SIL OFL 1.1).

- YouTube player at the bottom of the sidebar. Clicking a screenshot's timestamp seeks it to
  that second instead of opening YouTube (wide screens; on narrow ones the link still opens
  YouTube). Opened from disk (`file://`), YouTube refuses the embed, so the sidebar shows how to
  serve the folder instead.
- `obsidian.py`: copies a finished article into an Obsidian vault as a note with properties
  (speaker, url, date, duration, tags, status), the YouTube video embedded, the first mention
  of each existing vault note turned into a `[[wikilink]]`, and a `Talks.base` table of every
  talk. Existing notes are never overwritten. Offered in the menu as an extra; the vault path
  is remembered after the first run. Once exported, the page shows an "Open in Obsidian"
  button (not in pages for external use, since the link holds a local path).

### Fixed
- Page search now covers the intro above the first heading, shows a snippet of the matching
  text under each result, highlights every match in the article, and jumps to the first match
  instead of the section heading. Table cells no longer run together in the searched text.

### Changed
- The skill now lives in the `polaarts/skills` collection, under `skills/talk-to-article/`.
  Install it with `npx skills add polaarts/skills@talk-to-article` or by copying the folder.
- `SKILL.md` frontmatter gains `license` and `metadata` (version, category, platforms and
  per-language summaries) for the catalog.
