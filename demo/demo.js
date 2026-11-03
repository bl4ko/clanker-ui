import * as ui from "../clanker-ui.js"

const demoTokens = ["background", "foreground", "card", "card-foreground", "popover", "popover-foreground", "primary", "primary-foreground", "secondary", "secondary-foreground", "muted", "muted-foreground", "accent", "accent-foreground", "destructive", "border", "input", "ring", "chart-1", "chart-2", "chart-3", "chart-4", "chart-5", "chart-6", "chart-7", "chart-8", "sidebar", "sidebar-foreground", "sidebar-primary", "sidebar-primary-foreground", "sidebar-accent", "sidebar-accent-foreground", "sidebar-border", "sidebar-ring"]
const demoRadii = ["sm", "md", "lg", "xl", "2xl", "3xl", "4xl"]
const demoNav = document.getElementById("demo-nav")
const demoNarrow = matchMedia("(max-width: 767px)")
function demoNavMode() {
  if (!demoNarrow.matches && demoNav.matches(":popover-open")) demoNav.hidePopover()
  demoNav.popover = demoNarrow.matches ? "auto" : null
}
demoNavMode()
demoNarrow.addEventListener("change", demoNavMode)
const demoLinks = [...demoNav.querySelectorAll('a[href^="#"]')]

document.getElementById("h-proof").replaceChildren(ui.h("code", null, '<img src="x" onerror="alert(document.domain)">'))

document.getElementById("theme-colors").replaceChildren(
  ...demoTokens.map(token => ui.h("div", { "data-demo": "swatch" }, ui.h("div", { "data-demo": "swatch-chip", style: { background: `var(--${token})` } }), ui.h("code", null, `--${token}`))),
)

document.getElementById("theme-radius").replaceChildren(
  ...demoRadii.map(size => ui.h("div", { "data-demo": "radius" }, ui.h("div", { "data-demo": "radius-box", style: { borderRadius: `var(--radius-${size})` } }), `radius-${size}`)),
)

document.getElementById("icon-grid").replaceChildren(...ui.iconNames.map(name => ui.h("div", { "data-demo": "icon-tile", title: name }, ui.icon(name), name)))
document.getElementById("icon-grid").after(ui.h("p", { "data-demo": "icon-count" }, `${ui.iconNames.length} icons. Aliases: loader-2, more-horizontal, more-vertical, home, trash-2, filter, circle-help.`))

const demoSchemeGrid = document.getElementById("scheme-grid")
const demoBaseSchemes = ui.theme.schemes.filter(s => s.group !== "accent")
const demoSwatchTokens = ["primary", "secondary", "accent", "destructive", "chart-1", "chart-2", "chart-3", "chart-4", "chart-5"]
demoSchemeGrid.replaceChildren(
  ...demoBaseSchemes.map(({ value, label }) =>
    ui.h(
      "button",
      { type: "button", "data-demo": "scheme-tile", "data-scheme": value, "data-value": value, "aria-pressed": "false" },
      ui.h("span", { "data-demo": "scheme-name" }, label),
      ui.h("span", { "data-demo": "scheme-sample", "aria-hidden": "true" }, ui.h("span", null, "Aa"), ui.h("span", { "data-demo": "scheme-muted" }, "muted")),
      ui.h("span", { "data-demo": "scheme-swatches", "aria-hidden": "true" }, ...demoSwatchTokens.map(token => ui.h("span", { "data-demo": "scheme-swatch", style: { background: `var(--${token})` } }))),
    ),
  ),
)
demoSchemeGrid.addEventListener("click", event => {
  const tile = event.target.closest("[data-demo='scheme-tile']")
  if (!tile) return
  const bases = new Set(demoBaseSchemes.map(s => s.value))
  ui.theme.setScheme([tile.dataset.value, ...ui.theme.scheme().split(" ").filter(t => t && !bases.has(t))].join(" "))
})

function demoThemeStatus() {
  document.getElementById("theme-status").textContent = `Mode: ${ui.theme.get()}. Showing ${ui.theme.resolved()}.`
  const scheme = ui.theme.scheme()
  document.getElementById("scheme-status").textContent = `Scheme: ${scheme || "none (kit default)"}.`
  const tokens = scheme.split(" ")
  const base = demoBaseSchemes.find(s => tokens.includes(s.value))?.value ?? "neutral"
  for (const tile of demoSchemeGrid.children) tile.setAttribute("aria-pressed", String(tile.dataset.value === base))
}
demoThemeStatus()
document.documentElement.addEventListener("theme:change", demoThemeStatus)

demoNav.addEventListener("click", event => {
  if (event.target.closest("a") && demoNav.matches(":popover-open")) demoNav.hidePopover()
})

const demoSections = [...document.querySelectorAll('[data-demo="section"], [data-demo="hero"]')]
let demoFrame = 0
let demoCurrent = null
function demoReveal(link) {
  if (!demoNav.checkVisibility()) return
  const edge = 48
  const nav = demoNav.getBoundingClientRect()
  const r = link.getBoundingClientRect()
  if (r.top < nav.top + edge) demoNav.scrollTop -= nav.top + edge - r.top
  else if (r.bottom > nav.bottom - edge) demoNav.scrollTop += r.bottom - nav.bottom + edge
}
function demoTrack() {
  demoFrame = 0
  let current = demoSections[0]
  for (const section of demoSections) if (section.getBoundingClientRect().top <= 120) current = section
  const link = demoLinks.find(l => l.hash === `#${current.id}`) ?? null
  if (link === demoCurrent) return
  demoCurrent?.removeAttribute("aria-current")
  demoCurrent = link
  if (!link) return
  link.setAttribute("aria-current", "true")
  demoReveal(link)
}
addEventListener("scroll", () => {
  if (!demoFrame) demoFrame = requestAnimationFrame(demoTrack)
}, { passive: true })
demoNav.addEventListener("toggle", event => {
  if (event.newState === "open" && demoCurrent) demoReveal(demoCurrent)
})
demoTrack()
const formDemo = document.getElementById("form-profile")
const formDemoResult = document.getElementById("form-result")

formDemo.addEventListener("form:submit", event => {
  event.preventDefault()
  formDemoResult.textContent = `Submitted: ${JSON.stringify(event.detail.values)}`
})
formDemo.addEventListener("form:invalid", event => {
  const count = event.detail.errors.length
  formDemoResult.textContent = `${count} ${count === 1 ? "field needs" : "fields need"} attention.`
})
formDemo.addEventListener("reset", () => {
  formDemoResult.textContent = ""
})
document.getElementById("form-items").addEventListener("form:submit", event => event.preventDefault())
document.getElementById("field-checkout").addEventListener("submit", event => event.preventDefault())

const fieldDemoPrice = document.getElementById("field-price")
fieldDemoPrice.addEventListener("input", () => {
  const [low, high] = fieldDemoPrice.querySelectorAll("input")
  document.getElementById("field-price-min").textContent = low.value
  document.getElementById("field-price-max").textContent = high.value
})

const inputOtpDemoValue = document.getElementById("input-otp-value")
document.getElementById("input-otp-controlled").addEventListener("input", event => {
  inputOtpDemoValue.textContent = event.target.value ? `You entered: ${event.target.value}` : "Enter your one-time password."
})

