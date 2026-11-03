# Hover Card (`hover-card`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `hover-card-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |

Other parts: `hover-card` (root).

Part attributes: `data-hover-card-trigger` boolean.

Other options named in the docs: `data-close-delay` any; `data-delay` any; `data-open-delay` any.

Events: `hover-card:open`; `hover-card:close`.

```html
<div data-slot="hover-card">
  <a data-slot="button" data-variant="link" href="/nextjs" data-hover-card-trigger data-delay="10" data-close-delay="100">@nextjs</a>
  <div data-slot="hover-card-content" data-side="bottom">The React Framework, created and maintained by @vercel.</div>
</div>
```

## Full text

### Tooltip and Hover Card

`hover-card` > trigger + `hover-card-content`. `data-delay` (600) and `data-close-delay` (300) on the trigger or the root (`data-open-delay` also works), the Base UI defaults; shadcn examples set `data-delay="10" data-close-delay="100"`. Placement: bottom, center, 4 px, `alignOffset` 4. Opens on hover and keyboard focus, never on touch. It closes at once when focus leaves the trigger and the card (Base UI); the close delay is for the pointer. A card that focus opened stays open when the pointer leaves the card or a press in it moves focus away, as in Base UI; it closes when the pointer leaves the trigger.
