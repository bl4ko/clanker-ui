# Design rules

Rules for pages that look like an official shadcn block. Each rule names the kit part, attribute, or token that does the work, and the design lint rule (`clankerDesignLint()`, see [testing.md](testing.md)) that finds a break. Start every page from the closest block in [blocks/](blocks/); the blocks follow all of these rules. Take the shell from `dashboard` (sidebar) or `data-table` (top header) and keep it on every page; take the page content from any block. `states` is a catalog of patterns, not a page. Component choice: [choosing.md](choosing.md).

## 1. Page structure

- Pick one shell per app and keep it on every page:
  - Sidebar app, 6 or more sections or tools: `sidebar-wrapper` > `sidebar` (`data-variant="inset"`, `data-collapsible="offcanvas"`) + `sidebar-inset` > `site-header` + `page`. Block: `dashboard`, `form`, `detail`.
  - Top header, up to 5 sections: `site-header data-size="lg"` with `brand`, `site-header-nav`, and `site-header-actions`, then `<main data-slot="page">`. In a sidebar app the same content goes in `sidebar-inset` > `site-header` + `<div data-slot="page">`. Below 48rem the nav goes into a `dropdown-menu` behind a `menu` icon button. Block: `data-table`, `settings`, `states`.
  - One task without navigation (sign in, invite, error page): `<main data-slot="page" data-layout="center">`. Block: `login`.
- One `page` per view. It sets the gutters (16 px, 24 px from 64rem) and the gaps between its children (16 px, 24 px from 48rem). Do not add margins or padding around kit parts.
- Width: tables, dashboards, and lists fill the page (no `data-size`). Forms: `data-size="sm"` (42rem). Detail and settings: full width with `page-body`, or `data-size="md"`. Never a fixed pixel width.
- The first child of `page` is `page-header`: one `<h1 data-slot="page-title">` (the noun of the view: "Invoices", "New project"), one `page-description` sentence, and the view actions in `page-actions` at the end. In a sidebar app the `site-header` holds the breadcrumb, not the title. Exception: a dashboard home with no `page-header` (as in shadcn dashboard-01); then `site-header-title` is the `h1` and names the active nav item. Lint: `heading-order`.
- Order of a data page: header, key numbers (`section-cards`, `stat-grid`, or `statTile()` tiles on plain `div`s in a `section-cards` grid; in a `card` a tile has no frame; `notation: "standard"` shows full values), the main chart, the main table or list. The most important content is first on a phone too.
- Two columns only with `page-body`: a `page-aside` first is the 12rem section nav (settings), a `page-aside` last is the 20rem side column (detail). Below 64rem they stack. No app grids.
- Edges align: every card, table, and header starts at the page gutter. No card in a card; a table in a card has no `data-table` border. Lint: `misaligned`.
- A region with little content does not get a large box: do not stretch cards to fill height. Lint: `empty-region`.
- In a top-header app a detail page puts a `breadcrumb` or a back link first in `page`, above the `page-header` ([recipes.md](recipes.md)).
- Long pages condense: a summary row per group, and only groups with a problem open (`collapsible`, `accordion`).

## Make it specific

- One identity move per app, while the kit parts stay plain: a brand panel on the sign-in page (block `login-split`), a hero or feature card first on the main page, believable placeholder art built from tokens (`cover`; never flat gray boxes).
- Fake data looks real in volume and mix: 8 or more rows, several reviews or updates, and mixed states (empty, overdue, failed).
- Each page does its whole job, not only the minimum fields: a form has a summary or policy card in a `page-aside`, an edit page has its destructive action, a detail page has side panels and related records.

## 2. Spacing and size

- Spacing comes from the parts: `page` 16/24 px, `card` 16 px, `field-group` 20 px, `field` 8 px, toolbars and button rows 8 px. If an app part needs space, use `calc(var(--spacing) * N)` with N = 1, 2, 3, 4, 6, 8, or 12, and N = 0.5 for the gap between dense marks (uptime bars). No other px or rem values.
- Kit parts bring their corners; do not change them. App parts take a kit radius: `--radius-sm` for marks and swatches, `--radius-md` for small tiles, `--radius-lg` (`--radius`) for art and large tiles, `50%` for dots. Shadows: only the kit ones. Borders: `--border`, 1 px.
- All controls in one row have one height. Default controls are 32 px (`h-8`); `data-size="sm"` is 28 px. Inputs, input groups, and select triggers are 32 px, so a button next to one is default size (or `icon`), except in `data-table-toolbar`, where `sm` buttons are 32 px high like shadcn.

## 3. Typography

