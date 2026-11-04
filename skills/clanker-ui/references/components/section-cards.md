# Section Cards (`section-cards`)

Group `core`. Needs none. CSS only.

Other parts: `section-cards` (root).

## Full text

### Section Cards

```html
<div data-slot="section-cards">
  <div data-slot="card">
    <div data-slot="card-header">
      <div data-slot="card-description">Total Revenue</div>
      <div data-slot="card-title">$1,250.00</div>
      <div data-slot="card-action"><span data-slot="badge" data-variant="outline"><svg data-lucide="trending-up"></svg>+12.5%</span></div>
    </div>
    <div data-slot="card-footer">
      <div>Trending up this month <svg data-lucide="trending-up"></svg></div>
      <div data-slot="card-description">Visitors for the last 6 months</div>
    </div>
  </div>
</div>
```

- The KPI cards of shadcn `dashboard-01`. Columns follow the width of the grid itself: 1, then 2 from 34rem, then 4 from 61rem; exactly 3 cards go to 3 columns from 44rem. Use 2, 3, 4, or 8 cards.
- Each card is a subgrid row of the grid, so the headers and the footers of one row line up when a label wraps. A card with a `card-content` takes three rows.
- `card-title` is the value: 24 px (30 px when the card is at least 250 px wide), weight 600, tabular numbers. It wraps instead of being cut. The footer holds a medium trend line with an icon and a `card-description`.
- `statTile()` elements can be the children too.
- The trend `badge` holds any short delta (`+12.5%`, `4 late`). Compute values and deltas from the data and today's date (`new Date()`), not from fixed strings.
