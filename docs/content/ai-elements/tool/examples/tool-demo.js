import { h, icon } from "./clanker-ui.js"

const root = document.getElementById("tool-demo")
const replay = document.getElementById("tool-demo-replay")
const question = root.querySelector('[data-slot="bubble-content"]').textContent
const answer = root.querySelector("p").textContent

const calls = [
  { command: "node --version", output: "v24.18.0" },
  { command: "npm --version", output: "11.6.2" },
  { command: "pnpm --version", error: "command not found: pnpm" },
]

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function line(title, status) {
  return h("span", { "data-slot": "trace-line", "data-status": status },
    h("span", { "data-slot": "trace-icon" }, icon("terminal")),
    h("span", { "data-slot": "trace-title" }, title))
}

replay.addEventListener("click", async () => {
  replay.hidden = true
  for (const el of root.querySelectorAll(':scope > [data-slot="message"]')) el.remove()
  root.insertBefore(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" }, h("div", { "data-slot": "bubble-content" }, question)))), replay)
  const trace = h("div", { "data-slot": "trace" })
  const content = h("div", { "data-slot": "message-content", class: "gap-4" }, trace)
  root.insertBefore(h("div", { "data-slot": "message" }, content), replay)
  for (const call of calls) {
    const running = line(`Running ${call.command}`, "running")
    trace.append(running)
    await wait(900)
    const failed = call.error !== undefined
    running.replaceWith(h("div", { "data-slot": "trace-collapsible" },
      h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, line(`${failed ? "Failed to run" : "Ran"} ${call.command}`, failed ? "error" : null)),
      h("div", { "data-slot": "trace-collapsible-content" },
        h("div", { "data-slot": "code-block", "data-size": "sm" },
          h("pre", { "data-slot": "code-block-content", "data-wrap": "true", class: "max-h-64" },
            h("code", { "data-slot": "code-block-code" }, failed ? call.error : call.output))))))
  }
  const text = new Text("")
  content.append(h("p", {}, text))
  for (const word of answer.match(/\S+\s*/g)) {
    await wait(20)
    text.appendData(word)
  }
  replay.hidden = false
})
