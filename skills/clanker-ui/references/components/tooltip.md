# Tooltip (`tooltip`)

Group `overlays`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `tooltip-arrow` (kit adds) |  | `data-side` |
| `tooltip-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `tooltip-provider` | `data-delay-duration` any; `data-skip-delay-duration` any |  |

Other parts: `tooltip` (root).

Part attributes: `data-tooltip-trigger` boolean.

Other options named in the docs: `data-close-delay` any; `data-delay` any; `data-timeout` any.

Events: `tooltip:open`; `tooltip:close`.

```html
<div data-slot="tooltip">
  <button type="button" data-slot="button" data-variant="outline" data-size="icon-sm" data-tooltip-trigger aria-label="Save"><svg data-lucide="save"></svg></button>
  <div data-slot="tooltip-content" data-side="top">Save changes <kbd data-slot="kbd">S</kbd></div>
</div>
```

## Full text

### Tooltip and Hover Card

`tooltip` > trigger (`tooltip-trigger` or `data-tooltip-trigger`) + `tooltip-content`. Timing is the shadcn setup (a `TooltipProvider` with `delay` 0 at the app root): `data-delay` (open, default 0), `data-close-delay` (default 0), and `data-timeout` (default 400) on the trigger, the root, or a `tooltip-provider` (`data-delay-duration` and `data-skip-delay-duration` also work). When a tooltip is open, or closed less than `data-timeout` ago, the next one opens at once. It opens on keyboard focus too; it closes on leave, Escape, press, and blur. Like Base UI, it stays open when the page scrolls and follows the trigger. A grace area lets the pointer move into the content. Touch never opens it. Default side `top`, 4 px; the kit adds the arrow (`<div data-slot="tooltip-arrow">`), which points at the trigger center. Like Base UI, the content and the arrow get `data-instant`: `delay` (opened at once because another tooltip was open or closed less than `data-timeout` ago), `focus` (opened by keyboard focus), `dismiss` (closed by Escape or a press).

Many small marks with their own readout (a bar per day in an uptime row): one tooltip per mark is too heavy. Use one `popover="manual"` readout placed with the core `position()` ([Popover](popover.md) has the code). For the keyboard, make the row one Tab stop (`tabindex="0"`, `role="group"`, an `aria-label` with the summary): Left and Right move a current mark, place the readout on it, and write the same text into a visually hidden `role="status"` element; Escape hides it.
