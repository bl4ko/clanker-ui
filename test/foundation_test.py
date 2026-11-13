import re
import time

START = "/demo?only=introduction,getting-started"

EVIL = '<img src="x" onerror="alert(document.domain)">'


def lightness(color):
    m = re.match(r"oklch\(\s*([\d.]+)(%?)", color)
    if m:
        value = float(m.group(1))
        return value / 100 if m.group(2) else value
    m = re.match(r"(?:rgba?|color\(srgb)\(?\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)", color)
    assert m, f"cannot parse color {color}"
    r, g, b = (float(x) for x in m.groups())
    scale = 1 if color.startswith("color(") else 255
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / scale


def page_is_dark(page):
    return lightness(page.evaluate("getComputedStyle(document.body).backgroundColor")) < 0.5


def check_page(t):
    t.docs("/demo")
    page = t.page
    assert page.title() == "clanker-ui"
    assert page.locator("h1").first.is_visible()
    empty = page.evaluate("() => [...document.querySelectorAll('svg[data-lucide]')].filter(s => !s.firstElementChild).length")
    assert empty == 0, f"{empty} icons were not filled"
    assert page_is_dark(page) == (t.theme == "dark")
    if t.mobile:
        nav = page.locator("#demo-nav")
        assert not nav.is_visible()
        page.get_by_role("button", name="Open navigation").click()
        assert nav.is_visible()
        t.settle()
        t.shot("nav-open", page)
        nav.get_by_role("link", name="Typography").click()
        assert not nav.is_visible()
    t.shot("top", page)


NAV_COUNT = """() => {
  window.__navAdded = 0
  window.__navWatch?.disconnect()
  window.__navWatch = new MutationObserver(records => {
    for (const r of records) if (r.oldValue === null) window.__navAdded++
  })
  window.__navWatch.observe(document.getElementById("demo-nav"), { subtree: true, attributeFilter: ["aria-current"], attributeOldValue: true })
}"""

PAGE_REST = """() => new Promise(resolve => {
  let last = null
  let still = 0
  const tick = () => {
    still = scrollY === last ? still + 1 : 0
    last = scrollY
    if (still < 20) requestAnimationFrame(tick)
    else resolve(scrollY)
  }
  requestAnimationFrame(tick)
})"""

NAV_LOOK = """(e, side) => {
  const s = getComputedStyle(e)
  const bar = getComputedStyle(e, "::before")
  return [s.backgroundColor, s.color, s.fontWeight, bar.content, bar.width, bar[side]]
}"""

NAV_INSIDE = """() => {
  const nav = document.getElementById("demo-nav")
  const n = nav.getBoundingClientRect()
  const r = nav.querySelector("a[aria-current]").getBoundingClientRect()
  const top = nav.scrollTop < 1 || r.top >= n.top + 47
  const bottom = nav.scrollTop > nav.scrollHeight - nav.clientHeight - 1 || r.bottom <= n.bottom - 47
  return [r.top >= n.top && r.bottom <= n.bottom, top && bottom, Math.round(scrollY)]
}"""


def demo_nav_close(t):
    if t.mobile and t.page.locator("#demo-nav").is_visible():
        t.page.keyboard.press("Escape")
        t.page.wait_for_function("() => !document.getElementById('demo-nav').matches(':popover-open')")


def demo_nav_open(t):
    nav = t.page.locator("#demo-nav")
    if t.mobile and not nav.is_visible():
        t.page.get_by_role("button", name="Open navigation").click()
        t.page.wait_for_function("() => document.getElementById('demo-nav').matches(':popover-open')")
        t.settle()
    return nav


def check_demo_nav(t):
    t.docs("/demo")
    page = t.page
    nav = demo_nav_open(t)
    current = nav.locator("a[aria-current]")
    assert current.count() == 1 and current.get_attribute("href") == "#introduction"
    hovered = nav.locator('a[href="#typography"]')
    hovered.hover()
    t.settle()
    side = "right" if t.rtl else "left"
    now, hover = current.evaluate(NAV_LOOK, side), hovered.evaluate(NAV_LOOK, side)
    assert now[2:] == ["600", '""', "2px", "0px"]
    assert hover[2:4] == ["500", "none"]
    assert now != hover
    t.shot("nav-hover", nav)
    for target in ["chart", "calendar"]:
        nav = demo_nav_open(t)
        link = nav.locator(f'a[href="#{target}"]')
        link.evaluate("a => { const n = a.closest('nav'); n.scrollTop += a.getBoundingClientRect().top - n.getBoundingClientRect().top - n.clientHeight / 2 }")
        box = link.bounding_box()
        page.evaluate(NAV_COUNT)
        frames = t.paint("() => Math.round(scrollY)", lambda: page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2), ms=500)
        page.evaluate(PAGE_REST)
        added = page.evaluate("window.__navAdded")
        assert added == 1, (target, added)
        assert link.get_attribute("aria-current") == "true"
        assert len(set(frames)) <= 2, frames
        top = page.locator(f"#{target} [data-demo=title]").evaluate("e => e.getBoundingClientRect().top")
        assert abs(top - 144) <= 1, (target, top)
        if t.mobile:
            assert not nav.is_visible()
    main = page.locator('[data-demo="main"]').bounding_box()
    for step in range(1, 10):
        demo_nav_close(t)
        page.mouse.move(main["x"] + main["width"] / 2, 400)
        page.evaluate("f => scrollTo({ top: f * (document.documentElement.scrollHeight - innerHeight), behavior: 'instant' })", step / 10)
        page.evaluate(PAGE_REST)
        page.mouse.wheel(0, 600)
        page.evaluate(PAGE_REST)
        nav = demo_nav_open(t)
        inside, margin, y = page.evaluate(NAV_INSIDE)
        assert inside and margin, (y, inside, margin)
    t.shot("nav-follow", nav)
    assert page.evaluate("""() => new Promise(resolve => {
      const nav = document.getElementById("demo-nav")
      nav.scrollTop = 0
      dispatchEvent(new Event("scroll"))
      requestAnimationFrame(() => requestAnimationFrame(() => resolve(nav.scrollTop)))
    })""") == 0


def check_theme(t):
    page = t.page
    root = page.locator("html")
    switch = page.locator("#theming [data-slot='theme-switch']")
    assert root.get_attribute("data-theme") == "system"
    assert switch.get_by_role("button", name="System theme").get_attribute("aria-pressed") == "true"
    assert page_is_dark(page) == (t.theme == "dark")
    page.evaluate("() => { window.__themeEvents = []; document.documentElement.addEventListener('theme:change', e => window.__themeEvents.push(e.detail)) }")
    switch.get_by_role("button", name="Dark theme").click()
    assert root.get_attribute("data-theme") == "dark"
    assert switch.get_by_role("button", name="Dark theme").get_attribute("aria-pressed") == "true"
    assert switch.get_by_role("button", name="System theme").get_attribute("aria-pressed") == "false"
    assert page.evaluate("localStorage.getItem('clanker-ui-theme')") == "dark"
    assert page_is_dark(page)
    assert page.evaluate("window.__themeEvents") == [{"mode": "dark", "resolved": "dark", "scheme": ""}]
    page.reload(wait_until="load")
    assert root.get_attribute("data-theme") == "dark"
    assert page_is_dark(page)
    switch.get_by_role("button", name="Light theme").click()
    assert not page_is_dark(page)
    toggle = page.locator("#theming [data-theme-set='toggle']")
    toggle.scroll_into_view_if_needed()
    toggle.click()
    assert root.get_attribute("data-theme") == "dark" and page_is_dark(page)
    assert page.locator("#theme-status").inner_text() == "Mode: dark. Showing dark."
    toggle.click()
    assert root.get_attribute("data-theme") == "light"
    switch.get_by_role("button", name="System theme").click()
    assert page.evaluate("localStorage.getItem('clanker-ui-theme')") is None
    assert page_is_dark(page) == (t.theme == "dark")
    t.section("theming")


THEME_FRAMES = """(() => {
  const frames = window.__themeFrames = []
  const tick = () => {
    frames.push([document.body !== null, document.documentElement?.getAttribute("data-theme") ?? null])
    if (frames.length < 240) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
})()"""


def check_theme_first_frame(t):
    page = t.page
    stored = "light" if t.theme == "dark" else "dark"
    page.evaluate("v => localStorage.setItem('clanker-ui-theme', v)", stored)
    page.add_init_script(THEME_FRAMES)
    page.route(re.compile(r"/clanker-ui\.js$"), lambda route: (time.sleep(0.5), route.continue_()))
    page.reload(wait_until="load")
    page.unroute_all()
    painted = [theme for body, theme in page.evaluate("window.__themeFrames") if body]
    assert painted, "no frame was painted before load"
    assert painted[0] == stored, f"the first painted frame has data-theme {painted[0]!r}, want {stored!r}"
    assert set(painted) == {stored}, painted
    assert page.evaluate("getComputedStyle(document.body).backgroundColor") != "rgba(0, 0, 0, 0)", "<body> has no kit styles"
    assert page_is_dark(page) == (stored == "dark")


SCHEME_GATES = [
    ["text", "foreground", ["background", "card", "popover", "muted"], 4.5],
    ["text", "card-foreground", ["card"], 4.5],
    ["text", "popover-foreground", ["popover"], 4.5],
    ["text", "secondary-foreground", ["secondary"], 4.5],
    ["text", "accent-foreground", ["accent"], 4.5],
    ["muted-foreground", "muted-foreground", ["background", "muted", "card", "popover"], 4.5],
    ["primary-foreground", "primary-foreground", ["primary"], 4.5],
    ["destructive text", "destructive", ["background", "card", "popover"], 4.5],
    ["input", "input-edge", ["background", "card", "popover", "sidebar"], 3],
    ["focus-ring", "focus-ring", ["background", "card", "popover"], 3],
    *[["status text", f"{k}-text", [f"{k}-bg"], 4.5] for k in ["success", "info", "warning", "error"]],
    *[["status border", f"{k}-border", ["background", "card"], 3] for k in ["success", "info", "warning", "error"]],
    ["sidebar text", "sidebar-foreground", ["sidebar", "sidebar-accent"], 4.5],
    ["sidebar text", "sidebar-accent-foreground", ["sidebar-accent"], 4.5],
    ["sidebar text", "sidebar-primary-foreground", ["sidebar-primary"], 4.5],
]

