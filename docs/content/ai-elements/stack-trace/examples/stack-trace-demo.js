import { h, icon } from "./clanker-ui.js"

const root = document.getElementById("stack-trace-demo")
const replay = document.getElementById("stack-trace-demo-replay")
const question = root.querySelector('[data-slot="bubble-content"]').textContent
const answer = root.querySelector("p:not(.font-mono)").textContent
const [ran, failed] = root.querySelectorAll('[data-slot="message-content"] > [data-slot="trace"] > [data-slot="trace-collapsible"]')
const reset = {
  command: ran.querySelector('[data-slot="trace-title"]').textContent.replace(/^Ran /, ""),
  stdout: ran.querySelector('[data-slot="code-block-code"]').textContent,
}
const seed = {
  command: replay.dataset.command,
  error: failed.querySelector("p").textContent,
  links: [...failed.querySelectorAll("a")].map(a => ({ href: a.getAttribute("href"), title: a.textContent.trim() })),
  frames: [...failed.querySelectorAll("li")].map(li => li.textContent),
}

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function line(name, title, status) {
  return h("span", { "data-slot": "trace-line", "data-status": status },
    h("span", { "data-slot": "trace-icon" }, icon(name)),
    h("span", { "data-slot": "trace-title" }, title))
}

function collapsible(attrs, trigger, ...content) {
  return h("div", { "data-slot": "trace-collapsible", ...attrs },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, trigger),
    h("div", { "data-slot": "trace-collapsible-content" }, ...content))
}

function stackTrace({ error, links, frames }) {
  return collapsible({ "data-default-open": "" }, line("terminal", `Failed: ${error}`, "error"),
    h("div", { class: "flex flex-col gap-2" },
      h("p", { class: "font-mono text-xs text-destructive" }, error),
      h("div", { "data-slot": "trace" },
        links.map(link => h("a", { href: link.href }, line("file-code", link.title))),
        collapsible({}, line("layers", `${frames.length} framework frames`),
          h("ol", { class: "flex flex-col gap-1 overflow-x-auto rounded-md bg-muted p-3 font-mono text-xs" },
            frames.map(frame => h("li", { class: "whitespace-nowrap" }, frame)))))))
}

replay.addEventListener("click", async () => {
  replay.hidden = true
  for (const el of root.querySelectorAll(':scope > [data-slot="message"]')) el.remove()
  root.insertBefore(h("div", { "data-slot": "message", "data-align": "end" },
    h("div", { "data-slot": "message-content" },
      h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" }, h("div", { "data-slot": "bubble-content" }, question)))), replay)
  const trace = h("div", { "data-slot": "trace" })
  const content = h("div", { "data-slot": "message-content", class: "gap-4" }, trace)
  root.insertBefore(h("div", { "data-slot": "message" }, content), replay)
  let running = line("terminal", `Running ${reset.command}`, "running")
  trace.append(running)
  await wait(900)
  running.replaceWith(collapsible({}, line("terminal", `Ran ${reset.command}`),
    h("div", { "data-slot": "code-block", "data-size": "sm" },
      h("pre", { "data-slot": "code-block-content", "data-wrap": "true", class: "max-h-64" },
        h("code", { "data-slot": "code-block-code" }, reset.stdout)))))
  running = line("terminal", `Running ${seed.command}`, "running")
  trace.append(running)
  await wait(1200)
  running.replaceWith(stackTrace(seed))
  const text = new Text("")
  content.append(h("p", {}, text))
  for (const word of answer.match(/\S+\s*/g)) {
    await wait(20)
    text.appendData(word)
  }
  replay.hidden = false
})
