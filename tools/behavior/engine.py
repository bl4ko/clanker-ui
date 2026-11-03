import difflib
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import sys
import time

from playwright.sync_api import Error as PlaywrightError

ROOT = pathlib.Path(__file__).resolve().parents[2]
BEHAVIOR = ROOT / "test" / "behavior"
SCENARIOS = BEHAVIOR / "scenarios"
GOLDEN = BEHAVIOR / "golden"
FIXTURES = BEHAVIOR / "fixtures"
SITE = "https://ui.shadcn.com"
SITE_HOST = "ui.shadcn.com"
FONT = "Arial"
ANCHOR_Y = 300
TOLERANCE = {"ms": 20, "px": 1, "opacity": 0.02}
TOUCH_SLOP = 15
FRAME = 17
INTENT = {"hover", "leave", "focus", "tab_in", "tab", "shift_tab", "wait"}
CLASSES = ("focus", "keyboard", "state", "ARIA", "dismiss", "timing", "geometry")
SEVERITIES = ("broken", "visible", "minor")


def _runner():
    spec = importlib.util.spec_from_file_location("clanker_behavior_runner", ROOT / "test" / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RUNNER = _runner()
WIDTHS = RUNNER.WIDTHS
TODAY = RUNNER.TODAY


def pin_clock(year, month, day):
    return TODAY.replace("new Real(2026, 9, 28, 12)", f"new Real({year}, {month - 1}, {day}, 12)")

SHADCN_FONT = f"*, *::before, *::after, ::placeholder {{ font-family: {FONT} !important; }} html {{ scroll-behavior: auto !important; }}"

HELPERS = r"""
(cfg) => {
  const norm = s => (s || "").replace(/\s+/g, " ").trim()
  const all = (scope, css) => { try { return [...scope.querySelectorAll(css)] } catch { return [] } }
  const vis = el => {
    if (!el || !el.isConnected || el.nodeType !== 1) return false
    if (el.checkVisibility && !el.checkVisibility({ visibilityProperty: true, checkVisibilityCSS: true })) return false
    const r = el.getBoundingClientRect()
    return r.width > 0 && r.height > 0
  }
  const IMPLICIT = {
    button: "button, input[type=button], input[type=submit], input[type=reset], summary, [role=button]",
    link: "a[href], [role=link]",
    checkbox: "input[type=checkbox], [role=checkbox]",
    radio: "input[type=radio], [role=radio]",
    slider: "input[type=range], [role=slider]",
    textbox: "input:not([type]), input[type=text], input[type=email], input[type=password], input[type=tel], input[type=url], input[type=number], textarea, [role=textbox]",
    combobox: "select, input[list], [role=combobox]",
    listbox: "select[multiple], select[size], [role=listbox]",
    dialog: "dialog, [role=dialog]",
    heading: "h1, h2, h3, h4, h5, h6, [role=heading]",
    list: "ul, ol, [role=list]",
    listitem: "li, [role=listitem]",
    navigation: "nav, [role=navigation]",
    region: "section[aria-label], section[aria-labelledby], [role=region]",
    separator: "hr, [role=separator]",
    table: "table, [role=table]",
    grid: "[role=grid]",
    gridcell: "td, [role=gridcell]",
    group: "fieldset, details, [role=group]",
    form: "form, [role=form]"
  }
  const implicit = el => {
    const t = el.localName
    if (t === "button" || t === "summary") return "button"
    if (t === "a") return el.hasAttribute("href") ? "link" : "generic"
    if (t === "select") return el.multiple || el.size > 1 ? "listbox" : "combobox"
    if (t === "textarea") return "textbox"
    if (t === "dialog") return "dialog"
    if (/^h[1-6]$/.test(t)) return "heading"
    if (t === "ul" || t === "ol") return "list"
    if (t === "li") return "listitem"
    if (t === "nav") return "navigation"
    if (t === "hr") return "separator"
    if (t === "fieldset" || t === "details") return "group"
    if (t === "table") return "table"
    if (t === "td") return "gridcell"
    if (t === "form") return "form"
    if (t === "section" && (el.hasAttribute("aria-label") || el.hasAttribute("aria-labelledby"))) return "region"
    if (t === "input") {
      const ty = (el.getAttribute("type") || "text").toLowerCase()
      return { checkbox: "checkbox", radio: "radio", range: "slider", button: "button", submit: "button", reset: "button", search: "searchbox", hidden: "none" }[ty] || "textbox"
    }
    return "generic"
  }
  const role = el => (el.getAttribute("role") || "").split(/\s+/)[0] || implicit(el)
  const text = el => {
    if (!el) return ""
    let s = ""
    for (const n of el.childNodes) {
      if (n.nodeType === 3) s += n.textContent
      else if (n.nodeType === 1 && n.getAttribute("aria-hidden") !== "true" && !["script", "style", "template"].includes(n.localName)) s += " " + text(n) + " "
    }
    return s
  }
  const name = el => {
    if (!el) return ""
    const label = el.getAttribute("aria-label")
    if (label) return norm(label)
    const by = el.getAttribute("aria-labelledby")
    if (by) return norm(by.split(/\s+/).map(id => text(document.getElementById(id))).join(" "))
    if (el.labels && el.labels.length) return norm([...el.labels].map(text).join(" "))
    if (el.id) {
      const lab = [...document.querySelectorAll("label[for]")].filter(l => l.htmlFor === el.id)
      if (lab.length) return norm(lab.map(text).join(" "))
    }
    const wrap = el.closest("label")
    if (wrap && ["checkbox", "radio", "switch", "slider", "textbox", "combobox"].includes(role(el))) return norm(text(wrap))
    if (["input", "select", "textarea"].includes(el.localName)) return norm(el.getAttribute("placeholder") || el.getAttribute("title") || "")
    return norm(text(el) || el.getAttribute("title") || "")
  }
  const roots = all(document, cfg.root)
  const bh = window.__bh = { specs: cfg.parts, root: roots[cfg.rootNth || 0] || null, vis, norm, role, name, seen: new WeakMap(), count: 0 }
  if (!bh.root) return "root not found: " + cfg.root
  const candidates = (scope, s) => {
    if (s.css) return all(scope, s.css)
    if (s.slot) return all(scope, `[data-slot="${s.slot}"], [data-${s.slot}]`)
    if (s.role) return all(scope, IMPLICIT[s.role] ? IMPLICIT[s.role] + `, [role="${s.role}"]` : `[role="${s.role}"]`)
    return []
  }
  bh.find = (n, depth = 0) => {
    const s = typeof n === "string" ? bh.specs[n] : n
    if (!s || depth > 6) return null
    let scope = s.popup || s.in === "page" ? document : bh.root
    if (s.within) {
      scope = bh.find(s.within, depth + 1)
      if (!scope) return null
    }
    let els = candidates(scope, s)
    if (s.role) els = els.filter(e => role(e) === s.role)
    if (s.name != null) els = els.filter(e => name(e).startsWith(s.name))
    if (s.text != null) els = els.filter(e => norm(text(e)).includes(s.text))
    if (!s.hidden) {
      els = els.filter(e => !(e.localName === "input" && e.type === "hidden"))
      const shown = els.filter(e => e.getAttribute("aria-hidden") !== "true")
      if (shown.length) els = shown
    }
    if (s.visible !== false) els = els.filter(e => s.sized === false ? e.getClientRects().length > 0 && (!e.checkVisibility || e.checkVisibility({ visibilityProperty: true, checkVisibilityCSS: true })) : vis(e))
    if (s.popup && !s.within) {
      const inRoot = els.filter(e => bh.root.contains(e))
      if (s.notIn) {
        const other = bh.find(s.notIn, depth + 1)
        if (other) els = els.filter(e => e !== other && !e.contains(other) && !other.contains(e))
      }
      void inRoot
    }
    for (const e of els) if (!bh.seen.has(e)) bh.seen.set(e, ++bh.count)
    if (s.min && els.length < s.min) return null
    if (s.order === "oldest") els.sort((a, b) => bh.seen.get(a) - bh.seen.get(b))
    if (s.order === "newest") els.sort((a, b) => bh.seen.get(b) - bh.seen.get(a))
    const i = s.nth || 0
    return (i < 0 ? els[els.length + i] : els[i]) || null
  }
  bh.tab = el => {
    if (el.matches("input[type=radio]")) {
      const g = el.name ? [...document.querySelectorAll("input[type=radio]")].filter(r => r.name === el.name && r.form === el.form) : [el]
      const c = g.find(r => r.checked && !r.disabled)
      if (el.disabled) return -1
      return (c ? c === el : g.find(r => !r.disabled) === el) ? 0 : -1
    }
    if (el.disabled) return -1
    if (el.hasAttribute("tabindex") || el.matches("button, a[href], input:not([type=hidden]), select, textarea, summary, [contenteditable]")) return el.tabIndex
    return null
  }
  bh.native = (el, a) => {
    const out = {}
    const t = el.localName
    if (t === "input" && (el.type === "checkbox" || el.type === "radio") && !("aria-checked" in a)) out["aria-checked"] = el.indeterminate ? "mixed" : String(el.checked)
    if (["input", "button", "select", "textarea", "fieldset", "option"].includes(t) && el.disabled && !("aria-disabled" in a)) out["aria-disabled"] = "true"
    if (t === "input" && el.type === "range") {
      if (!("aria-valuenow" in a)) out["aria-valuenow"] = el.value
      if (!("aria-valuemin" in a)) out["aria-valuemin"] = el.min || "0"
      if (!("aria-valuemax" in a)) out["aria-valuemax"] = el.max || "100"
    }
    if (t === "summary" && el.parentElement && el.parentElement.localName === "details" && !("aria-expanded" in a)) out["aria-expanded"] = String(el.parentElement.open)
    if (t === "option" && !("aria-selected" in a)) out["aria-selected"] = String(el.selected)
    if (["input", "select", "textarea"].includes(t) && el.required && !("aria-required" in a)) out["aria-required"] = "true"
    return out
  }
  const depthOf = el => { let d = 0; for (let e = el; e; e = e.parentElement) d++; return d }
  bh.partOf = el => {
    let part = null, pd = -1
    for (const n of Object.keys(bh.specs)) {
      const p = bh.find(n)
      if (p && (p === el || p.contains(el))) {
        const d = depthOf(p)
        if (d > pd) { pd = d; part = n }
      }
    }
    if (part) return part
    return bh.root.contains(el) ? "root" : "outside"
  }
  bh.place = (a, b) => {
    const r = v => Math.round(v * 10) / 10
    const gaps = { bottom: b.top - a.bottom, top: a.top - b.bottom, right: b.left - a.right, left: a.left - b.right }
    let side = null, off = -Infinity
    for (const [k, v] of Object.entries(gaps)) if (v >= -1.5 && v > off) { side = k; off = v }
    if (!side) return { side: "overlap", dx: r(b.left - a.left), dy: r(b.top - a.top) }
    const horiz = side === "top" || side === "bottom"
    const al = horiz
      ? { start: b.left - a.left, center: b.left + b.width / 2 - a.left - a.width / 2, end: b.right - a.right }
      : { start: b.top - a.top, center: b.top + b.height / 2 - a.top - a.height / 2, end: b.bottom - a.bottom }
    let align = null, ao = Infinity
    for (const [k, v] of Object.entries(al)) if (Math.abs(v) < Math.abs(ao) - 0.01) { align = k; ao = v }
    return { side, offset: r(off), align, alignOffset: r(ao) }
  }
  const interactive = "a[href],button,input,select,textarea,summary,label,[role],[tabindex],[contenteditable]"
  bh.outsidePoints = () => {
    const r = bh.root.getBoundingClientRect()
    const xs = [r.left + 8, r.right - 8, r.left + r.width / 2, r.left + r.width / 4, r.right - r.width / 4]
    const ys = [r.top + 8, r.bottom - 8, r.top + r.height / 2]
    const pts = []
    for (const y of ys) for (const x of xs) pts.push([x, y])
    return pts.filter(([x, y]) => x >= 2 && y >= 2 && x <= innerWidth - 2 && y <= innerHeight - 2).map(([x, y]) => [Math.round(x), Math.round(y)])
  }
  bh.outside = () => {
    const boxes = Object.keys(bh.specs).map(n => bh.find(n)).filter(Boolean).map(e => e.getBoundingClientRect())
    for (const [x, y] of bh.outsidePoints()) {
      if (boxes.some(b => x >= b.left - 4 && x <= b.right + 4 && y >= b.top - 4 && y <= b.bottom + 4)) continue
      const e = document.elementFromPoint(x, y)
      if (!e) continue
      if (e.localName === "dialog") return [x, y]
      const hit = e.closest(interactive)
      if (hit && hit !== bh.root && !hit.contains(bh.root) && (bh.root.contains(hit) || hit.getAttribute("role") !== "presentation")) {
        const p = bh.partOf(hit)
        if (p !== "outside" || hit.matches("a[href],button,input,select,textarea,summary,[tabindex]")) continue
      }
      return [x, y]
    }
    return null
  }
  const ov = e => { const cs = getComputedStyle(e); return `${cs.overflowX}/${cs.overflowY}` }
  bh.lock0 = { html: ov(document.documentElement), body: ov(document.body), pos: getComputedStyle(document.body).position }
  bh.scroll0 = Math.round(scrollY)
  bh.root.setAttribute("data-bh-root", "")
  return null
}
"""

STATE_ATTRS = [
    "data-open", "data-closed", "data-popup-open", "data-pressed", "data-checked", "data-unchecked", "data-indeterminate",
    "data-highlighted", "data-selected", "data-active", "data-disabled", "data-readonly", "data-panel-open", "data-side",
    "data-align", "data-orientation", "data-activation-direction", "data-placeholder", "data-dragging", "data-expanded",
    "data-swipe-direction", "data-nested-drawer-open", "data-state", "data-focused", "data-touched", "data-dirty",
    "aria-expanded", "aria-selected", "aria-checked", "aria-pressed", "aria-disabled", "aria-haspopup", "aria-modal",
    "aria-hidden", "aria-orientation", "aria-valuenow", "aria-valuetext", "aria-valuemin", "aria-valuemax", "aria-current",
    "aria-invalid", "aria-readonly", "aria-required", "aria-autocomplete", "aria-multiselectable",
    "role", "tabindex", "disabled", "hidden", "inert",
]

PRESENCE_ATTRS = ["aria-controls", "aria-activedescendant"]

OBSERVE = r"""
([attrs, presence]) => {
  const bh = window.__bh
  const r1 = v => Math.round(v * 10) / 10
  const out = { parts: {}, place: {}, focus: null, active: null, highlight: null }
  for (const e of document.querySelectorAll("[data-bh-part]")) e.removeAttribute("data-bh-part")
  for (const e of document.querySelectorAll("[data-bh-focus]")) e.removeAttribute("data-bh-focus")
  const found = {}
  for (const n of Object.keys(bh.specs)) {
    const el = bh.find(n)
    found[n] = el
    if (!el) { out.parts[n] = null; continue }
    if (bh.specs[n].popup) el.setAttribute("data-bh-part", (el.getAttribute("data-bh-part") ? el.getAttribute("data-bh-part") + " " : "") + n)
    const a = {}
    for (const k of attrs) if (el.hasAttribute(k)) a[k] = el.getAttribute(k)
    for (const k of presence) if (el.hasAttribute(k)) a[k] = "*"
    delete a.tabindex
    const tab = bh.tab(el)
    if (tab !== null) a.tabindex = String(tab)
    Object.assign(a, bh.native(el, a))
    a.role = bh.role(el)
    const modal = [...document.querySelectorAll("dialog")].some(d => d.matches(":modal") && !d.contains(el))
    const blocked = !!el.closest('[inert],[aria-hidden="true"]') || modal
    const desc = (el.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean).map(id => document.getElementById(id)).filter(Boolean).map(e => bh.norm(e.textContent)).join(" ")
    const r = el.getBoundingClientRect()
    out.parts[n] = { state: a, blocked, description: desc || null, rect: [r1(r.left), r1(r.top), r1(r.width), r1(r.height)], edges: [r1(r.left), r1(r.top), r1(innerWidth - r.right), r1(innerHeight - r.bottom)] }
    if (bh.specs[n].scroll) out.parts[n].scroll = [Math.round(el.scrollLeft), Math.round(el.scrollTop)]
  }
  for (const [p, a, mode] of bh.positions || []) {
    const pe = found[p], ae = found[a]
    if (!pe || !ae) continue
    const ra = ae.getBoundingClientRect(), rb = pe.getBoundingClientRect()
    out.place[p] = mode === "center" ? { side: "overlap", dx: r1(rb.left + rb.width / 2 - ra.left), dy: r1(rb.top + rb.height / 2 - ra.top), center: true } : bh.place(ra, rb)
  }
  const f = document.activeElement
  if (f && f !== document.body && f !== document.documentElement) {
    f.setAttribute("data-bh-focus", "")
    const markers = [...f.attributes].filter(x => x.name.startsWith("data-") && x.value === "" && !x.name.startsWith("data-bh") && !attrs.includes(x.name)).map(x => x.name.slice(5))
    let visible = false
    try { visible = f.matches(":focus-visible") } catch {}
    const cs = getComputedStyle(f)
    const outline = cs.outlineStyle !== "none" && parseFloat(cs.outlineWidth) > 0 && !/rgba\([^)]*,\s*0\)|transparent/.test(cs.outlineColor)
    const ring = (cs.boxShadow.match(/(?:[a-z]+\([^)]*\)|#\w+)?\s*-?[\d.]+px\s+-?[\d.]+px(?:\s+-?[\d.]+px){0,2}(?:\s+inset)?/g) || []).some(sh => {
      const nums = (sh.match(/-?[\d.]+px/g) || []).map(parseFloat)
      const color = (sh.match(/^[a-z]+\([^)]*\)|^#\w+/) || [""])[0]
      const clear = /^rgba\([^)]*,\s*0\)$/.test(color) || /\/\s*0\)$/.test(color) || color === "transparent"
      return nums.length >= 4 && nums[0] === 0 && nums[1] === 0 && nums[2] === 0 && nums[3] > 0 && !clear
    })
    let popup = null
    for (const n of Object.keys(bh.specs)) if (bh.specs[n].popup && found[n] && found[n].contains(f)) popup = n
    const plain = ["generic", "presentation", "none"].includes(bh.role(f))
    out.focus = { role: plain ? "generic" : bh.role(f), name: (plain ? bh.norm(f.getAttribute("aria-label") || "") : bh.name(f)).slice(0, 80), slot: f.getAttribute("data-slot"), markers, part: bh.partOf(f), popup, visible, ring: outline || ring }
    const ad = f.getAttribute("aria-activedescendant")
    const ae = ad && document.getElementById(ad)
    if (ae) out.active = { role: bh.role(ae), name: bh.name(ae).slice(0, 80), part: bh.partOf(ae) }
  }
  const scopes = [bh.root, ...Object.keys(bh.specs).filter(n => bh.specs[n].popup && found[n]).map(n => found[n])]
  for (const s of scopes) {
    const h = [...s.querySelectorAll("[data-highlighted]")].filter(e => bh.vis(e) && !(e.parentElement && e.parentElement.closest("[data-highlighted]") && s.contains(e.parentElement.closest("[data-highlighted]")))).pop()
    if (h) out.highlight = { role: bh.role(h), name: bh.name(h).slice(0, 80), part: bh.partOf(h) }
    const sel = [...s.querySelectorAll('[role="option"][aria-selected="true"]')].filter(bh.vis).pop()
    if (sel) out.selected = { role: "option", name: bh.name(sel).slice(0, 80) }
  }
  const ov = e => { const cs = getComputedStyle(e); return `${cs.overflowX}/${cs.overflowY}` }
  const lock = { html: ov(document.documentElement), body: ov(document.body), pos: getComputedStyle(document.body).position }
  const hid = v => /hidden|clip/.test(v)
  out.lock = (hid(lock.html) && !hid(bh.lock0.html)) || (hid(lock.body) && !hid(bh.lock0.body)) || (lock.pos === "fixed" && bh.lock0.pos !== "fixed")
  out.overflow = `html ${lock.html}, body ${lock.body}, body position ${lock.pos}`
  out.scroll = Math.round(scrollY) - bh.scroll0
  out.modalOutside = [...document.querySelectorAll("dialog")].some(d => d.matches(":modal") && !d.contains(bh.root) && !bh.root.contains(d)) || [...document.querySelectorAll("dialog")].some(d => d.matches(":modal") && bh.root.contains(d))
  const controls = new Set()
  for (const s of scopes) for (const c of s.querySelectorAll("input, select, textarea")) controls.add(c)
  const rendered = c => (c.type || "").toLowerCase() === "hidden" ? bh.vis(c.parentElement) : c.getClientRects().length > 0 && (!c.checkVisibility || c.checkVisibility({ visibilityProperty: true, checkVisibilityCSS: true }))
  out.form = [...controls].filter(c => !["button", "submit", "reset", "image"].includes((c.type || "").toLowerCase()) && rendered(c)).map(c => {
    const ty = c.localName === "input" ? (c.type || "text").toLowerCase() : c.localName
    const v = ty === "checkbox" || ty === "radio" ? (c.checked ? "checked" : "unchecked") + (c.indeterminate ? " mixed" : "") : c.localName === "select" && c.multiple ? [...c.selectedOptions].map(o => o.value).join(",") : c.value
    return { type: ty === "checkbox" || ty === "radio" || ty === "range" ? ty : "value", value: v, name: c.name || null, disabled: c.disabled }
  })
  return out
}
"""

MOTION = r"""
({parts, ms}) => {
  const bh = window.__bh
  bh.ta = null
  bh.taType = null
  const types = ["keydown", "pointerover", "pointerenter", "pointerdown", "pointermove", "mouseover", "mousedown", "click", "contextmenu", "wheel", "touchstart"]
  const mark = e => { if (bh.ta == null && e.isTrusted) { bh.ta = performance.now(); bh.taType = e.type } }
  for (const t of types) addEventListener(t, mark, { capture: true })
  const probe = document.createElement("div")
  probe.setAttribute("aria-hidden", "true")
  Object.assign(probe.style, { position: "fixed", left: "-10px", top: "-10px", width: "1px", height: "1px", pointerEvents: "none" })
  document.documentElement.append(probe)
  const MOVING = /^(opacity|transform|scale|translate|rotate|width|height|top|left|right|bottom|inset|clip-path|filter|display|overlay|visibility|max-height|max-width|margin|padding|all)$/
  const opacity = el => { let o = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o }
  const frames = [], dom = [], anims = {}
  const last = {}
  for (const p of parts) anims[p] = {}
  const STATE = ["data-open", "data-closed", "data-state", "data-ending-style", "data-starting-style", "open", "hidden", "data-popup-open", "data-panel-open", "aria-expanded"]
  const sig = el => {
    if (!el) return "absent"
    if (!bh.vis(el)) return "hidden"
    return "shown " + STATE.filter(a => el.hasAttribute(a)).map(a => `${a}=${el.getAttribute(a)}`).join(" ")
  }
  const held = {}
  const get = p => {
    if (!(bh.specs[p] || {}).stick) return bh.find(p)
    if (p in held) return held[p].isConnected ? held[p] : null
    const el = bh.find(p)
    if (el) held[p] = el
    return el
  }
  const domSnap = () => {
    const now = performance.now()
    for (const p of parts) {
      const s = sig(get(p))
      if (s !== last[p]) { dom.push({ t: now, p, s }); last[p] = s }
    }
  }
  domSnap()
  const mo = new MutationObserver(domSnap)
  mo.observe(document, { subtree: true, childList: true, attributes: true })
  const t0 = performance.now()
  let n = 0
  const sample = () => {
      const now = performance.now()
      const f = { t: now, els: {} }
      for (const p of parts) {
        const el = get(p)
        if (!el) continue
        const r = el.getBoundingClientRect()
        f.els[p] = [Math.round(opacity(el) * 1000) / 1000, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]
        for (const a of el.getAnimations()) {
          if (a.transitionProperty && !MOVING.test(a.transitionProperty)) continue
          const key = a.animationName ? "animation " + a.animationName : a.transitionProperty ? "transition " + a.transitionProperty : "animation"
          if (anims[p][key]) continue
          const tm = a.effect && a.effect.getTiming ? a.effect.getTiming() : {}
          let easing = tm.easing || null
          if (a.animationName) { try { easing = a.effect.getKeyframes()[0].easing || easing } catch {} }
          anims[p][key] = { name: key, duration: typeof tm.duration === "number" ? Math.round(tm.duration) : 0, delay: Math.round(tm.delay || 0), easing, at: now }
        }
      }
      frames.push(f)
      return now
  }
  sample()
  bh.motion = new Promise(resolve => {
    const ro = new ResizeObserver(() => {
      const now = sample()
      if (now - t0 >= ms) {
        ro.disconnect()
        mo.disconnect()
        domSnap()
        probe.remove()
        for (const t of types) removeEventListener(t, mark, { capture: true })
        resolve({ t0, ta: bh.ta, taType: bh.taType, frames, dom, anims: Object.fromEntries(parts.map(p => [p, Object.values(anims[p])])) })
      }
    })
    ro.observe(probe)
    const tick = () => {
      probe.style.width = `${++n % 2 + 1}px`
      if (performance.now() - t0 < ms + 200) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  })
  return true
}
"""

SETTLE = """() => document.getAnimations().every(a => a.playState !== "running" || a.timeline !== document.timeline || a.effect?.getComputedTiming().endTime === Infinity || (a.effect?.target && !a.effect.target.checkVisibility?.({ contentVisibilityAuto: true })))"""

HYDRATED = """(sel) => {
  const el = document.querySelector(sel)
  if (!el) return false
  return [el, ...el.querySelectorAll("*")].some(e => Object.keys(e).some(k => k.startsWith("__reactProps")))
}"""


class StepError(Exception):
    pass


def scenario_names():
    return sorted(f.stem for f in SCENARIOS.glob("*.json"))


def load_scenario(name):
    sc = json.loads((SCENARIOS / f"{name}.json").read_text())
    sc["name"] = name
    return sc


def scenario_hash(sc):
    body = {k: v for k, v in sc.items() if k not in ("name", "allowed", "note")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def run_key(engine, width, reduced_motion=False, rtl=False):
    key = f"{engine} {width}"
    if reduced_motion:
        key += " reduced-motion"
    if rtl:
        key += " rtl"
    return key


def parts_for(sc, side):
    out = {}
    for n, spec in sc.get("parts", {}).items():
        s = {k: v for k, v in spec.items() if k not in ("shadcn", "ours")}
        s.update(spec.get(side, {}))
        out[n] = s
    return out


def popups(sc):
    return [n for n, s in sc.get("parts", {}).items() if s.get("popup")]


def anchor_name(sc):
    if "anchor" in sc:
        return sc["anchor"]
    return "trigger" if "trigger" in sc.get("parts", {}) else None


def positions(sc):
    if "positions" in sc:
        return sc["positions"]
    a = anchor_name(sc)
    return [[p, a] for p in popups(sc)] if a else []


def install(page, sc, side, root):
    err = page.evaluate(HELPERS, {"root": root, "rootNth": 0, "parts": parts_for(sc, side)})
    if err:
        raise StepError(err)
    page.evaluate("p => { window.__bh.positions = p }", positions(sc))


def anchor_rect(page, sc):
    return page.evaluate(
        """n => {
          const bh = window.__bh
          const el = (n && bh.find(n)) || bh.root
          const r = el.getBoundingClientRect()
          return [Math.round(r.left * 10) / 10, Math.round(r.top * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]
        }""",
        anchor_name(sc),
    )


def place_anchor(page, sc, target_x=None):
    if target_x is not None:
        page.evaluate(
            """([n, x]) => {
              const bh = window.__bh
              const el = (n && bh.find(n)) || bh.root
              const stage = document.querySelector("[data-behavior=stage]") || bh.root
              stage.style.position = "relative"
              stage.style.left = "0px"
              const r = el.getBoundingClientRect()
              stage.style.left = `${Math.round((x - r.left) * 10) / 10}px`
            }""",
            [anchor_name(sc), target_x],
        )
    y = sc.get("anchorY", ANCHOR_Y)
    page.evaluate(
        """([n, y]) => {
          const bh = window.__bh
          const el = (n && bh.find(n)) || bh.root
          const html = document.documentElement
          const prev = html.style.scrollBehavior
          html.style.scrollBehavior = "auto"
          const r = el.getBoundingClientRect()
          scrollTo(0, Math.max(0, r.top + r.height / 2 + scrollY - y))
          html.style.scrollBehavior = prev
        }""",
        [anchor_name(sc), y],
    )
    page.wait_for_timeout(120)
    page.evaluate("() => { const bh = window.__bh; bh.scroll0 = Math.round(scrollY) }")


SCROLLED = """async (wait) => {
  if (wait) await new Promise(r => setTimeout(r, wait))
  const pos = () => {
    const bh = window.__bh
    const r = bh && bh.root
    let v = `${scrollX},${scrollY}`
    if (r) for (const e of [r, ...r.querySelectorAll("*")]) if (e.scrollTop || e.scrollLeft) v += `|${e.scrollTop},${e.scrollLeft}`
    if (bh) for (const n of Object.keys(bh.specs)) { const e = bh.find(n); if (e) { const b = e.getBoundingClientRect(); v += `|${Math.round(b.left)},${Math.round(b.top)},${Math.round(b.width)},${Math.round(b.height)}` } }
    return v
  }
  let last = pos(), same = 0
  for (let i = 0; i < 40 && same < (wait ? 4 : 3); i++) {
    await new Promise(r => setTimeout(r, wait ? 50 : 40))
    const v = pos()
    same = v === last ? same + 1 : 0
    last = v
  }
}"""


SCROLL_KEYS = re.compile(r"^(Shift\+)?(ArrowUp|ArrowDown|ArrowLeft|ArrowRight|PageUp|PageDown|Home|End|Space| )$")


def settle(page, timeout=2500, scroll_wait=0):
    try:
        page.wait_for_function(SETTLE, timeout=timeout, polling=50)
    except PlaywrightError:
        pass
    try:
        page.evaluate(SCROLLED, scroll_wait)
    except PlaywrightError:
        pass


def point(page, target, at=None):
    box = page.evaluate(
        """([n, at]) => {
          const el = window.__bh.find(n)
          if (!el) return null
          let r = el.getBoundingClientRect()
          if (r.top < 0 || r.left < 0 || r.bottom > innerHeight || r.right > innerWidth) {
            el.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "instant" })
            r = el.getBoundingClientRect()
          }
          const fx = at ? at[0] : 0.5, fy = at ? at[1] : 0.5
          return [r.left + r.width * fx, r.top + r.height * fy]
        }""",
        [target, at],
    )
    if box is None:
        raise StepError(f"target not found: {target}")
    return box


def outside(page):
    p = page.evaluate("() => window.__bh.outside()")
    if p is None:
        raise StepError("no free point outside the component")
    return p


def touch(page, x, y, dx, dy, n, interval):
    cdp = page.context.new_cdp_session(page)
    length = math.hypot(dx, dy) or 1
    dx, dy = dx * (1 + TOUCH_SLOP / length), dy * (1 + TOUCH_SLOP / length)
    try:
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
        start, i = time.monotonic(), 0
        while i < n:
            i = min(n, max(i + 1, int((time.monotonic() - start) * 1000 / interval)))
            time.sleep(max(0, start + i * interval / 1000 - time.monotonic()))
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + dx * i / n, "y": y + dy * i / n}]})
        time.sleep(max(0, start + (n * interval + 100) / 1000 - time.monotonic()))
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    finally:
        cdp.detach()


