---
title: Stack Trace
description: Displays a failed tool call and its stack frames.
---

{{example "stack-trace-demo" height="auto"}}

Stack Trace is a line for a tool call that failed. The error is the title, like "Failed: TypeError". Open it for the stack frames, which can link to the file and line.

Stack Trace is built with a `trace` with a `trace-collapsible` for the frames.

## Installation

Stack Trace is built with the [Trace](/docs/components/trace) and [Code Block](/docs/components/code-block) components. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible">
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line" data-status="error">
        <span data-slot="trace-icon"><svg data-lucide="circle-x"></svg></span>
        <span data-slot="trace-title">Failed: TypeError: Cannot read properties of undefined</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div class="flex flex-col gap-2 rounded-md bg-muted p-3 font-mono text-xs">
        <p class="text-destructive">TypeError: Cannot read properties of undefined</p>
        <ol>
          <li class="text-foreground">at formatInvoice (app/lib/billing.ts:42:31)</li>
          <li>at beginWork (node_modules/react-dom/cjs/react-dom.development.js:19049:16)</li>
        </ol>
      </div>
    </div>
  </div>
</div>
```

The title truncates, so repeat the full error at the top of the content. Frames from `node_modules` stay muted, so your own frames stand out.

## Frame Links

Turn your own frames into links that open the file at the line. The examples link to `#`; point the links at your editor or code viewer, such as `vscode://file/<absolute path>:<line>`. Fold the framework frames into a collapsible line of their own, so the frames you can fix come first.

{{example "stack-trace-frames" height="auto"}}

A link that holds a `trace-line` is a step like a button: put it straight in the `trace`, so it gets the focus ring and the hover color.

```html
<a href="vscode://file/home/me/acme/app/lib/billing.ts:42">
  <span data-slot="trace-line">
    <span data-slot="trace-icon"><svg data-lucide="file-code"></svg></span>
    <span data-slot="trace-title">formatInvoice in app/lib/billing.ts:42</span>
  </span>
</a>
```

## From code

When a tool throws, send the stack as the error text of the call, not only the message. A stack shows file paths from your server, so only send it in development. Split it into the error and the frames:

```js
const [error, ...frames] = errorText.split("\n").map(line => line.trim())
const parsed = frames.map(line => {
  const match = line.match(/^at (.+) \((.+):(\d+):(\d+)\)$/)
  return { line, name: match?.[1], file: match?.[2], lineNumber: match?.[3], internal: line.includes("node_modules") }
})
```

Make a link `trace-line` for each frame that is not internal, and an `<ol>` in a collapsible line for the rest. Map the other tool states as in [Tool](/docs/ai-elements/tool#states).

## API Reference

See [Trace](/docs/components/trace#api-reference).
