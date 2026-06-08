# tgen vs jngen — Feature Comparison

*Generated 2026-06-08 02:50 UTC*

> **Styled tables and geometry samples:** [view on GitHub Pages](https://brunomaletta.github.io/tgen_vs_jngen/). GitHub's Markdown renderer cannot reproduce the HTML layout.

Comparison of non-trivial generation operations. See [benchmarks.md](benchmarks.md) for timing results.

## Graphs

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Connected random graph | Yes<br><code>Graph::random(n, m).connected()</code> | Yes<br><code>graph(n, m).get_connected()</code> | **jngen:**<br>Non‑uniform<br>**tgen:**<br>Non‑uniform | **jngen:** **O(n + m)** expected (inferred); Prüfer spanning tree + rejection edge add<br>**tgen:** **O(n + m log n)**; Prüfer spanning tree + rejection edge add<hr>Same Prüfer tree + rejection edge add. Neither uniform over all connected labeled graphs. | **jngen:** 1263 ms<br>**tgen:** 1214 ms<br>0.96x<br><sub>n=1e6, m=1e6</sub> |
| Random graph with fixed n, m | Yes<br><code>Graph::random(n, m)</code> | Yes<br><code>graph(n, m).gen()</code> | **jngen:**<br>Non‑uniform (inferred)<br>**tgen:**<br>Uniform | **jngen:** **O(n + m)** expected (inferred); rejection on random vertex pairs<br>**tgen:** **O(n + m log n)**; rejection with constraint machinery<hr>**tgen** documents uniform sampling among valid graphs; **jngen** does not. | **jngen:** 578 ms<br>**tgen:** 892 ms<br>1.54x<br><sub>n=1e6, m=1e6</sub> |
| Skewed / stretched connected graph | Yes<br><code>Graph::randomStretched(n, m, elongation, spread)</code> | Yes<br><code>graph::gen_skewed(n, m, elongation, spread)</code> | **jngen:**<br>Non‑uniform<br>**tgen:**<br>Non‑uniform | **jngen:** **O(n + m)** expected (inferred); randomPrim backbone + parent-hop edges; may throw after 1000 failures<br>**tgen:** **O(n + m log n)**; wnext backbone + ancestor-biased edges<hr>Both intentionally biased toward high diameter. Parent-hop semantics differ slightly (k in [2, spread] vs up to spread hops). | **jngen:** 755 ms<br>**tgen:** 190 ms<br>0.25x<br><sub>n=1e6, m=1e6, elongation=1e2, spread=2</sub> |
| Graph modifiers (directed, multi, acyclic, loops) | Yes<br><code>Graph::random(...).directed().allowMulti().acyclic()<br>...</code> | Yes<br><code>graph(...).directed().multi().acyclic()...</code> | **jngen:**<br>Varies (inferred)<br>**tgen:**<br>Varies | **jngen:** **O(n + m)** expected (inferred); same as Graph::random with modifier traits<br>**tgen:** Declarative constraint composition<hr>Both support modifier chains; **tgen** documents uniformity where promised. | — |
| Bipartite graph (random / complete) | Yes<br><code>Graph::randomBipartite(n1, n2, m), completeBipartite(n1, n2)</code> | Yes<br><code>graph::gen_bipartite(n1, n2, m), K(n1, n2)</code> | **jngen:**<br>Non‑uniform (inferred)<br>**tgen:**<br>Uniform | **jngen:** **O(n1 + n2 + m)** expected (inferred); rejection on random cross edges<br>**tgen:** **O(n1 + n2 + m log(n1 + n2)**); uniform cross edges<hr>Both support random and complete bipartite graphs. **tgen** documents uniform sampling among valid bipartite graphs with m edges. | **jngen:** 206 ms<br>**tgen:** 874 ms<br>4.24x<br><sub>n1=1e3, n2=1e3, m=5e5</sub> |
| Complete and named graphs | Yes<br><code>Graph::complete(n), completeBipartite(n1, n2)</code> | Yes<br><code>K(n), K(n1,n2), C(n), P(n), S(n) graph helpers</code> | **jngen:**<br>Varies<br>**tgen:**<br>Varies | **jngen:** **O(n²)** (inferred); deterministic edge lists<br>**tgen:** **O(n²)** edges for cliques; **O(n)** for path/star/cycle<hr>**tgen** exposes more named helpers (cycle, path, star as graphs). completeBipartite is deterministic. | — |
| Directed / acyclic random graph | Yes<br><code>Graph::random(n, m).directed().acyclic().g()</code> | Yes<br><code>graph(n, m, directed=true).gen(), .get_acyclic()</code> | **jngen:**<br>Non‑uniform (inferred)<br>**tgen:**<br>Varies | **jngen:** **O(n + m)** expected (inferred); rejection + acyclic shuffle when needed<br>**tgen:** **O(n + m log n)**; same rejection machinery with directed constraints<hr>Comparable directed sampling via modifier chains. **tgen** documents uniformity for some constrained variants. | **jngen:** 623 ms<br>**tgen:** 416 ms<br>0.67x<br><sub>n=1e6, m=1e6</sub> |
| Weighted graphs and trees | Yes<br><code>Graph::setVertexWeights / setEdgeWeight<br>; Tree inherits graph weights</code> | Yes<br><code>wgraph / wtree (vertex- and edge-weighted variants)</code> | **jngen:**<br>Non‑uniform (inferred)<br>**tgen:**<br>Non‑uniform (inferred) | **jngen:** **O(n + m)** (inferred); base generator + weight assignment<br>**tgen:** Same generators as unweighted, plus weight assignment | — |

## Trees

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Random labeled tree | Yes<br><code>Tree::random(n)</code> | Yes<br><code>tree(n).gen()</code> | **jngen:**<br>Uniform<br>**tgen:**<br>Uniform | **jngen:** **O(n)**; Prüfer sequence<br>**tgen:** **O(n)**; Prüfer sequence<hr>Same Prüfer algorithm. **jngen** prints sorted edges rooted at 0 by default. | **jngen:** 690 ms<br>**tgen:** 579 ms<br>0.84x<br><sub>n=1e6</sub> |
| Rooted tree output / edge order | Yes<br><code>Tree::random(n)<br>; .println() / Repr with printEdges, shuffle</code> | Yes<br><code>tree(n).gen()<br>; stream output with configurable 1-based vertices</code> | **jngen:**<br>Undocumented<br>**tgen:**<br>Undocumented | **jngen:** **O(n)** (inferred)<br>**tgen:** **O(n)** generation; **O(n)** print<hr>**jngen** defaults to sorted edges rooted at vertex 0. **tgen** uses declarative print helpers and 0-based internal indices. | — |
| Skewed tree (wnext / Prim-like) | Yes<br><code>Tree::randomPrim(n, elongation)</code> | Yes<br><code>tree::gen_skewed(n, elongation)</code> | **jngen:**<br>Non‑uniform<br>**tgen:**<br>Non‑uniform | **jngen:** **O(n)**; same wnext process<br>**tgen:** **O(n)**; parent(i) = wnext(i, elongation)<hr>Equivalent algorithms. Large positive elongation → path; large negative → star. | **jngen:** 250 ms<br>**tgen:** 161 ms<br>0.64x<br><sub>n=1e6, elongation=1e2</sub> |
| Named tree shapes (star, path, caterpillar, k-ary) | Yes<br><code>Tree::star, bamboo, caterpillar, binary, kary, ...</code> | Yes<br><code>S(n) star, P(n) path; no caterpillar/binary/k-ary</code> | **jngen:**<br>Varies (inferred) | **jngen:** **O(n)** (inferred)<br>**tgen:** **O(n)**; standard graph helpers (also valid trees)<hr>**tgen** exposes star and path as graph helpers; **jngen** has a richer set of named tree generators. | — |
| Random tree (Kruskal-like) | Yes<br><code>Tree::randomKruskal(n)</code> | **No** | **jngen:**<br>Non‑uniform | **jngen:** **O(n²)** expected (inferred); rejection until connected | — |

## Lists and sequences

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Distinct values in range | Yes<br><code>Array::randomUnique(k, lo, hi)</code> | Yes<br><code>list<int>(k, lo, hi).all_different().gen()</code> | **jngen:**<br>Uniform<br>**tgen:**<br>Uniform | **jngen:** **O(k log k)** expected (inferred); hash-set rejection<br>**tgen:** **O(k log k)**; Fisher–Yates + forbidden-value map<hr>Both produce uniform distinct samples. | **jngen:** 254 ms<br>**tgen:** 1884 ms<br>7.42x<br><sub>n=1e6, value_left=1, value_right=2e6</sub> |
| Uniform random permutation | Yes<br><code>Array::id(n).shuffled()</code> | Yes<br><code>permutation(n).gen()</code> | **jngen:**<br>Uniform<br>**tgen:**<br>Uniform | **jngen:** **O(n)**<br>**tgen:** **O(n)** | **jngen:** 17 ms<br>**tgen:** 12 ms<br>0.71x<br><sub>n=1e6</sub> |
| Pairs, tuples, structured printing | Yes<br><code>Array / Graph .println(), Repr modifiers (shuffle, reverse, edges)</code> | Yes<br><code>pair(...), list/str/... with << and multi-line tuple layout</code> | **jngen:**<br>Undocumented<br>**tgen:**<br>Varies | **jngen:** **O(output size)** (inferred)<br>**tgen:** **O(output size)**<hr>**tgen** has first-class pair/tuple generators and stream formatting. **jngen** focuses on testlib-style println helpers. | — |
| Declarative constraints (sorted, palindrome, cycles) | **No** | Yes<br><code>list/str/permutation/pair with .sorted(), .palindrome(), .cycles()...</code> | **tgen:**<br>Varies | **tgen:** Constraint-based uniform sampling where documented | — |

## Math

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Ordered partition into k parts (composition) | Yes<br><code>rndm.partition(n, numParts, minSize, maxSize)</code> | Yes<br><code>math::gen_partition_fixed_size(n, k, part_left, part_right)</code> | **jngen:**<br>Non‑uniform<br>**tgen:**<br>Uniform | **jngen:** **O(k log k)** (inferred); random delimiters, sort, heuristic redistribution<br>**tgen:** **O(n)** stars-and-bars (unbounded parts) or **O(n·k)** DP with bounds<hr>Different algorithms and semantics. **tgen** returns an ordered composition sampled uniformly. **jngen** sorts parts in non-increasing order (not a uniform composition); source comments that bounded redistribution 'need a smarter way'. | — |
| Ordered partition, variable number of parts | **No** | Yes<br><code>math::gen_partition(n, part_left, part_right)</code> | **tgen:**<br>Uniform | **tgen:** **O(n)**; DP in log space | — |
| Random prime in range | Yes<br><code>rndm.randomPrime(l, r)</code> | Yes<br><code>math::gen_prime(left, right)</code> | **jngen:**<br>Uniform (inferred)<br>**tgen:**<br>Uniform | **jngen:** **O((r−l)** log r) worst case (inferred); Miller–Rabin rejection<br>**tgen:** **O(log³ n)** expected<hr>**tgen** documents uniform sampling among primes in the interval. | — |
| Random integer with congruence constraints | **No** | Yes<br><code>math::gen_congruent(l, r, rems, mods)</code> | **tgen:**<br>Uniform | **tgen:** **O(|mods| + log r)** | — |
| Partition array into k groups | Yes<br><code>rndm.partition(elements, numParts, minSize, maxSize)</code> | **No** | **jngen:**<br>Non‑uniform | **jngen:** **O(n + k log k)** (inferred); shuffle + partition sizes + split | — |

## Geometry

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Random convex polygon | Yes<br><code>rndg.convexPolygon(n, min, max)</code> | Yes<br><code>geometry::random_convex_polygon(n, min, max)</code> | **jngen:**<br>Non‑uniform<br>**tgen:**<br>Non‑uniform | **jngen:** **O(n log n)** (inferred); hull of 10n ellipse points, subsample n<br>**tgen:** **O(n log n)**; Valtr construction filling bounding box<hr>Different shape distributions. **jngen** needs a large coordinate range at high n (hull subsampling); benchmark uses n=3.6e5, max=3e9 for both. | **jngen:** 968 ms<br>**tgen:** 498 ms<br>0.51x<br><sub>n=3.6e5, min=0, max=3e9</sub> |
| Points in general position (no three collinear) | Yes<br><code>rndg.pointsInGeneralPosition(n, min, max)</code> | Yes<br><code>geometry::random_points_general_position(n, min, max)</code> | **jngen:**<br>Non‑uniform (inferred)<br>**tgen:**<br>Non‑uniform | **jngen:** **O(n² log n)** expected (inferred); rejection until no collinearity<br>**tgen:** **O(n)**; algebraic construction over F_p<hr>Not benchmarked head-to-head: **jngen** is asymptotically slower. | **tgen:** 150 ms<br><sub>n=1e6, min=0, max=3e6</sub> |
| Random simple polygon | **No** | Yes<br><code>geometry::random_simple_polygon(n, min, max)</code> | **tgen:**<br>Non‑uniform | **tgen:** **O(n log n)** expected; points + polygonization | **tgen:** 1234 ms<br><sub>n=1e6, min=0, max=3e6</sub> |
| Simple polygon through given points | **No** | Yes<br><code>geometry::random_simple_polygon_through_points(pts)</code> | **tgen:**<br>Non‑uniform | **tgen:** **O(n log n)** expected; randomized divide-and-conquer Hamiltonian path | **tgen:** 1097 ms<br><sub>n=1e6</sub> |
| Random convex polygon at n=1e6 (tgen scale) | **No** | Yes<br><code>geometry::random_convex_polygon(1e6, min, max)</code> | **tgen:**<br>Non‑uniform | **tgen:** **O(n log n)**; Valtr construction<hr>**jngen** convexPolygon needs hull(10n) vertices and large coordinates; practical n is much lower at the same max coordinate. | **tgen:** 2070 ms<br><sub>n=1e6, min=0, max=3e9</sub> |

### Samples

| Operation | jngen | tgen |
|-----------|-------|------|
| Random convex polygon | Yes<br><code>rndg.convexPolygon(n, min, max)</code><br><sub>n=80, min=0, max=1000</sub><br><img src="gallery/geometry_convex_polygon_jngen.svg" alt="jngen sample"><br><sub>n=15000, min=0, max=3e9</sub><br><img src="gallery/geometry_convex_polygon_large_jngen.svg" alt="jngen sample"> | Yes<br><code>geometry::random_convex_polygon(n, min, max)</code><br><sub>n=80, min=0, max=1000</sub><br><img src="gallery/geometry_convex_polygon_tgen.svg" alt="tgen sample"><br><sub>n=15000, min=0, max=3e9</sub><br><img src="gallery/geometry_convex_polygon_large_tgen.svg" alt="tgen sample"> |
| Points in general position (no three collinear) | Yes<br><code>rndg.pointsInGeneralPosition(n, min, max)</code><br><sub>n=2000, min=0, max=3e6</sub><br><img src="gallery/geometry_points_general_position_jngen.svg" alt="jngen sample"> | Yes<br><code>geometry::random_points_general_position(n, min, max)</code><br><sub>n=2000, min=0, max=3e6</sub><br><img src="gallery/geometry_points_general_position_tgen.svg" alt="tgen sample"> |
| Random simple polygon | **No** | Yes<br><code>geometry::random_simple_polygon(n, min, max)</code><br><sub>n=80, min=0, max=1000</sub><br><img src="gallery/geometry_simple_polygon_tgen.svg" alt="tgen sample"> |
| Simple polygon through given points | **No** | Yes<br><code>geometry::random_simple_polygon_through_points(pts)</code><br><sub>10×10 input grid, min=0, max=1000</sub><br><img src="gallery/geometry_simple_polygon_through_points_tgen.svg" alt="tgen sample"> |

## Strings

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Regex / pattern strings | Yes<br><code>rnd.next("[a-z]{10}") / rnds.random(pattern)</code> | Yes<br><code>str("[a-z]{10}").gen()</code> | **jngen:**<br>Non‑uniform<br>**tgen:**<br>Uniform | **jngen:** **O(output length)** (inferred); testlib-compatible pattern generation<br>**tgen:** **O(n)**; uniform over matches when each string has a unique parse<hr>Same testlib-style regex syntax. **tgen** samples uniformly among matches (documented); **jngen** explicitly does not — e.g. rnd.next("[1-9][0-9]{1,2}") does not yield uniform digit strings. | — |

## Hacks

| Operation | jngen | tgen | Uniformity | Complexity / notes | Benchmark |
|-----------|-------|------|------------|-------------------|-----------|
| Polynomial hash collision strings (signed mod) | Yes<br><code>rnds.antiHash({{mod, base}, ...}, alphabet, len)</code> | Yes<br><code>hack::polynomial_hash_hack(alphabet, base, mod)</code> | **jngen:**<br>Undocumented<br>**tgen:**<br>Undocumented | **jngen:** **O(√mod)** expected (inferred); brute force over short strings<br>**tgen:** Birthday attack; up to 2 (base, mod) pairs<hr>Deterministic collision construction, not random sampling. Both generate colliding strings for rolling hash. | — |
| Polynomial hash collision (unsigned / power-of-two mod) | **No** | Yes<br><code>hack::unsigned_polynomial_hash_hack()</code> | — | **tgen:** **O(1)**; Thue–Morse construction | — |
| std::unordered_set collision inputs | Yes<br><code>rnda.antiUnorderedSet(n, maxLoadFactor, reserve)</code> | Yes<br><code>hack::std_unordered(size)</code> | — | **jngen:** GCC 4.x only; tuned load factor/reserve<br>**tgen:** GCC multiplier-based collision keys<hr>Overlap in purpose; different APIs and compiler support. | — |
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
| testlib integration | Yes<br><code>registerGen, global rnd/rndm/rndg, testlib-compatible patterns</code> | **No** | — | **jngen** is built on testlib. **tgen** is a standalone header with register_gen and its own constraint API. | — |
| Built-in SVG visualization | Yes<br><code>Drawer d; d.polygon(...); d.dumpSvg("out.svg")</code> | **No** | — | **jngen:** Drawer for points, segments, circles, polygons. | — |

