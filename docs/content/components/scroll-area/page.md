---
title: Scroll Area
description: Augments native scroll functionality for custom, cross-browser styling.
---

{{example "scroll-area-demo" height="24rem"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-layout.min.css`, and their `.min.js` files.

## Usage

```html
<div data-slot="scroll-area" class="h-[200px] w-[350px] rounded-md border p-4">
  <div data-slot="scroll-area-viewport" aria-label="Terms">
    Jokester began sneaking into the castle in the middle of the night and leaving jokes all over the place: under the king's pillow, in his soup, even in the royal toilet.
  </div>
</div>
```

The viewport is the real scroll container. The kit makes it focusable, hides the native scrollbars, and adds a vertical scrollbar with a draggable thumb. Give the viewport a name with `aria-label`.

## Composition

```text
scroll-area
├── scroll-area-viewport
└── scroll-area-scrollbar (optional, data-orientation="horizontal")
    └── scroll-area-thumb (the kit adds it)
```

## Horizontal

Add a `scroll-area-scrollbar` with `data-orientation="horizontal"` for a horizontal scrollbar.

{{example "scroll-area-horizontal-demo"}}

## RTL

The scrollbar moves to the left in RTL. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "scroll-area-rtl" height="auto"}}

## API Reference

### Scroll Area

The `scroll-area` part is the root. Set its size with your CSS.

### Scroll Area Viewport

The `scroll-area-viewport` part is the scroll container. The kit sets `tabindex="0"` on it.

### Scroll Area Scrollbar

| Attribute | Values | Default |
| --- | --- | --- |
| `data-orientation` | `"vertical" \| "horizontal"` | `"vertical"` |

Like Base UI, a scrollbar shows while its content overflows. The kit sets `data-hovering` while the pointer is over the scroll area, and `data-scrolling` while its axis scrolls or its thumb is dragged. A click on the track centers the thumb at the pointer.

### Keyboard and Accessibility

The viewport is focusable, so the arrow keys, Page Up, Page Down, Home, and End scroll it.
