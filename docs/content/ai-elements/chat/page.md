---
title: Chat
description: The thread. Message Scroller keeps your place while the reply streams.
---

{{example "chat-demo" height="auto"}}

Chat is the thread of a conversation with the agent. Each turn is a [Message](/docs/ai-elements/message) inside [Message Scroller](/docs/components/message-scroller). The person's message is the scroll anchor, so a new question settles near the top and the reply streams in under it. The field is a [Prompt Input](/docs/ai-elements/prompt-input).

## Installation

Chat is built with the [Message Scroller](/docs/components/message-scroller), [Message](/docs/components/message), [Bubble](/docs/components/bubble), and [Input Group](/docs/components/input-group) components. Load the `chat`, `forms`, and `overlays` groups, or the one-file set.

## Usage

```html
<div data-slot="message-scroller" data-auto-scroll>
  <div data-slot="message-scroller-viewport">
    <div data-slot="message-scroller-content">
      <div data-slot="message-scroller-item" data-message-id="u1" data-scroll-anchor="true">
        <div data-slot="message" data-align="end">
          <div data-slot="message-content">
            <div data-slot="bubble" data-align="end" data-variant="muted">
              <div data-slot="bubble-content">Add a dark mode toggle to the settings page.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <button type="button" data-slot="message-scroller-button"></button>
</div>
```

`data-scroll-anchor="true"` goes on the person's turn. `data-auto-scroll` follows the reply while the person stays at the live edge. Give the scroller a height, for example with a flex column around it.

See [Message Scroller](/docs/components/message-scroller).

## From code

Add a `message-scroller-item` for each turn. The kit keeps the scroll position, and an anchored row moves near the top. Stream the reply into the agent's turn: append text, or render the Markdown again for each part that arrives.

```js
import { h } from "./clanker-ui.js"

function addTurn(content, { id, user }) {
  const row = h("div", { "data-slot": "message-scroller-item", "data-message-id": id, "data-scroll-anchor": user ? "true" : null },
    h("div", { "data-slot": "message", "data-align": user ? "end" : null },
      h("div", { "data-slot": "message-content" }, user
        ? h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" }, h("div", { "data-slot": "bubble-content" }, user))
        : null)))
  content.append(row)
  return row
}

async function streamReply(response, target) {
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  for (let part = await reader.read(); !part.done; part = await reader.read()) {
    target.append(part.value)
  }
}
```

Count and remove rows with `:scope > [data-slot="message-scroller-item"]`: the kit keeps a spacer as the last child of the content. Set `aria-busy="true"` on the content while a reply streams.

The demo plays a script of three turns. Each agent turn streams reasoning, a tool call, and a reply; the field holds the next scripted message, and other text gets one fallback reply.

## API Reference

See [Message Scroller](/docs/components/message-scroller#api-reference), [Message](/docs/components/message#api-reference), and [Input Group](/docs/components/input-group#api-reference).
