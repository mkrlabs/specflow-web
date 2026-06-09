#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pillow", "numpy"]
# ///
"""
Optimise PNG art for the web: cap the pixel dimensions to what the page
actually displays (× a retina factor) and palette-quantise, preserving alpha.

The generated robot art ships at 1024² — fine as a source, far too heavy when
a sprite renders at ~112px. This is the Sharp-equivalent step: downscale to a
sensible max edge and quantise the colours (these illustrations use a small
palette, so PNG-8 is near-lossless and tiny).

Usage:
  uv run scripts/optimize-images.py --max 288 --colors 64 agents/*.png
  uv run scripts/optimize-images.py --max 1200 --colors 96 hero-team.png
  uv run scripts/optimize-images.py --max 720 --out-dir out/ feature-*.png

In place by default; --out-dir writes copies. Idempotent.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image


def optimize(path: str, dst: str, max_edge: int, colors: int) -> tuple[int, int]:
    im = Image.open(path).convert("RGBA")
    before = os.path.getsize(path)

    longest = max(im.width, im.height)
    if longest > max_edge:
        scale = max_edge / longest
        im = im.resize(
            (round(im.width * scale), round(im.height * scale)),
            Image.LANCZOS,
        )

    # Quantise RGB to a small palette, reattach the (resized) alpha channel so
    # transparency survives. Pixel-art / flat-shaded art compresses beautifully.
    alpha = im.split()[3]
    rgb = im.convert("RGB").quantize(colors=colors, method=Image.MAXCOVERAGE)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    out.save(dst, optimize=True)
    return before, os.path.getsize(dst)


def main() -> int:
    ap = argparse.ArgumentParser(description="Resize + quantise PNGs for the web.")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--max", type=int, default=512, help="max edge in px")
    ap.add_argument("--colors", type=int, default=96, help="palette size")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)

    total_before = total_after = 0
    for path in args.images:
        dst = os.path.join(args.out_dir, os.path.basename(path)) if args.out_dir else path
        before, after = optimize(path, dst, args.max, args.colors)
        total_before += before
        total_after += after
        print(f"{os.path.basename(path):26} {before // 1024:>5} KB -> {after // 1024:>4} KB")
    print(f"{'TOTAL':26} {total_before // 1024:>5} KB -> {total_after // 1024:>4} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
