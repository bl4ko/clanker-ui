# Accordion (`accordion`)

Group `layout`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `accordion` (root) | `data-type` `multiple`, `single` |  |
| `accordion-content` |  | `data-closed`, `data-open`, `data-state` |
| `accordion-item` | `data-state` string; `data-value` string |  |

Other parts: `accordion-trigger`.

Kit adds: `accordion-trigger-icon`.

Events: `accordion:change` `{ value }`.

## Full text

### Accordion

```html
<div data-slot="accordion" data-type="single|multiple">
  <div data-slot="accordion-item" data-value="shipping" data-state="open">
    <h3><button type="button" data-slot="accordion-trigger">What are your shipping options?</button></h3>
    <div data-slot="accordion-content"><div>Standard, express, and overnight.</div></div>
  </div>
  <div data-slot="accordion-item" data-value="returns">
    <h3><button type="button" data-slot="accordion-trigger">What is your return policy?</button></h3>
    <div data-slot="accordion-content" hidden="until-found"><div>Returns within 30 days.</div></div>
  </div>
</div>
```

The Base UI DOM: a heading with the trigger button, and a panel with one inner `div` (the padding is on it). `data-type="single|multiple"`, `data-state="open"` on an item that starts open, `hidden="until-found"` on the panel of an item that starts closed (so the page does not move when the module loads), `data-disabled` on an item. Like Base UI, a single accordion can close its open item, so all items can be closed. The kit adds the two chevrons (`accordion-trigger-icon`, down when closed, up when open), ids, `aria-expanded`, `aria-controls`, `role="region"`, `aria-labelledby`, `data-open`, `data-closed`, `data-state`, `data-panel-open` on the trigger, and `data-index`. A closed panel has `hidden="until-found"`, so find in page opens its item (`beforematch`). The panel animates with `--accordion-panel-height` (`auto` after the open animation). Keys: Enter and Space toggle; as in Base UI, the arrow keys do not move focus. Like Base UI, the trigger of a disabled item stays in the Tab order (`aria-disabled="true"`), and Enter, Space, or a click does not open it. Event: `accordion:change` `{ value }`.

A count or status in a trigger: a `badge` after the text (`<button type="button" data-slot="accordion-trigger">Payments<span data-slot="badge" data-variant="warning"><svg data-lucide="triangle-alert"></svg>Degraded</span></button>`) sits at the end, before the chevron, centered on the text.
