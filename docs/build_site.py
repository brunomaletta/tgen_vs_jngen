#!/usr/bin/env python3
"""Bundle pinned vendor sources and docs for local preview and GitHub Pages."""

from __future__ import annotations

import html
import os
import re
import shutil
import sys

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(DOCS_DIR)
sys.path.insert(0, DOCS_DIR)

try:
    import yaml
except ImportError:
    sys.stderr.write("build_site: install PyYAML (pip install pyyaml)\n")
    sys.exit(1)

from cpp_highlight import highlight_cpp_file  # noqa: E402
from render_docs import (  # noqa: E402
    JNGEN_CATEGORY_DOC,
    JNGEN_OP_DOC,
    load_yaml,
)

TGEN_VENDOR = os.path.join(ROOT_DIR, "vendor", "tgen")
JNGEN_VENDOR = os.path.join(ROOT_DIR, "vendor", "jngen")
TGEN_DOC_BUILD = os.path.join(TGEN_VENDOR, "docs", "build")
TGEN_EMBED_CSS = os.path.join(DOCS_DIR, "tgen_embed.css")
TGEN_EMBED_LINK = '<link href="tgen_embed.css" rel="stylesheet" type="text/css"/>'

SOURCE_VIEWER_CSS = """
:root {
  color-scheme: dark;
  --bg: #0d1117;
  --text: #e6edf3;
  --muted: #8b949e;
  --line-bg: #161b22;
  --highlight: #1f3a5f;
  --link: #58a6ff;
  --scroll-offset: 20vh;
}
html {
  scroll-padding-top: var(--scroll-offset);
}
body {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.45;
  margin: 0;
  background: var(--bg);
  color: var(--text);
}
header {
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 0.75rem 1rem;
  background: var(--line-bg);
  border-bottom: 1px solid #30363d;
  font-family: system-ui, sans-serif;
  font-size: 0.9rem;
}
header a { color: var(--link); text-decoration: none; }
header a:hover { text-decoration: underline; }
pre {
  margin: 0;
  padding: 0.5rem 0;
}
.line {
  display: block;
  padding: 0 1rem 0 4.5rem;
  white-space: pre;
  position: relative;
  scroll-margin-top: var(--scroll-offset);
}
.line:target, .line.highlight {
  background: var(--highlight);
}
.line-num {
  position: absolute;
  left: 0;
  width: 3.5rem;
  padding-right: 0.75rem;
  text-align: right;
  color: var(--muted);
  text-decoration: none;
  user-select: none;
}
.line-num:hover { color: var(--link); }
.code { display: inline; }
.tok-kw { color: #ff7b72; }
.tok-type { color: #79c0ff; }
.tok-fn { color: #d2a8ff; }
.tok-cm { color: #8b949e; font-style: italic; }
.tok-str { color: #a5d6ff; }
.tok-num { color: #79c0ff; }
.tok-op { color: #e6edf3; }
.tok-pp { color: #d2a8ff; }
"""

SOURCE_VIEWER_SCRIPT = """
(function () {
  if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
  }
  function scrollToHash() {
    var hash = location.hash;
    if (!hash) return;
    var el = document.querySelector(hash);
    if (!el) return;
    document.querySelectorAll('.line.highlight').forEach(function (n) {
      n.classList.remove('highlight');
    });
    el.classList.add('highlight');
    var offset = Math.round(window.innerHeight * 0.2);
    var y = el.getBoundingClientRect().top + window.pageYOffset - offset;
    window.scrollTo(0, y);
  }
  window.addEventListener('hashchange', scrollToHash);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scrollToHash);
  } else {
    scrollToHash();
  }
})();
"""

