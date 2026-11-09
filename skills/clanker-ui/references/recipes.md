# Recipes

App patterns made from kit parts. Each one works under the strict CSP. Component details: `components/<name>.md`.

## Set values from code

| Control | Set | Event |
| --- | --- | --- |
| Checkbox, switch | toggle `data-checked` on the button | none |
| Radio group | `data-checked` on the item (the group `data-value` is read only at init) | none |
| Select, combobox | `data-value` on the root (combobox multiple: `"a,b"`) | none |
| Toggle group | `data-value` on the root | none |
| Tabs | `data-value` on the root (selects that tab) | none |
| Dropdown radio group, checkbox item | `data-value` on the radio group, `data-checked` on the item | none |
| Date picker | `calendarSetValue(calendar, "2026-10-29")` | `{ emit: true }` sends `calendar:change` |
| Calendar or date picker range | `data-min`, `data-max` on the `calendar` (ISO dates); the days update at once | none |
| Input, textarea, native select | `.value` | none |
| Slider | `input.value`, then dispatch `input` | the dispatched one |

Fill an edit form after `form.reset()` or in its `reset` listener; the kit keeps those values.

## Form in a dialog or a sheet

Block: `overlay-form`. `<form data-slot="form">` is the direct child of `dialog-content` or `sheet-content` and holds the header, the fields, and the footer; the kit makes it `display: contents`, so the content gap and the sheet column stay. The submit button is in the footer. Close on success with `dialogClose()` in `form:submit`.

The sheet footer is a column: the primary first, Cancel under it (dialog footers are a row: Cancel first). A `field-group data-columns="2"` stacks to one column in a narrow sheet; that is expected.

Long form: the fields go in a `sheet-body` (drawer: `drawer-body`, dialog: `dialog-body`) between the header and the footer. Only the body scrolls; the footer stays in view:

```html
<dialog data-slot="sheet-content" data-side="right">
  <form data-slot="form" id="customer-form">
    <div data-slot="sheet-header"><h2 data-slot="sheet-title">Edit customer</h2><p data-slot="sheet-description">Changes apply to new invoices.</p></div>
    <div data-slot="sheet-body">
      <div data-slot="field" role="group"><label data-slot="field-label" for="c-name">Name</label><input data-slot="input" id="c-name" name="name" required data-error-value-missing="Enter a name."></div>
    </div>
    <div data-slot="sheet-footer"><button type="submit" data-slot="button">Save customer</button><button type="button" data-slot="button" data-variant="outline" data-sheet-close>Cancel</button></div>
  </form>
</dialog>
```

## Several rules on one field

Omit `data-error-custom-error` and `data-error` on the control, and call `setCustomValidity(message)` in the control's own `input` or `change` listener (it runs before the kit validates). The kit shows `validationMessage`, so each rule has its own message. `setCustomValidity("")` clears it.

```js
receipt.addEventListener("change", () => {
  const file = receipt.files[0]
  receipt.setCustomValidity(!file && amount.valueAsNumber > 75 ? "Add a receipt for expenses over €75." : file && file.size > 10e6 ? "Use a file of 10 MB or less." : "")
})
```

## Star rating

Block: `overlay-form`. Input: a `radio-group` with `data-name`, `data-required`, and `data-error-value-missing`; one horizontal `field` per score, highest first, each label a read-only `rating` (`role="img"`, `aria-label="4 of 5 stars"`) and a word ("Liked it"). No app CSS. A read-only score: the `rating` part with the number as text next to it (`4.5`).

## Card grid

Block: `card-grid`. Records with an image or a preview: the `card-grid` part with one `card` per record, the image or a `cover` first, then the `card-header` with the title and a muted detail line, and the status `badge` in the `card-footer`. A `cover` is placeholder art from tokens (`data-tone`, an `svg` drawn with `currentColor`, `aria-hidden="true"`), never a flat gray box and never text on the art: the title and author go in the card body. Keep icons and badges out of the card title, so long titles wrap. A feature card above the grid ("This month's pick"): `card data-orientation="horizontal"` with the `cover` first and a `div` with the header, the content, and a `card-footer` row of actions.

## Shared header on static pages

One module builds the header on every page; each page has an empty `<header data-slot="site-header" data-size="lg" id="app-header"></header>` (it keeps its height, so nothing moves) and loads `<script type="module" src="/header.js"></script>`.

