#!/usr/bin/env python3
"""Generate comparison.html from YAML + JSON."""

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(DOCS_DIR)
sys.path.insert(0, DOCS_DIR)

from tgen_source_index import (  # noqa: E402
    TgenSourceIndex,
    TGEN_SITE_DOCS_PREFIX,
    default_xml_dir,
    local_source_url,
    save_index_cache,
)

try:
    import yaml
except ImportError:
    sys.stderr.write("render_docs.py: install PyYAML (pip install pyyaml)\n")
    sys.exit(1)


COMPLEXITY_RE = re.compile(r"(?:O|Omega)\((?:[^()]*|\([^()]*\))+\)")
LIB_MENTION_RE = re.compile(r"\b(jngen|tgen)(?::(?!:)| )")

EMPTY_CELL_MARK = "—"


def empty_cell_html():
    return f'<span class="cell-empty">{EMPTY_CELL_MARK}</span>'


def is_empty_cell(content):
    return content in (EMPTY_CELL_MARK, empty_cell_html())


def format_empty_aware_td(content, *extra_classes):
    classes = [c for c in extra_classes if c]
    if is_empty_cell(content) and "cell-empty" not in classes:
        classes.append("cell-empty")
    class_attr = f' class="{" ".join(classes)}"' if classes else ""
    return f"<td{class_attr}>{content}</td>"


def format_generated_at(ts):
    if not ts or ts == "—":
        return "—"
    text = ts.strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        cleaned = text.replace("T", " ", 1).removesuffix("Z")
        return f"{cleaned} UTC"


def format_compiler_display(compiler):
    if not compiler or compiler == "—":
        return "—"
    text = compiler.strip()
    lower = text.lower()
    if "gcc" in lower or "g++" in lower or "clang" in lower:
        return text
    return f"GCC {text}"


def render_vendor_commits_html(vendors, repos=None):
    repos = repos or {}
    chunks = []
    for lib in ("tgen", "jngen"):
        sha = vendors.get(lib)
        if not sha:
            continue
        repo = repos.get(lib)
        if repo:
            repo_url = f"https://github.com/{repo}/tree/{sha}"
            sha_part = (
                f'<a href="{html.escape(repo_url)}">'
                f"<code>{html.escape(sha)}</code></a>"
            )
        else:
            sha_part = f"<code>{html.escape(sha)}</code>"
        lib_part = f'<strong class="lib-label lib-{lib}">{lib}</strong>'
        chunks.append(f"{lib_part} {sha_part}")
    return ", ".join(chunks)


INFERRED_SUFFIX = " (inferred)"
INFERRED_MARK_HTML = '<span class="inferred-mark">*</span>'
TABLE_INFERRED_FOOTNOTE_HTML = (
    '<p class="table-footnote">'
    f"{INFERRED_MARK_HTML} Uniformity or complexity is undocumented "
    "and is inferred by code inspection.</p>"
)


def split_inferred(value):
    if not value or not isinstance(value, str):
        return value, False
    if value.endswith(INFERRED_SUFFIX):
        return value[: -len(INFERRED_SUFFIX)], True
    return value, False


def strip_inferred(text):
    if not text or INFERRED_SUFFIX not in text:
        return text, False
    return text.replace(INFERRED_SUFFIX, ""), True


def bold_complexities_md(text):
    if not text:
        return text
    return COMPLEXITY_RE.sub(r"**\g<0>**", text)


def bold_complexities_html(text):
    if not text:
        return text
    out = []
    last = 0
    for match in COMPLEXITY_RE.finditer(text):
        out.append(html.escape(text[last : match.start()]))
        out.append(
            f'<strong class="complexity">{html.escape(match.group(0))}</strong>'
        )
        last = match.end()
    out.append(html.escape(text[last:]))
    return "".join(out)


def format_undocumented_md():
    return "*Undocumented*"


def format_undocumented_html():
    return format_uniform_value_html("Undocumented")


def format_inferred_text_md(text):
    if not text:
        return text
    if text.strip().lower() == "undocumented":
        return format_undocumented_md()
    if INFERRED_SUFFIX not in text:
        return bold_complexities_md(highlight_lib_labels_md(text))
    idx = text.index(INFERRED_SUFFIX)
    before = text[:idx]
    after = text[idx + len(INFERRED_SUFFIX) :]
    return (
        format_inferred_text_md(before)
        + "*"
        + format_inferred_text_md(after)
    )


def format_inferred_text_html(text):
    if not text:
        return text
    if text.strip().lower() == "undocumented":
        return format_undocumented_html()
    if INFERRED_SUFFIX not in text:
        return bold_complexities_html(text)
    idx = text.index(INFERRED_SUFFIX)
    before = text[:idx]
    after = text[idx + len(INFERRED_SUFFIX) :]
    return (
        format_inferred_text_html(before)
        + INFERRED_MARK_HTML
        + format_inferred_text_html(after)
    )


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


JNGEN_CATEGORY_DOC = {
    "graphs": "doc/graph.md",
    "trees": "doc/tree.md",
    "lists": "doc/array.md",
    "math": "doc/math.md",
    "geometry": "doc/geometry.md",
    "strings": "doc/strings.md",
}

JNGEN_OP_DOC = {
    "testlib_integration": "doc/random.md",
    "str_regex": "doc/random.md",
    "geometry_svg_drawer": "doc/drawer.md",
    "anti_hash_strings": "doc/strings.md",
}


JNGEN_VENDOR_DOC_PREFIX = "vendor/jngen"
JNGEN_VENDOR_SOURCE_PREFIX = "vendor/jngen"


class ApiSourceResolver:
    def __init__(
        self,
        sources_meta,
        tgen_index,
        benchmark_to_op=None,
        op_categories=None,
    ):
        self.entries = (sources_meta or {}).get("entries", {})
        self.tgen_index = tgen_index
        self.benchmark_to_op = benchmark_to_op or {}
        self.op_categories = op_categories or {}

    def url(self, op_id, lib):
        entry = self.entries.get(op_id, {}).get(lib)
        if not entry:
            return None
        if lib == "tgen":
            symbol = entry if isinstance(entry, str) else entry.get("symbol")
            if not symbol or self.tgen_index is None:
                return None
            return self.tgen_index.source_url(symbol)
        if lib == "jngen":
            if isinstance(entry, str):
                return None
            file_path = entry.get("file")
            line = entry.get("line")
            if not file_path or line is None:
                return None
            return local_source_url(
                file_path, int(line), prefix=JNGEN_VENDOR_SOURCE_PREFIX
            )
        return None

    def op_id_for_benchmark(self, bench_id):
        return self.benchmark_to_op.get(bench_id)

    def url_for_benchmark(self, bench_id, lib="tgen"):
        op_id = self.op_id_for_benchmark(bench_id)
        if not op_id:
            return None
        return self.url(op_id, lib)

    def doc_url(self, op_id, lib):
        entry = self.entries.get(op_id, {}).get(lib)
        if lib == "tgen":
            if isinstance(entry, dict) and entry.get("doc"):
                return f"{TGEN_SITE_DOCS_PREFIX}/{entry['doc']}"
            symbol = entry if isinstance(entry, str) else (
                entry.get("symbol") if entry else None
            )
            if not symbol or self.tgen_index is None:
                return None
            return self.tgen_index.docs_url(symbol)
        if lib == "jngen":
            if not entry or isinstance(entry, str):
                return None
            doc_path = entry.get("doc") or JNGEN_OP_DOC.get(op_id)
            if not doc_path:
                doc_path = JNGEN_CATEGORY_DOC.get(self.op_categories.get(op_id))
            if not doc_path:
                return None
            html_path = doc_path.replace(".md", ".html")
            return f"{JNGEN_VENDOR_DOC_PREFIX}/{html_path}"
        return None

    def doc_url_for_benchmark(self, bench_id, lib="tgen"):
        op_id = self.op_id_for_benchmark(bench_id)
        if not op_id:
            return None
        return self.doc_url(op_id, lib)


def build_benchmark_to_op_map(operations, sources_meta):
    mapping = {}
    for op in operations or []:
        bench_id = op.get("benchmark_id")
        if bench_id:
            mapping[bench_id] = op["id"]
    for bench_id, target in (sources_meta or {}).get("benchmarks", {}).items():
        if isinstance(target, str):
            mapping[bench_id] = target
        elif isinstance(target, dict) and target.get("op"):
            mapping[bench_id] = target["op"]
    return mapping


