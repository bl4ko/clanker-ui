import { toast } from "/vendor/clanker-ui/clanker-ui.min.js"

const grid = document.getElementById("books")
const cards = [...grid.children]
const empty = document.getElementById("shelf-empty")
const filter = document.getElementById("shelf-filter")
const tabs = document.getElementById("shelf")
const select = document.getElementById("shelf-select")
const sorts = {
  added: (a, b) => b.dataset.added.localeCompare(a.dataset.added),
  title: (a, b) => a.dataset.title.localeCompare(b.dataset.title),
  author: (a, b) => a.dataset.author.split(" ").at(-1).localeCompare(b.dataset.author.split(" ").at(-1)),
  rating: (a, b) => b.dataset.rating - a.dataset.rating,
}
let status = "all"
let sort = "added"

function render() {
  const query = filter.value.trim().toLowerCase()
  const shown = cards.filter(card => (status === "all" || card.dataset.status === status) && (!query || `${card.dataset.title} ${card.dataset.author}`.toLowerCase().includes(query)))
  for (const card of cards) card.hidden = !shown.includes(card)
  grid.append(...cards.toSorted(sorts[sort]))
  grid.hidden = shown.length === 0
  empty.hidden = shown.length > 0
}

function setStatus(value) {
  status = value
  if (select.dataset.value !== value) select.dataset.value = value
  const trigger = tabs.querySelector(`[data-slot="tabs-trigger"][data-value="${value}"]`)
  if (trigger.getAttribute("aria-selected") !== "true") trigger.click()
  render()
}

tabs.addEventListener("tabs:change", event => setStatus(event.detail.value))
select.addEventListener("select:change", event => setStatus(event.detail.value))
document.getElementById("shelf-sort").addEventListener("select:change", event => { sort = event.detail.value; render() })
filter.addEventListener("input", render)
document.getElementById("shelf-clear").addEventListener("click", () => {
  filter.value = ""
  setStatus("all")
})
document.getElementById("suggest").addEventListener("click", () => toast("Suggestions open on Nov 19", { description: "After the meeting, every member can suggest one book." }))

render()
