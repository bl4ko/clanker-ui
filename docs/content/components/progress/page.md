---
title: Progress
description: Displays an indicator showing the completion progress of a task, typically displayed as a progress bar.
---

{{example "progress-demo"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css` and `clanker-ui-core.min.js`.

## Usage

```html
<div data-slot="progress" data-value="33" aria-label="Progress"></div>
```

The kit adds the Base UI parts `progress-track` and `progress-indicator`, `role="progressbar"`, `aria-valuenow`, and `aria-valuetext`. Change `data-value` to update it.

## Composition

```text
progress
├── progress-label (optional)
├── progress-value (optional, the kit writes the percent)
└── progress-track (the kit adds it)
    └── progress-indicator
```

## Label

Use `progress-label` and `progress-value` to add a label and value display.

{{example "progress-label"}}

## Controlled

Set `data-value` from your code, here from a [Slider](/docs/components/slider).

{{example "progress-controlled"}}

## RTL

The indicator grows from the start side. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "progress-rtl"}}

## API Reference

### Progress

| Attribute | Values | Default |
| --- | --- | --- |
| `data-value` | A number from 0 to `data-max`; missing: indeterminate | |
| `data-max` | A number | `100` |

The kit sets `data-state="loading|complete|indeterminate"` and `data-progressing`, `data-complete`, or `data-indeterminate` on every part.

### Progress Label

The `progress-label` part labels the bar.

### Progress Value

The `progress-value` part shows the value as a percent. The kit writes it.
