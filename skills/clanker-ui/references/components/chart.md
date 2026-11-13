# Chart (`chart`)

Group `chart`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `chart` (root) |  | `data-sparkline` |
| `chart-legend-indicator` (kit adds) |  | `data-shape` |
| `chart-stat-delta` (kit adds) |  | `data-direction`, `data-tone` |
| `chart-tooltip-item` (kit adds) |  | `data-total` |

Other parts: `chart-stat`.

Kit adds: `chart-footer`, `chart-legend`, `chart-legend-item`, `chart-legend-label`, `chart-live`, `chart-plot`, `chart-probe`, `chart-stat-change`, `chart-stat-description`, `chart-stat-header`, `chart-stat-label`, `chart-stat-period`, `chart-stat-trend`, `chart-stat-value`, `chart-svg`, `chart-table`, `chart-table-toggle`, `chart-tooltip`, `chart-tooltip-extra`, `chart-tooltip-indicator`, `chart-tooltip-items`, `chart-tooltip-label`, `chart-tooltip-name`, `chart-tooltip-value`.

Other options named in the docs: `data-part` any.

Events: `chart:active` `{ index, key, row }`; `chart:legend` `{ key, visible, hidden }`; `chart:view` `{ view }`.

Exports (readable set: `clanker-ui-chart.js`; `.min` set: `clanker-ui-chart.min.js`):

