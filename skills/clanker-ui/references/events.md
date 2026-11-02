# clanker-ui events

Generated from `clanker-ui.json` (same directory) by `go run ./tools/gen catalog`.

All events are bubbling, composed `CustomEvent`s named `<component>:<action>`. Listen on the root or on `document`, and read `event.detail`. A cancelable event stops the default action when a listener calls `event.preventDefault()`. Components that wrap a native control (slider, native select, input, the hidden input of checkbox, switch, and radio) also fire the native `input` and `change` events.

```js
document.addEventListener("select:change", event => console.log(event.target, event.detail.value))
```

| Event | Component | Target | `detail` | Notes |
| --- | --- | --- | --- | --- |
| `theme:change` | `theme` | `<html>` | `mode`, `resolved`, `scheme` | `{ mode, resolved, scheme }`, after a mode or scheme change |
| `input-otp:complete` | `input-otp` | `input-otp` | `value` |  |
| `form:invalid` | `form` | `form` | `errors` |  |
| `form:submit` | `form` | `form` | `formData`, `values`, `submitter` | `{ formData, values, submitter }`, cancelable |
| `checkbox:change` | `checkbox` | `checkbox` | `checked`, `value` | `{ checked, value }` (`value` is `checked`) |
| `radio-group:change` | `radio-group` | `radio-group` | `value` |  |
| `switch:change` | `switch` | `switch` | `checked`, `value` | `{ checked, value }` (`value` is `checked`) |
| `select:open` | `select` | `select` | none |  |
| `select:close` | `select` | `select` | none |  |
| `select:change` | `select` | `select` | `value` |  |
| `combobox:open` | `combobox` | `combobox` | none |  |
| `combobox:close` | `combobox` | `combobox` | none |  |
| `combobox:change` | `combobox` | `combobox` | `value` | `{ value }` (array for `multiple`) |
| `toggle:change` | `toggle` | `toggle` | `pressed`, `value` |  |
| `toggle-group:change` | `toggle-group` | `toggle-group` | `value` | `{ value }` (string, or array for `multiple`) |
| `dialog:open` | `dialog` | `root` | `trigger` |  |
| `dialog:close` | `dialog` | `root` | `reason` | `{ reason }`, cancelable. `reason`: `escape`, `outside`, `close`, `action`, `cancel`, `submit`, `swipe`, `api` |
| `alert-dialog:open` | `alert-dialog` | `root` | `trigger` |  |
| `alert-dialog:close` | `alert-dialog` | `root` | `reason` | `{ reason }`, cancelable. `reason`: `escape`, `outside`, `close`, `action`, `cancel`, `submit`, `swipe`, `api` |
| `sheet:open` | `sheet` | `root` | `trigger` |  |
| `sheet:close` | `sheet` | `root` | `reason` | `{ reason }`, cancelable. `reason`: `escape`, `outside`, `close`, `action`, `cancel`, `submit`, `swipe`, `api` |
| `drawer:open` | `drawer` | `root` | `trigger` |  |
| `drawer:close` | `drawer` | `root` | `reason` | `{ reason }`, cancelable. `reason`: `escape`, `outside`, `close`, `action`, `cancel`, `submit`, `swipe`, `api` |
| `drawer:release` | `drawer` | `drawer` | `delta` | `{ delta }` when a swipe springs back |
| `drawer:snap-point-change` | `drawer` | `drawer` | `snapPoint` | `{ snapPoint }` as Base UI `onSnapPointChange`: when a swipe settles (also on the same point), `null` before a swipe close (the old point again if the close is cancelled), and the default point when the drawer closes |
| `popover:open` | `popover` | `popover` | `trigger` |  |
| `popover:close` | `popover` | `popover` | `reason` |  |
| `tooltip:open` | `tooltip` | `root` | none |  |
| `tooltip:close` | `tooltip` | `root` | none |  |
| `hover-card:open` | `hover-card` | `root` | none |  |
| `hover-card:close` | `hover-card` | `root` | none |  |
| `dropdown-menu:open` | `dropdown-menu` | `root` | `trigger` |  |
| `dropdown-menu:close` | `dropdown-menu` | `root` | `reason` |  |
| `dropdown-menu:select` | `dropdown-menu` | `root` | `value`, `item`, `checked` | `{ value, item, checked }`, cancelable (keeps the menu open) |
| `dropdown-menu:change` | `dropdown-menu` | `root` | `value`, `checked`, `item`, `group` | `{ value, checked, item, group }` for checkbox and radio items |
| `context-menu:open` | `context-menu` | `root` | `trigger` |  |
| `context-menu:close` | `context-menu` | `root` | `reason` |  |
| `context-menu:select` | `context-menu` | `root` | `value`, `item`, `checked` | `{ value, item, checked }`, cancelable (keeps the menu open) |
| `context-menu:change` | `context-menu` | `root` | `value`, `checked`, `item`, `group` | `{ value, checked, item, group }` for checkbox and radio items |
| `menubar:open` | `menubar` | `root` | `trigger` |  |
| `menubar:close` | `menubar` | `root` | `reason` |  |
| `menubar:select` | `menubar` | `root` | `value`, `item`, `checked` | `{ value, item, checked }`, cancelable (keeps the menu open) |
| `menubar:change` | `menubar` | `root` | `value`, `checked`, `item`, `group` | `{ value, checked, item, group }` for checkbox and radio items |
| `navigation-menu:change` | `navigation-menu` | `navigation-menu` | `value` | `{ value }` of the open item, `""` when closed |
| `navigation-menu:select` | `navigation-menu` | `navigation-menu` | `link`, `href` |  |
| `command:select` | `command` | `command` | `value`, `item` |  |
| `toast:open` | `toast` | `toast` | `id` |  |
| `toast:close` | `toast` | `toast` | `id`, `reason` | `{ id, reason }`: `timeout`, `close`, `action`, `swipe`, `escape`, `dismiss` |
| `toast:action` | `toast` | `toast` | `id` |  |
| `avatar:change` | `avatar` | `avatar` | `value` | `{ value }`: `loaded` or `error` |
| `accordion:change` | `accordion` | `accordion` | `value` | `{ value }` (string, or array for `multiple`) |
| `collapsible:open` | `collapsible` | `collapsible` | none |  |
| `collapsible:close` | `collapsible` | `collapsible` | none |  |
| `tabs:change` | `tabs` | `tabs` | `value` |  |
| `resizable:change` | `resizable` | `resizable-panel-group` | `value` | `{ value }`: the panel sizes in percent |
| `sidebar:open` | `sidebar` | `sidebar` | `mobile` |  |
| `sidebar:close` | `sidebar` | `sidebar` | `mobile` |  |
| `carousel:change` | `carousel` | `carousel` | `value`, `count` | `{ value: index, count }` (snap index and snap count; also once at start and after a new measure that changes them) |
| `message-scroller:scrollable` | `message-scroller` | `message-scroller` | `start`, `end` |  |
| `trace:open` | `trace` | `trace-collapsible` | none |  |
| `trace:close` | `trace` | `trace-collapsible` | none |  |
| `questionnaire:change` | `questionnaire` | `questionnaire` | `value`, `index`, `total` | `{ value, index, total }` (active item name) |
| `questionnaire:status` | `questionnaire` | `questionnaire` | `item`, `value` | `{ item, value }`: `answered`, `skipped`, `unanswered` |
| `questionnaire:submit` | `questionnaire` | `questionnaire` | `value`, `status` | `{ value, status }`, before the native `submit` |
| `code-block:copy` | `code-block` | `code-block` | `value` |  |
| `code-block:wrap` | `code-block` | `code-block` | `value` |  |
| `calendar:change` | `calendar` | `calendar` | `value`, `mode`, `source` | `{ value, mode, source }`: `day`, `api`, `reset` |
| `calendar:navigate` | `calendar` | `calendar` | `value` |  |
| `date-picker:open` | `date-picker` | `date-picker` | none |  |
| `date-picker:close` | `date-picker` | `date-picker` | none |  |
| `chart:active` | `chart` | `chart element` | `index`, `key`, `row` | `{ index, key, row }`, or `null` when the tooltip closes |
| `chart:legend` | `chart` | `chart element` | `key`, `visible`, `hidden` |  |
| `chart:view` | `chart` | `chart element` | `view` | `{ view }`: `chart` or `table` |
