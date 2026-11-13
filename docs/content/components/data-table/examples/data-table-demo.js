export function paymentsTable(root) {
  if (!root) return
  const filter = root.querySelector('[data-js="filter"]')
  const body = root.querySelector("tbody")
  const rows = [...body.querySelectorAll("tr[data-id]")]
  const empty = root.querySelector('[data-js="empty"]')
  const all = root.querySelector('[data-js="all"]')
  const selection = root.querySelector('[data-js="selection"]')
  const email = row => row.querySelector('[data-column="email"]').textContent.trim()
  let dir = 0

  const shown = () => rows.filter(row => email(row).toLowerCase().includes(filter.value.trim().toLowerCase()))
  const checked = row => row.querySelector('[data-slot="checkbox"]').hasAttribute("data-checked")

  function render() {
    const visible = shown()
    if (dir) visible.sort((a, b) => email(a).localeCompare(email(b)) * dir)
    for (const row of rows) row.hidden = !visible.includes(row)
    body.prepend(...visible)
    body.append(empty)
    empty.hidden = visible.length > 0
    const picked = visible.filter(checked).length
    all.toggleAttribute("data-checked", visible.length > 0 && picked === visible.length)
    all.toggleAttribute("data-indeterminate", picked > 0 && picked < visible.length)
    for (const row of rows) row.toggleAttribute("data-state", false)
    for (const row of rows.filter(checked)) row.dataset.state = "selected"
    selection.textContent = `${picked} ${selection.dataset.of} ${visible.length} ${selection.dataset.suffix}`
  }

  filter.addEventListener("input", render)
  root.addEventListener("table:sort", event => {
    event.preventDefault()
    dir = { ascending: 1, descending: -1 }[event.detail.dir] ?? 0
    render()
  })
  root.addEventListener("checkbox:change", event => {
    if (event.target === all) for (const row of shown()) row.querySelector('[data-slot="checkbox"]').toggleAttribute("data-checked", event.detail.checked)
    render()
  })
  root.querySelector('[data-js="columns"]').addEventListener("dropdown-menu:change", event => {
    for (const cell of root.querySelectorAll(`[data-column="${event.detail.value}"]`)) cell.hidden = !event.detail.checked
  })
  root.addEventListener("dropdown-menu:select", event => {
    if (event.detail.item.dataset.js === "copy") navigator.clipboard.writeText(event.detail.item.closest("tr").dataset.id)
  })
  render()
}

paymentsTable(document.querySelector('[data-js="payments"]:not([dir])'))
