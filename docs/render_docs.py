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
    default_xml_dir,
    local_source_url,
)

try:
    import yaml
except ImportError:
    sys.stderr.write("render_docs.py: install PyYAML (pip install pyyaml)\n")
    sys.exit(1)


O_COMPLEXITY_RE = re.compile(r"O\([^)]+\)")
LIB_MENTION_RE = re.compile(r"\b(jngen|tgen)(?=\s)")


def bold_complexities_md(text):
    if not text:
        return text
    return O_COMPLEXITY_RE.sub(r"**\g<0>**", text)


def bold_complexities_html(text):
    if not text:
        return text
    out = []
    last = 0
    for match in O_COMPLEXITY_RE.finditer(text):
        out.append(html.escape(text[last : match.start()]))
        out.append(
            f'<strong class="complexity">{html.escape(match.group(0))}</strong>'
        )
        last = match.end()
    out.append(html.escape(text[last:]))
    return "".join(out)


def format_lib_part_md(part):
    return bold_complexities_md(highlight_lib_labels_md(part))


def format_lib_part_html(part):
    if part.startswith("jngen: "):
        label = '<strong class="lib-label lib-jngen">jngen:</strong> '
        rest = part[7:]
    elif part.startswith("tgen: "):
        label = '<strong class="lib-label lib-tgen">tgen:</strong> '
        rest = part[6:]
    else:
        return bold_complexities_html(part)
    return label + bold_complexities_html(rest)


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
    "graph_weighted": "doc/generic_graph.md",
    "tree_rooted_output": "doc/printers.md",
    "structured_output": "doc/printers.md",
    "testlib_integration": "doc/random.md",
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


def build_tgen_source_index(xml_dir=None):
    xml_dir = xml_dir or default_xml_dir(ROOT_DIR)
    index = TgenSourceIndex(xml_dir)
    if len(index) == 0:
        sys.stderr.write(
            "render_docs: tgen Doxygen XML missing or empty — run "
            "'cd vendor/tgen && make doc-prepare' (API links for tgen will be omitted)\n"
        )
        return None
    return index


def yes_no(val):
    if val is True:
        return "Yes"
    if val is False:
        return "No"
    return val or "—"


def uniform_label(val):
    if not val:
        return "—"
    inferred = val.endswith(" (inferred)")
    base = val[:-11] if inferred else val
    mapping = {
        "uniform": "Uniform",
        "non-uniform": "Non\u2011uniform",
        "undocumented": "Undocumented",
        "varies": "Varies",
    }
    label = mapping.get(base, base)
    if inferred:
        return f"{label} (inferred)"
    return label


def lib_label(text, lib):
    return f"{lib}: {text}"


# Ops where uniformity is N/A (deterministic construction or not random sampling).
NO_DEFAULT_UNIFORM_OPS = frozenset({
    "tree_named_shapes",
    "hack_unsigned_polynomial_hash",
    "hack_mt19937_xor_hash",
    "hack_rotating_calipers",
    "geometry_svg_drawer",
})

NO_DEFAULT_UNIFORM_CATEGORIES = frozenset({"hacks", "other"})


def effective_uniform(lib_info, category, op_id):
    if not lib_info.get("has"):
        return None
    uniform = lib_info.get("uniform")
    if uniform:
        return uniform
    if category in NO_DEFAULT_UNIFORM_CATEGORIES:
        return None
    if op_id in NO_DEFAULT_UNIFORM_OPS:
        return None
    return "undocumented"


def lib_uniformity_parts(tg, jg, category, op_id):
    parts = []
    jg_u = effective_uniform(jg, category, op_id)
    tg_u = effective_uniform(tg, category, op_id)
    if jg_u:
        parts.append(lib_label(uniform_label(jg_u), "jngen"))
    if tg_u:
        parts.append(lib_label(uniform_label(tg_u), "tgen"))
    return parts


def lib_complexity_parts(tg, jg):
    parts = []
    if jg.get("complexity"):
        parts.append(lib_label(jg["complexity"], "jngen"))
    if tg.get("complexity"):
        parts.append(lib_label(tg["complexity"], "tgen"))
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


def highlight_lib_names_html(text):
    if not text:
        return text
    out = []
    last = 0
    for match in LIB_MENTION_RE.finditer(text):
        out.append(html.escape(text[last : match.start()]))
        lib = match.group(1)
        out.append(f'<strong class="lib-label lib-{lib}">{lib}</strong>')
        last = match.end()
    out.append(html.escape(text[last:]))
    return "".join(out)