DOC_VIEWER_CSS = """
:root {
  color-scheme: dark;
  --bg: #0f1117;
  --surface: #161b22;
  --border: #30363d;
  --text: #e6edf3;
  --muted: #8b949e;
  --link: #58a6ff;
  --code-bg: #21262d;
}
body {
  font-family: system-ui, sans-serif;
  max-width: 900px;
  margin: 2rem auto;
  padding: 0 1rem 3rem;
  line-height: 1.55;
  background: var(--bg);
  color: var(--text);
}
header {
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.9rem;
}
header a { color: var(--link); text-decoration: none; }
header a:hover { text-decoration: underline; }
h1, h2, h3, h4 { color: var(--text); border-bottom: 1px solid var(--border); padding-bottom: 0.25rem; }
h1 { font-size: 1.6rem; }
h2 { font-size: 1.25rem; margin-top: 2rem; }
h3, h4 { font-size: 1rem; margin-top: 1.25rem; border-bottom: none; }
p, ul { margin: 0.75rem 0; }
ul { padding-left: 1.5rem; }
li { margin: 0.35rem 0; }
code {
  background: var(--code-bg);
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.92em;
}
pre {
  background: var(--code-bg);
  padding: 0.85rem 1rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.88rem;
}
pre code { background: none; padding: 0; }
a { color: var(--link); }
em { color: var(--muted); font-style: italic; }
"""


def collect_jngen_source_files(api_sources) -> set[str]:
    files: set[str] = set()
    for lib_map in api_sources.get("entries", {}).values():
        entry = lib_map.get("jngen")
        if isinstance(entry, dict) and entry.get("file"):
            files.add(entry["file"])
    return files


def collect_jngen_doc_files(api_sources, operations) -> set[str]:
    op_categories = {op["id"]: op.get("category") for op in operations}
    docs: set[str] = set()
    for op_id, lib_map in api_sources.get("entries", {}).items():
        if "jngen" not in lib_map:
            continue
        doc_path = None
        entry = lib_map["jngen"]
        if isinstance(entry, dict):
            doc_path = entry.get("doc")
        if not doc_path:
            doc_path = JNGEN_OP_DOC.get(op_id)
        if not doc_path:
            doc_path = JNGEN_CATEGORY_DOC.get(op_categories.get(op_id))
        if doc_path:
            docs.add(doc_path)
    return docs


def collect_tgen_source_files(api_sources) -> set[str]:
    files: set[str] = set()
    for lib_map in api_sources.get("entries", {}).values():
        if lib_map.get("tgen"):
            files.add("single_include/tgen.h")
    return files


def comparison_back_href(out_dir: str, out_path: str, comparison_page: str) -> str:
    rel = os.path.relpath(out_dir, os.path.dirname(out_path))
    return f"{rel.replace(os.sep, '/')}/{comparison_page}"


def render_source_html(rel_path: str, content: str, back_href: str) -> str:
    lines = content.splitlines()
    highlighted = highlight_cpp_file(content)
    body = ["<pre>"]
    for i, line in enumerate(lines, 1):
        code = highlighted[i - 1] if i - 1 < len(highlighted) else html.escape(line)
        body.append(
            f'<span class="line" id="L{i}">'
            f'<a class="line-num" href="#L{i}">{i}</a>'
            f'<span class="code">{code}</span></span>'
        )
    body.append("</pre>")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(rel_path)}</title>
  <style>{SOURCE_VIEWER_CSS}</style>
</head>
<body>
  <header><a href="{html.escape(back_href)}">← comparison</a> · {html.escape(rel_path)}</header>
  {''.join(body)}
  <script>{SOURCE_VIEWER_SCRIPT}</script>
