const root = document.querySelector('[data-js="calendar-presets"]')
const calendar = root.querySelector('[data-slot="calendar"]')
const now = new Date()
const month = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`
const iso = date => `${month(date)}-${String(date.getDate()).padStart(2, "0")}`
calendar.dataset.value = iso(new Date(now.getFullYear(), 1, 12))
calendar.dataset.month = month(now)

root.addEventListener("click", event => {
  const button = event.target.closest("[data-days]")
  if (!button) return
  const date = new Date(now.getFullYear(), now.getMonth(), now.getDate() + Number(button.dataset.days))
  calendar.dataset.value = iso(date)
  calendar.dataset.month = month(date)
})
