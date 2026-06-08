# tgen vs jngen — Benchmarks

- **Generated:** 2026-06-07T23:19:03Z
- **Compiler:** 15.2.0
- **Flags:** -std=c++17 -O2
- **Host:** bruno-inspiron14

## Head-to-head (shared operations)

| Operation | Parameters | jngen (median) | tgen (median) | Ratio (jngen/tgen) |
|-----------|------------|----------------|---------------|---------------------|
| <code>graph::get_connected (m=n)</code> | n=1e6, m=1e6 | 989ms | 849ms | 1.17x |
| <code>graph::get_connected (m=2n)</code> | n=1e6, m=2e6 | 1.54s | 1.79s | 0.86x |
| <code>graph::gen</code> | n=1e6, m=1e6 | 432ms | 677ms | 0.64x |
| <code>graph::gen_skewed (m=n)</code> | n=1e6, m=1e6, elongation=1e2, spread=2 | 575ms | 149ms | 3.87x |
| <code>graph::gen_skewed (m=2n)</code> | n=1e6, m=2e6, elongation=1e2, spread=6 | 949ms | 434ms | 2.18x |
| <code>graph::gen_skewed (distinct worst)</code> | n=1e6, m=2n-3, elongation=1e2, spread=2 | 1.11s | 335ms | 3.30x |
| <code>tree::gen</code> | n=1e6 | 524ms | 442ms | 1.19x |
| <code>tree::gen_skewed</code> | n=1e6, elongation=1e2 | 212ms | 127ms | 1.67x |
| <code>list<int>::gen (all_different)</code> | n=1e6, value_left=1, value_right=2e6 | 184ms | 1.37s | 0.13x |
| <code>geometry::random_convex_polygon</code> | n=1000, min=0, max=3e6 | 2ms | 0ms | 4.44x |

## tgen-only timings

| Operation | Parameters | tgen (median) |
|-----------|------------|---------------|
| <code>geometry<br>random_points_general_position</code> | n=1e6, min=0, max=3e6 | 123ms |
| <code>geometry::random_simple_polygon</code> | n=1e6, min=0, max=3e6 | 925ms |
| <code>geometry<br>random_simple_polygon_through_points</code> | n=1e6 | 814ms |
