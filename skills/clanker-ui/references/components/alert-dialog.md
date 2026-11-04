# Alert Dialog (`alert-dialog`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `alert-dialog-action` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `alert-dialog-cancel` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `alert-dialog-content` | `data-size` `default`, `sm` | `data-closed`, `data-open`, `data-state` |

Other parts: `alert-dialog` (root), `alert-dialog-description`, `alert-dialog-footer`, `alert-dialog-header`, `alert-dialog-media`, `alert-dialog-title`.

Part attributes: `data-alert-dialog-action` boolean; `data-alert-dialog-cancel` boolean; `data-alert-dialog-trigger` boolean.

Events: `alert-dialog:open` `{ trigger }`; `alert-dialog:close` `{ reason }` (cancelable).

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-overlays.min.js`):

- `dialogOpen(target, { trigger }?) → boolean`: Works for `dialog`, `alert-dialog`, `sheet`, and `drawer`.
- `dialogClose(target, reason = "api") → boolean`: `reason` goes to the `:close` event.

```html
<div data-slot="alert-dialog">
  <button type="button" data-slot="button" data-variant="outline" data-alert-dialog-trigger>Delete account</button>
  <dialog data-slot="alert-dialog-content" data-size="sm">
    <div data-slot="alert-dialog-header">
      <h2 data-slot="alert-dialog-title">Are you absolutely sure?</h2>
      <p data-slot="alert-dialog-description">This action cannot be undone.</p>
    </div>
    <div data-slot="alert-dialog-footer">
      <button type="button" data-slot="alert-dialog-cancel" data-variant="outline">Cancel</button>
      <button type="button" data-slot="alert-dialog-action" data-variant="destructive">Delete</button>
    </div>
  </dialog>
</div>
```

## Full text

### Dialog, Alert Dialog, Sheet, Drawer

- A dialog, alert dialog, or sheet is a native `<dialog>` opened with `showModal()`: focus trap, Escape, scroll lock, inert page, focus returns to the trigger. The first tabbable element gets the focus; a pointer open shows no focus ring on a button.
- A main-button click on `::backdrop` closes a dialog, sheet, or drawer, as Base UI (an alert dialog stays open): a held press closes after the release; a right or middle click, a press that starts or ends in the popup, and a touch drag do not close.
- Alert dialog: `data-size="sm"`, `alert-dialog-media`. The footer buttons are `<button data-slot="alert-dialog-cancel" data-variant="outline">` and `<button data-slot="alert-dialog-action">` (`data-variant="destructive"` for a red action), as in shadcn (`data-alert-dialog-cancel` and `data-alert-dialog-action` on a `button` part also work). Cancel closes it. The action is a plain button, as in shadcn: it does not close the dialog, so the app closes it with `dialogClose()` when its work is done, or the action gets `data-alert-dialog-close`. Like Base UI, the first tabbable element gets the initial focus (usually Cancel).
- A form in a dialog, alert dialog, sheet, or drawer: put `<form data-slot="form">` (or a plain `<form>`) as the direct child of the content around the header, the body, and the footer. It is `display: contents`, so the parts keep the content layout (gap, sticky footer).
