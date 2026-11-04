import { toast } from "/vendor/clanker-ui/clanker-ui.min.js"

const form = document.getElementById("project-form")
const start = document.getElementById("project-start")
const due = document.getElementById("project-due")
const key = document.getElementById("project-key")

key.addEventListener("input", () => { key.value = key.value.toUpperCase() })

function checkDates() {
  due.setCustomValidity(start.value && due.value && due.value < start.value ? "Select a due date after the start date." : "")
}
start.addEventListener("change", checkDates)
due.addEventListener("change", checkDates)

form.addEventListener("form:submit", event => {
  event.preventDefault()
  const { name } = event.detail.values
  toast.success("Project created", { description: `${name} is ready. Invite your team next.` })
  form.reset()
})
