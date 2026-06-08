#!/usr/bin/env python3
"""Generate comparison.md, benchmarks.md, and comparison.html from YAML + JSON."""

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    sys.stderr.write("render_docs.py: install PyYAML (pip install pyyaml)\n")
    sys.exit(1)


O_COMPLEXITY_RE = re.compile(r"O\([^)]+\)")


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


def yes_no(val):
    if val is True:
        return "Yes"
    if val is False:
        return "No"
    return val or "—"


def uniform_label(val):
    if not val:
        return "—"
    mapping = {
        "uniform": "Uniform",
        "non-uniform": "Non-uniform",
        "undocumented": "Undocumented",
        "varies": "Varies",
    }
    return mapping.get(val, val)


def lib_label(text, lib):
    return f"{lib}: {text}"


def lib_uniformity_parts(tg, jg):
    parts = []
    if jg.get("has") and jg.get("uniform"):
        parts.append(lib_label(uniform_label(jg["uniform"]), "jngen"))
    if tg.get("has") and tg.get("uniform"):
        parts.append(lib_label(uniform_label(tg["uniform"]), "tgen"))
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


def format_lib_parts_md(parts):
    if not parts:
        return ""
    return "<br>".join(format_lib_part_md(part) for part in parts)


def format_lib_parts_html(parts):
    if not parts:
        return ""
    return "<br>".join(format_lib_part_html(part) for part in parts)


def format_uniformity_md(tg, jg):
    parts = lib_uniformity_parts(tg, jg)
    return format_lib_parts_md(parts) if parts else "—"


def format_uniformity_html(tg, jg):
    parts = lib_uniformity_parts(tg, jg)
    return format_lib_parts_html(parts) if parts else "—"


def format_notes_md(tg, jg, extra_notes):
    blocks = []
    complexity_parts = lib_complexity_parts(tg, jg)
    if complexity_parts:
        blocks.append(format_lib_parts_md(complexity_parts))
    if extra_notes:
        blocks.append(bold_complexities_md(extra_notes))
    return "<br>".join(blocks) if blocks else "—"


def format_notes_html(tg, jg, extra_notes):
    blocks = []
    complexity_parts = lib_complexity_parts(tg, jg)
    if complexity_parts:
        blocks.append(format_lib_parts_html(complexity_parts))
    if extra_notes:
        blocks.append(bold_complexities_html(extra_notes))
    return "<br>".join(blocks) if blocks else "—"


API_WRAP_MAX_LEN = 38


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
    """Break API strings at :: and before chained calls; keep identifiers intact."""
    if len(api) <= max_len:
        return api

    if "::" in api:
        parts = api.split("::")
        merged = []
        current = parts[0]
        for segment in parts[1:]:
            candidate = current + "::" + segment
            if len(candidate) <= max_len:
                current = candidate
            else:
                merged.append(current)
                current = segment
        merged.append(current)
        if len(merged) > 1:
            return "<br>".join(wrap_api_line(line, max_len) for line in merged)

    return wrap_api_line(api, max_len)


def wrap_api_html(api):
    return wrap_api(html.escape(api))


def format_api_md(api):
    return f"<code>{wrap_api(api)}</code>"


def format_api_html(api):
    return f"<code>{wrap_api_html(api)}</code>"


def format_lib_api_cell_md(lib_info):
    if not lib_info.get("has"):
        return "**No**"
    cell = "Yes"
    if lib_info.get("api"):
        cell += f"<br>{format_api_md(lib_info['api'])}"
    return cell


def format_lib_api_cell_html(lib_info):
    if not lib_info.get("has"):
        return "<strong>No</strong>"
    cell = "Yes"
    if lib_info.get("api"):
        cell += f"<br>{format_api_html(lib_info['api'])}"
    return cell


def wrap_benchmark_name(name):
    return wrap_api(name)


def wrap_params(params):
    return params


def format_benchmark_name_md(name):
    return f"<code>{wrap_benchmark_name(name)}</code>"


def format_benchmark_name_html(name):
    return f"<code>{wrap_api_html(name)}</code>"


def format_params_md(params):
    return wrap_params(params)


def format_params_html(params):
    return wrap_params(html.escape(params))


def sample_svg_path(op_id, lib):
    return f"gallery/{op_id}_{lib}.svg"


def sample_svg_exists(op_id, lib):
    return os.path.isfile(os.path.join("docs", sample_svg_path(op_id, lib)))