def by_width(page, value):
    if isinstance(value, dict):
        return value.get(str(page.viewport_size["width"]), value.get("default"))
    return value


def act(page, step, engine):
    kind = step["do"]
    times = step.get("times", 1)
    if kind == "tab_in":
        page.evaluate("() => { const r = window.__bh.root; r.__bhTab = !r.hasAttribute('tabindex'); if (r.__bhTab) r.tabIndex = -1; r.focus({ preventScroll: true }) }")
        page.keyboard.press("Tab")
        page.evaluate("() => { const r = window.__bh.root; if (r.__bhTab) r.removeAttribute('tabindex') }")
    elif kind == "focus":
        if not page.evaluate("n => { const el = window.__bh.find(n); if (!el) return false; el.focus({ preventScroll: true }); return true }", step["target"]):
            raise StepError(f"target not found: {step['target']}")
    elif kind == "tab":
        for _ in range(times):
            page.keyboard.press("Tab")
    elif kind == "shift_tab":
        for _ in range(times):
            page.keyboard.press("Shift+Tab")
    elif kind == "press":
        for _ in range(times):
            page.keyboard.press(step["key"])
    elif kind == "type":
        page.keyboard.type(step["text"], delay=step.get("delay", 50))
    elif kind in ("click", "right_click", "dblclick"):
        x, y = point(page, step["target"], step.get("at"))
        page.mouse.move(x, y)
        if kind == "dblclick":
            page.mouse.dblclick(x, y)
        else:
            page.mouse.click(x, y, button="right" if kind == "right_click" else "left")
    elif kind == "hover":
        x, y = point(page, step["target"], step.get("at"))
        page.mouse.move(x, y, steps=step.get("steps", 1))
    elif kind == "press_hold":
        x, y = point(page, step["target"], step.get("at"))
        page.mouse.move(x, y)
        page.mouse.down()
        page.wait_for_timeout(step.get("hold", 200))
        page.mouse.up()
    elif kind == "click_outside":
        x, y = outside(page)
        page.mouse.click(x, y)
    elif kind == "leave":
        x, y = outside(page)
        page.mouse.move(x, y, steps=step.get("steps", 4))
    elif kind in ("drag", "swipe"):
        x, y = point(page, step["target"], step.get("at"))
        dx, dy = by_width(page, step.get("by", [0, 0]))
        vw, vh = page.viewport_size["width"], page.viewport_size["height"]
        dx = min(max(x + dx, 1), vw - 1) - x
        dy = min(max(y + dy, 1), vh - 1) - y
        n = step.get("steps", 10)
        interval = step.get("interval", 16)
        if kind == "swipe" and engine == "chromium":
            touch(page, x, y, dx, dy, n, interval)
        else:
            page.mouse.move(x, y)
            page.mouse.down()
            for i in range(1, n + 1):
                page.wait_for_timeout(interval)
                page.mouse.move(x + dx * i / n, y + dy * i / n)
            if step.get("hold"):
                page.wait_for_timeout(step["hold"])
            page.mouse.up()
    elif kind == "wheel":
        x, y = point(page, step["target"], step.get("at"))
        page.mouse.move(x, y)
        dx, dy = step.get("by", [0, 200])
        page.mouse.wheel(dx, dy)
    elif kind == "blur":
        page.evaluate("() => { const f = document.activeElement; if (f && f !== document.body) f.blur() }")
    elif kind == "wait":
        page.wait_for_timeout(step.get("ms", 300))
    else:
        raise StepError(f"unknown step: {kind}")


