import { svg, toast } from "/vendor/clanker-ui/clanker-ui.min.js"

document.getElementById("login-form").addEventListener("form:submit", event => {
  event.preventDefault()
  const submit = event.detail.submitter
  const spinner = svg("svg", { "data-slot": "spinner", role: "none" })
  submit.disabled = true
  submit.prepend(spinner)
  setTimeout(() => {
    spinner.remove()
    submit.disabled = false
    toast.success("Signed in", { description: `Welcome back, ${event.detail.values.email}.` })
  }, 600)
})
