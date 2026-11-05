import { icon } from "./clanker-ui.js"

const copy = document.getElementById("message-pattern-copy")
let timer

function label(button, text) {
  button.setAttribute("aria-label", text)
  button.closest('[data-slot="tooltip"]').querySelector('[data-slot="tooltip-content"]').firstChild.textContent = text
}

copy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(document.getElementById("message-pattern-reply").innerText)
  } catch {
    return
  }
  copy.replaceChildren(icon("check"))
  label(copy, "Copied")
  clearTimeout(timer)
  timer = setTimeout(() => {
    copy.replaceChildren(icon("copy"))
    label(copy, "Copy")
  }, 2000)
})

const feedback = ["message-pattern-like", "message-pattern-dislike"].map(id => document.getElementById(id))

for (const button of feedback) {
  button.addEventListener("click", () => {
    const pressed = button.getAttribute("aria-pressed") !== "true"
    for (const other of feedback) {
      const on = other === button && pressed
      other.setAttribute("aria-pressed", String(on))
      other.querySelector("svg").classList.toggle("fill-current", on)
    }
  })
}
