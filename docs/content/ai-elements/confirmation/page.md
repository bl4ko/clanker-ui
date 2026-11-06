---
title: Confirmation
description: Asks for approval before a tool runs.
---

{{example "confirmation-demo" height="auto"}}

Confirmation asks the person for a yes or no before a tool runs. The question is an [Item](/docs/components/item) with Deny and Approve buttons. Once the person answers, the call becomes a Tool line: a `trace-line` in a [Trace](/docs/components/trace).

## Installation

Confirmation is built with the [Item](/docs/components/item) and [Button](/docs/components/button) components, and the answered call with [Trace](/docs/components/trace). Load the `layout` and `chat` groups, or the one-file set.

## Usage

```html
<div data-slot="item" data-variant="outline" data-size="sm">
  <div data-slot="item-media" data-variant="icon"><svg data-lucide="terminal"></svg></div>
  <div data-slot="item-content">
    <div data-slot="item-title">Run rm -rf dist?</div>
    <p data-slot="item-description">The command runs in this project.</p>
  </div>
  <div data-slot="item-actions">
    <button type="button" data-slot="button" data-variant="outline" data-size="sm" id="deny">Deny</button>
    <button type="button" data-slot="button" data-size="sm" id="approve">Approve</button>
  </div>
</div>
```

## From code

While the call waits for an answer, show the item outside the `trace`: it is a question for the person, not a step that the agent took. Send the answer to your server, and replace the item with the line of the call. Approve runs the tool, so the line reads "Running …" with `data-status="running"`, then "Ran …" when the output arrives. Deny gives the line "Denied …" without a status.

```js
import { h, icon } from "./clanker-ui.js"

function toolLine(title, status) {
  return h("div", { "data-slot": "trace" },
    h("span", { "data-slot": "trace-line", "data-status": status },
      h("span", { "data-slot": "trace-icon" }, icon("terminal")),
      h("span", { "data-slot": "trace-title" }, title)))
}

approve.addEventListener("click", async () => {
  const line = toolLine("Running rm -rf dist", "running")
  item.replaceWith(line)
  await fetch("/api/approval", { method: "POST", body: JSON.stringify({ id, approved: true }) })
  line.replaceWith(toolLine("Ran rm -rf dist"))
})

deny.addEventListener("click", () => {
  item.replaceWith(toolLine("Denied rm -rf dist"))
  fetch("/api/approval", { method: "POST", body: JSON.stringify({ id, approved: false }) })
})
```

The agent continues once every call has an answer. In the demo, the next turn says what happened: "Removed the dist folder." or "Okay, I left the dist folder in place."

## API Reference

See [Item](/docs/components/item#api-reference), [Button](/docs/components/button#api-reference), and [Trace](/docs/components/trace#api-reference).
