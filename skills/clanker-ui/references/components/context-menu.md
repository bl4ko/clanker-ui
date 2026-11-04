# Context Menu (`context-menu`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `context-menu-checkbox-item` | `data-checked` boolean | `data-disabled`, `data-inset` |
| `context-menu-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `context-menu-item` | `data-variant` `destructive` | `data-disabled`, `data-inset` |
| `context-menu-label` |  | `data-inset` |
| `context-menu-radio-group` | `data-value` string |  |
| `context-menu-radio-item` | `data-checked` boolean; `data-value` string | `data-disabled`, `data-inset` |
| `context-menu-sub-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `context-menu-sub-trigger` |  | `data-inset`, `data-open`, `data-state` |

Other parts: `context-menu` (root), `context-menu-group`, `context-menu-separator`, `context-menu-shortcut`, `context-menu-sub`, `context-menu-trigger`.

Other options named in the docs: `data-close-on-click` any; `data-disabled` any; `data-inset` any; `data-state` string; `data-text-value` any.

Events: `context-menu:open` `{ trigger }`; `context-menu:close` `{ reason }`; `context-menu:select` `{ value, item, checked }` (cancelable); `context-menu:change` `{ value, checked, item, group }`.

```html
<div data-slot="context-menu">
  <div data-slot="context-menu-trigger" tabindex="0" aria-label="Context menu area">Right click here</div>
  <div data-slot="context-menu-content">
    <div data-slot="context-menu-group">
      <div data-slot="context-menu-item">Back<span data-slot="context-menu-shortcut">⌘[</span></div>
      <div data-slot="context-menu-item" data-disabled>Forward</div>
      <div data-slot="context-menu-sub">
        <div data-slot="context-menu-sub-trigger">More Tools</div>
        <div data-slot="context-menu-sub-content">
          <div data-slot="context-menu-item" data-variant="destructive">Delete</div>
        </div>
      </div>
    </div>
    <div data-slot="context-menu-separator"></div>
    <div data-slot="context-menu-checkbox-item" data-checked>Show Bookmarks</div>
    <div data-slot="context-menu-radio-group" data-value="pedro">
      <div data-slot="context-menu-label">People</div>
      <div data-slot="context-menu-radio-item" data-value="pedro" data-checked>Pedro Duarte</div>
      <div data-slot="context-menu-radio-item" data-value="colm">Colm Tuite</div>
    </div>
  </div>
</div>
```

## Full text

### Dropdown Menu, Context Menu, Menubar

- Same parts with the `context-menu-` and `menubar-` prefixes, plus `-group`, `-radio-group`, and `-label` (`menubar-label` too). Items: `data-disabled`, `data-inset`, `data-variant="destructive"` (other items get `data-variant="default"`), `data-value`, `data-text-value` (typeahead label), `data-close-on-click`. Checkbox and radio items: `data-checked` (or `data-state="checked"`). `data-value` on a radio group selects the item with that value. A later change of `data-value` on the radio group or of `data-checked` on an item, from code, updates the items (no event). Links work as items.
- Base UI DOM and states: a label gets `role="presentation"` and names its group (`aria-labelledby`); a separator gets `data-orientation="horizontal"`; checkbox and radio items get `data-checked` or `data-unchecked` and an indicator as the first child (`dropdown-menu-checkbox-item-indicator`, `dropdown-menu-radio-item-indicator`; a `span` without a slot in context menus and menubars) that holds `<span data-checked aria-hidden="true">` with the `check` icon only while checked. The highlighted item has `data-highlighted`; an open sub menu's trigger has `data-popup-open` and loses `data-highlighted` while focus or the pointer is in the sub menu. The content has `data-open` or `data-closed`, `data-side`, `data-align`, and `data-instant` (`click` when a keyboard key or a right click opened it, `group` when a menubar switched menus, `dismiss` after Escape); the trigger has `data-popup-open` and `data-pressed` while open.
- A plain item closes the menu; checkbox and radio items keep it open (Base UI `closeOnClick`), unless `data-close-on-click` says otherwise.
- A mouse press on the trigger opens the menu; release over an item to choose it (press, drag, release). Placement: dropdown bottom, start, 4 px; context menu at the pointer, right, start, `alignOffset` 4; menubar bottom, start, 8 px, `alignOffset` -4; sub menus right, start, `alignOffset` -3 (context menu 4); 5 px from the viewport edge.
- Keyboard per WAI-ARIA APG with Base UI focus looping: Enter, Space, and ArrowDown open at the first item, ArrowUp at the last; arrows wrap from the last item to the first and back, Home, End, typeahead; arrows also stop on disabled items (highlighted, `aria-disabled`, they do not run), as in Base UI; ArrowRight opens a sub menu, ArrowLeft closes it (mirrored in RTL); Escape closes the innermost menu; Tab closes all. Typeahead continues across a space (`New W` reaches "New Window"); Space activates the item only when no typeahead is in progress.
- A sub menu opens 100 ms after the pointer rests on its trigger. On the way to the sub menu the pointer may cross other items inside the triangle from the pointer to the sub menu (Base UI safe polygon). The sub menu closes when the pointer leaves the trigger on the side away from the sub menu, leaves the triangle, moves slower than 0.1 px/ms, or stops for 40 ms; then the menu keeps focus with no highlight until the pointer moves again.
- A trigger click runs app `click` listeners as usual, also when a mouse press already opened the menu.
- A menu item that opens a dialog (`data-dialog-trigger="id"`) returns focus to the menu trigger when the dialog closes.
- Context menu: `context-menu-trigger` is the area (give it `tabindex="0"`). Right click, long press (700 ms), Shift+F10, or the ContextMenu key open it.
