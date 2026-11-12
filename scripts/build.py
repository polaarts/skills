#!/usr/bin/env python3
"""Render the package's article.md as <package>/index.html, with a fixed table of contents.

Usage:
  build.py <package> [--clean]

The page references the package's images/ and clips/ folders (relative paths), so the talk's
folder is the deliverable: open index.html, or zip/host the folder as is.
--clean removes the working files (video, candidates, sheets, peeks, subtitles) and keeps only
what the page and later edits need: index.html, article.md, images/, clips/, transcript, manifest
(external use also drops the transcript).

Supports the Markdown subset style.md allows: headings, paragraphs, bullet/numbered lists,
blockquotes, images, links, bold, italic, inline code, fenced code and pipe tables.
GIFs embed like images; .mp4 links to clips become <video> players.
"""
import argparse
import html
import os
import re
import shutil
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, load_manifest, pkg_dir, ts  # noqa: E402

UI = {  # sidebar strings per article language
    "es": {"toc": "Contenido", "search": "Buscar", "none": "Sin resultados", "theme": "Cambiar tema claro/oscuro"},
    "en": {"toc": "Contents", "search": "Search", "none": "No results", "theme": "Toggle light/dark theme"},
    "pt": {"toc": "Conteúdo", "search": "Buscar", "none": "Nenhum resultado", "theme": "Alternar tema claro/escuro"},
}
WORK_FILES = ("candidates", "sheets", "peek", "publish", "info.json", "candidates.json",
              "images/_preview.jpg", "article.html")

LIGHT = "--bg:#f7f8fa;--card:#fff;--fg:#1f2328;--muted:#6b7280;--line:#e6e8ec;--accent:#0a66c2;--code:#f1f3f5;--hover:#f3f4f6;--active:#eceef1;--field:#f3f4f6"
DARK = "--bg:#111214;--card:#18191c;--fg:#ececef;--muted:#9a9ca3;--line:#2a2c31;--accent:#5aa9ff;--code:#222429;--hover:#222429;--active:#2a2c32;--field:#202226"

CSS = """
:root{""" + LIGHT + """;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){""" + DARK + """;color-scheme:dark}}
:root[data-theme=dark]{""" + DARK + """;color-scheme:dark}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--fg);
font:17px/1.65 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.layout{display:grid;grid-template-columns:280px minmax(0,1fr)}
.side{position:sticky;top:0;align-self:start;height:100vh;display:flex;flex-direction:column;
background:var(--bg);border-right:1px solid var(--line);overflow:hidden}
.side-head{display:flex;align-items:flex-start;gap:12px;padding:18px 16px 16px;border-bottom:1px solid var(--line)}
.side-title{flex:1;min-width:0}.side-title b{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:15px;line-height:1.35;font-weight:650}
.side-title span{display:block;margin-top:3px;font-size:13.5px;line-height:1.3;color:var(--muted)}
.icon-btn{flex:none;width:32px;height:32px;display:grid;place-items:center;border:0;border-radius:8px;
background:transparent;color:var(--muted);cursor:pointer}.icon-btn:hover{color:var(--fg)}
.icon-btn:hover{background:var(--hover)}.icon-btn svg{width:18px;height:18px}
.icon-btn .sun{display:none}:root[data-dark] .icon-btn .sun{display:block}:root[data-dark] .icon-btn .moon{display:none}
.search{position:relative;margin:16px 16px 8px}
.search input{width:100%;height:42px;padding:0 64px 0 14px;font:inherit;font-size:15px;color:var(--fg);background:var(--field);
border:1px solid transparent;border-radius:8px;outline:none}
.search input::placeholder{color:var(--muted)}.search input:focus{border-color:var(--accent)}
.search input::-webkit-search-cancel-button{display:none}
.search kbd{position:absolute;right:8px;top:50%;transform:translateY(-50%);padding:2px 7px;font-family:inherit;font-size:12.5px;font-weight:500;line-height:1.4;
color:var(--muted);background:transparent;border:0;pointer-events:none}
.toc{flex:1;overflow-y:auto;padding:4px 12px 16px;font-size:15px;line-height:1.35}
.toc ul{list-style:none;margin:0;padding:0}
.toc a{display:flex;align-items:center;gap:8px;padding:8px 10px;margin:1px 0;border-radius:6px;color:var(--fg);text-decoration:none}
.toc a:hover{background:var(--hover)}
.toc a span{flex:1;min-width:0}
.toc li.l3 a{padding-left:24px;font-size:14px;color:var(--muted)}
.toc a[aria-current=true]{background:var(--active);color:var(--fg);font-weight:600}
.toc .badge{flex:none;min-width:22px;padding:1px 6px;font-size:12px;font-weight:500;text-align:center;color:var(--muted);background:var(--active);border-radius:6px}
.toc .empty{padding:8px 10px;color:var(--muted);font-size:14px}
main{width:100%;max-width:808px;margin:0 auto;padding:40px 24px 80px;min-width:0}
h1{font-size:2.1em;line-height:1.2;margin:0 0 .4em}h2{font-size:1.45em;margin:2em 0 .5em}h3{font-size:1.15em;margin:1.5em 0 .4em}
h2,h3{scroll-margin-top:16px}
p,ul,ol,blockquote,table,pre{margin:0 0 1em}a{color:var(--accent)}
img,video{display:block;max-width:100%;height:auto;border-radius:4px;border:1px solid var(--line);margin:1.2em 0 .3em}
img+em,video+em,p>em:only-child{display:block;color:var(--muted);font-size:.88em;margin-bottom:1.2em}
blockquote{border-left:3px solid var(--line);padding:.2em 1em;color:var(--muted)}
code{background:var(--code);padding:.1em .35em;border-radius:4px;font-size:.92em}
pre{background:var(--code);padding:14px;border-radius:8px;overflow-x:auto}pre code{padding:0;background:none}
table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}th,td{border:1px solid var(--line);padding:6px 10px;text-align:left}
@media (max-width:900px){.layout{display:block}.side{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line)}.toc{max-height:50vh}main{padding:32px 16px 64px}}
"""

