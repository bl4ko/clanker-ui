import { h, icon, traceClose, traceOpen } from "./clanker-ui.js"

const root = document.getElementById("terminal-demo")
const replay = document.getElementById("terminal-demo-replay")
const question = root.querySelector('[data-slot="bubble-content"]').textContent
const answer = root.querySelector("p").textContent
const commands = [...root.querySelectorAll('[data-slot="trace-collapsible"]')].map(row => ({
  command: row.querySelector('[data-slot="trace-title"]').textContent.replace(/^Ran /, ""),
  output: row.querySelector('[data-slot="code-block-code"]').textContent.split("\n"),
}))

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

replay.addEventListener("click", async () => {
  replay.hidden = true
  for (const el of root.querySelectorAll(':scope > [data-slot="message"]')) el.remove()
  root.insertBefore(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" }, h("div", { "data-slot": "bubble-content" }, question)))), replay)
  const trace = h("div", { "data-slot": "trace" })
  const content = h("div", { "data-slot": "message-content", class: "gap-4" }, trace)
  root.insertBefore(h("div", { "data-slot": "message" }, content), replay)
  for (const { command, output } of commands) {
    const title = h("span", { "data-slot": "trace-title" }, `Running ${command}`)
    const line = h("span", { "data-slot": "trace-line", "data-status": "running" }, h("span", { "data-slot": "trace-icon" }, icon("terminal")), title)
    const code = h("code", { "data-slot": "code-block-code" })
    let touched = false
    const row = h("div", { "data-slot": "trace-collapsible" },
      h("button", { type: "button", "data-slot": "trace-collapsible-trigger", onclick: () => { touched = true } }, line),
      h("div", { "data-slot": "trace-collapsible-content" },
        h("div", { "data-slot": "code-block", "data-size": "sm" },
          h("pre", { "data-slot": "code-block-content", "data-wrap": "true", class: "max-h-64" }, code))))
    trace.append(row)
    for (let i = 0; i < output.length; i++) {
      await wait(i ? 200 : 20)
      code.textContent = output.slice(0, i + 1).join("\n")
      if (!i && !touched) traceOpen(row)
    }
    await wait(200)
    line.removeAttribute("data-status")
    title.textContent = `Ran ${command}`
    if (!touched) traceClose(row)
  }
  const text = new Text("")
  content.append(h("p", {}, text))
  for (const word of answer.match(/\S+\s*/g)) {
    await wait(20)
    text.appendData(word)
  }
  replay.hidden = false
})