```js
import { h, icon } from "/vendor/clanker-ui/clanker-ui.min.js"

const links = [["/", "Overview"], ["/expenses.html", "Expenses"], ["/settings.html", "Settings"]]
const here = location.pathname === "/index.html" ? "/" : location.pathname
const link = slot => ([href, text]) => h("a", { href, "data-slot": slot, "aria-current": href === here ? "page" : null }, text)

document.getElementById("app-header").replaceChildren(
  h("div", { "data-slot": "dropdown-menu", "data-hide-from": "md" },
    h("button", { type: "button", "data-slot": "button", "data-variant": "ghost", "data-size": "icon", "data-dropdown-menu-trigger": "", "aria-label": "Menu" }, icon("menu")),
    h("div", { "data-slot": "dropdown-menu-content", "data-align": "start" }, ...links.map(link("dropdown-menu-item")))),
  h("a", { "data-slot": "brand", href: "/" }, h("span", { "data-slot": "brand-mark", "data-size": "sm" }, icon("wallet")), "Tally"),
  h("nav", { "data-slot": "site-header-nav", "aria-label": "Main", "data-show-from": "md" }, ...links.map(link(null))),
  h("div", { "data-slot": "site-header-actions" },
    h("button", { type: "button", "data-slot": "button", "data-variant": "ghost", "data-size": "icon", "data-theme-set": "toggle", "aria-label": "Dark mode" }, icon("contrast"))),
)
```

Every primary link is in both the nav and the phone menu.

## Back link and breadcrumb in the top-header shell

The `site-header` holds the app nav, so a detail page puts the path above its title, as the first child of `page`:

```html
<main data-slot="page">
  <nav data-slot="breadcrumb">
    <ol data-slot="breadcrumb-list">
      <li data-slot="breadcrumb-item"><a data-slot="breadcrumb-link" href="/books.html">Books</a></li>
      <li data-slot="breadcrumb-separator"></li>
      <li data-slot="breadcrumb-item"><span data-slot="breadcrumb-page">Piranesi</span></li>
    </ol>
  </nav>
  <div data-slot="page-header">...</div>
</main>
```

One level up only: `<a data-slot="button" data-variant="ghost" data-size="sm" href="/books.html"><svg data-lucide="arrow-left"></svg>Books</a>` in the same place.

## Category bar chart

Spend by category, top items: one series, so one color (`--chart-1`). Sort descending, show values on the bars, and size the chart to the bars, so the card has no empty band:

```js
rows.sort((a, b) => b.total - a.total)
chart(el, { rows, config: { total: { label: "Spent" } } }, { type: "bar", horizontal: true, labels: true, x: "category", height: rows.length * 36 + 32, format: { style: "currency", currency: "EUR" }, label: "Spend by category, October" })
```

More than 8 categories: the top 7 and "Other" (`--chart-other`). When each category has a fixed color elsewhere on the page (dots in a table), show that dot next to the category name, and keep the bars one color.

## Status strips and uptime bars

- Fill tokens for status marks (bars, dots, meters, strips): `--success-fill`, `--warning-fill`, `--error-fill`, `--info-fill`, and `--neutral-fill` for no data. 3:1 or more on the card, same hue in light and dark. `--*-text` tokens are for text; `badge` and `alert` variants are for words.
- 30 to 90 bars, gap `calc(var(--spacing) * 0.5)`, bar height 32 px; below 40rem of strip width show the last 30 days. A legend with the same fills and words.
- One shared readout placed with `position()`, not a tooltip per bar. The strip is one Tab stop; Left and Right move a current bar, Escape hides the readout, and a hidden `role="status"` reads the same text.

```html
<div class="uptime" tabindex="0" role="group" aria-label="API: 99.95 % uptime, last 90 days" id="api-uptime"></div>
<div class="uptime-tip" popover="manual" id="uptime-tip"></div>
<p class="sr-only" role="status" id="uptime-live"></p>
```

```css
.uptime { display: flex; gap: calc(var(--spacing) * 0.5); height: calc(var(--spacing) * 8); border-radius: var(--radius-sm); }
.uptime:focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; }
.uptime > span { flex: 1 1 0; min-width: 0; border-radius: var(--radius-sm); background-color: var(--success-fill); }
.uptime > [data-state="degraded"] { background-color: var(--warning-fill); }
.uptime > [data-state="down"] { background-color: var(--error-fill); }
.uptime > [data-state="none"] { background-color: var(--neutral-fill); }
.uptime > [data-current] { outline: 2px solid var(--foreground); outline-offset: 1px; }
.uptime-tip { margin: 0; inset: auto; padding: calc(var(--spacing) * 2) calc(var(--spacing) * 3); border: 1px solid var(--border); border-radius: var(--radius-md); background-color: var(--popover); color: var(--popover-foreground); box-shadow: var(--shadow-md); font-size: var(--text-xs); line-height: var(--text-xs--line-height); pointer-events: none; }
```

