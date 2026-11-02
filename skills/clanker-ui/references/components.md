# clanker-ui components

Generated from `clanker-ui.json` (same directory) by `go run ./tools/gen catalog`. Version 0.1.0, shadcn `b8d7baa`, Base UI 1.6.0.

## Groups

Each group has `clanker-ui-<group>.min.css` and (except core CSS-only parts) `clanker-ui-<group>.min.js`. Load `core` always, then the group of each component and the groups in its **Needs**.

| Group | CSS | JS | Components |
| --- | --- | --- | --- |
| `core` | `clanker-ui-core.min.css` | `clanker-ui-core.min.js` | button, separator, direction, theme, input, textarea, label, kbd, card, badge, alert, table, skeleton, spinner, empty, progress, aspect-ratio |
| `forms` | `clanker-ui-forms.min.css` | `clanker-ui-forms.min.js` | button-group, input-group, input-otp, field, form, checkbox, radio-group, switch, slider, select, native-select, combobox, toggle, toggle-group |
| `overlays` | `clanker-ui-overlays.min.css` | `clanker-ui-overlays.min.js` | dialog, alert-dialog, sheet, drawer, popover, tooltip, hover-card, dropdown-menu, context-menu, menubar, navigation-menu, command, toast, sonner |
| `layout` | `clanker-ui-layout.min.css` | `clanker-ui-layout.min.js` | avatar, accordion, collapsible, tabs, breadcrumb, pagination, scroll-area, resizable, sidebar, carousel, item |
| `chat` | `clanker-ui-chat.min.css` | `clanker-ui-chat.min.js` | message, bubble, attachment, message-scroller, trace, marker, questionnaire, code-block, calendar, date-picker |
| `chart` | `clanker-ui-chart.min.css` | `clanker-ui-chart.min.js` | chart |

Global attributes (any element): `data-align` `center`, `end`, `start`; `data-align-offset` number; `data-icon` `inline-end`, `inline-start`; `data-lucide` string; `data-scheme` string; `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top`; `data-side-offset` number; `data-theme-picker` string; `data-theme-set` `dark`, `light`, `system`, `toggle`; `data-typography` (empty), `blockquote`, `h1`, `h2`, `h3`, `h4`, `inline-code`, `large`, `lead`, `list`, `muted`, `p`, `small`, `table`; `data-string-<key>` (localized label override).

## Components

Per component: **Parts** lists each `data-slot`. **Write** = attributes you may author. **State** = attributes the kit sets; style on them, never write them. **Kit adds** = parts the kit creates; do not write them. **Part attributes** go on an element of another component (for example a `button`) to give it this component's behavior.

### Button (`button`)

Group `core`. Needs none. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/button/. Full text: https://github.com/bl4ko/clanker-ui#button

| Part | Write | State |
| --- | --- | --- |
| `button` (root) | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` | `data-calendar-day-button`, `data-range-end`, `data-range-middle`, `data-range-start`, `data-selected-single` |

Keyboard and focus:

- A `<button>` without a `tabindex` gets `tabindex="0"` like the Base UI button, so Tab reaches it also in Safari.

```html
<button type="button" data-slot="button" data-variant="outline" data-size="sm"><svg data-lucide="send"></svg>Send</button>
<a data-slot="button" data-variant="link" href="/docs">Docs</a>
```

### Separator (`separator`)

Group `core`. Needs none. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/separator/. Full text: https://github.com/bl4ko/clanker-ui#alert-aspect-ratio-badge-card-empty-item-separator-skeleton

| Part | Write | State |
| --- | --- | --- |
| `separator` (root) | `data-orientation` `horizontal`, `vertical` |  |

```html
<div>Blog</div>
<div data-slot="separator"></div>
<div data-slot="separator" data-orientation="vertical" role="separator"></div>
```

### Direction (`direction`)

Group `core`. Needs none. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/direction/. Full text: https://github.com/bl4ko/clanker-ui#direction

| Part | Write | State |
| --- | --- | --- |

Exports (import from the module that the page loads):

- `direction(el = <html>) → "ltr" | "rtl"`

Keyboard and focus:

- Kit styles use logical properties (`inset-inline`, `margin-inline`, `padding-inline`, `border-inline`, `text-align: start`) for everything that follows the reading direction; icons that point along the reading direction flip with `:dir(rtl)`; keyboard arrows follow the visual direction.
- Physical sides stay where a value names one: sheet `data-side`, drawer `data-swipe-direction`, popup `data-side="left|right"`, toast swipe directions, and parts that JavaScript places (popups, the tooltip arrow, the slider thumb, the chart tooltip).
- The questionnaire keeps the upstream keys in RTL (ArrowLeft goes to the previous item).

```html
<div dir="rtl" lang="ar">
  <button type="button" data-slot="button" data-variant="outline"><svg data-lucide="arrow-right"></svg>التالي</button>
</div>
```

### Theme Switch (`theme`)

Group `core`. Needs none. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/theme-switch/. Full text: https://github.com/bl4ko/clanker-ui#theme-toggle-and-switch

| Part | Write | State |
| --- | --- | --- |
| `theme-switch` |  |  |

Events: `theme:change` `{ mode, resolved, scheme }`.

Exports (import from the module that the page loads):

- `theme.get(), theme.set("light"|"dark"|"system"), theme.resolved(), theme.toggle(), theme.scheme(), theme.setScheme(value), theme.schemes`: The mode is stored in `localStorage["clanker-ui-theme"]` and applied as `data-theme` on `<html>`. `resolved()` returns the mode that shows (`dark` for a dark-only scheme). `toggle()` does what the toggle button does. `scheme()` returns `data-scheme` (`""` when there is none). `setScheme` takes names separated by spaces (`a-z`, `0-9`, `-`, at most 200 characters, else a `TypeError`) and stores them in `localStorage["clanker-ui-scheme"]`; `""` removes the scheme. `schemes` is the frozen list `{ value, label, group }` (`group`: `shadcn`, `editor`, or `accent`). See [Color schemes](https://github.com/bl4ko/clanker-ui#color-schemes).

Keyboard and focus:

- `aria-keyshortcuts="D"` on a toggle turns on the shadcn `D` key: `D` without Ctrl, Meta, or Alt toggles the theme.

```html
<div data-slot="theme-switch" role="group" aria-label="Theme">
  <button type="button" data-theme-set="light" aria-label="Light theme"><svg data-lucide="sun"></svg></button>
  <button type="button" data-theme-set="dark" aria-label="Dark theme"><svg data-lucide="moon"></svg></button>
  <button type="button" data-theme-set="system" aria-label="System theme"><svg data-lucide="monitor"></svg></button>
</div>
```

### Input (`input`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/input/. Full text: https://github.com/bl4ko/clanker-ui#input-textarea-label-kbd

| Part | Write | State |
| --- | --- | --- |
| `input` (root) | `data-error-value-missing` string |  |

```html
<input data-slot="input" type="email" placeholder="Email">
```

### Textarea (`textarea`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/textarea/. Full text: https://github.com/bl4ko/clanker-ui#input-textarea-label-kbd

| Part | Write | State |
| --- | --- | --- |
| `textarea` (root) |  |  |

```html
<textarea data-slot="textarea"></textarea>
```

### Label (`label`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/label/. Full text: https://github.com/bl4ko/clanker-ui#input-textarea-label-kbd

| Part | Write | State |
| --- | --- | --- |
| `label` (root) |  |  |

```html
<label data-slot="label" for="email">Email</label>
```

### Kbd (`kbd`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/kbd/. Full text: https://github.com/bl4ko/clanker-ui#input-textarea-label-kbd

| Part | Write | State |
| --- | --- | --- |
| `kbd` (root) |  |  |
| `kbd-group` |  |  |

```html
<kbd data-slot="kbd-group"><kbd data-slot="kbd">Ctrl</kbd><kbd data-slot="kbd">K</kbd></kbd>
```

### Card (`card`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/card/. Full text: https://github.com/bl4ko/clanker-ui#alert-aspect-ratio-badge-card-empty-item-separator-skeleton

| Part | Write | State |
| --- | --- | --- |
| `card` (root) | `data-size` `sm` |  |
| `card-action` |  |  |
| `card-content` |  |  |
| `card-description` |  |  |
| `card-footer` |  |  |
| `card-header` |  |  |
| `card-title` |  |  |

```html
<div data-slot="card" data-size="sm">
  <div data-slot="card-header">
    <div data-slot="card-title">Team members</div>
    <div data-slot="card-description">Invite your team members to collaborate.</div>
    <div data-slot="card-action"><button type="button" data-slot="button" data-variant="link">Invite</button></div>
  </div>
  <div data-slot="card-content">Content</div>
  <div data-slot="card-footer"><button type="button" data-slot="button" data-variant="outline">Manage access</button></div>
</div>
```

### Badge (`badge`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/badge/. Full text: https://github.com/bl4ko/clanker-ui#alert-aspect-ratio-badge-card-empty-item-separator-skeleton

| Part | Write | State |
| --- | --- | --- |
| `badge` (root) | `data-variant` `default`, `destructive`, `ghost`, `info`, `link`, `outline`, `secondary`, `success`, `warning` |  |

```html
<span data-slot="badge">Badge</span>
<span data-slot="badge" data-variant="secondary">Secondary</span>
<a data-slot="badge" data-variant="success" href="#status"><svg data-lucide="circle-check"></svg>Passing</a>
```

### Alert (`alert`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/alert/. Full text: https://github.com/bl4ko/clanker-ui#alert-aspect-ratio-badge-card-empty-item-separator-skeleton

| Part | Write | State |
| --- | --- | --- |
| `alert` (root) | `data-variant` `default`, `destructive`, `info`, `success`, `warning` |  |
| `alert-action` |  |  |
| `alert-description` |  |  |
| `alert-title` |  |  |

```html
<div data-slot="alert" data-variant="destructive" role="alert">
  <svg data-lucide="circle-alert"></svg>
  <div data-slot="alert-title">Payment failed</div>
  <div data-slot="alert-description">Check your payment method and try again.</div>
  <div data-slot="alert-action"><button type="button" data-slot="button" data-variant="outline" data-size="sm">Retry</button></div>
</div>
```

### Table (`table`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/table/. Full text: https://github.com/bl4ko/clanker-ui#table

| Part | Write | State |
| --- | --- | --- |
| `table` (root) |  |  |
| `table-body` |  |  |
| `table-caption` |  |  |
| `table-cell` |  |  |
| `table-container` |  |  |
| `table-footer` |  |  |
| `table-head` |  |  |
| `table-header` |  |  |
| `table-row` | `data-state` string |  |

```html
<div data-slot="table-container">
  <table data-slot="table">
    <caption data-slot="table-caption">A list of your recent invoices.</caption>
    <thead data-slot="table-header">
      <tr data-slot="table-row"><th data-slot="table-head" scope="col">Invoice</th><th data-slot="table-head" scope="col">Amount</th></tr>
    </thead>
    <tbody data-slot="table-body">
      <tr data-slot="table-row" data-state="selected"><td data-slot="table-cell">INV001</td><td data-slot="table-cell">$250.00</td></tr>
    </tbody>
    <tfoot data-slot="table-footer">
      <tr data-slot="table-row"><td data-slot="table-cell">Total</td><td data-slot="table-cell">$250.00</td></tr>
    </tfoot>
  </table>
