# Internal vs external use

This is practical guidance, not legal advice. The article reuses someone else's work (their
ideas, slides and footage), so how much of it is reproduced should match who will read it.

## Internal (default)

Notes for the user or their team, a company wiki, a doc shared inside the organization.
Comparable to taking detailed notes of a talk. The normal style rules apply. Still credit the
source in the "Fuente" section.

## External publication

Public blog, LinkedIn, Medium, newsletter, client deliverable. Apply all of these:

1. **Attribution block first**, right under the title, as a blockquote:
   `> Resumen no oficial de la charla [<title>](<url>) de <speaker>, presentada en <event>.`
   (translated to the article's language). `check.py` verifies it.
2. **Condense and comment**, don't reproduce: aim for well under the transcript's length; no
   long verbatim quotes (one or two short quotes, marked as such, are fine).
3. **Fewer images**: the key ones only (roughly half of what an internal article would use).
4. **Clips ≤ 15 s** (`clip.py` enforces it) and GIFs ≤ 10 s, each linked to its moment in the
   original.
5. **No downloads** of the full video, audio or transcript in the published piece.
6. In the final report, suggest asking the speaker for permission or tagging them, and keep
   the link to the original prominent.
