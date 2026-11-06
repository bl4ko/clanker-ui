---
title: Input Group
description: Add addons, buttons, and helper content to inputs.
---

{{example "input-group-demo" height="26rem"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-forms.min.css`, and their `.min.js` files.

## Usage

```html
<div data-slot="input-group">
  <input data-slot="input-group-control" placeholder="Search...">
  <div data-slot="input-group-addon">
    <svg data-lucide="search"></svg>
  </div>
  <div data-slot="input-group-addon" data-align="inline-end">
    <button type="button" data-slot="button" data-input-group-button>Search</button>
  </div>
</div>
```

## Composition

Use the following composition to build an input group:

```text
input-group
├── input-group-control (input or textarea)
├── input-group-addon
├── button (data-input-group-button)
└── input-group-text
```

## Align

Use `data-align` on `input-group-addon` to position the addon relative to the input.

> For proper focus management, put `input-group-addon` after the `input-group-control` in the DOM. Use `data-align` to position the addon visually.

### inline-start

Use `data-align="inline-start"` to position the addon at the start of the input. This is the default.

{{example "input-group-inline-start" height="12rem"}}

### inline-end

Use `data-align="inline-end"` to position the addon at the end of the input.

{{example "input-group-inline-end" height="12rem"}}

### block-start

Use `data-align="block-start"` to position the addon above the input.

{{example "input-group-block-start" height="24rem"}}

### block-end

Use `data-align="block-end"` to position the addon below the input.

{{example "input-group-block-end" height="26rem"}}

## Icon

{{example "input-group-icon" height="20rem"}}

## Text

{{example "input-group-text" height="20rem"}}

## Button

{{example "input-group-button" height="18rem"}}

## Kbd

{{example "input-group-kbd" height="10rem"}}

## Dropdown

{{example "input-group-dropdown" height="14rem"}}

## Spinner

{{example "input-group-spinner" height="20rem"}}

## Textarea

{{example "input-group-textarea" height="24rem"}}

## Custom Input

Add `data-slot="input-group-control"` to your own input for automatic focus state handling.

Here is an example of a textarea that grows with its text (`field-sizing: content`).

{{example "input-group-custom" height="14rem"}}

## RTL

The input group uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "input-group-rtl" height="30rem"}}

## API Reference

### Input Group

The input group is the border and the focus ring around a control and its addons. The kit sets `role="group"`.

### Input Group Addon

| Attribute | Values | Default |
| --- | --- | --- |
| `data-align` | `"inline-start" \| "inline-end" \| "block-start" \| "block-end"` | `"inline-start"` |

A click on an addon (not on a button) focuses the control. The kit sets `role="group"`.

### Input Group Button

A button with `data-input-group-button` in an addon.

| Attribute | Values | Default |
| --- | --- | --- |
| `data-variant` | Any [Button](/docs/components/button) variant | `"ghost"` |
| `data-size` | `"xs" \| "sm" \| "icon-xs" \| "icon-sm"` | `"xs"` |

### Input Group Text

`<span data-slot="input-group-text">` for text and icons in an addon.

### Input Group Control

An `input` or a `textarea` with `data-slot="input-group-control"`. Use any element with this slot for a custom control.
