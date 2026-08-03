"""The two showpiece graphics: an animated terminal and a live-looking DAG.

Neither needs the API -- the content is fixed -- so this runs standalone:

    python scripts/scenes.py

Both obey the same rule as everything else here: the base attribute values are
the *finished* frame, so a renderer that ignores SMIL still shows something
sensible rather than an empty box.
"""

from __future__ import annotations

import svgkit as k

WIDTH = 620
CW = 12 * k.ADVANCE  # advance width at 12px


# --------------------------------------------------------------------------
# scene 1: a terminal that types itself out
# --------------------------------------------------------------------------

# (kind, text). Keep this generic and a bit funny -- it is a personality
# sketch, not a CV, and nothing here should be tied to an employer's domain.
SESSION = [
    ("cmd", "whoami"),
    ("out", "aaron murphy · backend engineer · dublin, ie"),
    ("gap", ""),
    ("cmd", "uptime"),
    ("out", "5 years up,  load average: 0.71 0.94 1.22"),
    ("gap", ""),
    ("cmd", "git log --oneline -4"),
    ("git", "a1c3f9d  fix: it was dns"),
    ("good", "7e21b04  perf: kill the n+1  (5m → 30s)"),
    ("git", "3fd8ac1  revert: it was not the n+1"),
    ("git", "9b0e772  feat: ship it, watch it, learn from it"),
    ("gap", ""),
    ("cmd", "ls ~/stack"),
    ("out", "python/  go/  sql/  airflow/  celery/  redis/  postgres/  docker/"),
    ("gap", ""),
    ("cmd", "cat ~/.plan"),
    ("out", "make the slow thing fast. delete more than i add."),
]

TYPE_RATE = 0.045   # seconds per character
PAUSE = 0.28        # beat between a command finishing and its output


def terminal() -> str:
    size = 12
    lh = 17
    pad_x, top = 16, 42
    prompt = "$ "
    body: list[str] = []
    defs: list[str] = []
    chars: set[str] = set(prompt)

    # chrome
    body.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="0" rx="8" '
        f'fill="var(--card)" stroke="var(--faint)"/>'
    )
    body.append(
        f'<line x1="0" y1="27" x2="{WIDTH}" y2="27" stroke="var(--faint)"/>'
    )
    for i, colour in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        body.append(f'<circle cx="{18 + i * 15}" cy="14" r="5" fill="{colour}"/>')
    title = "aaronmurphy45 — zsh"
    chars |= set(title)
    body.append(k.text(WIDTH / 2, 14, title, cls="muted", size=10, anchor="middle"))

    clock = 0.35
    row = 0
    for kind, content in SESSION:
        if kind == "gap":
            clock += 0.18
            row += 1
            continue

        y = top + row * lh
        row += 1

        if kind == "cmd":
            line = prompt + content
            chars |= set(line)
            width = len(line) * CW
            # No typing animation. A clip that reveals from width 0 is blank at
            # frame zero, and frame zero is the only frame GitHub ever renders
            # -- see the note above fade_in in svgkit.
            body.append(
                "<g>"
                + k.text(pad_x, y, prompt, cls="accent b", size=size,
                         extra=f' textLength="{len(prompt) * CW:.1f}" lengthAdjust="spacing"')
                + k.text(pad_x + len(prompt) * CW, y, content, cls="fg", size=size,
                         extra=f' xml:space="preserve" textLength="{len(content) * CW:.1f}" '
                               'lengthAdjust="spacing"')
                + "</g>"
            )
            chars |= set(line)
            clock += len(line) * TYPE_RATE + PAUSE
        elif kind == "git":
            # Short hash dimmed, subject at full weight -- reads like real
            # `git log --oneline` rather than a flat grey line.
            chars |= set(content)
            sha, subject = content[:7], content[7:]
            body.append(
                "<g>"
                + k.text(pad_x, y, sha, cls="faint", size=size,
                         extra=f' textLength="{len(sha) * CW:.1f}" lengthAdjust="spacing"')
                + k.text(pad_x + len(sha) * CW, y, subject, cls="fg", size=size,
                         extra=f' xml:space="preserve" textLength="{len(subject) * CW:.1f}" '
                               'lengthAdjust="spacing"')
                + k.fade_in(clock, 0.3)
                + "</g>"
            )
            clock += 0.16
        else:
            cls = {"ok": "ok", "dim": "muted", "good": "good", "out": "muted"}[kind]
            chars |= set(content)
            body.append(
                "<g>"
                + k.text(pad_x, y, content, cls=cls, size=size,
                         extra=f' xml:space="preserve" textLength="{len(content) * CW:.1f}" '
                               'lengthAdjust="spacing"')
                + k.fade_in(clock, 0.3)
                + "</g>"
            )
            clock += 0.16

    # trailing prompt with a cursor that blinks forever
    y = top + (row + 1) * lh
    body.append(
        "<g>"
        + k.text(pad_x, y, prompt, cls="accent b", size=size)
        + k.fade_in(clock, 0.2)
        + "</g>"
    )
    # Base opacity 1 so the cursor is a solid block at frame zero; the blink is
    # a bonus for anyone who opens the SVG directly.
    body.append(
        f'<rect x="{pad_x + len(prompt) * CW:.1f}" y="{y - 7}" width="{CW:.1f}" height="14" '
        f'fill="var(--accent)" opacity="1">'
        f'<animate attributeName="opacity" values="0;1;1;0;0;1;1;0;0" '
        f'keyTimes="0;0.01;0.5;0.51;0.75;0.76;0.99;1;1" '
        f'begin="{clock + 0.2:.2f}s" dur="1.1s" repeatCount="indefinite"/>'
        f"</rect>"
    )

    height = y + 22
    body[0] = body[0].replace('height="0"', f'height="{height - 1}"')

    extra_css = (
        ".ok{fill:#2da44e}.good{fill:#2da44e;font-weight:700}"
        "@media(prefers-color-scheme:dark){.ok{fill:#3fb950}.good{fill:#3fb950}}"
    )
    return _wrap(WIDTH, int(height), f"<defs>{''.join(defs)}</defs>" + "".join(body),
                 "".join(sorted(chars)), "terminal", extra_css)


