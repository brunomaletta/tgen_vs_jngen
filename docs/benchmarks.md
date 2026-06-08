# tgen vs jngen — Benchmarks

- **Generated:** 2026-06-08T00:02:10Z
- **Compiler:** 15.2.0
- **Flags:** -std=c++17 -O2 -DQUICK
- **Host:** bruno-inspiron14

## Head-to-head (shared operations)

| Operation | Parameters | jngen (median) | tgen (median) | Ratio (jngen/tgen) |
|-----------|------------|----------------|---------------|---------------------|
| <code>graph::get_connected (m=n)</code> | n=1e6, m=1e6 | 46ms | 39ms | 1.17x |
| <code>graph::get_connected (m=2n)</code> | n=1e6, m=2e6 | 74ms | 97ms | 0.76x |
| <code>graph::gen</code> | n=1e6, m=1e6 | 24ms | 38ms | 0.63x |
| <code>graph::gen_skewed (m=n)</code> | n=1e6, m=1e6, elongation=1e2, spread=2 | 39ms | 11ms | 3.42x |
| <code>graph::gen_skewed (m=2n)</code> | n=1e6, m=2e6, elongation=1e2, spread=6 | 74ms | 33ms | 2.27x |
| <code>graph::gen_skewed (distinct worst)</code> | n=1e6, m=2n-3, elongation=1e2, spread=2 | 59ms | 24ms | 2.46x |
| <code>tree::gen</code> | n=1e6 | 28ms | 25ms | 1.12x |
| <code>tree::gen_skewed</code> | n=1e6, elongation=1e2 | 18ms | 9ms | 1.97x |
| <code>list<int>::gen (all_different)</code> | n=1e6, value_left=1, value_right=2e6 | 8ms | 78ms | 0.10x |
| <code>geometry::random_convex_polygon</code> | n=1000, min=0, max=3e6 | 2ms | 0ms | 4.59x |

## tgen-only timings

| Operation | Parameters | tgen (median) |
|-----------|------------|---------------|
| <code>geometry<br>random_points_general_position</code> | n=1e6, min=0, max=3e6 | 12ms |
| <code>geometry::random_simple_polygon</code> | n=1e6, min=0, max=3e6 | 55ms |
| <code>geometry<br>random_simple_polygon_through_points</code> | n=1e6 | 44ms |
