const year = new Date().getFullYear()
const el = document.querySelector('[data-js="calendar-week-numbers"]')
el.dataset.month = `${year}-01`
el.dataset.value = `${year}-01-12`
