---
title: Introduction
description: clanker-ui is a dependency-free port of shadcn/ui for plain HTML, CSS, and JavaScript. No build step, no npm, no CDN.
---

**This is shadcn/ui for apps that do not use React, a bundler, or a package manager.**

The markup mirrors the DOM that shadcn/ui renders. If you know the shadcn JSX, you can write the HTML 1:1. Behavior comes from HTML attributes. Everything runs under a strict CSP with Trusted Types.

- **No build step:** Copy the files into your project and load them.
- **No dependencies:** No npm, no CDN, no framework, no third-party code at run time.
- **Declarative:** Components read `data-slot`, `data-variant`, `data-size`, and `data-state`. There are no init calls. HTML that you insert later works too.
- **Secure by default:** No `innerHTML`, no inline scripts or styles. The kit works with `require-trusted-types-for 'script'`.
- **Same look:** Spacing, radius, shadows, focus rings, and transitions come from the shadcn v4 Tailwind classes.

## Files

Get the files from a [release](https://github.com/bl4ko/clanker-ui/releases) (zip and `SHA256SUMS`) or from the [repository](https://github.com/bl4ko/clanker-ui). A project needs `clanker-ui.css` and `clanker-ui.js`. The other files are optional:

| File | Contents |
| --- | --- |
| `clanker-ui.css` | Tokens, reset, typography, all component styles |
| `clanker-ui.js` | ES module: core helpers and all component behavior |
| `clanker-ui-chart.js` | Optional ES module: SVG charts, stat tiles, sparklines. Imports `./clanker-ui.js` |
| `clanker-ui-theme.js` | Optional classic script for apps with a theme switch. It copies the stored theme to `data-theme` on `<html>` before the first paint. |
| `clanker-ui-themes.css` | Optional color schemes: the shadcn base colors and accent themes, and editor palettes. Set `data-scheme` on `<html>`. |
| `clanker-ui-a11y.css` | Optional accessibility layer: stronger form-control edges, focus outline, and status colors for WCAG 2.2 AA |

Never edit a copy. Fix bugs in the kit first, then copy the files again. Find outdated copies with `shasum`.

## Load order

Load the kit first, then the optional files, then the app:

```html
<meta name="color-scheme" content="light dark">
<link rel="stylesheet" href="clanker-ui.css">
<link rel="stylesheet" href="clanker-ui-themes.css">
<link rel="stylesheet" href="clanker-ui-a11y.css">
<link rel="stylesheet" href="app.css">
<script src="clanker-ui-theme.js"></script>
<script type="module" src="clanker-ui.js"></script>
```

Put app styles in `app.css`. The kit CSS is in cascade layers, so every unlayered rule in `app.css` wins without specificity fights. Recipes for tokens, fonts, dialog width, Tailwind, and `!important` rules: [Override the kit](https://github.com/bl4ko/clanker-ui#override-the-kit).

## Content Security Policy

The kit needs no more than this policy. Send it as a header on every HTML response:

```text
default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; require-trusted-types-for 'script'
```

A static host that cannot send headers uses a meta tag as the first element of `<head>`, without `frame-ancestors` (browsers ignore it in a meta tag):

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; require-trusted-types-for 'script'">
```

Do not use inline `<script>`, inline `<style>`, `style=""`, or `on*=""` attributes. [csp.md](https://github.com/bl4ko/clanker-ui/blob/main/skills/clanker-ui/references/csp.md) has the Caddy and nginx lines and a small Go test server.

## Local test

Open the page through a web server, for example `python3 -m http.server -b 127.0.0.1 8000`, not as a file: browsers do not load module scripts from `file://`. The [README](https://github.com/bl4ko/clanker-ui#quick-start) has a quick start page.

## Minified and group files

`dist/` has minified copies of the kit and one file for each component group, so an app loads only the groups that it uses. Copy them byte for byte, like the readable files. Use the `.min` files together or the readable files together, never both.

| Group | Components | Needs |
| --- | --- | --- |
| `core` | button, separator, direction, theme, input, textarea, label, kbd, card, badge, alert, table, skeleton, spinner, empty, progress, aspect-ratio, page, site-header, section-cards, stat-grid, data-table, brand, text-stack, card-grid, cover, rating |  |
| `forms` | button-group, input-group, input-otp, field, form, checkbox, radio-group, switch, slider, select, native-select, combobox, toggle, toggle-group |  |
| `overlays` | dialog, alert-dialog, sheet, drawer, popover, tooltip, hover-card, dropdown-menu, context-menu, menubar, navigation-menu, command, toast, sonner, calendar, date-picker | command: `forms`; date-picker: `forms` |
| `layout` | avatar, accordion, collapsible, tabs, breadcrumb, pagination, scroll-area, resizable, sidebar, carousel, item | sidebar: `overlays` |
| `chat` | message, bubble, attachment, message-scroller, trace, marker, questionnaire, code-block |  |
| `chart` | chart |  |

Add the groups in the "Needs" column for the components you use. An app that uses 3 or more of the 4 component groups (`forms`, `overlays`, `layout`, `chat`) loads the one-file set: `clanker-ui.min.css`, `clanker-ui.min.js`, and `clanker-ui-core.min.js`. Other apps link the group CSS in the order of the table and load one module for each group with behavior; the browser loads the core through the import.

```html
<link rel="stylesheet" href="clanker-ui-core.min.css">
<link rel="stylesheet" href="clanker-ui-overlays.min.css">
<link rel="stylesheet" href="clanker-ui-layout.min.css">
<link rel="stylesheet" href="app.css">
<link rel="modulepreload" href="clanker-ui-core.min.js">
<script type="module" src="clanker-ui-overlays.min.js"></script>
<script type="module" src="clanker-ui-layout.min.js"></script>
```

## Components

The kit has all 65 shadcn/ui registry components, a chart module, and typography. See [Components](/docs/components).

```html
<button type="button" data-slot="button" data-variant="outline">Button</button>
```

## Browsers

Chrome, Safari (also iOS), and Firefox released in the last two years.