# Search filters the contents by heading and section text (accent-insensitive); Cmd+K / Ctrl+K
# focuses it. Scroll-spy marks the section being read. The theme toggle overrides the OS setting.
JS = """
(()=>{const root=document.documentElement,mq=matchMedia('(prefers-color-scheme: dark)');
const btn=document.querySelector('.theme');
const get=()=>{try{return localStorage.getItem('tta-theme')}catch(e){return null}};
const apply=t=>{if(t)root.dataset.theme=t;const dark=t?t==='dark':mq.matches;
root.toggleAttribute('data-dark',dark);btn.setAttribute('aria-pressed',dark)};
apply(get());mq.addEventListener('change',()=>apply(get()));
btn.addEventListener('click',()=>{const t=root.hasAttribute('data-dark')?'light':'dark';try{localStorage.setItem('tta-theme',t)}catch(e){}apply(t)});
const mac=/mac|iphone|ipad/i.test(navigator.userAgentData?.platform||navigator.platform||'');
const kbd=document.querySelector('.search kbd');kbd.textContent=mac?'\\u2318K':'Ctrl K';
const input=document.querySelector('.search input');input.setAttribute('aria-keyshortcuts',mac?'Meta+K':'Control+K');
const links=[...document.querySelectorAll('.toc a')],heads=links.map(a=>document.getElementById(a.hash.slice(1)));
const norm=t=>t.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
const texts=heads.map(h=>{let t=h.textContent,n=h.nextElementSibling;
while(n&&!/^H[1-3]$/.test(n.tagName)){t+=' '+n.textContent;n=n.nextElementSibling}return norm(t)});
const empty=document.querySelector('.toc .empty');
input.addEventListener('input',()=>{const q=norm(input.value.trim());let shown=0;
links.forEach((a,i)=>{const ok=!q||texts[i].includes(q);a.parentElement.hidden=!ok;shown+=ok});empty.hidden=shown>0});
input.addEventListener('keydown',e=>{if(e.key==='Enter'){const a=links.find(a=>!a.parentElement.hidden);if(a){a.click();input.blur()}}
if(e.key==='Escape'){input.value='';input.dispatchEvent(new Event('input'));input.blur()}});
addEventListener('keydown',e=>{if(e.key.toLowerCase()==='k'&&(mac?e.metaKey:e.ctrlKey)){e.preventDefault();input.focus();input.select()}});
let cur=null;function spy(){let i=0;const y=innerHeight*.3;
heads.forEach((h,k)=>{if(h.getBoundingClientRect().top<=y)i=k});
if(innerHeight+scrollY>=document.body.scrollHeight-2)i=heads.length-1;
if(links[i]===cur)return;if(cur)cur.removeAttribute('aria-current');cur=links[i];
cur.setAttribute('aria-current','true');if(innerWidth>900)cur.scrollIntoView({block:'nearest'})}
let t;addEventListener('scroll',()=>{cancelAnimationFrame(t);t=requestAnimationFrame(spy)},{passive:true});spy()})();
"""

MOON = '<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
SUN = '<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
# Applied before first paint so a saved theme doesn't flash.
EARLY = "<script>try{const t=localStorage.getItem('tta-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>"

def anchor(text, used):
    base = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", "", text)).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "-", html.unescape(base).lower()).strip("-")[:50] or "s"
    hid, n = base, 2
    while hid in used:
        hid, n = f"{base}-{n}", n + 1
    used.add(hid)
    return hid


def inline(text):
    out = html.escape(text, quote=False)

    def media(m):
        alt, src = m.group(1), m.group(2)
        if src.endswith(".mp4"):
            return f'<video controls preload="metadata" src="{html.escape(src)}"></video>'
        return f'<img alt="{alt}" src="{src}" loading="lazy">'

    out = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", media, out)
    out = re.sub(r"(?<!\")\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", out)
    return out


