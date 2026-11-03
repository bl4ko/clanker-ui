# Menubar (`menubar`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `menubar-checkbox-item` | `data-checked` boolean | `data-disabled`, `data-inset` |
| `menubar-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `menubar-item` | `data-variant` `destructive` | `data-disabled`, `data-inset` |
| `menubar-label` |  | `data-inset` |
| `menubar-radio-group` | `data-value` string |  |
| `menubar-radio-item` | `data-checked` boolean; `data-value` string | `data-disabled`, `data-inset` |
| `menubar-sub-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `menubar-sub-trigger` |  | `data-inset`, `data-open`, `data-popup-open`, `data-state` |

Other parts: `menubar` (root), `menubar-group`, `menubar-menu`, `menubar-separator`, `menubar-shortcut`, `menubar-sub`, `menubar-trigger`.

Other options named in the docs: `data-close-on-click` any; `data-disabled` any; `data-inset` any; `data-modal` `false`, `true`; `data-state` string; `data-text-value` any.

Events: `menubar:open` `{ trigger }`; `menubar:close` `{ reason }`; `menubar:select` `{ value, item, checked }` (cancelable); `menubar:change` `{ value, checked, item, group }`.

```html
<div data-slot="menubar">
  <div data-slot="menubar-menu">
    <button type="button" data-slot="menubar-trigger">File</button>
    <div data-slot="menubar-content">
      <div data-slot="menubar-group">
        <div data-slot="menubar-item">New Tab<span data-slot="menubar-shortcut">⌘T</span></div>
        <div data-slot="menubar-item" data-disabled>New Incognito Window</div>
      </div>
      <div data-slot="menubar-separator"></div>
      <div data-slot="menubar-sub">
        <div data-slot="menubar-sub-trigger">Share</div>
        <div data-slot="menubar-sub-content">
          <div data-slot="menubar-item">Email link</div>
        </div>
      </div>
    </div>
  </div>
  <div data-slot="menubar-menu">
    <button type="button" data-slot="menubar-trigger">View</button>
    <div data-slot="menubar-content">
      <div data-slot="menubar-checkbox-item" data-checked>Full URLs</div>
      <div data-slot="menubar-item" data-inset>Reload</div>
    </div>
  </div>
</div>
```

## Full text

### Dropdown Menu, Context Menu, Menubar

- Same parts with the `context-menu-` and `menubar-` prefixes, plus `-group`, `-radio-group`, and `-label` (`menubar-label` too). Items: `data-disabled`, `data-inset`, `data-variant="destructive"` (other items get `data-variant="default"`), `data-value`, `data-text-value` (typeahead label), `data-close-on-click`. Checkbox and radio items: `data-checked` (or `data-state="checked"`). Links work as items.
- Base UI DOM and states: a label gets `role="presentation"` and names its group (`aria-labelledby`); a separator gets `data-orientation="horizontal"`; checkbox and radio items get `data-checked` or `data-unchecked` and an indicator as the first child (`dropdown-menu-checkbox-item-indicator`, `dropdown-menu-radio-item-indicator`; a `span` without a slot in context menus and menubars) that holds `<span data-checked aria-hidden="true">` with the `check` icon only while checked. The highlighted item has `data-highlighted`; an open sub menu's trigger has `data-popup-open` and loses `data-highlighted` while focus or the pointer is in the sub menu. The content has `data-open` or `data-closed`, `data-side`, `data-align`, and `data-instant` (`click` when a keyboard key or a right click opened it, `group` when a menubar switched menus, `dismiss` after Escape); the trigger has `data-popup-open` and `data-pressed` while open.
- A plain item closes the menu; checkbox and radio items keep it open (Base UI `closeOnClick`), unless `data-close-on-click` says otherwise.
- Like Base UI, menus are modal (`data-modal="false"` on the root or `menubar` turns this off): page scroll is locked, and the first press outside only closes the menu (the click does not reach the element below, and focus returns to the trigger). A touch outside closes it when the tap ends, or during a drag of more than 10 px.
- A mouse press on the trigger opens the menu; release over an item to choose it (press, drag, release). Placement: dropdown bottom, start, 4 px; context menu at the pointer, right, start, `alignOffset` 4; menubar bottom, start, 8 px, `alignOffset` -4; sub menus right, start, `alignOffset` -3 (context menu 4); 5 px from the viewport edge.
- Keyboard per WAI-ARIA APG with Base UI focus looping: Enter, Space, and ArrowDown open at the first item, ArrowUp at the last; arrows wrap from the last item to the first and back, Home, End, typeahead; arrows also stop on disabled items (highlighted, `aria-disabled`, they do not run), as in Base UI; ArrowRight opens a sub menu, ArrowLeft closes it (mirrored in RTL); Escape closes the innermost menu; Tab closes all. Typeahead continues across a space (`New W` reaches "New Window"); Space activates the item only when no typeahead is in progress.
- A sub menu opens 100 ms after the pointer rests on its trigger. On the way to the sub menu the pointer may cross other items inside the triangle from the pointer to the sub menu (Base UI safe polygon). The sub menu closes when the pointer leaves the trigger on the side away from the sub menu, leaves the triangle, moves slower than 0.1 px/ms, or stops for 40 ms; then the menu keeps focus with no highlight until the pointer moves again.
- A trigger click runs app `click` listeners as usual, also when a mouse press already opened the menu.
- A menu item that opens a dialog (`data-dialog-trigger="id"`) returns focus to the menu trigger when the dialog closes.
- Menubar: `menubar` > `menubar-menu` > `menubar-trigger` + `menubar-content`. The bar gets `aria-orientation`, `data-orientation="horizontal"`, and `data-modal`. Roving focus; ArrowLeft and ArrowRight in an open menu open the next menu and focus its popup (no item highlighted; ArrowDown goes to the first item); while a menu is open, hover switches menus and moves focus to the new menu (the old menu closes 45 ms later, as Base UI closes it after the new menu renders); a click on another trigger while a menu is open, or on the open trigger, closes the menus and focuses that trigger. An outside press closes the menu and returns focus to the trigger, as in other modal menus.
