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
| `format`, `tickFormat`, `xFormat`, `labelFormat`, `locale` | `Intl` options or a function. Axis ticks are compact from 1,000. `locale` defaults to `<html lang>` when it is a valid language tag, else to the browser language. |
| `stack` | `true` or `"expand"` for `bar` and `area` |
| `horizontal`, `labels`, `diverging`, `highlight`, `barSize` | Bar options |
| `curve`, `dots`, `gradient`, `zero`, `domain` | `monotone` (default), `linear`, `step`; dots; gradient fill; `zero: false`; fixed `[min, max]` (finite numbers or `null`; else a `TypeError`) |
| `grid`, `valueAxis`, `categoryAxis`, `legend`, `table` | `false` hides each part |
| Pie and donut | `labels: "value" \| "percent" \| "name"`, `labelPosition: "inside"`, `innerRadius`, `center`, `highlight` |
| Radar | `grid: "polygon" \| "circle" \| "none"`, `fill: false`, `dots`, `max` |
| Radial | `stacked`, `startAngle`, `endAngle`, `max`, `track`, `grid`, `labels`, `center`, `innerRadius` |
| `tooltip` | `{ indicator: "line" \| "dot" \| "dashed", hideLabel, hideIndicator }` |
| `view`, `animate` | `"chart"` or `"table"`; `animate: false` skips the entrance animation |

- The SVG is `role="application"` with `tabindex="0"`, so screen readers pass the arrow keys to it. Its accessible name is an automatic summary; the marks inside are hidden from assistive technology, and the table view has every value. Pointer: crosshair for line and area, per-mark tooltip otherwise. Keyboard: arrows move between points, Home, End, Escape. A polite live region reads the readout. The legend is a toolbar of toggle buttons with one tab stop. The table button switches to an accessible `<table>`.
- `--chart-surface` is the gap and dot ring color (default `--card`); set it to the background the chart sits on.
- A label inside a fill uses `--chart-ink-light` (`#fff`) or `--chart-ink-dark` (`#0b0b0b`), whichever has the higher WCAG contrast against the fill. Override both on `[data-slot="chart"]`.
- Charts redraw on `theme:change` while they are in the document. A removed chart closes its tooltip, is not tracked, and redraws when it is inserted again. A destroyed chart never redraws.
- Fixed labels (chart names, legend, table button, table header, summary sentences) come from `strings` (see [Localization](https://github.com/bl4ko/clanker-ui#localization)); `data-string-<key>` on the chart element or an ancestor overrides one chart.
- Parts: `chart-plot`, `chart-svg`, `chart-tooltip` (`-label`, `-items`, `-item`, `-indicator`, `-name`, `-value`), `chart-legend`, `chart-legend-item`, `chart-table`, `chart-table-toggle`, `chart-footer`, `chart-live`. SVG marks use `data-part`.

#### Stat tile and sparkline

```js
statTile(el, { label: "Total revenue", value: 1250, format: { style: "currency", currency: "USD" }, delta: 0.125, period: "vs last month", trend: [820, 940, 1250] })
sparkline(el, [980, 1020, 1284], { area: true, label: "Requests per minute" })
```

- `statTile` renders `data-slot="chart-stat"` (`role="group"`) with `chart-stat-label`, `chart-stat-value` (compact from 10,000), `chart-stat-delta` (`data-direction`, `data-tone`, icon, signed percent, `chart-stat-period`), and an optional `chart-stat-trend` sparkline. `goodWhen: "down"` when a fall is good. Options: `label`, `value`, `format`, `delta`, `deltaFormat`, `period`, `goodWhen`, `trend`, `trendOptions`, `icon`, `description`, `locale`. `locale` sets the number locale (default as for charts). A failed `update()` throws and keeps the last good options; a `statTile()` call that throws leaves the element as it was.
- `sparkline` is a line (or `area: true`) without axes or legend, in `--chart-other` with the latest point in the accent. It keeps the tooltip, the keyboard readout, and the table view: a toggle next to the line shows a transposed table (one row per series, one column per point). Pass `table: false` only when the same values are visible next to it.