def load_api_sources(path=None):
    path = path or os.path.join(DOCS_DIR, "api_sources.yaml")
    if not os.path.isfile(path):
        return {}
    return load_yaml(path)


def build_tgen_source_index(xml_dir=None, cache_path=None):
    xml_dir = xml_dir or default_xml_dir(ROOT_DIR)
    cache_path = cache_path or os.path.join(DOCS_DIR, "tgen_symbol_index.json")
    index = TgenSourceIndex(xml_dir)
    if len(index) > 0:
        save_index_cache(index._index, cache_path)
        return index
    cached = TgenSourceIndex.from_cache(cache_path)
    if cached and len(cached) > 0:
        sys.stderr.write(
            f"render_docs: using cached tgen symbol index ({len(cached)} symbols)\n"
        )
        return cached
    sys.stderr.write(
        "render_docs: tgen Doxygen XML missing or empty — run "
        "'cd vendor/tgen && make doc-prepare' (API links for tgen will be omitted)\n"
    )
    return None


def yes_no(val):
    if val is True:
        return "Yes"
    if val is False:
        return "No"
    return val or "—"


# Ops where uniformity is N/A (deterministic construction or not random sampling).
NO_DEFAULT_UNIFORM_OPS = frozenset({
    "declarative_generators",
    "hack_unsigned_polynomial_hash",
    "hack_mt19937_xor_hash",
    "hack_rotating_calipers",
    "geometry_svg_drawer",
})

NO_DEFAULT_UNIFORM_CATEGORIES = frozenset({"hacks", "other"})


def uniform_label(base):
    if not base:
        return "—"
    mapping = {
        "uniform": "Uniform",
        "non-uniform": "Non\u2011uniform",
        "undocumented": "Undocumented",
    }
    return mapping.get(base, base)


def get_uniform_raw(lib_info, category, op_id):
    if not lib_info.get("has"):
        return None, False
    uniform = lib_info.get("uniform")
    if uniform:
        return split_inferred(uniform)
    if category in NO_DEFAULT_UNIFORM_CATEGORIES:
        return None, False
    if op_id in NO_DEFAULT_UNIFORM_OPS:
        return None, False
    return "undocumented", False


def lib_uniformity_parts(tg, jg, category, op_id):
    parts = []
    for lib, info in (("jngen", jg), ("tgen", tg)):
        base, inferred = get_uniform_raw(info, category, op_id)
        if base:
            parts.append((lib, uniform_label(base), inferred))
    return parts


def highlight_lib_labels_md(text):
    return text.replace("tgen:", "**tgen:**").replace("jngen:", "**jngen:**")


def highlight_lib_names_md(text):
    if not text:
        return text
    text = highlight_lib_labels_md(text)

    def repl(match):
        return f"**{match.group(1)}**"

    return LIB_MENTION_RE.sub(repl, text)


LIB_NAME_PREFIXES = ("tgen", "jngen")


def capitalize_doc_text(text):
    if not text:
        return text
    if text[0].islower() and not any(
        text.startswith(f"{name}:") or text.startswith(f"{name} ")
        for name in LIB_NAME_PREFIXES
    ):
        text = text[0].upper() + text[1:]

    def cap_letter(match):
        prefix = match.group(1)
        letter = match.group(2)
        following = text[match.start(2) :]
        if prefix in (". ", "; ") and any(
            following.startswith(name) for name in LIB_NAME_PREFIXES
        ):
            return prefix + letter
        return prefix + letter.upper()

    text = re.sub(r"(\. )([a-z])", cap_letter, text)
    text = re.sub(r"(; )([a-z])", cap_letter, text)
    text = re.sub(r"((?:tgen|jngen): )([a-z])", cap_letter, text)
    return text


def highlight_lib_names_html(text):
    if not text:
        return text
    out = []
    last = 0
    for match in LIB_MENTION_RE.finditer(text):
        out.append(html.escape(text[last : match.start()]))
        lib = match.group(1)
        if match.group(0).endswith(":"):
            out.append(f'<strong class="lib-label lib-{lib}">{lib}:</strong>')
        else:
            out.append(f'<strong class="lib-label lib-{lib}">{lib}</strong> ')
        last = match.end()
    out.append(html.escape(text[last:]))
    return "".join(out)


def format_notes_text_md(text):
    return bold_complexities_md(highlight_lib_names_md(capitalize_doc_text(text)))


def format_notes_text_html(text):
    if not text:
        return text
    text = capitalize_doc_text(text)
    if INFERRED_SUFFIX not in text:
        out = []
        last = 0
        for match in COMPLEXITY_RE.finditer(text):
            out.append(highlight_lib_names_html(text[last : match.start()]))
            out.append(
                f'<strong class="complexity">{html.escape(match.group(0))}</strong>'
            )
            last = match.end()
        out.append(highlight_lib_names_html(text[last:]))
        return "".join(out)
    idx = text.index(INFERRED_SUFFIX)
    before = text[:idx]
    after = text[idx + len(INFERRED_SUFFIX) :]
    return (
        format_notes_text_html(before)
        + INFERRED_MARK_HTML
        + format_notes_text_html(after)
    )


def format_exclusive_md(lib):
    return f"**{lib}-only**"


def format_exclusive_html(lib):
    return f'<strong class="lib-label lib-{html.escape(lib)}">{html.escape(lib)}-only</strong>'


def show_exclusive_badge(tg, jg, exclusive):
    if exclusive not in ("jngen", "tgen"):
        return False
    if exclusive == "tgen" and not jg.get("has") and tg.get("has"):
        return False
    if exclusive == "jngen" and not tg.get("has") and jg.get("has"):
        return False
    return True


def format_uniformity_md(tg, jg, category, op_id):
    parts = lib_uniformity_parts(tg, jg, category, op_id)
    if not parts:
        return "—"
    rows = []
    for lib, label, inferred in parts:
        suffix = "*" if inferred else ""
        rows.append(f"**{lib}:**<br>{label}{suffix}")
    return "<br>".join(rows)


def op_has_inferred(op):
    for lib in ("jngen", "tgen"):
        info = op.get(lib, {})
        uniform = info.get("uniform")
        if uniform and isinstance(uniform, str) and uniform.endswith(INFERRED_SUFFIX):
            return True
        complexity = info.get("complexity")
        if complexity and INFERRED_SUFFIX in complexity:
            return True
    return False


def category_has_inferred(ops):
    return any(
        op_has_inferred(op) for op in ops if not op.get("gallery_only")
    )


def uniform_value_class(text):
    if text == "Uniform":
        return "uniform-yes"
    if text == "Non\u2011uniform":
        return "uniform-no"
    return ""


def format_uniform_value_html(text, inferred=False):
    if text == "Undocumented":
        return f'<span class="uniform-val uniform-undocumented"><em>{html.escape(text)}</em></span>'
    css = uniform_value_class(text)
    mark = INFERRED_MARK_HTML if inferred else ""
    inner = html.escape(text)
    if css:
        return (
            f'<span class="uniform-val {css}">'
            f"<strong>{inner}</strong>{mark}</span>"
        )
    return f'<span class="uniform-val">{inner}{mark}</span>'


def format_uniformity_html(tg, jg, category, op_id):
    parts = lib_uniformity_parts(tg, jg, category, op_id)
    if not parts:
        return "—"
    rows = []
    for lib, label, inferred in parts:
        if lib == "jngen":
            row_label = '<strong class="lib-label lib-jngen">jngen:</strong>'
        else:
            row_label = '<strong class="lib-label lib-tgen">tgen:</strong>'
        rows.append(
            '<div class="uniform-entry">'
            f"{row_label}"
            f"{format_uniform_value_html(label, inferred)}"
            "</div>"
        )
    return "".join(rows)


def format_lib_uniformity_html(lib_info, category, op_id):
    base, inferred = get_uniform_raw(lib_info, category, op_id)
    if not base:
        return ""
    label = uniform_label(base)
    return (
        '<span class="api-uniformity">'
        f"{format_uniform_value_html(label, inferred)}"
        "</span>"
    )