def label(step):
    kind = step["do"]
    bits = [kind]
    for k in ("key", "target"):
        if k in step:
            bits.append(str(step[k]))
    if "text" in step:
        bits.append(repr(step["text"]))
    if step.get("times", 1) > 1:
        bits.append(f"x{step['times']}")
    if "by" in step:
        by = step["by"]
        bits.append(f"by {by.get('default', by) if isinstance(by, dict) else by}")
    return step.get("label") or " ".join(bits)


def aria(page, sel):
    loc = page.locator(sel)
    try:
        if loc.count() == 0:
            return None
        return loc.first.aria_snapshot(timeout=3000)
    except PlaywrightError:
        return None


ARIA_DROP = re.compile(r"^(/url|/children)\b")


def aria_lines(snap):
    out = []
    names = []
    for line in (snap or "").splitlines():
        s = line.strip()
        if not s:
            continue
        depth = (len(line) - len(line.lstrip())) // 2
        names = names[:depth]
        s = s.removeprefix("- ").strip()
        if ARIA_DROP.match(s):
            continue
        s = re.sub(r"\s+", " ", s).rstrip(":").strip()
        m = re.match(r'^[\w-]+ "((?:[^"\\]|\\.)*)"', s)
        names.append(m.group(1) if m else None)
        if s in ("generic", "none", "presentation", "img", ""):
            continue
        t = re.match(r"^text: (.*)$", s)
        if t and any(n is not None and n.strip() == t.group(1).strip() for n in names[:-1]):
            continue
        out.append(s)
    return out


