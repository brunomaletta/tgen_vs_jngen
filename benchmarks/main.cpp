#include "benchmark.h"
#include "cases.h"

#include <cmath>
#include <cstdio>
#include <iostream>
#include <unordered_map>

std::unordered_map<std::string, benchmark::CaseFn> tgen_cases();
std::unordered_map<std::string, benchmark::CaseFn> jngen_cases();
void tgen_init();
void jngen_init();
void tgen_prepare_through_points();

namespace {

void usage(const char *prog) {
	std::cerr << "Usage: " << prog << " [--json PATH]\n"
			  << "  Default: docs/benchmark_results.json\n";
}

std::string git_rev_parse(const char *repo_path) {
	char cmd[256];
	std::snprintf(cmd, sizeof(cmd),
				  "git -C %s rev-parse --short HEAD 2>/dev/null", repo_path);
	FILE *pipe = popen(cmd, "r");
	if (!pipe)
		return "unknown";
	char buf[64] = {};
	if (!fgets(buf, sizeof(buf), pipe)) {
		pclose(pipe);
		return "unknown";
	}
	pclose(pipe);
	std::string out = buf;
	while (!out.empty() && (out.back() == '\n' || out.back() == '\r'))
		out.pop_back();
	return out.empty() ? "unknown" : out;
}

} // namespace

int main(int argc, char **argv) {
	std::string json_path = "docs/benchmark_results.json";

	for (int i = 1; i < argc; ++i) {
		std::string arg = argv[i];
		if (arg == "--json" and i + 1 < argc)
			json_path = argv[++i];
		else if (arg == "--help" or arg == "-h") {
			usage(argv[0]);
			return 0;
		} else {
			std::cerr << "Unknown argument: " << arg << '\n';
			usage(argv[0]);
			return 1;
		}
	}

	tgen_init();
	jngen_init();

	auto tgen = tgen_cases();
	auto jngen = jngen_cases();
	const auto specs = all_case_specs();

	tgen_prepare_through_points();

	benchmark::Report report;
	report.generated_at = benchmark::iso_timestamp();
	report.compiler = __VERSION__;
#ifdef QUICK
	report.flags = "-std=c++17 -O2 -DQUICK";
#else
	report.flags = "-std=c++17 -O2";
#endif
	report.hostname = benchmark::hostname();
	report.vendor_tgen = git_rev_parse("vendor/tgen");
	report.vendor_jngen = git_rev_parse("vendor/jngen");

	for (const auto &spec : specs) {
		benchmark::CaseResult row;
		row.id = spec.id;
		row.name = spec.name;
		row.name_suffix = spec.name_suffix;
		row.params = spec.params;
		row.compare_both = spec.compare_both;

		std::cout << "Benchmarking " << spec.name << spec.name_suffix
				  << " [tgen]...\n"
				  << std::flush;
		auto tgen_it = tgen.find(spec.id);
		if (tgen_it != tgen.end()) {
			row.tgen = benchmark::run_library_case(tgen_it->second);
			if (row.tgen.status == "timeout")
				std::cout << "  [tgen] timed out (>" << benchmark::format_ms(
								 benchmark::kMaxRunMs)
						  << " ms)\n";
		} else {
			row.tgen.status = "skipped";
			row.tgen.error = "no tgen case registered";
		}

		if (spec.compare_both) {
			std::cout << "Benchmarking " << spec.name << spec.name_suffix
					  << " [jngen]...\n"
					  << std::flush;
			auto jngen_it = jngen.find(spec.id);
			if (jngen_it != jngen.end()) {
				row.jngen = benchmark::run_library_case(jngen_it->second);
				if (row.jngen.status == "timeout")
					std::cout << "  [jngen] timed out (>"
							  << benchmark::format_ms(benchmark::kMaxRunMs)
							  << " ms)\n";
			} else {
				row.jngen.status = "skipped";
				row.jngen.error = "no jngen case registered";
			}
		} else {
			row.jngen.status = "skipped";
			row.jngen.error = "comparison not applicable";
		}

		if (row.compare_both && row.tgen.status == "ok" &&
			row.jngen.status == "ok" && row.jngen.median_ms > 0) {
			const auto round_ms = [](double ms) {
				return std::round(ms * 1000.0) / 1000.0;
			};
			row.ratio = round_ms(row.tgen.median_ms) /
						round_ms(row.jngen.median_ms);
		}

		report.results.push_back(std::move(row));
	}

	try {
		benchmark::write_json(report, json_path);
	} catch (const std::exception &e) {
		std::cerr << e.what() << '\n';
		return 1;
	}

	std::cout << "Wrote " << json_path << '\n';
	return 0;
}
