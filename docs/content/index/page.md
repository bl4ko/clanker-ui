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

A project copies three files, plus one optional file:

| File | Contents |
| --- | --- |
| `clanker-ui.css` | Tokens, reset, typography, all component styles |
| `clanker-ui.js` | ES module: core helpers and all component behavior |
| `clanker-ui-chart.js` | ES module: SVG charts, stat tiles, sparklines. Imports `./clanker-ui.js` |
| `clanker-ui-theme.js` | Optional classic script for apps with a theme switch. It copies the stored theme to `data-theme` on `<html>` before the first paint. |

Never edit a copy. Fix bugs in the kit first, then copy the files again. Find outdated copies with `shasum`.

## Load order

Load the kit first, then the app:

```html
<meta name="color-scheme" content="light dark">
<link rel="stylesheet" href="clanker-ui.css">
<link rel="stylesheet" href="app.css">
<script src="clanker-ui-theme.js"></script>
<script type="module" src="clanker-ui.js"></script>
```

Put app styles in `app.css`. The kit CSS is in cascade layers, so every unlayered rule in `app.css` wins without specificity fights.

## Minified and group files

`dist/` has minified copies of the kit and one file for each component group, so an app loads only the groups that it uses. Copy them byte for byte, like the readable files. Use the `.min` files together or the readable files together, never both.

| Group | Components | Needs |
| --- | --- | --- |
| `core` | button, separator, direction, theme, input, textarea, label, kbd, card, badge, alert, table, skeleton, spinner, empty, progress, aspect-ratio |  |
| `forms` | button-group, input-group, input-otp, field, form, checkbox, radio-group, switch, slider, select, native-select, combobox, toggle, toggle-group |  |
| `overlays` | dialog, alert-dialog, sheet, drawer, popover, tooltip, hover-card, dropdown-menu, context-menu, menubar, navigation-menu, command, toast, sonner | command: `forms` |
| `layout` | avatar, accordion, collapsible, tabs, breadcrumb, pagination, scroll-area, resizable, sidebar, carousel, item | sidebar: `overlays` |
| `chat` | message, bubble, attachment, message-scroller, trace, marker, questionnaire, code-block, calendar, date-picker | date-picker: `overlays`, `forms` |
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
