# Form (`form`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `form-label` | `data-error` any |  |

Other parts: `form` (root), `form-description`, `form-item`, `form-message`.

Other options named in the docs: `data-error-type-mismatch` any; `data-error-value-missing` any.

Events: `form:invalid` `{ errors }`; `form:submit` `{ formData, values, submitter }` (cancelable).

## Full text

### Form

```html
<form data-slot="form">
  <div data-slot="field" role="group">
    <label data-slot="field-label" for="name">Name</label>
    <input id="name" data-slot="input" name="name" required data-error-value-missing="Name is required.">
  </div>
</form>
```

- Native constraint validation. The kit sets `novalidate` and shows its own errors: after the user changed a control and left it, and on submit, then live.
- An invalid control gets `aria-invalid="true"` and `aria-describedby` to a `field-error` (`role="alert"`), created if missing. The field gets `data-invalid="true"`. Legacy `form-item`, `form-label` (`data-error`), `form-description`, and `form-message` work the same way.
- Message: `data-error-<validity-flag>` (`data-error-value-missing`, `data-error-type-mismatch`, ...), then `data-error`, then the browser message, read from the control, the visible control, or the component root (`radio-group`, `select`, `combobox`, `input-otp`, `slider`).
- Checkbox, switch, and radio validate through their hidden native input; `aria-invalid` (and so `data-invalid`) goes on the button, and submit focuses the button.
- Submit with errors focuses the first invalid control and emits `form:invalid`. A valid submit emits cancelable `form:submit` (`values` has an array for repeated names). Form `reset` clears errors and resets all components.
