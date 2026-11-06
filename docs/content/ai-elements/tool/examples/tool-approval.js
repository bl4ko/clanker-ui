import { h, icon, traceClose } from "./clanker-ui.js"

const root = document.getElementById("tool-approval")
const turn = document.getElementById("tool-approval-turn")
const button = document.getElementById("tool-approval-send")
const command = "rm -rf dist"

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

async function stream(node, text) {
  for (const word of text.match(/\S+\s*/g)) {
    await wait(20)
    node.appendData(word)
  }
}

function line(title, status) {
  return h("div", { "data-slot": "trace" },
    h("span", { "data-slot": "trace-line", "data-status": status },
      h("span", { "data-slot": "trace-icon" }, icon("terminal")),
      h("span", { "data-slot": "trace-title" }, title)))
}

async function answer(content, item, approved) {
  button.hidden = true
  const result = line(approved ? `Running ${command}` : `Denied ${command}`, approved ? "running" : null)
  item.replaceWith(result)
  if (approved) {
    await wait(100)
    result.replaceWith(line(`Ran ${command}`, null))
  }
  await wait(600)
  const text = new Text("")
  content.append(h("p", {}, text))
  await stream(text, approved ? "Removed the dist folder." : "Okay, I left the dist folder in place.")
  button.hidden = false
}

button.addEventListener("click", async () => {
  if (button.textContent === "Reset") {
    for (const el of root.querySelectorAll(':scope > [data-slot="message"]')) el.remove()
    button.textContent = "Send message"
    return
  }
  button.hidden = true
  const [question, reply] = turn.content.cloneNode(true).children
  const content = reply.firstElementChild
  const [trace, item] = content.children
  const collapsible = trace.firstElementChild
  const thinking = collapsible.lastElementChild.textContent
  const status = collapsible.querySelector('[data-slot="trace-icon"]')
  const title = collapsible.querySelector('[data-slot="trace-title"]')
  const line = collapsible.querySelector('[data-slot="trace-line"]')
  const words = new Text("")
  let touched = false
  collapsible.firstElementChild.addEventListener("click", () => { touched = true })
  collapsible.lastElementChild.replaceChildren(words)
  collapsible.setAttribute("data-default-open", "")
  line.setAttribute("data-status", "running")
  status.replaceChildren(icon("loader-circle", { class: "animate-spin" }))
  title.textContent = "Thinking"
  item.remove()
  root.insertBefore(question, button)
  await wait(600)
  root.insertBefore(reply, button)
  await stream(words, thinking)
  line.removeAttribute("data-status")
  status.replaceChildren(icon("circle-check"))
  title.textContent = "Thought"
  if (!touched) traceClose(collapsible)
  await wait(400)
  content.append(item)
  const [deny, approve] = item.querySelectorAll('[data-slot="button"]')
  deny.addEventListener("click", () => answer(content, item, false))
  approve.addEventListener("click", () => answer(content, item, true))
  button.textContent = "Reset"
  button.hidden = false
})
