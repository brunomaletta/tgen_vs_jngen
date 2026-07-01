#include "cases.h"

#include "../vendor/tgen/single_include/tgen.h"

#include <unordered_map>

namespace {

volatile uint64_t sink = 0;

void consume_graph(const tgen::graph::value &g) {
	sink += static_cast<uint64_t>(g.n()) + static_cast<uint64_t>(g.m());
	for (const auto &e : g.edges())
		sink +=
			static_cast<uint64_t>(e.first) + static_cast<uint64_t>(e.second);
}

void consume_tree(const tgen::tree::value &t) {
	sink +=
		static_cast<uint64_t>(t.n()) + static_cast<uint64_t>(t.edges().size());
	for (const auto &e : t.edges())
		sink +=
			static_cast<uint64_t>(e.first) + static_cast<uint64_t>(e.second);
}

void consume_polygon(
	const std::vector<tgen::geometry::point<long long>> &poly) {
	for (const auto &p : poly)
		sink += static_cast<uint64_t>(p.x()) + static_cast<uint64_t>(p.y());
}

void consume_list(const tgen::list<int>::value &list) {
	for (int i = 0; i < list.size(); ++i)
		sink += static_cast<uint64_t>(list[i]);
}

void consume_permutation(const tgen::permutation::value &perm) {
	for (int i = 0; i < perm.size(); ++i)
		sink += static_cast<uint64_t>(perm[i]);
}

void consume_string(const std::string &s) {
	for (unsigned char c : s)
		sink += c;
}

void consume_partition(const std::vector<int> &part) {
	for (int x : part)
		sink += static_cast<uint64_t>(x);
}

void consume_partition(const std::vector<uint64_t> &part) {
	for (uint64_t x : part)
		sink += x;
}

template <typename T>
void consume_partition_groups(const std::vector<std::vector<T>> &groups) {
	for (const auto &group : groups)
		for (const T &x : group)
			sink += static_cast<uint64_t>(x);
}

std::vector<tgen::geometry::point<long long>> polygon_through_points;

void register_cases(std::unordered_map<std::string, benchmark::CaseFn> &out) {
	const std::string str_pat = bench_str_regex_pattern();
	out["graph_connected_m_eq_n"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M).get_connected());
	};
	out["graph_connected_m_eq_2n"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M_2N).get_connected());
	};
	out["graph_gen"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M).gen());
	};
	out["graph_gen_m_eq_2n"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M_2N).gen());
	};
	out["graph_gen_skewed_m_eq_n"] = [] {
		consume_graph(tgen::graph::gen_skewed(
			BENCH_N, BENCH_M, BENCH_ELONGATION, BENCH_SPREAD_SMALL));
	};
	out["graph_gen_skewed_m_eq_2n"] = [] {
		consume_graph(tgen::graph::gen_skewed(
			BENCH_N, BENCH_M_2N, BENCH_ELONGATION, BENCH_SPREAD_LARGE));
	};
	out["graph_gen_skewed_distinct_worst"] = [] {
		consume_graph(tgen::graph::gen_skewed(
			BENCH_N, BENCH_M_DISTINCT_WORST, BENCH_ELONGATION,
			BENCH_SPREAD_SMALL));
	};
	out["tree_gen"] = [] { consume_tree(tgen::tree(BENCH_N).gen()); };
	out["tree_gen_skewed"] = [] {
		consume_tree(tgen::tree::gen_skewed(BENCH_N, BENCH_ELONGATION));
	};
	out["tree_gen_kruskal"] = [] {
		consume_tree(tgen::tree::gen_kruskal(BENCH_KRUSKAL_N));
	};
	out["list_all_different"] = [] {
		consume_list(tgen::list<int>(BENCH_LIST_ALL_DIFF_N, 1,
									 BENCH_LIST_ALL_DIFF_HI)
						 .all_different()
						 .gen());
	};
	out["list_random"] = [] {
		consume_list(tgen::list<int>(BENCH_LIST_RANDOM_N, 1, BENCH_LIST_RANDOM_HI)
						 .gen());
	};
	out["geometry_convex_polygon"] = [] {
		consume_polygon(tgen::geometry::random_convex_polygon(
			BENCH_N, 0, BENCH_CONVEX_COORD_MAX));
	};
	out["geometry_convex_polygon_strict"] = [] {
		consume_polygon(tgen::geometry::random_convex_polygon(
			BENCH_N, 0, BENCH_CONVEX_STRICT_COORD_MAX, true));
	};
	out["geometry_points_general_position"] = [] {
		consume_polygon(tgen::geometry::random_points_general_position(
			BENCH_N, 0, BENCH_GENERAL_POSITION_COORD_MAX));
	};
	out["geometry_points_general_position_small"] = [] {
		consume_polygon(tgen::geometry::random_points_general_position(
			BENCH_GENERAL_POSITION_SMALL_N, 0,
			BENCH_GENERAL_POSITION_COORD_MAX));
	};
	out["geometry_random_simple_polygon"] = [] {
		consume_polygon(tgen::geometry::random_simple_polygon(
			BENCH_GEOM_N, 0, BENCH_COORD_MAX));
	};
	out["geometry_random_orthogonal_polygon"] = [] {
		consume_polygon(tgen::geometry::random_orthogonal_polygon(
			BENCH_GEOM_N, 0, BENCH_COORD_MAX));
	};
	out["geometry_simple_polygon_through_points"] = [] {
		if (polygon_through_points.empty())
			polygon_through_points =
				tgen::geometry::random_points_general_position(
					BENCH_GEOM_N, 0, BENCH_COORD_MAX);
		consume_polygon(tgen::geometry::random_simple_polygon_through_points(
			polygon_through_points));
	};
	out["permutation_uniform"] = [] {
		consume_permutation(tgen::permutation(BENCH_PERM_N).gen());
	};
	out["graph_bipartite"] = [] {
		consume_graph(tgen::graph::gen_bipartite(
			BENCH_BIP_N1, BENCH_BIP_N2, BENCH_BIP_M));
	};
	out["graph_directed"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M, true).gen());
	};
	out["graph_directed_acyclic"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M, true).get_acyclic());
	};
	out["str_regex"] = [str_pat] {
		consume_string(tgen::str(str_pat).gen().to_std());
	};
	out["math_partition"] = [] {
		consume_partition(tgen::math::gen_partition(BENCH_PARTITION_N));
	};
	out["math_partition_fixed_size"] = [] {
		consume_partition(tgen::math::gen_partition_fixed_size(
			static_cast<int>(BENCH_PARTITION_FIXED_N), BENCH_PARTITION_K));
	};
	out["math_partition_fixed_size_fast"] = [] {
		consume_partition(tgen::math::gen_partition_fixed_size_fast(
			BENCH_PARTITION_FAST_N, BENCH_PARTITION_FAST_K));
	};
	out["math_partition_array"] = [] {
		std::vector<int> elements(BENCH_PARTITION_ARRAY_N);
		for (int i = 0; i < BENCH_PARTITION_ARRAY_N; ++i)
			elements[i] = i;
		consume_partition_groups(tgen::math::partition_elements(
			std::move(elements), BENCH_PARTITION_ARRAY_K));
	};
}

} // namespace

void tgen_init() { tgen::register_gen(42); }

void tgen_prepare_through_points() {
	polygon_through_points = tgen::geometry::random_points_general_position(
		BENCH_GEOM_N, 0, BENCH_COORD_MAX);
}

std::unordered_map<std::string, benchmark::CaseFn> tgen_cases() {
	std::unordered_map<std::string, benchmark::CaseFn> out;
	register_cases(out);
	return out;
}
