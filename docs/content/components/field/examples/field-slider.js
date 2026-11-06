const field = document.querySelector('[data-js="price-field"]')
const [low, high] = field.querySelectorAll('[data-js="price"] input')

field.addEventListener("input", () => {
  field.querySelector('[data-js="min"]').textContent = low.value
  field.querySelector('[data-js="max"]').textContent = high.value
})