- `chart(element, data, options) → { update(data, options), destroy() }`: In `clanker-ui-chart.js`, see [Chart](https://github.com/bl4ko/clanker-ui#chart).
- `sparkline(element, values, options?) → { update, destroy }`
- `statTile(element, options) → { update(options), destroy() }`

```html
<div id="visitors"></div>
<div id="revenue-tile"></div>
```

## Full text

### Chart

SVG charts with no library, in `clanker-ui-chart.js`. Follows the dataviz rules: fixed categorical order, thin marks, one axis, a legend for two or more series (none for one), hover and keyboard tooltip, and a table view for every chart and sparkline.

```js
import { chart, sparkline, statTile } from "./clanker-ui-chart.js"

const view = chart(document.getElementById("visitors"), {
  rows: [{ month: "January", desktop: 186, mobile: 80 }, { month: "February", desktop: 305, mobile: 200 }],
  config: { desktop: { label: "Desktop", icon: "monitor" }, mobile: { label: "Mobile" } },
}, { type: "bar", x: "month", label: "Visitors, 2024" })
view.update({ rows: next }, { stack: true })
view.destroy()
```

- `data` is `{ rows, config }` or a rows array. `update()` keeps what you do not pass; `update(null, options)` changes options only. A failed `update()` throws and keeps the last good rows, config, options, and view. Calling `chart()` again on the same element destroys the old chart first. `destroy()` restores the element.
- `config` is shadcn's `ChartConfig`: `{ key: { label, color, theme: { light, dark }, icon } }`. `color` is a slot number (`1`–`8`), a token name (`"chart-1"`), or a CSS color. A color with `url(`, `src(`, a quote, or a backslash throws a `TypeError`. Without `color`, a key gets `--chart-N` from its position in `config`; the `x` key, and for pie, donut, and radial the value columns, do not count. Keys that are not in `config` follow in data order. Color follows the entity: a key with no data, a missing row, or a hidden series never repaints the others. More than 8 series without a color throws a `RangeError`.
- The element becomes `data-slot="chart"` with `data-type`. Size: 16 / 9 (pie, donut, radar, radial: square, max 250 px); set `height` in options or CSS. A `ResizeObserver` redraws it. `--color-<key>` is set for every series and slice; characters other than letters, digits, `_`, and `-` become `-` (`"page views"` gives `--color-page-views`).

| Option | Values |
| --- | --- |
| `type` | `bar` (default), `area`, `line`, `pie`, `donut`, `radar`, `radial` |
| `x`, `y` | Category key (default: the first non-numeric column). `y`: one key or a list. |
| `label`, `summary` | Name for the `aria-label`, table caption, and table region. `summary` replaces the automatic `aria-label`. |
| `format`, `tickFormat`, `xFormat`, `labelFormat`, `locale`, `timeZone` | `Intl` options or a function. Axis ticks are compact from 1,000. `locale` sets the language of numbers and dates (`"de-DE"`); it defaults to `<html lang>` when it is a valid language tag, else to the browser language. `timeZone` (an IANA name such as `"UTC"` or `"Europe/Ljubljana"`) places the time axis ticks and shows every date and time in that zone; the default is the browser time zone. An unknown zone throws a `RangeError`. |
| `stack` | `true` or `"expand"` for `bar` and `area` |
| `horizontal`, `labels`, `diverging`, `highlight`, `barSize` | Bar options |
| `curve`, `dots`, `gradient`, `zero`, `domain` | `monotone` (default), `linear`, `step`; dots; gradient fill; `zero: false`; fixed `[min, max]` (finite numbers or `null`; else a `TypeError`) |
| `references` | Bar, line, and area: a list of `{ value, label, tone, position }` (a dashed line) or `{ from, to, label, tone, position }` (a band with dashed edges). See [Reference lines and time axis](chart.md). |
| `scale`, `connectNulls` | `scale: "time"` (line and area) puts each row at its date. `connectNulls`: `true` or a list of keys; the line goes across missing values. |
| `grid`, `valueAxis`, `categoryAxis`, `legend`, `table` | `false` hides each part |
| Pie and donut | `labels: "value" \| "percent" \| "name"`, `labelPosition: "inside"`, `innerRadius`, `center`, `highlight` |
| Radar | `grid: "polygon" \| "circle" \| "none"`, `fill: false`, `dots`, `max` |
| Radial | `stacked`, `startAngle`, `endAngle`, `max`, `track`, `grid`, `labels`, `center`, `innerRadius` |
| `tooltip` | `{ indicator: "line" \| "dot" \| "dashed", hideLabel, hideIndicator }` |
| `view`, `animate` | `"chart"` or `"table"`; `animate: false` skips the entrance animation |

- The SVG is `role="application"` with `tabindex="0"`, so screen readers pass the arrow keys to it. Its accessible name is an automatic summary; the marks inside are hidden from assistive technology, and the table view has every value. Pointer: crosshair for line and area, per-mark tooltip otherwise. Keyboard: arrows move between points, Home, End, Escape. A polite live region reads the readout. The legend is a toolbar of toggle buttons with one tab stop. The table button switches to an accessible `<table>`.
- Colors: `--chart-1`…`--chart-8` is a categorical palette with 8 distinct hues, validated with the dataviz `validate_palette.js` in light and dark. shadcn's own `--chart-1`…`--chart-5` are a gray ramp (the base color), which does not separate series; the kit uses the validated hues by default. The shadcn base schemes of `clanker-ui-themes.css` (`data-scheme="neutral"`, `zinc`, ...) set the exact shadcn gray ramp; the accessibility layer and the editor schemes keep hues. Brand colors: override `--chart-1`… in `app.css` (light and dark), or give a series `color` in `config`.
- `--chart-surface` is the gap and dot ring color (default `--card`); set it to the background the chart sits on.
- The tooltip sits next to the pointer. When it is too wide for either side, it goes above the hovered points, or below them when there is more room. `--chart-tooltip-border` is its border color (default `--border` at 50 %, like shadcn); the editor schemes where `--background` equals `--card` set it to the full `--border` in dark mode.
- A label inside a fill uses `--chart-ink-light` (`#fff`) or `--chart-ink-dark` (`#0b0b0b`), whichever has the higher WCAG contrast against the fill. Override both on `[data-slot="chart"]`.
- Charts redraw on `theme:change` while they are in the document. A removed chart closes its tooltip, is not tracked, and redraws when it is inserted again. A destroyed chart never redraws.
- Fixed labels (chart names, legend, table button, table header, summary sentences) come from `strings` (see [Localization](https://github.com/bl4ko/clanker-ui#localization)); `data-string-<key>` on the chart element or an ancestor overrides one chart.
- Parts: `chart-plot`, `chart-svg`, `chart-tooltip` (`-label`, `-items`, `-item`, `-indicator`, `-name`, `-value`), `chart-legend`, `chart-legend-item`, `chart-table`, `chart-table-toggle`, `chart-footer`, `chart-live`. SVG marks use `data-part`.

#### Reference lines and time axis

```js
chart(document.getElementById("weight"), {
  rows: [
    { day: "2026-09-01", plan: 84, actual: 84.2 },
    { day: "2026-09-08", actual: 83.6 },
    { day: "2026-10-01", plan: 82 },
    { day: "2026-10-20", actual: 80.6 },
    { day: "2026-11-01", plan: 80, actual: 79.8 },
  ],
  config: { actual: { label: "Actual" }, plan: { label: "Plan", color: "chart-other" } },
}, {
  type: "line", x: "day", scale: "time", connectNulls: true, zero: false, label: "Weight, kg",
  references: [{ value: 78, label: "Goal 78 kg" }, { from: 79, to: 81, label: "Healthy", tone: "chart-2" }],
})
```

- A reference is a dashed line at `value`, or a band from `from` to `to` with a light fill and dashed edges, across the plot (vertical in a horizontal bar chart). It is not in the legend or the tooltip. The value axis grows to show it, except past a fixed `domain`. `tone` is a color as in `config` (default `--muted-foreground`). The label is small text in `--muted-foreground` at the end of the line (`position: "start"` puts it at the start); it moves to the other side of the line, or is left out, when it would leave the plot or cover another label. A sparkline draws no reference labels. The automatic summary names each reference (`referenceAt`, `referenceBand`), and the table view has a second table with each reference. A reference that is not an object with a finite `value`, or a finite `from` and `to`, throws a `TypeError`; so do references on pie, donut, radar, and radial charts.
- `scale: "time"` needs a `Date` or an ISO date (`2026-10-01`, or a date and time) in every `x` value; else it throws a `TypeError`. Give the rows in time order. The axis picks ticks of minutes, hours, days, weeks (from Monday), months, or years, so that the labels do not touch (24 px apart). A tick shows the day (`Oct 3`), the time, the month (`Oct`), or the year (on a January tick and on year ticks). An `xFormat` object sets the `Intl` options of all ticks; an `xFormat` function gets the tick `Date`. Hover finds the nearest point by time; the arrow keys move through the rows in data order.
- Data with one row per plan point and one row per measurement leaves gaps in each series; `connectNulls` draws each series as one line.

#### Stat tile and sparkline

```js
statTile(el, { label: "Total revenue", value: 1250, format: { style: "currency", currency: "USD" }, delta: 0.125, period: "vs last month", trend: [820, 940, 1250] })
sparkline(el, [980, 1020, 1284], { area: true, label: "Requests per minute" })
```

- `statTile` renders `data-slot="chart-stat"` (`role="group"`) with `chart-stat-label`, `chart-stat-value`, `chart-stat-delta` (`data-direction`, `data-tone`, icon, signed percent, `chart-stat-period`), and an optional `chart-stat-trend` sparkline.
- The tile draws its own card (border, radius, background, shadow, 24 px padding): call it on a plain `<div>` in a grid of tiles. Inside a `card` (any depth) it drops that frame, so a tile in a card has one border.
- Value: from 10,000 the value is compact (`notation: "compact"`, at most 1 decimal: `€30.5K`). Pass `format: { style: "currency", currency: "EUR", notation: "standard" }` for the full amount, or a function. `deltaFormat` defaults to `{ style: "percent", maximumFractionDigits: 1, signDisplay: "exceptZero" }`; your options are merged over it, and a `minimumFractionDigits` above the default maximum raises the maximum (`{ minimumFractionDigits: 2 }` gives `+12.50%`). `goodWhen: "down"` when a fall is good. Options: `label`, `value`, `format`, `delta`, `deltaFormat`, `period`, `goodWhen`, `trend`, `trendOptions`, `icon`, `description`, `locale`. `locale` sets the number locale (default as for charts). A failed `update()` throws and keeps the last good options; a `statTile()` call that throws leaves the element as it was.
- `sparkline` is a line (or `area: true`) without axes or legend, in `--chart-other` with the latest point in the accent. It keeps the tooltip, the keyboard readout, and the table view: a toggle next to the line shows a transposed table (one row per series, one column per point). Pass `table: false` only when the same values are visible next to it.
