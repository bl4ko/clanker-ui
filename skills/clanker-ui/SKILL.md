---
name: clanker-ui
description: Build web pages with clanker-ui, the shadcn/ui components (Base UI, Nova style) for plain HTML, CSS, and JavaScript. No build step, no npm, no framework; works under a strict Content-Security-Policy with Trusted Types. Use when a project needs shadcn-style UI without React or a bundler, when it has files named clanker-ui*.css or clanker-ui*.js, when plain HTML (not JSX or TSX) uses shadcn data-slot parts, or when the user mentions clanker-ui.
license: MIT
metadata:
  version: "0.1.0"
  repository: https://github.com/bl4ko/clanker-ui
---

# clanker-ui

clanker-ui is shadcn/ui as static files. You write the HTML that shadcn renders (`data-slot` parts). The kit module adds the behavior, ARIA, and missing decorations. You never call an init function. In React projects, use shadcn/ui, not this kit.

References in this skill:

- [references/components.md](references/components.md): each component with its group, parts, attributes, state, events, keys, and a minimal example. Read the section of each component before you write its markup.
- [references/events.md](references/events.md): all events and their `detail` fields.
- [references/csp.md](references/csp.md): the CSP header, the meta tag for static hosts, and the code rules.

- [references/clanker-ui.json](references/clanker-ui.json): the same component data as JSON, for scripts ([schema](references/clanker-ui.schema.json)).

## 1. Get the files

Use one release version for all files. Get it in one of these ways:

- Zip: `gh release download v0.1.0 -R bl4ko/clanker-ui -p 'clanker-ui-*.zip' -p SHA256SUMS`, or `curl -fLO https://github.com/bl4ko/clanker-ui/releases/download/v0.1.0/clanker-ui-0.1.0.zip`. The zip has one folder: the readable kit files, `dist/` (the `.min` files), the license files, and this skill.
- Single files: each kit file is also a release asset, for example `https://github.com/bl4ko/clanker-ui/releases/download/v0.1.0/clanker-ui.min.css`.
- A local checkout of the repository: copy the files from its root and from `dist/`.

Check each downloaded file against `SHA256SUMS` (also a release asset): `grep ' clanker-ui-0.1.0.zip$' SHA256SUMS | shasum -a 256 -c` (Linux: `sha256sum -c`). Optional: `gh attestation verify <file> -R bl4ko/clanker-ui`.

Copy only the files that the page loads (step 2) into one directory of the static site. The examples below use `static/vendor/clanker-ui/`, with `static/` as the web root, so the URLs start with `/vendor/clanker-ui/`. Put the files from `dist/` in the same directory as the readable files, not in a subdirectory: the modules import each other by relative path. Do not change the files. Put your styles in your own `app.css` and your code in your own module, for example `app.js`.

## 2. Choose a file set

Make a list of the components on the page. Find the group of each component in [references/components.md](references/components.md) ("Groups" table, and "Group" and "Needs" in the component section). For existing HTML files, this command lists the groups with their "Needs" (use the path of `references/clanker-ui.json` in this skill):

```sh
grep -rhoE 'data-slot="[a-z0-9-]+"' --include='*.html' . | cut -d'"' -f2 | sort -u |
  jq -Rn --slurpfile c references/clanker-ui.json '[inputs] as $s | [$c[0].components[] | select(any(.parts[]; .slot as $p | $s | index($p))) | .group, .needs[]] | unique'
```

Add `overlays` for `toast()` and `chart` for `chart()`: they have no markup. A missing group fails without a message; if you are not sure, use the one-file set.

| Page uses | Load |
| --- | --- |
| 3 or more of the groups `forms`, `overlays`, `layout`, `chat` | One-file set: `clanker-ui.min.css`, module `clanker-ui.min.js` (it imports `clanker-ui-core.min.js`) |
| Fewer groups | Group set: `clanker-ui-core.min.css`, then the CSS of each group in the order `forms`, `overlays`, `layout`, `chat`, `chart`; one module per group with behavior (`clanker-ui-<group>.min.js`). Add the groups in "Needs". |
| Only core components | `clanker-ui-core.min.css` and module `clanker-ui-core.min.js` |
| Development, readable code | `clanker-ui.css` and module `clanker-ui.js` |

