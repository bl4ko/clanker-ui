(() => {
  const RULES = ["unknown-slot", "part-outside-root", "unknown-attr", "bad-value", "kit-added", "missing-group", "unknown-class"]
  const KIT_JS = /\/(clanker-ui(?:-[a-z]+)?)(\.min)?\.js(?:[?#]|$)/
  const TAILWIND = /[:[]|-\d|px|full|auto/
  const SHARED = new Set(T.shared)
  const SIBLING = {}
  for (const s of Object.values(T.slots)) for (const a of Object.keys(s.a || {})) (SIBLING[s.c] ??= new Set()).add(a)
  let snapshot = null
  if (document.readyState === "loading") document.addEventListener("readystatechange", () => (snapshot ??= document.documentElement.cloneNode(true)), { once: true })

  function sel(el) {
    const parts = []
    for (let e = el; e && e.nodeType === 1 && parts.length < 6; e = e.parentElement) {
      if (e.id) {
        parts.unshift("#" + CSS.escape(e.id))
        break
      }
      let p = e.localName
      const slot = e.getAttribute("data-slot")
      if (slot) p += `[data-slot="${slot}"]`
      const same = e.parentElement ? [...e.parentElement.children].filter(c => c.localName === e.localName) : []
      if (same.length > 1) p += `:nth-of-type(${same.indexOf(e) + 1})`
      parts.unshift(p)
      if (e.localName === "body") break
    }
    return parts.join(" > ")
  }

  const list = spec => spec.map(v => (v === "" ? "(no value)" : v)).join(", ")

  function problem(spec, name, value, root) {
    if (Array.isArray(spec)) {
      if (spec.includes(value)) return ""
      if (value === "" && spec.includes("true")) return `write ${name}="true"; the bare attribute does not turn it on here`
      return `${name}="${value}" is not one of ${list(spec)}`
    }
    if (spec === "boolean" && value !== "" && value !== "true") return `${name}="${value}": write ${name}="true" for on and leave it out for off`
    if (spec === "number" && (value.trim() === "" || !Number.isFinite(Number(value)))) return `${name}="${value}" is not a number`
    if (spec === "id" && value !== "" && !root.querySelector("#" + CSS.escape(value))) return `${name}="${value}": no element has this id`
    return ""
  }

  function inRoot(el, comp, root) {
    for (let p = el.parentElement; p; p = p.parentElement) if (T.slots[p.getAttribute("data-slot")]?.c === comp) return true
    const roots = [...root.querySelectorAll(`[data-slot="${comp}"][id]`)].map(r => r.id)
    if ([...el.attributes].some(a => roots.includes(a.value))) return true
    return !!el.id && [...root.querySelectorAll("[data-slot]")].some(o => T.slots[o.getAttribute("data-slot")]?.c === comp && [...o.attributes].some(a => a.name !== "id" && a.value === el.id))
  }

  function near(a, b) {
    const max = Math.min(a.length, b.length) > 10 ? 2 : 1
    if (Math.abs(a.length - b.length) > max) return false
    let row = [...Array(b.length + 1).keys()]
    for (let i = 1; i <= a.length; i++) {
      const next = [i]
      for (let j = 1; j <= b.length; j++) next[j] = Math.min(row[j] + 1, next[j - 1] + 1, row[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1))
      row = next
    }
    return row[b.length] <= max
  }

  function kitLike(name, part, owners) {
    if (SHARED.has(name) || SIBLING[part.c]?.has(name) || new RegExp(`^data-${part.c}-`).test(name)) return true
    const valid = [...Object.keys(part.a || {}), ...Object.keys(T.global), ...owners.flatMap(o => Object.keys(o || {}))]
    return valid.some(v => near(name, v))
  }

  function options(el) {
    const out = []
    for (let p = el; p; p = p.parentElement) {
      const c = T.slots[p.getAttribute("data-slot")]?.c
      if (c) out.push(T.comps[c].o)
    }
    return out
  }

  function known() {
    const names = new Set()
    const unescape = s => s.replace(/\\(?:([0-9a-fA-F]{1,6})\s?|(.))/g, (_, hex, ch) => (hex ? String.fromCodePoint(parseInt(hex, 16)) : ch))
    const walk = rules => {
      for (const r of rules) {
        if (r.selectorText) for (const m of r.selectorText.matchAll(/\.((?:\\[0-9a-fA-F]{1,6}\s?|\\.|[\w-]|[^\x00-\x7f])+)/g)) names.add(unescape(m[1]))
        if (r.styleSheet) sheet(r.styleSheet)
        if (r.cssRules) walk(r.cssRules)
      }
    }
    const sheet = s => {
      try {
        walk(s.cssRules)
      } catch {}
    }
    for (const s of [...document.styleSheets, ...document.adoptedStyleSheets]) sheet(s)
    return names
  }

  function groups(used, report) {
    const urls = [...document.scripts].map(s => s.src).concat(performance.getEntriesByType("resource").map(e => e.name))
    const files = new Set(urls.map(u => KIT_JS.exec(u)).filter(m => m && m[1] !== "clanker-ui-theme" && m[1] !== "clanker-ui-code").map(m => m[1] + (m[2] || "")))
    const min = [...files].filter(f => f.endsWith(".min"))
    if (min.length && min.length < files.size) report(null, `the page mixes readable and .min kit files (${[...files].sort().join(", ")}); use one set`)
    const bundle = files.has("clanker-ui") || files.has("clanker-ui.min")
    const parts = [...files].map(f => f.replace(/\.min$/, "").replace(/^clanker-ui-?/, ""))
    if (bundle && parts.some(g => g && g !== "core" && g !== "chart")) report(null, "the page loads clanker-ui.min.js together with a group file; load the one-file set or the group files, not both")
    const loaded = new Set(parts.filter(Boolean))
    if (bundle) for (const c of Object.values(T.comps)) if (c.g !== "chart") loaded.add(c.g)
    if (bundle || parts.some(g => g && g !== "chart")) loaded.add("core")
    const done = new Set()
    for (const [comp, el] of used) {
      for (const g of [T.comps[comp].g, ...(T.comps[comp].n || [])]) {
        if (loaded.has(g) || done.has(g)) continue
        done.add(g)
        report(el, `${comp} needs the ${g} group: load the module clanker-ui-${g}${min.length ? ".min" : ""}.js${g === "chart" ? "" : " or the one-file set"}`)
      }
    }
  }

  function lint(opts = {}) {
    const live = !!opts.live || !snapshot
    const root = live ? document.documentElement : snapshot
    const only = new Set(opts.rules || RULES)
    const findings = []
    const report = (rule, severity, el, message) => {
      if (only.has(rule)) findings.push({ rule, severity, selector: el ? sel(el) : "html", message })
    }
    const used = new Map()
    for (const el of root.querySelectorAll("[data-slot]")) {
      const slot = el.getAttribute("data-slot")
      const part = T.slots[slot]
      if (!part) {
        report("unknown-slot", "error", el, `data-slot="${slot}" is not a clanker-ui part; check the name in components.md`)
        continue
      }
      const comp = T.comps[part.c]
      if (comp.j && !used.has(part.c)) used.set(part.c, el)
      if (part.k && !live) {
        report("kit-added", "error", el, `the kit adds ${slot}; remove it from the markup`)
        continue
      }
      if (part.i && !inRoot(el, part.c, root)) report("part-outside-root", "error", el, `${slot} is outside a ${part.c} root; put it inside data-slot="${part.c}" or link it with the id of the root`)
      const owners = options(el)
      for (const { name, value } of el.attributes) {
        if (!name.startsWith("data-") || name === "data-slot" || name === "data-lint-ignore" || name.startsWith("data-string-")) continue
        const spec = part.a?.[name] ?? T.global[name] ?? owners.find(o => o?.[name] !== undefined)?.[name] ?? T.parts[name]
        if (spec === undefined) {
          if (part.s?.includes(name) || T.kit.includes(name)) {
            if (!live) report("kit-added", "error", el, `the kit sets ${name} on ${slot}; use it only as a CSS selector`)
          } else if (kitLike(name, part, owners)) report("unknown-attr", "error", el, `${slot} has no attribute ${name}; see components/${part.c}.md`)
          continue
        }
        const p = problem(spec, name, value, root)
        if (p) report("bad-value", "error", el, p)
      }
    }
    for (const el of root.querySelectorAll("*")) {
      if (el.hasAttribute("data-slot")) continue
      for (const { name, value } of el.attributes) {
        const spec = T.parts[name]
        const p = spec === undefined ? "" : problem(spec, name, value, root)
        if (p) report("bad-value", "error", el, p)
      }
    }
    if (only.has("missing-group")) groups(used, (el, message) => report("missing-group", "error", el, message))
    if (only.has("unknown-class")) {
      const names = known()
      const seen = new Set()
      for (const el of root.querySelectorAll("[class]")) {
        for (const c of el.classList) {
          if (names.has(c) || seen.has(c) || /^lucide(-|$)/.test(c)) continue
          seen.add(c)
          if (TAILWIND.test(c)) report("unknown-class", "error", el, `class "${c}" matches no rule in the page stylesheets and looks like a Tailwind utility; the kit has no Tailwind: use kit parts and attributes, or a rule in app.css`)
          else report("unknown-class", "warn", el, `class "${c}" matches no rule in the page stylesheets; add a rule in app.css or remove it`)
        }
      }
    }
    return { findings }
  }

  lint.rules = RULES
  window.clankerMarkupLint = lint
  if (document.currentScript)
    addEventListener(
      "load",
      () => {
        for (const f of lint().findings) console[f.severity === "error" ? "error" : "warn"](`clanker-ui markup: ${f.rule} ${f.selector}: ${f.message}`)
      },
      { once: true },
    )
})()
