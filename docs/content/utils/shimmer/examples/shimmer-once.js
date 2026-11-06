const root = document.querySelector('[data-js="shimmer-once"]')

root.querySelector("button").addEventListener("click", () => {
  const text = root.querySelector("p")
  text.replaceWith(text.cloneNode(true))
})
