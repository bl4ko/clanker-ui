---
title: Task
description: Displays the steps the agent takes, as it takes them.
---

{{example "task-demo" height="auto"}}

Task is a piece of work the agent is doing, such as finding the project files or updating a page. Each step, like a search, a read or an edit, appears under the task when the agent takes it.

Task is built with a `trace` with a `trace-collapsible` for each task.

## Task or Plan

Both are a list of steps under a collapsible line. The difference is when the steps are known.

Use [Plan](/docs/ai-elements/plan) when the agent decides the steps before it starts. Use Task when the steps come from the work itself, and the agent only knows the next one once it has taken the last.

|  | Plan | Task |
| --- | --- | --- |
| Steps | Every step, from the start | Each step, once the agent takes it |
| Pending steps | Yes, waiting their turn | None |
| Title | The goal, with progress: "2 of 4 done" | What the agent is doing, then what it did |
| Per reply | One plan | One or more tasks, each closing when it is done |

## Installation

Task is built with the [Trace](/docs/components/trace) component. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible" data-default-open>
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line">
        <span data-slot="trace-title">Found the project files</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div data-slot="trace">
        <span data-slot="trace-line">
          <span data-slot="trace-icon"><svg data-lucide="search"></svg></span>
          <span data-slot="trace-title">Searched for app/page.tsx</span>
        </span>
        <a href="/files/app/page.tsx">
          <span data-slot="trace-line">
            <span data-slot="trace-icon"><svg data-lucide="file-text"></svg></span>
            <span data-slot="trace-title">Read app/page.tsx</span>
          </span>
        </a>
      </div>
    </div>
  </div>
</div>
```

## Status

Set the task's status from its steps. Write the title in the present tense while the task runs, and in the past tense once it is done.

| Steps | `data-status` | Title |
| --- | --- | --- |
| A step is still running | `running` | Updating the page metadata |
| A step failed | `error` | Failed to update the page metadata |
| Every step is done | none | Updated the page metadata |

Put several tasks in one `trace`. Keep the running task open, and close each task with `traceClose()` once it is done.

## From code

Send each task with its own `id`, and write it again with every new step. Keep the row of each task by its `id` and update it in place: set the status and the title, and append the new step.

```js
import { h, traceClose } from "./clanker-ui.js"

const rows = new Map()

function updateTask(trace, task) {
  let row = rows.get(task.id)
  if (!row) {
    row = h("div", { "data-slot": "trace-collapsible", "data-default-open": "" },
      h("button", { type: "button", "data-slot": "trace-collapsible-trigger" },
        h("span", { "data-slot": "trace-line" }, h("span", { "data-slot": "trace-title" }))),
      h("div", { "data-slot": "trace-collapsible-content" }, h("div", { "data-slot": "trace" })))
    rows.set(task.id, row)
    trace.append(row)
  }
  const running = task.steps.some(step => step.status === "running")
  const line = row.querySelector('[data-slot="trace-line"]')
  if (running) line.setAttribute("data-status", "running")
  else line.removeAttribute("data-status")
  line.querySelector('[data-slot="trace-title"]').textContent = task.title
  row.querySelector('[data-slot="trace-collapsible-content"] [data-slot="trace"]').replaceChildren(...task.steps.map(step =>
    h("span", { "data-slot": "trace-line", "data-status": step.status === "done" ? null : step.status }, h("span", { "data-slot": "trace-title" }, step.title))))
  if (!running) traceClose(row)
}
```

## API Reference

See [Trace](/docs/components/trace#api-reference).
