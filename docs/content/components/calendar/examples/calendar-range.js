const year = new Date().getFullYear()
const iso = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`
const el = document.querySelector('[data-js="calendar-range"]')
el.dataset.month = `${year}-01`
el.dataset.value = `${iso(new Date(year, 0, 12))}/${iso(new Date(year, 0, 42))}`