def format_sample_cell_md(op_id, lib_info, lib):
    cell = format_lib_api_cell_md(lib_info)
    if sample_svg_exists(op_id, lib):
        path = sample_svg_path(op_id, lib)
        cell += f'<br><img src="{path}" alt="{lib} sample">'
    return cell


def format_sample_cell_html(op_id, lib_info, lib):
    cell = format_lib_api_cell_html(lib_info)
    if sample_svg_exists(op_id, lib):
        path = sample_svg_path(op_id, lib)
        cell += (
            f'<img class="sample-img" src="{html.escape(path)}" '
            f'alt="{html.escape(lib)} sample">'
        )
    return cell


def sample_cell_td_class(op_id, lib_info, lib):
    if sample_svg_exists(op_id, lib):
        return "col-api sample-has-visual"
    if not lib_info.get("has"):
        return "col-api sample-unavailable"
    return "col-api"


def geometry_sample_operations(operations):
    return [op for op in operations if op.get("visualize")]


def render_geometry_samples_md(operations):
    ops = geometry_sample_operations(operations)
    if not ops:
        return []
    lines = [
        "### Samples",
        "",
        "Visual output for the geometry operations above "
        "(seed **42**, coordinates in **[0, 1000]**; **n = 80** except "
        "simple polygon through points, which uses a **10×10 rectangular grid**).",
        "",
        "| Operation | jngen | tgen |",
        "|-----------|-------|------|",
    ]
    for op in ops:
        oid = op["id"]
        lines.append(
            f"| {op['name']} | "
            f"{format_sample_cell_md(oid, op.get('jngen', {}), 'jngen')} | "
            f"{format_sample_cell_md(oid, op.get('tgen', {}), 'tgen')} |"
        )
    lines.append("")
    return lines


def render_geometry_samples_html(operations):
    ops = geometry_sample_operations(operations)
    if not ops:
        return []
    parts = [
        "<h3>Samples</h3>",
        "<p>Visual output for the geometry operations above "
        "(seed <strong>42</strong>, coordinates in <strong>[0, 1000]</strong>; "
        "<strong>n = 80</strong> except simple polygon through points, which uses a "
        "<strong>10×10 rectangular grid</strong>).</p>",
        '<div class="table-scroll"><table class="comparison-table samples-table">',
        "<colgroup>"
        '<col class="col-op">'
        '<col class="col-api">'
        '<col class="col-api">'
        "</colgroup>",
        '<tr><th class="col-op sample-op">Operation</th>'
        '<th class="col-api">jngen</th>'
        '<th class="col-api">tgen</th></tr>',
    ]
    for op in ops:
        oid = op["id"]
        parts.append(
            "<tr>"
            f'<td class="col-op sample-op">{html.escape(op["name"])}</td>'
            f'<td class="{sample_cell_td_class(oid, op.get("jngen", {}), "jngen")}">'
            f'{format_sample_cell_html(oid, op.get("jngen", {}), "jngen")}</td>'
            f'<td class="{sample_cell_td_class(oid, op.get("tgen", {}), "tgen")}">'
            f'{format_sample_cell_html(oid, op.get("tgen", {}), "tgen")}</td>'
            "</tr>"
        )
    parts.append("</table></div>")
    return parts


def render_comparison_md(meta, operations, categories, bench_index):
    lines = [
        "# tgen vs jngen — Feature Comparison",
        "",
        f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "> **Styled tables and geometry samples:** "
        "[view on GitHub Pages](https://brunomaletta.github.io/tgen_vs_jngen/). "
        "GitHub's Markdown renderer cannot reproduce the HTML layout.",
        "",
        "Comparison of non-trivial generation operations. See "
        "[benchmarks.md](benchmarks.md) for timing results.",
        "",
    ]

    by_cat = {}
    for op in operations:
        by_cat.setdefault(op["category"], []).append(op)

    for cat_id, cat_label in categories.items():
        if cat_id not in by_cat:
            continue
        lines.append(f"## {cat_label}")
        lines.append("")
        lines.append(
            "| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |"
        )
        lines.append(
            "|-----------|-------|------|------------|-------------------|-----------|"
        )
        for op in by_cat[cat_id]:
            tg = op.get("tgen", {})
            jg = op.get("jngen", {})
            jngen_cell = format_lib_api_cell_md(jg)
            tgen_cell = format_lib_api_cell_md(tg)

            uni = format_uniformity_md(tg, jg)
            notes = format_notes_md(tg, jg, op.get("notes", ""))
            bench = format_benchmark_cell_md(op, bench_index)

            lines.append(
                f"| {op['name']} | {jngen_cell} | {tgen_cell} | "
                f"{uni} | {notes} | {bench} |"
            )
        lines.append("")
        if cat_id == "geometry":
            lines.extend(render_geometry_samples_md(operations))

    return "\n".join(lines) + "\n"


