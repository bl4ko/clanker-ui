# Data Table (`data-table`)

Group `core`. Needs none. CSS only.

Other parts: `data-table` (root), `data-table-pagination`, `data-table-selection`, `data-table-text`, `data-table-toolbar`.

Other options named in the docs: `data-table-pagination` any; `data-table-selection` any; `data-table-text` any.

## Full text

### Data Table

```html
<div data-slot="data-table">
  <div data-slot="data-table-toolbar">
    <div>
      <input data-slot="input" type="search" placeholder="Filter tasks..." aria-label="Filter tasks">
    </div>
    <div>
      <button type="button" data-slot="button" data-size="sm">Add task</button>
    </div>
  </div>
  <div data-slot="table-container">
    <table data-slot="table">
      <thead data-slot="table-header"><tr data-slot="table-row"><th data-slot="table-head" scope="col">Task</th><th data-slot="table-head" scope="col" data-align="end">Hours</th></tr></thead>
      <tbody data-slot="table-body"><tr data-slot="table-row"><td data-slot="table-cell">TASK-8782</td><td data-slot="table-cell" data-align="end">12</td></tr></tbody>
    </table>
  </div>
  <div data-slot="data-table-pagination">
    <div data-slot="data-table-selection">0 of 68 row(s) selected.</div>
    <div>Page 1 of 7</div>
    <div>
      <button type="button" data-slot="button" data-variant="outline" data-size="icon-sm" aria-label="Go to previous page" disabled><svg data-lucide="chevron-left"></svg></button>
      <button type="button" data-slot="button" data-variant="outline" data-size="icon-sm" aria-label="Go to next page"><svg data-lucide="chevron-right"></svg></button>
    </div>
  </div>
</div>
```

- The frame of the shadcn data table (tasks example and `dashboard-01`): a toolbar, the table in a bordered, rounded `table-container` with a muted header, and the pagination row. Sorting, filtering, and paging are app code.
- `data-table-toolbar` has two `div` groups: filters at the start (the first grows; a text input in it is 150 to 250 px) and actions at the end. Both wrap. Small buttons in it are 32 px high, as high as the input (shadcn `h-8`). Below 40rem, when the first control of the start group is an `input` or `input-group` (the search), the search takes the whole first row, and the filters and the end group share the next row, with the end group at the end.
- `data-table-pagination` is a row of `div` groups at the end, 14 px, weight 500. `data-table-selection` is the muted selection text that fills the start.
- `data-table-text` is the text of a cell: one line, cut with an ellipsis at 32rem (or 60 % of the table width). With an icon first it is an icon and label row (the icon is muted). A sort button: a ghost `button` alone in the `table-head`, with `aria-sort` on the head.
- `data-align="end"` on a `table-head` or `table-cell` aligns numbers to the end with tabular figures; `data-align="center"` centers. A cell with only a `checkbox` is 2rem wide. A cell with an `empty` has no padding: use it with `colspan` for the empty state.
