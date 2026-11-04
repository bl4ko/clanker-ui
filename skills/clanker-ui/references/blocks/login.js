import { toast } from "/vendor/clanker-ui/clanker-ui.min.js"

document.getElementById("login-form").addEventListener("form:submit", event => {
  event.preventDefault()
  const submit = event.detail.submitter
  submit.disabled = true
  setTimeout(() => {
    submit.disabled = false
    toast.success("Signed in", { description: `Welcome back, ${event.detail.values.email}.` })
  }, 600)
})
