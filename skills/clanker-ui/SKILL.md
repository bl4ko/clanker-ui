---
name: clanker-ui
description: Build web pages with clanker-ui, the shadcn/ui components (Base UI, Nova style) for plain HTML, CSS, and JavaScript. No build step, no npm, no framework; works under a strict Content-Security-Policy with Trusted Types. Use when a project needs shadcn-style UI without React or a bundler, when it has files named clanker-ui*.css or clanker-ui*.js, when plain HTML (not JSX or TSX) uses shadcn data-slot parts, or when the user mentions clanker-ui.
license: MIT
metadata:
  version: "0.2.1"
  repository: https://github.com/bl4ko/clanker-ui
---

# clanker-ui

**Version: the `version` in the front matter is the last release. Kit files that came with this skill can be newer (a copy from `main`); then this skill describes those files, so use them and ignore the number.**

clanker-ui is shadcn/ui as static files. You write the HTML that shadcn renders (`data-slot` parts). The kit module adds the behavior, ARIA, and missing decorations. You never call an init function. In React projects, use shadcn/ui, not this kit.

References in this skill:

- [references/components.md](references/components.md): the groups with their components, and the global attributes.
- `references/components/<name>.md`: one component: group, needs, parts, attributes, state, events, exports, and the full text with the examples and keys.
- [references/csp.md](references/csp.md): the CSP header, the meta tag for static hosts, a small Go server, and the code rules.
- [references/setup.md](references/setup.md): file checks, other ways to get the files, the group command for existing HTML, and which file exports which names.
- [references/design.md](references/design.md): design rules for layout, spacing, type, buttons, color, forms, states, and phones. [references/choosing.md](references/choosing.md): which component for which job.
- `references/blocks/<name>.html` (and `.js`): whole pages to start from.
- [references/ai-elements.md](references/ai-elements.md): chat and agent patterns (message, prompt, steps, sources, code output) and which one to use.
- [references/recipes.md](references/recipes.md): set values from code, forms in overlays, several rules per field, star rating, card grid, a shared header on static pages, breadcrumbs in the top header, category bar charts, uptime strips, long pages, a toast after a page change, a dropzone, lists in cards, phone tables, a dashboard in the top-header shell.
- [references/events.md](references/events.md), [references/theming.md](references/theming.md), [references/testing.md](references/testing.md) (Playwright check and design lint), [references/clanker-ui.json](references/clanker-ui.json) (all component data as JSON).

## 1. Get the files

When the kit files came with this skill, use those files and skip the download. Else use one release version for all files: `gh release download v0.2.1 -R bl4ko/clanker-ui -p 'clanker-ui-*.zip' -p SHA256SUMS`, or `curl -fLO https://github.com/bl4ko/clanker-ui/releases/download/v0.2.1/clanker-ui-0.2.1.zip`. The zip has the readable files, `dist/` (the `.min` files), and this skill.

Copy the files that the page loads (step 2) and the files they import into one directory, for example `static/vendor/clanker-ui/` with `static/` as the web root. Put the `dist/` files in that directory, not in a subdirectory. Do not change the files. Put your styles in `app.css` and your code in a module such as `app.js`.

## 2. Choose a file set

Find the group of each component in [references/components.md](references/components.md), and the "Needs" in its component file. Add `overlays` for `toast()` and `chart` for `chart()`.

| Page uses | Load |
| --- | --- |
| 3 or more of the groups `forms`, `overlays`, `layout`, `chat` | `clanker-ui.min.css` and module `clanker-ui.min.js`; copy `clanker-ui-core.min.js` too (the module imports it) |
| Fewer groups | `clanker-ui-core.min.css`, then the CSS of each group in the order `forms`, `overlays`, `layout`, `chat`, `chart`; one module `clanker-ui-<group>.min.js` per group |
| Only core components | `clanker-ui-core.min.css` and module `clanker-ui-core.min.js` |

- A group module imports `clanker-ui-core.min.js` itself. Never mix readable and `.min` files, and never load `clanker-ui.min.js` with a group file. A missing group fails without a message; if you are not sure, use the one-file set.
- Charts: module `clanker-ui-chart.min.js`. `clanker-ui.min.css` has the chart CSS; with group files also load `clanker-ui-chart.min.css`.
- Syntax colors in a code block: module `clanker-ui-code.min.js` and `data-language` on `code-block-content`.
- Style: Nova is the default. For the shadcn Rhea style, load `clanker-ui-rhea.min.css` (or `clanker-ui-rhea-<group>.min.css`) instead of the Nova CSS, never both. Markup and JS do not change.
- Every kit file has a `.min` version: the theme script is `clanker-ui-theme.min.js` in the `.min` set and `clanker-ui-theme.js` in the readable set.
- Always load `clanker-ui-a11y.min.css` after the kit CSS (every block does): the kit keeps the shadcn values, and status badges, the avatar fallback, muted text, and input borders are below WCAG 2.2 AA without it.

## 3. Write the head

Every page and every block has this head, in this order:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; require-trusted-types-for 'script'">
  <meta name="referrer" content="no-referrer">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>Invoices - Tally</title>
  <link rel="icon" href="data:,">
  <link rel="stylesheet" href="/vendor/clanker-ui/clanker-ui.min.css">
  <link rel="stylesheet" href="/vendor/clanker-ui/clanker-ui-a11y.min.css">
  <link rel="stylesheet" href="/app.css">
  <link rel="modulepreload" href="/vendor/clanker-ui/clanker-ui-core.min.js">
  <script src="/vendor/clanker-ui/clanker-ui-theme.min.js"></script>
  <script type="module" src="/vendor/clanker-ui/clanker-ui.min.js"></script>
  <script type="module" src="/app.js"></script>
