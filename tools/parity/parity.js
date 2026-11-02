(cfg) => {
  if (window.__parity) return
  const P = (window.__parity = {})
  const PROPS = cfg.props
  const ids = new WeakMap()
  const byId = new Map()
  let next = 1
  P.id = el => {
    let i = ids.get(el)
    if (!i) {
      i = el.getAttribute?.("data-pid") ? Number(el.getAttribute("data-pid")) : cfg.ours ? -next++ : next++
      ids.set(el, i)
      byId.set(i, el)
    }
    return i
  }
  P.el = i => {
    const e = byId.get(i)
    if (e && e.isConnected) return e
    const f = document.querySelector(`[data-pid="${i}"]`)
    return f
  }
  const canvas = document.createElement("canvas").getContext("2d", { willReadFrequently: true })
  const COLOR = /(rgba?|oklch|oklab|lab|lch|hsla?|hwb|color)\((?:[^()]|\([^()]*\))*\)|#[0-9a-fA-F]{3,8}\b|\btransparent\b/g
  const norm = s => s.replace(COLOR, m => {
    canvas.clearRect(0, 0, 1, 1)
    canvas.fillStyle = "#010203"
    canvas.fillStyle = m
    canvas.fillRect(0, 0, 1, 1)
    const d = canvas.getImageData(0, 0, 1, 1).data
    return d[3] === 0 ? "transparent" : `rgba(${d[0]},${d[1]},${d[2]},${(d[3] / 255).toFixed(2)})`
  })
  P.read = (el, pseudo) => {
    const cs = getComputedStyle(el, pseudo || null)
    const out = {}
    if (pseudo === "::before" || pseudo === "::after") {
      const c = cs.getPropertyValue("content")
      if (c === "none" || c === "normal") return null
      for (const p of cfg.pseudoProps) out[p] = norm(cs.getPropertyValue(p)).trim()
      return out
    }
    for (const p of PROPS) out[p] = norm(cs.getPropertyValue(p)).trim()
    if (!pseudo) {
      const r = el.getBoundingClientRect()
      out["@x"] = Math.round(r.x * 10) / 10
      out["@y"] = Math.round(r.y * 10) / 10
      out["@w"] = Math.round(r.width * 10) / 10
      out["@h"] = Math.round(r.height * 10) / 10
      out["@visible"] = r.width > 0 && r.height > 0 && cs.visibility !== "hidden" ? 1 : 0
    }
    return out
  }
  const SVG = new Set(["svg", "path", "circle", "ellipse", "line", "polyline", "polygon", "rect", "g", "use", "text", "tspan", "defs", "clippath", "lineargradient", "stop", "mask", "symbol"])
  P.initials = tags => {
    const box = document.createElement("div")
    box.style.display = "none"
    document.body.append(box)
    const out = {}
    for (const t of tags) {
      const e = SVG.has(t) ? document.createElementNS("http://www.w3.org/2000/svg", t) : document.createElement(t)
      e.style.setProperty("all", "initial")
      box.append(e)
      const cs = getComputedStyle(e)
      out[t] = {}
      for (const p of PROPS) out[t][p] = norm(cs.getPropertyValue(p)).trim()
    }
    box.remove()
    return out
  }
  P.readAll = list => {
    const out = {}
    for (const [i, pseudo] of list) {
      const e = P.el(i)
      if (!e) continue
      const v = P.read(e, pseudo)
      if (v) out[pseudo ? `${i}${pseudo}` : i] = v
    }
    return out
  }
  const SKIP = new Set(["script", "style", "iframe", "noscript", "template", "link", "meta"])
  P.serialize = root => {
    const walk = n => {
      if (n.nodeType === 3) return n.textContent
      if (n.nodeType !== 1 || SKIP.has(n.localName)) return null
      const attrs = []
      for (const a of n.attributes) if (!a.name.startsWith("on")) attrs.push([a.name, a.value])
      const kids = []
      for (const c of n.childNodes) {
        const k = walk(c)
        if (k !== null) kids.push(k)
      }
      const node = { i: P.id(n), t: n.localName, a: attrs, c: kids }
      if (n.namespaceURI === "http://www.w3.org/2000/svg") node.svg = 1
      if (n.matches?.(":disabled")) node.dis = 1
      return node
    }
    return walk(root)
  }
  P.scopes = () => [...document.querySelectorAll(cfg.scope)]
  const PREVIEW = cfg.scope
  const shown = e => e.getClientRects().length > 0
  P.mark = () => {
    P.before = new WeakMap()
    for (const e of document.querySelectorAll("body *")) P.before.set(e, shown(e))
  }
  P.portals = () => {
    const scopes = P.scopes()
    const roots = new Set()
    for (const e of document.querySelectorAll("body [data-slot]")) {
      if (P.before.get(e) === true || !shown(e) || scopes.some(s => s.contains(e))) continue
      let r = e
      while (r.parentElement && r.parentElement !== document.body && !r.parentElement.querySelector(PREVIEW)) r = r.parentElement
      roots.add(r)
    }
    return [...roots].filter(r => ![...roots].some(o => o !== r && o.contains(r)))
  }
  P.attrs = roots => {
    const out = {}
    for (const r of roots) for (const e of [r, ...r.querySelectorAll("*")]) {
      const o = {}
      for (const a of e.attributes) o[a.name] = a.value
      out[P.id(e)] = o
    }
    return out
  }
  const frames = n => new Promise(r => {
    const step = k => (k ? requestAnimationFrame(() => step(k - 1)) : r())
    step(n)
  })
  P.settle = async (ms = 1500) => {
    await frames(2)
    const running = document.getAnimations().filter(a => a.playState === "running" && Number.isFinite(a.effect?.getComputedTiming().endTime))
    await Promise.race([Promise.all(running.map(a => a.finished.catch(() => null))), new Promise(r => setTimeout(r, ms))])
    for (const a of document.getAnimations()) if (a instanceof CSSTransition && a.playState === "running") a.finish()
    for (const a of document.getAnimations()) if (a.timeline === document.timeline && !Number.isFinite(a.effect?.getComputedTiming().endTime)) { a.pause(); a.currentTime = 0 }
    await frames(2)
  }
  P.active = () => {
    const a = document.activeElement
    return a && a !== document.body ? P.id(a) : 0
  }
  P.sync = ([before, states]) => {
    const diffs = []
    for (const [i, attrs] of Object.entries(before || {})) {
      const e = P.el(Number(i))
      if (!e) continue
      for (const [k, v] of Object.entries(attrs)) if (k !== "class" && k !== "data-pid" && k !== "data-slot" && e.getAttribute(k) !== v) diffs.push([Number(i), k, v])
      for (const k of states) if (e.hasAttribute(k) && !(k in attrs)) diffs.push([Number(i), k, null])
    }
    return P.apply(diffs)
  }
  P.apply = diffs => {
    const prev = []
    for (const [i, name, value] of diffs) {
      const e = P.el(i)
      if (!e) continue
      prev.unshift([i, name, e.getAttribute(name)])
      if (value === null) e.removeAttribute(name)
      else e.setAttribute(name, value)
    }
    return prev
  }
}
