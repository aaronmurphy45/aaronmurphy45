"""Draw every stat graphic on the profile from the GitHub GraphQL API.

Run daily by .github/workflows/stats.yml. Writes only files whose bytes
changed, so a quiet day produces an empty diff and no commit.

    GITHUB_TOKEN=... GITHUB_LOGIN=aaronmurphy45 python scripts/generate.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

import svgkit as k

API = "https://api.github.com/graphql"
WIDTH = 620

QUERY = """
query($login:String!, $cursor:String) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first:100, after:$cursor, ownerAffiliations:OWNER,
                 isFork:false, privacy:PUBLIC) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        languages(first:12, orderBy:{field:SIZE, direction:DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def query(token: str, login: str, cursor: str | None) -> dict:
    payload = json.dumps({"query": QUERY, "variables": {"login": login, "cursor": cursor}})
    request = urllib.request.Request(
        API,
        data=payload.encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{login}-profile-generator",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.load(response)
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def fetch(token: str, login: str) -> tuple[dict, list[dict]]:
    user = query(token, login, None)
    calendar = user["contributionsCollection"]["contributionCalendar"]
    repos = list(user["repositories"]["nodes"])
    page = user["repositories"]["pageInfo"]
    while page["hasNextPage"]:
        user = query(token, login, page["endCursor"])
        repos.extend(user["repositories"]["nodes"])
        page = user["repositories"]["pageInfo"]
    return calendar, repos


# --------------------------------------------------------------------------
# derived numbers
# --------------------------------------------------------------------------

def flatten(calendar: dict) -> list[tuple[date, int]]:
    days = []
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            days.append((date.fromisoformat(day["date"]), day["contributionCount"]))
    return sorted(days)


def streaks(days: list[tuple[date, int]]) -> tuple[int, int, date | None, date | None]:
    """Current streak, longest streak, and the longest streak's date range.

    Today is excluded from breaking the current streak -- a day still in
    progress with no commits yet shouldn't zero out a live streak.
    """
    today = date.today()
    longest = run = 0
    best_end = run_start = None
    best_start = None
    for day, count in days:
        if count > 0:
            run = run + 1 if run else 1
            if run == 1:
                run_start = day
            if run > longest:
                longest, best_start, best_end = run, run_start, day
        else:
            run = 0

    current = 0
    for day, count in reversed(days):
        if count > 0:
            current += 1
        elif day != today:
            break
    return current, longest, best_start, best_end


def language_totals(repos: list[dict]) -> tuple[list[tuple[str, int, str]], list[tuple[str, int, str]]]:
    """Language bytes and repo counts, both descending. Public repos only."""
    by_bytes: dict[str, int] = {}
    by_repo: dict[str, int] = {}
    colours: dict[str, str] = {}
    for repo in repos:
        seen = set()
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            colours[name] = edge["node"]["color"] or "#8b949e"
            by_bytes[name] = by_bytes.get(name, 0) + edge["size"]
            seen.add(name)
        for name in seen:
            by_repo[name] = by_repo.get(name, 0) + 1

    rank = lambda d: sorted(d.items(), key=lambda kv: -kv[1])
    return (
        [(n, v, colours[n]) for n, v in rank(by_bytes)],
        [(n, v, colours[n]) for n, v in rank(by_repo)],
    )


def human_bytes(n: int) -> str:
    for unit in ("B", "K", "M", "G"):
        if n < 1024 or unit == "G":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}G"


# --------------------------------------------------------------------------
# graphics
# --------------------------------------------------------------------------

def calendar_svg(days: list[tuple[date, int]], total: int) -> str:
    cell, gap = 8, 2
    step = cell + gap
    top = 22
    peak = max((c for _, c in days), default=0)

    def level(count: int) -> int:
        if count == 0 or peak == 0:
            return 0
        return min(4, 1 + int(3 * count / peak))

    # Column 0 is the week containing the first day; weekday 0 = Sunday.
    first = days[0][0]
    origin = first - timedelta(days=(first.weekday() + 1) % 7)

    # Group cells by diagonal band rather than by column: the grid then washes
    # in on a wave from the top-left instead of wiping left to right. One
    # <animate> per band keeps the file about the same size as per-column.
    bands: dict[int, list[str]] = {}
    columns: set[int] = set()
    for day, count in days:
        offset = (day - origin).days
        col, row = divmod(offset, 7)
        columns.add(col)
        rect = (
            f'<rect x="{col * step}" y="{top + row * step}" width="{cell}" height="{cell}" '
            f'rx="2" fill="var(--l{level(count)})"/>'
        )
        bands.setdefault(col + row * 3, []).append(rect)

    weeks = max(columns) + 1
    body = [k.text(0, 8, f"{total:,} contributions in the last year", cls="muted", size=12)]
    for band in sorted(bands):
        body.append(f'<g>{"".join(bands[band])}{k.fade_in(band * 0.011, 0.4)}</g>')

    # Month ticks along the bottom. The first column is usually a partial week,
    # so its month label can land within a few pixels of the next one -- keep a
    # minimum gap rather than letting them overprint each other.
    baseline = top + 7 * step + 12
    min_gap = 4 * 10 * k.ADVANCE  # three glyphs plus a space, at size 10
    label_chars = set()
    seen_month = None
    last_x = None
    for col in sorted(columns):
        day = origin + timedelta(days=col * 7)
        x = col * step
        if day.month == seen_month or col >= weeks - 2:
            continue
        seen_month = day.month
        if last_x is not None and x - last_x < min_gap:
            continue
        last_x = x
        name = day.strftime("%b").lower()
        label_chars |= set(name)
        body.append(k.text(x, baseline, name, cls="muted", size=10))

    chars = f"{total:,} contributions in the last year" + "".join(sorted(label_chars))
    return k.svg(WIDTH, baseline + 8, "".join(body), chars,
                 f"{total} contributions in the last year")


def streak_svg(total: int, current: int, longest: int,
               best_start: date | None, best_end: date | None) -> str:
    fmt = lambda d: d.strftime("%d %b %Y").lower() if d else "--"
    blocks = [
        (f"{total:,}", "contributions", "last 12 months"),
        (f"{current}", "current streak", "days" if current != 1 else "day"),
        (f"{longest}", "longest streak", f"{fmt(best_start)} - {fmt(best_end)}"),
    ]

    body, chars = [], set()
    column = WIDTH / 3
    for i, (value, label, note) in enumerate(blocks):
        cx = column * i + column / 2
        chars |= set(value + label + note)
        body.append(
            f'<g>'
            + k.text(cx, 26, value, cls="accent b", size=30, anchor="middle")
            + k.text(cx, 52, label, cls="fg", size=12, anchor="middle")
            + k.text(cx, 69, note, cls="muted", size=10, anchor="middle")
            + k.fade_in(0.1 + i * 0.14)
            + "</g>"
        )
        if i:
            body.append(
                f'<rect x="{column * i:.1f}" y="14" width="1" height="52" fill="var(--faint)"/>'
            )
    return k.svg(WIDTH, 84, "".join(body), "".join(sorted(chars)),
                 "Current and longest streak")


def langs_svg(by_bytes: list, by_repo: list, top: int = 6) -> str:
    bars, chars = [], set()
    row_h, y = 20, 30
    label_w, bar_w = 110, 170

    def column(items, x0, heading_text, formatter, delay):
        nonlocal chars
        chars |= set(heading_text)
        out = [k.text(x0, 10, heading_text, cls="muted", size=10)]
        top_value = max((v for _, v, _ in items[:top]), default=1)
        for i, (name, value, colour) in enumerate(items[:top]):
            row_y = y + i * row_h
            shown = formatter(value)
            chars |= set(name + shown)
            width = max(2.0, bar_w * value / top_value)
            out.append(k.text(x0, row_y, name[:14], cls="fg", size=11))
            out.append(
                f'<rect x="{x0 + label_w}" y="{row_y - 4}" height="8" rx="4" '
                f'width="{width:.1f}" fill="{colour}">'
                f'{k.grow(delay + i * 0.07, width)}</rect>'
            )
            out.append(
                k.text(x0 + label_w + bar_w + 10, row_y, shown, cls="muted", size=10, anchor="end")
            )
        return out

    half = WIDTH / 2 + 10
    bars += column(by_bytes, 0, "by bytes", human_bytes, 0.15)
    bars += column(by_repo, half, "by repo", lambda v: f"{v}", 0.25)
    height = y + row_h * min(top, max(len(by_bytes), len(by_repo), 1)) + 4
    return k.svg(WIDTH, int(height), "".join(bars), "".join(sorted(chars)),
                 "Top languages by bytes and by repo")


def year_svg(days: list[tuple[date, int]]) -> str:
    """The last year, one character per day, using the portrait's ramp."""
    size = 11
    cw = size * k.ADVANCE
    lh = 13
    top = 20
    peak = max((c for _, c in days), default=0)

    first = days[0][0]
    origin = first - timedelta(days=(first.weekday() + 1) % 7)
    grid: dict[int, dict[int, str]] = {}
    for day, count in days:
        col, row = divmod((day - origin).days, 7)
        idx = 0 if count == 0 or peak == 0 else min(3, 1 + int(2 * count / peak))
        grid.setdefault(row, {})[col] = k.RAMP[idx]

    width_cols = max((max(cols) for cols in grid.values()), default=0) + 1
    body = [k.text(0, 8, f"{k.RAMP[0]} quiet   {k.RAMP[-1]} loud", cls="muted", size=10)]
    for row in range(7):
        line = "".join(grid.get(row, {}).get(col, " ") for col in range(width_cols))
        body.append(
            f'<g>'
            + k.text(0, top + row * lh, line, cls="fg", size=size,
                     extra=f' xml:space="preserve" textLength="{width_cols * cw:.1f}" '
                           'lengthAdjust="spacing"')
            + k.fade_in(0.1 + row * 0.06)
            + "</g>"
        )
    chars = k.RAMP + " quietloud"
    return k.svg(WIDTH, top + 7 * lh, "".join(body), chars,
                 "The last year, one character per day")


# --------------------------------------------------------------------------

def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    login = os.environ.get("GITHUB_LOGIN")
    if not token or not login:
        print("set GITHUB_TOKEN and GITHUB_LOGIN", file=sys.stderr)
        return 1

    try:
        calendar, repos = fetch(token, login)
    except urllib.error.HTTPError as exc:
        print(f"GitHub API returned {exc.code}: {exc.read()[:300]!r}", file=sys.stderr)
        return 1

    days = flatten(calendar)
    if not days:
        print("no contribution data returned", file=sys.stderr)
        return 1

    total = calendar["totalContributions"]
    current, longest, best_start, best_end = streaks(days)
    by_bytes, by_repo = language_totals(repos)

    files = {
        "stats.svg": calendar_svg(days, total),
        "streak.svg": streak_svg(total, current, longest, best_start, best_end),
        "langs.svg": langs_svg(by_bytes, by_repo),
        "year.svg": year_svg(days),
    }
    changed = [name for name, content in files.items() if k.write(k.ROOT / name, content)]
    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"{stamp}: {len(changed)} of {len(files)} changed"
          + (f" -> {', '.join(sorted(changed))}" if changed else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
