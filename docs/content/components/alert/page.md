---
title: Alert
description: Displays a callout for user attention.
---

{{example "alert-demo"}}

## Installation

Load `clanker-ui.css`. With `clanker-ui.js`, the kit keeps room for an `alert-action`.

With the minified group files, load `clanker-ui-core.min.css` and `clanker-ui-core.min.js`.

## Usage

```html
<div data-slot="alert" role="alert">
  <svg data-lucide="info"></svg>
  <div data-slot="alert-title">Heads up!</div>
  <div data-slot="alert-description">You can add components and dependencies to your app using the cli.</div>
  <div data-slot="alert-action">
    <button type="button" data-slot="button" data-variant="outline">Enable</button>
  </div>
</div>
```

## Composition

```text
alert
├── svg (optional icon)
├── alert-title
├── alert-description
└── alert-action
```

## Basic

A basic alert with an icon, title, and description.

{{example "alert-basic"}}

## Destructive

Use `data-variant="destructive"` to create a destructive alert.

{{example "alert-destructive"}}

## Action

Use `alert-action` to add a button or other action element to the alert. It sits at the top end, and the title and the description never go under it.

{{example "alert-action"}}

## Custom Colors

You can customize the alert colors with your own CSS on the `alert` part, as with the Tailwind classes `bg-amber-50 dark:bg-amber-950` here.

{{example "alert-colors"}}

The kit also has status variants: `data-variant="success"`, `"warning"`, and `"info"` use the status tokens for the border, the background, and the text.

## RTL

The alert uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "alert-rtl"}}

## API Reference

### Alert

The `alert` part is the root. Give it `role="alert"`.

| Attribute | Values | Default |
| --- | --- | --- |
| `data-variant` | `"default" \| "destructive" \| "success" \| "warning" \| "info"` | `"default"` |

### Alert Title

The `alert-title` part is the title of the alert.

### Alert Description

The `alert-description` part is the text of the alert.

### Alert Action

The `alert-action` part holds a button or a link at the top end of the alert.
