# Changelog

All notable changes of each release. Versions follow [Semantic Versioning](https://semver.org). Before 1.0, a minor version can change markup, attributes, events, or exports; these changes are listed first, under "Breaking", with the steps to upgrade. The release notes on GitHub are the section of that version.

When you upgrade, replace all kit files with the files of one release. Do not mix files of two versions.

## Unreleased

### Breaking

- `calendar` and `date-picker` move from the `chat` group to the `overlays` group, so a form with a date picker needs only `forms` and `overlays`. The one-file set does not change. To upgrade with group files: load `clanker-ui-overlays.min.css` and `.js` (and `forms` for the date picker) instead of `chat` for these components.

### Added

- AI Elements (shadcn/ui October 2026): docs pages at `/docs/ai-elements` with patterns for chat and agent pages, built only from kit components: Message. Each page has the shadcn sections, live examples, and the module that plays the demo. `clanker-ui.json` has a `patterns` list (name, title, description, the components of the examples, docs links), and the skill has `references/ai-elements.md` (which pattern for which job).
- Lucide icons `circle-dashed`, `flask-conical`, `list-todo`, `message-circle-dashed`, `route`, and `telescope` (242 in total).
- Kit parts (core, CSS only): `card-grid` (a grid of record cards, `data-size="sm|lg"`), `cover` (placeholder art from tokens, `data-tone="1"`…`"5"`, `data-ratio="square|video"`), `rating` (read-only stars), and `data-layout="split"` on `page` (shadcn login-02: a form column and a `page-aside` art panel from 64rem).
- `sheet-body` and `drawer-body`: the scrolling middle of a sheet or drawer between a fixed header and footer.
- Status fill tokens `--success-fill`, `--warning-fill`, `--error-fill`, and `--info-fill` for bars, dots, and meters: 3:1 or more on the card and the same hue in light and dark.
- Blocks: ten whole pages built only from kit parts, in the skill (`references/blocks/<name>.html` and `.js`) and on the docs site under Blocks with a live preview, a phone width toggle, and the code: `dashboard` (shadcn dashboard-01), `data-table` (shadcn tasks example), `settings`, `form`, `detail`, `login` (shadcn login-03), `login-split` (shadcn login-02, a brand panel of token art and a quote), `card-grid` (books with token covers, filter tabs with counts, sort, and the no-results state), `overlay-form` (a validated review form with a star rating in a dialog, and a long form in a sheet with a scrolling body), and `states` (empty, loading, and error).
- Blocks carry the static-host CSP meta tag of `references/csp.md` as the second element of `<head>`; the docs server and the export no longer add one, and a block without it does not load. The `form` block has a date range, a live summary and project rules in a side column, and an edit mode (`?id=web`) that fills the fields from code and offers Delete with an `alert-dialog`. The `data-table` block shows the status under the title on phones, and the unsorted header icon is always `chevrons-up-down`. The `detail` block confirms Delete with an `alert-dialog` and shows more activity. Each works under the strict CSP in light and dark at 1280 and 390 px.
- Page parts (core group, CSS only): `page` (gutters, gaps, `data-size="sm|md|lg"`, `data-layout="center"`), `page-header` with `page-title`, `page-description`, and `page-actions`, `page-body` with `page-aside` and `page-nav`, `site-header` (`site-header-title`, `site-header-nav`, `site-header-actions`, `data-size="lg"`), `section-cards` (the dashboard-01 KPI cards; a subgrid keeps the headers and footers of a row aligned, and values wrap instead of being cut), `stat-grid` (static numbers from a `dl`, `data-size="sm"` for facts), the `data-table` frame (`data-table-toolbar`, `data-table-pagination`, `data-table-selection`, `data-table-text`), `brand` with `brand-mark`, and `text-stack`.
- `data-show-from="sm|md|lg|xl"` and `data-hide-from="sm|md|lg|xl"` hide an element below or from a viewport width, like `hidden lg:flex` in the shadcn blocks.
- `data-align="end|center"` on `table-head` and `table-cell`; `data-columns="2|3"` and `data-span="2"` on `field-group` fields (aligned at the top, so an error does not move the next field); `field-label-row` for a label with a link at the end; a count `badge` in a `tabs-trigger` gets the dashboard-01 look; a `skeleton` with text takes the size of that text.
- Skill: `references/design.md` (design rules with the kit part and the lint rule of each), `references/choosing.md` (which component for which job), and a "Build a page" step in `SKILL.md`.
- 109 more Lucide icons that apps often need (for example `layout-grid`, `receipt`, `wallet`, `euro`, `server`, `database`, `map-pin`, `phone`, `chart-bar`, `chart-pie`, `loader`), 236 in total. The old Lucide names (`alert-triangle`, `help-circle`, `check-circle`, `unlock`, `bar-chart`, ...) work as aliases. The core module grows by 19.6 KB (5.7 KB gzip).
- `registerIcons({ name: nodes })` adds app icons from Lucide icon nodes, under the strict CSP.
- Agent skill: `references/icons.md` lists every icon name and alias and shows how to add an icon. It is made from the kit by `go run ./tools/gen catalog`.
- `dist/clanker-ui-theme.min.js`, so every kit file has a `.min` version.
- Chart `timeZone` option: the time axis places its ticks, and every date and time shows, in that IANA zone (default: the browser zone). An ISO date (`2026-10-01`) is that day in the zone.
- Docs: chart `locale`, the stat tile compact default (`€30.5K` from 10,000) and `notation: "standard"`, and the stat tile in a card.
- Date picker: `data-required` on the root. In a `data-slot="form"` an empty picker gets the `field-error`, `aria-invalid` on the trigger, and focus on submit.
- Toggle group: `data-required` (the last pressed item stays pressed, and a form needs a value), `data-name` (submits the value), `form.reset()`, and `data-value` changes from code.
- Tabs: a `tabs-content` without `data-value` is a shared panel for every tab (a tab bar that filters one table).
- Pagination: `aria-disabled="true"` on Previous or Next dims the link and blocks the click.
- Docs: the `form:submit` default action (a native submit), all `data-error-<flag>` names, the date picker language and labels, a file input and dropzone recipe, `position()` for custom floating content, a dropdown `data-align="end"` example, and the favicon 404 in the test steps.
- Agent skill: a design lint, `references/design-lint.js` (plain JavaScript, no dependencies). A Playwright test loads it into the page and calls `clankerDesignLint()` to find design mistakes that a screenshot shows: buttons of two sizes in one row, two primary buttons, cut text, a page wider than the viewport, small targets, low contrast, colors that are not tokens, missing labels, skipped headings, near-miss alignment, and a card with a large empty area. `clankerDesignLint.watchShift()` finds controls that move during an interaction. `references/testing.md` tells how to run it and lists the rules. The server and the docs site serve the file.
- Agent skill: `references/recipes.md`: set values from code, a form in a dialog or a sheet with a scrolling body, several custom rules on one field, an accessible star rating, a card grid, a shared header on static pages without a build step, a breadcrumb or back link in the top-header shell, a category bar chart, status strips with keyboard access, and long pages.
- Docs: design rules from the second agent evaluation: one identity move per app, realistic data and complete pages, phone tables that keep status and the main value, chart height and status fills, condensed long pages, muted secondary links, and phone navigation with every primary link. Also kit radius and display sizes for app parts, a `python3 -m http.server` test recipe, the CSP meta tag in the head example, which pagination a table uses, badge or icon and word in tables, toggle group labels, the `item-description` two-line clamp, list spacing with separators, and where `dropdown-menu:change` is emitted.

### Changed

- Agent skill: load `clanker-ui-a11y.css` in every app (it was optional); the head example and the known lint results show it. The version line says that it is the last release and that a copy from `main` can be newer. The dropzone recipe uses `span` parts inside its `label`.
- Color schemes: each editor scheme (Tokyo Night, Catppuccin, Gruvbox, Nord, Dracula, Rosé Pine, Solarized, One, Kanagawa, Everforest, GitHub) has chart colors from its own accents, ordered and checked for color-vision deficiency, normal vision, and 3:1 contrast against the card in light and dark. They set `--chart-other` and `--chart-good` too. Before, all editor schemes used one generic palette that looked muddy on their surfaces, and `--chart-6` had no dark value.
- An unknown icon name no longer throws. `icon()` and `<svg data-lucide>` log one `console.warn` per name and render an empty icon, as Lucide `createIcons` does.
- Chart colors: the kit `--chart-1`…`--chart-5` are the validated categorical hues of the accessibility layer, not the shadcn gray ramp, so a chart with several series is readable without app tokens. The shadcn base schemes of `clanker-ui-themes.css` still set the exact shadcn values.

### Fixed

- A `<form data-slot="form">` that is the direct child of a dialog, alert dialog, sheet, or drawer content is `display: contents`, like a plain form, so the header, fields, and footer keep the content gap and the sheet footer stays at the bottom.
- Dropdown menu, context menu, and menubar: `data-value` on a radio group selects its item at load, and a later change of the group `data-value` or of an item `data-checked` from code updates the items.
- Date picker: in a vertical `field` the picker fills the width like an input; with `clanker-ui-a11y.css` the trigger has the same border as the inputs.
- Design lint: `button-size-mismatch` compares the outer height of a horizontal `toggle-group` with the other controls in its row, so a 28 px `sm` toggle group next to a 32 px input in a toolbar is an error. The items inside the group are still not compared. The docs block page width toggle is `sm`, like the Open in New Tab button next to it.
- A `select` in a vertical `field` is full width, as the shadcn field makes every child full width.
- Stat tile: `deltaFormat: { minimumFractionDigits: 2 }` no longer throws "maximumFractionDigits value is out of range"; the default maximum rises to the minimum.
- Stat tile: inside a `card` the tile drops its own border, background, shadow, and padding, so there is one border.
- Form reset: a value that the app sets right after `form.reset()` or in its `reset` listener (select, combobox, toggle group `data-value`, `calendarSetValue`) is no longer overwritten by the kit restore one task later.
- Date picker: `calendarSetValue()` without `{ emit: true }` and a `data-value` change on the calendar update the trigger text.
- Field: `field-separator` draws its line; the kit adds the `separator` child and `data-content`, as shadcn renders them.
- Form: after a submit, leaving a control does not validate it; only a change does, as in React Hook Form. Before, a field that the app cleared after a valid send showed its error on blur, and the layout shift could move the next click target.

## 0.2.1 - 2026-11-04

The kit files do not change. This release updates only the docs site.

### Fixed

- Docs site: no page shows "This page is not ported yet." Every component and guide page is a real page made from the catalog, the README, and the live demo section: preview, installation, usage, examples, API reference, and keyboard notes. The `.md` alternate of each page is the page Markdown, and `sitemap.xml` lists every page. (#47)

## 0.2.0 - 2026-11-03

### Breaking

- A boolean option with the value `"false"` is now off, like an absent option, everywhere (for example `data-disabled="false"` on select and combobox items, `data-multiple="false"`, `data-loop="false"`). Before, some options read any value as on. To upgrade: remove `data-x="false"` where you want the option on. (#16)

### Added

- The `play` and `pause` icons. (#34)
- Docs site: a Native Select page. Every docs page links its Markdown (`<link rel="alternate" type="text/markdown">`) and `llms.txt` (`rel="describedby"`). The Markdown of a component page that is not ported yet is the component file of the skill, and a guide page that is not ported yet links its README section. `sitemap.xml` lists only real pages, and the site has no `robots.txt`. (#43)
- Chart reference lines and bands (`references`), a time axis for line and area charts (`scale: "time"`), and `connectNulls`. (#38)
- Agent skill: one Markdown file for each component in `references/components/`; `components.md` is an index. Setup, theming, and test steps move from `SKILL.md` to `references/setup.md`, `theming.md`, and `testing.md`. `dialogOpen` and `dialogClose` are also listed for alert dialog, sheet, and drawer. (#41)
- README: an install command for the agent skill, a quick start that works when you paste it, and recipes to override the kit (tokens, dialog width, fonts, Tailwind layer order, `!important`). (#14)

### Changed

- `clanker-ui.css` is readable, not minified. Use `dist/clanker-ui.min.css` for the minified file. Every rule is in a `clanker.*` layer; a reduced-motion `.shimmer` rule outside all layers is gone. (#12)
- Menubar: on a hover switch, the old menu closes 45 ms after the new menu opens, as in shadcn. After a press outside a modal menubar, focus goes back to the trigger. (#1, #4)
- `llms-full.txt` is smaller (259 KB to 221 KB): it does not repeat README examples, keyboard lines, and exports. (#28)

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
- The navigation menu stays open after a click that comes less than 500 ms after a hover open. (#29)
- The catalog gives each component of a combined README section its own lines, lists the indicators that the kit makes as kit parts, and gives no state from the attributes of other components. (#28)
- The skill and README name the right file to import each export from, for the one-file set and for the group set. (#25)

## 0.1.0 - 2026-11-02

First public release.

- 67 shadcn/ui components (Base UI base, Nova style) as plain HTML, CSS, and JavaScript, with no dependencies and no build step. They work under a strict Content Security Policy with Trusted Types.
- The kit files `clanker-ui.css` and `clanker-ui.js`, the chart module `clanker-ui-chart.js`, the theme script `clanker-ui-theme.js`, the optional color schemes `clanker-ui-themes.css`, and the accessibility layer `clanker-ui-a11y.css`.
- Minified files and per-group files (core, forms, overlays, layout, chat, chart) in `dist/`.
- The Agent Skill `skills/clanker-ui/` with the component catalog `clanker-ui.json`, `components.md`, `events.md`, and `csp.md`.
- Docs site and demo of all components: <https://bl4ko.github.io/clanker-ui/>.
- Release assets: every kit file, a zip with the kit, `dist/`, the license files, and the skill, `SHA256SUMS`, and build provenance attestations.
