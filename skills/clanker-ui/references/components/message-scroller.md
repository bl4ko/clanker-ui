# Message Scroller (`message-scroller`)

Group `chat`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `message-scroller` (root) | `data-auto-scroll` boolean; `data-default-scroll-position` `end`, `last-anchor`, `start` |  |
| `message-scroller-button` | `data-direction` string; `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `destructive`, `ghost`, `link`, `outline`, `secondary` | `data-active` |
| `message-scroller-item` | `data-message-id` string; `data-scroll-anchor` `false`, `true` |  |
| `message-scroller-viewport` |  | `data-autoscrolling`, `data-pending-scroll` |

Other parts: `message-scroller-content`.

Part attributes: `data-message-scroller-spacer` boolean.

Other options named in the docs: `data-active` `false`, `true`; `data-scroll-edge-threshold` any; `data-scroll-margin` any; `data-scroll-previous-item-peek` any.

Events: `message-scroller:scrollable` `{ start, end }`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-chat.min.js`):

- `messageScrollerScrollToEnd(el, { behavior }?) → boolean`
- `messageScrollerScrollToStart(el, { behavior }?) → boolean`
- `messageScrollerScrollToMessage(el, id, { align, behavior, scrollMargin }?) → boolean`: Waits for the row if the list is still empty.
- `messageScrollerScrollable(el) → { start, end }`
- `messageScrollerVisibility(el) → { currentAnchorId, visibleMessageIds }`

## Full text

### Message Scroller

```html
<div data-slot="message-scroller" data-auto-scroll data-default-scroll-position="end|start|last-anchor">
  <div data-slot="message-scroller-viewport">
    <div data-slot="message-scroller-content">
      <div data-slot="message-scroller-item" data-message-id="u1" data-scroll-anchor="true">…</div>
    </div>
  </div>
  <button data-slot="message-scroller-button" data-direction="end"></button>
</div>
```

Give the root a height. Options: `data-auto-scroll`, `data-default-scroll-position`, `data-scroll-edge-threshold` (8), `data-scroll-margin` (0), `data-scroll-previous-item-peek` (64). A new anchor row moves near the top; rows added above keep the visible row in place. Only upward intent releases following: wheel up, a touch drag down, and ArrowUp, PageUp, Home, or Shift+Space on the viewport itself (keys in an input inside the log never release it); downward input keeps following. The button is `inert` with `data-active="false"` when there is nothing to scroll to; it defaults to `data-direction="end" data-variant="secondary" data-size="icon-sm"`. Rows default to `data-scroll-anchor="false"`. With the opening position `end` or `last-anchor`, the root and the viewport have `data-pending-scroll` (the viewport is invisible) until the position is set; put the attribute in the HTML to hide the first paint before the kit runs. The content ends with a hidden `<div aria-hidden="true" data-message-scroller-spacer>` that holds an anchored row at the top; the kit keeps it last when rows are added. App code counts and removes rows with `:scope > [data-slot="message-scroller-item"]`, never with the content's `children` or `lastElementChild`. The exported scroller functions return `false` or defaults for a scroller that is not in the document; set-up runs when it is inserted.
