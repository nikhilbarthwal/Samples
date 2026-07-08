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
from jinja2 import Environment, FileSystemLoader
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
# Rendering (HTML/CSS/JS live in the Jinja template alongside this file)
# --------------------------------------------------------------------------- #

_TEMPLATE_DIR = Path(__file__).resolve().parent
_TEMPLATE_NAME = "notebook_template.html.j2"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=True,          # titles etc. are escaped; raw HTML is passed with |safe
    trim_blocks=True,
    lstrip_blocks=True,
)


def _tab_style(color: str) -> str:
    """Inline CSS custom properties that colour a single section tab."""
    return (
        f"--tab:{color};--tab-ink:{ink_for(color)};"
        f'--tab-tint:{mix(color, "#ffffff", 0.86)};'
        f'--tab-hover:{mix(color, "#ffffff", 0.76)}'
    )


def _root_vars(notebook_color: str, accent: str) -> str:
    """The :root{...} block of CSS custom properties (colours + fonts)."""
    return (
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


def render(title: str, notebook_color: str, sections: list[Section], code_style: str) -> str:
    """Render the self-contained HTML page from the external Jinja template."""
    accent = sections[0].color if sections else notebook_color
    ctx_sections = [
        {
            "id": sec.id,
            "title": sec.title,
            "tab_style": _tab_style(sec.color),
            "pages": [
                {"id": p.id, "title": p.title, "level": p.level, "html": p.html}
                for p in sec.pages
            ],
        }
        for sec in sections
    ]
    template = _jinja_env.get_template(_TEMPLATE_NAME)
    return template.render(
        title=title,
        root_vars=_root_vars(notebook_color, accent),
        pygments_css=HtmlFormatter(style=code_style).get_style_defs(".highlight"),
        sections=ctx_sections,
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
