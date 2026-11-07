---
title: Reasoning
description: Displays the agent's thinking as it streams.
---

{{example "reasoning-demo" height="auto"}}

Reasoning is a line for the agent's thinking. It reads "Thinking" and opens while the model thinks, then reads "Thought" and closes when it is done. The thinking itself sits inside, and the line can show how long it took.

Reasoning is built with a `trace` with a `trace-collapsible` for the thinking.

## Installation

Reasoning is built with the [Trace](/docs/components/trace) component. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible">
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line">
        <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
        <span data-slot="trace-title">Thought</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content" class="whitespace-pre-wrap">The deploy log has three phases.</div>
  </div>
</div>
```

## Duration

Time the reasoning on the server, send it with the message, and show it in a `trace-description` after the title.

{{example "reasoning-duration" height="auto"}}

```html
<span data-slot="trace-line">
  <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
  <span data-slot="trace-title">Thought</span>
  <span data-slot="trace-description">12s</span>
</span>
```

## From code

Render each reasoning part as a line. It starts as a plain `trace-line` and becomes a `trace-collapsible` once text arrives, so there is nothing to open before the model has written anything. It opens while the model thinks and closes when it finishes. If the person opens or closes it, their choice wins. See [Trace](/docs/components/trace).

```js
import { h, icon, traceClose } from "./clanker-ui.js"

function reasoningLine(trace) {
  const title = h("span", { "data-slot": "trace-title" }, "Thinking")
  const status = h("span", { "data-slot": "trace-icon" }, icon("loader-circle", { class: "animate-spin" }))
  const line = h("span", { "data-slot": "trace-line", "data-status": "running" }, status, title)
  const text = new Text("")
  let touched = false
  const collapsible = h("div", { "data-slot": "trace-collapsible", "data-default-open": "" },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger", onclick: () => { touched = true } }),
    h("div", { "data-slot": "trace-collapsible-content", class: "whitespace-pre-wrap" }, text))
  trace.append(line)
  return {
    write(delta) {
      if (!collapsible.isConnected) {
        collapsible.firstChild.append(line)
        trace.append(collapsible)
      }
      text.appendData(delta)
    },
    done() {
      line.removeAttribute("data-status")
      status.replaceChildren(icon("circle-check"))
      title.textContent = "Thought"
      if (!touched && collapsible.isConnected) traceClose(collapsible)
    },
  }
}
```

Call `write()` for each reasoning delta and `done()` when the part ends. Some models send several reasoning parts in one message. Each one is a line in the same `trace`.

## API Reference

See [Trace](/docs/components/trace#api-reference).
