import { h, icon, traceClose } from "./clanker-ui.js"

const root = document.getElementById("chain-of-thought-demo")
const replay = document.getElementById("chain-of-thought-demo-replay")
const question = root.querySelector('[data-slot="bubble-content"]').textContent
const answer = root.querySelector("p").textContent

const links = [
  ["Image component | nextjs.org", "https://nextjs.org/docs/app/api-reference/components/image"],
  ["Build cache | vercel.com", "https://vercel.com/docs/deployments/troubleshoot-a-build"],
]

const steps = [
  {
    running: "Reading the build log for dpl_8Kx2",
    done: "Read the build log for dpl_8Kx2",
    open: true,
    output: () => h("div", { "data-slot": "code-block", "data-size": "sm" },
      h("pre", { "data-slot": "code-block-content", "data-wrap": "true", class: "max-h-64" },
        h("code", { "data-slot": "code-block-code" }, "install    41s\ncompile    38s\nimages   3m 52s"))),
  },
  {
    running: "Searching the web for next.js image cache key",
    done: "Searched the web for next.js image cache key",
    output: () => h("div", { "data-slot": "trace" }, links.map(([title, href]) =>
      h("a", { href, target: "_blank", rel: "noreferrer" },
        h("span", { "data-slot": "trace-line" },
          h("span", { "data-slot": "trace-icon" }, icon("globe")),
          h("span", { "data-slot": "trace-title" }, title, h("span", { class: "sr-only" }, " (opens in a new tab)")),
          h("span", { "data-slot": "trace-icon" }, icon("arrow-up-right")))))),
  },
  {
    running: "Searching the code for cacheKey",
    done: "Searched the code for cacheKey",
    output: () => h("div", { class: "flex flex-wrap gap-1.5" }, ["next.config.ts", "scripts/optimize-images.ts"].map(file =>
      h("span", { "data-slot": "badge", "data-variant": "secondary", class: "font-mono" }, file))),
  },
]

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function line(title, running) {
  return h("span", { "data-slot": "trace-line", "data-status": running ? "running" : null },
    h("span", { "data-slot": "trace-icon" }, running ? icon("loader-circle", { class: "animate-spin" }) : icon("circle-check")),
    h("span", { "data-slot": "trace-title" }, title))
}

replay.addEventListener("click", async () => {
  replay.hidden = true
  for (const el of root.querySelectorAll(':scope > [data-slot="message"]')) el.remove()
  root.insertBefore(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" }, h("div", { "data-slot": "bubble-content" }, question)))), replay)
  let touched = false
  const list = h("div", { "data-slot": "trace" })
  const trigger = h("button", { type: "button", "data-slot": "trace-collapsible-trigger", onclick: () => { touched = true } }, line("Researching", true))
  const summary = h("div", { "data-slot": "trace-collapsible", "data-default-open": "" }, trigger,
    h("div", { "data-slot": "trace-collapsible-content" }, list))
  const content = h("div", { "data-slot": "message-content", class: "gap-4" }, h("div", { "data-slot": "trace" }, summary))
  root.insertBefore(h("div", { "data-slot": "message" }, content), replay)
  for (const step of steps) {
    const running = line(step.running, true)
    list.append(running)
    await wait(900)
    running.replaceWith(h("div", { "data-slot": "trace-collapsible", "data-default-open": step.open ? "" : null },
      h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, line(step.done, false)),
      h("div", { "data-slot": "trace-collapsible-content" }, step.output())))
  }
  trigger.firstElementChild.replaceWith(line(`Researched in ${steps.length} steps`, false))
  if (!touched) traceClose(summary)
  const text = new Text("")
  content.append(h("p", {}, text))
  for (const word of answer.match(/\S+\s*/g)) {
    await wait(20)
    text.appendData(word)
  }
  replay.hidden = false
})
