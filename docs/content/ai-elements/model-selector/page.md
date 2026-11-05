---
title: Model Selector
description: Two menus. One picks the model the agent runs, the other picks how hard it thinks.
---

{{example "model-selector-demo" height="auto"}}

## Installation

Model Selector is built with the [Dropdown Menu](/docs/components/dropdown-menu) and [Input Group](/docs/components/input-group) components. Load the `forms` and `overlays` groups.

## Usage

```html
<div data-slot="input-group">
  <textarea data-slot="input-group-control" placeholder="Ask the agent to change your code..." aria-label="Message"></textarea>
  <div data-slot="input-group-addon" data-align="block-end">
    <div data-slot="dropdown-menu" id="model">
      <button type="button" data-slot="button" data-input-group-button data-size="sm" data-dropdown-menu-trigger><span>GPT-5</span><svg data-lucide="chevron-down"></svg></button>
      <div data-slot="dropdown-menu-content" data-align="start">
        <div data-slot="dropdown-menu-radio-group" data-value="gpt-5">
          <div data-slot="dropdown-menu-group">
            <div data-slot="dropdown-menu-label">OpenAI</div>
            <div data-slot="dropdown-menu-radio-item" data-value="gpt-5" data-close-on-click>GPT-5</div>
            <div data-slot="dropdown-menu-radio-item" data-value="gpt-5-mini" data-close-on-click>GPT-5 mini</div>
          </div>
        </div>
      </div>
    </div>
    <div data-slot="dropdown-menu" id="effort">
      <button type="button" data-slot="button" data-input-group-button data-size="sm" data-dropdown-menu-trigger><span>Medium</span><svg data-lucide="chevron-down"></svg></button>
      <div data-slot="dropdown-menu-content" data-align="start">
        <div data-slot="dropdown-menu-radio-group" data-value="medium">
          <div data-slot="dropdown-menu-radio-item" data-value="low" data-close-on-click>Low</div>
          <div data-slot="dropdown-menu-radio-item" data-value="medium" data-close-on-click>Medium</div>
          <div data-slot="dropdown-menu-radio-item" data-value="high" data-close-on-click>High</div>
        </div>
      </div>
    </div>
    <button type="submit" data-slot="button" data-input-group-button data-variant="default" data-size="icon-sm" class="ms-auto" aria-label="Send"><svg data-lucide="arrow-up"></svg></button>
  </div>
</div>
```

Radio items keep a menu open; `data-close-on-click` closes it after a pick, like `closeOnClick` in shadcn/ui. The kit emits `dropdown-menu:change` on the menu root. Write the name of the picked item into the trigger, and name the trigger by its value (`aria-label="Model: GPT-5"`):

```js
menu.addEventListener("dropdown-menu:change", event => {
  const label = event.detail.item.textContent.trim()
  const trigger = menu.querySelector("[data-dropdown-menu-trigger]")
  trigger.querySelector("span").textContent = label
  trigger.setAttribute("aria-label", `Model: ${label}`)
})
```

## From code

Send the model and the effort with the message. Read the value of each radio group, and map it to a model and its options on the server.

```js
const model = document.querySelector('#model [data-slot="dropdown-menu-radio-group"]').dataset.value
const effort = document.querySelector('#effort [data-slot="dropdown-menu-radio-group"]').dataset.value

await fetch("/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text, model, effort }),
})
```

Each provider reads its own effort option and ignores the rest.

## API Reference

See [Dropdown Menu](/docs/components/dropdown-menu#api-reference) and [Input Group](/docs/components/input-group#api-reference).
