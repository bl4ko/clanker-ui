import { h } from "./clanker-ui.js"

const marker = document.getElementById("checkpoint-demo-rename")
const restore = document.getElementById("checkpoint-demo-restore")
const next = document.getElementById("checkpoint-demo-continue")
const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

restore.addEventListener("click", () => {
  while (marker.nextElementSibling !== next) marker.nextElementSibling.remove()
  restore.remove()
  next.hidden = false
})

next.addEventListener("click", async () => {
  next.hidden = true
  next.before(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" },
        h("div", { "data-slot": "bubble-content" }, "Update the docs to match.")))))
  const p = h("p")
  next.before(h("div", { "data-slot": "message" }, h("div", { "data-slot": "message-content" }, p)))
  for (const word of "Updated the Button page to say Action.".match(/\S+\s*/g)) {
    await wait(20)
    p.append(word)
  }
  marker.querySelector('[data-slot="marker-content"]').append(restore)
})
