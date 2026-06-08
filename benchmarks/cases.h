#pragma once

#include "benchmark.h"

#include <unordered_map>
#include <vector>

#ifdef QUICK
constexpr int BENCH_N = 100'000;
#else
constexpr int BENCH_N = 1'000'000;
#endif

constexpr int BENCH_GEOM_N = BENCH_N;
constexpr int BENCH_M = BENCH_N;
constexpr int BENCH_M_2N = 2 * BENCH_N;
constexpr int BENCH_M_DISTINCT_WORST = 2 * BENCH_N - 3;
constexpr int BENCH_LIST_HI = 2 * BENCH_N;
// tgen general-position needs max - min >= prime_from(2n) - 1.
constexpr int BENCH_COORD_MAX = 3 * BENCH_GEOM_N;
constexpr int BENCH_ELONGATION = 100;
constexpr int BENCH_SPREAD_SMALL = 2;
constexpr int BENCH_SPREAD_LARGE = 6;
// jngen convexPolygon needs hull(10n) >= n vertices; max n grows with coordinate range.
#ifdef QUICK
constexpr int BENCH_CONVEX_N = 10'000;
constexpr int BENCH_CONVEX_COORD_MAX = 3 * BENCH_N;
constexpr const char *BENCH_PARAMS_CONVEX = "n=1e4, min=0, max=3e5";
#else
constexpr int BENCH_CONVEX_N = 360'000;
constexpr long long BENCH_CONVEX_COORD_MAX = 3'000'000'000LL;
constexpr const char *BENCH_PARAMS_CONVEX = "n=3.6e5, min=0, max=3e9";
#endif

#ifdef QUICK
constexpr const char *BENCH_PARAMS_N = "n=1e5";
constexpr const char *BENCH_PARAMS_N_M = "n=1e5, m=1e5";
constexpr const char *BENCH_PARAMS_N_M_2N = "n=1e5, m=2e5";
constexpr const char *BENCH_PARAMS_N_M_2N_3 = "n=1e5, m=2n-3";
constexpr const char *BENCH_PARAMS_LIST = "n=1e5, value_left=1, value_right=2e5";
constexpr const char *BENCH_PARAMS_GEOM = "n=1e5, min=0, max=3e5";
constexpr const char *BENCH_PARAMS_THROUGH = "n=1e5";
constexpr const char *BENCH_PARAMS_SKEWED_N =
	"n=1e5, m=1e5, elongation=1e2, spread=2";
constexpr const char *BENCH_PARAMS_SKEWED_2N =
	"n=1e5, m=2e5, elongation=1e2, spread=6";
constexpr const char *BENCH_PARAMS_SKEWED_WORST =
	"n=1e5, m=2n-3, elongation=1e2, spread=2";
constexpr const char *BENCH_PARAMS_TREE_SKEWED = "n=1e5, elongation=1e2";
#else
constexpr const char *BENCH_PARAMS_N = "n=1e6";
constexpr const char *BENCH_PARAMS_N_M = "n=1e6, m=1e6";
constexpr const char *BENCH_PARAMS_N_M_2N = "n=1e6, m=2e6";
constexpr const char *BENCH_PARAMS_N_M_2N_3 = "n=1e6, m=2n-3";
constexpr const char *BENCH_PARAMS_LIST = "n=1e6, value_left=1, value_right=2e6";
constexpr const char *BENCH_PARAMS_GEOM = "n=1e6, min=0, max=3e6";
constexpr const char *BENCH_PARAMS_THROUGH = "n=1e6";
constexpr const char *BENCH_PARAMS_SKEWED_N =
	"n=1e6, m=1e6, elongation=1e2, spread=2";
constexpr const char *BENCH_PARAMS_SKEWED_2N =
	"n=1e6, m=2e6, elongation=1e2, spread=6";
constexpr const char *BENCH_PARAMS_SKEWED_WORST =
	"n=1e6, m=2n-3, elongation=1e2, spread=2";
constexpr const char *BENCH_PARAMS_TREE_SKEWED = "n=1e6, elongation=1e2";
#endif

inline std::vector<benchmark::CaseSpec> all_case_specs() {
	return {
		{"graph_connected_m_eq_n", "graph::get_connected", " (m=n)",
		 BENCH_PARAMS_N_M, true},
		{"graph_connected_m_eq_2n", "graph::get_connected", " (m=2n)",
		 BENCH_PARAMS_N_M_2N, true},
		{"graph_gen", "graph::gen", "", BENCH_PARAMS_N_M, true},
		{"graph_gen_skewed_m_eq_n", "graph::gen_skewed", " (m=n)",
		 BENCH_PARAMS_SKEWED_N, true},
		{"graph_gen_skewed_m_eq_2n", "graph::gen_skewed", " (m=2n)",
		 BENCH_PARAMS_SKEWED_2N, true},
		{"graph_gen_skewed_distinct_worst", "graph::gen_skewed",
		 " (distinct worst)", BENCH_PARAMS_SKEWED_WORST, true},
		{"tree_gen", "tree::gen", "", BENCH_PARAMS_N, true},
		{"tree_gen_skewed", "tree::gen_skewed", "",
		 BENCH_PARAMS_TREE_SKEWED, true},
		{"list_all_different", "list<int>::gen", " (all_different)",
		 BENCH_PARAMS_LIST, true},
		{"geometry_convex_polygon", "geometry::random_convex_polygon", "",
		 BENCH_PARAMS_CONVEX, true},
		{"geometry_points_general_position",
		 "geometry::random_points_general_position", "",
		 BENCH_PARAMS_GEOM, false},
		{"geometry_random_simple_polygon", "geometry::random_simple_polygon",
		 "", BENCH_PARAMS_GEOM, false},
		{"geometry_simple_polygon_through_points",
		 "geometry::random_simple_polygon_through_points", "",
		 BENCH_PARAMS_THROUGH, false},
	};
}
