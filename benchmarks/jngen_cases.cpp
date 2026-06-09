#include "cases.h"

#include "../vendor/jngen/jngen.h"

#include <unordered_map>

using namespace jngen;
using namespace std;

namespace {

volatile uint64_t sink = 0;

void consume_graph(const Graph &g) {
	sink += static_cast<uint64_t>(g.n()) + static_cast<uint64_t>(g.m());
	for (const auto &e : g.edges())
		sink += static_cast<uint64_t>(e.first) +
				static_cast<uint64_t>(e.second);
}

void consume_tree(const Tree &t) { consume_graph(t); }

void consume_polygon(const Polygon &poly) {
	for (const auto &p : poly)
		sink += static_cast<uint64_t>(p.x) + static_cast<uint64_t>(p.y);
}

void consume_array(const Array &a) {
	for (size_t i = 0; i < a.size(); ++i)
		sink += static_cast<uint64_t>(a[i]);
}

void consume_string(const std::string &s) {
	for (unsigned char c : s)
		sink += c;
}

void register_cases(std::unordered_map<std::string, benchmark::CaseFn> &out) {
	const std::string str_pat = bench_str_regex_pattern();
	out["graph_connected_m_eq_n"] = [] {
		consume_graph(Graph::random(BENCH_N, BENCH_M).connected().g());
	};
	out["graph_connected_m_eq_2n"] = [] {
		consume_graph(Graph::random(BENCH_N, BENCH_M_2N).connected().g());
	};
	out["graph_gen"] = [] {
		consume_graph(Graph::random(BENCH_N, BENCH_M).g());
	};
	out["graph_gen_m_eq_2n"] = [] {
		consume_graph(Graph::random(BENCH_N, BENCH_M_2N).g());
	};
	out["graph_gen_skewed_m_eq_n"] = [] {
		consume_graph(Graph::randomStretched(
						  BENCH_N, BENCH_M, BENCH_ELONGATION, BENCH_SPREAD_SMALL)
						  .g());
	};
	out["graph_gen_skewed_m_eq_2n"] = [] {
		consume_graph(Graph::randomStretched(
						  BENCH_N, BENCH_M_2N, BENCH_ELONGATION,
						  BENCH_SPREAD_LARGE)
						  .g());
	};
	out["graph_gen_skewed_distinct_worst"] = [] {
		consume_graph(Graph::randomStretched(
						  BENCH_N, BENCH_M_DISTINCT_WORST, BENCH_ELONGATION,
						  BENCH_SPREAD_SMALL)
						  .g());
	};
	out["tree_gen"] = [] { consume_tree(Tree::random(BENCH_N)); };
	out["tree_gen_skewed"] = [] {
		consume_tree(Tree::randomPrim(BENCH_N, BENCH_ELONGATION));
	};
	out["list_all_different"] = [] {
		consume_array(Array::randomUnique(BENCH_N, 1, BENCH_LIST_HI));
	};
	out["list_random"] = [] {
		consume_array(Array::random(BENCH_N, 1, BENCH_LIST_HI));
	};
	out["geometry_convex_polygon"] = [] {
		consume_polygon(rndg.convexPolygon(BENCH_N, 0, BENCH_CONVEX_COORD_MAX));
	};
	out["geometry_points_general_position"] = [] {
		consume_polygon(rndg.pointsInGeneralPosition(
			BENCH_N, 0, BENCH_GENERAL_POSITION_COORD_MAX));
	};
	out["geometry_points_general_position_small"] = [] {
		consume_polygon(rndg.pointsInGeneralPosition(
			BENCH_GENERAL_POSITION_SMALL_N, 0,
			BENCH_GENERAL_POSITION_COORD_MAX));
	};
	out["permutation_uniform"] = [] {
		consume_array(Array::id(BENCH_PERM_N).shuffled());
	};
	out["graph_bipartite"] = [] {
		consume_graph(Graph::randomBipartite(
						  BENCH_BIP_N1, BENCH_BIP_N2, BENCH_BIP_M)
						  .g());
	};
	out["graph_directed"] = [] {
		consume_graph(Graph::random(BENCH_N, BENCH_M).directed().g());
	};
	out["graph_directed_acyclic"] = [] {
		consume_graph(
			Graph::random(BENCH_N, BENCH_M).directed().acyclic().g());
	};
	out["str_regex"] = [str_pat] {
		consume_string(rnds.random(str_pat));
	};
}

} // namespace

void jngen_init() {
	rnd.seed(42);
	config.generateLargeObjects = true;
}

std::unordered_map<std::string, benchmark::CaseFn> jngen_cases() {
	std::unordered_map<std::string, benchmark::CaseFn> out;
	register_cases(out);
	return out;
}