def remove_block(lines, block):
    n = len(block)
    if not n:
        return lines
    for i in range(len(lines) - n + 1):
        if lines[i:i + n] == block:
            return lines[:i] + lines[i + n:]
    return lines


WRAP = """parts => {
  const bh = window.__bh
  const quiet = c => c.getAttribute("aria-hidden") === "true" || !c.innerText.trim() && !c.matches("[aria-label], [aria-labelledby], [role]:not([role=presentation]):not([role=none]), button, a[href], input, select, textarea, img, svg[role]")
  for (const p of parts) {
    const el = bh.find(p)
    if (!el) continue
    const text = el.innerText.trim()
    let w = el
    while (w.parentElement && w.parentElement !== bh.root && w.parentElement !== document.body && !w.parentElement.contains(bh.root) && w.parentElement.innerText.trim() === text && [...w.parentElement.children].every(c => c === w || quiet(c))) w = w.parentElement
    if (w !== el) w.setAttribute("data-bh-wrap", p)
  }
}"""


GUARDS = "[data-base-ui-focus-guard]:not([aria-hidden]), [data-floating-ui-focus-guard]:not([aria-hidden])"


def observe(page, sc):
    obs = page.evaluate(OBSERVE, [STATE_ATTRS, PRESENCE_ATTRS])
    page.evaluate("s => { for (const e of document.querySelectorAll(s)) { e.setAttribute('aria-hidden', 'true'); e.setAttribute('data-bh-guard', '') } }", GUARDS)
    root = aria_lines(aria(page, "[data-bh-root]"))
    modal = obs.pop("modalOutside", False)
    blocks = {}
    for p in popups(sc):
        if obs["parts"].get(p) and sc["parts"][p].get("aria", True):
            blocks[p] = aria_lines(aria(page, f'[data-bh-part~="{p}"]'))
    page.evaluate(WRAP, list(blocks))
    for p in sorted(blocks, key=lambda p: -len(blocks[p])):
        wrap = aria_lines(aria(page, f'[data-bh-wrap="{p}"]'))
        cut = remove_block(root, wrap) if wrap else root
        root = cut if cut is not root else remove_block(root, blocks[p])
    for p, b in blocks.items():
        for q, c in blocks.items():
            if q != p and len(c) < len(b):
                b = remove_block(b, c)
        blocks[p] = b
    if modal:
        root = []
    obs["aria"] = {"root": root, **{p: blocks[p] for p in sorted(blocks)}}
    if obs.get("focus") and obs["focus"].get("role") != "generic":
        snap = aria(page, "[data-bh-focus]")
        first = (snap or "").splitlines()[0].strip() if snap else ""
        m = re.match(r'^- (\w+)(?: "((?:[^"\\]|\\.)*)")?', first)
        if m:
            obs["focus"]["role"] = m.group(1)
            obs["focus"]["name"] = (m.group(2) or "").replace('\\"', '"')[:80]
    page.evaluate("() => { for (const e of document.querySelectorAll('[data-bh-guard]')) { e.removeAttribute('aria-hidden'); e.removeAttribute('data-bh-guard') } for (const e of document.querySelectorAll('[data-bh-part],[data-bh-focus],[data-bh-wrap]')) { e.removeAttribute('data-bh-part'); e.removeAttribute('data-bh-focus'); e.removeAttribute('data-bh-wrap') } }")
    return obs


