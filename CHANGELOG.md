# Changelog

All notable changes of each release. Versions follow [Semantic Versioning](https://semver.org). Before 1.0, a minor version can change markup, attributes, events, or exports; these changes are listed first, under "Breaking", with the steps to upgrade. The release notes on GitHub are the section of that version.

When you upgrade, replace all kit files with the files of one release. Do not mix files of two versions.

## 0.4.0 - 2026-11-14

### Added

- Behavior drift check: `tools/behavior drift` records the live shadcn pages again and lists the behavior changes against the committed references (a difference counts only when two records have it), and the weekly `behavior-drift` workflow opens one issue `behavior drift: <component>` per changed component.
- Chart: `tooltip: { hideEmpty: true }` leaves out the series without a value at the hovered point, like Recharts `filterNull`; `hideEmpty: "zero"` also leaves out 0. The keyboard readout uses the same rows. Default unchanged (#124).
- Table: opt-in sortable column heads. `data-sort` (`number`, `date`, `text`, or empty for auto) on a `table-head` makes it a ghost button with the sort icon and `aria-sort`; a click sorts the rows ascending, descending, and back to the first order. Numbers and dates follow the `lang` of the table, text uses `Intl.Collator`, empty values go last, and the sort is stable. `table:sort` (`{ column, dir }`, cancelable for server or paged sorting) and the export `tableSort(head, dir)`. The head button lines up with the cells in any table, and `data-align="end"` puts the icon before the label. The data-table block and the docs data-table example use it instead of their own sort code (#126).

### Changed

- Behavior drift check: the calendar scenario pins a fixed day (`dates.clock.day`, 2026-10-28) in every record and check, so the calendar is compared on each run and no longer goes `stale` on each new shadcn build day. The calendar reference is recorded again on macOS (3 engines, 2 widths, checked twice).
- Parity tool: the example pages of every style are measured against a reference app, a real shadcn install of that style (`tools/parity/refapp.py`: shadcn CLI, the pinned registry items and package versions, `tailwind-merge`), not against the live example page with its `@layer base` file order. Equal (part, state, theme) pairs on the example pages: Nova 91.7 to 98.9 %, Luma 92.7 to 99.0 %, Lyra 93.2 to 98.8 %, Maia 92.7 to 99.0 %, Mira 91.1 to 98.8 %, Sera 96.8 to 98.6 %, Vega 92.6 to 98.0 %. The `parity` workflow runs it on a pull request with the label `parity-ci`. New parity issues #143 and #144.
- Smaller kit CSS with the same computed styles: `dist/clanker-ui.min.css` 634,103 to 599,426 bytes (gzip 58,122 to 55,868, brotli 40,363 to 39,023), `dist/clanker-ui-core.min.css` 90,748 to 87,543 bytes, and the same for the other styles. The generator merges rules with the same selector and `@media` blocks with the same condition and parts where the cascade order permits, and drops `@property` rules that nothing uses. All `--tw-*` definitions and reads stay, so a Tailwind utility on a kit part composes with the kit value as before. `tools/gen/guard` compares every computed style of the old and the new CSS in Chromium, Firefox, and WebKit.
- Tooling: Playwright 1.65.0 (Chromium 158, Firefox 159, WebKit 27.2) in CI and the parity workflow (#147); Node 26 in the parity workflow (#148).
- Behavior references: the carousel reference is recorded again on Playwright 1.65.0 (#149).
- Tests: `docs.docs_sidebar_scroll_restore` accepts the whole-pixel scroll restore of Firefox (#122); `g4.trace` waits for the end of the trace icon rotation (#151).

### Fixed

- Vega style: `card-content` is a flex column with a 12 px gap, like a shadcn install. The generator now reads a compound `.cn-*` style rule like the shadcn style map: its classes go to the plain part, without the condition (#143).
- Navigation menu: in Firefox 159 a menu opened by hover closes again after a press on a link that is dragged out of the menu and released, as on the live shadcn site; the close timer now also starts on `mouseout`, because Firefox 159 sends no `pointerout` after the release (#145).
- Card grid: `card-grid` has `width: 100%`, so it keeps its columns in a parent that sizes it to its content (a centering flex or grid container). Before, it was one 24 px column with cards, and with covers in Firefox 159; with covers in Chromium and WebKit it was as wide as the content of the covers (2 columns in the Cover section of the demo) and now has as many columns as fit (#146).
- Chart: the active dots of line, area, and radar charts no longer fade in again on every pointer move; only the first draw animates (#119).
- Chart: a tooltip that is too wide for either side of the pointer goes above the hovered points (or below them when there is more room), so it no longer covers them (#120).
- Chart tooltip: the editor schemes where `--background` equals `--card` (Catppuccin, Dracula, Everforest, GitHub, Gruvbox, Kanagawa, Nord, One, Solarized, Tokyo Night) give the tooltip the full `--border` in dark mode, so it has an edge on a card. New token `--chart-tooltip-border` (default: `--border` at 50 %) (#121).
- Sidebar: in icon mode the hidden `sidebar-group-label` (moved up 32 px, `opacity: 0`) no longer takes the clicks of the last menu button of the group above (`pointer-events: none`) (#125). shadcn has the same gap.
- Sidebar: `sidebar-inset` has `min-width: 0`, so a wide table scrolls inside its `table-container` and the page no longer scrolls sideways (#123). shadcn `SidebarInset` has the same gap.
- Accessibility layer: the text of destructive badges, buttons, alert-dialog actions, and pagination links is the new token `--destructive-text`. The editor schemes (Tokyo Night, Catppuccin, Gruvbox, Nord, Dracula, Rosé Pine, Solarized, One, Kanagawa, Everforest) mix `--destructive` with black (light) or white (dark), so the text has 4.5:1 on its tinted background, also on hover (#129). The design lint finds the token, so `non-token-color` no longer warns on these parts (#127).
- Design lint `empty-region`: a start-aligned row of three or more columns (a board) is not checked, and a start-aligned item no longer gets the hint "align the row to start" (#131).
- Catalog: an attribute that the kit JavaScript only reads (`data-sticky-header` of `table-container`, `data-layout` of `page`) is a Write attribute, not State, so agents that follow the skill write it (#128).
- Icon size utilities (`[&_svg:not([class*='size-'])]:size-*`) of different parts are written in the Tailwind order (smaller size first), as in a shadcn install, so a button icon in a Lyra marker is 16 px like the button, not 14 px (#144).
- Generator: a base class stays when a later variant class does not set all of its properties (a base `size-6` with a later `w-full` lost its height) (#141).

### Docs

- Recipe "Board (columns of cards)": a Kanban board from `card-grid`, `card`, `item-group`, `badge`, and `empty`, with one line of app CSS. A dedicated board part waits until after 1.0 (#130).

## 0.3.0 - 2026-11-10

### Breaking

- `calendar` and `date-picker` move from the `chat` group to the `overlays` group, so a form with a date picker needs only `forms` and `overlays`. The one-file set does not change. To upgrade with group files: load `clanker-ui-overlays.min.css` and `.js` (and `forms` for the date picker) instead of `chat` for these components.

### Added

- Each kit and `dist/` file of a release names its version in the first-line license comment: `/*! clanker-ui v0.3.0 | MIT | ...`. `head -n 1 <file>` shows which release a copied file is from. The files in the repository have no version.
- Parity of the Luma, Lyra, Maia, Mira, Sera, and Vega styles against the live shadcn preview of each style (`tools/parity --page-style`, `known-<style>.tsv`).
- Calendar: `data-month-format="long"` shows long month names in the month dropdown, like the shadcn `calendar-custom-days` example (#91).
- Rhea style: `clanker-ui-rhea.css` (and `dist/clanker-ui-rhea.min.css`, `dist/clanker-ui-rhea-<group>.min.css`) is the kit CSS generated from the shadcn `style-rhea.css`. Load it instead of `clanker-ui.css`; markup and JavaScript are the same. Nova stays the default and does not change. The catalog lists the styles in `files.styles`.
- Luma, Lyra, Maia, Mira, Sera, and Vega styles: `clanker-ui-<style>.css` (and `dist/clanker-ui-<style>.min.css`, `dist/clanker-ui-<style>-<group>.min.css`), generated from the shadcn `style-<style>.css` like Rhea. All 8 shadcn styles are in the kit; load one style file only.
- Docs: the Attachment, Bubble, Code Block, Drawer, Marker, Message, Message Scroller, and Trace previews and all AI Elements previews are in the Rhea style, like the shadcn docs (the blue scheme where shadcn uses `theme-blue`). The docs chrome stays Nova.
- `data-variant="sticky"` on a last `page-aside`: the side column stays in view below the header from 64rem (the live summary of the `form` block).
- AI Elements (shadcn/ui October 2026): docs pages at `/docs/ai-elements` with patterns for chat and agent pages, built only from kit components: Chat, Message, Prompt Input, Model Selector, Context, and Suggestion. Each page has the shadcn sections, live examples, and the module that plays the demo. `clanker-ui.json` has a `patterns` list (name, title, description, the components of the examples, docs links), and the skill has `references/ai-elements.md` (which pattern for which job).
- AI Elements: Sources (a trace line that opens into the links of a reply, with a Replay demo), Inline Citation (hover cards in a sentence, all `span` parts), and File Tree (folders as collapsibles, a click selects a file).
- AI Elements: Reasoning, Chain of Thought, Tool, Task, and Plan, the agent steps of a turn as `trace` lines, each with the shadcn examples (Tool also with its states, output in a sheet, and an approval item) and a Replay that streams the steps and the reply again.
- AI Elements: Queue (todo sections that update as the agent works), Subagent (a run with its nested tool calls, running and details examples), Confirmation (approve or deny a tool call; the answer turns into a tool line), and Checkpoint (a marker with Restore that drops the later turns). Each demo plays its steps again from plain JavaScript.
- AI Elements: Terminal, Stack Trace, and Test Results, the command, error, and test run lines of a turn, each with the shadcn examples and a Replay that streams the run again.
- Lucide icons `circle-dashed`, `flask-conical`, `list-todo`, `message-circle-dashed`, `route`, and `telescope` (256 in total).
- Icons `audio-lines`, `building-2`, `clipboard-paste`, `clock-2`, `corner-down-left`, `languages`, `panels-top-left` (alias `layout`), and `scissors` (Lucide 1.63.0), used by the shadcn docs examples.
- Page parts: `data-size="lg"` on `page-header` (a 30 px detail title) and `page-meta` (a wrapping row of facts under the description). `data-orientation="horizontal"` on `card`: a first-child `cover` at the start and the other parts in a column next to it (a feature or record card). A `badge` in an `accordion-trigger` sits at the end, before the chevron.
- Agent skill: one head for every page and block in `SKILL.md` (charset, CSP meta, the a11y CSS, the core `modulepreload`, the theme script), checked against every block by `go test`, with the block slots, the ghost `icon` theme toggle, and the footer button order. Recipes for an uptime strip with full code, a toast after a page change, a dropzone with a labeled file input, lists in cards, the status under the amount in phone tables, and a dashboard in the top-header shell; the scheme and accent names in `references/theming.md`; what `detail.group` of `dropdown-menu:change` holds; rules for one page width per app, one structure for KPI cards, one status per row, public pages, and balancing a side column.
- Kit parts (core, CSS only): `card-grid` (a grid of record cards, `data-size="sm|lg"`), `cover` (placeholder art from tokens, `data-tone="1"`…`"5"`, `data-ratio="square|video"`), `rating` (read-only stars), and `data-layout="split"` on `page` (shadcn login-02: a form column and a `page-aside` art panel from 64rem).
- `sheet-body` and `drawer-body`: the scrolling middle of a sheet or drawer between a fixed header and footer.
- Status fill tokens `--success-fill`, `--warning-fill`, `--error-fill`, and `--info-fill` for bars, dots, and meters: 3:1 or more on the card and the same hue in light and dark. `--neutral-fill` is the gray for "no data" marks, also 3:1 or more on the card (`--muted` is almost invisible on a light card).
- Blocks: ten whole pages built only from kit parts, in the skill (`references/blocks/<name>.html` and `.js`) and on the docs site under Blocks with a live preview, a phone width toggle, and the code: `dashboard` (shadcn dashboard-01), `data-table` (shadcn tasks example), `settings`, `form`, `detail`, `login` (shadcn login-03), `login-split` (shadcn login-02, a brand panel of token art and a quote), `card-grid` (books with token covers, filter tabs with counts, sort, and the no-results state), `overlay-form` (a validated review form with a star rating in a dialog, and a long form in a sheet with a scrolling body), and `states` (empty, loading, and error).
- Blocks carry the static-host CSP meta tag of `references/csp.md` as the second element of `<head>`; the docs server and the export no longer add one, and a block without it does not load. The `form` block has a date range, a live summary and project rules in a side column, and an edit mode (`?id=web`) that fills the fields from code and offers Delete with an `alert-dialog`. The `data-table` block shows the status under the title on phones, and the unsorted header icon is always `chevrons-up-down`. The `detail` block confirms Delete with an `alert-dialog` and shows more activity. Each works under the strict CSP in light and dark at 1280 and 390 px.
- Page parts (core group, CSS only): `page` (gutters, gaps, `data-size="sm|md|lg"`, `data-layout="center"`), `page-header` with `page-title`, `page-description`, and `page-actions`, `page-body` with `page-aside` and `page-nav`, `site-header` (`site-header-title`, `site-header-nav`, `site-header-actions`, `data-size="lg"`), `section-cards` (the dashboard-01 KPI cards; a subgrid keeps the headers and footers of a row aligned, and values wrap instead of being cut), `stat-grid` (static numbers from a `dl`, `data-size="sm"` for facts), the `data-table` frame (`data-table-toolbar`, `data-table-pagination`, `data-table-selection`, `data-table-text`), `brand` with `brand-mark`, and `text-stack`.
- `data-show-from="sm|md|lg|xl"` and `data-hide-from="sm|md|lg|xl"` hide an element below or from a viewport width, like `hidden lg:flex` in the shadcn blocks.
- `data-align="end|center"` on `table-head` and `table-cell`; `data-columns="2|3"` and `data-span="2"` on `field-group` fields (aligned at the top, so an error does not move the next field); `field-label-row` for a label with a link at the end; a count `badge` in a `tabs-trigger` gets the dashboard-01 look; a `skeleton` with text takes the size of that text.
- Skill: `references/design.md` (design rules with the kit part and the lint rule of each), `references/choosing.md` (which component for which job), and a "Build a page" step in `SKILL.md`.
- 115 more Lucide icons that apps often need (for example `layout-grid`, `receipt`, `wallet`, `euro`, `server`, `database`, `map-pin`, `phone`, `chart-bar`, `chart-pie`, `loader`, `film`, `tv`, `webhook`, `container`, `rss`, `key-round`), 242 in total. The old Lucide names (`alert-triangle`, `help-circle`, `check-circle`, `unlock`, `bar-chart`, ...) work as aliases. The core module grows by 19.6 KB (5.7 KB gzip).
- `registerIcons({ name: nodes })` adds app icons from Lucide icon nodes, under the strict CSP.
- Code block syntax colors: the optional module `clanker-ui-code.js` (`clanker-ui-code.min.js`, 8.4 KB, 3.8 KB gzip) colors `code-block-content` with `data-language` in the languages of the shadcn highlighter (`ts`, `tsx`, `js`, `jsx`, `json`, `html`, `css`, `bash`, `yaml`, `python`, `diff`, `markdown`, `sql`, `ansi`) plus `go`, and exports `codeBlockHighlight(code, language)`. No dependency, no `innerHTML`: it builds text nodes and `<span data-token>`. Colors are `--code-*` tokens: the shadcn GitHub Light and Dark colors at 4.5:1 on the block, highlighted lines, and removed lines; every editor scheme sets its own, and `clanker-ui-a11y.css` lifts them to 4.5:1. Cost outside the module: core CSS +0.4 KB (+0.2 KB gzip, the `--code-*` defaults), `chat` CSS +6.5 KB (+0.4 KB gzip), `chat` JS +0.7 KB (+0.2 KB gzip), themes +6.5 KB (+0.9 KB gzip), a11y +6.2 KB (+1.2 KB gzip), core JS +20 bytes.
- `code-block-download-button`: saves the block text as `data-filename` (default: the last part of the title) and emits `code-block:download` `{ value, filename }`.
- Docs: the Code Block page shows the shadcn demo (file header, wrap, download, and copy, line numbers, highlighted lines 6 to 10, TypeScript colors), and the Syntax highlighting, Languages, and Terminal output examples.
- Agent skill: `references/icons.md` lists every icon name and alias and shows how to add an icon. It is made from the kit by `go run ./tools/gen catalog`.
- `dist/clanker-ui-theme.min.js`, so every kit file has a `.min` version.
- Chart `timeZone` option: the time axis places its ticks, and every date and time shows, in that IANA zone (default: the browser zone). An ISO date (`2026-10-01`) is that day in the zone.
- Docs: chart `locale`, the stat tile compact default (`€30.5K` from 10,000) and `notation: "standard"`, and the stat tile in a card.
- Date picker: `data-required` on the root. In a `data-slot="form"` an empty picker gets the `field-error`, `aria-invalid` on the trigger, and focus on submit.
- Toggle group: `data-required` (the last pressed item stays pressed, and a form needs a value), `data-name` (submits the value), `form.reset()`, and `data-value` changes from code.
- Tabs: a `tabs-content` without `data-value` is a shared panel for every tab (a tab bar that filters one table).
- Pagination: `aria-disabled="true"` on Previous or Next dims the link and blocks the click.
- Tabs: `data-value` on the root selects a tab from code (no `tabs:change`), like select and toggle group; the kit keeps it in sync when the user picks a tab.
- Docs: the `form:submit` default action (a native submit), all `data-error-<flag>` names, the date picker language and labels, a file input and dropzone recipe, `position()` for custom floating content, a dropdown `data-align="end"` example, and the favicon 404 in the test steps.
- Agent skill: a design lint, `references/design-lint.js` (plain JavaScript, no dependencies). A Playwright test loads it into the page and calls `clankerDesignLint()` to find design mistakes that a screenshot shows: buttons of two sizes in one row, two primary buttons, cut text, a page wider than the viewport, small targets, low contrast, colors that are not tokens, missing labels, skipped headings, near-miss alignment, and a card with a large empty area. `clankerDesignLint.watchShift()` finds controls that move during an interaction. `references/testing.md` tells how to run it and lists the rules. The server and the docs site serve the file.
- Agent skill: `references/recipes.md`: set values from code, a form in a dialog or a sheet with a scrolling body, several custom rules on one field, an accessible star rating, a card grid, a shared header on static pages without a build step, a breadcrumb or back link in the top-header shell, a category bar chart, status strips with keyboard access, and long pages.
- Docs: design rules from the second agent evaluation: one identity move per app, realistic data and complete pages, phone tables that keep status and the main value, chart height and status fills, condensed long pages, muted secondary links, and phone navigation with every primary link. Also kit radius and display sizes for app parts, a `python3 -m http.server` test recipe, the CSP meta tag in the head example, which pagination a table uses, badge or icon and word in tables, toggle group labels, the `item-description` two-line clamp, list spacing with separators, and where `dropdown-menu:change` is emitted.
- `dialog-body`: the scrolling middle of a dialog between the header and the footer; the dialog is at most the window height less 2rem, and the header and the footer stay in view (#104).
- Progress: `data-variant="success|warning|destructive|info"` colors the indicator with the status fill tokens, and `--progress-indicator` on the root sets any color (#105).
- `clanker-ui-a11y.css`: the native select has 16 px text below 48rem, like the input, so iOS Safari does not zoom the page on focus (#108).
- `data-wrap` on `card-action`: the action moves under the title and the description when the card header is narrower than 24rem (#107).
- `data-sticky-header` on `table-container`: the header row sticks to the page scroll when the table fits its box; the kit sets `data-fits`, and the box and its card clip instead of scrolling (#103).
- `data-layout="stack"` on `table-container` with `data-label` on `table-cell`: below 40rem each row is a block of label and value lines, with the table roles set by the kit (#109).

### Changed

- Chart: in RTL a vertical bar, line, or area chart reverses the category axis (the first category at the right) and puts the value axis on the right, like the shadcn `chart-rtl` example; ArrowLeft goes to the next category, as Recharts (#82).
- Progress: `progress-value` and `aria-valuetext` use `Intl.NumberFormat` with `style: "percent"` in the nearest `lang`, like Base UI `Progress.Value` (#84).
- `clanker-ui-a11y.css`: the text of destructive buttons and badges is `--destructive` mixed with 25 % `--foreground`, 4.5:1 on the tinted background (shadcn 3.83:1 in light). Blocks have no `empty-region` or `low-contrast` warning: the `detail` block has a Files card and 4 activity rows, the `overlay-form` block has tags and a Next meeting card, and the `form` summary is sticky. The `card-grid` search is the first control of the toolbar, so it takes the first row on phones.
- Blocks load `clanker-ui-a11y.min.css` and preload the core module, as `SKILL.md` says. The theme toggle is a ghost `icon` button (32 px, as the shadcn site header) everywhere. Footer order: Cancel first and the primary last in a dialog or alert dialog footer; the primary first in a sheet or drawer footer, a card footer, and a page form. A rating input is a `radio-group` with a `rating` in each label (block `overlay-form`), the only way in the skill. The `detail` and `overlay-form` blocks have a 30 px title with a meta row, and `overlay-form` and `card-grid` show their cover in a horizontal card; covers in the `card-grid` block carry no text. The `data-table` block has a New task page action. The CSP meta tag comes right after `<meta charset>` in the docs, as in the blocks.
- Agent skill: load `clanker-ui-a11y.css` in every app (it was optional); the head example and the known lint results show it. The version line says that it is the last release and that a copy from `main` can be newer. The dropzone recipe uses `span` parts inside its `label`.
- Color schemes: each editor scheme (Tokyo Night, Catppuccin, Gruvbox, Nord, Dracula, Rosé Pine, Solarized, One, Kanagawa, Everforest, GitHub) has chart colors from its own accents, ordered and checked for color-vision deficiency, normal vision, and 3:1 contrast against the card in light and dark. They set `--chart-other` and `--chart-good` too. Before, all editor schemes used one generic palette that looked muddy on their surfaces, and `--chart-6` had no dark value.
- An unknown icon name no longer throws. `icon()` and `<svg data-lucide>` log one `console.warn` per name and render an empty icon, as Lucide `createIcons` does.
- Chart colors: the kit `--chart-1`…`--chart-5` are the validated categorical hues of the accessibility layer, not the shadcn gray ramp, so a chart with several series is readable without app tokens. The shadcn base schemes of `clanker-ui-themes.css` still set the exact shadcn values.

### Fixed

- Rhea, Luma, and Sera: a button group with an outline button no longer gives its input, input group, or select trigger the border color; shadcn buttons do not render `data-variant`, so the shadcn rule `has-[>[data-variant=outline]]` matches only parts that render it, like the descendant form already did.
- Sera: input group addons with a button or kbd no longer get a negative margin; the generator now skips rules that a style file has in a comment.
- Vega: a card content with questionnaire choices is a column with a 0.75rem gap; the generator now reads a style rule with a compound selector (`.cn-card-content:has(...)`) and keeps its condition.

- Docs: the ghost bubble of the Bubble variants example has the shadcn Markdown text, paragraph spacing, and inline code look.
- `data-layout="split"`: a child of the form column with `hidden` stays hidden (before, the layout made it `display: flex`).
- Input group: a click in a menu or another popup inside an addon (a model menu next to the field) no longer moves focus to the field; the menu returns focus to its trigger.
- `sheet-body` and `drawer-body` are in the catalog and the component files.
- `card-grid` block: the empty state uses `empty-icon` (it used `empty-media`, which has no style).
- Alert: an `alert-action` wider than the 72 px that shadcn keeps free (for example "View incident" at 390 px) no longer covers the title and the description; the alert reserves the width of the action. A short action keeps the shadcn layout.
- Section cards: with a description and a trend `badge` in `card-action`, the value takes the full width of the card under them, so a long number (`€38,550.00`) no longer breaks in the middle next to the badge.
- Item: a `cover` in `item-media` is 40 px wide (32 px in `sm`, 24 px in `xs`) and keeps its ratio, without its text; before, it had almost no width.
- Design lint: `button-size-mismatch` compares input groups, native selects, and the triggers of select and other popup roots with the other controls in their row, so a 32 px search next to 28 px `sm` select triggers is an error. Switches, checkboxes, and radios are not compared with buttons. `watchShift()` ignores controls inside `aria-hidden` (the hidden form input of a switch).
- `card-grid`: the cards of one row have one height, and each `card-footer` sits at the bottom of its card. Before, a card with a short title was shorter than its neighbor.
- `cover`: a title word breaks only when it alone is wider than the cover (`overflow-wrap: break-word`, `hyphens: auto`). Before, `overflow-wrap: anywhere` gave the cover a one-letter minimum width, so in a `min-content` or `auto` column every word broke.
- `item` below 40rem: when `item-actions` holds a text button (not an `icon` size button, a switch, or a badge), the actions go to their own line under the content, so the text keeps the row width.
- `data-table-toolbar` below 40rem: when the first control of the start group is an `input` or `input-group` (the search), the search takes the whole first row, and the filters and the end group share the next row, with the end group at the end. Before, the controls wrapped into uneven rows.
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
- Code block: the wrap button has the ghost `icon-xs` button look of the copy button (it had no button styles), and a pressed wrap button has the foreground color.
- Docs: a code block in a component preview keeps its inline padding and its start line; a docs rule for the View Code panel had removed both.
- Form: after a submit, leaving a control does not validate it; only a change does, as in React Hook Form. Before, a field that the app cleared after a valid send showed its error on blur, and the layout shift could move the next click target.
- Popup content (popover, hover card, tooltip, dropdown, context, and menubar menus, select, combobox, navigation menu) no longer shows in the page flow until the kit script runs, so the page does not move at load (#102).
- Dialog: a dialog taller than the window scrolls; before, its top and end were out of reach (#104).
- Card: a `card-action` with two or more children (a badge and a button) has an 8 px gap between them; before, they touched (#106).
- Card: in a header with a `card-action` and no `card-description`, the title is centered on the action line; before, a one-line title sat about 6 px above the center of a default button (#110).

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
