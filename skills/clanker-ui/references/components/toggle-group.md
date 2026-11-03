# Toggle Group (`toggle-group`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `toggle-group` (root) | `data-disabled` boolean; `data-orientation` `horizontal`, `vertical`; `data-size` `sm`; `data-spacing` `0`, `1`, `2`, `3`, `4`, `6`, `8`; `data-type` `multiple`, `single`; `data-value` string; `data-variant` `outline` |  |
| `toggle-group-item` | `data-size` `default`, `lg`, `sm`; `data-spacing` `0`; `data-value` string; `data-variant` `default`, `outline` | `data-state` |

Events: `toggle-group:change` `{ value }`.

## Full text

### Toggle and Toggle Group

```html
<button type="button" data-slot="toggle" data-variant="outline" data-size="sm|lg" aria-pressed="false">Bold</button>
<div data-slot="toggle-group" data-type="single|multiple" data-variant="outline" data-size="sm" data-spacing="2|0|1|3|4|6|8" data-orientation="horizontal|vertical" data-value="bold,italic" data-disabled>
  <button type="button" data-slot="toggle-group-item" data-value="bold" aria-label="Bold"><svg data-lucide="bold"></svg></button>
</div>
```

Toggle group: one tab stop, arrows (RTL aware), Home, End. Single items use `role="radio"` and `aria-checked`, multiple items `aria-pressed`. A pressed single item can be unpressed. Like shadcn, the group gets `data-spacing` (default `2`, an 8 px gap with separate rounded items; `0` joins them) and `data-orientation` (default `horizontal`), and `--gap` from `data-spacing`. Items get the group `data-variant` and `data-size` (the group wins over the item; `default` when neither has one), its `data-spacing`, and `data-pressed` while pressed.
