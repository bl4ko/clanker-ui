---
title: Suggestion
description: A short prompt you can send to the agent in one click.
---

{{example "suggestion-demo" height="auto"}}

Suggestion is a prompt you send without typing. Each one is a [Button](/docs/components/button) with the prompt as its label. Put a row of them above the [Prompt Input](/docs/ai-elements/prompt-input).

## Installation

Suggestion is built with the [Button](/docs/components/button) component. It is in the core group; the field under it needs `forms` for the [Input Group](/docs/components/input-group).

## Usage

```html
<div class="suggestions scroll-fade-x">
  <button type="button" data-slot="button" data-variant="outline" data-size="sm">Add a dark mode toggle</button>
  <button type="button" data-slot="button" data-variant="outline" data-size="sm">Fix the failing build</button>
</div>
```

```css title="app.css"
.suggestions {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scrollbar-width: none;
}

.suggestions > [data-slot="button"] { flex-shrink: 0; }
```

## Scrolling

The row scrolls sideways when the suggestions do not fit. [`scroll-fade-x`](/docs/utils/scroll-fade) fades the edge that has more to show, and `flex-shrink: 0` keeps each label on one line.

## From code

The label is the message. Send it as is.

```js
row.addEventListener("click", event => {
  const button = event.target.closest("button")
  if (button) send(button.textContent)
})
```

## API Reference

See [Button](/docs/components/button#api-reference).
