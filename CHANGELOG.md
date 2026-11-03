# Changelog

All notable changes of each release. Versions follow [Semantic Versioning](https://semver.org). Before 1.0, a minor version can change markup, attributes, events, or exports; these changes are listed first, under "Breaking", with the steps to upgrade. The release notes on GitHub are the section of that version.

When you upgrade, replace all kit files with the files of one release. Do not mix files of two versions.

## Unreleased

### Breaking

- A boolean option with the value `"false"` is now off, like an absent option, everywhere (for example `data-disabled="false"` on select and combobox items, `data-multiple="false"`, `data-loop="false"`). Before, some options read any value as on. To upgrade: remove `data-x="false"` where you want the option on. (#16)

### Added

- The `play` and `pause` icons. (#34)

### Changed

- `clanker-ui.css` is readable, not minified. Use `dist/clanker-ui.min.css` for the minified file. Every rule is in a `clanker.*` layer; a reduced-motion `.shimmer` rule outside all layers is gone. (#12)

### Fixed

- `.shimmer-once` runs once and `.shimmer-reverse` runs in reverse. (#12)
- An open drawer that leaves the page (for example after an htmx or SPA swap) no longer blocks Tab on the page and removes its `touchmove` listener. (#13)
- A toast that leaves the page no longer captures F6. (#13)
- A `reset` event that the app cancels with `preventDefault()` no longer resets select, combobox, and calendar values. (#13)
- The chart treats an impossible ISO date (`2026-02-30`) as invalid, not as the next month. (#13)
- Select and combobox keep the authored `data-value` when the items arrive later, and follow a later `data-value` change. (#16)
- The slider shows a `value` change from code after an `input` or `change` event, and `disabled`, `min`, `max`, and `step` changes on its inputs. (#16)
- `el.disabled = false` enables a checkbox, switch, or radio item again. (#16)
- A fast click on a select trigger no longer leaves a `mouseup` listener on the document that keeps the removed select in memory. (#34)
- The chart draws values near ±1e308 without NaN coordinates and console errors; a stacked total that is not a finite number is left out, like a value that is not a finite number. (#34)
- The message scroller no longer reads the layout of every message on each scroll event (8000 messages: 6.3 ms to 0.07 ms per event). (#34)
- A `<select>` made with `h()` no longer reports a `style-src-attr` CSP violation in Safari 27.2 (WebKit bug 327212). (#36)
- `clanker-ui.min.js` exports the core API (`h`, `icon`, `theme`, `isOpen`, ...), the same names as `clanker-ui.js`. Before, an import of a core name from the one-file `.min` set failed. (#37)
- `toast()` works after the app replaces the content of an open modal dialog, and the visible toasts stay. (#30)
- Focus goes back to a dialog trigger that was disabled when the dialog opened. (#31)
- An alert dialog that opens with the pointer shows no focus ring flash on Cancel in Safari. (#32)

## 0.1.0 - 2026-11-02

First public release.

- 67 shadcn/ui components (Base UI base, Nova style) as plain HTML, CSS, and JavaScript, with no dependencies and no build step. They work under a strict Content Security Policy with Trusted Types.
- The kit files `clanker-ui.css` and `clanker-ui.js`, the chart module `clanker-ui-chart.js`, the theme script `clanker-ui-theme.js`, the optional color schemes `clanker-ui-themes.css`, and the accessibility layer `clanker-ui-a11y.css`.
- Minified files and per-group files (core, forms, overlays, layout, chat, chart) in `dist/`.
- The Agent Skill `skills/clanker-ui/` with the component catalog `clanker-ui.json`, `components.md`, `events.md`, and `csp.md`.
- Docs site and demo of all components: <https://bl4ko.github.io/clanker-ui/>.
- Release assets: every kit file, a zip with the kit, `dist/`, the license files, and the skill, `SHA256SUMS`, and build provenance attestations.
