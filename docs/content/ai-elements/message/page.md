---
title: Message
description: One turn. The person's message, and the agent's reply with its actions.
---

{{example "message-pattern" height="auto"}}

Use Message for one turn in a thread. The person's text is a [Bubble](/docs/components/bubble) in a [Message](/docs/components/message) with `data-align="end"`. The agent's reply is formatted text in a Message, with actions under it. A thread of these turns is a chat.

## Installation

Message is built with the [Message](/docs/components/message), [Bubble](/docs/components/bubble), and [Tooltip](/docs/components/tooltip) components. Load the `chat` and `overlays` groups, or the one-file set.

## Usage

```html
<div data-slot="message" data-align="end">
  <div data-slot="message-content">
    <div data-slot="bubble" data-align="end" data-variant="muted">
      <div data-slot="bubble-content">How do I add a settings dialog?</div>
    </div>
  </div>
</div>
<div data-slot="message">
  <div data-slot="message-content" class="gap-2">
    <p>Install Dialog, then open it from the gear button.</p>
    <div data-slot="message-footer">
      <button type="button" data-slot="button" data-variant="ghost" data-size="icon-sm" aria-label="Copy"><svg data-lucide="copy"></svg></button>
    </div>
  </div>
</div>
```

See [Message](/docs/components/message).

## Actions

Put actions in `message-footer`. It follows the message alignment, so on the person's turn the actions sit on the right. Use ghost icon buttons with a [Tooltip](/docs/components/tooltip) for each.

- **Copy** writes the reply to the clipboard and swaps to a check for two seconds.
- **Good response** and **Bad response** are toggles. Set `aria-pressed` so screen readers announce the state.
- **Retry** runs the turn again.
- **Edit** on the person's turn puts the text back in the field.

```js
copy.addEventListener("click", async () => {
  await navigator.clipboard.writeText(reply.innerText)
  copy.replaceChildren(icon("check"))
  copy.setAttribute("aria-label", "Copied")
  setTimeout(() => {
    copy.replaceChildren(icon("copy"))
    copy.setAttribute("aria-label", "Copy")
  }, 2000)
})
```

## Markdown

The reply streams as Markdown. The kit has no Markdown renderer, and the strict CSP blocks `innerHTML`, so render it to elements with `h()` (or on the server). Put fenced code in a [Code Block](/docs/components/code-block), so code in the reply gets line numbers and a copy button, and inline code in `<code data-typography="inline-code">`.

## From code

Branch on the message role. The person's turn is the bubble. The agent's turn is the reply, with a Retry button that sends the turn again.

```js
import { h, icon } from "./clanker-ui.js"

function turn(message) {
  if (message.role === "user") {
    return h("div", { "data-slot": "message", "data-align": "end" },
      h("div", { "data-slot": "message-content" },
        h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" },
          h("div", { "data-slot": "bubble-content" }, message.text))))
  }
  return h("div", { "data-slot": "message" },
    h("div", { "data-slot": "message-content", class: "gap-2" },
      h("p", {}, message.text),
      h("div", { "data-slot": "message-footer" },
        h("button", { type: "button", "data-slot": "button", "data-variant": "ghost", "data-size": "icon-sm", "aria-label": "Retry", onclick: () => regenerate(message.id) }, icon("refresh-ccw")))))
}
```

## API Reference

See [Message](/docs/components/message#api-reference), [Bubble](/docs/components/bubble#api-reference), and [Tooltip](/docs/components/tooltip#api-reference).
