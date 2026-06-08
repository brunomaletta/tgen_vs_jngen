#!/usr/bin/env python3
"""Validate operations.yaml against benchmark_results.json."""

import json
import os
import sys

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

    if errors:
        print("check_docs: FAILED", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    print("check_docs: OK")


if __name__ == "__main__":
    main()