def render(md):
    lines, out, toc, used, i = md.splitlines(), [], [], set(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            lang, code = line[3:].strip(), []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            out.append(f'<pre><code class="{html.escape(lang)}">{html.escape(chr(10).join(code))}</code></pre>')
            i += 1
            continue
        m = re.match(r"(#{1,3})\s+(.*)", line)
        if m:
            n, text = len(m.group(1)), inline(m.group(2))
            if n == 1:
                out.append(f"<h1>{text}</h1>")
            else:
                hid = anchor(text, used)
                toc.append((n, hid, re.sub(r"<[^>]+>", "", text)))
                out.append(f'<h{n} id="{hid}">{text}</h{n}>')
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"\|\s*:?-", lines[i + 1]):
            head = [c.strip() for c in line.strip("|").split("|")]
            rows, i = [], i + 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            tb = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>")
            continue
        if re.match(r"\s*([-*]|\d+\.)\s+", line):
            ordered = bool(re.match(r"\s*\d+\.", line))
            items = []
            while i < len(lines) and (re.match(r"\s*([-*]|\d+\.)\s+", lines[i]) or (lines[i].startswith("    ") and items)):
                if lines[i].startswith("    ") and not re.match(r"\s{0,3}([-*]|\d+\.)\s+", lines[i]):
                    items[-1] += " " + lines[i].strip()
                else:
                    items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip("> "))
                i += 1
            out.append(f"<blockquote>{inline(' '.join(quote))}</blockquote>")
            continue
        if not line.strip():
            i += 1
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"(#{1,3}\s|```|\||>|\s*([-*]|\d+\.)\s)", lines[i]):
            para.append(lines[i])
            i += 1
        text = inline(" ".join(para))
        out.append(text if text.startswith(("<img", "<video")) else f"<p>{text}</p>")
    return "\n".join(out), toc


def sidebar(toc, title, subtitle, ui):
    rows = []
    for i, (n, hid, t) in enumerate(toc):
        kids = 0
        if n == 2:
            for m, _, _ in toc[i + 1:]:
                if m == 2:
                    break
                kids += 1
        badge = f'<span class="badge">{kids}</span>' if kids else ""
        rows.append(f'<li class="l{n}"><a href="#{hid}"><span>{html.escape(t)}</span>{badge}</a></li>')
    return (f'<aside class="side"><div class="side-head"><div class="side-title"><b>{html.escape(title)}</b>'
            f'<span>{html.escape(subtitle)}</span></div>'
            f'<button class="icon-btn theme" type="button" aria-label="{ui["theme"]}" title="{ui["theme"]}">{MOON}{SUN}</button></div>'
            f'<div class="search" role="search"><input type="search" placeholder="{ui["search"]}" aria-label="{ui["search"]}" autocomplete="off">'
            f'<kbd>Ctrl K</kbd></div>'
            f'<nav class="toc" aria-label="{ui["toc"]}"><ul>{"".join(rows)}</ul><p class="empty" hidden>{ui["none"]}</p></nav></aside>')

def clean(d, external):
    # legal.md: an externally shared folder must not carry the full transcript.
    extra = ("transcript.md", "transcript.json") if external else ()
    for name in WORK_FILES + extra + tuple(n for n in os.listdir(d) if n.startswith(("video.", "subs."))):
        p = os.path.join(d, name)
        if os.path.isdir(p) and not os.path.islink(p):
            shutil.rmtree(p)
        elif os.path.lexists(p):
            os.remove(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("--clean", action="store_true")
    a = ap.parse_args()
    d = pkg_dir(a.package)
    src = os.path.join(d, "article.md")
    if not os.path.isfile(src):
        die("article.md not found; write it first")
    md = open(src, encoding="utf-8").read()
    m = load_manifest(d)
    title = re.search(r"^#\s+(.+)$", md, re.M)
    title = title.group(1) if title else (m["meta"].get("title") or "Talk")
    body, toc = render(md)
    lang = m["options"].get("lang", "es")
    meta = m["meta"]
    subtitle = " · ".join(x for x in (meta.get("speaker_or_channel"), ts(meta["duration"]) if meta.get("duration") else None) if x)
    nav = sidebar(toc, html.unescape(re.sub(r"<[^>]+>", "", inline(title))), subtitle, UI.get(lang, UI["en"])) if toc else ""
    page = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title>{EARLY}<style>{CSS}</style></head><body>"
            f'<div class="layout">{nav}<main>{body}</main></div><script>{JS}</script></body></html>')
    out = os.path.join(d, "index.html")
    open(out, "w", encoding="utf-8").write(page)
    if a.clean:
        clean(d, m["options"].get("use") == "external")
    print(f"{out}  ({len(toc)} entries in the table of contents)")


if __name__ == "__main__":
    main()
