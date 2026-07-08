#!/usr/bin/env python3
"""
md_to_onenote.py - Convert a folder of Markdown files into a single,
self-contained, OneNote-style HTML notebook.

STRUCTURE CONVENTION
---------------------
    <input_dir>/
        Folder A/              -> becomes a vertical tab ("section")
            01 Welcome.md        -> becomes a horizontal tab ("page")
            02 Setup.md
        Folder B/
            ...
        loose_file.md            -> collected into a "General" section

- Folder and file names become titles. A short leading ordering prefix
  such as "01 ", "01-" or "01_" is stripped from the *displayed* title
  but still used for sorting, so "01 Getting Started.md" sorts first
  and is shown simply as "Getting Started". Use --raw-titles to disable
  this and use names exactly as they appear on disk.
- Fenced code blocks (```lang ... ```) are syntax highlighted at build
  time with Pygments, so the output needs no JS highlighting library
  and still works fully offline. Every code block gets a "Copy" button.
- Local images referenced with a relative path are embedded as base64
  data URIs, so the output HTML is a single, fully portable file.
- Links from one .md file to another are rewired to switch tabs inside
  the notebook instead of trying to open a raw .md file.
- A small search box lets you jump straight to any page by title or
  content.

REQUIREMENTS
------------
    pip install markdown beautifulsoup4 pygments --break-system-packages

USAGE
-----
    python md_to_onenote.py <input_dir> [-o output.html] [-t "Notebook Title"]

EXAMPLES
--------
    python md_to_onenote.py ./my_notes
    python md_to_onenote.py ./docs -o team_wiki.html -t "Team Wiki"
    python md_to_onenote.py ./docs --raw-titles
"""

import argparse
import base64
import mimetypes
import re
import sys
from html import escape
from pathlib import Path
from urllib.parse import unquote

try:
    import markdown
except ImportError:
    sys.exit(
        "Missing dependency 'markdown'.\n"
        "Install it with:  pip install markdown beautifulsoup4 pygments --break-system-packages"
    )

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit(
        "Missing dependency 'beautifulsoup4'.\n"
        "Install it with:  pip install markdown beautifulsoup4 pygments --break-system-packages"
    )

try:
    from pygments.formatters import HtmlFormatter
except ImportError:
    sys.exit(
        "Missing dependency 'pygments'.\n"
        "Install it with:  pip install markdown beautifulsoup4 pygments --break-system-packages"
    )


MD_SUFFIXES = {".md", ".markdown"}
EXCLUDED_DIR_NAMES = {
    ".git", ".github", ".svn", ".hg", "__pycache__",
    "node_modules", ".venv", "venv", ".idea", ".vscode",
}

# Syntax highlighting theme (baked into the CSS at build time - no JS
# highlighter needed at runtime, so the output stays a single offline file).
PYGMENTS_STYLE = "one-dark"
MD_EXTENSIONS = ["extra", "sane_lists", "toc", "codehilite"]
MD_EXTENSION_CONFIGS = {
    "codehilite": {
        "guess_lang": False,
        "css_class": "codehilite",
        "pygments_style": PYGMENTS_STYLE,
    }
}
PYGMENTS_CSS = HtmlFormatter(style=PYGMENTS_STYLE).get_style_defs(".codehilite")

# Cycled across sections/vertical tabs - OneNote-esque jewel tones.
TAB_COLORS = [
    "#7719AA", "#0078D4", "#0B6A0B", "#CA5010",
    "#C239B3", "#03787C", "#986F0B", "#C42B1C",
]

ORDER_PREFIX_RE = re.compile(r"^\s*(\d{1,3})[\s._-]+(.+)$")


def prettify(stem: str, raw: bool = False):
    """Return (sort_key, display_title) for a file/folder name stem."""
    if raw:
        return (1, 0, stem.lower()), stem

    match = ORDER_PREFIX_RE.match(stem)
    if match:
        order, rest = match.groups()
        rest = rest.strip() or stem
        sort_key = (0, int(order), stem.lower())
    else:
        rest = stem
        sort_key = (1, 0, stem.lower())

    title = rest.replace("_", " ").replace("-", " ")
    title = re.sub(r"\s+", " ", title).strip() or stem
    return sort_key, title


