# clanker-ui components

Generated from `clanker-ui.json` (same directory) by `go run ./tools/gen catalog`. Version 0.1.0, shadcn `b8d7baa`, Base UI 1.6.0.

## Groups

Each group has `clanker-ui-<group>.min.css` and (except core CSS-only parts) `clanker-ui-<group>.min.js`. Load `core` always, then the group of each component and the groups in its **Needs**.

| Group | Components |
| --- | --- |
| `core` | [button](components/button.md), [separator](components/separator.md), [direction](components/direction.md), [theme](components/theme.md), [input](components/input.md), [textarea](components/textarea.md), [label](components/label.md), [kbd](components/kbd.md), [card](components/card.md), [badge](components/badge.md), [alert](components/alert.md), [table](components/table.md), [skeleton](components/skeleton.md), [spinner](components/spinner.md), [empty](components/empty.md), [progress](components/progress.md), [aspect-ratio](components/aspect-ratio.md) |
| `forms` | [button-group](components/button-group.md), [input-group](components/input-group.md), [input-otp](components/input-otp.md), [field](components/field.md), [form](components/form.md), [checkbox](components/checkbox.md), [radio-group](components/radio-group.md), [switch](components/switch.md), [slider](components/slider.md), [select](components/select.md), [native-select](components/native-select.md), [combobox](components/combobox.md), [toggle](components/toggle.md), [toggle-group](components/toggle-group.md) |
| `overlays` | [dialog](components/dialog.md), [alert-dialog](components/alert-dialog.md), [sheet](components/sheet.md), [drawer](components/drawer.md), [popover](components/popover.md), [tooltip](components/tooltip.md), [hover-card](components/hover-card.md), [dropdown-menu](components/dropdown-menu.md), [context-menu](components/context-menu.md), [menubar](components/menubar.md), [navigation-menu](components/navigation-menu.md), [command](components/command.md), [toast](components/toast.md), [sonner](components/sonner.md) |
| `layout` | [avatar](components/avatar.md), [accordion](components/accordion.md), [collapsible](components/collapsible.md), [tabs](components/tabs.md), [breadcrumb](components/breadcrumb.md), [pagination](components/pagination.md), [scroll-area](components/scroll-area.md), [resizable](components/resizable.md), [sidebar](components/sidebar.md), [carousel](components/carousel.md), [item](components/item.md) |
| `chat` | [message](components/message.md), [bubble](components/bubble.md), [attachment](components/attachment.md), [message-scroller](components/message-scroller.md), [trace](components/trace.md), [marker](components/marker.md), [questionnaire](components/questionnaire.md), [code-block](components/code-block.md), [calendar](components/calendar.md), [date-picker](components/date-picker.md) |
| `chart` | [chart](components/chart.md) |

Global attributes (any element): `data-align` `center`, `end`, `start`; `data-align-offset` number; `data-icon` `inline-end`, `inline-start`; `data-loop` boolean; `data-lucide` string; `data-multiple` boolean; `data-required` boolean; `data-scheme` string; `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top`; `data-side-offset` number; `data-theme-picker` string; `data-theme-set` `dark`, `light`, `system`, `toggle`; `data-typography` (empty), `blockquote`, `h1`, `h2`, `h3`, `h4`, `inline-code`, `large`, `lead`, `list`, `muted`, `p`, `small`, `table`; `data-string-<key>` (localized label override).

## Component files

Each component has one file, `components/<name>.md`: group, needs, parts, attributes, events, exports, and the full text from the README. **Parts** lists each `data-slot`. **Write** = attributes you may author. **State** = attributes the kit sets; style on them, never write them. **Kit adds** = parts the kit creates; do not write them. **Part attributes** go on an element of another component (for example a `button`) to give it this component's behavior.
