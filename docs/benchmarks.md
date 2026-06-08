# tgen vs jngen — Benchmarks

- **Generated:** 2026-06-08T02:01:52Z
- **Compiler:** 15.2.0
- **Flags:** -std=c++17 -O2
- **Host:** bruno-inspiron14
- **Vendor commits:** tgen `6870854`, jngen `8d1e33b`

## Timing comparison

| Operation | Parameters | Comparison | Ratio (tgen/jngen) |
|-----------|------------|------------|---------------------|
| <code>graph::get_connected (m=n)</code> | n=1e6, m=1e6 | 1263 ms / 1214 ms | 0.96x |
| <code>graph::get_connected (m=2n)</code> | n=1e6, m=2e6 | 2031 ms / 2373 ms | 1.17x |
| <code>graph::gen</code> | n=1e6, m=1e6 | 578 ms / 892 ms | 1.54x |
| <code>graph::gen_skewed (m=n)</code> | n=1e6, m=1e6, elongation=1e2, spread=2 | 755 ms / 190 ms | 0.25x |
| <code>graph::gen_skewed (m=2n)</code> | n=1e6, m=2e6, elongation=1e2, spread=6 | 1289 ms / 515 ms | 0.40x |
| <code>graph::gen_skewed (distinct worst)</code> | n=1e6, m=2n-3, elongation=1e2, spread=2 | 1491 ms / 409 ms | 0.27x |
| <code>tree::gen</code> | n=1e6 | 690 ms / 579 ms | 0.84x |
| <code>tree::gen_skewed</code> | n=1e6, elongation=1e2 | 250 ms / 161 ms | 0.64x |
| <code>list<int>::gen (all_different)</code> | n=1e6, value_left=1, value_right=2e6 | 254 ms / 1884 ms | 7.42x |
| <code>geometry::random_convex_polygon</code> | n=3.6e5, min=0, max=3e9 | 968 ms / 498 ms | 0.51x |
| <code>permutation::gen</code> | n=1e6 | 17 ms / 12 ms | 0.71x |
| <code>graph::gen_bipartite</code> | n1=1e3, n2=1e3, m=5e5 | 206 ms / 874 ms | 4.24x |
| <code>graph::gen (directed)</code> | n=1e6, m=1e6 | 623 ms / 416 ms | 0.67x |
## tgen-only timings

| Operation | Parameters | tgen |
|-----------|------------|------|
| <code>geometry::random_points_general_position</code> | n=1e6, min=0, max=3e6 | 150 ms |
| <code>geometry::random_simple_polygon</code> | n=1e6, min=0, max=3e6 | 1234 ms |
| <code>geometry::random_simple_polygon_through_points</code> | n=1e6 | 1097 ms |
| <code>geometry::random_convex_polygon (tgen scale)</code> | n=1e6, min=0, max=3e9 | 2070 ms |