</body>
</html>
"""


def _inline_markdown(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: (
            f'<a href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>'
        ),
        text,
    )
    return text


def markdown_to_html(text: str) -> str:
    out: list[str] = []
    lines = text.splitlines()
    i = 0
    in_code = False
    code_lines: list[str] = []
    list_open = False

    def close_list():
        nonlocal list_open
        if list_open:
            out.append("</ul>")
            list_open = False

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            close_list()
            if in_code:
                out.append(
                    "<pre><code>"
                    + html.escape("\n".join(code_lines))
                    + "</code></pre>"
                )
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not line.strip():
            close_list()
            i += 1
            continue

        if line.startswith("#### "):
            close_list()
            out.append(f"<h4>{_inline_markdown(line[5:])}</h4>")
        elif line.startswith("### "):
            close_list()
            out.append(f"<h3>{_inline_markdown(line[4:])}</h3>")
        elif line.startswith("## "):
            close_list()
            out.append(f"<h2>{_inline_markdown(line[3:])}</h2>")
        elif line.startswith("# "):
            close_list()
            out.append(f"<h1>{_inline_markdown(line[2:])}</h1>")
        elif line.startswith("* ") or line.startswith("- "):
            if not list_open:
                out.append("<ul>")
                list_open = True
            out.append(f"<li>{_inline_markdown(line[2:])}</li>")
        else:
            close_list()
            out.append(f"<p>{_inline_markdown(line)}</p>")
        i += 1

    if in_code:
        out.append(
            "<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>"
        )
    close_list()
    return "\n".join(out)


def render_doc_html(rel_path: str, body_html: str, back_href: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(os.path.basename(rel_path))}</title>
  <style>{DOC_VIEWER_CSS}</style>
</head>
<body>
  <header><a href="{html.escape(back_href)}">← comparison</a> · {html.escape(rel_path)}</header>
  {body_html}
</body>
</html>
"""


def write_source_viewer(
    out_dir: str,
    vendor: str,
    rel_path: str,
    src_root: str,
    comparison_page: str,
):
    src = os.path.join(src_root, rel_path)
    if not os.path.isfile(src):
        sys.stderr.write(f"build_site: missing source {src}\n")
        return
    out_path = os.path.join(out_dir, "vendor", vendor, f"{rel_path}.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    back_href = comparison_back_href(out_dir, out_path, comparison_page)
    with open(src, encoding="utf-8", errors="replace") as f:
        content = f.read()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(render_source_html(rel_path, content, back_href))


def copy_tgen_docs(out_dir: str, comparison_page: str):
    dest = os.path.join(out_dir, "vendor", "tgen", "docs")
    if not os.path.isdir(TGEN_DOC_BUILD):
        raise FileNotFoundError(
            "build_site: tgen HTML docs missing — run 'cd vendor/tgen && make doc'"
        )
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(
        TGEN_DOC_BUILD,
        dest,
        ignore=shutil.ignore_patterns("xml", "*.xml", "llms"),
    )
    if os.path.isfile(TGEN_EMBED_CSS):
        shutil.copy2(TGEN_EMBED_CSS, os.path.join(dest, "tgen_embed.css"))
    for fname in os.listdir(dest):
        if not fname.endswith(".html"):
            continue
        out_path = os.path.join(dest, fname)
        back_href = comparison_back_href(out_dir, out_path, comparison_page)
        with open(out_path, encoding="utf-8") as f:
            content = f.read()
        if TGEN_EMBED_LINK not in content:
            content = content.replace("</head>", f"  {TGEN_EMBED_LINK}\n</head>", 1)
        banner = (
            f'<header style="margin:0 0 1rem;padding:0.75rem 1rem;'
            f'background:#161b22;border-bottom:1px solid #30363d;font-family:system-ui,sans-serif;font-size:0.9rem">'
            f'<a href="{html.escape(back_href)}" style="color:#58a6ff;text-decoration:none">'
            f"← comparison</a></header>"
        )
        if "← comparison" in content:
            content = re.sub(
                r'(<header[^>]*>.*?← comparison</a></header>)',
                banner,
                content,
                count=1,
                flags=re.DOTALL,
            )
        elif "<body>" in content:
            content = content.replace("<body>", f"<body>\n{banner}", 1)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)