SCHEME_MEASURE = r"""async gates => {
  const { theme } = await import("/clanker-ui.js")
  const root = document.documentElement
  const saved = ["data-scheme", "data-theme"].map(n => [n, root.getAttribute(n)])
  const tokens = [...new Set(gates.flatMap(([, fg, bgs]) => [fg, ...bgs]))]
  const host = document.body.appendChild(document.createElement("div"))
  Object.assign(host.style, { position: "fixed", left: "-100px", top: "0", width: "1px", height: "1px", overflow: "hidden" })
  const probes = tokens.map(t => {
    const p = host.appendChild(document.createElement("span"))
    p.style.color = `color-mix(in srgb, var(--${t}) 100%, transparent)`
    return [t, p]
  })
  const parse = s => {
    const m = s.match(/color\(srgb ([-\d.e]+) ([-\d.e]+) ([-\d.e]+)(?: \/ ([\d.]+))?\)/)
    return [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]].map(x => Math.min(1, Math.max(0, x)))
  }
  const over = (f, b) => [0, 1, 2].map(i => f[3] * f[i] + (1 - f[3]) * b[i]).concat(1)
  const lum = c => { const [x, y, z] = c.slice(0, 3).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); return 0.2126 * x + 0.7152 * y + 0.0722 * z }
  const ratio = (f, b) => { const p = lum(over(f, b)), q = lum(b); return (Math.max(p, q) + 0.05) / (Math.min(p, q) + 0.05) }
  const bases = theme.schemes.filter(s => s.group !== "accent").map(s => s.value)
  const shadcn = theme.schemes.filter(s => s.group === "shadcn").map(s => s.value)
  const accents = theme.schemes.filter(s => s.group === "accent").map(s => s.value)
  const combos = [...bases, ...shadcn.flatMap(b => [...accents, "menu-bold"].map(a => `${b} ${a}`))]
  const worst = {}, failures = [], signature = {}, shown = {}
  root.setAttribute("data-theme-switching", "")
  const hidden = [...document.body.children].filter(el => el !== host).map(el => [el, el.style.display])
  for (const [el] of hidden) el.style.display = "none"
  for (const scheme of combos) {
    for (const mode of ["light", "dark"]) {
      root.setAttribute("data-scheme", scheme)
      root.setAttribute("data-theme", mode)
      const c = Object.fromEntries(probes.map(([t, p]) => [t, parse(getComputedStyle(p).color)]))
      const page = c.background
      if (bases.includes(scheme)) {
        signature[scheme] = (signature[scheme] ?? "") + JSON.stringify([c.background, c.primary])
        shown[`${scheme} ${mode}`] = getComputedStyle(root).colorScheme
      }
      for (const [gate, fg, bgs, min] of gates) {
        for (const bg of bgs) {
          const b = c[bg][3] < 1 ? over(c[bg], page) : c[bg]
          const r = ratio(c[fg], b)
          const key = `${scheme.split(" ")[0]}|${scheme.includes(" ") ? "accent" : "base"}|${mode}|${gate}`
          if (!worst[key] || r < worst[key][0]) worst[key] = [+r.toFixed(2), `${fg} on ${bg}`, scheme]
          if (r < min) failures.push(`${scheme} ${mode}: ${fg} on ${bg} ${r.toFixed(2)} < ${min}`)
        }
      }
    }
  }
  for (const [n, v] of saved) v === null ? root.removeAttribute(n) : root.setAttribute(n, v)
  for (const [el, display] of hidden) el.style.display = display
  void root.offsetHeight
  root.removeAttribute("data-theme-switching")
  host.remove()
  return { combos: combos.length, bases: bases.length, distinct: new Set(Object.values(signature)).size, failures, worst, shown }
}"""


SCHEME_EXACT = """want => {
  const root = document.documentElement
  const saved = ["data-scheme", "data-theme"].map(n => [n, root.getAttribute(n)])
  const names = ["muted-foreground", "input", "chart-1", "primary", "sidebar-primary"]
  const probe = document.body.appendChild(document.createElement("span"))
  const color = v => { probe.style.color = v; return getComputedStyle(probe).color }
  const bad = []
  for (const [key, values] of Object.entries(want)) {
    const [scheme, mode] = key.split(" ")
    root.setAttribute("data-scheme", scheme === "blue" ? "neutral blue" : scheme)
    root.setAttribute("data-theme", mode)
    names.forEach((n, i) => {
      const got = color(`var(--${n})`), exp = color(values[i])
      if (got !== exp) bad.push(`${key} --${n}: ${got} != ${exp}`)
    })
  }
  probe.remove()
  for (const [n, v] of saved) v === null ? root.removeAttribute(n) : root.setAttribute(n, v)
  return bad
}"""
SCHEME_EXACT_WANT = {
    "stone light": ["oklch(0.553 0.013 58.071)", "oklch(0.923 0.003 48.717)", "oklch(0.869 0.005 56.366)", "oklch(0.216 0.006 56.043)", "oklch(0.216 0.006 56.043)"],
    "stone dark": ["oklch(0.709 0.01 56.259)", "oklch(1 0 0 / 15%)", "oklch(0.869 0.005 56.366)", "oklch(0.923 0.003 48.717)", "oklch(0.488 0.243 264.376)"],
    "neutral light": ["oklch(0.556 0 0)", "oklch(0.922 0 0)", "oklch(0.87 0 0)", "oklch(0.205 0 0)", "oklch(0.205 0 0)"],
    "zinc dark": ["oklch(0.705 0.015 286.067)", "oklch(1 0 0 / 15%)", "oklch(0.871 0.006 286.286)", "oklch(0.92 0.004 286.32)", "oklch(0.488 0.243 264.376)"],
    "blue light": ["oklch(0.556 0 0)", "oklch(0.922 0 0)", "oklch(0.87 0 0)", "oklch(0.488 0.243 264.376)", "oklch(0.546 0.245 262.881)"],
}


def check_scheme_contrast(t):
    if t.mobile:
        t.skip("colors do not depend on the viewport width")
    page = t.page
    exact = page.evaluate(SCHEME_EXACT, SCHEME_EXACT_WANT)
    assert exact == [], exact
    t.a11y()
    result = page.evaluate(SCHEME_MEASURE, SCHEME_GATES)
    assert result["bases"] == 26 and result["combos"] == 26 + 9 * 18, (result["bases"], result["combos"])
    assert result["distinct"] == result["bases"], f"only {result['distinct']} of {result['bases']} schemes change the colors"
    assert not result["failures"], f"{len(result['failures'])} contrast failures: {result['failures'][:20]}"
    forced = sorted(k.split(" ")[0] for k, v in result["shown"].items() if k.endswith(" light") and v == "dark")
    assert forced == ["nord"], forced
    t.section("themes")


CODE_CONTRAST = r"""async () => {
  const { theme, h } = await import("/clanker-ui.js")
  const root = document.documentElement
  const saved = ["data-scheme", "data-theme"].map(n => [n, root.getAttribute(n)])
  const tokens = ["comment", "keyword", "string", "constant", "function", "variable", "tag", "inserted", "deleted"]
  const host = document.body.appendChild(h("div"))
  Object.assign(host.style, { position: "fixed", left: "-2000px", top: "0", width: "600px" })
  const probe = host.appendChild(h("span"))
  const parse = s => {
    const m = s.match(/color\(srgb ([-\d.e]+) ([-\d.e]+) ([-\d.e]+)(?: \/ ([\d.]+))?\)/)
    return [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]].map(x => Math.min(1, Math.max(0, x)))
  }
  const srgb = v => { probe.style.color = `color-mix(in srgb, ${v} 100%, transparent)`; return parse(getComputedStyle(probe).color) }
  const over = (f, b) => [0, 1, 2].map(i => f[3] * f[i] + (1 - f[3]) * b[i]).concat(1)
  const lum = c => { const [x, y, z] = c.slice(0, 3).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); return 0.2126 * x + 0.7152 * y + 0.0722 * z }
  const ratio = (f, b) => { const p = lum(over(f, b)), q = lum(b); return (Math.max(p, q) + 0.05) / (Math.min(p, q) + 0.05) }
  const parents = ["background", "card"].map(bg => {
    const lines = ["default", "highlighted", "removed"].map(v => h("span", { "data-slot": "code-block-line", "data-variant": v }, tokens.map(k => h("span", { "data-token": k }, k))))
    const parent = host.appendChild(h("div", h("div", { "data-slot": "code-block" }, h("pre", { "data-slot": "code-block-content" }, h("code", { "data-slot": "code-block-code" }, lines)))))
    parent.style.backgroundColor = `var(--${bg})`
    return [bg, parent, parent.firstChild, lines]
  })
  const bases = theme.schemes.filter(s => s.group !== "accent").map(s => s.value)
  const failures = [], signature = {}
  let worst = 99
  root.setAttribute("data-theme-switching", "")
  for (const scheme of ["", ...bases]) {
    for (const mode of ["light", "dark"]) {
      scheme ? root.setAttribute("data-scheme", scheme) : root.removeAttribute("data-scheme")
      root.setAttribute("data-theme", mode)
      for (const [bg, parent, block, lines] of parents) {
        const fill = over(srgb(getComputedStyle(block).backgroundColor), srgb(getComputedStyle(parent).backgroundColor))
        for (const line of lines) {
          const band = over(srgb(getComputedStyle(line).backgroundColor), fill)
          for (const span of line.children) {
            const color = getComputedStyle(span).color
            if (bg === "background" && line.dataset.variant === "default") signature[scheme] = (signature[scheme] ?? "") + color
            const r = ratio(srgb(color), band)
            worst = Math.min(worst, r)
            if (r < 4.5) failures.push(`${scheme || "kit"} ${mode} ${span.dataset.token} on ${bg} ${line.dataset.variant} ${r.toFixed(2)}`)
          }
        }
      }
    }
  }
  for (const [n, v] of saved) v === null ? root.removeAttribute(n) : root.setAttribute(n, v)
  void root.offsetHeight
  root.removeAttribute("data-theme-switching")
  host.remove()
  const editors = theme.schemes.filter(s => s.group === "editor").map(s => s.value)
  return { failures, worst: +worst.toFixed(2), same: editors.filter(s => signature[s] === signature[""]), editors: editors.length }
}"""


def check_code_token_contrast(t):
    if t.mobile:
        t.skip("colors do not depend on the viewport width")
    page = t.page
    plain = page.evaluate(CODE_CONTRAST)
    kit = [f for f in plain["failures"] if f.startswith("kit ")]
    assert kit == [], kit
    t.a11y()
    result = page.evaluate(CODE_CONTRAST)
    assert result["editors"] == 17 and result["same"] == [], result
    assert not result["failures"], f"{len(result['failures'])} code token contrast failures: {result['failures'][:20]}"


DESTRUCTIVE_TINT = r"""async () => {
  const { theme, h, icon } = await import("/clanker-ui.js")
  const root = document.documentElement
  const saved = ["data-scheme", "data-theme"].map(n => [n, root.getAttribute(n)])
  const host = document.body.appendChild(h("div"))
  Object.assign(host.style, { position: "fixed", left: "-2000px", top: "0", width: "600px" })
  const probe = host.appendChild(h("span"))
  const parse = s => {
    const m = s.match(/color\(srgb ([-\d.e]+) ([-\d.e]+) ([-\d.e]+)(?: \/ ([\d.]+))?\)/)
    return [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]].map(x => Math.min(1, Math.max(0, x)))
  }
  const srgb = v => { probe.style.color = `color-mix(in srgb, ${v} 100%, transparent)`; return parse(getComputedStyle(probe).color) }
  const over = (f, b) => [0, 1, 2].map(i => f[3] * f[i] + (1 - f[3]) * b[i]).concat(1)
  const lum = c => { const [x, y, z] = c.slice(0, 3).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); return 0.2126 * x + 0.7152 * y + 0.0722 * z }
  const ratio = (f, b) => { const p = lum(over(f, b)), q = lum(b); return (Math.max(p, q) + 0.05) / (Math.min(p, q) + 0.05) }
  const parts = ["background", "card", "popover"].map(bg => {
    const box = host.appendChild(h("div", h("span", { "data-slot": "badge", "data-variant": "destructive" }, icon("clock"), "Overdue"), h("button", { "data-slot": "button", "data-variant": "destructive", type: "button" }, "Delete")))
    box.style.backgroundColor = `var(--${bg})`
    return [bg, box]
  })
  const failures = [], untokened = []
  let worst = 99
  for (const scheme of theme.schemes.filter(s => s.group !== "accent").map(s => s.value)) {
    theme.setScheme(scheme)
    for (const mode of ["light", "dark"]) {
      theme.set(mode)
      const dark = getComputedStyle(root).colorScheme === "dark"
      for (const [bg, box] of parts) {
        const surface = srgb(`var(--${bg})`)
        for (const el of box.children) {
          const text = srgb(getComputedStyle(el).color)
          probe.style.color = "color-mix(in srgb, var(--destructive-text) 100%, transparent)"
          const token = /color\(srgb/.test(getComputedStyle(probe).color) ? parse(getComputedStyle(probe).color) : null
          if (!token || text.some((v, i) => Math.abs(v - token[i]) > 0.002)) untokened.push(`${scheme} ${mode} ${el.dataset.slot}`)
          for (const tint of dark ? [20, 30] : [10, 20]) {
            const r = ratio(text, over(srgb(`color-mix(in oklab, var(--destructive) ${tint}%, transparent)`), surface))
            worst = Math.min(worst, r)
            if (r < 4.5) failures.push(`${scheme} ${mode} ${el.dataset.slot} on ${bg} + ${tint} %: ${r.toFixed(2)}`)
          }
        }
      }
    }
  }
  host.remove()
  for (const [n, v] of saved) v === null ? root.removeAttribute(n) : root.setAttribute(n, v)
  return { failures, untokened, worst: +worst.toFixed(2) }
}"""