def run_step(page, step, engine):
    motion = None
    parts = step.get("motion")
    if parts:
        parts = parts if isinstance(parts, list) else [parts]
        page.evaluate(MOTION, {"parts": parts, "ms": step.get("ms", 800)})
        page.evaluate("() => { window.__bh.tb = performance.now() }")
        act(page, step, engine)
        motion = page.evaluate("() => window.__bh.motion")
        motion["tb"] = page.evaluate("() => window.__bh.tb")
    else:
        act(page, step, engine)
        if step.get("after"):
            page.wait_for_timeout(step["after"])
    settle(page, scroll_wait=150 if step["do"] == "press" and SCROLL_KEYS.match(step.get("key", "")) else 0)
    page.wait_for_timeout(step.get("pause", 120))
    return motion


def motion_summary(raw, part):
    if not raw:
        return None
    ta = raw.get("ta") or raw.get("tb") or raw["t0"]
    dom = [(e["t"] - ta, e["s"]) for e in raw.get("dom", []) if e["p"] == part]
    init = dom[0][1] if dom else "absent"
    was = init.startswith("shown")
    out = {"input": raw.get("taType") or "none", "before": init.split(" ")[0]}
    after = [(t, s) for t, s in dom[1:]]
    if not was:
        shown = next((t for t, s in after if s.startswith("shown")), None)
        if shown is not None:
            out["dom_open"] = round(shown)
    else:
        change = next((t for t, s in after if s != init), None)
        gone = next((t for t, s in after if not s.startswith("shown")), None)
        if change is not None:
            out["dom_close"] = round(change)
        if gone is not None:
            out["dom_gone"] = round(gone)
    rows = []
    for f in raw["frames"]:
        t = f["t"] - ta
        rows.append((t, f["els"].get(part)))
    pre = [v for t, v in rows if t < 0]
    base = pre[-1] if pre else (rows[0][1] if rows else None)
    post = [(t, v) for t, v in rows if t >= 0]
    gaps = [b[0] - a[0] for a, b in zip(post, post[1:])]
    out["max_frame_gap"] = round(max(gaps)) if gaps else 0

    def visible(v):
        return v is not None and v[0] > 0.01 and v[3] > 0 and v[4] > 0

    def differs(a, b):
        if visible(a) != visible(b):
            return True
        if not visible(a):
            return False
        return abs(a[0] - b[0]) > 0.005 or any(abs(a[i] - b[i]) > 0.25 for i in range(1, 5))

    prev = base
    first = last = None
    for t, v in post:
        if differs(v, prev):
            if first is None:
                first = t
            last = t
        prev = v
    if first is not None:
        out["paint_start"] = round(first)
        out["paint_end"] = round(last)
    vis_t = next((t for t, v in post if visible(v)), None) if not visible(base) else None
    hid_t = next((t for t, v in post if not visible(v)), None) if visible(base) else None
    if vis_t is not None:
        out["paint_open"] = round(vis_t)
    if hid_t is not None:
        out["paint_close"] = round(hid_t)
    final = post[-1][1] if post else None
    out["end"] = {"visible": visible(final), "opacity": final[0] if final else None, "size": [final[3], final[4]] if final else None}
    anims = [a for a in (raw.get("anims") or {}).get(part, []) if a.get("duration", 0) > 0]
    out["animations"] = sorted(({"name": a["name"], "duration": a["duration"], "delay": a["delay"], "easing": a["easing"]} for a in anims), key=lambda a: a["name"])
    return out


def live_dates(page, sc):
    spec = sc.get("dates") or {}
    return page.evaluate(
        """q => { const r = window.__bh.root; const o = {}; for (const [k, sel] of Object.entries(q)) { const e = r.querySelector(sel); o[k] = e ? e.getAttribute("data-day") : null } return o }""",
        spec.get("read", {}),
    )


def set_dates(page, sc, dates):
    spec = sc.get("dates") or {}
    page.evaluate(
        """([target, attrs, dates]) => { const t = window.__bh.root.querySelector(target); if (!t) return; for (const [k, a] of Object.entries(attrs)) if (dates[k]) t.setAttribute(a, dates[k]) }""",
        [spec.get("target"), spec.get("write", {}), dates or {}],
    )
    page.wait_for_timeout(300)


def run_side(page, sc, side, engine, root, target_x=None, dates=None):
    install(page, sc, side, root)
    found = None
    if sc.get("dates"):
        if side == "shadcn":
            found = live_dates(page, sc)
        else:
            set_dates(page, sc, dates)
    place_anchor(page, sc, target_x)
    anchor = anchor_rect(page, sc)
    p = outside(page)
    page.mouse.move(*p)
    page.wait_for_timeout(150)
    rows = [{"label": "rest", "obs": observe(page, sc), "motion": None, "error": None}]
    for step in sc["steps"]:
        row = {"label": label(step), "obs": None, "motion": None, "error": None}
        if step.get("engines") and engine not in step["engines"]:
            row["skipped"] = f"not in {engine}"
            rows.append(row)
            continue
        if step.get("widths") and page.viewport_size["width"] not in step["widths"]:
            row["skipped"] = f"not at {page.viewport_size['width']} px"
            rows.append(row)
            continue
        raw = None
        try:
            raw = run_step(page, step, engine)
        except StepError as e:
            row["error"] = str(e)
        except PlaywrightError as e:
            row["error"] = str(e).splitlines()[0]
        if raw:
            row["motion"] = {p: motion_summary(raw, p) for p in (step["motion"] if isinstance(step["motion"], list) else [step["motion"]])}
        try:
            row["obs"] = observe(page, sc)
        except PlaywrightError as e:
            row["error"] = (row["error"] or "") + " observe: " + str(e).splitlines()[0]
        rows.append(row)
    out = {"anchor": anchor, "rows": rows}
    if found is not None:
        out["dates"] = found
    return out


