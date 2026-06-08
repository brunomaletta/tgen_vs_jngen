# tgen vs jngen — Feature Comparison

*Generated 2026-06-07 23:59 UTC*

Comparison of non-trivial generation operations. See [benchmarks.md](benchmarks.md) for timing results.

## Graphs

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Connected random graph | Yes<br><code>Graph::random(n, m).connected()</code> | Yes<br><code>tgen::graph(n, m).get_connected()</code> | **jngen:** Non-uniform<br>**tgen:** Non-uniform | **jngen:** Tree::random(n) + rejection edge add<br>**tgen:** **O(n + m log n)**; spanning forest + uniform edge completion<br>Both produce connected graphs but not uniformly over all connected labeled graphs. | **jngen:** 989ms<br>**tgen:** 849ms<br>**1.17x**<br><sub>n=1e6, m=1e6</sub> |
| Random graph with fixed n, m | Yes<br><code>Graph::random(n, m)</code> | Yes<br><code>tgen::graph(n, m).gen()</code> | **jngen:** Undocumented<br>**tgen:** Uniform | **jngen:** Rejection on random vertex pairs; no documented bound<br>**tgen:** **O(n + m log n)**; rejection with constraint machinery<br>tgen documents uniform sampling among valid graphs; jngen uses undocumented rejection. | **jngen:** 432ms<br>**tgen:** 677ms<br>**0.64x**<br><sub>n=1e6, m=1e6</sub> |
| Skewed / stretched connected graph | Yes<br><code>Graph<br>randomStretched(n, m, elongation, spread)</code> | Yes<br><code>tgen::graph<br>gen_skewed(n, m, elongation, spread)</code> | **jngen:** Non-uniform<br>**tgen:** Non-uniform | **jngen:** Tree::randomPrim + parent-hop biased edges; may throw after 1000 failures<br>**tgen:** **O(n + m log n)**; wnext backbone + ancestor-biased edges<br>Both intentionally biased toward high diameter. Parent-hop semantics differ slightly (k in [2, spread] vs up to spread hops). | **jngen:** 575ms<br>**tgen:** 149ms<br>**3.87x**<br><sub>n=1e6, m=1e6, elongation=1e2, spread=2</sub> |
| Graph modifiers (directed, multi, acyclic, loops) | Yes<br><code>Graph<br>random(...).directed().allowMulti()<br>.acyclic()...</code> | Yes<br><code>tgen<br>graph(...).directed().multi()<br>.acyclic()...</code> | **jngen:** Undocumented<br>**tgen:** Varies | **jngen:** Chaining modifiers on BuilderProxy<br>**tgen:** Declarative constraint composition<br>Both support modifier chains; tgen uses declarative generators with documented uniformity where promised. | — |

## Trees

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Random labeled tree | Yes<br><code>Tree::random(n)</code> | Yes<br><code>tgen::tree(n).gen()</code> | **jngen:** Uniform<br>**tgen:** Uniform | **jngen:** **O(n)**; Prüfer sequence<br>**tgen:** **O(n)**; Prüfer sequence<br>Both uniform over labeled trees. jngen returns sorted edges rooted at 0 by default. | **jngen:** 524ms<br>**tgen:** 442ms<br>**1.19x**<br><sub>n=1e6</sub> |
| Skewed tree (wnext / Prim-like) | Yes<br><code>Tree::randomPrim(n, elongation)</code> | Yes<br><code>tgen::tree::gen_skewed(n, elongation)</code> | **jngen:** Non-uniform<br>**tgen:** Non-uniform | **jngen:** **O(n)**; same wnext process<br>**tgen:** **O(n)**; parent(i) = wnext(i, elongation)<br>Equivalent algorithms. Large positive elongation → path; large negative → star. | **jngen:** 212ms<br>**tgen:** 127ms<br>**1.67x**<br><sub>n=1e6, elongation=1e2</sub> |
| Random tree (Kruskal-like) | Yes<br><code>Tree::randomKruskal(n)</code> | **No** | **jngen:** Non-uniform | **jngen:** Rejection on random edges<br>jngen-only generator. | — |

## Lists and sequences

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Distinct values in range | Yes<br><code>Array::randomUnique(k, lo, hi)</code> | Yes<br><code>tgen<br>list<int>(k, lo, hi).all_different()<br>.gen()</code> | **jngen:** Uniform<br>**tgen:** Uniform | **jngen:** **O(k log k)** rejection<br>**tgen:** **O(k log k)**; Fisher–Yates + forbidden-value map<br>Both produce uniform distinct samples. tgen supports richer declarative constraints (.different(), sorted, etc.). | **jngen:** 184ms<br>**tgen:** 1.37s<br>**0.13x**<br><sub>n=1e6, value_left=1, value_right=2e6</sub> |
| Declarative list constraints (sorted, palindrome, cycles) | **No** | Yes<br><code>tgen<br>list/str/permutation/pair builders with .sorted(), .palindrome(), .cycles()...</code> | **tgen:** Varies | **tgen:** Constraint-based uniform sampling where documented<br>tgen-only declarative generator framework. | — |

