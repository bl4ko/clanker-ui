import { svg, toast } from "/vendor/clanker-ui/clanker-ui.min.js"

document.getElementById("toast-success").addEventListener("click", () => toast.success("Invoice sent", { description: "INV-1042 went to billing@acme.com." }))
document.getElementById("toast-error").addEventListener("click", () => toast.error("Invoice not sent", { description: "The email server is not available. Try again in a minute." }))

const retry = document.getElementById("retry")
retry.addEventListener("click", () => {
  const icon = retry.firstElementChild
  const spinner = svg("svg", { "data-slot": "spinner", role: "none" })
  retry.disabled = true
  icon.replaceWith(spinner)
  setTimeout(() => {
    spinner.replaceWith(icon)
    retry.disabled = false
    toast.error("Still not available", { description: "We try again in 30 seconds." })
  }, 800)
})
