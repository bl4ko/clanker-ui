import { toast } from "/vendor/clanker-ui/clanker-ui.min.js"

const root = document.getElementById("tasks")
const body = root.querySelector("tbody")
const rows = [...body.querySelectorAll("tr[data-status]")]
const empty = document.getElementById("task-empty")
const filter = document.getElementById("task-filter")
const reset = document.getElementById("task-reset")
const all = root.querySelector('thead [data-slot="checkbox"]')
const selection = root.querySelector('[data-slot="data-table-selection"]')
const pageLabel = document.getElementById("task-page")
const order = { status: ["backlog", "todo", "in progress", "done", "canceled"], priority: ["low", "medium", "high"] }
const facets = { status: new Set(), priority: new Set() }
let sort = { key: "", dir: 1 }
let page = 0
let size = 10

const text = (row, key) => key === "title" ? row.cells[2].querySelector("[title]").title : row.dataset[key]
const compare = (a, b, key) => order[key] ? order[key].indexOf(a.dataset[key]) - order[key].indexOf(b.dataset[key]) : text(a, key).localeCompare(text(b, key))

function matches(row) {
  const query = filter.value.trim().toLowerCase()
  return (!query || row.textContent.toLowerCase().includes(query)) &&
    (!facets.status.size || facets.status.has(row.dataset.status)) &&
    (!facets.priority.size || facets.priority.has(row.dataset.priority))
}

function render() {
  const shown = rows.filter(matches)
  if (sort.key) shown.sort((a, b) => compare(a, b, sort.key) * sort.dir)
  const pages = Math.max(1, Math.ceil(shown.length / size))
  page = Math.min(page, pages - 1)
  const visible = new Set(shown.slice(page * size, page * size + size))
  for (const row of rows) row.hidden = !visible.has(row)
  body.prepend(...shown, ...rows.filter(row => !shown.includes(row)))
  body.append(empty)
  empty.hidden = shown.length > 0
  pageLabel.textContent = `Page ${shown.length ? page + 1 : 0} of ${shown.length ? pages : 0}`
  root.querySelector('[data-page="first"]').disabled = root.querySelector('[data-page="previous"]').disabled = page === 0
  root.querySelector('[data-page="last"]').disabled = root.querySelector('[data-page="next"]').disabled = page >= pages - 1
  const filtered = filter.value.trim() !== "" || facets.status.size > 0 || facets.priority.size > 0
  reset.hidden = !filtered
  syncSelection()
}

function syncSelection() {
  const boxes = rows.filter(row => !row.hidden).map(row => row.querySelector('[data-slot="checkbox"]'))
  const checked = rows.filter(row => row.querySelector('[data-slot="checkbox"]').hasAttribute("data-checked")).length
  const visibleChecked = boxes.filter(box => box.hasAttribute("data-checked")).length
  all.toggleAttribute("data-checked", boxes.length > 0 && visibleChecked === boxes.length)
  all.toggleAttribute("data-indeterminate", visibleChecked > 0 && visibleChecked < boxes.length)
  selection.textContent = `${checked} of ${rows.filter(matches).length} row(s) selected.`
  for (const row of rows) row.dataset.state = row.querySelector('[data-slot="checkbox"]').hasAttribute("data-checked") ? "selected" : ""
}

function clearFilters() {
  filter.value = ""
  for (const [key, set] of Object.entries(facets)) {
    set.clear()
    const menu = root.querySelector(`[data-filter="${key}"]`)
    for (const item of menu.querySelectorAll("[data-value]")) item.removeAttribute("data-checked")
    menu.querySelector('[data-slot="badge"]').hidden = true
  }
  page = 0
  render()
}

filter.addEventListener("input", () => { page = 0; render() })
reset.addEventListener("click", clearFilters)
document.getElementById("task-clear").addEventListener("click", clearFilters)

for (const menu of root.querySelectorAll("[data-filter]")) {
  menu.addEventListener("dropdown-menu:change", event => {
    const set = facets[menu.dataset.filter]
    if (event.detail.checked) set.add(event.detail.value)
    else set.delete(event.detail.value)
    const badge = menu.querySelector('[data-slot="badge"]')
    badge.hidden = set.size === 0
    badge.textContent = `${set.size} selected`
    page = 0
    render()
  })
}

document.getElementById("task-view").addEventListener("dropdown-menu:change", event => {
  for (const cell of root.querySelectorAll(`[data-column="${event.detail.value}"]`)) cell.hidden = !event.detail.checked
})

root.addEventListener("table:sort", event => {
  event.preventDefault()
  const key = event.target.tHead.rows[0].cells[event.detail.column].dataset.column
  sort = event.detail.dir === "none" ? { key: "", dir: 1 } : { key, dir: event.detail.dir === "ascending" ? 1 : -1 }
  render()
})

root.addEventListener("checkbox:change", event => {
  if (event.target === all) {
    for (const row of rows) if (!row.hidden) row.querySelector('[data-slot="checkbox"]').toggleAttribute("data-checked", event.detail.checked)
  }
  syncSelection()
})

root.addEventListener("click", event => {
  const step = event.target.closest("[data-page]")?.dataset.page
  if (!step) return
  const pages = Math.ceil(rows.filter(matches).length / size)
  page = { first: 0, previous: page - 1, next: page + 1, last: pages - 1 }[step]
  render()
})

document.getElementById("task-page-size-select").addEventListener("select:change", event => {
  size = Number(event.detail.value)
  page = 0
  render()
})

root.addEventListener("dropdown-menu:select", event => {
  const row = event.detail.item.closest("tr")
  if (!row || event.detail.item.dataset.action !== "delete") return
  const index = rows.indexOf(row)
  rows.splice(index, 1)
  row.remove()
  render()
  toast("Task deleted", {
    description: row.cells[1].textContent,
    action: { label: "Undo", onClick: () => { rows.splice(index, 0, row); body.append(row); render() } },
  })
})

render()

document.getElementById("task-new").addEventListener("click", () => toast("New task", { description: "The task form opens here." }))
