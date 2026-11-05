import { h, icon, traceClose } from "./clanker-ui.js"

const root = document.getElementById("task-demo")
const replay = document.getElementById("task-demo-replay")
const question = root.querySelector('[data-slot="bubble-content"]').textContent
const answer = root.querySelector("p").textContent

const tasks = [
  {
    title: ["Finding the project files", "Found the project files"],
    steps: [
      ["Searching for generateMetadata", "Searched for generateMetadata"],
      ["Reading app/layout.tsx", "Read app/layout.tsx"],
      ["Reading app/page.tsx", "Read app/page.tsx"],
    ],
  },
  {
    title: ["Updating the page metadata", "Updated the page metadata"],
    steps: [
      ["Editing app/layout.tsx", "Edited app/layout.tsx"],
      ["Editing app/page.tsx", "Edited app/page.tsx"],
    ],
  },
]

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function setLine(line, title, running) {
  if (running) line.setAttribute("data-status", "running")
  else line.removeAttribute("data-status")
  line.querySelector('[data-slot="trace-title"]').textContent = title
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
  for (const task of tasks) {
    let touched = false
    const status = h("span", { "data-slot": "trace-icon" }, icon("loader-circle", { class: "animate-spin" }))
    const line = h("span", { "data-slot": "trace-line", "data-status": "running" }, status, h("span", { "data-slot": "trace-title" }, task.title[0]))
    const list = h("div", { "data-slot": "trace" })
    const row = h("div", { "data-slot": "trace-collapsible", "data-default-open": "" },
      h("button", { type: "button", "data-slot": "trace-collapsible-trigger", onclick: () => { touched = true } }, line),
      h("div", { "data-slot": "trace-collapsible-content" }, list))
    trace.append(row)
    let previous = null
    for (const [running, done] of task.steps) {
      if (previous) setLine(previous.line, previous.done, false)
      const step = h("span", { "data-slot": "trace-line", "data-status": "running" }, h("span", { "data-slot": "trace-title" }, running))
      list.append(step)
      previous = { line: step, done }
      await wait(900)
    }
    setLine(previous.line, previous.done, false)
    setLine(line, task.title[1], false)
    status.replaceChildren(icon("circle-check"))
    if (!touched) traceClose(row)
    await wait(900)
  }
  const text = new Text("")
  content.append(h("p", {}, text))
  for (const word of answer.match(/\S+\s*/g)) {
    await wait(20)
    text.appendData(word)
  }
  replay.hidden = false
})
