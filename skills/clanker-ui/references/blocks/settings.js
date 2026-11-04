import { toast } from "/vendor/clanker-ui/clanker-ui.min.js"

document.getElementById("profile").addEventListener("form:submit", event => {
  event.preventDefault()
  toast.success("Profile saved", { description: `Your profile shows as ${event.detail.values.name}.` })
})

document.getElementById("notifications").addEventListener("switch:change", event => {
  const label = event.target.closest("label").querySelector('[data-slot="field-content"] > [data-slot="field-label"]').textContent
  toast(`${label} emails ${event.detail.checked ? "on" : "off"}`)
})

document.getElementById("notifications").addEventListener("radio-group:change", () => toast("Notification setting saved"))

const nav = document.querySelector('[data-slot="page-nav"]')
nav.addEventListener("click", event => {
  const link = event.target.closest("a")
  if (!link) return
  for (const other of nav.querySelectorAll("a")) other.removeAttribute("aria-current")
  link.setAttribute("aria-current", "page")
})

document.getElementById("delete-account").addEventListener("click", () => {
  toast("Account deletion started", { description: "We send a confirmation to m@example.com." })
})
