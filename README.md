# tgen vs jngen

Side-by-side comparison of [tgen](https://github.com/brunomaletta/tgen) and [jngen](https://github.com/ifsmirnov/jngen): feature matrix, performance benchmarks, and sample visualizations.

## Quick start

```bash
make vendor    # init submodules and build jngen.h
make all       # benchmark + visualize + regenerate docs
make opendoc   # open rendered docs/comparison.html in Chrome
```

Benchmarks run **locally** and are stored in `docs/benchmark_results.json` (committed). GitHub Actions only reads that file when building the Pages site.

```bash
make benchmark              # full timings (n=1e6)
make benchmark QUICK=1      # faster refresh (n=1e5)
git add docs/benchmark_results.json && git commit -m "Update benchmark results"
```

For docs/Pages without re-running benchmarks:

```bash
make site    # visualize + render docs + docs/site/
```

## Documentation

Requires Python 3 with PyYAML (`pip install pyyaml`). `make docs` also runs tgen’s Doxygen XML pass (needs Doxygen) so API cells link to pinned GitHub source lines.

**Live site (styled tables + geometry samples):**  
<https://brunomaletta.github.io/tgen_vs_jngen/>

| Document | Description |
|----------|-------------|
| [docs/comparison.html](docs/comparison.html) | Feature comparison, benchmarks, and geometry samples (also on [GitHub Pages](https://brunomaletta.github.io/tgen_vs_jngen/)) |

Run `make site` to rebuild the Pages bundle locally (`docs/site/index.html`).

Geometry sample SVGs live under `docs/gallery/` (50 variants per sample, seeds 42–91; built by `make visualize`, not committed). Each sample has a ↻ button in the comparison page — click to cycle, Shift-click for a random variant.

## What is compared

**Benchmarked head-to-head** (same parameters where both libraries support them):

- Connected and random graphs (including directed), skewed graphs, bipartite graphs
- Random and skewed trees, uniform permutations
- Distinct integer lists
- Convex polygons (n=1e6, max=3e10 — jngen needs a wider range at this n; both use the same n)

**Feature table** (not all rows are timed): named graphs, rooted tree output, structured printing, testlib integration, math, geometry, strings, `hack::` generators — see [docs/comparison.html](docs/comparison.html).

**Tgen-only benchmarks** (in the table, not head-to-head): simple polygons.

Validate docs against committed timings and API source mappings:

```bash
make check
```

API strings in the comparison table link to GitHub source (tgen line numbers from Doxygen XML; jngen from `docs/api_sources.yaml`). Links use vendor SHAs from `benchmark_results.json`.

## Project layout

```
vendor/tgen/     git submodule
vendor/jngen/    git submodule (run build.py to produce jngen.h)
benchmarks/      C++ harness
visualize/       sample generators + SVG output
docs/            operations.yaml, api_sources.yaml, benchmark_results.json, generated HTML
results/         ephemeral build outputs (gitignored)
```

## License

This comparison project is MIT-licensed. tgen and jngen retain their respective licenses.
