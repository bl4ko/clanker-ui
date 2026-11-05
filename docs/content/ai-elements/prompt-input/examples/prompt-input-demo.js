import { h, icon } from "./clanker-ui.js"

const form = document.getElementById("prompt-input-demo")
const text = document.getElementById("prompt-input-demo-text")
const files = document.getElementById("prompt-input-demo-files")
const list = document.getElementById("prompt-input-demo-list")
const send = form.querySelector('button[type="submit"]')

function attachment(name) {
  const item = h("div", { "data-slot": "attachment", "data-size": "sm" },
    h("div", { "data-slot": "attachment-media" }, icon("file-text")),
    h("div", { "data-slot": "attachment-content" }, h("span", { "data-slot": "attachment-title" }, name)),
    h("div", { "data-slot": "attachment-actions" },
      h("button", { type: "button", "data-slot": "attachment-action", "aria-label": `Remove ${name}`, onclick: () => {
        item.remove()
        list.hidden = list.children.length === 0
        text.focus()
      } }, icon("x"))))
  return item
}

document.getElementById("prompt-input-demo-attach").addEventListener("click", () => files.click())

files.addEventListener("change", () => {
  list.append(...Array.from(files.files, file => attachment(file.name)))
  list.hidden = list.children.length === 0
  files.value = ""
})

for (const [id, name] of [["prompt-input-demo-model", "Model"], ["prompt-input-demo-effort", "Effort"]]) {
  const menu = document.getElementById(id)
  menu.addEventListener("dropdown-menu:change", event => {
    const trigger = menu.querySelector("[data-dropdown-menu-trigger]")
    const label = event.detail.item.textContent.trim()
    trigger.querySelector("svg").previousSibling.replaceWith(label)
    trigger.setAttribute("aria-label", `${name}: ${label}`)
  })
}

text.addEventListener("input", () => {
  send.disabled = text.value.trim() === ""
})

text.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault()
    form.requestSubmit()
  }
})

form.addEventListener("submit", event => {
  event.preventDefault()
  if (text.value.trim() === "") return
  text.value = ""
  list.replaceChildren()
  list.hidden = true
  send.disabled = true
})
