cfg => {
  if (window.__guard) return
  const G = (window.__guard = {})
  const html = document.documentElement
  const SEP = "\u0001"
  const PROPS = [...new Set([...getComputedStyle(html)].filter(p => !p.startsWith("--")).concat(cfg.custom))]
  const valid = s => {
    try {
      html.matches(s)
      return true
    } catch {
      return false
    }
  }
  const FIXED = { "::placeholder": "input,textarea", "::backdrop": "dialog,[popover]", "::file-selector-button": 'input[type="file"]' }
  const PSEUDO = cfg.pseudo.map(([pe, sels]) => [pe, FIXED[pe] ?? sels.filter(valid).join(",")]).filter(p => p[1])
  const TESTS = cfg.tests.map(([name, op, value, keys]) => [name, value, op ? `[${name}${op}"${CSS.escape(value)}"]` : `[${name}]`, new Set(keys)]).filter(t => valid(t[2]))
  const NAMES = cfg.names.map(([name, keys]) => [name, new Set(keys)])
  const DYN = Object.fromEntries(Object.entries(cfg.dyn).map(([p, keys]) => [p, new Set(keys)]))
  let near = new Map()
  const index = els => {
    near = new Map(els.map(e => [e, new Set(["*", "@" + e.localName, e.getAttribute("data-slot")])]))
    for (const e of els) {
      const s = e.getAttribute("data-slot")
      if (!s) continue
      const key = "^" + s
      for (let a = e.parentElement; a; a = a.parentElement) near.get(a)?.add(key)
      for (const d of e.querySelectorAll("*")) near.get(d).add(key)
      for (const d of e.parentElement?.children ?? []) near.get(d)?.add(key)
    }
  }
  const hit = (el, keys) => {
    for (const k of near.get(el) ?? []) if (keys.has(k)) return true
    return false
  }
  const all = () => [html, document.body, ...document.body.querySelectorAll("*")]
  const read = (el, pe) => {
    const cs = getComputedStyle(el, pe)
    let s = ""
    for (let i = 0; i < PROPS.length; i++) s += cs.getPropertyValue(PROPS[i]) + SEP
    return s
  }
  const one = el => {
    const out = [["", read(el)]]
    for (const pe of ["::before", "::after"]) {
      const c = getComputedStyle(el, pe).content
      out.push([pe, c === "none" || c === "normal" || c === "" ? "-" : read(el, pe)])
    }
    if (getComputedStyle(el).display === "list-item") out.push(["::marker", read(el, "::marker")])
    for (const [pe, sel] of PSEUDO) if (el.matches(sel)) out.push([pe, read(el, pe)])
    return out
  }
  const path = el => {
    const p = []
    for (let e = el; e && e !== html; e = e.parentElement) {
      const s = e.getAttribute("data-slot")
      p.unshift(e.localName + (s ? `[${s}]` : "") + ":" + ([...e.parentElement.children].indexOf(e) + 1))
    }
    return p.join(">") || "html"
  }
  const diff = (els, a, b) => {
    const out = []
    let n = 0
    for (let i = 0; i < els.length; i++) {
      const x = a[i], y = b[i]
      for (let j = 0; j < Math.max(x.length, y.length); j++) {
        const [pa, va] = x[j] ?? ["none", ""], [pb, vb] = y[j] ?? ["none", ""]
        if (pa === pb && va === vb) continue
        n++
        if (out.length >= cfg.cap) continue
        const A = va.split(SEP), B = vb.split(SEP), props = []
        if (pa !== pb || A.length !== B.length) props.push(["(pseudo-element)", pa + " " + va.slice(0, 20), pb + " " + vb.slice(0, 20)])
        else for (let k = 0; k < PROPS.length && props.length < 8; k++) if (A[k] !== B[k]) props.push([PROPS[k], A[k], B[k]])
        out.push({ el: path(els[i]), pseudo: pa, props })
      }
    }
    return { n, out }
  }
  const settle = () => {
    for (let round = 0; round < 3; round++) {
      void document.body.offsetWidth
      const live = document.getAnimations().filter(a => a.playState === "running" || a.pending)
      if (!live.length) return
      for (const a of live) {
        try {
          a.finish()
        } catch {
          try {
            a.pause()
            a.currentTime = 0
          } catch {}
        }
      }
    }
  }
  const use = (style, which) => {
    for (const s of G.sheets) s.sheet.disabled = !(s.style === style && s.which === which)
    settle()
  }
  G.load = async files => {
    const links = [...document.querySelectorAll('link[rel="stylesheet"]')]
    const at = new Map()
    const pending = files.map(f => new Promise((resolve, reject) => {
      const re = new RegExp(f.anchor ?? "/clanker-ui(\\.min)?\\.css$")
      const orig = links.find(l => re.test(new URL(l.href).pathname))
      if (!orig) return reject(new Error("no stylesheet link " + re.source))
      const l = document.createElement("link")
      l.rel = "stylesheet"
      l.href = f.href
      l.onload = () => resolve({ ...f, sheet: l.sheet })
      l.onerror = () => reject(new Error("load " + f.href))
      ;(at.get(orig) ?? orig).after(l)
      at.set(orig, l)
    }))
    G.sheets = await Promise.all(pending)
    for (const orig of at.keys()) orig.sheet.disabled = true
    for (const s of G.sheets) s.sheet.disabled = true
    return PROPS.length
  }
  G.sweep = configs => {
    const els = all(), out = []
    const theme = html.getAttribute("data-theme")
    for (const [style, t] of configs) {
      if (t) html.setAttribute("data-theme", t)
      else html.removeAttribute("data-theme")
      use(style, "old")
      const a = els.map(one)
      use(style, "new")
      const d = diff(els, a, els.map(one))
      if (d.n) out.push({ config: style + "/" + (t ?? "auto"), ...d })
    }
    if (theme === null) html.removeAttribute("data-theme")
    else html.setAttribute("data-theme", theme)
    return { elements: els.length, sweeps: configs.length, diffs: out }
  }
  const state = (label, targets, apply, undo, configs, res) => {
    if (!targets.length) return
    for (const e of targets) apply(e)
    const r = G.sweep(configs)
    for (const e of targets) undo(e)
    res.states++
    res.sweeps += r.sweeps
    for (const d of r.diffs) res.diffs.push({ state: label, targets: targets.length, ...d })
  }
  G.attrs = (configs, from = 0, to = 1e9) => {
    const els = all(), res = { states: 0, sweeps: 0, diffs: [], total: TESTS.length + NAMES.length }
    index(els)
    const jobs = []
    for (const [name, value, sel, keys] of TESTS) jobs.push([sel, e => hit(e, keys) && !e.matches(sel), e => e.setAttribute(name, value ?? ""), name])
    for (const [name, keys] of NAMES) jobs.push([`-[${name}]`, e => e.hasAttribute(name) && hit(e, keys), e => e.removeAttribute(name), name])
    for (const [label, want, apply, name] of jobs.slice(from, to)) {
      const targets = els.filter(want)
      const prev = new Map(targets.map(e => [e, e.getAttribute(name)]))
      state(label, targets, apply, e => (prev.get(e) === null ? e.removeAttribute(name) : e.setAttribute(name, prev.get(e))), configs, res)
    }
    return res
  }
  G.app = configs => {
    const res = { states: 0, sweeps: 0, diffs: [] }
    const tokens = Object.entries(cfg.tokens)
    state("app tokens", [html], e => tokens.forEach(([k, v]) => e.style.setProperty(k, v)), e => tokens.forEach(([k]) => e.style.removeProperty(k)), configs, res)
    const sheet = new CSSStyleSheet()
    sheet.replaceSync(cfg.appCss)
    state("app css", [html], () => (document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet]), () => (document.adoptedStyleSheets = document.adoptedStyleSheets.filter(x => x !== sheet)), configs, res)
    return res
  }
  const own = el => el.localName + cfg.attrNames.map(a => (el.hasAttribute(a) ? `[${a}=${el.getAttribute(a)}]` : "")).join("") + (el.previousElementSibling ? "" : "^") + (el.nextElementSibling ? "" : "$")
  const sig = el => {
    let s = own(el) + "{" + [...el.children].map(c => own(c) + "{" + [...c.children].map(own).join(",") + "}").join(",") + "}"
    for (let e = el.parentElement; e; e = e.parentElement) s += "<" + own(e)
    return s
  }
  const dedupe = list => {
    const seen = new Set()
    return list.filter(e => {
      const s = sig(e)
      return !seen.has(s) && seen.add(s)
    })
  }
  G.candidates = pseudos => {
    const els = all(), at = new Map(els.map((e, i) => [e, i]))
    index(els)
    const keys = pseudos.map(p => DYN[p]).filter(Boolean)
    const hits = els.filter(e => keys.some(k => hit(e, k)))
    G.picked = dedupe(hits.filter(e => near.get(e).size > 3 || e.matches("a,button,input,select,textarea,summary,[tabindex]")))
    return {
      all: hits.map(e => at.get(e)),
      picked: G.picked.map(e => {
        const chain = []
        for (let a = e; a; a = a.parentElement) chain.push(at.get(a))
        return chain
      }),
    }
  }
  G.triggers = () => {
    G.picked = dedupe([...document.body.querySelectorAll('[aria-haspopup]:not(a[href]),[aria-expanded="false"]:not(a[href]),button[data-slot$="trigger"]')])
    return G.picked.length
  }
  G.point = k => {
    const e = G.picked[k]
    e.scrollIntoView({ block: "center", inline: "center" })
    const r = e.getBoundingClientRect()
    return r.width && r.height ? [r.x + r.width / 2, r.y + r.height / 2] : null
  }
  G.is = (k, sel) => G.picked[k].matches(sel)
}
