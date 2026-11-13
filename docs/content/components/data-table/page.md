---
title: Data Table
description: Powerful table and datagrids built with the Table component and a few lines of JavaScript.
---

{{example "data-table-demo" align="start" height="auto"}}

## Introduction

A data table is a [Table](/docs/components/table) with app code for sorting, filtering, column visibility, row selection, and paging. shadcn/ui builds it with TanStack Table. The kit has no table engine: the parts give the look, and the example module above does the rest in about 50 lines. Use it as a start and change it for your data.

## Installation

Load `clanker-ui.css` and `clanker-ui.js`. The demo uses [Table](/docs/components/table), [Checkbox](/docs/components/checkbox), [Dropdown Menu](/docs/components/dropdown-menu), [Input](/docs/components/input), and [Button](/docs/components/button).

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-forms.min.css`, `clanker-ui-overlays.min.css`, and their `.min.js` files.

## Structure

```text
div (toolbar: filter input, Columns dropdown menu)
div.rounded-md.border
└── table-container
    └── table
        ├── table-header → table-row → table-head (checkbox, columns, actions)
        └── table-body → table-row (one per item) → table-cell
div (selection text, Previous and Next buttons)
```

Mark each cell of a column with `data-column="<id>"`, so one query finds the whole column.

## Row Actions

Each row has a [Dropdown Menu](/docs/components/dropdown-menu) with an icon button. Listen for `dropdown-menu:select` on the table and read the row from the item:

```js
root.addEventListener("dropdown-menu:select", event => {
  if (event.detail.item.dataset.js === "copy") navigator.clipboard.writeText(event.detail.item.closest("tr").dataset.id)
})
```

## Sorting

Put `data-sort` on the header cell (see [Table](/docs/components/table)). The kit makes the head a ghost button with the sort icon, sets `aria-sort`, and sorts the rows. With filtering and paging, call `preventDefault()` on `table:sort` and sort your own list, as this example does.

## Filtering

Listen for `input` on the filter field and set `hidden` on the rows that do not match. Show a `No results.` row when no row is left.

## Visibility

A Columns menu with `dropdown-menu-checkbox-item` parts sends `dropdown-menu:change` with `{ value, checked }`. Set `hidden` on every cell with that `data-column`.

## Row Selection

A [Checkbox](/docs/components/checkbox) in the first cell of each row sends `checkbox:change`. The header checkbox selects all visible rows; set `data-indeterminate` on it when only some are selected. Give a selected row `data-state="selected"` for the muted background of the table row.

## Kit frame

The kit also has the frame of the data table of the shadcn tasks example and `dashboard-01`: a `data-table` root with a `data-table-toolbar`, the table in a bordered `table-container` with a muted header, and a `data-table-pagination` row. See the [Data Table block](/docs/blocks/data-table) for a full page.

{{example "data-table-frame" align="start" height="auto"}}

## RTL

The table parts use logical properties. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "data-table-rtl" align="start" height="auto"}}

## API Reference

### Data Table

The kit frame parts. They are CSS only.

| Part | Element |
| --- | --- |
| `data-table` | The root of the frame. |
| `data-table-toolbar` | The row above the table: a start group (filters) and an end group (actions), as two `div` children. |
| `data-table-pagination` | The row below the table: selection text, page text, and page buttons. |
| `data-table-selection` | The selection text in the pagination row. |
| `data-table-text` | A cell text that truncates. |
