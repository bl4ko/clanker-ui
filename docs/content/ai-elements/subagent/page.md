---
title: Subagent
description: Displays a subagent run, with its tool calls and result.
---

{{example "subagent-demo" height="auto"}}

Subagent is a line for work the agent hands to a subagent. The run is the title, like "Ran the research agent". Open it for the tool calls the subagent made and what it found.

Subagent is built with `trace` with a `trace-collapsible` for the run and a nested `trace` for its tool calls.

## Installation

Subagent is built with the [Trace](/docs/components/trace), [Code Block](/docs/components/code-block), and [Badge](/docs/components/badge) components. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible">
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line">
        <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
        <span data-slot="trace-title">Ran the research agent</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div class="flex flex-col gap-3">
        <div data-slot="trace">
          <span data-slot="trace-line">
            <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
            <span data-slot="trace-title">Ran grep -rn cacheKey scripts</span>
          </span>
        </div>
        <p>The cache is keyed on the commit SHA.</p>
      </div>
    </div>
  </div>
</div>
```

The kit wraps the children of `trace-collapsible-content` in an inner element, so put layout classes on your own wrapper, as `flex flex-col gap-3` above.

## Running

While the subagent runs, the line has `data-status="running"` and its content shows the tool calls so far. Add the result when the subagent finishes.

{{example "subagent-running" height="auto"}}

## Details

Put the task the subagent was given at the top of the content, with its model and tools as [Badge](/docs/components/badge) items. Show how long it ran in a `trace-description` after the title.

{{example "subagent-details" height="auto"}}

## From code

A subagent streams its own steps. Render the run as the line and the subagent's steps as the nested `trace`. Map each nested step as in the Tool pattern: a running `trace-line`, then a `trace-collapsible` with the output in a Code Block. Until the final output arrives, keep the run `running`; then remove the status, set the title to "Ran …", and add the result.

| Run state | `data-status` | Title |
| --- | --- | --- |
| Started, no output yet | `running` while the reply streams | Running … |
| Partial output (steps so far) | `running` while the reply streams | Running … |
| Final output | none | Ran … |
| Failed, or still running after the reply stops | `error` | Failed to run … |

```js
import { h, icon } from "./clanker-ui.js"

function finish(collapsible, report) {
  const line = collapsible.querySelector('[data-slot="trace-line"]')
  line.removeAttribute("data-status")
  line.querySelector('[data-slot="trace-icon"]').replaceChildren(icon("circle-check"))
  line.querySelector('[data-slot="trace-title"]').textContent = "Ran the research agent"
  collapsible.querySelector('[data-slot="trace-collapsible-content"] [data-slot="trace"]').after(h("p", {}, report))
}
```

## API Reference

See [Trace](/docs/components/trace#api-reference), [Code Block](/docs/components/code-block#api-reference), and [Badge](/docs/components/badge#api-reference).
