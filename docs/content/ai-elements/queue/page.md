---
title: Queue
description: Displays the agent's todo list, split into what is left and what is done.
---

{{example "queue-demo" height="auto"}}

Queue is the agent's todo list. Todos sit in two sections, To do and Completed, and the icon on each todo shows its status. The agent updates the list as it works, so a todo moves from one section to the other when it is done.

Queue is built with `trace` with a `trace-collapsible` for each section.

## Installation

Queue is built with the [Trace](/docs/components/trace) component. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible" data-default-open>
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line">
        <span data-slot="trace-icon"><svg data-lucide="list-todo"></svg></span>
        <span data-slot="trace-title">2 to do</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div data-slot="trace">
        <span data-slot="trace-line">
          <span data-slot="trace-icon"><svg data-lucide="circle"></svg></span>
          <span data-slot="trace-title">Update the registry snapshots</span>
        </span>
        <span data-slot="trace-line">
          <span data-slot="trace-icon"><svg data-lucide="circle"></svg></span>
          <span data-slot="trace-title">Add tests for the combobox</span>
        </span>
      </div>
    </div>
  </div>
  <div data-slot="trace-collapsible">
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line">
        <span data-slot="trace-icon"><svg data-lucide="list-checks"></svg></span>
        <span data-slot="trace-title">1 completed</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div data-slot="trace">
        <span data-slot="trace-line">
          <span data-slot="trace-icon"><svg data-lucide="circle-check"></svg></span>
          <span data-slot="trace-title">Add a changeset</span>
        </span>
      </div>
    </div>
  </div>
</div>
```

## Descriptions

A todo with a description is a `trace-collapsible` that opens to show it. A todo without one stays a `trace-line`.

{{example "queue-descriptions" height="auto"}}

```html
<div data-slot="trace-collapsible">
  <button type="button" data-slot="trace-collapsible-trigger">
    <span data-slot="trace-line">
      <span data-slot="trace-icon"><svg data-lucide="circle"></svg></span>
      <span data-slot="trace-title">Fix the focus ring on the select trigger</span>
    </span>
  </button>
  <div data-slot="trace-collapsible-content">It is clipped by overflow-hidden on the field.</div>
</div>
```

## From code

The agent writes its todos with a tool. Each call sends the whole list, so render the last call: update the section titles and replace the lines of each section. Keep the section elements, so a section that the person closed stays closed.

Map each todo status to a section, an icon, and a `trace-line` status. Set `data-status="running"` on the todo in progress only while the reply streams, so its title stops shimmering when the agent stops.

| Todo status | Section | Icon | `data-status` |
| --- | --- | --- | --- |
| `pending` | To do | `circle` | none |
| `in_progress` | To do | `circle-dot` | `running` while the reply streams |
| `completed` | Completed | `circle-check` | none |

```js
import { h, icon } from "./clanker-ui.js"

function todoLine(todo, streaming) {
  const name = { completed: "circle-check", in_progress: "circle-dot" }[todo.status] ?? "circle"
  return h("span", { "data-slot": "trace-line", "data-status": streaming && todo.status === "in_progress" ? "running" : null },
    h("span", { "data-slot": "trace-icon" }, icon(name)),
    h("span", { "data-slot": "trace-title" }, todo.content))
}

function render(section, todos, word, streaming) {
  section.querySelector('[data-slot="trace-title"]').textContent = `${todos.length} ${word}`
  section.querySelector('[data-slot="trace-collapsible-content"] [data-slot="trace"]').replaceChildren(...todos.map(todo => todoLine(todo, streaming)))
}
```

## API Reference

See [Trace](/docs/components/trace#api-reference).
