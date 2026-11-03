# Avatar (`avatar`)

Group `layout`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `avatar` (root) | `data-size` `lg`, `sm` |  |

Other parts: `avatar-badge`, `avatar-fallback`, `avatar-group`, `avatar-group-count`, `avatar-image`.

Other options named in the docs: `data-status` `error`, `loaded`, `loading`.

Events: `avatar:change` `{ value }`.

## Full text

### Avatar

```html
<span data-slot="avatar" data-size="sm|lg">
  <img data-slot="avatar-image" src="..." alt="">
  <span data-slot="avatar-fallback">CN</span>
  <span data-slot="avatar-badge"></span>
</span>
```

The fallback shows until the image loads and stays when it fails (`data-status="loading|loaded|error"` on the image). Base UI renders only one of them; the kit hides the other with `visibility: hidden`. Put the image before the fallback, as shadcn does. `avatar-group` stacks avatars; `avatar-group-count` shows the rest.
