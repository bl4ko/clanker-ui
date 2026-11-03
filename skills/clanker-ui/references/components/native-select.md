# Native Select (`native-select`)

Group `forms`. Needs `core`. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `native-select` (root) | `data-size` `sm` |  |

Other parts: `native-select-icon`, `native-select-optgroup`, `native-select-option`, `native-select-wrapper`.

## Full text

### Native Select

```html
<div data-slot="native-select-wrapper">
  <select data-slot="native-select" data-size="sm">
    <option data-slot="native-select-option" value="todo">Todo</option>
  </select>
  <svg data-lucide="chevron-down" data-slot="native-select-icon"></svg>
</div>
```

CSS only.
