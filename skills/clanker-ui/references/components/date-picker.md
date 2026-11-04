# Date Picker (`date-picker`)

Group `overlays`. Needs `core`, `forms`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `date-picker` (root) | `data-format` string; `data-placeholder` string |  |

Other parts: `date-picker-value`.

Part attributes: `data-date-picker-content` boolean; `data-date-picker-input` boolean; `data-date-picker-preset` boolean; `data-date-picker-trigger` boolean.

Other options named in the docs: `data-keep-open` any; `data-lang` string; `data-name` any; `data-value` any.

Events: `date-picker:open`; `date-picker:close`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-overlays.min.js`):

- `datePickerOpen(target) → boolean`
- `datePickerClose(target, { restoreFocus = true }?) → boolean`

## Full text

### Date Picker

A composition, as in shadcn: a `button` trigger, a `popover-content` popup, and a `calendar`, joined by the `date-picker` root.

```html
<div data-slot="date-picker" data-placeholder="Pick a date" data-format="long" data-required>
  <button type="button" id="due-trigger" data-slot="button" data-variant="outline" data-date-picker-trigger><svg data-lucide="calendar"></svg><span data-slot="date-picker-value"></span></button>
  <div data-slot="popover-content" data-date-picker-content data-align="start" aria-label="Choose date">
    <div data-slot="native-select-wrapper">
      <select data-slot="native-select" data-date-picker-preset aria-label="Presets"><option value="">Select</option><option value="1">Tomorrow</option></select>
      <svg data-lucide="chevron-down" data-slot="native-select-icon"></svg>
    </div>
    <div data-slot="calendar" data-name="due"></div>
  </div>
</div>
```

- Focus moves to the first part in the popup that can take focus (the previous-month button, or the next-month button when the previous one is disabled), as the Base UI popover does; Tab moves to the next-month button, then to the selected day or today. Escape, an outside click, or focus leaving closes it; a single date selection closes it unless `data-keep-open`. Focus returns to the trigger.
- The trigger shows the formatted date (`data-format`: `long|medium|short|full|numeric`; ranges show `from - to`). The language is the calendar language: `data-lang` on the calendar, else the nearest `lang` attribute, else the browser language. `lang="en"` gives US English (`October 29, 2026`); set `lang="en-GB"` on the `date-picker` root or on `<html>` for `29 October 2026`, or `data-lang="de"` on the calendar for `29. Oktober 2026`. Month and day names in the popup use the same language.
- Value from code: `data-value` on the calendar in the markup, or `calendarSetValue(calendar, "2026-10-29")` later. Both update the trigger text and the form value at once, without a `calendar:change` event (pass `{ emit: true }` for the event).
- Label the trigger with `<label for="due-trigger">` (a button is a labelable element) or `aria-labelledby`. In a vertical `field` the picker and its trigger fill the width, like an input.
- `data-required` on the root: in a form the picker needs a date. The kit adds a visually hidden `required` input to the root; a `data-slot="form"` shows the `field-error` of the field around the trigger (`data-error-value-missing` on the root), sets `aria-invalid` on the trigger (or the `data-date-picker-input`), and focuses it on submit. The calendar `data-name` still submits the value. `data-required` on the calendar is a different option: a click on the selected day does not clear it.
- `data-date-picker-input` on an input (for example in an `input-group`, with an icon button as the trigger) shows the date, parses typed dates on `change`, and opens the popup on ArrowDown. Typed text is read as ISO `yyyy-m-d`, as a numeric date in the order of the calendar language (en-US `m/d/yyyy`, de `d.m.yyyy`, ja `yyyy/m/d`), or as day, month name, and year in the language's long date order (`June 4, 2025`, `1. Juni 2025`). The year needs 4 digits; localized digits are accepted. Empty text clears the date. Text that does not parse keeps the old date and sets `aria-invalid="true"` on the input until the next valid change.
- A preset value is a day offset or an ISO date. The demo also shows date of birth, time, dialog, and RTL compositions. Not built: the natural language picker (needs chrono-node).
