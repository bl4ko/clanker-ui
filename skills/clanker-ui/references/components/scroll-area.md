# Scroll Area (`scroll-area`)

Group `layout`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `scroll-area-scrollbar` | `data-orientation` `horizontal`, `vertical` | `data-overflow` |

Other parts: `scroll-area` (root), `scroll-area-viewport`.

Kit adds: `scroll-area-thumb`.

## Full text

### Scroll Area

```html
<div data-slot="scroll-area">
  <div data-slot="scroll-area-viewport" aria-label="Tags">...</div>
  <div data-slot="scroll-area-scrollbar" data-orientation="horizontal"></div>
</div>
```

The viewport is the real scroll container; the kit makes it focusable, hides the native scrollbars, and adds a vertical scrollbar with a draggable thumb. Like Base UI, a scrollbar shows while its content overflows and is hidden without overflow; it has `data-orientation` (also on the thumb), `data-hovering` while the pointer is over the scroll area, and `data-scrolling` while its own axis scrolls or its thumb is dragged. A click on the track centers the thumb at the pointer with the Base UI formula (it subtracts the scrollbar padding); a press on the scrollbar does not keep focus in the viewport.
