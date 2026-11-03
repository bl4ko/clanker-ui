# Input OTP (`input-otp`)

Group `forms`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `input-otp` (root) | `data-pattern` `alphanumeric`, `chars`, `digits` |  |
| `input-otp-slot` |  | `data-active` |

Other parts: `input-otp-group`, `input-otp-separator`.

Kit adds: `input-otp-caret`.

Events: `input-otp:complete` `{ value }`.

## Full text

### Input OTP

```html
<div data-slot="input-otp" data-pattern="digits|chars|alphanumeric">
  <input maxlength="6" name="code" aria-label="One-time code">
  <div data-slot="input-otp-group"><div data-slot="input-otp-slot"></div></div>
  <div data-slot="input-otp-separator" role="separator"><svg data-lucide="minus"></svg></div>
</div>
```

One real input lies over the slots (autofill, form value, `required`, `minlength` stay native). The active empty slot shows `input-otp-caret` with an inner `div` (the blinking line). The kit gives the input the inline styles of the `input-otp` library (transparent text over the slots, `data-input-otp`) and the root `--root-height`. `aria-invalid="true"` on the input also marks every slot, as shadcn sets it on the slots. The pattern filters typed and pasted characters. Arrows move between slots; in RTL the slots run right to left and the kit moves the caret with the visual arrow (ArrowRight goes to the previous slot) in every engine.
