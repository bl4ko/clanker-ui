# Code Block (`code-block`)

Group `chat`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `code-block` (root) | `data-size` `sm`; `data-variant` `default`, `destructive` |  |
| `code-block-content` | `data-numbered` `false`, `true`; `data-start-line` number; `data-wrap` `false`, `true` |  |
| `code-block-copy-button` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `code-block-line` | `data-variant` `added`, `highlighted`, `removed` |  |

Other parts: `code-block-actions`, `code-block-code`, `code-block-footer`, `code-block-header`, `code-block-title`, `code-block-wrap-button`.

Kit adds: `code-block-line-content`.

Other options named in the docs: `data-timeout` any.

Events: `code-block:copy` `{ value }`; `code-block:wrap` `{ value }`.

## Full text

### Code Block

```html
<div data-slot="code-block" data-size="sm" data-variant="destructive">
  <div data-slot="code-block-header">
    <div data-slot="code-block-title"><svg data-lucide="file-text"></svg>app.ts</div>
    <div data-slot="code-block-actions">
      <button data-slot="code-block-wrap-button" aria-label="Wrap lines"><svg data-lucide="text-wrap"></svg></button>
      <button data-slot="code-block-copy-button"></button>
    </div>
  </div>
  <pre data-slot="code-block-content" data-numbered="true" data-start-line="14" data-wrap="true"><code data-slot="code-block-code">code</code></pre>
</div>
```

Plain monospace, no highlighter. `data-numbered` splits text into `code-block-line` rows; write `<span data-slot="code-block-line" data-variant="added|removed|highlighted">` rows for diffs. Copy uses the Clipboard API: `data-value` or the block text without line numbers; it shows a check for 2 s (`data-timeout`) and announces "Copied" (`strings.copied`). A copy button that leaves the page goes back to its copy state. The wrap button toggles `data-wrap` and `aria-pressed`.