def complexity_first_clause(complexity):
    if not complexity:
        return complexity
    return complexity.split(";", 1)[0].strip()


TIME_QUALIFIERS = ("expected",)


def complexity_clause_with_time(clause):
    text = clause.strip()
    if not text:
        return text
    if text.endswith("."):
        text = text[:-1].rstrip()
    inferred = INFERRED_SUFFIX in text
    if inferred:
        text = text.replace(INFERRED_SUFFIX, "")
        text = re.sub(r"\s+", " ", text).strip()
    match = COMPLEXITY_RE.search(text)
    if not match:
        return clause.strip()
    head = text[: match.end()]
    tail = text[match.end() :].strip()
    qualifier = ""
    for word in TIME_QUALIFIERS:
        if tail == word or tail.startswith(word + " "):
            qualifier = word
            tail = tail[len(word) :].strip()
            break
    out = head
    if qualifier:
        out += " " + qualifier
    out += " time"
    if inferred:
        out += INFERRED_SUFFIX
    if tail:
        out += " " + tail
    return out


COMPLEXITY_OR_SEP = " or "
COMPLEXITY_OR_MARKER = "__OR__"


def complexity_alternatives(complexity):
    if COMPLEXITY_OR_SEP not in complexity:
        return [complexity]
    alts = [part.strip() for part in complexity.split(COMPLEXITY_OR_SEP)]
    if len(alts) >= 2 and all(COMPLEXITY_RE.search(part) for part in alts):
        return alts
    return [complexity]


def complexity_with_time_clauses(complexity):
    if not complexity:
        return []
    lines = []
    for i, alternative in enumerate(complexity_alternatives(complexity)):
        if i > 0:
            lines.append(COMPLEXITY_OR_MARKER)
        parts = alternative.split("; ") if "; " in alternative else [alternative]
        lines.extend(complexity_clause_with_time(part) for part in parts)
    return lines


def format_lib_complexity_html(lib_info, brief=False):
    complexity = lib_info.get("complexity", "")
    if not complexity or not lib_info.get("has"):
        return ""
    if brief:
        complexity = complexity_first_clause(complexity)
    lines = []
    for clause in complexity_with_time_clauses(complexity):
        if clause == COMPLEXITY_OR_MARKER:
            lines.append('<span class="api-complexity-or">or</span>')
            continue
        if not COMPLEXITY_RE.search(clause):
            continue
        lines.append(
            f'<span class="api-complexity-line">'
            f"{format_inferred_text_html(clause)}</span>"
        )
    return '<span class="api-complexity">' + "".join(lines) + "</span>"


NOTES_SEP_MD = "<hr>"
NOTES_SEP_HTML = '<hr class="notes-sep">'


def join_notes_blocks(blocks, sep="<br>"):
    out = []
    for block in blocks:
        if block in (NOTES_SEP_MD, NOTES_SEP_HTML):
            out.append(block)
        elif out and out[-1] not in (NOTES_SEP_MD, NOTES_SEP_HTML):
            out.append(sep)
            out.append(block)
        else:
            out.append(block)
    return "".join(out) if out else "—"


def format_notes_md(tg, jg, extra_notes, exclusive=None):
    blocks = []
    if extra_notes:
        blocks.append(format_notes_text_md(extra_notes))
    if show_exclusive_badge(tg, jg, exclusive):
        blocks.append(format_exclusive_md(exclusive))
    return join_notes_blocks(blocks)


def format_notes_html(tg, jg, extra_notes, exclusive=None):
    blocks = []
    if extra_notes:
        blocks.append(format_notes_text_html(extra_notes))
    if show_exclusive_badge(tg, jg, exclusive):
        blocks.append(format_exclusive_html(exclusive))
    text = join_notes_blocks(blocks)
    return empty_cell_html() if text == EMPTY_CELL_MARK else text


API_WRAP_MAX_LEN = 52


def wrap_api_line(line, max_len):
    if len(line) <= max_len:
        return line
    best = None
    pos = 0
    while True:
        idx = line.find(").", pos)
        if idx == -1:
            break
        head = line[: idx + 1]
        if len(head) <= max_len:
            best = idx
        pos = idx + 2
    if best is not None:
        head = line[: best + 1]
        tail = line[best + 2 :]
        return head + "<br>." + wrap_api_line(tail, max_len)
    return line


def wrap_api(api, max_len=API_WRAP_MAX_LEN):
    """Break long API strings at chained calls or semicolon-separated items."""
    if len(api) <= max_len:
        return api

    if "; " in api:
        parts = api.split("; ")
        if len(api) > max_len or any(len(part) > max_len for part in parts):
            lines = [parts[0]] + ["; " + part for part in parts[1:]]
            return "<br>".join(wrap_api_line(line, max_len) for line in lines)

    return wrap_api_line(api, max_len)


def wrap_api_html(api):
    return wrap_api(html.escape(api))


def normalize_tgen_api(api):
    if not api:
        return api
    return api.replace("tgen::", "")


def format_api_md(api):
    return f"<code>{wrap_api(api)}</code>"


def format_api_code_box_html(api, source_url=None):
    code = f"<code>{wrap_api_html(api)}</code>"
    inner = code
    if source_url:
        inner = (
            f'<a class="api-source-link" href="{html.escape(source_url)}" '
            f'target="_blank" rel="noopener">{code}</a>'
        )
    return f'<div class="api-code-box">{inner}</div>'


def format_api_html(api, source_url=None, doc_url=None):
    return format_api_code_box_html(api, source_url) + format_doc_line_html(doc_url)


def format_doc_line_html(doc_url):
    if doc_url:
        return (
            f'<span class="api-doc-line">'
            f'<a class="api-doc-link" href="{html.escape(doc_url)}" '
            f'target="_blank" rel="noopener">Docs</a>'
            f"</span>"
        )
    return f'<span class="api-doc-line"><em>Undocumented</em></span>'


def format_lib_api_cell_md(lib_info, lib=None):
    if not lib_info.get("has"):
        return "**No**"
    cell = "Yes"
    if lib_info.get("api"):
        api = lib_info["api"]
        if lib == "tgen":
            api = normalize_tgen_api(api)
        cell += f"<br>{format_api_md(api)}"
    return cell


def format_lib_api_cell_html(
    lib_info,
    lib=None,
    op_id=None,
    source_resolver=None,
    category=None,
    complexity_brief=False,
):
    if not lib_info.get("has"):
        return "<strong>No</strong>"
    parts = ['<div class="api-cell">', '<div class="api-cell-yes">Yes</div>']
    if lib_info.get("api"):
        api = lib_info["api"]
        if lib == "tgen":
            api = normalize_tgen_api(api)
        source_url = None
        doc_url = None
        if source_resolver and op_id and lib:
            source_url = source_resolver.url(op_id, lib)
            doc_url = source_resolver.doc_url(op_id, lib)
        parts.append(format_api_code_box_html(api, source_url))
        parts.append(format_doc_line_html(doc_url))
    uniformity = format_lib_uniformity_html(lib_info, category, op_id)
    if uniformity:
        parts.append(uniformity)
    complexity = format_lib_complexity_html(lib_info, brief=complexity_brief)
    if complexity:
        parts.append(complexity)
    parts.append("</div>")
    return "".join(parts)


def wrap_benchmark_name(name):
    return wrap_api(name)


def wrap_params(params):
    return params


def _format_scientific_number_html(num_str, min_exp_gt=2):
    num_str = num_str.strip()
    e_pos = -1
    for sep in ("e", "E"):
        pos = num_str.find(sep)
        if pos != -1:
            e_pos = pos
            break
    if e_pos == -1:
        return html.escape(num_str)

    mantissa = num_str[:e_pos]
    exponent = num_str[e_pos + 1 :]
    if not mantissa or not exponent:
        return html.escape(num_str)
    try:
        exp_val = int(exponent)
    except ValueError:
        return html.escape(num_str)
    if abs(exp_val) <= min_exp_gt:
        try:
            val = float(num_str)
            if val == int(val):
                return html.escape(str(int(val)))
        except ValueError:
            pass
        return html.escape(num_str)

    exp_html = html.escape(exponent)
    if mantissa == "1":
        return f"10<sup>{exp_html}</sup>"
    return f"{html.escape(mantissa)}&times;10<sup>{exp_html}</sup>"


