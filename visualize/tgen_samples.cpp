#include "../vendor/tgen/single_include/tgen.h"

#include <fstream>
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
	tgen::register_gen(42);
	const int n = 80;
	const int coord = 1000;

	write_points_json(
		out_dir + "/geometry_convex_polygon.points.json",
		tgen::geometry::random_convex_polygon(n, 0, coord), "polygon", coord);

	write_points_json(
		out_dir + "/geometry_simple_polygon.points.json",
		tgen::geometry::random_simple_polygon(n, 0, coord), "polygon", coord);

	write_points_json(
		out_dir + "/geometry_points_general_position.points.json",
		tgen::geometry::random_points_general_position(n, 0, coord), "scatter",
		coord);

	const int grid_rows = 10;
	const int grid_cols = 10;
	const auto grid = rectangular_grid(grid_rows, grid_cols, 0, coord);
	write_points_json(
		out_dir + "/geometry_simple_polygon_through_points.points.json",
		tgen::geometry::random_simple_polygon_through_points(grid), "polygon",
		coord);
}