const sliderDemoTemperature = document.getElementById("slider-temperature")
sliderDemoTemperature.addEventListener("input", () => {
  document.getElementById("slider-temperature-value").textContent = [...sliderDemoTemperature.querySelectorAll("input")].map(i => i.value).join(", ")
})

document.getElementById("select-align").addEventListener("switch:change", event => {
  document.querySelector('#select-aligned [data-slot="select-content"]').dataset.alignTrigger = String(event.detail.checked)
})

document.getElementById("toggle-group-weight").addEventListener("toggle-group:change", event => {
  document.querySelector("#toggle-group-weight-text code").textContent = `font-${event.detail.value || "normal"}`
})
const toastDemoActions = {
  demo: () => ui.toast("Event has been created", { description: "Sunday, December 03, 2023 at 9:00 AM", action: { label: "Undo", onClick: () => ui.toast("Event restored") } }),
  default: () => ui.toast("Event has been created"),
  success: () => ui.toast.success("Event has been created"),
  info: () => ui.toast.info("Be at the area 10 minutes before the event time"),
  warning: () => ui.toast.warning("Event start time cannot be earlier than 8am"),
  error: () => ui.toast.error("Event has not been created"),
  promise: () => ui.toast.promise(() => new Promise(resolve => setTimeout(() => resolve({ name: "Event" }), 2000)), { loading: "Loading...", success: data => `${data.name} has been created`, error: "Error" }),
  description: () => ui.toast("Event has been created", { description: "Monday, January 3rd at 6:00pm" }),
  "toast-demo": () => {
    const id = ui.toast.add({ title: "Event created", description: "Sunday, December 3 at 9:00 AM", actionProps: { children: "Undo", onClick: () => ui.toast.close(id) } })
  },
  "add-default": () => ui.toast.add({ description: "Event has been created." }),
  "add-success": () => ui.toast.add({ type: "success", description: "Event has been created." }),
  "add-info": () => ui.toast.add({ type: "info", description: "Arrive 10 minutes before the event." }),
  "add-warning": () => ui.toast.add({ type: "warning", description: "The event cannot start before 8:00 AM." }),
  "add-error": () => ui.toast.add({ type: "error", description: "The event could not be created.", priority: "high" }),
  "add-promise": () => ui.toast.promise(new Promise(resolve => setTimeout(() => resolve({ name: "Event" }), 2000)), { loading: "Creating event…", success: data => `${data.name} created.`, error: "Could not create event." }),
  loading: () => {
    const id = ui.toast.loading("Uploading report.pdf...")
    setTimeout(() => ui.toast.success("Upload complete", { id }), 1500)
  },
  sticky: () => ui.toast("This toast stays until you close it", { timeout: 0 }),
  dismiss: () => ui.toast.close(),
  stack: () => {
    ;["First", "Second", "Third", "Fourth"].forEach((name, i) => setTimeout(() => ui.toast(`${name} notification`, { description: "Hover the stack to expand it." }), i * 150))
  },
}

document.addEventListener("click", event => {
  const button = event.target instanceof Element ? event.target.closest("[data-demo-toast]") : null
  if (button) toastDemoActions[button.dataset.demoToast]?.(button)
})

const drawerDemoBars = document.getElementById("drawer-bars")
let drawerDemoGoal = 350

drawerDemoBars?.replaceChildren(...[400, 300, 200, 300, 200, 278, 189, 239, 300, 200, 278, 189, 349].map(value => ui.h("span", { style: { height: `${value / 4}%` } })))

document.addEventListener("click", event => {
  const button = event.target instanceof Element ? event.target.closest("[data-drawer-goal]") : null
  if (!button) return
  drawerDemoGoal = Math.max(200, Math.min(400, drawerDemoGoal + Number(button.dataset.drawerGoal)))
  document.getElementById("drawer-goal").textContent = String(drawerDemoGoal)
  for (const control of document.querySelectorAll("[data-drawer-goal]")) control.disabled = Number(control.dataset.drawerGoal) < 0 ? drawerDemoGoal <= 200 : drawerDemoGoal >= 400
})

const drawerDemo = document.getElementById("drawer-demo")
const drawerMobile = matchMedia("(max-width: 767px)")
const drawerDemoMode = () => {
  for (const root of [drawerDemo, ...document.querySelectorAll("[data-demo-responsive-drawer]")]) {
    root.dataset.swipeDirection = drawerMobile.matches ? "down" : "right"
    root.toggleAttribute("data-show-swipe-handle", drawerMobile.matches)
  }
}
drawerDemoMode()
drawerMobile.addEventListener("change", drawerDemoMode)

document.getElementById("drawer-responsive")?.addEventListener("click", event => {
  ui.dialogOpen(matchMedia("(min-width: 768px)").matches ? "drawer-responsive-dialog" : "drawer-responsive-drawer", { trigger: event.currentTarget })
})

document.addEventListener("keydown", event => {
  if ((event.key !== "k" && event.key !== "K") || !(event.metaKey || event.ctrlKey) || event.altKey || event.shiftKey) return
  if (event.ctrlKey && !event.metaKey && event.target instanceof Element && event.target.closest('[data-slot="command"]')) return
  event.preventDefault()
  if (!ui.dialogClose("command-dialog", "shortcut")) ui.dialogOpen("command-dialog")
})

document.getElementById("command-palette")?.addEventListener("command:select", event => {
  ui.dialogClose("command-dialog", "select")
  ui.toast(`Selected ${event.detail.item.textContent.trim().replace(/⌘.$/, "")}`)
})

document.getElementById("dialog-demo")?.addEventListener("dialog:close", event => {
  if (event.detail.reason === "submit") ui.toast.success("Profile updated")
})
const carouselDemo = document.getElementById("carousel-demo")
carouselDemo.addEventListener("carousel:change", event => {
  document.getElementById("carousel-count").textContent = `Slide ${event.detail.value + 1} of ${event.detail.count}`
})

function progressDemoStep(delta) {
  const bar = document.getElementById("progress-demo")
  const value = Math.min(100, Math.max(0, Number(bar.dataset.value) + delta))
  bar.dataset.value = String(value)
  document.getElementById("progress-text").textContent = `${value}%`
}
document.getElementById("progress-less").addEventListener("click", () => progressDemoStep(-10))
document.getElementById("progress-more").addEventListener("click", () => progressDemoStep(10))

document.getElementById("scroll-area-tags").append(...Array.from({ length: 50 }, (_, i) => [ui.h("div", null, `v1.2.0-beta.${50 - i}`), ui.h("div", { "data-slot": "separator" })]).flat())

