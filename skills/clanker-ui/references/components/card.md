# Card (`card`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `card` (root) | `data-orientation` `horizontal`; `data-size` `sm` |  |
| `card-action` |  | `data-wrap` |

Other parts: `card-content`, `card-description`, `card-footer`, `card-header`, `card-title`.

Other options named in the docs: `data-wrap` any.

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
- `card` with `card-header` (`card-title`, `card-description`, `card-action`), `card-content`, `card-footer`. `data-size="sm"`; override `--card-spacing`. A first-child `<img>` sits flush with the top. Kit extension: `data-orientation="horizontal"` puts a first-child `cover` (6rem, 8rem from 48rem) at the start and the other parts in a `div` column next to it, with a wrapping `card-footer` (a hero or feature card: art left, text and actions right). A `card-action` with two or more children (a badge and a button) is a row with an 8 px gap, aligned to the end, that wraps. In a `card-header` with a `card-action` and no `card-description`, the title and the action are centered on one line (shadcn aligns them at the top, so a one-line title sits above the center of a 36 px button). Kit extension: `data-wrap` on `card-action` moves it to its own row under the title and the description, at the start, when the `card-header` is narrower than 24rem (for a text button or a select that would leave the title too narrow on a phone).
