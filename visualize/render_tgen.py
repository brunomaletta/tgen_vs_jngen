#!/usr/bin/env python3
"""Convert tgen point dumps (.points.json) to SVG."""

import argparse
import json
import os
import sys

CANVAS_SIZE = 2000
MARGIN = 80
PADDING_RATIO = 0.08
# jngen Drawer defaults in a 2000×2000 canvas (normalize_gallery rescales after crop).
GALLERY_POINT_R = 12
GALLERY_STROKE_W = 8
# Dense polygons (*_large): small markers so n≈1e4 stays readable.
GALLERY_POINT_R_DENSE = 2
GALLERY_STROKE_W_DENSE = 1.5
# General-position scatter (n≈2e3): between dense and default.
GALLERY_POINT_R_SCATTER = 5
GALLERY_STROKE_W_SCATTER = 3


def gallery_point_style(stem):
    if stem.endswith("_large") or "_large_" in stem:
        return GALLERY_POINT_R_DENSE, GALLERY_STROKE_W_DENSE
    if "general_position" in stem:
        return GALLERY_POINT_R_SCATTER, GALLERY_STROKE_W_SCATTER
    return GALLERY_POINT_R, GALLERY_STROKE_W


def svg_header(title):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_SIZE}" height="{CANVAS_SIZE}" viewBox="0 0 {CANVAS_SIZE} {CANVAS_SIZE}">
  <title>{title}</title>
"""


def bbox_of_points(points, extra_pad=0.0):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    if x1 == x0:
        x0 -= 0.5
        x1 += 0.5
    if y1 == y0:
        y0 -= 0.5
        y1 += 0.5
    pad_x = (x1 - x0) * PADDING_RATIO + extra_pad
    pad_y = (y1 - y0) * PADDING_RATIO + extra_pad
    return x0 - pad_x, y0 - pad_y, x1 + pad_x, y1 + pad_y


def fit_transform(x0, y0, x1, y1):
    """Map data bbox (y-up) into a square canvas region."""
    data_w = x1 - x0
    data_h = y1 - y0
    avail = CANVAS_SIZE - 2 * MARGIN
    scale = min(avail / data_w, avail / data_h)
    draw_w = data_w * scale
    draw_h = data_h * scale
    x_off = MARGIN + (avail - draw_w) / 2
    y_off = MARGIN + (avail - draw_h) / 2

    def tx(x):
        return x_off + (x - x0) * scale

    def ty(y):
        return y_off + (y1 - y) * scale

    return tx, ty


def format_point(tx, ty, x, y):
    return f"{tx(x):.1f},{ty(y):.1f}"


def render_polygon_svg(
    points,
    title="",
    stroke="#2563eb",
    fill="#3b82f666",
    point_r=GALLERY_POINT_R,
    stroke_w=GALLERY_STROKE_W,
):
    if not points:
        return ""
    x0, y0, x1, y1 = bbox_of_points(points)
    tx, ty = fit_transform(x0, y0, x1, y1)
    pts = " ".join(format_point(tx, ty, x, y) for x, y in points)
    dots = "\n".join(
        f'  <circle cx="{tx(x):.1f}" cy="{ty(y):.1f}" r="{point_r}" '
        f'fill="{stroke}"/>'
        for x, y in points
    )

    return (
        svg_header(title)
        + f'  <polygon points="{pts}" fill="{fill}" fill-rule="nonzero" '
        + f'stroke="{stroke}" stroke-width="{stroke_w}" '
        f'stroke-linejoin="round"/>\n'
        + dots
        + "\n</svg>\n"
    )


def render_scatter_svg(
    points,
    title="",
    stroke="#2563eb",
    fill="#2563eb",
    point_r=GALLERY_POINT_R,
):
    if not points:
        return ""
    x0, y0, x1, y1 = bbox_of_points(points)
    data_w = x1 - x0
    data_h = y1 - y0
    avail = CANVAS_SIZE - 2 * MARGIN
    scale = min(avail / data_w, avail / data_h)
    x0, y0, x1, y1 = bbox_of_points(
        points, extra_pad=(point_r * 2) / scale
    )
    tx, ty = fit_transform(x0, y0, x1, y1)

    dots = "\n".join(
        f'  <circle cx="{tx(x):.1f}" cy="{ty(y):.1f}" r="{point_r}" '
        f'fill="{fill}"/>'
        for x, y in points
    )

    return svg_header(title) + dots + "\n</svg>\n"


def process_file(src, dst):
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    stem = os.path.basename(src).replace(".points.json", "")
    title = data.get("title", stem.replace("_", " "))
    if "points" not in data:
        sys.stderr.write(f"render_tgen.py: unknown format in {src}\n")
        return
    kind = data.get("kind", "polygon")
    points = data.get("points", [])
    point_r, stroke_w = gallery_point_style(stem)
    if kind == "scatter":
        svg = render_scatter_svg(points, title=title, point_r=point_r)
    else:
        svg = render_polygon_svg(
            points, title=title, point_r=point_r, stroke_w=stroke_w
        )
    with open(dst, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {dst}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="directory with *.points.json")
    parser.add_argument("output_dir", help="directory for SVG output")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    found = False
    for name in sorted(os.listdir(args.input_dir)):
        if not name.endswith(".points.json"):
            continue
        found = True
        stem = name.replace(".points.json", "")
        process_file(
            os.path.join(args.input_dir, name),
            os.path.join(args.output_dir, f"{stem}_tgen.svg"),
        )
    if not found:
        sys.stderr.write("render_tgen.py: no sample JSON files found\n")


if __name__ == "__main__":
    main()
