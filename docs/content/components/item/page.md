---
title: Item
description: A versatile component for displaying content with media, title, description, and actions.
---

{{example "item-demo"}}

## Installation

Load `clanker-ui.css`. The item needs no JavaScript.

With the minified group files, load `clanker-ui-core.min.css` and `clanker-ui-layout.min.css`.

## Usage

```html
<div data-slot="item">
  <div data-slot="item-media" data-variant="icon"><svg data-lucide="inbox"></svg></div>
  <div data-slot="item-content">
    <div data-slot="item-title">Item</div>
    <p data-slot="item-description">Item</p>
  </div>
  <div data-slot="item-actions"></div>
</div>
```

## Composition

Use the following composition to build an item:

```text
item-group
└── item
    ├── item-header
    ├── item-media
    ├── item-content
    │   ├── item-title
    │   └── item-description
    ├── item-actions
    └── item-footer
```

## Item vs Field

Use [Field](/docs/components/field) if you need to display a form input such as a checkbox, input, radio, or select.

If you only need to display content such as a title, description, and actions, use the item.

## Variant

Use `data-variant` to change the visual style of the item.

{{example "item-variant" height="24rem"}}

## Size

Use `data-size` to change the size of the item. Available sizes are `default`, `sm`, and `xs`.

{{example "item-size" height="24rem"}}

## Icon

Use `item-media` with `data-variant="icon"` to display an icon.

{{example "item-icon"}}

## Avatar

You can use `item-media` with an [Avatar](/docs/components/avatar) to display an avatar.

{{example "item-avatar"}}

## Image

Use `item-media` with `data-variant="image"` to display an image.

{{example "item-image"}}

## Group

Use `item-group` (`role="list"`, items `role="listitem"`) to group related items together.

{{example "item-group" height="24rem"}}

## Header

Use `item-header` to add a header above the item content.

{{example "item-header" height="24rem"}}

## Link

Use an `<a data-slot="item">` to render the item as a link. The hover and focus states apply to the link.

{{example "item-link"}}

## Dropdown

{{example "item-dropdown"}}

## RTL

The item uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "item-rtl"}}

## API Reference

### Item

The main part for displaying content with media, title, description, and actions.

| Attribute | Values | Default |
| --- | --- | --- |
| `data-variant` | `"default" \| "outline" \| "muted"` | `"default"` |
| `data-size` | `"default" \| "sm" \| "xs"` | `"default"` |

### Item Group

A container that groups related items with consistent spacing. Put an `item-separator` between items for a line.

### Item Media

| Attribute | Values | Default |
| --- | --- | --- |
| `data-variant` | `"default" \| "icon" \| "image"` | `"default"` |

### Other parts

`item-content` wraps `item-title` and `item-description`. `item-actions` holds buttons or other interactive elements. `item-header` and `item-footer` span the full width above and below the item.
