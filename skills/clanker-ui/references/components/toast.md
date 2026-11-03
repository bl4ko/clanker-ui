# Toast (`toast`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `toast` (root) (kit adds) |  | `data-ending-style`, `data-expanded`, `data-limited`, `data-starting-style`, `data-swipe-direction` |
| `toast-content` (kit adds) |  | `data-behind`, `data-expanded` |
| `toast-portal` | `data-limit` number; `data-timeout` number |  |

Kit adds: `toast-action`, `toast-close`, `toast-description`, `toast-icon`, `toast-title`, `toast-viewport`.

Events: `toast:open` `{ id }`; `toast:close` `{ id, reason }`; `toast:action` `{ id }`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-overlays.min.js`):

- `toast(message, options?) → id`: Sonner-style calls and the Base UI manager (`toast.add`, `toast.update`, `toast.close`), see [Toast and Sonner](https://github.com/bl4ko/clanker-ui#toast-and-sonner).

```html
<div data-slot="toast-portal" data-limit="3" data-timeout="5000"></div>
<button type="button" data-slot="button" data-variant="outline" id="show-toast">Show Toast</button>
```

## Full text

### Toast and Sonner

```js
toast.add({ title: "Event created", description: "Sunday at 9:00", type: "success", timeout: 5000, priority: "low", actionProps: { children: "Undo", onClick() {} } })
toast.update(id, { description: "Saved" }); toast.update(id, prev => ({ title: `${prev.title}!` })); toast.close(id); toast.close()
toast("Event created", { description: "Sunday at 9:00", action: { label: "Undo", onClick() {} } })
toast.success(title, opts); toast.info(); toast.warning(); toast.error(); toast.loading(); toast.message()
toast.promise(promiseOrFn, { loading: "Creating event…", success: data => `${data.name} created.`, error: "Could not create event.", finally })
toast.dismiss(id); toast.dismiss(); toast.getToasts()
```

- The Base UI toast DOM (shadcn base `sonner` redirects to `toast`): `<div data-slot="toast-portal">` (created on load if missing) > `toast-viewport` (`role="region"`, `aria-live="polite"`, a manual popover in the top layer, open only while a toast shows, so a new toast shows above popups that opened before it) > `toast` (`role="dialog"`, `alertdialog` for `priority: "high"`) > `toast-content` > `toast-icon`, a `div` with `h2` `toast-title` and `p` `toast-description`, `toast-action`, `toast-close`. Every toast has the close button, like shadcn.
- `toast.add`, `toast.update`, `toast.close`, and `toast.promise` follow the Base UI manager. A string in `toast.promise` is the description; an object is the full options. `toast.add` with an existing `id` updates that toast and restarts its timer. `actionProps` (`children`, `onClick`) do not close the toast; call `toast.close(id)`.
- Kit calls: `toast(message, options)` and the typed variants put `message` in the title. Options: `id`, `title`, `description`, `type` (`success|info|warning|error|loading` show an icon), `timeout` (ms, `0` keeps it) or `duration` (`Infinity` keeps it), `priority` (`high` announces the toast at once in a hidden `role="alert"` region), `action` (`{ label, onClick }`, closes the toast unless `onClick` calls `event.preventDefault()`), `actionProps`, `icon` (Lucide name, node, or `null`), `className`, `onClose`, `onRemove`, `onDismiss`, `onAutoClose`. An unknown `icon` name throws before any state changes. `toast.promise` returns the id.
- `<div data-slot="toast-portal" data-limit="3" data-timeout="5000">` sets the limit and the default timeout. Toasts over the limit stay mounted with `data-limited` and `inert` (hidden) until a slot is free.
- State attributes as Base UI: `data-type`, `data-expanded` (viewport, toast, content), `data-behind` (content of toasts behind the front one), `data-limited`, `data-swiping`, `data-swipe-direction`, `data-starting-style`, `data-ending-style`; variables `--toast-index`, `--toast-offset-y`, `--toast-height`, `--toast-swipe-movement-x`, `--toast-swipe-movement-y`, and `--toast-frontmost-height` on the viewport.
- The stack expands while the pointer is over it or a toast has keyboard focus. Timers pause on hover, on keyboard focus, during a touch press, and while the window has no focus; a hidden page does not pause them (Base UI 1.6.0 has no `visibilitychange` handler). As in Base UI 1.6.0, the version shadcn uses, a pause sets the time left to the full timeout less the time since the last start or resume, so a toast that is hovered again runs longer. Later Base UI versions count the time left again; change this when the pinned version moves. A hover that ends during an exit animation applies after it. Swipe down or right more than 40 px to dismiss; other directions are damped and spring back. F6 moves focus to the viewport; Tab and Shift+Tab past the toasts return focus to where it was. Escape closes the focused toast (not an open dialog), and focus moves to the next toast.
