#include "../vendor/tgen/single_include/tgen.h"
#include "samples.h"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

void write_points_json(const std::string &path,
					   const std::vector<tgen::geometry::point<long long>> &pts,
					   const char *kind, long long coord_max) {
	std::ofstream out(path);
	out << "{\n  \"kind\": \"" << kind << "\",\n  \"coord_max\": " << coord_max
		<< ",\n  \"points\": [\n";
	for (size_t i = 0; i < pts.size(); ++i) {
		out << "    [" << pts[i].x() << ", " << pts[i].y() << "]";
		if (i + 1 < pts.size())
			out << ",";
		out << "\n";
	}
	out << "  ]\n}\n";
}

std::vector<tgen::geometry::point<long long>>
rectangular_grid(int rows, int cols, long long min_coord, long long max_coord) {
	std::vector<tgen::geometry::point<long long>> pts;
	pts.reserve(static_cast<size_t>(rows) * cols);
	const long long span = max_coord - min_coord;
	for (int y = 0; y < rows; ++y) {
		for (int x = 0; x < cols; ++x) {
			const long long px =
				min_coord + (cols == 1 ? 0 : x * span / (cols - 1));
			const long long py =
				min_coord + (rows == 1 ? 0 : y * span / (rows - 1));
			pts.emplace_back(px, py);
		}
	}
	return pts;
}

} // namespace

void run_tgen_samples(const std::string &out_dir) {
	const int grid_rows = 10;
	const int grid_cols = 10;
	const auto grid = rectangular_grid(grid_rows, grid_cols, 0, GALLERY_COORD);

	for (int vi = 0; vi < GALLERY_VARIANT_COUNT; ++vi) {
		const int seed = GALLERY_SEED_BASE + vi;
		const std::string tag = gallery_seed_tag(seed);
		std::cout << "tgen samples seed " << seed << "...\n" << std::flush;
		tgen::register_gen(seed);

		write_points_json(
			out_dir + "/geometry_convex_polygon" + tag + ".points.json",
			tgen::geometry::random_convex_polygon(
				GALLERY_CONVEX_N, 0, GALLERY_CONVEX_COORD),
			"polygon", GALLERY_CONVEX_COORD);
		write_points_json(
			out_dir + "/geometry_convex_polygon_large" + tag + ".points.json",
			tgen::geometry::random_convex_polygon(
				GALLERY_CONVEX_LARGE_N, 0, GALLERY_CONVEX_LARGE_COORD),
			"polygon", GALLERY_CONVEX_LARGE_COORD);

		write_points_json(
			out_dir + "/geometry_simple_polygon" + tag + ".points.json",
			tgen::geometry::random_simple_polygon(GALLERY_N, 0, GALLERY_COORD),
			"polygon", GALLERY_COORD);

		write_points_json(
			out_dir + "/geometry_orthogonal_polygon" + tag + ".points.json",
			tgen::geometry::random_orthogonal_polygon(
				GALLERY_N, 0, GALLERY_COORD),
			"polygon", GALLERY_COORD);

		write_points_json(
			out_dir + "/geometry_points_general_position" + tag + ".points.json",
			tgen::geometry::random_points_general_position(
				GALLERY_GENERAL_POSITION_N, 0, GALLERY_GENERAL_POSITION_COORD),
			"scatter", GALLERY_GENERAL_POSITION_COORD);

		write_points_json(
			out_dir + "/geometry_simple_polygon_through_points" + tag
				+ ".points.json",
			tgen::geometry::random_simple_polygon_through_points(grid),
			"polygon", GALLERY_COORD);
	}
}
