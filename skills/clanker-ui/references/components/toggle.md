# Toggle (`toggle`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `toggle` (root) | `data-size` `default`, `lg`, `sm`; `data-variant` `default`, `outline` | `data-state` |

Other options named in the docs: `data-name` any.

Events: `toggle:change` `{ pressed, value }`.

## Full text

### Toggle and Toggle Group

```html
<button type="button" data-slot="toggle" data-variant="outline" data-size="sm|lg" aria-pressed="false">Bold</button>
<div data-slot="toggle-group" data-type="single|multiple" data-variant="outline" data-size="sm" data-spacing="2|0|1|3|4|6|8" data-orientation="horizontal|vertical" data-value="bold,italic" data-name="format" data-required data-disabled>
  <button type="button" data-slot="toggle-group-item" data-value="bold" aria-label="Bold"><svg data-lucide="bold"></svg></button>
</div>
```

A `toggle` gets `tabindex="0"` like the Base UI toggle.

- `data-required`: the last pressed item cannot be unpressed (a view switch, a filter, or a rating that always has one value), and in a form the group needs a value: without one, a `data-slot="form"` shows the `field-error` (`data-error-value-missing` on the group) and focuses the first item.
- `data-name` submits the value: a visually hidden input after the group (single), or one hidden input per value (multiple). `form.reset()` restores the authored value.
- `data-value` is the value (comma-separated for multiple). A later change from code presses those items without a `toggle-group:change` event. The kit does not write `data-value`; read the value from `toggle-group:change`. Like shadcn, the group gets `data-spacing` (default `2`, an 8 px gap with separate rounded items; `0` joins them) and `data-orientation` (default `horizontal`), and `--gap` from `data-spacing`. Items get the group `data-variant` and `data-size` (the group wins over the item; `default` when neither has one), its `data-spacing`, and `data-pressed` while pressed.
