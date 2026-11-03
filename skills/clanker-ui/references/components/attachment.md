# Attachment (`attachment`)

Group `chat`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `attachment` (root) | `data-orientation` `horizontal`, `vertical`; `data-size` `default`, `sm`, `xs`; `data-state` string |  |
| `attachment-action` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `attachment-media` | `data-variant` `image` |  |

Other parts: `attachment-actions`, `attachment-content`, `attachment-description`, `attachment-group`, `attachment-title`, `attachment-trigger`.

## Full text

### Attachment

```html
<div data-slot="attachment" data-state="uploading" data-size="sm" data-orientation="vertical">
  <div data-slot="attachment-media" data-variant="image"><img src="a.png" alt="A"></div>
  <div data-slot="attachment-content">
    <span data-slot="attachment-title">a.png</span>
    <span data-slot="attachment-description">PNG · 820 KB</span>
  </div>
  <div data-slot="attachment-actions"><button data-slot="attachment-action" aria-label="Remove a.png"><svg data-lucide="x"></svg></button></div>
  <a data-slot="attachment-trigger" href="a.png" aria-label="Open a.png"></a>
</div>
```

States: `idle`, `uploading`, `processing`, `error`, `done`. Sizes: `default`, `sm`, `xs`. `attachment-group` is a scrolling, snapping row. `attachment-trigger` shows the standard focus ring.