def fmt_ms(ms):
    if ms >= 1000:
        return f"{ms/1000:.2f}s"
    return f"{ms:.0f}ms"


def build_benchmark_index(bench):
    if not bench:
        return {}
    return {row["id"]: row for row in bench.get("results", []) if row.get("id")}


def lib_timing_ms(lib_result):
    if lib_result.get("status") == "ok":
        return fmt_ms(float(lib_result["median_ms"]))
    return str(lib_result.get("status", "—"))


def format_benchmark_cell_md(op, bench_index):
    bid = op.get("benchmark_id")
    if not bid:
        return "—"

    row = bench_index.get(bid)
    if not row:
        return "—"

    lines = []
    if row.get("compare_both"):
        lines.append(f"**jngen:** {lib_timing_ms(row.get('jngen', {}))}")
        lines.append(f"**tgen:** {lib_timing_ms(row.get('tgen', {}))}")
        if row.get("ratio"):
            lines.append(f"**{row['ratio']:.2f}x**")
    else:
        lines.append(f"**tgen:** {lib_timing_ms(row.get('tgen', {}))}")
        lines.append("*tgen only*")

    params = row.get("params", "")
    if params:
        lines.append(f"<sub>{params}</sub>")

    return "<br>".join(lines)


def format_benchmark_cell_html(op, bench_index):
    bid = op.get("benchmark_id")
    if not bid:
        return "—"

    row = bench_index.get(bid)
    if not row:
        return "—"

    lines = []
    if row.get("compare_both"):
        lines.append(
            '<strong class="lib-label lib-jngen">jngen:</strong> '
            + html.escape(lib_timing_ms(row.get("jngen", {})))
        )
        lines.append(
            '<strong class="lib-label lib-tgen">tgen:</strong> '
            + html.escape(lib_timing_ms(row.get("tgen", {})))
        )
        if row.get("ratio"):
            lines.append(
                f'<strong class="bench-ratio">{row["ratio"]:.2f}x</strong>'
            )
    else:
        lines.append(
            '<strong class="lib-label lib-tgen">tgen:</strong> '
            + html.escape(lib_timing_ms(row.get("tgen", {})))
        )
        lines.append('<em>tgen only</em>')

    params = row.get("params", "")
    if params:
        lines.append(f'<span class="bench-params">{html.escape(params)}</span>')

    return "<br>".join(lines)


def render_benchmarks_md(bench):
    lines = [
        "# tgen vs jngen — Benchmarks",
        "",
    ]
    if not bench:
        lines.extend([
            "*No benchmark results yet. Run `make benchmark`.*",
            "",
        ])
        return "\n".join(lines)

    lines.extend([
        f"- **Generated:** {bench.get('generated_at', '—')}",
        f"- **Compiler:** {bench.get('compiler', '—')}",
        f"- **Flags:** {bench.get('flags', '—')}",
        f"- **Host:** {bench.get('hostname', '—')}",
        "",
        "## Head-to-head (shared operations)",
        "",
        "| Operation | Parameters | jngen (median) | tgen (median) | Ratio (jngen/tgen) |",
        "|-----------|------------|----------------|---------------|---------------------|",
    ])

    shared = [r for r in bench.get("results", []) if r.get("compare_both")]
    for row in shared:
        name = row.get("name", "") + row.get("name_suffix", "")
        params = row.get("params", "")
        tg = row.get("tgen", {})
        jg = row.get("jngen", {})
        tg_ms = fmt_ms(float(tg["median_ms"])) if tg.get("status") == "ok" else tg.get("status", "—")
        jg_ms = fmt_ms(float(jg["median_ms"])) if jg.get("status") == "ok" else jg.get("status", "—")
        ratio = f"{row['ratio']:.2f}x" if row.get("ratio") else "—"
        lines.append(
            f"| {format_benchmark_name_md(name)} | {format_params_md(params)} | "
            f"{jg_ms} | {tg_ms} | {ratio} |"
        )

    lines.extend([
        "",
        "## tgen-only timings",
        "",
        "| Operation | Parameters | tgen (median) |",
        "|-----------|------------|---------------|",
    ])

    tgen_only = [r for r in bench.get("results", []) if not r.get("compare_both")]
    for row in tgen_only:
        name = row.get("name", "") + row.get("name_suffix", "")
        params = row.get("params", "")
        tg = row.get("tgen", {})
        tg_ms = fmt_ms(float(tg["median_ms"])) if tg.get("status") == "ok" else tg.get("status", "—")
        lines.append(
            f"| {format_benchmark_name_md(name)} | {format_params_md(params)} | {tg_ms} |"
        )

    lines.append("")
    return "\n".join(lines)


