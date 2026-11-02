# Changelog

All notable changes of each release. Versions follow [Semantic Versioning](https://semver.org). Before 1.0, a minor version can change markup, attributes, events, or exports; these changes are listed first, under "Breaking", with the steps to upgrade. The release notes on GitHub are the section of that version.

When you upgrade, replace all kit files with the files of one release. Do not mix files of two versions.

## Unreleased

## 0.1.0 - 2026-11-02

First public release.

- 67 shadcn/ui components (Base UI base, Nova style) as plain HTML, CSS, and JavaScript, with no dependencies and no build step. They work under a strict Content Security Policy with Trusted Types.
- Readable files `clanker-ui.css` and `clanker-ui.js`, the chart module `clanker-ui-chart.js`, the theme script `clanker-ui-theme.js`, the optional color schemes `clanker-ui-themes.css`, and the accessibility layer `clanker-ui-a11y.css`.
- Minified files and per-group files (core, forms, overlays, layout, chat, chart) in `dist/`.
- The Agent Skill `skills/clanker-ui/` with the component catalog `clanker-ui.json`, `components.md`, `events.md`, and `csp.md`.
- Docs site and demo of all components: <https://bl4ko.github.io/clanker-ui/>.
- Release assets: every kit file, a zip with the kit, `dist/`, the license files, and the skill, `SHA256SUMS`, and build provenance attestations.
