#pragma once

#include "benchmark.h"

#include <string>
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
#ifdef QUICK
constexpr int BENCH_LIST_ALL_DIFF_N = 320'000;
constexpr int BENCH_LIST_ALL_DIFF_HI = 2 * BENCH_LIST_ALL_DIFF_N;
constexpr int BENCH_LIST_RANDOM_N = 700'000;
constexpr int BENCH_LIST_RANDOM_HI = 2 * BENCH_LIST_RANDOM_N;
#else
constexpr int BENCH_LIST_ALL_DIFF_N = 5'000'000;
constexpr int BENCH_LIST_ALL_DIFF_HI = 2 * BENCH_LIST_ALL_DIFF_N;
constexpr int BENCH_LIST_RANDOM_N = 5'000'000;
constexpr int BENCH_LIST_RANDOM_HI = 2 * BENCH_LIST_RANDOM_N;
#endif
#ifdef QUICK
constexpr int BENCH_STR_LEN = 500'000;
constexpr int BENCH_PERM_N = 500'000;
#else
constexpr int BENCH_STR_LEN = 10'000'000;
constexpr int BENCH_PERM_N = 5'000'000;
#endif

inline std::string bench_str_regex_pattern() {
	// 4-char units: digit block | hex block | literal pair repeat.
	const int repeats = BENCH_STR_LEN / 4;
	return "(([1-9][0-9]{3}|[A-F]{4})|(ab|cd){2}){" +
		   std::to_string(repeats) + "}";
}
// tgen general-position needs max - min >= prime_from(2n) - 1.
constexpr int BENCH_COORD_MAX = 3 * BENCH_GEOM_N;
constexpr int BENCH_ELONGATION = 100;
constexpr int BENCH_SPREAD_SMALL = 2;
constexpr int BENCH_SPREAD_LARGE = 6;
// Shared geometry head-to-head params (same n and range for tgen and jngen).
// jngen convexPolygon subsamples hull(10n); needs a wide range at large n.
constexpr long long BENCH_GENERAL_POSITION_COORD_MAX = 3'000'000LL;
#ifdef QUICK
constexpr long long BENCH_CONVEX_COORD_MAX = 3LL * BENCH_N;
constexpr long long BENCH_CONVEX_STRICT_COORD_MAX = 1'000'000'000'000LL;
constexpr const char *BENCH_PARAMS_CONVEX = "n=1e5, min=0, max=3e5, strict=false";
constexpr const char *BENCH_PARAMS_CONVEX_STRICT =
	"n=1e5, min=0, max=1e12, strict=true";
constexpr const char *BENCH_PARAMS_GENERAL_POSITION = "n=1e5, min=0, max=3e6";
constexpr const char *BENCH_GENERAL_POSITION_SUFFIX = "";
#else
constexpr long long BENCH_CONVEX_COORD_MAX = 30'000'000'000LL;
constexpr long long BENCH_CONVEX_STRICT_COORD_MAX = 1'000'000'000'000LL;
constexpr const char *BENCH_PARAMS_CONVEX = "n=1e6, min=0, max=3e10, strict=false";
constexpr const char *BENCH_PARAMS_CONVEX_STRICT =
	"n=1e6, min=0, max=1e12, strict=true";
constexpr const char *BENCH_PARAMS_GENERAL_POSITION = "n=1e6, min=0, max=3e6";
constexpr const char *BENCH_GENERAL_POSITION_SUFFIX = "";
#endif

#ifdef QUICK
constexpr int BENCH_KRUSKAL_N = 100'000;
constexpr const char *BENCH_PARAMS_KRUSKAL = "n=1e5";
#else
constexpr int BENCH_KRUSKAL_N = 1'000'000;
constexpr const char *BENCH_PARAMS_KRUSKAL = "n=1e6";
#endif

#ifdef QUICK
constexpr const char *BENCH_PARAMS_N = "n=1e5";
constexpr const char *BENCH_PARAMS_PERM = "n=5e5";
constexpr const char *BENCH_PARAMS_N_M = "n=1e5, m=1e5";
constexpr const char *BENCH_PARAMS_N_M_2N = "n=1e5, m=2e5";
constexpr const char *BENCH_PARAMS_N_M_2N_3 = "n=1e5, m=2n-3";
constexpr const char *BENCH_PARAMS_LIST =
	"n=3.2e5, value_left=1, value_right=6.4e5";
