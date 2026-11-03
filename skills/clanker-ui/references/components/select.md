# Select (`select`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `select` (root) | `data-name` string; `data-value` string |  |
| `select-content` | `data-align-trigger` `false`, `true`; `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `select-item` | `data-disabled` boolean; `data-label` string; `data-value` string |  |
| `select-trigger` | `data-size` `default`, `sm` | `data-placeholder` |

Other parts: `select-group`, `select-label`, `select-separator`, `select-value`.

Kit adds: `select-icon`, `select-item-indicator`, `select-item-text`, `select-scroll-down-button`, `select-scroll-up-button`, `select-viewport`.

Events: `select:open`; `select:close`; `select:change` `{ value }`.

## Full text

### Select

```html
<div data-slot="select" data-name="fruit" data-value="apple" data-required>
  <button data-slot="select-trigger" data-size="sm"><span data-slot="select-value">Select a fruit</span></button>
  <div data-slot="select-content" data-align-trigger="true|false">
    <div data-slot="select-group">
      <div data-slot="select-label">Fruits</div>
      <div data-slot="select-item" data-value="apple" data-label="Apple">Apple</div>
      <div data-slot="select-item" data-value="banana" data-disabled>Banana</div>
    </div>
    <div data-slot="select-separator"></div>
  </div>
</div>
```

- The first content of `select-value` is the placeholder (`data-placeholder` on the trigger and the value while no item is selected). The trigger shows a copy of the selected item, or `data-label`. The kit adds the chevron, scroll buttons, `select-viewport`, `select-item-text`, ARIA, and a visually hidden proxy input that submits `data-name`. Only the selected item has `data-selected` and a `select-item-indicator`; with no value, an item with `data-value=""` is the selected one, like the Base UI `null` item. The focused item has `data-highlighted`. While open, the trigger has `data-pressed` and `data-popup-side`. The trigger has `tabindex="0"` like Base UI, so Tab reaches it also in Safari.
- `data-required` makes the proxy `required`. In a `data-slot="form"` the kit shows the error. In other forms native validation reports the proxy (the browser shows its message just below the trigger) and the kit moves focus from the proxy to the trigger.
- Removing and inserting a select again keeps one proxy input, the authored placeholder, and the authored initial value (form reset goes back to it).
- `data-value` is the value: a later change selects that item without a `change` event, and items that arrive later (after a `fetch`) select the authored value. While no item matches, the trigger shows the placeholder and the proxy is empty.
- `data-align-trigger="true"` (default, Base UI `alignItemWithTrigger`) puts the selected item text over the value (`data-side="none"`); `false` (or the old `data-position="popper"`) places the list under the trigger.
- Pointer: a press on the trigger opens the list; moving to an item and releasing selects it, and releasing outside the trigger and the list closes it (Base UI). The focused item has no focus ring after a pointer open, unless the trigger had one (browsers without `focus({ focusVisible })`, before Chrome 145 and Safari 18.4, show the ring). Keyboard: Enter, Space, Up, Down open on the selected item; typing on the closed trigger selects the next match (750 ms buffer) without opening. In the list: arrows (no wrap), Home, End, typeahead (a space within 750 ms of a typed letter is part of the search), Enter or Space to select, Escape to close, Tab closes without a change and moves on. A press outside closes the list and focus goes back to the trigger, unless the press focused another control.
