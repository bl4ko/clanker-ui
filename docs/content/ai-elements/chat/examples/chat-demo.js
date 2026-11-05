import { h, icon, traceClose, traceOpen } from "./clanker-ui.js"

const turns = [
  {
    user: "Add a dark mode toggle to the settings page.",
    reasoning: "I need to know how themes are set up before I add a toggle. If next-themes is already in the layout, the toggle only has to call setTheme.",
    command: "rg -l ThemeProvider app",
    output: "app/layout.tsx",
    reply: "next-themes is already set up in `app/layout.tsx`, so the toggle only has to call `setTheme`.\n\n**Changes**\n\n- Added `components/mode-toggle.tsx` with a Light and Dark option.\n- Put `<ModeToggle />` next to the Appearance heading in `app/settings/page.tsx`.\n\n```tsx\nconst { setTheme } = useTheme()\n```",
  },
  {
    user: "Make it follow the system setting by default.",
    reasoning: "The default theme lives on the ThemeProvider. I should check what it is set to now.",
    command: "rg -n defaultTheme app/layout.tsx",
    output: '12:  <ThemeProvider attribute="class" defaultTheme="light">',
    reply: "It was set to `light`. I updated the `ThemeProvider` in `app/layout.tsx`:\n\n```tsx\n<ThemeProvider attribute=\"class\" defaultTheme=\"system\" enableSystem>\n```\n\nNew visitors now get the theme from their OS. The toggle also has a **System** option, so anyone who picked Light or Dark can switch back.",
  },
  {
    user: "Run the build before I ship it.",
    command: "pnpm build",
    wait: 1600,
    output: "▲ Next.js 16.0.0\n\n✓ Compiled successfully in 4.2s\n✓ Linting and checking validity of types\n✓ Generating static pages (12/12)",
    reply: "The build passes, so it is ready to ship.\n\n- Compiled in **4.2s**.\n- No lint or type errors.\n- Generated all **12** static pages.",
  },
]
const fallback = "This demo only knows the scripted turns. Press reset to start over."

const empty = document.getElementById("chat-demo-empty")
const scroller = document.getElementById("chat-demo-scroller")
scroller.remove()
scroller.hidden = false
const thread = document.getElementById("chat-demo-thread")
const form = document.getElementById("chat-demo-form")
const text = document.getElementById("chat-demo-text")
const send = document.getElementById("chat-demo-send")
const reset = document.getElementById("chat-demo-reset")
const still = matchMedia("(prefers-reduced-motion: reduce)")
let next = 0
let busy = false
let run = 0
let id = 0

const wait = ms => new Promise(resolve => setTimeout(() => resolve(), ms))

function inline(line) {
  return line.split(/(`[^`]+`|\*\*[^*]+\*\*)/).filter(Boolean).map(part => {
    if (part.startsWith("`") && part.endsWith("`") && part.length > 1) return h("code", { class: "rounded-sm bg-muted px-1 py-0.5 font-mono text-[0.9em]" }, part.slice(1, -1))
    if (part.startsWith("**") && part.endsWith("**") && part.length > 3) return h("strong", { class: "font-semibold" }, part.slice(2, -2))
    return part
  })
}

function markdown(source) {
  const out = []
  const lines = source.split("\n")
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim() || "text"
      const code = []
      while (++i < lines.length && !lines[i].startsWith("```")) code.push(lines[i])
      out.push(h("div", { "data-slot": "code-block" },
        h("div", { "data-slot": "code-block-header" },
          h("div", { "data-slot": "code-block-title" }, lang),
          h("div", { "data-slot": "code-block-actions" }, h("button", { type: "button", "data-slot": "code-block-copy-button", disabled: i >= lines.length })),
        ),
        h("pre", { "data-slot": "code-block-content", "data-numbered": "true" }, h("code", { "data-slot": "code-block-code" }, code.join("\n")))))
    } else if (line.startsWith("- ")) {
      const items = []
      for (; i < lines.length && lines[i].startsWith("- "); i++) items.push(h("li", { class: "py-1" }, inline(lines[i].slice(2))))
      i--
      out.push(h("ul", { class: "ms-4 list-disc" }, items))
    } else if (line.trim()) {
      out.push(h("p", {}, inline(line)))
    }
  }
  return out
}

async function stream(target, source, render, delay = 16) {
  let shown = ""
  for (const word of source.match(/\S+\s*/g) ?? []) {
    shown += word
    target.replaceChildren(...render(shown))
    await wait(delay)
  }
  target.replaceChildren(...render(source))
}

