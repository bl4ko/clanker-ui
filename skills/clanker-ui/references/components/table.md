# Table (`table`)

Group `core`. Needs none. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `table-container` | `data-sticky-header` any | `data-fits` |
| `table-row` | `data-state` string |  |

Other parts: `table` (root), `table-body`, `table-caption`, `table-cell`, `table-footer`, `table-head`, `table-header`.

Other options named in the docs: `data-label` any; `data-layout` string; `data-sort` string; `data-sort-first` string; `data-sort-icon` any; `data-sort-toggle` any.

Events: `table:sort` `{ column, dir }`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui-core.min.js`):

- `tableSort(head, dir?)`: `head` is a `table-head` with `data-sort` (or its id); `dir` is `ascending`, `descending`, or `none` (default: the first direction of the head, `data-sort-first`). Same as a click: sets `aria-sort` and the icons, fires `table:sort`, and moves the rows.

```html
<div data-slot="table-container">
  <table data-slot="table">
    <caption data-slot="table-caption">A list of your recent invoices.</caption>
    <thead data-slot="table-header">
      <tr data-slot="table-row"><th data-slot="table-head" scope="col">Invoice</th><th data-slot="table-head" scope="col" data-sort="number" data-sort-first="descending" data-align="end">Amount</th></tr>
    </thead>
    <tbody data-slot="table-body">
      <tr data-slot="table-row" data-state="selected"><td data-slot="table-cell">INV001</td><td data-slot="table-cell" data-align="end">$250.00</td></tr>
    </tbody>
    <tfoot data-slot="table-footer">
      <tr data-slot="table-row"><td data-slot="table-cell">Total</td><td data-slot="table-cell">$250.00</td></tr>
    </tfoot>
  </table>
</div>
```

## Full text

### Table

`table-container` > `table` > `table-caption`, `table-header`, `table-body`, `table-footer`, `table-row` (`data-state="selected"`), `table-head`, `table-cell`. Filtering, selection, column visibility, and paging are app code; the demo builds a data table with `h()`, a row actions `dropdown-menu`, a column `dropdown-menu`, and `toast`.

Sorting (kit extension, opt-in): `data-sort` on a `table-head` in the `table-header`. The kit puts the head content in a ghost `button` (or uses the `button` that is already there), adds the sort icon (`chevrons-up-down`, `arrow-up`, `arrow-down`), and sets `aria-sort="none"`. A click (Enter and Space are the native button keys) goes ascending, descending, and back to the first order; the other sortable heads of the row go back to `none`. `data-sort-first="descending"` on a head starts that column with the largest value or the newest date (descending, ascending, first order). `data-sort-toggle` on the `table` (or on one head) leaves out the first order: a click on the sorted head changes between its two directions, and a click on another head starts with that head's first direction. Then the kit fires `table:sort` and, unless the listener calls `preventDefault()`, moves the rows of each `tbody`:

- The value of a cell is its `data-value`, else its text. Put the plain value in `data-value` when the text is not a plain number or date (compact numbers such as `1,2 mio. €`, a relative date), and `data-value=""` for an empty value that shows text (`n/a`). Empty values (no text, `-`, `–`, `—`) go last in both directions.
- `data-sort="number"` reads numbers in the language of the nearest `lang` (`1.234,56 €` in `sl`, `12.5 %` in `en`); `data-sort="date"` reads ISO dates and the day, month, and year order of that language (`3. 11. 2026`); `data-sort="text"` compares with `Intl.Collator` of that language (č, š, ž in their place), numbers in text by value. An empty `data-sort` (or `auto`) is `number` when every value is a number without letters, else `text`. Other values are left to app code, so an older app sort with its own `data-sort` keys keeps working.
- The sort is stable, and the third click restores the first order. Rows added later go after the known rows in the first order.
- `data-align="end"` on the head puts the icon before the label, so the label ends at the cell edge.
- `data-sort-icon` on an `svg` in an authored head `button` marks the sort icon; its `data-lucide` is the icon of the unsorted state (shadcn uses `arrow-up-down`).

Kit extensions on `table-container`:

- `data-sticky-header`: the header row stays in view while the page scrolls. The kit measures the table (`ResizeObserver`) and sets `data-fits` when it fits its box; then the box and a `card` around it use `overflow: clip` instead of a scroll box, so the `table-header` sticks to the page (`top: var(--table-header-top, 0px)`, the page or card background). A wider table keeps its sideways scroll and a normal header. Below a sticky `site-header`, set `--table-header-top` to its height.
- `data-layout="stack"`: below 40rem each row is a block of label and value lines for phone tables where no column can go. The label is the `data-label` of each `table-cell` (a `--table-label-width` column, default 7rem, hidden from screen readers); a cell without `data-label` takes the full width. The header row is visually hidden, and the kit sets the roles `table`, `rowgroup`, `row`, `columnheader`, `rowheader`, and `cell` (CSS `display` changes drop the table semantics in some browsers). Set it in the markup; rows added later get their roles too.
