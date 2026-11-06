const root = document.querySelector('[data-js="input-otp-controlled"]')
const input = root.querySelector("input")
const text = root.querySelector("[aria-live]")

input.addEventListener("input", () => {
  text.textContent = input.value === "" ? "Enter your one-time password." : `You entered: ${input.value}`
})