function item(role, body) {
  const attrs = { "data-slot": "message-scroller-item", "data-message-id": `m${++id}` }
  if (role === "user") attrs["data-scroll-anchor"] = "true"
  const row = h("div", attrs,
    h("div", { "data-slot": "message", "data-align": role === "user" ? "end" : null }, body))
  thread.append(row)
  if (role === "user" && !still.matches) row.animate([{ opacity: 0, translate: "0 10px" }, { opacity: 1, translate: "0 0" }], { duration: 260, easing: "cubic-bezier(0.16, 1, 0.3, 1)" })
  return row
}

function line(iconName, title, status, spin) {
  return h("span", { "data-slot": "trace-line", "data-status": status },
    h("span", { "data-slot": "trace-icon" }, icon(iconName, spin ? { class: "animate-spin" } : {})),
    h("span", { "data-slot": "trace-title" }, title))
}

function setLine(target, iconName, title, status, spin) {
  target.replaceWith(line(iconName, title, status, spin))
}

async function reasoning(trace, source, token) {
  const content = h("div", { "data-slot": "trace-collapsible-content", class: "whitespace-pre-wrap" })
  const step = h("div", { "data-slot": "trace-collapsible" },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, line("loader-circle", "Thinking", "running", true)),
    content)
  let touched = false
  step.addEventListener("click", event => {
    if (event.target.closest('[data-slot="trace-collapsible-trigger"]')) touched = true
  })
  trace.append(step)
  traceOpen(step, { animate: false })
  await stream(content, source, shown => [shown])
  if (token !== run) return
  setLine(step.querySelector('[data-slot="trace-line"]'), "circle-check", "Thought")
  if (!touched) traceClose(step)
}

async function tool(trace, command, output, ms, token) {
  const running = line("terminal", `Running ${command}`, "running")
  trace.append(running)
  await wait(ms)
  if (token !== run) return
  running.replaceWith(h("div", { "data-slot": "trace-collapsible" },
    h("button", { type: "button", "data-slot": "trace-collapsible-trigger" }, line("terminal", `Ran ${command}`)),
    h("div", { "data-slot": "trace-collapsible-content" },
      h("div", { "data-slot": "code-block", "data-size": "sm" },
        h("pre", { "data-slot": "code-block-content", "data-wrap": "true", class: "max-h-64" }, h("code", { "data-slot": "code-block-code" }, output))))))
}

function state() {
  const has = thread.querySelector(':scope > [data-slot="message-scroller-item"]') !== null
  if (has && empty.isConnected) empty.replaceWith(scroller)
  if (!has && scroller.isConnected) scroller.replaceWith(empty)
  thread.setAttribute("aria-busy", String(busy))
  reset.disabled = busy
  send.disabled = busy || text.value.trim() === ""
}

async function play(prompt) {
  const token = run
  const turn = turns[next]?.user === prompt ? turns[next++] : null
  busy = true
  text.value = ""
  item("user", h("div", { "data-slot": "message-content" },
    h("div", { "data-slot": "bubble", "data-align": "end", "data-variant": "muted" }, h("div", { "data-slot": "bubble-content" }, prompt))))
  state()
  await wait(600)
  if (token !== run) return
  const content = h("div", { "data-slot": "message-content", class: "gap-3" })
  item("assistant", content)
  if (turn) {
    const trace = h("div", { "data-slot": "trace" })
    content.append(trace)
    if (turn.reasoning) {
      await reasoning(trace, turn.reasoning, token)
      await wait(400)
      if (token !== run) return
    }
    await tool(trace, turn.command, turn.output, turn.wait ?? 800, token)
    await wait(500)
    if (token !== run) return
  }
  const reply = h("div", { class: "flex flex-col gap-4" })
  content.append(reply)
  await stream(reply, turn ? turn.reply : fallback, markdown)
  if (token !== run) return
  busy = false
  text.value = turns[next]?.user ?? ""
  state()
}

text.addEventListener("input", state)

text.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault()
    form.requestSubmit()
  }
})

form.addEventListener("submit", event => {
  event.preventDefault()
  const prompt = text.value.trim()
  if (prompt && !busy) play(prompt)
})

reset.addEventListener("click", () => {
  run++
  busy = false
  next = 0
  for (const row of thread.querySelectorAll(':scope > [data-slot="message-scroller-item"]')) row.remove()
  text.value = turns[0].user
  state()
})

state()