- Sizes: `page-title` 24 px/600; `card-title` and `site-header-title` 16 px/500 (20 px card title in `data-layout="center"`); body text and `page-description` 16 px; controls, tables, and card text 14 px; descriptions and help 14 px muted; detail lines and badges 12 px; KPI values in `section-cards` 24 to 30 px/600 and in `stat-grid` 24 px/600. Only app art and one display number (a cover title, a large score) may use 1.25rem, 1.5rem, or 1.875rem; the kit has no text tokens above `--text-base`. Do not add other sizes.
- Weights 400, 500, and 600 only. Muted text (`--muted-foreground`) is for secondary text, never for values or labels of controls.
- Use one case style in the app: sentence case for titles, buttons, and labels.
- Numbers: tabular figures, end-aligned in tables (`data-align="end"`), units after the number, formatted with `Intl.NumberFormat` and `Intl.DateTimeFormat` in the page language.
- Long text: one line with an ellipsis (`data-table-text`, `text-stack`, `site-header-title`) and the full text in a `title` attribute or tooltip. Values never get cut: `section-cards` and `stat-grid` wrap them. Lint: `text-clipped`.

## 4. Buttons

- One primary button (default variant) per region: the page header, a toolbar, a card footer, or a dialog footer. On a page, at most one primary is visible above the fold. Other actions are `outline`. Icon and menu triggers in headers and table rows are `ghost`; in a row of outline buttons they are `outline` too. `link` is for navigation inside text; a secondary link next to a label ("Forgot your password?") is muted (`--muted-foreground`, underline on hover). Lint: `multiple-primary`.
- One size per row or group: all buttons in a row have the same `data-size`, and icon buttons use the matching icon size (`sm` with `icon-sm`, default with `icon`). Lint: `button-size-mismatch`.
- `destructive` only for actions that destroy data (delete, revoke, cancel a subscription). Confirm them with `alert-dialog` (action `data-variant="destructive"`) or offer Undo in a toast.
- Order: dialog and card footers put Cancel (`outline`) first and the primary last, at the end. A page form puts the primary first at the start and Cancel after it, as in the shadcn field demo.
- Labels are a verb and an object ("Create project", "Save changes"). Never "OK" or "Submit". An icon-only button has an `aria-label`; add a `tooltip` when the icon is not obvious. Lint: `missing-label`.
- While an action runs: `disabled` and a `spinner` before the label; the button keeps its width.

## 5. Color

- Surfaces are `--background`, `--card`, and `--muted` only. Do not color whole regions.
- `--primary` is for the primary button, the selected item, focus, and links. Not for icons, headings, or decoration.
- Status uses the `success`, `info`, and `warning` variants and `destructive` of `badge` and `alert`, always with an icon and a word ("Done", "Failed"). In tables use the `badge` with its icon; only a dense table of 6 or more columns may use an icon and a word in `data-table-text`. Status marks without words (bars, dots, meters, strips) use `--success-fill`, `--warning-fill`, `--error-fill`, and `--info-fill`, the same hue in light and dark; `--*-text` tokens are for text only. Keep badges out of headings. Color alone never carries meaning. Status colors are not chart series colors.
- No hex, rgb, or named colors in app CSS: override the tokens in `app.css` ([theming.md](theming.md)). Lint: `non-token-color`.
- Contrast: text 4.5:1, icons and control borders 3:1. Load `clanker-ui-a11y.css` in every app: the kit keeps the shadcn values, which are below AA for status badges, the avatar fallback, muted text, and input borders. Lint: `low-contrast`.
- Charts (the dataviz method):
  - Series take `--chart-1`, `--chart-2`, ... in a fixed order, and a series keeps its color on every chart and page. Never color by value or cycle the colors.
  - "Other" is `--chart-other`. Good and bad values are `--chart-good` and `--chart-bad`; a single series is `--chart-1`.
  - At most 5 series in a line or area chart, 8 in a bar chart. More: fold the rest into "Other" or use small multiples.
  - One value axis, a quiet grid (`--chart-grid`), a legend from 2 series, the table view on. The `chart()` defaults do this.
  - The chart height fits the data: a category bar chart is one series in one color, sorted descending, with `labels: true` and a height from the bar count ([recipes.md](recipes.md)). No empty band under the plot.
  - The kit default and the editor schemes in `clanker-ui-themes.css` (for example `tokyonight-storm`) have validated colored chart tokens: 3:1 against the card, adjacent colors apart for color-blind and normal vision. The shadcn base schemes (`neutral`, `zinc`, ...) keep the shadcn gray ramp, so they give gray charts. A brand palette must pass the same validator before it replaces them.
  - Set the chart `locale` and, for times, `timeZone`. Many small marks with their own readout (uptime bars): one shared popup placed with `position()`, not one tooltip per mark, and one Tab stop with arrow keys ([recipes.md](recipes.md)).

## 6. Forms

