<div align="center">

<img src="./hero.svg" width="620" alt="terminal"/>

[linkedin](https://www.linkedin.com/in/aaronmurphy45/) &nbsp;·&nbsp;
[email](mailto:aaronm2766@gmail.com)

</div>

<img src="./hd-about.svg" width="620" alt="about"/>

> Backend engineer in Dublin, Ireland.<br>
> Systems that have to stay up, and the pager that proves it.

Five years building things other people depend on. Mostly Python, some Go, a lot of<br>
SQL, and more YAML than I'd like to admit to in public.

I like the unglamorous half of the job: finding the N+1, deleting more than I add,<br>
making the slow thing fast, and writing the runbook so nobody has to guess at 3am.

<img src="./hd-the-loop.svg" width="620" alt="the loop"/>

<img src="./pipeline.svg" width="620" alt="commit, build, test, review, ship"/>

<img src="./hd-stack.svg" width="620" alt="stack"/>

<samp>python &nbsp; go &nbsp; sql &nbsp; javascript &nbsp; airflow &nbsp; celery &nbsp; redis &nbsp; postgres &nbsp; azure &nbsp; docker &nbsp; git &nbsp; linux</samp>

<!-- The projects section is parked until there are real public repos to point
     at. Restore it from git history rather than rewriting the placeholders:
     the heading art (hd-projects.svg) is still in the repo and unused. -->

<div align="center">

<img src="./portrait.jpg" width="360" alt="Aaron Murphy"/>

</div>

<img src="./hd-stats.svg" width="620" alt="stats"/>

<div align="center">

<img src="./stats.svg" width="620" alt="Contributions in the last year"/>

<img src="./streak.svg" width="620" alt="Current and longest streak"/>

<img src="./langs.svg" width="620" alt="Top languages by bytes and by repo"/>

<img src="./year.svg" width="620" alt="The last year, one character per day"/>

</div>

<img src="./hd-about-this-page.svg" width="620" alt="about this page"/>

No badge services here. Every image on this page is an SVG built in this repo<br>
and committed alongside the README, which means there is no third-party host to<br>
rate-limit me, change its API, or quietly shut down.

[A nightly action](.github/workflows/stats.yml) queries the GitHub GraphQL API,<br>
redraws the stat graphics, and commits only the files whose bytes actually<br>
changed — a quiet day produces no commit at all.

The headings are images because styling README text is impossible — GitHub<br>
sanitises `<script>` and `<style>` out of markdown — so the only route to a<br>
chosen typeface is to draw the words yourself.

That typeface is [JetBrains Mono](scripts/fonts), subset per graphic to the<br>
handful of glyphs it draws and base64-inlined, since an SVG loaded via `<img>`<br>
cannot fetch anything external.

Every graphic is drawn complete at frame zero. That constraint is the whole<br>
design, and it was learned the hard way: GitHub renders a README image at t=0<br>
and never advances the SMIL timeline, so a fade that starts at opacity 0 or a<br>
clip that reveals from width 0 is not a subtle animation — it is a blank box,<br>
permanently, for every visitor. The first version of this page shipped a<br>
terminal that typed itself out and was therefore invisible. Motion now only<br>
ever loops on top of an already-finished picture.

Language figures count public repositories only. `year.svg` draws one character<br>
per day: `:` `+` `#` `@`, quiet to loud.
