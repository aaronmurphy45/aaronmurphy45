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

<img src="./hd-projects.svg" width="620" alt="projects"/>

<!-- Replace these with real public repos as you seed them. Each block is:
     bold link · <samp>stack</samp>, then two or three lines of what it does.
     Say what it does and what was actually hard about it. -->

**[project-one](https://github.com/aaronmurphy45)** &nbsp;·&nbsp; <samp>python</samp><br>
One line on what it does. One line on the part that was actually difficult.

**[project-two](https://github.com/aaronmurphy45)** &nbsp;·&nbsp; <samp>go</samp><br>
One line on what it does. One line on the part that was actually difficult.

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

The motion is SMIL, declared inside each SVG. READMEs get their `<script>` and<br>
`<style>` tags sanitised away, so animation has to live somewhere GitHub does<br>
not sanitise — and an SVG rendered as an image is exactly that. The headings<br>
are images for the same reason: styling README text is impossible, so the only<br>
route to a chosen typeface is to draw the words yourself.

That typeface is [JetBrains Mono](scripts/fonts), subset per graphic to the<br>
handful of glyphs it draws and base64-inlined, since an SVG loaded via `<img>`<br>
cannot fetch anything external.

Every animated element carries its *finished* value as a plain attribute, with<br>
the delay encoded in `keyTimes` rather than `begin`. Anything that ignores SMIL<br>
still sees a complete graphic instead of an empty box.

Language figures count public repositories only. `year.svg` draws one character<br>
per day: `:` `+` `#` `@`, quiet to loud.
