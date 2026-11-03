# Trace (`trace`)

Group `chat`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `trace-collapsible` | `data-default-open` boolean |  |
| `trace-collapsible-content` |  | `data-ending-style`, `data-starting-style` |
| `trace-line` | `data-status` `error`, `pending`, `running` |  |

Other parts: `trace` (root), `trace-collapsible-trigger`, `trace-description`, `trace-icon`, `trace-title`.

Kit adds: `trace-collapsible-content-inner`.

Events: `trace:open`; `trace:close`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-chat.min.js`):

- `traceOpen(target, { animate = true }?) → boolean`: `target` is a `trace-collapsible` or an element in it.
- `traceClose(target, { animate = true }?) → boolean`

## Full text

### Trace

```html
<div data-slot="trace">
  <span data-slot="trace-line" data-status="running|error|pending">
    <span data-slot="trace-icon"><svg data-lucide="terminal"></svg></span>
    <span data-slot="trace-title">Running pnpm build</span>
    <span data-slot="trace-description">14s</span>
  </span>
  <div data-slot="trace-collapsible" data-default-open>
    <button data-slot="trace-collapsible-trigger"><span data-slot="trace-line">…</span></button>
    <div data-slot="trace-collapsible-content">Detail</div>
  </div>
</div>
```

The kit adds the chevron and keeps `aria-expanded` and `data-state` current. It sets the Base UI collapsible states: `data-open` or `data-closed` on the collapsible and the content, `data-panel-open` on the trigger, and `data-starting-style` (one frame on open) or `data-ending-style` (while it closes) on all three. The content height is a CSS transition on `--collapsible-panel-height`: the pixel height while it moves, `auto` when open.