constexpr const char *BENCH_PARAMS_LIST_RANDOM =
	"n=7e5, value_left=1, value_right=14e5";
constexpr const char *BENCH_PARAMS_STR_REGEX =
	"pattern=(([1-9][0-9]{3}|[A-F]{4})|(ab|cd){2}){r}, len=5e5";
constexpr const char *BENCH_PARAMS_GEOM = "n=1e5, min=0, max=3e5, strict=false";
constexpr const char *BENCH_PARAMS_THROUGH = "n=1e5";
constexpr const char *BENCH_PARAMS_SKEWED_N =
	"n=1e5, m=1e5, elongation=1e2, spread=2";
constexpr const char *BENCH_PARAMS_SKEWED_2N =
	"n=1e5, m=2e5, elongation=1e2, spread=6";
constexpr const char *BENCH_PARAMS_SKEWED_WORST =
	"n=1e5, m=2n-3, elongation=1e2, spread=2";
constexpr const char *BENCH_PARAMS_TREE_SKEWED = "n=1e5, elongation=1e2";
constexpr int BENCH_BIP_N1 = 100;
constexpr int BENCH_BIP_N2 = 100;
constexpr int BENCH_BIP_M = 5'000;
constexpr const char *BENCH_PARAMS_BIPARTITE = "n1=1e2, n2=1e2, m=5e3";
constexpr int BENCH_PARTITION_N = 480'000;
constexpr long long BENCH_PARTITION_FIXED_N = 5'000'000LL;
constexpr const char *BENCH_PARAMS_PARTITION = "n=4.8e5";
constexpr const char *BENCH_PARAMS_PARTITION_FIXED = "n=5e6, k=10, part_left=0";
constexpr uint64_t BENCH_PARTITION_FAST_N = 5'000'000ULL;
constexpr int BENCH_PARTITION_FAST_K = 10;
constexpr const char *BENCH_PARAMS_PARTITION_FAST = "n=5e6, k=10, part_left=0";
constexpr int BENCH_PARTITION_ARRAY_K = 100'000;
constexpr const char *BENCH_PARAMS_PARTITION_ARRAY = "n=1e5, k=1e5";
#else
constexpr const char *BENCH_PARAMS_N = "n=1e6";
constexpr const char *BENCH_PARAMS_PERM = "n=5e6";
constexpr const char *BENCH_PARAMS_N_M = "n=1e6, m=1e6";
constexpr const char *BENCH_PARAMS_N_M_2N = "n=1e6, m=2e6";
constexpr const char *BENCH_PARAMS_N_M_2N_3 = "n=1e6, m=2n-3";
constexpr const char *BENCH_PARAMS_LIST =
	"n=5e6, value_left=1, value_right=10e6";
constexpr const char *BENCH_PARAMS_LIST_RANDOM =
	"n=5e6, value_left=1, value_right=10e6";
constexpr const char *BENCH_PARAMS_STR_REGEX =
	"pattern=(([1-9][0-9]{3}|[A-F]{4})|(ab|cd){2}){r}, len=1e7";
constexpr const char *BENCH_PARAMS_GEOM = "n=1e6, min=0, max=3e6, strict=false";
constexpr const char *BENCH_PARAMS_THROUGH = "n=1e6";
constexpr const char *BENCH_PARAMS_SKEWED_N =
	"n=1e6, m=1e6, elongation=1e2, spread=2";
constexpr const char *BENCH_PARAMS_SKEWED_2N =
	"n=1e6, m=2e6, elongation=1e2, spread=6";
constexpr const char *BENCH_PARAMS_SKEWED_WORST =
	"n=1e6, m=2n-3, elongation=1e2, spread=2";
constexpr const char *BENCH_PARAMS_TREE_SKEWED = "n=1e6, elongation=1e2";
constexpr int BENCH_BIP_N1 = 1'000;
constexpr int BENCH_BIP_N2 = 1'000;
constexpr int BENCH_BIP_M = 500'000;
constexpr const char *BENCH_PARAMS_BIPARTITE = "n1=1e3, n2=1e3, m=5e5";
constexpr int BENCH_PARTITION_N = 4'800'000;
constexpr long long BENCH_PARTITION_FIXED_N = 50'000'000LL;
constexpr const char *BENCH_PARAMS_PARTITION = "n=4.8e6";
constexpr const char *BENCH_PARAMS_PARTITION_FIXED = "n=5e7, k=10, part_left=0";
constexpr uint64_t BENCH_PARTITION_FAST_N = 1'000'000'000'000'000'000ULL;
constexpr int BENCH_PARTITION_FAST_K = 3'000'000;
constexpr const char *BENCH_PARAMS_PARTITION_FAST = "n=1e18, k=3e6, part_left=0";
constexpr int BENCH_PARTITION_ARRAY_K = 1'000'000;
constexpr const char *BENCH_PARAMS_PARTITION_ARRAY = "n=1e6, k=1e6";
#endif

