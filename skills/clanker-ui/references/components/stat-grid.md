# Stat Grid (`stat-grid`)

Group `core`. Needs none. CSS only.

Other parts: `stat-grid` (root).

Other options named in the docs: `data-size` `sm`.

## Full text

### Stat Grid

```html
<dl data-slot="stat-grid">
  <div>
    <dt>Uptime</dt>
    <dd>99.98%</dd>
    <dd>Last 30 days</dd>
  </div>
  <div>
    <dt>Requests</dt>
    <dd>1.2M <span data-slot="badge" data-variant="success">+4%</span></dd>
    <dd>Last 30 days</dd>
  </div>
</dl>
```

- Static numbers without JavaScript in one card surface with 1 px dividers. Each child `div` holds a `dt` (label), a `dd` (value: 24 px, weight 600, tabular numbers, wraps instead of being cut), and an optional second `dd` (muted note).
- Columns follow the width of the list: 1, 2 from 20rem, and from 36rem 3 (3, 5, 6, or 9 items) or 4 (4, 7, 8 items).
- `data-size="sm"` shows the values in 14 px, weight 500: the facts of a detail page (owner, created, status).
