const now = new Date()
const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
document.querySelector('[data-js="calendar-time"]').dataset.value = `${month}-12`
