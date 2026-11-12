# Writing the article

## Voice

Write as a technical blog author explaining what the talk teaches, in the chosen language
(es / en / pt), whatever language the talk was in.

- Turn speech into prose: drop fillers, false starts, "so", "uh", "as you can see here",
  jokes that need the room. Merge points the speaker made across several sentences.
- State ideas directly ("Un caché local reduce…"), not as narration ("Luego la ponente dice que…").
  Name the speaker in the lead, and attribute opinions, numbers and claims where it matters
  ("según García, la migración les tomó tres semanas").
- Keep the speaker's concrete details: numbers, tool names, prompts, commands, timings,
  client examples. They are what makes the article worth reading.
- Translate prose, not identifiers: product names, commands, code, UI labels and quoted
  prompts stay as shown (optionally with a translation after them).
- Short paragraphs (≤ 3 sentences). Bullets for parallel items (controls, steps, options).
  Numbered lists for sequences. A table when items share attributes.
- No facts from outside the talk. Unclear audio → omit or flag it, don't guess.

## Structure (full article)

```
# <Title: the talk's thesis, in the chosen language>

<Lead: 2–3 sentences — the main idea, who gave the talk, where/when.>

## <Section per idea, tool, case or demo>
<Text>
![<alt>](images/mmss.jpg)
*<Label> [mm:ss](<deep link>) · <what the image shows>*

## <Recursos / Resources / Recursos>        (if the resources extra is on)
| Recurso | Qué es | Enlace |
(Drop the Enlace column if the talk and its description give no URLs; say so in one line
under the table instead of filling cells with "—".)

## <Conclusiones / Key takeaways / Conclusões>
<2–3 sentences + 3–5 bullets>

## <Fuente / Source / Fonte>
- Video: [<title>](<url>), <channel>, <date>, <duration>.
- Note that the text is based on the (auto) transcript, rewritten as an article.
- A table of the video's chapters with deep links, if it has chapters.
```

External use adds the attribution block right under the title (see `legal.md`).

Summary mode: title, lead, one H2 "Ideas clave" with 4–7 short subsections (H3) each with its
best screenshot, then resources and source.

## Captions

Every image and GIF gets the next line as its caption, in italics:
`*<Label> [mm:ss](<url>&t=<seconds>s) · <description>*`

Labels per language: es "Captura" / "Clip", en "Screenshot" / "Clip", pt "Captura" / "Clipe".
Deep links: YouTube `&t=235s`, Vimeo `#t=235s`; local files have no link (plain `mm:ss`).
Clips (.mp4) are linked, not embedded in Markdown: `[▶ Clip 16:20–16:28](clips/clip-1620-1628.mp4)`.

## Section names per language

| | es | en | pt |
|---|---|---|---|
| Resources | Recursos | Resources | Recursos |
| Conclusions | Conclusiones | Key takeaways | Conclusões |
| Source | Fuente | Source | Fonte |
| Key ideas (summary) | Ideas clave | Key ideas | Ideias-chave |
