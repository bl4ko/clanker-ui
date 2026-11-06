const day = new Date()
const iso = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`
document.querySelector('[data-js="calendar-demo"]').dataset.value = iso