</div>
```

### Skeleton (`skeleton`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/skeleton/. Full text: https://github.com/bl4ko/clanker-ui#alert-aspect-ratio-badge-card-empty-item-separator-skeleton

| Part | Write | State |
| --- | --- | --- |
| `skeleton` (root) |  |  |

```html
<div data-slot="skeleton" id="avatar-placeholder"></div>
<div data-slot="skeleton" id="line-placeholder"></div>
```

### Spinner (`spinner`)

Group `core`. Needs none. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/spinner/. Full text: https://github.com/bl4ko/clanker-ui#progress-spinner

| Part | Write | State |
| --- | --- | --- |
| `spinner` (root) | `data-size` `lg`, `sm`, `xl` |  |

```html
<svg data-slot="spinner"></svg>
<button type="button" data-slot="button" disabled><svg data-slot="spinner" data-size="sm" role="none"></svg>Saving</button>
```

### Empty (`empty`)

Group `core`. Needs none. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/empty/. Full text: https://github.com/bl4ko/clanker-ui#alert-aspect-ratio-badge-card-empty-item-separator-skeleton

| Part | Write | State |
| --- | --- | --- |
| `empty` (root) | `data-variant` `outline` |  |
| `empty-content` |  |  |
| `empty-description` |  |  |
| `empty-header` | `data-variant` `icon` |  |
| `empty-icon` | `data-variant` `default`, `icon` |  |
| `empty-title` |  |  |

```html
<div data-slot="empty" data-variant="outline">
  <div data-slot="empty-header">
    <div data-slot="empty-icon" data-variant="icon"><svg data-lucide="folder"></svg></div>
    <div data-slot="empty-title">No Projects Yet</div>
    <div data-slot="empty-description">Get started by creating your first project.</div>
  </div>
  <div data-slot="empty-content"><button type="button" data-slot="button">Create Project</button></div>
</div>
```

### Progress (`progress`)

Group `core`. Needs none. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/progress/. Full text: https://github.com/bl4ko/clanker-ui#progress-spinner

| Part | Write | State |
| --- | --- | --- |
| `progress` (root) | `data-max` number; `data-value` number |  |
| `progress-indicator` (kit adds) |  |  |
| `progress-label` |  |  |
| `progress-track` (kit adds) |  |  |
| `progress-value` |  |  |

```html
<div data-slot="progress" data-value="60" data-max="100" aria-label="Upload">
  <span data-slot="progress-label">Upload</span>
  <span data-slot="progress-value"></span>
</div>
```

### Aspect Ratio (`aspect-ratio`)

Group `core`. Needs none. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/aspect-ratio/. Full text: https://github.com/bl4ko/clanker-ui#alert-aspect-ratio-badge-card-empty-item-separator-skeleton

| Part | Write | State |
| --- | --- | --- |
| `aspect-ratio` (root) | `data-ratio` string |  |

```html
<div data-slot="aspect-ratio" data-ratio="16/9">
  <img src="photo.jpg" alt="A sunset over purple mountains" width="1600" height="900">
</div>
```

### Button Group (`button-group`)

Group `forms`. Needs `core`. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/button-group/. Full text: https://github.com/bl4ko/clanker-ui#button-group

| Part | Write | State |
| --- | --- | --- |
| `button-group` (root) | `data-orientation` `horizontal`, `vertical` |  |
| `button-group-separator` | `data-orientation` `horizontal`, `vertical` |  |
| `button-group-text` |  |  |

```html
<div data-slot="button-group" role="group" aria-label="Actions" data-orientation="horizontal">
  <button type="button" data-slot="button" data-variant="outline">Archive</button>
  <div data-slot="button-group-separator" data-orientation="vertical" role="none"></div>
  <span data-slot="button-group-text">.com</span>
</div>
```

### Input Group (`input-group`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/input-group/. Full text: https://github.com/bl4ko/clanker-ui#input-group

| Part | Write | State |
| --- | --- | --- |
| `input-group` (root) |  | `data-combobox-input` |
| `input-group-addon` | `data-align` `block-end`, `block-start`, `inline-end`, `inline-start` |  |
| `input-group-button` |  | `data-pressed` |
| `input-group-control` |  |  |
| `input-group-text` |  |  |

Part attributes: `data-input-group-button` boolean.

```html
<div data-slot="input-group" role="group">
  <input data-slot="input-group-control" placeholder="Search...">
  <div data-slot="input-group-addon" data-align="inline-start">
    <svg data-lucide="search"></svg>
    <span data-slot="input-group-text">USD</span>
    <button type="button" data-slot="button" data-input-group-button data-size="xs">Copy</button>
  </div>
</div>
```

### Input OTP (`input-otp`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/input-otp/. Full text: https://github.com/bl4ko/clanker-ui#input-otp

| Part | Write | State |
| --- | --- | --- |
| `input-otp` (root) | `data-pattern` `alphanumeric`, `chars`, `digits` |  |
| `input-otp-caret` (kit adds) |  |  |
| `input-otp-group` |  |  |
| `input-otp-separator` |  |  |
| `input-otp-slot` |  | `data-active` |

Events: `input-otp:complete` `{ value }`.

Keyboard and focus:

- Arrows move between slots; in RTL the slots run right to left and the kit moves the caret with the visual arrow (ArrowRight goes to the previous slot) in every engine.

```html
<div data-slot="input-otp" data-pattern="digits">
  <input maxlength="6" name="code" aria-label="One-time code">
  <div data-slot="input-otp-group"><div data-slot="input-otp-slot"></div></div>
  <div data-slot="input-otp-separator" role="separator"><svg data-lucide="minus"></svg></div>
</div>
```

### Field (`field`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/field/. Full text: https://github.com/bl4ko/clanker-ui#field

| Part | Write | State |
| --- | --- | --- |
| `field` (root) | `data-disabled` `false`, `true`; `data-invalid` `false`, `true`; `data-orientation` `horizontal`, `responsive`, `vertical` |  |
| `field-content` |  |  |
| `field-description` |  |  |
| `field-error` |  |  |
| `field-group` |  |  |
| `field-label` |  |  |
| `field-legend` | `data-variant` `label`, `legend` |  |
| `field-separator` |  |  |
| `field-separator-content` |  |  |
| `field-set` |  |  |

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

### Form (`form`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/form/. Full text: https://github.com/bl4ko/clanker-ui#form

| Part | Write | State |
| --- | --- | --- |
| `form` (root) |  |  |
| `form-description` |  |  |
| `form-item` |  |  |
| `form-label` | `data-error` any |  |
| `form-message` |  |  |

Other options named in the docs: `data-error-type-mismatch` any; `data-error-value-missing` any.

Events: `form:invalid` `{ errors }`; `form:submit` `{ formData, values, submitter }` (cancelable).

```html
<form data-slot="form">
  <div data-slot="field" role="group">
    <label data-slot="field-label" for="name">Name</label>
    <input id="name" data-slot="input" name="name" required data-error-value-missing="Name is required.">
  </div>
</form>
```

### Checkbox (`checkbox`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/checkbox/. Full text: https://github.com/bl4ko/clanker-ui#checkbox-switch-radio-group

| Part | Write | State |
| --- | --- | --- |
| `checkbox` (root) | `data-checked` boolean; `data-indeterminate` boolean; `data-name` string; `data-required` boolean | `data-state` |
| `checkbox-group` |  |  |
| `checkbox-indicator` |  |  |

Other options named in the docs: `data-value` any.

Events: `checkbox:change` `{ checked, value }`.

```html
<button type="button" data-slot="checkbox" id="terms" data-name="terms" value="yes" data-checked data-required></button>
<button type="button" data-slot="checkbox" data-indeterminate aria-label="Select all"></button>
```

### Radio Group (`radio-group`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/radio-group/. Full text: https://github.com/bl4ko/clanker-ui#checkbox-switch-radio-group

| Part | Write | State |
| --- | --- | --- |
| `radio-group` (root) | `data-name` string; `data-required` boolean; `data-value` string |  |
| `radio-group-indicator` |  |  |
| `radio-group-item` |  | `data-checked`, `data-state` |

Other options named in the docs: `data-checked` any; `data-indeterminate` any.

Events: `radio-group:change` `{ value }`.

```html
<div data-slot="radio-group" data-name="plan" data-value="free" data-required>
  <button type="button" data-slot="radio-group-item" id="plan-free" value="free"></button>
</div>
```

### Switch (`switch`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/switch/. Full text: https://github.com/bl4ko/clanker-ui#checkbox-switch-radio-group

| Part | Write | State |
| --- | --- | --- |
| `switch` (root) | `data-size` `default`, `sm` | `data-checked`, `data-disabled`, `data-state`, `data-unchecked` |
| `switch-thumb` (kit adds) |  | `data-checked`, `data-state`, `data-unchecked` |

Other options named in the docs: `data-checked` any; `data-indeterminate` any; `data-value` any.

Events: `switch:change` `{ checked, value }`.

Keyboard and focus:

- Click, Space, and a `<label for>` or wrapping `<label>` toggle.
- Enter toggles only the switch.
- Radio: one tab stop (the checked item, else the first enabled one, with `data-composite-item-active`); arrows move and check, wrap, skip disabled items, and follow RTL; Home and End do nothing.

```html
<button type="button" data-slot="switch" id="airplane" data-size="sm"></button>
```

### Slider (`slider`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/slider/. Full text: https://github.com/bl4ko/clanker-ui#slider

| Part | Write | State |
| --- | --- | --- |
| `slider` (root) | `data-large-step` number; `data-orientation` `horizontal`, `vertical` |  |
| `slider-range` (kit adds) | `data-orientation` `horizontal`, `vertical` |  |
| `slider-thumb` (kit adds) | `data-index` any |  |
| `slider-track` (kit adds) | `data-orientation` `horizontal`, `vertical` |  |

Keyboard and focus:

- Keys: arrows (RTL aware), Shift+arrow and Page Up/Down by `data-large-step` (default 10, in value units), Home, End.
- Keys stop at the next thumb.

```html
<div data-slot="slider" data-orientation="horizontal" data-large-step="10">
  <input type="range" min="0" max="100" step="5" value="25" name="min" aria-label="Minimum">
  <input type="range" min="0" max="100" step="5" value="75" name="max" aria-label="Maximum">
</div>
```

### Select (`select`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/select/. Full text: https://github.com/bl4ko/clanker-ui#select

| Part | Write | State |
| --- | --- | --- |
| `select` (root) | `data-name` string; `data-required` boolean; `data-value` string |  |
| `select-content` | `data-align-trigger` `false`, `true`; `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `select-group` |  |  |
| `select-icon` (kit adds) |  |  |
| `select-item` | `data-disabled` boolean; `data-label` string; `data-value` string |  |
| `select-item-indicator` (kit adds) |  |  |
| `select-item-text` (kit adds) |  |  |
| `select-label` |  |  |
| `select-scroll-down-button` (kit adds) |  |  |
| `select-scroll-up-button` (kit adds) |  |  |
| `select-separator` |  |  |
| `select-trigger` | `data-size` `default`, `sm` | `data-placeholder` |
| `select-value` |  |  |
| `select-viewport` (kit adds) |  |  |

Events: `select:open`; `select:close`; `select:change` `{ value }`.

Keyboard and focus:

- The trigger has `tabindex="0"` like Base UI, so Tab reaches it also in Safari.
- Keyboard: Enter, Space, Up, Down open on the selected item; typing on the closed trigger selects the next match (750 ms buffer) without opening.
- In the list: arrows (no wrap), Home, End, typeahead (a space within 750 ms of a typed letter is part of the search), Enter or Space to select, Escape to close, Tab closes without a change and moves on.