const tablePayments = [
  { id: "m5gr84i9", amount: 316, status: "success", email: "ken99@example.com" },
  { id: "3u1reuv4", amount: 242, status: "success", email: "Abe45@example.com" },
  { id: "derv1ws0", amount: 837, status: "processing", email: "Monserrat44@example.com" },
  { id: "5kma53ae", amount: 874, status: "success", email: "Silas22@example.com" },
  { id: "bhqecj4p", amount: 721, status: "failed", email: "carmella@example.com" },
  { id: "p0q8k2lm", amount: 129, status: "pending", email: "lena.ortiz@example.com" },
  { id: "x7c1v9bn", amount: 560, status: "success", email: "omar.haddad@example.com" },
  { id: "r4t6y8ui", amount: 95, status: "failed", email: "priya.k@example.com" },
  { id: "a2s4d6fg", amount: 410, status: "processing", email: "jonas.berg@example.com" },
  { id: "h8j6k4lq", amount: 688, status: "success", email: "mei.tanaka@example.com" },
  { id: "z1x3c5vb", amount: 233, status: "pending", email: "diego.ramos@example.com" },
  { id: "w9e7r5ty", amount: 999, status: "success", email: "ana.novak@example.com" },
]
const tableColumns = [
  { key: "status", label: "Status" },
  { key: "email", label: "Email", sort: true },
  { key: "amount", label: "Amount", sort: true, end: true },
]
const tableState = { sort: null, desc: false, filter: "", page: 0, size: 5, selected: new Set(), hidden: new Set() }
const tableMoney = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" })
const tableRoot = document.getElementById("table-data")

function tableFiltered() {
  const query = tableState.filter.trim().toLowerCase()
  const rows = tablePayments.filter(p => p.email.toLowerCase().includes(query))
  if (!tableState.sort) return rows
  const key = tableState.sort
  const sign = tableState.desc ? -1 : 1
  return [...rows].sort((a, b) => sign * (key === "amount" ? a.amount - b.amount : a[key].localeCompare(b[key], "en", { sensitivity: "base" })))
}

function tablePageRows() {
  const rows = tableFiltered()
  const pages = Math.max(1, Math.ceil(rows.length / tableState.size))
  tableState.page = Math.min(tableState.page, pages - 1)
  return { rows, pages, visible: rows.slice(tableState.page * tableState.size, (tableState.page + 1) * tableState.size) }
}

function tableSort(key) {
  if (tableState.sort !== key) {
    tableState.sort = key
    tableState.desc = false
  } else if (!tableState.desc) tableState.desc = true
  else tableState.sort = null
  tableRender()
}

function tableHead(column) {
  const sorted = tableState.sort === column.key
  const label = column.sort
    ? ui.h("button", { type: "button", "data-slot": "button", "data-variant": "ghost", "data-sort-key": column.key, onclick: () => tableSort(column.key) }, column.label, ui.icon(sorted ? (tableState.desc ? "arrow-down" : "arrow-up") : "arrow-up-down"))
    : column.label
  return ui.h("th", { "data-slot": "table-head", "data-demo": column.end ? "table-end" : null, "aria-sort": sorted ? (tableState.desc ? "descending" : "ascending") : null }, label)
}

function tableCell(column, row) {
  if (column.key === "amount") return ui.h("td", { "data-slot": "table-cell", "data-demo": "table-end table-strong" }, tableMoney.format(row.amount))
  if (column.key === "status") return ui.h("td", { "data-slot": "table-cell" }, row.status[0].toUpperCase() + row.status.slice(1))
  return ui.h("td", { "data-slot": "table-cell" }, row.email.toLowerCase())
}

function tableActions(row) {
  return ui.h(
    "div",
    { "data-slot": "dropdown-menu" },
    ui.h("button", { type: "button", "data-slot": "button", "data-variant": "ghost", "data-size": "icon-sm", "data-dropdown-menu-trigger": "", "aria-label": `Open menu for ${row.email}` }, ui.icon("ellipsis")),
    ui.h(
      "div",
      { "data-slot": "dropdown-menu-content", "data-align": "end" },
      ui.h("div", { "data-slot": "dropdown-menu-label" }, "Actions"),
      ui.h("div", { "data-slot": "dropdown-menu-item", "data-value": `copy:${row.id}` }, "Copy payment ID"),
      ui.h("div", { "data-slot": "dropdown-menu-separator" }),
      ui.h("div", { "data-slot": "dropdown-menu-item", "data-value": "customer" }, "View customer"),
      ui.h("div", { "data-slot": "dropdown-menu-item", "data-value": "details" }, "View payment details"),
    ),
  )
}

const tableSelectAll = ui.h("button", {
  type: "button",
  "data-slot": "checkbox",
  "aria-label": "Select all",
  "oncheckbox:change": event => {
    for (const row of tablePageRows().visible) {
      if (event.detail.checked) tableState.selected.add(row.id)
      else tableState.selected.delete(row.id)
    }
    tableSync()
  },
})
const tableFilter = ui.h("input", {
  type: "search",
  "data-slot": "input",
  placeholder: "Filter emails...",
  "aria-label": "Filter emails",
  oninput: event => {
    tableState.filter = event.target.value
    tableState.page = 0
    tableRender()
  },
})
const tableColumnMenu = ui.h(
  "div",
  {
    "data-slot": "dropdown-menu",
    "ondropdown-menu:change": event => {
      if (event.detail.checked) tableState.hidden.delete(event.detail.value)
      else tableState.hidden.add(event.detail.value)
      tableRender()
    },
  },
  ui.h("button", { type: "button", "data-slot": "button", "data-variant": "outline", "data-dropdown-menu-trigger": "" }, "Columns", ui.icon("chevron-down")),
  ui.h("div", { "data-slot": "dropdown-menu-content", "data-align": "end" }, tableColumns.map(c => ui.h("div", { "data-slot": "dropdown-menu-checkbox-item", "data-value": c.key, "data-state": "checked" }, c.label))),
)
const tableHeadRow = ui.h("tr", { "data-slot": "table-row" })
const tableBody = ui.h("tbody", { "data-slot": "table-body" })
const tableCount = ui.h("p", { "aria-live": "polite" })
const tablePrevious = ui.h("button", { type: "button", "data-slot": "button", "data-variant": "outline", "data-size": "sm", onclick: () => tableTurn(-1) }, "Previous")
const tableNext = ui.h("button", { type: "button", "data-slot": "button", "data-variant": "outline", "data-size": "sm", onclick: () => tableTurn(1) }, "Next")
const tablePageLabel = ui.h("span", { "data-demo": "table-page" })

function tableTurn(delta) {
  tableState.page += delta
  tableRender()
}

function tableSync() {
  const { rows, visible } = tablePageRows()
  for (const tr of tableBody.querySelectorAll("tr[data-id]")) {
    const on = tableState.selected.has(tr.dataset.id)
    if (on) tr.dataset.state = "selected"
    else delete tr.dataset.state
    tr.querySelector('[data-slot="checkbox"]').toggleAttribute("data-checked", on)
  }
  const picked = visible.filter(r => tableState.selected.has(r.id)).length
  tableSelectAll.toggleAttribute("data-checked", visible.length > 0 && picked === visible.length)
  tableSelectAll.toggleAttribute("data-indeterminate", picked > 0 && picked < visible.length)
  const total = rows.filter(r => tableState.selected.has(r.id)).length
  tableCount.textContent = `${total} of ${rows.length} row(s) selected.`
}

