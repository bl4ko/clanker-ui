# Cover (`cover`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `cover` (root) | `data-ratio` string; `data-tone` number |  |

## Full text

### Cover

```html
<div data-slot="cover" data-tone="4" data-ratio="square">
  <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><circle cx="80" cy="20" r="30" fill="currentColor" opacity="0.4"></circle></svg>
  <span>Field notes</span>
  <span>Volume 2</span>
</div>
```

- Placeholder art made from tokens, for a record without an image: a 2 / 3 box (`data-ratio="square"` 1 / 1, `video` 16 / 9) with the kit radius and a tint of `--chart-N` (`data-tone="1"` to `"5"`, default 1) on the card. An `svg` child fills the box behind the text in the tone color (draw with `currentColor`). The first text child is the title (16 px, weight 600), the others are 12 px; text wraps and is never cut.
