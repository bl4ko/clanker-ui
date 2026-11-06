---
title: Tool
description: Displays a tool call the agent makes, from input to output.
---

{{example "tool-demo" height="auto"}}

Tool is a tool call the agent makes, such as running a command or reading a file. The line follows the call from input to output, including errors and calls that wait for approval.

Tool is built with a `trace` with a `trace-collapsible` for each call that has output.

## Installation

Tool is built with the [Trace](/docs/components/trace) and [Code Block](/docs/components/code-block) components. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible">
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line">
        <span data-slot="trace-icon"><svg data-lucide="terminal"></svg></span>
        <span data-slot="trace-title">Ran git status --short</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div data-slot="code-block" data-size="sm">
        <pre data-slot="code-block-content" data-wrap="true" class="max-h-64"><code data-slot="code-block-code"> M components/chat.tsx</code></pre>
      </div>
    </div>
  </div>
</div>
```

## States

The kit does not read tool calls. Map the state of each call to a `data-status` and a title.

{{example "tool-states" height="auto"}}

| Tool call state | `data-status` | Title |
| --- | --- | --- |
| The input streams or is complete | `running` while the reply streams | Running … |
| The input is complete after the reply stops | `error` | Failed to run … |
| Approval requested | - | Not a line. An `item` outside the `trace` with Approve and Deny buttons. |
| Approval answered | `running` if approved, none if not | Running … if approved, Denied … if not |
| Output available | none | Ran … |
| Output error | `error` | Failed to run … |
| Denied | none | Denied … |

A tool is a plain `trace-line` while it runs, and a `trace-collapsible` once its output arrives.

```js
import { h, icon } from "./clanker-ui.js"

function toolLine(call, streaming) {
  const line = (title, status) => h("span", { "data-slot": "trace-line", "data-status": status },
    h("span", { "data-slot": "trace-icon" }, icon("terminal")),
    h("span", { "data-slot": "trace-title" }, title))
  if (call.state === "output-denied") return line(`Denied ${call.command}`, null)
  if (call.state === "output-available" || call.state === "output-error") {
    const failed = call.state === "output-error"
    return h("div", { "data-slot": "trace-collapsible" },
      h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, line(`${failed ? "Failed to run" : "Ran"} ${call.command}`, failed ? "error" : null)),
      h("div", { "data-slot": "trace-collapsible-content" },
        h("div", { "data-slot": "code-block", "data-size": "sm" },
          h("pre", { "data-slot": "code-block-content", "data-wrap": "true", class: "max-h-64" },
            h("code", { "data-slot": "code-block-code" }, failed ? call.errorText : call.stdout)))))
  }
  return line(`${streaming ? "Running" : "Failed to run"} ${call.command}`, streaming ? "running" : "error")
}
```

Replace the line of a call with `toolLine()` each time its state changes. A tool that runs in the browser stays "input available" after the reply stops until your code sends its output. Treat it as waiting, not failed.

## Output in a Sheet

For long output, make the `trace-line` the trigger of a [Sheet](/docs/components/sheet) and show the output in the sheet. A trigger outside the sheet root names the root: `data-sheet-trigger="<id>"`, so the button stays a direct child of the `trace` and gets its focus ring. The example keeps the finished turn in a `<template>` and adds it when you send the message.

{{example "tool-sheet" height="auto"}}

## Approval

A pending approval is a question for the person, not a step the agent took, so it sits outside the `trace` as an [Item](/docs/components/item). Once the person answers, the tool goes back to being a line. See [Confirmation](https://ui.shadcn.com/docs/ai-elements/base/confirmation) on the shadcn/ui site.

{{example "tool-approval" height="auto"}}

```html
<div data-slot="item" data-variant="outline" data-size="sm">
  <div data-slot="item-media" data-variant="icon"><svg data-lucide="terminal"></svg></div>
  <div data-slot="item-content">
    <div data-slot="item-title">Run rm -rf dist?</div>
  </div>
  <div data-slot="item-actions">
    <button type="button" data-slot="button" data-variant="outline" data-size="sm">Deny</button>
    <button type="button" data-slot="button" data-size="sm">Approve</button>
  </div>
</div>
```

Send the answer to your server when the person clicks a button, then replace the item with the line of the call.

## API Reference

See [Trace](/docs/components/trace#api-reference), [Code Block](/docs/components/code-block#api-reference), [Sheet](/docs/components/sheet#api-reference), and [Item](/docs/components/item#api-reference).
