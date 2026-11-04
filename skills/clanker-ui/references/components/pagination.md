# Pagination (`pagination`)

Group `layout`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `pagination-link` | `data-active` boolean; `data-pagination-next` boolean; `data-pagination-previous` boolean; `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |

Other parts: `pagination` (root), `pagination-content`, `pagination-ellipsis`, `pagination-item`.

## Full text

### Pagination

```html
<nav data-slot="pagination" aria-label="pagination">
  <ul data-slot="pagination-content">
    <li data-slot="pagination-item"><a data-slot="pagination-link" data-pagination-previous data-size="default" href="?p=1" aria-label="Go to previous page"><svg data-lucide="chevron-left" data-icon="inline-start"></svg><span>Previous</span></a></li>
    <li data-slot="pagination-item"><a data-slot="pagination-link" href="?p=1">1</a></li>
    <li data-slot="pagination-item"><a data-slot="pagination-link" data-variant="outline" href="?p=2" data-active aria-current="page">2</a></li>
    <li data-slot="pagination-item"><span data-slot="pagination-ellipsis" aria-hidden="true"><svg data-lucide="ellipsis"></svg><span class="sr-only">More pages</span></span></li>
    <li data-slot="pagination-item"><a data-slot="pagination-link" data-pagination-next data-size="default" href="?p=3" aria-label="Go to next page"><span>Next</span><svg data-lucide="chevron-right" data-icon="inline-end"></svg></a></li>
  </ul>
</nav>
```

The markup is the shadcn DOM: a link is a `ghost` button of size `icon` (32 px); the current page is `data-variant="outline"` with `aria-current="page"`. `data-pagination-previous` and `data-pagination-next` with `data-size="default"` mark Previous and Next; their text hides below 640 px and their chevrons turn in RTL.

Disabled Previous or Next (first or last page): `aria-disabled="true"` on the link, and remove its `href` so it is not a Tab stop. The link is dimmed (opacity 0.5) and takes no pointer events, like a disabled button; the kit also cancels a click on it, so a link that keeps its `href` does not navigate.
