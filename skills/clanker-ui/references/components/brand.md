# Brand (`brand`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `brand-mark` | `data-size` `sm` |  |

Other parts: `brand` (root).

## Full text

### Brand

```html
<a data-slot="brand" href="/"><span data-slot="brand-mark" data-size="sm"><svg data-lucide="layout-dashboard"></svg></span>Acme Inc.</a>
```

- The logo link of the app: `brand-mark` (a primary square, 32 px; `data-size="sm"` 24 px) and the name, weight 500 in the text size around it. In a `sidebar`, the mark uses `--sidebar-primary`. `brand-mark` also stands alone in a large `sidebar-menu-button`, before a `text-stack`.