def format_params_html(params):
    if not params:
        return ""
    out = []
    pos = 0
    while pos < len(params):
        eq = params.find("=", pos)
        if eq == -1:
            out.append(html.escape(params[pos:]))
            break
        out.append(html.escape(params[pos : eq + 1]))
        pos = eq + 1
        end = params.find(",", pos)
        if end == -1:
            end = len(params)
        out.append(_format_scientific_number_html(params[pos:end]))
        pos = end
        if pos < len(params):
            out.append(html.escape(params[pos]))
            pos += 1
            while pos < len(params) and params[pos] == " ":
                out.append(html.escape(params[pos]))
                pos += 1
    return "".join(out)


def format_benchmark_name_md(name):
    return f"<code>{wrap_benchmark_name(name)}</code>"


def format_benchmark_name_html(name, source_url=None, doc_url=None):
    code = f"<code>{wrap_api_html(name)}</code>"
    if source_url:
        code = (
            f'<a class="api-source-link" href="{html.escape(source_url)}" '
            f'target="_blank" rel="noopener">{code}</a>'
        )
    return code + format_doc_line_html(doc_url)


def format_params_md(params):
    return wrap_params(params)


GALLERY_SEED_BASE = 42
GALLERY_VARIANT_COUNT = 20
GALLERY_IMG_SIZE = 2000  # normalize_gallery.py CANVAS_SIZE


def gallery_seeds():
    return list(range(GALLERY_SEED_BASE, GALLERY_SEED_BASE + GALLERY_VARIANT_COUNT))


def sample_svg_path(op_id, lib, seed=GALLERY_SEED_BASE):
    return f"gallery/{op_id}_{lib}_s{seed}.svg"


def sample_svg_exists(op_id, lib, seed=GALLERY_SEED_BASE):
    return os.path.isfile(os.path.join("docs", sample_svg_path(op_id, lib, seed)))


def render_sample_widget(op_id, lib):
    seeds = gallery_seeds()
    prefix = f"gallery/{op_id}_{lib}"
    initial = f"{prefix}_s{seeds[0]}.svg"
    seeds_json = json.dumps(seeds)
    return (
        f'<div class="sample-widget" data-prefix="{html.escape(prefix)}" '
        f'data-seeds="{html.escape(seeds_json)}" data-index="0">'
        f'<img class="sample-img" src="{html.escape(initial)}" '
        f'width="{GALLERY_IMG_SIZE}" height="{GALLERY_IMG_SIZE}" '
        f'loading="lazy" decoding="async" '
        f'alt="{html.escape(lib)} sample">'
        f'<button type="button" class="sample-regen" '
        f'title="Next sample (Shift-click: random)">↻</button>'
        f"</div>"
    )


def _sample_stack_ids(op):
    return op.get("gallery_stack") or []


def _sample_lib_info(sid, parent_op, operations_by_id, lib):
    child = operations_by_id.get(sid)
    if child:
        info = child.get(lib, {})
        if info.get("complexity"):
            return info
    return parent_op.get(lib, {})


def _append_sample_images_html(cell, op, lib, operations_by_id):
    stack = _sample_stack_ids(op)
    if stack:
        top_params = op.get("gallery_stack_top_params", "")
        mid_params = op.get("gallery_stack_params", "")
        for i, sid in enumerate(stack):
            if i == 0 and top_params:
                cell += (
                    f'<span class="gallery-params gallery-params-stack">'
                    f"{format_params_html(top_params)}</span>"
                )
            if sample_svg_exists(sid, lib):
                cell += render_sample_widget(sid, lib)
            if i == 0 and len(stack) > 1 and mid_params:
                cell += (
                    f'<span class="gallery-params gallery-params-stack">'
                    f"{format_params_html(mid_params)}</span>"
                )
        return cell
    if sample_svg_exists(op["id"], lib):
        cell += render_sample_widget(op["id"], lib)
    return cell


def format_sample_cell_html(
    op_id, op, lib_info, lib, operations_by_id, source_resolver=None
):
    cell = format_lib_api_cell_html(
        lib_info,
        lib=lib,
        op_id=op_id,
        source_resolver=source_resolver,
        category=op.get("category"),
        complexity_brief=True,
    )
    if not lib_info.get("has"):
        return cell

    stack = _sample_stack_ids(op)
    params = op.get("gallery_params", "")
    if params and not stack:
        cell += (
            f'<br><span class="gallery-params">{format_params_html(params)}</span>'
        )

    cell = _append_sample_images_html(cell, op, lib, operations_by_id)
    return cell


def api_cell_td_class(lib_info, lib=None):
    classes = ["col-api"]
    if lib:
        classes.append(f"col-api-{lib}")
    if not lib_info.get("has"):
        classes.append("cell-unavailable")
    return " ".join(classes)


def sample_cell_td_class(op, lib_info, lib):
    classes = ["col-api", f"col-api-{lib}"]
    stack = _sample_stack_ids(op)
    if stack:
        if any(sample_svg_exists(sid, lib) for sid in stack):
            classes.append("sample-has-visual")
    elif sample_svg_exists(op["id"], lib):
        classes.append("sample-has-visual")
    if not lib_info.get("has"):
        classes.append("cell-unavailable")
    return " ".join(classes)


def comparison_table_header_row():
    return (
        "<tr><th>Operation</th>"
        '<th class="col-api"><strong class="lib-label lib-jngen">jngen</strong></th>'
        '<th class="col-api"><strong class="lib-label lib-tgen">tgen</strong></th>'
        "<th>Notes</th><th>Benchmark</th></tr>"
    )


def sample_table_header_row():
    return (
        '<tr><th class="col-op sample-op">Operation</th>'
        '<th class="col-api"><strong class="lib-label lib-jngen">jngen</strong></th>'
        '<th class="col-api"><strong class="lib-label lib-tgen">tgen</strong></th></tr>'
    )


def sample_operations_by_category(operations):
    by_cat = {}
    for op in operations:
        if not op.get("visualize") or op.get("gallery_only"):
            continue
        by_cat.setdefault(op.get("category", "other"), []).append(op)
    return by_cat


def samples_have_inferred(ops, operations_by_id):
    for op in ops:
        stack = _sample_stack_ids(op)
        sids = stack if stack else [op["id"]]
        category = op.get("category")
        for sid in sids:
            for lib in ("jngen", "tgen"):
                if not sample_svg_exists(sid, lib):
                    continue
                lib_info = _sample_lib_info(sid, op, operations_by_id, lib)
                complexity = lib_info.get("complexity", "")
                if complexity and INFERRED_SUFFIX in complexity:
                    return True
                uniform = lib_info.get("uniform")
                if uniform and isinstance(uniform, str) and uniform.endswith(
                    INFERRED_SUFFIX
                ):
                    return True
                if not lib_info.get("uniform"):
                    base, inferred = get_uniform_raw(lib_info, category, sid)
                    if inferred:
                        return True
    return False


def render_sample_category_table_html(ops, operations, source_resolver=None):
    if not ops:
        return []
    operations_by_id = {op["id"]: op for op in operations}
    parts = [
        '<div class="table-scroll"><table class="comparison-table samples-table">',
        "<colgroup>"
        '<col class="col-op">'
        '<col class="col-api">'
        '<col class="col-api">'
        "</colgroup>",
        sample_table_header_row(),
    ]
    for op in ops:
        oid = op["id"]
        parts.append(
            "<tr>"
                f"<td class=\"col-op sample-op\">{html.escape(op['name'])}</td>"
                f'<td class="{sample_cell_td_class(op, op.get("jngen", {}), "jngen")}">'
                f'{format_sample_cell_html(oid, op, op.get("jngen", {}), "jngen", operations_by_id, source_resolver)}</td>'
                f'<td class="{sample_cell_td_class(op, op.get("tgen", {}), "tgen")}">'
                f'{format_sample_cell_html(oid, op, op.get("tgen", {}), "tgen", operations_by_id, source_resolver)}</td>'
            "</tr>"
        )
    parts.append("</table></div>")
    if samples_have_inferred(ops, operations_by_id):
        parts.append(TABLE_INFERRED_FOOTNOTE_HTML)
    return parts


