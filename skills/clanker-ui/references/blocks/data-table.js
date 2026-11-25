import { dialogClose, h, icon, toast } from "/vendor/clanker-ui/clanker-ui.min.js"

const statuses = { backlog: ["circle-question-mark", "Backlog"], todo: ["circle", "Todo"], "in progress": ["timer", "In progress"], done: ["circle-check", "Done"], canceled: ["circle-x", "Canceled"] }
const priorities = { low: ["arrow-down", "Low"], medium: ["arrow-right", "Medium"], high: ["arrow-up", "High"] }
const more = [
  ["TASK-1280", "Bug", "Use the digital TLS panel, then you can transmit the haptic system!", "done", "high"],
  ["TASK-7262", "Feature", "The UTF8 application is down, parse the neural bandwidth so we can back up the PNG firewall!", "done", "high"],
  ["TASK-1138", "Feature", "Generating the driver won't do anything, we need to quantify the 1080p SMTP bandwidth!", "in progress", "medium"],
  ["TASK-7184", "Feature", "We need to program the back-end THX pixel!", "todo", "low"],
  ["TASK-5160", "Documentation", "Calculating the bus won't do anything, we need to navigate the back-end JSON protocol!", "in progress", "high"],
  ["TASK-5618", "Documentation", "Generating the driver won't do anything, we need to index the online SSL application!", "done", "medium"],
  ["TASK-6699", "Documentation", "I'll transmit the wireless JBOD capacitor, that should hard drive the SSD feed!", "backlog", "medium"],
  ["TASK-2858", "Bug", "We need to override the online UDP bus!", "backlog", "medium"],
  ["TASK-9864", "Bug", "I'll reboot the 1080p FTP panel, that should matrix the HEX hard drive!", "done", "high"],
  ["TASK-8404", "Bug", "We need to generate the virtual HEX alarm!", "in progress", "low"],
  ["TASK-5365", "Documentation", "Backing up the pixel won't do anything, we need to transmit the primary IB array!", "in progress", "low"],
]

function taskRow([id, label, title, status, priority]) {
  const [statusIcon, statusText] = statuses[status]
  const [priorityIcon, priorityText] = priorities[priority]
  const item = (action, text, attrs) => h("div", { "data-slot": "dropdown-menu-item", "data-action": action, ...attrs }, text)
  return h("tr", { "data-slot": "table-row", "data-status": status, "data-priority": priority },
    h("td", { "data-slot": "table-cell" }, h("button", { type: "button", "data-slot": "checkbox", "aria-label": `Select ${id}` })),
    h("td", { "data-slot": "table-cell", "data-column": "task", "data-show-from": "xl" }, id),
    h("td", { "data-slot": "table-cell", "data-column": "title" },
      h("span", { "data-slot": "badge", "data-variant": "outline", "data-show-from": "sm" }, label), " ",
      h("span", { "data-slot": "data-table-text", title, "data-show-from": "sm" }, title),
      h("span", { "data-slot": "data-table-text", "data-hide-from": "sm" },
        h("span", { "data-slot": "text-stack" }, h("span", { title }, title), h("span", {}, `${statusText} · ${priorityText} priority`)))),
    h("td", { "data-slot": "table-cell", "data-column": "status", "data-show-from": "sm" }, h("span", { "data-slot": "data-table-text" }, icon(statusIcon), statusText)),
    h("td", { "data-slot": "table-cell", "data-column": "priority", "data-show-from": "lg" }, h("span", { "data-slot": "data-table-text" }, icon(priorityIcon), priorityText)),
    h("td", { "data-slot": "table-cell", "data-align": "end" },
      h("div", { "data-slot": "dropdown-menu" },
        h("button", { type: "button", "data-slot": "button", "data-variant": "ghost", "data-size": "icon-sm", "data-dropdown-menu-trigger": true, "aria-label": `Actions for ${id}` }, icon("ellipsis")),
        h("div", { "data-slot": "dropdown-menu-content", "data-align": "end" },
          item("edit", "Edit", { "data-dialog-trigger": "task-edit" }),
          item("copy", "Make a copy"),
          item("favorite", "Favorite"),
          h("div", { "data-slot": "dropdown-menu-separator" }),
          item("delete", "Delete", { "data-variant": "destructive" })))))
}

const root = document.getElementById("tasks")
const body = root.querySelector("tbody")
const empty = document.getElementById("task-empty")
empty.before(...more.map(taskRow))
const rows = [...body.querySelectorAll("tr[data-status]")]
const filter = document.getElementById("task-filter")
const reset = document.getElementById("task-reset")
const all = root.querySelector('thead [data-slot="checkbox"]')
const selection = root.querySelector('[data-slot="data-table-selection"]')
const pageLabel = document.getElementById("task-page")
const order = { status: Object.keys(statuses), priority: Object.keys(priorities) }
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
  for (const item of root.querySelectorAll("[data-filter] [data-value]")) {
    const key = item.closest("[data-filter]").dataset.filter
    item.querySelector('[data-slot="dropdown-menu-shortcut"]').textContent = rows.filter(row => row.dataset[key] === item.dataset.value).length
  }
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

const editDialog = document.getElementById("task-edit")
const editForm = document.getElementById("task-edit-form")
let editing = null

const read = row => [row.cells[1].textContent, row.querySelector('[data-slot="badge"]').textContent, text(row, "title"), row.dataset.status, row.dataset.priority]

editDialog.addEventListener("dialog:open", event => {
  editing = event.detail.trigger.closest("tr")
  const [id, , title, status, priority] = read(editing)
  editDialog.querySelector('[data-slot="dialog-title"]').textContent = `Edit ${id}`
  document.getElementById("task-edit-title").value = title
  document.getElementById("task-edit-status-select").dataset.value = status
  document.getElementById("task-edit-priority-select").dataset.value = priority
})

editDialog.querySelector("dialog").addEventListener("close", () => editForm.reset())

editForm.addEventListener("form:submit", event => {
  event.preventDefault()
  const [id, label] = read(editing)
  const { title, status, priority } = event.detail.values
  const cells = [...taskRow([id, label, title, status, priority]).cells]
  for (const i of [2, 3, 4]) {
    cells[i].hidden = editing.cells[i].hidden
    editing.cells[i].replaceWith(cells[i])
  }
  Object.assign(editing.dataset, { status, priority })
  dialogClose(editDialog)
  render()
  toast.success("Task updated", { description: `${id} · ${title}` })
})

render()

document.getElementById("task-new").addEventListener("click", () => toast("New task", { description: "The task form opens here." }))
