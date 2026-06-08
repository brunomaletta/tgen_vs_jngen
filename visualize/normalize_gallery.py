#!/usr/bin/env python3
"""Ensure gallery SVGs share display size and frame content tightly."""

import argparse
import re
import sys
from pathlib import Path

CANVAS_SIZE = 2000
PADDING_RATIO = 0.06
# Match jngen Drawer defaults (width=1 -> point r=12, stroke=8 in 2000 canvas units).
GALLERY_POINT_R = 12
GALLERY_STROKE_W = 8
SVG_OPEN = re.compile(r"<svg\b([^>]*)>", re.IGNORECASE)
VIEWBOX = re.compile(r'\sviewBox="[^"]*"', re.IGNORECASE)
WIDTH = re.compile(r'\swidth="[^"]*"', re.IGNORECASE)
HEIGHT = re.compile(r'\sheight="[^"]*"', re.IGNORECASE)
BACKGROUND_RECT = re.compile(
    r'\s*<rect\b[^>]*\bwidth="100%"[^>]*\bheight="100%"[^>]*/>\s*',
    re.IGNORECASE,
)
BACKGROUND_CIRCLE = re.compile(
    r"\s*<circle\b[^>]*\bfill=['\"]white['\"][^>]*/>\s*",
    re.IGNORECASE,
)


def strip_background(text):
    text = BACKGROUND_RECT.sub("\n", text)
    # jngen Drawer paints a huge white circle behind the scene.
    def drop_large_white_circle(match):
        tag = match.group(0)
        r_match = re.search(r"\br=['\"]([^'\"]+)['\"]", tag)
        if not r_match:
            return tag
        if float(r_match.group(1)) > CANVAS_SIZE * 0.75:
            return "\n"
        return tag

    return BACKGROUND_CIRCLE.sub(drop_large_white_circle, text)


def parse_points(raw):
    points = []
    for token in raw.replace(",", " ").split():
        if not token:
            continue
        try:
            points.append(float(token))
        except ValueError:
            continue
    return [(points[i], points[i + 1]) for i in range(0, len(points) - 1, 2)]


def collect_points(text):
    points = []

    for match in re.finditer(r'points="([^"]+)"', text):
        points.extend(parse_points(match.group(1)))
    for match in re.finditer(r"points='([^']+)'", text):
        points.extend(parse_points(match.group(1)))

    for match in re.finditer(
        r'x1="([^"]+)"\s+y1="([^"]+)"\s+x2="([^"]+)"\s+y2="([^"]+)"', text
    ):
        points.append((float(match.group(1)), float(match.group(2))))
        points.append((float(match.group(3)), float(match.group(4))))
    for match in re.finditer(
        r"x1='([^']+)'\s+y1='([^']+)'\s+x2='([^']+)'\s+y2='([^']+)'", text
    ):
        points.append((float(match.group(1)), float(match.group(2))))
        points.append((float(match.group(3)), float(match.group(4))))

    for match in re.finditer(r'cx="([^"]+)"\s+cy="([^"]+)"\s+r="([^"]+)"', text):
        cx, cy, r = float(match.group(1)), float(match.group(2)), float(match.group(3))
        if r > CANVAS_SIZE * 0.75:
            continue
        points.append((cx, cy))
        points.extend([(cx - r, cy - r), (cx + r, cy + r)])
    for match in re.finditer(r"cx='([^']+)'\s+cy='([^']+)'\s+r='([^']+)'", text):
        cx, cy, r = float(match.group(1)), float(match.group(2)), float(match.group(3))
        if r > CANVAS_SIZE * 0.75:
            continue
        points.append((cx, cy))
        points.extend([(cx - r, cy - r), (cx + r, cy + r)])

    return points


def content_viewbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    if x1 == x0:
        x0 -= 1
        x1 += 1
    if y1 == y0:
        y0 -= 1
        y1 += 1

    pad_x = (x1 - x0) * PADDING_RATIO
    pad_y = (y1 - y0) * PADDING_RATIO
    x0 -= pad_x
    x1 += pad_x
    y0 -= pad_y
    y1 += pad_y

    width = x1 - x0
    height = y1 - y0
    side = max(width, height)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    return cx - side / 2, cy - side / 2, side, side


def scale_markup(text, viewbox_side):
    """Scale point radii and strokes so dots/lines look the same after crop."""
    point_r = GALLERY_POINT_R * viewbox_side / CANVAS_SIZE
    stroke_w = GALLERY_STROKE_W * viewbox_side / CANVAS_SIZE

    def scale_circle(match):
        tag = match.group(0)
        tag = re.sub(
            r"(\br=)(['\"])([\d.]+)\2",
            lambda m: f"{m.group(1)}{m.group(2)}{point_r:.4f}{m.group(2)}",
            tag,
            count=1,
        )
        if re.search(r"stroke-width=", tag, re.IGNORECASE):
            tag = re.sub(
                r'(stroke-width=")([\d.]+)(")',
                lambda m: f'{m.group(1)}{stroke_w:.4f}{m.group(3)}',
                tag,
                count=1,
            )
        return tag

    text = re.sub(r"<circle\b[^>]*/>", scale_circle, text, flags=re.IGNORECASE)

    def scale_style_stroke(match):
        style = match.group(1)
        style = re.sub(
            r"(stroke-width:)([\d.]+)",
            lambda m: f"{m.group(1)}{stroke_w:.4f}",
            style,
            count=1,
        )
        return f"style='{style}'"

    text = re.sub(r"style='([^']*)'", scale_style_stroke, text)

    text = re.sub(
        r'(<polygon\b[^>]*\bstroke-width=")([\d.]+)(")',
        lambda m: f"{m.group(1)}{stroke_w:.4f}{m.group(3)}",
        text,
        flags=re.IGNORECASE,
    )
    return text


def normalize_svg(text):
    text = strip_background(text)
    match = SVG_OPEN.search(text)
    if not match:
        return text

    attrs = match.group(1)
    attrs = WIDTH.sub("", attrs)
    attrs = HEIGHT.sub("", attrs)
    attrs = VIEWBOX.sub("", attrs)
    attrs = re.sub(r"\sviewBox='[^']*'", "", attrs, flags=re.IGNORECASE)

    points = collect_points(text)
    if points:
        vx, vy, vw, vh = content_viewbox(points)
        view_box = f'viewBox="{vx:.2f} {vy:.2f} {vw:.2f} {vh:.2f}"'
    else:
        view_box = f'viewBox="0 0 {CANVAS_SIZE} {CANVAS_SIZE}"'

    replacement = (
        f'<svg{attrs} width="{CANVAS_SIZE}" height="{CANVAS_SIZE}" {view_box}>'
    )
    text = text[: match.start()] + replacement + text[match.end() :]
    if points:
        text = scale_markup(text, vw)
    return text


def normalize_file(path):
    original = path.read_text(encoding="utf-8")
    updated = normalize_svg(original)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print(f"Normalized {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("gallery_dir", help="directory containing gallery SVG files")
    args = parser.parse_args()

    gallery = Path(args.gallery_dir)
    if not gallery.is_dir():
        sys.stderr.write(f"normalize_gallery.py: not a directory: {gallery}\n")
        sys.exit(1)

    for path in sorted(gallery.glob("*.svg")):
        normalize_file(path)


if __name__ == "__main__":
    main()