def unique_slug(base: str, used: set) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", base.strip().lower()).strip("-") or "item"
    candidate = slug
    i = 2
    while candidate in used:
        candidate = f"{slug}-{i}"
        i += 1
    used.add(candidate)
    return candidate


def tint(hex_color: str, amount: float = 0.82) -> str:
    """Mix a hex color toward white. amount=0 -> original, amount=1 -> white.
    Used to make a soft pastel wash of each section's color for active-tab
    backgrounds, without depending on browser support for CSS color-mix()."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r = round(r + (255 - r) * amount)
    g = round(g + (255 - g) * amount)
    b = round(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


class Page:
    def __init__(self, path: Path, title: str, sort_key):
        self.path = path
        self.title = title
        self.sort_key = sort_key
        self.slug = ""
        self.html = ""


class Section:
    def __init__(self, title: str, sort_key):
        self.title = title
        self.sort_key = sort_key
        self.slug = ""
        self.color = ""
        self.tint = ""
        self.pages = []


def find_md_files(folder: Path):
    return [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in MD_SUFFIXES]


def collect_sections(input_dir: Path, raw_titles: bool = False):
    sections = []

    entries = sorted(input_dir.iterdir(), key=lambda p: p.name.lower())
    subfolders = [
        p for p in entries
        if p.is_dir() and not p.name.startswith(".") and p.name not in EXCLUDED_DIR_NAMES
    ]
    loose_files = [p for p in entries if p.is_file() and p.suffix.lower() in MD_SUFFIXES]

    for folder in subfolders:
        sort_key, title = prettify(folder.name, raw_titles)
        section = Section(title, sort_key)

        used_page_slugs = set()
        seen_titles = {}
        md_files = sorted(find_md_files(folder), key=lambda p: p.name.lower())
        for md_path in md_files:
            p_sort_key, p_title = prettify(md_path.stem, raw_titles)
            rel_parent = md_path.parent.relative_to(folder)
            if str(rel_parent) != "." and p_title in seen_titles:
                p_title = f"{rel_parent.name} / {p_title}"
            seen_titles[p_title] = seen_titles.get(p_title, 0) + 1

            page = Page(md_path, p_title, p_sort_key)
            page.slug = unique_slug(p_title, used_page_slugs)
            section.pages.append(page)

        section.pages.sort(key=lambda pg: pg.sort_key)
        if section.pages:
            sections.append(section)

    if loose_files:
        general_title = "General"
        if any(s.title.lower() == "general" for s in sections):
            general_title = "Other Notes"
        general = Section(general_title, (2, 0, "general"))
        used_page_slugs = set()
        for md_path in sorted(loose_files, key=lambda p: p.name.lower()):
            p_sort_key, p_title = prettify(md_path.stem, raw_titles)
            page = Page(md_path, p_title, p_sort_key)
            page.slug = unique_slug(p_title, used_page_slugs)
            general.pages.append(page)
        general.pages.sort(key=lambda pg: pg.sort_key)
        sections.append(general)

    sections.sort(key=lambda s: s.sort_key)

    used_section_slugs = set()
    for i, section in enumerate(sections):
        section.slug = unique_slug(section.title, used_section_slugs)
        section.color = TAB_COLORS[i % len(TAB_COLORS)]
        section.tint = tint(section.color)

    return sections


def render_page_html(page: Page, path_map: dict) -> str:
    text = page.path.read_text(encoding="utf-8", errors="replace")
    fragment = markdown.markdown(text, extensions=MD_EXTENSIONS, extension_configs=MD_EXTENSION_CONFIGS)
    soup = BeautifulSoup(fragment, "html.parser")
    base_dir = page.path.parent

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith(("http://", "https://", "data:")):
            continue
        img_path = (base_dir / unquote(src)).resolve()
        if img_path.is_file():
            mime = mimetypes.guess_type(str(img_path))[0] or "application/octet-stream"
            try:
                data = base64.b64encode(img_path.read_bytes()).decode("ascii")
                img["src"] = f"data:{mime};base64,{data}"
            except OSError:
                print(f"Warning: could not read image {img_path}", file=sys.stderr)
        else:
            print(f"Warning: image not found: {src} (in {page.path})", file=sys.stderr)

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if not href or href.startswith("#"):
            continue
        if href.startswith(("http://", "https://")):
            a["target"] = "_blank"
            a["rel"] = "noopener noreferrer"
            continue
        if href.startswith("mailto:"):
            continue

        clean_href, _, anchor = href.partition("#")
        if not clean_href:
            continue
        target_path = (base_dir / unquote(clean_href)).resolve()
        if target_path in path_map:
            sec_slug, page_slug = path_map[target_path]
            a["href"] = "#"
            a["class"] = a.get("class", []) + ["internal-link"]
            a["data-goto-section"] = sec_slug
            a["data-goto-page"] = page_slug
            if anchor:
                a["data-goto-anchor"] = anchor
        elif clean_href.lower().endswith((".md", ".markdown")):
            print(f"Warning: linked file not in notebook: {clean_href} (in {page.path})", file=sys.stderr)

    for block in soup.find_all("div", class_="codehilite"):
        btn = soup.new_tag("button", type="button")
        btn["class"] = "copy-code-btn"
        btn.string = "Copy"
        block.append(btn)

    return str(soup)


def build_vtab_html(sections) -> str:
    items = []
    for s in sections:
        items.append(
            f'<button class="vtab" data-section="{escape(s.slug)}" '
            f'style="--tab-color:{s.color};--tab-tint:{s.tint}">'
            f'<span class="dot"></span><span class="label">{escape(s.title)}</span>'
            f"</button>"
        )
    return "\n".join(items)


def build_section_panels_html(sections) -> str:
    blocks = []
    for s in sections:
        htabs = "\n".join(
            f'<button class="htab" data-page="{escape(p.slug)}">{escape(p.title)}</button>'
            for p in s.pages
        )
        pages = "\n".join(
            f'<div class="page-panel" data-page="{escape(p.slug)}" data-title="{escape(p.title)}">'
            f'<div class="page-doc">{p.html}</div></div>'
            for p in s.pages
        )
        blocks.append(
            f'<section class="section-panel" data-section="{escape(s.slug)}" data-title="{escape(s.title)}" '
            f'style="--tab-color:{s.color};--tab-tint:{s.tint}">'
            f'<div class="htabs">{htabs}</div>'
            f'<div class="content">{pages}</div>'
            f"</section>"
        )
    return "\n".join(blocks)


STATIC_CSS = """
:root {
  --bg-app: #faf9f8;
  --bg-sidebar: #f3f2f1;
  --bg-content: #ffffff;
  --bg-tab-inactive: #eceae8;
  --line: #e1dfdd;
  --ink: #201f1e;
  --ink-soft: #605e5c;
  --accent: #7719aa;
  --radius: 8px;
  --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
}

