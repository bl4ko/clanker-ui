# Rating (`rating`)

Group `core`. Needs none. CSS only.

Other parts: `rating` (root).

Other options named in the docs: `data-size` `sm`.

## Full text

### Rating

```html
<span data-slot="rating" role="img" aria-label="4 of 5 stars"><svg data-lucide="star" fill="currentColor"></svg><svg data-lucide="star" fill="currentColor"></svg><svg data-lucide="star" fill="currentColor"></svg><svg data-lucide="star" fill="currentColor"></svg><svg data-lucide="star"></svg></span>
```

- A read-only star rating: a row of 16 px icons (`data-size="sm"` 12 px) with a 2 px gap. Filled stars (`fill="currentColor"`) are `--foreground`, empty stars `--muted-foreground`. Give the root `role="img"` and an `aria-label` with the value. For a rating input, use a `radio-group` (one item per value, each with a label such as "4 stars").
