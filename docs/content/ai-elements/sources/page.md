---
title: Sources
description: Displays the links the agent used for a reply.
---

{{example "sources-demo" height="auto"}}

Sources is a line that lists the links the agent used for a reply. It says how many there are, like "Used 3 sources", and opens into a link for each one.

Sources is built with `trace` with a `trace-collapsible` for the list.

## Installation

Sources is built with the [Trace](/docs/components/trace) component. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible">
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line">
        <span data-slot="trace-icon"><svg data-lucide="globe"></svg></span>
        <span data-slot="trace-title">Used 2 sources</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div data-slot="trace">
        <a href="https://pnpm.io/cli/create" target="_blank" rel="noreferrer">
          <span data-slot="trace-line">
            <span data-slot="trace-icon"><svg data-lucide="globe"></svg></span>
            <span data-slot="trace-title">pnpm create | pnpm.io<span class="sr-only"> (opens in a new tab)</span></span>
            <span data-slot="trace-icon"><svg data-lucide="arrow-up-right"></svg></span>
          </span>
        </a>
      </div>
    </div>
  </div>
</div>
```

## From code

Collect the sources of a message and render them after the text. The agent can cite the same page more than once, so remove the duplicates by `url`.

```js
const unique = sources.filter((source, index) => sources.findIndex(other => other.url === source.url) === index)
```

The title of a source is optional. Fall back to the host name of the URL: `source.title ?? new URL(source.url).hostname`. Build the lines with `h()` and add them to the inner `trace`; the kit gives the new collapsible its behavior.

## Accessibility

Each source is a plain link inside the list.

- Links open in a new tab. Add `sr-only` text, like "(opens in a new tab)", so screen readers announce it.
- The arrow icon is decorative. The title is the name of the link.
- The count in the trigger, like "Used 3 sources", tells the person what opens before they open it.

## API Reference

See [Trace](/docs/components/trace#api-reference).