```html
<div data-slot="select" data-name="fruit" data-value="apple" data-required>
  <button data-slot="select-trigger" data-size="sm"><span data-slot="select-value">Select a fruit</span></button>
  <div data-slot="select-content" data-align-trigger="true">
    <div data-slot="select-group">
      <div data-slot="select-label">Fruits</div>
      <div data-slot="select-item" data-value="apple" data-label="Apple">Apple</div>
      <div data-slot="select-item" data-value="banana" data-disabled>Banana</div>
    </div>
    <div data-slot="select-separator"></div>
  </div>
</div>
```

### Native Select (`native-select`)

Group `forms`. Needs `core`. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/native-select/. Full text: https://github.com/bl4ko/clanker-ui#native-select

| Part | Write | State |
| --- | --- | --- |
| `native-select` (root) | `data-size` `sm` |  |
| `native-select-icon` |  |  |
| `native-select-optgroup` |  |  |
| `native-select-option` |  |  |
| `native-select-wrapper` |  |  |

```html
<div data-slot="native-select-wrapper">
  <select data-slot="native-select" data-size="sm">
    <option data-slot="native-select-option" value="todo">Todo</option>
  </select>
  <svg data-lucide="chevron-down" data-slot="native-select-icon"></svg>
</div>
```

### Combobox (`combobox`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/combobox/. Full text: https://github.com/bl4ko/clanker-ui#combobox

| Part | Write | State |
| --- | --- | --- |
| `combobox` (root) | `data-auto-highlight` boolean; `data-name` string; `data-value` string |  |
| `combobox-chip` (kit adds) |  |  |
| `combobox-chip-input` |  |  |
| `combobox-chip-remove` (kit adds) |  |  |
| `combobox-chips` |  |  |
| `combobox-clear` |  |  |
| `combobox-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-chips`, `data-closed`, `data-open`, `data-state` |
| `combobox-empty` |  |  |
| `combobox-group` |  |  |
| `combobox-item` | `data-value` string | `data-disabled`, `data-highlighted` |
| `combobox-item-indicator` (kit adds) |  |  |
| `combobox-label` |  |  |
| `combobox-list` |  | `data-empty` |
| `combobox-separator` |  |  |
| `combobox-trigger-icon` (kit adds) |  |  |
| `combobox-value` |  |  |

Part attributes: `data-combobox-trigger` boolean.

Other options named in the docs: `data-multiple` any.

Events: `combobox:open`; `combobox:close`; `combobox:change` `{ value }`.

Keyboard and focus:

- Keyboard: Down and Up (also with Alt) open and move; after the last item (or before the first) the highlight goes back to the input, like Base UI `loopFocus`.
- Alt+Up closes, Enter selects (or closes when no item is highlighted), Escape closes; Escape on a closed combobox clears the value (all chips in multiple).
- Home and End move the caret and never scroll the page.
- Chips (`role="toolbar"`): Backspace in an empty input removes the last chip, Left moves into the chips, Backspace and Delete remove a chip.

```html
<div data-slot="combobox" data-name="framework" data-value="next" data-auto-highlight>
  <div data-slot="input-group">
    <input data-slot="input-group-control" placeholder="Select a framework" aria-label="Framework">
    <div data-slot="input-group-addon" data-align="inline-end">
      <button type="button" data-slot="input-group-button" data-combobox-trigger></button>
      <button type="button" data-slot="combobox-clear"></button>
    </div>
  </div>
  <div data-slot="combobox-content">
    <div data-slot="combobox-empty">No items found.</div>
    <div data-slot="combobox-list">
      <div data-slot="combobox-group">
        <div data-slot="combobox-label">Frameworks</div>
        <div data-slot="combobox-item" data-value="next">Next.js</div>
      </div>
      <div data-slot="combobox-separator"></div>
    </div>
  </div>
</div>
```

### Toggle (`toggle`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/toggle/. Full text: https://github.com/bl4ko/clanker-ui#toggle-and-toggle-group

| Part | Write | State |
| --- | --- | --- |
| `toggle` (root) | `data-size` `default`, `lg`, `sm`; `data-variant` `default`, `outline` | `data-state` |

Events: `toggle:change` `{ pressed, value }`.

Keyboard and focus:

- One tab stop, arrows (RTL aware), Home, End.

```html
<button type="button" data-slot="toggle" data-variant="outline" data-size="sm" aria-pressed="false">Bold</button>
```

### Toggle Group (`toggle-group`)

Group `forms`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/toggle-group/. Full text: https://github.com/bl4ko/clanker-ui#toggle-and-toggle-group

| Part | Write | State |
| --- | --- | --- |
| `toggle-group` (root) | `data-disabled` boolean; `data-orientation` `horizontal`, `vertical`; `data-size` `sm`; `data-spacing` `0`, `1`, `2`, `3`, `4`, `6`, `8`; `data-type` `multiple`, `single`; `data-value` string; `data-variant` `outline` |  |
| `toggle-group-item` | `data-size` `default`, `lg`, `sm`; `data-spacing` `0`; `data-value` string; `data-variant` `default`, `outline` | `data-state` |

Events: `toggle-group:change` `{ value }`.

```html
<div data-slot="toggle-group" data-type="single" data-variant="outline" data-size="sm" data-spacing="2" data-orientation="horizontal" data-value="bold,italic" data-disabled>
  <button type="button" data-slot="toggle-group-item" data-value="bold" aria-label="Bold"><svg data-lucide="bold"></svg></button>
</div>
```

### Dialog (`dialog`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/dialog/. Full text: https://github.com/bl4ko/clanker-ui#dialog-alert-dialog-sheet-drawer

| Part | Write | State |
| --- | --- | --- |
| `dialog` (root) |  |  |
| `dialog-close` |  |  |
| `dialog-content` |  | `data-closed`, `data-command-dialog`, `data-open`, `data-state` |
| `dialog-description` |  |  |
| `dialog-footer` | `data-show-close-button` boolean |  |
| `dialog-header` |  |  |
| `dialog-title` |  |  |

Part attributes: `data-dialog-close` boolean; `data-dialog-trigger` id.

Events: `dialog:open` `{ trigger }`; `dialog:close` `{ reason }` (cancelable).

Exports (import from the module that the page loads):

- `dialogOpen(target, { trigger }?) → boolean`: Works for `dialog`, `alert-dialog`, `sheet`, and `drawer`.
- `dialogClose(target, reason = "api") → boolean`: `reason` goes to the `:close` event.

```html
<div data-slot="dialog">
  <button type="button" data-slot="button" data-variant="outline" data-dialog-trigger>Open</button>
  <dialog data-slot="dialog-content">
    <div data-slot="dialog-header">
      <h2 data-slot="dialog-title">Edit profile</h2>
      <p data-slot="dialog-description">Make changes here.</p>
    </div>
    <div data-slot="dialog-footer">
      <button type="button" data-slot="button" data-variant="outline" data-dialog-close>Cancel</button>
    </div>
  </dialog>
</div>
```

### Alert Dialog (`alert-dialog`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/alert-dialog/. Full text: https://github.com/bl4ko/clanker-ui#dialog-alert-dialog-sheet-drawer

| Part | Write | State |
| --- | --- | --- |
| `alert-dialog` (root) |  |  |
| `alert-dialog-action` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `alert-dialog-cancel` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `alert-dialog-content` | `data-size` `default`, `sm` | `data-closed`, `data-open`, `data-state` |
| `alert-dialog-description` |  |  |
| `alert-dialog-footer` |  |  |
| `alert-dialog-header` |  |  |
| `alert-dialog-media` |  |  |
| `alert-dialog-title` |  |  |

Part attributes: `data-alert-dialog-action` boolean; `data-alert-dialog-cancel` boolean; `data-alert-dialog-trigger` boolean.

Events: `alert-dialog:open` `{ trigger }`; `alert-dialog:close` `{ reason }` (cancelable).

Keyboard and focus:

- A native `<dialog>` opened with `showModal()`: focus trap, Escape, scroll lock, inert page, focus returns to the trigger.

```html
<div data-slot="alert-dialog">
  <button type="button" data-slot="button" data-variant="outline" data-alert-dialog-trigger>Delete account</button>
  <dialog data-slot="alert-dialog-content" data-size="sm">
    <div data-slot="alert-dialog-header">
      <h2 data-slot="alert-dialog-title">Are you absolutely sure?</h2>
      <p data-slot="alert-dialog-description">This action cannot be undone.</p>
    </div>
    <div data-slot="alert-dialog-footer">
      <button type="button" data-slot="alert-dialog-cancel" data-variant="outline">Cancel</button>
      <button type="button" data-slot="alert-dialog-action" data-variant="destructive">Delete</button>
    </div>
  </dialog>
</div>
```

### Sheet (`sheet`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/sheet/. Full text: https://github.com/bl4ko/clanker-ui#dialog-alert-dialog-sheet-drawer

| Part | Write | State |
| --- | --- | --- |
| `sheet` (root) |  |  |
| `sheet-close` |  |  |
| `sheet-content` | `data-side` `bottom`, `left`, `right`, `top` | `data-ending-style`, `data-starting-style` |
| `sheet-description` |  |  |
| `sheet-footer` |  |  |
| `sheet-header` |  |  |
| `sheet-overlay` (kit adds) |  |  |
| `sheet-title` |  |  |

Part attributes: `data-sheet-close` boolean; `data-sheet-trigger` boolean.

Other options named in the docs: `data-show-close-button` `false`, `true`.

Events: `sheet:open` `{ trigger }`; `sheet:close` `{ reason }` (cancelable).

```html
<div data-slot="sheet">
  <button type="button" data-slot="button" data-variant="outline" data-sheet-trigger>Open</button>
  <dialog data-slot="sheet-content" data-side="right">
    <div data-slot="sheet-header">
      <h2 data-slot="sheet-title">Edit profile</h2>
      <p data-slot="sheet-description">Make changes to your profile here.</p>
    </div>
    <div data-slot="sheet-footer">
      <button type="button" data-slot="button" data-sheet-close>Save changes</button>
    </div>
  </dialog>
</div>
```

### Drawer (`drawer`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/drawer/. Full text: https://github.com/bl4ko/clanker-ui#dialog-alert-dialog-sheet-drawer

| Part | Write | State |
| --- | --- | --- |
| `drawer` (root) | `data-show-swipe-handle` boolean; `data-swipe-direction` string |  |
| `drawer-content` | `data-drawer-content` any |  |
| `drawer-description` |  |  |
| `drawer-footer` |  |  |
| `drawer-header` |  |  |
| `drawer-popup` |  | `data-ending-style`, `data-nested-drawer-open`, `data-nested-drawer-swiping`, `data-snap-points`, `data-starting-style`, `data-swipe-axis`, `data-swipe-direction`, `data-swiping` |
| `drawer-swipe-handle` (kit adds) | `data-show-swipe-handle` any |  |
| `drawer-title` |  |  |
| `drawer-viewport` |  | `data-ending-style`, `data-modal`, `data-snap-points`, `data-starting-style`, `data-swiping` |

Part attributes: `data-drawer-close` boolean; `data-drawer-trigger` boolean.

Other options named in the docs: `data-base-ui-swipe-ignore` any; `data-disable-pointer-dismissal` any; `data-modal` `false`, `true`; `data-snap-point` any; `data-snap-points` string; `data-snap-to-sequential-points` any; `data-swipe-axis` `x`, `y`.