Rules:

- Each group module imports `clanker-ui-core.min.js` itself. Do not add a separate `<script>` for the core when you load a group module; the `modulepreload` link only saves a round trip.
- Never mix the readable files and the `.min` files on one page. Never load `clanker-ui.min.js` together with a group file. The kit throws "already defined".
- Charts: add the module `clanker-ui-chart.min.js` (readable: `clanker-ui-chart.js`). With group files, add `clanker-ui-chart.min.css` too.
- Optional files, after the kit CSS and before `app.css`: `clanker-ui-themes(.min).css` (color schemes), then `clanker-ui-a11y(.min).css` (stronger contrast and focus outline). Use the a11y file when the app must meet WCAG 2.2 AA.

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

- All scripts are external files from the same origin. No inline `<script>`, no inline `<style>`, no `style=""`, no `onclick=""`. See [references/csp.md](references/csp.md).
- A theme toggle or switch: add `<script src="clanker-ui-theme.js"></script>` (classic script, no `type`, no `defer`) after the stylesheets and before the modules. It stops a flash of the wrong theme.

## 4. Write the markup

1. Open the component section in [references/components.md](references/components.md). Start from its example.
2. Keep every `data-slot`. The root part of a component holds its other parts. Use the parts in the order of the example.
3. For `data-*` attributes, write only the ones in the "Write" column, the part attributes, the "other options", and the global attributes. Use only the listed values. No attribute means the default value. Native HTML and ARIA attributes (`id`, `type`, `name`, `value`, `disabled`, `aria-label`, ...) are always allowed. The value types: `boolean` = present or absent; `id` = no value inside the component root, or the id of a root elsewhere; `any` = see the full text link of the component.
4. Do not write the "State" attributes (`data-open`, `data-highlighted`, ...) or the "kit adds" parts. The kit sets and creates them. Use state attributes only as CSS selectors.
5. A part that is another component (shadcn `asChild`): keep that component's slot and add the part attribute. For example a dialog trigger is `<button type="button" data-slot="button" data-variant="outline" data-dialog-trigger>` inside the `dialog` root. A trigger outside the root names the root id: `data-dialog-trigger="settings"` on the trigger and `id="settings"` on the root.
6. Each component section links its full text ("Full text"). Read it for attribute meanings and edge cases.
7. Icons: `<svg data-lucide="search"></svg>`. The kit fills it from its icon set (no network).
8. Markup that you add later (with `h()` or by moving nodes) gets its behavior automatically.
9. Form controls: a `<label for>` names the `id` of a `select-trigger`, a combobox input, or a switch, checkbox, or radio item button. `data-name` on the select, combobox, switch, checkbox, or radio group root submits the value. `form.reset()` restores the initial values. The kit sets `type="button"` on its trigger buttons, so they do not submit the form.

## 5. Use JavaScript only where needed

Most components need no code. For the API, import from the files that the page loads. Group set:

```js
import { h, icon } from "/vendor/clanker-ui/clanker-ui-core.min.js"
import { toast, dialogOpen } from "/vendor/clanker-ui/clanker-ui-overlays.min.js"

document.querySelector("#save").addEventListener("click", () => toast.success("Saved", { description: "Your changes are saved." }))
document.addEventListener("select:change", event => console.log(event.detail.value))
```

Which file exports which names:

| Names | Readable set | `.min` set |
| --- | --- | --- |
| Core API (`h`, `svg`, `icon`, `define`, `emit`, `strings`, `theme`, `direction`, `isOpen`, ...) | `clanker-ui.js` | `clanker-ui.min.js` or `clanker-ui-core.min.js` |
| Component API (`toast`, `dialogOpen`, `calendarSetValue`, ...) | `clanker-ui.js` | `clanker-ui.min.js` or the group file |
| Charts (`chart`, `sparkline`, `statTile`) | `clanker-ui-chart.js` | `clanker-ui-chart.min.js` |

