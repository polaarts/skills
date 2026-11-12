# Initial menu

Ask in the user's language, in **one call with four questions** (the usual limit of
structured-question tools). Recommended option first. The output is always the HTML folder,
so there is no destination question.

1. **Idioma / Language / Idioma** — header `Idioma`
   - Español · English · Português
2. **Uso** — header `Uso`
   - Interno (equipo, wiki, notas) — *default*
   - Publicación externa (blog, LinkedIn, cliente) — activa las reglas de `legal.md`
3. **Nivel de detalle** — header `Detalle`
   - Artículo completo — *default*
   - Resumen ejecutivo con capturas
4. **Extras** — header `Extras`, multiSelect
   - Tabla de recursos (herramientas, comandos, enlaces) — *default on*
   - GIFs de demos animadas
   - Clips .mp4 de momentos clave
   - Nota en Obsidian (copia el artículo a tu vault, enlazado con tus notas) — *default on* once
     the user has used it before (`~/.config/talk-to-article/vault` exists)
   With external use, describe clips as "clips cortos (≤ 15 s)".

## Without a question tool

Print one compact numbered menu and wait:

```
Antes de empezar (el resultado es una página HTML con índice lateral):
1) Idioma:   a) Español  b) English  c) Português
2) Uso:      a) Interno  b) Publicación externa
3) Detalle:  a) Artículo completo  b) Resumen ejecutivo
4) Extras (varios): a) Recursos  b) GIFs  c) Clips  d) Nota en Obsidian
Responde por ejemplo: 1a 2a 3a 4ab   (Enter = valores por defecto)
```

## No one can answer (headless / CI / batch sub-agent)

Use arguments if given, else defaults: `lang=es, use=internal, detail=full, extras=resources`.
Record them in `manifest.json` (fetch.py does this) and mention the defaults in the final report.

## Batch mode

Ask the menu once; the same options apply to every video.
