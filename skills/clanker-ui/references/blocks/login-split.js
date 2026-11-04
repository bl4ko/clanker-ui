import { svg, toast } from "/vendor/clanker-ui/clanker-ui.min.js"

const form = document.getElementById("login-form")
const email = document.getElementById("email")

form.addEventListener("form:submit", event => {
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

document.getElementById("magic-link").addEventListener("click", () => {
  if (!email.checkValidity()) {
    email.focus()
    toast.error("Enter your email first", { description: "We send the sign-in link to that address." })
    return
  }
  toast.success("Check your email", { description: `We sent a sign-in link to ${email.value}. It works for 15 minutes.` })
})
