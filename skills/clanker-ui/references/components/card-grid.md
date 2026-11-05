# Card Grid (`card-grid`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `card-grid` (root) | `data-size` `lg`, `sm` |  |

## Full text

### Card Grid

```html
<div data-slot="card-grid">
  <div data-slot="card">
    <div data-slot="cover" data-tone="2"><span>Piranesi</span><span>Susanna Clarke</span></div>
    <div data-slot="card-header"><h3 data-slot="card-title">Piranesi</h3><p data-slot="card-description">Susanna Clarke</p></div>
  </div>
  <div data-slot="card">
    <div data-slot="cover" data-tone="3"><span>Project Hail Mary</span><span>Andy Weir</span></div>
    <div data-slot="card-header"><h3 data-slot="card-title">Project Hail Mary</h3><p data-slot="card-description">Andy Weir</p></div>
  </div>
</div>
```

- A grid of records with a preview (books, products, projects): as many columns of at least 13rem as fit (`data-size="sm"` 10rem, `lg` 18rem), a 1rem gap, one column on a narrow screen. The cards of one row have one height, and a `card-footer` sits at the bottom of its card.
