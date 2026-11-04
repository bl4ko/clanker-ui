# clanker-ui components

Generated from `clanker-ui.json` (same directory) by `go run ./tools/gen catalog`. Version 0.2.1 (the last release; a copy from `main` can be newer, see the Unreleased part of `CHANGELOG.md`), shadcn `b8d7baa`, Base UI 1.6.0.

Read the file of each component: `components/<name>.md`, for example [components/button.md](components/button.md).

## Groups

Each group has `clanker-ui-<group>.min.css` and (except core CSS-only parts) `clanker-ui-<group>.min.js`. Load `core` always, then the group of each component and the groups in its **Needs**.

| Group | Components |
| --- | --- |
| `core` | button, separator, direction, theme, input, textarea, label, kbd, card, badge, alert, table, skeleton, spinner, empty, progress, aspect-ratio, page, site-header, section-cards, stat-grid, data-table, brand, text-stack |
| `forms` | button-group, input-group, input-otp, field, form, checkbox, radio-group, switch, slider, select, native-select, combobox, toggle, toggle-group |
| `overlays` | dialog, alert-dialog, sheet, drawer, popover, tooltip, hover-card, dropdown-menu, context-menu, menubar, navigation-menu, command, toast, sonner |
| `layout` | avatar, accordion, collapsible, tabs, breadcrumb, pagination, scroll-area, resizable, sidebar, carousel, item |
| `chat` | message, bubble, attachment, message-scroller, trace, marker, questionnaire, code-block, calendar, date-picker |
| `chart` | chart |

Global attributes (any element): `data-align` `center`, `end`, `start`; `data-align-offset` number; `data-hide-from` `lg`, `md`, `sm`, `xl`; `data-icon` `inline-end`, `inline-start`; `data-loop` boolean; `data-lucide` string; `data-multiple` boolean; `data-required` boolean; `data-scheme` string; `data-show-from` `lg`, `md`, `sm`, `xl`; `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top`; `data-side-offset` number; `data-theme-picker` string; `data-theme-set` `dark`, `light`, `system`, `toggle`; `data-typography` (empty), `blockquote`, `h1`, `h2`, `h3`, `h4`, `inline-code`, `large`, `lead`, `list`, `muted`, `p`, `small`, `table`; `data-string-<key>` (localized label override).

## Component files

Each component has one file, `components/<name>.md`: group, needs, parts, attributes, events, exports, and the full text from the README. **Parts** lists each `data-slot`. **Write** = attributes you may author. **State** = attributes the kit sets; style on them, never write them. **Kit adds** = parts the kit creates; do not write them. **Part attributes** go on an element of another component (for example a `button`) to give it this component's behavior.
