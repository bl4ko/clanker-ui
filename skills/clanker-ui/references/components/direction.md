# Direction (`direction`)

Group `core`. Needs none. CSS and JS.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui-core.min.js`):

- `direction(el = <html>) → "ltr" | "rtl"`

```html
<div dir="rtl" lang="ar">
  <button type="button" data-slot="button" data-variant="outline"><svg data-lucide="arrow-right"></svg>التالي</button>
</div>
```

## Full text

### Direction

Set `dir="rtl"` on `<html>` or a container. Kit styles use logical properties (`inset-inline`, `margin-inline`, `padding-inline`, `border-inline`, `text-align: start`) for everything that follows the reading direction; icons that point along the reading direction flip with `:dir(rtl)`; keyboard arrows follow the visual direction.

- Physical sides stay where a value names one: sheet `data-side`, drawer `data-swipe-direction`, popup `data-side="left|right"`, toast swipe directions, and parts that JavaScript places (popups, the tooltip arrow, the slider thumb, the chart tooltip).
- Sidebar `data-side="left|right"` means inline start and inline end: in RTL a `left` sidebar sits on the right, and its rail, border, collapsed tooltip, inset margin, and mobile sheet follow.
- The questionnaire keeps the upstream keys in RTL (ArrowLeft goes to the previous item).
- Chart plots stay left to right (`direction: ltr` on the SVG, like Recharts), so axes, labels, and negative numbers read the same in every page; the legend, table, and tooltip follow the page direction.