def check_scheme_destructive_text(t):
    if t.mobile:
        t.skip("colors do not depend on the viewport width")
    page = t.page
    t.a11y()
    result = page.evaluate(DESTRUCTIVE_TINT)
    assert result["failures"] == [], (f"{len(result['failures'])} destructive text failures, worst {result['worst']}:1", result["failures"][:20])
    assert result["untokened"] == [], ("destructive text is --destructive-text", result["untokened"][:10])


def check_scheme_persist(t):
    page = t.page
    root = page.locator("html")
    picker = page.locator("[data-demo='header'] select[data-theme-picker]")
    assert root.get_attribute("data-scheme") is None
    assert picker.locator("option").count() == 26 and picker.locator("optgroup").count() == 2
    assert picker.input_value() == "neutral"
    page.evaluate("() => { window.__schemeEvents = []; document.documentElement.addEventListener('theme:change', e => window.__schemeEvents.push(e.detail)) }")
    picker.select_option("tokyonight-storm")
    assert root.get_attribute("data-scheme") == "tokyonight-storm"
    assert page.evaluate("localStorage.getItem('clanker-ui-scheme')") == "tokyonight-storm"
    mode = t.theme
    assert page.evaluate("window.__schemeEvents") == [{"mode": "system", "resolved": mode, "scheme": "tokyonight-storm"}]
    storm = "rgb(36, 40, 59)" if mode == "dark" else "rgb(225, 226, 231)"
    body = "getComputedStyle(document.body).backgroundColor"
    assert page.evaluate(body) == storm
    t.section("themes")
    page.locator("#themes-accent").select_option("amber")
    page.locator("#themes-radius").select_option("radius-large")
    assert root.get_attribute("data-scheme") == "tokyonight-storm amber radius-large"
    assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--radius').trim()") == "0.875rem"
    assert page.locator("#themes-scheme").input_value() == "tokyonight-storm"
    page.reload(wait_until="load")
    assert root.get_attribute("data-scheme") == "tokyonight-storm amber radius-large"
    assert page.evaluate(body) == storm
    assert [picker.input_value(), page.locator("#themes-accent").input_value(), page.locator("#themes-radius").input_value(), page.locator("#themes-menu").input_value()] == ["tokyonight-storm", "amber", "radius-large", ""]
    assert page.locator("[data-demo='scheme-tile'][aria-pressed='true']").get_attribute("data-value") == "tokyonight-storm"
    picker.select_option("zinc")
    assert root.get_attribute("data-scheme") == "zinc amber radius-large"
    page.locator("[data-demo='scheme-tile'][data-value='nord']").click()
    assert root.get_attribute("data-scheme") == "nord amber radius-large"
    result = page.evaluate(
        """async () => {
          const { theme } = await import("/clanker-ui.js")
          theme.setScheme("nord")
          theme.set("light")
          const shown = [theme.resolved(), getComputedStyle(document.body).backgroundColor, document.querySelector("[data-demo='header'] [data-theme-set='toggle']").getAttribute("aria-pressed")]
          let bad = 0
          for (const value of ["<b>", "a  b c d e f g h i j k l m n o p q r s t u v w x y z".repeat(9), "A", "x;y"]) try { theme.setScheme(value) } catch (e) { if (e instanceof TypeError) bad++ }
          theme.setScheme(" ")
          theme.set("system")
          return [shown, bad, document.documentElement.hasAttribute("data-scheme"), localStorage.getItem("clanker-ui-scheme"), theme.scheme()]
        }"""
    )
    assert result == [["dark", "rgb(46, 52, 64)", "true"], 4, False, None, ""], result


SCHEME_FRAMES = """(() => {
  const frames = window.__schemeFrames = []
  const tick = () => {
    const body = document.body
    frames.push([body !== null, document.documentElement?.getAttribute("data-scheme") ?? null, body ? getComputedStyle(body).backgroundColor : null, document.querySelector('meta[name="theme-color"]:not([media])')?.content ?? null])
    if (frames.length < 240) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
})()"""


def check_scheme_first_frame(t):
    page = t.page
    mode = "light" if t.theme == "dark" else "dark"
    page.evaluate("m => { localStorage.setItem('clanker-ui-scheme', 'tokyonight-storm'); localStorage.setItem('clanker-ui-theme', m) }", mode)
    page.add_init_script(SCHEME_FRAMES)
    page.route(re.compile(r"/clanker-ui\.js$"), lambda route: (time.sleep(0.5), route.continue_()))
    page.reload(wait_until="load")
    page.unroute_all()
    painted = [(scheme, bg, meta) for body, scheme, bg, meta in page.evaluate("window.__schemeFrames") if body]
    bg = "rgb(36, 40, 59)" if mode == "dark" else "rgb(225, 226, 231)"
    want = ("tokyonight-storm", bg, bg)
    assert painted, "no frame was painted before load"
    assert painted[0] == want, f"the first painted frame has {painted[0]}, want {want}"
    assert set(painted) == {want}, painted


def check_theme_toggle(t):
    page = t.page
    dark = t.theme == "dark"
    stored = "localStorage.getItem('clanker-ui-theme')"
    toggle = t.section("theming").locator("[data-theme-set='toggle']")
    assert toggle.get_attribute("aria-pressed") == str(dark).lower()
    toggle.click()
    assert page.evaluate(stored) == ("light" if dark else "dark"), "the first press from system must store the opposite of the shown mode"
    assert page_is_dark(page) != dark and toggle.get_attribute("aria-pressed") == str(not dark).lower()
    toggle.click()
    assert page.evaluate(stored) == ("dark" if dark else "light")
    assert page_is_dark(page) == dark and toggle.get_attribute("aria-pressed") == str(dark).lower()
    header = page.locator("[data-demo='header'] [data-theme-set='toggle']")
    assert header.get_attribute("aria-label") == "Dark mode" and header.get_attribute("aria-pressed") == str(dark).lower()
    icon = header.locator("svg.lucide-contrast")
    assert icon.count() == 1 and icon.evaluate("s => [s.getBoundingClientRect().width, getComputedStyle(s.lastElementChild).fill !== 'none']") == [18, True]
    header.click()
    assert page.evaluate(stored) == ("light" if dark else "dark") and toggle.get_attribute("aria-pressed") == str(not dark).lower()
    page.evaluate("async () => (await import('/clanker-ui.js')).theme.set('system')")
    assert page.evaluate(stored) is None and header.get_attribute("aria-pressed") == str(dark).lower()
    t.shot("toggle")
    page.evaluate("scrollTo(0, 0)")
    t.shot("header", page)


def check_theme_key(t):
    t.docs("/demo?only=theming,input")
    page = t.page
    dark = t.theme == "dark"
    page.evaluate("document.querySelector(\"#theming [data-theme-set='toggle']\").setAttribute('aria-keyshortcuts', 'D')")
    page.evaluate("document.activeElement?.blur()")
    page.keyboard.press("d")
    assert page_is_dark(page) != dark, "D must toggle the theme"
    page.keyboard.press("Shift+D")
    assert page_is_dark(page) == dark, "Shift+D must toggle the theme"
    for combo in ["Control+d", "Alt+d", "Meta+d"]:
        page.keyboard.press(combo)
        assert page_is_dark(page) == dark, f"{combo} must not toggle the theme"
    page.keyboard.down("d")
    page.keyboard.down("d")
    page.keyboard.down("d")
    page.keyboard.up("d")
    assert page_is_dark(page) != dark, "a held D must toggle the theme once"
    page.keyboard.press("d")
    assert page_is_dark(page) == dark
    page.evaluate("() => { document.dispatchEvent(new Event('keydown', { bubbles: true })); document.body.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true })) }")
    assert page_is_dark(page) == dark, "a keydown without a key must do nothing"
    field = t.section("input").locator("[data-slot=input]").first
    field.fill("")
    field.focus()
    page.keyboard.press("d")
    assert page_is_dark(page) == dark and field.input_value() == "d", "D in a text field must type"
    editable = page.evaluate_handle("() => { const e = document.createElement('div'); e.contentEditable = 'true'; e.textContent = 'x'; document.querySelector('#input').append(e); e.focus(); return e }")
    page.keyboard.press("d")
    assert page_is_dark(page) == dark and sorted(editable.evaluate("e => e.textContent")) == ["d", "x"], "D in editable content must type"
    editable.evaluate("e => e.remove()")
    for role, item in [("menu", "menuitem"), ("menubar", "menuitem"), ("listbox", "option"), ("grid", "gridcell"), ("tree", "treeitem")]:
        page.evaluate(
            """([role, item]) => {
              const host = document.createElement("div")
              host.id = "key-host"
              host.setAttribute("role", role)
              const child = host.appendChild(document.createElement("div"))
              child.setAttribute("role", item)
              child.tabIndex = 0
              child.textContent = "Item"
              document.querySelector("#input").append(host)
              child.focus()
            }""",
            [role, item],
        )
        page.keyboard.press("d")
        page.evaluate("document.getElementById('key-host').remove()")
        assert page_is_dark(page) == dark, f"D in a {role} must not toggle the theme"
    page.evaluate("for (const e of document.querySelectorAll('[aria-keyshortcuts]')) if (e.matches(\"[data-theme-set='toggle']\")) e.removeAttribute('aria-keyshortcuts')")
    page.evaluate("document.activeElement?.blur()")
    page.keyboard.press("d")
    assert page_is_dark(page) == dark, "without aria-keyshortcuts the kit must add no key"


def check_theme_meta_color(t):
    page = t.page
    page.evaluate(
        """() => {
          if (!document.querySelector('meta[name="theme-color"]:not([media])')) document.head.append(Object.assign(document.createElement("meta"), { name: "theme-color", content: "#000000" }))
          const dark = Object.assign(document.createElement("meta"), { name: "theme-color", content: "#123456" })
          dark.media = "(prefers-color-scheme: dark)"
          document.head.append(dark)
        }"""
    )
    metas = """() => [...document.querySelectorAll('meta[name="theme-color"]')].map(m => [m.media, m.content]).concat([getComputedStyle(document.body).backgroundColor])"""
    switch = t.section("theming").locator("[data-slot='theme-switch']")
    for name in ["Dark theme", "Light theme"]:
        switch.get_by_role("button", name=name).click()
        found = page.evaluate(metas)
        body = found.pop()
        assert [content for media, content in found if not media] == [body], (name, found, body)
        assert [content for media, content in found if media] == ["#123456"], found


TRANSITIONS = """() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => r(document.getAnimations().filter(a => a instanceof CSSTransition && /color|fill|stroke|shadow/.test(a.transitionProperty) && !a.effect.target.closest?.('#demo-nav')).map(a => `${a.effect.target.localName}${a.effect.target.dataset?.slot ? "." + a.effect.target.dataset.slot : ""} ${a.transitionProperty}`)))))"""


def check_theme_no_transitions(t):
    t.docs("/demo")
    page = t.page
    switch = t.section("theming").locator("[data-slot='theme-switch']")
    t.settle()
    for name in ["Dark theme", "Light theme", "System theme"]:
        switch.get_by_role("button", name=name).evaluate("b => b.click()")
        running = page.evaluate(TRANSITIONS)
        assert running == [], f"{name}: the switch started CSS transitions: {running[:8]}"
    assert not page.evaluate("document.documentElement.hasAttribute('data-theme-switching')")
    page.evaluate("() => { window.__colorRuns = []; document.addEventListener('transitionrun', e => { if (/color|fill|stroke|shadow/.test(e.propertyName) && !e.target.closest?.('#demo-nav')) window.__colorRuns.push(`${e.target.localName} ${e.propertyName}`) }, true) }")
    other = "light" if t.theme == "dark" else "dark"
    page.emulate_media(color_scheme=other)
    if page.evaluate("matchMedia('(prefers-color-scheme: dark)').matches") != (other == "dark"):
        return
    page.wait_for_timeout(500)
    assert page_is_dark(page) == (other == "dark"), "the page must follow a system theme change in system mode"
    runs = page.evaluate("window.__colorRuns")
    assert runs == [], f"the system theme change started {len(runs)} CSS transitions: {runs[:8]}"
    page.emulate_media(color_scheme=t.theme)
    page.wait_for_timeout(500)
    assert page_is_dark(page) == (t.theme == "dark") and page.evaluate("window.__colorRuns") == []