* { box-sizing: border-box; }
html, body { height: 100%; margin: 0; }
body {
  font-family: var(--font-ui);
  color: var(--ink);
  background: var(--bg-app);
  -webkit-font-smoothing: antialiased;
}
button { font: inherit; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.app { display: flex; height: 100vh; overflow: hidden; }

.vtabs {
  width: 230px;
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.vtabs-header {
  padding: 20px 18px 14px;
  font-size: 14px;
  font-weight: 700;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vtab {
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  padding: 12px 16px;
  border: none;
  background: transparent;
  border-left: 6px solid var(--tab-color, var(--accent));
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
  cursor: pointer;
}
.vtab:hover { background: var(--tab-tint, rgba(0, 0, 0, 0.045)); }
.vtab.active {
  background: var(--tab-tint, var(--bg-content));
  font-weight: 700;
}
.vtab .dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--tab-color, var(--accent));
  flex-shrink: 0;
}
.vtab .label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.topbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 20px; padding: 14px 28px; border-bottom: 1px solid var(--line);
  background: var(--bg-content);
}
.topbar h1 {
  font-size: 16px; margin: 0; font-weight: 700; color: var(--ink-soft);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.topbar h1 .crumb-current { color: var(--ink); }

.search-wrap { position: relative; width: 260px; flex-shrink: 0; }
.search-wrap input {
  width: 100%; padding: 8px 14px; border: 1px solid var(--line);
  border-radius: 999px; font-size: 13.5px; outline: none; background: var(--bg-app);
  color: var(--ink);
}
.search-wrap input:focus {
  border-color: var(--accent); box-shadow: 0 0 0 3px rgba(119, 25, 170, 0.12);
  background: var(--bg-content);
}
.search-results {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0;
  background: var(--bg-content); border: 1px solid var(--line); border-radius: var(--radius);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.14); max-height: 320px; overflow-y: auto;
  display: none; z-index: 50;
}
.search-results.open { display: block; }
.search-result { padding: 9px 14px; cursor: pointer; border-bottom: 1px solid var(--line); }
.search-result:last-child { border-bottom: none; }
.search-result:hover { background: var(--bg-sidebar); }
.sr-title { font-size: 13.5px; font-weight: 600; }
.sr-section { font-size: 11.5px; color: var(--ink-soft); margin-top: 1px; }
.search-empty { padding: 10px 14px; font-size: 13px; color: var(--ink-soft); }

