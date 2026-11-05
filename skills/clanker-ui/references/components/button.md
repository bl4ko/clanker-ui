# Button (`button`)

Group `core`. Needs none. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `button` (root) | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |

## Full text

### Button

```html
<button type="button" data-slot="button" data-variant="outline" data-size="sm"><svg data-lucide="send"></svg>Send</button>
<a data-slot="button" data-variant="link" href="/docs">Docs</a>
```

Variants: `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`. Sizes: `default`, `xs`, `sm`, `lg`, `icon`, `icon-xs`, `icon-sm`, `icon-lg`. A `<button>` without a `tabindex` gets `tabindex="0"` like the Base UI button, so Tab reaches it also in Safari. The same applies to the kit trigger and close buttons that are not `data-slot="button"`: dialog, alert dialog, sheet, drawer, popover, and menu triggers, accordion, collapsible, tooltip, and hover card triggers, the carousel buttons, the dialog, sheet, and drawer close buttons, and the toast close and action buttons.

Parts that shadcn renders with `Button` keep their own `data-slot` and share the button rules, with these defaults when `data-variant` and `data-size` are missing:

| Part | Default |
| --- | --- |
| `pagination-link` | `ghost`, `icon`; the current page has `data-variant="outline"` |
| `carousel-previous`, `carousel-next` | `outline`, `icon-sm`, round 28 px |
| `sidebar-trigger` | `ghost`, 28 px |
| `attachment-action`, `code-block-copy-button`, `code-block-wrap-button`, `code-block-download-button` | `ghost`, `icon-xs` |
| `message-scroller-button` | `secondary`, `icon-sm` |
| `questionnaire-previous`, `questionnaire-skip` | `outline` |
| `questionnaire-next`, `questionnaire-submit` | `default` |
| `calendar-button-previous`, `calendar-button-next` | `ghost`, `--cell-size` |
