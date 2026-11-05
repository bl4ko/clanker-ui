# Drawer (`drawer`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `drawer` (root) | `data-show-swipe-handle` boolean; `data-swipe-direction` string |  |
| `drawer-content` | `data-drawer-content` any |  |
| `drawer-popup` |  | `data-ending-style`, `data-nested-drawer-open`, `data-nested-drawer-swiping`, `data-snap-points`, `data-starting-style`, `data-swipe-axis`, `data-swipe-direction`, `data-swiping` |
| `drawer-swipe-handle` (kit adds) |  | `data-show-swipe-handle` |
| `drawer-viewport` |  | `data-ending-style`, `data-modal`, `data-snap-points`, `data-starting-style`, `data-swiping` |

Other parts: `drawer-body`, `drawer-description`, `drawer-footer`, `drawer-header`, `drawer-title`.

Part attributes: `data-drawer-close` boolean; `data-drawer-trigger` boolean.

Other options named in the docs: `data-base-ui-swipe-ignore` any; `data-disable-pointer-dismissal` any; `data-modal` `false`, `true`; `data-snap-point` any; `data-snap-points` string; `data-snap-to-sequential-points` any; `data-swipe-axis` `x`, `y`.

Events: `drawer:open` `{ trigger }`; `drawer:close` `{ reason }` (cancelable); `drawer:release` `{ delta }`; `drawer:snap-point-change` `{ snapPoint }`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-overlays.min.js`):

- `dialogOpen(target, { trigger }?) → boolean`: Works for `dialog`, `alert-dialog`, `sheet`, and `drawer`.
- `dialogClose(target, reason = "api") → boolean`: `reason` goes to the `:close` event.

## Full text

### Dialog, Alert Dialog, Sheet, Drawer

- A main-button click on `::backdrop` closes a dialog, sheet, or drawer, as Base UI (an alert dialog stays open): a held press closes after the release; a right or middle click, a press that starts or ends in the popup, and a touch drag do not close.
- Long sheet and drawer content does not scroll by itself, as in shadcn: put it in a `sheet-body` or `drawer-body` (kit parts, like the shadcn `flex-1 overflow-y-auto px-4` wrapper): it fills the space between the header and the footer, scrolls, and holds its children in a column with a 1.5rem gap.
- A form in a dialog, alert dialog, sheet, or drawer: put `<form data-slot="form">` (or a plain `<form>`) as the direct child of the content around the header, the body, and the footer. It is `display: contents`, so the parts keep the content layout (gap, sticky footer).

### Drawer

```html
<div data-slot="drawer" data-swipe-direction="down" data-show-swipe-handle>
  <button type="button" data-slot="button" data-variant="outline" data-drawer-trigger>Open</button>
  <dialog data-slot="drawer-viewport">
    <div data-slot="drawer-popup">
      <div data-slot="drawer-content">
        <div data-slot="drawer-header">
          <h2 data-slot="drawer-title">Move Goal</h2>
          <p data-slot="drawer-description">Set your daily activity goal.</p>
        </div>
        <div data-slot="drawer-footer">
          <button type="button" data-slot="button" data-drawer-close>Submit</button>
        </div>
      </div>
    </div>
  </dialog>