```js
import { h, position } from "/vendor/clanker-ui/clanker-ui.min.js"

const words = { up: "No downtime", degraded: "Degraded", down: "Outage", none: "No data" }
const day = new Intl.DateTimeFormat("en", { month: "short", day: "numeric", timeZone: "UTC" })
const tip = document.getElementById("uptime-tip")
const live = document.getElementById("uptime-live")
let stop = null

function strip(el, days) {
  el.replaceChildren(...days.map(d => h("span", { "data-state": d.state, "data-label": `${day.format(new Date(d.date))}: ${words[d.state]}` })))
  const show = bar => {
    for (const b of el.children) b.toggleAttribute("data-current", b === bar)
    tip.textContent = bar.dataset.label
    if (!tip.matches(":popover-open")) tip.showPopover()
    stop?.()
    stop = position(tip, bar, { side: "top", sideOffset: 6 })
  }
  const hide = () => {
    stop?.()
    stop = null
    if (tip.matches(":popover-open")) tip.hidePopover()
    for (const b of el.children) b.removeAttribute("data-current")
  }
  el.addEventListener("pointerover", event => event.target.parentElement === el && show(event.target))
  el.addEventListener("pointerleave", hide)
  el.addEventListener("blur", hide)
  el.addEventListener("keydown", event => {
    const bars = [...el.children]
    const at = bars.findIndex(b => b.hasAttribute("data-current"))
    if (event.key === "Escape") return hide()
    const step = { ArrowLeft: -1, ArrowRight: 1 }[event.key]
    if (!step) return
    event.preventDefault()
    const bar = bars[Math.max(0, Math.min(bars.length - 1, at < 0 ? bars.length - 1 : at + step))]
    show(bar)
    live.textContent = bar.dataset.label
  })
}

strip(document.getElementById("api-uptime"), days)
```

`days` is `[{ date: "2026-08-01", state: "up" | "degraded" | "down" | "none" }, ...]`, oldest first. In RTL, swap the two arrow keys.

## Long pages

Many groups of similar rows (17 services in 6 groups): show a summary row per group ("6 of 6 operational") and open only the groups with a problem (`collapsible` or `accordion`). Lists over about 20 rows: pagination or "Show more".

## Toast after a page change

A toast for an action that ends on another page (delete on the edit page, then go to the list): store it before the navigation and show it on the next page.

```js
sessionStorage.setItem("toast", JSON.stringify({ title: "Expense deleted", description: "EXP-1236 is gone." }))
location.assign("/expenses.html")
```

```js
import { toast } from "/vendor/clanker-ui/clanker-ui.min.js"

const next = sessionStorage.getItem("toast")
if (next) {
  sessionStorage.removeItem("toast")
  const { title, description } = JSON.parse(next)
  toast.success(title, { description })
}
```

No Undo in such a toast: the page that could undo is gone. Offer Undo only when the toast shows on the same page.

## File input and dropzone

A field with a visible label, a dropzone around a hidden file input, and the chosen file as an `attachment` (group `chat`; the one-file set has it). The input is named by the field label and described by the hint:

```html
<div data-slot="field" role="group">
  <label data-slot="field-label" for="receipt" id="receipt-label">Receipt</label>
  <label data-slot="empty" data-variant="outline" class="dropzone">
    <input type="file" id="receipt" name="receipt" accept="image/*,application/pdf" class="sr-only" aria-labelledby="receipt-label" aria-describedby="receipt-hint" required data-error-value-missing="Add a receipt.">
    <span data-slot="empty-header">
      <span data-slot="empty-icon" data-variant="icon"><svg data-lucide="cloud-upload"></svg></span>
      <span data-slot="empty-title">Drop a file here, or click to choose one</span>
      <span data-slot="empty-description" id="receipt-hint">PNG, JPG, or PDF, up to 10 MB.</span>
    </span>
  </label>
  <div data-slot="attachment" data-size="sm" hidden id="receipt-file">
    <div data-slot="attachment-media"><svg data-lucide="file-text"></svg></div>
    <div data-slot="attachment-content"><span data-slot="attachment-title"></span><span data-slot="attachment-description"></span></div>
    <div data-slot="attachment-actions"><button type="button" data-slot="attachment-action" aria-label="Remove file"><svg data-lucide="x"></svg></button></div>
  </div>
</div>
```