.section-panel { display: none; flex: 1; flex-direction: column; min-height: 0; }
.section-panel.active { display: flex; }

.htabs {
  display: flex; flex-wrap: wrap; gap: 4px; padding: 10px 24px 0;
  background: var(--bg-sidebar); border-bottom: 1px solid var(--line);
}
.htab {
  padding: 9px 18px; border: 1px solid var(--line); border-bottom: none;
  border-top: 3px solid var(--tab-color, var(--accent));
  border-radius: 8px 8px 0 0; background: var(--bg-tab-inactive);
  font-size: 13.5px; font-weight: 500; color: var(--ink-soft);
  cursor: pointer; position: relative; top: 1px;
}
.htab:hover { background: #e2e0de; color: var(--ink); }
.htab.active {
  background: var(--tab-tint, var(--bg-content)); color: var(--ink); font-weight: 700;
}

.content { flex: 1; overflow-y: auto; background: var(--bg-content); }
.page-panel { display: none; padding: 32px 40px 60px; }
.page-panel.active { display: block; }
.page-doc { max-width: 860px; margin: 0 auto; line-height: 1.65; font-size: 15.5px; }

.page-doc h1, .page-doc h2, .page-doc h3, .page-doc h4 { font-weight: 700; line-height: 1.3; }
.page-doc h1 { font-size: 27px; margin: 0 0 18px; padding-bottom: 10px; border-bottom: 2px solid var(--line); }
.page-doc h2 { font-size: 20px; margin: 30px 0 12px; }
.page-doc h3 { font-size: 16.5px; margin: 22px 0 8px; }
.page-doc p { margin: 0 0 14px; }
.page-doc ul, .page-doc ol { margin: 0 0 14px; padding-left: 24px; }
.page-doc li { margin: 4px 0; }
.page-doc blockquote {
  margin: 0 0 14px; padding: 2px 16px; border-left: 3px solid var(--accent);
  color: var(--ink-soft); background: rgba(119, 25, 170, 0.05);
}
.page-doc code {
  font-family: var(--font-mono); background: rgba(0, 0, 0, 0.055);
  padding: 2px 5px; border-radius: 4px; font-size: 0.9em;
}
.page-doc table { border-collapse: collapse; margin: 0 0 16px; width: 100%; }
.page-doc th, .page-doc td { border: 1px solid var(--line); padding: 8px 12px; text-align: left; font-size: 14px; }
.page-doc th { background: var(--bg-sidebar); font-weight: 600; }
.page-doc img { max-width: 100%; border-radius: var(--radius); margin: 8px 0; }
.page-doc a { color: var(--accent); text-decoration: none; border-bottom: 1px solid rgba(119, 25, 170, 0.35); }
.page-doc a:hover { border-bottom-color: var(--accent); }
.page-doc a.internal-link::after { content: " \u203a"; }
.page-doc hr { border: none; border-top: 1px solid var(--line); margin: 28px 0; }

.page-doc pre {
  background: #282c34; color: #abb2bf; padding: 16px 18px; border-radius: var(--radius);
  overflow-x: auto; margin: 0 0 16px; font-family: var(--font-mono); font-size: 0.88em; line-height: 1.6;
}
.page-doc pre code { background: none; padding: 0; color: inherit; font-size: inherit; }

.page-doc .codehilite {
  position: relative; border-radius: var(--radius); padding: 16px 18px;
  overflow-x: auto; margin: 0 0 16px; font-size: 0.88em; line-height: 1.6;
}
.page-doc .codehilite pre { margin: 0; padding: 0; background: none; }
.page-doc .codehilite code {
  background: none; padding: 0; font-family: var(--font-mono); font-size: inherit; color: inherit;
}

.copy-code-btn {
  position: absolute; top: 8px; right: 8px; padding: 4px 10px; font-size: 11px; font-weight: 600;
  border-radius: 5px; border: 1px solid rgba(255, 255, 255, 0.18); background: rgba(255, 255, 255, 0.08);
  color: #d5d8de; cursor: pointer; opacity: 0.55; transition: opacity .15s ease, background .15s ease;
}
.copy-code-btn:hover, .copy-code-btn:focus-visible { opacity: 1; background: rgba(255, 255, 255, 0.18); }
.copy-code-btn.copied { background: #3a9c6d; border-color: #3a9c6d; color: #fff; opacity: 1; }

.empty-state { margin: auto; text-align: center; color: var(--ink-soft); padding: 40px; }

@media (max-width: 760px) {
  .vtabs { width: 56px; }
  .vtabs-header { display: none; }
  .vtab .label { display: none; }
  .vtab { justify-content: center; padding: 14px 0; }
  .topbar { padding: 12px 16px; gap: 10px; }
  .topbar h1 { font-size: 13px; }
  .search-wrap { width: 140px; }
  .htabs { padding: 8px 12px 0; }
  .page-panel { padding: 20px 18px 40px; }
}

@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; }
}
"""

STATIC_JS = """
const lastPage = {};