def check_safe_dom(t):
    page = t.page
    proof = t.section("introduction").locator("#h-proof")
    assert proof.locator("code").inner_text() == EVIL
    assert proof.locator("img").count() == 0
    result = page.evaluate(
        """async evil => {
          const { h, svg } = await import("/clanker-ui.js")
          let clicked = 0
          const el = h("div", { title: evil, "data-x": 1, hidden: false, onclick: () => clicked++, style: { "--x": "1px", marginTop: "2px" } }, evil, ["a", null, false, true, 2, [h("b", null, "c")]])
          document.body.append(el)
          el.click()
          const thrown = []
          for (const [tag, attrs] of [["div", { onclick: "alert(1)" }], ["div", { style: "color: red" }], ["iframe", { srcdoc: "<b>x</b>" }], ["script", {}]]) {
            try { h(tag, attrs) } catch (e) { thrown.push(e instanceof TypeError) }
          }
          const link = h("a", { href: " java\\tscript:alert(1)" }, "x")
          const icon = svg("svg", { viewBox: "0 0 24 24" }, svg("path", { d: "M0 0" }))
          el.remove()
          return {
            text: el.textContent,
            nodes: el.childNodes.length,
            elements: el.children.length,
            title: el.getAttribute("title"),
            hidden: el.hasAttribute("hidden"),
            dataX: el.getAttribute("data-x"),
            clicked,
            style: [el.style.getPropertyValue("--x"), el.style.marginTop],
            thrown,
            href: link.hasAttribute("href"),
            ns: icon.firstChild.namespaceURI,
          }
        }""",
        EVIL,
    )
    assert result["text"] == EVIL + "a2c"
    assert result["nodes"] == 4 and result["elements"] == 1
    assert result["title"] == EVIL and result["dataX"] == "1" and not result["hidden"]
    assert result["clicked"] == 1
    assert result["style"] == ["1px", "2px"]
    assert result["thrown"] == [True, True, True, True]
    assert result["href"] is False
    assert result["ns"] == "http://www.w3.org/2000/svg"


