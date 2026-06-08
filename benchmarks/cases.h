#pragma once

#include "benchmark.h"

#include <unordered_map>
#include <vector>

#ifdef QUICK
constexpr int BENCH_N = 100'000;
#else
constexpr int BENCH_N = 1'000'000;
#endif

constexpr int BENCH_M = BENCH_N;
constexpr int BENCH_M_2N = 2 * BENCH_N;
constexpr int BENCH_M_DISTINCT_WORST = 2 * BENCH_N - 3;
constexpr int BENCH_LIST_HI = 2 * BENCH_N;
constexpr int BENCH_COORD_MAX = 3'000'000;
constexpr int BENCH_ELONGATION = 100;
constexpr int BENCH_SPREAD_SMALL = 2;
constexpr int BENCH_SPREAD_LARGE = 6;
// jngen convexPolygon requires hull(10n) to have >= n vertices; fails at large n.
constexpr int BENCH_CONVEX_N = 1000;

inline std::vector<benchmark::CaseSpec> all_case_specs() {
	return {
		{"graph_connected_m_eq_n", "graph::get_connected", " (m=n)",
		 "n=1e6, m=1e6", true},
		{"graph_connected_m_eq_2n", "graph::get_connected", " (m=2n)",
		 "n=1e6, m=2e6", true},
		{"graph_gen", "graph::gen", "", "n=1e6, m=1e6", true},
		{"graph_gen_skewed_m_eq_n", "graph::gen_skewed", " (m=n)",
		 "n=1e6, m=1e6, elongation=1e2, spread=2", true},
		{"graph_gen_skewed_m_eq_2n", "graph::gen_skewed", " (m=2n)",
		 "n=1e6, m=2e6, elongation=1e2, spread=6", true},
		{"graph_gen_skewed_distinct_worst", "graph::gen_skewed",
		 " (distinct worst)", "n=1e6, m=2n-3, elongation=1e2, spread=2", true},
		{"tree_gen", "tree::gen", "", "n=1e6", true},
		{"tree_gen_skewed", "tree::gen_skewed", "",
		 "n=1e6, elongation=1e2", true},
		{"list_all_different", "list<int>::gen", " (all_different)",
		 "n=1e6, value_left=1, value_right=2e6", true},
		{"geometry_convex_polygon", "geometry::random_convex_polygon", "",
		 "n=1000, min=0, max=3e6", true},
		{"geometry_points_general_position",
		 "geometry::random_points_general_position", "",
		 "n=1e6, min=0, max=3e6", false},
		{"geometry_random_simple_polygon", "geometry::random_simple_polygon",
		 "", "n=1e6, min=0, max=3e6", false},
		{"geometry_simple_polygon_through_points",
		 "geometry::random_simple_polygon_through_points", "", "n=1e6", false},
	};
}