Events: `drawer:open` `{ trigger }`; `drawer:close` `{ reason }` (cancelable); `drawer:release` `{ delta }`; `drawer:snap-point-change` `{ snapPoint }`.

Keyboard and focus:

- While a modal dialog is open, the `toast-portal` element moves into the topmost open modal dialog (a modal makes everything else inert) and moves back when it closes, so toasts stay usable and Tab reaches them.

```html
<div data-slot="drawer" data-swipe-direction="down" data-show-swipe-handle>
  <button type="button" data-slot="button" data-variant="outline" data-drawer-trigger>Open</button>
  <dialog data-slot="drawer-viewport">
    <div data-slot="drawer-popup">
      <div data-slot="drawer-content">
        <div data-slot="drawer-header">
          <h2 data-slot="drawer-title">Move Goal</h2>
          <p data-slot="drawer-description">Set your daily activity goal.</p>
        </div>
        <div data-slot="drawer-footer">
          <button type="button" data-slot="button" data-drawer-close>Submit</button>
        </div>
      </div>
    </div>
  </dialog>
</div>
```

### Popover (`popover`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/popover/. Full text: https://github.com/bl4ko/clanker-ui#popover

| Part | Write | State |
| --- | --- | --- |
| `popover` (root) |  |  |
| `popover-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `popover-description` |  |  |
| `popover-header` |  |  |
| `popover-title` |  |  |
| `popover-trigger` | `data-popover-trigger` any |  |

Part attributes: `data-popover-trigger` boolean.

Events: `popover:open` `{ trigger }`; `popover:close` `{ reason }`.

Exports (import from the module that the page loads):

- `popoverOpen(target, { trigger, anchor }?) → boolean`
- `popoverClose(target, reason = "api") → boolean`

Keyboard and focus:

- Non-modal: focus moves into the content; Escape, outside click, and focus leaving close it.

```html
<div data-slot="popover">
  <button type="button" data-slot="button" data-variant="outline" data-popover-trigger>Open Popover</button>
  <div data-slot="popover-content" data-align="start">
    <div data-slot="popover-header">
      <div data-slot="popover-title">Dimensions</div>
      <p data-slot="popover-description">Set the dimensions for the layer.</p>
    </div>
  </div>
</div>
```

### Tooltip (`tooltip`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/tooltip/. Full text: https://github.com/bl4ko/clanker-ui#tooltip-and-hover-card

| Part | Write | State |
| --- | --- | --- |
| `tooltip` (root) |  |  |
| `tooltip-arrow` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` |  |
| `tooltip-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `tooltip-provider` | `data-delay-duration` any; `data-skip-delay-duration` any |  |

Part attributes: `data-tooltip-trigger` boolean.

Other options named in the docs: `data-close-delay` any; `data-delay` any; `data-timeout` any.

Events: `tooltip:open`; `tooltip:close`.

Keyboard and focus:

- It opens on keyboard focus too; it closes on leave, Escape, press, and blur.
- Default side `top`, 4 px; the kit adds the arrow (`<div data-slot="tooltip-arrow">`), which points at the trigger center.
- Like Base UI, the content and the arrow get `data-instant`: `delay` (opened at once because another tooltip was open or closed less than `data-timeout` ago), `focus` (opened by keyboard focus), `dismiss` (closed by Escape or a press).

```html
<div data-slot="tooltip">
  <button type="button" data-slot="button" data-variant="outline" data-size="icon-sm" data-tooltip-trigger aria-label="Save"><svg data-lucide="save"></svg></button>
  <div data-slot="tooltip-content" data-side="top">Save changes <kbd data-slot="kbd">S</kbd></div>
</div>
```

### Hover Card (`hover-card`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/hover-card/. Full text: https://github.com/bl4ko/clanker-ui#tooltip-and-hover-card

| Part | Write | State |
| --- | --- | --- |
| `hover-card` (root) |  |  |
| `hover-card-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |

Part attributes: `data-hover-card-trigger` boolean.

Other options named in the docs: `data-close-delay` any; `data-delay` any; `data-open-delay` any.

Events: `hover-card:open`; `hover-card:close`.

```html
<div data-slot="hover-card">
  <a data-slot="button" data-variant="link" href="/nextjs" data-hover-card-trigger data-delay="10" data-close-delay="100">@nextjs</a>
  <div data-slot="hover-card-content" data-side="bottom">The React Framework, created and maintained by @vercel.</div>
</div>
```

### Dropdown Menu (`dropdown-menu`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/dropdown-menu/. Full text: https://github.com/bl4ko/clanker-ui#dropdown-menu-context-menu-menubar

| Part | Write | State |
| --- | --- | --- |
| `dropdown-menu` (root) |  |  |
| `dropdown-menu-checkbox-item` | `data-checked` boolean | `data-disabled`, `data-inset` |
| `dropdown-menu-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `dropdown-menu-group` |  |  |
| `dropdown-menu-item` | `data-variant` `destructive` | `data-disabled`, `data-inset` |
| `dropdown-menu-label` |  | `data-inset` |
| `dropdown-menu-radio-group` | `data-value` string |  |
| `dropdown-menu-radio-item` | `data-checked` boolean; `data-value` string | `data-disabled`, `data-inset` |
| `dropdown-menu-separator` |  |  |
| `dropdown-menu-shortcut` |  |  |
| `dropdown-menu-sub` |  |  |
| `dropdown-menu-sub-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `dropdown-menu-sub-trigger` |  | `data-inset`, `data-open`, `data-popup-open`, `data-state` |
| `dropdown-menu-trigger` |  |  |

Part attributes: `data-dropdown-menu-trigger` boolean.

Other options named in the docs: `data-close-on-click` any; `data-disabled` any; `data-inset` any; `data-state` string; `data-text-value` any.

Events: `dropdown-menu:open` `{ trigger }`; `dropdown-menu:close` `{ reason }`; `dropdown-menu:select` `{ value, item, checked }` (cancelable); `dropdown-menu:change` `{ value, checked, item, group }`.

Keyboard and focus:

- The content has `data-open` or `data-closed`, `data-side`, `data-align`, and `data-instant` (`click` when a keyboard key or a right click opened it, `group` when a menubar switched menus, `dismiss` after Escape); the trigger has `data-popup-open` and `data-pressed` while open.
- Keyboard per WAI-ARIA APG with Base UI focus looping: Enter, Space, and ArrowDown open at the first item, ArrowUp at the last; arrows wrap from the last item to the first and back, Home, End, typeahead; arrows also stop on disabled items (highlighted, `aria-disabled`, they do not run), as in Base UI; ArrowRight opens a sub menu, ArrowLeft closes it (mirrored in RTL); Escape closes the innermost menu; Tab closes all.
- Typeahead continues across a space (`New W` reaches "New Window"); Space activates the item only when no typeahead is in progress.

```html
<div data-slot="dropdown-menu">
  <button type="button" data-slot="button" data-variant="outline" data-dropdown-menu-trigger>Open</button>
  <div data-slot="dropdown-menu-content">
    <div data-slot="dropdown-menu-group">
      <div data-slot="dropdown-menu-label">My Account</div>
      <div data-slot="dropdown-menu-item">Profile<span data-slot="dropdown-menu-shortcut">⇧⌘P</span></div>
      <div data-slot="dropdown-menu-checkbox-item" data-checked>Status Bar</div>
    </div>
    <div data-slot="dropdown-menu-radio-group" data-value="top">
      <div data-slot="dropdown-menu-radio-item" data-value="top" data-checked>Top</div>
    </div>
    <div data-slot="dropdown-menu-separator"></div>
    <div data-slot="dropdown-menu-sub">
      <div data-slot="dropdown-menu-sub-trigger">Invite users</div>
      <div data-slot="dropdown-menu-sub-content">...</div>
    </div>
  </div>
</div>
```

### Context Menu (`context-menu`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/context-menu/. Full text: https://github.com/bl4ko/clanker-ui#dropdown-menu-context-menu-menubar

| Part | Write | State |
| --- | --- | --- |
| `context-menu` (root) |  |  |
| `context-menu-checkbox-item` | `data-checked` boolean | `data-disabled`, `data-inset` |
| `context-menu-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `context-menu-group` |  |  |
| `context-menu-item` | `data-variant` `destructive` | `data-disabled`, `data-inset` |
| `context-menu-label` |  | `data-inset` |
| `context-menu-radio-group` | `data-value` string |  |
| `context-menu-radio-item` | `data-checked` boolean; `data-value` string | `data-disabled`, `data-inset` |
| `context-menu-separator` |  |  |
| `context-menu-shortcut` |  |  |
| `context-menu-sub` |  |  |
| `context-menu-sub-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `context-menu-sub-trigger` |  | `data-inset`, `data-open`, `data-state` |
| `context-menu-trigger` |  |  |

Other options named in the docs: `data-close-on-click` any; `data-disabled` any; `data-inset` any; `data-state` string; `data-text-value` any.

Events: `context-menu:open` `{ trigger }`; `context-menu:close` `{ reason }`; `context-menu:select` `{ value, item, checked }` (cancelable); `context-menu:change` `{ value, checked, item, group }`.

Keyboard and focus:

- The content has `data-open` or `data-closed`, `data-side`, `data-align`, and `data-instant` (`click` when a keyboard key or a right click opened it, `group` when a menubar switched menus, `dismiss` after Escape); the trigger has `data-popup-open` and `data-pressed` while open.
- Keyboard per WAI-ARIA APG with Base UI focus looping: Enter, Space, and ArrowDown open at the first item, ArrowUp at the last; arrows wrap from the last item to the first and back, Home, End, typeahead; arrows also stop on disabled items (highlighted, `aria-disabled`, they do not run), as in Base UI; ArrowRight opens a sub menu, ArrowLeft closes it (mirrored in RTL); Escape closes the innermost menu; Tab closes all.
- Typeahead continues across a space (`New W` reaches "New Window"); Space activates the item only when no typeahead is in progress.
- Right click, long press (700 ms), Shift+F10, or the ContextMenu key open it.

```html
<div data-slot="context-menu">
  <div data-slot="context-menu-trigger" tabindex="0" aria-label="Context menu area">Right click here</div>
  <div data-slot="context-menu-content">
    <div data-slot="context-menu-group">
      <div data-slot="context-menu-item">Back<span data-slot="context-menu-shortcut">⌘[</span></div>
      <div data-slot="context-menu-item" data-disabled>Forward</div>
      <div data-slot="context-menu-sub">
        <div data-slot="context-menu-sub-trigger">More Tools</div>
        <div data-slot="context-menu-sub-content">
          <div data-slot="context-menu-item" data-variant="destructive">Delete</div>
        </div>
      </div>
    </div>
    <div data-slot="context-menu-separator"></div>
    <div data-slot="context-menu-checkbox-item" data-checked>Show Bookmarks</div>
    <div data-slot="context-menu-radio-group" data-value="pedro">
      <div data-slot="context-menu-label">People</div>
      <div data-slot="context-menu-radio-item" data-value="pedro" data-checked>Pedro Duarte</div>
      <div data-slot="context-menu-radio-item" data-value="colm">Colm Tuite</div>
    </div>
  </div>
</div>
```

### Menubar (`menubar`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/menubar/. Full text: https://github.com/bl4ko/clanker-ui#dropdown-menu-context-menu-menubar