def check_safe_dom_select(t):
    result = t.page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const seen = []
          const watch = e => seen.push(`${e.violatedDirective} on <${e.target?.localName ?? "document"}>`)
          document.addEventListener("securitypolicyviolation", watch)
          const changed = []
          const made = [h("select", { name: "a", value: "2", onchange: e => changed.push(e.target.value) }, h("option", { value: "1" }, "One"), h("option", { value: "2" }, "Two")), h("SELECT", { multiple: true, size: "3" }, h("option", null, "x")), h("select")]
          const form = h("form", null, ...made)
          document.body.append(form)
          made[0].value = "1"
          made[0].dispatchEvent(new Event("change"))
          const data = [...new FormData(form)].map(e => e.join("="))
          await new Promise(r => setTimeout(r, 100))
          form.remove()
          document.removeEventListener("securitypolicyviolation", watch)
          return { seen, changed, data, owner: made.every(s => s.ownerDocument === document && s instanceof HTMLSelectElement && s.form === form), multiple: made[1].multiple && made[1].size === 3 }
        }"""
    )
    assert result["seen"] == [], f"h() selects must not report a style-src-attr violation (WebKit bug 327212): {result['seen']}"
    assert result["changed"] == ["1"] and result["data"] == ["a=1"], result
    assert result["owner"] and result["multiple"], result


def check_trusted_types(t):
    page = t.page
    if not page.evaluate("'trustedTypes' in window"):
        t.skip("engine has no Trusted Types")
    t.expect_console(r"trusted|require-trusted-types-for|TrustedHTML")
    outcome = page.evaluate(
        """() => {
          try { document.createElement("div").innerHTML = "<b>x</b>"; return "allowed" } catch (e) { return e.name }
        }"""
    )
    assert outcome == "TypeError", outcome


def check_button(t):
    t.docs("/demo?only=button")
    page = t.page
    section = t.section("button")
    sizes = page.evaluate(
        """() => [...document.querySelectorAll("#button [data-slot='button']")].map(b => {
          const r = b.getBoundingClientRect()
          return [b.dataset.size || "default", Math.round(r.height), Math.round(r.width)]
        })"""
    )
    heights = {"default": 32, "xs": 24, "sm": 28, "lg": 36, "icon": 32, "icon-xs": 24, "icon-sm": 28, "icon-lg": 36}
    for size, height, width in sizes:
        assert height == heights[size], (size, height)
        if size.startswith("icon"):
            assert width == height, (size, width)
    first = section.locator("[data-slot='button']").first
    page.keyboard.press("Shift")
    first.focus()
    assert first.evaluate("e => e.matches(':focus-visible')"), "button did not match :focus-visible after keyboard modality"
    t.settle()
    ring = page.evaluate("() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.boxShadow] }")
    assert ring[0] == "none" and "0px 0px 0px 3px" in ring[1], ring
    t.a11y()
    ring = page.evaluate("() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.outlineWidth] }")
    assert ring == ["solid", "3px"], ring
    disabled = section.locator("button[disabled]").last
    opacity = page.evaluate("b => getComputedStyle(b).opacity", disabled.element_handle())
    assert opacity == "0.5", opacity


def check_icons(t):
    page = t.page
    t.expect_console(r'^console\.warning: clanker-ui: unknown icon "no-such-icon"')
    grid = t.section("icons").locator("#icon-grid")
    count = page.evaluate("async () => (await import('/clanker-ui.js')).iconNames.length")
    assert count >= 230, count
    assert grid.locator("[data-demo='icon-tile']").count() == count
    result = page.evaluate(
        """async () => {
          const { icon } = await import("/clanker-ui.js")
          const a = icon("x", { "data-icon": "inline-start" })
          const b = icon("loader-2")
          const warned = []
          const warn = console.warn
          console.warn = (...args) => { warned.push(String(args[0])); warn.apply(console, args) }
          let unknown
          try {
            const u = icon("no-such-icon")
            icon("no-such-icon")
            const holder = document.createElement("div")
            const missing = document.createElementNS("http://www.w3.org/2000/svg", "svg")
            missing.setAttribute("data-lucide", "no-such-icon")
            holder.append(missing)
            document.body.append(holder)
            await new Promise(r => setTimeout(r, 0))
            unknown = [u.localName, u.childElementCount, u.getAttribute("aria-hidden"), missing.childElementCount, missing.getAttribute("aria-hidden"), warned.length]
            holder.remove()
          } finally {
            console.warn = warn
          }
          const holder = document.createElement("div")
          const i = document.createElement("i")
          i.setAttribute("data-lucide", "check")
          i.setAttribute("aria-label", "Done")
          holder.append(i)
          document.body.append(holder)
          await new Promise(r => setTimeout(r, 0))
          const replaced = holder.firstElementChild
          holder.remove()
          return [a.localName, a.getAttribute("data-icon"), a.childElementCount, b.getAttribute("data-lucide"), unknown, replaced.localName, replaced.getAttribute("aria-label"), replaced.childElementCount > 0]
        }"""
    )
    assert result == ["svg", "inline-start", 2, "loader-circle", ["svg", 0, "true", 0, "true", 1], "svg", "Done", True], result


def check_icons_register(t):
    result = t.page.evaluate(
        """async () => {
          const { icon, iconNames, registerIcons } = await import("/clanker-ui.js")
          const before = iconNames.length
          const holder = document.createElement("div")
          const waiting = document.createElementNS("http://www.w3.org/2000/svg", "svg")
          waiting.setAttribute("data-lucide", "app-ship")
          holder.append(waiting)
          document.body.append(holder)
          const warn = console.warn
          console.warn = () => {}
          await new Promise(r => setTimeout(r, 0))
          console.warn = warn
          const empty = waiting.childElementCount
          const errors = []
          for (const bad of [{ "Bad Name": ["M1 1h2"] }, { x: ["M1 1h2"] }, { "alert-triangle": ["M1 1h2"] }, { "app-a": [] }, { "app-b": [["script", {}]] }, { "app-c": [["path", { d: "M1 1", onload: "x" }]] }, { "app-d": [["path", { href: "javascript:x" }]] }]) {
            try { registerIcons(bad); errors.push(false) } catch (e) { errors.push(e.constructor.name) }
          }
          registerIcons({ "app-ship": ["M12 2v2", ["circle", { cx: 12, cy: 12, r: "3" }]] })
          const made = icon("app-ship")
          const live = await import("/clanker-ui.js")
          return {
            empty,
            errors,
            filled: [waiting.childElementCount, waiting.classList.contains("lucide-app-ship")],
            made: [...made.children].map(c => c.localName + ":" + (c.getAttribute("d") ?? c.getAttribute("cx"))),
            names: [live.iconNames.length - before, live.iconNames.includes("app-ship"), Object.isFrozen(live.iconNames)],
          }
        }"""
    )
    assert result["empty"] == 0, result
    assert result["errors"] == ["TypeError", "Error", "Error", "TypeError", "TypeError", "TypeError", "TypeError"], result
    assert result["filled"] == [2, True], result
    assert result["made"] == ["path:M12 2v2", "circle:12"], result
    assert result["names"] == [1, True, True], result


def check_icons_common(t):
    found = t.page.evaluate(
        """async () => {
          const { icon, iconNames } = await import("/clanker-ui.js")
          const names = ["layout-grid", "bookmark", "star", "star-half", "receipt", "wallet", "plane", "euro", "filter", "server", "database", "activity", "wifi", "upload", "download", "file", "image", "calendar-days", "clock", "map-pin", "mail", "phone", "globe", "lock", "unlock", "shield", "bell", "heart", "share", "link", "external-link", "copy", "trash", "pencil", "plus", "minus", "refresh-cw", "log-out", "user-plus", "users", "building", "credit-card", "banknote", "chart-bar", "chart-line", "chart-pie", "trending-up", "trending-down", "alert-triangle", "info", "help-circle", "check-circle", "x-circle", "loader"]
          const host = document.createElement("div")
          document.body.append(host)
          const bad = names.filter(name => {
            const el = icon(name)
            host.append(el)
            const b = el.getBBox()
            return !(el.childElementCount > 0 && Math.max(b.width, b.height) > 4 && b.x >= -0.5 && b.y >= -0.5 && b.x + b.width <= 24.5 && b.y + b.height <= 24.5)
          })
          host.remove()
          return { bad, aliases: ["unlock", "alert-triangle", "help-circle", "check-circle", "x-circle", "filter"].map(n => [n, iconNames.includes(n), icon(n).getAttribute("data-lucide")]) }
        }"""
    )
    assert found["bad"] == [], found
    assert found["aliases"] == [["unlock", False, "lock-open"], ["alert-triangle", False, "triangle-alert"], ["help-circle", False, "circle-question-mark"], ["check-circle", False, "circle-check-big"], ["x-circle", False, "circle-x"], ["filter", False, "funnel"]], found


def check_icons_added(t):
    found = t.page.evaluate(
        """async () => {
          const { icon, iconNames } = await import("/clanker-ui.js")
          const host = document.createElement("div")
          document.body.append(host)
          const out = ["message-square", "message-circle", "camera", "skip-forward", "book-open", "graduation-cap", "hammer", "play", "pause", "film", "tv", "webhook", "container", "rss", "key-round"].map(name => {
            const el = icon(name)
            host.append(el)
            const b = el.getBBox()
            return [name, iconNames.includes(name), [...el.children].map(c => c.localName).join(" "), b.x >= 0 && b.y >= 0 && b.x + b.width <= 24 && b.y + b.height <= 24 && b.width > 8 && b.height > 8]
          })
          host.remove()
          return out
        }"""
    )
    assert found == [
        ["message-square", True, "path", True],
        ["message-circle", True, "path", True],
        ["camera", True, "path circle", True],
        ["skip-forward", True, "path path", True],
        ["book-open", True, "path path", True],
        ["graduation-cap", True, "path path path", True],
        ["hammer", True, "path path path", True],
        ["play", True, "path", True],
        ["pause", True, "rect rect", True],
        ["film", True, "rect path path path path path path path", True],
        ["tv", True, "path rect", True],
        ["webhook", True, "path path path", True],
        ["container", True, "path path path path path", True],
        ["rss", True, "path path circle", True],
        ["key-round", True, "path circle", True],
    ], found


def check_typography(t):
    page = t.page
    section = t.section("typography")
    h1 = section.locator("article h1")
    assert page.evaluate("e => getComputedStyle(e).fontSize", h1.element_handle()) == "36px"
    assert page.evaluate("e => getComputedStyle(e).fontWeight", h1.element_handle()) == "800"
    code = section.locator("article code")
    bg = page.evaluate("e => getComputedStyle(e).backgroundColor", code.element_handle())
    muted = page.evaluate("() => { const p = document.createElement('p'); p.style.background = 'var(--muted)'; document.body.append(p); const c = getComputedStyle(p).backgroundColor; p.remove(); return c }")
    assert bg == muted, (bg, muted)


def check_core_registry(t):
    result = t.page.evaluate(
        """async () => {
          const { define, h, emit, uid, ensureId } = await import("/clanker-ui.js")
          const log = []
          define("probe", {
            init(el) { log.push("init " + el.id); return () => log.push("teardown " + el.id) },
            click(e, el) { log.push("click " + el.id) },
            "probe:ping"(e, el) { log.push("ping " + e.detail.n) },
          })
          define("probe-item", { click(e, el) { log.push("item"); if (el.dataset.stop) e.stopPropagation() } })
          let duplicate = false
          try { define("probe", {}) } catch { duplicate = true }
          const a = h("div", { "data-slot": "probe", id: "probe-a" }, h("button", { "data-slot": "probe-item" }, "x"))
          document.body.append(a)
          await new Promise(r => setTimeout(r, 0))
          a.querySelector("button").click()
          a.querySelector("button").dataset.stop = "1"
          a.querySelector("button").click()
          emit(a, "probe:ping", { n: 7 })
          a.remove()
          await new Promise(r => setTimeout(r, 0))
          const id = uid("probe")
          const b = document.createElement("div")
          return { log, duplicate, id: /^probe-\\d+$/.test(id), ensured: ensureId(b) === b.id && b.id.length > 0 }
        }"""
    )
    assert result["log"] == ["init probe-a", "item", "click probe-a", "item", "ping 7", "teardown probe-a"], result["log"]
    assert result["duplicate"] and result["id"] and result["ensured"]


def check_core_popup(t):
    page = t.page
    page.evaluate(
        """async () => {
          const { h, show, hide, isOpen } = await import("/clanker-ui.js")
          const trigger = h("button", { id: "pt", type: "button", style: { position: "fixed", left: "40px", bottom: "20px" } }, "Open")
          const pop = h("div", { id: "pp", popover: "manual", "data-side": "bottom", style: { width: "180px", height: "120px", background: "white" } }, h("button", { id: "pp-a" }, "A"), h("button", { id: "pp-b" }, "B"))
          document.body.append(trigger, pop)
          window.__popup = { show, hide, isOpen, trigger, pop }
        }"""
    )
    page.locator("#pt").focus()
    page.evaluate("() => { const p = window.__popup; p.show(p.pop, { trigger: p.trigger }) }")
    state = page.evaluate(
        """() => {
          const p = window.__popup, t = p.trigger.getBoundingClientRect(), r = p.pop.getBoundingClientRect()
          return { open: p.isOpen(p.pop), state: p.pop.dataset.state, side: p.pop.dataset.side, expanded: p.trigger.getAttribute("aria-expanded"), controls: p.trigger.getAttribute("aria-controls"), above: r.bottom <= t.top, focused: document.activeElement.id, inView: r.left >= 0 && r.right <= innerWidth }
        }"""
    )
    assert state == {"open": True, "state": "open", "side": "top", "expanded": "true", "controls": "pp", "above": True, "focused": "pp-a", "inView": True}, state
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.getElementById('pp').matches(':popover-open')")
    assert page.evaluate("document.activeElement.id") == "pt"
    assert page.locator("#pt").get_attribute("aria-expanded") == "false"
    page.evaluate("() => { const p = window.__popup; p.show(p.pop, { trigger: p.trigger }) }")
    page.mouse.click(5, 5)
    page.wait_for_function("() => !document.getElementById('pp').matches(':popover-open')")
    page.evaluate("() => { const p = window.__popup; p.show(p.pop, { trigger: p.trigger }) }")
    page.locator("#pt").dispatch_event("pointerdown")
    assert page.evaluate("window.__popup.isOpen(window.__popup.pop)")


GROW = """async ([slot, side, align]) => {
  const { h, show, hide } = await import("/clanker-ui.js")
  const frame = () => new Promise(requestAnimationFrame)
  const trigger = h("button", { type: "button", "data-slot": "button", style: { position: "fixed", right: "4px", top: "200px" } }, "Open")
  const item = text => h("div", { "data-slot": "dropdown-menu-item", role: "menuitem" }, text)
  const pop = h("div", { "data-slot": slot, popover: "manual", style: { width: "max-content" } }, slot === "tooltip-content" ? "Copy" : item("Copy"))
  document.body.append(trigger, pop)
  show(pop, { trigger, side, align, focus: null, restoreFocus: false })
  for (let i = 0; i < 10; i++) await frame()
  const text = "Copied the install command to the clipboard"
  if (slot === "tooltip-content") pop.firstChild.textContent = text
  else pop.append(item(text))
  let last = ""
  for (let still = 0, i = 0; still < 10 && i < 300; i++) {
    await frame()
    const r = pop.getBoundingClientRect()
    still = `${r.left} ${r.width}` === last ? still + 1 : 0
    last = `${r.left} ${r.width}`
  }
  const r = pop.getBoundingClientRect()
  const t = trigger.getBoundingClientRect()
  await hide(pop)
  pop.remove()
  trigger.remove()
  return { end: Math.round(document.documentElement.clientWidth - r.right), gap: Math.round(side === "top" ? t.top - r.bottom : r.top - t.bottom), width: Math.round(r.width) }
}"""


def check_core_popup_grow(t):
    for slot, side, align in [("tooltip-content", "top", "center"), ("dropdown-menu-content", "bottom", "start"), ("dropdown-menu-content", "bottom", "end")]:
        placed = t.page.evaluate(GROW, [slot, side, align])
        assert placed["end"] >= 7 and placed["gap"] == 4 and placed["width"] > 200, (slot, align, placed)


def check_core_base_ui_states(t):
    page = t.page
    result = page.evaluate(
        """async () => {
          const { h, show, hide, transition } = await import("/clanker-ui.js")
          const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
          const trigger = h("button", { type: "button", style: { position: "fixed", left: "40px", top: "200px" } }, "Open")
          const arrow = h("span", { "data-slot": "tooltip-arrow" })
          const inner = h("span", { "data-slot": "tooltip-arrow", "data-side": "top" })
          const pop = h("div", { "data-slot": "tooltip-content", popover: "manual", style: { width: "120px", height: "40px" } }, "Tip", arrow, h("div", inner))
          document.body.append(trigger, pop)
          show(pop, { trigger, side: "bottom", focus: null, restoreFocus: false, expanded: false })
          const open = [trigger.hasAttribute("data-popup-open"), arrow.dataset.side, pop.dataset.side, inner.dataset.side]
          await hide(pop)
          const closed = trigger.hasAttribute("data-popup-open")
          const box = h("div", { style: { opacity: "1", transition: "opacity 120ms linear" } })
          document.body.append(box)
          transition(box, true)
          const starting = box.hasAttribute("data-starting-style")
          await frame()
          const started = box.hasAttribute("data-starting-style")
          let resolved = false
          const ending = transition(box, false).then(() => { resolved = true })
          const endingAttr = [box.hasAttribute("data-ending-style"), box.hasAttribute("data-starting-style")]
          box.style.opacity = "0"
          await ending
          const legend = h("legend", { "data-slot": "field-legend" }, "Legend")
          const label = h("legend", { "data-slot": "field-legend", "data-variant": "label" }, "Label")
          const items = ["a", "b"].map(v => h("button", { type: "button", "data-slot": "toggle-group-item", "data-value": v }, v))
          const own = h("button", { type: "button", "data-slot": "toggle-group-item", "data-value": "c", "data-size": "lg" }, "c")
          const group = h("div", { "data-slot": "toggle-group", "data-type": "single", "data-variant": "outline", "data-size": "sm", "data-spacing": "2" }, items, own)
          const plain = h("div", { "data-slot": "toggle-group", "data-type": "single" }, h("button", { type: "button", "data-slot": "toggle-group-item", "data-value": "x" }, "x"), h("button", { type: "button", "data-slot": "toggle-group-item", "data-value": "y", "data-variant": "outline", "data-size": "sm" }, "y"))
          document.body.append(legend, label, group, plain)
          await new Promise(r => setTimeout(r, 0))
          const late = h("button", { type: "button", "data-slot": "toggle-group-item", "data-value": "d" }, "d")
          group.append(late)
          await new Promise(r => setTimeout(r, 0))
          const attrs = el => [el.dataset.variant ?? null, el.dataset.size ?? null, el.dataset.spacing ?? null]
          const out = {
            open, closed, starting, started, endingAttr, resolved,
            legend: [legend.dataset.variant, label.dataset.variant],
            items: [...items, own, late].map(attrs),
            plain: [...plain.children].map(attrs).concat([plain.style.getPropertyValue("--gap"), plain.dataset.spacing, plain.dataset.orientation, getComputedStyle(plain).columnGap, getComputedStyle(plain.firstElementChild).borderTopLeftRadius]),
            gap: group.style.getPropertyValue("--gap"),
          }
          for (const el of [trigger, pop, box, legend, label, group, plain]) el.remove()
          return out
        }"""
    )
    assert result["open"] == [True, "bottom", "bottom", "top"] and result["closed"] is False, result
    assert result["starting"] is True and result["started"] is False, result
    assert result["endingAttr"] == [True, False] and result["resolved"] is True, result
    assert result["legend"] == ["legend", "label"], result
    assert result["items"] == [["outline", "sm", "2"]] * 4, result
    assert result["plain"] == [["default", "default", "2"], ["outline", "sm", "2"], "2", "2", "horizontal", "8px", "10px"] and result["gap"] == "2", result


def check_core_popover_reset(t):
    found = t.page.evaluate(
        """() => {
          const plain = document.createElement("div")
          const pop = document.createElement("div")
          pop.popover = "manual"
          const viewport = document.createElement("ol")
          viewport.popover = "manual"
          viewport.dataset.slot = "toast-viewport"
          document.body.append(plain, pop, viewport)
          pop.showPopover()
          viewport.showPopover()
          const read = e => { const s = getComputedStyle(e); return [s.borderTopColor, s.borderTopWidth, s.borderTopStyle, s.marginTop, s.paddingTop, s.backgroundColor, s.overflowX] }
          const out = { plain: read(plain), pop: read(pop), viewport: getComputedStyle(viewport).borderTopColor }
          pop.hidePopover()
          viewport.hidePopover()
          plain.remove()
          pop.remove()
          viewport.remove()
          return out
        }"""
    )
    border = found["plain"][0]
    assert found["pop"] == [border, "0px", "solid", "0px", "0px", "rgba(0, 0, 0, 0)", "visible"], found
    assert found["viewport"] == border, found


def check_forced_colors_item_focus(t):
    t.docs("/demo?only=dropdown-menu")
    page = t.page
    t.a11y()
    page.emulate_media(forced_colors="active")
    if not page.evaluate("matchMedia('(forced-colors: active)').matches"):
        t.skip("engine has no forced-colors emulation")
    t.section("dropdown-menu")
    page.keyboard.press("Shift")
    page.locator("#dropdown-menu [data-slot=dropdown-menu-trigger], #dropdown-menu [data-dropdown-menu-trigger]").first.focus()
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowDown")
    found = page.evaluate("() => { const a = getComputedStyle(document.activeElement), n = getComputedStyle(document.activeElement.nextElementSibling); return [document.activeElement.dataset.slot, a.outlineStyle, a.outlineColor !== n.outlineColor] }")
    assert found == ["dropdown-menu-item", "solid", True], ("a focused menu item keeps the forced-colors outline", found)


def check_core_button_tabindex(t):
    t.docs("/demo?only=accordion,carousel,dialog,sheet")
    page = t.page
    found = page.evaluate("""async () => {
      const { h, toast } = await import("/clanker-ui.js")
      const host = h("div", { id: "tabindex-host" },
        h("div", { "data-slot": "collapsible" }, h("button", { "data-slot": "collapsible-trigger" }, "More"), h("div", { "data-slot": "collapsible-content" }, "Text")),
        h("div", { "data-slot": "tooltip" }, h("button", { "data-slot": "tooltip-trigger" }, "Tip"), h("div", { "data-slot": "tooltip-content" }, "Tip text")),
        h("div", { "data-slot": "hover-card" }, h("button", { "data-slot": "hover-card-trigger" }, "Card"), h("div", { "data-slot": "hover-card-content" }, "Card text")))
      document.body.append(host)
      toast("Saved", { duration: Infinity })
      await new Promise(r => setTimeout(r, 50))
      const q = s => document.querySelector(s)?.getAttribute("tabindex")
      const out = {}
      for (const s of ["#accordion-demo [data-slot=accordion-trigger]", "#carousel-demo [data-slot=carousel-next]", "#dialog-demo [data-slot=dialog-close]", "#sheet-demo [data-slot=sheet-close]", "[data-slot=toast-close]", "#tabindex-host [data-slot=collapsible-trigger]", "#tabindex-host [data-slot=tooltip-trigger]", "#tabindex-host [data-slot=hover-card-trigger]"]) out[s] = q(s)
      toast.dismiss()
      host.remove()
      return out
    }""")
    assert set(found.values()) == {"0"}, found
    t.section("accordion")
    triggers = page.locator("#accordion-demo [data-slot=accordion-trigger]")
    triggers.nth(1).click()
    assert triggers.nth(1).evaluate("e => e === document.activeElement"), "a click focuses a kit trigger in every engine, as Base UI sets tabindex=0"
    page.evaluate("() => document.activeElement.blur()")
    triggers.nth(1).focus()
    page.keyboard.press("Shift+Tab")
    assert triggers.nth(0).evaluate("e => e === document.activeElement"), "a kit trigger is a Tab stop in every engine"


def check_toast_in_modal_layout(t):
    t.docs("/demo?only=dialog")
    page = t.page
    t.section("dialog")
    page.locator("#dialog-demo [data-dialog-trigger]").evaluate("b => b.click()")
    page.wait_for_function("() => document.querySelector('#dialog-demo dialog').open")
    page.evaluate("""async () => {
      const { toast } = await import("/clanker-ui.js")
      toast("Saved", { duration: Infinity })
    }""")
    page.wait_for_timeout(400)
    t.settle(3000)
    found = page.evaluate("""() => {
      const dialog = document.querySelector('#dialog-demo dialog')
      const toaster = document.querySelector('[data-slot=toast-portal], [data-slot=sonner]')
      const inside = toaster.parentElement === dialog
      const shown = dialog.getBoundingClientRect().height
      toaster.hidden = true
      const bare = dialog.getBoundingClientRect().height
      toaster.hidden = false
      return { inside, shown, bare }
    }""")
    page.evaluate("async () => (await import('/clanker-ui.js')).toast.dismiss()")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#dialog-demo dialog').open")
    t.settle(3000)
    assert found["inside"], "the toaster moves into the open modal dialog"
    assert abs(found["shown"] - found["bare"]) < 0.5, ("the toaster in a modal dialog adds no grid row", found)


SHIMMER = """() => {
  const s = document.body.appendChild(document.createElement("span"))
  s.className = "shimmer"
  s.textContent = "Thinking"
  s.style.setProperty("--shimmer-color", "oklch(from currentColor zz)")
  const cs = getComputedStyle(s)
  const out = [cs.webkitTextFillColor, cs.color]
  s.remove()
  return out
}"""


def check_shimmer_fallback(t):
    page = t.page
    page.emulate_media(reduced_motion="no-preference")
    fill, color = page.evaluate(SHIMMER)
    assert fill == "rgba(0, 0, 0, 0)", ("exact shadcn: the text is transparent", fill)
    t.a11y()
    fill, color = page.evaluate(SHIMMER)
    assert fill == color and fill != "rgba(0, 0, 0, 0)", ("the a11y layer keeps the text visible", fill, color)


def check_shimmer_modifiers(t):
    page = t.page
    page.emulate_media(reduced_motion="no-preference")
    got = page.evaluate("""() => ["shimmer-once", "shimmer-reverse"].map(m => {
      const s = document.body.appendChild(document.createElement("span"))
      s.className = "shimmer " + m
      const cs = getComputedStyle(s)
      const out = [cs.animationName, cs.animationIterationCount, cs.animationDirection]
      s.remove()
      return out
    })""")
    assert got == [["tw-shimmer", "1", "reverse" if t.rtl else "normal"], ["tw-shimmer", "infinite", "reverse"]], got


GROUP_WRAPPERS = """async () => {
  const { h } = await import("/clanker-ui.js")
  const btn = (text, extra) => h("button", { type: "button", "data-slot": "button", "data-variant": "outline", ...extra }, text)
  const make = orientation => h("div", { "data-slot": "button-group", role: "group", "data-orientation": orientation },
    btn("A"),
    h("div", { "data-slot": "dropdown-menu" }, btn("B", { "data-dropdown-menu-trigger": "" }), h("div", { "data-slot": "dropdown-menu-content", popover: "manual" }, h("div", { "data-slot": "dropdown-menu-item", role: "menuitem" }, "One"))),
    h("div", { "data-slot": "popover" }, btn("C", { "data-popover-trigger": "" }), h("div", { "data-slot": "popover-content", popover: "manual" }, "Hi")))
  const host = h("div", make("horizontal"), make("vertical"))
  document.body.append(host)
  await new Promise(r => requestAnimationFrame(r))
  const read = g => [...g.querySelectorAll('[data-slot="button"]')].map(b => { const s = getComputedStyle(b); return [s.borderStartStartRadius, s.borderStartEndRadius, s.borderEndStartRadius, s.borderEndEndRadius, s.borderInlineStartWidth, s.borderTopWidth] })
  const out = { horizontal: read(host.children[0]), vertical: read(host.children[1]), radius: getComputedStyle(host.querySelector('[data-slot="button"]')).borderStartStartRadius }
  host.remove()
  return out
}"""


def check_button_group_popup_roots(t):
    found = t.page.evaluate(GROUP_WRAPPERS)
    r = found["radius"]
    assert r != "0px", found
    assert found["horizontal"] == [[r, "0px", r, "0px", "1px", "1px"], ["0px", "0px", "0px", "0px", "0px", "1px"], ["0px", r, "0px", r, "0px", "1px"]], found["horizontal"]
    assert [v[5] for v in found["vertical"]] == ["1px", "0px", "0px"], found["vertical"]


def check_core_modal(t):
    page = t.page
    page.evaluate(
        """async () => {
          const { h, show } = await import("/clanker-ui.js")
          const opener = h("button", { id: "mo" }, "Open")
          const dialog = h("dialog", { id: "md" }, h("input", { id: "md-a" }), h("button", { id: "md-b" }, "B"), h("button", { id: "md-c" }, "C"))
          document.body.append(opener, dialog)
          opener.addEventListener("click", () => show(dialog, { trigger: opener, modal: true }))
        }"""
    )
    page.locator("#mo").focus()
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.id") == "md-a"
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") == "hidden"
    page.keyboard.press("Shift+Tab")
    assert page.evaluate("document.activeElement.id") == "md-c"
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "md-a"
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.getElementById('md').open")
    assert page.evaluate("document.activeElement.id") == "mo"
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") != "hidden"
    assert page.locator("#md").get_attribute("data-state") == "closed"


def check_core_rove(t):
    page = t.page
    page.evaluate(
        """async () => {
          const { h, rove, setRoving } = await import("/clanker-ui.js")
          const items = ["Apple", "Banana", "Blueberry", "Cherry"].map(n => h("button", { "data-item": "", disabled: n === "Banana" }, n))
          const list = h("div", { id: "rl" }, items)
          document.body.append(list)
          setRoving(items)
          list.addEventListener("keydown", e => rove(e, items))
          items[0].focus()
        }"""
    )
    focused = lambda: page.evaluate("document.activeElement.textContent")
    page.keyboard.press("ArrowDown")
    assert focused() == "Blueberry"
    page.keyboard.press("End")
    assert focused() == "Cherry"
    page.keyboard.press("ArrowDown")
    assert focused() == "Apple"
    page.keyboard.press("c")
    assert focused() == "Cherry"
    page.keyboard.press("Home")
    assert focused() == "Apple"
    tabindexes = page.evaluate("() => [...document.querySelectorAll('#rl button')].map(b => b.tabIndex)")
    assert tabindexes == [0, -1, -1, -1], tabindexes


def check_strings(t):
    result = t.page.evaluate(
        """async () => {
          const { h, strings, stringFor, toast } = await import("/clanker-ui.js")
          const tick = () => new Promise(r => setTimeout(r, 0))
          const closeText = async attrs => {
            const d = h("dialog", { "data-slot": "dialog-content", ...attrs }, h("h2", { "data-slot": "dialog-title" }, "T"))
            document.body.append(d)
            await tick()
            const text = d.querySelector('[data-slot="dialog-close"]').textContent
            d.remove()
            return text
          }
          const out = { default: await closeText({}) }
          const saved = strings.close
          strings.close = "Zapri"
          out.object = await closeText({})
          strings.close = saved
          document.documentElement.setAttribute("data-string-close", "Schliessen")
          out.page = await closeText({})
          out.element = await closeText({ "data-string-close": "Fermer" })
          document.documentElement.removeAttribute("data-string-close")
          out.template = stringFor(null, "remove", { label: "Apple" })
          strings.remove = ({ label }) => `Odstrani ${label}`
          out.fn = stringFor(null, "remove", { label: "Apple" })
          strings.remove = "Remove {label}"
          out.missing = stringFor(null, "slideOf", { index: 1 })
          try { stringFor(null, "nope"); out.unknown = false } catch { out.unknown = true }
          const portal = document.querySelector('[data-slot="toast-portal"]')
          out.sonner = portal.querySelector('[data-slot="toast-viewport"]').getAttribute("aria-label")
          portal.setAttribute("data-string-close-toast", "Zapri obvestilo")
          const id = toast("Saved")
          out.toast = document.querySelector('[data-slot="toast-close"]').getAttribute("aria-label")
          toast.dismiss(id)
          portal.removeAttribute("data-string-close-toast")
          return out
        }"""
    )
    assert result == {
        "default": "Close",
        "object": "Zapri",
        "page": "Schliessen",
        "element": "Fermer",
        "template": "Remove Apple",
        "fn": "Odstrani Apple",
        "missing": "1 of {count}",
        "unknown": True,
        "sonner": "Notifications",
        "toast": "Zapri obvestilo",
    }, result


def check_safe_dom_filters(t):
    result = t.page.evaluate(
        """async () => {
          const { h, svg } = await import("/clanker-ui.js")
          const bad = [
            h("a", { href: "JaVaScRiPt:alert(1)" }),
            h("a", { href: "vbscript:msgbox(1)" }),
            h("img", { src: " javascript:alert(1)" }),
            h("iframe", { src: "java\\nscript:alert(1)" }),
            h("form", { action: "javascript:alert(1)" }),
            h("button", { formaction: "\\u0001javascript:alert(1)" }),
            h("video", { poster: "javascript:alert(1)" }),
            svg("a", { href: "javascript:alert(1)" }),
            svg("a", { "xlink:href": "javascript:alert(1)" }),
          ].map(el => el.attributes.length)
          const good = [h("a", { href: "/docs" }).getAttribute("href"), svg("a", { "xlink:href": "#x" }).getAttribute("xlink:href"), h("img", { src: "data:image/png;base64,AA==" }).getAttribute("src")]
          const tags = ["script", "SCRIPT", "object", "embed", "base", "style", "link", "meta", "frame", "frameset"].map(tag => { try { h(tag); return false } catch (e) { return e instanceof TypeError } })
          const animations = ["set", "animate", "animateMotion", "animateTransform", "script", "style"].map(tag => { try { svg(tag, { attributeName: "href", to: "javascript:alert(1)" }); return false } catch (e) { return e instanceof TypeError } })
          return { bad, good, tags, animations }
        }"""
    )
    assert result["bad"] == [0] * 9, result["bad"]
    assert result["good"] == ["/docs", "#x", "data:image/png;base64,AA=="], result["good"]
    assert all(result["tags"]), result["tags"]
    assert all(result["animations"]), result["animations"]


def check_core_layers(t):
    page = t.page
    page.evaluate(
        """async () => {
          const ui = await import("/clanker-ui.js")
          const { h } = ui
          const box = { width: "160px", height: "60px", background: "white" }
          const t1 = h("button", { id: "ly-t1", type: "button", style: { position: "fixed", left: "20px", top: "20px" } }, "One")
          const p1 = h("div", { id: "ly-p1", popover: "manual", style: box }, h("button", { id: "ly-t2", type: "button" }, "Two"))
          const p2 = h("div", { id: "ly-p2", popover: "manual", style: box }, h("button", { id: "ly-in2", type: "button" }, "In"))
          document.body.append(t1, p1, p2)
          window.__ly = { ui, t1, p1, p2 }
        }"""
    )
    open_ = lambda i: page.evaluate(f"() => window.__ly.ui.isOpen(document.getElementById('{i}'))")
    page.evaluate("() => { const l = window.__ly; l.ui.show(l.p1, { trigger: l.t1 }); l.ui.show(l.p2, { trigger: document.getElementById('ly-t2') }) }")
    assert open_("ly-p1") and open_("ly-p2")
    page.keyboard.press("Escape")
    assert not open_("ly-p2") and open_("ly-p1"), "Escape must close only the top layer"
    page.keyboard.press("Escape")
    assert not open_("ly-p1")
    page.wait_for_function("() => !document.getElementById('ly-p1').matches(':popover-open')")

    result = page.evaluate(
        """async () => {
          const l = window.__ly
          const tick = () => new Promise(r => setTimeout(r, 0))
          const p3 = l.ui.h("dialog", { id: "ly-p3" }, l.ui.h("button", { type: "button" }, "x"))
          document.body.append(p3)
          l.ui.show(p3, { modal: true })
          const locked = getComputedStyle(document.documentElement).overflow
          p3.remove()
          await tick()
          await tick()
          const esc = new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true })
          document.body.dispatchEvent(esc)
          return { locked, open: l.ui.isOpen(p3), escapeTaken: esc.defaultPrevented, overflow: getComputedStyle(document.documentElement).overflow }
        }"""
    )
    assert result == {"locked": "hidden", "open": False, "escapeTaken": False, "overflow": "visible"}, result

    log = page.evaluate(
        """async () => {
          const { define, h } = window.__ly.ui
          const tick = () => new Promise(r => setTimeout(r, 0))
          const log = []
          define("probe-reinit", { init(el) { log.push("init"); return () => log.push("teardown") } })
          const el = h("div", { "data-slot": "probe-reinit" })
          const host = h("div", null, el)
          document.body.append(host)
          await tick()
          el.remove()
          await tick()
          host.append(el)
          await tick()
          host.remove()
          await tick()
          return log
        }"""
    )
    assert log == ["init", "teardown", "init", "teardown"], log

    page.locator("#ly-t1").focus()
    page.evaluate(
        """() => {
          const l = window.__ly
          l.ui.show(l.p1, { trigger: l.t1 })
          l.ui.hide(l.p1, { restoreFocus: false })
          l.ui.show(l.p2, { trigger: document.getElementById("ly-t2") })
        }"""
    )
    page.wait_for_function("() => !document.getElementById('ly-p1').matches(':popover-open')")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.getElementById('ly-p2').matches(':popover-open')")
    assert page.evaluate("document.activeElement.id") == "ly-t1", "focus must return to the trigger of the popup that was closing"


CONTRAST = """([fg, bg]) => {
  const canvas = document.createElement("canvas")
  canvas.width = canvas.height = 1
  const ctx = canvas.getContext("2d", { willReadFrequently: true })
  const rgb = color => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = bg; ctx.fillRect(0, 0, 1, 1); ctx.fillStyle = color; ctx.fillRect(0, 0, 1, 1); return [...ctx.getImageData(0, 0, 1, 1).data].slice(0, 3) }
  const lum = c => { const [r, g, b] = c.map(v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4 }); return 0.2126 * r + 0.7152 * g + 0.0722 * b }
  const a = lum(rgb(fg)), b = lum(rgb(bg))
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
}"""


def resolved(page, prop, value, el="body"):
    return page.evaluate(
        """([prop, value, el]) => {
          const p = document.createElement("span")
          p.style.setProperty(prop, value)
          document.querySelector(el).append(p)
          const c = getComputedStyle(p).getPropertyValue(prop)
          p.remove()
          return c
        }""",
        [prop, value, el],
    )


def check_focus_contrast(t):
    t.docs("/demo?only=input")
    page = t.page
    t.a11y()
    bg = resolved(page, "color", "var(--background)")
    field = t.section("input").locator("[data-slot=input]").first
    page.keyboard.press("Shift")
    field.focus()
    t.settle()
    ring = field.evaluate("e => getComputedStyle(e).outlineColor")
    ratios = {
        "focus ring": page.evaluate(CONTRAST, [ring, bg]),
        "invalid focus ring": page.evaluate(CONTRAST, [resolved(page, "color", "var(--focus-ring-invalid)"), bg]),
        "muted-foreground on muted": page.evaluate(CONTRAST, [resolved(page, "color", "var(--muted-foreground)"), resolved(page, "color", "var(--muted)")]),
    }
    assert ratios["focus ring"] >= 3 and ratios["invalid focus ring"] >= 3, ratios
    assert ratios["muted-foreground on muted"] >= 4.5, ratios
    rich = page.evaluate(
        """async () => {
          const { toast } = await import("/clanker-ui.js")
          for (const type of ["success", "info", "warning", "error"]) toast[type](type, { description: "details", duration: Infinity })
          await new Promise(r => setTimeout(r, 50))
          const out = [...document.querySelectorAll('[data-slot="toast"]')].flatMap(e => [e.querySelector('[data-slot="toast-title"]'), e.querySelector('[data-slot="toast-description"]')].map(p => [e.dataset.type, getComputedStyle(p).color, getComputedStyle(e).backgroundColor]))
          toast.dismiss()
          return out
        }"""
    )
    for kind, fg, back in rich:
        r = page.evaluate(CONTRAST, [fg, back])
        assert r >= 4.5, (kind, fg, back, r)


INPUT_EDGES = """selectors => {
  const canvas = document.createElement("canvas")
  canvas.width = canvas.height = 1
  const ctx = canvas.getContext("2d", { willReadFrequently: true })
  const paint = colors => { ctx.clearRect(0, 0, 1, 1); for (const c of ["#fff", ...colors]) { ctx.fillStyle = c; ctx.fillRect(0, 0, 1, 1) } return [...ctx.getImageData(0, 0, 1, 1).data].slice(0, 3) }
  const lum = c => { const [r, g, b] = c.map(v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4 }); return 0.2126 * r + 0.7152 * g + 0.0722 * b }
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return +((Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05)).toFixed(2) }
  const out = {}
  for (const sel of selectors) {
    const e = [...document.querySelectorAll(sel)].find(el => el.checkVisibility())
    if (!e) continue
    const s = getComputedStyle(e)
    const layers = []
    for (let n = e.parentElement; n; n = n.parentElement) layers.unshift(getComputedStyle(n).backgroundColor)
    out[sel] = ratio(paint([...layers, e.dataset.slot === "switch" ? s.backgroundColor : s.borderTopColor]), paint(layers))
  }
  return out
}"""


EXACT_CONTRAST = r"""([fg, bg]) => {
  const rgba = v => {
    const p = document.body.appendChild(document.createElement("span"))
    p.style.color = `color-mix(in srgb, ${v} 100%, transparent)`
    const m = getComputedStyle(p).color.match(/color\(srgb ([-\d.e]+) ([-\d.e]+) ([-\d.e]+)(?: \/ ([\d.]+))?\)/)
    p.remove()
    return [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]].map(x => Math.min(1, Math.max(0, x)))
  }
  const f = rgba(fg), b = rgba(bg)
  const lum = c => { const [x, y, z] = c.map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); return 0.2126 * x + 0.7152 * y + 0.0722 * z }
  const p = lum([0, 1, 2].map(i => f[3] * f[i] + (1 - f[3]) * b[i])), q = lum(b.slice(0, 3))
  return +((Math.max(p, q) + 0.05) / (Math.min(p, q) + 0.05)).toFixed(3)
}"""


def check_input_contrast(t):
    t.docs("/demo?only=input,textarea,input-group,checkbox,radio-group,switch,select,native-select,input-otp,combobox,calendar,questionnaire,sidebar")
    page = t.page
    t.settle()
    t.a11y()
    tokens = {bg: page.evaluate(EXACT_CONTRAST, ["var(--input-edge)", f"var({bg})"]) for bg in ["--background", "--card", "--popover", "--sidebar"]}
    assert all(r >= 3.05 for r in tokens.values()), tokens
    fields = [
        "#input [data-slot=input]",
        "#textarea [data-slot=textarea]",
        "#input-group [data-slot=input-group]",
        "#checkbox [data-slot=checkbox]:not(:checked)",
        "#radio-group [data-slot=radio-group-item]:not(:checked)",
        "#switch-airplane",
        "#select [data-slot=select-trigger]",
        "#native-select [data-slot=native-select]",
        "#input-otp [data-slot=input-otp-slot]",
        "#combobox [data-slot=combobox-chips]",
        "#calendar-demo [data-slot=calendar-dropdown-root]",
        "#questionnaire-demo [data-slot=questionnaire-choice-indicator]",
    ]
    if not t.mobile:
        fields.append("[data-slot=sidebar-input]")
    edges = page.evaluate(INPUT_EDGES, fields)
    assert sorted(edges) == sorted(fields) and all(r >= 3 for r in edges.values()), edges
    t.section("input")


UPSTREAM_INPUT = "var(--input)"
DECORATIVE = """([parts, upstream]) => parts.map(([sel, prop, expr]) => {
  const e = document.querySelector(sel)
  const p = document.body.appendChild(document.createElement("span"))
  p.style.setProperty(prop, expr.replaceAll("UP", upstream))
  const want = getComputedStyle(p).getPropertyValue(prop)
  p.remove()
  return [sel, prop, e ? getComputedStyle(e).getPropertyValue(prop) : null, want]
})"""


def check_input_decorative(t):
    t.docs("/demo?only=button,button-group,combobox,input,toggle,tabs,code-block,message-scroller,questionnaire")
    page = t.page
    t.settle()
    mix = lambda n: f"color-mix(in oklab, UP {n}%, transparent)"
    parts = [
        ("#button-group [data-slot=button-group-separator]", "background-color", "UP"),
        ("#toggle [data-slot=toggle][data-variant=outline]", "border-top-color", "UP"),
        ("#code-block [data-slot=code-block][data-variant=default]", "border-top-color", "UP"),
        ("#questionnaire-demo [data-slot=questionnaire-choice]", "border-top-color", "UP"),
        ("#questionnaire-demo [data-slot=questionnaire-choice-shortcut]", "border-top-color", "UP"),
        ("#button [data-slot=button][data-variant=outline]", "border-top-color", "light-dark(var(--border), UP)"),
        ("#tabs [data-slot=tabs-list]:not([data-variant]) > [data-slot=tabs-trigger][data-state=active]", "border-top-color", "light-dark(transparent, UP)"),
        ("#input [data-slot=input]", "background-color", f"light-dark(transparent, {mix(30)})"),
        ("#questionnaire-demo [data-slot=questionnaire-choice]", "background-color", f"light-dark(transparent, {mix(20)})"),
        ("#combobox-popup [data-slot=combobox-content] > [data-slot=input-group]", "border-top-color", mix(30)),
        ("#combobox-popup [data-slot=combobox-content] > [data-slot=input-group]", "background-color", mix(30)),
        ("#message-scroller-composer", "background-color", f"light-dark(var(--background), {mix(30)})"),
    ]
    t.a11y()
    found = page.evaluate(DECORATIVE, [[list(x) for x in parts], UPSTREAM_INPUT])
    wrong = [f for f in found if f[2] != f[3]]
    assert not wrong, wrong
    t.section("toggle")


def check_reduced_motion(t):
    page = t.page
    page.emulate_media(reduced_motion="reduce")
    result = page.evaluate(
        """async () => {
          const { h, show, hide } = await import("/clanker-ui.js")
          const spinner = h("div", { "data-slot": "spinner" })
          const box = h("div", { "data-slot": "dialog-content" })
          const fade = h("div", { style: { transition: "opacity 400ms linear", opacity: "1" } })
          document.body.append(spinner, box, fade)
          fade.getBoundingClientRect()
          fade.style.opacity = "0"
          box.dataset.state = "open"
          await new Promise(r => requestAnimationFrame(r))
          const names = []
          const walk = rules => { for (const r of rules) { if (r instanceof CSSKeyframesRule) names.push(r.name); if (r.cssRules) walk(r.cssRules) } }
          for (const sheet of document.styleSheets) if (sheet.href?.endsWith("/clanker-ui.css")) walk(sheet.cssRules)
          const fades = ["attachment-group", "code-block-content", "message-scroller-viewport"].map(slot => {
            const e = h("div", { "data-slot": slot })
            document.body.append(e)
            const name = getComputedStyle(e).animationName
            e.remove()
            return name
          })
          const out = { spinner: spinner.getAnimations().length, dialog: box.getAnimations().length, override: fade.getAnimations().length, names, fades, timelines: CSS.supports("animation-timeline: scroll()") }
          spinner.remove(); box.remove(); fade.remove()
          return out
        }"""
    )
    assert result["spinner"] == 1, result
    assert result["dialog"] == 0, result
    assert result["override"] == 1, "app styles must be able to turn motion back on"
    if result["timelines"]:
        assert all(n.startswith("scroll-fade-reveal") for n in result["fades"]), ("scroll fades follow the scroll position, not time, so they stay", result["fades"])
    shadcn = {"spin", "pulse", "enter", "exit", "accordion-down", "accordion-up", "caret-blink", "tw-shimmer", "scroll-fade-reveal-t", "scroll-fade-reveal-b", "scroll-fade-reveal-s", "scroll-fade-reveal-e"}
    assert {"spin", "pulse", "enter", "exit", "accordion-down", "accordion-up"} <= set(result["names"]), f"expected the shadcn and tw-animate keyframes, got {result['names']}"
    assert not [n for n in result["names"] if n not in shadcn and not n.startswith("clanker-")], f"kit keyframes without the clanker- prefix: {result['names']}"


def check_safari_fallbacks(t):
    page = t.page
    css = page.request.get(t.base_url + "/clanker-ui.css").text()
    blocks = re.findall(r"\{[^{}]*\}", css)
    missing = [b[:80] for b in blocks if re.search(r"(?<!-webkit-)user-select:\s*none", b) and not re.search(r"-webkit-user-select:\s*none", b)]
    assert not missing, f"user-select without -webkit-user-select: {missing}"
    assert re.search(r"@supports not \(field-sizing:\s*content\)\s*\{\s*textarea\[data-slot=\"?input-group-control\"?\]\s*\{\s*resize:\s*vertical;?\s*\}", css), "textarea field-sizing fallback is missing"
    result = page.evaluate(
        """async () => {
          const { lockScroll } = await import("/clanker-ui.js")
          const root = document.documentElement
          const width = Object.getOwnPropertyDescriptor(window, "innerWidth")
          Object.defineProperty(window, "innerWidth", { configurable: true, get: () => root.clientWidth + 15 })
          const supports = CSS.supports
          CSS.supports = (p, v) => (p === "scrollbar-gutter" ? false : supports.call(CSS, p, v))
          const release = lockScroll()
          const locked = [root.style.scrollbarGutter, root.style.paddingInlineEnd]
          release()
          CSS.supports = supports
          if (width) Object.defineProperty(window, "innerWidth", width)
          else delete window.innerWidth
          return { gap: 15, locked, after: root.style.paddingInlineEnd }
        }"""
    )
    assert result["gap"] > 0, result
    assert result["locked"] == ["", f"{result['gap']}px"] and result["after"] == "", result


def check_runner(t):
    clock = t.page.evaluate(
        """async () => {
          const start = Date.now()
          await new Promise(r => setTimeout(r, 30))
          const d = new Date()
          return { day: [d.getFullYear(), d.getMonth() + 1, d.getDate()], elapsed: Date.now() - start, fixed: new Date(2024, 0, 2).getDate(), instance: d instanceof Date }
        }"""
    )
    assert clock["day"] == [2026, 10, 28] and clock["elapsed"] >= 20, f"pages see 2026-10-28 and time keeps running: {clock}"
    assert clock["fixed"] == 2 and clock["instance"], f"explicit dates stay real Date objects: {clock}"
    caught = t.page.evaluate("""() => {
      dispatchEvent(new ErrorEvent("error", { message: "runner probe" }))
      return window.__clankerWatch.errors.splice(0)
    }""")
    assert caught == ["runner probe"], f"window error events must be recorded: {caught}"


FILL_COLORS = """() => {
  const ctx = document.createElement("canvas").getContext("2d", { willReadFrequently: true })
  const rgb = name => {
    const p = document.createElement("p")
    p.style.color = `var(--${name})`
    document.body.append(p)
    const c = getComputedStyle(p).color
    p.remove()
    ctx.clearRect(0, 0, 1, 1)
    ctx.fillStyle = c
    ctx.fillRect(0, 0, 1, 1)
    return [...ctx.getImageData(0, 0, 1, 1).data].slice(0, 3)
  }
  return Object.fromEntries(["success-fill", "warning-fill", "error-fill", "info-fill", "neutral-fill", "card"].map(n => [n, rgb(n)]))
}"""


def fill_luminance(rgb):
    c = [v / 255 for v in rgb]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def fill_hue(rgb):
    r, g, b = (v / 255 for v in rgb)
    hi, lo = max(r, g, b), min(r, g, b)
    if hi == lo:
        return None
    d = hi - lo
    h = (g - b) / d % 6 if hi == r else (b - r) / d + 2 if hi == g else (r - g) / d + 4
    return h * 60


def check_status_fill_tokens(t):
    colors = t.page.evaluate(FILL_COLORS)
    card = fill_luminance(colors["card"])
    bands = {"success-fill": (120, 160), "warning-fill": (28, 48), "error-fill": (350, 375), "info-fill": (200, 225)}
    for name, (lo, hi) in bands.items():
        lum = fill_luminance(colors[name])
        ratio = (max(lum, card) + 0.05) / (min(lum, card) + 0.05)
        assert ratio >= 3, (name, colors[name], round(ratio, 2))
        hue = fill_hue(colors[name])
        hue = hue + 360 if hue is not None and hue < lo - 180 else hue
        assert hue is not None and lo <= hue <= hi, (name, colors[name], hue, "a status fill keeps its hue in light and dark")
    assert t.page.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--neutral-fill').trim()"), "--neutral-fill is defined"
    lum = fill_luminance(colors["neutral-fill"])
    ratio = (max(lum, card) + 0.05) / (min(lum, card) + 0.05)
    assert ratio >= 3, ("neutral-fill", colors["neutral-fill"], round(ratio, 2))
    assert max(colors["neutral-fill"]) - min(colors["neutral-fill"]) <= 16, ("neutral-fill is gray", colors["neutral-fill"])


def check_page_split_hidden(t):
    result = t.page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const main = h("main", { "data-slot": "page", "data-layout": "split" },
            h("div", {}, h("a", { "data-slot": "brand", href: "#" }, "Brand"), h("div", { id: "split-form" }, "Form"), h("div", { id: "split-sent", hidden: true }, "Check your email")),
            h("div", { "data-slot": "page-aside" }))
          document.body.prepend(main)
          const out = ["split-form", "split-sent"].map(id => getComputedStyle(document.getElementById(id)).display)
          main.remove()
          return out
        }"""
    )
    assert result == ["flex", "none"], result


