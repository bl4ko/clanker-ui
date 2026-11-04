---
name: clanker-ui
description: Build web pages with clanker-ui, the shadcn/ui components (Base UI, Nova style) for plain HTML, CSS, and JavaScript. No build step, no npm, no framework; works under a strict Content-Security-Policy with Trusted Types. Use when a project needs shadcn-style UI without React or a bundler, when it has files named clanker-ui*.css or clanker-ui*.js, when plain HTML (not JSX or TSX) uses shadcn data-slot parts, or when the user mentions clanker-ui.
license: MIT
metadata:
  version: "0.2.1"
  repository: https://github.com/bl4ko/clanker-ui
---

# clanker-ui

clanker-ui is shadcn/ui as static files. You write the HTML that shadcn renders (`data-slot` parts). The kit module adds the behavior, ARIA, and missing decorations. You never call an init function. In React projects, use shadcn/ui, not this kit.

References in this skill:

- [references/components.md](references/components.md): the groups with their components, and the global attributes.
- `references/components/<name>.md`: one component: group, needs, parts, attributes, state, events, exports, and the full text with the examples and keys.
- [references/csp.md](references/csp.md): the CSP header, the meta tag for static hosts, a small Go server, and the code rules.
- [references/setup.md](references/setup.md): file checks, other ways to get the files, the group command for existing HTML, and which file exports which names.
- [references/events.md](references/events.md), [references/theming.md](references/theming.md), [references/testing.md](references/testing.md) (Playwright check), [references/clanker-ui.json](references/clanker-ui.json) (all component data as JSON).

## 1. Get the files

Use one release version for all files: `gh release download v0.2.1 -R bl4ko/clanker-ui -p 'clanker-ui-*.zip' -p SHA256SUMS`, or `curl -fLO https://github.com/bl4ko/clanker-ui/releases/download/v0.2.1/clanker-ui-0.2.1.zip`. The zip has the readable files, `dist/` (the `.min` files), and this skill.

Copy only the files that the page loads (step 2) into one directory, for example `static/vendor/clanker-ui/` with `static/` as the web root. Put the `dist/` files in that directory, not in a subdirectory. Do not change the files. Put your styles in `app.css` and your code in a module such as `app.js`.

## 2. Choose a file set

Find the group of each component in [references/components.md](references/components.md), and the "Needs" in its component file. Add `overlays` for `toast()` and `chart` for `chart()`.

| Page uses | Load |
| --- | --- |
| 3 or more of the groups `forms`, `overlays`, `layout`, `chat` | `clanker-ui.min.css` and module `clanker-ui.min.js` |
| Fewer groups | `clanker-ui-core.min.css`, then the CSS of each group in the order `forms`, `overlays`, `layout`, `chat`, `chart`; one module `clanker-ui-<group>.min.js` per group |
| Only core components | `clanker-ui-core.min.css` and module `clanker-ui-core.min.js` |

- A group module imports `clanker-ui-core.min.js` itself. Never mix readable and `.min` files, and never load `clanker-ui.min.js` with a group file. A missing group fails without a message; if you are not sure, use the one-file set.
- Charts: module `clanker-ui-chart.min.js`; with group files also `clanker-ui-chart.min.css`.
- Optional, after the kit CSS: `clanker-ui-themes.min.css` (color schemes), then `clanker-ui-a11y.min.css` (WCAG 2.2 AA contrast and focus).

## 3. Write the head

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <link rel="stylesheet" href="/vendor/clanker-ui/clanker-ui-core.min.css">
  <link rel="stylesheet" href="/vendor/clanker-ui/clanker-ui-forms.min.css">
  <link rel="stylesheet" href="/vendor/clanker-ui/clanker-ui-overlays.min.css">
  <link rel="stylesheet" href="/app.css">
  <link rel="modulepreload" href="/vendor/clanker-ui/clanker-ui-core.min.js">
  <script type="module" src="/vendor/clanker-ui/clanker-ui-forms.min.js"></script>
  <script type="module" src="/vendor/clanker-ui/clanker-ui-overlays.min.js"></script>
  <script type="module" src="/app.js"></script>
</head>
```

- All scripts are external files from the same origin. No inline `<script>` or `<style>`, no `style=""`, no `onclick=""`.
- A theme toggle or theme switch (not the switch component): see [references/theming.md](references/theming.md).

## 4. Write the markup

1. Open `references/components/<name>.md` for each component. Start from its example.
2. Keep every `data-slot` and the order of the parts. The root part holds the other parts.
3. Write only the `data-*` attributes in the "Write" column, the part attributes, the "other options", and the global attributes, with the listed values. No attribute means the default. Native HTML and ARIA attributes are always allowed. `boolean` = present or absent; `id` = no value inside the root, or the id of a root elsewhere; `any` = see the full text.
4. Never write the "State" attributes or the "kit adds" parts. Use state attributes only as CSS selectors.
5. A part that is another component (shadcn `asChild`): keep its slot and add the part attribute, for example `<button type="button" data-slot="button" data-variant="outline" data-dialog-trigger>` inside the `dialog` root. Outside the root: `data-dialog-trigger="settings"` and `id="settings"` on the root.
6. Icons: `<svg data-lucide="search"></svg>`. Markup added later gets its behavior automatically.
7. Form controls: a `<label for>` names the `id` of a `select-trigger`, a combobox input, or a switch, checkbox, or radio item button. `data-name` on the select, combobox, switch, checkbox, or radio group root submits the value. `form.reset()` restores the initial values. Kit trigger buttons do not submit the form.

## 5. JavaScript

Most components need no code. Import from the files that the page loads (group files: core API from `clanker-ui-core.min.js`, component API from its group file):

```js
import { h, icon, theme, toast } from "/vendor/clanker-ui/clanker-ui.min.js"
```

- Events: `<component>:<action>` on the root; they bubble to `document`. Read `event.detail`; `event.preventDefault()` stops a cancelable action.
- Build DOM with `h(tag, attrs, ...children)`, `svg()`, and `icon()`. Never use `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, or `new Function`.
- Toast and chart have no markup; see their component files.

## 6. Accessibility

- Give each icon-only button an `aria-label` and each form control a label.
- Give each dialog, alert dialog, sheet, and drawer a title part.
- `<button type="button">` for actions, `<a href>` for navigation. Keep the native elements of the examples. Do not add `role` or `aria-*` that the kit sets, and do not remove focus rings.
- `dir="rtl"` on `<html>` or a container mirrors keys and layout. Give a chart a `label` option.

## 7. Check the result

Serve the page with the CSP header from [references/csp.md](references/csp.md). In a browser: 0 console errors and 0 CSP violations; each component works with the mouse and the keys in its full text; focus goes back to the trigger when a dialog or menu closes. If a component does not work, check the file set, the slot names, and the module loads (no 404).

Docs: https://bl4ko.github.io/clanker-ui/. Full text: https://bl4ko.github.io/clanker-ui/llms-full.txt.
