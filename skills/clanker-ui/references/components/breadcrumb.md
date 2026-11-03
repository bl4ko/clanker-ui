# Breadcrumb (`breadcrumb`)

Group `layout`. Needs `core`. CSS and JS.

Other parts: `breadcrumb` (root), `breadcrumb-ellipsis`, `breadcrumb-item`, `breadcrumb-link`, `breadcrumb-list`, `breadcrumb-page`, `breadcrumb-separator`.

## Full text

### Breadcrumb

```html
<nav data-slot="breadcrumb">
  <ol data-slot="breadcrumb-list">
    <li data-slot="breadcrumb-item"><a data-slot="breadcrumb-link" href="/">Home</a></li>
    <li data-slot="breadcrumb-separator"></li>
    <li data-slot="breadcrumb-item"><span data-slot="breadcrumb-ellipsis"></span></li>
    <li data-slot="breadcrumb-item"><span data-slot="breadcrumb-page">Breadcrumb</span></li>
  </ol>
</nav>
```

The kit adds `aria-label`, the chevron in an empty separator, the ellipsis icon with "More", and `aria-current="page"`. Put a `dropdown-menu` in an item for a menu; an ellipsis inside a button takes the button size.
