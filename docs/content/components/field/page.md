---
title: Field
description: Combine labels, controls, and help text to compose accessible form fields and grouped inputs.
---

{{example "field-demo" height="auto"}}

## Installation

Load `clanker-ui.css`. With `clanker-ui.js`, the kit fills in the parts that shadcn renders (the `field-legend` variant, the `field-separator` line).

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-forms.min.css`, and their `.min.js` files.

## Usage

```html
<fieldset data-slot="field-set">
  <legend data-slot="field-legend">Profile</legend>
  <p data-slot="field-description">This appears on invoices and emails.</p>
  <div data-slot="field-group">
    <div data-slot="field">
      <label data-slot="field-label" for="name">Full name</label>
      <input data-slot="input" id="name" autocomplete="off" placeholder="Evil Rabbit">
      <p data-slot="field-description">This appears on invoices and emails.</p>
    </div>
    <div data-slot="field">
      <label data-slot="field-label" for="username">Username</label>
      <input data-slot="input" id="username" autocomplete="off" aria-invalid="true">
      <div data-slot="field-error">Choose another username.</div>
    </div>
    <div data-slot="field" data-orientation="horizontal">
      <button type="button" data-slot="switch" id="newsletter"></button>
      <label data-slot="field-label" for="newsletter">Subscribe to the newsletter</label>
    </div>
  </div>
</fieldset>
```

## Composition

### Field

A single control with label, helper text, and validation.

```text
field
├── field-label
├── input / textarea / switch / select
├── field-description
└── field-error
```

### Field Group

Related fields in one group. Use `field-separator` between sections when needed.

```text
field-group
├── field
├── field-separator
└── field
```

### Field Set

Semantic grouping with a legend and description, usually containing a `field-group`.

```text
field-set
├── field-legend
├── field-description
└── field-group
    ├── field
    └── field
```

## Anatomy

- `field` is the core wrapper for a single field.
- `field-content` is a flex column that groups label and description. It is not required if you have no description.
- Wrap related fields with `field-group`, and use `field-set` with `field-legend` for semantic grouping.

## Form

See [Form](/docs/components/form) for validation and submission with the field parts.

## Input

{{example "field-input"}}

## Textarea

{{example "field-textarea"}}

## Select

{{example "field-select"}}

## Slider

{{example "field-slider"}}

## Fieldset

{{example "field-fieldset"}}

## Checkbox

{{example "field-checkbox" height="32rem"}}

## Radio

{{example "field-radio"}}

## Switch

{{example "field-switch"}}

## Choice Card

Wrap `field` parts inside a `field-label` to create selectable field groups. This works with radio group items, checkboxes, and switches.

{{example "field-choice-card"}}

## Field Group

Stack `field` parts in a `field-group`. Add a `field-separator` to divide them.

{{example "field-group" height="24rem"}}

## RTL

The field parts use logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "field-rtl" height="auto"}}

## Responsive Layout

- Vertical fields: the default orientation stacks label, control, and helper text, ideal for mobile-first layouts.
- Horizontal fields: set `data-orientation="horizontal"` on `field` to align the label and control side by side. Pair with `field-content` to keep descriptions aligned.
- Responsive fields: set `data-orientation="responsive"`; the field becomes a row when the closest `field-group` is at least 28rem wide.

{{example "field-responsive" height="auto"}}

## Validation and Errors

- Add `data-invalid="true"` to `field` to switch the entire block into an error state.
- Add `aria-invalid="true"` on the control itself for assistive technologies.
- Put `field-error` right after the control or inside `field-content` to keep error messages aligned with the field.

## Accessibility

- `field-set` and `field-legend` keep related controls grouped for keyboard and assistive technology users.
- Use `field-separator` sparingly, so screen readers encounter clear section boundaries.

## API Reference

### Field Set

A `<fieldset>` with `data-slot="field-set"`.

### Field Legend

| Attribute | Values | Default |
| --- | --- | --- |
| `data-variant` | `"legend" \| "label"` | `"legend"` |

### Field Group

A layout container that stacks fields. Kit extension: `data-columns="2|3"` puts its fields in 2 or 3 columns when the group is at least 28rem wide. `data-slot="checkbox-group"` gives the tight checkbox list spacing.

### Field

| Attribute | Values | Default |
| --- | --- | --- |
| `data-orientation` | `"vertical" \| "horizontal" \| "responsive"` | `"vertical"` |
| `data-invalid` | `"true"` | |
| `data-disabled` | `"true"` | |

### Other parts

`field-content` (a column for the label and the description), `field-label` (a `<label>`, or a `div` as the title of a choice card), `field-description`, `field-separator` (optional `field-separator-content` child), `field-error`, and the kit extension `field-label-row` (a label and a link at the end).
