# Slider (`slider`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `slider` (root) | `data-large-step` number; `data-orientation` `horizontal`, `vertical` |  |
| `slider-range` (kit adds) |  | `data-orientation` |
| `slider-thumb` (kit adds) |  | `data-index` |
| `slider-track` (kit adds) |  | `data-orientation` |

## Full text

### Slider

```html
<div data-slot="slider" data-orientation="horizontal|vertical" data-large-step="10">
  <input type="range" min="0" max="100" step="5" value="25" name="min" aria-label="Minimum">
  <input type="range" min="0" max="100" step="5" value="75" name="max" aria-label="Maximum">
</div>
```

- One native range per thumb. The kit builds the Base UI DOM: `role="group"` on the root, a control `div`, `slider-track` with `slider-range`, and one `div` `slider-thumb` (`data-index`) around each range input. The input is visually hidden and keeps focus, form value, and `aria-valuenow`; two thumbs get `aria-valuetext` (`25 start range`, `75 end range`).
- Thumbs are inset to the control edges (Base UI `thumbAlignment="edge"`). Every part has `data-orientation`, `data-disabled` (all inputs disabled), and `data-dragging` while a pointer drags. The active thumb gets `z-index`.
- A press on the control moves the closest thumb (on a tie the last one) and drags it; a dragged thumb pushes the others. Keys: arrows (RTL aware), Shift+arrow and Page Up/Down by `data-large-step` (default 10, in value units), Home, End. Keys stop at the next thumb.
- Events: native `input` while the value changes, `change` on key press and on pointer release.
- Code changes: after `input.value = 80`, dispatch an `input` or `change` event; the kit then updates the thumb and `aria-valuenow`. `disabled`, `min`, `max`, and `step` changes on the inputs apply at once.
