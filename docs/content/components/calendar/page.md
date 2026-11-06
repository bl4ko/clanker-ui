---
title: Calendar
description: A calendar component that allows users to select a date or a range of dates.
---

{{example "calendar-demo" height="24rem"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-overlays.min.css`, and their `.min.js` files.

## Usage

```html
<div data-slot="calendar" data-value="2026-10-28" class="rounded-lg border"></div>
```

The kit renders the grid in the root. Each day is a Button part, as in shadcn: `<td data-slot="calendar-day" data-day="2026-10-28"><button data-slot="button" data-calendar-day-button data-variant="ghost" data-size="icon">28</button></td>`. Read the value with `calendarGetValue(el)` or listen for `calendar:change`. To change it from code, set `data-value` or `data-month`, or call `calendarSetValue(el, value)`.

Month and day names come from `Intl` in the nearest `lang`. The week starts on Monday; set `data-week-start="0"` for Sunday, as in the shadcn examples.

## About

The shadcn `Calendar` is built on React DayPicker. The kit calendar has the same parts, states, and keyboard model, in plain JavaScript.

## Date Picker

You can use the calendar to build a date picker. See the [Date Picker](/docs/components/date-picker) page for more information.

## Persian / Hijri / Jalali Calendar

The kit calendar uses the Gregorian calendar only. Month and weekday names follow the `lang` of the calendar (`calendar: "gregory"`), and the digits stay localized.

## Selected Date (With TimeZone)

The kit reads and writes local dates (`2026-10-28`) without a time, so a selected date has no time zone offset. Today comes from the local clock; set `data-today` to change it.

## Basic

A basic calendar. We used `class="rounded-lg border"` to style the calendar.

{{example "calendar-basic" height="24rem"}}

## Range Calendar

Use `data-mode="range"` to enable range selection.

{{example "calendar-range" height="auto"}}

## Month and Year Selector

Use `data-caption-layout="dropdown"` to show month and year dropdowns.

{{example "calendar-caption" height="24rem"}}

## Presets

{{example "calendar-presets" height="650px"}}

## Date and Time Picker

{{example "calendar-time" height="600px"}}

## Booked dates

{{example "calendar-booked-dates" height="24rem"}}

## Custom Cell Size

{{example "calendar-custom-days" height="560px"}}

You can customize the size of calendar cells using the `--cell-size` CSS variable. You can also make it responsive by using breakpoint-specific values:

```html
<div data-slot="calendar" class="rounded-lg border [--cell-size:--spacing(11)] md:[--cell-size:--spacing(12)]"></div>
```

Or use fixed values in your app CSS:

```css
.booking [data-slot="calendar"] { --cell-size: 2.75rem; }
@media (width >= 48rem) { .booking [data-slot="calendar"] { --cell-size: 3rem; } }
```

## Week Numbers

Use `data-show-week-number` to show week numbers.

{{example "calendar-week-numbers" height="24rem"}}

## RTL

The calendar uses logical properties and mirrors the navigation. Set `dir="rtl"` and a `lang` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "calendar-rtl" height="24rem"}}

The names come from `Intl` in the `lang` of the calendar. `lang="ar"` shows Arabic-Indic digits; `lang="ar-u-nu-latn"` shows Latin digits, like the date-fns `arSA` locale.

## API Reference

### Calendar

| Attribute | Values | Default |
| --- | --- | --- |
| `data-mode` | `"single" \| "multiple" \| "range"` | `"single"` |
| `data-value` | `2026-10-28`; `multiple`: dates with spaces; `range`: `2026-10-01/2026-10-07` | |
| `data-month` | The first month shown: `2026-10` | The month of the value, or today |
| `data-months` | The number of months side by side | `1` |
| `data-caption-layout` | `"label" \| "dropdown" \| "dropdown-months" \| "dropdown-years"` | `"label"` |
| `data-start-year`, `data-end-year` | The years of the year dropdown | 100 years before today to this year |
| `data-min`, `data-max` | The first and last date to select | |
| `data-disabled-dates` | Dates and ranges (`a/b`) with spaces | |
| `data-disabled-weekdays` | Weekdays `0` (Sunday) to `6`, with spaces | |
| `data-disabled` | Boolean: disables the calendar | |
| `data-week-start` | `0` to `6` | `1` (Monday) |
| `data-button-variant` | The variant of the previous and next buttons | `"ghost"` |
| `data-outside-days` | `"false"` hides the days of the next and previous months | `"true"` |
| `data-show-week-number` | Boolean | |
| `data-fixed-weeks` | Boolean: always six weeks | |
| `data-required` | Boolean: a click on the selected day does not clear it | |
| `data-name` | The name of the hidden inputs for forms (`from/to` in `range`) | |
| `data-today` | Today: `2026-10-28` | The local date |
| `data-lang`, `data-label-previous`, `data-label-next` | Overrides of the language and the button names | |

The kit sets `data-mode`, `data-caption-layout`, and `data-button-variant` when they are missing, and `data-multiple-months="true"` with more than one month. A change to an attribute renders the grid again.

### Calendar Day

The kit adds the `calendar-day` cells. Style them with these states.

| Attribute | Values |
| --- | --- |
| `data-selected`, `data-today`, `data-outside`, `data-disabled`, `data-hidden` | `"true"` |
| `data-range-start`, `data-range-middle`, `data-range-end` | `"true"` |

The kit adds these parts. Do not write them: `calendar-months`, `calendar-month`, `calendar-nav`, `calendar-button-previous`, `calendar-button-next`, `calendar-month-caption`, `calendar-caption-label`, `calendar-dropdowns`, `calendar-dropdown-root`, `calendar-dropdown`, `calendar-month-grid`, `calendar-weekdays`, `calendar-weekday`, `calendar-weeks`, `calendar-week`, `calendar-week-number-header`, `calendar-week-number`, and `calendar-day`.

### Events

| Event | Target | Detail |
| --- | --- | --- |
| `calendar:change` | `calendar` | `{ value, mode, source }`: `day`, `api`, `reset` |
| `calendar:navigate` | `calendar` | `{ value }` |

### JavaScript

Import these functions from `clanker-ui.js`.

- `calendarGetValue(el) → value`: `"2026-10-28"`, an array (`multiple`), `{ from, to }` (`range`), or `null`.
- `calendarSetValue(el, value, { emit = false, month = true }?) → boolean`: `month` shows the month of the first selected date.
- `calendarSetMonth(el, "2026-10") → boolean`

### Keyboard and Accessibility

- Arrows move by day or week, Home and End to the ends of the week, PageUp and PageDown by month, Shift+PageUp and Shift+PageDown by year. Disabled days are skipped. In RTL, the left and right arrows change places.
- Each month caption is a live region, so the new month is announced. The grid has `aria-label` (the month caption) and `aria-multiselectable`.
- One ARIA difference from shadcn, by design: the navigation has a name (`aria-label`, default `Navigation bar`); React DayPicker leaves it empty.
