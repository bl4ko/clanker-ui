---
title: Chain of Thought
description: Displays a summary that expands into the steps an agent took.
---

{{example "chain-of-thought-demo" height="auto"}}

Chain of Thought is a summary line that expands into the steps an agent took. The summary says what happened, like "Researched in 3 steps". The steps sit inside it, each one a line of its own.

Chain of Thought is built with a `trace` with a `trace-collapsible` for the summary.

## Installation

Chain of Thought is built with the [Trace](/docs/components/trace), [Code Block](/docs/components/code-block), and [Badge](/docs/components/badge) components. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible" data-default-open>
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line">
        <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
        <span data-slot="trace-title">Researched in 3 steps</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div data-slot="trace">
        <span data-slot="trace-line">
          <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
          <span data-slot="trace-title">Read the build log for dpl_8Kx2</span>
        </span>
        <span data-slot="trace-line">
          <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
          <span data-slot="trace-title">Searched the web for next.js image cache key</span>
        </span>
        <span data-slot="trace-line">
          <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
          <span data-slot="trace-title">Searched the code for cacheKey</span>
        </span>
      </div>
    </div>
  </div>
</div>
```

## Steps

Each step is a `trace-line`. Set its `data-status` and write the title in the matching tense.

| Step | `data-status` | Title |
| --- | --- | --- |
| Running | `running` | Searching for … |
| Done, with detail | none | Searched for … |
| Done, links out | none | Read the Image component docs |
| Failed | `error` | Failed to search for … |

A closed `trace-collapsible-content` stays in the page (with `hidden`), so the steps keep their open state when the summary closes. shadcn/ui needs `keepMounted` for this.

## Search Results

When a step runs a web search, show the results as a `badge` for each hostname in the step's content.

```html
<div data-slot="trace-collapsible-content">
  <div class="flex flex-wrap gap-1.5">
    <span data-slot="badge" data-variant="secondary">nextjs.org</span>
    <span data-slot="badge" data-variant="secondary">vercel.com</span>
  </div>
</div>
```

## From code

Render each tool call as a step. The summary runs while the steps run, before the reply starts. Set its status and title from the steps. It opens while the steps run and closes when the reply starts, unless the person opened or closed it, as in [Reasoning](/docs/ai-elements/reasoning#from-code).

```js
import { icon, traceClose } from "./clanker-ui.js"

function setSummary(summary, steps, running, touched) {
  const failed = steps.filter(step => step.status === "error").length
  const line = summary.querySelector('[data-slot="trace-line"]')
  if (running) line.setAttribute("data-status", "running")
  else if (failed > 0) line.setAttribute("data-status", "error")
  else line.removeAttribute("data-status")
  line.querySelector('[data-slot="trace-icon"]').replaceChildren(running ? icon("loader-circle", { class: "animate-spin" }) : icon(failed > 0 ? "circle-alert" : "circle-check"))
  line.querySelector('[data-slot="trace-title"]').textContent = running ? "Researching" : `Researched in ${steps.length} steps${failed > 0 ? `, ${failed} failed` : ""}`
  if (!running && !touched) traceClose(summary)
}
```

`touched` is true once the person clicked the summary trigger. Each step is one tool call as a `trace-line`, as in [Tool](/docs/ai-elements/tool#states).

## API Reference

See [Trace](/docs/components/trace#api-reference) and [Badge](/docs/components/badge#api-reference).