constexpr int BENCH_PARTITION_K = 10;
constexpr int BENCH_PARTITION_ARRAY_N = BENCH_N;

inline std::vector<benchmark::CaseSpec> all_case_specs() {
	return {
		{"graph_connected_m_eq_n", "graph::get_connected", " (m=n)",
		 BENCH_PARAMS_N_M, true},
		{"graph_connected_m_eq_2n", "graph::get_connected", " (m=2n)",
		 BENCH_PARAMS_N_M_2N, true},
		{"graph_gen", "graph::gen", " (m=n)", BENCH_PARAMS_N_M, true},
		{"graph_gen_m_eq_2n", "graph::gen", " (m=2n)", BENCH_PARAMS_N_M_2N,
		 true},
		{"graph_gen_skewed_m_eq_n", "graph::gen_skewed", " (m=n)",
		 BENCH_PARAMS_SKEWED_N, true},
		{"graph_gen_skewed_m_eq_2n", "graph::gen_skewed", " (m=2n)",
		 BENCH_PARAMS_SKEWED_2N, true},
		{"graph_gen_skewed_distinct_worst", "graph::gen_skewed",
		 " (distinct worst)", BENCH_PARAMS_SKEWED_WORST, true},
		{"tree_gen", "tree::gen", "", BENCH_PARAMS_N, true},
		{"tree_gen_skewed", "tree::gen_skewed", "",
		 BENCH_PARAMS_TREE_SKEWED, true},
		{"tree_gen_kruskal", "tree::gen_kruskal", "", BENCH_PARAMS_KRUSKAL,
		 true},
		{"list_all_different", "list<int>::gen", " (all_different)",
		 BENCH_PARAMS_LIST, true},
		{"list_random", "list<int>::gen", "", BENCH_PARAMS_LIST_RANDOM, true},
		{"geometry_convex_polygon", "geometry::random_convex_polygon",
		 " (non strict)", BENCH_PARAMS_CONVEX, false},
		{"geometry_convex_polygon_strict", "geometry::random_convex_polygon",
		 " (strict)", BENCH_PARAMS_CONVEX_STRICT, true},
		{"geometry_points_general_position",
		 "geometry::random_points_general_position",
		 BENCH_GENERAL_POSITION_SUFFIX, BENCH_PARAMS_GENERAL_POSITION, true},
		{"geometry_random_simple_polygon", "geometry::random_simple_polygon",
		 "", BENCH_PARAMS_GEOM, false},
		{"geometry_random_orthogonal_polygon",
		 "geometry::random_orthogonal_polygon", "", BENCH_PARAMS_GEOM, false},
		{"geometry_simple_polygon_through_points",
		 "geometry::random_simple_polygon_through_points", "",
		 BENCH_PARAMS_THROUGH, false},
		{"permutation_uniform", "permutation::gen", "", BENCH_PARAMS_PERM,
		 true},
		{"graph_bipartite", "graph::gen_bipartite", "", BENCH_PARAMS_BIPARTITE,
		 true},
		{"graph_directed", "graph::gen", " (directed)", BENCH_PARAMS_N_M,
		 true},
		{"graph_directed_acyclic", "graph::get_acyclic", " (DAG)",
		 BENCH_PARAMS_N_M, true},
		{"str_regex", "str::gen", "", BENCH_PARAMS_STR_REGEX, true},
		{"math_partition", "math::gen_partition", "", BENCH_PARAMS_PARTITION,
		 false},
		{"math_partition_fixed_size", "math::gen_partition_fixed_size", "",
		 BENCH_PARAMS_PARTITION_FIXED, false},
		{"math_partition_fixed_size_fast", "math::gen_partition_fixed_size_fast",
		 "", BENCH_PARAMS_PARTITION_FAST, true},
		{"math_partition_array", "math::partition_elements", "",
		 BENCH_PARAMS_PARTITION_ARRAY, true},
	};
}