# --------------------------------------------------------------------------
# scene 2: a DAG with data actually moving through it
# --------------------------------------------------------------------------

TASKS = ["commit", "build", "test", "review", "ship"]

# `test` goes red now and then, because of course it does. Index into TASKS.
FLAKY = 2


def pipeline() -> str:
    # Inset by a pixel each side: the node stroke is centred on the edge, so a
    # node flush against x=WIDTH loses half its border to the viewport.
    node_w, node_h = 104, 38
    inset = 1.0
    span = WIDTH - inset * 2
    gap = (span - node_w * len(TASKS)) / (len(TASKS) - 1)
    # No caption -- the section heading above this graphic already names it.
    y = 6
    mid = y + node_h / 2
    body: list[str] = []
    chars: set[str] = set()

    xs = [inset + i * (node_w + gap) for i in range(len(TASKS))]

    # edges first, so nodes paint over them
    for i in range(len(TASKS) - 1):
        x1 = xs[i] + node_w
        x2 = xs[i + 1]
        body.append(
            f'<line x1="{x1:.1f}" y1="{mid}" x2="{x2:.1f}" y2="{mid}" '
            f'stroke="var(--faint)" stroke-width="2" stroke-dasharray="4 5" '
            f'stroke-dashoffset="0">'
            f'<animate attributeName="stroke-dashoffset" values="9;0" dur="0.7s" '
            f'repeatCount="indefinite"/></line>'
        )
        body.append(
            f'<path d="M{x2 - 6:.1f} {mid - 4} L{x2:.1f} {mid} L{x2 - 6:.1f} {mid + 4}" '
            f'fill="none" stroke="var(--faint)" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )

    # nodes
    for i, name in enumerate(TASKS):
        chars |= set(name)
        x = xs[i]
        cx = x + node_w / 2
        beat = i * 0.5
        body.append(
            f'<rect x="{x:.1f}" y="{y}" width="{node_w}" height="{node_h}" rx="7" '
            f'fill="var(--card)" stroke="var(--faint)"/>'
        )
        # the pulse: only opacity animates, so both themes stay correct
        body.append(
            f'<rect x="{x:.1f}" y="{y}" width="{node_w}" height="{node_h}" rx="7" '
            f'fill="var(--accent)" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.16;0" keyTimes="0;0.12;1" '
            f'begin="{beat:.2f}s" dur="2.5s" repeatCount="indefinite"/></rect>'
        )
        # status light, plus a ring that ripples out each time the task fires
        dot_x = x + 15
        body.append(
            f'<circle cx="{dot_x:.1f}" cy="{mid}" r="6" fill="none" '
            f'stroke="var(--accent)" stroke-width="1.5" opacity="0">'
            f'<animate attributeName="r" values="3.5;11" keyTimes="0;1" '
            f'begin="{beat:.2f}s" dur="1.1s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.55;0" keyTimes="0;1" '
            f'begin="{beat:.2f}s" dur="1.1s" repeatCount="indefinite"/></circle>'
        )
        body.append(f'<circle cx="{dot_x:.1f}" cy="{mid}" r="3.5" fill="var(--live)"/>')
        if i == FLAKY:
            # A red disc stacked over the green one, faded in on a long cycle.
            # Stacking beats animating `fill` because the colours are CSS
            # variables and SMIL cannot interpolate those across themes.
            body.append(
                f'<circle cx="{dot_x:.1f}" cy="{mid}" r="3.5" fill="var(--bad)" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
                f'keyTimes="0;0.55;0.6;0.78;0.83;1" dur="9s" '
                f'repeatCount="indefinite"/></circle>'
            )
        body.append(
            k.text(dot_x + 10 + (node_w - 25) / 2, mid, name, cls="fg", size=12,
                   anchor="middle")
        )

    # packets riding the edges
    for i in range(len(TASKS) - 1):
        x1 = xs[i] + node_w
        x2 = xs[i + 1]
        body.append(
            f'<circle r="3.5" cx="0" cy="0" fill="var(--accent)" opacity="0">'
            f'<animateMotion path="M{x1:.1f} {mid} L{x2:.1f} {mid}" '
            f'begin="{i * 0.5:.2f}s" dur="0.5s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.85;1" '
            f'begin="{i * 0.5:.2f}s" dur="0.5s" repeatCount="indefinite"/></circle>'
        )

    # footer legend
    foot_y = y + node_h + 24
    legend = [("var(--live)", "passing"), ("var(--bad)", "flaky — it is always the tests")]
    x = inset
    for colour, label in legend:
        chars |= set(label)
        body.append(f'<circle cx="{x + 3.5:.1f}" cy="{foot_y}" r="3.5" fill="{colour}"/>')
        body.append(k.text(x + 13, foot_y, label, cls="muted", size=10))
        x += 13 + len(label) * 10 * k.ADVANCE + 26

    palette = (
        ":root{--live:#2da44e;--bad:#cf222e}"
        "@media(prefers-color-scheme:dark){:root{--live:#3fb950;--bad:#f85149}}"
    )
    return _wrap(WIDTH, int(foot_y + 16), "".join(body), "".join(sorted(chars)),
                 "pipeline", palette)


# --------------------------------------------------------------------------

def _wrap(width: int, height: int, body: str, chars: str, title: str, extra_css: str = "") -> str:
    """Like svgkit.svg but with the card fill these two scenes need."""
    svg = k.svg(width, height, body, chars, title)
    card = (
        "</style>",
        ":root{--card:#ffffff}"
        "@media(prefers-color-scheme:dark){:root{--card:#0d1117}}"
        + extra_css
        + "</style>",
    )
    return svg.replace(*card, 1)


# --------------------------------------------------------------------------
# section headings
# --------------------------------------------------------------------------

HEADINGS = ["about", "the loop", "stack", "projects", "stats", "about this page"]


def heading(label: str) -> str:
    """A section heading: the word, then a rule that draws itself in."""
    size, pad = 12, 10
    text_w = len(label) * size * k.ADVANCE
    rule_x = text_w + pad + 12
    rule_w = WIDTH - rule_x
    body = (
        k.text(0, 14, label, cls="muted b", size=size, extra=' letter-spacing="1.6"')
        + f'<rect x="{rule_x:.1f}" y="13.5" height="1" width="{rule_w:.1f}" fill="var(--faint)">'
        + k.grow(0.15, rule_w)
        + "</rect>"
    )
    return k.svg(WIDTH, 28, body, chars=label, title=label)


def main() -> int:
    files = {"hero.svg": terminal(), "pipeline.svg": pipeline()}
    for label in HEADINGS:
        files[f"hd-{label.replace(' ', '-')}.svg"] = heading(label)

    for name, content in files.items():
        changed = k.write(k.ROOT / name, content)
        print(f"{'wrote' if changed else 'unchanged':>9} {name:<26} {len(content):>7,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
