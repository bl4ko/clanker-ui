---
title: Dropdown Menu
description: Displays a menu to the user, such as a set of actions or functions, triggered by a button.
---

{{example "dropdown-menu-demo"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-overlays.min.css`, and their `.min.js` files.

## Usage

```html
<div data-slot="dropdown-menu">
  <button type="button" data-slot="button" data-variant="outline" data-dropdown-menu-trigger>Open</button>
  <div data-slot="dropdown-menu-content">
    <div data-slot="dropdown-menu-group">
      <div data-slot="dropdown-menu-label">My Account</div>
      <div data-slot="dropdown-menu-item">Profile</div>
      <div data-slot="dropdown-menu-item">Billing</div>
    </div>
    <div data-slot="dropdown-menu-separator"></div>
    <div data-slot="dropdown-menu-group">
      <div data-slot="dropdown-menu-item">Team</div>
      <div data-slot="dropdown-menu-item">Subscription</div>
    </div>
  </div>
</div>
```

## Composition

Use the following composition to build a dropdown menu:

```text
dropdown-menu
├── button (data-dropdown-menu-trigger)
└── dropdown-menu-content
    ├── dropdown-menu-group
    │   ├── dropdown-menu-label
    │   ├── dropdown-menu-item
    │   └── dropdown-menu-item
    ├── dropdown-menu-separator
    ├── dropdown-menu-group
    │   ├── dropdown-menu-label
    │   ├── dropdown-menu-checkbox-item
    │   └── dropdown-menu-checkbox-item
    ├── dropdown-menu-separator
    ├── dropdown-menu-group
    │   ├── dropdown-menu-label
    │   └── dropdown-menu-radio-group
    │       ├── dropdown-menu-radio-item
    │       └── dropdown-menu-radio-item
    └── dropdown-menu-sub
        ├── dropdown-menu-sub-trigger
        └── dropdown-menu-sub-content
            └── dropdown-menu-group
                ├── dropdown-menu-label
                ├── dropdown-menu-item
                └── dropdown-menu-item
```

## Basic

A basic dropdown menu with labels and separators.

{{example "dropdown-menu-basic"}}

## Submenu

Use `dropdown-menu-sub` to nest secondary actions.

{{example "dropdown-menu-submenu"}}

## Shortcuts

Add `dropdown-menu-shortcut` to show keyboard hints.

{{example "dropdown-menu-shortcuts"}}

## Icons

Combine icons with labels for quick scanning.

{{example "dropdown-menu-icons"}}

## Checkboxes

Use `dropdown-menu-checkbox-item` for toggles.

{{example "dropdown-menu-checkboxes"}}

## Checkboxes Icons

Add icons to checkbox items.

{{example "dropdown-menu-checkboxes-icons"}}

## Radio Group

Use `dropdown-menu-radio-group` for exclusive choices.

{{example "dropdown-menu-radio-group"}}

## Radio Icons

Show radio options with icons.

{{example "dropdown-menu-radio-icons"}}

## Destructive

Use `data-variant="destructive"` for irreversible actions.

{{example "dropdown-menu-destructive"}}

## Avatar

An account switcher dropdown triggered by an avatar.

{{example "dropdown-menu-avatar"}}

## Complex

A richer example combining groups, icons, and submenus.

{{example "dropdown-menu-complex"}}

## RTL

The menu uses logical properties, and the arrow keys of sub menus are mirrored. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "dropdown-menu-rtl"}}

## API Reference

### Dropdown Menu

| Attribute | Values | Default |
| --- | --- | --- |
| `data-modal` | `"false"` turns off the scroll lock and the outside click block | modal |

The trigger is a button with `data-dropdown-menu-trigger`. It gets `data-popup-open` and `data-pressed` while the menu is open.

### Dropdown Menu Content

| Attribute | Values | Default |
| --- | --- | --- |
| `data-side` | `"top" \| "right" \| "bottom" \| "left"` | `"bottom"` |
| `data-align` | `"start" \| "center" \| "end"` | `"start"` |

The kit sets `data-open` or `data-closed` and `data-instant` (`click`, `group`, or `dismiss`).

### Dropdown Menu Item

| Attribute | Values |
| --- | --- |
| `data-variant` | `"default" \| "destructive"` |
| `data-disabled` | Boolean |
| `data-inset` | Boolean: indent an item without an icon |
| `data-text-value` | The typeahead label |
| `data-close-on-click` | `"true" \| "false"`: a plain item closes the menu, checkbox and radio items keep it open |

### Dropdown Menu Checkbox Item and Radio Item

Use `data-checked` on a checkbox item. Use `data-value` on the radio group and on each radio item; the group selects the item with its value. The kit adds the indicator as the first child.

### Events

| Event | Target | Detail |
| --- | --- | --- |
| `dropdown-menu:select` | `dropdown-menu` | `{ value, item, checked }`, cancelable (keeps the menu open) |
| `dropdown-menu:change` | `dropdown-menu` | `{ value, checked, item, group }` for checkbox and radio items |

### Keyboard and Accessibility

- Enter, Space, and ArrowDown open the menu at the first item, ArrowUp at the last. The arrow keys wrap, Home and End go to the ends, and typeahead finds an item.
- ArrowRight opens a sub menu and ArrowLeft closes it (mirrored in RTL). Escape closes the innermost menu; Tab closes all.
- A label names its group (`aria-labelledby`).