| Part | Write | State |
| --- | --- | --- |
| `menubar` (root) |  |  |
| `menubar-checkbox-item` | `data-checked` boolean | `data-disabled`, `data-inset` |
| `menubar-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `menubar-group` |  |  |
| `menubar-item` | `data-variant` `destructive` | `data-disabled`, `data-inset` |
| `menubar-label` |  | `data-inset` |
| `menubar-menu` |  |  |
| `menubar-radio-group` | `data-value` string |  |
| `menubar-radio-item` | `data-checked` boolean; `data-value` string | `data-disabled`, `data-inset` |
| `menubar-separator` |  |  |
| `menubar-shortcut` |  |  |
| `menubar-sub` |  |  |
| `menubar-sub-content` | `data-side` `bottom`, `inline-end`, `inline-start`, `left`, `right`, `top` | `data-closed`, `data-open`, `data-state` |
| `menubar-sub-trigger` |  | `data-inset`, `data-open`, `data-popup-open`, `data-state` |
| `menubar-trigger` |  |  |

Other options named in the docs: `data-close-on-click` any; `data-disabled` any; `data-inset` any; `data-modal` `false`, `true`; `data-state` string; `data-text-value` any.

Events: `menubar:open` `{ trigger }`; `menubar:close` `{ reason }`; `menubar:select` `{ value, item, checked }` (cancelable); `menubar:change` `{ value, checked, item, group }`.

Keyboard and focus:

- The content has `data-open` or `data-closed`, `data-side`, `data-align`, and `data-instant` (`click` when a keyboard key or a right click opened it, `group` when a menubar switched menus, `dismiss` after Escape); the trigger has `data-popup-open` and `data-pressed` while open.
- Keyboard per WAI-ARIA APG with Base UI focus looping: Enter, Space, and ArrowDown open at the first item, ArrowUp at the last; arrows wrap from the last item to the first and back, Home, End, typeahead; arrows also stop on disabled items (highlighted, `aria-disabled`, they do not run), as in Base UI; ArrowRight opens a sub menu, ArrowLeft closes it (mirrored in RTL); Escape closes the innermost menu; Tab closes all.
- Typeahead continues across a space (`New W` reaches "New Window"); Space activates the item only when no typeahead is in progress.
- Roving focus; ArrowLeft and ArrowRight in an open menu open the next menu and focus its popup (no item highlighted; ArrowDown goes to the first item); while a menu is open, hover switches menus and moves focus to the new menu; a click on another trigger while a menu is open, or on the open trigger, closes the menus and focuses that trigger.

```html
<div data-slot="menubar">
  <div data-slot="menubar-menu">
    <button type="button" data-slot="menubar-trigger">File</button>
    <div data-slot="menubar-content">
      <div data-slot="menubar-group">
        <div data-slot="menubar-item">New Tab<span data-slot="menubar-shortcut">⌘T</span></div>
        <div data-slot="menubar-item" data-disabled>New Incognito Window</div>
      </div>
      <div data-slot="menubar-separator"></div>
      <div data-slot="menubar-sub">
        <div data-slot="menubar-sub-trigger">Share</div>
        <div data-slot="menubar-sub-content">
          <div data-slot="menubar-item">Email link</div>
        </div>
      </div>
    </div>
  </div>
  <div data-slot="menubar-menu">
    <button type="button" data-slot="menubar-trigger">View</button>
    <div data-slot="menubar-content">
      <div data-slot="menubar-checkbox-item" data-checked>Full URLs</div>
      <div data-slot="menubar-item" data-inset>Reload</div>
    </div>
  </div>
</div>
```

### Navigation Menu (`navigation-menu`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/navigation-menu/. Full text: https://github.com/bl4ko/clanker-ui#navigation-menu

| Part | Write | State |
| --- | --- | --- |
| `navigation-menu` (root) |  |  |
| `navigation-menu-content` |  | `data-activation-direction`, `data-closed`, `data-ending-style`, `data-motion`, `data-open`, `data-starting-style`, `data-state` |
| `navigation-menu-focus-guard` (kit adds) |  |  |
| `navigation-menu-indicator` |  | `data-state` |
| `navigation-menu-indicator-arrow` (kit adds) |  |  |
| `navigation-menu-item` |  |  |
| `navigation-menu-link` | `data-active` any; `data-close-on-click` any; `data-variant` `trigger` | `data-open`, `data-popup-open`, `data-state` |
| `navigation-menu-list` |  |  |
| `navigation-menu-popup` (kit adds) |  | `data-ending-style`, `data-starting-style` |
| `navigation-menu-positioner` (kit adds) | `data-align` any; `data-side` `bottom` | `data-instant` |
| `navigation-menu-trigger` |  | `data-open`, `data-popup-open`, `data-state` |
| `navigation-menu-viewport` (kit adds) |  |  |

Other options named in the docs: `data-close-delay` any; `data-delay` any; `data-viewport` `false`, `true`.

Events: `navigation-menu:change` `{ value }`; `navigation-menu:select` `{ link, href }`.

Keyboard and focus:

- Enter, Space, or ArrowDown on a closed trigger opens it and focuses the first link in the panel; ArrowDown or Tab on an open trigger enters the panel; Home and End do nothing (the page scrolls), as in Base UI; Tab after its last link goes to the next trigger, Shift+Tab from its first link goes back and Shift+Tab from the next trigger goes to its last link (focus guards at both ends of the popup and after the open trigger, as in Base UI, so this also works in Safari, where Tab skips links; Tab from the last trigger leaves the menu); arrows move between links; Escape closes and focuses the open trigger, also when a hover switch moved the open panel.

```html
<nav data-slot="navigation-menu" aria-label="Main">
  <ul data-slot="navigation-menu-list">
    <li data-slot="navigation-menu-item">
      <button type="button" data-slot="navigation-menu-trigger">Getting started</button>
      <div data-slot="navigation-menu-content">
        <ul>
          <li><a data-slot="navigation-menu-link" href="/docs">Introduction</a></li>
          <li><a data-slot="navigation-menu-link" href="/docs/installation">Installation</a></li>
        </ul>
      </div>
    </li>
    <li data-slot="navigation-menu-item">
      <a data-slot="navigation-menu-link" data-variant="trigger" href="/docs" data-active>Docs</a>
    </li>
  </ul>
</nav>
```

### Command (`command`)

Group `overlays`. Needs `core`, `forms`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/command/. Full text: https://github.com/bl4ko/clanker-ui#command

| Part | Write | State |
| --- | --- | --- |
| `command` (root) |  |  |
| `command-empty` |  |  |
| `command-group` | `data-heading` any |  |
| `command-group-heading` (kit adds) |  |  |
| `command-input` |  |  |
| `command-input-wrapper` (kit adds) |  |  |
| `command-item` | `data-disabled` any; `data-keywords` string; `data-value` any | `data-selected` |
| `command-list` |  |  |
| `command-separator` |  |  |
| `command-shortcut` |  |  |

Other options named in the docs: `data-loop` any; `data-should-filter` `false`, `true`.

Events: `command:select` `{ value, item }`.

Keyboard and focus:

- Typing filters, scores, and sorts; ArrowUp/Down, Home, End, Ctrl+N/J/P/K, Alt+arrows (next group), Meta+arrows (first/last), Enter.

```html
<div data-slot="command">
  <input data-slot="command-input" placeholder="Type a command or search...">
  <div data-slot="command-list">
    <div data-slot="command-empty">No results found.</div>
    <div data-slot="command-group" data-heading="Suggestions">
      <div data-slot="command-item"><svg data-lucide="calendar"></svg><span>Calendar</span></div>
      <div data-slot="command-item" data-keywords="emoji, smiley"><svg data-lucide="smile"></svg><span>Search Emoji</span></div>
      <div data-slot="command-item" data-disabled><svg data-lucide="calculator"></svg><span>Calculator</span></div>
    </div>
    <div data-slot="command-separator"></div>
    <div data-slot="command-group" data-heading="Settings">
      <div data-slot="command-item" data-value="profile"><svg data-lucide="user"></svg><span>Profile</span><span data-slot="command-shortcut">⌘P</span></div>
    </div>
  </div>
</div>
```

### Toast (`toast`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/toast/. Full text: https://github.com/bl4ko/clanker-ui#toast-and-sonner

| Part | Write | State |
| --- | --- | --- |
| `toast` (root) (kit adds) |  | `data-ending-style`, `data-expanded`, `data-limited`, `data-starting-style`, `data-swipe-direction` |
| `toast-action` (kit adds) |  |  |
| `toast-close` (kit adds) |  |  |
| `toast-content` (kit adds) |  | `data-behind`, `data-expanded` |
| `toast-description` (kit adds) |  |  |
| `toast-icon` (kit adds) |  |  |
| `toast-portal` | `data-limit` number; `data-timeout` number |  |
| `toast-title` (kit adds) |  |  |
| `toast-viewport` (kit adds) |  |  |

Events: `toast:open` `{ id }`; `toast:close` `{ id, reason }`; `toast:action` `{ id }`.

Exports (import from the module that the page loads):

- `toast(message, options?) → id`: Sonner-style calls and the Base UI manager (`toast.add`, `toast.update`, `toast.close`), see [Toast and Sonner](https://github.com/bl4ko/clanker-ui#toast-and-sonner).

Keyboard and focus:

- F6 moves focus to the viewport; Tab and Shift+Tab past the toasts return focus to where it was.
- Escape closes the focused toast (not an open dialog), and focus moves to the next toast.

```html
<div data-slot="toast-portal" data-limit="3" data-timeout="5000"></div>
<button type="button" data-slot="button" data-variant="outline" id="show-toast">Show Toast</button>
```

```js
toast.add({ title: "Event created", description: "Sunday at 9:00", type: "success", timeout: 5000, priority: "low", actionProps: { children: "Undo", onClick() {} } })
toast.update(id, { description: "Saved" }); toast.update(id, prev => ({ title: `${prev.title}!` })); toast.close(id); toast.close()
toast("Event created", { description: "Sunday at 9:00", action: { label: "Undo", onClick() {} } })
toast.success(title, opts); toast.info(); toast.warning(); toast.error(); toast.loading(); toast.message()
toast.promise(promiseOrFn, { loading: "Creating event…", success: data => `${data.name} created.`, error: "Could not create event.", finally })
toast.dismiss(id); toast.dismiss(); toast.getToasts()
```

### Sonner (`sonner`)

Group `overlays`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/sonner/. Full text: https://github.com/bl4ko/clanker-ui#toast-and-sonner

Same component as `toast`: use its markup, events, and API.

| Part | Write | State |
| --- | --- | --- |
| `sonner` (root) |  |  |

Other options named in the docs: `data-limit` any; `data-timeout` any.

Exports (import from the module that the page loads):

- `toast(message, options?) → id`: Sonner-style calls and the Base UI manager (`toast.add`, `toast.update`, `toast.close`), see [Toast and Sonner](https://github.com/bl4ko/clanker-ui#toast-and-sonner).

```html
<div data-slot="toast-portal" data-limit="3" data-timeout="5000"></div>
<button type="button" data-slot="button" data-variant="outline" id="show-toast">Show Toast</button>
```

```js
toast.add({ title: "Event created", description: "Sunday at 9:00", type: "success", timeout: 5000, priority: "low", actionProps: { children: "Undo", onClick() {} } })
toast.update(id, { description: "Saved" }); toast.update(id, prev => ({ title: `${prev.title}!` })); toast.close(id); toast.close()
toast("Event created", { description: "Sunday at 9:00", action: { label: "Undo", onClick() {} } })
toast.success(title, opts); toast.info(); toast.warning(); toast.error(); toast.loading(); toast.message()
toast.promise(promiseOrFn, { loading: "Creating event…", success: data => `${data.name} created.`, error: "Could not create event.", finally })
toast.dismiss(id); toast.dismiss(); toast.getToasts()
```

### Avatar (`avatar`)

Group `layout`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/avatar/. Full text: https://github.com/bl4ko/clanker-ui#avatar

| Part | Write | State |
| --- | --- | --- |
| `avatar` (root) | `data-size` `lg`, `sm` |  |
| `avatar-badge` |  |  |
| `avatar-fallback` |  |  |
| `avatar-group` |  |  |
| `avatar-group-count` |  |  |
| `avatar-image` |  |  |

Other options named in the docs: `data-status` `error`, `loaded`, `loading`.

Events: `avatar:change` `{ value }`.

```html
<span data-slot="avatar" data-size="sm">
  <img data-slot="avatar-image" src="..." alt="">
  <span data-slot="avatar-fallback">CN</span>
  <span data-slot="avatar-badge"></span>
