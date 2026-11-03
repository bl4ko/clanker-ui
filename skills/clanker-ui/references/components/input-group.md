# Input Group (`input-group`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `input-group-addon` | `data-align` `block-end`, `block-start`, `inline-end`, `inline-start` |  |
| `input-group-button` |  | `data-pressed` |

Other parts: `input-group` (root), `input-group-control`, `input-group-text`.

Part attributes: `data-input-group-button` boolean.

## Full text

### Input Group

```html
<div data-slot="input-group" role="group">
  <input data-slot="input-group-control" placeholder="Search...">
  <div data-slot="input-group-addon" data-align="inline-start|inline-end|block-start|block-end">
    <svg data-lucide="search"></svg>
    <span data-slot="input-group-text">USD</span>
    <button type="button" data-slot="button" data-input-group-button data-size="xs|sm|icon-xs|icon-sm">Copy</button>
  </div>
</div>
```

The control can be a `textarea`. A click on an addon (not on a button) focuses the control. `input-group` and `input-group-addon` get `role="group"`; an addon without `data-align` gets `inline-start`. Buttons in an addon are `InputGroupButton`: add `data-input-group-button`; the kit sets `data-variant="ghost"` and `data-size="xs"` when they are missing. Sizes: `xs`, `sm`, `icon-xs`, `icon-sm`. Not built: the `.border-b` and `.border-t` class variants of block addons (Tailwind classes, not attributes).
