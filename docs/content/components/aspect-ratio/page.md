---
title: Aspect Ratio
description: Displays content within a desired ratio.
---

{{example "aspect-ratio-demo"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`. The kit reads `data-ratio` and sets the `--ratio` custom property.

With the minified group files, load `clanker-ui-core.min.css` and `clanker-ui-core.min.js`.

## Usage

```html
<div data-slot="aspect-ratio" data-ratio="16/9">
  <img src="photo.jpg" alt="Image" class="rounded-md object-cover">
</div>
```

The children are not positioned. Give an image `position: absolute; inset: 0; width: 100%; height: 100%`, like the `fill` prop of the shadcn examples.

## Square

A square aspect ratio with `data-ratio="1/1"`. This is useful for displaying images in a square format.

{{example "aspect-ratio-square"}}

## Portrait

A portrait aspect ratio with `data-ratio="9/16"`. This is useful for displaying images in a portrait format.

{{example "aspect-ratio-portrait" height="24rem"}}

## RTL

The aspect ratio has no direction. Set `dir="rtl"` on `<html>` or on a container for the content around it. See [Direction](/docs/components/direction).

{{example "aspect-ratio-rtl" height="24rem"}}

## API Reference

### Aspect Ratio

The `aspect-ratio` part displays content within a desired ratio.

| Attribute | Values | Default |
| --- | --- | --- |
| `data-ratio` | A ratio: `"16/9"`, `"4/3"`, `"1/1"`, or a number such as `"2.4"` | |