def render_comparison_html(operations, categories, bench_index):
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
        parts.append(
            "<tr><th>Operation</th><th class=\"col-api\">jngen</th><th class=\"col-api\">tgen</th>"
            "<th>Uniformity</th><th>Complexity / notes</th><th>Benchmark</th></tr>"
        )
        for op in by_cat[cat_id]:
            tg = op.get("tgen", {})
            jg = op.get("jngen", {})
            jngen_cell = format_lib_api_cell_html(jg)
            tgen_cell = format_lib_api_cell_html(tg)

            uni = format_uniformity_html(tg, jg)
            notes = format_notes_html(tg, jg, op.get("notes", ""))
            bench = format_benchmark_cell_html(op, bench_index)

            parts.append(
                "<tr>"
                f"<td>{html.escape(op['name'])}</td>"
                f"<td class=\"col-api\">{jngen_cell}</td>"
                f"<td class=\"col-api\">{tgen_cell}</td>"
                f"<td>{uni}</td>"
                f"<td>{notes}</td>"
                f"<td>{bench}</td>"
                "</tr>"
            )
        parts.append("</table></div>")
        if cat_id == "geometry":
            parts.extend(render_geometry_samples_html(operations))

    parts.append("</section>")
    return "\n".join(parts)


def render_benchmarks_html(bench):
    parts = [
        "<section id=\"benchmarks\">",
        "<h1>tgen vs jngen — Benchmarks</h1>",
    ]
    if not bench:
        parts.append("<p><em>No benchmark results yet. Run <code>make benchmark</code>.</em></p>")
        parts.append("</section>")
        return "\n".join(parts)

    parts.extend([
        "<ul>",
        f"<li><strong>Generated:</strong> {html.escape(bench.get('generated_at', '—'))}</li>",
        f"<li><strong>Compiler:</strong> {html.escape(bench.get('compiler', '—'))}</li>",
        f"<li><strong>Flags:</strong> {html.escape(bench.get('flags', '—'))}</li>",
        f"<li><strong>Host:</strong> {html.escape(bench.get('hostname', '—'))}</li>",
        "</ul>",
        "<h2>Head-to-head (shared operations)</h2>",
        '<div class="table-scroll"><table>',
        "<tr><th>Operation</th><th>Parameters</th><th>jngen (median)</th>"
        "<th>tgen (median)</th><th>Ratio (jngen/tgen)</th></tr>",
    ])

    for row in [r for r in bench.get("results", []) if r.get("compare_both")]:
        name = row.get("name", "") + row.get("name_suffix", "")
        params = row.get("params", "")
        tg = row.get("tgen", {})
        jg = row.get("jngen", {})
        tg_ms = fmt_ms(float(tg["median_ms"])) if tg.get("status") == "ok" else tg.get("status", "—")
        jg_ms = fmt_ms(float(jg["median_ms"])) if jg.get("status") == "ok" else jg.get("status", "—")
        ratio = f"{row['ratio']:.2f}x" if row.get("ratio") else "—"
        parts.append(
            "<tr>"
            f"<td>{format_benchmark_name_html(name)}</td>"
            f"<td>{format_params_html(params)}</td>"
            f"<td>{html.escape(str(jg_ms))}</td>"
            f"<td>{html.escape(str(tg_ms))}</td>"
            f"<td>{html.escape(ratio)}</td>"
            "</tr>"
        )

    parts.extend([
        "</table></div>",
        "<h2>tgen-only timings</h2>",
        '<div class="table-scroll"><table>',
        "<tr><th>Operation</th><th>Parameters</th><th>tgen (median)</th></tr>",
    ])

    for row in [r for r in bench.get("results", []) if not r.get("compare_both")]:
        name = row.get("name", "") + row.get("name_suffix", "")
        params = row.get("params", "")
        tg = row.get("tgen", {})
        tg_ms = fmt_ms(float(tg["median_ms"])) if tg.get("status") == "ok" else tg.get("status", "—")
        parts.append(
            "<tr>"
            f"<td>{format_benchmark_name_html(name)}</td>"
            f"<td>{format_params_html(params)}</td>"
            f"<td>{html.escape(str(tg_ms))}</td>"
            "</tr>"
        )

    parts.append("</table></div></section>")
    return "\n".join(parts)


