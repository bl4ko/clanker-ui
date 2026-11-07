const year = new Date().getFullYear()
const el = document.querySelector('[data-js="calendar-booked-dates"]')
el.dataset.month = `${year}-01`
el.dataset.value = `${year}-01-06`
el.dataset.disabledDates = `${year}-01-12/${year}-01-26`
