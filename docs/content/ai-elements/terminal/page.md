---
title: Terminal
description: Displays a command the agent runs, with its output as it streams.
---

{{example "terminal-demo" height="auto"}}

Terminal is a shell command the agent runs, such as a lint, a test run or a build. The line shows the command, and its output streams in underneath while it runs.

Terminal is built with a `trace` with a `trace-collapsible` for each command.

## Installation

Terminal is built with the [Trace](/docs/components/trace) and [Code Block](/docs/components/code-block) components. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible">
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line">
        <span data-slot="trace-icon"><svg data-lucide="terminal"></svg></span>
        <span data-slot="trace-title">Ran pnpm build</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div data-slot="code-block" data-size="sm">
        <pre data-slot="code-block-content" data-wrap="true" class="max-h-64"><code data-slot="code-block-code">&gt; next build</code></pre>
      </div>
    </div>
  </div>
</div>
```

## Exit Code

A command that exits with any code other than `0` failed. Set `data-status="error"`.

{{example "terminal-error" height="auto"}}

| Command | `data-status` | Title |
| --- | --- | --- |
| Running | `running` | Running pnpm build |
| Exited with `0` | none | Ran pnpm build |
| Exited with another code | `error` | pnpm lint exited with code 1 |

The command is a tool call, so its states map the same way as in [Tool](/docs/ai-elements/tool#states).

## Open While Running

Open the line once the first output arrives, so the output is visible while the command runs. Leave it open or closed after that, as in [Trace](/docs/components/trace). If the person opens or closes it, their choice wins.

## From code

The output of a command arrives in parts while it runs. Keep the whole output so far, and set it as the text of the `code-block-code` each time it grows. For terminal colors, load `clanker-ui-code.js` and fill the `code-block-code` with the nodes of `codeBlockHighlight(output, "ansi")` instead of the text; the escape codes go away (see [Code Block](/docs/components/code-block)).

```js
import { h, icon, traceClose, traceOpen } from "./clanker-ui.js"

function terminalLine(trace, command) {
  const title = h("span", { "data-slot": "trace-title" }, `Running ${command}`)
  const line = h("span", { "data-slot": "trace-line", "data-status": "running" },
    h("span", { "data-slot": "trace-icon" }, icon("terminal")), title)
  const code = h("code", { "data-slot": "code-block-code" })
  let touched = false
  const row = h("div", { "data-slot": "trace-collapsible" },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger", onclick: () => { touched = true } }, line),
    h("div", { "data-slot": "trace-collapsible-content" },
      h("div", { "data-slot": "code-block", "data-size": "sm" },
        h("pre", { "data-slot": "code-block-content", "data-wrap": "true", class: "max-h-64" }, code))))
  trace.append(row)
  return {
    write(output) {
      if (!code.textContent && output && !touched) traceOpen(row)
      code.textContent = output
    },
    exit(exitCode) {
      if (exitCode === 0) line.removeAttribute("data-status")
      else line.setAttribute("data-status", "error")
      title.textContent = exitCode === 0 ? `Ran ${command}` : `${command} exited with code ${exitCode}`
      if (!touched) traceClose(row)
    },
  }
}
```

Call `write()` with the output so far each time it grows, and `exit()` with the exit code.

## API Reference

See [Trace](/docs/components/trace#api-reference) and [Code Block](/docs/components/code-block#api-reference).
