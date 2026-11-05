# Choose a component

Pick by the job, not by the look. Each row names the kit part; its file is `components/<name>.md`.

## Overlays

| Need | Use | Not |
| --- | --- | --- |
| A short task that blocks the page: a small form, a choice, a preview (up to about 6 fields) | `dialog` | a new page |
| Confirm an action that destroys data or costs money | `alert-dialog` (action `destructive`) | `dialog`, `confirm()` |
| A long form or details next to the list, while the list stays in view (edit a row, filters, a cart) | `sheet` (`data-side="right"`) | `dialog` |
| A task on a phone that starts from the bottom (actions, a picker, a short form) | `drawer` | `sheet` |
| Small content tied to a control, no blocking: a date picker, a color, a short form of 1 or 2 fields | `popover` | `dialog` |
| A list of actions for one object | `dropdown-menu` (right click: `context-menu`) | `popover` with buttons |
| A label for an icon button, or a short hint on hover and focus | `tooltip` | `hover-card` |
| A preview of a linked object on hover (a user, a page) | `hover-card` | `popover` |
| Search and run commands, jump to pages | `command` in a `dialog` (⌘K) | `combobox` |

## Choices

| Need | Use |
| --- | --- |
| 2 to 5 options, all visible, one at a time, in a form | `radio-group` (choice cards when each option needs a description) |
| 2 to 5 options that change a view at once (range, mode, layout) | `toggle-group` `data-type="single" data-required` (`outline`; one value always selected) |
| Turn one setting on or off, applies at once | `switch` |
| Agree, select, or several options that wait for submit | `checkbox` |
| 6 to about 15 options, one at a time | `select` (`native-select` on very simple or long system lists) |
| Many options, or the user types to find one (people, countries, tags) | `combobox` (`data-multiple` for several) |
| A date or a range | `date-picker` (a `calendar` in a `popover`) |
| A number in a range where the exact value does not matter (volume, size) | `slider`; else an `input type="number"` |
| A rating of 1 to 5 | input: star radios ([recipes.md](recipes.md)), not a `toggle-group`; read-only: `rating` |

## Messages

| Need | Use |
| --- | --- |
| The result of an action the user just did | `toast` (`toast.success`, `toast.error`, Undo action) |
| A state of the page that stays until something changes | `alert` (`info`, `warning`, `destructive`) |
| One field is wrong | `field-error` (the kit form shows it) |
| There is no data, or no match | `empty` |
| Content is loading | `skeleton` in the shape of the content; `spinner` in a button |
| A count or a state on an item | `badge` (status: with an icon) |

## Structure

| Need | Use |
| --- | --- |
| A group of content with a title and its own actions, next to other groups | `card` |
| The main content of the page, alone | no card: put it in `page` with a `page-header` |
| Key numbers | `section-cards` (with a trend and a note each), or `stat-grid` (many small numbers, facts on a detail page) |
| Views of the same object (Overview, Activity, Settings of one project) | `tabs` |
| A filter of one list (All, Active, Archived) | `tabs` with one shared `tabs-content` without `data-value`, or `toggle-group` `data-type="single" data-required` |
| Different areas of the app | separate pages in the sidebar or the top nav |
| Steps of a long form | one page with `field-set` sections; a wizard only when a step needs the answer of the one before |
| Show and hide extra content in place | `collapsible`; many sections: `accordion` |
| Where am I | sidebar app: `breadcrumb` in the `site-header`; top-header app: `breadcrumb` or back link above the `page-header` |
| Pages of a table | `data-table-pagination` |
| Pages of content with their own URLs (results, articles, a gallery) | `pagination` |

## Chat and agents

| Need | Use |
| --- | --- |
| A chat page, agent steps, sources, or code output | the patterns in [ai-elements.md](ai-elements.md): `message`, `bubble`, `trace`, `message-scroller`, `input-group` |
| A step the agent took (a command, a search, thinking) | a `trace-line` in a `trace`, not a `card` or an `alert` |
| A question that the agent asks the person | `questionnaire`; approve or deny one action: an `item` with two buttons |

## Data

| Need | Use |
| --- | --- |
| Many records with the same fields, to compare, sort, or select | `table` in the `data-table` frame |
| Few records, or records with different content (people, events, notifications) | `item-group` with `item` |
| Records with an image or a large preview | `card-grid` of `card`, each with an image or a `cover` (block `card-grid`; `section-cards` only for 2, 3, 4, or 8 key numbers) |
| Values over time or by category | `chart()`; one number with its trend: `section-cards` or `statTile()` |
| Many small marks with their own hover (90-day uptime bars) | one shared readout placed with `position()` and one Tab stop with arrow keys ([recipes.md](recipes.md)), not one tooltip per mark |
| Status of a row in a table | `badge` with icon and word; icon and word in `data-table-text` only in tables of 6 or more columns |
