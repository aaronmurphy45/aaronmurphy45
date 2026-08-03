# fonts

Drop the two TTFs here:

- `JetBrainsMono-Regular.ttf`
- `JetBrainsMono-Bold.ttf`

From <https://github.com/JetBrains/JetBrainsMono/releases> (OFL-1.1 — free to
redistribute, keep the licence file alongside them).

`svgkit.font_face()` subsets each one to just the characters a given graphic
draws, converts to WOFF2, and inlines it as base64. Without these files
everything still generates and lays out correctly; it just falls back to the
viewer's default monospace, and the ASCII portrait may look horizontally
squeezed on machines whose default is narrower than 0.600 em.
