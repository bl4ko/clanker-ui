import { h, icon } from "./clanker-ui.js"

const root = document.getElementById("tool-sheet")
const turn = document.getElementById("tool-sheet-turn")
const button = document.getElementById("tool-sheet-send")

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

button.addEventListener("click", async () => {
  if (button.textContent === "Reset") {
    for (const el of root.querySelectorAll(':scope > [data-slot="message"]')) el.remove()
    button.textContent = "Send message"
    return
  }
  button.hidden = true
  const [question, reply] = turn.content.cloneNode(true).children
  root.insertBefore(question, button)
  const content = reply.firstElementChild
  const parts = [...content.children]
  const answer = parts.pop()
  const text = answer.textContent
  content.replaceChildren(h("div", { "data-slot": "trace" },
    h("span", { "data-slot": "trace-line", "data-status": "running" },
      h("span", { "data-slot": "trace-icon" }, icon("file-text")),
      h("span", { "data-slot": "trace-title" }, "Reading package.json"))))
  root.insertBefore(reply, button)
  await wait(900)
  content.replaceChildren(...parts)
  const words = new Text("")
  answer.replaceChildren(words)
  content.append(answer)
  for (const word of text.match(/\S+\s*/g)) {
    await wait(20)
    words.appendData(word)
  }
  button.textContent = "Reset"
  button.hidden = false
})
