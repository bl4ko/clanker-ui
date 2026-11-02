(() => {
  const key = "docs-sidebar-scroll"
  let stored = null
  try {
    stored = JSON.parse(sessionStorage.getItem(key) ?? "null")
  } catch {}
  let done = false
  const save = content => {
    if (!content.clientHeight) return
    try {
      sessionStorage.setItem(key, JSON.stringify({ pathname: location.pathname, scrollTop: content.scrollTop }))
    } catch {}
  }
  const activeItem = content => {
    const box = content.getBoundingClientRect()
    const center = box.top + content.clientHeight / 2
    let best = null
    let length = -1
    let distance = Infinity
    for (const item of content.querySelectorAll('[data-active="true"]')) {
      const href = item.getAttribute("href") ?? ""
      const rect = item.getBoundingClientRect()
      const d = Math.abs(rect.top + rect.height / 2 - center)
      if (href.length > length || (href.length === length && d < distance)) {
        best = item
        length = href.length
        distance = d
      }
    }
    return best
  }
  const restore = parsed => {
    if (done) return
    const content = document.querySelector("[data-docs-sidebar-content]")
    if (!content) return
    const complete = parsed || content.parentElement?.nextElementSibling != null
    if (content.clientHeight && typeof stored?.scrollTop === "number") content.scrollTop = stored.scrollTop
    if (!complete) return
    done = true
    observer.disconnect()
    if (content.clientHeight && stored?.pathname !== location.pathname) {
      const active = activeItem(content)
      if (active) {
        const box = content.getBoundingClientRect()
        const rect = active.getBoundingClientRect()
        if (rect.top < box.top || rect.bottom > box.bottom) content.scrollTop += rect.top - box.top - (content.clientHeight - rect.height) / 2
      }
    }
    save(content)
    content.addEventListener("scroll", () => save(content), { passive: true })
  }
  const observer = new MutationObserver(() => restore(false))
  observer.observe(document.documentElement, { childList: true, subtree: true })
  document.addEventListener("DOMContentLoaded", () => restore(true), { once: true })
})()