function showPage(sectionSlug, pageSlug, anchor) {
  const panel = document.querySelector('.section-panel[data-section="' + sectionSlug + '"]');
  if (!panel) return;
  panel.querySelectorAll(".page-panel").forEach(function (el) {
    el.classList.toggle("active", el.dataset.page === pageSlug);
  });
  panel.querySelectorAll(".htab").forEach(function (el) {
    el.classList.toggle("active", el.dataset.page === pageSlug);
  });
  lastPage[sectionSlug] = pageSlug;

  const contentWrap = panel.querySelector(".content");
  if (contentWrap) contentWrap.scrollTop = 0;

  updateBreadcrumb(panel, pageSlug);

  if (anchor) {
    setTimeout(function () {
      const activePanel = panel.querySelector(".page-panel.active");
      const target = activePanel ? activePanel.querySelector('[id="' + anchor + '"]') : null;
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 30);
  }
}

function updateBreadcrumb(sectionPanel, pageSlug) {
  const crumb = document.getElementById("breadcrumb");
  if (!crumb) return;
  const sectionTitle = sectionPanel.dataset.title || "";
  const pagePanel = sectionPanel.querySelector('.page-panel[data-page="' + pageSlug + '"]');
  const pageTitle = pagePanel ? pagePanel.dataset.title || "" : "";
  crumb.innerHTML = "";
  const sectionSpan = document.createElement("span");
  sectionSpan.textContent = sectionTitle;
  crumb.appendChild(sectionSpan);
  if (pageTitle) {
    crumb.appendChild(document.createTextNode(" \u203a "));
    const pageSpan = document.createElement("span");
    pageSpan.className = "crumb-current";
    pageSpan.textContent = pageTitle;
    crumb.appendChild(pageSpan);
  }
}

function goToPage(sectionSlug, pageSlug, anchor) {
  document.querySelectorAll(".section-panel").forEach(function (el) {
    el.classList.toggle("active", el.dataset.section === sectionSlug);
  });
  document.querySelectorAll(".vtab").forEach(function (el) {
    el.classList.toggle("active", el.dataset.section === sectionSlug);
  });
  showPage(sectionSlug, pageSlug, anchor);
}

function activateSection(sectionSlug) {
  const panel = document.querySelector('.section-panel[data-section="' + sectionSlug + '"]');
  if (!panel) return;
  const remembered = lastPage[sectionSlug];
  const firstTab = panel.querySelector(".htab");
  const target = remembered || (firstTab ? firstTab.dataset.page : null);
  if (target) goToPage(sectionSlug, target);
}

document.querySelectorAll(".vtab").forEach(function (btn) {
  btn.addEventListener("click", function () { activateSection(btn.dataset.section); });
});

document.querySelectorAll(".htab").forEach(function (btn) {
  btn.addEventListener("click", function () {
    const sectionSlug = btn.closest(".section-panel").dataset.section;
    showPage(sectionSlug, btn.dataset.page);
  });
});

document.querySelectorAll("a.internal-link").forEach(function (a) {
  a.addEventListener("click", function (e) {
    e.preventDefault();
    goToPage(a.dataset.gotoSection, a.dataset.gotoPage, a.dataset.gotoAnchor || null);
  });
});

document.addEventListener("click", function (e) {
  const btn = e.target.closest(".copy-code-btn");
  if (!btn) return;
  const block = btn.closest(".codehilite");
  const codeEl = block ? block.querySelector("code") : null;
  if (!codeEl) return;
  const text = codeEl.innerText;
  const done = function () {
    btn.textContent = "Copied!";
    btn.classList.add("copied");
    setTimeout(function () {
      btn.textContent = "Copy";
      btn.classList.remove("copied");
    }, 1400);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, done);
  } else {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (err) {}
    document.body.removeChild(ta);
    done();
  }
});

