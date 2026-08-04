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


def isolate(image):
    """Drop the background to white and spread the subject over the full ramp.

    Two problems, one fix each.

    A snapshot has its subject and its background in overlapping tonal ranges,
    so the ramp describes the palm trees as enthusiastically as the face. A
    feathered ellipse pushes everything outside the head to white, which the
    ramp reads as blank.

    And a sunlit photo bunches almost every pixel into a narrow band of light
    mid-tones, so nearly every cell picks the same glyph and the result is a
    uniform smudge. Equalising against the histogram of the *masked region
    only* spreads the face across all ten ramp levels. Equalising the whole
    frame does not work -- the background dominates the histogram and the face
    stays compressed.
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageOps

    width, height = image.size
    hard = Image.new("L", (width, height), 0)
    ImageDraw.Draw(hard).ellipse(
        (width * 0.09, height * 0.05, width * 0.91, height * 0.97), fill=255
    )
    equalised = ImageOps.equalize(image, mask=hard)
    soft = hard.filter(ImageFilter.GaussianBlur(width // 50))
    return Image.composite(equalised, Image.new("L", (width, height), 255), soft)


def render(image_path: Path, cols: int, contrast: float, invert: bool,
           crop: tuple[int, ...] | None = None, cut_out: bool = True) -> list[str]:
    from PIL import Image, ImageEnhance, ImageOps

    image = Image.open(image_path).convert("L")
    if crop:
        image = image.crop(crop)
    if cut_out:
        # isolate() already equalised; autocontrast on top of that only clips
        # the extremes back together and muddies the midtones.
        image = isolate(image)
    else:
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
                        help="dark subject on a light page -- almost always what you want")
    parser.add_argument("--crop", help="x0,y0,x1,y1 in source pixels, applied first")
    parser.add_argument("--no-isolate", action="store_true",
                        help="skip background removal and masked equalisation")
    parser.add_argument("--out", type=Path, default=k.ROOT / "ascii.svg")
    args = parser.parse_args()

    if not args.image.exists():
        print(f"no such image: {args.image}")
        return 1

    crop = tuple(int(v) for v in args.crop.split(",")) if args.crop else None
    lines = render(args.image, args.cols, args.contrast, args.invert,
                   crop=crop, cut_out=not args.no_isolate)
    print("\n".join(lines))
    k.write(args.out, to_svg(lines, args.size))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
