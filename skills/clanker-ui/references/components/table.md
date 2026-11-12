# Table (`table`)

Group `core`. Needs none. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `table-container` | `data-sticky-header` any | `data-fits` |
| `table-row` | `data-state` string |  |

Other parts: `table` (root), `table-body`, `table-caption`, `table-cell`, `table-footer`, `table-head`, `table-header`.

Other options named in the docs: `data-label` any; `data-layout` string.

```html
<div data-slot="table-container">
  <table data-slot="table">
    <caption data-slot="table-caption">A list of your recent invoices.</caption>
    <thead data-slot="table-header">
      <tr data-slot="table-row"><th data-slot="table-head" scope="col">Invoice</th><th data-slot="table-head" scope="col">Amount</th></tr>
    </thead>
    <tbody data-slot="table-body">
      <tr data-slot="table-row" data-state="selected"><td data-slot="table-cell">INV001</td><td data-slot="table-cell">$250.00</td></tr>
    </tbody>
    <tfoot data-slot="table-footer">
      <tr data-slot="table-row"><td data-slot="table-cell">Total</td><td data-slot="table-cell">$250.00</td></tr>
    </tfoot>
  </table>
</div>
```

## Full text

### Table

`table-container` > `table` > `table-caption`, `table-header`, `table-body`, `table-footer`, `table-row` (`data-state="selected"`), `table-head`, `table-cell`. Sorting, filtering, selection, column visibility, and paging are app code; the demo builds a data table with `h()`, `aria-sort`, a row actions `dropdown-menu`, a column `dropdown-menu`, and `toast`.

Kit extensions on `table-container`:

- `data-sticky-header`: the header row stays in view while the page scrolls. The kit measures the table (`ResizeObserver`) and sets `data-fits` when it fits its box; then the box and a `card` around it use `overflow: clip` instead of a scroll box, so the `table-header` sticks to the page (`top: var(--table-header-top, 0px)`, the page or card background). A wider table keeps its sideways scroll and a normal header. Below a sticky `site-header`, set `--table-header-top` to its height.
- `data-layout="stack"`: below 40rem each row is a block of label and value lines for phone tables where no column can go. The label is the `data-label` of each `table-cell` (a `--table-label-width` column, default 7rem, hidden from screen readers); a cell without `data-label` takes the full width. The header row is visually hidden, and the kit sets the roles `table`, `rowgroup`, `row`, `columnheader`, `rowheader`, and `cell` (CSS `display` changes drop the table semantics in some browsers). Set it in the markup; rows added later get their roles too.
