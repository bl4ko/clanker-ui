# Navigation Menu (`navigation-menu`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `navigation-menu-content` |  | `data-activation-direction`, `data-closed`, `data-ending-style`, `data-motion`, `data-open`, `data-starting-style`, `data-state` |
| `navigation-menu-indicator` |  | `data-state` |
| `navigation-menu-link` | `data-active` any; `data-close-on-click` any; `data-variant` `trigger` | `data-open`, `data-popup-open`, `data-state` |
| `navigation-menu-popup` (kit adds) |  | `data-ending-style`, `data-starting-style` |
| `navigation-menu-positioner` (kit adds) |  | `data-align`, `data-instant`, `data-side` |
| `navigation-menu-trigger` |  | `data-open`, `data-popup-open`, `data-state` |

Other parts: `navigation-menu` (root), `navigation-menu-item`, `navigation-menu-list`.

Kit adds: `navigation-menu-focus-guard`, `navigation-menu-indicator-arrow`, `navigation-menu-viewport`.

Other options named in the docs: `data-close-delay` any; `data-delay` any; `data-viewport` `false`, `true`.

Events: `navigation-menu:change` `{ value }`; `navigation-menu:select` `{ link, href }`.

```html
<nav data-slot="navigation-menu" aria-label="Main">
  <ul data-slot="navigation-menu-list">
    <li data-slot="navigation-menu-item">
      <button type="button" data-slot="navigation-menu-trigger">Getting started</button>
      <div data-slot="navigation-menu-content">
        <ul>
          <li><a data-slot="navigation-menu-link" href="/docs">Introduction</a></li>
          <li><a data-slot="navigation-menu-link" href="/docs/installation">Installation</a></li>
        </ul>
      </div>
    </li>
    <li data-slot="navigation-menu-item">
      <a data-slot="navigation-menu-link" data-variant="trigger" href="/docs" data-active>Docs</a>
    </li>
  </ul>
</nav>
```

## Full text

### Navigation Menu

`nav[data-slot="navigation-menu"]` > `navigation-menu-list` > `navigation-menu-item` > `navigation-menu-trigger` + `navigation-menu-content`, or a `navigation-menu-link` (`data-variant="trigger"`, `data-active`, `data-close-on-click`). Optional `navigation-menu-indicator`. The app sets only `data-active` on the current link; the kit keeps `aria-current="page"` in sync, also when `data-active` changes later.

- The kit adds the Base UI parts at the end of the root: `navigation-menu-positioner` (a top-layer popup at the open trigger: bottom, `data-align` of the root or `start`, 8 px) > `nav[data-slot="navigation-menu-popup"]` > `navigation-menu-viewport`. The open content moves into the viewport and back to its item when it closes. `data-viewport="false"` places each content under its trigger instead (8 px).
- States as in Base UI: root and list `data-open`; trigger `data-popup-open` and `aria-expanded`; positioner and popup `data-open`/`data-closed`, `data-side`, `data-align`; content `data-open`/`data-closed`, `data-starting-style`/`data-ending-style`, and `data-activation-direction` (`right` when the new item comes after the old one in the list, `left` before; logical, so the motion follows RTL). The positioner has `data-instant` on the first open (no slide), `--positioner-width`/`--positioner-height`, and the popup `--popup-width`/`--popup-height`: when the panel changes, the popup animates from the old size to the new one, the positioner slides to the new trigger, and the old content leaves (absolute, `data-ending-style`) while the new one enters.
- Hover opens after 50 ms and closes 50 ms after the pointer leaves (`data-delay`, `data-close-delay` on the root); a switch to another panel waits for the same delay; a click toggles. The open trigger has `data-pressed`. Enter, Space, or ArrowDown on a closed trigger opens it and focuses the first link in the panel; ArrowDown or Tab on an open trigger enters the panel; Home and End do nothing (the page scrolls), as in Base UI; Tab after its last link goes to the next trigger, Shift+Tab from its first link goes back and Shift+Tab from the next trigger goes to its last link (focus guards at both ends of the popup and after the open trigger, as in Base UI, so this also works in Safari, where Tab skips links; Tab from the last trigger leaves the menu); arrows move between links; Escape closes and focuses the open trigger, also when a hover switch moved the open panel. The positioner follows the size of the open content (`ResizeObserver`); sizes are layout sizes, so a scale animation does not shrink them. A link click keeps the menu open (Base UI `closeOnClick` is false) unless the link has `data-close-on-click`. A menu removed while open comes back closed.
- An outside press closes the menu on the click, as in Base UI (a held press, a right or middle click, or a touch drag keep it open). Only a menu that hover opened closes when the pointer leaves; a menu opened by a click or a key stays open, and so does a menu where a press on a link starts a drag.
