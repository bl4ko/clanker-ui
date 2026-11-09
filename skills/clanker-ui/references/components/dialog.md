# Dialog (`dialog`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `dialog-content` |  | `data-closed`, `data-open`, `data-state` |
| `dialog-footer` | `data-show-close-button` boolean |  |

Other parts: `dialog` (root), `dialog-body`, `dialog-close`, `dialog-description`, `dialog-header`, `dialog-title`.

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
- Long dialog content: put the middle of the dialog in a `dialog-body` (kit part, like the shadcn `-mx-4 max-h-[50vh] overflow-y-auto px-4` wrapper of the Scrollable Content and Sticky Footer examples). The `dialog-content` is then a column of at most the window height less 2rem: the body takes the free space and scrolls, and the header and the footer stay in view. The body reaches the dialog edges with the scrollbar and has 4 px of padding at the top and the bottom for focus rings. A dialog without a body that is taller than the window scrolls as a whole (the kit gives `dialog-content` `max-height: calc(100dvh - 2rem)` and `overflow-y: auto`; in shadcn the top and the end of such a dialog are out of reach).
- A form in a dialog, alert dialog, sheet, or drawer: put `<form data-slot="form">` (or a plain `<form>`) as the direct child of the content around the header, the body, and the footer. It is `display: contents`, so the parts keep the content layout (gap, sticky footer).
