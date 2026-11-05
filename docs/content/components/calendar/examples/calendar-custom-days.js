import { h } from "./clanker-ui.js"

const year = new Date().getFullYear()
const el = document.querySelector('[data-js="calendar-custom-days"]')

function prices() {
  for (const button of el.querySelectorAll("td:not([data-outside]) > [data-calendar-day-button]:not(:has(span))")) {
    const day = new Date(`${button.parentElement.dataset.day}T00:00`).getDay()
    button.append(h("span", {}, day === 0 || day === 6 ? "$120" : "$100"))
  }
}

new MutationObserver(prices).observe(el, { childList: true, subtree: true })
el.dataset.month = `${year}-12`
el.dataset.value = `${year}-12-08/${year}-12-18`
prices()
