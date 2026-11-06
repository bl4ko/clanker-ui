---
title: Command
description: Command menu for search and quick actions.
---

{{example "command-demo" align="start" height="24.5rem"}}

## About

The command follows the behavior of [`cmdk`](https://github.com/dip/cmdk) by [Dip](https://www.dip.org/), which shadcn/ui uses: filtering, scoring, sorting, and the keyboard.

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-overlays.min.css`, and their `.min.js` files.

## Usage

```html
<div data-slot="command">
  <input data-slot="command-input" placeholder="Type a command or search...">
  <div data-slot="command-list">
    <div data-slot="command-empty">No results found.</div>
    <div data-slot="command-group" data-heading="Suggestions">
      <div data-slot="command-item">Calendar</div>
      <div data-slot="command-item">Search Emoji</div>
      <div data-slot="command-item">Calculator</div>
    </div>
    <div data-slot="command-separator"></div>
    <div data-slot="command-group" data-heading="Settings">
      <div data-slot="command-item">Profile</div>
      <div data-slot="command-item">Billing</div>
      <div data-slot="command-item">Settings</div>
    </div>
  </div>
</div>
```

## Composition

```text
command
├── command-input
└── command-list
    ├── command-empty
    ├── command-group
    │   └── command-item
    │       └── command-shortcut
    ├── command-separator
    └── command-group
```

For a command dialog, put the command in a [Dialog](/docs/components/dialog) `dialog-content`. The kit gives the content `data-command-dialog` and no close button.

## Basic

A simple command menu in a dialog.

{{example "command-basic"}}

## Shortcuts

{{example "command-shortcuts"}}

## Groups

A command menu with groups, icons and separators.

{{example "command-groups"}}

## Scrollable

Scrollable command menu with multiple items.

{{example "command-scrollable"}}

## RTL

The command uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "command-rtl" align="start" height="24.5rem"}}

## API Reference

### Command

| Attribute | Values | Default |
| --- | --- | --- |
| `data-loop` | Boolean: the selection wraps | |
| `data-should-filter` | `"false"`: no filtering | |

### Command Group

| Attribute | Values | Default |
| --- | --- | --- |
| `data-heading` | The heading text (or a `command-group-heading` child) | |

### Command Item

| Attribute | Values | Default |
| --- | --- | --- |
| `data-value` | The value for filtering and events | The text |
| `data-keywords` | Extra search words: `"a, b"` | |
| `data-disabled` | Boolean | |

### Keyboard and Accessibility

- Typing filters, scores, and sorts the items.
- ArrowUp and ArrowDown, Home and End, Ctrl+N, Ctrl+J, Ctrl+P, and Ctrl+K move the selection; Alt+arrows go to the next group; Enter selects.
