# Sonner (`sonner`)

Group `overlays`. Needs `core`. CSS and JS.

Same component as `toast`: use its markup, events, and API.

Other parts: `sonner` (root).

Other options named in the docs: `data-limit` any; `data-timeout` any.

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
