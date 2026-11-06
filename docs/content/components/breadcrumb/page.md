---
title: Breadcrumb
description: Displays the path to the current resource using a hierarchy of links.
---

{{example "breadcrumb-demo"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-layout.min.css`, and their `.min.js` files.

## Usage

```html
<nav data-slot="breadcrumb">
  <ol data-slot="breadcrumb-list">
    <li data-slot="breadcrumb-item"><a data-slot="breadcrumb-link" href="/">Home</a></li>
    <li data-slot="breadcrumb-separator"></li>
    <li data-slot="breadcrumb-item"><a data-slot="breadcrumb-link" href="/components">Components</a></li>
    <li data-slot="breadcrumb-separator"></li>
    <li data-slot="breadcrumb-item"><span data-slot="breadcrumb-page">Breadcrumb</span></li>
  </ol>
</nav>
```

## Composition

Use the following composition to build a breadcrumb:

```text
breadcrumb
└── breadcrumb-list
    ├── breadcrumb-item
    │   └── breadcrumb-link
    ├── breadcrumb-separator
    ├── breadcrumb-item
    │   └── breadcrumb-link
    ├── breadcrumb-separator
    └── breadcrumb-item
        └── breadcrumb-page
```

## Basic

A basic breadcrumb with a home link and a components link.

{{example "breadcrumb-basic"}}

## Custom separator

Put your own icon in `breadcrumb-separator` to change the separator.

{{example "breadcrumb-separator"}}

## Dropdown

You can put a [Dropdown Menu](/docs/components/dropdown-menu) in a `breadcrumb-item` to show a dropdown in the breadcrumb.

{{example "breadcrumb-dropdown"}}

## Collapsed

Use `breadcrumb-ellipsis` to show a collapsed state when the breadcrumb is too long.

{{example "breadcrumb-ellipsis"}}

## Link component

The link is a plain `<a data-slot="breadcrumb-link">`. Use the `href` of your router.

{{example "breadcrumb-link"}}

## RTL

The breadcrumb uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "breadcrumb-rtl"}}

## API Reference

### Breadcrumb

A `<nav>`. The kit adds `aria-label="breadcrumb"` when it has none.

### Breadcrumb List

An `<ol>` with the items and separators.

### Breadcrumb Item

An `<li>` for a link, a page, an ellipsis, or a dropdown menu.

### Breadcrumb Link

An `<a>` with `href`.

### Breadcrumb Page

A `<span>` for the current page. The kit adds `aria-current="page"`, `role="link"`, and `aria-disabled="true"`.

### Breadcrumb Separator

An `<li>`, hidden from screen readers. The kit adds the chevron when it is empty; put your own icon in it to change it.

### Breadcrumb Ellipsis

A `<span>`. The kit adds the ellipsis icon and hides the part from screen readers; give its button a name. In a button it takes the button size.
