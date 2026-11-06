---
title: Input OTP
description: Accessible one-time password component with copy-paste functionality.
---

{{example "input-otp-demo"}}

## About

The shadcn Input OTP is built on [input-otp](https://github.com/guilhermerodz/input-otp) by Guilherme Rodz. The kit has the same parts and the same single real input, in plain JavaScript.

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-forms.min.css`, and their `.min.js` files.

## Usage

```html
<div data-slot="input-otp">
  <input maxlength="6" name="code" aria-label="One-time password">
  <div data-slot="input-otp-group">
    <div data-slot="input-otp-slot"></div>
    <div data-slot="input-otp-slot"></div>
    <div data-slot="input-otp-slot"></div>
  </div>
  <div data-slot="input-otp-separator" role="separator"><svg data-lucide="minus"></svg></div>
  <div data-slot="input-otp-group">
    <div data-slot="input-otp-slot"></div>
    <div data-slot="input-otp-slot"></div>
    <div data-slot="input-otp-slot"></div>
  </div>
</div>
```

One real input lies over the slots, so autofill, the form value, `required`, and `minlength` stay native.

## Composition

Use the following composition to build an input OTP:

```text
input-otp
├── input
├── input-otp-group
│   ├── input-otp-slot
│   ├── input-otp-slot
│   └── input-otp-slot
├── input-otp-separator
├── input-otp-group
│   ├── input-otp-slot
│   ├── input-otp-slot
│   └── input-otp-slot
├── input-otp-separator
└── input-otp-group
    ├── input-otp-slot
    └── input-otp-slot
```

## Pattern

Use `data-pattern` on the root to filter the typed and pasted characters: `digits`, `chars`, or `alphanumeric`.

```html
<div data-slot="input-otp" data-pattern="alphanumeric">
  ...
</div>
```

{{example "input-otp-pattern"}}

## Separator

Use `input-otp-separator` to add a separator between input groups.

{{example "input-otp-separator"}}

## Disabled

Use the `disabled` attribute on the input to disable it.

{{example "input-otp-disabled"}}

## Controlled

Set `value` on the input, and listen for `input` events to read the value.

{{example "input-otp-controlled"}}

## Invalid

Use `aria-invalid="true"` on the input to show an error state. The kit marks every slot.

{{example "input-otp-invalid"}}

## Four Digits

A common pattern for PIN codes. This uses `data-pattern="digits"`.

{{example "input-otp-four-digits"}}

## Alphanumeric

Use `data-pattern="alphanumeric"` to accept both letters and numbers.

{{example "input-otp-alphanumeric"}}

## Form

{{example "input-otp-form" height="30rem"}}

## RTL

In RTL the slots run right to left, and the arrow keys follow the visual order. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "input-otp-rtl"}}

## API Reference

### Input OTP

| Attribute | Values | Default |
| --- | --- | --- |
| `data-pattern` | `"digits" \| "chars" \| "alphanumeric"` | Any character |

The root holds one `<input>` with `maxlength`, `value`, `name`, `required`, `disabled`, and `aria-invalid`.

### Input OTP Slot

The kit fills each slot with the character at its position. The active slot has `data-active="true"`; the active empty slot shows the `input-otp-caret`.

### Input OTP Separator

A `role="separator"` element between groups, usually with the `minus` icon.

### Keyboard and Accessibility

- The input is a normal text input: typing, paste, autofill (`autocomplete="one-time-code"`), and Backspace work as usual.
- The arrow keys move between slots.
