# Badge (`badge`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `badge` (root) | `data-variant` `default`, `destructive`, `ghost`, `info`, `link`, `outline`, `secondary`, `success`, `warning` |  |

```html
<span data-slot="badge">Badge</span>
<span data-slot="badge" data-variant="secondary">Secondary</span>
<a data-slot="badge" data-variant="success" href="#status"><svg data-lucide="circle-check"></svg>Passing</a>
```

## Full text

### Alert, Aspect Ratio, Badge, Card, Empty, Item, Separator, Skeleton

- Kit extension to shadcn: `data-variant="success|warning|info"` on `alert` and `badge`. CSS only. Border, background, and text use the status tokens (see [CSS rules for components](https://github.com/bl4ko/clanker-ui#css-rules-for-components)); the alert description uses `--foreground`. A status `<a data-slot="badge">` shows an underline on hover.
- `<div data-slot="aspect-ratio" data-ratio="16/9">` (any ratio, `"4/3"`, `"2.4"`): the kit sets `--ratio`, like shadcn. Children are not positioned; give an image `position: absolute; inset: 0; width: 100%; height: 100%` (the shadcn examples use `fill`).
- `badge` (`data-variant="secondary|destructive|outline|ghost|link"`, or `<a data-slot="badge">`). Icons and spinners inside are 12 px.