- A label above every control (`field-label`), help below it (`field-description`), and the error below the help (`field-error`, the kit adds it). Placeholders are examples, not labels.
- Put `<form data-slot="form">` around a form; around the `card` when the form is a card. One form per card, its submit button in the `card-footer`. In a `dialog` or `sheet` the form is the direct child of the content, around header, fields, and footer (block `overlay-form`).
- Validation follows shadcn with React Hook Form: the kit shows an error after the user changed a field and left it, and on submit; after that, errors update as the user types. Submit with errors focuses the first invalid field. Write each message with `data-error-<flag>`: what is wrong and how to fix it ("Use 2 to 5 capital letters.").
- The layout never moves sideways: put fields side by side only in `field-group data-columns="2|3"` (they align at the top, so an error under one field does not move the other). An error pushes the content below it down; that is expected.
- Inputs fill their column; selects and date pickers in a vertical `field` are full width. Group related fields in `field-set` with a `field-legend` and a `field-separator` between sets.
- Switches apply at once and save without a button. In a form with a submit button, checkboxes, radios, and inputs wait for submit; a card without a submit button applies every change at once and says so in its description. Choice cards (a `field-label` that wraps a `field`) for 2 to 4 options that need a description.
- Keep the submit button enabled and show the errors on submit. Mark optional fields in the help text ("Optional."), not required ones. A required date: `data-required` on the `date-picker` root. A rating: star radios, the chosen stars filled with `--primary` ([recipes.md](recipes.md)).

## 7. Tables and lists

- A filter bar over one list: `tabs` with one `tabs-content` without `data-value` (a shared panel), or `toggle-group data-type="single" data-required` (one value always selected).
- Every list and table has four states: loading (`skeleton` with the same shape, `aria-busy`), empty (`empty` with one action), no results (`empty` with "Clear filters"), and error (`alert` `destructive` with "Try again"). Block: `states`.
- Use the `data-table` frame: `data-table-toolbar` (filters at the start, actions at the end), the bordered `table-container`, and `data-table-pagination` (not `pagination`, which is for pages of content with their own URLs). Block: `data-table`.
- Columns: identity first, then status (`badge` with icon), then numbers (`data-align="end"`), then the row action (`ellipsis` ghost `icon-sm` with a `dropdown-menu`, destructive item last after a separator).
- At 390 px keep identity, status, the main value (amount, balance), and the action; hide only secondary columns with `data-show-from` (phone-only parts: `data-hide-from`; `sm` 40rem, `md` 48rem, `lg` 64rem, `xl` 80rem of the viewport, so in a sidebar app the content is 16rem narrower), or show the rows as an `item-group` list below 40rem. A table scrolls inside `table-container`, never the page, and status and amount never scroll out of view. Lint: `horizontal-scroll`.
- Selection: a checkbox column first and the count in `data-table-selection`.
- People, events, and settings rows are lists, not tables: `item-group` with `item`. With `item-separator` between rows, set the group gap to 0.

## 8. Feedback

| Situation | Use |
| --- | --- |
| Result of an action the user just did (saved, sent, deleted) | `toast`; Undo for deletes |
| A problem that stays until it is fixed (cannot load, no permission, plan limit) | `alert` in the page or card |
| One invalid field | `field-error` under the field |
| Confirm a destructive or expensive action | `alert-dialog` |
| No data yet, or no match | `empty` |
| Work in progress | `skeleton` for content, `spinner` in the button that started it |

- One toast per action. Error toasts say what to do next. Never show an error only in a toast when the user must act: use an `alert`.

## 9. Density and phones

- Use the kit sizes. For a dense tool, set `data-size="sm"` on whole groups (toolbar, table controls), never on single controls in a row.
- At 390 px: one column, no horizontal page scroll, page actions wrap under the title (`page-header` does it), the sidebar becomes a sheet, the top nav becomes a menu with every primary link. Tabs that do not fit at 390 px get a `select` below 40rem.
- Touch targets: every target is at least 24 px (WCAG 2.5.8); on phones make the main targets 44 px by using full rows (`item`, choice cards, sidebar and menu items) and keep 8 px between small icon buttons. Lint: `small-target`.

## 10. Dark mode and theme control

- Check every page in light and dark. Use tokens only, so both modes come from the same CSS.
- Theme control as on shadcn sites: one ghost `icon-sm` toggle (`data-theme-set="toggle"`, `contrast` icon) in `site-header-actions`, before the user menu. An app with settings also offers light, dark, and system with `theme-switch` in Settings, Appearance. Never two theme controls in one header, and never in page content except Settings, Appearance. Load `clanker-ui-theme.js` ([theming.md](theming.md)).
- Color schemes (`data-scheme`) are an app choice for the whole app, not per page.

## 11. Icons

- Lucide icons through `data-lucide`, 16 px. One icon in a button, before the label (chevrons, arrows, and the X of Reset after it). One icon per meaning: row actions are `ellipsis`. The same icon means the same thing on every page.
- Icons are decoration unless they are the only content: then the control has an `aria-label`.

## 12. Motion

- Only the kit motion: popups, sheets, drawers, accordion, toasts, chart entrance. No app animations on page load. The kit follows `prefers-reduced-motion`.
- Nothing moves after a click except what the click opened. Lint: `layout-shift` (`clankerDesignLint.watchShift()`).

## Check

1. Run `clankerDesignLint()` from `design-lint.js` at 1280 and 390 px, in light and dark: 0 errors; look at each warning. Load it from the test as [testing.md](testing.md) shows, never with a `<script>` in the page (the CSP blocks it).
2. Take the four screenshots and compare them with the block you started from: same gutters, same header, same button sizes, no empty boxes, no cut text.
