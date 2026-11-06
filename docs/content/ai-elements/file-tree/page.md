---
title: File Tree
description: The files the agent changed, as a folder tree.
---

{{example "file-tree-demo" height="auto"}}

File Tree is the files the agent changed, shown as folders you can open. A folder is a [Collapsible](/docs/components/collapsible). A file is a [Button](/docs/components/button). For a single file the agent read or edited, use a [Trace](/docs/components/trace) line instead.

## Installation

File Tree is built with the [Collapsible](/docs/components/collapsible) and [Button](/docs/components/button) components. Load the `layout` group, or the one-file set.

## Usage

Nest each folder's children in its `collapsible-content`. The trigger is a ghost button with `data-collapsible-trigger`; the kit sets `aria-expanded` on it, and the chevron turns when the folder is open.

```html
<div data-slot="collapsible" data-state="open">
  <button type="button" data-slot="button" data-variant="ghost" data-size="sm" class="w-full justify-start" data-collapsible-trigger>
    <svg data-lucide="chevron-right" class="transition-transform group-aria-expanded:rotate-90"></svg>
    <svg data-lucide="folder"></svg>
    components
  </button>
  <div data-slot="collapsible-content">
    <div class="ms-4 flex flex-col">
      <button type="button" data-slot="button" data-variant="ghost" data-size="sm" class="w-full justify-start"><svg data-lucide="file"></svg>login-form.tsx</button>
    </div>
  </div>
</div>
```

The kit has no rule for the chevron. Turn it in `app.css`:

```css title="app.css"
[aria-expanded="true"] > .group-aria-expanded\:rotate-90 {
  rotate: 90deg;
}
```

Mark the selected file with `aria-current="true"` and the accent background:

```js
tree.addEventListener("click", event => {
  const file = event.target.closest('[data-slot="button"]:not([data-collapsible-trigger])')
  if (!file) return
  tree.querySelector('[aria-current="true"]')?.removeAttribute("aria-current")
  file.setAttribute("aria-current", "true")
})
```

See [Collapsible](/docs/components/collapsible#details-element-and-file-tree).
