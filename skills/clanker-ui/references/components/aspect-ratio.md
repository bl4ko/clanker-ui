# Aspect Ratio (`aspect-ratio`)

Group `core`. Needs none. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `aspect-ratio` (root) | `data-ratio` string |  |

```html
<div data-slot="aspect-ratio" data-ratio="16/9">
  <img src="photo.jpg" alt="A sunset over purple mountains" width="1600" height="900">
</div>
```

## Full text

### Alert, Aspect Ratio, Badge, Card, Empty, Item, Separator, Skeleton

- `<div data-slot="aspect-ratio" data-ratio="16/9">` (any ratio, `"4/3"`, `"2.4"`): the kit sets `--ratio`, like shadcn. Children are not positioned; give an image `position: absolute; inset: 0; width: 100%; height: 100%` (the shadcn examples use `fill`).
