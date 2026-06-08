# tgen vs jngen — Benchmarks

- **Generated:** 2026-06-08T00:54:45Z
- **Compiler:** 15.2.0
- **Flags:** -std=c++17 -O2
- **Host:** bruno-inspiron14

## Timing comparison

| Operation | Parameters | Comparison | Ratio (tgen/jngen) |
|-----------|------------|------------|---------------------|
| <code>graph::get_connected (m=n)</code> | n=1e6, m=1e6 | 1114 ms / 1061 ms | 0.95x |
| <code>graph::get_connected (m=2n)</code> | n=1e6, m=2e6 | 2054 ms / 2051 ms | 1.00x |
| <code>graph::gen</code> | n=1e6, m=1e6 | 624 ms / 833 ms | 1.33x |
| <code>graph::gen_skewed (m=n)</code> | n=1e6, m=1e6, elongation=1e2, spread=2 | 827 ms / 219 ms | 0.26x |
| <code>graph::gen_skewed (m=2n)</code> | n=1e6, m=2e6, elongation=1e2, spread=6 | 1354 ms / 729 ms | 0.54x |
| <code>graph::gen_skewed (distinct worst)</code> | n=1e6, m=2n-3, elongation=1e2, spread=2 | 1526 ms / 462 ms | 0.30x |
| <code>tree::gen</code> | n=1e6 | 695 ms / 573 ms | 0.82x |
| <code>tree::gen_skewed</code> | n=1e6, elongation=1e2 | 342 ms / 236 ms | 0.69x |
| <code>list<int>::gen (all_different)</code> | n=1e6, value_left=1, value_right=2e6 | 247 ms / 1869 ms | 7.57x |
| <code>geometry::random_convex_polygon</code> | n=3.6e5, min=0, max=3e9 | 1039 ms / 536 ms | 0.52x |
