"""Shared SVG primitives: theming, font embedding, monospace layout.

Everything here exists to satisfy two GitHub constraints:

  1. GitHub strips <script> and CSS from README markdown, so anything that
     moves must be SMIL *inside* an SVG, and any typography must live inside
     the SVG too.
  2. An SVG referenced via <img> cannot load external resources, so the font
     has to be subset and base64-inlined or it will not render at all.

Media queries inside the SVG's own <style> still work, so light/dark themes
follow the viewer's browser.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path(__file__).resolve().parent / "fonts"

# JetBrains Mono advance width, in em. The portrait grid depends on this being
# exact -- a viewer whose fallback monospace is narrower sees a squeezed image.
ADVANCE = 0.600

FONT_STACK = '"JBM",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'

# Contribution ramp, quiet to loud. Matches make_portrait.py's character ramp.
RAMP = ":+#@"

THEME = {
    "light": {
        "fg": "#1f2328",
        "muted": "#59636e",
        "faint": "#d1d9e0",
        "accent": "#0969da",
        "level": ["#ebedf0", "#aceebb", "#4ac26b", "#2da44e", "#116329"],
    },
    "dark": {
        "fg": "#e6edf3",
        "muted": "#8b949e",
        "faint": "#30363d",
        "accent": "#58a6ff",
        "level": ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"],
    },
}


def _vars(theme: dict[str, object]) -> str:
    out = [
        f"--fg:{theme['fg']}",
        f"--muted:{theme['muted']}",
        f"--faint:{theme['faint']}",
        f"--accent:{theme['accent']}",
    ]
    for i, colour in enumerate(theme["level"]):  # type: ignore[arg-type]
        out.append(f"--l{i}:{colour}")
    return ";".join(out) + ";"


def _subset_woff2(ttf: Path, chars: str) -> str | None:
    """Subset `ttf` to `chars` and return it base64-encoded, or None."""
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        return None

    font = TTFont(str(ttf))
    options = subset.Options()
    options.layout_features = []
    options.notdef_outline = True
    options.desubroutinize = True
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text="".join(sorted(set(chars))))
    subsetter.subset(font)

    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def font_face(chars: str) -> str:
    """Inline @font-face rules for every weight we can find, subset to `chars`.

    Returns "" when the TTFs are absent -- the SVG then falls back to the
    viewer's monospace, which still lays out correctly, just off-brand.
    """
    rules = []
    for weight, filename in ((400, "JetBrainsMono-Regular.ttf"), (700, "JetBrainsMono-Bold.ttf")):
        path = FONT_DIR / filename
        if not path.exists():
            continue
        encoded = _subset_woff2(path, chars)
        if not encoded:
            continue
        rules.append(
            '@font-face{font-family:"JBM";'
            f'src:url(data:font/woff2;base64,{encoded}) format("woff2");'
            f"font-weight:{weight};font-style:normal;font-display:block}}"
        )
    return "".join(rules)


def svg(width: int, height: int, body: str, chars: str, title: str = "") -> str:
    """Wrap `body` in a themed, font-embedded SVG document."""
    style = (
        font_face(chars)
        + f":root{{{_vars(THEME['light'])}}}"
        + f"@media(prefers-color-scheme:dark){{:root{{{_vars(THEME['dark'])}}}}}"
        + f"text{{font-family:{FONT_STACK};dominant-baseline:middle}}"
        + ".fg{fill:var(--fg)}.muted{fill:var(--muted)}.accent{fill:var(--accent)}"
        + ".faint{fill:var(--muted);opacity:0.65}"
        + ".b{font-weight:700}"
    )
    label = f"<title>{esc(title)}</title>" if title else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        f"{label}<style>{style}</style>{body}</svg>"
    )


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def text(x: float, y: float, content: str, cls: str = "fg", size: int = 13,
         anchor: str = "start", extra: str = "") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" class="{cls}" '
        f'text-anchor="{anchor}"{extra}>{esc(content)}</text>'
    )


def _staggered(attr: str, delay: float, target: str, dur: float, splines: str | None) -> str:
    """An animation that encodes its delay in keyTimes rather than in `begin`.

    This matters more than it looks. If the delay lived in begin= and the
    element's base state were the hidden one, every renderer that ignores SMIL
    -- GitHub's mobile app, feed readers, PDF exports, anything rasterising at
    t=0 -- would show a permanently blank graphic. Starting at t=0 instead lets
    the element carry its *final* value as the base attribute, so no-SMIL
    viewers get the finished graphic and SMIL viewers get the animation.
    """
    total = delay + dur
    if delay <= 0:
        values, times = f"0;{target}", "0;1"
        keys = splines
    else:
        values, times = f"0;0;{target}", f"0;{delay / total:.4f};1"
        keys = f"0 0 0 1;{splines}" if splines else None
    spline_attrs = f' calcMode="spline" keySplines="{keys}"' if keys else ""
    return (
        f'<animate attributeName="{attr}" values="{values}" keyTimes="{times}" '
        f'begin="0s" dur="{total:.2f}s" fill="freeze"{spline_attrs}/>'
    )


# One-shot reveals are disabled, and this is the most important comment here.
#
# GitHub renders a README image at frame zero and never advances the SMIL
# timeline. Whatever a graphic looks like at t=0 is what every visitor sees,
# permanently. So anything that starts hidden -- a fade from opacity 0, a bar
# growing from width 0, a clip revealing from width 0 -- renders as a blank box
# on the one surface this repo exists to serve.
#
# Encoding the delay in keyTimes with begin="0s" makes this strictly worse, not
# better: it guarantees the element is at its *first* value at t=0 rather than
# at its base attribute. That mistake is what shipped the first time.
#
# Kept as no-ops rather than deleted so call sites still read as "an element was
# revealed here", and so re-enabling has one obvious place to change.
#
# Looping animations remain fine and are still used -- see scenes.pipeline,
# where frame zero is already the finished DAG and the motion is decoration on
# top. The rule is not "no animation", it is "frame zero is the finished graphic".

def fade_in(delay: float, dur: float = 0.45) -> str:
    return ""


def grow(delay: float, target: float, dur: float = 0.7, attr: str = "width") -> str:
    return ""


def write(path: Path, content: str) -> bool:
    """Write only when the bytes actually changed. Returns True if written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True