const searchInput = document.getElementById("searchInput");
const searchResults = document.getElementById("searchResults");

function runSearch(query) {
  const q = query.trim().toLowerCase();
  searchResults.innerHTML = "";
  if (!q) { searchResults.classList.remove("open"); return; }

  const matches = [];
  document.querySelectorAll(".page-panel").forEach(function (panel) {
    const sectionPanel = panel.closest(".section-panel");
    const title = (panel.dataset.title || "").toLowerCase();
    const text = (panel.textContent || "").toLowerCase();
    if (title.indexOf(q) !== -1 || text.indexOf(q) !== -1) {
      matches.push({
        sectionSlug: sectionPanel.dataset.section,
        pageSlug: panel.dataset.page,
        title: panel.dataset.title,
        sectionTitle: sectionPanel.dataset.title,
      });
    }
  });

  if (matches.length === 0) {
    const empty = document.createElement("div");
    empty.className = "search-empty";
    empty.textContent = "No matches found";
    searchResults.appendChild(empty);
  } else {
    matches.slice(0, 8).forEach(function (m) {
      const item = document.createElement("div");
      item.className = "search-result";
      const t = document.createElement("div");
      t.className = "sr-title";
      t.textContent = m.title;
      const s = document.createElement("div");
      s.className = "sr-section";
      s.textContent = m.sectionTitle;
      item.appendChild(t);
      item.appendChild(s);
      item.addEventListener("click", function () {
        goToPage(m.sectionSlug, m.pageSlug);
        searchInput.value = "";
        searchResults.classList.remove("open");
      });
      searchResults.appendChild(item);
    });
  }
  searchResults.classList.add("open");
}

