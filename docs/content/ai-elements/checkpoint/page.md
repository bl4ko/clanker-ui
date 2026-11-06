---
title: Checkpoint
description: Marks a point in the conversation you can return to.
---

{{example "checkpoint-demo" height="auto"}}

Checkpoint is a point in the conversation you can return to. It is a [Marker](/docs/components/marker) after a turn, with a Restore button. Restore keeps that turn and drops every message after it.

## Installation

Checkpoint is built with the [Marker](/docs/components/marker) and [Button](/docs/components/button) components. Load the `chat` group, or the one-file set.

## Usage

Render a marker after the turn, with a button that restores it.

```html
<div data-slot="marker" data-variant="separator">
  <span data-slot="marker-content" class="inline-flex items-center gap-2">
    Button renamed
    <button type="button" data-slot="button" data-variant="outline" data-size="xs" aria-label="Restore to Button renamed">Restore</button>
  </span>
</div>
```

See [Marker](/docs/components/marker).

## From code

Restore replaces the thread with the messages up to and including that turn. Every later turn is removed. Send a new message to continue from there. The last turn has nothing to restore, so its marker has no button.

```js
restore.addEventListener("click", () => {
  while (marker.nextElementSibling) marker.nextElementSibling.remove()
  restore.remove()
  history = history.slice(0, history.findIndex(message => message.id === turnId) + 1)
})
```

Keep the checkpoint with the agent's turn on your server, with the id of that turn, so a reload shows the same markers.

## API Reference

See [Marker](/docs/components/marker#api-reference) and [Button](/docs/components/button#api-reference).
