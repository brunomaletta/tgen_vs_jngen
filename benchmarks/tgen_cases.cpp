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

std::vector<tgen::geometry::point<long long>> polygon_through_points;

void register_cases(std::unordered_map<std::string, benchmark::CaseFn> &out) {
	out["graph_connected_m_eq_n"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M).get_connected());
	};
	out["graph_connected_m_eq_2n"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M_2N).get_connected());
	};
	out["graph_gen"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M).gen());
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
	out["list_all_different"] = [] {
		consume_list(tgen::list<int>(BENCH_N, 1, BENCH_LIST_HI)
						 .all_different()
						 .gen());
	};
	out["geometry_convex_polygon"] = [] {
		consume_polygon(tgen::geometry::random_convex_polygon(
			BENCH_CONVEX_N, 0, BENCH_CONVEX_COORD_MAX));
	};
	out["geometry_points_general_position"] = [] {
		consume_polygon(tgen::geometry::random_points_general_position(
			BENCH_GEOM_N, 0, BENCH_COORD_MAX));
	};
	out["geometry_random_simple_polygon"] = [] {
		consume_polygon(tgen::geometry::random_simple_polygon(
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
		consume_permutation(tgen::permutation(BENCH_N).gen());
	};
	out["graph_bipartite"] = [] {
		consume_graph(tgen::graph::gen_bipartite(
			BENCH_BIP_N1, BENCH_BIP_N2, BENCH_BIP_M));
	};
	out["graph_directed"] = [] {
		consume_graph(tgen::graph(BENCH_N, BENCH_M, true).gen());
	};
	out["geometry_convex_polygon_tgen_n1e6"] = [] {
		consume_polygon(tgen::geometry::random_convex_polygon(
			BENCH_N, 0, BENCH_CONVEX_TGEN_COORD_MAX));
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
