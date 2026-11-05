# Tabs (`tabs`)

Group `layout`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `tabs` (root) | `data-default-value` string; `data-orientation` `horizontal`, `vertical`; `data-value` string |  |
| `tabs-content` | `data-value` string |  |
| `tabs-list` | `data-variant` `default`, `line` |  |
| `tabs-trigger` | `data-value` string | `data-active`, `data-state` |

Other options named in the docs: `data-activation` string.

Events: `tabs:change` `{ value }`.

## Full text

### Tabs

```html
<div data-slot="tabs" data-default-value="account" data-orientation="horizontal|vertical">
  <div data-slot="tabs-list" data-variant="line">
    <button data-slot="tabs-trigger" data-value="account">Account</button>
  </div>
  <div data-slot="tabs-content" data-value="account">...</div>
</div>
```

```html
<div data-slot="tabs" data-value="password">...</div>
```

Set the tab from code with `data-value` on the root (`tabs.dataset.value = "password"`): the kit selects that tab without a `tabs:change` event, as for a select. A root with `data-value` keeps it in sync when the user picks a tab, and `data-value` in the markup wins over `data-default-value`. A value that no trigger has changes nothing.

Keep a tab bar short enough for 390 px: when it scrolls, the cut last label has no other sign. With more tabs, put a `select` with the same choices next to the list, as shadcn `dashboard-01` does: `data-hide-from="sm"` on the select and `data-show-from="sm"` on the `tabs-list`; or use fewer and shorter labels. A `tabs-content` without `data-value` is a shared panel: it shows for every tab and is labelled by the selected tab. Use it for a tab bar that filters one list or table: render the rows on `tabs:change`. A filter with no panel at all is a toggle group (`data-type="single" data-required`), not tabs.

Manual activation as in Base UI: the arrow keys move focus, Enter, Space, or a click selects (`data-activation="automatic"` selects on focus), roving tabindex, arrows (RTL aware), Home, End; disabled tabs are skipped. Tab panels are focusable (`tabindex="0"`) and show the standard focus ring.

A horizontal `tabs-list` is never wider than the root: when the triggers do not fit, the list scrolls horizontally without a scrollbar, and the triggers keep their width. The selected trigger scrolls fully into view at load, when the list becomes visible, and when the list changes size. A trigger that gets keyboard focus (arrow keys, Home, End, Tab) or a click also scrolls fully into view. Only the list scrolls, also in a scaled container. The kit hides the old panel before `tabs:change`. In the handler, render only the new panel, not the whole tabs root: a new root makes the page jump. The kit measures the list before it changes the tab and reads no layout after `tabs:change`, so an app can fill the new panel in the same task (for example in a microtask) and the page does not jump. A fill in a later task (fetch, timer) can still change the page height. App CSS that makes the selected trigger wider than the others can leave part of it hidden, because the kit measures before the change. The kit sets `tabindex="-1"` on a horizontal list that has no `tabindex`, so the list is not a Tab stop (Firefox stops on a scroll container). The horizontal root has `min-width: 0`, so a long list does not widen a grid or flex parent. Vertical tabs do not scroll.
