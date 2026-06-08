#include "../vendor/jngen/jngen.h"
#include "samples.h"

#include <iostream>
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
	for (int vi = 0; vi < GALLERY_VARIANT_COUNT; ++vi) {
		const int seed = GALLERY_SEED_BASE + vi;
		const string tag = gallery_seed_tag(seed);
		cout << "jngen samples seed " << seed << "...\n" << flush;
		rnd.seed(seed);

		draw_polygon_svg(
			out_dir + "/geometry_convex_polygon_jngen" + tag + ".svg",
			rndg.convexPolygon(GALLERY_CONVEX_N, 0, GALLERY_CONVEX_COORD));
		draw_polygon_svg(
			out_dir + "/geometry_convex_polygon_large_jngen" + tag + ".svg",
			rndg.convexPolygon(GALLERY_CONVEX_LARGE_N, 0,
							   GALLERY_CONVEX_LARGE_COORD));

		draw_points_svg(
			out_dir + "/geometry_points_general_position_jngen" + tag + ".svg",
			rndg.pointsInGeneralPosition(GALLERY_GENERAL_POSITION_N, 0,
										 GALLERY_GENERAL_POSITION_COORD));
	}
}
