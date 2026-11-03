# Separator (`separator`)

Group `core`. Needs none. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `separator` (root) | `data-orientation` `horizontal`, `vertical` |  |

```html
<div>Blog</div>
<div data-slot="separator"></div>
<div data-slot="separator" data-orientation="vertical" role="separator"></div>
```

## Full text

### Alert, Aspect Ratio, Badge, Card, Empty, Item, Separator, Skeleton

- `<div data-slot="aspect-ratio" data-ratio="16/9">` (any ratio, `"4/3"`, `"2.4"`): the kit sets `--ratio`, like shadcn. Children are not positioned; give an image `position: absolute; inset: 0; width: 100%; height: 100%` (the shadcn examples use `fill`).
- `separator` (`data-orientation="vertical"`): decorative (`role="none"`) unless you add `role="separator"`.
