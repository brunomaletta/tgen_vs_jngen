#!/usr/bin/env python3
"""Validate operations.yaml against benchmark_results.json and api_sources.yaml."""

import json
import os
import sys

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(DOCS_DIR)
sys.path.insert(0, DOCS_DIR)

from tgen_source_index import TgenSourceIndex, default_xml_dir  # noqa: E402

try:
    import yaml
except ImportError:
    print("check_docs: install PyYAML (pip install pyyaml)", file=sys.stderr)
    sys.exit(1)


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def median_ratio(tgen_result, jngen_result):
    if tgen_result.get("status") != "ok" or jngen_result.get("status") != "ok":
        return None
    tg = tgen_result.get("median_ms")
    jg = jngen_result.get("median_ms")
    if tg is None or jg is None or float(jg) <= 0:
        return None
    return float(tg) / float(jg)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(root, "docs", "operations.yaml")
    json_path = os.path.join(root, "docs", "benchmark_results.json")

    meta = load_yaml(yaml_path)
    bench = load_json(json_path)
    bench_index = {row["id"]: row for row in bench.get("results", []) if row.get("id")}

    errors = []

    for op in meta.get("operations", []):
        if not op.get("benchmark"):
            continue
        bid = op.get("benchmark_id")
        if not bid:
            errors.append(f"{op['id']}: benchmark=true but missing benchmark_id")
            continue
        if bid not in bench_index:
            errors.append(f"{op['id']}: benchmark_id {bid!r} missing from JSON")

    for row in bench.get("results", []):
        if not row.get("compare_both"):
            continue
        ratio = row.get("ratio")
        if ratio is None:
            continue
        tg = row.get("tgen", {})
        jg = row.get("jngen", {})
        if tg.get("status") != "ok" or jg.get("status") != "ok":
            continue
        expected = median_ratio(tg, jg)
        if expected is None:
            continue
        if abs(expected - float(ratio)) > 1e-4:
            errors.append(
                f"{row['id']}: ratio {ratio} != tgen/jngen {expected:.4f}"
            )

    sources_path = os.path.join(root, "docs", "api_sources.yaml")
    if os.path.isfile(sources_path):
        sources = load_yaml(sources_path)
        entries = sources.get("entries", {})
        tgen_index = TgenSourceIndex(default_xml_dir(root))
        if len(tgen_index) == 0:
            errors.append(
                "api_sources: tgen Doxygen XML missing — run "
                "'cd vendor/tgen && make doc-prepare'"
            )
        else:
            for op_id, lib_map in entries.items():
                for lib, entry in lib_map.items():
                    if lib == "tgen":
                        symbol = entry if isinstance(entry, str) else entry.get("symbol")
                        if symbol and tgen_index.lookup(symbol) is None:
                            errors.append(
                                f"api_sources {op_id}.tgen: symbol {symbol!r} "
                                "not found in Doxygen XML"
                            )
                    elif lib == "jngen":
                        if isinstance(entry, str):
                            errors.append(
                                f"api_sources {op_id}.jngen: expected file/line map"
                            )
                        elif not entry.get("file") or entry.get("line") is None:
                            errors.append(
                                f"api_sources {op_id}.jngen: missing file or line"
                            )

        for op in meta.get("operations", []):
            op_id = op["id"]
            if op.get("gallery_only"):
                continue
            for lib in ("tgen", "jngen"):
                info = op.get(lib, {})
                if not info.get("has") or not info.get("api"):
                    continue
                if op_id not in entries or lib not in entries[op_id]:
                    errors.append(
                        f"{op_id}.{lib}: has API but no api_sources.yaml entry"
                    )

        benchmark_to_op = {}
        for op in meta.get("operations", []):
            bid = op.get("benchmark_id")
            if bid:
                benchmark_to_op[bid] = op["id"]
        for bench_id, target in sources.get("benchmarks", {}).items():
            benchmark_to_op[bench_id] = (
                target if isinstance(target, str) else target.get("op")
            )

        for row in bench.get("results", []):
            bench_id = row.get("id")
            if not bench_id:
                continue
            op_id = benchmark_to_op.get(bench_id)
            if not op_id:
                errors.append(
                    f"benchmark {bench_id!r}: no operation mapping "
                    "(set benchmark_id in operations.yaml or benchmarks: in api_sources.yaml)"
                )
                continue
            tg = row.get("tgen", {})
            if tg.get("status") == "ok" and (
                op_id not in entries or "tgen" not in entries[op_id]
            ):
                errors.append(
                    f"benchmark {bench_id!r} -> {op_id}: missing tgen api_sources entry"
                )

    if errors:
        print("check_docs: FAILED", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    print("check_docs: OK")


if __name__ == "__main__":
    main()
