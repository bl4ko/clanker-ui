# Marker (`marker`)

Group `chat`. Needs `core`. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `marker` (root) | `data-variant` `border`, `separator` |  |

Other parts: `marker-content`, `marker-icon`.

```html
<div data-slot="marker" role="status">
  <span data-slot="marker-icon"><svg data-lucide="git-branch"></svg></span>
  <span data-slot="marker-content">Switched to a new branch</span>
</div>
<div data-slot="marker" data-variant="separator">
  <span data-slot="marker-content">Conversation compacted</span>
</div>
```

## Full text

### Message, Bubble, Marker

`message-group` stacks messages from one sender. Bubble variants: `default`, `secondary`, `muted`, `tinted`, `outline`, `ghost`, `destructive`; `bubble-group`; `bubble-reactions` (`data-side`, `data-align`). `<div data-slot="marker" data-variant="separator|border" role="status">` with `marker-icon` and `marker-content`. CSS only.