def step_kind(step):
    kind = step.get("do")
    if kind == "press":
        key = step.get("key", "")
        if key == "Escape":
            return "dismiss"
        if key in ("Tab", "Shift+Tab"):
            return "tab"
        return "key"
    if kind == "type":
        return "key"
    if kind in ("tab", "shift_tab", "tab_in", "focus"):
        return "tab"
    if kind in ("click_outside", "leave"):
        return "dismiss"
    return "pointer"


def diff(step, what, ref, ours, cls, sev, note=None):
    return {"step": step, "what": what, "shadcn": ref, "ours": ours, "class": cls, "severity": sev, "note": note}


def fdesc(f):
    if not f or f.get("part") == "outside":
        return "outside the component"
    s = f.get("role") or "?"
    if f.get("name"):
        s += f' "{f["name"][:48]}"'
    if f.get("slot"):
        s += f" [{f['slot']}]"
    if f.get("part") and f.get("part") != "root":
        s += f" in {f['part']}"
    return s


def same_focus(a, b):
    oa = a is None or a.get("part") == "outside"
    ob = b is None or b.get("part") == "outside"
    if oa or ob:
        return oa == ob
    return a.get("role") == b.get("role") and a.get("name") == b.get("name") and bool(a.get("popup")) == bool(b.get("popup"))


def slot_ok(ref, ours):
    s = ref.get("slot")
    if not s:
        return True
    return ours.get("slot") == s or s in (ours.get("markers") or [])


CANON = {
    "open": [("data-open", None, "open"), ("data-closed", None, "closed"), ("data-popup-open", None, "open"), ("data-panel-open", None, "open"), ("data-state", "open", "open"), ("data-state", "closed", "closed")],
    "checked": [("data-checked", None, "checked"), ("data-unchecked", None, "unchecked"), ("data-indeterminate", None, "mixed"), ("data-state", "checked", "checked"), ("data-state", "unchecked", "unchecked"), ("data-state", "indeterminate", "mixed")],
    "pressed": [("data-state", "on", "on"), ("data-state", "off", "off")],
    "active": [("data-active", None, "active"), ("data-selected", None, "active"), ("data-state", "active", "active"), ("data-state", "inactive", "inactive")],
}
CANON_ATTRS = {a for rules in CANON.values() for a, _, _ in rules if a != "data-state"}
ORIENTATION = {"tablist": "horizontal", "menubar": "horizontal", "toolbar": "horizontal", "slider": "horizontal", "separator": "horizontal", "menu": "vertical", "listbox": "vertical", "radiogroup": None, "tree": "vertical", "scrollbar": "vertical"}
ARIA_VISIBLE = {"aria-expanded", "aria-selected", "aria-checked", "aria-pressed", "aria-haspopup", "aria-modal", "aria-disabled", "aria-valuenow", "aria-orientation", "aria-current", "aria-hidden", "role", "aria-autocomplete", "aria-multiselectable"}
DEFAULT_FALSE = {"aria-selected", "aria-pressed", "aria-disabled", "aria-invalid", "aria-readonly", "aria-required", "aria-hidden", "aria-modal"}


NEGATIVE = {"closed", "unchecked", "off", "inactive"}


def canon(state):
    out = {}
    for key, rules in CANON.items():
        for attr, val, res in rules:
            if attr in state and (val is None or state[attr] == val):
                if res not in NEGATIVE:
                    out[key] = (res, attr)
                break
    return out


def norm_attr(k, v, role=None):
    if v is None:
        return None
    if k in DEFAULT_FALSE and v == "false":
        return None
    if k == "aria-autocomplete" and v == "none":
        return None
    if k == "aria-orientation" and role in ORIENTATION and v == ORIENTATION[role]:
        return None
    if k == "disabled" or k == "hidden" or k == "inert":
        return "" if v is not None else None
    return v


INTERACTIVE_ROLE = re.compile(r"^(button|checkbox|combobox|link|listbox|menu|menubar|menuitem|menuitemcheckbox|menuitemradio|option|radio|radiogroup|slider|spinbutton|switch|tab|tablist|tabpanel|textbox|searchbox|dialog|alertdialog|tooltip|tree|treeitem|grid|gridcell|row|navigation|region|separator|group|toolbar|progressbar|status|alert|log)\b")


def scroll_dir(o, before):
    d = (o.get("scroll") or 0) - ((before or {}).get("scroll") or 0)
    return "down" if d > 2 else "up" if d < -2 else "none"


