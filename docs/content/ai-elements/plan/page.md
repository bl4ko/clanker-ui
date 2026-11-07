---
title: Plan
description: Displays the steps the agent plans to take, and how far it has got.
---

{{example "plan-demo" height="auto"}}

Plan is the list of steps the agent decides on before it starts, such as the steps of a migration. Each step is done, running or pending, and the title counts how many are done.

Plan is built with a `trace` with a `trace-collapsible` for the plan.

When the steps are not known up front, use [Task](/docs/ai-elements/task#task-or-plan) instead.

## Installation

Plan is built with the [Trace](/docs/components/trace) component. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible" data-default-open>
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line" data-status="running">
        <span data-slot="trace-icon"><svg data-lucide="route"></svg></span>
        <span data-slot="trace-title">Plan: migrate to Base UI</span>
        <span data-slot="trace-description">2 of 5 done</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div data-slot="trace">
        <span data-slot="trace-line">
          <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
          <span data-slot="trace-title">Replace the Radix imports</span>
        </span>
        <span data-slot="trace-line" data-status="running">
          <span data-slot="trace-icon"><svg data-lucide="circle-dot"></svg></span>
          <span data-slot="trace-title">Rename asChild to render</span>
        </span>
        <span data-slot="trace-line" data-status="pending">
          <span data-slot="trace-icon"><svg data-lucide="circle"></svg></span>
          <span data-slot="trace-title">Run the type checker</span>
        </span>
      </div>
    </div>
  </div>
</div>
```

## Details

Put a description above the steps, inside `trace-collapsible-content`.

{{example "plan-description" height="auto"}}

## From code

Send the plan with a fixed `id`, and write it again when a step changes. Keep one row and update it in place: the status of the plan, the count, and the steps.

```js
import { h, icon } from "./clanker-ui.js"

const icons = { done: "circle-check", running: "circle-dot", pending: "circle" }

function updatePlan(row, plan, streaming) {
  const done = plan.steps.filter(step => step.status === "done").length
  const line = row.querySelector('[data-slot="trace-collapsible-trigger"] [data-slot="trace-line"]')
  if (streaming && done < plan.steps.length) line.setAttribute("data-status", "running")
  else line.removeAttribute("data-status")
  line.querySelector('[data-slot="trace-title"]').textContent = plan.title
  line.querySelector('[data-slot="trace-description"]').textContent = `${done} of ${plan.steps.length} done`
  row.querySelector('[data-slot="trace-collapsible-content"] [data-slot="trace"]').replaceChildren(...plan.steps.map(step =>
    h("span", { "data-slot": "trace-line", "data-status": step.status === "done" ? null : step.status },
      h("span", { "data-slot": "trace-icon" }, icon(icons[step.status])),
      h("span", { "data-slot": "trace-title" }, step.title))))
}
```

## API Reference

See [Trace](/docs/components/trace#api-reference).
