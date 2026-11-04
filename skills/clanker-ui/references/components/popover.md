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

Custom floating content, for example one readout for many small hover targets (a bar per day in an uptime row, where one tooltip per bar is too heavy): use the core `position()` with your own `popover="manual"` element. It places the element next to an anchor element or a virtual anchor (`{ getBoundingClientRect() }`), flips at the viewport edge, follows scroll and resize, and returns `stop()`. It sets `data-side`, `data-align`, and the `--anchor-*`, `--available-*`, and `--transform-origin` variables, as for kit popups ([Popups](https://github.com/bl4ko/clanker-ui#popups)). Dismissal and focus stay app code; for an interactive popup use `popover`.

```js
import { position } from "/vendor/clanker-ui/clanker-ui.min.js"

const tip = document.getElementById("day-tip")
let stop = null
grid.addEventListener("pointerover", event => {
  const bar = event.target.closest("[data-day]")
  if (!bar) return
  tip.textContent = bar.dataset.label
  if (!tip.matches(":popover-open")) tip.showPopover()
  stop?.()
  stop = position(tip, bar, { side: "top", sideOffset: 6 })
})
grid.addEventListener("pointerleave", () => {
  stop?.()
  stop = null
  tip.hidePopover()
})
```
