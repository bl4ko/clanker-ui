# Field (`field`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `field` (root) | `data-disabled` `false`, `true`; `data-invalid` `false`, `true`; `data-orientation` `horizontal`, `responsive`, `vertical` |  |
| `field-group` |  | `data-columns` |
| `field-legend` | `data-variant` `label`, `legend` |  |
| `field-separator` | `data-content` any |  |

Other parts: `field-content`, `field-description`, `field-error`, `field-label`, `field-label-row`, `field-separator-content`, `field-set`.

Other options named in the docs: `data-columns` `2`, `3`; `data-span` number.

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
    <div data-slot="field" role="group" data-orientation="horizontal">
      <div data-slot="field-content">
        <label data-slot="field-label" for="save-card">Save card</label>
        <p data-slot="field-description">Use this card for later payments.</p>
      </div>
      <button type="button" data-slot="switch" id="save-card"></button>
    </div>
    <div data-slot="field-separator"><span data-slot="field-separator-content">Or pay with</span></div>
    <div data-slot="radio-group" data-name="method">
      <label data-slot="field-label" for="method-bank">
        <span data-slot="field" role="group" data-orientation="horizontal">
          <span data-slot="field-content">
            <span data-slot="field-label">Bank transfer</span>
            <span data-slot="field-description">Pay within 14 days.</span>
          </span>
          <button type="button" data-slot="radio-group-item" id="method-bank" value="bank"></button>
        </span>
      </label>
    </div>
  </div>
</fieldset>
```

## Full text

### Field

`field-set` (a `fieldset`), `field-legend` (`data-variant="legend|label"`; the kit sets `legend` when it is missing, as shadcn renders it), `field-group`, `field` (`data-orientation="vertical|horizontal|responsive"`, `data-invalid="true"`, `data-disabled="true"`), `field-content`, `field-label`, `field-description`, `field-separator` (optional `field-separator-content` child; the kit adds the `separator` line and `data-content`, as shadcn renders them), `field-error`. A `field-label` that wraps a `field` (with `field-content` and a radio, checkbox, or switch) is a choice card. A row with a switch or checkbox next to its label is a `field` with `data-orientation="horizontal"`. `responsive` switches to a row when the closest `field-group` is at least 28rem wide. `data-slot="checkbox-group"` gives the tight checkbox list spacing.

Kit extensions: `field-label-row` holds a `field-label` and a link that goes to the end ("Forgot your password?"). `data-columns="2|3"` on a `field-group` puts its fields in 2 or 3 columns when the group is at least 28rem wide; the fields align at the top, so an error message under one field does not move the others. `data-span="2"` on a field in a 3-column group takes two columns.
