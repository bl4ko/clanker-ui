import { h } from "./clanker-ui.js"

const replies = {
  "Add a dark mode toggle": "Added a ModeToggle to the site header. It calls setTheme from next-themes.",
  "Fix the failing build": "The build failed on a missing import in app/page.tsx. I added it and the build passes.",
  "Write tests for the form": "Added four tests in signup-form.test.tsx. They cover the empty, invalid and valid states.",
  "Upgrade to Next.js 16": "Ran the codemod and bumped next to 16. Two routes needed async params, so I updated them.",
  "Add a loading state": "Added a loading.tsx to the dashboard route. It shows skeletons while the data loads.",
  "Find unused dependencies": "Three packages are not imported anywhere: lodash, moment and classnames. Should I remove them?",
}

const demo = document.getElementById("suggestion-demo")
const form = document.getElementById("suggestion-demo-form")
const text = document.getElementById("suggestion-demo-text")
const sendButton = document.getElementById("suggestion-demo-send")
let turn = null

function send(prompt) {
  const next = h("div", { class: "flex flex-col gap-4" },
    h("div", { "data-slot": "message", "data-align": "end" },
      h("div", { "data-slot": "message-content" },
        h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" },
          h("div", { "data-slot": "bubble-content" }, prompt)))),
    h("div", { "data-slot": "message" },
      h("div", { "data-slot": "message-content" },
        h("p", {}, replies[prompt] ?? "This demo only knows the suggestions. Pick one."))))
  if (turn) turn.replaceWith(next)
  else demo.prepend(next)
  turn = next
  text.value = ""
  sendButton.disabled = true
}

document.getElementById("suggestion-demo-list").addEventListener("click", event => {
  const button = event.target.closest("button")
  if (button) send(button.textContent)
})

text.addEventListener("input", () => {
  sendButton.disabled = text.value.trim() === ""
})

text.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault()
    form.requestSubmit()
  }
})

form.addEventListener("submit", event => {
  event.preventDefault()
  if (text.value.trim()) send(text.value.trim())
})