def format_notes_text_md(text):
    return bold_complexities_md(highlight_lib_names_md(text))


def format_notes_text_html(text):
    if not text:
        return text
    out = []
    last = 0
    for match in O_COMPLEXITY_RE.finditer(text):
        out.append(highlight_lib_names_html(text[last : match.start()]))
        out.append(
            f'<strong class="complexity">{html.escape(match.group(0))}</strong>'
        )
        last = match.end()
    out.append(highlight_lib_names_html(text[last:]))
    return "".join(out)


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


def format_lib_parts_md(parts):
    if not parts:
        return ""
    return "<br>".join(format_lib_part_md(part) for part in parts)


def format_lib_parts_html(parts):
    if not parts:
        return ""
    return "<br>".join(format_lib_part_html(part) for part in parts)


def format_uniformity_md(tg, jg, category, op_id):
    parts = lib_uniformity_parts(tg, jg, category, op_id)
    if not parts:
        return "—"
    rows = []
    for part in parts:
        if part.startswith("jngen: "):
            rows.append(f"**jngen:**<br>{part[7:]}")
        elif part.startswith("tgen: "):
            rows.append(f"**tgen:**<br>{part[6:]}")
        else:
            rows.append(format_lib_part_md(part))
    return "<br>".join(rows)


def format_uniformity_html(tg, jg, category, op_id):
    parts = lib_uniformity_parts(tg, jg, category, op_id)
    if not parts:
        return "—"
    rows = []
    for part in parts:
        if part.startswith("jngen: "):
            label = '<strong class="lib-label lib-jngen">jngen:</strong>'
            rest = part[7:]
        elif part.startswith("tgen: "):
            label = '<strong class="lib-label lib-tgen">tgen:</strong>'
            rest = part[6:]
        else:
            rows.append(bold_complexities_html(part))
            continue
        rows.append(
            '<div class="uniform-entry">'
            f"{label}"
            f'<span class="uniform-val">{html.escape(rest)}</span>'
            "</div>"
        )
    return "".join(rows)


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
    complexity_parts = lib_complexity_parts(tg, jg)
    if complexity_parts:
        blocks.append(format_lib_parts_md(complexity_parts))
    if extra_notes:
        if complexity_parts:
            blocks.append(NOTES_SEP_MD)
        blocks.append(format_notes_text_md(extra_notes))
    if show_exclusive_badge(tg, jg, exclusive):
        blocks.append(format_exclusive_md(exclusive))
    return join_notes_blocks(blocks)


def format_notes_html(tg, jg, extra_notes, exclusive=None):
    blocks = []
    complexity_parts = lib_complexity_parts(tg, jg)
    if complexity_parts:
        blocks.append(format_lib_parts_html(complexity_parts))
    if extra_notes:
        if complexity_parts:
            blocks.append(NOTES_SEP_HTML)
        blocks.append(format_notes_text_html(extra_notes))
    if show_exclusive_badge(tg, jg, exclusive):
        blocks.append(format_exclusive_html(exclusive))
    return join_notes_blocks(blocks)


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


def format_api_html(api, source_url=None, doc_url=None):
    code = f"<code>{wrap_api_html(api)}</code>"
    if source_url:
        code = (
            f'<a class="api-source-link" href="{html.escape(source_url)}" '
            f'target="_blank" rel="noopener">{code}</a>'
        )
    return code + format_doc_line_html(doc_url)


def format_doc_line_html(doc_url):
    if doc_url:
        return (
            f'<br><span class="api-doc-line">'
            f'<a class="api-doc-link" href="{html.escape(doc_url)}" '
            f'target="_blank" rel="noopener">Docs</a>'
            f"</span>"
        )
    return f'<br><span class="api-doc-line"><em>Undocumented</em></span>'


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


def format_lib_api_cell_html(lib_info, lib=None, op_id=None, source_resolver=None):
    if not lib_info.get("has"):
        return "<strong>No</strong>"
    cell = "Yes"
    if lib_info.get("api"):
        api = lib_info["api"]
        if lib == "tgen":
            api = normalize_tgen_api(api)
        source_url = None
        doc_url = None
        if source_resolver and op_id and lib:
            source_url = source_resolver.url(op_id, lib)
            doc_url = source_resolver.doc_url(op_id, lib)
        cell += f"<br>{format_api_html(api, source_url, doc_url)}"
    return cell


def wrap_benchmark_name(name):
    return wrap_api(name)


