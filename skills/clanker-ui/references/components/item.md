# Item (`item`)

Group `layout`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `item` (root) | `data-size` `default`, `sm`, `xs`; `data-variant` `default`, `muted`, `outline` |  |
| `item-media` | `data-variant` `default`, `icon`, `image` |  |
| `item-separator` | `data-orientation` `horizontal`, `vertical` |  |

Other parts: `item-actions`, `item-content`, `item-description`, `item-footer`, `item-group`, `item-header`, `item-title`.

```html
<div data-slot="item-group" role="list">
  <div data-slot="item" data-variant="outline" role="listitem">
    <div data-slot="item-media" data-variant="icon"><svg data-lucide="badge-check"></svg></div>
    <div data-slot="item-content">
      <div data-slot="item-title">Basic Item</div>
      <p data-slot="item-description">A simple item with title and description.</p>
    </div>
    <div data-slot="item-actions"><button type="button" data-slot="button" data-variant="outline" data-size="sm">Action</button></div>
  </div>
  <div data-slot="item-separator"></div>
  <a data-slot="item" data-size="sm" href="/profile" role="listitem">
    <div data-slot="item-content"><div data-slot="item-title">Your profile has been verified.</div></div>
  </a>
</div>
```

## Full text

### Alert, Aspect Ratio, Badge, Card, Empty, Item, Separator, Skeleton

- `<div data-slot="aspect-ratio" data-ratio="16/9">` (any ratio, `"4/3"`, `"2.4"`): the kit sets `--ratio`, like shadcn. Children are not positioned; give an image `position: absolute; inset: 0; width: 100%; height: 100%` (the shadcn examples use `fill`).
- `item` (`data-variant="outline|muted"`, `data-size="sm|xs"`, or `<a data-slot="item">`) with `item-media` (`data-variant="icon|image"`), `item-content` (`item-title`, `item-description`), `item-actions`, `item-header`, `item-footer`; `item-group` (`role="list"`) and `item-separator`. As in shadcn, `item-title` is one line and `item-description` at most two lines (`line-clamp`): give a cut text a `title`, or for long text (a timeline update) use a `p` in `item-content`, not `item-description`. A `cover` in `item-media` is 40 px wide (32 px in a `sm` item, 24 px in `xs`) with its ratio and without its text; in `data-variant="image"` it fills the square. `item-group` has a 16 px gap and `item-separator` adds 8 px above and below: in a list with separators set the group gap to 0 in app CSS (`.list { gap: 0 }`), so the rows are as close as without them.
