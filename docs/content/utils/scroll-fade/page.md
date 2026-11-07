---
title: scroll-fade
description: Utilities for adding a fade effect to the edges of a scroll container.
---

{{example "scroll-fade-demo" height="auto"}}

## Installation

Load `clanker-ui.css`. The kit has `.scroll-fade` (vertical) and `.scroll-fade-x` (horizontal). The other classes on this page (`scroll-fade-t`, `scroll-fade-b`, `scroll-fade-s`, `scroll-fade-e`, `scroll-fade-<number>`, `scroll-fade-none`, `no-scrollbar`) are the Tailwind utilities of the shadcn `tailwind.css`. Without Tailwind, set the custom properties in your CSS:

```css title="app.css"
.my-list {
  --scroll-fade-size: 6rem;
  --scroll-fade-reveal: 64px;
}
.my-list.flat {
  --scroll-fade-mask: none;
}
```

## Usage

Add `scroll-fade` to the scroll container, the element that has `overflow-y: auto`.

```html
<div class="scroll-fade">...</div>
```

The fade is scroll-aware and tracks the scroll position:

- At rest, the top edge is crisp and the bottom edge fades to hint at more content.
- As you scroll, a fade appears at the top and both edges stay faded mid-scroll.
- At the end, the bottom edge sharpens to show you have reached the last item.

The fade is a `mask-image`, so it dissolves the content itself rather than overlaying a color, and it adapts to any background. If your scroll area sits inside a card, put the background and border on a wrapper and `scroll-fade` on the inner scroller, so the fade dissolves the content and not the card.

The kit uses the same fade on the viewports of [Scroll Area](/docs/components/scroll-area) and [Message Scroller](/docs/components/message-scroller).

## No Overflow, No Fade

If the content does not overflow, no fade is shown. You can apply `scroll-fade` to any list without checking whether it scrolls.

{{example "scroll-fade-overflow" height="auto"}}

## Horizontal Scrolling

Use `scroll-fade-x` on containers that scroll horizontally. The horizontal fade is direction-aware: in RTL, the crisp edge and the fade follow the reading direction.

{{example "scroll-fade-horizontal" height="16rem"}}

## Edge Fades

Use edge utilities when only one edge should track the scroll position: `scroll-fade-t` and `scroll-fade-b` for vertical scrollers, `scroll-fade-s` and `scroll-fade-e` for logical inline edges that mirror in RTL.

{{example "scroll-fade-edge" height="auto"}}

## Fade Size

The fade depth defaults to `12%` of the container, capped at `40px`. Use `scroll-fade-<number>` (or `--scroll-fade-size`) for a fixed size. The fade eases in and out over `--scroll-fade-reveal` (`96px` by default).

{{example "scroll-fade-size" height="auto"}}

## Disabling the Fade

Use `scroll-fade-none` (or `--scroll-fade-mask: none`) to remove the fade.

{{example "scroll-fade-none" height="auto"}}

## Fallback

The scroll-aware behavior uses CSS scroll-driven animations, with no JavaScript. Browsers without them show a static fade on both edges. A visible scrollbar fades with the content; hide it with `scrollbar-width: none` (`no-scrollbar`).

## RTL

`scroll-fade-x` follows the reading direction. At rest, the start edge is crisp and the end edge fades. In RTL that means a crisp right edge and a fade on the left.

{{example "scroll-fade-rtl"}}
