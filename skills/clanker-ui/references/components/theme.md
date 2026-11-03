# Theme Switch (`theme`)

Group `core`. Needs none. CSS and JS.

Other parts: `theme-switch`.

Events: `theme:change` `{ mode, resolved, scheme }`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui-core.min.js`):

- `theme.get(), theme.set("light"|"dark"|"system"), theme.resolved(), theme.toggle(), theme.scheme(), theme.setScheme(value), theme.schemes`: The mode is stored in `localStorage["clanker-ui-theme"]` and applied as `data-theme` on `<html>`. `resolved()` returns the mode that shows (`dark` for a dark-only scheme). `toggle()` does what the toggle button does. `scheme()` returns `data-scheme` (`""` when there is none). `setScheme` takes names separated by spaces (`a-z`, `0-9`, `-`, at most 200 characters, else a `TypeError`) and stores them in `localStorage["clanker-ui-scheme"]`; `""` removes the scheme. `schemes` is the frozen list `{ value, label, group }` (`group`: `shadcn`, `editor`, or `accent`). See [Color schemes](https://github.com/bl4ko/clanker-ui#color-schemes).

## Full text

### Theme toggle and switch

```html
<button type="button" data-slot="button" data-variant="ghost" data-size="icon-sm" data-theme-set="toggle" aria-label="Dark mode" aria-keyshortcuts="D"><svg data-lucide="contrast"></svg></button>
<div data-slot="theme-switch" role="group" aria-label="Theme">
  <button type="button" data-theme-set="light" aria-label="Light theme"><svg data-lucide="sun"></svg></button>
  <button type="button" data-theme-set="dark" aria-label="Dark theme"><svg data-lucide="moon"></svg></button>
  <button type="button" data-theme-set="system" aria-label="System theme"><svg data-lucide="monitor"></svg></button>
</div>
```

- The toggle is the control of the shadcn site: one button that changes between light and dark. The first press from `system` stores the opposite of the mode that shows. Then each press changes the stored mode. There is no way back to `system` in the toggle; use `theme.set("system")` or the switch.
- The kit sets `aria-pressed="true"` on the toggle while dark shows. Give it a label that matches, for example `Dark mode`. The `contrast` icon is 18 px and its right half is filled. Older markup with a `sun` and a `moon` icon still shows one of the two.
- `aria-keyshortcuts="D"` on a toggle turns on the shadcn `D` key: `D` without Ctrl, Meta, or Alt toggles the theme. The key does nothing in text fields, selects, editable content, menus, lists, grids, and trees, or when a handler already called `preventDefault()`. Without the attribute, the kit adds no key.
- The switch sets `light`, `dark`, or `system`.
- A theme or scheme change sets `data-theme-switching` on `<html>` until the next frame. It stops all CSS transitions, so colors change at once (like next-themes `disableTransitionOnChange`).
- In `system` mode the kit pins the shown mode with `data-system-theme="light|dark"` on `<html>` (the CSS sets `color-scheme` from it). When the system theme changes, the kit changes the attribute inside the same no-transition switch, so a system change also starts no transitions. Without JavaScript, `color-scheme: light dark` follows the system.
- `clanker-ui-theme.js` sets `<meta name="theme-color">` (without `media`) to `--background` before the first paint. After each change, the module copies the `<body>` background color to it.

An app with a theme toggle or switch also loads `clanker-ui-theme.js` in `<head>` after the stylesheets (see [Use in a project](https://github.com/bl4ko/clanker-ui#use-in-a-project)).