def wrap_params(params):
    return params


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


def format_params_html(params):
    return wrap_params(html.escape(params))


def sample_svg_path(op_id, lib):
    return f"gallery/{op_id}_{lib}.svg"


def sample_svg_exists(op_id, lib):
    return os.path.isfile(os.path.join("docs", sample_svg_path(op_id, lib)))


def _sample_stack_ids(op):
    return op.get("gallery_stack") or []


def _append_sample_images_html(cell, op, lib):
    stack = _sample_stack_ids(op)
    if stack:
        top_params = op.get("gallery_stack_top_params", "")
        mid_params = op.get("gallery_stack_params", "")
        for i, sid in enumerate(stack):
            if i == 0 and top_params:
                cell += (
                    f'<span class="gallery-params gallery-params-stack">'
                    f"{html.escape(top_params)}</span>"
                )
            if sample_svg_exists(sid, lib):
                path = sample_svg_path(sid, lib)
                cell += (
                    f'<img class="sample-img" src="{html.escape(path)}" '
                    f'alt="{html.escape(lib)} sample">'
                )
            if i == 0 and len(stack) > 1 and mid_params:
                cell += (
                    f'<span class="gallery-params gallery-params-stack">'
                    f"{html.escape(mid_params)}</span>"
                )
        return cell
    if sample_svg_exists(op["id"], lib):
        path = sample_svg_path(op["id"], lib)
        cell += (
            f'<img class="sample-img" src="{html.escape(path)}" '
            f'alt="{html.escape(lib)} sample">'
        )
    return cell


def format_sample_cell_html(op_id, op, lib_info, lib, source_resolver=None):
    cell = format_lib_api_cell_html(
        lib_info, lib=lib, op_id=op_id, source_resolver=source_resolver
    )
    params = op.get("gallery_params", "")
    if params and lib_info.get("has") and not _sample_stack_ids(op):
        cell += (
            f'<br><span class="gallery-params">{html.escape(params)}</span>'
        )
    if lib_info.get("has"):
        cell = _append_sample_images_html(cell, op, lib)
    return cell


def api_cell_td_class(lib_info):
    if not lib_info.get("has"):
        return "col-api cell-unavailable"
    return "col-api"


def sample_cell_td_class(op, lib_info, lib):
    stack = _sample_stack_ids(op)
    if stack:
        if any(sample_svg_exists(sid, lib) for sid in stack):
            return "col-api sample-has-visual"
    elif sample_svg_exists(op["id"], lib):
        return "col-api sample-has-visual"
    if not lib_info.get("has"):
        return "col-api cell-unavailable"
    return "col-api"


def comparison_table_header_row():
    return (
        "<tr><th>Operation</th>"
        '<th class="col-api"><strong class="lib-label lib-jngen">jngen</strong></th>'
        '<th class="col-api"><strong class="lib-label lib-tgen">tgen</strong></th>'
        "<th>Uniformity</th><th>Complexity / notes</th><th>Benchmark</th></tr>"
    )


def sample_table_header_row():
    return (
        '<tr><th class="col-op sample-op">Operation</th>'
        '<th class="col-api"><strong class="lib-label lib-jngen">jngen</strong></th>'
        '<th class="col-api"><strong class="lib-label lib-tgen">tgen</strong></th></tr>'
    )


def geometry_sample_operations(operations):
    return [
        op
        for op in operations
        if op.get("visualize") and not op.get("gallery_only")
    ]


def render_geometry_samples_html(operations, source_resolver=None):
    ops = geometry_sample_operations(operations)
    if not ops:
        return []
    parts = [
        "<h3>Samples</h3>",
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
                f'{format_sample_cell_html(oid, op, op.get("jngen", {}), "jngen", source_resolver)}</td>'
                f'<td class="{sample_cell_td_class(op, op.get("tgen", {}), "tgen")}">'
                f'{format_sample_cell_html(oid, op, op.get("tgen", {}), "tgen", source_resolver)}</td>'
            "</tr>"
        )
    parts.append("</table></div>")
    return parts


def fmt_ms(ms):
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


def bench_ratio(row):
    jg_ms = lib_median_ms_raw(row.get("jngen", {}))
    tg_ms = lib_median_ms_raw(row.get("tgen", {}))
    if jg_ms is None or tg_ms is None or jg_ms <= 0:
        return None
    return tg_ms / jg_ms


def format_ratio_html(row):
    ratio = bench_ratio(row)
    if ratio is None:
        return "—"
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


