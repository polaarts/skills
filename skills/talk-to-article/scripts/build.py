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
import base64
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

# Same monochrome system as the project site (site/index.html): hairlines, zero radius, Geist.
# Light values are the reference tokens; dark mirrors them so the page keeps its theme toggle.
LIGHT = ("--ink:#0a0a0a;--mute-1:#3d3d3d;--mute-2:#6b6b6b;--mute-3:#9a9a9a;--line:#e6e6e6;--line-3:#f0f0f0;"
         "--paper:#fff;--paper-2:#fafafa;--paper-3:#f4f4f4;--code-bg:#0a0a0a;--code-fg:#fff")
DARK = ("--ink:#fafafa;--mute-1:#c4c4c4;--mute-2:#949494;--mute-3:#6b6b6b;--line:#262626;--line-3:#1a1a1a;"
        "--paper:#0a0a0a;--paper-2:#111;--paper-3:#161616;--code-bg:#161616;--code-fg:#fafafa")

CSS = """
:root{""" + LIGHT + """;color-scheme:light;
--sans:Geist,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
--mono:"Geist Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){""" + DARK + """;color-scheme:dark}}
:root[data-theme=dark]{""" + DARK + """;color-scheme:dark}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--mute-1);font:16px/1.625 var(--sans);
-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
::selection{background:var(--ink);color:var(--paper)}
:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
.layout{display:grid;grid-template-columns:300px minmax(0,1fr)}
.side{position:sticky;top:0;align-self:start;height:100vh;display:flex;flex-direction:column;
background:var(--paper);border-right:1px solid var(--line);overflow:hidden}
.side-head{display:flex;align-items:flex-start;gap:12px;padding:20px;border-bottom:1px solid var(--line)}
.side-title{flex:1;min-width:0}
.side-title b{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
font-size:15px;line-height:1.35;font-weight:600;letter-spacing:-.01em;color:var(--ink)}
.side-title span{display:block;margin-top:6px;font:11px/1.4 var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--mute-2)}
.icon-btn{flex:none;width:32px;height:32px;display:grid;place-items:center;border:1px solid var(--line);border-radius:0;
background:var(--paper);color:var(--mute-2);cursor:pointer;transition:color .15s,border-color .15s}
.icon-btn:hover{color:var(--ink);border-color:var(--ink)}.icon-btn svg{width:16px;height:16px}
.icon-btn .sun{display:none}:root[data-dark] .icon-btn .sun{display:block}:root[data-dark] .icon-btn .moon{display:none}
.search{position:relative;margin:16px 20px 8px}
.search input{width:100%;height:36px;padding:0 64px 0 12px;font:12px var(--mono);color:var(--ink);background:var(--paper-2);
border:1px solid var(--line);border-radius:0;outline:none;transition:border-color .15s}
.search input::placeholder{color:var(--mute-2)}.search input:hover,.search input:focus{border-color:var(--ink)}
.search input::-webkit-search-cancel-button{display:none}
.search kbd{position:absolute;right:8px;top:50%;transform:translateY(-50%);padding:2px 6px;font:10px var(--mono);
color:var(--mute-2);background:var(--paper);border:1px solid var(--line);pointer-events:none}
.toc{flex:1;overflow-y:auto;padding:8px 20px 20px;font-size:13px;line-height:1.4}
.toc ul{list-style:none;margin:0;padding:0;border-left:1px solid var(--line)}
.toc a{display:flex;align-items:center;gap:8px;padding:6px 0 6px 12px;margin-left:-1px;border-left:1px solid transparent;
color:var(--mute-2);text-decoration:none;font-weight:400;transition:color .15s,border-color .15s}
.toc a:hover{color:var(--ink)}
.toc a span{flex:1;min-width:0}
.toc li.l3 a{padding-left:24px;font-size:12px}
.toc a[aria-current=true]{color:var(--ink);border-left-color:var(--ink);font-weight:600}
.toc .badge{flex:none;min-width:22px;padding:1px 6px;font:10px/1.5 var(--mono);text-align:center;color:var(--mute-2);
background:var(--paper-3);border:1px solid var(--line)}
.toc .empty{padding:8px 0;color:var(--mute-2);font-size:13px}
.toc.searching .badge{display:none}
.toc .snip{display:block;margin-top:4px;font-size:12px;line-height:1.45;font-weight:400;color:var(--mute-2);overflow-wrap:anywhere}
.toc .snip mark{background:var(--ink);color:var(--paper);padding:0 2px}
::highlight(tta-search){background-color:var(--ink);color:var(--paper)}
main{width:100%;max-width:808px;margin:0 auto;padding:56px 32px 96px;min-width:0}
h1,h2,h3{color:var(--ink);text-wrap:balance}
h1{font-size:48px;line-height:1.05;font-weight:500;letter-spacing:-.03em;margin:0 0 .6em}
h2{font-size:24px;line-height:1.33;font-weight:600;letter-spacing:-.01em;margin:2em 0 .6em}
h3{font-size:18px;line-height:1.4;font-weight:600;margin:1.75em 0 .5em}
h2,h3{scroll-margin-top:24px}
p,ul,ol,blockquote,table,pre{margin:0 0 1em}ul,ol{padding-left:1.25em}li+li{margin-top:.375em}
strong{color:var(--ink);font-weight:600}
a{color:var(--ink);font-weight:500;text-decoration:underline;text-underline-offset:4px;text-decoration-thickness:1px}
a:hover{text-decoration-thickness:2px}
img,video{display:block;max-width:100%;height:auto;border:1px solid var(--line);margin:1.5em 0 .5em;background:var(--paper-3)}
img+em,video+em,p>em:only-child{display:block;font-style:normal;font-size:13px;line-height:1.5;color:var(--mute-2);margin-bottom:1.5em}
blockquote{border-left:2px solid var(--ink);padding:.1em 0 .1em 1em}
code{font-family:var(--mono);font-size:.85em;color:var(--ink);background:var(--paper-3);border:1px solid var(--line);padding:.05em .35em}
pre{background:var(--code-bg);color:var(--code-fg);border:1px solid var(--code-bg);padding:12px 16px;overflow-x:auto;font-size:14px;line-height:1.6}
pre code{padding:0;background:none;border:0;color:inherit;font-size:inherit}
table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;font-size:14px}
th,td{border:1px solid var(--line);padding:8px 12px;text-align:left;vertical-align:top}
th{background:var(--paper-2);color:var(--ink);font-weight:600}
@media (max-width:900px){.layout{display:block}.side{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line)}
.toc{max-height:50vh}main{padding:32px 16px 64px}h1{font-size:36px;line-height:1.1}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
"""

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")