```css
.dropzone { cursor: pointer; }
.dropzone:has(input:focus-visible) { outline: 2px solid var(--ring); outline-offset: 2px; }
.dropzone[data-dragging] { border-color: var(--primary); }
```

```js
const zone = document.querySelector(".dropzone")
const input = document.getElementById("receipt")
const file = document.getElementById("receipt-file")
const size = new Intl.NumberFormat("en", { style: "unit", unit: "kilobyte", maximumFractionDigits: 0 })
zone.addEventListener("dragover", event => { event.preventDefault(); zone.dataset.dragging = "" })
zone.addEventListener("dragleave", () => delete zone.dataset.dragging)
zone.addEventListener("drop", event => {
  event.preventDefault()
  delete zone.dataset.dragging
  input.files = event.dataTransfer.files
  input.dispatchEvent(new Event("change", { bubbles: true }))
})
input.addEventListener("change", () => {
  const chosen = input.files[0]
  file.hidden = !chosen
  if (!chosen) return
  file.querySelector('[data-slot="attachment-title"]').textContent = chosen.name
  file.querySelector('[data-slot="attachment-description"]').textContent = size.format(chosen.size / 1000)
})
file.querySelector('[data-slot="attachment-action"]').addEventListener("click", () => {
  input.value = ""
  input.dispatchEvent(new Event("change", { bubbles: true }))
  input.focus()
})
```

The zone stays (drop another file to replace it), and the input stays in the label, so the field validates and the kit shows its `field-error`. A rule such as "receipt over €75" uses `setCustomValidity` (Several rules on one field).

## Lists in cards and longer text

- In a `card-content`: `item-group` with `data-size="sm"` items (`xs` for one-line rows such as a team list). A small `cover` in `item-media` is 40 px wide (32 px in `sm`, 24 px in `xs`) and shows no text. With `item-separator` between rows: group gap 0 and `xs` items.
- `item-description` clamps at 2 lines (shadcn). Longer secondary text (a review, a note) is a plain `p` in `item-content` after the description; it is 14 px `--foreground`. For a long muted note use `<p data-slot="card-description">` in a card or `field-description` in a form, not app CSS.

## Phone tables: status with the amount

At 390 px a table keeps identity, status, amount, and action. When the status column does not fit, hide it below `sm` and show the status under the amount in the amount cell:

```html
<td data-slot="table-cell" data-align="end">
  <span data-slot="text-stack"><span>€1,240.00</span><span data-hide-from="sm">Overdue</span></span>
</td>
<td data-slot="table-cell" data-show-from="sm"><span data-slot="badge" data-variant="warning"><svg data-lucide="clock"></svg>Overdue</span></td>
```

Block `data-table` does the same with the title and status.

When no column can go (a shop list with quantity, price, link, and action), use stacked rows: `data-layout="stack"` on the `table-container` and a `data-label` on each value cell. Below 40rem each row is a block of label and value lines; the kit keeps the table roles:

```html
<div data-slot="table-container" data-layout="stack">
  <table data-slot="table">
    <thead data-slot="table-header"><tr data-slot="table-row"><th data-slot="table-head" scope="col">Item</th><th data-slot="table-head" scope="col" data-align="end">Price</th></tr></thead>
    <tbody data-slot="table-body"><tr data-slot="table-row"><td data-slot="table-cell">Chef's knife</td><td data-slot="table-cell" data-label="Price" data-align="end">€79.00</td></tr></tbody>
  </table>
</div>
```

A long table in a card: `data-sticky-header` on the `table-container` keeps the header row in view on the page scroll, without a second scroll box.

## Dashboard in the top-header shell

The `dashboard` content (section cards, chart, table) without a sidebar: the `site-header data-size="lg"` of `data-table` (brand, nav, actions), then `<main data-slot="page">` with a `page-header` ("Overview" and its actions) and the `dashboard` sections in the same order. The `site-header-title` rule of the sidebar shell does not apply: the `page-title` is the `h1`.
