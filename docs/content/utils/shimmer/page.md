---
title: shimmer
description: Utilities for adding a shimmer effect to text elements.
---

{{example "shimmer-demo"}}

## Installation

Load `clanker-ui.css`. The kit has `.shimmer`, `.shimmer-once`, `.shimmer-reverse`, and `.shimmer-none`. The `shimmer-color-*`, `shimmer-duration-*`, `shimmer-spread-*`, and `shimmer-angle-*` classes on this page are the Tailwind utilities of the shadcn `tailwind.css`. Without Tailwind, set the custom properties in your CSS:

```css title="app.css"
.status {
  --shimmer-color: oklch(0.623 0.214 259.815 / 60%);
  --shimmer-duration: 1s;
  --shimmer-spread: 6rem;
  --shimmer-angle: 45deg;
}
```

## Usage

Add `shimmer` to a text element.

```html
<p class="shimmer">Generating response&hellip;</p>
```

The shimmer is built on `currentColor`, so it adapts to the element: the highlight comes from the text color, it works on any color, and in dark mode the highlight brightens to stay visible. The text is painted with `background-clip: text`, and the highlight sweeps across it in a seamless loop.

## With Marker

The shimmer composes with any part that renders text. A common pattern is a [Marker](/docs/components/marker) showing a live status while the assistant is working.

{{example "shimmer-marker"}}

## Color

Set the highlight color with `--shimmer-color` (`shimmer-color-<color>` in Tailwind).

{{example "shimmer-color"}}

## Duration

Set the duration of one sweep with `--shimmer-duration` (`shimmer-duration-<number>`, in milliseconds). The default is `2s`.

{{example "shimmer-duration"}}

## Spread

Set the width of the highlight band with `--shimmer-spread` (`shimmer-spread-<number>`). The default is `calc(3ch + 40px)`.

{{example "shimmer-spread"}}

## Angle

Set the tilt of the highlight band with `--shimmer-angle` (`shimmer-angle-<number>`). The default is `20deg`.

{{example "shimmer-angle"}}

## Reverse

Use `shimmer-reverse` to sweep the highlight in the opposite direction. In RTL the sweep already follows the reading direction.

## Play Once

Use `shimmer-once` to play a single sweep instead of looping, useful as a reveal when streaming completes.

{{example "shimmer-once"}}

## Disabling the Shimmer

Use `shimmer-none` to turn the effect off and render the text normally. It works in any class order, so the typical use is responsive or stateful.

{{example "shimmer-none"}}

## Fallback

The shimmer uses relative color syntax and `color-mix()`. When the shimmer color cannot be computed, the kit keeps the text plain and visible.

## Reduced Motion

When the user prefers reduced motion, the animation stops and the text renders normally.

## RTL

The sweep follows the reading direction, left to right in LTR and right to left in RTL, with no extra classes.

{{example "shimmer-rtl"}}
