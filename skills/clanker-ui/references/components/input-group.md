# Input Group (`input-group`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `input-group-addon` | `data-align` `block-end`, `block-start`, `inline-end`, `inline-start` |  |
| `input-group-button` |  | `data-pressed` boolean |

Other parts: `input-group` (root), `input-group-control`, `input-group-text`.

Part attributes: `data-input-group-button` boolean.

Other options named in the docs: `data-size` `icon-sm`, `icon-xs`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary`.

## Full text

### Input Group

```html
<div data-slot="input-group" role="group">
  <input data-slot="input-group-control" placeholder="Search...">
  <div data-slot="input-group-addon" data-align="inline-start">
    <svg data-lucide="search"></svg>
    <span data-slot="input-group-text">USD</span>
    <button type="button" data-slot="button" data-input-group-button data-size="xs">Copy</button>
  </div>
</div>
```

The control can be a `textarea`. A click on an addon (not on a button) focuses the control. `input-group` and `input-group-addon` get `role="group"`; an addon without `data-align` gets `inline-start`. Buttons in an addon are `InputGroupButton`: add `data-input-group-button`; the kit sets `data-variant="ghost"` and `data-size="xs"` when they are missing. Button options: `data-variant="default|destructive|outline|secondary|ghost|link"` and `data-size="xs|sm|icon-xs|icon-sm"`. A button in an addon that opens a popover or menu has `data-pressed` while it is open. Not built: the `.border-b` and `.border-t` class variants of block addons (Tailwind classes, not attributes).