function tableRender() {
  const { pages, visible } = tablePageRows()
  const columns = tableColumns.filter(c => !tableState.hidden.has(c.key))
  const focused = document.activeElement?.closest("[data-sort-key]")?.dataset.sortKey
  tableHeadRow.replaceChildren(ui.h("th", { "data-slot": "table-head" }, tableSelectAll), ...columns.map(tableHead), ui.h("th", { "data-slot": "table-head" }, ui.h("span", { class: "sr-only" }, "Actions")))
  if (focused) tableHeadRow.querySelector(`[data-sort-key="${focused}"]`)?.focus()
  tableBody.replaceChildren(
    ...(visible.length
      ? visible.map(row =>
          ui.h(
            "tr",
            { "data-slot": "table-row", "data-id": row.id },
            ui.h(
              "td",
              { "data-slot": "table-cell" },
              ui.h("button", {
                type: "button",
                "data-slot": "checkbox",
                "aria-label": `Select ${row.email}`,
                "oncheckbox:change": event => {
                  if (event.detail.checked) tableState.selected.add(row.id)
                  else tableState.selected.delete(row.id)
                  tableSync()
                },
              }),
            ),
            columns.map(c => tableCell(c, row)),
            ui.h("td", { "data-slot": "table-cell", "data-demo": "table-actions" }, tableActions(row)),
          ),
        )
      : [ui.h("tr", { "data-slot": "table-row" }, ui.h("td", { "data-slot": "table-cell", colspan: String(columns.length + 2), "data-demo": "table-empty" }, "No results."))]),
  )
  tablePrevious.disabled = tableState.page === 0
  tableNext.disabled = tableState.page >= pages - 1
  tablePageLabel.textContent = `Page ${tableState.page + 1} of ${pages}`
  tableSync()
}

tableRoot.addEventListener("dropdown-menu:select", event => {
  const value = String(event.detail.value)
  if (!value.startsWith("copy:")) return
  const id = value.slice(5)
  navigator.clipboard?.writeText(id).catch(() => {})
  ui.toast("Payment ID copied", { description: id })
})

