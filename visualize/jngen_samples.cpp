#include "../vendor/jngen/jngen.h"

#include <string>

using namespace jngen;
using namespace std;

namespace {

void draw_polygon_svg(const string &path, const Polygon &poly,
					  const string &stroke = "darkgreen") {
	Drawer d;
	d.enableGrid(false);
	d.setStroke("");
	d.setFill(stroke);
	d.setOpacity(0.32);
	d.polygon(poly);
	d.setStroke(stroke);
	d.setFill("");
	d.setOpacity(0.85);
	d.polygon(poly);
	d.setFill(stroke);
	for (const auto &p : poly)
		d.point(p);
	d.dumpSvg(path);
}

void draw_points_svg(const string &path, const TArray<Point> &pts,
					 const string &stroke = "darkgreen") {
	Drawer d;
	d.enableGrid(false);
	d.setStroke(stroke);
	d.setFill(stroke);
	for (const auto &p : pts)
		d.point(p);
	d.dumpSvg(path);
}

} // namespace

void run_jngen_samples(const string &out_dir) {
	rnd.seed(42);
	const int n = 80;
	const int coord = 1000;

	draw_polygon_svg(out_dir + "/geometry_convex_polygon_jngen.svg",
					 rndg.convexPolygon(n, 0, coord));

	draw_points_svg(out_dir + "/geometry_points_general_position_jngen.svg",
					rndg.pointsInGeneralPosition(n, 0, coord));
}