def check_item_media_cover(t):
    result = t.page.evaluate(
        """async () => {
          const { h, svg } = await import("/clanker-ui.js")
          const out = []
          for (const size of [null, "sm", "xs"]) {
            for (const variant of [null, "image"]) {
              const item = h("div", { "data-slot": "item", "data-variant": "outline", "data-size": size },
                h("div", { "data-slot": "item-media", "data-variant": variant },
                  h("div", { "data-slot": "cover", "data-tone": "2" }, svg("svg", { viewBox: "0 0 40 60", "aria-hidden": "true" }, svg("circle", { cx: "20", cy: "30", r: "12", fill: "currentColor" })), h("span", {}, "Piranesi"))),
                h("div", { "data-slot": "item-content" }, h("div", { "data-slot": "item-title" }, "Piranesi")))
              document.body.prepend(item)
              const r = item.querySelector('[data-slot="cover"]').getBoundingClientRect()
              const text = item.querySelector('[data-slot="cover"] > span').getBoundingClientRect()
              out.push([size, variant, Math.round(r.width), Math.round(r.height), text.width > 0])
              item.remove()
            }
          }
          return out
        }"""
    )
    want = {None: 40, "sm": 32, "xs": 24}
    for size, variant, w, hgt, text in result:
        assert w == want[size], (size, variant, w, hgt)
        assert hgt == (w if variant == "image" else round(w * 1.5)), (size, variant, w, hgt)
        assert not text, (size, variant, "cover text is hidden at media size")


