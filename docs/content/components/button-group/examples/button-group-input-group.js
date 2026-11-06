const root = document.querySelector('[data-js="button-group-input-group"]')
const input = root.querySelector("input")
const voice = root.querySelector("[data-input-group-button]")

voice.addEventListener("click", () => {
  const on = voice.dataset.active !== "true"
  voice.dataset.active = String(on)
  voice.setAttribute("aria-pressed", String(on))
  input.disabled = on
  input.placeholder = on ? "Record and send audio..." : "Send a message..."
})