tableRoot.replaceChildren(
  ui.h("div", { "data-demo": "table-toolbar" }, tableFilter, tableColumnMenu),
  ui.h("div", { "data-slot": "table-container" }, ui.h("table", { "data-slot": "table", "aria-label": "Payments" }, ui.h("thead", { "data-slot": "table-header" }, tableHeadRow), tableBody)),
  ui.h("div", { "data-demo": "table-footer" }, tableCount, tablePageLabel, tablePrevious, tableNext),
)
tableRender()
function calendarDemoIso(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`
}

const calendarDemoToday = calendarDemoIso(new Date())

document.getElementById("attachment").addEventListener("click", event => {
  const status = document.getElementById("attachment-status")
  const remove = event.target.closest("[data-attachment-remove]")
  if (remove) {
    const attachment = remove.closest('[data-slot="attachment"]')
    status.textContent = `Removed ${attachment.querySelector('[data-slot="attachment-title"]')?.textContent ?? "the file"}.`
    attachment.remove()
    return
  }
  if (event.target.closest("#attachment-preview")) status.textContent = "Opened the preview of research-summary.pdf."
  else if (event.target.closest("#attachment-copy-link")) status.textContent = "Copied the link to research-summary.pdf."
})

document.getElementById("bubble-buttons").addEventListener("click", event => {
  const reply = event.target.closest('[data-slot="bubble-content"]')
  if (!reply || !reply.matches("button, a")) return
  event.preventDefault()
  document.getElementById("bubble-status").textContent = `You picked: ${reply.textContent}`
})

document.getElementById("bubble-run").addEventListener("click", event => {
  event.currentTarget.textContent = "Running..."
  event.currentTarget.disabled = true
})

const bubbleDemoText = "The accessibility review found two focus states that were visually too subtle in dark mode.\n\nI checked the dialog, menu, and drawer paths because each one renders focusable controls inside a layered surface.\n\nThe dialog and drawer are fine. The menu needs the hover and focus tokens split so keyboard focus stays visible when the pointer is not involved.\n\nI also recommend keeping the change in the style file instead of the primitive so the other themes can choose their own focus treatment later."

document.getElementById("bubble-more-toggle").addEventListener("click", event => {
  const toggle = event.currentTarget
  const open = toggle.getAttribute("aria-expanded") !== "true"
  toggle.setAttribute("aria-expanded", String(open))
  document.getElementById("bubble-more-text").textContent = open ? bubbleDemoText : `${bubbleDemoText.slice(0, 180)}...`
  toggle.replaceChildren(open ? "Show less" : "Show more", ui.icon("chevron-down", { "data-icon": "inline-end" }))
})
document.getElementById("bubble-more-text").textContent = `${bubbleDemoText.slice(0, 180)}...`

document.getElementById("calendar-range").setAttribute("data-max", calendarDemoToday)
document.querySelector('#date-picker-birth [data-slot="calendar"]').setAttribute("data-max", calendarDemoToday)
ui.calendarSetValue(document.getElementById("calendar-demo"), calendarDemoToday)
document.getElementById("calendar-demo-value").textContent = `Selected ${calendarDemoToday}.`

document.getElementById("calendar").addEventListener("calendar:change", event => {
  const value = event.detail.value
  if (event.target.id === "calendar-demo") document.getElementById("calendar-demo-value").textContent = value ? `Selected ${value}.` : "No date selected."
  if (event.target.id === "calendar-range") document.getElementById("calendar-range-value").textContent = value ? `Range: ${value.from} to ${value.to}` : "No range selected."
})

document.getElementById("calendar-form").addEventListener("submit", event => {
  event.preventDefault()
  const stay = new FormData(event.currentTarget).get("stay")
  document.getElementById("calendar-form-value").textContent = `The form sent stay=${stay || "(empty)"}.`
})

document.getElementById("code-block-more-toggle").addEventListener("click", event => {
  const toggle = event.currentTarget
  const content = document.getElementById("code-block-more-content")
  const open = !content.toggleAttribute("data-collapsed")
  toggle.setAttribute("aria-expanded", String(open))
  toggle.replaceChildren(open ? "Show less" : "Show more", ui.icon("chevron-down", { "data-icon": "inline-end" }))
})

document.getElementById("date-picker-form").addEventListener("submit", event => {
  const due = new FormData(event.currentTarget).get("due")
  document.getElementById("date-picker-form-value").textContent = due ? `Scheduled for ${due}.` : "No date picked."
})

document.getElementById("marker-revert").addEventListener("click", () => {
  document.getElementById("marker-status-text").textContent = "You clicked the revert button."
})

document.getElementById("message-actions").addEventListener("click", event => {
  const button = event.target.closest('[data-slot="button"][aria-pressed]')
  if (button) button.setAttribute("aria-pressed", String(button.getAttribute("aria-pressed") !== "true"))
})

document.getElementById("message-retry").addEventListener("click", event => {
  document.getElementById("message-failed-text").textContent = "Delivered"
  document.getElementById("message-failed-text").removeAttribute("id")
  event.currentTarget.remove()
})

const messageScrollerDemoRoot = document.getElementById("message-scroller-main")
const messageScrollerDemoContent = document.getElementById("message-scroller-transcript")
const messageScrollerDemoInput = document.getElementById("message-scroller-input")
const messageScrollerDemoRows = () => messageScrollerDemoContent.querySelectorAll(':scope > [data-slot="message-scroller-item"]')
const messageScrollerDemoInitialCount = messageScrollerDemoRows().length
const messageScrollerDemoPrompts = ["How do I stop this from happening again?", "Can CI tell me which package changed?", "Thanks. Summarize the fix in one line."]
const messageScrollerDemoReplies = [
  "Add a check that runs pnpm install --frozen-lockfile on every pull request, so a lockfile that does not match package.json fails before the merge instead of on main. A pre-commit hook can run the same check whenever package.json changes. With both in place, the lockfile and the manifest cannot drift apart without someone noticing, and the failure message points at the exact command to run locally.",
  "Yes. Run git diff --name-only on the base branch and filter for package.json files. Print the workspace names in the job summary, then fail with a short message that tells the author to run pnpm install and commit the lockfile. The summary shows up on the pull request, so reviewers see the cause without opening the logs.",
  "The commit changed package.json without the lockfile; regenerate the lockfile, commit it, and let CI check that they stay in sync.",
]
const messageScrollerDemoAnswers = { regenerate: "Done. I ran pnpm install, which updated pnpm-lock.yaml for the new version, and committed the lockfile on its own. The frozen install passes again in CI.", patch: "Done. I changed only the resolution of the bumped package in pnpm-lock.yaml and left every other entry as it was. The frozen install passes again in CI." }
let messageScrollerDemoTurn = 0
let messageScrollerDemoBusy = false

function messageScrollerDemoItem(id, anchor, ...children) {
  return ui.h("div", { "data-slot": "message-scroller-item", "data-message-id": id, "data-scroll-anchor": anchor ? "true" : null }, children)
}

function messageScrollerDemoUser(id, text) {
  return messageScrollerDemoItem(id, true, ui.h("div", { "data-slot": "message", "data-align": "end" }, ui.h("div", { "data-slot": "message-content" }, ui.h("div", { "data-slot": "bubble" }, ui.h("div", { "data-slot": "bubble-content" }, text)))))
}

function messageScrollerDemoFooter() {
  return ui.h("div", { "data-slot": "message-footer" },
    ui.h("button", { type: "button", "data-slot": "button", "data-variant": "ghost", "data-size": "icon-sm", "aria-label": "Copy", title: "Copy" }, ui.icon("copy")),
    ui.h("button", { type: "button", "data-slot": "button", "data-variant": "ghost", "data-size": "icon-sm", "aria-label": "Like", title: "Like" }, ui.icon("thumbs-up")),
    ui.h("button", { type: "button", "data-slot": "button", "data-variant": "ghost", "data-size": "icon-sm", "aria-label": "Dislike", title: "Dislike" }, ui.icon("thumbs-down")),
  )
}

function messageScrollerDemoStream(id, reply, done) {
  const thinking = ui.h("div", { "data-slot": "marker", role: "status" }, ui.h("span", { "data-slot": "marker-icon", "aria-hidden": "true" }, ui.icon("loader-circle", { "data-demo": "spin" })), ui.h("span", { "data-slot": "marker-content", class: "shimmer" }, "Thinking..."))
  const body = ui.h("div", { "data-slot": "message-content" }, thinking)
  messageScrollerDemoContent.append(messageScrollerDemoItem(id, false, ui.h("div", { "data-slot": "message" }, body)))
  setTimeout(() => {
    const text = ui.h("div", { "data-slot": "bubble-content" })
    thinking.replaceWith(
      ui.h("div", { "data-slot": "trace" },
        ui.h("div", { "data-slot": "trace-collapsible" },
          ui.h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, ui.h("span", { "data-slot": "trace-line" }, ui.h("span", { "data-slot": "trace-icon" }, ui.icon("circle-check")), ui.h("span", { "data-slot": "trace-title" }, "Thought for 1s"))),
          ui.h("div", { "data-slot": "trace-collapsible-content" }, "The user wants a lasting fix, not a one-off. Keep it short and actionable."),
        ),
      ),
      ui.h("div", { "data-slot": "bubble", "data-variant": "ghost" }, text),
    )
    const words = reply.split(" ")
    let index = 0
    const tick = () => {
      if (!text.isConnected) return
      text.append(document.createTextNode(`${index ? " " : ""}${words[index]}`))
      index += 1
      if (index < words.length) {
        setTimeout(tick, 28)
        return
      }
      body.append(messageScrollerDemoFooter())
      done()
    }
    tick()
  }, 600)
}

function messageScrollerDemoFinish() {
  messageScrollerDemoBusy = false
  messageScrollerDemoContent.removeAttribute("aria-busy")
  document.getElementById("message-scroller-send").disabled = false
  messageScrollerDemoInput.value = messageScrollerDemoPrompts[messageScrollerDemoTurn] ?? ""
}

function messageScrollerDemoSend(text, reply) {
  if (messageScrollerDemoBusy) return
  messageScrollerDemoBusy = true
  document.getElementById("message-scroller-send").disabled = true
  messageScrollerDemoContent.setAttribute("aria-busy", "true")
  const turn = messageScrollerDemoTurn
  messageScrollerDemoTurn += 1
  messageScrollerDemoContent.append(messageScrollerDemoUser(`u${turn}`, text))
  messageScrollerDemoStream(`a${turn}`, reply, messageScrollerDemoFinish)
}

document.getElementById("message-scroller-composer").addEventListener("submit", event => {
  event.preventDefault()
  const text = messageScrollerDemoInput.value.trim()
  if (!text) return
  messageScrollerDemoInput.value = ""
  messageScrollerDemoSend(text, messageScrollerDemoReplies[messageScrollerDemoTurn % messageScrollerDemoReplies.length])
})

messageScrollerDemoInput.addEventListener("keydown", event => {
  if (event.key !== "Enter" || event.shiftKey || event.isComposing) return
  event.preventDefault()
  event.currentTarget.form.requestSubmit()
})

document.getElementById("message-scroller-question").addEventListener("submit", event => {
  event.preventDefault()
})

document.getElementById("message-scroller-question").addEventListener("questionnaire:submit", event => {
  const choice = event.detail.value.lockfile
  const label = choice === "patch" ? "Patch the changed entry" : "Regenerate it"
  messageScrollerDemoSend(label, messageScrollerDemoAnswers[choice] ?? messageScrollerDemoAnswers.regenerate)
})

document.getElementById("message-scroller-reset").addEventListener("click", () => {
  for (const row of [...messageScrollerDemoRows()].slice(messageScrollerDemoInitialCount)) row.remove()
  messageScrollerDemoTurn = 0
  messageScrollerDemoFinish()
  document.getElementById("message-scroller-question").reset()
  ui.messageScrollerScrollToEnd(messageScrollerDemoRoot)
})

const messageScrollerDemoTopics = [
  ["What is a scroll anchor?", "The row that starts a turn. When a new anchor is appended, the viewport moves it near the top and keeps a peek of the previous row above it."],
  ["Why not always scroll to the bottom?", "Because the reader may be reading. Auto-scroll only follows while the view is already at the live edge."],
  ["What releases auto-scroll?", "Any deliberate move up: wheel, touch, scroll keys on the viewport, dragging the scrollbar, or an explicit jump to a message."],
  ["How do I return to the latest reply?", "Press the arrow button at the bottom of the viewport. It scrolls to the end and resumes following."],
  ["What happens when history loads above?", "The first visible row keeps its position, so the reader does not lose their place."],
  ["Is the transcript accessible?", "The viewport is a labelled region you can focus and scroll, and the content is a log that announces new rows."],
  ["Can I open a saved thread?", "Use last-anchor to open at the latest turn with its reply below, instead of the absolute bottom."],
  ["Does it work with streaming?", "Yes. A new turn anchors near the top and the reply grows into the space below it."],
  ["What about long threads?", "Rows use content-visibility, so the browser skips rendering work for rows far outside the viewport."],
  ["Can I jump to a message?", "Give each row a stable message id and call messageScrollerScrollToMessage."],
  ["How do I style the scroll state?", "Use the data-scrollable attribute on the root or the viewport. It lists the edges you can scroll toward."],
  ["Is there a flash on reload?", "No. The opening position is applied before the first paint."],
]
let messageScrollerDemoLoaded = false

function messageScrollerDemoTopicItems(index) {
  const [question, answer] = messageScrollerDemoTopics[index]
  return [
    messageScrollerDemoUser(`h${index + 1}-q`, question),
    messageScrollerDemoItem(`h${index + 1}-a`, false, ui.h("div", { "data-slot": "message" }, ui.h("div", { "data-slot": "message-content" }, ui.h("div", { "data-slot": "bubble", "data-variant": "muted" }, ui.h("div", { "data-slot": "bubble-content" }, answer))))),
  ]
}

const messageScrollerDemoHistory = document.getElementById("message-scroller-history-content")
messageScrollerDemoHistory.append(...Array.from({ length: 6 }, (_, i) => messageScrollerDemoTopicItems(i + 6)).flat())

document.getElementById("message-scroller-load").addEventListener("click", event => {
  if (messageScrollerDemoLoaded) return
  messageScrollerDemoLoaded = true
  messageScrollerDemoHistory.prepend(...Array.from({ length: 6 }, (_, i) => messageScrollerDemoTopicItems(i)).flat())
  event.currentTarget.disabled = true
})

document.getElementById("message-scroller-jump").addEventListener("click", () => {
  ui.messageScrollerScrollToMessage(document.getElementById("message-scroller-history"), messageScrollerDemoLoaded ? "h1-q" : "h7-q", { behavior: "smooth" })
})

document.getElementById("message-scroller-latest").addEventListener("click", () => {
  ui.messageScrollerScrollToEnd(document.getElementById("message-scroller-history"), { behavior: "smooth" })
})

document.getElementById("questionnaire-demo").addEventListener("submit", event => event.preventDefault())
document.getElementById("questionnaire-demo").addEventListener("questionnaire:submit", event => {
  const value = event.detail.value
  document.getElementById("questionnaire-result").textContent = `Agent plan saved. Direction: ${value.direction ?? "None"} · Progress signals: ${value.signals.join(", ") || "None"} · Timing: ${value.timing ?? "None"}`
})

document.getElementById("questionnaire-resume").addEventListener("submit", event => event.preventDefault())
document.getElementById("questionnaire-resume").addEventListener("questionnaire:submit", event => {
  const { value, status } = event.detail
  document.getElementById("questionnaire-resume-result").textContent = `Prototype: ${value.prototype ?? "None"} · Detail: ${status.detail === "skipped" ? "Skipped" : (value.detail ?? "None")}${"audience" in value ? ` · Audience: ${value.audience ?? "None"}` : ""}`
})

document.getElementById("questionnaire-toggle").addEventListener("checkbox:change", event => {
  document.getElementById("questionnaire-audience").disabled = !event.detail.checked
  ui.questionnaireRefresh(document.getElementById("questionnaire-resume"))
})

const traceDemoSteps = [
  { id: "trace-thinking", running: "Thinking", icon: "circle-check", time: 1400 },
  { id: "trace-version", running: "Running pnpm --version", icon: "circle-check", time: 700 },
  { id: "trace-install", running: "Running pnpm install --frozen-lockfile", icon: "circle-alert", time: 1100, status: "error", open: true },
  { id: "trace-sources", running: "Using 2 sources", icon: "globe", time: 800 },
]

for (const step of traceDemoSteps) step.title = document.querySelector(`#${step.id} [data-slot="trace-title"]`).textContent

function traceDemoLine(step, running) {
  const collapsible = document.getElementById(step.id)
  const line = collapsible.querySelector('[data-slot="trace-line"]')
  line.querySelector('[data-slot="trace-icon"]').replaceChildren(ui.icon(running ? "loader-circle" : step.icon, running ? { "data-demo": "spin" } : {}))
  line.querySelector('[data-slot="trace-title"]').textContent = running ? step.running : step.title
  if (running) line.setAttribute("data-status", "running")
  else if (step.status) line.setAttribute("data-status", step.status)
  else line.removeAttribute("data-status")
  return collapsible
}

document.getElementById("trace-replay").addEventListener("click", event => {
  const replay = event.currentTarget
  replay.disabled = true
  const answer = document.getElementById("trace-demo-answer")
  answer.hidden = true
  for (const step of traceDemoSteps) {
    const collapsible = document.getElementById(step.id)
    ui.traceClose(collapsible, { animate: false })
    collapsible.hidden = true
  }
  let delay = 0
  traceDemoSteps.forEach((step, index) => {
    setTimeout(() => {
      const collapsible = traceDemoLine(step, true)
      collapsible.hidden = false
      if (index === 0) ui.traceOpen(collapsible)
    }, delay)
    delay += step.time
    setTimeout(() => {
      const collapsible = traceDemoLine(step, false)
      if (step.open) ui.traceOpen(collapsible)
      else ui.traceClose(collapsible)
      if (index === traceDemoSteps.length - 1) {
        answer.hidden = false
        replay.disabled = false
      }
    }, delay)
  })
})

document.getElementById("trace-pnpm-toggle").addEventListener("click", event => {
  const collapsible = document.getElementById("trace-pnpm")
  if (collapsible.dataset.state === "open") ui.traceClose(collapsible)
  else ui.traceOpen(collapsible)
})

document.getElementById("trace-pnpm").addEventListener("trace:open", () => {
  document.getElementById("trace-pnpm-toggle").textContent = "Hide the pnpm output"
})

document.getElementById("trace-pnpm").addEventListener("trace:close", () => {
  document.getElementById("trace-pnpm-toggle").textContent = "Show the pnpm output"
})
import { chart, sparkline as chartSparkline, statTile as chartStatTile } from "../clanker-ui-chart.js"

const chartMonths = [
  { month: "January", desktop: 186, mobile: 80 },
  { month: "February", desktop: 305, mobile: 200 },
  { month: "March", desktop: 237, mobile: 120 },
  { month: "April", desktop: 73, mobile: 190 },
  { month: "May", desktop: 209, mobile: 130 },
  { month: "June", desktop: 214, mobile: 140 },
]
const chartDevices = { desktop: { label: "Desktop" }, mobile: { label: "Mobile" } }
const chartDesktop = { desktop: { label: "Desktop" } }
const chartBrowsers = [
  { browser: "chrome", visitors: 275 },
  { browser: "safari", visitors: 200 },
  { browser: "firefox", visitors: 187 },
  { browser: "edge", visitors: 173 },
  { browser: "other", visitors: 90 },
]
const chartBrowserConfig = {
  visitors: { label: "Visitors" },
  chrome: { label: "Chrome" },
  safari: { label: "Safari" },
  firefox: { label: "Firefox" },
  edge: { label: "Edge" },
  other: { label: "Other" },
}
const chartBrowserDevices = [
  { browser: "chrome", desktop: 186, mobile: 89 },
  { browser: "safari", desktop: 120, mobile: 80 },
  { browser: "firefox", desktop: 132, mobile: 55 },
  { browser: "edge", desktop: 97, mobile: 76 },
  { browser: "other", desktop: 52, mobile: 38 },
]
const chartShort = value => String(value).slice(0, 3)
const chartDailyDesktop = [222, 97, 167, 242, 373, 301, 245, 409, 59, 261, 327, 292, 342, 137, 120, 138, 446, 364, 243, 89, 137, 224, 138, 387, 215, 75, 383, 122, 315, 454, 165, 293, 247, 385, 481, 498, 388, 149, 227, 293, 335, 197, 197, 448, 473, 338, 499, 315, 235, 177, 82, 81, 252, 294, 201, 213, 420, 233, 78, 340, 178, 178, 470, 103, 439, 88, 294, 323, 385, 438, 155, 92, 492, 81, 426, 307, 371, 475, 107, 341, 408, 169, 317, 480, 132, 141, 434, 448, 149, 103, 446]
const chartDailyMobile = [150, 180, 120, 260, 290, 340, 180, 320, 110, 190, 350, 210, 380, 220, 170, 190, 360, 410, 180, 150, 200, 170, 230, 290, 250, 130, 420, 180, 240, 380, 220, 310, 190, 420, 390, 520, 300, 210, 180, 330, 270, 240, 160, 490, 380, 400, 420, 350, 180, 230, 140, 120, 290, 220, 250, 170, 460, 190, 130, 280, 230, 200, 410, 160, 380, 140, 250, 370, 320, 480, 200, 150, 420, 130, 380, 350, 310, 520, 170, 290, 450, 210, 270, 530, 180, 190, 380, 490, 200, 160, 400]
const chartDaily = chartDailyDesktop.map((desktop, i) => {
  const day = new Date(2024, 3, 1 + i)
  const date = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`
  return { date, desktop, mobile: chartDailyMobile[i] }
})
const chartViews = new Map()

function chartMount(id, data, options) {
  const el = document.getElementById(id)
  if (!el) return null
  const view = chart(el, data, options)
  chartViews.set(id, view)
  return view
}

const chartMonthData = { rows: chartMonths, config: chartDevices }
const chartMonthOptions = { x: "month", xFormat: chartShort, label: "Visitors, January to June 2024" }

chartMount("chart-demo", chartMonthData, { ...chartMonthOptions, type: "bar" })
chartMount(
  "chart-colors",
  { rows: chartMonths, config: { desktop: { label: "Desktop", icon: "monitor", color: "chart-7" }, mobile: { label: "Mobile", icon: () => ui.icon("smartphone"), theme: { light: "#1baf7a", dark: "#199e70" } } } },
  { ...chartMonthOptions, type: "area", stack: true },
)
chartMount("chart-tooltip-line", chartMonthData, { ...chartMonthOptions, type: "bar", stack: true })
chartMount("chart-tooltip-dot", chartMonthData, { ...chartMonthOptions, type: "bar", stack: true, tooltip: { indicator: "dot" } })
chartMount("chart-tooltip-dashed", chartMonthData, { ...chartMonthOptions, type: "bar", stack: true, tooltip: { indicator: "dashed" } })
chartMount("chart-tooltip-label", chartMonthData, { ...chartMonthOptions, type: "bar", stack: true, tooltip: { hideLabel: true } })

chartMount("chart-area-default", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "area" })
chartMount("chart-area-linear", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "area", curve: "linear" })
chartMount("chart-area-step", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "area", curve: "step" })
chartMount("chart-area-stacked", chartMonthData, { ...chartMonthOptions, type: "area", stack: true })
chartMount("chart-area-expanded", chartMonthData, { ...chartMonthOptions, type: "area", stack: "expand" })
chartMount("chart-area-gradient", chartMonthData, { ...chartMonthOptions, type: "area", gradient: true })

chartMount("chart-bar-default", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "bar" })
chartMount("chart-bar-horizontal", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "bar", horizontal: true })
chartMount("chart-bar-multiple", chartMonthData, { ...chartMonthOptions, type: "bar" })
chartMount("chart-bar-stacked", chartMonthData, { ...chartMonthOptions, type: "bar", stack: true })
chartMount("chart-bar-label", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "bar", labels: true })
chartMount("chart-bar-horizontal-stacked", { rows: chartBrowserDevices, config: { ...chartDevices, ...chartBrowserConfig } }, { type: "bar", x: "browser", horizontal: true, stack: true, label: "Visitors by browser and device" })
chartMount(
  "chart-bar-negative",
  { rows: [{ month: "January", visitors: 186 }, { month: "February", visitors: 205 }, { month: "March", visitors: -207 }, { month: "April", visitors: 173 }, { month: "May", visitors: -209 }, { month: "June", visitors: 214 }], config: { visitors: { label: "Visitors" } } },
  { ...chartMonthOptions, type: "bar", diverging: true, labels: true, label: "Change in visitors, January to June 2024" },
)
chartMount("chart-bar-emphasis", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "bar", highlight: 1 })
chartMount("chart-bar-reference", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "bar", references: [{ value: 200, label: "Goal" }] })

chartMount("chart-line-default", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "line" })
chartMount("chart-line-linear", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "line", curve: "linear" })
chartMount("chart-line-step", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "line", curve: "step" })
chartMount("chart-line-multiple", chartMonthData, { ...chartMonthOptions, type: "line" })
chartMount("chart-line-dots", chartMonthData, { ...chartMonthOptions, type: "line", dots: true })
chartMount("chart-line-label", chartMonthData, { ...chartMonthOptions, type: "line", dots: true, labels: true })
chartMount("chart-line-reference", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "line", references: [{ from: 180, to: 250, label: "Target" }, { value: 300, label: "Limit", tone: "destructive" }] })
chartMount(
  "chart-line-time",
  {
    rows: [
      { day: "2026-09-01", plan: 84, actual: 84.2 },
      { day: "2026-09-08", actual: 83.6 },
      { day: "2026-09-15", actual: 83.1 },
      { day: "2026-09-29", actual: 82.4 },
      { day: "2026-10-01", plan: 82 },
      { day: "2026-10-06", actual: 81.7 },
      { day: "2026-10-07", actual: 81.9 },
      { day: "2026-10-08", actual: 81.5 },
      { day: "2026-10-20", actual: 80.6 },
      { day: "2026-11-01", plan: 80, actual: 79.8 },
      { day: "2026-11-03", actual: 79.6 },
      { day: "2026-12-01", plan: 78 },
    ],
    config: { actual: { label: "Actual" }, plan: { label: "Plan", color: "chart-other" } },
  },
  { type: "line", x: "day", scale: "time", connectNulls: true, curve: "linear", dots: true, zero: false, format: { maximumFractionDigits: 1 }, references: [{ value: 78, label: "Goal 78 kg", position: "start" }], label: "Weight, plan and actual, kg" },
)

const chartBrowserData = { rows: chartBrowsers, config: chartBrowserConfig }
const chartBrowserOptions = { x: "browser", y: "visitors", label: "Visitors by browser, January to June 2024" }
chartMount("chart-pie-simple", chartBrowserData, { ...chartBrowserOptions, type: "pie" })
chartMount("chart-pie-label", chartBrowserData, { ...chartBrowserOptions, type: "pie", labels: "value" })
chartMount("chart-pie-label-list", chartBrowserData, { ...chartBrowserOptions, type: "pie", labels: "percent", labelPosition: "inside" })
chartMount("chart-pie-donut", chartBrowserData, { ...chartBrowserOptions, type: "donut" })
chartMount("chart-pie-donut-text", chartBrowserData, { ...chartBrowserOptions, type: "donut", center: true })
chartMount("chart-pie-donut-active", chartBrowserData, { ...chartBrowserOptions, type: "donut", highlight: 0 })

chartMount("chart-radar-default", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "radar" })
chartMount("chart-radar-dots", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "radar", dots: true })
chartMount("chart-radar-multiple", chartMonthData, { ...chartMonthOptions, type: "radar" })
chartMount("chart-radar-lines", chartMonthData, { ...chartMonthOptions, type: "radar", fill: false, dots: true })
chartMount("chart-radar-grid-circle", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "radar", grid: "circle", dots: true })
chartMount("chart-radar-grid-none", { rows: chartMonths, config: chartDesktop }, { ...chartMonthOptions, type: "radar", grid: "none", dots: true })

chartMount("chart-radial-simple", chartBrowserData, { ...chartBrowserOptions, type: "radial" })
chartMount("chart-radial-label", chartBrowserData, { ...chartBrowserOptions, type: "radial", labels: true, startAngle: -90, endAngle: 270 })
chartMount("chart-radial-grid", chartBrowserData, { ...chartBrowserOptions, type: "radial", grid: true, track: false })
chartMount("chart-radial-text", { rows: [{ browser: "safari", visitors: 200 }], config: chartBrowserConfig }, { ...chartBrowserOptions, type: "radial", max: 250, center: true, label: "Safari visitors against a goal of 250" })
chartMount("chart-radial-shape", { rows: [{ browser: "safari", visitors: 1260 }], config: chartBrowserConfig }, { ...chartBrowserOptions, type: "radial", max: 4500, track: "full", center: true, label: "Safari visitors against a goal of 4,500" })
chartMount("chart-radial-stacked", { rows: [{ month: "January", desktop: 1260, mobile: 570 }], config: chartDevices }, { type: "radial", x: "month", stacked: true, startAngle: -90, endAngle: 90, center: { label: "Visitors" }, label: "Visitors in January 2024" })

chartStatTile(document.getElementById("chart-stat-revenue"), { label: "Total revenue", value: 1250, format: { style: "currency", currency: "USD" }, delta: 0.125, period: "vs last month", trend: [820, 940, 910, 1010, 980, 1100, 1060, 1150, 1120, 1190, 1210, 1250] })
chartStatTile(document.getElementById("chart-stat-customers"), { label: "New customers", value: 1234, delta: -0.2, period: "vs last month", trend: [1650, 1590, 1600, 1520, 1480, 1500, 1420, 1390, 1350, 1300, 1270, 1234] })
chartStatTile(document.getElementById("chart-stat-accounts"), { label: "Active accounts", value: 45678, delta: 0.125, period: "vs last month", trend: [38900, 39400, 40100, 40600, 41000, 41900, 42300, 43000, 43800, 44500, 45100, 45678] })
chartStatTile(document.getElementById("chart-stat-churn"), { label: "Churn rate", value: 0.024, format: { style: "percent", maximumFractionDigits: 1 }, delta: 0.003, deltaFormat: { style: "percent", maximumFractionDigits: 1, signDisplay: "always" }, goodWhen: "down", period: "vs last month", trend: [0.018, 0.019, 0.019, 0.02, 0.021, 0.02, 0.022, 0.021, 0.022, 0.023, 0.023, 0.024] })

const chartDashTiles = {
  visitors: chartStatTile(document.getElementById("chart-stat-visitors"), { label: "Visitors" }),
  desktop: chartStatTile(document.getElementById("chart-stat-desktop"), { label: "Desktop visitors" }),
  mobile: chartStatTile(document.getElementById("chart-stat-mobile"), { label: "Mobile visitors" }),
}
const chartDashArea = chartMount("chart-stat-area", { rows: [], config: chartDevices }, { type: "area", x: "date", stack: true, gradient: true, height: 250, label: "Desktop and mobile visitors per day" })

function chartDashRange(days) {
  const rows = chartDaily.slice(-days)
  const before = chartDaily.slice(-2 * days, -days)
  const sum = (list, key) => list.reduce((a, r) => a + (key ? r[key] : r.desktop + r.mobile), 0)
  const change = (now, then) => (then ? now / then - 1 : null)
  const period = `vs previous ${days} days`
  for (const [key, tile] of Object.entries(chartDashTiles)) {
    const field = key === "visitors" ? null : key
    const now = sum(rows, field)
    tile.update({ value: now, delta: change(now, sum(before, field)), period, trend: rows.map(r => (field ? r[field] : r.desktop + r.mobile)) })
  }
  chartDashArea?.update({ rows })
  for (const button of document.querySelectorAll("#chart-stat [data-range]")) {
    const on = Number(button.dataset.range) === days
    button.setAttribute("aria-pressed", String(on))
    button.dataset.variant = on ? "secondary" : "outline"
  }
}

document.querySelector('#chart-stat [data-demo="chart-filters"]')?.addEventListener("click", event => {
  const button = event.target.closest("[data-range]")
  if (button) chartDashRange(Number(button.dataset.range))
})
chartDashRange(30)

chartSparkline(document.getElementById("chart-stat-spark-line"), [980, 1020, 1110, 1060, 1190, 1150, 1230, 1210, 1180, 1260, 1240, 1284], { label: "Requests per minute" })
chartSparkline(document.getElementById("chart-stat-spark-area"), [0.48, 0.5, 0.53, 0.52, 0.55, 0.57, 0.56, 0.58, 0.6, 0.59, 0.61, 0.62], { area: true, label: "Memory use", format: { style: "percent", maximumFractionDigits: 0 } })
chartSparkline(document.getElementById("chart-stat-spark-flat"), [0.002, 0.002, 0.003, 0.002, 0.002, 0.002, 0.002, 0.003, 0.002, 0.002, 0.002, 0.002], { label: "Error rate", zero: true, format: { style: "percent", maximumFractionDigits: 1 } })
