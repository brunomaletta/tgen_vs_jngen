#!/usr/bin/env python3
"""Ensure gallery SVGs share display size and frame content tightly."""

import argparse
import re
import sys
from pathlib import Path

CANVAS_SIZE = 2000
PADDING_RATIO = 0.06
SVG_OPEN = re.compile(r"<svg\b([^>]*)>", re.IGNORECASE)
VIEWBOX = re.compile(r'\sviewBox="[^"]*"', re.IGNORECASE)
WIDTH = re.compile(r'\swidth="[^"]*"', re.IGNORECASE)
HEIGHT = re.compile(r'\sheight="[^"]*"', re.IGNORECASE)


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


def normalize_svg(text):
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
    return text[: match.start()] + replacement + text[match.end() :]


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
