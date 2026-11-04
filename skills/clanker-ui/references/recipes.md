# Recipes

App patterns made from kit parts. Each one works under the strict CSP. Component details: `components/<name>.md`.

## Set values from code

| Control | Set | Event |
| --- | --- | --- |
| Checkbox, switch | toggle `data-checked` on the button | none |
| Radio group | `data-checked` on the item (the group `data-value` is read only at init) | none |
| Select, combobox | `data-value` on the root (combobox multiple: `"a,b"`) | none |
| Toggle group | `data-value` on the root | none |
| Dropdown radio group, checkbox item | `data-value` on the radio group, `data-checked` on the item | none |
| Date picker | `calendarSetValue(calendar, "2026-10-29")` | `{ emit: true }` sends `calendar:change` |
| Input, textarea, native select | `.value` | none |
| Slider | `input.value`, then dispatch `input` | the dispatched one |

Fill an edit form after `form.reset()` or in its `reset` listener; the kit keeps those values.

## Form in a dialog or a sheet

Block: `overlay-form`. `<form data-slot="form">` is the direct child of `dialog-content` or `sheet-content` and holds the header, the fields, and the footer; the kit makes it `display: contents`, so the content gap and the sheet column stay. The submit button is in the footer. Close on success with `dialogClose()` in `form:submit`.

Sheet with a long form: header, a scrolling body, and the footer. Only the body scrolls:

```css
.sheet-body { flex: 1; min-height: 0; overflow-y: auto; padding-inline: calc(var(--spacing) * 4); }
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

Native radios, so the browser gives the keys (arrows) and the form value; the kit form shows the error (give every input the message). Each label comes before its input.

```html
<fieldset data-slot="field-set" class="rating">
  <legend data-slot="field-legend" data-variant="label">Rating</legend>
  <div class="stars">
    <label for="r1"><svg data-lucide="star"></svg><span class="sr-only">1 star</span></label><input type="radio" id="r1" name="rating" value="1" class="sr-only" required data-error-value-missing="Choose a rating.">
    <label for="r2"><svg data-lucide="star"></svg><span class="sr-only">2 stars</span></label><input type="radio" id="r2" name="rating" value="2" class="sr-only" data-error-value-missing="Choose a rating.">
    <label for="r3"><svg data-lucide="star"></svg><span class="sr-only">3 stars</span></label><input type="radio" id="r3" name="rating" value="3" class="sr-only" data-error-value-missing="Choose a rating.">
  </div>
</fieldset>
```

```css
.stars { display: flex; gap: calc(var(--spacing) * 1); }
.stars label { display: inline-flex; padding: calc(var(--spacing) * 1); border-radius: var(--radius-sm); color: var(--muted-foreground); cursor: pointer; }
.stars label svg { width: calc(var(--spacing) * 6); height: calc(var(--spacing) * 6); }
.stars label:has(~ input:checked) { color: var(--primary); }
.stars label:has(~ input:checked) svg { fill: currentColor; }
.stars label:has(+ input:focus-visible) { outline: 2px solid var(--ring); outline-offset: 2px; }
```

A read-only score: the icons and the number as text (`4.5 of 5`), no inputs.

## Card grid

Block: `card-grid`. Records with an image or a cover: a grid of `card` with the art first, then title, a muted detail line, and a status `badge`. Placeholder art comes from tokens (a gradient of two app tokens, initials or the title in it), never flat gray boxes. Keep icons and badges outside the title box, so long titles wrap.

```css
.grid { display: grid; gap: calc(var(--spacing) * 4); grid-template-columns: repeat(auto-fill, minmax(min(100%, 12rem), 1fr)); }
```

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

- Fill tokens for status marks (bars, dots, meters, strips): `--success-fill`, `--warning-fill`, `--error-fill`, `--info-fill`, and `--muted` for no data. Same hue in light and dark, 3:1 on the card. `--*-text` tokens are for text; `badge` and `alert` variants are for words.
- A strip of 30 to 90 bars: gap `calc(var(--spacing) * 0.5)`, radius `var(--radius-sm)`, bar height 32 px. Below 40rem of strip width show the last 30 days. A legend with the same fills and words.
- One shared readout placed with `position()` ([components/tooltip.md](components/tooltip.md)), not a tooltip per bar.
- Keyboard: the strip is one Tab stop (`tabindex="0"`, `role="group"`, `aria-label` with the summary, "Uptime 99.95 %, last 90 days"). Left and Right move a current bar (`data-current` for the outline), place the readout on it, and write the same text into a visually hidden `role="status"` element. Escape hides the readout.

## Long pages

Many groups of similar rows (17 services in 6 groups): show a summary row per group ("6 of 6 operational") and open only the groups with a problem (`collapsible` or `accordion`). Lists over about 20 rows: pagination or "Show more".