def render_html(comparison_body, benchmarks_body):
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
    table.comparison-table .col-uni {{ width: 12%; }}
    table.comparison-table .col-notes {{ width: 31%; }}
    table.comparison-table .col-bench {{ width: 16%; }}
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
    .lib-tgen {{ color: #58a6ff; }}
    .lib-jngen {{ color: #3fb950; }}
    strong.complexity {{ font-weight: 700; color: #f0c674; }}
    strong.bench-ratio {{ color: #d2a8ff; }}
    .bench-params {{ font-size: 0.85rem; color: var(--muted); }}
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
    table.samples-table td.sample-unavailable {{
      color: var(--muted);
    }}
    table.samples-table td.sample-unavailable strong {{
      font-size: 1.05rem;
    }}
    table.samples-table td.col-api img.sample-img {{
      display: block;
      width: 100%;
      max-width: 420px;
      margin: 0.65rem auto 0;
      border-radius: 4px;
      background: #fff;
      border: 1px solid var(--border);
    }}
    nav {{
      margin-bottom: 1.5rem;
      padding: 0.75rem 1rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
    }}
    nav a {{ margin-right: 1rem; }}
  </style>
</head>
<body>
  <nav>
    <a href="#comparison">Feature comparison</a>
    <a href="#benchmarks">Benchmarks</a>
    <a href="https://github.com/brunomaletta/tgen_vs_jngen/blob/main/docs/comparison.md">comparison.md</a> (GitHub)
  </nav>
  {comparison_body}
  {benchmarks_body}
</body>
</html>
"""


def build_site(out_dir, site_dir):
    import shutil

    html_path = os.path.join(out_dir, "comparison.html")
    if not os.path.isfile(html_path):
        raise FileNotFoundError(f"build_site: missing {html_path}")

    gallery_src = os.path.join(out_dir, "gallery")
    if os.path.isdir(site_dir):
        shutil.rmtree(site_dir)
    os.makedirs(site_dir, exist_ok=True)
    shutil.copy2(html_path, os.path.join(site_dir, "index.html"))
    if os.path.isdir(gallery_src):
        shutil.copytree(gallery_src, os.path.join(site_dir, "gallery"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml", default="docs/operations.yaml")
    parser.add_argument("--json", default="results/benchmark_results.json")
    parser.add_argument("--out-dir", default="docs")
    parser.add_argument(
        "--site-dir",
        default="",
        help="if set, also build a GitHub Pages site (index.html + gallery/)",
    )
    args = parser.parse_args()

    meta = load_yaml(args.yaml)
    bench = load_json(args.json)
    bench_index = build_benchmark_index(bench)
    categories = meta.get("categories", {})
    operations = meta.get("operations", [])

    comparison_md = render_comparison_md(meta, operations, categories, bench_index)
    benchmarks_md = render_benchmarks_md(bench)
    comparison_html = render_comparison_html(operations, categories, bench_index)
    benchmarks_html = render_benchmarks_html(bench)

    os.makedirs(args.out_dir, exist_ok=True)
    page_html = render_html(comparison_html, benchmarks_html)
    with open(os.path.join(args.out_dir, "comparison.md"), "w", encoding="utf-8") as f:
        f.write(comparison_md)
    with open(os.path.join(args.out_dir, "benchmarks.md"), "w", encoding="utf-8") as f:
        f.write(benchmarks_md)
    with open(os.path.join(args.out_dir, "comparison.html"), "w", encoding="utf-8") as f:
        f.write(page_html)
    site_dir = args.site_dir or os.path.join(args.out_dir, "site")
    if args.site_dir or os.environ.get("BUILD_PAGES_SITE") == "1":
        build_site(args.out_dir, site_dir)
        print(f"Wrote {site_dir}/")

    print(f"Wrote {args.out_dir}/comparison.md")
    print(f"Wrote {args.out_dir}/benchmarks.md")
    print(f"Wrote {args.out_dir}/comparison.html")


if __name__ == "__main__":
    main()
