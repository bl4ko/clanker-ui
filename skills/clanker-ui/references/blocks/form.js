import { calendarGetValue, calendarSetValue, h, icon, toast } from "/vendor/clanker-ui/clanker-ui.min.js"

const form = document.getElementById("project-form")
const key = document.getElementById("project-key")
const budget = document.getElementById("project-budget")
const status = document.getElementById("project-status-select")
const calendar = document.getElementById("project-calendar")
const visibility = document.getElementById("project-visibility")
const summary = Object.fromEntries([...document.querySelectorAll("[data-summary]")].map(el => [el.dataset.summary, el]))
const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 })
const labels = { planned: "Planned", active: "Active", paused: "Paused", private: "Private", team: "Team", public: "Public" }
const project = { name: "Website redesign", key: "WEB", description: "New marketing site with a faster checkout.", status: "active", budget: 48000, timeline: "2026-10-05/2026-12-11", visibility: "team" }
const editing = new URLSearchParams(location.search).get("id") === "web"
let state = { status: "", visibility: "team" }

function weeks(range) {
  if (!range?.from || !range?.to) return 0
  return Math.max(1, Math.round((Date.parse(range.to) - Date.parse(range.from)) / 6048e5))
}

function render() {
  const range = calendarGetValue(calendar)
  const amount = Number(budget.value)
  const span = weeks(range)
  summary.key.textContent = key.value || "—"
  summary.status.textContent = labels[state.status] ?? "—"
  summary.budget.textContent = budget.value ? money.format(amount) : "—"
  summary.weekly.textContent = budget.value && span ? money.format(amount / span) : "—"
  summary.duration.textContent = span ? `${span} weeks` : "—"
  summary.visibility.textContent = labels[state.visibility]
}

key.addEventListener("input", () => { key.value = key.value.toUpperCase() })
form.addEventListener("input", render)
status.addEventListener("select:change", event => { state.status = event.detail.value; render() })
visibility.addEventListener("radio-group:change", event => { state.visibility = event.detail.value; render() })
calendar.addEventListener("calendar:change", render)

if (editing) {
  document.title = `Edit ${project.name} - Acme Inc.`
  document.getElementById("project-title").textContent = project.name
  document.querySelector('[data-slot="breadcrumb-page"]').textContent = project.name
  document.getElementById("project-lead").replaceChildren(h("span", { "data-slot": "badge", "data-variant": "info" }, icon("clock"), "Active"), " Created Oct 2 by Olivia Martin. 42 of 68 tasks done.")
  document.getElementById("project-submit").textContent = "Save changes"
  document.getElementById("project-danger").hidden = false
  document.getElementById("project-name").value = project.name
  key.value = project.key
  document.getElementById("project-description").value = project.description
  budget.value = project.budget
  status.dataset.value = project.status
  document.getElementById(`visibility-${project.visibility}`).setAttribute("data-checked", "")
  calendarSetValue(calendar, project.timeline)
  state = { status: project.status, visibility: project.visibility }
}
render()

form.addEventListener("form:submit", event => {
  event.preventDefault()
  const { name } = event.detail.values
  if (editing) {
    toast.success("Changes saved", { description: `${name} is up to date.` })
    return
  }
  toast.success("Project created", { description: `${name} is ready. Invite your team next.` })
  form.reset()
})

form.addEventListener("reset", () => setTimeout(() => { state = { status: "", visibility: "team" }; render() }))

document.getElementById("project-delete").addEventListener("click", () => {
  toast("Project deleted", { description: `${project.name} and its tasks are in the trash for 30 days.` })
})
