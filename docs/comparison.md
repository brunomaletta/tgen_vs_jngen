# tgen vs jngen — Feature Comparison

*Generated 2026-06-08 01:07 UTC*

> **Styled tables and geometry samples:** [view on GitHub Pages](https://brunomaletta.github.io/tgen_vs_jngen/). GitHub's Markdown renderer cannot reproduce the HTML layout.

Comparison of non-trivial generation operations. See [benchmarks.md](benchmarks.md) for timing results.

## Graphs

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Connected random graph | Yes<br><code>Graph::random(n, m).connected()</code> | Yes<br><code>graph(n, m).get_connected()</code> | **jngen:** Non-uniform<br>**tgen:** Non-uniform | **jngen:** Tree::random(n) + rejection edge add<br>**tgen:** **O(n + m log n)**; spanning forest + uniform edge completion<br>Both produce connected graphs but not uniformly over all connected labeled graphs. | **jngen:** 1114 ms<br>**tgen:** 1061 ms<br>0.95x<br><sub>n=1e6, m=1e6</sub> |
| Random graph with fixed n, m | Yes<br><code>Graph::random(n, m)</code> | Yes<br><code>graph(n, m).gen()</code> | **jngen:** Undocumented<br>**tgen:** Uniform | **jngen:** Rejection on random vertex pairs; no documented bound<br>**tgen:** **O(n + m log n)**; rejection with constraint machinery<br>**tgen** documents uniform sampling among valid graphs; **jngen** uses undocumented rejection. | **jngen:** 624 ms<br>**tgen:** 833 ms<br>1.33x<br><sub>n=1e6, m=1e6</sub> |
| Skewed / stretched connected graph | Yes<br><code>Graph::randomStretched(n, m, elongation, spread)</code> | Yes<br><code>graph::gen_skewed(n, m, elongation, spread)</code> | **jngen:** Non-uniform<br>**tgen:** Non-uniform | **jngen:** Tree::randomPrim + parent-hop biased edges; may throw after 1000 failures<br>**tgen:** **O(n + m log n)**; wnext backbone + ancestor-biased edges<br>Both intentionally biased toward high diameter. Parent-hop semantics differ slightly (k in [2, spread] vs up to spread hops). | **jngen:** 827 ms<br>**tgen:** 219 ms<br>0.26x<br><sub>n=1e6, m=1e6, elongation=1e2, spread=2</sub> |
| Graph modifiers (directed, multi, acyclic, loops) | Yes<br><code>Graph::random(...).directed().allowMulti().acyclic()<br>...</code> | Yes<br><code>graph(...).directed().multi().acyclic()...</code> | **jngen:** Undocumented<br>**tgen:** Varies | **jngen:** Chaining modifiers on BuilderProxy<br>**tgen:** Declarative constraint composition<br>Both support modifier chains; **tgen** documents uniformity where promised. | — |
| Bipartite graph (random / complete) | Yes<br><code>Graph::randomBipartite(n1, n2, m), completeBipartite(n1, n2)</code> | Yes<br><code>graph::gen_bipartite(n1, n2, m), K(n1, n2)</code> | **jngen:** Undocumented<br>**tgen:** Uniform | **jngen:** Rejection on random cross edges<br>**tgen:** **O(n1 + n2 + m log(n1 + n2)**); uniform cross edges<br>Both support random and complete bipartite graphs. **tgen** documents uniform sampling among valid bipartite graphs with m edges. | — |
| Weighted graphs and trees | Yes<br><code>Graph::setVertexWeights / setEdgeWeight<br>; Tree inherits graph weights</code> | Yes<br><code>wgraph / wtree (vertex- and edge-weighted variants)</code> | **jngen:** Undocumented<br>**tgen:** Undocumented | **jngen:** Post-hoc weight assignment on generated structure<br>**tgen:** Same generators as unweighted, plus weight assignment | — |

## Trees

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Random labeled tree | Yes<br><code>Tree::random(n)</code> | Yes<br><code>tree(n).gen()</code> | **jngen:** Uniform<br>**tgen:** Uniform | **jngen:** **O(n)**; Prüfer sequence<br>**tgen:** **O(n)**; Prüfer sequence<br>Both uniform over labeled trees. **jngen** returns sorted edges rooted at 0 by default. | **jngen:** 695 ms<br>**tgen:** 573 ms<br>0.82x<br><sub>n=1e6</sub> |
| Skewed tree (wnext / Prim-like) | Yes<br><code>Tree::randomPrim(n, elongation)</code> | Yes<br><code>tree::gen_skewed(n, elongation)</code> | **jngen:** Non-uniform<br>**tgen:** Non-uniform | **jngen:** **O(n)**; same wnext process<br>**tgen:** **O(n)**; parent(i) = wnext(i, elongation)<br>Equivalent algorithms. Large positive elongation → path; large negative → star. | **jngen:** 342 ms<br>**tgen:** 236 ms<br>0.69x<br><sub>n=1e6, elongation=1e2</sub> |
| Named tree shapes (star, path, caterpillar, k-ary) | Yes<br><code>Tree::star, bamboo, caterpillar, binary, kary, ...</code> | Yes<br><code>S(n) star, P(n) path; no caterpillar/binary/k-ary</code> | **jngen:** Undocumented | **jngen:** **O(n)**<br>**tgen:** **O(n)**; standard graph helpers (also valid trees)<br>**tgen** exposes star and path as graph helpers; **jngen** has a richer set of named tree generators. | — |
| Random tree (Kruskal-like) | Yes<br><code>Tree::randomKruskal(n)</code> | **No** | **jngen:** Non-uniform | **jngen:** Rejection on random edges | — |

## Lists and sequences

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Distinct values in range | Yes<br><code>Array::randomUnique(k, lo, hi)</code> | Yes<br><code>list<int>(k, lo, hi).all_different().gen()</code> | **jngen:** Uniform<br>**tgen:** Uniform | **jngen:** **O(k log k)** rejection<br>**tgen:** **O(k log k)**; Fisher–Yates + forbidden-value map<br>Both produce uniform distinct samples. | **jngen:** 247 ms<br>**tgen:** 1869 ms<br>7.57x<br><sub>n=1e6, value_left=1, value_right=2e6</sub> |
| Uniform random permutation | Yes<br><code>Array::id(n).shuffled()</code> | Yes<br><code>permutation(n).gen()</code> | **jngen:** Uniform<br>**tgen:** Uniform | **jngen:** **O(n)**<br>**tgen:** **O(n)** | — |
| Declarative constraints (sorted, palindrome, cycles) | **No** | Yes<br><code>list/str/permutation/pair with .sorted(), .palindrome(), .cycles()...</code> | **tgen:** Varies | **tgen:** Constraint-based uniform sampling where documented | — |

## Math

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Ordered partition into k parts (composition) | Yes<br><code>rndm.partition(n, numParts, minSize, maxSize)</code> | Yes<br><code>math::gen_partition_fixed_size(n, k, part_left, part_right)</code> | **jngen:** Non-uniform<br>**tgen:** Uniform | **jngen:** Random delimiters, then sort parts descending + heuristic redistribution<br>**tgen:** **O(n)** stars-and-bars (unbounded parts) or **O(n·k)** DP with bounds<br>Different algorithms and semantics. **tgen** returns an ordered composition sampled uniformly. **jngen** sorts parts in non-increasing order (not a uniform composition); source comments that bounded redistribution 'need a smarter way'. | — |
| Ordered partition, variable number of parts | **No** | Yes<br><code>math::gen_partition(n, part_left, part_right)</code> | **tgen:** Uniform | **tgen:** **O(n)**; DP in log space | — |
| Random prime in range | Yes<br><code>rndm.randomPrime(l, r)</code> | Yes<br><code>math::gen_prime(left, right)</code> | **jngen:** Undocumented<br>**tgen:** Uniform | **jngen:** Rejection on rnd.next(l, r) until prime<br>**tgen:** **O(log³ n)** expected<br>**tgen** documents uniform sampling among primes in the interval. | — |
| Random integer with congruence constraints | **No** | Yes<br><code>math::gen_congruent(l, r, rems, mods)</code> | **tgen:** Uniform | **tgen:** **O(|mods| + log r)** | — |
| Partition array into k groups | Yes<br><code>rndm.partition(elements, numParts, minSize, maxSize)</code> | **No** | **jngen:** Non-uniform | **jngen:** Shuffle elements, split by partition sizes from rndm.partition | — |

## Geometry

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Random convex polygon | Yes<br><code>rndg.convexPolygon(n, min, max)</code> | Yes<br><code>geometry::random_convex_polygon(n, min, max)</code> | **jngen:** Non-uniform<br>**tgen:** Non-uniform | **jngen:** Convex hull of 10n ellipse points, subsample n<br>**tgen:** **O(n log n)**; Valtr construction filling bounding box<br>Different shape distributions. **jngen** needs a large coordinate range at high n (hull subsampling); benchmark uses n=3.6e5, max=3e9 for both. | **jngen:** 1039 ms<br>**tgen:** 536 ms<br>0.52x<br><sub>n=3.6e5, min=0, max=3e9</sub> |
| Points in general position (no three collinear) | Yes<br><code>rndg.pointsInGeneralPosition(n, min, max)</code> | Yes<br><code>geometry::random_points_general_position(n, min, max)</code> | **jngen:** Undocumented<br>**tgen:** Non-uniform | **jngen:** **O(n² log n)**; rejection until no collinearity<br>**tgen:** **O(n)**; algebraic construction over F_p<br>Not benchmarked head-to-head: **jngen** is asymptotically slower. | **tgen:** 167 ms<br><sub>n=1e6, min=0, max=3e6</sub> |
| Random simple polygon | **No** | Yes<br><code>geometry::random_simple_polygon(n, min, max)</code> | **tgen:** Non-uniform | **tgen:** **O(n log n)** expected; points + polygonization | **tgen:** 1263 ms<br><sub>n=1e6, min=0, max=3e6</sub> |
| Simple polygon through given points | **No** | Yes<br><code>geometry::random_simple_polygon_through_points(pts)</code> | **tgen:** Non-uniform | **tgen:** **O(n log n)** expected; randomized divide-and-conquer Hamiltonian path | **tgen:** 1131 ms<br><sub>n=1e6</sub> |

### Samples

| Operation | jngen | tgen |
|-----------|-------|------|
| Random convex polygon | Yes<br><code>rndg.convexPolygon(n, min, max)</code><br><img src="gallery/geometry_convex_polygon_jngen.svg" alt="jngen sample"> | Yes<br><code>geometry::random_convex_polygon(n, min, max)</code><br><img src="gallery/geometry_convex_polygon_tgen.svg" alt="tgen sample"> |
| Points in general position (no three collinear) | Yes<br><code>rndg.pointsInGeneralPosition(n, min, max)</code><br><img src="gallery/geometry_points_general_position_jngen.svg" alt="jngen sample"> | Yes<br><code>geometry::random_points_general_position(n, min, max)</code><br><img src="gallery/geometry_points_general_position_tgen.svg" alt="tgen sample"> |
| Random simple polygon | **No** | Yes<br><code>geometry::random_simple_polygon(n, min, max)</code><br><img src="gallery/geometry_simple_polygon_tgen.svg" alt="tgen sample"> |
| Simple polygon through given points | **No** | Yes<br><code>geometry::random_simple_polygon_through_points(pts)</code><br><img src="gallery/geometry_simple_polygon_through_points_tgen.svg" alt="tgen sample"> |

## Strings and hashing

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Regex / pattern strings | Yes<br><code>rnd.next("[a-z]{10}") / rnds.random(pattern)</code> | Yes<br><code>str("[a-z]{10}").gen()</code> | **jngen:** Non-uniform<br>**tgen:** Uniform | **jngen:** testlib-compatible pattern syntax<br>**tgen:** **O(n)**; uniform over matches when each string has a unique parse<br>Same testlib-style regex syntax. **tgen** samples uniformly among matches (documented); **jngen** explicitly does not — e.g. rnd.next("[1-9][0-9]{1,2}") does not yield uniform digit strings. | — |
| Polynomial hash collision strings (signed mod) | Yes<br><code>rnds.antiHash({{mod, base}, ...}, alphabet, len)</code> | Yes<br><code>hack::polynomial_hash_hack(alphabet, base, mod)</code> | **jngen:** Undocumented<br>**tgen:** Undocumented | **jngen:** Brute force; up to 2 mod/base pairs<br>**tgen:** Birthday attack; up to 2 (base, mod) pairs<br>Both generate colliding strings for rolling hash. | — |
| Polynomial hash collision (unsigned / power-of-two mod) | **No** | Yes<br><code>hack::unsigned_polynomial_hash_hack()</code> | — | **tgen:** **O(1)**; Thue–Morse construction | — |

## Adversarial / hack generators

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| std::unordered_set collision inputs | Yes<br><code>rnda.antiUnorderedSet(n, maxLoadFactor, reserve)</code> | Yes<br><code>hack::std_unordered(size)</code> | — | **jngen:** GCC 4.x only; tuned load factor/reserve<br>**tgen:** GCC multiplier-based collision keys<br>Overlap in purpose; different APIs and compiler support. | — |
| std::set collision strings | **No** | Yes<br><code>hack::string_set(size)</code> | — | **tgen:** Distinct strings with equal std::set ordering keys | — |
| Max-flow worst case (Dinitz / Edmonds-Karp) | **No** | Yes<br><code>hack::dinitz_worst_case(k, l)</code> | — | **tgen:** **O(k·l)** vertices; Zadeh network | — |
| Mo's algorithm worst-case queries | **No** | Yes<br><code>hack::mo(n, q)</code> | — | **tgen:** **O(q)** range queries on a path | — |
| SPFA TLE graph | **No** | Yes<br><code>hack::spfa_hack(n)</code> | — | **tgen:** **O(n)** vertices/edges; forces Ω(n²) relaxations | — |
| Stale-heap Dijkstra bug graph | **No** | Yes<br><code>hack::stale_heap_dijkstra_bug(n)</code> | — | **tgen:** Catches lazy Dijkstra without decrease-key / stale entries | — |
| Non-strict relaxation Dijkstra bug graph | **No** | Yes<br><code>hack::non_strict_relaxation_dijkstra_bug(n)</code> | — | **tgen:** Catches Dijkstra that relaxes on dist[v] == dist[u] + w | — |
| mt19937 XOR-hash collision mask | **No** | Yes<br><code>hack::mt19937_xor_hash_hack<T>()</code> | — | **tgen:** **O(1)**; bitmask for int or long long outputs | — |
| Segment-tree-beats worst case | **No** | Yes<br><code>hack::segment_tree_beats_hack(k, q)</code> | — | **tgen:** Initial array + q range chmin updates | — |
| Rotating calipers bug polygon | **No** | Yes<br><code>hack::naive_rotating_calipers_max_dist_bug()</code> | — | **tgen:** **O(1)**; fixed 6-vertex convex polygon | — |

## Other

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Built-in SVG visualization | Yes<br><code>Drawer d; d.polygon(...); d.dumpSvg("out.svg")</code> | **No** | — | **jngen:** Drawer for points, segments, circles, polygons. | — |

