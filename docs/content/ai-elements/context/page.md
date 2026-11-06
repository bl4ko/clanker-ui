---
title: Context
description: How much of the context window the conversation has used.
---

{{example "context-demo" height="auto"}}

Context shows how much of the model's context window the conversation has used. It is a [Hover Card](/docs/components/hover-card) with a [Progress](/docs/components/progress) bar.

## Installation

Context is built with the [Hover Card](/docs/components/hover-card) and [Progress](/docs/components/progress) components. Load the `overlays` group for the hover card; the progress bar is in the core group.

## Usage

```html
<div data-slot="hover-card">
  <button type="button" data-slot="button" data-variant="outline" data-size="sm" data-hover-card-trigger data-delay="10" data-close-delay="100">8% context</button>
  <div data-slot="hover-card-content" class="context">
    <div class="context-head">
      <span>Context</span>
      <span>10.7k / 128k</span>
    </div>
    <div data-slot="progress" data-value="8" aria-label="Context used"></div>
  </div>
</div>
```

## From code

Read the token usage that your server sends with the agent's message, and write the label, the bar, and the numbers. `limit` is the model's context window; set it from the model you use.

```js
function tokens(value) {
  return value < 1000 ? String(value) : `${(value / 1000).toFixed(1).replace(/\.0$/, "")}k`
}

function showContext(root, usage, limit) {
  const used = usage.input + usage.output + usage.reasoning
  const percent = Math.round((used / limit) * 100)
  root.querySelector("[data-hover-card-trigger]").textContent = `${percent}% context`
  root.querySelector('[data-slot="progress"]').dataset.value = percent
  root.querySelector(".context-head > :last-child").textContent = `${tokens(used)} / ${tokens(limit)}`
}
```

The progress bar follows a change of `data-value`.

## API Reference

See [Hover Card](/docs/components/hover-card#api-reference) and [Progress](/docs/components/progress#api-reference).
