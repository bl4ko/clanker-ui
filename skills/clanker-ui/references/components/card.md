# Card (`card`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `card` (root) | `data-size` `sm` |  |

Other parts: `card-action`, `card-content`, `card-description`, `card-footer`, `card-header`, `card-title`.

```html
<div data-slot="card" data-size="sm">
  <div data-slot="card-header">
    <div data-slot="card-title">Team members</div>
    <div data-slot="card-description">Invite your team members to collaborate.</div>
    <div data-slot="card-action"><button type="button" data-slot="button" data-variant="link">Invite</button></div>
  </div>
  <div data-slot="card-content">Content</div>
  <div data-slot="card-footer"><button type="button" data-slot="button" data-variant="outline">Manage access</button></div>
</div>
```

## Full text

### Alert, Aspect Ratio, Badge, Card, Empty, Item, Separator, Skeleton

- `<div data-slot="aspect-ratio" data-ratio="16/9">` (any ratio, `"4/3"`, `"2.4"`): the kit sets `--ratio`, like shadcn. Children are not positioned; give an image `position: absolute; inset: 0; width: 100%; height: 100%` (the shadcn examples use `fill`).
- `card` with `card-header` (`card-title`, `card-description`, `card-action`), `card-content`, `card-footer`. `data-size="sm"`; override `--card-spacing`. A first-child `<img>` sits flush with the top.
