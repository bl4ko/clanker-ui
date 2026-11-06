import { icon } from "./clanker-ui.js"

const root = document.querySelector('[data-js="input-group-button"]')
const copy = root.querySelector('[data-js="copy"]')
const favorite = root.querySelector('[data-js="favorite"]')

copy.addEventListener("click", async () => {
  await navigator.clipboard.writeText("https://x.com/shadcn").catch(() => {})
  copy.replaceChildren(icon("check"))
  setTimeout(() => copy.replaceChildren(icon("copy")), 2000)
})

favorite.addEventListener("click", () => {
  const star = favorite.querySelector("svg")
  const on = star.dataset.favorite !== "true"
  star.dataset.favorite = String(on)
  favorite.setAttribute("aria-pressed", String(on))
})
