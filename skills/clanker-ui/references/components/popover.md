# Popover (`popover`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `popover-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `popover-trigger` | `data-popover-trigger` any |  |

Other parts: `popover` (root), `popover-description`, `popover-header`, `popover-title`.

Part attributes: `data-popover-trigger` boolean.

Events: `popover:open` `{ trigger }`; `popover:close` `{ reason }`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-overlays.min.js`):

- `popoverOpen(target, { trigger, anchor }?) → boolean`
- `popoverClose(target, reason = "api") → boolean`

```html
<div data-slot="popover">
  <button type="button" data-slot="button" data-variant="outline" data-popover-trigger>Open Popover</button>
  <div data-slot="popover-content" data-align="start">
    <div data-slot="popover-header">
      <div data-slot="popover-title">Dimensions</div>
      <p data-slot="popover-description">Set the dimensions for the layer.</p>
    </div>
  </div>
</div>
```

## Full text

### Popover

`popover` > `popover-trigger` (or `data-popover-trigger`), optional `popover-anchor`, `popover-content` with `popover-header`, `popover-title`, `popover-description`. Non-modal: focus moves into the content; Escape, outside click, and focus leaving close it. As in Base UI, a mouse press outside closes it on the click (a held press, a right or middle click, or a press that ends in the popup keep it open); a touch outside closes it at the end of the tap. `data-modal` on the root traps focus and locks scroll. Default placement: bottom, center, 4 px; the trigger has `data-pressed` while it is open.
