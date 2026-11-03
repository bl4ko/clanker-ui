# Table (`table`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `table-row` | `data-state` string |  |

Other parts: `table` (root), `table-body`, `table-caption`, `table-cell`, `table-container`, `table-footer`, `table-head`, `table-header`.

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
