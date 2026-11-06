import { h, icon } from "./clanker-ui.js"

const root = document.getElementById("test-results-demo")
const replay = document.getElementById("test-results-demo-replay")
const question = root.querySelector('[data-slot="bubble-content"]').textContent
const answer = root.querySelector("p").textContent
const command = replay.dataset.command

const suites = [
  {
    name: "cart.test.ts",
    tests: [
      { name: "adds an item", status: "passed" },
      { name: "removes an item", status: "passed" },
      { name: "applies a discount code", status: "passed" },
    ],
  },
  {
    name: "payment.test.ts",
    tests: [
      { name: "charges the saved card", status: "passed" },
      { name: "retries a declined card", status: "failed", error: "Expected 2 charge attempts, received 1\n\n  at Object.<anonymous> (src/payment.test.ts:58:22)" },
    ],
  },
]

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function count(tests) {
  const failed = tests.filter(test => test.status === "failed").length
  const skipped = tests.filter(test => test.status === "skipped").length
  return { failed, text: [`${tests.length} tests`, failed && `${failed} failed`, skipped && `${skipped} skipped`].filter(Boolean).join(", ") }
}

function line(name, title, status) {
  return h("span", { "data-slot": "trace-line", "data-status": status },
    h("span", { "data-slot": "trace-icon" }, icon(name)),
    h("span", { "data-slot": "trace-title" }, title))
}

function collapsible(open, trigger, content) {
  return h("div", { "data-slot": "trace-collapsible", "data-default-open": open ? "" : null },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, trigger),
    h("div", { "data-slot": "trace-collapsible-content" }, content))
}

function testRow(test) {
  if (test.status === "failed") {
    return collapsible(true, line("x", test.name, "error"),
      h("div", { "data-slot": "code-block", "data-size": "sm" },
        h("pre", { "data-slot": "code-block-content", "data-wrap": "true", class: "max-h-64" },
          h("code", { "data-slot": "code-block-code" }, test.error))))
  }
  return test.status === "skipped" ? line("circle-dashed", `Skipped ${test.name}`) : line("check", test.name)
}

function testResults(list) {
  const summary = count(list.flatMap(suite => suite.tests))
  return collapsible(summary.failed > 0, line("flask-conical", `Ran ${summary.text}`, summary.failed ? "error" : null),
    h("div", { "data-slot": "trace" }, ...list.map(suite => {
      const counts = count(suite.tests)
      return collapsible(counts.failed > 0, line("file-code", `${suite.name}, ${counts.text}`, counts.failed ? "error" : null),
        h("div", { "data-slot": "trace" }, ...suite.tests.map(testRow)))
    })))
}

replay.addEventListener("click", async () => {
  replay.hidden = true
  for (const el of root.querySelectorAll(':scope > [data-slot="message"]')) el.remove()
  root.insertBefore(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" }, h("div", { "data-slot": "bubble-content" }, question)))), replay)
  const running = line("flask-conical", `Running ${command}`, "running")
  const content = h("div", { "data-slot": "message-content", class: "gap-4" }, h("div", { "data-slot": "trace" }, running))
  root.insertBefore(h("div", { "data-slot": "message" }, content), replay)
  await wait(1500)
  running.replaceWith(testResults(suites))
  const text = new Text("")
  content.append(h("p", {}, text))
  for (const word of answer.match(/\S+\s*/g)) {
    await wait(20)
    text.appendData(word)
  }
  replay.hidden = false
})
