# Button Group (`button-group`)

Group `forms`. Needs `core`. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `button-group` (root) | `data-orientation` `horizontal`, `vertical` |  |
| `button-group-separator` | `data-orientation` `horizontal`, `vertical` |  |

Other parts: `button-group-text`.

## Full text

### Button Group

```html
<div data-slot="button-group" role="group" aria-label="Actions" data-orientation="horizontal|vertical">
  <button type="button" data-slot="button" data-variant="outline">Archive</button>
  <div data-slot="button-group-separator" data-orientation="vertical" role="none"></div>
  <span data-slot="button-group-text">.com</span>
</div>
```

Nest groups for spacing. A `select`, `dropdown-menu`, `popover`, `tooltip`, or `hover-card` root in a group joins its trigger to the group. CSS only.
