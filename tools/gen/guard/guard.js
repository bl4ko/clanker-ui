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
  const TESTS = cfg.tests.map(([name, op, value, keys, aff]) => [name, value, op ? `[${name}${op}"${CSS.escape(value)}"]` : `[${name}]`, new Set(keys), new Set(aff)]).filter(t => valid(t[2]))
  const NAMES = cfg.names.map(([name, keys, aff]) => [name, new Set(keys), new Set(aff)])
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
    const v = new Array(PROPS.length)
    for (let i = 0; i < PROPS.length; i++) v[i] = cs.getPropertyValue(PROPS[i])
    return v.join(SEP)
  }
  const hash = s => {
    let a = 0xdeadbeef, b = 0x41c6ce57
    for (let i = 0; i < s.length; i++) {
      const c = s.charCodeAt(i)
      a = Math.imul(a ^ c, 2654435761)
      b = Math.imul(b ^ c, 1597334677)
    }
    a = Math.imul(a ^ (a >>> 16), 2246822507) ^ Math.imul(b ^ (b >>> 13), 3266489909)
    b = Math.imul(b ^ (b >>> 16), 2246822507) ^ Math.imul(a ^ (a >>> 13), 3266489909)
    return 4294967296 * (2097151 & b) + (a >>> 0)
  }
  const NOBOX = [["", "-"]]
  const noBox = el => {
    if (el === html || el.checkVisibility()) return false
    for (let a = el.parentElement; a; a = a.parentElement) {
      if (a.checkVisibility()) return false
      if (getComputedStyle(a).display !== "contents") return true
    }
    return false
  }
  const one = (el, full) => {
    if (cfg.skipNoBox && noBox(el)) return NOBOX
    const get = full ? read : (e, pe) => hash(read(e, pe))
    const out = [["", get(el)]]
    for (const pe of ["::before", "::after"]) {
      const c = getComputedStyle(el, pe).content
      out.push([pe, c === "none" || c === "normal" || c === "" ? "-" : get(el, pe)])
    }
    if (getComputedStyle(el).display === "list-item") out.push(["::marker", get(el, "::marker")])
    for (const [pe, sel] of PSEUDO) if (el.matches(sel)) out.push([pe, get(el, pe)])
    return out
  }
  const same = (a, b) => a.every((x, i) => x.length === b[i].length && x.every((p, j) => p[0] === b[i][j][0] && p[1] === b[i][j][1]))
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
  const kill = new CSSStyleSheet()
  kill.replaceSync("*, *::before, *::after { transition: none !important }")
  const quiet = (change, els = []) => {
    document.adoptedStyleSheets = [...document.adoptedStyleSheets, kill]
    change()
    void document.body.offsetWidth
    for (const e of els) void getComputedStyle(e).opacity
    document.adoptedStyleSheets = document.adoptedStyleSheets.filter(s => s !== kill)
    settle()
  }
  const theme = t => (t ? html.setAttribute("data-theme", t) : html.removeAttribute("data-theme"))
  const run = (configs, states) => {
    const before = html.getAttribute("data-theme"), styles = new Map(), res = { sweeps: 0, retried: 0, diffs: [] }
    for (const [style, t] of configs) styles.set(style, [...(styles.get(style) ?? []), t])
    for (const [style, themes] of styles) {
      const pass = (which, list, ts, again) => {
        const on = w => () => G.sheets.forEach(s => (s.sheet.disabled = !(s.style === style && s.which === w)))
        quiet(on(which))
        return list.map(st => {
          const r = ts.map((t, j) => {
            if (again) quiet(() => theme(t), st.els)
            quiet(() => {
              if (!j) st.apply?.()
              theme(t)
            }, st.els)
            if (again) {
              quiet(on(which === "old" ? "new" : "old"))
              quiet(on(which), st.els)
            }
            return st.els.map(e => one(e, again))
          })
          st.undo?.()
          return r
        })
      }
      const got = ["old", "new"].map(which => pass(which, states, themes))
      states.forEach((st, i) => themes.forEach((t, j) => {
        res.sweeps++
        if (same(got[0][i][j], got[1][i][j])) return
        const d = diff(st.els, pass("old", [st], [t], true)[0][0], pass("new", [st], [t], true)[0][0])
        if (d.n) res.diffs.push({ config: style + "/" + (t ?? "auto"), ...(st.label ? { state: st.label, targets: st.targets } : {}), ...d })
        else res.retried++
      }))
    }
    quiet(() => theme(before))
    return res
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
  const region = (els, targets, aff) => {
    if (aff.has("*")) return els
    const roots = new Set(targets.map(e => e.parentElement ?? e))
    for (const e of els) if (aff.has(e.getAttribute("data-slot"))) roots.add(e.parentElement ?? e)
    if (roots.has(html) || roots.has(document.body)) return els
    return els.filter(e => {
      for (let a = e; a; a = a.parentElement) if (roots.has(a)) return true
      return false
    })
  }
  G.sweep = configs => {
    const els = all()
    return { elements: els.length, ...run(configs, [{ els }]) }
  }
  G.attrs = (configs, from, cap) => {
    const els = all(), states = []
    index(els)
    const jobs = []
    for (const [name, value, sel, keys, aff] of TESTS) jobs.push([sel, e => hit(e, keys) && !e.matches(sel), e => e.setAttribute(name, value ?? ""), name, aff])
    for (const [name, keys, aff] of NAMES) jobs.push([`-[${name}]`, e => e.hasAttribute(name) && hit(e, keys), e => e.removeAttribute(name), name, aff])
    let next = from
    for (let reads = 0; next < jobs.length && reads < cap; next++) {
      const [label, want, apply, name, aff] = jobs[next]
      const targets = els.filter(want)
      if (!targets.length) continue
      const prev = new Map(targets.map(e => [e, e.getAttribute(name)]))
      const undo = e => (prev.get(e) === null ? e.removeAttribute(name) : e.setAttribute(name, prev.get(e)))
      states.push({ label, targets: targets.length, els: region(els, targets, aff), apply: () => targets.forEach(apply), undo: () => targets.forEach(undo) })
      reads += states.at(-1).els.length
    }
    return { states: states.length, total: jobs.length, next, ...run(configs, states) }
  }
  G.app = configs => {
    const tokens = Object.entries(cfg.tokens), els = all()
    const sheet = new CSSStyleSheet()
    sheet.replaceSync(cfg.appCss)
    return {
      states: 2,
      ...run(configs, [
        { label: "app tokens", targets: 1, els, apply: () => tokens.forEach(([k, v]) => html.style.setProperty(k, v)), undo: () => tokens.forEach(([k]) => html.style.removeProperty(k)) },
        { label: "app css", targets: 1, els, apply: () => (document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet]), undo: () => (document.adoptedStyleSheets = document.adoptedStyleSheets.filter(x => x !== sheet)) },
      ]),
    }
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
