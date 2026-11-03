# Sheet (`sheet`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `sheet-content` | `data-side` `bottom`, `left`, `right`, `top` | `data-ending-style`, `data-starting-style` |

Other parts: `sheet` (root), `sheet-close`, `sheet-description`, `sheet-footer`, `sheet-header`, `sheet-title`.

Kit adds: `sheet-overlay`.

Part attributes: `data-sheet-close` boolean; `data-sheet-trigger` boolean.

Other options named in the docs: `data-show-close-button` `false`, `true`.

Events: `sheet:open` `{ trigger }`; `sheet:close` `{ reason }` (cancelable).

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-overlays.min.js`):

- `dialogOpen(target, { trigger }?) → boolean`: Works for `dialog`, `alert-dialog`, `sheet`, and `drawer`.
- `dialogClose(target, reason = "api") → boolean`: `reason` goes to the `:close` event.

```html
<div data-slot="sheet">
  <button type="button" data-slot="button" data-variant="outline" data-sheet-trigger>Open</button>
  <dialog data-slot="sheet-content" data-side="right">
    <div data-slot="sheet-header">
      <h2 data-slot="sheet-title">Edit profile</h2>
      <p data-slot="sheet-description">Make changes to your profile here.</p>
    </div>
    <div data-slot="sheet-footer">
      <button type="button" data-slot="button" data-sheet-close>Save changes</button>
    </div>
  </dialog>
</div>
```

## Full text

### Dialog, Alert Dialog, Sheet, Drawer

- A dialog, alert dialog, or sheet is a native `<dialog>` opened with `showModal()`: focus trap, Escape, scroll lock, inert page, focus returns to the trigger. The first tabbable element gets the focus; a pointer open shows no focus ring on a button.
- A main-button click on `::backdrop` closes a dialog, sheet, or drawer, as Base UI (an alert dialog stays open): a held press closes after the release; a right or middle click, a press that starts or ends in the popup, and a touch drag do not close.
- Dialog and sheet add a close button unless `data-show-close-button="false"`. `<div data-slot="dialog-footer" data-show-close-button>` adds an outline Close button. A `<form method="dialog">` inside closes with an exit animation.
- Sheet: `data-side="top|right|bottom|left"` (default `right`). It opens with `data-starting-style` (set before `showModal()`, removed after one frame) and closes with `data-ending-style` until its transition ends, as Base UI; the backdrop follows the same attributes.
- Long sheet and drawer content does not scroll by itself, as in shadcn: put it in a flex item with `overflow-y: auto` (the shadcn examples use `flex-1 overflow-y-auto`).