</span>
```

### Accordion (`accordion`)

Group `layout`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/accordion/. Full text: https://github.com/bl4ko/clanker-ui#accordion

| Part | Write | State |
| --- | --- | --- |
| `accordion` (root) | `data-type` string |  |
| `accordion-content` |  | `data-closed`, `data-open`, `data-state` |
| `accordion-item` | `data-state` string; `data-value` string |  |
| `accordion-trigger` |  |  |
| `accordion-trigger-icon` (kit adds) |  |  |

Events: `accordion:change` `{ value }`.

Keyboard and focus:

- Keys: Enter and Space toggle; as in Base UI, the arrow keys do not move focus.
- Like Base UI, the trigger of a disabled item stays in the Tab order (`aria-disabled="true"`), and Enter, Space, or a click does not open it.

```html
<div data-slot="accordion" data-type="single">
  <div data-slot="accordion-item" data-value="shipping" data-state="open">
    <h3><button type="button" data-slot="accordion-trigger">What are your shipping options?</button></h3>
    <div data-slot="accordion-content"><div>Standard, express, and overnight.</div></div>
  </div>
  <div data-slot="accordion-item" data-value="returns">
    <h3><button type="button" data-slot="accordion-trigger">What is your return policy?</button></h3>
    <div data-slot="accordion-content" hidden="until-found"><div>Returns within 30 days.</div></div>
  </div>
</div>
```

### Collapsible (`collapsible`)

Group `layout`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/collapsible/. Full text: https://github.com/bl4ko/clanker-ui#collapsible

| Part | Write | State |
| --- | --- | --- |
| `collapsible` (root) | `data-state` string |  |
| `collapsible-content` |  |  |
| `collapsible-trigger` |  |  |

Part attributes: `data-collapsible-trigger` boolean.

Events: `collapsible:open`; `collapsible:close`.

```html
<details data-slot="collapsible">
  <summary data-slot="collapsible-trigger">Advanced settings</summary>
  <div data-slot="collapsible-content">...</div>
</details>
<div data-slot="collapsible" data-state="closed">
  <button type="button" data-slot="button" data-variant="ghost" data-size="icon-sm" data-collapsible-trigger>...</button>
  <div>Always visible</div>
  <div data-slot="collapsible-content" hidden>...</div>
</div>
```

### Tabs (`tabs`)

Group `layout`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/tabs/. Full text: https://github.com/bl4ko/clanker-ui#tabs

| Part | Write | State |
| --- | --- | --- |
| `tabs` (root) | `data-default-value` string; `data-orientation` `horizontal`, `vertical` |  |
| `tabs-content` | `data-value` string |  |
| `tabs-list` | `data-variant` `default`, `line` |  |
| `tabs-trigger` | `data-value` string | `data-active`, `data-state` |

Other options named in the docs: `data-activation` string.

Events: `tabs:change` `{ value }`.

Keyboard and focus:

- Manual activation as in Base UI: the arrow keys move focus, Enter, Space, or a click selects (`data-activation="automatic"` selects on focus), roving tabindex, arrows (RTL aware), Home, End; disabled tabs are skipped.
- Tab panels are focusable (`tabindex="0"`) and show the standard focus ring.
- A trigger that gets keyboard focus (arrow keys, Home, End, Tab) or a click also scrolls fully into view.
- The kit sets `tabindex="-1"` on a horizontal list that has no `tabindex`, so the list is not a Tab stop (Firefox stops on a scroll container).

```html
<div data-slot="tabs" data-default-value="account" data-orientation="horizontal">
  <div data-slot="tabs-list" data-variant="line">
    <button data-slot="tabs-trigger" data-value="account">Account</button>
  </div>
  <div data-slot="tabs-content" data-value="account">...</div>
</div>
```

### Breadcrumb (`breadcrumb`)

Group `layout`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/breadcrumb/. Full text: https://github.com/bl4ko/clanker-ui#breadcrumb

| Part | Write | State |
| --- | --- | --- |
| `breadcrumb` (root) |  |  |
| `breadcrumb-ellipsis` |  |  |
| `breadcrumb-item` |  |  |
| `breadcrumb-link` |  |  |
| `breadcrumb-list` |  |  |
| `breadcrumb-page` |  |  |
| `breadcrumb-separator` |  |  |

```html
<nav data-slot="breadcrumb">
  <ol data-slot="breadcrumb-list">
    <li data-slot="breadcrumb-item"><a data-slot="breadcrumb-link" href="/">Home</a></li>
    <li data-slot="breadcrumb-separator"></li>
    <li data-slot="breadcrumb-item"><span data-slot="breadcrumb-ellipsis"></span></li>
    <li data-slot="breadcrumb-item"><span data-slot="breadcrumb-page">Breadcrumb</span></li>
  </ol>
</nav>
```

### Pagination (`pagination`)

Group `layout`. Needs `core`. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/pagination/. Full text: https://github.com/bl4ko/clanker-ui#pagination

| Part | Write | State |
| --- | --- | --- |
| `pagination` (root) |  |  |
| `pagination-content` |  |  |
| `pagination-ellipsis` |  |  |
| `pagination-item` |  |  |
| `pagination-link` | `data-active` boolean; `data-pagination-next` boolean; `data-pagination-previous` boolean; `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |

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

### Scroll Area (`scroll-area`)

Group `layout`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/scroll-area/. Full text: https://github.com/bl4ko/clanker-ui#scroll-area

| Part | Write | State |
| --- | --- | --- |
| `scroll-area` (root) |  |  |
| `scroll-area-scrollbar` | `data-orientation` `horizontal`, `vertical` | `data-overflow` |
| `scroll-area-thumb` (kit adds) |  |  |
| `scroll-area-viewport` |  |  |

```html
<div data-slot="scroll-area">
  <div data-slot="scroll-area-viewport" aria-label="Tags">...</div>
  <div data-slot="scroll-area-scrollbar" data-orientation="horizontal"></div>
</div>
```

### Resizable (`resizable`)

Group `layout`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/resizable/. Full text: https://github.com/bl4ko/clanker-ui#resizable

| Part | Write | State |
| --- | --- | --- |
| `resizable-handle` | `data-with-handle` boolean |  |
| `resizable-panel` | `data-default-size` number; `data-max-size` number; `data-min-size` number |  |
| `resizable-panel-group` | `data-orientation` `horizontal`, `vertical` |  |

Other options named in the docs: `data-keyboard-step` any.

Events: `resizable:change` `{ value }`.

Keyboard and focus:

- The handle is a WAI-ARIA window splitter: drag it or use the arrow keys (`data-keyboard-step`, default 5), Home, and End.

```html
<div data-slot="resizable-panel-group" data-orientation="horizontal">
  <div data-slot="resizable-panel" data-default-size="25" data-min-size="15" data-max-size="60">...</div>
  <div data-slot="resizable-handle" data-with-handle></div>
  <div data-slot="resizable-panel">...</div>
</div>
```

### Sidebar (`sidebar`)

Group `layout`. Needs `core`, `overlays`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/sidebar/. Full text: https://github.com/bl4ko/clanker-ui#sidebar

| Part | Write | State |
| --- | --- | --- |
| `sidebar` (root) | `data-collapsible` `icon`, `none`, `offcanvas`; `data-side` `bottom`, `left`, `right`, `top`; `data-variant` `floating`, `inset`, `sidebar` | `data-ending-style`, `data-mobile`, `data-starting-style`, `data-state` |
| `sidebar-container` | `data-side` `left`, `right`; `data-variant` `floating`, `inset` |  |
| `sidebar-content` |  |  |
| `sidebar-footer` |  |  |
| `sidebar-gap` | `data-variant` `floating`, `inset` |  |
| `sidebar-group` |  |  |
| `sidebar-group-action` |  |  |
| `sidebar-group-content` |  |  |
| `sidebar-group-label` |  |  |
| `sidebar-header` |  |  |
| `sidebar-inner` |  |  |
| `sidebar-input` |  |  |
| `sidebar-inset` |  |  |
| `sidebar-menu` |  |  |
| `sidebar-menu-action` | `data-show-on-hover` any |  |
| `sidebar-menu-badge` |  |  |
| `sidebar-menu-button` | `data-active` `false`, `true`; `data-size` `default`, `lg`, `sm`; `data-tooltip` string; `data-variant` `default`, `outline` | `data-state` |
| `sidebar-menu-item` |  |  |
| `sidebar-menu-skeleton` | `data-show-icon` any |  |
| `sidebar-menu-sub` |  |  |
| `sidebar-menu-sub-button` | `data-size` `md`, `sm` | `data-active`, `data-state` |
| `sidebar-menu-sub-item` |  |  |
| `sidebar-rail` |  |  |
| `sidebar-separator` | `data-orientation` `horizontal`, `vertical` |  |
| `sidebar-trigger` |  |  |
| `sidebar-wrapper` |  |  |

Other options named in the docs: `data-mobile` string.

Events: `sidebar:open` `{ mobile }`; `sidebar:close` `{ mobile }`.

Keyboard and focus:

- Ctrl/⌘+B toggles the sidebar of the focused wrapper, else the first one.
- When Escape, a trigger, or Ctrl/⌘+B closes the sheet, focus goes back to the element that had focus when it opened (the trigger, when the trigger opened it).

```html
<div data-slot="sidebar-wrapper" id="app">
  <div data-slot="sidebar" data-side="left" data-variant="sidebar" data-collapsible="offcanvas">
    <div data-slot="sidebar-gap"></div>
    <div data-slot="sidebar-container">
      <div data-slot="sidebar-inner">
        <div data-slot="sidebar-header">...</div>
        <div data-slot="sidebar-content">
          <div data-slot="sidebar-group">
            <div data-slot="sidebar-group-label">Platform</div>
            <ul data-slot="sidebar-menu">
              <li data-slot="sidebar-menu-item">
                <a data-slot="sidebar-menu-button" data-active="true" data-tooltip="Home" href="/"><svg data-lucide="house"></svg><span>Home</span></a>
                <div data-slot="sidebar-menu-badge">24</div>
              </li>
            </ul>
          </div>
        </div>
        <div data-slot="sidebar-footer">...</div>
      </div>
      <button data-slot="sidebar-rail"></button>
    </div>
  </div>
  <main data-slot="sidebar-inset"><button data-slot="sidebar-trigger"></button>...</main>
</div>
```

