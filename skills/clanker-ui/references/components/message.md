# Message (`message`)

Group `chat`. Needs `core`. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `message` (root) | `data-align` `end` |  |

Other parts: `message-avatar`, `message-content`, `message-footer`, `message-group`, `message-header`.

## Full text

### Message, Bubble, Marker

```html
<div data-slot="message" data-align="end">
  <div data-slot="message-avatar"><span data-slot="avatar"><img data-slot="avatar-image" src="me.png" alt="@me"><span data-slot="avatar-fallback">ME</span></span></div>
  <div data-slot="message-content">
    <div data-slot="message-header">Olivia</div>
    <div data-slot="bubble" data-variant="muted"><div data-slot="bubble-content">Deploying to prod.</div></div>
    <div data-slot="message-footer">Delivered</div>
  </div>
</div>
```

`message-group` stacks messages from one sender. Bubble variants: `default`, `secondary`, `muted`, `tinted`, `outline`, `ghost`, `destructive`; `bubble-group`; `bubble-reactions` (`data-side`, `data-align`). `<div data-slot="marker" data-variant="separator|border" role="status">` with `marker-icon` and `marker-content`. CSS only.
