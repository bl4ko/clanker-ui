# Input (`input`)

Group `core`. Needs none. CSS only.

| Part | Write | State |
| --- | --- | --- |
| `input` (root) | `accept` string; `data-error-value-missing` string |  |

## Full text

### Input, Textarea, Label, Kbd

```html
<input data-slot="input" type="email" placeholder="Email">
<textarea data-slot="textarea"></textarea>
<label data-slot="label" for="email">Email</label>
<kbd data-slot="kbd-group"><kbd data-slot="kbd">Ctrl</kbd><kbd data-slot="kbd">K</kbd></kbd>
```

File upload: `<input data-slot="input" type="file" accept="image/*,application/pdf" name="receipt">` is the shadcn file input (the button is plain `text-sm` text with no border). shadcn has no dropzone component. A dropzone is a `<label>` with the outline `empty` style around a visually hidden file input, and a few lines of app code for drag and drop; show the chosen file with an `attachment` (it works outside a chat). A `label` holds only phrasing content, so the `empty` parts are `span`s:

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

App CSS: `.dropzone { cursor: pointer }`, a focus ring with `.dropzone:has(input:focus-visible) { outline: 2px solid var(--ring); outline-offset: 2px }`, and `.dropzone[data-dragging] { border-color: var(--primary) }`. A `required` file input in a `data-slot="form"` gets the `field-error` of its field. On `change` with a file, set `hidden` on the zone's header and show an `attachment` with the file name, size, and a remove button (`attachment-action`) in the same field; the remove button clears `input.value`, removes the attachment, and shows the header again. Keep the input in the label, so the field still validates.
