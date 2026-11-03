# Skeleton (`skeleton`)

Group `core`. Needs none. CSS only.

Other parts: `skeleton` (root).

```html
<div data-slot="skeleton" id="avatar-placeholder"></div>
<div data-slot="skeleton" id="line-placeholder"></div>
```

## Full text

### Alert, Aspect Ratio, Badge, Card, Empty, Item, Separator, Skeleton

- `<div data-slot="aspect-ratio" data-ratio="16/9">` (any ratio, `"4/3"`, `"2.4"`): the kit sets `--ratio`, like shadcn. Children are not positioned; give an image `position: absolute; inset: 0; width: 100%; height: 100%` (the shadcn examples use `fill`).
- `skeleton`, sized by app CSS.
