import { h, icon } from "./clanker-ui.js"

const question = "How do I start an Astro project with pnpm?"
const answer = "Run pnpm create astro@latest and follow the prompts. It scaffolds the project and installs the dependencies."
const sources = [
  { url: "https://docs.astro.build/en/install-and-setup/", title: "Install Astro | docs.astro.build" },
  { url: "https://www.npmjs.com/package/create-astro", title: "create-astro | npmjs.com" },
  { url: "https://docs.astro.build/en/install-and-setup/", title: "Install Astro | docs.astro.build" },
  { url: "https://pnpm.io/cli/create", title: "pnpm create | pnpm.io" },
]

const thread = document.getElementById("sources-demo-thread")
const replay = document.getElementById("sources-demo-replay")
const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function sourceList(list) {
  const unique = list.filter((source, index) => list.findIndex(other => other.url === source.url) === index)
  return h("div", { "data-slot": "trace" },
    h("div", { "data-slot": "trace-collapsible", "data-default-open": true },
      h("button", { type: "button", "data-slot": "trace-collapsible-trigger" },
        h("span", { "data-slot": "trace-line" },
          h("span", { "data-slot": "trace-icon" }, icon("globe")),
          h("span", { "data-slot": "trace-title" }, `Used ${unique.length} sources`))),
      h("div", { "data-slot": "trace-collapsible-content" },
        h("div", { "data-slot": "trace" }, unique.map(source =>
          h("a", { href: source.url, target: "_blank", rel: "noreferrer" },
            h("span", { "data-slot": "trace-line" },
              h("span", { "data-slot": "trace-title" }, source.title ?? new URL(source.url).hostname, h("span", { class: "sr-only" }, " (opens in a new tab)")),
              h("span", { "data-slot": "trace-icon" }, icon("arrow-up-right")))))))))
}

replay.addEventListener("click", async () => {
  replay.hidden = true
  thread.replaceChildren(
    h("div", { "data-slot": "message", "data-align": "end" },
      h("div", { "data-slot": "message-content" },
        h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" },
          h("div", { "data-slot": "bubble-content" }, question)))))
  const text = h("p")
  const content = h("div", { "data-slot": "message-content", class: "gap-4" }, text)
  for (const word of answer.match(/\S+\s*/g)) {
    await wait(20)
    if (!content.isConnected) thread.append(h("div", { "data-slot": "message" }, content))
    text.append(word)
  }
  content.append(sourceList(sources))
  replay.hidden = false
})