def render_samples_section_html(operations, categories, source_resolver=None):
    by_cat = sample_operations_by_category(operations)
    if not by_cat:
        return []
    parts = ["<h2>Samples</h2>"]
    for cat_id, cat_label in categories.items():
        ops = by_cat.get(cat_id)
        if not ops:
            continue
        parts.append(f"<h3>{html.escape(cat_label)}</h3>")
        parts.extend(
            render_sample_category_table_html(ops, operations, source_resolver)
        )
    return parts


def fmt_ms(ms):
    if ms < 1:
        return "<1 ms"
    if ms < 10:
        text = f"{ms:.1f}".rstrip("0").rstrip(".")
        return f"{text} ms"
    return f"{round(ms)} ms"


def build_benchmark_index(bench):
    if not bench:
        return {}
    return {row["id"]: row for row in bench.get("results", []) if row.get("id")}


def lib_median_ms_raw(lib_result):
    if lib_result.get("status") == "ok" and lib_result.get("median_ms") is not None:
        return float(lib_result["median_ms"])
    return None


def render_bench_bar_row(label, label_class, ms, max_ms, show_time=True):
    if ms is None or max_ms is None or max_ms <= 0:
        return ""
    pct = min(100.0, 100.0 * ms / max_ms)
    time_html = (
        f'<span class="bench-bar-time">{html.escape(fmt_ms(ms))}</span>'
        if show_time
        else ""
    )
    return (
        f'<div class="bench-bar-row">'
        f'<span class="bench-bar-label {label_class}">{html.escape(label)}</span>'
        f'<div class="bench-bar-body">'
        f'<div class="bench-bar-track">'
        f'<div class="bench-bar-fill {label_class}" style="width:{pct:.1f}%"></div>'
        f"</div>"
        f"{time_html}"
        f"</div>"
        f"</div>"
    )


def render_bench_bars_html(jg_ms, tg_ms, show_times=True):
    if jg_ms is None or tg_ms is None:
        return "—"
    max_ms = max(jg_ms, tg_ms)
    parts = ['<div class="bench-bars">']
    parts.append(render_bench_bar_row("jngen", "lib-jngen", jg_ms, max_ms, show_times))
    parts.append(render_bench_bar_row("tgen", "lib-tgen", tg_ms, max_ms, show_times))
    parts.append("</div>")
    return "".join(parts)


def lib_benchmark_ok(lib_result):
    return lib_result.get("status") == "ok"


def render_bench_fail_row(label, label_class, lib_result, *, show_detail=True):
    status = lib_result.get("status", "failed")
    if status == "error":
        badge = "FAILURE"
    elif status == "timeout":
        badge = "TIMEOUT"
    else:
        badge = status.upper()

    error = lib_result.get("error", "").strip()
    detail = ""
    if show_detail and error and status in ("error", "timeout"):
        if len(error) > 140:
            error = error[:137] + "..."
        detail = f'<div class="bench-fail-detail">{html.escape(error)}</div>'

    return (
        f'<div class="bench-bar-row bench-fail-row bench-fail-row-{label_class}">'
        f'<span class="bench-bar-label {label_class}">{html.escape(label)}</span>'
        f'<div class="bench-bar-body">'
        f'<div class="bench-bar-track">'
        f'<div class="bench-bar-fill bench-bar-fill-fail {label_class}" '
        f'style="width:100.0%">'
        f'<span class="bench-fail-label">{html.escape(badge)}</span>'
        f"</div></div>"
        f"{detail}"
        f"</div>"
        f"</div>"
    )


def render_bench_comparison_html(
    jg_result, tg_result, show_times=True, *, show_fail_detail=True
):
    jg_ok = lib_benchmark_ok(jg_result)
    tg_ok = lib_benchmark_ok(tg_result)
    jg_ms = lib_median_ms_raw(jg_result) if jg_ok else None
    tg_ms = lib_median_ms_raw(tg_result) if tg_ok else None

    if jg_ok and tg_ok and jg_ms is not None and tg_ms is not None:
        return render_bench_bars_html(jg_ms, tg_ms, show_times)

    ms_values = [m for m in (jg_ms, tg_ms) if m is not None]
    max_ms = max(ms_values) if ms_values else 1

    parts = ['<div class="bench-bars">']
    if jg_ok and jg_ms is not None:
        parts.append(
            render_bench_bar_row("jngen", "lib-jngen", jg_ms, max_ms, show_times)
        )
    else:
        parts.append(
            render_bench_fail_row(
                "jngen", "lib-jngen", jg_result, show_detail=show_fail_detail
            )
        )
    if tg_ok and tg_ms is not None:
        parts.append(
            render_bench_bar_row("tgen", "lib-tgen", tg_ms, max_ms, show_times)
        )
    else:
        parts.append(
            render_bench_fail_row(
                "tgen", "lib-tgen", tg_result, show_detail=show_fail_detail
            )
        )
    parts.append("</div>")
    return "".join(parts)


def bench_ratio(row):
    jg_ms = lib_median_ms_raw(row.get("jngen", {}))
    tg_ms = lib_median_ms_raw(row.get("tgen", {}))
    if jg_ms is None or tg_ms is None or jg_ms <= 0:
        return None
    return tg_ms / jg_ms


def format_ratio_html(row):
    ratio = bench_ratio(row)
    if ratio is None:
        return empty_cell_html()
    if ratio > 0 and ratio < 0.01:
        text = "<0.01x"
    else:
        text = f"{ratio:.2f}x"
    if ratio > 1:
        css = "bench-ratio bench-ratio-jngen"
    elif ratio < 1:
        css = "bench-ratio bench-ratio-tgen"
    else:
        css = "bench-ratio"
    return f'<strong class="{css}">{html.escape(text)}</strong>'


def benchmark_is_comparable(row):
    if not row.get("compare_both"):
        return False
    params = row.get("params", "")
    # Different n per library (e.g. jngen convex polygon capped at n=1e3).
    if "(tgen)" in params and "(jngen)" in params:
        return False
    return True


def lib_timing_ms(lib_result):
    if lib_result.get("status") == "ok":
        return fmt_ms(float(lib_result["median_ms"]))
    return str(lib_result.get("status", "—"))


def render_benchmark_row_lines(
    row, *, include_ratio=False, include_params=True, show_fail_detail=True
):
    lines = []
    if row.get("compare_both"):
        lines.append(
            render_bench_comparison_html(
                row.get("jngen", {}),
                row.get("tgen", {}),
                show_times=True,
                show_fail_detail=show_fail_detail,
            )
        )
        if include_ratio:
            if benchmark_is_comparable(row) and bench_ratio(row) is not None:
                lines.append(format_ratio_html(row))
            elif not benchmark_is_comparable(row):
                lines.append(
                    '<em class="bench-params">Different n — not comparable</em>'
                )
    else:
        lines.append(
            '<strong class="lib-label lib-tgen">tgen:</strong> '
            + html.escape(lib_timing_ms(row.get("tgen", {})))
        )

    if include_params:
        params = row.get("params", "")
        if params:
            lines.append(
                f'<span class="bench-params">{format_params_html(params)}</span>'
            )

    return lines


def join_benchmark_cell_lines(lines):
    """Join benchmark lines without a blank row where ratio is omitted.

    A block-level ``bench-bars`` div already ends on its own line; inserting
    ``<br>`` before params when ratio is skipped leaves an extra empty line.
    """
    if not lines:
        return ""

    parts = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            i + 1 < len(lines)
            and 'class="bench-bars"' in line
            and '<span class="bench-params">' in lines[i + 1]
        ):
            parts.append(line + lines[i + 1])
            i += 2
            continue
        parts.append(line)
        i += 1
    return "<br>".join(parts)


def format_benchmark_cell_html(op, bench_index):
    bids = []
    if op.get("benchmark_id"):
        bids.append(op["benchmark_id"])
    bids.extend(op.get("secondary_benchmark_ids", []))
    if not bids:
        return empty_cell_html()

    blocks = []
    for bid in bids:
        row = bench_index.get(bid)
        if not row:
            continue
        lines = render_benchmark_row_lines(
            row, include_ratio=True, show_fail_detail=False
        )
        suffix = row.get("name_suffix", "").strip()
        if suffix and len(bids) > 1:
            lines.insert(
                0, f'<em class="bench-variant">{html.escape(suffix.lstrip())}</em>'
            )
        blocks.append(join_benchmark_cell_lines(lines))

    return "<br><br>".join(blocks) if blocks else empty_cell_html()


