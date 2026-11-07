---
title: Button Group
description: A container that groups related buttons together with consistent styling.
---

{{example "button-group-demo"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-forms.min.css`, and their `.min.js` files.

## Usage

```html
<div data-slot="button-group" role="group">
  <button type="button" data-slot="button">Button 1</button>
  <button type="button" data-slot="button">Button 2</button>
</div>
```

## Composition

Use the following composition to build a button group:

```text
button-group
├── button or input
├── button-group-separator
└── button-group-text
```

## Accessibility

- The button group has `role="group"`.
- Use Tab to move between the buttons in the group.
- Use `aria-label` or `aria-labelledby` to label the button group.

```html
<div data-slot="button-group" role="group" aria-label="Button group">
  <button type="button" data-slot="button">Button 1</button>
  <button type="button" data-slot="button">Button 2</button>
</div>
```

## ButtonGroup vs ToggleGroup

- Use the button group when you want to group buttons that perform an action.
- Use the [Toggle Group](/docs/components/toggle-group) when you want to group buttons that toggle a state.

## Orientation

Set `data-orientation` to change the button group layout.

{{example "button-group-orientation"}}

## Size

Control the size of buttons with `data-size` on each button.

{{example "button-group-size"}}

## Nested

Nest button groups to create button groups with spacing.

{{example "button-group-nested"}}

## Separator

The `button-group-separator` part visually divides buttons within a group.

Buttons with variant `outline` do not need a separator since they have a border. For other variants, a separator is recommended to improve the visual hierarchy.

{{example "button-group-separator"}}

## Split

Create a split button group by adding two buttons separated by a `button-group-separator`.

{{example "button-group-split"}}

## Input

Wrap an [Input](/docs/components/input) with buttons.

{{example "button-group-input"}}

## Input Group

Wrap an [Input Group](/docs/components/input-group) to create complex input layouts.

{{example "button-group-input-group"}}

## Dropdown Menu

Create a split button group with a [Dropdown Menu](/docs/components/dropdown-menu).

{{example "button-group-dropdown"}}

## Select

Pair with a [Select](/docs/components/select).

{{example "button-group-select"}}

## Popover

Use with a [Popover](/docs/components/popover).

{{example "button-group-popover"}}

## RTL

The button group uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "button-group-rtl"}}

## API Reference

### Button Group

The button group joins its children: the inner corners and borders of the first and last child meet. A `select`, `dropdown-menu`, `popover`, `tooltip`, or `hover-card` root in a group joins its trigger to the group. CSS only.

| Attribute | Values | Default |
| --- | --- | --- |
| `role` | `"group"` | |
| `data-orientation` | `"horizontal" \| "vertical"` | `"horizontal"` |
| `aria-label` | The name of the group | |

### Button Group Separator

```html
<div data-slot="button-group-separator" data-orientation="vertical" role="none"></div>
```

| Attribute | Values | Default |
| --- | --- | --- |
| `data-orientation` | `"horizontal" \| "vertical"` | `"vertical"` |

### Button Group Text

Text in the group, for example a prefix or a suffix of an input. Use a `<label>` when it names the input.

```html
<div data-slot="button-group" role="group">
  <label data-slot="button-group-text" for="url">https://</label>
  <input data-slot="input" id="url" placeholder="my-app">
  <span data-slot="button-group-text">.com</span>
</div>
```
