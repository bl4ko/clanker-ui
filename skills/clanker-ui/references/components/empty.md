# Empty (`empty`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `empty` (root) | `data-variant` `outline` |  |
| `empty-header` | `data-variant` `icon` |  |
| `empty-icon` | `data-variant` `default`, `icon` |  |

Other parts: `empty-content`, `empty-description`, `empty-title`.

```html
<div data-slot="empty" data-variant="outline">
  <div data-slot="empty-header">
    <div data-slot="empty-icon" data-variant="icon"><svg data-lucide="folder"></svg></div>
    <div data-slot="empty-title">No Projects Yet</div>
    <div data-slot="empty-description">Get started by creating your first project.</div>
  </div>
  <div data-slot="empty-content"><button type="button" data-slot="button">Create Project</button></div>
</div>
```

## Full text

### Alert, Aspect Ratio, Badge, Card, Empty, Item, Separator, Skeleton

- `<div data-slot="aspect-ratio" data-ratio="16/9">` (any ratio, `"4/3"`, `"2.4"`): the kit sets `--ratio`, like shadcn. Children are not positioned; give an image `position: absolute; inset: 0; width: 100%; height: 100%` (the shadcn examples use `fill`).
- `empty` with `empty-header` (`empty-icon` with `data-variant="icon"`, `empty-title`, `empty-description`) and `empty-content`. Kit extension: `data-variant="outline"` adds the 1 px dashed border.
