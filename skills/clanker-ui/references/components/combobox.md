# Combobox (`combobox`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `combobox` (root) | `data-auto-highlight` boolean; `data-name` string; `data-value` string |  |
| `combobox-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-chips`, `data-closed`, `data-open`, `data-state` |
| `combobox-item` | `data-value` string | `data-disabled`, `data-highlighted` |
| `combobox-list` |  | `data-empty` |

Other parts: `combobox-chip-input`, `combobox-chips`, `combobox-clear`, `combobox-empty`, `combobox-group`, `combobox-label`, `combobox-separator`, `combobox-value`.

Kit adds: `combobox-chip`, `combobox-chip-remove`, `combobox-item-indicator`, `combobox-trigger-icon`.

Part attributes: `data-combobox-trigger` boolean.

Events: `combobox:open`; `combobox:close`; `combobox:change` `{ value }`.

## Full text

### Combobox

```html
<div data-slot="combobox" data-name="framework" data-value="next" data-auto-highlight>
  <div data-slot="input-group">
    <input data-slot="input-group-control" placeholder="Select a framework" aria-label="Framework">
    <div data-slot="input-group-addon" data-align="inline-end">
      <button type="button" data-slot="input-group-button" data-combobox-trigger></button>
      <button type="button" data-slot="combobox-clear"></button>
    </div>
  </div>
  <div data-slot="combobox-content">
    <div data-slot="combobox-empty">No items found.</div>
    <div data-slot="combobox-list">
      <div data-slot="combobox-group">
        <div data-slot="combobox-label">Frameworks</div>
        <div data-slot="combobox-item" data-value="next">Next.js</div>
      </div>
      <div data-slot="combobox-separator"></div>
    </div>
  </div>
</div>
```

- Outside press as in Base UI: a mouse press outside closes the list at the press; a touch outside closes it only on the tap click, so a touch drag to scroll keeps it open.
- Multiple: `data-multiple`, `<div data-slot="combobox-chips"><input data-slot="combobox-chip-input"></div>` instead of the input group, initial values in `data-value="a,b"`. The kit renders `combobox-chip` and `combobox-chip-remove`.
- Popup: `<button type="button" data-slot="button" data-variant="outline" data-combobox-trigger><span data-slot="combobox-value">Select country</span></button>` outside the content and the input group inside it.
- The input group gets `data-combobox-input`. The trigger is `data-slot="input-group-button"` (`data-size="icon-xs"` when missing) with `data-combobox-trigger`; it has `tabindex="0"` like Base UI (the label `Show options` stays, Base UI has none). `combobox-clear` has `tabindex="-1"` like Base UI. While the list is open, a visually hidden `<span role="button" aria-label="Dismiss">` (string `dismiss`) before the input closes the list. `combobox-empty` is a polite `role="status"` region; the content and the list have `tabindex="-1"`. While the list is open, the input and the trigger have `data-pressed`, `data-popup-open`, and `data-popup-side`; the trigger has `data-placeholder` without a value; both have `data-list-empty` when the filter shows nothing. A pointer press on the trigger opens the list at once.
- `data-disabled`, `data-required`, `data-name` as in `select` (one hidden proxy input, focus moves from the proxy to the input). `data-value` as in `select`: later items and a later `data-value` change apply it without a `change` event; the kit does not write it back. Typing filters by label (case-insensitive substring), hides empty groups and separators, and shows `combobox-empty`. The highlighted item is `aria-activedescendant`.
- Keyboard: Down and Up (also with Alt) open and move; after the last item (or before the first) the highlight goes back to the input, like Base UI `loopFocus`. Alt+Up closes, Enter selects (or closes when no item is highlighted), Escape closes; Escape on a closed combobox clears the value (all chips in multiple). Home and End move the caret and never scroll the page. Chips (`role="toolbar"`): Backspace in an empty input removes the last chip, Left moves into the chips, Backspace and Delete remove a chip.
