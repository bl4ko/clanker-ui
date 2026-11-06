import { h, icon } from "./clanker-ui.js"

const root = document.getElementById("plan-demo")
const replay = document.getElementById("plan-demo-replay")
const question = root.querySelector('[data-slot="bubble-content"]').textContent
const answer = root.querySelector("p").textContent
const title = root.querySelector('[data-slot="trace-collapsible-trigger"] [data-slot="trace-title"]').textContent
const steps = [...root.querySelectorAll('[data-slot="trace-collapsible-content"] [data-slot="trace-title"]')].map(el => el.textContent)

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function render(line, list, description, current) {
  if (current < steps.length) line.setAttribute("data-status", "running")
  else line.removeAttribute("data-status")
  description.textContent = `${Math.min(current, steps.length)} of ${steps.length} done`
  list.replaceChildren(...steps.map((step, index) => {
    const status = index < current ? null : index === current ? "running" : "pending"
    return h("span", { "data-slot": "trace-line", "data-status": status },
      h("span", { "data-slot": "trace-icon" }, icon(status === null ? "circle-check" : status === "running" ? "circle-dot" : "circle")),
      h("span", { "data-slot": "trace-title" }, step))
  }))
}

replay.addEventListener("click", async () => {
  replay.hidden = true
  for (const el of root.querySelectorAll(':scope > [data-slot="message"]')) el.remove()
  root.insertBefore(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" }, h("div", { "data-slot": "bubble-content" }, question)))), replay)
  const description = h("span", { "data-slot": "trace-description" })
  const line = h("span", { "data-slot": "trace-line" },
    h("span", { "data-slot": "trace-icon" }, icon("route")),
    h("span", { "data-slot": "trace-title" }, title),
    description)
  const list = h("div", { "data-slot": "trace" })
  const content = h("div", { "data-slot": "message-content", class: "gap-4" },
    h("div", { "data-slot": "trace" },
      h("div", { "data-slot": "trace-collapsible", "data-default-open": "" },
        h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, line),
        h("div", { "data-slot": "trace-collapsible-content" }, list))))
  root.insertBefore(h("div", { "data-slot": "message" }, content), replay)
  for (let current = 0; current <= steps.length; current++) {
    render(line, list, description, current)
    if (current < steps.length) await wait(1200)
  }
  const text = new Text("")
  content.append(h("p", {}, text))
  for (const word of answer.match(/\S+\s*/g)) {
    await wait(20)
    text.appendData(word)
  }
  replay.hidden = false
})
