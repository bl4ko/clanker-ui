# clanker-ui

clanker-ui is a dependency-free port of [shadcn/ui](https://ui.shadcn.com) (the base-nova style on [Base UI](https://base-ui.com)) for plain HTML, CSS, and JavaScript. It has no build step, no npm, no framework, and needs no CDN. You write the shadcn markup with `data-slot` attributes, and the kit adds the behavior. Everything runs under a strict Content Security Policy with Trusted Types.

- Docs: <https://bl4ko.github.io/clanker-ui/>
- Demo of all components: <https://bl4ko.github.io/clanker-ui/demo/>
- Releases: <https://github.com/bl4ko/clanker-ui/releases>

## Use with AI agents

Add the [agent skill](skills/clanker-ui/SKILL.md) to a project with the [skills CLI](https://github.com/vercel-labs/skills). It finds the agents of the project and writes the skill to the skills folder of each one:

```sh
pnpm dlx skills add bl4ko/clanker-ui
```

- Pin the skill to a release: `pnpm dlx skills add https://github.com/bl4ko/clanker-ui/tree/v0.2.1/skills/clanker-ui`.
- Without the CLI: copy `skills/clanker-ui/` from the release zip to `.agents/skills/` (Codex, Cursor, GitHub Copilot, Gemini CLI, Cline, OpenCode), `.claude/skills/` (Claude Code), or `.windsurf/skills/` (Windsurf). It is a portable [Agent Skill](https://agentskills.io) and works without network access.
- Chat tools without skills: give the agent [`llms.txt`](https://bl4ko.github.io/clanker-ui/llms.txt). [`llms-full.txt`](https://bl4ko.github.io/clanker-ui/llms-full.txt) is the full text in one file.
- Catalog: [`clanker-ui.json`](skills/clanker-ui/references/clanker-ui.json) lists each component with its group file, parts, attributes and allowed values, state attributes, events, keys, and a minimal example ([schema](skills/clanker-ui/references/clanker-ui.schema.json)). `go run ./tools/gen catalog` makes it; the skill has a Markdown file for each component.
- Contributors: [`AGENTS.md`](AGENTS.md) has the build, test, and code rules.

## Quick start

1. Download the latest release, check it, and copy the two kit files into a new `site` folder:

   ```sh
   gh release download -R bl4ko/clanker-ui -p 'clanker-ui-*.zip' -p SHA256SUMS
   shasum -a 256 -c --ignore-missing SHA256SUMS
   unzip -q clanker-ui-*.zip
   mkdir site && cp clanker-ui-*/clanker-ui.css clanker-ui-*/clanker-ui.js site/
   ```

   On Linux, use `sha256sum` in place of `shasum -a 256`. Without `gh`, download the kit files one by one: each is a release asset (`https://github.com/bl4ko/clanker-ui/releases/latest/download/clanker-ui.css`). You can also copy the files from this repository.

2. Save this page as `site/index.html`:

   ```html
   <!doctype html>
   <html lang="en">
   <head>
     <meta charset="utf-8">
     <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; require-trusted-types-for 'script'">
     <meta name="viewport" content="width=device-width, initial-scale=1">
     <meta name="color-scheme" content="light dark">
     <title>clanker-ui</title>
     <link rel="stylesheet" href="clanker-ui.css">
     <script type="module" src="clanker-ui.js"></script>
   </head>
   <body>
     <div data-slot="dialog">
       <button type="button" data-slot="button" data-variant="outline" data-dialog-trigger>Open</button>
       <dialog data-slot="dialog-content">
         <div data-slot="dialog-header">
           <h2 data-slot="dialog-title">Edit profile</h2>
           <p data-slot="dialog-description">Make changes here.</p>
         </div>
       </dialog>
     </div>
   </body>
   </html>
   ```

   The kit finds every `data-slot` in the page, also in content that is added later. No init call is necessary.

3. Serve the folder and open <http://127.0.0.1:8000/>:

   ```sh
   python3 -m http.server -b 127.0.0.1 -d site 8000
   ```

   Open the page through a web server, not as a file: browsers do not load module scripts from `file://`.

4. In production, send the policy as a header with `frame-ancestors 'none'` (see [Use in a project](#use-in-a-project)). The meta tag is for static hosts that cannot set headers; it comes right after `<meta charset>`, before every `<link>` and `<script>`. [`csp.md`](skills/clanker-ui/references/csp.md) has the Caddy and nginx lines and a small Go test server.

A smaller page can load only the component groups that it uses: see [Minified and group files](#minified-and-group-files). To change the look, see [Override the kit](#override-the-kit).

## Files

| File | Contents |
| --- | --- |
| `clanker-ui.css` | Tokens, reset, typography, all component styles. Generated from the shadcn source (Base UI base, Nova style) plus a small kit layer. It looks exactly like shadcn. |
| `clanker-ui-rhea.css` | The same file in the shadcn Rhea style (rounder, fills and rings in place of borders). Load it instead of `clanker-ui.css`, never both; the markup and JavaScript are the same. |
| `clanker-ui-luma.css` | The same file in the shadcn Luma style (rounded, soft elevation, breathable layouts). Load it instead of `clanker-ui.css`, never both. |
| `clanker-ui-lyra.css` | The same file in the shadcn Lyra style (boxy and sharp, square corners; pairs well with mono fonts). Load it instead of `clanker-ui.css`, never both. |
| `clanker-ui-maia.css` | The same file in the shadcn Maia style (soft and rounded, generous spacing). Load it instead of `clanker-ui.css`, never both. |
| `clanker-ui-mira.css` | The same file in the shadcn Mira style (compact, for dense interfaces). Load it instead of `clanker-ui.css`, never both. |
| `clanker-ui-sera.css` | The same file in the shadcn Sera style (minimal and editorial: underline controls, uppercase headings, square corners). Load it instead of `clanker-ui.css`, never both. |
| `clanker-ui-vega.css` | The same file in the shadcn Vega style (the classic shadcn/ui look). Load it instead of `clanker-ui.css`, never both. |
| `clanker-ui-a11y.css` | Optional accessibility layer. Load it after the kit: 3:1 form-control edges, a 3:1 focus outline and list keyboard highlight, stronger status borders and text, darker light muted text, and the dataviz-validated chart palette. See [Accessibility layer](#accessibility-layer). |
| `clanker-ui.js` | ES module: core helpers and all component behavior |
| `clanker-ui-chart.js` | ES module: SVG charts, stat tiles, sparklines. Imports `./clanker-ui.js` |
| `clanker-ui-code.js` | Optional ES module: syntax colors for the [code block](#code-block). Imports `./clanker-ui.js` |
| `clanker-ui-theme.js` | Optional classic script for apps with a [theme toggle or switch](#theme-toggle-and-switch). Before the first paint it copies the stored theme (`light` or `dark`) to `data-theme` and the stored [color scheme](#color-schemes) to `data-scheme` on `<html>`, sets `data-system-theme`, and sets `<meta name="theme-color">` (without `media`) to `--background`. The module still owns all theme behavior. |
| `clanker-ui-themes.css` | Optional [color schemes](#color-schemes): the shadcn base colors and accent themes, and editor palettes (Tokyo Night, Catppuccin, Gruvbox, Nord, Dracula, Rosé Pine, Solarized, One, Kanagawa, Everforest, GitHub). Load it after `clanker-ui.css`. Apps without schemes do not need it. |
| `dist/` | Minified copies of every file and one file for each component group. See [Minified and group files](#minified-and-group-files). |

## Use in a project

1. Copy the files from one release. Never edit a copy: fix a bug in this repository (or report it), then copy the new files again. Find outdated copies with `shasum`. Read [CHANGELOG.md](CHANGELOG.md) before an update: it lists the breaking markup changes first.
2. Load the kit first, then the app:

   ```html
   <meta name="color-scheme" content="light dark">
   <link rel="stylesheet" href="clanker-ui.css">
   <link rel="stylesheet" href="clanker-ui-themes.css">
   <link rel="stylesheet" href="clanker-ui-a11y.css">
   <link rel="stylesheet" href="app.css">
   <script src="clanker-ui-theme.js"></script>
   <script type="module" src="clanker-ui.js"></script>
   ```

   Put all scripts in `<head>`. Load `clanker-ui-theme.js` (only in apps with a theme toggle, switch, or scheme picker) after the stylesheets, as a classic script without `type="module"`, `defer`, or `async`. It runs before `<body>` is parsed, so a stored theme that differs from the system theme shows from the first frame. Do not put it before the stylesheets: then WebKit sometimes keeps `<body>` without the kit styles. A module runs only after the document is parsed. Without the theme file, the page shows the system theme until the module runs (0.2 s to 1.8 s measured). Apps without a theme switch do not need the file. `clanker-ui-themes.css` is optional too.

3. Put app styles in `app.css`. The kit CSS is in cascade layers (`clanker.tokens`, `clanker.themes`, `clanker.base`, `clanker.components`, `clanker.utilities`), so every unlayered rule in `app.css` wins without specificity fights. Token overrides in `app.css` also win over color schemes.
4. Re-brand by overriding tokens in `app.css`. Light values are on `:root`; dark values are on `[data-theme="dark"]` and, for the system theme, in `@media (prefers-color-scheme: dark)` on `:root:not([data-theme="light"])`. Give a color for each mode (or use `light-dark()` in one `:root` rule, because the kit sets `color-scheme`):

   ```css
   :root { --primary: oklch(0.55 0.2 260); --radius: 0.5rem; }
   [data-theme="dark"] { --primary: oklch(0.75 0.15 260); }
   @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --primary: oklch(0.75 0.15 260); } }
   ```

   `clanker-ui-themes.css` is optional. Load `clanker-ui-a11y.css` in every app: the kit keeps the shadcn values for parity, and some of them are below WCAG 2.2 AA (status badges and alerts, the avatar fallback, muted text on `--muted`, input borders, the focus ring); the layer fixes them (see [Accessibility layer](#accessibility-layer)). Load them in this order after `clanker-ui.css` and before `app.css`: the accessibility layer has adjustments for each color scheme that must come after the schemes.

5. Send this CSP header (the dev server does):

   ```text
   default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; require-trusted-types-for 'script'
   ```

   On a static host that cannot send headers, put the same policy without `frame-ancestors 'none'` in `<meta http-equiv="Content-Security-Policy" content="...">` right after `<meta charset>` and before every `<link>` and `<script>` (browsers ignore `frame-ancestors` in a meta tag). To load the kit from a CDN (for example jsDelivr, `https://cdn.jsdelivr.net/gh/bl4ko/clanker-ui@vX.Y.Z/dist/clanker-ui.min.css`), add the CDN host to `script-src` and `style-src` and use `integrity` hashes; copying the files stays the default.

   Do not use inline `<script>`, inline `<style>`, `style=""`, or `on*=""` attributes. Setting `element.style.x` from JavaScript is allowed. The kit needs no `data:` URLs; `img-src data:` is for app images.

   Safari 27.2 logs one "Refused to apply a stylesheet" error (a `style-src-attr` violation, also sent to CSP report endpoints) for each `<select>` in the HTML of a page with this policy ([WebKit bug 327212](https://bugs.webkit.org/show_bug.cgi?id=327212)). It has no visual effect unless the select sets `text-overflow`. Selects made with `h()` do not report it.

Browsers: Chrome, Safari (also iOS), and Firefox released in the last two years.

### Override the kit

Put overrides in `app.css` after the kit files, without a layer.

- Change tokens, not properties. `.brand { --primary: oklch(0.55 0.2 260); --primary-foreground: oklch(0.985 0 0) }` on a button keeps the kit hover, focus, and dark states. A `background-color` on the button also wins, but then the hover shows no change.
- A wider dialog or sheet: set `max-width` (`.wide { max-width: 50rem }` on `dialog-content`). The kit sets `max-width`, so a `width` alone does not make it wider.
- Fonts: set `--font-sans` and `--font-mono` on `:root`. The body, the controls, and the popups use them.
- Tailwind or other layered CSS: load a first stylesheet that has only `@layer theme, base, clanker, components, utilities;`. Without it, layers that come after the kit layers win over the kit: the Tailwind reset in `base` removes the background and the radius of the buttons.
- Kit `!important` declarations (for example the 12 px icon in a badge) win over `app.css`, also over `!important` in `app.css`. Put `@layer app-important, clanker;` in that first stylesheet, and put the override in `@layer app-important { ... }` with `!important`.

### Minified and group files

`dist/` has minified copies of the kit and one file for each component group, so an app loads only the groups that it uses. `go run ./tools/gen dist` makes them from the readable files, and the generator runs it after it writes `clanker-ui.css`. The readable files stay the source: do not edit `dist/`. Copy `dist/` files byte for byte into the same directory as the other kit files.

| File | Contents |
| --- | --- |
| `clanker-ui.min.css` | All CSS: the group files below in group order |
| `clanker-ui-<group>.min.css` | The CSS of one group. Each file starts with the layer order. |
| `clanker-ui-<style>.min.css`, `clanker-ui-<style>-<group>.min.css` | The same files in another shadcn style (`rhea`, `luma`, `lyra`, `maia`, `mira`, `sera`, `vega`). Use them instead of the Nova CSS files. |
| `clanker-ui-themes.min.css`, `clanker-ui-a11y.min.css`, `clanker-ui-theme.min.js` | Minified copies of the optional files (`clanker-ui-theme.min.js` is a classic script, like `clanker-ui-theme.js`) |
| `clanker-ui-core.min.js` | Core helpers, icons, strings, theme, and the behavior of the core components |
| `clanker-ui.min.js` | The behavior of all other components. Imports `./clanker-ui-core.min.js` |
| `clanker-ui-<group>.min.js` | The behavior of one group (`forms`, `overlays`, `layout`, `chat`). Imports `./clanker-ui-core.min.js` |
| `clanker-ui-chart.min.js` | The chart module. Imports `./clanker-ui-core.min.js` |
| `clanker-ui-code.min.js` | The syntax color module. Imports `./clanker-ui-core.min.js` |

| Group | Components | Needs |
| --- | --- | --- |
| `core` | button, separator, direction, theme, input, textarea, label, kbd, card, badge, alert, table, skeleton, spinner, empty, progress, aspect-ratio, page, site-header, section-cards, stat-grid, data-table, brand, text-stack, card-grid, cover, rating |  |
| `forms` | button-group, input-group, input-otp, field, form, checkbox, radio-group, switch, slider, select, native-select, combobox, toggle, toggle-group |  |
| `overlays` | dialog, alert-dialog, sheet, drawer, popover, tooltip, hover-card, dropdown-menu, context-menu, menubar, navigation-menu, command, toast, sonner, calendar, date-picker | command: `forms`; date-picker: `forms` |
| `layout` | avatar, accordion, collapsible, tabs, breadcrumb, pagination, scroll-area, resizable, sidebar, carousel, item | sidebar: `overlays` |
| `chat` | message, bubble, attachment, message-scroller, trace, marker, questionnaire, code-block |  |
| `chart` | chart |  |

1. Make a list of the components that the app uses and find their groups. Add the groups in the "Needs" column: these components put parts of another group in the page. This command lists the groups, with their "Needs", of the `data-slot` parts in the HTML files of the current folder. It reads `clanker-ui.json` (in the zip at `skills/clanker-ui/references/`):

   ```sh
   grep -rhoE 'data-slot="[a-z0-9-]+"' --include='*.html' . | cut -d'"' -f2 | sort -u |
     jq -Rn --slurpfile c clanker-ui.json '[inputs] as $s | [$c[0].components[] | select(any(.parts[]; .slot as $p | $s | index($p))) | .group, .needs[]] | unique'
   ```

   Components that only JavaScript makes are not in the HTML: add `overlays` for `toast()` and `chart` for `chart()`. A missing group fails without a message, so if you are not sure, use the one-file set.
2. If the app uses 3 or more of the 4 component groups (`forms`, `overlays`, `layout`, `chat`), use the one-file set: `clanker-ui.min.css`, `clanker-ui.min.js`, and `clanker-ui-core.min.js`.
3. If not, link the CSS in this order: `core`, `forms`, `overlays`, `layout`, `chat`, `chart`, then `clanker-ui-themes.min.css`, `clanker-ui-a11y.min.css`, and `app.css`. Load one module script for each group whose behavior the app uses; the browser loads the core through the import. `modulepreload` for the core prevents a second round trip. A page with only core components loads `clanker-ui-core.min.js`.

   ```html
   <link rel="stylesheet" href="clanker-ui-core.min.css">
   <link rel="stylesheet" href="clanker-ui-overlays.min.css">
   <link rel="stylesheet" href="clanker-ui-layout.min.css">
   <link rel="stylesheet" href="app.css">
   <link rel="modulepreload" href="clanker-ui-core.min.js">
   <script type="module" src="clanker-ui-overlays.min.js"></script>
   <script type="module" src="clanker-ui-layout.min.js"></script>
   ```

4. Charts: `clanker-ui-chart.min.js`, and `clanker-ui-chart.min.css` with group files (`clanker-ui.min.css` has the chart CSS). Syntax colors: `clanker-ui-code.min.js` (its CSS is in the `chat` group).

- Use the `.min` files together or the readable files together, never both: two cores attach every listener two times. Two group files never define the same slot; `clanker-ui.min.js` together with a group file stops with "already defined".
- In the readable set, `clanker-ui.js` exports everything except the chart API (`clanker-ui-chart.js`) and `codeBlockHighlight` (`clanker-ui-code.js`). In the one-file `.min` set, `clanker-ui.min.js` exports the same names as `clanker-ui.js`: the core API (`h`, `svg`, `icon`, `define`, `strings`, `theme`, `direction`, and the other core exports) and the component API (`toast`, `dialogOpen`, `calendarSetValue`, ...). In the group set, import the core API from `./clanker-ui-core.min.js` and a component API from its group file. The group files do not export the core API again:

   ```js
   import { h, icon, theme, toast, dialogOpen } from "./clanker-ui.min.js"
   ```
- All files are external modules from `'self'` with static relative imports, so the strict CSP and Trusted Types need no change.

## Markup conventions

Markup mirrors the DOM that shadcn v4 renders. If you know the shadcn JSX, you can write the HTML 1:1.

| Attribute | Meaning |
| --- | --- |
| `data-slot="card"`, `data-slot="card-header"` | Component and part. CSS and behavior key off this. |
| `data-variant="outline"` | Variant. No attribute means `default`. |
| `data-size="sm"` | Size. No attribute means `default`. |
| `data-state="open\|closed\|checked\|unchecked\|active\|inactive"` | State. The kit sets it. |
| `data-orientation="horizontal\|vertical"` | Orientation. |
| `data-side`, `data-align`, `data-side-offset`, `data-align-offset` | Requested popup placement. After open, `data-side` and `data-align` hold the resolved placement. |
| `data-disabled` | Disabled non-form element. Form elements use `disabled`. |
| `data-multiple`, `data-loop`, `data-required`, ... | Boolean options: present means on, `"false"` means off (as a JSX `false` prop renders). Also for `data-disabled` on items. |
| `data-lucide="name"` | Icon placeholder. `<svg data-lucide="x"></svg>` is filled in place; `<i data-lucide="x">` is replaced by an `<svg>`. |
| `data-typography` | Typography container (styles direct-child `h1`–`h4`, `p`, `blockquote`, `ul`, `ol`, links, inline `code`). |
| `data-typography="h1\|h2\|h3\|h4\|p\|lead\|large\|small\|muted\|blockquote\|list\|inline-code\|table"` | One typography style on one element. `table` goes on a wrapper `div` around the `<table>`. |
| `data-theme-set="light\|dark\|system\|toggle"` | A button that sets the theme. `toggle` changes between light and dark. The kit keeps `aria-pressed` in sync (for `toggle`: `true` while dark shows). See [Theme toggle and switch](#theme-toggle-and-switch). |
| `data-scheme="<scheme> [accent] [options]"` on `<html>` | [Color scheme](#color-schemes), a list of names separated by spaces. On another element it scopes the scheme to that element. |
| `data-theme-picker`, `data-theme-picker="accent\|<name>"` | A `<select>` that changes one part of `data-scheme`. See [Color schemes](#color-schemes). |
| `data-system-theme="light\|dark"` on `<html>` | Set by the kit: the system mode that shows in `system` mode. See [Theme toggle and switch](#theme-toggle-and-switch). |
| `data-keyboard` on `<html>` | Set by the kit. Present after a trusted key press without Ctrl, Meta, or Alt, like `:focus-visible` (a lone modifier and the key `Unidentified` do not count). Removed when the pointer moves to new coordinates or presses; a move with the same coordinates (WebKit sends one when content scrolls under the cursor) does not count. While it is present, select, combobox, command, and menu items ignore pointer hover and leave events, so the keyboard item keeps the highlight. CSS for keyboard-only indicators keys off it. |
| `data-show-from="sm\|md\|lg\|xl"`, `data-hide-from="sm\|md\|lg\|xl"` | Responsive visibility: `display: none` below (`show-from`) or from (`hide-from`) the viewport width 40rem, 48rem, 64rem, or 80rem, like the Tailwind `hidden lg:flex` and `lg:hidden` of the shadcn blocks. |
| `class="sr-only"` | Visually hidden text. |

Add ARIA per the WAI-ARIA APG. The kit adds the ARIA it can (`role`, `aria-expanded`, `aria-controls`, `aria-labelledby`, ...).

### Parts that are other components (`asChild`)

When shadcn renders a part through another component (`asChild` or `render`), keep that component's `data-slot` and add the part as a boolean attribute. The element gets the look of the component and the behavior of the part:

```html
<button type="button" data-slot="button" data-variant="outline" data-dialog-trigger>Open</button>
<div data-slot="popover-content" data-date-picker-content>...</div>
<select data-slot="native-select" data-date-picker-preset>...</select>
```

A part attribute with a value targets a component elsewhere by id, for example a menu item that opens a dialog: `<div data-slot="dropdown-menu-item" data-dialog-trigger="dialog-settings">`.

Part attributes: `data-dialog-trigger`, `data-dialog-close`, `data-alert-dialog-trigger`, `data-alert-dialog-action`, `data-alert-dialog-cancel`, `data-sheet-trigger`, `data-sheet-close`, `data-drawer-trigger`, `data-drawer-close`, `data-popover-trigger`, `data-tooltip-trigger`, `data-hover-card-trigger`, `data-dropdown-menu-trigger`, `data-collapsible-trigger`, `data-combobox-trigger`, `data-date-picker-trigger`, `data-date-picker-content`, `data-date-picker-input`, `data-date-picker-preset`.

Overlay roots (`dialog`, `popover`, `tooltip`, `hover-card`, `dropdown-menu`, ...) render no box (`display: contents`), like Radix roots. A `button-group` treats the trigger inside such a root as its own child.

### Button

```html
<button type="button" data-slot="button" data-variant="outline" data-size="sm"><svg data-lucide="send"></svg>Send</button>
<a data-slot="button" data-variant="link" href="/docs">Docs</a>
```

Variants: `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`. Sizes: `default`, `xs`, `sm`, `lg`, `icon`, `icon-xs`, `icon-sm`, `icon-lg`. A `<button>` without a `tabindex` gets `tabindex="0"` like the Base UI button, so Tab reaches it also in Safari. The same applies to the kit trigger and close buttons that are not `data-slot="button"`: dialog, alert dialog, sheet, drawer, popover, and menu triggers, accordion, collapsible, tooltip, and hover card triggers, the carousel buttons, the dialog, sheet, and drawer close buttons, and the toast close and action buttons.

Parts that shadcn renders with `Button` keep their own `data-slot` and share the button rules, with these defaults when `data-variant` and `data-size` are missing:

| Part | Default |
| --- | --- |
| `pagination-link` | `ghost`, `icon`; the current page has `data-variant="outline"` |
| `carousel-previous`, `carousel-next` | `outline`, `icon-sm`, round 28 px |
| `sidebar-trigger` | `ghost`, 28 px |
| `attachment-action`, `code-block-copy-button`, `code-block-wrap-button`, `code-block-download-button` | `ghost`, `icon-xs` |
| `message-scroller-button` | `secondary`, `icon-sm` |
| `questionnaire-previous`, `questionnaire-skip` | `outline` |
| `questionnaire-next`, `questionnaire-submit` | `default` |
| `calendar-button-previous`, `calendar-button-next` | `ghost`, `--cell-size` |

### Theme toggle and switch

```html
<button type="button" data-slot="button" data-variant="ghost" data-size="icon" data-theme-set="toggle" aria-label="Dark mode" aria-keyshortcuts="D"><svg data-lucide="contrast"></svg></button>
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

An app with a theme toggle or switch also loads `clanker-ui-theme.js` in `<head>` after the stylesheets (see [Use in a project](#use-in-a-project)).

### Color schemes

```html
<link rel="stylesheet" href="clanker-ui.css">
<link rel="stylesheet" href="clanker-ui-themes.css">
<link rel="stylesheet" href="clanker-ui-a11y.css">
...
<html data-scheme="tokyonight-storm">
<html data-scheme="stone amber radius-large menu-bold">
<div data-slot="native-select-wrapper">
  <select data-slot="native-select" data-theme-picker aria-label="Color scheme"></select>
  <svg data-lucide="chevron-down" data-slot="native-select-icon"></svg>
</div>
<select data-slot="native-select" data-theme-picker="accent" aria-label="Accent"></select>
```

- `data-scheme` is a list of names separated by spaces: one base scheme, then an optional accent, radius, and menu accent. The mode stays `data-theme` (`light`, `dark`, `system`). Each base scheme has a light side and a dark side, written with `light-dark()`.
- The rules are in the layer `clanker.themes`, between `clanker.tokens` and `clanker.base`. A shadcn base scheme sets the shadcn tokens and `--chart-1`…`--chart-5` with the exact shadcn values (what `shadcn init` writes for that base color). An editor scheme also sets the status tokens and `--chart-1`…`--chart-8`. Other tokens keep the kit values. `data-scheme` on any element (for example a preview card) shows that scheme inside the element.
- `theme.setScheme(value)` sets the list and stores it in `localStorage["clanker-ui-scheme"]`. `clanker-ui-theme.js` sets `data-scheme` from storage before the first paint; the module does it too. An empty value removes the attribute and the stored value. Without a stored value, the `data-scheme` of the markup stays (the app default).
- A picker is a `<select>` with `data-theme-picker`. The kit fills an empty picker: `data-theme-picker` lists the base schemes in two groups (shadcn and editor themes), and `data-theme-picker="accent"` lists `Base color` (no accent) and the accents. A picker with its own `<option>`s works the same, for example for the radius. On change, the kit removes every name in `data-scheme` that is an option value of that picker and adds the selected value (a base scheme first, other parts last). When no name matches, the picker shows its first option. Every change fires `theme:change`.

| Base scheme | Light side | Dark side |
| --- | --- | --- |
| `zinc`, `neutral`, `stone`, `mauve`, `olive`, `mist`, `taupe` (shadcn `/create` base colors), `gray`, `slate` (legacy shadcn v4 base colors) | shadcn light | shadcn dark |
| `tokyonight-night`, `tokyonight-storm`, `tokyonight-moon` | Tokyo Night Day | Night, Storm, Moon |
| `catppuccin-mocha`, `catppuccin-macchiato`, `catppuccin-frappe` | Catppuccin Latte | Mocha, Macchiato, Frappé |
| `gruvbox` | Gruvbox light (medium) | Gruvbox dark (medium) |
| `nord` | none, shows dark | Nord |
| `dracula` | Alucard | Dracula |
| `rose-pine`, `rose-pine-moon` | Rosé Pine Dawn | Rosé Pine, Moon |
| `solarized` | Solarized light | Solarized dark |
| `one` | One Light | One Dark |
| `kanagawa-wave`, `kanagawa-dragon` | Kanagawa Lotus | Wave, Dragon |
| `everforest` | Everforest light (medium) | Everforest dark (medium) |
| `github` | GitHub light (Primer) | GitHub dark (Primer) |

- Accents are the 17 shadcn `/create` themes: `amber`, `blue`, `cyan`, `emerald`, `fuchsia`, `green`, `indigo`, `lime`, `orange`, `pink`, `purple`, `red`, `rose`, `sky`, `teal`, `violet`, `yellow`. Each sets `--primary`, `--primary-foreground`, `--secondary`, `--secondary-foreground`, `--sidebar-primary`, and `--sidebar-primary-foreground`, like shadcn (base color, then theme). They are made for the shadcn base colors; with `clanker-ui-a11y.css`, every shadcn base color with every accent passes the gates below. shadcn `rose` also sets a dark `--sidebar`; the kit does not port that value.
- Options: `radius-none`, `radius-small`, `radius-medium`, `radius-large` set `--radius` to `0`, `0.45rem`, `0.625rem`, `0.875rem`. `menu-bold` sets `--accent` to `--primary` and `--accent-foreground` to `--primary-foreground` (the shadcn bold menu accent).
- `nord` has no light side. It sets `color-scheme: dark`, so it shows dark also in light mode. Then `theme.resolved()` returns `dark` and the toggle shows pressed; a press still changes the stored mode for the other schemes.
- The token map follows each palette: page, text, surfaces, accent color (primary), red (destructive), and green, blue or cyan, yellow, and red for the status tokens. A status background mixes its color with the page (12 % light, 16 % dark, in OKLab). `--input` and `--border` are the subtle edge color, as in shadcn, and `--ring` is the accent.
- The schemes have the source colors without changes. `clanker-ui-a11y.css` has, in the same layer, the changes that each scheme needs to pass the contrast gates below, so load it after `clanker-ui-themes.css`. Contrast gates, measured by `check_scheme_contrast` from computed colors with `clanker-ui-a11y.css`, in every base scheme, every shadcn base color with every accent and with `menu-bold`, in light and dark: text 4.5:1 (`--foreground` on `--background`, `--card`, `--popover`, `--muted`; each `*-foreground` on its surface; sidebar text on `--sidebar`, `--sidebar-accent`, and `--sidebar-primary`); `--muted-foreground` 4.5:1 on `--background`, `--muted`, `--card`, `--popover`; `--primary-foreground` 4.5:1 on `--primary`; `--destructive` 4.5:1 on `--background`, `--card`, `--popover` (error text); `--input-edge` 3:1 on `--background`, `--card`, `--popover`, `--sidebar`; `--focus-ring` 3:1 on `--background`, `--card`, `--popover`; `--*-text` 4.5:1 on `--*-bg`; `--*-border` 3:1 on `--background` and `--card`.
- When a source color fails a gate, the accessibility layer uses the smallest OKLCH lightness change that passes, with the same hue and chroma (lower chroma only to stay in sRGB). A text color or its surface changes, whichever needs the smaller change. Linked tokens with the same source color change together. `--input-edge` and `--focus-ring` start from their mixes (`--input` with 35 % `--foreground`, `--ring` with 25 % `--foreground`). All changes are in the table below.
- Chart colors: the shadcn base schemes use the exact shadcn `--chart-1`…`--chart-5` (each base color is a gray ramp); `clanker-ui-a11y.css` replaces them with the validated kit palette. `solarized` uses its 8 accent colors (blue, orange, cyan, yellow, magenta, green, violet, red); they pass the dataviz `validate_palette.js` in light (on `#fdf6e3`, three slots below 3:1, so the same relief as the kit palette) and dark. The other editor schemes use the validated kit palette: Tokyo Night, Catppuccin, Kanagawa, and GitHub fail the lightness band or the chroma floor; Gruvbox, Nord, Dracula, Rosé Pine, One, and Everforest have fewer than 8 chart hues.
- Sources and licenses of the palettes: `THIRD_PARTY_NOTICES`.

#### Adjusted tokens

| Schemes | Mode | Tokens in `clanker-ui-a11y.css` (scheme → a11y) |
| --- | --- | --- |
| `neutral` | light | `muted-foreground` `oklch(0.556 0 0)` → `oklch(0.546 0 0)` |
| `stone` | light | `muted-foreground` `oklch(0.553 0.013 58.071)` → `oklch(0.547 0.013 58.071)` |
| `zinc` | light | `muted-foreground` `oklch(0.552 0.016 285.938)` → `oklch(0.544 0.016 285.938)` |
| `gray` | light | `muted-foreground` `oklch(0.551 0.027 264.364)` → `oklch(0.543 0.027 264.364)` |
| `slate` | light | `muted-foreground` `oklch(0.554 0.046 257.417)` → `oklch(0.544 0.046 257.417)` |
| `olive` | light | `muted-foreground` `oklch(0.58 0.031 107.3)` → `oklch(0.542 0.031 107.3)` |
| `mist` | light | `muted-foreground` `oklch(0.56 0.021 213.5)` → `oklch(0.538 0.021 213.5)` |
| `taupe` | light | `muted-foreground` `oklch(0.547 0.021 43.1)` → `oklch(0.539 0.021 43.1)` |
| `tokyonight-night`, `tokyonight-storm`, `tokyonight-moon` | light | `accent-foreground` `#3760bf` → `#284eac`, `card-foreground` `#3760bf` → `#284eac`, `destructive` `#f52a65` → `#c9004c`, `error-text` `#c64343` → `#ac292e`, `foreground` `#3760bf` → `#284eac`, `info-text` `#07879d` → `#006678`, `input-edge` `oklch(0.67 0.082 268.1)` → `oklch(0.572 0.082 268.1)`, `muted-foreground` `#68709a` → `#4b527a`, `popover-foreground` `#3760bf` → `#284eac`, `primary` `#2e7de9` → `#0961cb`, `secondary-foreground` `#3760bf` → `#284eac`, `sidebar-accent-foreground` `#3760bf` → `#284eac`, `sidebar-foreground` `#6172b0` → `#43518c`, `sidebar-primary` `#2e7de9` → `#0961cb`, `success-text` `#587539` → `#486428`, `warning-text` `#8c6c3e` → `#755628` |
| `tokyonight-night` | dark | `error-text` `#db4b4b` → `#f2605e`, `muted-foreground` `#737aa2` → `#8c94bd` |
| `tokyonight-storm` | dark | `error-text` `#db4b4b` → `#ff6f6b`, `input-edge` `oklch(0.547 0.056 274.217)` → `oklch(0.555 0.056 274.217)`, `muted-foreground` `#737aa2` → `#8c94bd` |
| `tokyonight-moon` | dark | `error-border` `#c53b53` → `#c63c54`, `error-text` `#c53b53` → `#f6687b`, `muted-foreground` `#737aa2` → `#939bc4`, `sidebar-foreground` `#828bb8` → `#929bc9` |
| `catppuccin-mocha`, `catppuccin-macchiato`, `catppuccin-frappe` | light | `error-text` `#d20f39` → `#c80033`, `info-text` `#1e66f5` → `#0e58e6`, `input-edge` `oklch(0.678 0.026 275.84)` → `oklch(0.618 0.026 275.84)`, `muted-foreground` `#6c6f85` → `#56586d`, `success-border` `#40a02b` → `#3e9e29`, `success-text` `#40a02b` → `#1d7600`, `warning-border` `#df8e1d` → `#c57a00`, `warning-text` `#df8e1d` → `#955b00` |
| `catppuccin-frappe` | dark | `error-text` `#e78284` → `#fc9596`, `info-text` `#8caaee` → `#95b3f7`, `muted-foreground` `#a5adce` → `#aab2d3` |
| `gruvbox` | light | `input-edge` `oklch(0.657 0.035 82.848)` → `oklch(0.609 0.035 82.848)`, `muted-foreground` `#7c6f64` → `#6b5e54`, `success-text` `#79740e` → `#6b6600`, `warning-text` `#b57614` → `#8e5a00` |
| `gruvbox` | dark | `destructive` `#fb4934` → `#ff503b`, `error-text` `#fb4934` → `#ff7460`, `info-text` `#83a598` → `#88aa9d`, `muted-foreground` `#a89984` → `#afa08b` |
| `nord` | light | `destructive` `#bf616a` → `#f6929a`, `error-text` `#bf616a` → `#f18e95`, `info-text` `#81a1c1` → `#92b3d3`, `input-edge` `oklch(0.585 0.027 263.835)` → `oklch(0.643 0.027 263.835)`, `muted-foreground` `#4c566a` → `#a3aec5` |
| `nord` | dark | `destructive` `#bf616a` → `#f6929a`, `error-text` `#bf616a` → `#f18e95`, `info-text` `#81a1c1` → `#92b3d3`, `input-edge` `oklch(0.585 0.027 263.835)` → `oklch(0.643 0.027 263.835)`, `muted-foreground` `#4c566a` → `#a3aec5` |
| `dracula` | light | `error-text` `#cb3a2a` → `#c33223`, `muted-foreground` `#6c664b` → `#5f593e`, `warning-text` `#846e15` → `#7d6707` |
| `dracula` | dark | `error-text` `#ff5555` → `#ff7c76`, `muted-foreground` `#6272a4` → `#a3b5eb` |
| `rose-pine`, `rose-pine-moon` | light | `destructive` `#b4637a` → `#a05169`, `error-text` `#b4637a` → `#9c4e65`, `info-text` `#56949f` → `#31707b`, `input-edge` `oklch(0.741 0.022 299.172)` → `oklch(0.623 0.022 299.172)`, `muted-foreground` `#797593` → `#6a6683`, `primary` `#907aa9` → `#7d6795`, `sidebar-primary` `#907aa9` → `#7d6795`, `warning-border` `#ea9d34` → `#c67e00`, `warning-text` `#ea9d34` → `#965e00` |
| `rose-pine` | dark | `success-text` `#31748f` → `#5193af` |
| `rose-pine-moon` | dark | `destructive` `#eb6f92` → `#f6799c`, `error-text` `#eb6f92` → `#f17497`, `input-edge` `oklch(0.571 0.038 289.836)` → `oklch(0.609 0.038 289.836)`, `muted-foreground` `#908caa` → `#a29ebc`, `success-text` `#3e8fb0` → `#53a3c5` |
| `solarized` | light | `accent-foreground` `#657b83` → `#576c74`, `card-foreground` `#657b83` → `#576c74`, `destructive` `#dc322f` → `#d72c2a`, `error-text` `#dc322f` → `#cb1c20`, `foreground` `#657b83` → `#576c74`, `info-text` `#268bd2` → `#006dad`, `input-edge` `oklch(0.804 0.013 128.459)` → `oklch(0.646 0.013 128.459)`, `muted-foreground` `#93a1a1` → `#5e6b6b`, `popover-foreground` `#657b83` → `#576c74`, `primary` `#268bd2` → `#0076bb`, `secondary-foreground` `#657b83` → `#576c74`, `sidebar-accent-foreground` `#657b83` → `#576c74`, `sidebar-foreground` `#657b83` → `#576c74`, `sidebar-primary` `#268bd2` → `#0076bb`, `success-border` `#859900` → `#849800`, `success-text` `#859900` → `#617000`, `warning-border` `#b58900` → `#b48800`, `warning-text` `#b58900` → `#866400` |
| `solarized` | dark | `accent` `#073642` → `#002f3b`, `destructive` `#dc322f` → `#fa5149`, `error-text` `#dc322f` → `#ff6a5f`, `info-text` `#268bd2` → `#43a3ec`, `input-edge` `oklch(0.43 0.04 217.216)` → `oklch(0.542 0.04 217.216)`, `muted` `#073642` → `#002f3b`, `muted-foreground` `#586e75` → `#7e959c`, `primary` `#268bd2` → `#3193db`, `secondary` `#073642` → `#002f3b`, `sidebar-accent` `#073642` → `#002f3b`, `sidebar-primary` `#268bd2` → `#3193db`, `success-text` `#859900` → `#93a823`, `warning-text` `#b58900` → `#c49722` |
| `one` | light | `destructive` `#e45649` → `#ce4136`, `error-text` `#e45649` → `#c3372d`, `info-text` `#0184bc` → `#0070a1`, `input-edge` `oklch(0.724 0.005 274.503)` → `oklch(0.622 0.005 274.503)`, `muted-foreground` `#696c77` → `#646772`, `primary` `#4078f2` → `#356ce5`, `sidebar-primary` `#4078f2` → `#356ce5`, `success-text` `#50a14f` → `#287b2a`, `warning-text` `#cb7701` → `#9d5b00` |
| `one` | dark | `destructive` `#e06c75` → `#e36e77`, `error-text` `#e06c75` → `#f78189`, `input-edge` `oklch(0.518 0.022 264.84)` → `oklch(0.562 0.022 264.84)`, `muted-foreground` `#828997` → `#a3abb9` |
| `kanagawa-wave`, `kanagawa-dragon` | light | `destructive` `#e82424` → `#d60012`, `error-text` `#e82424` → `#c5000f`, `info-text` `#5a7785` → `#486472`, `input-edge` `oklch(0.726 0.048 97.237)` → `oklch(0.586 0.048 97.237)`, `muted-foreground` `#8a8980` → `#616058`, `success-text` `#6f894e` → `#51692f`, `warning-border` `#e98a00` → `#c47300`, `warning-text` `#e98a00` → `#935500` |
| `kanagawa-wave` | dark | `destructive` `#e82424` → `#fb3c36`, `error-text` `#e82424` → `#ff5b4f`, `info-text` `#658594` → `#799aa9`, `muted-foreground` `#727169` → `#939289` |
| `kanagawa-dragon` | dark | `destructive` `#e82424` → `#f2312d`, `error-text` `#e82424` → `#ff453d`, `info-text` `#658594` → `#7191a0`, `input-edge` `oklch(0.513 0.004 115.351)` → `oklch(0.515 0.004 115.351)`, `muted-foreground` `#737c73` → `#879087` |
| `everforest` | light | `destructive` `#f85552` → `#cc262d`, `error-text` `#f85552` → `#ca252c`, `focus-ring` `#80943d` → `#7b8e37`, `info-text` `#3a94c5` → `#00709f`, `input-edge` `oklch(0.76 0.014 119.791)` → `oklch(0.62 0.014 119.791)`, `muted-foreground` `#829181` → `#5f6d5e`, `primary` `#8da101` → `#697800`, `sidebar-primary` `#8da101` → `#697800`, `success-border` `#8da101` → `#849700`, `success-text` `#8da101` → `#637100`, `warning-border` `#dfa000` → `#ba8500`, `warning-text` `#dfa000` → `#8d6400` |
| `everforest` | dark | `destructive` `#e67e80` → `#ff9697`, `error-text` `#e67e80` → `#fc9193`, `info-text` `#7fbbb3` → `#81beb6`, `input-edge` `oklch(0.586 0.007 126.089)` → `oklch(0.66 0.007 126.089)`, `muted-foreground` `#9da9a0` → `#abb7ae` |
| `github` | light | `input-edge` `oklch(0.662 0.012 247.352)` → `oklch(0.65 0.012 247.352)` |
| `amber` | light | `sidebar-primary` `oklch(0.666 0.179 58.318)` → `oklch(0.57 0.179 58.318)` |
| `blue` | dark | `sidebar-primary` `oklch(0.623 0.214 259.815)` → `oklch(0.555 0.214 259.815)` |
| `cyan` | light | `sidebar-primary` `oklch(0.609 0.126 221.723)` → `oklch(0.539 0.126 221.723)` |
| `emerald` | light | `sidebar-primary` `oklch(0.596 0.145 163.225)` → `oklch(0.526 0.145 163.225)` |
| `fuchsia` | light | `sidebar-primary` `oklch(0.591 0.293 322.896)` → `oklch(0.575 0.293 322.896)` |
| `fuchsia` | dark | `sidebar-primary` `oklch(0.667 0.295 322.15)` → `oklch(0.575 0.295 322.15)` |
| `green` | light | `sidebar-primary` `oklch(0.627 0.194 149.214)` → `oklch(0.525 0.194 149.214)` |
| `green` | dark | `sidebar-primary` `oklch(0.723 0.219 149.579)` → `oklch(0.517 0.219 149.579)` |
| `indigo` | dark | `sidebar-primary` `oklch(0.585 0.233 277.117)` → `oklch(0.559 0.233 277.117)` |
| `lime` | light | `sidebar-primary` `oklch(0.648 0.2 131.684)` → `oklch(0.54 0.2 131.684)` |
| `lime` | dark | `primary-foreground` `oklch(0.405 0.101 131.063)` → `oklch(0.401 0.101 131.063)` |
| `orange` | light | `sidebar-primary` `oklch(0.646 0.222 41.116)` → `oklch(0.574 0.222 41.116)` |
| `orange` | dark | `sidebar-primary` `oklch(0.705 0.213 47.604)` → `oklch(0.571 0.213 47.604)` |
| `pink` | light | `sidebar-primary` `oklch(0.592 0.249 0.584)` → `oklch(0.562 0.249 0.584)` |
| `pink` | dark | `sidebar-primary` `oklch(0.656 0.241 354.308)` → `oklch(0.574 0.241 354.308)` |
| `purple` | dark | `sidebar-primary` `oklch(0.627 0.265 303.9)` → `oklch(0.583 0.265 303.9)` |
| `red` | light | `sidebar-primary` `oklch(0.577 0.245 27.325)` → `oklch(0.563 0.245 27.325)` |
| `red` | dark | `sidebar-primary` `oklch(0.637 0.237 25.331)` → `oklch(0.571 0.237 25.331)` |
| `rose` | light | `sidebar-primary` `oklch(0.586 0.253 17.585)` → `oklch(0.552 0.253 17.585)` |
| `rose` | dark | `sidebar-primary` `oklch(0.645 0.246 16.439)` → `oklch(0.559 0.246 16.439)` |
| `sky` | light | `sidebar-primary` `oklch(0.588 0.158 241.966)` → `oklch(0.54 0.158 241.966)` |
| `teal` | light | `sidebar-primary` `oklch(0.6 0.118 184.704)` → `oklch(0.534 0.118 184.704)` |
| `violet` | dark | `sidebar-primary` `oklch(0.606 0.25 292.717)` → `oklch(0.572 0.25 292.717)` |
| `yellow` | light | `sidebar-primary` `oklch(0.681 0.162 75.834)` → `oklch(0.563 0.162 75.834)` |
| `yellow` | dark | `sidebar-primary` `oklch(0.795 0.184 86.047)` → `oklch(0.559 0.184 86.047)` |

### Core exports

| Export | Signature | Notes |
| --- | --- | --- |
| `h` | `h(tag, attrs?, ...children) → Element` | Safe DOM builder. Strings and numbers become text nodes. Attributes use `setAttribute`. `on*` props must be functions (`onclick`, `"ontabs:change"`). `style` must be an object (`{ marginTop: "1px", "--x": "2px" }`). `null`, `undefined`, `false` are skipped; `true` sets an empty attribute. Arrays and iterables are flattened. Refuses `<script>`, `<style>`, `<link>`, `<meta>`, `<object>`, `<embed>`, `<base>`, `<frame>`, `<frameset>`, the SVG animation elements `<set>`, `<animate>`, `<animateMotion>`, `<animateTransform>` (they can write a `javascript:` URL into `href`), `srcdoc`, string handlers, and string `style`. `<iframe>` is allowed (`src` is filtered). Drops `javascript:` and `vbscript:` URLs in `href`, `src`, `action`, `formaction`, `xlink:href`, `poster`, `ping`, `cite`, and `background`. If `attrs` is a string, node, or array, it is a child. |
| `svg` | `svg(tag, attrs?, ...children) → SVGElement` | Same as `h` in the SVG namespace. |
| `icon` | `icon(name, attrs?) → SVGSVGElement` | Lucide icon with `class="lucide lucide-<name>"`. It gets `aria-hidden="true"` unless `attrs` has `role`, `aria-label`, or `aria-labelledby`. `attrs` override the defaults. An unknown name logs one `console.warn` per name and gives an empty `<svg>` (as Lucide `createIcons` does); it does not throw. `<svg data-lucide>` follows the same rule. All names and aliases: `skills/clanker-ui/references/icons.md`. |
| `iconNames` | `string[]` | All icon names (244 Lucide icons, without the old Lucide names that are aliases, for example `alert-triangle`, `home`, `filter`, `unlock`). Frozen; `registerIcons` replaces it with a list that has the new names. |
| `registerIcons` | `registerIcons({ name: nodes })` | Adds icons. `nodes` is a Lucide icon node: a list of path `d` strings or `[tag, attrs]` pairs (`path`, `circle`, `rect`, `line`, `polyline`, `polygon`, `ellipse`; geometry, `fill`, `stroke*`, `fill-rule`, `clip-rule`, `opacity`, `transform`). Other tags or attributes, a name that is not lowercase words joined by `-`, or a name that exists throw. `<svg data-lucide>` elements in the page with a new name are filled. |
| `define` | `define(slot, spec)` | Behavior registry, see below. Throws if the slot is already defined. |
| `emit` | `emit(target, name, detail?, { cancelable }?) → boolean` | Dispatches a bubbling, composed `CustomEvent`. Returns `false` if a listener called `preventDefault()`. |
| `uid` | `uid(prefix = "clanker") → string` | Unique id that is not in the document. |
| `ensureId` | `ensureId(el, prefix?) → string` | Returns `el.id`, sets one first if empty. |
| `strings` | `object` | Every fixed UI string of the kit (chart module included), English by default. See [Localization](#localization). |
| `stringFor` | `stringFor(el, key, params?) → string` | Reads one string with the per-element override. See [Localization](#localization). |
| `show` | `show(el, options?)` | Opens a popup, see [Popups](#popups). |
| `hide` | `hide(el, { restoreFocus = true, after, focusVisible }?) → Promise` | Closes after exit animations finish. `after` (a promise) replaces the wait for the animations on `el`, for parts that animate a child (drawer popup); it closes also when `after` rejects. `focusVisible` sets whether the returned focus shows a ring (default: the rule below). |
| `isOpen` | `isOpen(el) → boolean` | `true` between `show` and `hide`. |
| `position` | `position(floating, anchor, { side, align, sideOffset, alignOffset, collisionPadding, flip, lazyFlip, settle }?) → stop()` | Places `floating` next to `anchor` (an element or `{ getBoundingClientRect }`) and keeps it placed on scroll and resize. `settle: true` ends a running `left`/`top` transition at each move (select, combobox). After a size change of `floating` or `anchor`, it moves before the next paint, but only if the move does not change its size (an automatic width depends on `left`); otherwise it moves in the next frame. The size variables always change in the next frame. This prevents a `ResizeObserver` loop error. Scroll and window resize place it once per frame. |
| `dismissable` | `dismissable(el, onDismiss(reason, event), { escape, outside, focusOutside, intentional, ignore }?) → release()` | Layer stack. Escape closes the top layer. An outside press closes layers from the top down, with the Base UI 1.6.0 `outsidePressEvent` rule for each pointer type. Sloppy (the default): a mouse or pen press closes at `pointerdown`; a touch closes at the end of a tap (the compatibility `mousedown`), at the end of a touch that moved more than 5 px, or during a move of more than 10 px. `intentional` closes only on a main-button `click` outside whose press started outside and did not end in the layer; `true` uses it for all pointers (dialogs, sheets, the mobile sidebar, the navigation menu), `"mouse"` for mouse and pen only (popover, date picker, non-modal drawer), `"touch"` for touch only (combobox). A press that ends with no click (right or middle button, a cancelled touch) does not leave a pending close for a later click. `reason` is `"escape"`, `"outside"`, or `"focus"`. Focus changes during a pointer press never dismiss (WebKit moves focus to a focusable ancestor on press). Pointer down or focus inside an open toast never dismisses a layer. |
| `trapFocus` | `trapFocus(container) → release()` | Tab and Shift+Tab wrap inside the top trap. Like the Base UI focus guards, it puts a hidden `data-slot="focus-guard"` span (`tabindex="0"`) first and last in `container`; focus on the first goes to the last stop, focus on the last goes to the first stop, and the browser order applies everywhere else. |
| `focusFirst` | `focusFirst(container) → Element` | Focuses `[autofocus]`, else the first tabbable outside a toast, else the container. |
| `tabbables` | `tabbables(container) → Element[]` | Visible, enabled, tabbable elements in order. |
| `saveFocus` | `saveFocus(trigger?) → restore(visible?)` | Focuses `trigger` first when it is in the document and does not have focus (Safari does not focus a button on click). Then remembers `document.activeElement`. `restore(visible)` focuses it again with a ring when `visible` is true or the keyboard is in use; if it already has focus with the wrong ring state, it focuses it again. |
| `hideOthers` | `hideOthers(elements) → release()` | Sets `aria-hidden="true"` on everything outside `elements` and live regions (`[aria-live]`), as Base UI does for a modal context menu. `release()` removes only what it set. |
| `lockScroll` | `lockScroll() → release()` | Counted page scroll lock without layout shift. |
| `rove` | `rove(event, items, { orientation = "vertical", loop = true, typeahead = true, focus = true, active, label, ms, skipDisabled = true }?) → Element \| null` | Call from `keydown`. Handles arrows (RTL aware), Home, End, and typeahead (`ms` goes to `typeahead`). Skips hidden items, and disabled items unless `skipDisabled: false` (menus, as Base UI). Calls `preventDefault()` when it handles the key. With `focus: false` it only returns the next item (use for `aria-activedescendant`). |
| `setRoving` | `setRoving(items, active?) → Element \| null` | Sets `tabindex="0"` on one item and `-1` on the rest. |
| `typeahead` | `typeahead(event, items, { active, label, visible = true, ms = 500 }?) → Element \| null` | `ms` search buffer (the select uses 750 ms, like Base UI); repeated letters cycle. A space inside the buffer time is part of the search. With `visible: false` it also searches items that are not rendered, for example a closed list. |
| `transition` | `transition(el, open) → Promise` | Base UI transition states. Open: sets `data-starting-style` for one frame, so a CSS transition runs from the starting style. Close: sets `data-ending-style` and resolves when the transitions and animations on `el` end; the attribute stays until the next open. |
| `afterAnimations` | `afterAnimations(el) → Promise` | Resolves when the finite animations and transitions on `el` end. Animations on another timeline than `el.ownerDocument.timeline` (scroll-driven animations, for example `.scroll-fade`) do not count. |
| `theme` | `theme.get()`, `theme.set("light"\|"dark"\|"system")`, `theme.resolved()`, `theme.toggle()`, `theme.scheme()`, `theme.setScheme(value)`, `theme.schemes` | The mode is stored in `localStorage["clanker-ui-theme"]` and applied as `data-theme` on `<html>`. `resolved()` returns the mode that shows (`dark` for a dark-only scheme). `toggle()` does what the toggle button does. `scheme()` returns `data-scheme` (`""` when there is none). `setScheme` takes names separated by spaces (`a-z`, `0-9`, `-`, at most 200 characters, else a `TypeError`) and stores them in `localStorage["clanker-ui-scheme"]`; `""` removes the scheme. `schemes` is the frozen list `{ value, label, group }` (`group`: `shadcn`, `editor`, or `accent`). See [Color schemes](#color-schemes). |

### Component exports

Only the components below export functions; every name starts with the component name. `target` is the root, a part, or an id. Open and close functions return `true` when the state changed. Other components (select, combobox, menus, tooltip, hover card, navigation menu, accordion, collapsible, tabs, sidebar) change state through their triggers and keyboard only.

| Export | Signature | Notes |
| --- | --- | --- |
| `dialogOpen` | `dialogOpen(target, { trigger }?) → boolean` | Works for `dialog`, `alert-dialog`, `sheet`, and `drawer`. |
| `dialogClose` | `dialogClose(target, reason = "api") → boolean` | `reason` goes to the `:close` event. |
| `popoverOpen` | `popoverOpen(target, { trigger, anchor }?) → boolean` | |
| `popoverClose` | `popoverClose(target, reason = "api") → boolean` | |
| `datePickerOpen` | `datePickerOpen(target) → boolean` | |
| `datePickerClose` | `datePickerClose(target, { restoreFocus = true }?) → boolean` | |
| `traceOpen` | `traceOpen(target, { animate = true }?) → boolean` | `target` is a `trace-collapsible` or an element in it. |
| `traceClose` | `traceClose(target, { animate = true }?) → boolean` | |
| `toast` | `toast(message, options?) → id` | Sonner-style calls and the Base UI manager (`toast.add`, `toast.update`, `toast.close`), see [Toast and Sonner](#toast-and-sonner). |
| `calendarGetValue` | `calendarGetValue(el) → value` | `"2026-10-28"`, an array (`multiple`), `{ from, to }` (`range`), or `null`. |
| `calendarSetValue` | `calendarSetValue(el, value, { emit = false, month = true }?) → boolean` | `month` shows the month of the first selected date. |
| `calendarSetMonth` | `calendarSetMonth(el, "2026-10") → boolean` | |
| `messageScrollerScrollToEnd` | `messageScrollerScrollToEnd(el, { behavior }?) → boolean` | |
| `messageScrollerScrollToStart` | `messageScrollerScrollToStart(el, { behavior }?) → boolean` | |
| `messageScrollerScrollToMessage` | `messageScrollerScrollToMessage(el, id, { align, behavior, scrollMargin }?) → boolean` | Waits for the row if the list is still empty. |
| `messageScrollerScrollable` | `messageScrollerScrollable(el) → { start, end }` | |
| `messageScrollerVisibility` | `messageScrollerVisibility(el) → { currentAnchorId, visibleMessageIds }` | |
| `questionnaireGoTo` | `questionnaireGoTo(el, name) → boolean` | |
| `questionnaireRefresh` | `questionnaireRefresh(el)` | Call after you enable or disable an item. |
| `direction` | `direction(el = <html>) → "ltr" \| "rtl"` | |
| `codeBlockHighlight` | `codeBlockHighlight(code, language) → Node[][] \| null` | In `clanker-ui-code.js`: one list of nodes per line for `code-block-line` rows, or `null` for an unknown language. See [Code Block](#code-block). |
| `chart` | `chart(element, data, options) → { update(data, options), destroy() }` | In `clanker-ui-chart.js`, see [Chart](#chart). |
| `sparkline` | `sparkline(element, values, options?) → { update, destroy }` | |
| `statTile` | `statTile(element, options) → { update(options), destroy() }` | |

### Events

Components dispatch bubbling, composed `CustomEvent`s named `<component>:<action>` on the component root. Value changes use `:change` with `detail.value`; open state uses `:open` and `:close`. Components that wrap a native form control fire the native `input` and `change` events instead.

| Event | Target | `detail` |
| --- | --- | --- |
| `theme:change` | `<html>` | `{ mode, resolved, scheme }`, after a mode or scheme change |
| `toggle:change` | `toggle` | `{ pressed, value }` |
| `toggle-group:change` | `toggle-group` | `{ value }` (string, or array for `multiple`) |
| `checkbox:change`, `switch:change` | `checkbox`, `switch` | `{ checked, value }` (`value` is `checked`) |
| `radio-group:change` | `radio-group` | `{ value }` |
| `select:open`, `select:close` | `select` | — |
| `select:change` | `select` | `{ value }` |
| `combobox:open`, `combobox:close` | `combobox` | — |
| `combobox:change` | `combobox` | `{ value }` (array for `multiple`) |
| `input-otp:complete` | `input-otp` | `{ value }` |
| `form:invalid` | `form` | `{ errors: [{ name, message, element }] }` |
| `form:submit` | `form` | `{ formData, values, submitter }`, cancelable. Default action: the native submit (the page navigates to `action`); call `preventDefault()` to send with `fetch` |
| `dialog:open`, `alert-dialog:open`, `sheet:open`, `drawer:open` | root | `{ trigger }` |
| `dialog:close`, `alert-dialog:close`, `sheet:close`, `drawer:close` | root | `{ reason }`, cancelable. `reason`: `escape`, `outside`, `close`, `action`, `cancel`, `submit`, `swipe`, `api` |
| `drawer:release` | `drawer` | `{ delta }` when a swipe springs back |
| `drawer:snap-point-change` | `drawer` | `{ snapPoint }` as Base UI `onSnapPointChange`: when a swipe settles (also on the same point), `null` before a swipe close (the old point again if the close is cancelled), and the default point when the drawer closes |
| `popover:open` | `popover` | `{ trigger }` |
| `popover:close` | `popover` | `{ reason }` |
| `tooltip:open`, `tooltip:close`, `hover-card:open`, `hover-card:close` | root | — |
| `dropdown-menu:open`, `context-menu:open`, `menubar:open` | root | `{ trigger }` |
| `dropdown-menu:close`, `context-menu:close`, `menubar:close` | root | `{ reason }` |
| `dropdown-menu:select`, `context-menu:select`, `menubar:select` | root | `{ value, item, checked }`, cancelable (keeps the menu open) |
| `dropdown-menu:change`, `context-menu:change`, `menubar:change` | root | `{ value, checked, item, group }` for checkbox and radio items |
| `navigation-menu:change` | `navigation-menu` | `{ value }` of the open item, `""` when closed |
| `navigation-menu:select` | `navigation-menu` | `{ link, href }` |
| `command:select` | `command` | `{ value, item }` |
| `toast:open` | `toast` | `{ id }` |
| `toast:close` | `toast` | `{ id, reason }`: `timeout`, `close`, `action`, `swipe`, `escape`, `dismiss` |
| `toast:action` | `toast` | `{ id }` |
| `accordion:change` | `accordion` | `{ value }` (string, or array for `multiple`) |
| `avatar:change` | `avatar` | `{ value }`: `loaded` or `error` |
| `carousel:change` | `carousel` | `{ value: index, count }` (snap index and snap count; also once at start and after a new measure that changes them) |
| `collapsible:open`, `collapsible:close` | `collapsible` | — |
| `resizable:change` | `resizable-panel-group` | `{ value }`: the panel sizes in percent |
| `sidebar:open`, `sidebar:close` | `sidebar` | `{ mobile }` |
| `tabs:change` | `tabs` | `{ value }` |
| `trace:open`, `trace:close` | `trace-collapsible` | — |
| `code-block:copy`, `code-block:wrap` | `code-block` | `{ value }` |
| `code-block:download` | `code-block` | `{ value, filename }` |
| `message-scroller:scrollable` | `message-scroller` | `{ start, end }` |
| `questionnaire:change` | `questionnaire` | `{ value, index, total }` (active item name) |
| `questionnaire:status` | `questionnaire` | `{ item, value }`: `answered`, `skipped`, `unanswered` |
| `questionnaire:submit` | `questionnaire` | `{ value, status }`, before the native `submit` |
| `calendar:change` | `calendar` | `{ value, mode, source }`: `day`, `api`, `reset` |
| `calendar:navigate` | `calendar` | `{ value: "YYYY-MM" }` |
| `date-picker:open`, `date-picker:close` | `date-picker` | — |
| `chart:active` | chart element | `{ index, key, row }`, or `null` when the tooltip closes |
| `chart:legend` | chart element | `{ key, visible, hidden }` |
| `chart:view` | chart element | `{ view }`: `chart` or `table` |

### Localization

Every fixed label of the kit (chart module included) comes from the exported `strings` object, English by default. Components read it through `stringFor(el, key, params)` when they create or update a label, so a change shows on the next render or update.

```js
import { strings } from "./clanker-ui.js"
Object.assign(strings, { closeToast: "Zapri obvestilo", remove: "Odstrani {label}", questionOf: p => `Vprašanje ${p.current} / ${p.total}` })
```

```html
<html lang="sl" data-string-close="Zapri" data-string-show-options="Prikaži možnosti">
```

- A value is a string with `{name}` placeholders (unknown placeholders stay as written) or a function `params => string`, for plurals and grammar.
- `data-string-<kebab-key>` on an element or its closest ancestor wins over `strings` (`showOptions` → `data-string-show-options`). On `<html>` it covers the whole page, also markup that the kit initializes at load, before app code runs.
- An unknown key throws. Authored labels (`aria-label`, `data-label-previous`, `data-label-next`, `data-template`, `data-placeholder`) still win; `stringFor` is their fallback.
- Chart series lists in summaries ("Desktop and Mobile") use `Intl.ListFormat` in the chart locale, not a key.

| Key | Default | Used by |
| --- | --- | --- |
| `close`, `closeToast`, `notifications` | `Close`, `Close toast`, `Notifications` | dialog and sheet close buttons, toast close, toast viewport |
| `showOptions`, `dismiss`, `clear`, `remove` | `Show options`, `Dismiss`, `Clear`, `Remove {label}` | combobox trigger, dismiss button, clear, chip remove |
| `commandMenu`, `suggestions` | `Command menu`, `Suggestions` | command input and list |
| `loading` | `Loading` | spinner |
| `breadcrumb`, `more` | `breadcrumb`, `More` | breadcrumb `nav` and ellipsis |
| `resize` | `Resize` | resizable handle |
| `carousel`, `slide`, `slideOf`, `previousSlide`, `nextSlide` | `carousel`, `slide`, `{index} of {count}`, `Previous slide`, `Next slide` | carousel |
| `sidebar`, `toggleSidebar` | `Sidebar`, `Toggle Sidebar` | mobile sidebar, trigger, rail |
| `editorThemes`, `baseColor` | `Editor themes`, `Base color` | scheme picker group, accent picker first option |
| `copy`, `copied`, `wrapLines`, `download` | `Copy`, `Copied`, `Wrap lines`, `Download` | code block |
| `messages`, `scrollToStart`, `scrollToEnd` | `Messages`, `Scroll to start`, `Scroll to end` | message scroller |
| `previous`, `next`, `skip`, `submit` | `Previous`, `Next`, `Skip`, `Submit` | questionnaire buttons |
| `questionnaireProgress`, `questionOf` | `Questionnaire progress`, `Question {current} of {total}` | questionnaire progress |
| `answerRequired`, `answerOrSkip` | `Choose an answer to continue.`, `Choose an answer or skip this question.` | questionnaire error |
| `previousMonth`, `nextMonth`, `chooseMonth`, `chooseYear`, `calendarNavigation` | `Go to the Previous Month`, `Go to the Next Month`, `Choose the Month`, `Choose the Year`, `Navigation bar` | calendar navigation |
| `weekNumber`, `week`, `today`, `selected` | `Week Number`, `Week {week}`, `Today, {date}`, `{date}, selected` | calendar grid |
| `pickDate`, `chooseDate` | `Pick a date`, `Choose date` | date picker |
| `areaChart`, `barChart`, `lineChart`, `pieChart`, `donutChart`, `radarChart`, `radialChart`, `sparkline` | `Area chart`, ..., `Sparkline` | chart name in the summary and table caption |
| `legend`, `tableView`, `tableOf`, `trendOf` | `Legend`, `Table view`, `{caption} data`, `{label} trend` | chart legend, table toggle, table region, stat tile trend |
| `total`, `value`, `share` | `Total`, `Value`, `Share` | chart tooltip and table |
| `noData`, `allHidden`, `onePoint`, `points`, `noValues`, `seriesRange`, `sparklineRange` | `No data.`, `All series are hidden.`, `1 point, {x}`, `{count} points from {from} to {to}`, `{label} has no values`, `{label} from {low} to {high}`, `low {low}, high {high}, latest {latest}` | chart summary |
| `reference`, `references`, `referenceAt`, `referenceBand` | `Reference`, `Reference lines`, `{label} at {value}`, `{label} from {from} to {to}` | chart reference lines in the summary and the table view |

### Behavior registry

```js
define("tabs-trigger", {
  init(el) {
    el.setAttribute("role", "tab")
    return () => {}
  },
  click(event, el) {},
  keydown(event, el) {},
})
```

- `init(el)` runs once for every element with that `data-slot`: the elements in the page when `define` runs and every element that is inserted later. If it returns a function, the kit calls it when the element leaves the document. `init` must not depend on another slot's `init`.
- Every other key is a DOM event type. The handler gets `(event, el)`; `el` is the element with the slot.
- Handlers use one listener per event type on `document`. Bubbling events walk from `event.target` up to the root and call each matching slot, innermost first. `event.stopPropagation()` stops the walk.
- Non-bubbling events (`focus`, `blur`, `mouseenter`, `mouseleave`, `pointerenter`, `pointerleave`, `load`, `error`, `scroll`, `scrollend`, `toggle`, `beforetoggle`, `close`, `cancel`, `invalid`, `resize`, `play`, `pause`, `ended`, `timeupdate`, `loadedmetadata`) call only the slot on `event.target` itself. Use `focusin`, `focusout`, `pointerover`, `pointerout` when you need bubbling.
- `click`, `keydown`, and `focusin` slot handlers run before the core Escape, Tab-trap, and focus handlers. Call `event.preventDefault()` in your handler to stop the core reaction for that event.
- Document-level `wheel` and `touch*` listeners are passive. Use pointer events and CSS `touch-action`.

### Popups

```js
show(content, { trigger, anchor = trigger, side, align, sideOffset = 4, alignOffset = 0, collisionPadding = 8, flip = true, modal = false, escape = true, outside = true, focusOutside = false, intentional = false, focus = "first", restoreFocus = true, expanded = true, onDismiss, onClose })
```

- `content` is a `<dialog>` (`showModal()` if `modal`, else `show()`), an element with `popover` (`showPopover()`), a `<details>`, or any element with `hidden`.
- Use `popover="manual"` for floating content. Do not use `popover="auto"`; the core owns dismissal so all components behave the same.
- `show` focuses `trigger` first with `saveFocus(trigger)` when `restoreFocus` is on (Safari does not focus a button on click), so focus can return to it. It sets `data-state="open"` and `data-open` on `content` (`hide` sets `data-closed`), `data-state="open"` (not with `triggerState: false`, for tooltips, so a toggle trigger keeps its state) and `data-popup-open` on `trigger` (`hide` removes `data-popup-open`), `aria-expanded` and `aria-controls` on `trigger` (not with `expanded: false`, for tooltips and hover cards), places the content next to `anchor`, registers a dismiss layer (`trigger` is ignored by outside-dismiss), traps focus and locks scroll if `modal` (`scrollLock: true` locks scroll without a focus trap, for modal menus; every close path releases it), and moves focus (`"first"`, `"content"`, an element, or `null`). A modal `<dialog>` opened by a pointer focuses its first control again with `focusVisible: false` when the native `showModal()` gave it a focus ring (WebKit), so only keyboard opens and text fields show the ring, as in Base UI.
- `hide` sets `data-state="closed"`, waits for exit animations, then closes natively, then restores focus to the element that had focus before `show` when focus is lost (on `<body>`, inside the closed popup, or on an ancestor of it). While a pointer is pressed it waits one task, so the press can move focus first and a press on a focusable element outside keeps focus there. The returned focus shows a ring (`focusVisible`) when the last focus change came from the keyboard: a key press sets it, and only a pointer press that moves focus to another control clears it (a press on empty space or on the focused element keeps it). So a dialog opened with the keyboard and closed by a press outside returns a ring, a close button press does not, and a select or menu opened with the mouse from a trigger that had a ring returns the ring, as on the live site in all three engines. The kit focuses a menu or popup with the same `focusVisible` state, and a menu item selection returns focus to the trigger the same way. A press outside a modal dialog that ignores outside presses (alert dialog) moves focus out of the dialog, as in Base UI. Popovers, dropdown menus, and menubars return focus after an outside press too; hover popups do not.
- `show(el, { hideOthers: [elements] })` hides the rest of the page from assistive technology (`aria-hidden`) except the popup, those elements, and live regions. Only the modal context menu uses it, as Base UI does; dropdown menus and menubars do not hide the page.
- A `scrollLock` or `hideOthers` popup closes when it is no longer rendered (for example its container gets `hidden`), and `hide()` or a native close of a parent closes the popups inside it first, so no `aria-hidden` and no scroll lock stay.
- A popup opened from an element inside a closing popup (for example a menu item that opens a dialog) returns focus to where the closing popup would have returned it (the menu trigger), not to the item.
- An open popup that leaves the document is closed by the core: no dismiss layer, focus trap, or scroll lock stays.
- Default dismissal calls `hide(content)`. Pass `onDismiss(reason)` to do more, for example to emit an event.
- For `<dialog>`, the dialog element is the visible box. A click on its `::backdrop` counts as outside.
- `position` writes `left`/`top` (fixed), `data-side` and `data-align`, and these CSS variables on the floating element: `--anchor-width`, `--anchor-height`, `--available-width`, `--available-height`, `--transform-origin` (the anchor point, `sideOffset` outside the popup, like Base UI), and `--arrow-x`/`--arrow-y` (the anchor center on the floating element). A `[data-slot="tooltip-arrow"]` inside gets `data-side`, `data-align`, `position: absolute`, and `left` (top and bottom sides) or `top` (left and right sides) at the anchor center, at least 5 px from the popup edges (Base UI `arrowPadding`), and `data-uncentered` when it cannot be centered. `alignOffset` also moves a centered popup (mirrored in RTL, as Floating UI). Use them like Radix variables: `max-height: var(--available-height); transform-origin: var(--transform-origin); min-width: var(--anchor-width)`.
- It flips to the opposite side when there is no space; a `left`/`right` popup with no space on either side goes below (or above) its anchor; a `start`/`end` alignment that overflows swaps to the other one when that fits (Base UI `collisionAvoidance` defaults: side flip, align flip, fallback axis side end). Then it shifts along the cross axis to stay `collisionPadding` from the viewport edge. With `lazyFlip: true` a flipped side stays while the popup is open (Base UI `lazyFlip`; the combobox uses it, so filtering does not flip it back). With `settle: true` a move ends a `left` or `top` transition at once, like the Base UI positioner (select and combobox use it); without it a CSS `left`/`top` transition runs (the Nova navigation positioner slides). It is JavaScript because CSS anchor positioning is not in every target browser.

### CSS rules for components

- `clanker-ui.css` has two parts. The first part is the output of `tools/gen` ([Generated CSS](DEVELOPMENT.md#generated-css)): Tailwind preflight, the shadcn tokens, and one rule set per shadcn part in `@layer clanker.components`. The second part is `tools/gen/kit.css`, hand-written, in the same layers: kit tokens, typography, the chart, the theme switch and toggle, form, date picker, status variants of `alert` and `badge`, spinner sizes, the `empty` outline variant, `.scroll-fade`, the horizontal tab list scroll, and glue for what Base UI and its libraries do with inline styles or conditional rendering (scroll area structure, avatar image or fallback, sidebar widths and the mobile sheet, resizable panels, `[popover]` and `<dialog>` resets for the kit top layer, and popup roots: Base UI renders no element for the root of a select, menu, popover, or dialog, so `select` and `combobox` roots get `display: contents`, and the button group joins and rounds a trigger inside such a root like a direct child). Do not edit `clanker-ui.css`; change the generator or `kit.css`.
- Tokens are the shadcn values. Dark values apply with `data-theme="dark"` on `<html>`, or with `prefers-color-scheme: dark` when `<html>` does not have `data-theme="light"`, so a page without the theme module follows the system.
- Focus is the shadcn look: `ring-3` in `--ring` at 50 % (a box shadow) and `--ring` on the border. `clanker-ui-a11y.css` adds a 3:1 outline.
- Animations use the tw-animate keyframes `enter` and `exit` (`--tw-enter-opacity`, `--tw-enter-scale`, `--tw-enter-translate-x`, ... and the same with `--tw-exit-`), and the shadcn keyframes `spin`, `pulse`, `accordion-down`, `accordion-up`, `caret-blink`, `tw-shimmer`, and `scroll-fade-reveal-*`. Keyframes of the kit layer start with `clanker-` (`clanker-chart-grow`, `clanker-scroll-fade-start`, ...).
- `prefers-reduced-motion: reduce` sets `animation: none`, `transition: none`, and `scroll-behavior: auto` in `clanker.utilities` without `!important`, so state changes are instant and app CSS (or an inline style) can turn motion back on. Spinners (`[data-slot="spinner"]`) keep turning. `.scroll-fade`, `.scroll-fade-x`, and the shadcn scroll fades of `attachment-group`, `code-block-content`, and `message-scroller-viewport` keep their fade animation, because it follows the scroll position. Kit code waits with `afterAnimations`, which resolves at once when nothing runs.
- Text entry controls use 16 px text below 48rem and 14 px from 48rem (shadcn `text-base md:text-sm`), so iOS does not zoom on focus.
- Safari 2024: every `user-select` has `-webkit-user-select` next to it; textareas in an input group get `resize: vertical` when `field-sizing` is not supported; `lockScroll` pads the root by the scrollbar width when `scrollbar-gutter` is not supported.
- Height animations (accordion, trace) turn off page scroll anchoring while they run, so Firefox does not disable it. A close animates from the current height, also when the item opened without animation (open in markup, `animate: false`, find in page). The collapsible has no motion, like shadcn.
- Utilities: `.sr-only`; `.shimmer` (text shimmer, override `--shimmer-color`, `--shimmer-duration`, `--shimmer-spread`, `--shimmer-angle`); `.scroll-fade` and `.scroll-fade-x` (see below).
- `.scroll-fade` goes on a vertical scroll container, `.scroll-fade-x` on a horizontal one. A mask fades the edge where more content is: at rest only the end edge fades, in the middle both edges fade, at the end only the start edge fades. Without overflow, nothing fades. `.scroll-fade-x` mirrors in RTL. It uses scroll-driven animations (`animation-timeline: scroll()`); browsers without them (Firefox today) show no fade. Override `--scroll-fade-size` (default `min(12%, 2.5rem)`), one edge with `--scroll-fade-t-size`, `--scroll-fade-b-size`, `--scroll-fade-s-size`, or `--scroll-fade-e-size`, the whole mask with `--scroll-fade-mask` (`none` turns it off), and `--scroll-fade-reveal` (scroll distance until the fade is full, default `6rem`; `ease-in-out`). The class sets `animation`, so put it on an inner scroller, not on an element with its own enter or exit animation. It follows the shadcn `scroll-fade` utility, with one difference: without scroll-driven animations shadcn shows a fixed fade on both edges, the kit shows none (a fixed fade covers content that does not scroll).
- shadcn tokens: `--background`, `--foreground`, `--card`, `--card-foreground`, `--popover`, `--popover-foreground`, `--primary`, `--primary-foreground`, `--secondary`, `--secondary-foreground`, `--muted`, `--muted-foreground`, `--accent`, `--accent-foreground`, `--destructive`, `--border`, `--input`, `--ring`, `--chart-1`…`--chart-5`, `--sidebar`, `--sidebar-foreground`, `--sidebar-primary`, `--sidebar-primary-foreground`, `--sidebar-accent`, `--sidebar-accent-foreground`, `--sidebar-border`, `--sidebar-ring`, `--radius`.
- Kit tokens: `--radius-sm`…`--radius-4xl`, `--shadow-2xs`…`--shadow-2xl`, `--ease-in`, `--ease-out`, `--ease-in-out`, `--font-sans`, `--font-mono`, `--spacing`; status tokens `--success-bg`, `--success-border`, `--success-text`, and the same for `info`, `warning`, and `error` (the `success`, `warning`, and `info` variants of `alert` and `badge` use them); status fills `--success-fill`, `--warning-fill`, `--error-fill`, `--info-fill` for marks such as bars, dots, and meters (3:1 or more against the card, the same hue in light and dark), and `--neutral-fill` (gray, 3:1 or more against the card) for "no data" marks; chart tokens `--chart-6`…`--chart-8`, `--chart-other`, `--chart-negative`, `--chart-good`, `--chart-bad`, `--chart-surface`, `--chart-grid`, `--chart-axis`, `--chart-area-opacity`, `--chart-ink-light`, `--chart-ink-dark` (label ink inside a fill, set on `[data-slot="chart"]`).

### Accessibility layer

`clanker-ui-a11y.css` loads after `clanker-ui.css` (and after `clanker-ui-themes.css`). It is a separate file only so that the kit itself keeps the shadcn values; load it in every app. It changes only what the list below names, in the kit layers, so `app.css` still wins.

- With a [color scheme](#color-schemes), its last part (layer `clanker.themes`) has the changes for that scheme: the gate fixes in [Adjusted tokens](#adjusted-tokens), and the validated chart palette for the shadcn base schemes. It is hand-written, like `clanker-ui-themes.css`; the `foundation` check `check_scheme_contrast` is the gate.

- `--input-edge` (`--input` mixed with 35 % `--foreground`) is the border of form controls whose border is their only boundary: input, textarea, input group, select, native select, calendar dropdown, OTP slot, checkbox, radio (also the questionnaire choice indicator), combobox chips, and sidebar input; and the fill of the unchecked switch track. It has at least 3:1 on `--background`, `--card`, `--popover`, and `--sidebar` in both themes (WCAG 1.4.11). Focus, invalid, and checked states keep their shadcn colors. Decorative uses of `--input` (separators, outline buttons and toggles, tabs, code block, choice cards, `bg-input/30` fills) keep the shadcn value.
- Focus: every `:focus-visible` element gets `outline: 3px solid var(--focus-ring)`. `--focus-ring` mixes `--ring` with 25 % `--foreground` (at least 3:1 on `--background`; the shadcn ring at 50 % is below 2:1). `aria-invalid="true"` and destructive buttons use `--focus-ring-invalid` (`--destructive`). Composite fields (input group, OTP slot, combobox chips, calendar dropdown, code block, questionnaire choice, slider thumb) draw the outline on the field, not on the inner control. Sidebar items use a 2 px outline of `--sidebar-ring` mixed with 25 % `--sidebar-foreground`; the resizable handle a 1 px outline.
- Keyboard highlight in item lists (select, combobox, and command items, dropdown, context, and menubar items, menubar triggers, and links in navigation menu content): a 2 px `--focus-ring` outline inside the item (`outline-offset: -2px`), only while `<html>` has `data-keyboard` (the kit sets it during keyboard use). Pointer hover shows only the `--accent` background, like shadcn.
- Status tokens: borders reach 3:1 on `--background` (in dark also on `--card`) and light text reaches 4.5:1 on its background (success `hsl(140 100% 25%)`, info `hsl(210 92% 43%)`, warning `hsl(31 92% 35%)`, error `hsl(360 100% 43%)`).
- Destructive buttons and badges (the tinted shadcn `destructive` variant): the text is `--destructive` mixed with 25 % `--foreground`, so it has 4.5:1 on its tinted background, also on hover. The background keeps the shadcn value.
- Light `--muted-foreground` is `oklch(0.54 0 0)` (shadcn 0.556), so it has 4.6:1 on `--muted`.
- `--chart-1`…`--chart-8` is the categorical palette validated with the dataviz `validate_palette.js` in light and dark: all checks pass. In light, slots 3, 4, and 5 are below 3:1 contrast; every chart and sparkline has a tooltip and a table view as relief, and charts with two or more series also have a legend. The kit tokens have the same palette; the layer also gives it to the shadcn base schemes, which set a gray ramp.
- Shimmer text (`.shimmer`, running trace titles, uploading or processing attachment titles): when the shimmer color cannot be computed (an invalid `--shimmer-color`, or a browser without relative color syntax), the text stays plain and visible. Without the layer, the text is transparent then, as in shadcn.
- Forced colors: one `@media (forced-colors: active)` block keeps checkbox ticks, radio dots, switch thumbs, the slider track, range, and thumb, focused menu, select, and navigation items, and highlighted combobox and command items visible with the system colors.

### Security rules

Kit, demo, and docs code (`docs/assets`, templates, content, examples) never use `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, `new Function` or `window.Function`, timers whose first argument is not a function, `DOMParser`, `createContextualFragment`, `setHTML`, `setHTMLUnsafe`, `parseHTMLUnsafe`, `srcdoc`, `javascript:` URLs, `setAttribute` or `setAttributeNS` with `style`, `srcdoc`, or an `on*` name, `createElement("script")` or `createElement("style")`, `execCommand`, or dynamic `import()`. HTML has no inline `<script>` or `<style>`, `style`, `on*`, or `srcdoc` attributes, `javascript:` URLs, remote resources, or comments. Build DOM with `h()`, `svg()`, and `icon()`. Demo images go in `demo/assets/` (CSP allows `'self'` and `data:` only). Templates and content have no `{{/* */}}` comments either. `go test` enforces these rules on all of these files and on every rendered docs page. The same rules keep app code safe under the strict CSP.

## Components

All 65 shadcn registry components, the chart module, and typography. The demo has one section per component with every variant and the shadcn docs examples.

### Forms and inputs

#### Button Group

```html
<div data-slot="button-group" role="group" aria-label="Actions" data-orientation="horizontal|vertical">
  <button type="button" data-slot="button" data-variant="outline">Archive</button>
  <div data-slot="button-group-separator" data-orientation="vertical" role="none"></div>
  <span data-slot="button-group-text">.com</span>
</div>
```

Nest groups for spacing. A `select`, `dropdown-menu`, `popover`, `tooltip`, or `hover-card` root in a group joins its trigger to the group. CSS only.

#### Input, Textarea, Label, Kbd

```html
<input data-slot="input" type="email" placeholder="Email">
<textarea data-slot="textarea"></textarea>
<label data-slot="label" for="email">Email</label>
<kbd data-slot="kbd-group"><kbd data-slot="kbd">Ctrl</kbd><kbd data-slot="kbd">K</kbd></kbd>
```

`aria-invalid="true"` shows the error border. A label after a `:disabled` control is dimmed. A `kbd` inside `tooltip-content` uses the inverted tooltip colors. CSS only.

File upload: `<input data-slot="input" type="file" accept="image/*,application/pdf" name="receipt">` is the shadcn file input (the button is plain `text-sm` text with no border). shadcn has no dropzone component. A dropzone is a `<label>` with the outline `empty` style around a visually hidden file input, and a few lines of app code for drag and drop; show the chosen file with an `attachment` (it works outside a chat). A `label` holds only phrasing content, so the `empty` parts are `span`s:

```html
<label data-slot="empty" data-variant="outline" class="dropzone">
  <input type="file" name="receipt" accept="image/*,application/pdf" class="sr-only">
  <span data-slot="empty-header">
    <span data-slot="empty-icon" data-variant="icon"><svg data-lucide="cloud-upload"></svg></span>
    <span data-slot="empty-title">Upload a receipt</span>
    <span data-slot="empty-description">Drop a file here, or click to choose one. PNG, JPG, or PDF.</span>
  </span>
</label>
```

```js
const zone = document.querySelector(".dropzone")
const input = zone.querySelector("input")
zone.addEventListener("dragover", event => { event.preventDefault(); zone.dataset.dragging = "" })
zone.addEventListener("dragleave", () => delete zone.dataset.dragging)
zone.addEventListener("drop", event => {
  event.preventDefault()
  delete zone.dataset.dragging
  input.files = event.dataTransfer.files
  input.dispatchEvent(new Event("change", { bubbles: true }))
})
```

App CSS: `.dropzone { cursor: pointer }`, a focus ring with `.dropzone:has(input:focus-visible) { outline: 2px solid var(--ring); outline-offset: 2px }`, and `.dropzone[data-dragging] { border-color: var(--primary) }`. A `required` file input in a `data-slot="form"` gets the `field-error` of its field. On `change` with a file, set `hidden` on the zone's header and show an `attachment` with the file name, size, and a remove button (`attachment-action`) in the same field; the remove button clears `input.value`, removes the attachment, and shows the header again. Keep the input in the label, so the field still validates.

#### Input Group

```html
<div data-slot="input-group" role="group">
  <input data-slot="input-group-control" placeholder="Search...">
  <div data-slot="input-group-addon" data-align="inline-start|inline-end|block-start|block-end">
    <svg data-lucide="search"></svg>
    <span data-slot="input-group-text">USD</span>
    <button type="button" data-slot="button" data-input-group-button data-size="xs|sm|icon-xs|icon-sm">Copy</button>
  </div>
</div>
```

The control can be a `textarea`. A click on an addon (not on a button) focuses the control. `input-group` and `input-group-addon` get `role="group"`; an addon without `data-align` gets `inline-start`. Buttons in an addon are `InputGroupButton`: add `data-input-group-button`; the kit sets `data-variant="ghost"` and `data-size="xs"` when they are missing. Sizes: `xs`, `sm`, `icon-xs`, `icon-sm`. Not built: the `.border-b` and `.border-t` class variants of block addons (Tailwind classes, not attributes).

#### Field

`field-set` (a `fieldset`), `field-legend` (`data-variant="legend|label"`; the kit sets `legend` when it is missing, as shadcn renders it), `field-group`, `field` (`data-orientation="vertical|horizontal|responsive"`, `data-invalid="true"`, `data-disabled="true"`), `field-content`, `field-label`, `field-description`, `field-separator` (optional `field-separator-content` child; the kit adds the `separator` line and `data-content`, as shadcn renders them), `field-error`. A `field-label` that wraps a `field` (with `field-content` and a radio, checkbox, or switch) is a choice card. A row with a switch or checkbox next to its label is a `field` with `data-orientation="horizontal"`. `responsive` switches to a row when the closest `field-group` is at least 28rem wide. `data-slot="checkbox-group"` gives the tight checkbox list spacing.

Kit extensions: `field-label-row` holds a `field-label` and a link that goes to the end ("Forgot your password?"). `data-columns="2|3"` on a `field-group` puts its fields in 2 or 3 columns when the group is at least 28rem wide; the fields align at the top, so an error message under one field does not move the others. `data-span="2"` on a field in a 3-column group takes two columns.

#### Form

```html
<form data-slot="form">
  <div data-slot="field" role="group">
    <label data-slot="field-label" for="name">Name</label>
    <input id="name" data-slot="input" name="name" required data-error-value-missing="Name is required.">
  </div>
</form>
```

- Native constraint validation. The kit sets `novalidate` and shows its own errors: after the user changed a control and left it, and on submit, then live. After a submit, leaving a control does not validate it, as in React Hook Form (`reValidateMode: "onChange"`): a control that the app clears after a send shows no error on blur.
- An invalid control gets `aria-invalid="true"` and `aria-describedby` to a `field-error` (`role="alert"`), created if missing. The field gets `data-invalid="true"`. Legacy `form-item`, `form-label` (`data-error`), `form-description`, and `form-message` work the same way.
- Message: `data-error-<validity-flag>`, then `data-error`, then the browser message (`validationMessage`), read from the control, the visible control, or the component root (`radio-group`, `select`, `combobox`, `toggle-group`, `date-picker`, `input-otp`, `slider`). The flags, in the order the kit checks them: `data-error-value-missing`, `data-error-type-mismatch`, `data-error-pattern-mismatch`, `data-error-too-long`, `data-error-too-short`, `data-error-range-underflow`, `data-error-range-overflow`, `data-error-step-mismatch`, `data-error-bad-input`, `data-error-custom-error` (for `setCustomValidity()`). Several custom rules on one field: leave out `data-error-custom-error` and `data-error`, and pass each message to `setCustomValidity(message)` in the control's own `input` or `change` listener; the kit shows it.
- Checkbox, switch, and radio validate through their hidden native input; `aria-invalid` (and so `data-invalid`) goes on the button, and submit focuses the button.
- Submit with errors focuses the first invalid control and emits `form:invalid`; the browser does not submit. A valid submit emits cancelable `form:submit` (`values` has an array for repeated names). If no listener calls `event.preventDefault()`, the browser submits the form natively (to `action`, or to the page URL with `method="get"` when there is no `action`), so the page navigates. A static page or an app that sends with `fetch` must call `preventDefault()` in its `form:submit` listener.
- Form `reset` clears errors and resets all components to their authored values after the reset event. A value that the app sets right after `form.reset()` (`data-value` on a select, combobox, or toggle group, or `calendarSetValue`) stays; the kit does not overwrite it.
- A form that is also a card: `data-slot` takes one value, so put the card inside the form (`<form data-slot="form"><div data-slot="card">...</div></form>`).
- Date picker and toggle group: see their sections for `data-required` and `data-name`.

#### Checkbox, Switch, Radio Group

```html
<button type="button" data-slot="checkbox" id="terms" data-name="terms" value="yes" data-checked data-required></button>
<label data-slot="label" for="terms">Accept terms</label>
<button type="button" data-slot="checkbox" data-indeterminate aria-label="Select all"></button>
<button type="button" data-slot="switch" id="airplane" data-name="airplane" data-size="sm"></button>
<div data-slot="radio-group" data-name="plan" data-value="free" data-required>
  <button type="button" data-slot="radio-group-item" id="plan-free" value="free"></button>
</div>
```

- The Base UI DOM with a native button: `role="checkbox"`, `role="switch"`, or `role="radio"`, `aria-checked` (`mixed` for indeterminate), and the state attributes `data-checked` or `data-unchecked`, `data-indeterminate`, `data-disabled`, `data-readonly`, `data-required`, `data-invalid` (from `aria-invalid="true"`). `data-state` stays in sync.
- The kit adds a hidden native input right after the button (`aria-hidden`, `tabindex="-1"`) for form submission, reset, and validation. It gets `data-name` (radio: the group `data-name`), `value` (default `on`), `required` (`data-required` on the button or the group), and `disabled`. Focus on the hidden input moves to the button. The input follows the button: a removed button takes it out of the form, a moved button moves it. `form.reset()` restores the initial state, also `data-indeterminate`.
- Children: `checkbox-indicator` (check icon) and `radio-group-indicator` exist only while checked; `switch-thumb` is always there and has the same state attributes.
- Initial state: `data-checked` on the button. Change it later the same way: toggle `data-checked` on the button. `disabled`, `aria-invalid`, `data-required`, and `data-readonly` changes are applied at once. The kit moves `disabled` to `aria-disabled`, so enable the control again with `el.disabled = false` or by removing `aria-disabled` (removing the `disabled` attribute has no effect). Read-only controls do not change. A click on a disabled control does not move focus.
- Checkbox: `data-indeterminate` gives the mixed state; toggle it later the same way. Click, Space, and a `<label for>` or wrapping `<label>` toggle; Enter does nothing.
- Switch: `data-name`, `data-required`, and `data-readonly` on the button. Click, Space, Enter, and a `<label for>` or wrapping `<label>` toggle.
- Radio group: the group `data-value` selects the initial item; later, toggle `data-checked` on an item (a `data-value` change on the group does nothing). `data-disabled`, `data-readonly`, and `data-required` on the group apply to all items (`data-disabled` only at init). One tab stop (the checked item, else the first enabled one, with `data-composite-item-active`); arrows move and check, wrap, skip disabled items, and follow RTL; Home and End do nothing. Click, Space, and a `<label for>` check an item; Enter does nothing.
- Events: `checkbox:change` and `switch:change` on the button (`{ checked, value }`), `radio-group:change` on the group (`{ value }`), and native `input` and `change` on the hidden input.

#### Native Select

```html
<div data-slot="native-select-wrapper">
  <select data-slot="native-select" data-size="sm">
    <option data-slot="native-select-option" value="todo">Todo</option>
  </select>
  <svg data-lucide="chevron-down" data-slot="native-select-icon"></svg>
</div>
```

CSS only.

#### Select

```html
<div data-slot="select" data-name="fruit" data-value="apple" data-required>
  <button data-slot="select-trigger" data-size="sm"><span data-slot="select-value">Select a fruit</span></button>
  <div data-slot="select-content" data-align-trigger="true|false">
    <div data-slot="select-group">
      <div data-slot="select-label">Fruits</div>
      <div data-slot="select-item" data-value="apple" data-label="Apple">Apple</div>
      <div data-slot="select-item" data-value="banana" data-disabled>Banana</div>
    </div>
    <div data-slot="select-separator"></div>
  </div>
</div>
```

- The first content of `select-value` is the placeholder (`data-placeholder` on the trigger and the value while no item is selected). The trigger shows a copy of the selected item, or `data-label`. The kit adds the chevron, scroll buttons, `select-viewport`, `select-item-text`, ARIA, and a visually hidden proxy input that submits `data-name`. Only the selected item has `data-selected` and a `select-item-indicator`; with no value, an item with `data-value=""` is the selected one, like the Base UI `null` item. The focused item has `data-highlighted`. While open, the trigger has `data-pressed` and `data-popup-side`. The trigger has `tabindex="0"` like Base UI, so Tab reaches it also in Safari.
- `data-required` makes the proxy `required`. In a `data-slot="form"` the kit shows the error. In other forms native validation reports the proxy (the browser shows its message just below the trigger) and the kit moves focus from the proxy to the trigger.
- Removing and inserting a select again keeps one proxy input, the authored placeholder, and the authored initial value (form reset goes back to it).
- `data-value` is the value: a later change selects that item without a `change` event, and items that arrive later (after a `fetch`) select the authored value. While no item matches, the trigger shows the placeholder and the proxy is empty.
- `data-align-trigger="true"` (default, Base UI `alignItemWithTrigger`) puts the selected item text over the value (`data-side="none"`); `false` (or the old `data-position="popper"`) places the list under the trigger.
- Pointer: a press on the trigger opens the list; moving to an item and releasing selects it, and releasing outside the trigger and the list closes it (Base UI). The focused item has no focus ring after a pointer open, unless the trigger had one (browsers without `focus({ focusVisible })`, before Chrome 145 and Safari 18.4, show the ring). Keyboard: Enter, Space, Up, Down open on the selected item; typing on the closed trigger selects the next match (750 ms buffer) without opening. In the list: arrows (no wrap), Home, End, typeahead (a space within 750 ms of a typed letter is part of the search), Enter or Space to select, Escape to close, Tab closes without a change and moves on. A press outside closes the list and focus goes back to the trigger, unless the press focused another control.

#### Combobox

```html
<div data-slot="combobox" data-name="framework" data-value="next" data-auto-highlight>
  <div data-slot="input-group">
    <input data-slot="input-group-control" placeholder="Select a framework" aria-label="Framework">
    <div data-slot="input-group-addon" data-align="inline-end">
      <button type="button" data-slot="input-group-button" data-combobox-trigger></button>
      <button type="button" data-slot="combobox-clear"></button>
    </div>
  </div>
  <div data-slot="combobox-content">
    <div data-slot="combobox-empty">No items found.</div>
    <div data-slot="combobox-list">
      <div data-slot="combobox-group">
        <div data-slot="combobox-label">Frameworks</div>
        <div data-slot="combobox-item" data-value="next">Next.js</div>
      </div>
      <div data-slot="combobox-separator"></div>
    </div>
  </div>
</div>
```

- Outside press as in Base UI: a mouse press outside closes the list at the press; a touch outside closes it only on the tap click, so a touch drag to scroll keeps it open.
- Multiple: `data-multiple`, `<div data-slot="combobox-chips"><input data-slot="combobox-chip-input"></div>` instead of the input group, initial values in `data-value="a,b"`. The kit renders `combobox-chip` and `combobox-chip-remove`.
- Popup: `<button type="button" data-slot="button" data-variant="outline" data-combobox-trigger><span data-slot="combobox-value">Select country</span></button>` outside the content and the input group inside it.
- The input group gets `data-combobox-input`. The trigger is `data-slot="input-group-button"` (`data-size="icon-xs"` when missing) with `data-combobox-trigger`; it has `tabindex="0"` like Base UI (the label `Show options` stays, Base UI has none). `combobox-clear` has `tabindex="-1"` like Base UI. While the list is open, a visually hidden `<span role="button" aria-label="Dismiss">` (string `dismiss`) before the input closes the list. `combobox-empty` is a polite `role="status"` region; the content and the list have `tabindex="-1"`. While the list is open, the input and the trigger have `data-pressed`, `data-popup-open`, and `data-popup-side`; the trigger has `data-placeholder` without a value; both have `data-list-empty` when the filter shows nothing. A pointer press on the trigger opens the list at once.
- `data-disabled`, `data-required`, `data-name` as in `select` (one hidden proxy input, focus moves from the proxy to the input). `data-value` as in `select`: later items and a later `data-value` change apply it without a `change` event; the kit does not write it back. Typing filters by label (case-insensitive substring), hides empty groups and separators, and shows `combobox-empty`. The highlighted item is `aria-activedescendant`.
- Keyboard: Down and Up (also with Alt) open and move; after the last item (or before the first) the highlight goes back to the input, like Base UI `loopFocus`. Alt+Up closes, Enter selects (or closes when no item is highlighted), Escape closes; Escape on a closed combobox clears the value (all chips in multiple). Home and End move the caret and never scroll the page. Chips (`role="toolbar"`): Backspace in an empty input removes the last chip, Left moves into the chips, Backspace and Delete remove a chip.

#### Input OTP

```html
<div data-slot="input-otp" data-pattern="digits|chars|alphanumeric">
  <input maxlength="6" name="code" aria-label="One-time code">
  <div data-slot="input-otp-group"><div data-slot="input-otp-slot"></div></div>
  <div data-slot="input-otp-separator" role="separator"><svg data-lucide="minus"></svg></div>
</div>
```

One real input lies over the slots (autofill, form value, `required`, `minlength` stay native). The active empty slot shows `input-otp-caret` with an inner `div` (the blinking line). The kit gives the input the inline styles of the `input-otp` library (transparent text over the slots, `data-input-otp`) and the root `--root-height`. `aria-invalid="true"` on the input also marks every slot, as shadcn sets it on the slots. The pattern filters typed and pasted characters. Arrows move between slots; in RTL the slots run right to left and the kit moves the caret with the visual arrow (ArrowRight goes to the previous slot) in every engine.

#### Slider

```html
<div data-slot="slider" data-orientation="horizontal|vertical" data-large-step="10">
  <input type="range" min="0" max="100" step="5" value="25" name="min" aria-label="Minimum">
  <input type="range" min="0" max="100" step="5" value="75" name="max" aria-label="Maximum">
</div>
```

- One native range per thumb. The kit builds the Base UI DOM: `role="group"` on the root, a control `div`, `slider-track` with `slider-range`, and one `div` `slider-thumb` (`data-index`) around each range input. The input is visually hidden and keeps focus, form value, and `aria-valuenow`; two thumbs get `aria-valuetext` (`25 start range`, `75 end range`).
- Thumbs are inset to the control edges (Base UI `thumbAlignment="edge"`). Every part has `data-orientation`, `data-disabled` (all inputs disabled), and `data-dragging` while a pointer drags. The active thumb gets `z-index`.
- A press on the control moves the closest thumb (on a tie the last one) and drags it; a dragged thumb pushes the others. Keys: arrows (RTL aware), Shift+arrow and Page Up/Down by `data-large-step` (default 10, in value units), Home, End. Keys stop at the next thumb.
- Events: native `input` while the value changes, `change` on key press and on pointer release.
- Code changes: after `input.value = 80`, dispatch an `input` or `change` event; the kit then updates the thumb and `aria-valuenow`. `disabled`, `min`, `max`, and `step` changes on the inputs apply at once.

#### Toggle and Toggle Group

```html
<button type="button" data-slot="toggle" data-variant="outline" data-size="sm|lg" aria-pressed="false">Bold</button>
<div data-slot="toggle-group" data-type="single|multiple" data-variant="outline" data-size="sm" data-spacing="2|0|1|3|4|6|8" data-orientation="horizontal|vertical" data-value="bold,italic" data-name="format" data-required data-disabled>
  <button type="button" data-slot="toggle-group-item" data-value="bold" aria-label="Bold"><svg data-lucide="bold"></svg></button>
</div>
```

A `toggle` gets `tabindex="0"` like the Base UI toggle.

Toggle group: one tab stop, arrows (RTL aware), Home, End. A group is not labelable, so `<label for>` does not name it: give the `field-label` an `id` and the group `aria-labelledby` with it. Single items use `role="radio"` and `aria-checked`, multiple items `aria-pressed`. A pressed single item can be unpressed, as in shadcn.

- `data-required`: the last pressed item cannot be unpressed (a view switch, a filter, or a rating that always has one value), and in a form the group needs a value: without one, a `data-slot="form"` shows the `field-error` (`data-error-value-missing` on the group) and focuses the first item.
- `data-name` submits the value: a visually hidden input after the group (single), or one hidden input per value (multiple). `form.reset()` restores the authored value.
- `data-value` is the value (comma-separated for multiple). A later change from code presses those items without a `toggle-group:change` event. The kit does not write `data-value`; read the value from `toggle-group:change`. Like shadcn, the group gets `data-spacing` (default `2`, an 8 px gap with separate rounded items; `0` joins them) and `data-orientation` (default `horizontal`), and `--gap` from `data-spacing`. Items get the group `data-variant` and `data-size` (the group wins over the item; `default` when neither has one), its `data-spacing`, and `data-pressed` while pressed.

### Overlays and menus

The kit adds missing ARIA and decorations (close buttons, item indicators, sub-menu chevrons, the drawer handle, the tooltip arrow). Placement: `data-side`, `data-align`, `data-side-offset`, `data-align-offset` on the content.

Until the kit script runs, popup content without a `popover` attribute (`popover-content`, `hover-card-content`, `tooltip-content`, the `-content` and `-sub-content` of dropdown, context, and menubar menus, `select-content`, `combobox-content`) and a `navigation-menu-content` without `data-state` have `display: none` (`@media (scripting: enabled)`), so the page does not move when the script makes them popups. Without script they stay in the page flow.

Overlays inside a shadow root are not supported: event delegation and focus tracking see only the shadow host, so outside presses, focus traps, and Tab order do not work there. Put overlays in the light DOM.

The kit sets `type="button"` on dialog, alert dialog, sheet, drawer, popover, dropdown menu, menubar, and navigation menu triggers and on close, action, and cancel buttons (at init and again on click), so they never submit a form.

#### Dialog, Alert Dialog, Sheet, Drawer

```html
<div data-slot="dialog">
  <button type="button" data-slot="button" data-variant="outline" data-dialog-trigger>Open</button>
  <dialog data-slot="dialog-content">
    <div data-slot="dialog-header">
      <h2 data-slot="dialog-title">Edit profile</h2>
      <p data-slot="dialog-description">Make changes here.</p>
    </div>
    <div data-slot="dialog-footer">
      <button type="button" data-slot="button" data-variant="outline" data-dialog-close>Cancel</button>
    </div>
  </dialog>
</div>
```

- A dialog, alert dialog, or sheet is a native `<dialog>` opened with `showModal()`: focus trap, Escape, scroll lock, inert page, focus returns to the trigger. The first tabbable element gets the focus; a pointer open shows no focus ring on a button.
- A main-button click on `::backdrop` closes a dialog, sheet, or drawer, as Base UI (an alert dialog stays open): a held press closes after the release; a right or middle click, a press that starts or ends in the popup, and a touch drag do not close.
- Dialog and sheet add a close button unless `data-show-close-button="false"`. `<div data-slot="dialog-footer" data-show-close-button>` adds an outline Close button. A `<form method="dialog">` inside closes with an exit animation.
- Alert dialog: `data-size="sm"`, `alert-dialog-media`. The footer buttons are `<button data-slot="alert-dialog-cancel" data-variant="outline">` and `<button data-slot="alert-dialog-action">` (`data-variant="destructive"` for a red action), as in shadcn (`data-alert-dialog-cancel` and `data-alert-dialog-action` on a `button` part also work). Cancel closes it. The action is a plain button, as in shadcn: it does not close the dialog, so the app closes it with `dialogClose()` when its work is done, or the action gets `data-alert-dialog-close`. Like Base UI, the first tabbable element gets the initial focus (usually Cancel).
- Sheet: `data-side="top|right|bottom|left"` (default `right`). It opens with `data-starting-style` (set before `showModal()`, removed after one frame) and closes with `data-ending-style` until its transition ends, as Base UI; the backdrop follows the same attributes.
- Long dialog content: put the middle of the dialog in a `dialog-body` (kit part, like the shadcn `-mx-4 max-h-[50vh] overflow-y-auto px-4` wrapper of the Scrollable Content and Sticky Footer examples). The `dialog-content` is then a column of at most the window height less 2rem: the body takes the free space and scrolls, and the header and the footer stay in view. The body reaches the dialog edges with the scrollbar and has 4 px of padding at the top and the bottom for focus rings. A dialog without a body that is taller than the window scrolls as a whole (the kit gives `dialog-content` `max-height: calc(100dvh - 2rem)` and `overflow-y: auto`; in shadcn the top and the end of such a dialog are out of reach).
- Long sheet and drawer content does not scroll by itself, as in shadcn: put it in a `sheet-body` or `drawer-body` (kit parts, like the shadcn `flex-1 overflow-y-auto px-4` wrapper): it fills the space between the header and the footer, scrolls, and holds its children in a column with a 1.5rem gap.
- A form in a dialog, alert dialog, sheet, or drawer: put `<form data-slot="form">` (or a plain `<form>`) as the direct child of the content around the header, the body, and the footer. It is `display: contents`, so the parts keep the content layout (gap, sticky footer).

#### Drawer

```html
<div data-slot="drawer" data-swipe-direction="down" data-show-swipe-handle>
  <button type="button" data-slot="button" data-variant="outline" data-drawer-trigger>Open</button>
  <dialog data-slot="drawer-viewport">
    <div data-slot="drawer-popup">
      <div data-slot="drawer-content">
        <div data-slot="drawer-header">
          <h2 data-slot="drawer-title">Move Goal</h2>
          <p data-slot="drawer-description">Set your daily activity goal.</p>
        </div>
        <div data-slot="drawer-footer">
          <button type="button" data-slot="button" data-drawer-close>Submit</button>
        </div>
      </div>
    </div>
  </dialog>
</div>
```

- The Base UI drawer DOM: the viewport is the `<dialog>` and its `::backdrop` is the overlay; `drawer-popup` holds the optional `drawer-swipe-handle` (the kit adds it for `data-show-swipe-handle`) and `drawer-content` (`data-drawer-content`). A short form `<dialog data-slot="drawer-content">` with the parts inside is upgraded to this DOM on load.
- Root options as shadcn props: `data-swipe-direction="down|up|left|right"` (default `down`; the old `data-direction="bottom|top|left|right"` still works), `data-show-swipe-handle`, `data-modal="false"` (page stays usable, no backdrop) or `"trap-focus"` (focus trap only), `data-disable-pointer-dismissal` (an outside press, and for a non-modal drawer also focus leaving, does not close it). A non-modal drawer closes on a mouse click outside and at the end of a touch tap outside (or a touch drag outside of more than 10 px), as Base UI without a backdrop (the shadcn "Non Modal" example sets `disablePointerDismissal`).
- State as Base UI: `data-swipe-direction`, `data-swipe-axis="x|y"`, `data-swiping`, `data-swipe-dismiss`, `data-starting-style`, `data-ending-style`, and the variables `--drawer-swipe-movement-x`, `--drawer-swipe-movement-y`, `--drawer-swipe-progress`, `--drawer-swipe-strength`, `--nested-drawers` on the popup; `data-modal`, `data-nested`, `data-swiping`, `data-swipe-dismiss`, `--drawer-swipe-progress` on the viewport (for the backdrop). Opening focuses the popup.
- Swipe toward the edge to dismiss: on touch anywhere on the drawer, with a mouse or pen only outside `drawer-content` (the swipe handle), so text in the content stays selectable. It closes when it moved more than half its size or faster than 0.5 px/ms; the exit moves in `--drawer-swipe-strength` × 400 ms (0.1 to 1 from the release speed of the last move, with a 16 ms minimum sample time), while the hidden opacity transition keeps 400 ms, so the drawer closes and returns focus after 400 ms (Base UI 1.6.0 sets `data-ending-style` before the strength). Other directions are damped and spring back. A press or touch on the backdrop of a modal drawer starts the swipe when the pointer reaches the popup, and a main-button click on the backdrop (press and release there) closes the drawer, as Base UI. Buttons, links, and fields do not start a mouse swipe; `data-base-ui-swipe-ignore` (old `data-drawer-no-drag`) stops any swipe; a touch inside a scroller swipes only from its start edge.
- Snap points (vertical drawers): `data-snap-points="31rem 1"` on the root (space or comma list: a number up to 1 is a share of the window height, a larger number or `px` is pixels, `rem` is root ems), `data-snap-point` (the Base UI `defaultSnapPoint`: read at each open, first one when missing; a change while open does nothing), `data-snap-to-sequential-points`. The popup gets `data-snap-points`, `--drawer-snap-point-offset`, and `data-expanded` at the snap point `1`; the viewport gets `data-snap-points` (backdrop minimum 0.5). A swipe up or down settles on the nearest snap point after the release speed (above 0.5 px/ms it pushes 300 px per px/ms) or closes past the last one; `drawer:snap-point-change` `{ snapPoint }` fires on the root. Each open starts at the default snap point. A `ResizeObserver` keeps the snap offsets right after a resize or a rotation (a parent keeps its height while a nested drawer is open).
- Nested drawers: a drawer whose root is inside an open drawer opens on top of it, as Base UI. Its viewport moves out of the parent popup while it is open (into the parent viewport) and moves back when it closes, because the shadcn `group-data-*/drawer-popup` rules match every popup above it. While it is open: find the viewport with the trigger `aria-controls`; DOM events from inside it (`click`, `input`, `submit`, kit events) do not reach its own root or the elements between the root and the parent popup; CSS selectors through the root do not match; a `<form>` around the root does not contain its fields. `dialogOpen` and `dialogClose` still accept the root, the trigger, or an id. Closing a parent sends its `drawer:close` first; if no listener cancels it, the open nested drawers close, the deepest first (their `drawer:close` cannot be cancelled), then the parent. Parents get `data-nested-drawer-open`, `--nested-drawers` (open drawers above), `--drawer-height` (their own height), and `--drawer-frontmost-height`; during a swipe of the front drawer they get `data-nested-drawer-swiping` and its `--drawer-swipe-progress`. The nested drawer has `data-nested` and no visible backdrop, and a parent with an open nested drawer does not swipe.
- Changed with the move to Base UI (old → new): `dialog[data-slot=drawer-content]` → the viewport, popup, and content DOM (the old form is upgraded); `data-direction="bottom|top"` → `data-swipe-direction="down|up"`; `drawer-handle` (always) → `drawer-swipe-handle` with `data-show-swipe-handle` (an author-written handle stays); close threshold 25 % → 50 % or 0.5 px/ms; a mouse drag on the content no longer swipes; `drawer:close` reason `drag` → `swipe`; `data-drawer-no-drag` → `data-base-ui-swipe-ignore` (both work).
- While a modal dialog is open, the `toast-portal` element moves into the topmost open modal dialog (a modal makes everything else inert) and moves back when it closes, so toasts stay usable and Tab reaches them.

#### Popover

`popover` > `popover-trigger` (or `data-popover-trigger`), optional `popover-anchor`, `popover-content` with `popover-header`, `popover-title`, `popover-description`. Non-modal: focus moves into the content; Escape, outside click, and focus leaving close it. As in Base UI, a mouse press outside closes it on the click (a held press, a right or middle click, or a press that ends in the popup keep it open); a touch outside closes it at the end of the tap. `data-modal` on the root traps focus and locks scroll. Default placement: bottom, center, 4 px; the trigger has `data-pressed` while it is open.

Custom floating content (also linked from Tooltip), for example one readout for many small hover targets (a bar per day in an uptime row, where one tooltip per bar is too heavy): use the core `position()` with your own `popover="manual"` element. It places the element next to an anchor element or a virtual anchor (`{ getBoundingClientRect() }`), flips at the viewport edge, follows scroll and resize, and returns `stop()`. It sets `data-side`, `data-align`, and the `--anchor-*`, `--available-*`, and `--transform-origin` variables, as for kit popups ([Popups](#popups)). Dismissal and focus stay app code; for an interactive popup use `popover`.

```js
import { position } from "/vendor/clanker-ui/clanker-ui.min.js"

const tip = document.getElementById("day-tip")
let stop = null
grid.addEventListener("pointerover", event => {
  const bar = event.target.closest("[data-day]")
  if (!bar) return
  tip.textContent = bar.dataset.label
  if (!tip.matches(":popover-open")) tip.showPopover()
  stop?.()
  stop = position(tip, bar, { side: "top", sideOffset: 6 })
})
grid.addEventListener("pointerleave", () => {
  stop?.()
  stop = null
  tip.hidePopover()
})
```

#### Tooltip and Hover Card

`tooltip` > trigger (`tooltip-trigger` or `data-tooltip-trigger`) + `tooltip-content`. Timing is the shadcn setup (a `TooltipProvider` with `delay` 0 at the app root): `data-delay` (open, default 0), `data-close-delay` (default 0), and `data-timeout` (default 400) on the trigger, the root, or a `tooltip-provider` (`data-delay-duration` and `data-skip-delay-duration` also work). When a tooltip is open, or closed less than `data-timeout` ago, the next one opens at once. It opens on keyboard focus too; it closes on leave, Escape, press, and blur. Like Base UI, it stays open when the page scrolls and follows the trigger. A grace area lets the pointer move into the content. Touch never opens it. Default side `top`, 4 px; the kit adds the arrow (`<div data-slot="tooltip-arrow">`), which points at the trigger center. Like Base UI, the content and the arrow get `data-instant`: `delay` (opened at once because another tooltip was open or closed less than `data-timeout` ago), `focus` (opened by keyboard focus), `dismiss` (closed by Escape or a press).

Many small marks with their own readout (a bar per day in an uptime row): one tooltip per mark is too heavy. Use one `popover="manual"` readout placed with the core `position()` ([Popover](#popover) has the code). For the keyboard, make the row one Tab stop (`tabindex="0"`, `role="group"`, an `aria-label` with the summary): Left and Right move a current mark, place the readout on it, and write the same text into a visually hidden `role="status"` element; Escape hides it.

`hover-card` > trigger + `hover-card-content`. `data-delay` (600) and `data-close-delay` (300) on the trigger or the root (`data-open-delay` also works), the Base UI defaults; shadcn examples set `data-delay="10" data-close-delay="100"`. Placement: bottom, center, 4 px, `alignOffset` 4. Opens on hover and keyboard focus, never on touch. It closes at once when focus leaves the trigger and the card (Base UI); the close delay is for the pointer. A card that focus opened stays open when the pointer leaves the card or a press in it moves focus away, as in Base UI; it closes when the pointer leaves the trigger.

#### Dropdown Menu, Context Menu, Menubar

```html
<div data-slot="dropdown-menu">
  <button type="button" data-slot="button" data-variant="outline" data-dropdown-menu-trigger>Open</button>
  <div data-slot="dropdown-menu-content" data-side="bottom" data-align="end">
    <div data-slot="dropdown-menu-group">
      <div data-slot="dropdown-menu-label">My Account</div>
      <div data-slot="dropdown-menu-item">Profile<span data-slot="dropdown-menu-shortcut">⇧⌘P</span></div>
      <div data-slot="dropdown-menu-checkbox-item" data-checked>Status Bar</div>
    </div>
    <div data-slot="dropdown-menu-radio-group" data-value="top">
      <div data-slot="dropdown-menu-radio-item" data-value="top" data-checked>Top</div>
    </div>
    <div data-slot="dropdown-menu-separator"></div>
    <div data-slot="dropdown-menu-sub">
      <div data-slot="dropdown-menu-sub-trigger">Invite users</div>
      <div data-slot="dropdown-menu-sub-content">...</div>
    </div>
  </div>
</div>
```

- Same parts with the `context-menu-` and `menubar-` prefixes, plus `-group`, `-radio-group`, and `-label` (`menubar-label` too). Items: `data-disabled`, `data-inset`, `data-variant="destructive"` (other items get `data-variant="default"`), `data-value`, `data-text-value` (typeahead label), `data-close-on-click`. Checkbox and radio items: `data-checked` (or `data-state="checked"`). `data-value` on a radio group selects the item with that value. A later change of `data-value` on the radio group or of `data-checked` on an item, from code, updates the items (no event). Links work as items.
- Base UI DOM and states: a label gets `role="presentation"` and names its group (`aria-labelledby`); a separator gets `data-orientation="horizontal"`; checkbox and radio items get `data-checked` or `data-unchecked` and an indicator as the first child (`dropdown-menu-checkbox-item-indicator`, `dropdown-menu-radio-item-indicator`; a `span` without a slot in context menus and menubars) that holds `<span data-checked aria-hidden="true">` with the `check` icon only while checked. The highlighted item has `data-highlighted`; an open sub menu's trigger has `data-popup-open` and loses `data-highlighted` while focus or the pointer is in the sub menu. The content has `data-open` or `data-closed`, `data-side`, `data-align`, and `data-instant` (`click` when a keyboard key or a right click opened it, `group` when a menubar switched menus, `dismiss` after Escape); the trigger has `data-popup-open` and `data-pressed` while open.
- `dropdown-menu:change` and `:select` are emitted on the `dropdown-menu` root (also for an item in a sub menu or a radio group) and bubble to `document`; a listener on the radio group gets nothing. `detail.group` is the radio group element (`dropdown-menu-radio-group`, `null` outside a group; it is absent for a checkbox item): read `event.detail.group.id` or `.dataset` to tell two groups apart, and `detail.value` for the new value (the group `data-value` is already set).
- A plain item closes the menu; checkbox and radio items keep it open (Base UI `closeOnClick`), unless `data-close-on-click` says otherwise.
- Like Base UI, menus are modal (`data-modal="false"` on the root or `menubar` turns this off): page scroll is locked, and the first press outside only closes the menu (the click does not reach the element below, and focus returns to the trigger). A touch outside closes it when the tap ends, or during a drag of more than 10 px.
- A mouse press on the trigger opens the menu; release over an item to choose it (press, drag, release). Placement: dropdown bottom, start, 4 px; context menu at the pointer, right, start, `alignOffset` 4; menubar bottom, start, 8 px, `alignOffset` -4; sub menus right, start, `alignOffset` -3 (context menu 4); 5 px from the viewport edge.
- Keyboard per WAI-ARIA APG with Base UI focus looping: Enter, Space, and ArrowDown open at the first item, ArrowUp at the last; arrows wrap from the last item to the first and back, Home, End, typeahead; arrows also stop on disabled items (highlighted, `aria-disabled`, they do not run), as in Base UI; ArrowRight opens a sub menu, ArrowLeft closes it (mirrored in RTL); Escape closes the innermost menu; Tab closes all. Typeahead continues across a space (`New W` reaches "New Window"); Space activates the item only when no typeahead is in progress.
- A sub menu opens 100 ms after the pointer rests on its trigger. On the way to the sub menu the pointer may cross other items inside the triangle from the pointer to the sub menu (Base UI safe polygon). The sub menu closes when the pointer leaves the trigger on the side away from the sub menu, leaves the triangle, moves slower than 0.1 px/ms, or stops for 40 ms; then the menu keeps focus with no highlight until the pointer moves again.
- A trigger click runs app `click` listeners as usual, also when a mouse press already opened the menu.
- A menu item that opens a dialog (`data-dialog-trigger="id"`) returns focus to the menu trigger when the dialog closes.
- Context menu: `context-menu-trigger` is the area (give it `tabindex="0"`). Right click, long press (700 ms), Shift+F10, or the ContextMenu key open it.
- Menubar: `menubar` > `menubar-menu` > `menubar-trigger` + `menubar-content`. The bar gets `aria-orientation`, `data-orientation="horizontal"`, and `data-modal`. Roving focus; ArrowLeft and ArrowRight in an open menu open the next menu and focus its popup (no item highlighted; ArrowDown goes to the first item); while a menu is open, hover switches menus and moves focus to the new menu (the old menu closes 45 ms later, as Base UI closes it after the new menu renders); a click on another trigger while a menu is open, or on the open trigger, closes the menus and focuses that trigger. An outside press closes the menu and returns focus to the trigger, as in other modal menus.

#### Navigation Menu

`nav[data-slot="navigation-menu"]` > `navigation-menu-list` > `navigation-menu-item` > `navigation-menu-trigger` + `navigation-menu-content`, or a `navigation-menu-link` (`data-variant="trigger"`, `data-active`, `data-close-on-click`). Optional `navigation-menu-indicator`. The app sets only `data-active` on the current link; the kit keeps `aria-current="page"` in sync, also when `data-active` changes later.

- The kit adds the Base UI parts at the end of the root: `navigation-menu-positioner` (a top-layer popup at the open trigger: bottom, `data-align` of the root or `start`, 8 px) > `nav[data-slot="navigation-menu-popup"]` > `navigation-menu-viewport`. The open content moves into the viewport and back to its item when it closes. `data-viewport="false"` places each content under its trigger instead (8 px).
- States as in Base UI: root and list `data-open`; trigger `data-popup-open` and `aria-expanded`; positioner and popup `data-open`/`data-closed`, `data-side`, `data-align`; content `data-open`/`data-closed`, `data-starting-style`/`data-ending-style`, and `data-activation-direction` (`right` when the new item comes after the old one in the list, `left` before; logical, so the motion follows RTL). The positioner has `data-instant` on the first open (no slide), `--positioner-width`/`--positioner-height`, and the popup `--popup-width`/`--popup-height`: when the panel changes, the popup animates from the old size to the new one, the positioner slides to the new trigger, and the old content leaves (absolute, `data-ending-style`) while the new one enters.
- Hover opens after 50 ms and closes 50 ms after the pointer leaves (`data-delay`, `data-close-delay` on the root); a switch to another panel waits for the same delay; a click toggles. The open trigger has `data-pressed`. Enter, Space, or ArrowDown on a closed trigger opens it and focuses the first link in the panel; ArrowDown or Tab on an open trigger enters the panel; Home and End do nothing (the page scrolls), as in Base UI; Tab after its last link goes to the next trigger, Shift+Tab from its first link goes back and Shift+Tab from the next trigger goes to its last link (focus guards at both ends of the popup and after the open trigger, as in Base UI, so this also works in Safari, where Tab skips links; Tab from the last trigger leaves the menu); arrows move between links; Escape closes and focuses the open trigger, also when a hover switch moved the open panel. The positioner follows the size of the open content (`ResizeObserver`); sizes are layout sizes, so a scale animation does not shrink them. A link click keeps the menu open (Base UI `closeOnClick` is false) unless the link has `data-close-on-click`. A menu removed while open comes back closed.
- An outside press closes the menu on the click, as in Base UI (a held press, a right or middle click, or a touch drag keep it open). Only a menu that hover opened closes when the pointer leaves; a menu opened by a click or a key stays open, and so does a menu where a press on a link starts a drag.

#### Command

`command` > `command-input`, `command-list` > `command-empty`, `command-group` (`data-heading` or a `command-group-heading` child) > `command-item` (`data-value`, `data-keywords="a, b"`, `data-disabled`) with `command-shortcut`; `command-separator`. Typing filters, scores, and sorts; ArrowUp/Down, Home, End, Ctrl+N/J/P/K, Alt+arrows (next group), Meta+arrows (first/last), Enter. `data-loop` wraps, `data-should-filter="false"` disables filtering. The kit builds the shadcn input DOM (`command-input-wrapper` > `input-group` > the input + `input-group-addon` with the search icon), gives group headings the cmdk `cmdk-group-heading` attribute, and appends the shadcn `check` icon to each item (shown with `data-checked="true"`, hidden when the item has a shortcut). Inside a `dialog-content` it becomes the command dialog: the content gets `data-command-dialog` and no close button unless `data-show-close-button="true"`. The list has `tabindex="-1"`, so a pointer press on an item moves focus to the list (as in cmdk) and the keys keep working there; the input and the list carry `aria-activedescendant` of the selected item. Items inserted later get `role="option"`, an id, and their disabled state; the empty state and the selection follow. `data-disabled` in any form except `"false"` disables an item.

#### Toast and Sonner

```js
toast.add({ title: "Event created", description: "Sunday at 9:00", type: "success", timeout: 5000, priority: "low", actionProps: { children: "Undo", onClick() {} } })
toast.update(id, { description: "Saved" }); toast.update(id, prev => ({ title: `${prev.title}!` })); toast.close(id); toast.close()
toast("Event created", { description: "Sunday at 9:00", action: { label: "Undo", onClick() {} } })
toast.success(title, opts); toast.info(); toast.warning(); toast.error(); toast.loading(); toast.message()
toast.promise(promiseOrFn, { loading: "Creating event…", success: data => `${data.name} created.`, error: "Could not create event.", finally })
toast.dismiss(id); toast.dismiss(); toast.getToasts()
```

- The Base UI toast DOM (shadcn base `sonner` redirects to `toast`): `<div data-slot="toast-portal">` (created on load if missing) > `toast-viewport` (`role="region"`, `aria-live="polite"`, a manual popover in the top layer, open only while a toast shows, so a new toast shows above popups that opened before it) > `toast` (`role="dialog"`, `alertdialog` for `priority: "high"`) > `toast-content` > `toast-icon`, a `div` with `h2` `toast-title` and `p` `toast-description`, `toast-action`, `toast-close`. Every toast has the close button, like shadcn.
- `toast.add`, `toast.update`, `toast.close`, and `toast.promise` follow the Base UI manager. A string in `toast.promise` is the description; an object is the full options. `toast.add` with an existing `id` updates that toast and restarts its timer. `actionProps` (`children`, `onClick`) do not close the toast; call `toast.close(id)`.
- Kit calls: `toast(message, options)` and the typed variants put `message` in the title. Options: `id`, `title`, `description`, `type` (`success|info|warning|error|loading` show an icon), `timeout` (ms, `0` keeps it) or `duration` (`Infinity` keeps it), `priority` (`high` announces the toast at once in a hidden `role="alert"` region), `action` (`{ label, onClick }`, closes the toast unless `onClick` calls `event.preventDefault()`), `actionProps`, `icon` (Lucide name, node, or `null`), `className`, `onClose`, `onRemove`, `onDismiss`, `onAutoClose`. An unknown `icon` name throws before any state changes. `toast.promise` returns the id.
- Changed with the move to Base UI (old → new):
  - removed: `position`, `cancel` and the `toast:cancel` event, `closeButton`, `closeButtonAriaLabel`, `richColors`, `invert`, `dismissible`, Alt+T (F6 now). Move the viewport with app CSS on `[data-slot="toast-viewport"]` if needed.
  - `<section data-slot="sonner">` → `<div data-slot="toast-portal">`; `data-duration` → `data-timeout`; `data-visible-toasts` → `data-limit`; the other `sonner` attributes are gone.
  - default timeout 4000 ms → 5000 ms; the close button shows on every toast; the action closes the toast as before, `actionProps` do not.
  - a string in `toast.promise` was the title and is now the description; `toast.promise` without `loading` showed no toast and now shows an empty loading toast.
- `<div data-slot="toast-portal" data-limit="3" data-timeout="5000">` sets the limit and the default timeout. Toasts over the limit stay mounted with `data-limited` and `inert` (hidden) until a slot is free.
- State attributes as Base UI: `data-type`, `data-expanded` (viewport, toast, content), `data-behind` (content of toasts behind the front one), `data-limited`, `data-swiping`, `data-swipe-direction`, `data-starting-style`, `data-ending-style`; variables `--toast-index`, `--toast-offset-y`, `--toast-height`, `--toast-swipe-movement-x`, `--toast-swipe-movement-y`, and `--toast-frontmost-height` on the viewport.
- The stack expands while the pointer is over it or a toast has keyboard focus. Timers pause on hover, on keyboard focus, during a touch press, and while the window has no focus; a hidden page does not pause them (Base UI 1.6.0 has no `visibilitychange` handler). As in Base UI 1.6.0, the version shadcn uses, a pause sets the time left to the full timeout less the time since the last start or resume, so a toast that is hovered again runs longer. Later Base UI versions count the time left again; change this when the pinned version moves. A hover that ends during an exit animation applies after it. Swipe down or right more than 40 px to dismiss; other directions are damped and spring back. F6 moves focus to the viewport; Tab and Shift+Tab past the toasts return focus to where it was. Escape closes the focused toast (not an open dialog), and focus moves to the next toast.

### Layout and display

#### Accordion

```html
<div data-slot="accordion" data-type="single|multiple">
  <div data-slot="accordion-item" data-value="shipping" data-state="open">
    <h3><button type="button" data-slot="accordion-trigger">What are your shipping options?</button></h3>
    <div data-slot="accordion-content"><div>Standard, express, and overnight.</div></div>
  </div>
  <div data-slot="accordion-item" data-value="returns">
    <h3><button type="button" data-slot="accordion-trigger">What is your return policy?</button></h3>
    <div data-slot="accordion-content" hidden="until-found"><div>Returns within 30 days.</div></div>
  </div>
</div>
```

The Base UI DOM: a heading with the trigger button, and a panel with one inner `div` (the padding is on it). `data-type="single|multiple"`, `data-state="open"` on an item that starts open, `hidden="until-found"` on the panel of an item that starts closed (so the page does not move when the module loads), `data-disabled` on an item. Like Base UI, a single accordion can close its open item, so all items can be closed. The kit adds the two chevrons (`accordion-trigger-icon`, down when closed, up when open), ids, `aria-expanded`, `aria-controls`, `role="region"`, `aria-labelledby`, `data-open`, `data-closed`, `data-state`, `data-panel-open` on the trigger, and `data-index`. A closed panel has `hidden="until-found"`, so find in page opens its item (`beforematch`). The panel animates with `--accordion-panel-height` (`auto` after the open animation). Keys: Enter and Space toggle; as in Base UI, the arrow keys do not move focus. Like Base UI, the trigger of a disabled item stays in the Tab order (`aria-disabled="true"`), and Enter, Space, or a click does not open it. Event: `accordion:change` `{ value }`.

A count or status in a trigger: a `badge` after the text (`<button type="button" data-slot="accordion-trigger">Payments<span data-slot="badge" data-variant="warning"><svg data-lucide="triangle-alert"></svg>Degraded</span></button>`) sits at the end, before the chevron, centered on the text.

#### Alert, Aspect Ratio, Badge, Card, Empty, Item, Separator, Skeleton

- `alert` (`role="alert"`, `data-variant="destructive"`) with an optional leading `<svg>`, `alert-title`, `alert-description`, `alert-action`. As in shadcn, the action sits at the top end and the alert keeps 72 px free for it; a wider action ("View incident") gets its own width plus 12 px, so the title and the description never go under it.
- Kit extension to shadcn: `data-variant="success|warning|info"` on `alert` and `badge`. CSS only. Border, background, and text use the status tokens (see [CSS rules for components](#css-rules-for-components)); the alert description uses `--foreground`. A status `<a data-slot="badge">` shows an underline on hover.
- `<div data-slot="aspect-ratio" data-ratio="16/9">` (any ratio, `"4/3"`, `"2.4"`): the kit sets `--ratio`, like shadcn. Children are not positioned; give an image `position: absolute; inset: 0; width: 100%; height: 100%` (the shadcn examples use `fill`).
- `badge` (`data-variant="secondary|destructive|outline|ghost|link"`, or `<a data-slot="badge">`). Icons and spinners inside are 12 px.
- `card` with `card-header` (`card-title`, `card-description`, `card-action`), `card-content`, `card-footer`. `data-size="sm"`; override `--card-spacing`. A first-child `<img>` sits flush with the top. Kit extension: `data-orientation="horizontal"` puts a first-child `cover` (6rem, 8rem from 48rem) at the start and the other parts in a `div` column next to it, with a wrapping `card-footer` (a hero or feature card: art left, text and actions right).
- `empty` with `empty-header` (`empty-icon` with `data-variant="icon"`, `empty-title`, `empty-description`) and `empty-content`. Kit extension: `data-variant="outline"` adds the 1 px dashed border.
- `item` (`data-variant="outline|muted"`, `data-size="sm|xs"`, or `<a data-slot="item">`) with `item-media` (`data-variant="icon|image"`), `item-content` (`item-title`, `item-description`), `item-actions`, `item-header`, `item-footer`; `item-group` (`role="list"`) and `item-separator`. As in shadcn, `item-title` is one line and `item-description` at most two lines (`line-clamp`): give a cut text a `title`, or for long text (a timeline update) use a `p` in `item-content`, not `item-description`. A `cover` in `item-media` is 40 px wide (32 px in a `sm` item, 24 px in `xs`) with its ratio and without its text; in `data-variant="image"` it fills the square. `item-group` has a 16 px gap and `item-separator` adds 8 px above and below: in a list with separators set the group gap to 0 in app CSS (`.list { gap: 0 }`), so the rows are as close as without them. Below 40rem, `item-actions` with a text button (not an `icon` size button, a switch, or a badge) goes to its own line under the content.
- `separator` (`data-orientation="vertical"`): decorative (`role="none"`) unless you add `role="separator"`.
- `skeleton`, sized by app CSS.

#### Avatar

```html
<span data-slot="avatar" data-size="sm|lg">
  <img data-slot="avatar-image" src="..." alt="">
  <span data-slot="avatar-fallback">CN</span>
  <span data-slot="avatar-badge"></span>
</span>
```

The fallback shows until the image loads and stays when it fails (`data-status="loading|loaded|error"` on the image). Base UI renders only one of them; the kit hides the other with `visibility: hidden`. Put the image before the fallback, as shadcn does. `avatar-group` stacks avatars; `avatar-group-count` shows the rest.

#### Breadcrumb

```html
<nav data-slot="breadcrumb">
  <ol data-slot="breadcrumb-list">
    <li data-slot="breadcrumb-item"><a data-slot="breadcrumb-link" href="/">Home</a></li>
    <li data-slot="breadcrumb-separator"></li>
    <li data-slot="breadcrumb-item"><span data-slot="breadcrumb-ellipsis"></span></li>
    <li data-slot="breadcrumb-item"><span data-slot="breadcrumb-page">Breadcrumb</span></li>
  </ol>
</nav>
```

The kit adds `aria-label`, the chevron in an empty separator, the ellipsis icon with "More", and `aria-current="page"`. Put a `dropdown-menu` in an item for a menu; an ellipsis inside a button takes the button size.

#### Carousel

```html
<div data-slot="carousel" data-orientation="horizontal|vertical" data-align="start|center|end" data-loop aria-label="Featured">
  <div data-slot="carousel-content"><div>
    <div data-slot="carousel-item">...</div>
  </div></div>
  <button data-slot="carousel-previous"></button>
  <button data-slot="carousel-next"></button>
</div>
```

The inner `div` is the track; set item width with `flex-basis`. The kit adds the carousel and slide roles, slide labels, the arrow icons, and disables a button at the end (`disabled`, `data-disabled`). Like shadcn, focus does not move when the focused button becomes disabled, so Tab continues to the other button. The motion is a port of Embla 8, the engine of the shadcn carousel, with its default options: the track moves with `transform`, `data-align` sets the slide alignment (default `center`, like Embla; the shadcn size and orientation examples use `start`), and `data-loop` loops the slides (as Embla, only when there are enough slides to fill the view). The buttons and the arrow keys (RTL aware) move one slide with duration 25 and friction 0.68 (about 750 ms; at once with reduced motion); a press during the motion changes its target. A mouse drag or a touch swipe moves the track with the pointer. On release, the speed is multiplied by 300 for the mouse or 400 for touch; a release force over 20 % of the view (limited to 50 to 225 px) goes to the next or previous slide, and a smaller force snaps to the nearest slide. Past the first or last slide the track resists and springs back (at once with reduced motion). A drag over 10 px cancels the click that follows. A touch swipe that starts more vertical than horizontal is left to the page. Tab into a slide jumps to it at once. The carousel measures again, as Embla `reInit` does, when its size or its slides change, when `data-orientation`, `data-align`, or `data-loop` changes, and when a `dir` change gives it another direction; it keeps the selected snap. The kit sets `transform` inline on the track and on looped slides, so app CSS `transform` on these parts has no effect. `carousel:change` (`value`: the selected snap index, `count`: the number of snaps, which is less than the slides when several slides fit in the view) fires once after the carousel starts (like the Embla `init` event), when the selected snap changes, and after a new measure that changes the index or the count. Like the shadcn carousel, the mouse wheel does not move the slides (no wheel plugin). Not built: autoplay and other plugins.

#### Collapsible

```html
<details data-slot="collapsible">
  <summary data-slot="collapsible-trigger">Advanced settings</summary>
  <div data-slot="collapsible-content">...</div>
</details>

<div data-slot="collapsible" data-state="closed">
  <button type="button" data-slot="button" data-variant="ghost" data-size="icon-sm" data-collapsible-trigger>...</button>
  <div>Always visible</div>
  <div data-slot="collapsible-content" hidden>...</div>
</div>
```

Use `<details>` when the trigger comes first; use a `<div>` root when content around the trigger must stay visible. A trigger with a button look is `data-slot="button"` with `data-collapsible-trigger`. `data-disabled` on the root. Like shadcn, the content shows and hides at once (no motion).

#### Direction

Set `dir="rtl"` on `<html>` or a container. Kit styles use logical properties (`inset-inline`, `margin-inline`, `padding-inline`, `border-inline`, `text-align: start`) for everything that follows the reading direction; icons that point along the reading direction flip with `:dir(rtl)`; keyboard arrows follow the visual direction.

- Physical sides stay where a value names one: sheet `data-side`, drawer `data-swipe-direction`, popup `data-side="left|right"`, toast swipe directions, and parts that JavaScript places (popups, the tooltip arrow, the slider thumb, the chart tooltip).
- Sidebar `data-side="left|right"` means inline start and inline end: in RTL a `left` sidebar sits on the right, and its rail, border, collapsed tooltip, inset margin, and mobile sheet follow.
- The questionnaire keeps the upstream keys in RTL (ArrowLeft goes to the previous item).
- Chart plots stay left to right (`direction: ltr` on the SVG, like Recharts), so labels and negative numbers read the same in every page; the legend, table, and tooltip follow the page direction. In a vertical bar, line, or area chart in RTL the category axis is reversed (the first category at the right) and the value axis is on the right, like the shadcn `chart-rtl` example (Recharts `reversed`); ArrowLeft moves to the next category, as in Recharts. Horizontal bar charts and sparklines keep the left-to-right layout.

#### Pagination

```html
<nav data-slot="pagination" aria-label="pagination">
  <ul data-slot="pagination-content">
    <li data-slot="pagination-item"><a data-slot="pagination-link" data-pagination-previous data-size="default" href="?p=1" aria-label="Go to previous page"><svg data-lucide="chevron-left" data-icon="inline-start"></svg><span>Previous</span></a></li>
    <li data-slot="pagination-item"><a data-slot="pagination-link" href="?p=1">1</a></li>
    <li data-slot="pagination-item"><a data-slot="pagination-link" data-variant="outline" href="?p=2" data-active aria-current="page">2</a></li>
    <li data-slot="pagination-item"><span data-slot="pagination-ellipsis" aria-hidden="true"><svg data-lucide="ellipsis"></svg><span class="sr-only">More pages</span></span></li>
    <li data-slot="pagination-item"><a data-slot="pagination-link" data-pagination-next data-size="default" href="?p=3" aria-label="Go to next page"><span>Next</span><svg data-lucide="chevron-right" data-icon="inline-end"></svg></a></li>
  </ul>
</nav>
```

The markup is the shadcn DOM: a link is a `ghost` button of size `icon` (32 px); the current page is `data-variant="outline"` with `aria-current="page"`. `data-pagination-previous` and `data-pagination-next` with `data-size="default"` mark Previous and Next; their text hides below 640 px and their chevrons turn in RTL.

Use `pagination` for pages of content (search results, a blog, a gallery) where each page has its own URL. A table uses the `data-table-pagination` row (rows per page, "Page 1 of 7", icon buttons), as in the shadcn tasks example.

Disabled Previous or Next (first or last page): `aria-disabled="true"` on the link, and remove its `href` so it is not a Tab stop. The link is dimmed (opacity 0.5) and takes no pointer events, like a disabled button; the kit also cancels a click on it, so a link that keeps its `href` does not navigate.

#### Progress, Spinner

- `<div data-slot="progress" data-value="60" data-max="100" aria-label="Upload"></div>`: the kit adds the Base UI parts `progress-track` > `progress-indicator` (width in percent), `role="progressbar"`, `aria-valuenow`, `aria-valuetext`, `data-state="loading|complete|indeterminate"`, and `data-progressing`, `data-complete`, or `data-indeterminate` on every part. Optional `progress-label` (it labels the bar) and `progress-value` (the kit writes the percent) go before the track. The percent in `progress-value` and `aria-valuetext` is `Intl.NumberFormat` with `style: "percent"` in the language of the nearest `lang` attribute, like Base UI `Progress.Value`. The digits follow the browser locale data: `lang="ar-u-nu-arab"` gives Arabic-Indic digits (`٥٦٪؜`) in every browser. Change `data-value` to update it. At 0 and when indeterminate, the indicator has no width.
- `<svg data-slot="spinner" data-size="sm|lg|xl"></svg>` (sizes are a kit extension: 12, 24, 32 px; default 16 px): the kit fills the icon and adds `role="status"` and `aria-label="Loading"` (`strings.loading`). Use `role="none"` for a decorative spinner in a labelled control. Spinners keep turning under reduced motion.

#### Resizable

```html
<div data-slot="resizable-panel-group" data-orientation="horizontal|vertical">
  <div data-slot="resizable-panel" data-default-size="25" data-min-size="15" data-max-size="60">...</div>
  <div data-slot="resizable-handle" data-with-handle></div>
  <div data-slot="resizable-panel">...</div>
</div>
```

Sizes are percentages. The handle is a WAI-ARIA window splitter: drag it or use the arrow keys (`data-keyboard-step`, default 5), Home, and End. `data-orientation="vertical"` stacks the panels; `data-with-handle` adds the shadcn grip (an empty `div`, a 4 × 24 px pill). Not built: collapsible panels and saved layouts.

#### Scroll Area

```html
<div data-slot="scroll-area">
  <div data-slot="scroll-area-viewport" aria-label="Tags">...</div>
  <div data-slot="scroll-area-scrollbar" data-orientation="horizontal"></div>
</div>
```

The viewport is the real scroll container; the kit makes it focusable, hides the native scrollbars, and adds a vertical scrollbar with a draggable thumb. Like Base UI, a scrollbar shows while its content overflows and is hidden without overflow; it has `data-orientation` (also on the thumb), `data-hovering` while the pointer is over the scroll area, and `data-scrolling` while its own axis scrolls or its thumb is dragged. A click on the track centers the thumb at the pointer with the Base UI formula (it subtracts the scrollbar padding); a press on the scrollbar does not keep focus in the viewport.

#### Sidebar

```html
<div data-slot="sidebar-wrapper" id="app">
  <div data-slot="sidebar" data-side="left" data-variant="sidebar|floating|inset" data-collapsible="offcanvas|icon|none">
    <div data-slot="sidebar-gap"></div>
    <div data-slot="sidebar-container">
      <div data-slot="sidebar-inner">
        <div data-slot="sidebar-header">...</div>
        <div data-slot="sidebar-content">
          <div data-slot="sidebar-group">
            <div data-slot="sidebar-group-label">Platform</div>
            <ul data-slot="sidebar-menu">
              <li data-slot="sidebar-menu-item">
                <a data-slot="sidebar-menu-button" data-active="true" data-tooltip="Home" href="/"><svg data-lucide="house"></svg><span>Home</span></a>
                <div data-slot="sidebar-menu-badge">24</div>
              </li>
            </ul>
          </div>
        </div>
        <div data-slot="sidebar-footer">...</div>
      </div>
      <button data-slot="sidebar-rail"></button>
    </div>
  </div>
  <main data-slot="sidebar-inset"><button data-slot="sidebar-trigger"></button>...</main>
</div>
```

- Parts: `sidebar-group-action`, `sidebar-group-content`, `sidebar-menu-button` (`data-variant="outline"`, `data-size="sm|lg"`, `data-active`), `sidebar-menu-action` (`data-show-on-hover`), `sidebar-menu-skeleton` (`data-show-icon`), `sidebar-menu-sub`, `sidebar-menu-sub-item`, `sidebar-menu-sub-button`, `sidebar-input`, `sidebar-separator`.
- A trigger controls the sidebar in its wrapper, or the one named by `aria-controls`. Ctrl/⌘+B toggles the sidebar of the focused wrapper, else the first one. The state is stored in `localStorage["sidebar_state:<wrapper id>"]`.
- In icon mode, collapsed menu buttons with `data-tooltip` show a `tooltip-content`. Below 768 px the sidebar is a modal sheet (`data-mobile="open"`). When Escape, a trigger, or Ctrl/⌘+B closes the sheet, focus goes back to the element that had focus when it opened (the trigger, when the trigger opened it). An outside click closes it and does not move focus back.
- `data-side="left|right"` is inline start and inline end (see [Direction](#direction)). The kit copies it to `sidebar-container`, like shadcn, and sets `--sidebar-width: 16rem` and `--sidebar-width-icon: 3rem` on the wrapper.
- The mobile sheet is the `sidebar` root, like the shadcn mobile sidebar (a sheet): 75 % of the viewport wide, at most 24rem, at the inline-start side. While it is open, the kit shows it in the top layer (`popover="manual"`) above a `sheet-overlay` element that it adds before the root: the overlay covers the viewport with `rgb(0 0 0 / 0.1)` and a 4 px blur, and a click on it closes the sheet. The sheet fades in from 2.5rem with `data-starting-style` and out with `data-ending-style` (200 ms); the overlay fades in 150 ms. The kit removes the overlay when the sheet is closed.

#### Table

`table-container` > `table` > `table-caption`, `table-header`, `table-body`, `table-footer`, `table-row` (`data-state="selected"`), `table-head`, `table-cell`. Sorting, filtering, selection, column visibility, and paging are app code; the demo builds a data table with `h()`, `aria-sort`, a row actions `dropdown-menu`, a column `dropdown-menu`, and `toast`.

#### Tabs

```html
<div data-slot="tabs" data-default-value="account" data-orientation="horizontal|vertical">
  <div data-slot="tabs-list" data-variant="line">
    <button data-slot="tabs-trigger" data-value="account">Account</button>
  </div>
  <div data-slot="tabs-content" data-value="account">...</div>
</div>
```

```html
<div data-slot="tabs" data-value="password">...</div>
```

Set the tab from code with `data-value` on the root (`tabs.dataset.value = "password"`): the kit selects that tab without a `tabs:change` event, as for a select. A root with `data-value` keeps it in sync when the user picks a tab, and `data-value` in the markup wins over `data-default-value`. A value that no trigger has changes nothing.

Keep a tab bar short enough for 390 px: when it scrolls, the cut last label has no other sign. With more tabs, put a `select` with the same choices next to the list, as shadcn `dashboard-01` does: `data-hide-from="sm"` on the select and `data-show-from="sm"` on the `tabs-list`; or use fewer and shorter labels. A `tabs-content` without `data-value` is a shared panel: it shows for every tab and is labelled by the selected tab. Use it for a tab bar that filters one list or table: render the rows on `tabs:change`. A filter with no panel at all is a toggle group (`data-type="single" data-required`), not tabs.

Manual activation as in Base UI: the arrow keys move focus, Enter, Space, or a click selects (`data-activation="automatic"` selects on focus), roving tabindex, arrows (RTL aware), Home, End; disabled tabs are skipped. Tab panels are focusable (`tabindex="0"`) and show the standard focus ring.

A horizontal `tabs-list` is never wider than the root: when the triggers do not fit, the list scrolls horizontally without a scrollbar, and the triggers keep their width. The selected trigger scrolls fully into view at load, when the list becomes visible, and when the list changes size. A trigger that gets keyboard focus (arrow keys, Home, End, Tab) or a click also scrolls fully into view. Only the list scrolls, also in a scaled container. The kit hides the old panel before `tabs:change`. In the handler, render only the new panel, not the whole tabs root: a new root makes the page jump. The kit measures the list before it changes the tab and reads no layout after `tabs:change`, so an app can fill the new panel in the same task (for example in a microtask) and the page does not jump. A fill in a later task (fetch, timer) can still change the page height. App CSS that makes the selected trigger wider than the others can leave part of it hidden, because the kit measures before the change. The kit sets `tabindex="-1"` on a horizontal list that has no `tabindex`, so the list is not a Tab stop (Firefox stops on a scroll container). The horizontal root has `min-width: 0`, so a long list does not widen a grid or flex parent. Vertical tabs do not scroll.

### Chat and calendar

Scrollable parts (`attachment-group`, `code-block-content`, `message-scroller-viewport`) fade the edges they can scroll toward. The fade is CSS only (shadcn `scroll-fade-*`): a scroll-driven animation sets `--scroll-fade-s`, `--scroll-fade-e`, `--scroll-fade-t`, `--scroll-fade-b`; a browser without scroll timelines (Firefox) shows a static fade on both edges, as on ui.shadcn.com. The kit sets the attributes that shadcn always renders when they are missing: `message` `data-align="start"`, `bubble` `data-variant="default" data-align="start"`, `bubble-reactions` `data-align="end" data-side="bottom"`, `marker` `data-variant="default"`, `attachment` `data-state="done" data-size="default" data-orientation="horizontal"`, `attachment-media` `data-variant="icon"`, `code-block` `data-variant="default" data-size="default"`, `aria-hidden="true"` on `marker-icon` and `trace-icon`. Running trace titles and uploading or processing attachment titles shimmer. When the shimmer color cannot be computed (an invalid `--shimmer-color`, or a browser without relative color syntax), the text is transparent, as in shadcn; with `clanker-ui-a11y.css` it stays plain and visible.

#### Message, Bubble, Marker

```html
<div data-slot="message" data-align="end">
  <div data-slot="message-avatar"><span data-slot="avatar"><img data-slot="avatar-image" src="me.png" alt="@me"><span data-slot="avatar-fallback">ME</span></span></div>
  <div data-slot="message-content">
    <div data-slot="message-header">Olivia</div>
    <div data-slot="bubble" data-variant="muted"><div data-slot="bubble-content">Deploying to prod.</div></div>
    <div data-slot="message-footer">Delivered</div>
  </div>
</div>
```

`message-group` stacks messages from one sender. Bubble variants: `default`, `secondary`, `muted`, `tinted`, `outline`, `ghost`, `destructive`; `bubble-group`; `bubble-reactions` (`data-side`, `data-align`). `<div data-slot="marker" data-variant="separator|border" role="status">` with `marker-icon` and `marker-content`. CSS only.

#### Attachment

```html
<div data-slot="attachment" data-state="uploading" data-size="sm" data-orientation="vertical">
  <div data-slot="attachment-media" data-variant="image"><img src="a.png" alt="A"></div>
  <div data-slot="attachment-content">
    <span data-slot="attachment-title">a.png</span>
    <span data-slot="attachment-description">PNG · 820 KB</span>
  </div>
  <div data-slot="attachment-actions"><button data-slot="attachment-action" aria-label="Remove a.png"><svg data-lucide="x"></svg></button></div>
  <a data-slot="attachment-trigger" href="a.png" aria-label="Open a.png"></a>
</div>
```

States: `idle`, `uploading`, `processing`, `error`, `done`. Sizes: `default`, `sm`, `xs`. `attachment-group` is a scrolling, snapping row. `attachment-trigger` shows the standard focus ring.

#### Trace

```html
<div data-slot="trace">
  <span data-slot="trace-line" data-status="running|error|pending">
    <span data-slot="trace-icon"><svg data-lucide="terminal"></svg></span>
    <span data-slot="trace-title">Running pnpm build</span>
    <span data-slot="trace-description">14s</span>
  </span>
  <div data-slot="trace-collapsible" data-default-open>
    <button data-slot="trace-collapsible-trigger"><span data-slot="trace-line">…</span></button>
    <div data-slot="trace-collapsible-content">Detail</div>
  </div>
</div>
```

The kit adds the chevron and keeps `aria-expanded` and `data-state` current. It sets the Base UI collapsible states: `data-open` or `data-closed` on the collapsible and the content, `data-panel-open` on the trigger, and `data-starting-style` (one frame on open) or `data-ending-style` (while it closes) on all three. The content height is a CSS transition on `--collapsible-panel-height`: the pixel height while it moves, `auto` when open.

#### Code Block

```html
<div data-slot="code-block" data-size="sm" data-variant="destructive">
  <div data-slot="code-block-header">
    <div data-slot="code-block-title"><svg data-lucide="file-text"></svg>app.ts</div>
    <div data-slot="code-block-actions">
      <button data-slot="code-block-wrap-button" aria-label="Wrap lines"><svg data-lucide="text-wrap"></svg></button>
      <button data-slot="code-block-download-button" data-filename="app.ts"></button>
      <button data-slot="code-block-copy-button"></button>
    </div>
  </div>
  <pre data-slot="code-block-content" data-language="ts" data-numbered="true" data-start-line="14" data-wrap="true"><code data-slot="code-block-code">code</code></pre>
</div>
```

`data-numbered` splits text into `code-block-line` rows; write `<span data-slot="code-block-line" data-variant="added|removed|highlighted">` rows for diffs and highlighted lines. Copy uses the Clipboard API: `data-value` or the block text without line numbers; it shows a check for 2 s (`data-timeout`) and announces "Copied" (`strings.copied`). A copy button that leaves the page goes back to its copy state. The wrap button toggles `data-wrap` and `aria-pressed` (pressed text is `--foreground`). The download button saves `data-value` or the block text as `data-filename` (default: the last part of the title, else `code.txt`).

Syntax colors: load `clanker-ui-code.js` and set `data-language` on `code-block-content`. Languages: `ts`, `tsx`, `js`, `jsx`, `json`, `html`, `css`, `bash`, `yaml`, `go`, `python`, `diff`, `markdown`, `sql`, `ansi` (terminal colors; the escape codes go away), and the usual aliases (`typescript`, `javascript`, `sh`, `shell`, `zsh`, `yml`, `py`, `md`, `xml`, `svg`); other languages and text over 200 000 characters stay plain, as without the module. It colors plain text and plain rows when a block starts; rows with elements stay as they are. For text that changes, build the rows again:

```js
import { h } from "./clanker-ui.js"
import { codeBlockHighlight } from "./clanker-ui-code.js"

code.replaceChildren(...codeBlockHighlight(text, "ts").map(line =>
  h("span", { "data-slot": "code-block-line" }, h("span", { "data-slot": "code-block-line-content" }, line.length ? line : "\n"))))
```

Tokens are `<span data-token="…">` with `comment`, `keyword`, `string`, `constant`, `function`, `variable`, `tag`, `inserted`, `deleted`, or `bold`, colored by `--code-<token>` (on `:root`). The defaults are the GitHub Light and Dark colors of the shadcn highlighter, darkened or lightened to 4.5:1 on the block, its highlighted lines, and removed lines; each editor scheme sets its own (`clanker-ui-a11y.css` has the 4.5:1 changes).

#### Message Scroller

```html
<div data-slot="message-scroller" data-auto-scroll data-default-scroll-position="end|start|last-anchor">
  <div data-slot="message-scroller-viewport">
    <div data-slot="message-scroller-content">
      <div data-slot="message-scroller-item" data-message-id="u1" data-scroll-anchor="true">…</div>
    </div>
  </div>
  <button data-slot="message-scroller-button" data-direction="end"></button>
</div>
```

Give the root a height. Options: `data-auto-scroll`, `data-default-scroll-position`, `data-scroll-edge-threshold` (8), `data-scroll-margin` (0), `data-scroll-previous-item-peek` (64). A new anchor row moves near the top; rows added above keep the visible row in place. Only upward intent releases following: wheel up, a touch drag down, and ArrowUp, PageUp, Home, or Shift+Space on the viewport itself (keys in an input inside the log never release it); downward input keeps following. The button is `inert` with `data-active="false"` when there is nothing to scroll to; it defaults to `data-direction="end" data-variant="secondary" data-size="icon-sm"`. Rows default to `data-scroll-anchor="false"`. With the opening position `end` or `last-anchor`, the root and the viewport have `data-pending-scroll` (the viewport is invisible) until the position is set; put the attribute in the HTML to hide the first paint before the kit runs. The content ends with a hidden `<div aria-hidden="true" data-message-scroller-spacer>` that holds an anchored row at the top; the kit keeps it last when rows are added. App code counts and removes rows with `:scope > [data-slot="message-scroller-item"]`, never with the content's `children` or `lastElementChild`. The exported scroller functions return `false` or defaults for a scroller that is not in the document; set-up runs when it is inserted.

#### Questionnaire

```html
<form data-slot="questionnaire" data-shortcuts="letters|numbers" data-default-item="direction">
  <div data-slot="questionnaire-progress" data-template="Step {current} of {total}"></div>
  <fieldset data-slot="questionnaire-item" name="direction" data-required data-multiple>
    <legend data-slot="questionnaire-title">Question</legend>
    <p data-slot="questionnaire-description">Help text</p>
    <div data-slot="questionnaire-choices">
      <label data-slot="questionnaire-choice" data-value="a" data-default-checked>Label<span data-slot="questionnaire-choice-description">More</span></label>
      <input data-slot="questionnaire-input" aria-label="Other answer">
    </div>
    <p data-slot="questionnaire-error"></p>
  </fieldset>
  <div data-slot="questionnaire-actions">
    <button data-slot="questionnaire-previous"></button><button data-slot="questionnaire-skip"></button>
    <button data-slot="questionnaire-next"></button><button data-slot="questionnaire-submit"></button>
  </div>
</form>
```

One item at a time. The kit builds the native radio or checkbox, the indicator, and the shortcut hint (the input, the choice, and the hint carry `data-type`, `data-shortcut`, `data-checked` or `data-unchecked`; a required single-choice radio is `required` until a text answer is given; the action buttons default to `data-variant` `outline` (previous, skip) or `default` (next, submit) and `data-size="default"`), validates before Next and Submit, and fills the progress text and error message. Keys: letters or numbers pick, Up and Down move, Left and Right change the item, Enter continues, Ctrl or Cmd+Enter continues from anywhere. Skipped items are left out of the form data.

- A text answer can be `<input data-slot="questionnaire-input">` or `<textarea data-slot="questionnaire-input">` (Enter inserts a newline; Ctrl or Cmd+Enter continues). Text answers use the input and textarea styles. A selected text answer must pass native constraint validation (`type="email"`, `pattern`, `minlength`, ...); the automatic error then shows the browser's `validationMessage`. Text answers stay in the form (no `form=""`); an unselected text answer has no `name`.

#### Calendar

`<div data-slot="calendar" data-mode="single|multiple|range" data-value="2026-10-28" data-name="date"></div>`. The kit renders the grid. Each day is a Button part, as in shadcn: `<td data-slot="calendar-day" data-day="2026-10-28"><button data-slot="button" data-calendar-day-button data-variant="ghost" data-size="icon" data-day="10/28/2026">28</button></td>` (`data-day` on the button is the local date text). The cell of the focused day has `data-focused="true"`. In `range` mode with a value, every button has `data-range-start`, `data-range-middle`, `data-range-end` (`true` or `false`). A disabled previous or next button has `aria-disabled="true"` and `tabindex="-1"`, as in react-day-picker, so the date picker focuses the next part. The root gets `data-mode="single"`, `data-caption-layout="label"`, and `data-button-variant="ghost"` when it has none (the shadcn defaults of `mode`, `captionLayout`, and `buttonVariant`; the generated CSS selects on them), and `data-multiple-months="true"` with more than one month. `data-button-variant` is also the `data-variant` of the previous and next buttons. Week numbers have two digits (`05`).

| Attribute | Meaning |
| --- | --- |
| `data-value` | `2026-10-28`; `multiple`: space-separated dates; `range`: `2026-10-01/2026-10-07` |
| `data-month`, `data-months` | First month shown (`2026-10`), number of months side by side |
| `data-min`, `data-max`, `data-disabled-dates`, `data-disabled-weekdays`, `data-disabled` | Limits. Ranges use `a/b`. Weekdays `0` (Sunday) to `6`. A change from code (for example `data-max` set to today when the page loads) renders the grid again. |
| `data-week-start` | `0`–`6`, default `1` (Monday) |
| `data-caption-layout` | `label`, `dropdown`, `dropdown-months`, `dropdown-years`; years from `data-start-year` to `data-end-year` (default: 100 years before today to this year, or the years of `data-min` and `data-max`). With a year dropdown, navigation stops at January of the first and December of the last year, as in react-day-picker; for future dates set `data-end-year` or `data-max`. A `data-min` in a later year extends the default end year, and a `data-max` in an earlier year extends the default start year. |
| `data-month-format` | Month names in the month dropdown: `short` (default, `Dec`) or `long` (`December`, the shadcn `formatMonthDropdown` of `calendar-custom-days`) |
| `data-button-variant` | Button variant of the previous and next buttons, default `ghost` |
| `data-outside-days="false"`, `data-show-week-number`, `data-fixed-weeks`, `data-required` | rdp options (`data-show-week-number` is the shadcn `showWeekNumber` prop) |
| `data-name` | Hidden input(s) for forms: one per date in `multiple`, `from/to` in `range` |
| `data-today`, `data-lang`, `data-label-previous`, `data-label-next` | Overrides. Names come from `Intl` in the nearest `lang`. |

Keyboard (APG date grid): arrows by day or week, Home and End to the week ends, PageUp and PageDown by month, Shift+PageUp and Shift+PageDown by year. Disabled days are skipped; RTL is supported. Cell size: `--cell-size`.

- Month and weekday names always use the Gregorian calendar (`calendar: "gregory"`), also for languages whose default calendar differs (`fa`, `th`, `ar-SA`, ...). Digits stay localized.
- Each month caption is a live region (`role="status"`, `aria-live="polite"`), as in react-day-picker: the caption label in the `label` layout, a visually hidden span after the dropdowns in the dropdown layouts. The kit keeps it in place and changes its text, so the new month is announced. The grid has `aria-label` (the month caption) and `aria-multiselectable` (`false` in `single` mode).
- One ARIA difference from shadcn, by design: the navigation has a name (`aria-label`, `strings.calendarNavigation`, default `Navigation bar`); react-day-picker leaves it empty.
- English day labels use ordinals, as date-fns `PPPP` (`Tuesday, October 27th, 2026`); other languages use `Intl`. Days before the first or after the last month that navigation can show are hidden (`data-hidden="true"`).
- State (selection, shown month) survives removal and insertion. API calls before insertion work; the language (`lang` of an ancestor) and form reset are wired when the calendar enters the document.

#### Date Picker

A composition, as in shadcn: a `button` trigger, a `popover-content` popup, and a `calendar`, joined by the `date-picker` root.

```html
<div data-slot="date-picker" data-placeholder="Pick a date" data-format="long" data-required>
  <button type="button" id="due-trigger" data-slot="button" data-variant="outline" data-date-picker-trigger><svg data-lucide="calendar"></svg><span data-slot="date-picker-value"></span></button>
  <div data-slot="popover-content" data-date-picker-content data-align="start" aria-label="Choose date">
    <div data-slot="native-select-wrapper">
      <select data-slot="native-select" data-date-picker-preset aria-label="Presets"><option value="">Select</option><option value="1">Tomorrow</option></select>
      <svg data-lucide="chevron-down" data-slot="native-select-icon"></svg>
    </div>
    <div data-slot="calendar" data-name="due"></div>
  </div>
</div>
```

- Focus moves to the first part in the popup that can take focus (the previous-month button, or the next-month button when the previous one is disabled), as the Base UI popover does; Tab moves to the next-month button, then to the selected day or today. Escape, an outside click, or focus leaving closes it; a single date selection closes it unless `data-keep-open`. Focus returns to the trigger.
- The trigger shows the formatted date (`data-format`: `long|medium|short|full|numeric`; ranges show `from - to`). The language is the calendar language: `data-lang` on the calendar, else the nearest `lang` attribute, else the browser language. `lang="en"` gives US English (`October 29, 2026`); set `lang="en-GB"` on the `date-picker` root or on `<html>` for `29 October 2026`, or `data-lang="de"` on the calendar for `29. Oktober 2026`. Month and day names in the popup use the same language.
- Value from code: `data-value` on the calendar in the markup, or `calendarSetValue(calendar, "2026-10-29")` later. Both update the trigger text and the form value at once, without a `calendar:change` event (pass `{ emit: true }` for the event).
- Label the trigger with `<label for="due-trigger">` (a button is a labelable element) or `aria-labelledby`. In a vertical `field` the picker and its trigger fill the width, like an input.
- `data-required` on the root: in a form the picker needs a date. The kit adds a visually hidden `required` input to the root; a `data-slot="form"` shows the `field-error` of the field around the trigger (`data-error-value-missing` on the root), sets `aria-invalid` on the trigger (or the `data-date-picker-input`), and focuses it on submit. The calendar `data-name` still submits the value. `data-required` on the calendar is a different option: a click on the selected day does not clear it.
- `data-date-picker-input` on an input (for example in an `input-group`, with an icon button as the trigger) shows the date, parses typed dates on `change`, and opens the popup on ArrowDown. Typed text is read as ISO `yyyy-m-d`, as a numeric date in the order of the calendar language (en-US `m/d/yyyy`, de `d.m.yyyy`, ja `yyyy/m/d`), or as day, month name, and year in the language's long date order (`June 4, 2025`, `1. Juni 2025`). The year needs 4 digits; localized digits are accepted. Empty text clears the date. Text that does not parse keeps the old date and sets `aria-invalid="true"` on the input until the next valid change.
- A preset value is a day offset or an ISO date. The demo also shows date of birth, time, dialog, and RTL compositions. Not built: the natural language picker (needs chrono-node).

### Chart

SVG charts with no library, in `clanker-ui-chart.js`. Follows the dataviz rules: fixed categorical order, thin marks, one axis, a legend for two or more series (none for one), hover and keyboard tooltip, and a table view for every chart and sparkline.

```js
import { chart, sparkline, statTile } from "./clanker-ui-chart.js"

const view = chart(document.getElementById("visitors"), {
  rows: [{ month: "January", desktop: 186, mobile: 80 }, { month: "February", desktop: 305, mobile: 200 }],
  config: { desktop: { label: "Desktop", icon: "monitor" }, mobile: { label: "Mobile" } },
}, { type: "bar", x: "month", label: "Visitors, 2024" })
view.update({ rows: next }, { stack: true })
view.destroy()
```

- `data` is `{ rows, config }` or a rows array. `update()` keeps what you do not pass; `update(null, options)` changes options only. A failed `update()` throws and keeps the last good rows, config, options, and view. Calling `chart()` again on the same element destroys the old chart first. `destroy()` restores the element.
- `config` is shadcn's `ChartConfig`: `{ key: { label, color, theme: { light, dark }, icon } }`. `color` is a slot number (`1`–`8`), a token name (`"chart-1"`), or a CSS color. A color with `url(`, `src(`, a quote, or a backslash throws a `TypeError`. Without `color`, a key gets `--chart-N` from its position in `config`; the `x` key, and for pie, donut, and radial the value columns, do not count. Keys that are not in `config` follow in data order. Color follows the entity: a key with no data, a missing row, or a hidden series never repaints the others. More than 8 series without a color throws a `RangeError`.
- The element becomes `data-slot="chart"` with `data-type`. Size: 16 / 9 (pie, donut, radar, radial: square, max 250 px); set `height` in options or CSS. A `ResizeObserver` redraws it. `--color-<key>` is set for every series and slice; characters other than letters, digits, `_`, and `-` become `-` (`"page views"` gives `--color-page-views`).

| Option | Values |
| --- | --- |
| `type` | `bar` (default), `area`, `line`, `pie`, `donut`, `radar`, `radial` |
| `x`, `y` | Category key (default: the first non-numeric column). `y`: one key or a list. |
| `label`, `summary` | Name for the `aria-label`, table caption, and table region. `summary` replaces the automatic `aria-label`. |
| `format`, `tickFormat`, `xFormat`, `labelFormat`, `locale`, `timeZone` | `Intl` options or a function. Axis ticks are compact from 1,000. `locale` sets the language of numbers and dates (`"de-DE"`); it defaults to `<html lang>` when it is a valid language tag, else to the browser language. `timeZone` (an IANA name such as `"UTC"` or `"Europe/Ljubljana"`) places the time axis ticks and shows every date and time in that zone; the default is the browser time zone. An unknown zone throws a `RangeError`. |
| `stack` | `true` or `"expand"` for `bar` and `area` |
| `horizontal`, `labels`, `diverging`, `highlight`, `barSize` | Bar options |
| `curve`, `dots`, `gradient`, `zero`, `domain` | `monotone` (default), `linear`, `step`; dots; gradient fill; `zero: false`; fixed `[min, max]` (finite numbers or `null`; else a `TypeError`) |
| `references` | Bar, line, and area: a list of `{ value, label, tone, position }` (a dashed line) or `{ from, to, label, tone, position }` (a band with dashed edges). See [Reference lines and time axis](#reference-lines-and-time-axis). |
| `scale`, `connectNulls` | `scale: "time"` (line and area) puts each row at its date. `connectNulls`: `true` or a list of keys; the line goes across missing values. |
| `grid`, `valueAxis`, `categoryAxis`, `legend`, `table` | `false` hides each part |
| Pie and donut | `labels: "value" \| "percent" \| "name"`, `labelPosition: "inside"`, `innerRadius`, `center`, `highlight` |
| Radar | `grid: "polygon" \| "circle" \| "none"`, `fill: false`, `dots`, `max` |
| Radial | `stacked`, `startAngle`, `endAngle`, `max`, `track`, `grid`, `labels`, `center`, `innerRadius` |
| `tooltip` | `{ indicator: "line" \| "dot" \| "dashed", hideLabel, hideIndicator }` |
| `view`, `animate` | `"chart"` or `"table"`; `animate: false` skips the entrance animation |

- The SVG is `role="application"` with `tabindex="0"`, so screen readers pass the arrow keys to it. Its accessible name is an automatic summary; the marks inside are hidden from assistive technology, and the table view has every value. Pointer: crosshair for line and area, per-mark tooltip otherwise. Keyboard: arrows move between points, Home, End, Escape. A polite live region reads the readout. The legend is a toolbar of toggle buttons with one tab stop. The table button switches to an accessible `<table>`.
- Colors: `--chart-1`…`--chart-8` is a categorical palette with 8 distinct hues, validated with the dataviz `validate_palette.js` in light and dark. shadcn's own `--chart-1`…`--chart-5` are a gray ramp (the base color), which does not separate series; the kit uses the validated hues by default. The shadcn base schemes of `clanker-ui-themes.css` (`data-scheme="neutral"`, `zinc`, ...) set the exact shadcn gray ramp; the accessibility layer and the editor schemes keep hues. Brand colors: override `--chart-1`… in `app.css` (light and dark), or give a series `color` in `config`.
- `--chart-surface` is the gap and dot ring color (default `--card`); set it to the background the chart sits on.
- A label inside a fill uses `--chart-ink-light` (`#fff`) or `--chart-ink-dark` (`#0b0b0b`), whichever has the higher WCAG contrast against the fill. Override both on `[data-slot="chart"]`.
- Charts redraw on `theme:change` while they are in the document. A removed chart closes its tooltip, is not tracked, and redraws when it is inserted again. A destroyed chart never redraws.
- Fixed labels (chart names, legend, table button, table header, summary sentences) come from `strings` (see [Localization](#localization)); `data-string-<key>` on the chart element or an ancestor overrides one chart.
- Parts: `chart-plot`, `chart-svg`, `chart-tooltip` (`-label`, `-items`, `-item`, `-indicator`, `-name`, `-value`), `chart-legend`, `chart-legend-item`, `chart-table`, `chart-table-toggle`, `chart-footer`, `chart-live`. SVG marks use `data-part`.

#### Reference lines and time axis

```js
chart(document.getElementById("weight"), {
  rows: [
    { day: "2026-09-01", plan: 84, actual: 84.2 },
    { day: "2026-09-08", actual: 83.6 },
    { day: "2026-10-01", plan: 82 },
    { day: "2026-10-20", actual: 80.6 },
    { day: "2026-11-01", plan: 80, actual: 79.8 },
  ],
  config: { actual: { label: "Actual" }, plan: { label: "Plan", color: "chart-other" } },
}, {
  type: "line", x: "day", scale: "time", connectNulls: true, zero: false, label: "Weight, kg",
  references: [{ value: 78, label: "Goal 78 kg" }, { from: 79, to: 81, label: "Healthy", tone: "chart-2" }],
})
```

- A reference is a dashed line at `value`, or a band from `from` to `to` with a light fill and dashed edges, across the plot (vertical in a horizontal bar chart). It is not in the legend or the tooltip. The value axis grows to show it, except past a fixed `domain`. `tone` is a color as in `config` (default `--muted-foreground`). The label is small text in `--muted-foreground` at the end of the line (`position: "start"` puts it at the start); it moves to the other side of the line, or is left out, when it would leave the plot or cover another label. A sparkline draws no reference labels. The automatic summary names each reference (`referenceAt`, `referenceBand`), and the table view has a second table with each reference. A reference that is not an object with a finite `value`, or a finite `from` and `to`, throws a `TypeError`; so do references on pie, donut, radar, and radial charts.
- `scale: "time"` needs a `Date` or an ISO date (`2026-10-01`, or a date and time) in every `x` value; else it throws a `TypeError`. Give the rows in time order. The axis picks ticks of minutes, hours, days, weeks (from Monday), months, or years, so that the labels do not touch (24 px apart). A tick shows the day (`Oct 3`), the time, the month (`Oct`), or the year (on a January tick and on year ticks). An `xFormat` object sets the `Intl` options of all ticks; an `xFormat` function gets the tick `Date`. Hover finds the nearest point by time; the arrow keys move through the rows in data order.
- Data with one row per plan point and one row per measurement leaves gaps in each series; `connectNulls` draws each series as one line.

#### Stat tile and sparkline

```js
statTile(el, { label: "Total revenue", value: 1250, format: { style: "currency", currency: "USD" }, delta: 0.125, period: "vs last month", trend: [820, 940, 1250] })
sparkline(el, [980, 1020, 1284], { area: true, label: "Requests per minute" })
```

- `statTile` renders `data-slot="chart-stat"` (`role="group"`) with `chart-stat-label`, `chart-stat-value`, `chart-stat-delta` (`data-direction`, `data-tone`, icon, signed percent, `chart-stat-period`), and an optional `chart-stat-trend` sparkline.
- The tile draws its own card (border, radius, background, shadow, 24 px padding): call it on a plain `<div>` in a grid of tiles. Inside a `card` (any depth) it drops that frame, so a tile in a card has one border.
- Value: from 10,000 the value is compact (`notation: "compact"`, at most 1 decimal: `€30.5K`). Pass `format: { style: "currency", currency: "EUR", notation: "standard" }` for the full amount, or a function. `deltaFormat` defaults to `{ style: "percent", maximumFractionDigits: 1, signDisplay: "exceptZero" }`; your options are merged over it, and a `minimumFractionDigits` above the default maximum raises the maximum (`{ minimumFractionDigits: 2 }` gives `+12.50%`). `goodWhen: "down"` when a fall is good. Options: `label`, `value`, `format`, `delta`, `deltaFormat`, `period`, `goodWhen`, `trend`, `trendOptions`, `icon`, `description`, `locale`. `locale` sets the number locale (default as for charts). A failed `update()` throws and keeps the last good options; a `statTile()` call that throws leaves the element as it was.
- `sparkline` is a line (or `area: true`) without axes or legend, in `--chart-other` with the latest point in the accent. It keeps the tooltip, the keyboard readout, and the table view: a toggle next to the line shows a transposed table (one row per series, one column per point). Pass `table: false` only when the same values are visible next to it.

### Page patterns

Kit parts for page structure, ported from the layout of the shadcn blocks (`dashboard-01`, `login-03`, `sidebar-07`, and the tasks example) so that an app needs no layout CSS. All are CSS only and in the core group. Full pages that use them: [Blocks](https://bl4ko.github.io/clanker-ui/docs/blocks/).

#### Page

```html
<main data-slot="page" data-size="sm">
  <div data-slot="page-header">
    <h1 data-slot="page-title">Projects</h1>
    <p data-slot="page-description">All projects of your team.</p>
    <div data-slot="page-actions">
      <button type="button" data-slot="button" data-variant="outline">Export</button>
      <button type="button" data-slot="button">New project</button>
    </div>
  </div>
  <div data-slot="page-body">
    <aside data-slot="page-aside">
      <nav data-slot="page-nav" aria-label="Settings">
        <a data-slot="button" data-variant="ghost" href="#profile" aria-current="page">Profile</a>
        <a data-slot="button" data-variant="ghost" href="#account">Account</a>
      </nav>
    </aside>
    <div>Content</div>
  </div>
</main>
```

- `data-layout="split"` on `page` is the sign-in layout of shadcn `login-02`: two columns from 64rem. The first child is the form column: its first child is the top bar (a `brand`, or a `div` with the `brand` and a theme toggle at the ends), and the next children (the form, and a step such as "Check your email") are centered at most 20rem wide; a child with `hidden` stays hidden. A `page-aside` second child is the art panel (hidden below 64rem): `--muted`, its text at the bottom, an `svg` child that fills it behind the text (`--muted-foreground` at 35 %), and a `blockquote` (18 px, weight 500, at most 28rem) with a muted `footer`.
- `data-layout="center"` on `page` is the sign-in layout of shadcn `login-03`: a muted full-height page with its children centered at most 24rem wide. In it, card headers are centered, the card title is 20 px, a `field-description` child of the page is centered, and so is one in the field of the submit button.
- `page` is the content column: gutters of 1rem (1.5rem from 64rem), a 1rem gap between its children (1.5rem from 48rem), and `container: page`. Put it in `sidebar-inset` or `<body>`. `data-size="sm|md|lg"` limits the content to 42rem, 56rem, or 72rem and centers it; no size fills the width (dashboards, tables).
- `page-header` is a grid: `page-title` (24 px, weight 600) and `page-description` (muted) on the start side, `page-actions` (a row of buttons, `gap` 0.5rem) on the end side. Below 32rem of header width, the actions move under the text. `data-size="lg"` makes the title 30 px (the header of a detail page). `page-meta` after the description is a wrapping row of facts (14 px, muted, 1rem apart; an icon or a `badge` before each word).
- `page-body` puts its children in one column. With a `page-aside` first, it is a 12rem navigation column (sticky below a header of `--header-height`, default 3.5rem) and a content column of at most 42rem from 64rem; with a `page-aside` last, a 20rem side column; `data-variant="sticky"` on that aside keeps it in view below the header (a live summary next to a long form; only for an aside shorter than the screen). Each child is a flex column with a 1.5rem gap.
- `page-nav` holds ghost buttons (`aria-current="page"` on the current one gets the muted background). It is a row that scrolls below 64rem and a column from 64rem.

#### Site Header

```html
<header data-slot="site-header">
  <button data-slot="sidebar-trigger"></button>
  <div data-slot="separator" data-orientation="vertical"></div>
  <h1 data-slot="site-header-title">Documents</h1>
  <div data-slot="site-header-actions">
    <button type="button" data-slot="button" data-variant="ghost" data-size="icon" data-theme-set="toggle" aria-label="Dark mode"><svg data-lucide="contrast"></svg></button>
  </div>
</header>
```

- The top bar of a page, as in shadcn `dashboard-01`: `--header-height` high (default 3rem), a bottom border, sticky at the top, 1rem gutters (1.5rem from 64rem). A `sidebar-trigger` first and a vertical `separator` get the shadcn spacing. `site-header-title` is 16 px, weight 500, on one line. `site-header-actions` goes to the end.
- Without a sidebar it is the app header: a `brand` link, then `site-header-nav` with links (muted, `aria-current="page"` in the foreground), then `site-header-actions`. `data-size="lg"` makes the bar 3.5rem high.
- A `breadcrumb` can stand in place of the title.

#### Section Cards

```html
<div data-slot="section-cards">
  <div data-slot="card">
    <div data-slot="card-header">
      <div data-slot="card-description">Total Revenue</div>
      <div data-slot="card-title">$1,250.00</div>
      <div data-slot="card-action"><span data-slot="badge" data-variant="outline"><svg data-lucide="trending-up"></svg>+12.5%</span></div>
    </div>
    <div data-slot="card-footer">
      <div>Trending up this month <svg data-lucide="trending-up"></svg></div>
      <div data-slot="card-description">Visitors for the last 6 months</div>
    </div>
  </div>
</div>
```

- The KPI cards of shadcn `dashboard-01`. Columns follow the width of the grid itself: 1, then 2 from 34rem, then 4 from 61rem; exactly 3 cards go to 3 columns from 44rem. Use 2, 3, 4, or 8 cards.
- Each card is a subgrid row of the grid, so the headers and the footers of one row line up when a label wraps. A card with a `card-content` takes three rows.
- `card-title` is the value: 24 px (30 px when the card is at least 250 px wide), weight 600, tabular numbers. With a description first and a `badge` in `card-action`, the value takes the full width of the row under them, so a number does not break next to the badge. It wraps at spaces, and only a value wider than the card breaks inside. The footer holds a medium trend line with an icon and a `card-description`.
- `statTile()` elements can be the children too.
- The trend `badge` holds any short delta (`+12.5%`, `4 late`). Compute values and deltas from the data and today's date (`new Date()`), not from fixed strings.

#### Stat Grid

```html
<dl data-slot="stat-grid">
  <div>
    <dt>Uptime</dt>
    <dd>99.98%</dd>
    <dd>Last 30 days</dd>
  </div>
  <div>
    <dt>Requests</dt>
    <dd>1.2M <span data-slot="badge" data-variant="success">+4%</span></dd>
    <dd>Last 30 days</dd>
  </div>
</dl>
```

- Static numbers without JavaScript in one card surface with 1 px dividers. Each child `div` holds a `dt` (label), a `dd` (value: 24 px, weight 600, tabular numbers, wraps instead of being cut), and an optional second `dd` (muted note).
- Columns follow the width of the list: 1, 2 from 20rem, and from 36rem 3 (3, 5, 6, or 9 items) or 4 (4, 7, 8 items).
- `data-size="sm"` shows the values in 14 px, weight 500: the facts of a detail page (owner, created, status).

#### Data Table

```html
<div data-slot="data-table">
  <div data-slot="data-table-toolbar">
    <div>
      <input data-slot="input" type="search" placeholder="Filter tasks..." aria-label="Filter tasks">
    </div>
    <div>
      <button type="button" data-slot="button" data-size="sm">Add task</button>
    </div>
  </div>
  <div data-slot="table-container">
    <table data-slot="table">
      <thead data-slot="table-header"><tr data-slot="table-row"><th data-slot="table-head" scope="col">Task</th><th data-slot="table-head" scope="col" data-align="end">Hours</th></tr></thead>
      <tbody data-slot="table-body"><tr data-slot="table-row"><td data-slot="table-cell">TASK-8782</td><td data-slot="table-cell" data-align="end">12</td></tr></tbody>
    </table>
  </div>
  <div data-slot="data-table-pagination">
    <div data-slot="data-table-selection">0 of 68 row(s) selected.</div>
    <div>Page 1 of 7</div>
    <div>
      <button type="button" data-slot="button" data-variant="outline" data-size="icon-sm" aria-label="Go to previous page" disabled><svg data-lucide="chevron-left"></svg></button>
      <button type="button" data-slot="button" data-variant="outline" data-size="icon-sm" aria-label="Go to next page"><svg data-lucide="chevron-right"></svg></button>
    </div>
  </div>
</div>
```

- The frame of the shadcn data table (tasks example and `dashboard-01`): a toolbar, the table in a bordered, rounded `table-container` with a muted header, and the pagination row. Sorting, filtering, and paging are app code.
- `data-table-toolbar` has two `div` groups: filters at the start (the first grows; a text input in it is 150 to 250 px) and actions at the end. Both wrap. Small buttons in it are 32 px high, as high as the input (shadcn `h-8`). Below 40rem, when the first control of the start group is an `input` or `input-group` (the search), the search takes the whole first row, and the filters and the end group share the next row, with the end group at the end.
- `data-table-pagination` is a row of `div` groups at the end, 14 px, weight 500. `data-table-selection` is the muted selection text that fills the start.
- `data-table-text` is the text of a cell: one line, cut with an ellipsis at 32rem (or 60 % of the table width). With an icon first it is an icon and label row (the icon is muted). A sort button: a ghost `button` alone in the `table-head`, with `aria-sort` on the head.
- `data-align="end"` on a `table-head` or `table-cell` aligns numbers to the end with tabular figures; `data-align="center"` centers. A cell with only a `checkbox` is 2rem wide. A cell with an `empty` has no padding: use it with `colspan` for the empty state.

#### Brand

```html
<a data-slot="brand" href="/"><span data-slot="brand-mark" data-size="sm"><svg data-lucide="layout-dashboard"></svg></span>Acme Inc.</a>
```

- The logo link of the app: `brand-mark` (a primary square, 32 px; `data-size="sm"` 24 px) and the name, weight 500 in the text size around it. In a `sidebar`, the mark uses `--sidebar-primary`. `brand-mark` also stands alone in a large `sidebar-menu-button`, before a `text-stack`.

#### Text Stack

```html
<span data-slot="text-stack"><span>shadcn</span><span>m@example.com</span></span>
```

- A name and a detail line, as in the shadcn team switcher and user menu: the first line is 14 px, weight 500; the next lines are 12 px at 70 % of the text color. Each line is cut with an ellipsis. Use it after an `avatar` or a `brand-mark` in a `sidebar-menu-button`, a `dropdown-menu-label`, or a table cell.


#### Card Grid

```html
<div data-slot="card-grid">
  <div data-slot="card">
    <div data-slot="cover" data-tone="2"><svg viewBox="0 0 100 150" preserveAspectRatio="none" aria-hidden="true"><circle cx="70" cy="40" r="28" fill="currentColor" opacity="0.5"></circle></svg></div>
    <div data-slot="card-header"><h3 data-slot="card-title">Piranesi</h3><p data-slot="card-description">Susanna Clarke</p></div>
  </div>
  <div data-slot="card">
    <div data-slot="cover" data-tone="3"><svg viewBox="0 0 100 150" preserveAspectRatio="none" aria-hidden="true"><rect y="90" width="100" height="60" fill="currentColor" opacity="0.4"></rect></svg></div>
    <div data-slot="card-header"><h3 data-slot="card-title">Project Hail Mary</h3><p data-slot="card-description">Andy Weir</p></div>
  </div>
</div>
```

- A grid of records with a preview (books, products, projects): as many columns of at least 13rem as fit (`data-size="sm"` 10rem, `lg` 18rem), a 1rem gap, one column on a narrow screen. The cards of one row have one height, and a `card-footer` sits at the bottom of its card.

#### Cover

```html
<div data-slot="cover" data-tone="4" data-ratio="square">
  <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><circle cx="80" cy="20" r="30" fill="currentColor" opacity="0.4"></circle></svg>
  <span>Field notes</span>
  <span>Volume 2</span>
</div>
```

- Placeholder art made from tokens, for a record without an image: a 2 / 3 box (`data-ratio="square"` 1 / 1, `video` 16 / 9) with the kit radius and a tint of `--chart-N` (`data-tone="1"` to `"5"`, default 1) on the card. An `svg` child fills the box behind the text in the tone color (draw with `currentColor`). The first text child is the title (16 px, weight 600), the others are 12 px; text wraps and is never cut. In a card that shows the title in its `card-header`, the cover is art only: no text on the art. A word breaks only when it alone is wider than the cover (with a hyphen where the browser knows the page language).


#### Rating

```html
<span data-slot="rating" role="img" aria-label="4 of 5 stars"><svg data-lucide="star" fill="currentColor"></svg><svg data-lucide="star" fill="currentColor"></svg><svg data-lucide="star" fill="currentColor"></svg><svg data-lucide="star" fill="currentColor"></svg><svg data-lucide="star"></svg></span>
```

- A read-only star rating: a row of 16 px icons (`data-size="sm"` 12 px) with a 2 px gap. Filled stars (`fill="currentColor"`) are `--foreground`, empty stars `--muted-foreground`. Give the root `role="img"` and an `aria-label` with the value. For a rating input, use native radio inputs with star labels (the agent skill `references/recipes.md` has the markup and CSS): the browser gives the arrow keys and the form value, and a `data-slot="form"` shows the error.


## How parity with shadcn is tested

The reference is the live site <https://ui.shadcn.com> at one pinned shadcn commit and the Base UI version of that commit (1.6.0 now).

- **CSS.** `tools/gen` makes `clanker-ui.css` from the pinned shadcn source. `tools/parity` loads each live component page and a copy of it with the generated CSS, and compares 96 computed style properties of every part in light and dark, at rest and with hover, press, focus, open, and disabled states. The strict mode fails when a part differs more than the reviewed list `tools/parity/known.tsv` allows.
- **Behavior.** `tools/behavior` runs the same scripted user actions (click, keys, hover, drag, touch swipe) on the live page and on a kit page in Chromium, Firefox, and WebKit. It compares what a user can observe: focus, ARIA tree, state attributes, popup position, scroll lock, form values, and the timing of open and close animations. The live runs are stored as reference files, so the gate runs offline in CI.
- **Browser tests.** `test/run.py` runs more than 300 checks in 3 engines, light and dark, at 1280 and 390 px. A check also fails on any console error, CSP or Trusted Types violation, or failed request.

Differences by design (each one is a narrow `allowed` entry in the behavior gate):

- Better ARIA than the live site: tooltip `role=tooltip` and `aria-describedby`; names on the resizable handles, the combobox trigger, the command input ("Command menu"), the carousel slides, and the calendar navigation; a command `aria-activedescendant` that points at the selected item (cmdk can keep a stale value); the combobox keeps its input addon and trigger button in the ARIA tree while the list is open (Base UI hides the addon with `aria-hidden`, and with it a focusable button); the drawer keeps the native `<dialog>` as the dialog.
- Live defects that the kit does not copy: the calendar keeps focus on the day after Enter or a click (the live page replaces the day buttons, so focus falls to the body); a resizable touch swipe that is cancelled does not set the panel to 100 %.
- Firefox keeps the keyboard focus ring after a key closes a select, dropdown menu, or drawer, or moves in a radio group (Base UI moves focus after the key event, so live Firefox paints no ring).
- The checked state of the context menu and menubar demo items changes after a click, as in an app (the live demos have fixed state).

Details of all tools: [DEVELOPMENT.md](DEVELOPMENT.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). A pull request can merge only when the required checks `ci-result` and `gitleaks` pass. Report security problems as described in [SECURITY.md](SECURITY.md).

## Credits

clanker-ui ports [shadcn/ui](https://github.com/shadcn-ui/ui) and [Base UI](https://github.com/mui/base-ui), and its carousel is a port of [Embla Carousel](https://github.com/davidjerleke/embla-carousel). The CSS includes output of [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) and [tw-animate-css](https://github.com/Wombosvideo/tw-animate-css). Icons are from [Lucide](https://github.com/lucide-icons/lucide). The color schemes use the editor palettes that `THIRD_PARTY_NOTICES` lists. Behavior references: [react-day-picker](https://github.com/gpbl/react-day-picker), [cmdk](https://github.com/pacocoursey/cmdk), [Floating UI](https://github.com/floating-ui/floating-ui), [vaul](https://github.com/emilkowalski/vaul), [input-otp](https://github.com/guilhermerodz/input-otp), [react-resizable-panels](https://github.com/bvaughn/react-resizable-panels), [Radix Primitives](https://github.com/radix-ui/primitives), [Recharts](https://github.com/recharts/recharts), and [date-fns](https://github.com/date-fns/date-fns). The generator follows the method of [Basecoat](https://basecoatui.com).

clanker-ui is not affiliated with shadcn/ui, Base UI, or Vercel.

## License

MIT, see [LICENSE](LICENSE). The notices and licenses of the third-party parts are in [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES). Each kit file starts with a one-line license comment that names them; keep it when you copy or minify the file.
