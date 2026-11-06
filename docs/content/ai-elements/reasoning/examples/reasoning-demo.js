import { h, traceClose } from "./clanker-ui.js"

const root = document.getElementById("reasoning-demo")
const replay = document.getElementById("reasoning-demo-replay")
const question = root.querySelector('[data-slot="bubble-content"]').textContent
const thinking = root.querySelector('[data-slot="trace-collapsible-content"]').textContent
const answer = root.querySelector("p").textContent

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

async function stream(node, text, ms) {
  for (const word of text.match(/\S+\s*/g)) {
    await wait(ms)
    node.appendData(word)
  }
}

function message(...children) {
  return h("div", { "data-slot": "message" }, h("div", { "data-slot": "message-content", class: "gap-4" }, ...children))
}

replay.addEventListener("click", async () => {
  replay.hidden = true
  for (const el of root.querySelectorAll(':scope > [data-slot="message"]')) el.remove()
  root.insertBefore(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" }, h("div", { "data-slot": "bubble-content" }, question)))), replay)
  const title = h("span", { "data-slot": "trace-title" }, "Thinking")
  const line = h("span", { "data-slot": "trace-line", "data-status": "running" }, title)
  const trace = h("div", { "data-slot": "trace" }, line)
  const reply = message(trace)
  root.insertBefore(reply, replay)
  const words = new Text("")
  let touched = false
  const collapsible = h("div", { "data-slot": "trace-collapsible", "data-default-open": "" },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger", onclick: () => { touched = true } }),
    h("div", { "data-slot": "trace-collapsible-content", class: "whitespace-pre-wrap" }, words))
  await wait(20)
  words.appendData(thinking.match(/\S+\s*/)[0])
  collapsible.firstChild.append(line)
  trace.append(collapsible)
  await stream(words, thinking.slice(words.length), 40)
  line.removeAttribute("data-status")
  title.textContent = "Thought for 5s"
  if (!touched) traceClose(collapsible)
  await wait(400)
  const text = new Text("")
  reply.firstChild.append(h("p", {}, text))
  await stream(text, answer, 20)
  replay.hidden = false
})