</div>
```

- The Base UI drawer DOM: the viewport is the `<dialog>` and its `::backdrop` is the overlay; `drawer-popup` holds the optional `drawer-swipe-handle` (the kit adds it for `data-show-swipe-handle`) and `drawer-content` (`data-drawer-content`). A short form `<dialog data-slot="drawer-content">` with the parts inside is upgraded to this DOM on load.
- Root options as shadcn props: `data-swipe-direction="down|up|left|right"` (default `down`; the old `data-direction="bottom|top|left|right"` still works), `data-show-swipe-handle`, `data-modal="false"` (page stays usable, no backdrop) or `"trap-focus"` (focus trap only), `data-disable-pointer-dismissal` (an outside press, and for a non-modal drawer also focus leaving, does not close it). A non-modal drawer closes on a mouse click outside and at the end of a touch tap outside (or a touch drag outside of more than 10 px), as Base UI without a backdrop (the shadcn "Non Modal" example sets `disablePointerDismissal`).
- State as Base UI: `data-swipe-direction`, `data-swipe-axis="x|y"`, `data-swiping`, `data-swipe-dismiss`, `data-starting-style`, `data-ending-style`, and the variables `--drawer-swipe-movement-x`, `--drawer-swipe-movement-y`, `--drawer-swipe-progress`, `--drawer-swipe-strength`, `--nested-drawers` on the popup; `data-modal`, `data-nested`, `data-swiping`, `data-swipe-dismiss`, `--drawer-swipe-progress` on the viewport (for the backdrop). Opening focuses the popup.
- Swipe toward the edge to dismiss: on touch anywhere on the drawer, with a mouse or pen only outside `drawer-content` (the swipe handle), so text in the content stays selectable. It closes when it moved more than half its size or faster than 0.5 px/ms; the exit moves in `--drawer-swipe-strength` × 400 ms (0.1 to 1 from the release speed of the last move, with a 16 ms minimum sample time), while the hidden opacity transition keeps 400 ms, so the drawer closes and returns focus after 400 ms (Base UI 1.6.0 sets `data-ending-style` before the strength). Other directions are damped and spring back. A press or touch on the backdrop of a modal drawer starts the swipe when the pointer reaches the popup, and a main-button click on the backdrop (press and release there) closes the drawer, as Base UI. Buttons, links, and fields do not start a mouse swipe; `data-base-ui-swipe-ignore` (old `data-drawer-no-drag`) stops any swipe; a touch inside a scroller swipes only from its start edge.
- Snap points (vertical drawers): `data-snap-points="31rem 1"` on the root (space or comma list: a number up to 1 is a share of the window height, a larger number or `px` is pixels, `rem` is root ems), `data-snap-point` (the Base UI `defaultSnapPoint`: read at each open, first one when missing; a change while open does nothing), `data-snap-to-sequential-points`. The popup gets `data-snap-points`, `--drawer-snap-point-offset`, and `data-expanded` at the snap point `1`; the viewport gets `data-snap-points` (backdrop minimum 0.5). A swipe up or down settles on the nearest snap point after the release speed (above 0.5 px/ms it pushes 300 px per px/ms) or closes past the last one; `drawer:snap-point-change` `{ snapPoint }` fires on the root. Each open starts at the default snap point. A `ResizeObserver` keeps the snap offsets right after a resize or a rotation (a parent keeps its height while a nested drawer is open).
- Nested drawers: a drawer whose root is inside an open drawer opens on top of it, as Base UI. Its viewport moves out of the parent popup while it is open (into the parent viewport) and moves back when it closes, because the shadcn `group-data-*/drawer-popup` rules match every popup above it. While it is open: find the viewport with the trigger `aria-controls`; DOM events from inside it (`click`, `input`, `submit`, kit events) do not reach its own root or the elements between the root and the parent popup; CSS selectors through the root do not match; a `<form>` around the root does not contain its fields. `dialogOpen` and `dialogClose` still accept the root, the trigger, or an id. Closing a parent sends its `drawer:close` first; if no listener cancels it, the open nested drawers close, the deepest first (their `drawer:close` cannot be cancelled), then the parent. Parents get `data-nested-drawer-open`, `--nested-drawers` (open drawers above), `--drawer-height` (their own height), and `--drawer-frontmost-height`; during a swipe of the front drawer they get `data-nested-drawer-swiping` and its `--drawer-swipe-progress`. The nested drawer has `data-nested` and no visible backdrop, and a parent with an open nested drawer does not swipe.
- While a modal dialog is open, the `toast-portal` element moves into the topmost open modal dialog (a modal makes everything else inert) and moves back when it closes, so toasts stay usable and Tab reaches them.
