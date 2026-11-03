# Kbd (`kbd`)

Group `core`. Needs none. CSS only.

Other parts: `kbd` (root), `kbd-group`.

## Full text

### Input, Textarea, Label, Kbd

```html
<input data-slot="input" type="email" placeholder="Email">
<textarea data-slot="textarea"></textarea>
<label data-slot="label" for="email">Email</label>
<kbd data-slot="kbd-group"><kbd data-slot="kbd">Ctrl</kbd><kbd data-slot="kbd">K</kbd></kbd>
```

`aria-invalid="true"` shows the error border. A label after a `:disabled` control is dimmed. A `kbd` inside `tooltip-content` uses the inverted tooltip colors. CSS only.