</head>
```

- `<meta charset>` is first (it must be in the first 1024 bytes). The CSP meta tag comes next, before every `<link>` and `<script>`: a meta policy does not apply to elements before it. A server that sends the CSP header ([references/csp.md](references/csp.md)) can leave the meta tag out.
- Group files: replace `clanker-ui.min.css` with the group CSS files and `clanker-ui.min.js` with one module per group (step 2). Color schemes: `clanker-ui-themes.min.css` between the kit CSS and the a11y file. A real icon: `<link rel="icon" href="/favicon.svg">`.
- All scripts are external files from the same origin. No inline `<script>` or `<style>`, no `style=""`, no `onclick=""`.
- Theme toggle and theme switch (not the switch component): [references/theming.md](references/theming.md).

## 4. Build a page

1. Start from the closest block in `references/blocks/`: copy `<name>.html` and `<name>.js`, keep the shell, the `page-header`, and the order of the sections, and replace the sample content. One shell per app: the sidebar of `dashboard` or the top header of `data-table`.

   | Block | For |
   | --- | --- |
   | `dashboard` | A sidebar app: key numbers, a chart, a table |
   | `data-table` | A top-header app: a list with filters, sorting, and paging |
   | `settings` | Settings in sections with their own save actions |
   | `form` | Create or edit one record, with a live summary and Delete in edit mode |
   | `detail` | One record: a large title with a meta row, facts, and activity |
   | `login`, `login-split` | Sign in: centered card, or a form next to a brand panel |
   | `card-grid` | Records with a preview (books, products): filters, sort, a grid of cards |
   | `overlay-form` | A record page with a cover: a form in a dialog and a long form in a sheet with a scrolling body |
   | `states` | Empty, loading, and error states (a catalog: copy single cards) |

2. Follow [references/design.md](references/design.md) and [references/choosing.md](references/choosing.md). The page parts (`page`, `site-header`, `section-cards`, `stat-grid`, `data-table`) do the layout: `app.css` holds token overrides and real app parts only.
3. Run `clankerDesignLint()` from `references/design-lint.js` in the test, not in the page, at 1280 and 390 px, in light and dark ([references/testing.md](references/testing.md)); fix every error and look at the screenshots.

## 5. Write the markup

1. Open `references/components/<name>.md` for each component. Start from its example.
2. Keep every `data-slot` and the order of the parts. The root part holds the other parts.
3. Write only the `data-*` attributes in the "Write" column, the part attributes, the "other options", and the global attributes, with the listed values. No attribute means the default. Native HTML and ARIA attributes are always allowed. `boolean` = present or absent; `id` = no value inside the root, or the id of a root elsewhere; `any` = see the full text.
4. Never write the "State" attributes or the "kit adds" parts. Use state attributes only as CSS selectors.
5. A part that is another component (shadcn `asChild`): keep its slot and add the part attribute, for example `<button type="button" data-slot="button" data-variant="outline" data-dialog-trigger>` inside the `dialog` root. Outside the root: `data-dialog-trigger="settings"` and `id="settings"` on the root.
6. Icons: `<svg data-lucide="search"></svg>`; all names and aliases are in [references/icons.md](references/icons.md). An unknown name gives an empty icon and a `console.warn`; add icons with `registerIcons()`. Markup added later gets its behavior automatically.
7. Form controls: a `<label for>` names the `id` of a `select-trigger`, a combobox input, or a switch, checkbox, or radio item button. `data-name` on the select, combobox, switch, checkbox, or radio group root submits the value. `form.reset()` restores the initial values. Set values from code: [references/recipes.md](references/recipes.md). Kit trigger buttons do not submit the form. Without `event.preventDefault()` in `form:submit` the browser submits the form; call it on static pages and when you send with `fetch`.

## 6. JavaScript

Most components need no code. Import from the files that the page loads (group files: core API from `clanker-ui-core.min.js`, component API from its group file):

```js
import { h, icon, theme, toast } from "/vendor/clanker-ui/clanker-ui.min.js"
```

- Events: `<component>:<action>` on the root; they bubble to `document`. Read `event.detail`; `event.preventDefault()` stops a cancelable action.
- Build DOM with `h(tag, attrs, ...children)`, `svg()`, and `icon()`. Never use `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, or `new Function`.
- Toast and chart have no markup; see their component files.

## 7. Accessibility

- Give each icon-only button an `aria-label` and each form control a label.
- Give each dialog, alert dialog, sheet, and drawer a title part.
- `<button type="button">` for actions, `<a href>` for navigation. Keep the native elements of the examples. Do not add `role` or `aria-*` that the kit sets, and do not remove focus rings.
- `dir="rtl"` on `<html>` or a container mirrors keys and layout. Give a chart a `label` option.

## 8. Check the result

Serve the page with the CSP header from [references/csp.md](references/csp.md), or with the meta tag on a static server. Add `<link rel="icon" href="/favicon.svg">` (or `data:,`), so the browser does not log a favicon 404. In a browser: 0 console errors and 0 CSP violations; each component works with the mouse and the keys in its full text; focus goes back to the trigger when a dialog or menu closes. If a component does not work, check the file set, the slot names, and the module loads (no 404).

Docs: https://bl4ko.github.io/clanker-ui/. Full text: https://bl4ko.github.io/clanker-ui/llms-full.txt.
