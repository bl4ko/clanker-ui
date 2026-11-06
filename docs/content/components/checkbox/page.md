---
title: Checkbox
description: A control that allows the user to toggle between checked and not checked.
---

{{example "checkbox-demo" height="20rem"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-forms.min.css`, and their `.min.js` files.

## Usage

```html
<button type="button" data-slot="checkbox" id="terms" data-name="terms"></button>
<label data-slot="label" for="terms">Accept terms</label>
```

The checkbox is a `<button>` with the Base UI DOM: `role="checkbox"`, `aria-checked`, and the state attributes. The kit adds a hidden native input after it, so `data-name`, `value` (default `on`), `data-required`, `form.reset()`, and `FormData` work as usual.

## Checked State

Use `data-checked` for the initial state. Toggle `data-checked` on the button to change it later, and listen for `checkbox:change` (`{ checked, value }`) on the button.

```js
el.addEventListener("checkbox:change", event => console.log(event.detail.checked))
el.toggleAttribute("data-checked", true)
```

## Invalid State

Set `aria-invalid="true"` on the checkbox and `data-invalid="true"` on the field to show the invalid styles.

{{example "checkbox-invalid"}}

## Basic

Pair the checkbox with `field` and `field-label` for proper layout and labeling.

{{example "checkbox-basic"}}

## Description

Use `field-content` and `field-description` for helper text.

{{example "checkbox-description"}}

## Disabled

Use the `disabled` attribute to prevent interaction and add `data-disabled="true"` to the `field` for disabled styles.

{{example "checkbox-disabled"}}

## Group

Use multiple fields to create a checkbox list.

{{example "checkbox-group"}}

## Table

Use `data-indeterminate` on a select-all checkbox when only some rows are selected.

{{example "checkbox-table"}}

## RTL

The checkbox uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "checkbox-rtl" height="20rem"}}

## API Reference

### Checkbox

| Attribute | Values | Default |
| --- | --- | --- |
| `data-checked` | Boolean: the initial and current state | |
| `data-indeterminate` | Boolean: the mixed state | |
| `data-name` | The name of the hidden input | |
| `value` | The value of the hidden input | `"on"` |
| `data-required` | Boolean | |
| `data-readonly` | Boolean | |
| `disabled` | Boolean | |
| `aria-invalid` | `"true"` | |

The kit sets `role`, `aria-checked`, `data-checked` or `data-unchecked`, `data-state`, `data-disabled`, `data-readonly`, `data-required`, and `data-invalid`. It adds the `checkbox-indicator` part while the checkbox is checked.

### Events

| Event | Target | Detail |
| --- | --- | --- |
| `checkbox:change` | `checkbox` | `{ checked, value }` |

### Keyboard and Accessibility

- Space toggles the checkbox. Enter does nothing.
- A `<label for>` or a wrapping `<label>` toggles it.
