const root = document.querySelector('[data-js="card-spacing"]')
const card = root.querySelector('[data-slot="card"]')
const spacing = { 4: "[--card-spacing:--spacing(4)]", 5: "[--card-spacing:--spacing(5)]", 6: "[--card-spacing:--spacing(6)]", 8: "[--card-spacing:--spacing(8)]" }

root.addEventListener("toggle-group:change", event => {
  if (!event.detail.value) return
  card.classList.remove(...Object.values(spacing))
  card.classList.add(spacing[event.detail.value])
})
