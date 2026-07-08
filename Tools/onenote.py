#!/usr/bin/env python3
"""md2onenote - turn a folder of Markdown files into a single OneNote-style HTML page.

Expected layout::

    notes/
        Getting Started/       -> SECTION tab (horizontal, across the top)
            01_intro.md        -> PAGE tab (vertical, left sidebar)
            02_setup.md        -> PAGE tab
            Advanced/          -> nested files become indented sub-pages
                tips.md
        Reference/             -> another section
            cheatsheet.md
        loose_note.md          -> top-level files collect into a "Notes" section

Folder and file names become the titles. Fenced code blocks are syntax
highlighted with Pygments. Folders are horizontal tabs across the top and
files are a vertical tab list in the left sidebar; each section has its own
color and the top bar takes on the active section's color (use
--single-color to make it a single notebook color throughout).

Usage::

    python md2onenote.py ./notes -o notebook.html --title "My Notebook" --color "#7719AA"

Requires::

    pip install markdown pygments pymdown-extensions
"""
from __future__ import annotations

import argparse
import base64
import html as html_lib
import mimetypes
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DEFAULT_NOTEBOOK_COLOR = "#7719AA"          # OneNote's signature purple

# Fluent-inspired palette cycled across section tabs.
SECTION_PALETTE = [
    "#B4009E", "#0078D4", "#00B294", "#107C10", "#D29200",
    "#D83B01", "#E3008C", "#5C2D91", "#008272", "#B146C2",
    "#C239B3", "#486991", "#498205", "#8764B8",
]

MD_EXTS = {".md", ".markdown", ".mdown", ".mkd", ".mkdn", ".mdwn"}

# Strip a *short* ordering prefix used only for sorting (01_, 1., 2) ...) but
# leave real numbers such as a "2024_report" alone.
ORDER_PREFIX = re.compile(r"^\s*\d{1,3}\s*[._)\-]\s*")


# --------------------------------------------------------------------------- #
# Small colour helpers
# --------------------------------------------------------------------------- #

def normalize_hex(color: str | None) -> str | None:
    if not color:
        return None
    color = color.strip()
    if not color.startswith("#"):
        color = "#" + color
    if re.fullmatch(r"#[0-9a-fA-F]{3}", color):
        color = "#" + "".join(ch * 2 for ch in color[1:])
    if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        return color.lower()
    return None


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    h = color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(color: str, other: str, weight: float) -> str:
    """Blend two hex colours; ``weight`` is the amount of ``other`` (0..1)."""
    a, b = hex_to_rgb(color), hex_to_rgb(other)
    c = [round(a[i] * (1 - weight) + b[i] * weight) for i in range(3)]
    return "#{:02x}{:02x}{:02x}".format(*c)