### Carousel (`carousel`)

Group `layout`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/carousel/. Full text: https://github.com/bl4ko/clanker-ui#carousel

| Part | Write | State |
| --- | --- | --- |
| `carousel` (root) | `data-loop` boolean; `data-orientation` `horizontal`, `vertical` |  |
| `carousel-content` |  |  |
| `carousel-item` |  |  |
| `carousel-next` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `carousel-previous` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |

Events: `carousel:change` `{ value, count }`.

Keyboard and focus:

- The kit adds the carousel and slide roles, slide labels, the arrow icons, and disables a button at the end (`disabled`, `data-disabled`).
- Like shadcn, focus does not move when the focused button becomes disabled, so Tab continues to the other button.
- The buttons and the arrow keys (RTL aware) move one slide with duration 25 and friction 0.68 (about 750 ms; at once with reduced motion); a press during the motion changes its target.
- Tab into a slide jumps to it at once.

```html
<div data-slot="carousel" data-orientation="horizontal" data-align="start" data-loop aria-label="Featured">
  <div data-slot="carousel-content"><div>
    <div data-slot="carousel-item">...</div>
  </div></div>
  <button data-slot="carousel-previous"></button>
  <button data-slot="carousel-next"></button>
</div>
```

### Item (`item`)

Group `layout`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/item/. Full text: https://github.com/bl4ko/clanker-ui#alert-aspect-ratio-badge-card-empty-item-separator-skeleton

| Part | Write | State |
| --- | --- | --- |
| `item` (root) | `data-size` `default`, `sm`, `xs`; `data-variant` `default`, `muted`, `outline` |  |
| `item-actions` |  |  |
| `item-content` |  |  |
| `item-description` |  |  |
| `item-footer` |  |  |
| `item-group` |  |  |
| `item-header` |  |  |
| `item-media` | `data-variant` `default`, `icon`, `image` |  |
| `item-separator` | `data-orientation` `horizontal`, `vertical` |  |
| `item-title` |  |  |

```html
<div data-slot="item-group" role="list">
  <div data-slot="item" data-variant="outline" role="listitem">
    <div data-slot="item-media" data-variant="icon"><svg data-lucide="badge-check"></svg></div>
    <div data-slot="item-content">
      <div data-slot="item-title">Basic Item</div>
      <p data-slot="item-description">A simple item with title and description.</p>
    </div>
    <div data-slot="item-actions"><button type="button" data-slot="button" data-variant="outline" data-size="sm">Action</button></div>
  </div>
  <div data-slot="item-separator"></div>
  <a data-slot="item" data-size="sm" href="/profile" role="listitem">
    <div data-slot="item-content"><div data-slot="item-title">Your profile has been verified.</div></div>
  </a>
</div>
```

### Message (`message`)

Group `chat`. Needs `core`. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/message/. Full text: https://github.com/bl4ko/clanker-ui#message-bubble-marker

| Part | Write | State |
| --- | --- | --- |
| `message` (root) | `data-align` `end` |  |
| `message-avatar` |  |  |
| `message-content` |  |  |
| `message-footer` |  |  |
| `message-group` |  |  |
| `message-header` |  |  |

```html
<div data-slot="message" data-align="end">
  <div data-slot="message-avatar"><span data-slot="avatar"><img data-slot="avatar-image" src="me.png" alt="@me"><span data-slot="avatar-fallback">ME</span></span></div>
  <div data-slot="message-content">
    <div data-slot="message-header">Olivia</div>
    <div data-slot="bubble" data-variant="muted"><div data-slot="bubble-content">Deploying to prod.</div></div>
    <div data-slot="message-footer">Delivered</div>
  </div>
</div>
```

### Bubble (`bubble`)

Group `chat`. Needs `core`. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/bubble/. Full text: https://github.com/bl4ko/clanker-ui#message-bubble-marker

| Part | Write | State |
| --- | --- | --- |
| `bubble` (root) | `data-align` `end`; `data-variant` `ghost`, `muted` |  |
| `bubble-content` |  |  |
| `bubble-group` |  |  |
| `bubble-reactions` | `data-align` `end`, `start`; `data-side` `bottom`, `top` |  |

```html
<div data-slot="message" data-align="end">
  <div data-slot="message-avatar"><span data-slot="avatar"><img data-slot="avatar-image" src="me.png" alt="@me"><span data-slot="avatar-fallback">ME</span></span></div>
  <div data-slot="message-content">
    <div data-slot="message-header">Olivia</div>
    <div data-slot="bubble" data-variant="muted"><div data-slot="bubble-content">Deploying to prod.</div></div>
    <div data-slot="message-footer">Delivered</div>
  </div>
</div>
```

### Attachment (`attachment`)

Group `chat`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/attachment/. Full text: https://github.com/bl4ko/clanker-ui#attachment

| Part | Write | State |
| --- | --- | --- |
| `attachment` (root) | `data-orientation` `horizontal`, `vertical`; `data-size` `default`, `sm`, `xs`; `data-state` string |  |
| `attachment-action` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `attachment-actions` |  |  |
| `attachment-content` |  |  |
| `attachment-description` |  |  |
| `attachment-group` |  |  |
| `attachment-media` | `data-variant` `image` |  |
| `attachment-title` |  |  |
| `attachment-trigger` |  |  |

```html
<div data-slot="attachment" data-state="uploading" data-size="sm" data-orientation="vertical">
  <div data-slot="attachment-media" data-variant="image"><img src="a.png" alt="A"></div>
  <div data-slot="attachment-content">
    <span data-slot="attachment-title">a.png</span>
    <span data-slot="attachment-description">PNG · 820 KB</span>
  </div>
  <div data-slot="attachment-actions"><button data-slot="attachment-action" aria-label="Remove a.png"><svg data-lucide="x"></svg></button></div>
  <a data-slot="attachment-trigger" href="a.png" aria-label="Open a.png"></a>
</div>
```

### Message Scroller (`message-scroller`)

Group `chat`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/message-scroller/. Full text: https://github.com/bl4ko/clanker-ui#message-scroller

| Part | Write | State |
| --- | --- | --- |
| `message-scroller` (root) | `data-auto-scroll` boolean; `data-default-scroll-position` `end`, `last-anchor`, `start` |  |
| `message-scroller-button` | `data-direction` string; `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `destructive`, `ghost`, `link`, `outline`, `secondary` | `data-active` |
| `message-scroller-content` |  |  |
| `message-scroller-item` | `data-message-id` string; `data-scroll-anchor` `false`, `true` |  |
| `message-scroller-viewport` |  | `data-autoscrolling`, `data-pending-scroll` |

Part attributes: `data-message-scroller-spacer` boolean.

Other options named in the docs: `data-active` `false`, `true`; `data-scroll-edge-threshold` any; `data-scroll-margin` any; `data-scroll-previous-item-peek` any.

Events: `message-scroller:scrollable` `{ start, end }`.

Exports (import from the module that the page loads):

- `messageScrollerScrollToEnd(el, { behavior }?) → boolean`
- `messageScrollerScrollToStart(el, { behavior }?) → boolean`
- `messageScrollerScrollToMessage(el, id, { align, behavior, scrollMargin }?) → boolean`: Waits for the row if the list is still empty.
- `messageScrollerScrollable(el) → { start, end }`
- `messageScrollerVisibility(el) → { currentAnchorId, visibleMessageIds }`

Keyboard and focus:

- Only upward intent releases following: wheel up, a touch drag down, and ArrowUp, PageUp, Home, or Shift+Space on the viewport itself (keys in an input inside the log never release it); downward input keeps following.

```html
<div data-slot="message-scroller" data-auto-scroll data-default-scroll-position="end">
  <div data-slot="message-scroller-viewport">
    <div data-slot="message-scroller-content">
      <div data-slot="message-scroller-item" data-message-id="u1" data-scroll-anchor="true">…</div>
    </div>
  </div>
  <button data-slot="message-scroller-button" data-direction="end"></button>
</div>
```

### Trace (`trace`)

Group `chat`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/trace/. Full text: https://github.com/bl4ko/clanker-ui#trace

| Part | Write | State |
| --- | --- | --- |
| `trace` (root) |  |  |
| `trace-collapsible` | `data-default-open` boolean |  |
| `trace-collapsible-content` |  | `data-ending-style`, `data-starting-style` |
| `trace-collapsible-content-inner` (kit adds) |  |  |
| `trace-collapsible-trigger` |  |  |
| `trace-description` |  |  |
| `trace-icon` |  |  |
| `trace-line` | `data-status` `error`, `pending`, `running` |  |
| `trace-title` |  |  |

Events: `trace:open`; `trace:close`.

Exports (import from the module that the page loads):

- `traceOpen(target, { animate = true }?) → boolean`: `target` is a `trace-collapsible` or an element in it.
- `traceClose(target, { animate = true }?) → boolean`

```html
<div data-slot="trace">
  <span data-slot="trace-line" data-status="running">
    <span data-slot="trace-icon"><svg data-lucide="terminal"></svg></span>
    <span data-slot="trace-title">Running pnpm build</span>
    <span data-slot="trace-description">14s</span>
  </span>
  <div data-slot="trace-collapsible" data-default-open>
    <button data-slot="trace-collapsible-trigger"><span data-slot="trace-line">…</span></button>
    <div data-slot="trace-collapsible-content">Detail</div>
  </div>
</div>
```

### Marker (`marker`)

Group `chat`. Needs `core`. CSS only. Docs: https://bl4ko.github.io/clanker-ui/docs/components/marker/. Full text: https://github.com/bl4ko/clanker-ui#message-bubble-marker

| Part | Write | State |
| --- | --- | --- |
| `marker` (root) | `data-variant` `border`, `separator` |  |
| `marker-content` |  |  |
| `marker-icon` |  |  |

```html
<div data-slot="marker" role="status">
  <span data-slot="marker-icon"><svg data-lucide="git-branch"></svg></span>
  <span data-slot="marker-content">Switched to a new branch</span>
</div>
<div data-slot="marker" data-variant="separator">
  <span data-slot="marker-content">Conversation compacted</span>
