---
title: Table
description: A responsive table component.
---

{{example "table-demo" height="30rem"}}

## Installation

Load `clanker-ui.css`. The table needs no JavaScript; `data-sticky-header` and `data-layout="stack"` use the core module (`clanker-ui.js`).

With the minified group files, load `clanker-ui-core.min.css`.

## Usage

```html
<div data-slot="table-container">
  <table data-slot="table">
    <caption data-slot="table-caption">A list of your recent invoices.</caption>
    <thead data-slot="table-header">
      <tr data-slot="table-row">
        <th data-slot="table-head" scope="col" class="w-[100px]">Invoice</th>
        <th data-slot="table-head" scope="col">Status</th>
        <th data-slot="table-head" scope="col">Method</th>
        <th data-slot="table-head" scope="col" class="text-right">Amount</th>
      </tr>
    </thead>
    <tbody data-slot="table-body">
      <tr data-slot="table-row">
        <td data-slot="table-cell" class="font-medium">INV001</td>
        <td data-slot="table-cell">Paid</td>
        <td data-slot="table-cell">Credit Card</td>
        <td data-slot="table-cell" class="text-right">$250.00</td>
      </tr>
    </tbody>
  </table>
</div>
```

## Composition

Use the following composition to build a table:

```text
table-container
└── table
    ├── table-caption
    ├── table-header
    │   └── table-row
    │       ├── table-head
    │       └── table-head
    ├── table-body
    │   └── table-row
    │       ├── table-cell
    │       └── table-cell
    └── table-footer
```

## Footer

Use a `<tfoot data-slot="table-footer">` to add a footer to the table.

{{example "table-footer"}}

## Actions

A table showing actions for each row using a [Dropdown Menu](/docs/components/dropdown-menu).

{{example "table-actions"}}

## Sticky Header

A kit extension: `data-sticky-header` on `table-container` keeps the header row in view while the page scrolls past the table. The kit measures the table: when it fits its box, the box (and a `card` around it) clips with `overflow: clip` instead of scrolling, so the header sticks to the page, not to the box. A wider table keeps its sideways scroll and a normal header. The header gets the page or the card background. Below a sticky site header, set `--table-header-top` on the container to its height (`--table-header-top: var(--header-height, 3rem)`).

The header sticks to the nearest scroll container. In an app that is the page; in this preview it is a 16rem box.

{{example "table-sticky-header" height="24rem"}}

## Stacked Rows

A kit extension for phone tables where every column is needed: `data-layout="stack"` on `table-container`. Below 40rem each row is a block, and each cell shows its `data-label` at the start (7rem column, `--table-label-width`) and its value next to it. A cell without `data-label` takes the full row (the item name, a row action). The header row is visually hidden, and the kit sets `role="table"`, `rowgroup`, `row`, `columnheader`, `rowheader`, and `cell`, because some browsers drop the table semantics when CSS changes `display`. The label is hidden from screen readers (`content: attr(data-label) / ""`): they announce the column header.

{{example "table-stack" height="auto"}}

## Data Table

You can use the table parts to build more complex data tables with sorting, filtering, and pagination. See the [Data Table](/docs/components/data-table) documentation for more information, and the [Data Table block](/docs/blocks/data-table) for a full page.

## RTL

The table uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "table-rtl" height="auto"}}

## API Reference

### Table Container

The `table-container` part is a `div` around the table. It scrolls the table horizontally when it is wider than its container.

| Attribute | Values | Default |
| --- | --- | --- |
| `data-sticky-header` | boolean (kit extension): the header row sticks to the page scroll when the table fits | |
| `data-layout` | `"stack"` (kit extension): rows as label and value blocks below 40rem | |

| State | Meaning |
| --- | --- |
| `data-fits` | Set by the kit with `data-sticky-header`: the table fits its box, so the header sticks. |

Custom properties: `--table-header-top` (the sticky header offset, default `0px`) and `--table-label-width` (the label column of stacked rows, default `7rem`).

### Table

The `table` part is the `<table>` element.

### Table Row

| Attribute | Values | Default |
| --- | --- | --- |
| `data-state` | `"selected"`: the muted background of a selected row | |

### Other parts

`table-caption` (`<caption>`, below the table), `table-header` (`<thead>`), `table-body` (`<tbody>`), `table-footer` (`<tfoot>`), `table-head` (`<th>`), and `table-cell` (`<td>`).

### Table Cell

| Attribute | Values | Default |
| --- | --- | --- |
| `data-label` | the column name that a stacked row shows next to the value (kit extension) | |
