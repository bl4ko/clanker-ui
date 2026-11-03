# Resizable (`resizable`)

Group `layout`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `resizable-handle` | `data-with-handle` boolean |  |
| `resizable-panel` | `data-default-size` number; `data-max-size` number; `data-min-size` number |  |
| `resizable-panel-group` | `data-orientation` `horizontal`, `vertical` |  |

Other options named in the docs: `data-keyboard-step` any.

Events: `resizable:change` `{ value }`.

## Full text

### Resizable

```html
<div data-slot="resizable-panel-group" data-orientation="horizontal|vertical">
  <div data-slot="resizable-panel" data-default-size="25" data-min-size="15" data-max-size="60">...</div>
  <div data-slot="resizable-handle" data-with-handle></div>
  <div data-slot="resizable-panel">...</div>
</div>
```

Sizes are percentages. The handle is a WAI-ARIA window splitter: drag it or use the arrow keys (`data-keyboard-step`, default 5), Home, and End. `data-orientation="vertical"` stacks the panels; `data-with-handle` adds the shadcn grip (an empty `div`, a 4 × 24 px pill). Not built: collapsible panels and saved layouts.