def render_comparison_html(operations, categories, bench_index, source_resolver=None):
    parts = [
        "<section id=\"comparison\">",
        "<h1>tgen vs jngen — Feature Comparison</h1>",
        "<p>Comparison of non-trivial generation operations. "
        "See <a href=\"#benchmarks\">benchmarks</a> below.</p>",
    ]

    by_cat = {}
    for op in operations:
        by_cat.setdefault(op["category"], []).append(op)

    for cat_id, cat_label in categories.items():
        if cat_id not in by_cat:
            continue
        parts.append(f"<h2>{html.escape(cat_label)}</h2>")
        parts.append('<div class="table-scroll"><table class="comparison-table">')
        parts.append(
            "<colgroup>"
            '<col class="col-op">'
            '<col class="col-api">'
            '<col class="col-api">'
            '<col class="col-notes">'
            '<col class="col-bench">'
            "</colgroup>"
        )
        parts.append(comparison_table_header_row())
        for op in by_cat[cat_id]:
            if op.get("gallery_only"):
                continue
            tg = op.get("tgen", {})
            jg = op.get("jngen", {})
            jngen_cell = format_lib_api_cell_html(
                jg,
                lib="jngen",
                op_id=op["id"],
                source_resolver=source_resolver,
                category=cat_id,
            )
            tgen_cell = format_lib_api_cell_html(
                tg,
                lib="tgen",
                op_id=op["id"],
                source_resolver=source_resolver,
                category=cat_id,
            )

            notes = format_notes_html(tg, jg, op.get("notes", ""), op.get("exclusive"))
            bench = format_benchmark_cell_html(op, bench_index)
            notes_td_class = (
                "col-notes cell-empty" if is_empty_cell(notes) else "col-notes"
            )
            bench_td_class = (
                "col-bench cell-empty" if is_empty_cell(bench) else "col-bench"
            )

            parts.append(
                "<tr>"
                f"<td>{html.escape(op['name'])}</td>"
                f'<td class="{api_cell_td_class(jg, "jngen")}">{jngen_cell}</td>'
                f'<td class="{api_cell_td_class(tg, "tgen")}">{tgen_cell}</td>'
                f'<td class="{notes_td_class}">{notes}</td>'
                f'<td class="{bench_td_class}">{bench}</td>'
                "</tr>"
            )
        parts.append("</table></div>")
        if category_has_inferred(by_cat[cat_id]):
            parts.append(TABLE_INFERRED_FOOTNOTE_HTML)

    parts.extend(render_samples_section_html(operations, categories, source_resolver))
    parts.append("</section>")
    return "\n".join(parts)


def render_benchmarks_html(bench, source_resolver=None, repos=None):
    parts = [
        "<section id=\"benchmarks\">",
        "<h1>tgen vs jngen — Benchmarks</h1>",
    ]
    if not bench:
        parts.append("<p><em>No benchmark results yet. Run <code>make benchmark</code>.</em></p>")
        parts.append("</section>")
        return "\n".join(parts)

    vendors = bench.get("vendors", {})
    parts.extend([
        "<ul>",
        f"<li><strong>Compiler:</strong> "
        f"{html.escape(format_compiler_display(bench.get('compiler', '—')))}</li>",
        f"<li><strong>Flags:</strong> {html.escape(bench.get('flags', '—'))}</li>",
        f"<li><strong>Host:</strong> {html.escape(bench.get('hostname', '—'))}</li>",
    ])
    if vendors:
        parts.append(
            "<li><strong>Vendor commits:</strong> "
            f"{render_vendor_commits_html(vendors, repos)}</li>"
        )
    parts.extend([
        "</ul>",
        "<h2>Timing comparison</h2>",
        '<p class="bench-table-legend">'
        "Bar length is relative to the slower library per operation "
        "(<strong class=\"lib-label lib-jngen\">jngen</strong> vs "
        "<strong class=\"lib-label lib-tgen\">tgen</strong>). "
        "Ratio is colored by the faster library.</p>",
        '<div class="table-scroll"><table class="bench-table bench-table-timing">',
        "<colgroup>"
        '<col class="bench-col-op">'
        '<col class="bench-col-params">'
        '<col class="bench-col-comparison">'
        '<col class="bench-col-ratio">'
        "</colgroup>",
        "<tr><th>Operation</th><th>Parameters</th><th>Comparison</th>"
        '<th class="bench-col-ratio-header">Ratio (tgen/jngen)</th></tr>',
    ])

    shared = [
        r for r in bench.get("results", []) if benchmark_is_comparable(r)
    ]
    for row in shared:
        name = row.get("name", "") + row.get("name_suffix", "")
        params = row.get("params", "")
        comparison = "<br>".join(
            render_benchmark_row_lines(
                row, include_params=False, show_fail_detail=True
            )
        )
        source_url = None
        doc_url = None
        if source_resolver:
            bench_id = row.get("id")
            source_url = source_resolver.url_for_benchmark(bench_id, "tgen")
            doc_url = source_resolver.doc_url_for_benchmark(bench_id, "tgen")
        parts.append(
            "<tr>"
            f'<td class="bench-col-op">'
            f"{format_benchmark_name_html(name, source_url, doc_url)}</td>"
            f'<td class="bench-col-params">{format_params_html(params)}</td>'
            f'<td class="bench-col-comparison-cell">{comparison}</td>'
            f'{format_empty_aware_td(format_ratio_html(row), "bench-col-ratio-cell")}'
            "</tr>"
        )

    parts.append("</table></div>")

    tgen_only = [
        r
        for r in bench.get("results", [])
        if not r.get("compare_both") and r.get("tgen", {}).get("status") == "ok"
    ]
    if tgen_only:
        parts.extend([
            "<h2>tgen-only timings</h2>",
            '<div class="table-scroll"><table class="bench-table bench-table-tgen-only">',
            "<tr><th>Operation</th><th>Parameters</th><th>tgen</th></tr>",
        ])
        for row in tgen_only:
            name = row.get("name", "") + row.get("name_suffix", "")
            params = row.get("params", "")
            tg_ms = lib_timing_ms(row.get("tgen", {}))
            source_url = None
            doc_url = None
            if source_resolver:
                bench_id = row.get("id")
                source_url = source_resolver.url_for_benchmark(bench_id, "tgen")
                doc_url = source_resolver.doc_url_for_benchmark(bench_id, "tgen")
            parts.append(
                "<tr>"
                f'<td class="bench-col-op">'
                f"{format_benchmark_name_html(name, source_url, doc_url)}</td>"
                f'<td class="bench-col-params">{format_params_html(params)}</td>'
                f"<td>{html.escape(tg_ms)}</td>"
                "</tr>"
            )
        parts.append("</table></div>")

    parts.append("</section>")
    return "\n".join(parts)


def render_page_meta(bench, repos=None):
    if not bench:
        return ""
    vendors = bench.get("vendors", {})
    parts = [
        '<div class="page-meta">',
        f"<div><strong>Generated:</strong> "
        f"{html.escape(format_generated_at(bench.get('generated_at', '—')))}</div>",
    ]
    if vendors:
        parts.append(
            "<div><strong>Vendor commits:</strong> "
            f"{render_vendor_commits_html(vendors, repos)}</div>"
        )
    parts.append("</div>")
    return "\n".join(parts)


