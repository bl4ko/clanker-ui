# Sidebar (`sidebar`)

Group `layout`. Needs `core`, `overlays`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `sidebar` (root) | `data-collapsible` `icon`, `none`, `offcanvas`; `data-side` `bottom`, `left`, `right`, `top`; `data-variant` `floating`, `inset`, `sidebar` | `data-ending-style`, `data-mobile`, `data-starting-style`, `data-state` |
| `sidebar-container` | `data-side` `left`, `right` |  |
| `sidebar-menu-action` | `data-show-on-hover` any |  |
| `sidebar-menu-button` | `data-active` `false`, `true`; `data-size` `default`, `lg`, `sm`; `data-tooltip` string; `data-variant` `default`, `outline` | `data-state` |
| `sidebar-menu-skeleton` | `data-show-icon` any |  |
| `sidebar-menu-sub-button` | `data-size` `md`, `sm` | `data-active`, `data-state` |
| `sidebar-separator` | `data-orientation` `horizontal`, `vertical` |  |

Other parts: `sidebar-content`, `sidebar-footer`, `sidebar-gap`, `sidebar-group`, `sidebar-group-action`, `sidebar-group-content`, `sidebar-group-label`, `sidebar-header`, `sidebar-inner`, `sidebar-input`, `sidebar-inset`, `sidebar-menu`, `sidebar-menu-badge`, `sidebar-menu-item`, `sidebar-menu-sub`, `sidebar-menu-sub-item`, `sidebar-rail`, `sidebar-trigger`, `sidebar-wrapper`.

Other options named in the docs: `data-mobile` string.

Events: `sidebar:open` `{ mobile }`; `sidebar:close` `{ mobile }`.

## Full text

### Sidebar

```html
<div data-slot="sidebar-wrapper" id="app">
  <div data-slot="sidebar" data-side="left" data-variant="sidebar|floating|inset" data-collapsible="offcanvas|icon|none">
    <div data-slot="sidebar-gap"></div>
    <div data-slot="sidebar-container">
      <div data-slot="sidebar-inner">
        <div data-slot="sidebar-header">...</div>
        <div data-slot="sidebar-content">
          <div data-slot="sidebar-group">
            <div data-slot="sidebar-group-label">Platform</div>
            <ul data-slot="sidebar-menu">
              <li data-slot="sidebar-menu-item">
                <a data-slot="sidebar-menu-button" data-active="true" data-tooltip="Home" href="/"><svg data-lucide="house"></svg><span>Home</span></a>
                <div data-slot="sidebar-menu-badge">24</div>
              </li>
            </ul>
          </div>
        </div>
        <div data-slot="sidebar-footer">...</div>
      </div>
      <button data-slot="sidebar-rail"></button>
    </div>
  </div>
  <main data-slot="sidebar-inset"><button data-slot="sidebar-trigger"></button>...</main>
</div>
```

- Parts: `sidebar-group-action`, `sidebar-group-content`, `sidebar-menu-button` (`data-variant="outline"`, `data-size="sm|lg"`, `data-active`), `sidebar-menu-action` (`data-show-on-hover`), `sidebar-menu-skeleton` (`data-show-icon`), `sidebar-menu-sub`, `sidebar-menu-sub-item`, `sidebar-menu-sub-button`, `sidebar-input`, `sidebar-separator`.
- A trigger controls the sidebar in its wrapper, or the one named by `aria-controls`. Ctrl/⌘+B toggles the sidebar of the focused wrapper, else the first one. The state is stored in `localStorage["sidebar_state:<wrapper id>"]`.
- In icon mode, collapsed menu buttons with `data-tooltip` show a `tooltip-content`. Below 768 px the sidebar is a modal sheet (`data-mobile="open"`). When Escape, a trigger, or Ctrl/⌘+B closes the sheet, focus goes back to the element that had focus when it opened (the trigger, when the trigger opened it). An outside click closes it and does not move focus back.
- `data-side="left|right"` is inline start and inline end (see [Direction](direction.md)). The kit copies it to `sidebar-container`, like shadcn, and sets `--sidebar-width: 16rem` and `--sidebar-width-icon: 3rem` on the wrapper.
- The mobile sheet is the `sidebar` root, like the shadcn mobile sidebar (a sheet): 75 % of the viewport wide, at most 24rem, at the inline-start side. While it is open, the kit shows it in the top layer (`popover="manual"`) above a `sheet-overlay` element that it adds before the root: the overlay covers the viewport with `rgb(0 0 0 / 0.1)` and a 4 px blur, and a click on it closes the sheet. The sheet fades in from 2.5rem with `data-starting-style` and out with `data-ending-style` (200 ms); the overlay fades in 150 ms. The kit removes the overlay when the sheet is closed.
