---
title: Prompt Input
description: A message field with attachments and a send button.
---

{{example "prompt-input-demo" height="auto"}}

Prompt Input is the field the person types into to message the agent. It is an [Input Group](/docs/components/input-group) with a textarea, an attach button, the [Model Selector](/docs/ai-elements/model-selector) menus and a send button. Attached files show as [Attachment](/docs/components/attachment) chips above the text.

## Installation

Prompt Input is built with the [Input Group](/docs/components/input-group), [Attachment](/docs/components/attachment) and [Dropdown Menu](/docs/components/dropdown-menu) components. Load the `forms`, `overlays`, and `chat` groups, or the one-file set.

## Usage

```html
<form id="prompt">
  <input type="file" multiple class="sr-only" tabindex="-1" aria-label="Attach files" id="files">
  <div data-slot="input-group">
    <textarea data-slot="input-group-control" placeholder="Ask the agent to change your code..." aria-label="Message"></textarea>
    <div data-slot="input-group-addon" data-align="block-end">
      <button type="button" data-slot="button" data-input-group-button data-variant="outline" data-size="icon-sm" aria-label="Attach files" id="attach"><svg data-lucide="plus"></svg></button>
      <button type="submit" data-slot="button" data-input-group-button data-variant="default" data-size="icon-sm" class="ms-auto" aria-label="Send" disabled><svg data-lucide="arrow-up"></svg></button>
    </div>
  </div>
</form>
```

Enable the send button when the field has text. In the Nova style, an input group with a disabled control is shown at 50 % opacity (shadcn/ui `has-disabled:opacity-50`), so the field looks dimmed until the person types.

```js
text.addEventListener("input", () => {
  send.disabled = text.value.trim() === ""
})
```

## Attachments

The attach button opens the hidden file input. Show each file as an [Attachment](/docs/components/attachment) in an addon with `data-align="block-start"`, with a button to remove it.

```js
attach.addEventListener("click", () => files.click())

files.addEventListener("change", () => {
  for (const file of files.files) {
    const item = h("div", { "data-slot": "attachment", "data-size": "sm" },
      h("div", { "data-slot": "attachment-media" }, icon("file-text")),
      h("div", { "data-slot": "attachment-content" }, h("span", { "data-slot": "attachment-title" }, file.name)),
      h("div", { "data-slot": "attachment-actions" },
        h("button", { type: "button", "data-slot": "attachment-action", "aria-label": `Remove ${file.name}`, onclick: () => item.remove() }, icon("x"))))
    list.append(item)
  }
  files.value = ""
})
```

## Model and Effort

Put the two [Model Selector](/docs/ai-elements/model-selector) menus in the `block-end` addon, between the attach and send buttons. Move `ms-auto` from the send button to the first menu trigger, so both menus sit next to the send button.

## Keyboard

Enter sends the message. Shift+Enter adds a new line.

```js
text.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault()
    form.requestSubmit()
  }
})
```

## From code

Keep the `File` objects of the attachments in a list (`picked`), and send them with the text in one request. Stream the reply into the thread.

```js
form.addEventListener("submit", async event => {
  event.preventDefault()
  const body = new FormData()
  body.append("text", text.value)
  for (const file of picked) body.append("files", file)
  const response = await fetch("/api/chat", { method: "POST", body })
})
```

## API Reference

See [Input Group](/docs/components/input-group#api-reference), [Attachment](/docs/components/attachment#api-reference), and [Dropdown Menu](/docs/components/dropdown-menu#api-reference).