def render_html(comparison_body, benchmarks_body, page_meta=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>tgen vs jngen</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0f1117;
      --surface: #161b22;
      --border: #30363d;
      --text: #e6edf3;
      --muted: #8b949e;
      --link: #58a6ff;
      --link-hover: #79c0ff;
      --code-bg: #21262d;
      --th-bg: #1c2128;
      --gallery-bg: #161b22;
    }}
    body {{
      font-family: system-ui, sans-serif;
      max-width: 1100px;
      margin: 2rem auto;
      padding: 0 1rem;
      line-height: 1.5;
      background: var(--bg);
      color: var(--text);
    }}
    h1, h2 {{
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.3rem;
      color: var(--text);
    }}
    a {{ color: var(--link); }}
    a:hover {{ color: var(--link-hover); }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 0;
      font-size: 0.92rem;
      background: var(--surface);
    }}
    table.comparison-table {{
      table-layout: fixed;
    }}
    .table-scroll {{
      overflow-x: auto;
      margin: 1rem 0;
    }}
    th, td {{
      border: 1px solid var(--border);
      padding: 0.45rem 0.6rem;
      vertical-align: top;
      overflow-wrap: anywhere;
      word-break: break-word;
      min-width: 0;
    }}
    table.comparison-table .col-op {{ width: 11%; }}
    table.comparison-table .col-api {{ width: 23%; }}
    table.comparison-table.samples-table .col-op {{ width: 22%; }}
    table.comparison-table.samples-table .col-api {{ width: 39%; }}
    .api-uniformity,
    .api-complexity {{
      display: block;
      font-size: 0.85rem;
      margin-top: 0.2rem;
      line-height: 1.35;
    }}
    .api-complexity-line {{
      display: block;
    }}
    .api-complexity-line + .api-complexity-line {{
      margin-top: 0.2rem;
    }}
    .api-complexity-or {{
      display: block;
      margin-top: 0.25rem;
      color: var(--muted);
      font-size: 0.8rem;
      font-style: italic;
    }}
    .gallery-params {{ display: block; font-size: 0.85rem; color: var(--muted); margin-top: 0.2rem; }}
    .api-doc-line {{ display: block; font-size: 0.85rem; color: var(--muted); margin-top: 0.15rem; }}
    a.api-doc-link {{ color: var(--link); text-decoration: none; }}
    a.api-doc-link:hover, a.api-doc-link:focus-visible {{ text-decoration: underline; }}
    table.comparison-table .col-notes {{ width: 27%; }}
    table.comparison-table .col-bench {{ width: 16%; }}
    .uniform-val {{
      display: inline;
    }}
    .uniform-val.uniform-undocumented {{
      color: var(--muted);
      font-size: 0.85rem;
    }}
    .uniform-val.uniform-yes strong {{
      font-weight: 700;
      color: #a6e3a6;
    }}
    .uniform-val.uniform-no strong {{
      font-weight: 700;
      color: #f0c674;
    }}
    .inferred-mark {{
      color: #f85149;
      font-weight: 700;
    }}
    .table-footnote {{
      margin: 0.5rem 0 1.25rem;
      font-size: 0.85rem;
      color: var(--muted);
    }}
    hr.notes-sep {{
      border: 0;
      border-top: 1px solid var(--border);
      margin: 0.45rem 0;
    }}
    th {{
      background: var(--th-bg);
      text-align: left;
      color: var(--text);
    }}
    tr:nth-child(even) td {{ background: rgba(255, 255, 255, 0.02); }}
    td.col-api, th.col-api {{
      overflow: hidden;
      vertical-align: top;
    }}
    .api-cell {{
      width: 100%;
      min-width: 0;
    }}
    .api-cell-yes {{
      margin-bottom: 0.25rem;
    }}
    .api-code-box {{
      min-width: 0;
    }}
    .api-code-box .api-source-link {{
      display: block;
    }}
    td.col-api code,
    .api-code-box code {{
      display: block;
      max-width: 100%;
      white-space: pre-line;
      overflow-wrap: anywhere;
      word-break: break-word;
      line-height: 1.35;
      box-sizing: border-box;
      padding: 0.25rem 0.35rem;
    }}
    table.comparison-table td.col-api-jngen code {{
      color: #3fb950;
    }}
    table.comparison-table td.col-api-tgen code {{
      color: #58a6ff;
    }}
    code {{
      background: var(--code-bg);
      color: #f0883e;
      padding: 0.1rem 0.25rem;
      border-radius: 3px;
      font-size: 0.88em;
    }}
    strong {{ color: #ff7b72; }}
    .lib-label {{ font-weight: 700; }}
    .lib-label.lib-jngen {{ color: #3fb950; }}
    .lib-label.lib-tgen {{ color: #58a6ff; }}
    strong.complexity {{ font-weight: 700; color: #f0c674; }}
    strong.bench-ratio {{ font-weight: 700; }}
    strong.bench-ratio-jngen {{ color: #3fb950; }}
    strong.bench-ratio-tgen {{ color: #58a6ff; }}
    .bench-params {{ font-size: 0.85rem; color: var(--muted); }}
    .bench-table-legend {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 0.75rem; }}
    .bench-bars {{
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      width: 100%;
      min-width: 0;
    }}
    .bench-bar-row {{
      display: grid;
      grid-template-columns: 3.25rem minmax(0, 1fr);
      gap: 0.35rem 0.45rem;
      align-items: start;
    }}
    .bench-bar-body {{
      display: flex;
      flex-direction: column;
      gap: 0.12rem;
      min-width: 0;
    }}
    .bench-bar-label {{
      font-size: 0.74rem;
      font-weight: 700;
      line-height: 1.2;
      padding-top: 0.1rem;
    }}
    .bench-bar-label.lib-jngen {{ color: #3fb950; }}
    .bench-bar-label.lib-tgen {{ color: #58a6ff; }}
    .bench-bar-track {{
      height: 0.85rem;
      width: 100%;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 3px;
      overflow: hidden;
    }}
    .bench-bar-fill {{
      height: 100%;
      border-radius: 3px;
      min-width: 2px;
    }}
    .bench-bar-fill.lib-jngen {{ background: #3fb950; }}
    .bench-bar-fill.lib-tgen {{ background: #58a6ff; }}
    .bench-bar-time {{
      font-size: 0.78rem;
      color: var(--muted);
      text-align: right;
      font-variant-numeric: tabular-nums;
      line-height: 1.2;
    }}
    td.col-bench .bench-bars {{
      margin-top: 0.25rem;
    }}
    td.col-bench .bench-bars + .bench-params {{
      display: block;
      margin-top: 0.2rem;
    }}
    .bench-bar-fill-fail {{
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 100%;
      background: #da3633;
      border: 1px solid #ff7b72;
      box-shadow: 0 0 8px rgba(248, 81, 73, 0.45);
      box-sizing: border-box;
    }}
    .bench-bar-fill-fail.lib-jngen {{
      background: #f85149;
      box-shadow: 0 0 10px rgba(248, 81, 73, 0.65);
    }}
    .bench-fail-label {{
      color: #fff;
      font-weight: 800;
      font-size: 0.62rem;
      letter-spacing: 0.08em;
      line-height: 1;
      text-transform: uppercase;
      user-select: none;
      position: relative;
      top: 1px;
    }}
    .bench-fail-badge-inline {{
      display: inline-block;
      background: #f85149;
      color: #fff;
      font-weight: 800;
      font-size: 0.62rem;
      padding: 1px 5px;
      border-radius: 3px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      border: 1px solid #ff7b72;
      vertical-align: middle;
      line-height: 1.3;
    }}
    .bench-fail-detail {{
      color: #ff7b72;
      font-size: 0.72rem;
      line-height: 1.35;
      word-break: break-word;
    }}
    table.bench-table.bench-table-timing {{
      table-layout: fixed;
    }}
    table.bench-table.bench-table-timing .bench-col-op {{ width: 20%; }}
    table.bench-table.bench-table-timing .bench-col-params {{ width: 15%; }}
    table.bench-table.bench-table-timing .bench-col-comparison {{ width: 50%; }}
    table.bench-table.bench-table-timing .bench-col-ratio {{ width: 15%; }}
    table.bench-table.bench-table-timing th.bench-col-ratio-header,
    table.bench-table.bench-table-timing td.bench-col-ratio-cell {{
      vertical-align: middle;
      text-align: center;
    }}
    table.bench-table.bench-table-timing td.bench-col-comparison-cell {{
      min-width: 280px;
    }}
    table.bench-table.bench-table-timing td.bench-col-op code,
    table.bench-table.bench-table-tgen-only td.bench-col-op code {{
      color: #58a6ff;
    }}
    em {{ color: var(--muted); }}
    ul {{ color: var(--muted); }}
    ul strong {{ color: var(--text); }}
    table.samples-table th,
    table.samples-table td {{
      vertical-align: middle;
      text-align: center;
    }}
    table.samples-table td.col-api .api-cell {{
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    table.samples-table td.col-api .api-code-box {{
      width: fit-content;
      max-width: 100%;
      margin: 0 auto;
    }}
    table.samples-table td.col-api .api-code-box code {{
      text-align: center;
      display: block;
    }}
    table.samples-table td.col-api .api-doc-line,
    table.samples-table td.col-api .api-uniformity,
    table.samples-table td.col-api .api-complexity {{
      text-align: center;
      width: 100%;
      max-width: 420px;
    }}
    .sample-widget {{
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 0.45rem;
      width: 100%;
      max-width: 420px;
      margin: 0.65rem auto 0;
    }}
    table.samples-table td.col-api .sample-widget .sample-img {{
      display: block;
      flex: 1;
      width: auto;
      height: auto;
      min-width: 0;
      max-width: none;
      margin: 0;
    }}
    .sample-regen {{
      flex-shrink: 0;
      width: 2rem;
      height: 2rem;
      padding: 0;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--code-bg);
      color: var(--text);
      font-size: 1.15rem;
      line-height: 1;
      cursor: pointer;
    }}
    .sample-regen:hover,
    .sample-regen:focus-visible {{
      border-color: var(--link);
      color: var(--link);
      outline: none;
    }}
    table.samples-table td.col-api .gallery-params-stack {{
      margin: 0.35rem auto 0.15rem;
    }}
    a.api-source-link {{
      color: inherit;
      text-decoration: none;
    }}
    a.api-source-link:hover code,
    a.api-source-link:focus-visible code {{
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    td.cell-unavailable {{
      vertical-align: middle;
      text-align: center;
      color: var(--muted);
    }}
    td.cell-unavailable strong {{
      font-size: 1.05rem;
    }}
    td.cell-empty {{
      vertical-align: middle;
      text-align: center;
      color: var(--muted);
    }}
    nav {{
      margin-bottom: 1.5rem;
      padding: 0.75rem 1rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
    }}
    nav a {{ margin-right: 1rem; }}
    .page-meta {{
      margin-bottom: 1.5rem;
      padding: 0.75rem 1rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .page-meta strong {{ color: var(--text); }}
    .page-meta code {{
      background: var(--code-bg);
      padding: 0.1rem 0.35rem;
      border-radius: 4px;
      font-size: 0.88em;
    }}
    .page-meta div + div {{ margin-top: 0.35rem; }}
  </style>
</head>
<body>
  {page_meta}
  <nav>
    <a href="#comparison">Feature comparison</a>
    <a href="#benchmarks">Benchmarks</a>
    <a href="https://github.com/brunomaletta/tgen_vs_jngen">GitHub</a>
  </nav>
  {comparison_body}
  {benchmarks_body}
  <script>
  (function () {{
    const PREFETCH_AHEAD = 5;
    const prefetched = new Set();

    function equalizeApiCodeBoxes() {{
      document.querySelectorAll("table.comparison-table:not(.samples-table)").forEach(function (table) {{
        table.querySelectorAll("tr").forEach(function (row) {{
          const boxes = Array.from(
            row.querySelectorAll("td.col-api:not(.cell-unavailable) .api-code-box")
          );
          if (boxes.length < 2) return;
          boxes.forEach(function (box) {{
            box.style.minHeight = "";
          }});
          let max = 0;
          boxes.forEach(function (box) {{
            max = Math.max(max, box.getBoundingClientRect().height);
          }});
          if (max <= 0) return;
          const height = Math.ceil(max) + "px";
          boxes.forEach(function (box) {{
            box.style.minHeight = height;
          }});
        }});
      }});
    }}

    let resizeTimer;
    window.addEventListener("resize", function () {{
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(equalizeApiCodeBoxes, 100);
    }});
    equalizeApiCodeBoxes();
    if (document.fonts && document.fonts.ready) {{
      document.fonts.ready.then(equalizeApiCodeBoxes);
    }}

    function runWhenIdle(fn) {{
      if (typeof requestIdleCallback === "function") {{
        requestIdleCallback(fn, {{ timeout: 4000 }});
      }} else {{
        setTimeout(fn, 250);
      }}
    }}

    function sampleUrl(prefix, seed) {{
      return prefix + "_s" + seed + ".svg";
    }}

    function prefetchVariant(widget, index) {{
      const seeds = JSON.parse(widget.dataset.seeds);
      const prefix = widget.dataset.prefix;
      const i = ((index % seeds.length) + seeds.length) % seeds.length;
      const url = sampleUrl(prefix, seeds[i]);
      if (prefetched.has(url)) return;
      prefetched.add(url);
      const img = new Image();
      img.src = url;
    }}

    function prefetchAhead(widget, fromIndex, stagger) {{
      if (!stagger) {{
        for (let off = 1; off <= PREFETCH_AHEAD; off++) {{
          prefetchVariant(widget, fromIndex + off);
        }}
        return;
      }}
      let off = 1;
      function next() {{
        if (off > PREFETCH_AHEAD) return;
        prefetchVariant(widget, fromIndex + off);
        off += 1;
        runWhenIdle(next);
      }}
      runWhenIdle(next);
    }}

    function scheduleBackgroundPrefetch(widget) {{
      if (widget.dataset.prefetchScheduled === "1") return;
      widget.dataset.prefetchScheduled = "1";
      runWhenIdle(function () {{
        const start = parseInt(widget.dataset.index || "0", 10);
        prefetchAhead(widget, start, true);
      }});
    }}

    function setVariant(widget, index) {{
      const seeds = JSON.parse(widget.dataset.seeds);
      const prefix = widget.dataset.prefix;
      const img = widget.querySelector("img.sample-img");
      const i = ((index % seeds.length) + seeds.length) % seeds.length;
      widget.dataset.index = String(i);
      img.src = sampleUrl(prefix, seeds[i]);
      prefetchAhead(widget, i, false);
    }}

    const widgets = document.querySelectorAll(".sample-widget");
    if (typeof IntersectionObserver === "function") {{
      const observer = new IntersectionObserver(function (entries) {{
        entries.forEach(function (entry) {{
          if (!entry.isIntersecting) return;
          scheduleBackgroundPrefetch(entry.target);
          observer.unobserve(entry.target);
        }});
      }}, {{ rootMargin: "120px" }});
      widgets.forEach(function (widget) {{
        observer.observe(widget);
      }});
    }} else {{
      window.addEventListener("load", function () {{
        widgets.forEach(scheduleBackgroundPrefetch);
      }});
    }}

    widgets.forEach(function (widget) {{
      const btn = widget.querySelector(".sample-regen");
      if (!btn) return;
      btn.addEventListener("click", function (event) {{
        const seeds = JSON.parse(widget.dataset.seeds);
        let index = parseInt(widget.dataset.index || "0", 10);
        if (event.shiftKey) {{
          if (seeds.length <= 1) return;
          do {{
            index = Math.floor(Math.random() * seeds.length);
          }} while (index === parseInt(widget.dataset.index || "0", 10));
        }} else {{
          index = (index + 1) % seeds.length;
        }}
        setVariant(widget, index);
      }});
    }});
  }})();
  </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml", default="docs/operations.yaml")
    parser.add_argument("--json", default="docs/benchmark_results.json")
    parser.add_argument("--out-dir", default="docs")
    args = parser.parse_args()

    meta = load_yaml(args.yaml)
    bench = load_json(args.json)
    bench_index = build_benchmark_index(bench)
    categories = meta.get("categories", {})
    operations = meta.get("operations", [])

    api_sources = load_api_sources()
    tgen_index = build_tgen_source_index()
    benchmark_to_op = build_benchmark_to_op_map(operations, api_sources)
    op_categories = {op["id"]: op.get("category") for op in operations}
    source_resolver = ApiSourceResolver(
        api_sources,
        tgen_index,
        benchmark_to_op=benchmark_to_op,
        op_categories=op_categories,
    )

    comparison_html = render_comparison_html(
        operations, categories, bench_index, source_resolver
    )
    repos = api_sources.get("repos", {})
    benchmarks_html = render_benchmarks_html(bench, source_resolver, repos)
    os.makedirs(args.out_dir, exist_ok=True)
    page_meta = render_page_meta(bench, repos)
    page_html = render_html(comparison_html, benchmarks_html, page_meta)
    with open(os.path.join(args.out_dir, "comparison.html"), "w", encoding="utf-8") as f:
        f.write(page_html)

    print(f"Wrote {args.out_dir}/comparison.html")


if __name__ == "__main__":
    main()
