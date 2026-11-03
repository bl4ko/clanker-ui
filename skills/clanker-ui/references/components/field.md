# Field (`field`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `field` (root) | `data-disabled` `false`, `true`; `data-invalid` `false`, `true`; `data-orientation` `horizontal`, `responsive`, `vertical` |  |
| `field-legend` | `data-variant` `label`, `legend` |  |

Other parts: `field-content`, `field-description`, `field-error`, `field-group`, `field-label`, `field-separator`, `field-separator-content`, `field-set`.

```html
<fieldset data-slot="field-set">
  <legend data-slot="field-legend">Payment Method</legend>
  <p data-slot="field-description">All transactions are secure and encrypted.</p>
  <div data-slot="field-group">
    <div data-slot="field" role="group">
      <label data-slot="field-label" for="card-name">Name on Card</label>
      <input id="card-name" data-slot="input" placeholder="Evil Rabbit" required>
      <p data-slot="field-description">As printed on the card.</p>
      <div data-slot="field-error"></div>
    </div>
    <div data-slot="field-separator"></div>
    <div data-slot="field" role="group" data-orientation="horizontal">
      <button type="button" data-slot="checkbox" id="same-address" data-checked></button>
      <div data-slot="field-content">
        <label data-slot="field-label" for="same-address">Same as shipping address</label>
      </div>
    </div>
  </div>
</fieldset>
```

## Full text

### Field

`field-set` (a `fieldset`), `field-legend` (`data-variant="legend|label"`; the kit sets `legend` when it is missing, as shadcn renders it), `field-group`, `field` (`data-orientation="vertical|horizontal|responsive"`, `data-invalid="true"`, `data-disabled="true"`), `field-content`, `field-label`, `field-description`, `field-separator` (optional `field-separator-content` child), `field-error`. A `field-label` that wraps a `field` is a choice card. `responsive` switches to a row when the closest `field-group` is at least 28rem wide. `data-slot="checkbox-group"` gives the tight checkbox list spacing.
