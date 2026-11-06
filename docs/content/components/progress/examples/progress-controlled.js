const root = document.querySelector('[data-js="progress-controlled"]')

root.addEventListener("input", event => root.querySelector('[data-slot="progress"]').setAttribute("data-value", event.target.value))
