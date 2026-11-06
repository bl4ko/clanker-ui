---
title: Inline Citation
description: A source in the sentence that opens on hover.
---

{{example "inline-citation-demo" height="auto"}}

Inline Citation is a source that sits in the sentence it supports. It is a [Hover Card](/docs/components/hover-card) on a [Button](/docs/components/button).

To show a list of sources after the reply, use [Sources](/docs/ai-elements/sources).

## Installation

Inline Citation is built with the [Hover Card](/docs/components/hover-card) and [Button](/docs/components/button) components. Load the `overlays` group, or the one-file set. It needs no JavaScript of its own.

## Usage

A citation sits inside a `<p>`, so every part is a `<span>`: a `<div>` would end the paragraph.

```html
<span data-slot="hover-card">
  <button type="button" data-slot="button" data-variant="secondary" data-size="xs" data-hover-card-trigger data-delay="10" data-close-delay="100">nextjs.org</button>
  <span data-slot="hover-card-content" class="flex w-64 flex-col gap-1">
    <span class="font-medium">Linking and Navigating</span>
    <a href="https://nextjs.org/docs/app/getting-started/linking-and-navigating" target="_blank" rel="noreferrer">nextjs.org<span class="sr-only"> (opens in a new tab)</span></a>
  </span>
</span>
```

## From code

A source of the reply is the citation. Put the host name on the button, and the title, the description, and the link in the card.

```js
import { h } from "./clanker-ui.js"

function citation(source) {
  const host = new URL(source.url).hostname.replace(/^www\./, "")
  return h("span", { "data-slot": "hover-card" },
    h("button", { type: "button", "data-slot": "button", "data-variant": "secondary", "data-size": "xs", "data-hover-card-trigger": true, "data-delay": "10", "data-close-delay": "100" }, host),
    h("span", { "data-slot": "hover-card-content", class: "flex w-64 flex-col gap-1" },
      h("span", { class: "font-medium" }, source.title ?? host),
      h("a", { href: source.url, target: "_blank", rel: "noreferrer" }, host, h("span", { class: "sr-only" }, " (opens in a new tab)"))))
}
```

The title is optional. Fall back to the host name of the URL.

## API Reference

See [Hover Card](/docs/components/hover-card#api-reference) and [Button](/docs/components/button#api-reference).
