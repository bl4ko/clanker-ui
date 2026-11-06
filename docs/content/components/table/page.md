---
title: Table
description: A responsive table component.
---

{{example "table-demo" height="30rem"}}

## Installation

Load `clanker-ui.css`. The table needs no JavaScript.

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

## Data Table

You can use the table parts to build more complex data tables with sorting, filtering, and pagination. See the [Data Table](/docs/components/data-table) documentation for more information, and the [Data Table block](/docs/blocks/data-table) for a full page.

## RTL

The table uses logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "table-rtl" height="auto"}}

## API Reference

### Table Container

The `table-container` part is a `div` around the table. It scrolls the table horizontally when it is wider than its container.

### Table

The `table` part is the `<table>` element.

### Table Row

| Attribute | Values | Default |
| --- | --- | --- |
| `data-state` | `"selected"`: the muted background of a selected row | |

### Other parts

`table-caption` (`<caption>`, below the table), `table-header` (`<thead>`), `table-body` (`<tbody>`), `table-footer` (`<tfoot>`), `table-head` (`<th>`), and `table-cell` (`<td>`).
