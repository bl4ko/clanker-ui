# Toggle (`toggle`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `toggle` (root) | `data-size` `default`, `lg`, `sm`; `data-variant` `default`, `outline` | `data-state` |

Events: `toggle:change` `{ pressed, value }`.

## Full text

### Toggle and Toggle Group

```html
<button type="button" data-slot="toggle" data-variant="outline" data-size="sm|lg" aria-pressed="false">Bold</button>
<div data-slot="toggle-group" data-type="single|multiple" data-variant="outline" data-size="sm" data-spacing="2|0|1|3|4|6|8" data-orientation="horizontal|vertical" data-value="bold,italic" data-disabled>
  <button type="button" data-slot="toggle-group-item" data-value="bold" aria-label="Bold"><svg data-lucide="bold"></svg></button>
</div>
```

A `toggle` gets `tabindex="0"` like the Base UI toggle.
