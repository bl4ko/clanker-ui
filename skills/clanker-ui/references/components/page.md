# Page (`page`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `page` (root) | `data-size` `lg`, `md`, `sm` | `data-layout` |

Other parts: `page-actions`, `page-aside`, `page-body`, `page-description`, `page-header`, `page-nav`, `page-title`.

Other options named in the docs: `data-layout` string.

## Full text

### Page

```html
<main data-slot="page" data-size="sm">
  <div data-slot="page-header">
    <h1 data-slot="page-title">Projects</h1>
    <p data-slot="page-description">All projects of your team.</p>
    <div data-slot="page-actions">
      <button type="button" data-slot="button" data-variant="outline">Export</button>
      <button type="button" data-slot="button">New project</button>
    </div>
  </div>
  <div data-slot="page-body">
    <aside data-slot="page-aside">
      <nav data-slot="page-nav" aria-label="Settings">
        <a data-slot="button" data-variant="ghost" href="#profile" aria-current="page">Profile</a>
        <a data-slot="button" data-variant="ghost" href="#account">Account</a>
      </nav>
    </aside>
    <div>Content</div>
  </div>
</main>
```

- `data-layout="center"` on `page` is the sign-in layout of shadcn `login-03`: a muted full-height page with its children centered at most 24rem wide. In it, card headers are centered, the card title is 20 px, a `field-description` child of the page is centered, and so is one in the field of the submit button.
- `page` is the content column: gutters of 1rem (1.5rem from 64rem), a 1rem gap between its children (1.5rem from 48rem), and `container: page`. Put it in `sidebar-inset` or `<body>`. `data-size="sm|md|lg"` limits the content to 42rem, 56rem, or 72rem and centers it; no size fills the width (dashboards, tables).
- `page-header` is a grid: `page-title` (24 px, weight 600) and `page-description` (muted) on the start side, `page-actions` (a row of buttons, `gap` 0.5rem) on the end side. Below 32rem of header width, the actions move under the text.
- `page-body` puts its children in one column. With a `page-aside` first, it is a 12rem navigation column (sticky below a header of `--header-height`, default 3.5rem) and a content column of at most 42rem from 64rem; with a `page-aside` last, a 20rem side column. Each child is a flex column with a 1.5rem gap.
- `page-nav` holds ghost buttons (`aria-current="page"` on the current one gets the muted background). It is a row that scrolls below 64rem and a column from 64rem.
