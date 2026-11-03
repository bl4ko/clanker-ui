---
title: Native Select
description: A styled native HTML select element with consistent design system integration.
---

> For a styled select component, see the [Select](/docs/components/select) component.

{{example "native-select-demo"}}

## Installation

Load `clanker-ui.css`. The native select needs no JavaScript. With `clanker-ui.js`, the kit copies `data-size` between the wrapper and the select.

## Usage

```html
<div data-slot="native-select-wrapper">
  <select data-slot="native-select" aria-label="Fruit">
    <option data-slot="native-select-option" value="">Select a fruit</option>
    <option data-slot="native-select-option" value="apple">Apple</option>
    <option data-slot="native-select-option" value="banana">Banana</option>
    <option data-slot="native-select-option" value="blueberry">Blueberry</option>
    <option data-slot="native-select-option" value="pineapple">Pineapple</option>
  </select>
  <svg data-lucide="chevron-down" data-slot="native-select-icon"></svg>
</div>
```

Give the select a name: a `<label for>` with the `id` of the `<select>`, or `aria-label`. The select is a real `<select>`, so `name`, `required`, `form.reset()`, and `FormData` work as usual.

## Composition

### Simple

Options placed directly under `native-select` (no `native-select-optgroup`).

```text
native-select-wrapper
├── native-select
│   ├── native-select-option
│   ├── native-select-option
│   └── native-select-option
└── native-select-icon
```

### With groups

Use `native-select-optgroup` to organize options into categories.

```text
native-select-wrapper
├── native-select
│   ├── native-select-optgroup
│   │   ├── native-select-option
│   │   └── native-select-option
│   └── native-select-optgroup
│       ├── native-select-option
│       └── native-select-option
└── native-select-icon
```

## Groups

Use an `<optgroup>` with `data-slot="native-select-optgroup"` to organize options into categories.

{{example "native-select-groups"}}

## Disabled

Add the `disabled` attribute to the `<select>` to disable the select. The wrapper then has 50 % opacity.

{{example "native-select-disabled"}}

## Invalid

Use `aria-invalid="true"` on the `<select>` to show validation errors. In a [Field](/docs/components/field), also set `data-invalid` on the field.

{{example "native-select-invalid"}}

## Native Select vs Select

- Use the native select for native browser behavior, better performance, or mobile-optimized dropdowns.
- Use [Select](/docs/components/select) for custom styling, animations, or complex interactions.

## RTL

The native select uses logical properties: the icon moves to the left. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "native-select-rtl"}}

## API Reference

### Native Select

The `native-select` part is a `<select>` element inside a `native-select-wrapper`. It is CSS only.

| Attribute | Values | Default |
| --- | --- | --- |
| `data-size` | `"default" \| "sm"` (on the select or the wrapper) | `"default"` |
| `disabled` | Boolean | |
| `aria-invalid="true"` | Destructive border and focus ring | |

### Native Select Option

An `<option>` with `data-slot="native-select-option"`.

| Attribute | Values | Default |
| --- | --- | --- |
| `value` | String | |
| `disabled` | Boolean | |

### Native Select OptGroup

An `<optgroup>` with `data-slot="native-select-optgroup"`.

| Attribute | Values | Default |
| --- | --- | --- |
| `label` | String | |
| `disabled` | Boolean | |

### Native Select Icon

The `<svg data-lucide="chevron-down" data-slot="native-select-icon">` after the `<select>`. It does not take pointer events, so a click on it opens the select.