def font_faces():
    """Geist and Geist Mono (SIL OFL, assets/fonts/OFL.txt), embedded so the page makes no external requests.
    Latin subset only; other scripts fall back to system fonts. A missing file just means the fallback stack."""
    css = ""
    for family, name in (("Geist", "Geist-latin.woff2"), ("Geist Mono", "GeistMono-latin.woff2")):
        path = os.path.join(FONTS, name)
        if os.path.isfile(path):
            data = base64.b64encode(open(path, "rb").read()).decode()
            css += (f'@font-face{{font-family:"{family}";font-style:normal;font-weight:100 900;font-display:swap;'
                    f'src:url(data:font/woff2;base64,{data}) format("woff2")}}')
    return css

# Search looks through every section's text, including the intro above the first heading
# (accent- and case-insensitive): matching sections show a snippet, matches are highlighted in the
# article, and a result jumps to its first match. Cmd+K / Ctrl+K focuses it. Scroll-spy marks the section being read. The theme toggle overrides the OS setting.
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
const toc=document.querySelector('.toc'),main=document.querySelector('main'),intro=toc.querySelector('li.intro');
const links=[...toc.querySelectorAll('li:not(.intro) a')],heads=links.map(a=>document.getElementById(a.hash.slice(1)));
const fold=c=>c.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
// Folded text plus a map back to original offsets: matching ignores case and accents, results still point at the real text.
const folded=s=>{let t='';const m=[];for(let i=0;i<s.length;i++){const f=fold(s[i]);t+=f;for(let k=0;k<f.length;k++)m.push(i)}return{t,m}};
const block=h=>{const els=[h];let n=h.nextElementSibling;while(n&&!/^H[1-3]$/.test(n.tagName)){els.push(n);n=n.nextElementSibling}return els};
const secs=heads.map((h,i)=>({li:links[i].parentElement,a:links[i],els:block(h)}));
const h1=main.querySelector('h1');if(h1&&intro){const els=block(h1);if(els.length>1)secs.unshift({li:intro,a:intro.firstElementChild,els})}
secs.forEach(s=>{s.text=s.els.map(e=>e.innerText||e.textContent).join(' ').replace(/\\s+/g,' ').trim();s.f=folded(s.text)});
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function snippet(s,q){const i=s.f.t.indexOf(q),a=s.f.m[i],b=s.f.m[i+q.length-1]+1,from=Math.max(0,a-40),to=Math.min(s.text.length,b+60);
return(from?'\\u2026':'')+esc(s.text.slice(from,a))+'<mark>'+esc(s.text.slice(a,b))+'</mark>'+esc(s.text.slice(b,to))+(to<s.text.length?'\\u2026':'')}
// Every match in the article body, highlighted with the CSS Custom Highlight API (no DOM changes) where supported.
const canHl=window.CSS&&CSS.highlights&&typeof Highlight==='function';
function ranges(q){const out=[],w=document.createTreeWalker(main,NodeFilter.SHOW_TEXT);let n;
while((n=w.nextNode())){const f=folded(n.data);let i=f.t.indexOf(q);
while(i>-1){const r=new Range();r.setStart(n,f.m[i]);r.setEnd(n,f.m[i+q.length-1]+1);out.push(r);i=f.t.indexOf(q,i+q.length)}}return out}
const empty=toc.querySelector('.empty');let hits=[];
input.addEventListener('input',()=>{const q=fold(input.value.trim()).replace(/\\s+/g,' ');let shown=0;
toc.classList.toggle('searching',!!q);
secs.forEach(s=>{const ok=q?s.f.t.includes(q):s.li!==intro;s.li.hidden=!ok;shown+=ok;
s.a.querySelector('.snip')?.remove();
if(q&&ok){const p=document.createElement('small');p.className='snip';p.innerHTML=snippet(s,q);s.a.firstElementChild.append(p)}});
empty.hidden=shown>0;hits=q?ranges(q):[];
if(canHl){if(hits.length)CSS.highlights.set('tta-search',new Highlight(...hits));else CSS.highlights.delete('tta-search')}});
// While searching, a result jumps to its first match instead of the section heading.
toc.addEventListener('click',e=>{const a=e.target.closest('a'),s=a&&secs.find(s=>s.a===a);if(!s||!hits.length)return;
const r=hits.find(r=>s.els.some(el=>el.contains(r.startContainer)));if(!r)return;
e.preventDefault();history.replaceState(null,'',a.hash);r.startContainer.parentElement.scrollIntoView({block:'center'})});
input.addEventListener('keydown',e=>{if(e.key==='Enter'){const s=secs.find(s=>!s.li.hidden);if(s){s.a.click();input.blur()}}
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
    lines, out, toc, used, i = md.splitlines(), [], [], {"top"}, 0  # "top" is the H1's id
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
                out.append(f'<h1 id="top">{text}</h1>')
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
    # The intro (text above the first heading) has no contents entry; this one only shows as a search result.
    rows = [f'<li class="l2 intro" hidden><a href="#top"><span>{html.escape(title)}</span></a></li>']
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
            f"<title>{html.escape(title)}</title>{EARLY}<style>{font_faces()}{CSS}</style></head><body>"
            f'<div class="layout">{nav}<main>{body}</main></div><script>{JS}</script></body></html>')
    out = os.path.join(d, "index.html")
    open(out, "w", encoding="utf-8").write(page)
    if a.clean:
        clean(d, m["options"].get("use") == "external")
    print(f"{out}  ({len(toc)} entries in the table of contents)")


if __name__ == "__main__":
    main()
