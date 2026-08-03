"""Push a photo through a character ramp and draw the result as ascii.svg.

One-off: run it when you change the photo, commit the SVG, forget about it.

    python scripts/make_portrait.py portrait.jpg --cols 92

The grid assumes a monospace advance width of exactly 0.600 em, which is what
JetBrains Mono gives us. That is why the font is embedded rather than left to
the viewer -- a narrower fallback would squeeze the face horizontally.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import svgkit as k

# Quiet to loud. Denser than the contribution ramp because a face needs the
# tonal range; the last few glyphs carry the shadows.
RAMP = " .:-=+*#%@"


def render(image_path: Path, cols: int, contrast: float, invert: bool) -> list[str]:
    from PIL import Image, ImageEnhance, ImageOps

    image = Image.open(image_path).convert("L")
    image = ImageOps.autocontrast(image, cutoff=2)
    if contrast != 1.0:
        image = ImageEnhance.Contrast(image).enhance(contrast)
    if invert:
        image = ImageOps.invert(image)

    # A character cell is taller than it is wide, so rows get compressed by
    # the aspect ratio of the cell itself (advance width / line height).
    cell_aspect = k.ADVANCE / 1.15
    rows = max(1, int(image.height / image.width * cols * cell_aspect))
    image = image.resize((cols, rows), Image.LANCZOS)

    pixels = list(image.getdata())
    lines = []
    for row in range(rows):
        line = "".join(
            RAMP[min(len(RAMP) - 1, pixels[row * cols + col] * len(RAMP) // 256)]
            for col in range(cols)
        )
        lines.append(line.rstrip() or " ")
    return lines


def to_svg(lines: list[str], size: int = 7) -> str:
    cw = size * k.ADVANCE
    lh = size * 1.15
    cols = max(len(line) for line in lines)
    width = int(cols * cw) + 2
    height = int(len(lines) * lh) + 6

    body = []
    for i, line in enumerate(lines):
        body.append(
            f'<g>'
            + k.text(1, 4 + i * lh, line, cls="fg", size=size,
                     extra=f' xml:space="preserve" textLength="{len(line) * cw:.2f}" '
                           'lengthAdjust="spacing"')
            + k.fade_in(i * 0.008, 0.5)
            + "</g>"
        )
    chars = "".join(sorted(set("".join(lines))))
    return k.svg(width, height, "".join(body), chars, "portrait")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--cols", type=int, default=92, help="grid width in characters")
    parser.add_argument("--contrast", type=float, default=1.25)
    parser.add_argument("--size", type=int, default=7, help="font size in px")
    parser.add_argument("--invert", action="store_true",
                        help="use for light subjects on dark backgrounds")
    parser.add_argument("--out", type=Path, default=k.ROOT / "ascii.svg")
    args = parser.parse_args()

    if not args.image.exists():
        print(f"no such image: {args.image}")
        return 1

    lines = render(args.image, args.cols, args.contrast, args.invert)
    print("\n".join(lines))
    k.write(args.out, to_svg(lines, args.size))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
