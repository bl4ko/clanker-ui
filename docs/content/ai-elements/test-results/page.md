---
title: Test Results
description: Displays a test run by the agent, with its suites and failures.
---

{{example "test-results-demo" height="auto"}}

Test Results is a test run by the agent. The summary line counts what passed and failed. Open it to see each suite, its tests, and the error for each failure.

Test Results is built with a `trace` with a `trace-collapsible` for the run and for each suite.

## Installation

Test Results is built with the [Trace](/docs/components/trace) and [Code Block](/docs/components/code-block) components. Load the `chat` group, or the one-file set.

## Usage

```html
<div data-slot="trace">
  <div data-slot="trace-collapsible">
    <button type="button" data-slot="trace-collapsible-trigger">
      <span data-slot="trace-line" data-status="error">
        <span data-slot="trace-icon"><svg data-lucide="flask-conical"></svg></span>
        <span data-slot="trace-title">Ran 2 tests, 1 failed</span>
      </span>
    </button>
    <div data-slot="trace-collapsible-content">
      <div data-slot="trace">
        <span data-slot="trace-line">
          <span data-slot="trace-icon"><svg data-lucide="check"></svg></span>
          <span data-slot="trace-title">creates a user</span>
        </span>
        <div data-slot="trace-collapsible">
          <button type="button" data-slot="trace-collapsible-trigger">
            <span data-slot="trace-line" data-status="error">
              <span data-slot="trace-icon"><svg data-lucide="x"></svg></span>
              <span data-slot="trace-title">updates a user profile</span>
            </span>
          </button>
          <div data-slot="trace-collapsible-content">
            <div data-slot="code-block" data-size="sm">
              <pre data-slot="code-block-content" data-wrap="true" class="max-h-64"><code data-slot="code-block-code">Expected status 200, received 500</code></pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

## Suites

Group tests by file. Each suite is a collapsible line with a `trace` of its tests. Open the suites that have a failure.

{{example "test-results-suites" height="auto"}}

```html
<div data-slot="trace-collapsible" data-default-open>
  <button type="button" data-slot="trace-collapsible-trigger">
    <span data-slot="trace-line" data-status="error">
      <span data-slot="trace-icon"><svg data-lucide="file-code"></svg></span>
      <span data-slot="trace-title">user-api.test.ts, 14 tests, 2 failed</span>
    </span>
  </button>
  <div data-slot="trace-collapsible-content">
    <div data-slot="trace">…</div>
  </div>
</div>
```

## From code

Run the tests as a tool and render its output. The tool states map the same way as in [Tool](/docs/ai-elements/tool#states).

```js
import { h, icon } from "./clanker-ui.js"

function testRunLine(suites) {
  const tests = suites.flatMap(suite => suite.tests)
  const failed = tests.filter(test => test.status === "failed").length
  return h("div", { "data-slot": "trace-collapsible", "data-default-open": failed > 0 ? "" : null },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger" },
      h("span", { "data-slot": "trace-line", "data-status": failed > 0 ? "error" : null },
        h("span", { "data-slot": "trace-icon" }, icon("flask-conical")),
        h("span", { "data-slot": "trace-title" }, `Ran ${tests.length} tests${failed > 0 ? `, ${failed} failed` : ""}`))),
    h("div", { "data-slot": "trace-collapsible-content" }, h("div", { "data-slot": "trace" }, ...suites.map(suiteLine))))
}
```

`suiteLine()` builds a suite the same way, with a `trace-line` for each test that passed or was skipped and a `trace-collapsible` with a [Code Block](/docs/components/code-block) for each test that failed.

## API Reference

See [Trace](/docs/components/trace#api-reference) and [Code Block](/docs/components/code-block#api-reference).
