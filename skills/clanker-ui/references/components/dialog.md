# Dialog (`dialog`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `dialog-content` |  | `data-closed`, `data-open`, `data-state` |
| `dialog-footer` | `data-show-close-button` boolean |  |

Other parts: `dialog` (root), `dialog-close`, `dialog-description`, `dialog-header`, `dialog-title`.

Part attributes: `data-dialog-close` boolean; `data-dialog-trigger` id.

Events: `dialog:open` `{ trigger }`; `dialog:close` `{ reason }` (cancelable).

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-overlays.min.js`):

- `dialogOpen(target, { trigger }?) → boolean`: Works for `dialog`, `alert-dialog`, `sheet`, and `drawer`.
- `dialogClose(target, reason = "api") → boolean`: `reason` goes to the `:close` event.

## Full text

### Dialog, Alert Dialog, Sheet, Drawer

```html
<div data-slot="dialog">
  <button type="button" data-slot="button" data-variant="outline" data-dialog-trigger>Open</button>
  <dialog data-slot="dialog-content">
    <div data-slot="dialog-header">
      <h2 data-slot="dialog-title">Edit profile</h2>
      <p data-slot="dialog-description">Make changes here.</p>
    </div>
    <div data-slot="dialog-footer">
      <button type="button" data-slot="button" data-variant="outline" data-dialog-close>Cancel</button>
    </div>
  </dialog>
</div>
```

- A dialog, alert dialog, or sheet is a native `<dialog>` opened with `showModal()`: focus trap, Escape, scroll lock, inert page, focus returns to the trigger. The first tabbable element gets the focus; a pointer open shows no focus ring on a button.
- A main-button click on `::backdrop` closes a dialog, sheet, or drawer, as Base UI (an alert dialog stays open): a held press closes after the release; a right or middle click, a press that starts or ends in the popup, and a touch drag do not close.
- Dialog and sheet add a close button unless `data-show-close-button="false"`. `<div data-slot="dialog-footer" data-show-close-button>` adds an outline Close button. A `<form method="dialog">` inside closes with an exit animation.
