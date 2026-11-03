# Questionnaire (`questionnaire`)

Group `chat`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `questionnaire` (root) | `data-default-item` string; `data-shortcuts` `letters`, `numbers` |  |
| `questionnaire-choice` | `data-default-checked` boolean; `data-value` string | `data-checked`, `data-disabled`, `data-invalid`, `data-state` |
| `questionnaire-next` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `questionnaire-previous` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `questionnaire-progress` | `data-template` string |  |
| `questionnaire-skip` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |
| `questionnaire-submit` | `data-size` `default`, `icon`, `icon-lg`, `icon-sm`, `icon-xs`, `lg`, `sm`, `xs`; `data-variant` `default`, `destructive`, `ghost`, `link`, `outline`, `secondary` |  |

Other parts: `questionnaire-actions`, `questionnaire-choice-description`, `questionnaire-choices`, `questionnaire-description`, `questionnaire-error`, `questionnaire-input`, `questionnaire-item`, `questionnaire-title`.

Kit adds: `questionnaire-choice-indicator`, `questionnaire-choice-indicator-check`, `questionnaire-choice-indicator-dot`, `questionnaire-choice-input`, `questionnaire-choice-label`, `questionnaire-choice-shortcut`, `questionnaire-input-wrapper`.

Events: `questionnaire:change` `{ value, index, total }`; `questionnaire:status` `{ item, value }`; `questionnaire:submit` `{ value, status }`.

Exports (readable set: `clanker-ui.js`; `.min` set: `clanker-ui.min.js` or `clanker-ui-chat.min.js`):

- `questionnaireGoTo(el, name) → boolean`
- `questionnaireRefresh(el)`: Call after you enable or disable an item.

## Full text

### Questionnaire

```html
<form data-slot="questionnaire" data-shortcuts="letters|numbers" data-default-item="direction">
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

One item at a time. The kit builds the native radio or checkbox, the indicator, and the shortcut hint (the input, the choice, and the hint carry `data-type`, `data-shortcut`, `data-checked` or `data-unchecked`; a required single-choice radio is `required` until a text answer is given; the action buttons default to `data-variant` `outline` (previous, skip) or `default` (next, submit) and `data-size="default"`), validates before Next and Submit, and fills the progress text and error message. Keys: letters or numbers pick, Up and Down move, Left and Right change the item, Enter continues, Ctrl or Cmd+Enter continues from anywhere. Skipped items are left out of the form data.

- A text answer can be `<input data-slot="questionnaire-input">` or `<textarea data-slot="questionnaire-input">` (Enter inserts a newline; Ctrl or Cmd+Enter continues). Text answers use the input and textarea styles. A selected text answer must pass native constraint validation (`type="email"`, `pattern`, `minlength`, ...); the automatic error then shows the browser's `validationMessage`. Text answers stay in the form (no `form=""`); an unselected text answer has no `name`.
