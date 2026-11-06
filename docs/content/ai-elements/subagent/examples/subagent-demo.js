import { h, icon } from "./clanker-ui.js"

const STEPS = [
  { command: "grep -rn cacheKey scripts", stdout: "scripts/optimize-images.ts:14:  const cacheKey = process.env.COMMIT_SHA" },
  { command: "sed -n 13,15p scripts/optimize-images.ts", stdout: 'const cacheDir = ".next/cache/images"\nconst cacheKey = process.env.COMMIT_SHA\nconst cached = await restoreCache(cacheDir, cacheKey)' },
  { command: "ls public/images | wc -l", stdout: "1240" },
]
const REPORT = "The cache is keyed on the commit SHA, so every deploy misses it and optimizes all 1,240 images again."
const ANSWER = "Image optimization reruns because its cache is keyed on the commit SHA, which changes on every deploy. Key the cache on a hash of public/images instead, and unchanged images will be skipped."

const root = document.getElementById("subagent-demo")
const replay = document.getElementById("subagent-demo-replay")
const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function spinner() {
  const el = icon("loader-circle")
  el.classList.add("animate-spin")
  return el
}

function line(title, running) {
  return h("span", { "data-slot": "trace-line", "data-status": running ? "running" : null },
    h("span", { "data-slot": "trace-icon" }, running ? spinner() : icon("circle-check")),
    h("span", { "data-slot": "trace-title" }, title))
}

function stepRow(step, done) {
  if (!done) return line(`Running ${step.command}`, true)
  return h("div", { "data-slot": "trace-collapsible" },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, line(`Ran ${step.command}`, false)),
    h("div", { "data-slot": "trace-collapsible-content" },
      h("div", { "data-slot": "code-block", "data-size": "sm" },
        h("pre", { "data-slot": "code-block-content", "data-wrap": "true", class: "max-h-64" },
          h("code", { "data-slot": "code-block-code" }, step.stdout)))))
}

async function stream(parent, text) {
  const p = h("p")
  for (const word of text.match(/\S+\s*/g)) {
    await wait(20)
    if (!p.isConnected) parent.append(p)
    p.append(word)
  }
}

replay.addEventListener("click", async () => {
  replay.hidden = true
  for (const message of root.querySelectorAll(':scope > [data-slot="message"]')) message.remove()
  replay.before(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" },
        h("div", { "data-slot": "bubble-content" }, "Why does image optimization rerun on every deploy?")))))
  const trace = h("div", { "data-slot": "trace" }, line("Running the research subagent", true))
  const content = h("div", { "data-slot": "message-content", class: "gap-4" }, trace)
  replay.before(h("div", { "data-slot": "message" }, content))
  await wait(600)
  const title = h("span", { "data-slot": "trace-title" }, "Running the research subagent")
  const status = h("span", { "data-slot": "trace-line", "data-status": "running" }, h("span", { "data-slot": "trace-icon" }, spinner()), title)
  const steps = h("div", { "data-slot": "trace" })
  const body = h("div", { "data-slot": "trace-collapsible-content" }, h("div", { class: "flex flex-col gap-3" }, steps))
  trace.replaceChildren(h("div", { "data-slot": "trace-collapsible", "data-default-open": true },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, status), body))
  for (let done = 0; done <= STEPS.length; done++) {
    if (done > 0) {
      await wait(1000)
      steps.lastElementChild.replaceWith(stepRow(STEPS[done - 1], true))
    }
    if (done < STEPS.length) steps.append(stepRow(STEPS[done], false))
  }
  status.removeAttribute("data-status")
  status.querySelector('[data-slot="trace-icon"]').replaceChildren(icon("circle-check"))
  title.textContent = "Ran the research subagent"
  steps.after(h("p", {}, REPORT))
  await wait(400)
  await stream(content, ANSWER)
  replay.hidden = false
})