def format_benchmark_cell_html(op, bench_index):
    bid = op.get("benchmark_id")
    if not bid:
        return "—"

    row = bench_index.get(bid)
    if not row:
        return "—"

    lines = []
    if row.get("compare_both"):
        jg_ms = lib_median_ms_raw(row.get("jngen", {}))
        tg_ms = lib_median_ms_raw(row.get("tgen", {}))
        bars = render_bench_bars_html(jg_ms, tg_ms, show_times=True)
        if bars != "—":
            lines.append(bars)
        else:
            lines.append(
                '<strong class="lib-label lib-jngen">jngen:</strong> '
                + html.escape(lib_timing_ms(row.get("jngen", {})))
            )
            lines.append(
                '<strong class="lib-label lib-tgen">tgen:</strong> '
                + html.escape(lib_timing_ms(row.get("tgen", {})))
            )
        if benchmark_is_comparable(row) and bench_ratio(row) is not None:
            lines.append(format_ratio_html(row))
        elif not benchmark_is_comparable(row):
            lines.append(
                '<em class="bench-params">different n — not comparable</em>'
            )
    else:
        lines.append(
            '<strong class="lib-label lib-tgen">tgen:</strong> '
            + html.escape(lib_timing_ms(row.get("tgen", {})))
        )

    params = row.get("params", "")
    if params:
        lines.append(f'<span class="bench-params">{html.escape(params)}</span>')

    return "<br>".join(lines)


def render_comparison_html(operations, categories, bench_index, source_resolver=None):
    parts = [
        "<section id=\"comparison\">",
        "<h1>tgen vs jngen — Feature Comparison</h1>",
        f"<p><em>Generated {html.escape(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}</em></p>",
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
            '<col class="col-uni">'
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
                jg, lib="jngen", op_id=op["id"], source_resolver=source_resolver
            )
            tgen_cell = format_lib_api_cell_html(
                tg, lib="tgen", op_id=op["id"], source_resolver=source_resolver
            )

            uni = format_uniformity_html(tg, jg, cat_id, op["id"])
            notes = format_notes_html(tg, jg, op.get("notes", ""), op.get("exclusive"))
            bench = format_benchmark_cell_html(op, bench_index)

            parts.append(
                "<tr>"
                f"<td>{html.escape(op['name'])}</td>"
                f'<td class="{api_cell_td_class(jg)}">{jngen_cell}</td>'
                f'<td class="{api_cell_td_class(tg)}">{tgen_cell}</td>'
                f'<td class="{"col-uni cell-unavailable" if uni == "—" else "col-uni"}">{uni}</td>'
                f'<td class="col-notes">{notes}</td>'
                f'<td class="{"col-bench cell-unavailable" if bench == "—" else "col-bench"}">{bench}</td>'
                "</tr>"
            )
        parts.append("</table></div>")
        if cat_id == "geometry":
            parts.extend(render_geometry_samples_html(operations, source_resolver))

    parts.append("</section>")
    return "\n".join(parts)


def render_benchmarks_html(bench, source_resolver=None):
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
        f"<li><strong>Generated:</strong> {html.escape(bench.get('generated_at', '—'))}</li>",
        f"<li><strong>Compiler:</strong> {html.escape(bench.get('compiler', '—'))}</li>",
        f"<li><strong>Flags:</strong> {html.escape(bench.get('flags', '—'))}</li>",
        f"<li><strong>Host:</strong> {html.escape(bench.get('hostname', '—'))}</li>",
    ])
    if vendors:
        parts.append(
            "<li><strong>Vendor commits:</strong> "
            f"tgen <code>{html.escape(vendors.get('tgen', '—'))}</code>, "
            f"jngen <code>{html.escape(vendors.get('jngen', '—'))}</code></li>"
        )
    parts.extend([
        "</ul>",
        "<h2>Timing comparison</h2>",
        '<p class="bench-table-legend">'
        "Bar length is relative to the slower library per operation "
        "(<span class=\"lib-label lib-jngen\">jngen</span> vs "
        "<span class=\"lib-label lib-tgen\">tgen</span>). "
        "Ratio is colored by the faster library.</p>",
        '<div class="table-scroll"><table class="bench-table">',
        "<tr><th>Operation</th><th>Parameters</th><th>Comparison</th>"
        "<th>Ratio (tgen/jngen)</th></tr>",
    ])

    shared = [
        r for r in bench.get("results", []) if benchmark_is_comparable(r)
    ]
    for row in shared:
        name = row.get("name", "") + row.get("name_suffix", "")
        params = row.get("params", "")
        jg_ms = lib_median_ms_raw(row.get("jngen", {}))
        tg_ms = lib_median_ms_raw(row.get("tgen", {}))
        bars = render_bench_bars_html(jg_ms, tg_ms, show_times=True)
        source_url = None
        doc_url = None
        if source_resolver:
            bench_id = row.get("id")
            source_url = source_resolver.url_for_benchmark(bench_id, "tgen")
            doc_url = source_resolver.doc_url_for_benchmark(bench_id, "tgen")
        parts.append(
            "<tr>"
            f"<td>{format_benchmark_name_html(name, source_url, doc_url)}</td>"
            f"<td>{format_params_html(params)}</td>"
            f"<td>{bars}</td>"
            f"<td>{format_ratio_html(row)}</td>"
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
            '<div class="table-scroll"><table class="bench-table">',
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
                f"<td>{format_benchmark_name_html(name, source_url, doc_url)}</td>"
                f"<td>{format_params_html(params)}</td>"
                f"<td>{html.escape(tg_ms)}</td>"
                "</tr>"
            )
        parts.append("</table></div>")

    parts.append("</section>")
    return "\n".join(parts)