if (searchInput) {
  searchInput.addEventListener("input", function () { runSearch(searchInput.value); });
  searchInput.addEventListener("focus", function () { if (searchInput.value) runSearch(searchInput.value); });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".search-wrap")) searchResults.classList.remove("open");
  });
}

const firstTabBtn = document.querySelector(".vtab");
if (firstTabBtn) activateSection(firstTabBtn.dataset.section);
"""

EMPTY_DOC_CSS = """
body {
  font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  display: flex; align-items: center; justify-content: center;
  height: 100vh; margin: 0; background: #faf9f8; color: #605e5c;
}
.msg { text-align: center; max-width: 480px; padding: 20px; }
.msg h1 { color: #201f1e; font-size: 20px; margin-bottom: 8px; }
.msg code { background: rgba(0,0,0,0.06); padding: 2px 6px; border-radius: 4px; }
"""


def build_html_doc(notebook_title: str, sections) -> str:
    vtabs_html = build_vtab_html(sections)
    panels_html = build_section_panels_html(sections)
    body = f"""
<div class="app">
  <nav class="vtabs">
    <div class="vtabs-header">\U0001f4d3 {escape(notebook_title)}</div>
    {vtabs_html}
  </nav>
  <div class="main">
    <header class="topbar">
      <h1 id="breadcrumb"></h1>
      <div class="search-wrap">
        <input id="searchInput" type="text" placeholder="Search notebook..." autocomplete="off">
        <div id="searchResults" class="search-results"></div>
      </div>
    </header>
    {panels_html}
  </div>
</div>
"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(notebook_title)}</title>
<style>{STATIC_CSS}
{PYGMENTS_CSS}
</style>
</head>
<body>
{body}
<script>{STATIC_JS}</script>
</body>
</html>
"""


def build_empty_doc(notebook_title: str, input_dir: Path) -> str:
    message = f"No .md files were found under {input_dir}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{escape(notebook_title)}</title>
<style>{EMPTY_DOC_CSS}</style>
</head>
<body>
<div class="msg"><h1>{escape(notebook_title)}</h1><p>{escape(message)}</p></div>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(
        description="Convert a folder of Markdown files into a single OneNote-style HTML notebook.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python md_to_onenote.py ./my_notes\n"
            "  python md_to_onenote.py ./docs -o team_wiki.html -t \"Team Wiki\"\n"
            "  python md_to_onenote.py ./docs --raw-titles\n"
        ),
    )
    parser.add_argument("input_dir", help="Path to the root folder containing your notes")
    parser.add_argument("-o", "--output", default="notebook.html", help="Output HTML file path (default: notebook.html)")
    parser.add_argument("-t", "--title", default=None, help="Notebook title shown in the header (default: input folder name)")
    parser.add_argument("--raw-titles", action="store_true", help="Use file/folder names exactly as-is (skip prefix stripping and cleanup)")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    if not input_dir.is_dir():
        sys.exit(f"Error: '{input_dir}' is not a directory.")

    notebook_title = args.title or input_dir.name.replace("_", " ").replace("-", " ").strip() or "Notebook"

    sections = collect_sections(input_dir, raw_titles=args.raw_titles)

    out_path = Path(args.output)

    if not sections:
        out_path.write_text(build_empty_doc(notebook_title, input_dir), encoding="utf-8")
        print(f"No Markdown files found under {input_dir}.")
        print(f"Wrote a placeholder page to {out_path.resolve()}")
        return

    path_map = {}
    for s in sections:
        for p in s.pages:
            path_map[p.path.resolve()] = (s.slug, p.slug)

    total_pages = 0
    for s in sections:
        for p in s.pages:
            p.html = render_page_html(p, path_map)
            total_pages += 1

    out_path.write_text(build_html_doc(notebook_title, sections), encoding="utf-8")

    print(f"Notebook created: {out_path.resolve()}")
    print(f"  Sections: {len(sections)}")
    print(f"  Pages:    {total_pages}")


if __name__ == "__main__":
    main()
