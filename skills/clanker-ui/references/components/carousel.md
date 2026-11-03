# Carousel (`carousel`)

Group `layout`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `carousel` (root) | `data-orientation` `horizontal`, `vertical` |  |
| `carousel-next` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `carousel-previous` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |

Other parts: `carousel-content`, `carousel-item`.

Events: `carousel:change` `{ value, count }`.

## Full text

### Carousel

```html
<div data-slot="carousel" data-orientation="horizontal|vertical" data-align="start|center|end" data-loop aria-label="Featured">
  <div data-slot="carousel-content"><div>
    <div data-slot="carousel-item">...</div>
  </div></div>
  <button data-slot="carousel-previous"></button>
  <button data-slot="carousel-next"></button>
</div>
```

The inner `div` is the track; set item width with `flex-basis`. The kit adds the carousel and slide roles, slide labels, the arrow icons, and disables a button at the end (`disabled`, `data-disabled`). Like shadcn, focus does not move when the focused button becomes disabled, so Tab continues to the other button. The motion is a port of Embla 8, the engine of the shadcn carousel, with its default options: the track moves with `transform`, `data-align` sets the slide alignment (default `center`, like Embla; the shadcn size and orientation examples use `start`), and `data-loop` loops the slides (as Embla, only when there are enough slides to fill the view). The buttons and the arrow keys (RTL aware) move one slide with duration 25 and friction 0.68 (about 750 ms; at once with reduced motion); a press during the motion changes its target. A mouse drag or a touch swipe moves the track with the pointer. On release, the speed is multiplied by 300 for the mouse or 400 for touch; a release force over 20 % of the view (limited to 50 to 225 px) goes to the next or previous slide, and a smaller force snaps to the nearest slide. Past the first or last slide the track resists and springs back (at once with reduced motion). A drag over 10 px cancels the click that follows. A touch swipe that starts more vertical than horizontal is left to the page. Tab into a slide jumps to it at once. The carousel measures again, as Embla `reInit` does, when its size or its slides change, when `data-orientation`, `data-align`, or `data-loop` changes, and when a `dir` change gives it another direction; it keeps the selected snap. The kit sets `transform` inline on the track and on looped slides, so app CSS `transform` on these parts has no effect. `carousel:change` (`value`: the selected snap index, `count`: the number of snaps, which is less than the slides when several slides fit in the view) fires once after the carousel starts (like the Embla `init` event), when the selected snap changes, and after a new measure that changes the index or the count. Like the shadcn carousel, the mouse wheel does not move the slides (no wheel plugin). Not built: autoplay and other plugins.
