# Textarea (`textarea`)

Group `core`. Needs none. CSS only.

Other parts: `textarea` (root).

## Full text

### Input, Textarea, Label, Kbd

```html
<input data-slot="input" type="email" placeholder="Email">
<textarea data-slot="textarea"></textarea>
<label data-slot="label" for="email">Email</label>
<kbd data-slot="kbd-group"><kbd data-slot="kbd">Ctrl</kbd><kbd data-slot="kbd">K</kbd></kbd>
```

```js
const zone = document.querySelector(".dropzone")
const input = zone.querySelector("input")
zone.addEventListener("dragover", event => { event.preventDefault(); zone.dataset.dragging = "" })
zone.addEventListener("dragleave", () => delete zone.dataset.dragging)
zone.addEventListener("drop", event => {
  event.preventDefault()
  delete zone.dataset.dragging
  input.files = event.dataTransfer.files
  input.dispatchEvent(new Event("change", { bubbles: true }))
})
```
