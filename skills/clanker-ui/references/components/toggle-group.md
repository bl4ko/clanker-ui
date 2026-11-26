# Toggle Group (`toggle-group`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `toggle-group` (root) | `data-disabled` boolean; `data-name` string; `data-orientation` `horizontal`, `vertical`; `data-size` `lg`, `sm`; `data-spacing` `0`, `1`, `2`, `3`, `4`, `6`, `8`; `data-type` `multiple`, `single`; `data-value` string; `data-variant` `outline` |  |
| `toggle-group-item` | `data-size` `default`, `lg`, `sm`; `data-spacing` `0`; `data-value` string; `data-variant` `default`, `outline` | `data-state` `off`, `on` |

Events: `toggle-group:change` `{ value }`.

## Full text

### Toggle and Toggle Group

```html
<button type="button" data-slot="toggle" data-variant="outline" data-size="sm" aria-pressed="false">Bold</button>
<div data-slot="toggle-group" data-type="single" data-variant="outline" data-size="sm" data-spacing="2" data-orientation="horizontal" data-value="bold,italic" data-name="format" data-required="true" data-disabled="true">
  <button type="button" data-slot="toggle-group-item" data-value="bold" aria-label="Bold"><svg data-lucide="bold"></svg></button>
</div>
```

`data-size="sm|lg"` on the `toggle`. `data-type="single|multiple"`, `data-size="sm|lg"`, `data-spacing="0|1|2|3|4|6|8"`, and `data-orientation="horizontal|vertical"` on the `toggle-group`.

A `toggle` gets `tabindex="0"` like the Base UI toggle. The kit keeps `data-state="on|off"` on `toggle` and `toggle-group-item` in sync with `aria-pressed`.

Toggle group: one tab stop, arrows (RTL aware), Home, End. A group is not labelable, so `<label for>` does not name it: give the `field-label` an `id` and the group `aria-labelledby` with it. Single items use `role="radio"` and `aria-checked`, multiple items `aria-pressed`. A pressed single item can be unpressed, as in shadcn.

- `data-required`: the last pressed item cannot be unpressed (a view switch, a filter, or a rating that always has one value), and in a form the group needs a value: without one, a `data-slot="form"` shows the `field-error` (`data-error-value-missing` on the group) and focuses the first item.
- `data-name` submits the value: a visually hidden input after the group (single), or one hidden input per value (multiple). `form.reset()` restores the authored value.
