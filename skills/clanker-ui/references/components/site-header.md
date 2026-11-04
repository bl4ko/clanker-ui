# Site Header (`site-header`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `site-header` (root) | `data-size` `lg` |  |

Other parts: `site-header-actions`, `site-header-nav`, `site-header-title`.

## Full text

### Site Header

```html
<header data-slot="site-header">
  <button data-slot="sidebar-trigger"></button>
  <div data-slot="separator" data-orientation="vertical"></div>
  <h1 data-slot="site-header-title">Documents</h1>
  <div data-slot="site-header-actions">
    <button type="button" data-slot="button" data-variant="ghost" data-size="icon-sm" data-theme-set="toggle" aria-label="Dark mode"><svg data-lucide="contrast"></svg></button>
  </div>
</header>
```

- The top bar of a page, as in shadcn `dashboard-01`: `--header-height` high (default 3rem), a bottom border, sticky at the top, 1rem gutters (1.5rem from 64rem). A `sidebar-trigger` first and a vertical `separator` get the shadcn spacing. `site-header-title` is 16 px, weight 500, on one line. `site-header-actions` goes to the end.
- Without a sidebar it is the app header: a `brand` link, then `site-header-nav` with links (muted, `aria-current="page"` in the foreground), then `site-header-actions`. `data-size="lg"` makes the bar 3.5rem high.
- A `breadcrumb` can stand in place of the title.
