---
title: Context Menu
description: Displays a menu of actions triggered by a right click.
---

{{example "context-menu-demo"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-overlays.min.css`, and their `.min.js` files.

## Usage

```html
<div data-slot="context-menu">
  <div data-slot="context-menu-trigger" tabindex="0">Right click here</div>
  <div data-slot="context-menu-content">
    <div data-slot="context-menu-item">Profile</div>
    <div data-slot="context-menu-item">Billing</div>
    <div data-slot="context-menu-item">Team</div>
    <div data-slot="context-menu-item">Subscription</div>
  </div>
</div>
```

The trigger is the area. A right click, a long press (700 ms), Shift+F10, or the ContextMenu key opens the menu at the pointer. Give the area `tabindex="0"`, so the keyboard can reach it.

## Composition

Use the following composition to build a context menu:

```text
context-menu
├── context-menu-trigger
└── context-menu-content
    ├── context-menu-group
    │   ├── context-menu-label
    │   ├── context-menu-item
    │   └── context-menu-item
    ├── context-menu-separator
    ├── context-menu-group
    │   ├── context-menu-checkbox-item
    │   └── context-menu-checkbox-item
    ├── context-menu-separator
    ├── context-menu-radio-group
    │   ├── context-menu-radio-item
    │   └── context-menu-radio-item
    └── context-menu-sub
        ├── context-menu-sub-trigger
        └── context-menu-sub-content
            └── context-menu-item
```

## Basic

A simple context menu with a few actions.

{{example "context-menu-basic"}}

## Submenu

Use `context-menu-sub` to nest secondary actions.

{{example "context-menu-submenu"}}

## Shortcuts

Add `context-menu-shortcut` to show keyboard hints.

{{example "context-menu-shortcuts"}}

## Groups

Group related actions and separate them with dividers.

{{example "context-menu-groups"}}

## Icons

Combine icons with labels for quick scanning.

{{example "context-menu-icons"}}

## Checkboxes

Use `context-menu-checkbox-item` for toggles.

{{example "context-menu-checkboxes"}}

## Radio

Use `context-menu-radio-item` for exclusive choices.

{{example "context-menu-radio"}}

## Destructive

Use `data-variant="destructive"` to style the menu item as destructive.

{{example "context-menu-destructive"}}

## Sides

Control the menu placement with `data-side` and `data-align` on the content.

{{example "context-menu-sides"}}

## RTL

The menu uses logical properties, and the arrow keys of sub menus are mirrored. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "context-menu-rtl"}}

## API Reference

The context menu has the parts, attributes, and states of the [Dropdown Menu](/docs/components/dropdown-menu), with the `context-menu-` prefix. In context menus, the checkbox and radio indicators are a `span` without a slot.

### Context Menu Content

| Attribute | Values | Default |
| --- | --- | --- |
| `data-side` | `"top" \| "right" \| "bottom" \| "left"` | `"right"` |
| `data-align` | `"start" \| "center" \| "end"` | `"start"` |

### Events

| Event | Target | Detail |
| --- | --- | --- |
| `context-menu:select` | `context-menu` | `{ value, item, checked }`, cancelable (keeps the menu open) |
| `context-menu:change` | `context-menu` | `{ value, checked, item, group }` for checkbox and radio items |

### Keyboard and Accessibility

- Shift+F10 or the ContextMenu key opens the menu on the focused trigger.
- The arrow keys, Home, End, and typeahead move in the menu. ArrowRight opens a sub menu and ArrowLeft closes it (mirrored in RTL). Escape closes the innermost menu.