</div>
```

### Questionnaire (`questionnaire`)

Group `chat`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/questionnaire/. Full text: https://github.com/bl4ko/clanker-ui#questionnaire

| Part | Write | State |
| --- | --- | --- |
| `questionnaire` (root) | `data-default-item` string; `data-shortcuts` `letters`, `numbers` |  |
| `questionnaire-actions` |  |  |
| `questionnaire-choice` | `data-default-checked` boolean; `data-value` string | `data-checked`, `data-disabled`, `data-invalid`, `data-state` |
| `questionnaire-choice-description` |  |  |
| `questionnaire-choice-indicator` (kit adds) |  |  |
| `questionnaire-choice-indicator-check` (kit adds) |  |  |
| `questionnaire-choice-indicator-dot` (kit adds) |  |  |
| `questionnaire-choice-input` (kit adds) |  |  |
| `questionnaire-choice-label` (kit adds) |  |  |
| `questionnaire-choice-shortcut` (kit adds) |  |  |
| `questionnaire-choices` |  |  |
| `questionnaire-description` |  |  |
| `questionnaire-error` |  |  |
| `questionnaire-input` |  |  |
| `questionnaire-input-wrapper` (kit adds) |  |  |
| `questionnaire-item` | `data-multiple` boolean; `data-required` boolean |  |
| `questionnaire-next` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `questionnaire-previous` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `questionnaire-progress` | `data-template` string |  |
| `questionnaire-skip` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `questionnaire-submit` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `questionnaire-title` |  |  |

Events: `questionnaire:change` `{ value, index, total }`; `questionnaire:status` `{ item, value }`; `questionnaire:submit` `{ value, status }`.

Exports (import from the module that the page loads):

- `questionnaireGoTo(el, name) → boolean`
- `questionnaireRefresh(el)`: Call after you enable or disable an item.

Keyboard and focus:

- Keys: letters or numbers pick, Up and Down move, Left and Right change the item, Enter continues, Ctrl or Cmd+Enter continues from anywhere.
- A text answer can be `<input data-slot="questionnaire-input">` or `<textarea data-slot="questionnaire-input">` (Enter inserts a newline; Ctrl or Cmd+Enter continues).

```html
<form data-slot="questionnaire" data-shortcuts="letters" data-default-item="direction">
  <div data-slot="questionnaire-progress" data-template="Step {current} of {total}"></div>
  <fieldset data-slot="questionnaire-item" name="direction" data-required data-multiple>
    <legend data-slot="questionnaire-title">Question</legend>
    <p data-slot="questionnaire-description">Help text</p>
    <div data-slot="questionnaire-choices">
      <label data-slot="questionnaire-choice" data-value="a" data-default-checked>Label<span data-slot="questionnaire-choice-description">More</span></label>
      <input data-slot="questionnaire-input" aria-label="Other answer">
    </div>
    <p data-slot="questionnaire-error"></p>
  </fieldset>
  <div data-slot="questionnaire-actions">
    <button data-slot="questionnaire-previous"></button><button data-slot="questionnaire-skip"></button>
    <button data-slot="questionnaire-next"></button><button data-slot="questionnaire-submit"></button>
  </div>
</form>
```

### Code Block (`code-block`)

Group `chat`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/code-block/. Full text: https://github.com/bl4ko/clanker-ui#code-block

| Part | Write | State |
| --- | --- | --- |
| `code-block` (root) | `data-size` `sm`; `data-variant` `default`, `destructive` |  |
| `code-block-actions` |  |  |
| `code-block-code` |  |  |
| `code-block-content` | `data-numbered` `false`, `true`; `data-start-line` number; `data-wrap` `false`, `true` |  |
| `code-block-copy-button` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `code-block-footer` |  |  |
| `code-block-header` |  |  |
| `code-block-line` | `data-variant` `added`, `highlighted`, `removed` |  |
| `code-block-line-content` (kit adds) |  |  |
| `code-block-title` |  |  |
| `code-block-wrap-button` |  |  |

Other options named in the docs: `data-timeout` any.

Events: `code-block:copy` `{ value }`; `code-block:wrap` `{ value }`.

```html
<div data-slot="code-block" data-size="sm" data-variant="destructive">
  <div data-slot="code-block-header">
    <div data-slot="code-block-title"><svg data-lucide="file-text"></svg>app.ts</div>
    <div data-slot="code-block-actions">
      <button data-slot="code-block-wrap-button" aria-label="Wrap lines"><svg data-lucide="text-wrap"></svg></button>
      <button data-slot="code-block-copy-button"></button>
    </div>
  </div>
  <pre data-slot="code-block-content" data-numbered="true" data-start-line="14" data-wrap="true"><code data-slot="code-block-code">code</code></pre>
</div>
```

### Calendar (`calendar`)

Group `chat`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/calendar/. Full text: https://github.com/bl4ko/clanker-ui#calendar

| Part | Write | State |
| --- | --- | --- |
| `calendar` (root) | `data-button-variant` any; `data-caption-layout` any; `data-disabled` any; `data-disabled-dates` any; `data-disabled-weekdays` any; `data-fixed-weeks` any; `data-label-next` any; `data-label-previous` any; `data-lang` any; `data-max` any; `data-min` any; `data-mode` `multiple`, `range`, `single`; `data-month` any; `data-months` any; `data-name` string; `data-outside-days` `false`, `true`; `data-required` any; `data-show-week-number` any; `data-today` any; `data-value` string; `data-week-start` any |  |
| `calendar-button-next` (kit adds) |  |  |
| `calendar-button-previous` (kit adds) |  |  |
| `calendar-caption-label` (kit adds) |  |  |
| `calendar-day` |  | `data-disabled`, `data-hidden`, `data-outside`, `data-range-end`, `data-range-middle`, `data-range-start`, `data-selected`, `data-today` |
| `calendar-dropdown` (kit adds) |  |  |
| `calendar-dropdown-root` (kit adds) |  |  |
| `calendar-dropdowns` (kit adds) |  |  |
| `calendar-month` (kit adds) |  |  |
| `calendar-month-caption` (kit adds) |  |  |
| `calendar-month-grid` (kit adds) |  |  |
| `calendar-months` (kit adds) |  |  |
| `calendar-nav` (kit adds) |  |  |
| `calendar-week` (kit adds) |  |  |
| `calendar-week-number` (kit adds) |  |  |
| `calendar-week-number-header` (kit adds) |  |  |
| `calendar-weekday` (kit adds) |  |  |
| `calendar-weekdays` (kit adds) |  |  |
| `calendar-weeks` (kit adds) |  |  |

Other options named in the docs: `data-day` any; `data-hidden` `false`, `true`.

Events: `calendar:change` `{ value, mode, source }`; `calendar:navigate` `{ value }`.

Exports (import from the module that the page loads):

- `calendarGetValue(el) → value`: `"2026-10-28"`, an array (`multiple`), `{ from, to }` (`range`), or `null`.
- `calendarSetValue(el, value, { emit = false, month = true }?) → boolean`: `month` shows the month of the first selected date.
- `calendarSetMonth(el, "2026-10") → boolean`

Keyboard and focus:

- Keyboard (APG date grid): arrows by day or week, Home and End to the week ends, PageUp and PageDown by month, Shift+PageUp and Shift+PageDown by year.

```html
<div data-slot="calendar" data-mode="single" data-value="2026-10-28" data-month="2026-10" data-name="date" data-min="2026-10-01" data-disabled-weekdays="0 6"></div>
```

### Date Picker (`date-picker`)

Group `chat`. Needs `core`, `overlays`, `forms`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/date-picker/. Full text: https://github.com/bl4ko/clanker-ui#date-picker

| Part | Write | State |
| --- | --- | --- |
| `date-picker` (root) | `data-format` string; `data-placeholder` string |  |
| `date-picker-value` |  |  |

Part attributes: `data-date-picker-content` boolean; `data-date-picker-input` boolean; `data-date-picker-preset` boolean; `data-date-picker-trigger` boolean.

Other options named in the docs: `data-keep-open` any.

Events: `date-picker:open`; `date-picker:close`.

Exports (import from the module that the page loads):

- `datePickerOpen(target) → boolean`
- `datePickerClose(target, { restoreFocus = true }?) → boolean`

Keyboard and focus:

- Focus moves to the first part in the popup that can take focus (the previous-month button, or the next-month button when the previous one is disabled), as the Base UI popover does; Tab moves to the next-month button, then to the selected day or today.
- Escape, an outside click, or focus leaving closes it; a single date selection closes it unless `data-keep-open`.
- `data-date-picker-input` on an input (for example in an `input-group`, with an icon button as the trigger) shows the date, parses typed dates on `change`, and opens the popup on ArrowDown.

```html
<div data-slot="date-picker" data-placeholder="Pick a date" data-format="long">
  <button type="button" data-slot="button" data-variant="outline" data-date-picker-trigger><svg data-lucide="calendar"></svg><span data-slot="date-picker-value"></span></button>
  <div data-slot="popover-content" data-date-picker-content data-align="start" aria-label="Choose date">
    <div data-slot="native-select-wrapper">
      <select data-slot="native-select" data-date-picker-preset aria-label="Presets"><option value="">Select</option><option value="1">Tomorrow</option></select>
      <svg data-lucide="chevron-down" data-slot="native-select-icon"></svg>
    </div>
    <div data-slot="calendar" data-name="due"></div>
  </div>
</div>
```

### Chart (`chart`)

Group `chart`. Needs `core`. CSS and JS. Docs: https://bl4ko.github.io/clanker-ui/docs/components/chart/. Full text: https://github.com/bl4ko/clanker-ui#chart

| Part | Write | State |
| --- | --- | --- |
| `chart` (root) |  | `data-sparkline` |
| `chart-footer` (kit adds) |  |  |
| `chart-legend` (kit adds) |  |  |
| `chart-legend-indicator` (kit adds) |  | `data-shape` |
| `chart-legend-item` (kit adds) |  |  |
| `chart-legend-label` (kit adds) |  |  |
| `chart-live` (kit adds) |  |  |
| `chart-plot` (kit adds) |  |  |
| `chart-probe` (kit adds) |  |  |
| `chart-stat` |  |  |
| `chart-stat-change` (kit adds) |  |  |
| `chart-stat-delta` (kit adds) | `data-direction` any; `data-tone` any |  |
| `chart-stat-description` (kit adds) |  |  |
| `chart-stat-header` (kit adds) |  |  |
| `chart-stat-label` (kit adds) |  |  |
| `chart-stat-period` (kit adds) |  |  |
| `chart-stat-trend` (kit adds) |  |  |
| `chart-stat-value` (kit adds) |  |  |
| `chart-svg` (kit adds) |  |  |
| `chart-table` (kit adds) |  |  |
| `chart-table-toggle` (kit adds) |  |  |
| `chart-tooltip` (kit adds) |  |  |
| `chart-tooltip-extra` (kit adds) |  |  |
| `chart-tooltip-indicator` (kit adds) |  |  |
| `chart-tooltip-item` (kit adds) |  | `data-total` |
| `chart-tooltip-items` (kit adds) |  |  |
| `chart-tooltip-label` (kit adds) |  |  |
| `chart-tooltip-name` (kit adds) |  |  |
| `chart-tooltip-value` (kit adds) |  |  |

Other options named in the docs: `data-part` any.

Events: `chart:active` `{ index, key, row }`; `chart:legend` `{ key, visible, hidden }`; `chart:view` `{ view }`.

Exports (import from the module that the page loads):

- `chart(element, data, options) → { update(data, options), destroy() }`: In `clanker-ui-chart.js`, see [Chart](https://github.com/bl4ko/clanker-ui#chart).
- `sparkline(element, values, options?) → { update, destroy }`
- `statTile(element, options) → { update(options), destroy() }`

Keyboard and focus:

- Keys that are not in `config` follow in data order.
- The SVG is `role="application"` with `tabindex="0"`, so screen readers pass the arrow keys to it.
- Keyboard: arrows move between points, Home, End, Escape.

```html
<div id="visitors"></div>
<div id="revenue-tile"></div>
```

```js
import { chart, sparkline, statTile } from "./clanker-ui-chart.js"

const view = chart(document.getElementById("visitors"), {
  rows: [{ month: "January", desktop: 186, mobile: 80 }, { month: "February", desktop: 305, mobile: 200 }],
  config: { desktop: { label: "Desktop", icon: "monitor" }, mobile: { label: "Mobile" } },
}, { type: "bar", x: "month", label: "Visitors, 2024" })
view.update({ rows: next }, { stack: true })
view.destroy()

statTile(el, { label: "Total revenue", value: 1250, format: { style: "currency", currency: "USD" }, delta: 0.125, period: "vs last month", trend: [820, 940, 1250] })
sparkline(el, [980, 1020, 1284], { area: true, label: "Requests per minute" })
```
