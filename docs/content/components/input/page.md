---
title: Input
description: A text input component for forms and user data entry with built-in styling and accessibility features.
---

{{example "input-demo"}}

## Installation

Load `clanker-ui.css`. The input needs no JavaScript.

With the minified group files, load `clanker-ui-core.min.css`.

## Usage

```html
<input data-slot="input" placeholder="Enter text">
```

The input is a real `<input>`, so `type`, `name`, `required`, and `FormData` work as usual.

## Basic

{{example "input-basic"}}

## Field

Use `field`, `field-label`, and `field-description` to create an input with a label and description.

{{example "input-field"}}

## Field Group

Use `field-group` to show multiple `field` blocks and to build forms.

{{example "input-fieldgroup"}}

## Disabled

Use the `disabled` attribute to disable the input. To style the disabled state, add `data-disabled="true"` to the `field`.

{{example "input-disabled"}}

## Invalid

Use `aria-invalid="true"` to mark the input as invalid. To style the invalid state, add `data-invalid="true"` to the `field`.

{{example "input-invalid"}}

## File

Use `type="file"` to create a file input.

{{example "input-file"}}

## Inline

Use a `field` with `data-orientation="horizontal"` to create an inline input. Pair it with a [Button](/docs/components/button) to create a search input with a button.

{{example "input-inline"}}

## Grid

Use a grid layout to place multiple inputs side by side.

{{example "input-grid"}}

## Required

Use the `required` attribute to indicate required inputs.

{{example "input-required"}}

## Badge

Use a [Badge](/docs/components/badge) in the label to highlight a recommended field.

{{example "input-badge"}}

## Input Group

To add icons, text, or buttons inside an input, use the [Input Group](/docs/components/input-group).

{{example "input-input-group"}}

## Button Group

To add buttons to an input, use the [Button Group](/docs/components/button-group).

{{example "input-button-group"}}

## Form

A full form example with multiple inputs, a select, and a button.

{{example "input-form" height="32rem"}}

## RTL

The input uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "input-rtl"}}

## API Reference

### Input

An `<input>` with `data-slot="input"`. All native attributes work.

| Attribute | Values | Default |
| --- | --- | --- |
| `aria-invalid` | `"true"`: destructive border and focus ring | |
| `disabled` | Boolean | |
