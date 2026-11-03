# Command (`command`)

Group `overlays`. Needs `core`, `forms`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `command-group` | `data-heading` any |  |
| `command-item` | `data-disabled` any; `data-keywords` string; `data-value` any | `data-selected` |

Other parts: `command` (root), `command-empty`, `command-input`, `command-list`, `command-separator`, `command-shortcut`.

Kit adds: `command-group-heading`, `command-input-wrapper`.

Other options named in the docs: `data-should-filter` `false`, `true`.

Events: `command:select` `{ value, item }`.

```html
<div data-slot="command">
  <input data-slot="command-input" placeholder="Type a command or search...">
  <div data-slot="command-list">
    <div data-slot="command-empty">No results found.</div>
    <div data-slot="command-group" data-heading="Suggestions">
      <div data-slot="command-item"><svg data-lucide="calendar"></svg><span>Calendar</span></div>
      <div data-slot="command-item" data-keywords="emoji, smiley"><svg data-lucide="smile"></svg><span>Search Emoji</span></div>
      <div data-slot="command-item" data-disabled><svg data-lucide="calculator"></svg><span>Calculator</span></div>
    </div>
    <div data-slot="command-separator"></div>
    <div data-slot="command-group" data-heading="Settings">
      <div data-slot="command-item" data-value="profile"><svg data-lucide="user"></svg><span>Profile</span><span data-slot="command-shortcut">⌘P</span></div>
    </div>
  </div>
</div>
```

## Full text

### Command

`command` > `command-input`, `command-list` > `command-empty`, `command-group` (`data-heading` or a `command-group-heading` child) > `command-item` (`data-value`, `data-keywords="a, b"`, `data-disabled`) with `command-shortcut`; `command-separator`. Typing filters, scores, and sorts; ArrowUp/Down, Home, End, Ctrl+N/J/P/K, Alt+arrows (next group), Meta+arrows (first/last), Enter. `data-loop` wraps, `data-should-filter="false"` disables filtering. The kit builds the shadcn input DOM (`command-input-wrapper` > `input-group` > the input + `input-group-addon` with the search icon), gives group headings the cmdk `cmdk-group-heading` attribute, and appends the shadcn `check` icon to each item (shown with `data-checked="true"`, hidden when the item has a shortcut). Inside a `dialog-content` it becomes the command dialog: the content gets `data-command-dialog` and no close button unless `data-show-close-button="true"`. The list has `tabindex="-1"`, so a pointer press on an item moves focus to the list (as in cmdk) and the keys keep working there; the input and the list carry `aria-activedescendant` of the selected item. Items inserted later get `role="option"`, an id, and their disabled state; the empty state and the selection follow. `data-disabled` in any form except `"false"` disables an item.
