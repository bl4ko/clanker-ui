# Dropdown Menu (`dropdown-menu`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `dropdown-menu-checkbox-item` | `data-checked` boolean | `data-disabled`, `data-inset` |
| `dropdown-menu-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `dropdown-menu-item` | `data-variant` `destructive` | `data-disabled`, `data-inset` |
| `dropdown-menu-label` |  | `data-inset` |
| `dropdown-menu-radio-group` | `data-value` string |  |
| `dropdown-menu-radio-item` | `data-checked` boolean; `data-value` string | `data-disabled`, `data-inset` |
| `dropdown-menu-sub-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `dropdown-menu-sub-trigger` |  | `data-inset`, `data-open`, `data-popup-open`, `data-state` |

Other parts: `dropdown-menu` (root), `dropdown-menu-group`, `dropdown-menu-separator`, `dropdown-menu-shortcut`, `dropdown-menu-sub`, `dropdown-menu-trigger`.

Kit adds: `dropdown-menu-checkbox-item-indicator`, `dropdown-menu-radio-item-indicator`.

Part attributes: `data-dropdown-menu-trigger` boolean.

Other options named in the docs: `data-close-on-click` any; `data-disabled` any; `data-inset` any; `data-state` string; `data-text-value` any.

Events: `dropdown-menu:open` `{ trigger }`; `dropdown-menu:close` `{ reason }`; `dropdown-menu:select` `{ value, item, checked }` (cancelable); `dropdown-menu:change` `{ value, checked, item, group }`.

## Full text

### Dropdown Menu, Context Menu, Menubar

```html
<div data-slot="dropdown-menu">
  <button type="button" data-slot="button" data-variant="outline" data-dropdown-menu-trigger>Open</button>
  <div data-slot="dropdown-menu-content" data-side="bottom" data-align="end">
    <div data-slot="dropdown-menu-group">
      <div data-slot="dropdown-menu-label">My Account</div>
      <div data-slot="dropdown-menu-item">Profile<span data-slot="dropdown-menu-shortcut">⇧⌘P</span></div>
      <div data-slot="dropdown-menu-checkbox-item" data-checked>Status Bar</div>
    </div>
    <div data-slot="dropdown-menu-radio-group" data-value="top">
      <div data-slot="dropdown-menu-radio-item" data-value="top" data-checked>Top</div>
    </div>
    <div data-slot="dropdown-menu-separator"></div>
    <div data-slot="dropdown-menu-sub">
      <div data-slot="dropdown-menu-sub-trigger">Invite users</div>
      <div data-slot="dropdown-menu-sub-content">...</div>
    </div>
  </div>
</div>
```

- Same parts with the `context-menu-` and `menubar-` prefixes, plus `-group`, `-radio-group`, and `-label` (`menubar-label` too). Items: `data-disabled`, `data-inset`, `data-variant="destructive"` (other items get `data-variant="default"`), `data-value`, `data-text-value` (typeahead label), `data-close-on-click`. Checkbox and radio items: `data-checked` (or `data-state="checked"`). `data-value` on a radio group selects the item with that value. A later change of `data-value` on the radio group or of `data-checked` on an item, from code, updates the items (no event). Links work as items.
- Base UI DOM and states: a label gets `role="presentation"` and names its group (`aria-labelledby`); a separator gets `data-orientation="horizontal"`; checkbox and radio items get `data-checked` or `data-unchecked` and an indicator as the first child (`dropdown-menu-checkbox-item-indicator`, `dropdown-menu-radio-item-indicator`; a `span` without a slot in context menus and menubars) that holds `<span data-checked aria-hidden="true">` with the `check` icon only while checked. The highlighted item has `data-highlighted`; an open sub menu's trigger has `data-popup-open` and loses `data-highlighted` while focus or the pointer is in the sub menu. The content has `data-open` or `data-closed`, `data-side`, `data-align`, and `data-instant` (`click` when a keyboard key or a right click opened it, `group` when a menubar switched menus, `dismiss` after Escape); the trigger has `data-popup-open` and `data-pressed` while open.
- `dropdown-menu:change` and `:select` are emitted on the `dropdown-menu` root (also for an item in a sub menu or a radio group) and bubble to `document`; a listener on the radio group gets nothing. `detail.group` is the radio group element (`dropdown-menu-radio-group`, `null` outside a group; it is absent for a checkbox item): read `event.detail.group.id` or `.dataset` to tell two groups apart, and `detail.value` for the new value (the group `data-value` is already set).
- A plain item closes the menu; checkbox and radio items keep it open (Base UI `closeOnClick`), unless `data-close-on-click` says otherwise.
- Keyboard per WAI-ARIA APG with Base UI focus looping: Enter, Space, and ArrowDown open at the first item, ArrowUp at the last; arrows wrap from the last item to the first and back, Home, End, typeahead; arrows also stop on disabled items (highlighted, `aria-disabled`, they do not run), as in Base UI; ArrowRight opens a sub menu, ArrowLeft closes it (mirrored in RTL); Escape closes the innermost menu; Tab closes all. Typeahead continues across a space (`New W` reaches "New Window"); Space activates the item only when no typeahead is in progress.
- A sub menu opens 100 ms after the pointer rests on its trigger. On the way to the sub menu the pointer may cross other items inside the triangle from the pointer to the sub menu (Base UI safe polygon). The sub menu closes when the pointer leaves the trigger on the side away from the sub menu, leaves the triangle, moves slower than 0.1 px/ms, or stops for 40 ms; then the menu keeps focus with no highlight until the pointer moves again.
- A trigger click runs app `click` listeners as usual, also when a mouse press already opened the menu.
- A menu item that opens a dialog (`data-dialog-trigger="id"`) returns focus to the menu trigger when the dialog closes.
