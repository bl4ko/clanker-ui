# Switch (`switch`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `switch` (root) | `data-name` string; `data-size` `default`, `sm` | `data-checked`, `data-disabled`, `data-state`, `data-unchecked` |
| `switch-thumb` (kit adds) |  | `data-checked`, `data-state`, `data-unchecked` |

Other options named in the docs: `data-checked` any; `data-readonly` any.

Events: `switch:change` `{ checked, value }`.

## Full text

### Checkbox, Switch, Radio Group

```html
<button type="button" data-slot="checkbox" id="terms" data-name="terms" value="yes" data-checked data-required></button>
<label data-slot="label" for="terms">Accept terms</label>
<button type="button" data-slot="checkbox" data-indeterminate aria-label="Select all"></button>
<button type="button" data-slot="switch" id="airplane" data-name="airplane" data-size="sm"></button>
<div data-slot="radio-group" data-name="plan" data-value="free" data-required>
  <button type="button" data-slot="radio-group-item" id="plan-free" value="free"></button>
</div>
```

- The Base UI DOM with a native button: `role="checkbox"`, `role="switch"`, or `role="radio"`, `aria-checked` (`mixed` for indeterminate), and the state attributes `data-checked` or `data-unchecked`, `data-indeterminate`, `data-disabled`, `data-readonly`, `data-required`, `data-invalid` (from `aria-invalid="true"`). `data-state` stays in sync.
- The kit adds a hidden native input right after the button (`aria-hidden`, `tabindex="-1"`) for form submission, reset, and validation. It gets `data-name` (radio: the group `data-name`), `value` (default `on`), `required` (`data-required` on the button or the group), and `disabled`. Focus on the hidden input moves to the button. The input follows the button: a removed button takes it out of the form, a moved button moves it. `form.reset()` restores the initial state, also `data-indeterminate`.
- Children: `checkbox-indicator` (check icon) and `radio-group-indicator` exist only while checked; `switch-thumb` is always there and has the same state attributes.
- Initial state: `data-checked` on the button. Change it later the same way: toggle `data-checked` on the button. `disabled`, `aria-invalid`, `data-required`, and `data-readonly` changes are applied at once. The kit moves `disabled` to `aria-disabled`, so enable the control again with `el.disabled = false` or by removing `aria-disabled` (removing the `disabled` attribute has no effect). Read-only controls do not change. A click on a disabled control does not move focus.
- Switch: `data-name`, `data-required`, and `data-readonly` on the button. Click, Space, Enter, and a `<label for>` or wrapping `<label>` toggle.
- Events: `checkbox:change` and `switch:change` on the button (`{ checked, value }`), `radio-group:change` on the group (`{ value }`), and native `input` and `change` on the hidden input.
