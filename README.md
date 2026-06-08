# tgen vs jngen

Side-by-side comparison of [tgen](https://github.com/brunomaletta/tgen) and [jngen](https://github.com/ifsmirnov/jngen): feature matrix, performance benchmarks, and sample visualizations.

## Quick start

```bash
make vendor    # init submodules and build jngen.h
make all       # benchmark + visualize + regenerate docs
make opendoc   # open rendered docs/comparison.html in Chrome
```

For faster benchmarks during development:

```bash
make benchmark QUICK=1
```

## Documentation

Requires Python 3 with PyYAML (`pip install pyyaml`).

| Document | Description |
|----------|-------------|
| [docs/comparison.md](docs/comparison.md) | Feature comparison table (API, uniformity, complexity) |
| [docs/benchmarks.md](docs/benchmarks.md) | Head-to-head timing results |
| [docs/comparison.html](docs/comparison.html) | Same content as Markdown, styled for local viewing |

Geometry sample SVGs live under `docs/gallery/` and are embedded in the comparison table.

## What is compared

**Benchmarked head-to-head** (same parameters as [tgen's benchmark suite](https://github.com/brunomaletta/tgen/tree/main/benchmarks)):

- Connected and random graphs, skewed graphs
- Random and skewed trees
- Distinct integer lists
- Convex polygons

**Comparison table only** (not timed against jngen):

- Points in general position (jngen is O(n²); different algorithms)
- Simple polygon generation (missing in jngen)

## Project layout

```
vendor/tgen/     git submodule
vendor/jngen/    git submodule (run build.py to produce jngen.h)
benchmarks/      C++ harness
visualize/       sample generators + SVG output
docs/            operations.yaml (source) + generated Markdown/HTML
results/         generated benchmark JSON and SVG (gitignored)
```

## License

This comparison project is MIT-licensed. tgen and jngen retain their respective licenses.