def compare_obs(lbl, step, a, b, sc, prev=(None, None)):
    out = []
    if a is None or b is None:
        return out
    kind = step_kind(step) if step else "rest"
    pops = popups(sc)
    fcls = "keyboard" if kind == "key" else "focus"
    fa, fb = a.get("focus"), b.get("focus")
    named = aria_name_rules(sc)
    if fa and fb and fa.get("role") == fb.get("role") and fa.get("role") in named and not fa.get("name") and fb.get("name") and fa.get("part") == fb.get("part"):
        out.append(dict(diff(lbl, f"accessible name on the focused {fa['role']}", "none", fb["name"], "ARIA", "minor"), allowed=named[fa["role"]]))
        fb = dict(fb, name="")
    if not same_focus(fa, fb):
        lost = (fb is None or fb.get("part") == "outside") and fa and fa.get("part") != "outside"
        into = fa and fa.get("popup") and not (fb and fb.get("popup"))
        out.append(diff(lbl, "focus", fdesc(fa), fdesc(fb), fcls, "broken" if lost or into else "visible"))
    elif fa and fb and fa.get("part") != "outside":
        if not slot_ok(fa, fb):
            out.append(diff(lbl, "focused data-slot", str(fa.get("slot")), str(fb.get("slot")), fcls, "minor"))
        if fa.get("ring") != fb.get("ring"):
            out.append(diff(lbl, "focus ring", "painted" if fa.get("ring") else "none", "painted" if fb.get("ring") else "none", "focus", "visible", "outline or box-shadow ring on the focused element"))
        elif fa.get("visible") != fb.get("visible"):
            out.append(diff(lbl, ":focus-visible", "matches" if fa.get("visible") else "no match", "matches" if fb.get("visible") else "no match", "focus", "minor"))
    for key in ("highlight", "active"):
        ha, hb = a.get(key), b.get(key)
        if bool(ha) != bool(hb) or (ha and hb and (ha.get("name") != hb.get("name") or ha.get("role") != hb.get("role"))):
            note = "ours points at the selected option" if key == "active" and hb and b.get("selected") and hb.get("name") == b["selected"].get("name") else None
            out.append(diff(lbl, "highlighted item" if key == "highlight" else "aria-activedescendant", fdesc(ha) if ha else "none", fdesc(hb) if hb else "none", "keyboard" if kind == "key" else "state", "visible", note))
    scls = "keyboard" if kind == "key" else "dismiss" if kind == "dismiss" else "state"
    for n in sc.get("parts", {}):
        pa, pb = a["parts"].get(n), b["parts"].get(n)
        if bool(pa) != bool(pb):
            if n in pops:
                out.append(diff(lbl, f"{n} open", "open" if pa else "closed", "open" if pb else "closed", scls, "broken"))
            elif not sc["parts"][n].get("optional"):
                out.append(diff(lbl, f"{n} shown", "yes" if pa else "no", "yes" if pb else "no", scls, "visible", "the part is visible on one side only"))
            continue
        if not pa:
            continue
        sa, sb = pa["state"], pb["state"]
        ca, cb = canon(sa), canon(sb)
        for k in sorted(set(ca) | set(cb)):
            va, vb = ca.get(k, (None, None)), cb.get(k, (None, None))
            if va[0] == vb[0]:
                continue
            if va[0] is None and vb[1] == "data-state":
                continue
            out.append(diff(lbl, f"{n} {k} state", va[0] or "none", vb[0] or "none", scls, "visible" if va[0] else "minor", None if va[0] else "Base UI does not set this state here"))
        for k in STATE_ATTRS + PRESENCE_ATTRS:
            if k in ("role", "data-highlighted") or k in CANON_ATTRS:
                continue
            va, vb = norm_attr(k, sa.get(k), sa.get("role")), norm_attr(k, sb.get(k), sb.get("role"))
            if va == vb or k == "aria-hidden":
                continue
            if k.startswith("aria-"):
                sev = "visible" if k in ARIA_VISIBLE else "minor"
                out.append(diff(lbl, f"{n} {k}", str(va), str(vb), "ARIA", sev))
            elif k == "tabindex":
                out.append(diff(lbl, f"{n} tabindex", str(va), str(vb), "focus", "minor"))
            elif k in ("disabled", "hidden", "inert", "data-state"):
                continue
            else:
                out.append(diff(lbl, f"{n} {k}", "absent" if va is None else repr(va), "absent" if vb is None else repr(vb), scls, "minor", "Base UI state attribute"))
        spec = sc["parts"][n]
        px = TOLERANCE["px"]
        axes = {"width": [2], "height": [3]}.get(spec.get("size"), [2, 3]) if spec.get("size") else []
        if axes and any(abs(pa["rect"][i] - pb["rect"][i]) > px for i in axes):
            d = max(abs(pa["rect"][i] - pb["rect"][i]) for i in axes)
            out.append(diff(lbl, f"{n} {spec['size'] if isinstance(spec['size'], str) else 'size'}", "x".join(f"{pa['rect'][i]:g}" for i in axes), "x".join(f"{pb['rect'][i]:g}" for i in axes), "geometry", "visible" if d > 4 else "minor"))
        if spec.get("edges") and pa.get("edges") and pb.get("edges") and any(abs(x - y) > px for x, y in zip(pa["edges"], pb["edges"])):
            d = max(abs(x - y) for x, y in zip(pa["edges"], pb["edges"]))
            fmt = lambda e: f"left {e[0]:g}, top {e[1]:g}, right {e[2]:g}, bottom {e[3]:g}"
            out.append(diff(lbl, f"{n} distance to the viewport edges", fmt(pa["edges"]), fmt(pb["edges"]), "geometry", "visible" if d > 4 else "minor"))
        if spec.get("scroll") and pa.get("scroll") is not None and pb.get("scroll") is not None and any(abs(x - y) > px + 1 for x, y in zip(pa["scroll"], pb["scroll"])):
            out.append(diff(lbl, f"{n} scroll position", f"{pa['scroll'][0]}, {pa['scroll'][1]} px", f"{pb['scroll'][0]}, {pb['scroll'][1]} px", "keyboard" if kind == "key" else "state", "visible", "scrollLeft, scrollTop"))
        if pa.get("blocked") != pb.get("blocked"):
            out.append(diff(lbl, f"{n} hidden from assistive tech", "yes" if pa["blocked"] else "no", "yes" if pb["blocked"] else "no", "ARIA", "visible", "inert, aria-hidden, or outside a modal dialog"))
        if (pa.get("description") or None) != (pb.get("description") or None):
            out.append(diff(lbl, f"{n} accessible description", str(pa.get("description")), str(pb.get("description")), "ARIA", "visible"))
    if a.get("lock") != b.get("lock"):
        out.append(diff(lbl, "page scroll lock", "locked" if a["lock"] else "free", "locked" if b["lock"] else "free", "dismiss" if kind == "dismiss" else "state", "visible", f"shadcn {a.get('overflow')}; ours {b.get('overflow')}"))
    da, db = scroll_dir(a, prev[0]), scroll_dir(b, prev[1])
    elsewhere = any(o and (o.get("focus") or {}).get("part") == "outside" for o in (a, b, prev[0], prev[1]))
    if da != db and not elsewhere:
        out.append(diff(lbl, "page scroll", da, db, "keyboard" if kind == "key" else "state", "visible", "direction of the page scroll in this step"))
    fa_, fb_ = [x for x in a.get("form", []) if not x.get("disabled")], [x for x in b.get("form", []) if not x.get("disabled")]
    va_, vb_ = [f"{x['type']}={x['value']}" for x in fa_], [f"{x['type']}={x['value']}" for x in fb_]
    if va_ != vb_:
        out.append(diff(lbl, "form value", ", ".join(va_) or "none", ", ".join(vb_) or "none", "keyboard" if kind == "key" else "state", "visible", "values of the form controls (hidden inputs included)"))
    for p in sorted(set(a.get("place", {})) | set(b.get("place", {}))):
        pa, pb = a.get("place", {}).get(p), b.get("place", {}).get(p)
        if not pa or not pb:
            continue
        out += compare_place(lbl, p, pa, pb)
    for key in sorted(set(a.get("aria", {})) | set(b.get("aria", {}))):
        la, lb = split_inline(a.get("aria", {}).get(key) or []), split_inline(b.get("aria", {}).get(key) or [])
        la, lb, eased = aria_rules(sc, la, lb)
        for what, reason in eased:
            out.append(dict(diff(lbl, f"{what} ({key})", "-", "-", "ARIA", "minor"), allowed=reason))
        if la == lb:
            continue
        d = [x for x in difflib.ndiff(la, lb) if x[:1] in "-+"]
        if not d:
            continue
        sev = "visible" if any(INTERACTIVE_ROLE.match(x[2:]) or re.search(r"\[(expanded|checked|selected|pressed|disabled|level=\d+)", x) for x in d) else "minor"
        if sorted(la) == sorted(lb):
            sev = "minor"
        text = ("same nodes in another order: " if sorted(la) == sorted(lb) else "") + "; ".join(("shadcn only: " if x[0] == "-" else "ours only: ") + x[2:] for x in d[:10])
        if len(d) > 10:
            text += f"; {len(d) - 10} more"
        out.append(diff(lbl, f"ARIA tree ({key})", f"{len(la)} nodes", f"{len(lb)} nodes", "ARIA", sev, text))
    return out


INLINE = re.compile(r'^([a-z][\w-]*(?: "(?:[^"\\]|\\.)*")?(?: \[[^\]]*\])*): (.+)$')


LINE = re.compile(r'^([a-z][\w-]*)(?: "((?:[^"\\]|\\.)*)")?(.*)$')


def aria_name_rules(sc):
    return {a["aria_name"]: a["reason"] for a in sc.get("allowed", []) if "aria_name" in a}


def aria_rules(sc, la, lb):
    names = aria_name_rules(sc)
    roles = {a["aria_role"]: a["reason"] for a in sc.get("allowed", []) if "aria_role" in a}
    eased = []
    if not names and not roles:
        return la, lb, eased
    ref_names = {(m.group(1), m.group(2)) for m in map(LINE.match, la) if m and m.group(2) is not None}
    ref_roles = {m.group(1) for m in map(LINE.match, la) if m}
    out = []
    for line in lb:
        m = LINE.match(line)
        if m and m.group(1) in roles and m.group(1) not in ref_roles:
            eased.append((f"extra {m.group(1)} role", roles[m.group(1)]))
            continue
        if m and m.group(1) in names and m.group(2) is not None and (m.group(1), m.group(2)) not in ref_names:
            eased.append((f"accessible name on {m.group(1)}", names[m.group(1)]))
            out.append(m.group(1) + m.group(3))
            continue
        out.append(line)
    return la, out, sorted(set(eased))


def split_inline(lines):
    out = []
    for line in lines:
        m = INLINE.match(line)
        if m and not line.startswith("text:"):
            out += [m.group(1), "text: " + m.group(2).strip('"')]
        else:
            out.append(line)
    return out


def compare_place(lbl, p, pa, pb):
    out = []
    px = TOLERANCE["px"]
    if pa["side"] != pb["side"]:
        return [diff(lbl, f"{p} side", pa["side"], pb["side"], "geometry", "visible")]
    if pa["side"] == "overlap":
        d = max(abs(pa["dx"] - pb["dx"]), abs(pa["dy"] - pb["dy"]))
        if d > px:
            note = "center of the part relative to the top-left corner of the anchor" if pa.get("center") else "top-left corner of the part relative to the top-left corner of the anchor"
            out.append(diff(lbl, f"{p} position", f"{pa['dx']:+}, {pa['dy']:+} px", f"{pb['dx']:+}, {pb['dy']:+} px", "geometry", "visible" if d > 4 else "minor", note))
        return out
    if pa["align"] != pb["align"] and abs(pa["alignOffset"] - pb["alignOffset"]) > px:
        out.append(diff(lbl, f"{p} align", f"{pa['align']} {pa['alignOffset']:+} px", f"{pb['align']} {pb['alignOffset']:+} px", "geometry", "visible"))
    elif abs(pa["alignOffset"] - pb["alignOffset"]) > px:
        d = abs(pa["alignOffset"] - pb["alignOffset"])
        out.append(diff(lbl, f"{p} align offset", f"{pa['align']} {pa['alignOffset']:+} px", f"{pb['align']} {pb['alignOffset']:+} px", "geometry", "visible" if d > 4 else "minor"))
    d = abs(pa["offset"] - pb["offset"])
    if d > px:
        out.append(diff(lbl, f"{p} offset from the trigger", f"{pa['side']} {pa['offset']} px", f"{pb['side']} {pb['offset']} px", "geometry", "visible" if d > 4 else "minor"))
    return out


def fmt_anim(a):
    return f"{a['name']} {a['duration']} ms" + (f" +{a['delay']} ms" if a.get("delay") else "") + (f" {a['easing']}" if a.get("easing") and a["easing"] != "ease" else "")