def ink_for(color: str) -> str:
    """Return black or white for readable text on ``color``."""
    r, g, b = hex_to_rgb(color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#ffffff" if luminance < 0.62 else "#201f1e"


# --------------------------------------------------------------------------- #
# Titles + ordering
# --------------------------------------------------------------------------- #

def natural_key(name: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def prettify(name: str, raw: bool) -> str:
    if raw:
        return name.strip() or "Untitled"
    name = ORDER_PREFIX.sub("", name)
    name = name.replace("_", " ").replace("-", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name or "Untitled"


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #

@dataclass
class Page:
    title: str
    level: int
    path: Path
    sec_index: int
    page_index: int
    html: str = ""

    @property
    def id(self) -> str:
        return f"s{self.sec_index}-p{self.page_index}"


@dataclass
class Section:
    title: str
    index: int
    color: str
    pages: list[Page] = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"s{self.index}"


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #

def _collect_pages(folder: Path, sec_index: int, raw_titles: bool) -> list[Page]:
    pages: list[Page] = []
    counter = 0

    def walk(directory: Path, level: int) -> None:
        nonlocal counter
        try:
            entries = sorted(directory.iterdir(), key=lambda p: natural_key(p.name))
        except OSError:
            return
        files = [e for e in entries if e.is_file() and e.suffix.lower() in MD_EXTS]
        subdirs = [e for e in entries if e.is_dir()]
        for f in files:
            pages.append(Page(prettify(f.stem, raw_titles), level, f, sec_index, counter))
            counter += 1
        for sub in subdirs:                       # nested files -> sub-pages
            walk(sub, level + 1)

    walk(folder, 0)
    return pages


def discover(root: Path, raw_titles: bool) -> list[Section]:
    entries = sorted(root.iterdir(), key=lambda p: natural_key(p.name))
    folders = [e for e in entries if e.is_dir()]
    loose = [e for e in entries if e.is_file() and e.suffix.lower() in MD_EXTS]

    sections: list[Section] = []
    idx = 0
    for folder in folders:
        pages = _collect_pages(folder, idx, raw_titles)
        if not pages:
            continue
        sections.append(Section(prettify(folder.name, raw_titles), idx, SECTION_PALETTE[0], pages))
        idx += 1

    if loose:
        pages = [Page(prettify(f.stem, raw_titles), 0, f, idx, i) for i, f in enumerate(loose)]
        sections.append(Section("Notes", idx, SECTION_PALETTE[0], pages))

    return sections


# --------------------------------------------------------------------------- #
# Markdown -> HTML
# --------------------------------------------------------------------------- #

def make_markdown() -> markdown.Markdown:
    return markdown.Markdown(
        extensions=[
            "pymdownx.superfences",   # robust fenced code blocks
            "pymdownx.highlight",     # Pygments highlighting
            "pymdownx.inlinehilite",  # `#!python highlighted` inline code
            "pymdownx.betterem",
            "pymdownx.tilde",
            "pymdownx.caret",
            "pymdownx.mark",          # ==highlight== -> <mark>

            "pymdownx.smartsymbols",
            "pymdownx.magiclink",
            "pymdownx.tasklist",
            "tables",
            "toc",
            "admonition",
            "attr_list",
            "def_list",
            "footnotes",
            "md_in_html",
            "sane_lists",
        ],
        extension_configs={
            "pymdownx.highlight": {
                "use_pygments": True,
                "pygments_lang_class": True,   # adds a language-xxx class
                "css_class": "highlight",
                "guess_lang": False,
                "linenums": False,
            },
            "pymdownx.tasklist": {"custom_checkbox": False},
            "pymdownx.magiclink": {"repo_url_shortener": False, "social_url_shortener": False},
            "toc": {"permalink": "#", "permalink_class": "headerlink",
                    "permalink_title": "Link to this section", "toc_depth": "2-4"},
        },
        output_format="html5",
    )


# Regexes for post-processing the generated HTML.
_ID_RE = re.compile(r'\bid="([^"]+)"')
_HASH_HREF_RE = re.compile(r'\bhref="#([^"]+)"')
_IMG_RE = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', re.I)
_A_TAG_RE = re.compile(r"<a\b([^>]*?)>", re.I)
_HREF_RE = re.compile(r'\bhref="([^"]*)"', re.I)
_EXTERNAL = re.compile(r"^(?:https?:|ftp:|mailto:|tel:|data:|#|//)", re.I)


def namespace_ids(html: str, page_id: str) -> str:
    """Prefix every id and in-page anchor so pages can't collide with each other."""
    html = _ID_RE.sub(lambda m: f'id="{page_id}__{m.group(1)}"', html)
    html = _HASH_HREF_RE.sub(lambda m: f'href="#{page_id}__{m.group(1)}"', html)
    return html


def embed_images(html: str, base_dir: Path) -> str:
    """Inline local images as data URIs so the output is a single portable file."""
    def repl(m: re.Match) -> str:
        pre, src, post = m.groups()
        if _EXTERNAL.match(src):
            return m.group(0)
        target = (base_dir / src).resolve()
        try:
            data = target.read_bytes()
        except OSError:
            return m.group(0)
        mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        b64 = base64.b64encode(data).decode("ascii")
        return f"{pre}data:{mime};base64,{b64}{post}"

    return _IMG_RE.sub(repl, html)


def rewrite_links(html: str, base_dir: Path, path_map: dict[Path, Page]) -> str:
    """Turn links to other .md files into in-page navigation."""
    def repl(m: re.Match) -> str:
        attrs = m.group(1)
        href_m = _HREF_RE.search(attrs)
        if not href_m:
            return m.group(0)
        href = html_lib.unescape(href_m.group(1))
        if _EXTERNAL.match(href):
            return m.group(0)
        target_str, _, frag = href.partition("#")
        if not target_str:
            return m.group(0)
        target = (base_dir / target_str).resolve()
        page = path_map.get(target)
        if page is None:
            return m.group(0)
        extra = f' class="xref" data-goto-page="{page.id}"'
        if frag:
            extra += f' data-goto-frag="{html_lib.escape(frag, quote=True)}"'
        new_attrs = _HREF_RE.sub('href="#"', attrs, count=1) + extra
        return f"<a{new_attrs}>"

    return _A_TAG_RE.sub(repl, html)


def convert_all(sections: list[Section], md: markdown.Markdown,
                path_map: dict[Path, Page]) -> None:
    for sec in sections:
        for page in sec.pages:
            try:
                text = page.path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                page.html = f'<p class="load-error">Could not read this file: {html_lib.escape(str(exc))}</p>'
                continue
            text = text.lstrip("\ufeff")
            md.reset()
            body = md.convert(text)
            body = namespace_ids(body, page.id)
            body = embed_images(body, page.path.parent)
            body = rewrite_links(body, page.path.parent, path_map)
            page.html = body


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

ICON = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H19a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H6.5A2.5 2.5 0 0 1 4 17.5z"/>'
    '<path d="M8 3v18"/></svg>'
)

CSS_STATIC = r'''
*{box-sizing:border-box}
html,body{height:100%}
html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{margin:0;font-family:var(--font);color:var(--ink);background:var(--bg);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
  -webkit-tap-highlight-color:transparent;
  display:flex;flex-direction:column;height:100vh;overflow:hidden}
#app{display:flex;flex-direction:column;height:100%;min-height:0}

/* ---- top bar (25% active tab colour, 75% white) ---- */
.topbar{background:var(--topbar);color:var(--topbar-ink);display:flex;
  align-items:center;gap:12px;padding:0 16px;height:52px;flex:0 0 auto;
  box-shadow:0 1px 0 rgba(0,0,0,.10);z-index:5;
  transition:background .18s,color .18s}
.brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:15px;
  letter-spacing:.2px;min-width:0}
.brand svg{flex:0 0 auto;opacity:.95}
.brand .name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.spacer{flex:1 1 auto}
.search{appearance:none;border:1px solid #000000;border-radius:6px;color:var(--topbar-ink);
  background:rgba(255,255,255,.18);padding:7px 12px;font:inherit;font-size:13px;
  width:210px;max-width:42vw;transition:background .15s}
.search::placeholder{color:var(--topbar-ink);opacity:.72}
.search:focus{outline:2px solid rgba(255,255,255,.65);outline-offset:1px;
  background:rgba(255,255,255,.28)}

/* ---- section tabs (folders) - horizontal strip below the top bar ---- */
.sections{display:flex;gap:3px;align-items:flex-end;background:var(--bg);
  padding:6px 12px 0;flex:0 0 auto;overflow-x:auto;scrollbar-width:thin;
  border-bottom:1px solid var(--border)}
.section-tab{appearance:none;cursor:pointer;font:inherit;font-size:13.5px;
  color:var(--ink);background:var(--tab-tint);border:1px solid var(--border);
  border-bottom:none;border-top:3px solid var(--tab);border-radius:9px 9px 0 0;
  padding:9px 16px 8px;margin-top:6px;white-space:nowrap;max-width:240px;
  overflow:hidden;text-overflow:ellipsis;position:relative;top:1px;
  transition:background .12s,margin .12s,padding .12s}
.section-tab:hover{background:var(--tab-hover)}
.section-tab.active{background:var(--surface);font-weight:600;margin-top:2px;
  padding-bottom:11px;box-shadow:0 -1px 4px rgba(0,0,0,.06)}
.section-tab:focus-visible{outline:2px solid var(--tab);outline-offset:2px}

/* ---- body: left sidebar (file tabs) + content ---- */
.body{flex:1 1 auto;display:flex;min-height:0}
.sidebar{flex:0 0 260px;display:flex;flex-direction:column;min-height:0;
  background:var(--rail);border-right:1px solid var(--border)}

/* ---- content pane (right) ---- */
.content{flex:1 1 auto;min-width:0;overflow:auto;scroll-behavior:smooth;
  background:var(--surface)}
.content-inner{max-width:820px;margin:0 auto;padding:40px 56px 96px}

/* ---- page rail (files) - vertical list in the left sidebar ---- */
.rail{flex:1 1 auto;min-height:0;background:transparent;overflow:auto;
  padding:14px 10px}
.rail-title{font-size:11px;text-transform:uppercase;letter-spacing:.9px;
  color:var(--ink-soft);padding:4px 12px 10px;font-weight:700}
.rail-section{display:none}
.rail-section.active{display:block}
.page-list{list-style:none;margin:0;padding:0}
.page-list li{margin:1px 0}
.page-tab{appearance:none;cursor:pointer;font:inherit;font-size:14px;text-align:left;
  width:100%;color:var(--ink);background:transparent;border:none;border-radius:7px;
  padding:8px 12px;line-height:1.35;border-left:3px solid transparent;
  transition:background .12s}
.page-tab[data-level="1"]{padding-left:30px;font-size:13px;color:var(--ink-soft)}
.page-tab[data-level="2"]{padding-left:46px;font-size:13px;color:var(--ink-soft)}
.page-tab[data-level="3"]{padding-left:62px;font-size:13px;color:var(--ink-soft)}
.page-tab:hover{background:rgba(0,0,0,.05)}
.page-tab.active{background:var(--accent-soft);border-left-color:var(--accent);
  color:var(--ink);font-weight:600}
.page-tab:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.rail-empty{color:var(--ink-soft);font-size:13px;padding:12px}

/* ---- full-text search results ---- */
.rail-sec-title{display:none;font-size:11px;text-transform:uppercase;
  letter-spacing:.7px;color:var(--ink-soft);font-weight:700;padding:12px 12px 3px}
.rail-section:first-child .rail-sec-title{padding-top:2px}
.page-snip{font-size:11.5px;color:var(--ink-soft);line-height:1.4;
  padding:0 12px 7px;margin-top:-2px;display:-webkit-box;-webkit-line-clamp:2;
  -webkit-box-orient:vertical;overflow:hidden}
.rail-none{color:var(--ink-soft);font-size:13px;padding:14px 12px;line-height:1.5}
/* while searching, reveal every section that has a hit + its label */
#app.searching .rail-title{display:none}
#app.searching .rail-section{display:none}
#app.searching .rail-section.search-hit{display:block}
#app.searching .rail-sec-title{display:block}

/* ---- page content ---- */
.page{animation:fade .18s ease}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.page-body{font-size:16px;line-height:1.7;color:var(--ink);overflow-wrap:break-word}
.page-body>*:first-child{margin-top:0}
.page-body h1,.page-body h2,.page-body h3,.page-body h4,.page-body h5,.page-body h6{
  line-height:1.25;font-weight:600;margin:1.6em 0 .5em;scroll-margin-top:16px}
.page-body h1{font-size:2em;border-bottom:1px solid var(--border);padding-bottom:.28em}
.page-body h2{font-size:1.5em}
.page-body h3{font-size:1.22em}
.page-body h4{font-size:1.05em}
.page-body p{margin:.7em 0}
.page-body a{color:var(--link);text-decoration:none;
  border-bottom:1px solid var(--link-underline)}
.page-body a:hover{border-bottom-color:var(--link)}
.page-body a.xref{color:var(--accent);border-bottom-color:transparent}
.page-body a.xref:hover{border-bottom-color:var(--accent)}
.page-body a.xref::before{content:"\203a\00a0";font-weight:700;opacity:.55}
.page-body .headerlink{opacity:0;margin-left:.35em;font-size:.78em;border:none;
  color:var(--ink-soft);text-decoration:none}
.page-body h1:hover .headerlink,.page-body h2:hover .headerlink,
.page-body h3:hover .headerlink,.page-body h4:hover .headerlink{opacity:.6}
.page-body .headerlink:hover{opacity:1}
.page-body ul,.page-body ol{margin:.6em 0;padding-left:1.5em}
.page-body li{margin:.25em 0}
.page-body ul.task-list{list-style:none;padding-left:.4em}
.page-body li.task-list-item{margin:.3em 0}
.page-body li.task-list-item input{margin:0 .55em 0 0;transform:translateY(1px)}
.page-body blockquote{margin:1em 0;padding:.5em 1.1em;border-left:4px solid var(--accent);
  background:var(--accent-soft);border-radius:0 8px 8px 0}
.page-body blockquote p{margin:.35em 0}
.page-body hr{border:none;border-top:1px solid var(--border);margin:2em 0}
.page-body img{max-width:100%;height:auto;border-radius:10px;
  box-shadow:0 2px 12px rgba(0,0,0,.10);margin:.6em 0}
.page-body dl{margin:1em 0}
.page-body dt{font-weight:600;margin-top:.6em}
.page-body dd{margin:0 0 .4em 1.2em;color:var(--ink-soft)}
.page-body table{border-collapse:collapse;margin:1.1em 0;font-size:14.5px;
  display:block;overflow-x:auto;max-width:100%}
.page-body th,.page-body td{border:1px solid var(--border);padding:8px 12px;text-align:left}
.page-body thead th{background:var(--rail);font-weight:600}
.page-body tbody tr:nth-child(even){background:#00000005}
.page-body :not(pre)>code{font-family:var(--mono);font-size:.88em;
  background:var(--inline-code-bg);border:1px solid var(--border);
  padding:.12em .4em;border-radius:5px}
.page-body sup,.page-body sub{line-height:0}
.load-error{color:#c50f1f}

/* ---- admonitions ---- */
.page-body .admonition{margin:1.2em 0;border:1px solid var(--border);
  border-left:4px solid var(--ad,#6b7280);border-radius:8px;
  padding:.15em 1.1em .55em;background:var(--ad-bg,#f7f7f8)}
.page-body .admonition-title{font-weight:700;margin:.6em 0 .25em;font-size:.82em;
  text-transform:uppercase;letter-spacing:.5px;color:var(--ad,#6b7280)}
.page-body .admonition.note{--ad:#0f6cbd;--ad-bg:#eef6fc}
.page-body .admonition.tip,.page-body .admonition.hint,
.page-body .admonition.success{--ad:#107c10;--ad-bg:#eff6ef}
.page-body .admonition.warning,.page-body .admonition.caution,
.page-body .admonition.attention{--ad:#c98a00;--ad-bg:#fdf6e3}
.page-body .admonition.danger,.page-body .admonition.error,
.page-body .admonition.failure{--ad:#c50f1f;--ad-bg:#fdf1f1}
.page-body .admonition.info{--ad:var(--accent);--ad-bg:var(--accent-soft)}

/* ---- code blocks ---- */
.page-body .highlight{position:relative;margin:1.3em 0;border:1px solid var(--border);
  border-left:4px solid var(--accent);border-radius:10px;overflow:hidden}
.page-body .highlight pre{margin:0;padding:14px 16px;overflow-x:auto;
  font-family:var(--mono);font-size:13.5px;line-height:1.55;-moz-tab-size:4;tab-size:4}
.page-body .highlight code{font-family:inherit;background:none;border:none;padding:0}
.code-head{display:flex;align-items:center;justify-content:space-between;
  padding:6px 10px 6px 14px;border-bottom:1px solid var(--border);
  background:rgba(0,0,0,.035);font-size:11px}
.code-lang{text-transform:uppercase;letter-spacing:.9px;font-weight:700;
  color:var(--ink-soft);font-family:var(--font)}
.code-copy{appearance:none;cursor:pointer;border:1px solid var(--border);
  background:var(--surface);color:var(--ink-soft);font:inherit;font-size:11px;
  padding:3px 10px;border-radius:6px;font-family:var(--font);transition:.12s}
.code-copy:hover{color:var(--ink);border-color:var(--accent)}
.code-copy.done{color:#107c10;border-color:#107c10}

/* ---- empty state ---- */
.empty{max-width:520px;margin:16vh auto;text-align:center;color:var(--ink-soft)}
.empty h2{color:var(--ink);margin-bottom:.4em}

/* ---- scrollbars ---- */
.content::-webkit-scrollbar,.rail::-webkit-scrollbar,
.highlight pre::-webkit-scrollbar{height:10px;width:10px}
.content::-webkit-scrollbar-thumb,.rail::-webkit-scrollbar-thumb,
.highlight pre::-webkit-scrollbar-thumb{background:#c8c6c4;border-radius:6px}

/* ---- responsive (phones / iPhone) ---- */
@media (max-width:820px){
  body{height:auto;min-height:100vh;min-height:100dvh;overflow:auto}
  #app{height:auto}

  /* top bar extends under the notch; content stays below it */
  .topbar{position:sticky;top:0;height:calc(52px + env(safe-area-inset-top));
    padding-top:env(safe-area-inset-top);
    padding-left:calc(16px + env(safe-area-inset-left));
    padding-right:calc(16px + env(safe-area-inset-right))}
  .spacer{display:none}
  .search{flex:1 1 auto;min-width:0;width:auto;max-width:none;font-size:16px;
    padding:8px 12px}                       /* 16px stops iOS zoom-on-focus */

  /* folder tabs pinned just under the top bar */
  .sections{position:sticky;top:calc(52px + env(safe-area-inset-top));z-index:4;
    padding-left:calc(12px + env(safe-area-inset-left));
    padding-right:calc(12px + env(safe-area-inset-right))}
  .section-tab{max-width:70vw;padding:10px 16px}

  .body{flex-direction:column}
  .sidebar{flex:0 0 auto;border-right:none;border-bottom:1px solid var(--border)}

  /* file tabs: horizontal chip row for quick switching */
  .rail{flex:0 0 auto;overflow-x:auto;
    padding:8px calc(10px + env(safe-area-inset-right)) 8px
            calc(10px + env(safe-area-inset-left))}
  .rail-title{display:none}
  .rail-section.active{display:flex;gap:6px}
  .page-list{display:flex;gap:6px}
  .page-list li{margin:0}
  .page-tab{white-space:nowrap;width:auto;border-left:none;
    border-bottom:3px solid transparent;border-radius:8px 8px 0 0;padding:10px 14px}
  .page-tab[data-level]{padding-left:14px}
  .page-tab.active{border-left-color:transparent;border-bottom-color:var(--accent)}

  /* search results read better as a vertical list on a phone */
  #app.searching .rail{overflow-x:visible}
  #app.searching .rail-section.search-hit{display:block}
  #app.searching .page-list{display:block}
  #app.searching .page-list li{margin:2px 0}
  #app.searching .page-tab{width:100%;white-space:normal;border-radius:7px;
    border-bottom:none;border-left:3px solid transparent;padding:9px 12px}
  #app.searching .page-tab.active{border-bottom:none;border-left-color:var(--accent)}

  .content{overflow:visible}
  .content-inner{padding:22px calc(18px + env(safe-area-inset-right))
                 calc(64px + env(safe-area-inset-bottom))
                 calc(18px + env(safe-area-inset-left))}

  /* anchored headings clear the sticky top bar + folder tabs */
  .page-body h1,.page-body h2,.page-body h3,.page-body h4,.page-body h5,
  .page-body h6{scroll-margin-top:calc(104px + env(safe-area-inset-top))}
  .page-body h1{font-size:1.7em}
  .page-body h2{font-size:1.35em}
  .code-copy{padding:6px 12px}              /* larger tap target */
}
@media (prefers-reduced-motion:reduce){
  *{animation:none !important;transition:none !important;scroll-behavior:auto !important}
}
'''

JS_STATIC = r"""
(function () {
  var app = document.getElementById('app');
  var sectionTabs = Array.prototype.slice.call(document.querySelectorAll('.section-tab'));
  var railSections = Array.prototype.slice.call(document.querySelectorAll('.rail-section'));
  var pages = Array.prototype.slice.call(document.querySelectorAll('.page'));
  var pageTabs = Array.prototype.slice.call(document.querySelectorAll('.page-tab'));
  var search = document.getElementById('search');
  var noResults = document.querySelector('.rail-none');
  var lastPage = {};   // sectionId -> last viewed pageId

  // Full-text search index: pageId -> searchable/lowercased text + a raw body
  // copy used to build result snippets. Built before code labels are injected
  // so "Copy"/language chrome is not indexed.
  var pageText = {};   // title + body, lowercased (used for matching)
  var bodyLower = {};  // body only, lowercased (used to locate a snippet)
  var bodyRaw = {};    // body only, original case (used to render a snippet)
  pages.forEach(function (p) {
    var pid = p.dataset.page;
    var bodyEl = p.querySelector('.page-body');
    var raw = (bodyEl ? bodyEl.textContent : '').replace(/\s+/g, ' ').trim();
    var title = (p.getAttribute('aria-label') || '');
    bodyRaw[pid] = raw;
    bodyLower[pid] = raw.toLowerCase();
    pageText[pid] = (title + ' ' + raw).toLowerCase();
  });

  function hexToRgb(h) {
    h = h.replace('#', '').trim();
    if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join('');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function contrast(hex) {
    var c = hexToRgb(hex);
    var l = (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255;
    return l < 0.62 ? '#ffffff' : '#201f1e';
  }
  function mix(hex, other, t) {
    var a = hexToRgb(hex), b = hexToRgb(other);
    return '#' + [0, 1, 2].map(function (i) {
      return Math.round(a[i] * (1 - t) + b[i] * t).toString(16).padStart(2, '0');
    }).join('');
  }

  function setAccent(color) {
    if (!color) return;
    app.style.setProperty('--accent', color);
    app.style.setProperty('--accent-ink', contrast(color));
    app.style.setProperty('--accent-soft', mix(color, '#ffffff', 0.88));
    var bar = mix(color, '#ffffff', 0.75);      // top bar = 25% tab colour, 75% white
    app.style.setProperty('--topbar', bar);
    app.style.setProperty('--topbar-ink', contrast(bar));
  }

  function firstPageOf(sectionId) {
    var rail = railSections.filter(function (r) { return r.dataset.section === sectionId; })[0];
    var first = rail && rail.querySelector('.page-tab');
    return first ? first.dataset.page : null;
  }

  function showPage(pageId) {
    if (!pageId) return;
    pages.forEach(function (p) { p.hidden = (p.dataset.page !== pageId); });
    pageTabs.forEach(function (t) {
      var on = t.dataset.page === pageId;
      t.classList.toggle('active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    lastPage[pageId.split('-')[0]] = pageId;
    var content = document.querySelector('.content');
    if (content) content.scrollTop = 0;
  }

  function makeSnippet(li, pid, query) {
    var old = li.querySelector('.page-snip');
    if (old) old.parentNode.removeChild(old);
    var body = bodyLower[pid] || '';
    var idx = body.indexOf(query);
    if (idx === -1) return;            // matched in the title only
    var raw = bodyRaw[pid] || '';
    var start = Math.max(0, idx - 30);
    var end = Math.min(raw.length, idx + query.length + 50);
    var text = (start > 0 ? '\u2026' : '') + raw.slice(start, end).trim()
             + (end < raw.length ? '\u2026' : '');
    var div = document.createElement('div');
    div.className = 'page-snip';
    div.textContent = text;
    li.appendChild(div);
  }

  function filterPages(query) {
    query = (query || '').trim().toLowerCase();
    var searching = query.length > 0;
    app.classList.toggle('searching', searching);
    var hits = 0;
    railSections.forEach(function (rail) {
      var sectionHit = false;
      rail.querySelectorAll('li').forEach(function (li) {
        var tab = li.querySelector('.page-tab');
        var pid = tab ? tab.dataset.page : '';
        var match = !searching || (pageText[pid] && pageText[pid].indexOf(query) !== -1);
        li.hidden = !match;
        if (searching && match) { sectionHit = true; hits++; makeSnippet(li, pid, query); }
        else { var s = li.querySelector('.page-snip'); if (s) s.parentNode.removeChild(s); }
      });
      rail.classList.toggle('search-hit', searching && sectionHit);
      var empty = rail.querySelector('.rail-empty');
      if (empty) empty.hidden = true;
    });
    if (noResults) noResults.hidden = !(searching && hits === 0);
  }

  // Navigate to a specific page in any section (used by page tabs, search
  // results and cross-page links). Switches section if needed and clears search.
  function goToPage(pageId) {
    if (!pageId) return;
    var sid = pageId.split('-')[0];
    var active = railSections.filter(function (r) { return r.classList.contains('active'); })[0];
    if (!active || active.dataset.section !== sid) {
      sectionTabs.forEach(function (t) {
        var on = t.dataset.section === sid;
        t.classList.toggle('active', on);
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        if (on) setAccent(getComputedStyle(t).getPropertyValue('--tab'));
      });
      railSections.forEach(function (r) { r.classList.toggle('active', r.dataset.section === sid); });
    }
    if (search) search.value = '';
    filterPages('');
    showPage(pageId);
  }

  function showSection(sectionId) {
    sectionTabs.forEach(function (t) {
      var on = t.dataset.section === sectionId;
      t.classList.toggle('active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      if (on) setAccent(getComputedStyle(t).getPropertyValue('--tab'));
    });
    railSections.forEach(function (r) { r.classList.toggle('active', r.dataset.section === sectionId); });
    if (search) search.value = '';
    filterPages('');
    showPage(lastPage[sectionId] || firstPageOf(sectionId));
  }

  sectionTabs.forEach(function (t) {
    t.addEventListener('click', function () { showSection(t.dataset.section); });
  });
  pageTabs.forEach(function (t) {
    t.addEventListener('click', function () { goToPage(t.dataset.page); });
  });
  if (search) search.addEventListener('input', function (e) { filterPages(e.target.value); });

  // Cross-page links (rewritten .md links).
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a.xref') : null;
    if (!a) return;
    e.preventDefault();
    var pageId = a.dataset.gotoPage;
    if (!pageId) return;
    goToPage(pageId);
    var frag = a.dataset.gotoFrag;
    if (frag) {
      var el = document.getElementById(pageId + '__' + frag);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });

  // Copy buttons + language labels on code blocks.
  function copyText(text, btn) {
    var done = function () {
      btn.textContent = 'Copied'; btn.classList.add('done');
      setTimeout(function () { btn.textContent = 'Copy'; btn.classList.remove('done'); }, 1200);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
    } else { fallback(text, done); }
  }
  function fallback(text, done) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.focus(); ta.select();
    try { document.execCommand('copy'); } catch (err) {}
    document.body.removeChild(ta); done();
  }
  document.querySelectorAll('.page-body .highlight').forEach(function (block) {
    var m = block.className.match(/language-([\w+#.-]+)/);
    var lang = m ? m[1] : 'text';
    var head = document.createElement('div');
    head.className = 'code-head';
    var label = document.createElement('span');
    label.className = 'code-lang'; label.textContent = lang;
    var btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'code-copy'; btn.textContent = 'Copy';
    head.appendChild(label); head.appendChild(btn);
    block.insertBefore(head, block.firstChild);
    btn.addEventListener('click', function () {
      var code = block.querySelector('pre code') || block.querySelector('pre');
      copyText(code ? code.innerText : '', btn);
    });
  });

  if (sectionTabs.length) showSection(sectionTabs[0].dataset.section);
})();
"""


def render(title: str, notebook_color: str, sections: list[Section], code_style: str) -> str:
    esc = lambda s: html_lib.escape(s, quote=True)

    accent = sections[0].color if sections else notebook_color
    root_vars = (
        ":root{"
        "--notebook:" + notebook_color + ";"
        "--notebook-ink:" + ink_for(notebook_color) + ";"
        "--bg:#f3f2f1;--surface:#ffffff;--rail:#faf9f8;--border:#e6e4e2;"
        "--ink:#242424;--ink-soft:#605e5c;--link:#0f6cbd;"
        "--link-underline:" + mix("#0f6cbd", "#ffffff", 0.6) + ";"
        "--inline-code-bg:#f3f2f1;"
        "--accent:" + accent + ";"
        "--accent-ink:" + ink_for(accent) + ";"
        "--accent-soft:" + mix(accent, "#ffffff", 0.88) + ";"
        "--topbar:" + mix(accent, "#ffffff", 0.75) + ";"
        "--topbar-ink:" + ink_for(mix(accent, "#ffffff", 0.75)) + ";"
        '--font:"Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;'
        '--mono:"Cascadia Code","Cascadia Mono",ui-monospace,"SF Mono",Consolas,'
        '"Liberation Mono",Menlo,monospace;'
        "}"
    )
    pygments_css = HtmlFormatter(style=code_style).get_style_defs(".highlight")
    style = "<style>\n" + root_vars + "\n" + pygments_css + "\n" + CSS_STATIC + "</style>"

    if not sections:
        sections_bar = ""
        rail_html = ""
        content = (
            '<main class="content"><div class="content-inner">'
            '<div class="empty"><h2>Nothing to show yet</h2>'
            '<p>No Markdown files were found. Add folders containing '
            "<code>.md</code> files and run the converter again.</p></div>"
            "</div></main>"
        )
    else:
        tabs = []
        for sec in sections:
            tab_style = (
                f"--tab:{sec.color};--tab-ink:{ink_for(sec.color)};"
                f'--tab-tint:{mix(sec.color, "#ffffff", 0.86)};'
                f'--tab-hover:{mix(sec.color, "#ffffff", 0.76)}'
            )
            tabs.append(
                f'<button class="section-tab" role="tab" data-section="{sec.id}" '
                f'aria-selected="false" style="{tab_style}">{esc(sec.title)}</button>'
            )
        sections_bar = ('<nav class="sections" role="tablist" aria-label="Sections">'
                        + "".join(tabs) + "</nav>")

        rails, page_blocks = [], []
        for sec in sections:
            items = []
            for page in sec.pages:
                items.append(
                    f'<li><button class="page-tab" role="tab" data-page="{page.id}" '
                    f'data-level="{page.level}" aria-selected="false">'
                    f"{esc(page.title)}</button></li>"
                )
                page_blocks.append(
                    '<article class="page" role="tabpanel" data-page="' + page.id
                    + '" aria-label="' + esc(page.title) + '" hidden><div class="page-body">'
                    + page.html + "</div></article>"
                )
            rails.append(
                f'<div class="rail-section" data-section="{sec.id}">'
                f'<div class="rail-sec-title">{esc(sec.title)}</div>'
                f'<ul class="page-list" role="tablist" aria-label="{esc(sec.title)} pages">'
                + "".join(items) + "</ul>"
                '<div class="rail-empty" hidden>No matching pages</div></div>'
            )

        rail_html = ('<div class="rail" aria-label="Pages">'
                     '<div class="rail-title">Pages</div>'
                     + "".join(rails)
                     + '<div class="rail-none" hidden>No pages match your search.</div>'
                     "</div>")
        content = (
            '<main class="content"><div class="content-inner">'
            + "".join(page_blocks) + "</div></main>"
        )

    search_box = (
        '<input id="search" class="search" type="search" '
        'placeholder="Search titles and text" '
        'aria-label="Search page titles and text">' if sections else ""
    )

    sidebar = ('<aside class="sidebar">' + rail_html + "</aside>"
               if sections else "")
    body = '<div class="body">' + sidebar + content + "</div>"

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, '
        'viewport-fit=cover">\n'
        "<title>" + esc(title) + "</title>\n" + style + "\n</head>\n<body>\n"
        '<div id="app">\n'
        '<header class="topbar"><div class="brand">' + ICON
        + '<span class="name">' + esc(title) + "</span></div>"
        '<div class="spacer"></div>' + search_box + "</header>\n"
        + sections_bar + "\n" + body + "\n</div>\n"
        "<script>\n" + JS_STATIC + "\n</script>\n</body>\n</html>\n"
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a folder of Markdown files into a OneNote-style HTML page.")
    parser.add_argument("input", help="Folder containing section subfolders of .md files")
    parser.add_argument("-o", "--output", help="Output .html file (default: <folder-name>.html)")
    parser.add_argument("-t", "--title", help="Notebook title (default: input folder name)")
    parser.add_argument("-c", "--color", default=DEFAULT_NOTEBOOK_COLOR,
                        help="Notebook / top-bar color, hex (default: %(default)s)")
    parser.add_argument("--palette",
                        help="Comma-separated hex colors to use for section tabs")
    parser.add_argument("--single-color", action="store_true",
                        help="Make every section tab the notebook color")
    parser.add_argument("--code-style", default="friendly",
                        help="Pygments style for code, e.g. friendly, monokai, "
                             "github-dark (default: %(default)s)")
    parser.add_argument("--raw-titles", action="store_true",
                        help="Use exact file/folder names as titles (skip prettifying)")
    args = parser.parse_args(argv)

    root = Path(args.input).expanduser()
    if not root.is_dir():
        parser.error(f"input folder not found: {root}")

    notebook_color = normalize_hex(args.color) or DEFAULT_NOTEBOOK_COLOR
    if normalize_hex(args.color) is None:
        print(f"warning: invalid color '{args.color}', using {DEFAULT_NOTEBOOK_COLOR}",
              file=sys.stderr)

    if args.palette:
        palette = [c for c in (normalize_hex(x) for x in args.palette.split(",")) if c]
        palette = palette or list(SECTION_PALETTE)
    else:
        palette = list(SECTION_PALETTE)

    title = args.title or prettify(root.name, args.raw_titles) or "Notebook"

    sections = discover(root, args.raw_titles)
    for sec in sections:
        sec.color = notebook_color if args.single_color else palette[sec.index % len(palette)]

    try:
        HtmlFormatter(style=args.code_style)
        code_style = args.code_style
    except Exception:
        print(f"warning: unknown code style '{args.code_style}', using 'friendly'",
              file=sys.stderr)
        code_style = "friendly"

    md = make_markdown()
    path_map = {p.path.resolve(): p for s in sections for p in s.pages}
    convert_all(sections, md, path_map)

    html_doc = render(title, notebook_color, sections, code_style)

    if args.output:
        out = Path(args.output).expanduser()
    else:
        out = Path(f"{root.resolve().name or 'notebook'}.html")
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_doc, encoding="utf-8")

    n_pages = sum(len(s.pages) for s in sections)
    print(f"\u2713 {out}  ({len(sections)} sections, {n_pages} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