def bundle_jngen_docs(
    out_dir: str, doc_paths: set[str], comparison_page: str
):
    for rel in sorted(doc_paths):
        src = os.path.join(JNGEN_VENDOR, rel)
        if not os.path.isfile(src):
            sys.stderr.write(f"build_site: missing jngen doc {src}\n")
            continue
        html_rel = rel.replace(".md", ".html")
        out_path = os.path.join(out_dir, "vendor", "jngen", html_rel)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        back_href = comparison_back_href(out_dir, out_path, comparison_page)
        with open(src, encoding="utf-8") as f:
            body = markdown_to_html(f.read())
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(render_doc_html(rel, body, back_href))


def bundle_vendor_assets(
    out_dir: str,
    api_sources: dict,
    operations: list,
    comparison_page: str = "comparison.html",
):
    vendor_root = os.path.join(out_dir, "vendor")
    if os.path.isdir(vendor_root):
        shutil.rmtree(vendor_root)

    for rel in sorted(collect_tgen_source_files(api_sources)):
        write_source_viewer(out_dir, "tgen", rel, TGEN_VENDOR, comparison_page)

    for rel in sorted(collect_jngen_source_files(api_sources)):
        write_source_viewer(out_dir, "jngen", rel, JNGEN_VENDOR, comparison_page)

    copy_tgen_docs(out_dir, comparison_page)
    bundle_jngen_docs(
        out_dir, collect_jngen_doc_files(api_sources, operations), comparison_page
    )


def assemble_pages_site(out_dir: str, site_dir: str):
    html_path = os.path.join(out_dir, "comparison.html")
    if not os.path.isfile(html_path):
        raise FileNotFoundError(f"build_site: missing {html_path}")

    gallery_src = os.path.join(out_dir, "gallery")
    vendor_src = os.path.join(out_dir, "vendor")
    if not os.path.isdir(vendor_src):
        raise FileNotFoundError(
            f"build_site: missing {vendor_src} — run bundle first (make docs)"
        )

    if os.path.isdir(site_dir):
        shutil.rmtree(site_dir)
    os.makedirs(site_dir, exist_ok=True)
    shutil.copy2(html_path, os.path.join(site_dir, "index.html"))
    if os.path.isdir(gallery_src):
        shutil.copytree(gallery_src, os.path.join(site_dir, "gallery"))
    shutil.copytree(vendor_src, os.path.join(site_dir, "vendor"))

    # Fix back links in bundled pages for index.html instead of comparison.html.
    for dirpath, _, filenames in os.walk(os.path.join(site_dir, "vendor")):
        for fname in filenames:
            if not fname.endswith(".html"):
                continue
            path = os.path.join(dirpath, fname)
            back_href = comparison_back_href(site_dir, path, "index.html")
            with open(path, encoding="utf-8") as f:
                content = f.read()
            updated = re.sub(
                r'(<a href=")[^"]*("(?: style="[^"]*")?>← comparison</a>)',
                rf"\1{back_href}\2",
                content,
                count=1,
            )
            if updated != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(updated)

    open(os.path.join(site_dir, ".nojekyll"), "w", encoding="utf-8").close()


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="docs")
    parser.add_argument("--site-dir", default="")
    parser.add_argument("--yaml", default="docs/operations.yaml")
    parser.add_argument("--sources", default="docs/api_sources.yaml")
    parser.add_argument(
        "--bundle-only",
        action="store_true",
        help="only bundle vendor assets into out-dir (default when --site-dir omitted)",
    )
    args = parser.parse_args()

    out_dir = os.path.join(ROOT_DIR, args.out_dir)
    meta = load_yaml(os.path.join(ROOT_DIR, args.yaml))
    api_sources = load_yaml(os.path.join(ROOT_DIR, args.sources))
    operations = meta.get("operations", [])

    bundle_vendor_assets(out_dir, api_sources, operations)
    print(f"build_site: bundled vendor assets under {args.out_dir}/vendor/")

    if args.site_dir:
        site_dir = os.path.join(ROOT_DIR, args.site_dir)
        assemble_pages_site(out_dir, site_dir)
        print(f"build_site: wrote {args.site_dir}/")


if __name__ == "__main__":
    main()