## Geometry

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Random convex polygon | Yes<br><code>rndg.convexPolygon(n, min, max)</code> | Yes<br><code>tgen::geometry<br>random_convex_polygon(n, min, max)</code> | **jngen:** Non-uniform<br>**tgen:** Non-uniform | **jngen:** Convex hull of 10n ellipse points, subsample n<br>**tgen:** **O(n log n)**; Valtr construction filling bounding box<br>Different shape distributions. jngen may throw if hull has fewer than n vertices; practical only at moderate n (benchmark uses n=1000). | **jngen:** 2ms<br>**tgen:** 0ms<br>**4.44x**<br><sub>n=1000, min=0, max=3e6</sub> |
| Points in general position (no three collinear) | Yes<br><code>rndg.pointsInGeneralPosition(n, min, max)</code> | Yes<br><code>tgen::geometry<br>random_points_general_position(n, min, max)</code> | **jngen:** Undocumented<br>**tgen:** Non-uniform | **jngen:** **O(n² log n)**; rejection until no collinearity<br>**tgen:** **O(n)**; algebraic construction over F_p<br>Not benchmarked head-to-head: jngen is asymptotically slower. tgen uses a deterministic algebraic method. | **tgen:** 123ms<br>*tgen only*<br><sub>n=1e6, min=0, max=3e6</sub> |
| Random simple polygon | **No** | Yes<br><code>tgen::geometry<br>random_simple_polygon(n, min, max)</code> | **tgen:** Non-uniform | **tgen:** **O(n log n)** expected; points + polygonization<br>tgen-only. jngen has no simple polygon generator. | **tgen:** 925ms<br>*tgen only*<br><sub>n=1e6, min=0, max=3e6</sub> |
| Simple polygon through given points | **No** | Yes<br><code>tgen::geometry<br>random_simple_polygon_through_points(pts)</code> | **tgen:** Non-uniform | **tgen:** **O(n log n)** expected; randomized divide-and-conquer Hamiltonian path<br>tgen-only. | **tgen:** 814ms<br>*tgen only*<br><sub>n=1e6</sub> |
| Built-in SVG visualization | Yes<br><code>Drawer d; d.polygon(...); d.dumpSvg("out.svg")</code> | **No** | — | jngen-only Drawer for points, segments, circles, polygons. | — |

### Samples

Visual output for the geometry operations above (seed **42**, coordinates in **[0, 1000]**; **n = 80** except simple polygon through points, which uses a **10×10 rectangular grid**).

| Operation | jngen | tgen |
|-----------|-------|------|
| Random convex polygon | Yes<br><code>rndg.convexPolygon(n, min, max)</code><br><img src="gallery/geometry_convex_polygon_jngen.svg" alt="jngen sample"> | Yes<br><code>tgen::geometry<br>random_convex_polygon(n, min, max)</code><br><img src="gallery/geometry_convex_polygon_tgen.svg" alt="tgen sample"> |
| Points in general position (no three collinear) | Yes<br><code>rndg.pointsInGeneralPosition(n, min, max)</code><br><img src="gallery/geometry_points_general_position_jngen.svg" alt="jngen sample"> | Yes<br><code>tgen::geometry<br>random_points_general_position(n, min, max)</code><br><img src="gallery/geometry_points_general_position_tgen.svg" alt="tgen sample"> |
| Random simple polygon | **No** | Yes<br><code>tgen::geometry<br>random_simple_polygon(n, min, max)</code><br><img src="gallery/geometry_simple_polygon_tgen.svg" alt="tgen sample"> |
| Simple polygon through given points | **No** | Yes<br><code>tgen::geometry<br>random_simple_polygon_through_points(pts)</code><br><img src="gallery/geometry_simple_polygon_through_points_tgen.svg" alt="tgen sample"> |

## Strings and hashing

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Polynomial hash collision strings | Yes<br><code>rnds.antiHash({{mod, base}, ...}, alphabet, len)</code> | Yes<br><code>tgen::hack::polynomial_hash_hack(...)</code> | — | **jngen:** Brute force for small mod/base sets<br>**tgen:** Birthday / Thue–Morse constructions<br>Both generate colliding strings for rolling hash. jngen limits to ≤2 mod/base pairs. | — |

## Adversarial / hack generators

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| std::unordered_set collision inputs | Yes<br><code>rnda.antiUnorderedSet(n, maxLoadFactor, reserve)</code> | Yes<br><code>tgen::hack::std_unordered(size)</code> | — | **jngen:** GCC 4.x only; tuned load factor/reserve<br>**tgen:** GCC multiplier-based collision keys<br>Overlap in purpose; different APIs and compiler support. | — |
| Max-flow worst case (Dinitz / Edmonds-Karp) | **No** | Yes<br><code>tgen::hack::dinitz_worst_case(k, l)</code> | — | **tgen:** Zadeh network construction<br>tgen-only adversarial flow network. | — |
| Shortest-path implementation traps (SPFA, Dijkstra) | **No** | Yes<br><code>tgen::hack<br>spfa_hack, stale_heap_dijkstra_bug, ...</code> | — | tgen-only. | — |
| Mo's algorithm worst-case queries | **No** | Yes<br><code>tgen::hack::mo(n, q)</code> | — | tgen-only. | — |

