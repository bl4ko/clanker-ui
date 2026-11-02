import { dialogClose, dialogOpen, h, popoverClose } from "./clanker-ui.js"

if (location.pathname === "/" && location.hash.length > 1) {
  let id = location.hash.slice(1)
  try {
    id = decodeURIComponent(id)
  } catch {}
  if (!document.getElementById(id)) location.replace(`/demo${location.hash}`)
}

const field = target => target instanceof HTMLElement && (target.isContentEditable || target.matches("input, textarea, select"))

document.addEventListener("keydown", event => {
  if (event.defaultPrevented || event.isComposing) return
  const shortcut = (event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey) && !event.altKey && !event.shiftKey
  const slash = event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey
  if (!(shortcut || slash) || field(event.target)) return
  if (!document.getElementById("docs-search")) return
  event.preventDefault()
  if (!dialogClose("docs-search", "shortcut")) dialogOpen("docs-search")
})

document.getElementById("docs-search")?.addEventListener("dialog:open", event => {
  const input = event.currentTarget.querySelector('[data-slot="command-input"]')
  if (!input || input.value === "") return
  input.value = ""
  input.dispatchEvent(new Event("input", { bubbles: true }))
})

document.addEventListener("click", event => {
  const target = event.target instanceof Element ? event.target : null
  if (target?.closest('#docs-search [data-slot="command-item"]')) dialogClose("docs-search", "select")
  const menuLink = target?.closest('[data-docs="menu"] a[href]')
  if (menuLink) popoverClose(menuLink.closest('[data-docs="mobile-menu"]'), "select")
})

document.addEventListener("collapsible:open", event => {
  const root = event.target instanceof Element ? event.target : null
  if (!root?.matches('[data-docs="code"]')) return
  root.querySelector('[data-slot="code-block-content"]')?.focus({ preventScroll: true })
})

const toc = document.querySelector('[data-docs="toc"]')
if (toc) {
  const links = new Map()
  for (const link of toc.querySelectorAll('a[href^="#"]')) {
    const heading = document.getElementById(decodeURIComponent(link.hash.slice(1)))
    if (heading) links.set(heading, link)
  }
  const observer = new IntersectionObserver(entries => {
    let current = null
    for (const entry of entries) if (entry.isIntersecting) current = entry.target
    if (!current) return
    for (const [heading, link] of links) link.dataset.active = String(heading === current)
  }, { rootMargin: "0% 0% -80% 0%" })
  for (const heading of links.keys()) observer.observe(heading)
}

const copyButton = document.querySelector('[data-docs="copy-page-button"]')
if (copyButton) {
  let pending = null
  let text = null
  let timer = 0
  const live = h("span", { "aria-live": "polite", class: "sr-only" })
  document.body.append(live)
  const load = () => {
    pending ??= fetch(copyButton.dataset.markdown).then(response => {
      if (!response.ok) throw new Error(`${response.status} ${response.url}`)
      return response.text()
    }).then(body => (text = body), error => {
      pending = null
      throw error
    })
    return pending
  }
  const write = async () => {
    if (text !== null) return navigator.clipboard.writeText(text)
    if (typeof ClipboardItem === "function") {
      try {
        return await navigator.clipboard.write([new ClipboardItem({ "text/plain": load().then(body => new Blob([body], { type: "text/plain" })) })])
      } catch {}
    }
    return navigator.clipboard.writeText(await load())
  }
  copyButton.addEventListener("pointerenter", () => load().catch(() => {}))
  copyButton.addEventListener("focus", () => load().catch(() => {}))
  copyButton.addEventListener("click", async () => {
    try {
      await write()
    } catch {
      return
    }
    copyButton.dataset.copied = ""
    live.textContent = "Copied"
    clearTimeout(timer)
    timer = setTimeout(() => {
      delete copyButton.dataset.copied
      live.textContent = ""
    }, 2000)
  })
}

const prefetched = new Set([location.pathname])
const prefetch = event => {
  const link = event.target instanceof Element ? event.target.closest("a[href]") : null
  if (!link || link.target || link.hasAttribute("download") || link.origin !== location.origin) return
  const url = link.pathname + link.search
  if (prefetched.has(url) || link.pathname.endsWith(".md")) return
  prefetched.add(url)
  const hint = document.createElement("link")
  hint.rel = "prefetch"
  hint.href = url
  document.head.append(hint)
}
document.addEventListener("pointermove", prefetch, { passive: true })
document.addEventListener("pointerdown", prefetch, { passive: true })
document.addEventListener("focusin", prefetch)
