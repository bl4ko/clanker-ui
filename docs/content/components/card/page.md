---
title: Card
description: Displays a card with header, content, and footer.
---

{{example "card-demo" height="30rem"}}

## Installation

Load `clanker-ui.css`. The card needs no JavaScript.

With the minified group files, load `clanker-ui-core.min.css`.

## Usage

```html
<div data-slot="card">
  <div data-slot="card-header">
    <div data-slot="card-title">Card Title</div>
    <div data-slot="card-description">Card Description</div>
    <div data-slot="card-action">Card Action</div>
  </div>
  <div data-slot="card-content">
    <p>Card Content</p>
  </div>
  <div data-slot="card-footer">
    <p>Card Footer</p>
  </div>
</div>
```

## Composition

Use the following composition to build a card:

```text
card
├── card-header
│   ├── card-title
│   ├── card-description
│   └── card-action
├── card-content
└── card-footer
```

## Size

Use `data-size="sm"` to set the size of the card to small. The small size uses smaller spacing.

{{example "card-small" height="24rem"}}

## Spacing

In addition to `data-size`, you can use the `--card-spacing` custom property to control the spacing between sections and the inset of card parts.

{{example "card-spacing" height="34rem"}}

Use negative margins of `--card-spacing` to make content go edge to edge while it stays aligned with the card inset. When the edge-to-edge content sits above a footer, also remove the section gap with a negative bottom margin on `card-content`.

{{example "card-edge-to-edge" height="24rem"}}

## Image

Add an image before the card header to create a card with an image.

{{example "card-image" height="32rem"}}

## Horizontal

A kit extension: `data-orientation="horizontal"` puts a first-child [Cover](/docs/components/cover) (6rem, 8rem from 48rem) at the start and the other parts in a `div` column next to it, with a wrapping `card-footer`. Use it for a hero or feature card.

## RTL

The card uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "card-rtl" height="30rem"}}

## API Reference

### Card

The `card` part is the root container for card content.

| Attribute | Values | Default |
| --- | --- | --- |
| `data-size` | `"default" \| "sm"` | `"default"` |
| `data-orientation` | `"horizontal"` (kit extension) | |

The custom property `--card-spacing` sets the gap between sections and the inset of the parts (default `1rem`, `0.75rem` for `sm`).

### Card Header

The `card-header` part holds a title, a description, and an optional action.

### Card Title

The `card-title` part is the card title.

### Card Description

The `card-description` part is the helper text under the title.

### Card Action

The `card-action` part places content in the top-right of the header (for example, a button or a badge).

### Card Content

The `card-content` part is the main card body.

### Card Footer

The `card-footer` part holds actions and secondary content at the bottom of the card.
