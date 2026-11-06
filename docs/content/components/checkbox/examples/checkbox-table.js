const root = document.querySelector('[data-js="checkbox-table"]')
const all = root.querySelector("#select-all-checkbox")
const boxes = [...root.querySelectorAll('tbody [data-slot="checkbox"]')]

function sync() {
  for (const box of boxes) box.closest("tr").toggleAttribute("data-state", false)
  for (const box of boxes.filter(box => box.hasAttribute("data-checked"))) box.closest("tr").dataset.state = "selected"
  all.toggleAttribute("data-checked", boxes.every(box => box.hasAttribute("data-checked")))
}

root.addEventListener("checkbox:change", event => {
  if (event.target === all) for (const box of boxes) box.toggleAttribute("data-checked", event.detail.checked)
  sync()
})
