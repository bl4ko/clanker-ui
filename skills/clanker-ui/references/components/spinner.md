# Spinner (`spinner`)

Group `core`. Needs none. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `spinner` (root) | `data-size` `lg`, `sm`, `xl` |  |

```html
<svg data-slot="spinner"></svg>
<button type="button" data-slot="button" disabled><svg data-slot="spinner" data-size="sm" role="none"></svg>Saving</button>
```

## Full text

### Progress, Spinner

- `<svg data-slot="spinner" data-size="sm|lg|xl"></svg>` (sizes are a kit extension: 12, 24, 32 px; default 16 px): the kit fills the icon and adds `role="status"` and `aria-label="Loading"` (`strings.loading`). Use `role="none"` for a decorative spinner in a labelled control. Spinners keep turning under reduced motion.
