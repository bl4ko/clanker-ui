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

## Action group

A `card-action` with two or more children (a badge and a button) lays them out in a row with an 8 px gap, aligned to the end, and wraps them when they do not fit. One child keeps the shadcn placement. shadcn has only the placement, and React code adds `className="flex gap-2"` for more children.

{{example "card-action-group" height="16rem"}}

## Action under the title

A kit extension: `data-wrap` on `card-action` moves the action to its own row under the title and the description, at the start, when the `card-header` is narrower than 24rem (a phone, or a narrow column). Use it for a wide action (a text button or a select), so the title keeps the width. Without `data-wrap`, the action stays in the second column at every width, as in shadcn.

{{example "card-action-wrap" height="16rem"}}

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

The `card-action` part places content in the top-right of the header (for example, a button or a badge). Two or more children get a row with an 8 px gap. Without a `card-description`, the title and the action are centered on one line.

| Attribute | Values | Default |
| --- | --- | --- |
| `data-wrap` | boolean (kit extension): under the title when the header is narrower than 24rem | |

### Card Content

The `card-content` part is the main card body.

### Card Footer

The `card-footer` part holds actions and secondary content at the bottom of the card.
