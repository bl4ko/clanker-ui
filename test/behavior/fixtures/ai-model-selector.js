const form = document.getElementById("model-selector-demo")
const text = form.querySelector("textarea")
const send = form.querySelector('button[type="submit"]')

for (const [id, name] of [["model-selector-demo-model", "Model"], ["model-selector-demo-effort", "Effort"]]) {
  const menu = document.getElementById(id)
  menu.addEventListener("dropdown-menu:change", event => {
    const trigger = menu.querySelector("[data-dropdown-menu-trigger]")
    const label = event.detail.item.textContent.trim()
    trigger.querySelector("span:last-of-type").textContent = label
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
  send.disabled = true
})
