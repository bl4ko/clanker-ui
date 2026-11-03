# Alert (`alert`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `alert` (root) | `data-variant` `default`, `destructive`, `info`, `success`, `warning` |  |

Other parts: `alert-action`, `alert-description`, `alert-title`.

```html
<div data-slot="alert" data-variant="destructive" role="alert">
  <svg data-lucide="circle-alert"></svg>
  <div data-slot="alert-title">Payment failed</div>
  <div data-slot="alert-description">Check your payment method and try again.</div>
  <div data-slot="alert-action"><button type="button" data-slot="button" data-variant="outline" data-size="sm">Retry</button></div>
</div>
```

## Full text

### Alert, Aspect Ratio, Badge, Card, Empty, Item, Separator, Skeleton

- `alert` (`role="alert"`, `data-variant="destructive"`) with an optional leading `<svg>`, `alert-title`, `alert-description`, `alert-action`.
- Kit extension to shadcn: `data-variant="success|warning|info"` on `alert` and `badge`. CSS only. Border, background, and text use the status tokens (see [CSS rules for components](https://github.com/bl4ko/clanker-ui#css-rules-for-components)); the alert description uses `--foreground`. A status `<a data-slot="badge">` shows an underline on hover.
- `<div data-slot="aspect-ratio" data-ratio="16/9">` (any ratio, `"4/3"`, `"2.4"`): the kit sets `--ratio`, like shadcn. Children are not positioned; give an image `position: absolute; inset: 0; width: 100%; height: 100%` (the shadcn examples use `fill`).
