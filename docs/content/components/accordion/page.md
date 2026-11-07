---
title: Accordion
description: A vertically stacked set of interactive headings that each reveal a section of content.
---

{{example "accordion-demo" align="start" height="300px"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-layout.min.css`, and their `.min.js` files.

## Usage

```html
<div data-slot="accordion" data-type="single">
  <div data-slot="accordion-item" data-value="item-1" data-state="open">
    <h3><button type="button" data-slot="accordion-trigger">Is it accessible?</button></h3>
    <div data-slot="accordion-content"><div>Yes. It adheres to the WAI-ARIA design pattern.</div></div>
  </div>
</div>
```

The kit adds the chevrons, ids, `aria-expanded`, `aria-controls`, `role="region"`, and the state attributes. A closed panel has `hidden="until-found"`, so find in page opens its item. Put `hidden="until-found"` on the panels that start closed, so the page does not move when the module loads.

## Composition

Use the following composition to build an accordion:

```text
accordion
├── accordion-item
│   ├── accordion-trigger (in a heading)
│   └── accordion-content
└── accordion-item
    ├── accordion-trigger
    └── accordion-content
```

## Basic

A basic accordion that shows one item at a time. The first item is open by default.

{{example "accordion-basic" align="start" height="300px"}}

## Multiple

Use `data-type="multiple"` to allow multiple items to be open at the same time.

{{example "accordion-multiple" align="start" height="450px"}}

## Disabled

Use `data-disabled` on an `accordion-item` to disable it.

{{example "accordion-disabled" align="start" height="300px"}}

## Borders

Add a border to the accordion and a bottom border to each item (except the last) to add borders to the items.

{{example "accordion-borders" align="start" height="300px"}}

## Card

Wrap the accordion in a [Card](/docs/components/card).

{{example "accordion-card" align="start" height="435px"}}

## RTL

The accordion uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "accordion-rtl" align="start" height="300px"}}

## API Reference

### Accordion

| Attribute | Values | Default |
| --- | --- | --- |
| `data-type` | `"single" \| "multiple"` | `"single"` |

Like Base UI, a single accordion can close its open item, so all items can be closed.

### Accordion Item

| Attribute | Values | Default |
| --- | --- | --- |
| `data-value` | String | |
| `data-state` | `"open"`: the item starts open | |
| `data-disabled` | Boolean | |

### Events

| Event | Target | Detail |
| --- | --- | --- |
| `accordion:change` | `accordion` | `{ value }` |

### Keyboard and Accessibility

- Enter and Space toggle the item. As in Base UI, the arrow keys do not move focus.
- The trigger of a disabled item stays in the Tab order (`aria-disabled="true"`).
