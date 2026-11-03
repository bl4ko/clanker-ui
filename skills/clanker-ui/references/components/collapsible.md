# Collapsible (`collapsible`)

Group `layout`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `collapsible` (root) | `data-state` string |  |

Other parts: `collapsible-content`, `collapsible-trigger`.

Part attributes: `data-collapsible-trigger` boolean.

Events: `collapsible:open`; `collapsible:close`.

## Full text

### Collapsible

```html
<details data-slot="collapsible">
  <summary data-slot="collapsible-trigger">Advanced settings</summary>
  <div data-slot="collapsible-content">...</div>
</details>

<div data-slot="collapsible" data-state="closed">
  <button type="button" data-slot="button" data-variant="ghost" data-size="icon-sm" data-collapsible-trigger>...</button>
  <div>Always visible</div>
  <div data-slot="collapsible-content" hidden>...</div>
</div>
```

Use `<details>` when the trigger comes first; use a `<div>` root when content around the trigger must stay visible. A trigger with a button look is `data-slot="button"` with `data-collapsible-trigger`. `data-disabled` on the root. Like shadcn, the content shows and hides at once (no motion).
