import { h, icon } from "./clanker-ui.js"

const TODOS = [
  "Add a dark variant to the theme tokens",
  "Read the theme from a cookie",
  "Add a toggle to the settings page",
  "Check contrast on the charts",
]

const root = document.getElementById("queue-demo")
const replay = document.getElementById("queue-demo-replay")
const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function todosAt(current) {
  return TODOS.map((content, index) => ({ content, status: index < current ? "completed" : index === current ? "in_progress" : "pending" }))
}

function todoLine(todo, streaming) {
  const name = todo.status === "completed" ? "circle-check" : todo.status === "in_progress" ? "circle-dot" : "circle"
  return h("span", { "data-slot": "trace-line", "data-status": streaming && todo.status === "in_progress" ? "running" : null },
    h("span", { "data-slot": "trace-icon" }, icon(name)),
    h("span", { "data-slot": "trace-title" }, todo.content))
}

function section(name) {
  const title = h("span", { "data-slot": "trace-title" })
  const list = h("div", { "data-slot": "trace" })
  const el = h("div", { "data-slot": "trace-collapsible", "data-default-open": true },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger" },
      h("span", { "data-slot": "trace-line" }, h("span", { "data-slot": "trace-icon" }, icon(name)), title)),
    h("div", { "data-slot": "trace-collapsible-content" }, list))
  return { el, title, list }
}

function render(trace, sections, todos, streaming) {
  const groups = [
    ["pending", "list-todo", "to do", todos.filter(todo => todo.status !== "completed")],
    ["completed", "list-checks", "completed", todos.filter(todo => todo.status === "completed")],
  ]
  for (const [key, name, word, items] of groups) {
    if (items.length === 0) {
      sections[key]?.el.remove()
      delete sections[key]
      continue
    }
    const s = (sections[key] ??= section(name))
    s.title.textContent = `${items.length} ${word}`
    s.list.replaceChildren(...items.map(todo => todoLine(todo, streaming)))
    if (!s.el.isConnected) key === "pending" ? trace.prepend(s.el) : trace.append(s.el)
  }
}

async function stream(parent, text) {
  const p = h("p")
  for (const word of text.match(/\S+\s*/g)) {
    await wait(20)
    if (!p.isConnected) parent.append(p)
    p.append(word)
  }
}

replay.addEventListener("click", async () => {
  replay.hidden = true
  for (const message of root.querySelectorAll(':scope > [data-slot="message"]')) message.remove()
  replay.before(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" },
        h("div", { "data-slot": "bubble-content" }, "Add dark mode to the settings page.")))))
  const trace = h("div", { "data-slot": "trace" })
  const content = h("div", { "data-slot": "message-content", class: "gap-4" }, trace)
  replay.before(h("div", { "data-slot": "message" }, content))
  const sections = {}
  for (let step = 0; step <= TODOS.length; step++) {
    if (step > 0) await wait(1400)
    render(trace, sections, todosAt(step), true)
  }
  await stream(content, "Dark mode is in. The toggle is under Settings, Appearance.")
  replay.hidden = false
})
