---
title: Button
description: Displays a button or a component that looks like a button.
---

{{example "button-demo"}}

## Installation

Load `clanker-ui.css`. The button needs no JavaScript.

## Usage

```html
<button type="button" data-slot="button" data-variant="outline">Button</button>
```

## Cursor

The kit keeps `cursor: pointer` on enabled buttons and on elements with `role="button"`. Tailwind v4, and so shadcn/ui, use `cursor: default`. To get the shadcn behavior, add this rule to `app.css`:

```css title="app.css"
button:not(:disabled),
[role="button"]:not([aria-disabled="true"]) {
  cursor: default;
}
```

## Size

Use the `data-size` attribute to change the size of the button.

{{example "button-size"}}

## Default

{{example "button-default"}}

## Outline

{{example "button-outline"}}

## Secondary

{{example "button-secondary"}}

## Ghost

{{example "button-ghost"}}

## Destructive

{{example "button-destructive"}}

## Link

{{example "button-link"}}

## Icon

{{example "button-icon"}}

## With Icon

An `<svg>` child changes the inline padding of the button. The `data-icon="inline-start"` and `data-icon="inline-end"` attributes are the same as in shadcn/ui. The kit does not need them.

{{example "button-with-icon"}}

## Rounded

Set the radius in `app.css`, for example with a `rounded-full` class: `.rounded-full { border-radius: 9999px; }`.

{{example "button-rounded"}}

## Spinner

Put a `spinner` inside the button to show a loading state. Use `role="none"` on the spinner, because the button text is the label.

{{example "button-spinner"}}

## Button Group

To make a button group, use the `button-group` component. See [Button Group](/docs/components/button-group) for more details.

{{example "button-group-demo"}}

## As Link

Put `data-slot="button"` on an `<a>` element to make a link look like a button. Do not use `role="button"` on a link. It removes the link role.

{{example "button-as-link"}}

## RTL

The button uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction). The arrow icon has the shadcn class `rtl:rotate-180`, which is not in the kit. Add the flip rule to `app.css`: `.rtl\:rotate-180:dir(rtl) { rotate: 180deg; }`.

{{example "button-rtl"}}

## API Reference

### Button

The `button` component is a `<button>` or `<a>` element with `data-slot="button"`. It is CSS only.

| Attribute | Values | Default |
| --- | --- | --- |
| `data-variant` | `"default" \| "outline" \| "ghost" \| "destructive" \| "secondary" \| "link"` | `"default"` |
| `data-size` | `"default" \| "xs" \| "sm" \| "lg" \| "icon" \| "icon-xs" \| "icon-sm" \| "icon-lg"` | `"default"` |
| `disabled` | Boolean. On `<a>`, use `aria-disabled="true"`. | |
| `aria-invalid="true"` | Destructive border and focus ring | |

### Parts with the button look

Parts that shadcn/ui renders with `Button` keep their own `data-slot` and share the button rules. When `data-variant` and `data-size` are missing, they use these defaults:

| Part | Default |
| --- | --- |
| `pagination-link` | `ghost`, `icon`; the current page has `data-variant="outline"` |
| `carousel-previous`, `carousel-next` | `outline`, `icon-sm`, round 28 px |
| `sidebar-trigger` | `ghost`, 28 px |
| `attachment-action`, `code-block-copy-button`, `code-block-wrap-button` | `ghost`, `icon-xs` |
| `message-scroller-button` | `secondary`, `icon-sm` |
| `questionnaire-previous`, `questionnaire-skip` | `outline` |
| `questionnaire-next`, `questionnaire-submit` | `default` |
| `calendar-button-previous`, `calendar-button-next` | `ghost`, `--cell-size` |