def render_page_meta(bench):
    if not bench:
        return ""
    vendors = bench.get("vendors", {})
    parts = [
        '<div class="page-meta">',
        f"<div><strong>Generated:</strong> {html.escape(bench.get('generated_at', '—'))}</div>",
    ]
    if vendors:
        parts.append(
            "<div><strong>Vendor commits:</strong> "
            f"tgen <code>{html.escape(vendors.get('tgen', '—'))}</code>, "
            f"jngen <code>{html.escape(vendors.get('jngen', '—'))}</code></div>"
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
    table.comparison-table .col-api {{ width: 15%; }}
    table.comparison-table.samples-table .col-op {{ width: 22%; }}
    table.comparison-table.samples-table .col-api {{ width: 39%; }}
    .gallery-params {{ display: block; font-size: 0.85rem; color: var(--muted); margin-top: 0.2rem; }}
    .api-doc-line {{ display: block; font-size: 0.85rem; color: var(--muted); margin-top: 0.15rem; }}
    a.api-doc-link {{ color: var(--link); text-decoration: none; }}
    a.api-doc-link:hover, a.api-doc-link:focus-visible {{ text-decoration: underline; }}
    table.comparison-table .col-uni {{ width: 13%; }}
    table.comparison-table .col-notes {{ width: 30%; }}
    table.comparison-table .col-bench {{ width: 16%; }}
    td.col-uni, th.col-uni {{
      overflow: hidden;
      word-break: normal;
      overflow-wrap: break-word;
    }}
    .uniform-entry + .uniform-entry {{
      margin-top: 0.45rem;
    }}
    .uniform-entry .lib-label {{
      display: block;
    }}
    .uniform-val {{
      display: block;
      margin-top: 0.1rem;
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
    }}
    td.col-api code {{
      display: block;
      max-width: 100%;
      white-space: pre-line;
      overflow-wrap: anywhere;
      word-break: break-word;
      line-height: 1.35;
      box-sizing: border-box;
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
    strong.lib-label.lib-jngen {{ color: #3fb950; }}
    strong.lib-label.lib-tgen {{ color: #58a6ff; }}
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
      transition: width 0.15s ease;
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
    table.bench-table td:nth-child(3) {{
      min-width: 140px;
    }}
    em {{ color: var(--muted); }}
    ul {{ color: var(--muted); }}
    ul strong {{ color: var(--text); }}
    table.samples-table th,
    table.samples-table td {{
      vertical-align: middle;
      text-align: center;
    }}
    table.samples-table td.col-api code {{
      display: inline-block;
      text-align: left;
      margin: 0 auto;
    }}
    table.samples-table td.col-api img.sample-img {{
      display: block;
      width: 100%;
      max-width: 420px;
      margin: 0.65rem auto 0;
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
    benchmarks_html = render_benchmarks_html(bench, source_resolver)

    os.makedirs(args.out_dir, exist_ok=True)
    page_meta = render_page_meta(bench)
    page_html = render_html(comparison_html, benchmarks_html, page_meta)
    with open(os.path.join(args.out_dir, "comparison.html"), "w", encoding="utf-8") as f:
        f.write(page_html)

    print(f"Wrote {args.out_dir}/comparison.html")


if __name__ == "__main__":
    main()