One-file `.min` set:

```js
import { h, icon, theme, isOpen, toast, dialogOpen } from "/vendor/clanker-ui/clanker-ui.min.js"
```

- `clanker-ui.min.js` exports the core API too. The group files do not export the core API again. Each component section in [references/components.md](references/components.md) names the file of its exports.
- Events: `<component>:<action>` on the component root; they bubble to `document`. Read `event.detail`. Call `event.preventDefault()` on a cancelable event (for example `dialog:close`) to stop the action. Full list: [references/events.md](references/events.md).
- Build DOM with `h(tag, attrs, ...children)`, `svg()`, and `icon()`. Never use `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, or `new Function`. Trusted Types blocks them.
- Toast and chart are created from JavaScript only. Their sections in [references/components.md](references/components.md) have the full call examples (`toast.success(title, options)`, `toast.promise(...)`, `chart(element, data, options)`). Toasts need no markup; an optional `<div data-slot="toast-portal" data-limit="3" data-timeout="5000"></div>` sets the limit and the default timeout.

## 6. Theme

- Light and dark follow the system. A toggle button: `<button type="button" data-slot="button" data-variant="ghost" data-size="icon-sm" data-theme-set="toggle" aria-label="Dark mode"><svg data-lucide="contrast"></svg></button>`. From code: `theme.set("light" | "dark" | "system")`.
- Brand colors: override the shadcn tokens in `app.css` (`--primary`, `--radius`, ...). Light values on `:root`, dark values on `[data-theme="dark"]` and in `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { ... } }`. Unlayered app CSS wins over the kit layers. Override tokens, not properties, so hover and dark states stay. With Tailwind or other layered CSS, or to override a kit `!important` rule, read [Override the kit](https://github.com/bl4ko/clanker-ui#override-the-kit).
- Color schemes: load `clanker-ui-themes.css` and set `data-scheme="<name>"` on `<html>`.

## 7. Accessibility rules

- Give each icon-only button an `aria-label`. Give each form control a `<label for>` or an `aria-label`.
- Give each dialog, alert dialog, sheet, and drawer a title part (`dialog-title`, ...). Add a description part when the dialog has one.
- Use `<button type="button">` for actions and `<a href>` for navigation. Keep the native elements of the examples (`<dialog>`, `<details>`, `<input>`).
- Do not add `role` or `aria-*` attributes that the kit sets. Do not remove focus rings. Do not put overlays inside a shadow root.
- Use `dir="rtl"` on `<html>` or a container for right-to-left text. The kit mirrors the keys and the layout.
- Give a chart a `label` option. Charts have a table view for screen readers.

## 8. Check the result

Serve the page with the CSP from [references/csp.md](references/csp.md) (it has a small Go server), then open it in a browser:

1. The console has 0 errors and 0 CSP or Trusted Types violations.
2. Each interactive component works with the mouse and with the keyboard (Tab, Enter, Space, Escape, arrows), as listed in its "Keyboard and focus" text.
3. Focus goes back to the trigger when a dialog or menu closes.

An automated check with Playwright for Python:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    errors = []
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:8300/", wait_until="load")
    page.get_by_role("button", name="Open").click()
    page.wait_for_selector('[data-slot="dialog-content"][data-open]')
    page.keyboard.press("Escape")
    page.wait_for_selector('[data-slot="dialog-content"]:not([open])', state="attached")
    assert not errors, errors
```

- Open popups have `data-open` (and `data-state="open"`); closed ones have `data-closed`. A `<dialog>` keeps `open` until its exit animation ends, so wait for the attribute, not for a fixed time.
- Toasts appear as `[data-slot="toast"]` inside `[data-slot="toast-viewport"]`.

If a component does not work: check the file set (step 2), the slot names (step 4), and that the module scripts load (no 404).

Docs: https://bl4ko.github.io/clanker-ui/. Full text reference: https://bl4ko.github.io/clanker-ui/llms-full.txt.
