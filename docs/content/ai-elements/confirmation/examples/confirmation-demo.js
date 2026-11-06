import { h, icon, traceClose } from "./clanker-ui.js"

const COMMAND = "rm -rf dist"
const THOUGHT = "The build output lives in dist. Deleting it cannot be undone, so I should ask before I run the command."

const root = document.getElementById("confirmation-demo")
const next = document.getElementById("confirmation-demo-next")
const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))
let run = 0

function spinner() {
  const el = icon("loader-circle")
  el.classList.add("animate-spin")
  return el
}

function button(variant, label, onclick) {
  return h("button", { type: "button", "data-slot": "button", "data-variant": variant, "data-size": "sm", onclick }, label)
}

function toolLine(title, running) {
  return h("div", { "data-slot": "trace" },
    h("span", { "data-slot": "trace-line", "data-status": running ? "running" : null },
      h("span", { "data-slot": "trace-icon" }, icon("terminal")),
      h("span", { "data-slot": "trace-title" }, `${title} ${COMMAND}`)))
}

async function stream(target, text, id) {
  for (const word of text.match(/\S+\s*/g)) {
    await wait(20)
    if (id !== run) return false
    target.append(word)
  }
  return true
}

async function reply(content, text, id) {
  await wait(600)
  if (id !== run) return
  const p = h("p")
  content.append(p)
  if (await stream(p, text, id)) idle()
}

function idle() {
  next.textContent = root.querySelector('[data-slot="message"]') ? "Reset" : "Send message"
  next.hidden = false
}

async function answer(item, content, approved, id) {
  next.hidden = true
  if (approved) {
    const trace = toolLine("Running", true)
    item.replaceWith(trace)
    await wait(50)
    if (id !== run) return
    trace.replaceWith(toolLine("Ran", false))
    await reply(content, "Removed the dist folder.", id)
  } else {
    item.replaceWith(toolLine("Denied", false))
    await reply(content, "Okay, I left the dist folder in place.", id)
  }
}

async function send() {
  const id = ++run
  next.hidden = true
  next.before(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" },
        h("div", { "data-slot": "bubble-content" }, "Clean up the build folder.")))))
  await wait(600)
  if (id !== run) return
  const line = h("span", { "data-slot": "trace-line", "data-status": "running" },
    h("span", { "data-slot": "trace-icon" }, spinner()),
    h("span", { "data-slot": "trace-title" }, "Thinking"))
  const text = h("div", { class: "whitespace-pre-wrap" })
  const trigger = h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, line)
  const reasoning = h("div", { "data-slot": "trace-collapsible", "data-default-open": true }, trigger,
    h("div", { "data-slot": "trace-collapsible-content" }, text))
  let touched = false
  trigger.addEventListener("click", () => { touched = true })
  const content = h("div", { "data-slot": "message-content", class: "gap-4" }, h("div", { "data-slot": "trace" }, reasoning))
  next.before(h("div", { "data-slot": "message" }, content))
  if (!(await stream(text, THOUGHT, id))) return
  line.removeAttribute("data-status")
  line.querySelector('[data-slot="trace-icon"]').replaceChildren(icon("circle-check"))
  line.querySelector('[data-slot="trace-title"]').textContent = "Thought"
  if (!touched) traceClose(reasoning)
  await wait(400)
  if (id !== run) return
  const item = h("div", { "data-slot": "item", "data-variant": "outline", "data-size": "sm" },
    h("div", { "data-slot": "item-media", "data-variant": "icon" }, icon("terminal")),
    h("div", { "data-slot": "item-content" },
      h("div", { "data-slot": "item-title" }, `Run ${COMMAND}?`),
      h("p", { "data-slot": "item-description" }, "The command runs in this project.")),
    h("div", { "data-slot": "item-actions" },
      button("outline", "Deny", () => answer(item, content, false, id)),
      button("default", "Approve", () => answer(item, content, true, id))))
  content.append(item)
  idle()
}

next.addEventListener("click", () => {
  if (!root.querySelector('[data-slot="message"]')) {
    send()
    return
  }
  run++
  for (const message of root.querySelectorAll(':scope > [data-slot="message"]')) message.remove()
  idle()
})
