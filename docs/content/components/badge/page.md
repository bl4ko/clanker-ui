---
title: Badge
description: Displays a badge or a component that looks like a badge.
---

{{example "badge-demo"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`. The badge is CSS only; the kit JavaScript draws icons and spinners.

With the minified group files, load `clanker-ui-core.min.css` and `clanker-ui-core.min.js`.

## Usage

```html
<span data-slot="badge" data-variant="default|outline|secondary|destructive">Badge</span>
```

## Variants

Use `data-variant` to change the variant of the badge.

{{example "badge-variants"}}

## With Icon

You can put an icon in the badge. Use `data-icon="inline-start"` to put the icon on the left and `data-icon="inline-end"` to put the icon on the right.

{{example "badge-icon"}}

## With Spinner

You can put a spinner in the badge. Remember to add `data-icon="inline-start"` or `data-icon="inline-end"` to the spinner.

{{example "badge-spinner"}}

## Link

Use an `<a data-slot="badge">` to show a link as a badge.

{{example "badge-link"}}

## Custom Colors

You can change the colors of a badge with classes such as `bg-green-50 dark:bg-green-800`, or with app CSS.

{{example "badge-colors"}}

## RTL

The badge uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "badge-rtl"}}

## API Reference

### Badge

| Attribute | Values | Default |
| --- | --- | --- |
| `data-variant` | `"default" \| "secondary" \| "destructive" \| "outline" \| "ghost" \| "link"` | `"default"` |

Kit extension: `data-variant="success|warning|info"` for a status. Icons and spinners in a badge are 12 px.
