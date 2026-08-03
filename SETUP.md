# Setup

Nothing here has been committed or pushed. These are local files — review them,
then move them into a repo yourself when you're happy.

## 1. The repo

The profile README only renders if the repo is named **exactly** your username:

    aaronmurphy45/aaronmurphy45

It must be **public**, and `README.md` must be at the root. Create it on
github.com, then copy this directory's contents into your clone.

## 2. Fonts

Download JetBrains Mono and put two files in `scripts/fonts/`:

    JetBrainsMono-Regular.ttf
    JetBrainsMono-Bold.ttf

From <https://github.com/JetBrains/JetBrainsMono/releases>. OFL-1.1, so
redistributing them in your repo is fine — include the licence file.

Everything works without them; you just get the viewer's default monospace, and
the portrait may look horizontally squeezed.

## 3. Generate

Two scripts, split by whether they need the API.

**No token needed** — the terminal, the pipeline, the section headings:

    pip install -r requirements.txt
    python scripts/scenes.py

These are already generated and committed here, so you only re-run this after
editing `SESSION` or `TASKS` in [`scripts/scenes.py`](scripts/scenes.py).

**Token needed** — the four stat graphics:

    GITHUB_TOKEN=<a classic PAT, public_repo scope is enough> \
    GITHUB_LOGIN=aaronmurphy45 \
    python scripts/generate.py

Writes `stats.svg`, `streak.svg`, `langs.svg`, `year.svg`. These are *not* in
this directory — the only run so far used synthetic test data, and shipping
invented contribution numbers would be worse than shipping nothing. Generate
them against your real account before the README will render fully.

To check your work, `python -m http.server` in this directory and open
`preview.html`. It has to be over HTTP rather than `file://` for the SMIL to
run. `preview.html` is gitignored.

## 4. Portrait

    python scripts/make_portrait.py photo.jpg --cols 92

Prints the ASCII to the terminal and writes `ascii.svg`. Tune with `--cols`,
`--contrast`, `--size`; add `--invert` for a light subject on a dark
background. A high-contrast, tightly-cropped headshot works far better than a
busy one — the ramp only has ten levels.

Run once, commit the SVG, forget it.

## 5. Automation

`.github/workflows/stats.yml` runs daily at 04:17 UTC and on demand from the
Actions tab. It uses the built-in `GITHUB_TOKEN` — no secret to configure.

**It commits to your repo.** That's the whole point, but it does mean an
automated daily commit if any stat changed. If you'd rather it never pushed,
delete the last step and run the generator by hand.

For it to push, Settings → Actions → General → Workflow permissions must be
**Read and write**.

## 6. Content still to write

The **projects** section in `README.md` is a placeholder — two dummy entries
marked with an HTML comment. Replace them with real public repos as you seed
them; an empty projects section reads better than invented ones.

Everything else is deliberately generic. The terminal session and the pipeline
say nothing about any employer or their problem domain — they're a personality
sketch, not a CV. Edit `SESSION` and `TASKS` in
[`scripts/scenes.py`](scripts/scenes.py) to change the jokes.

## Notes on the design

- **No third-party badge services.** Every image is generated here and
  committed, so nothing can rate-limit you or disappear.
- **Animation is SMIL, not JS.** GitHub strips `<script>` and `<style>` from
  README markdown, but an SVG rendered as an image keeps its own internals.
- **Base state is the finished state.** Animated elements carry their final
  values as plain attributes, and the SMIL delay lives in `keyTimes` rather
  than `begin`. Renderers that ignore SMIL — GitHub's mobile app, feed readers,
  anything rasterising at t=0 — show the completed graphic instead of a blank
  box. This was verified by stripping every `<animate>` and re-rendering.
- **Themes follow the viewer.** `prefers-color-scheme` inside the SVG works
  even when the SVG is an `<img>`.
- **Fonts must be inlined.** An SVG loaded via `<img>` cannot fetch anything
  external, so `svgkit.font_face()` subsets per graphic and base64-embeds.