def check_section_cards_value_wrap(t):
    result = t.page.evaluate(
        """async () => {
          const { h, icon } = await import("/clanker-ui.js")
          const card = value => h("div", { "data-slot": "card" },
            h("div", { "data-slot": "card-header" },
              h("div", { "data-slot": "card-description" }, "Outstanding"),
              h("div", { "data-slot": "card-title" }, value),
              h("div", { "data-slot": "card-action" }, h("span", { "data-slot": "badge", "data-variant": "outline" }, icon("trending-up"), "+12.5%"))),
            h("div", { "data-slot": "card-footer" }, h("div", {}, "Up this month"), h("div", { "data-slot": "card-description" }, "Last 6 months")))
          const out = []
          for (const width of [980, 600, 358]) {
            const host = h("div", { style: { width: width + "px" } }, h("div", { "data-slot": "section-cards" }, ["€38,550.00", "€1,250.00", "1,234", "4.5%"].map(card)))
            document.body.prepend(host)
            await new Promise(r => requestAnimationFrame(r))
            for (const title of host.querySelectorAll('[data-slot="card-title"]')) {
              const range = document.createRange()
              range.selectNodeContents(title)
              const lines = new Set([...range.getClientRects()].map(r => Math.round(r.top))).size
              const text = range.getBoundingClientRect()
              const action = title.parentElement.querySelector('[data-slot="card-action"]').getBoundingClientRect()
              const hit = text.left < action.right && text.right > action.left && text.top < action.bottom && text.bottom > action.top
              const header = title.parentElement.getBoundingClientRect()
              out.push([width, title.textContent, lines, hit, Math.round(title.getBoundingClientRect().top - header.top)])
            }
            host.remove()
          }
          return out
        }"""
    )
    for width, value, lines, hit, top in result:
        assert lines == 1 and not hit, (width, value, lines, hit)
        assert top == 24, (width, value, top, "the value stays in the second row under the description")
