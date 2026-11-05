# Calendar (`calendar`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `calendar` (root) | `data-button-variant` any; `data-caption-layout` any; `data-disabled` any; `data-disabled-dates` any; `data-disabled-weekdays` any; `data-fixed-weeks` any; `data-label-next` any; `data-label-previous` any; `data-lang` any; `data-max` any; `data-min` any; `data-mode` `multiple`, `range`, `single`; `data-month` any; `data-months` any; `data-name` string; `data-outside-days` `false`, `true`; `data-required` any; `data-show-week-number` any; `data-today` any; `data-value` string; `data-week-start` any |  |
| `calendar-day` (kit adds) |  | `data-disabled`, `data-hidden`, `data-outside`, `data-range-end`, `data-range-middle`, `data-range-start`, `data-selected`, `data-today` |

Kit adds: `calendar-button-next`, `calendar-button-previous`, `calendar-caption-label`, `calendar-dropdown`, `calendar-dropdown-root`, `calendar-dropdowns`, `calendar-month`, `calendar-month-caption`, `calendar-month-grid`, `calendar-months`, `calendar-nav`, `calendar-week`, `calendar-week-number`, `calendar-week-number-header`, `calendar-weekday`, `calendar-weekdays`, `calendar-weeks`.

Other options named in the docs: `data-day` any; `data-hidden` `false`, `true`.

Events: `calendar:change` `{ value, mode, source }`; `calendar:navigate` `{ value }`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-overlays.min.js`):

- `calendarGetValue(el) → value`: `"2026-10-28"`, an array (`multiple`), `{ from, to }` (`range`), or `null`.
- `calendarSetValue(el, value, { emit = false, month = true }?) → boolean`: `month` shows the month of the first selected date.
- `calendarSetMonth(el, "2026-10") → boolean`

```html
<div data-slot="calendar" data-mode="single" data-value="2026-10-28" data-month="2026-10" data-name="date" data-min="2026-10-01" data-disabled-weekdays="0 6"></div>
```

## Full text

### Calendar

`<div data-slot="calendar" data-mode="single|multiple|range" data-value="2026-10-28" data-name="date"></div>`. The kit renders the grid. Each day is a Button part, as in shadcn: `<td data-slot="calendar-day" data-day="2026-10-28"><button data-slot="button" data-calendar-day-button data-variant="ghost" data-size="icon" data-day="10/28/2026">28</button></td>` (`data-day` on the button is the local date text). The cell of the focused day has `data-focused="true"`. In `range` mode with a value, every button has `data-range-start`, `data-range-middle`, `data-range-end` (`true` or `false`). A disabled previous or next button has `aria-disabled="true"` and `tabindex="-1"`, as in react-day-picker, so the date picker focuses the next part. The root gets `data-mode="single"`, `data-caption-layout="label"`, and `data-button-variant="ghost"` when it has none (the shadcn defaults of `mode`, `captionLayout`, and `buttonVariant`; the generated CSS selects on them), and `data-multiple-months="true"` with more than one month. `data-button-variant` is also the `data-variant` of the previous and next buttons. Week numbers have two digits (`05`).

| Attribute | Meaning |
| --- | --- |
| `data-value` | `2026-10-28`; `multiple`: space-separated dates; `range`: `2026-10-01/2026-10-07` |
| `data-month`, `data-months` | First month shown (`2026-10`), number of months side by side |
| `data-min`, `data-max`, `data-disabled-dates`, `data-disabled-weekdays`, `data-disabled` | Limits. Ranges use `a/b`. Weekdays `0` (Sunday) to `6`. A change from code (for example `data-max` set to today when the page loads) renders the grid again. |
| `data-week-start` | `0`–`6`, default `1` (Monday) |
| `data-caption-layout` | `label`, `dropdown`, `dropdown-months`, `dropdown-years`; years from `data-start-year` to `data-end-year` (default: 100 years before today to this year, or the years of `data-min` and `data-max`). With a year dropdown, navigation stops at January of the first and December of the last year, as in react-day-picker; for future dates set `data-end-year` or `data-max`. A `data-min` in a later year extends the default end year, and a `data-max` in an earlier year extends the default start year. |
| `data-button-variant` | Button variant of the previous and next buttons, default `ghost` |
| `data-outside-days="false"`, `data-show-week-number`, `data-fixed-weeks`, `data-required` | rdp options (`data-show-week-number` is the shadcn `showWeekNumber` prop) |
| `data-name` | Hidden input(s) for forms: one per date in `multiple`, `from/to` in `range` |
| `data-today`, `data-lang`, `data-label-previous`, `data-label-next` | Overrides. Names come from `Intl` in the nearest `lang`. |

Keyboard (APG date grid): arrows by day or week, Home and End to the week ends, PageUp and PageDown by month, Shift+PageUp and Shift+PageDown by year. Disabled days are skipped; RTL is supported. Cell size: `--cell-size`.

- Month and weekday names always use the Gregorian calendar (`calendar: "gregory"`), also for languages whose default calendar differs (`fa`, `th`, `ar-SA`, ...). Digits stay localized.
- Each month caption is a live region (`role="status"`, `aria-live="polite"`), as in react-day-picker: the caption label in the `label` layout, a visually hidden span after the dropdowns in the dropdown layouts. The kit keeps it in place and changes its text, so the new month is announced. The grid has `aria-label` (the month caption) and `aria-multiselectable` (`false` in `single` mode).
- One ARIA difference from shadcn, by design: the navigation has a name (`aria-label`, `strings.calendarNavigation`, default `Navigation bar`); react-day-picker leaves it empty.
- English day labels use ordinals, as date-fns `PPPP` (`Tuesday, October 27th, 2026`); other languages use `Intl`. Days before the first or after the last month that navigation can show are hidden (`data-hidden="true"`).
- State (selection, shown month) survives removal and insertion. API calls before insertion work; the language (`lang` of an ancestor) and form reset are wired when the calendar enters the document.
