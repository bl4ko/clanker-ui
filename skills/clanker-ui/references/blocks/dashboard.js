import { chart } from "/vendor/clanker-ui/clanker-ui-chart.min.js"

const desktop = [222, 97, 167, 242, 373, 301, 245, 409, 59, 261, 327, 292, 342, 137, 120, 138, 446, 364, 243, 89, 137, 224, 138, 387, 215, 75, 383, 122, 315, 454, 165, 293, 247, 385, 481, 498, 388, 149, 227, 293, 335, 197, 197, 448, 473, 338, 499, 315, 235, 177, 82, 81, 252, 294, 201, 213, 420, 233, 78, 340, 178, 178, 470, 103, 439, 88, 294, 323, 385, 438, 155, 92, 492, 81, 426, 307, 371, 475, 107, 341, 408, 169, 317, 480, 132, 141, 434, 448, 149, 103, 446]
const mobile = [150, 180, 120, 260, 290, 340, 180, 320, 110, 190, 350, 210, 380, 220, 170, 190, 360, 410, 180, 150, 200, 170, 230, 290, 250, 130, 420, 180, 240, 380, 220, 310, 190, 420, 390, 520, 300, 210, 180, 330, 270, 240, 160, 490, 380, 400, 420, 350, 180, 230, 140, 120, 290, 220, 250, 170, 460, 190, 130, 280, 230, 200, 410, 160, 380, 140, 250, 370, 320, 480, 200, 150, 420, 130, 380, 350, 310, 520, 170, 290, 450, 210, 270, 530, 180, 190, 380, 490, 200, 160, 400]
const start = Date.UTC(2024, 3, 1)
const rows = desktop.map((value, i) => ({ date: new Date(start + i * 864e5).toISOString().slice(0, 10), desktop: value, mobile: mobile[i] }))
const days = { "90d": 90, "30d": 30, "7d": 7 }

const visitors = chart(document.getElementById("visitors-chart"), {
  rows,
  config: { desktop: { label: "Desktop", color: "chart-1" }, mobile: { label: "Mobile", color: "chart-2" } },
}, {
  type: "area", x: "date", scale: "time", stack: true, gradient: true, height: 250, valueAxis: false, legend: false,
  xFormat: { month: "short", day: "numeric", timeZone: "UTC" }, locale: "en-US", label: "Total visitors",
})

const toggle = document.getElementById("visitors-range")
const select = document.getElementById("visitors-range-select")
let range = ""

function setRange(value) {
  if (!days[value] || value === range) return
  range = value
  visitors.update({ rows: rows.slice(-days[value]) })
  const label = { "90d": "last 3 months", "30d": "last 30 days", "7d": "last 7 days" }[value]
  for (const span of document.querySelectorAll("[data-range-label]")) span.textContent = span.closest("[data-hide-from]") ? label[0].toUpperCase() + label.slice(1) : label
  if (toggle.dataset.value !== value) toggle.dataset.value = value
  if (select.dataset.value !== value) select.dataset.value = value
}

toggle.addEventListener("toggle-group:change", event => {
  if (event.detail.value) setRange(event.detail.value)
  else toggle.dataset.value = range
})
select.addEventListener("select:change", event => setRange(event.detail.value))
setRange(matchMedia("(width < 48rem)").matches ? "7d" : "90d")

const table = document.getElementById("outline-table")
const all = table.querySelector('thead [data-slot="checkbox"]')
const boxes = [...table.querySelectorAll('tbody [data-slot="checkbox"]')]
const status = table.querySelector('[data-slot="data-table-selection"]')

function sync() {
  const count = boxes.filter(box => box.hasAttribute("data-checked")).length
  all.toggleAttribute("data-checked", count === boxes.length)
  all.toggleAttribute("data-indeterminate", count > 0 && count < boxes.length)
  status.textContent = `${count} of 68 row(s) selected.`
  for (const box of boxes) box.closest("tr").dataset.state = box.hasAttribute("data-checked") ? "selected" : ""
}

table.addEventListener("checkbox:change", event => {
  if (event.target === all) for (const box of boxes) box.toggleAttribute("data-checked", event.detail.checked)
  sync()
})

document.getElementById("columns-menu").closest('[data-slot="dropdown-menu"]').addEventListener("dropdown-menu:change", event => {
  const column = event.detail.value
  const head = table.querySelector(`th[data-column="${column}"]`)
  const index = [...head.parentElement.children].indexOf(head)
  for (const tr of table.querySelectorAll("tr")) tr.children[index].hidden = !event.detail.checked
})
