# Form (`form`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `form-label` | `data-error` any |  |

Other parts: `form` (root), `form-description`, `form-item`, `form-message`.

Other options named in the docs: `data-error-bad-input` any; `data-error-custom-error` any; `data-error-pattern-mismatch` any; `data-error-range-overflow` any; `data-error-range-underflow` any; `data-error-step-mismatch` any; `data-error-too-long` any; `data-error-too-short` any; `data-error-type-mismatch` any; `data-error-value-missing` any; `data-name` any.

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

- Native constraint validation. The kit sets `novalidate` and shows its own errors: after the user changed a control and left it, and on submit, then live. After a submit, leaving a control does not validate it, as in React Hook Form (`reValidateMode: "onChange"`): a control that the app clears after a send shows no error on blur.
- An invalid control gets `aria-invalid="true"` and `aria-describedby` to a `field-error` (`role="alert"`), created if missing. The field gets `data-invalid="true"`. Legacy `form-item`, `form-label` (`data-error`), `form-description`, and `form-message` work the same way.
- Message: `data-error-<validity-flag>`, then `data-error`, then the browser message (`validationMessage`), read from the control, the visible control, or the component root (`radio-group`, `select`, `combobox`, `toggle-group`, `date-picker`, `input-otp`, `slider`). The flags, in the order the kit checks them: `data-error-value-missing`, `data-error-type-mismatch`, `data-error-pattern-mismatch`, `data-error-too-long`, `data-error-too-short`, `data-error-range-underflow`, `data-error-range-overflow`, `data-error-step-mismatch`, `data-error-bad-input`, `data-error-custom-error` (for `setCustomValidity()`). Several custom rules on one field: leave out `data-error-custom-error` and `data-error`, and pass each message to `setCustomValidity(message)` in the control's own `input` or `change` listener; the kit shows it.
- Checkbox, switch, and radio validate through their hidden native input; `aria-invalid` (and so `data-invalid`) goes on the button, and submit focuses the button.
- Submit with errors focuses the first invalid control and emits `form:invalid`; the browser does not submit. A valid submit emits cancelable `form:submit` (`values` has an array for repeated names). If no listener calls `event.preventDefault()`, the browser submits the form natively (to `action`, or to the page URL with `method="get"` when there is no `action`), so the page navigates. A static page or an app that sends with `fetch` must call `preventDefault()` in its `form:submit` listener.
- Form `reset` clears errors and resets all components to their authored values after the reset event. A value that the app sets right after `form.reset()` (`data-value` on a select, combobox, or toggle group, or `calendarSetValue`) stays; the kit does not overwrite it.
- A form that is also a card: `data-slot` takes one value, so put the card inside the form (`<form data-slot="form"><div data-slot="card">...</div></form>`).
- Date picker and toggle group: see their sections for `data-required` and `data-name`.