MOVING = re.compile(r"^(opacity|transform|scale|translate|rotate|width|height|top|left|right|bottom|inset|clip-path|filter|display|overlay|visibility|max-height|max-width|margin|padding|all)$")


def painted(st):
    if st.get("paint_start") is None:
        return []
    moved = st.get("paint_end") != st["paint_start"]
    return [a for a in st.get("animations") or [] if not a["name"].startswith("transition ") or moved and MOVING.match(a["name"].removeprefix("transition "))]


def compare_motion(lbl, part, sa, sb, step=None):
    out = []
    if not sa or not sb:
        return out
    if (sa.get("before") == "shown") != (sb.get("before") == "shown"):
        return out
    ms = TOLERANCE["ms"]
    intent = bool(step) and (step.get("do") in INTENT or step.get("delays"))
    gesture = bool(step) and step.get("do") in ("drag", "swipe", "press_hold")
    exit_a = sa["dom_gone"] - sa["dom_close"] if sa.get("dom_gone") is not None and sa.get("dom_close") is not None else None
    exit_b = sb["dom_gone"] - sb["dom_close"] if sb.get("dom_gone") is not None and sb.get("dom_close") is not None else None
    stays = bool((sa.get("end") or {}).get("visible")) and bool((sb.get("end") or {}).get("visible"))
    for key, name, note in (("dom_open", "open delay", "time from the input event to the DOM change"), ("dom_close", "state change delay" if stays else "close delay", "time from the input event to the first state change"), ("dom_gone", "exit length", "time from the first state change until the part is hidden or removed")):
        va, vb = (exit_a, exit_b) if key == "dom_gone" else (sa.get(key), sb.get(key))
        if va is None and vb is None:
            continue
        if key == "dom_gone" and (sa.get("animations") or sb.get("animations")):
            continue
        if gesture and key != "dom_gone" and va is not None and vb is not None:
            continue
        if va is None or vb is None:
            if key == "dom_gone":
                continue
            out.append(diff(lbl, f"{part} {name}", "no change" if va is None else f"{va} ms", "no change" if vb is None else f"{vb} ms", "timing", "visible", note))
            continue
        if key != "dom_gone" and not intent and vb - va <= ms + 2 * FRAME:
            continue
        if abs(va - vb) > ms + 2 * FRAME:
            out.append(diff(lbl, f"{part} {name}", f"{va} ms", f"{vb} ms", "timing", "visible", note))
    aa, ab = painted(sa), painted(sb)
    main_a = max(aa, key=lambda a: a["duration"] + a["delay"]) if aa else None
    main_b = max(ab, key=lambda a: a["duration"] + a["delay"]) if ab else None
    if bool(main_a) != bool(main_b):
        out.append(diff(lbl, f"{part} animation", fmt_anim(main_a) if main_a else "none", fmt_anim(main_b) if main_b else "none", "timing", "visible"))
    elif main_a and main_b:
        d = abs(main_a["duration"] + main_a["delay"] - main_b["duration"] - main_b["delay"])
        if d > ms:
            out.append(diff(lbl, f"{part} animation duration", fmt_anim(main_a), fmt_anim(main_b), "timing", "visible" if d > 100 else "minor"))
        elif (main_a.get("easing") or "") != (main_b.get("easing") or ""):
            out.append(diff(lbl, f"{part} easing", str(main_a.get("easing")), str(main_b.get("easing")), "timing", "minor"))
    slack = max(0, max(sa.get("max_frame_gap", 0), sb.get("max_frame_gap", 0)) - FRAME)
    if not main_a and not main_b:
        for key, name in (("paint_start", "painted motion start"), ("paint_end", "painted motion end")):
            va, vb = sa.get(key), sb.get(key)
            if va is None and vb is None:
                continue
            if va is None or vb is None:
                out.append(diff(lbl, f"{part} {name}", "no motion" if va is None else f"{va} ms", "no motion" if vb is None else f"{vb} ms", "timing", "visible", "painted frames"))
            elif not intent and vb - va <= ms + 2 * FRAME + slack:
                continue
            elif abs(va - vb) > ms + 2 * FRAME + slack:
                out.append(diff(lbl, f"{part} {name}", f"{va} ms", f"{vb} ms", "timing", "visible" if abs(va - vb) > 100 else "minor", "painted frames; a dropped frame widens the tolerance"))
    ea, eb = sa.get("end") or {}, sb.get("end") or {}
    if ea.get("visible") != eb.get("visible"):
        out.append(diff(lbl, f"{part} end state", "shown" if ea.get("visible") else "hidden", "shown" if eb.get("visible") else "hidden", "timing", "visible", "last painted frame of the sample window"))
    elif ea.get("visible"):
        if ea.get("opacity") is not None and eb.get("opacity") is not None and abs(ea["opacity"] - eb["opacity"]) > TOLERANCE["opacity"]:
            out.append(diff(lbl, f"{part} end opacity", str(ea["opacity"]), str(eb["opacity"]), "timing", "visible"))
        if ea.get("size") and eb.get("size") and any(abs(x - y) > TOLERANCE["px"] for x, y in zip(ea["size"], eb["size"])):
            out.append(diff(lbl, f"{part} end size", "x".join(f"{v:g}" for v in ea["size"]), "x".join(f"{v:g}" for v in eb["size"]), "geometry", "visible" if any(abs(x - y) > 4 for x, y in zip(ea["size"], eb["size"])) else "minor", "last painted frame"))
    return out


def ran(rows, i):
    return next((r.get("obs") for r in reversed(rows[:i]) if not r.get("skipped")), None)


def compare(sc, ref_rows, our_rows, engine=None):
    found = []
    steps = [None] + sc["steps"]
    for i, (ra, rb) in enumerate(zip(ref_rows, our_rows)):
        step = steps[i] if i < len(steps) else None
        lbl = f"{i}. {ra['label']}"
        if ra.get("skipped") or rb.get("skipped"):
            continue
        if rb.get("error") and not ra.get("error"):
            found.append(diff(lbl, "step", "ok", rb["error"], "state", "broken", "the step could not run on our page"))
        found += compare_obs(lbl, step, ra.get("obs"), rb.get("obs"), sc, (ran(ref_rows, i), ran(our_rows, i)))
        for part in sorted(set(ra.get("motion") or {}) | set(rb.get("motion") or {})):
            found += compare_motion(lbl, part, (ra.get("motion") or {}).get(part), (rb.get("motion") or {}).get(part), step)
    if len(ref_rows) != len(our_rows):
        found.append(diff("-", "steps", str(len(ref_rows)), str(len(our_rows)), "state", "broken", "different number of recorded steps"))
    seen = {}
    out = []
    for f in found:
        if f.get("note") == "Base UI state attribute":
            key = (f["what"], "absent" if f["shadcn"] == "absent" else "set", "absent" if f["ours"] == "absent" else "set")
        elif f["what"].startswith("ARIA tree"):
            key = (f["what"], f["shadcn"], f["ours"], f.get("note"))
        elif f["class"] in ("timing", "geometry"):
            key = (f["what"], re.sub(r"-?\d+(\.\d+)?", "#", str(f["shadcn"])), re.sub(r"-?\d+(\.\d+)?", "#", str(f["ours"])))
        else:
            key = (f["what"], f["shadcn"], f["ours"])
        if key in seen:
            first = seen[key]
            first["also"].append(f["step"].split(".")[0])
            for side in ("shadcn", "ours"):
                vals = first[side].split(" or ")
                if f[side] not in vals:
                    first[side] = " or ".join(vals + [f[side]])
            continue
        f["also"] = []
        seen[key] = f
        out.append(f)
    for f in out:
        for a in sc.get("allowed", []):
            if "match" in a and ("steps" not in a or {step_no(f), *(int(x) for x in f["also"] if x.isdigit())} <= set(a["steps"])) and ("engines" not in a or engine in a["engines"]) and ("platforms" not in a or sys.platform in a["platforms"]) and re.search(a["match"], f"{f['what']} | {f['shadcn']} | {f['ours']} | {f.get('note') or ''}"):
                f["allowed"] = a["reason"]
                break
    first = first_divergence(out)
    for f in out:
        n = step_no(f)
        f["first"] = first is not None and n == first and failing(f)
        f["after_first"] = first is not None and n > first
    return out


def step_no(f):
    head = f["step"].split(".")[0]
    return int(head) if head.isdigit() else 10 ** 6


def failing(f):
    return not f.get("allowed") and f["severity"] in ("broken", "visible")


def first_divergence(found):
    steps = [step_no(f) for f in found if failing(f)]
    return min(steps) if steps else None


def golden_path(name):
    return GOLDEN / f"{name}.json"


def load_golden(name):
    p = golden_path(name)
    return json.loads(p.read_text()) if p.exists() else None


def summary_line(f):
    also = f" (also steps {', '.join(f['also'][:8])})" if f.get("also") else ""
    if f.get("first"):
        also += " [first divergence]"
    note = f" [{f['note']}]" if f.get("note") else ""
    return f"{f['severity']} {f['class']}: step {f['step']}: {f['what']}: shadcn {f['shadcn']}; ours {f['ours']}{also}{note}"
