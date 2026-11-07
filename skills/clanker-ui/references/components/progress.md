# Progress (`progress`)

Group `core`. Needs none. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `progress` (root) | `data-max` number; `data-value` number |  |

Other parts: `progress-label`, `progress-value`.

Kit adds: `progress-indicator`, `progress-track`.

```html
<div data-slot="progress" data-value="60" data-max="100" aria-label="Upload">
  <span data-slot="progress-label">Upload</span>
  <span data-slot="progress-value"></span>
</div>
```

## Full text

### Progress, Spinner

- `<div data-slot="progress" data-value="60" data-max="100" aria-label="Upload"></div>`: the kit adds the Base UI parts `progress-track` > `progress-indicator` (width in percent), `role="progressbar"`, `aria-valuenow`, `aria-valuetext`, `data-state="loading|complete|indeterminate"`, and `data-progressing`, `data-complete`, or `data-indeterminate` on every part. Optional `progress-label` (it labels the bar) and `progress-value` (the kit writes the percent) go before the track. The percent in `progress-value` and `aria-valuetext` is `Intl.NumberFormat` with `style: "percent"` in the language of the nearest `lang` attribute, like Base UI `Progress.Value`. The digits follow the browser locale data: `lang="ar-u-nu-arab"` gives Arabic-Indic digits (`٥٦٪؜`) in every browser. Change `data-value` to update it. At 0 and when indeterminate, the indicator has no width.
