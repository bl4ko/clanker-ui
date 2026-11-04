(() => {
  const RULES = ["button-size-mismatch", "multiple-primary", "text-clipped", "horizontal-scroll", "small-target", "low-contrast", "non-token-color", "missing-label", "heading-order", "misaligned", "empty-region"]
  const TARGETS = 'a[href], button, input:not([type="hidden"]), select, textarea, summary, [role="button"], [role="link"], [role="checkbox"], [role="switch"], [role="radio"], [role="tab"], [role="menuitem"], [role="menuitemcheckbox"], [role="menuitemradio"], [role="option"], [role="slider"], [role="combobox"], [tabindex]:not([tabindex="-1"])'
  const CONTROLS = 'button, [role="button"], a[data-slot="button"], input:not([type="hidden"], [type="checkbox"], [type="radio"], [type="range"], [type="file"], [type="color"], [type="image"]), select, [data-slot="select-trigger"]'
  const NAMED = 'button, [role="button"], a[href], input:not([type="hidden"]), select, textarea, [role="checkbox"], [role="switch"], [role="radio"], [role="combobox"], [role="slider"], [role="tab"], [role="textbox"], [role="searchbox"], [role="spinbutton"], [role="menuitem"], [role="option"], img'
  const GROUPS = '[role="toolbar"], [data-slot="button-group"], [data-slot$="-footer"]'
  const REGIONS = 'dialog, [role="dialog"], [role="alertdialog"], [role="toolbar"], form, [data-slot$="-footer"], [data-slot="card"], [data-slot="button-group"], [data-slot="popover-content"]'
  const PRIMARY = '[data-slot="button"], [data-slot="alert-dialog-action"], [data-slot="questionnaire-next"], [data-slot="questionnaire-submit"]'
  const INSIDE = '[data-slot="input-group"], [data-slot="calendar"], [data-slot="input-otp"], [data-slot="toggle-group"], [data-slot="pagination"], [data-slot="tabs-list"], [data-slot="carousel"], [data-slot="combobox-chips"], [role="menu"], [role="listbox"], [role="tablist"], [role="radiogroup"], table'
  const colors = new Map()
  let ctx

  const num = s => (s.endsWith("%") ? parseFloat(s) / 100 : parseFloat(s))

  function rgba(str) {
    let v = colors.get(str)
    if (v) return v
    const legacy = /^rgba?\(([^)]*)\)$/.exec(str)
    if (legacy) {
      const p = legacy[1].split(/[\s,/]+/).filter(Boolean)
      v = [num(p[0]), num(p[1]), num(p[2]), p.length > 3 ? num(p[3]) : 1]
    } else if (str === "transparent") {
      v = [0, 0, 0, 0]
    } else {
      const a = /\/\s*([-\d.e]+%?)\s*\)$/.exec(str)
      ctx ??= Object.assign(document.createElement("canvas"), { width: 1, height: 1 }).getContext("2d", { willReadFrequently: true })
      ctx.clearRect(0, 0, 1, 1)
      ctx.fillStyle = "#000"
      ctx.fillStyle = a ? str.slice(0, a.index).trimEnd() + ")" : str
      ctx.fillRect(0, 0, 1, 1)
      const d = ctx.getImageData(0, 0, 1, 1).data
      v = [d[0], d[1], d[2], a ? num(a[1]) : d[3] / 255]
    }
    colors.set(str, v)
    return v
  }

  const over = (top, bottom) => {
    const a = top[3] + bottom[3] * (1 - top[3])
    if (!a) return [0, 0, 0, 0]
    return [0, 1, 2].map(i => (top[i] * top[3] + bottom[i] * bottom[3] * (1 - top[3])) / a).concat(a)
  }

  const luminance = c => {
    const [r, g, b] = c.slice(0, 3).map(v => {
      v /= 255
      return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
    })
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
  }

  const ratio = (a, b) => {
    const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p)
    return (x + 0.05) / (y + 0.05)
  }

  const hex = c => "#" + c.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, "0")).join("") + (c[3] < 1 ? ` at ${Math.round(c[3] * 100)}%` : "")

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
      if (e === document.body) break
    }
    return parts.join(" > ")
  }

  function lint(options = {}) {
    const root = options.root || document.body
    const only = new Set(options.rules || RULES)
    const ignore = Array.isArray(options.ignore) ? { "*": options.ignore } : options.ignore || {}
    const styles = new Map()
    const rects = new Map()
    const shown = new Map()
    const findings = []
    const cs = el => styles.get(el) || styles.set(el, getComputedStyle(el)).get(el)
    const box = el => rects.get(el) || rects.set(el, el.getBoundingClientRect()).get(el)
    const vis = el => {
      if (!shown.has(el)) {
        const r = box(el)
        shown.set(el, r.width >= 2 && r.height >= 2 && el.checkVisibility({ opacityProperty: true, visibilityProperty: true }))
      }
      return shown.get(el)
    }
    const skipped = (el, rule) => {
      const tag = el.closest("[data-lint-ignore]")
      if (tag && (!tag.dataset.lintIgnore.trim() || tag.dataset.lintIgnore.split(/\s+/).includes(rule))) return true
      return [...(ignore["*"] || []), ...(ignore[rule] || [])].some(s => el.closest(s))
    }
    const report = (rule, severity, el, message) => {
      if (only.has(rule) && !(el && skipped(el, rule))) findings.push({ rule, severity, selector: el ? sel(el) : "html", message })
    }
    const disabled = el => el.closest(':disabled, [aria-disabled="true"], [data-disabled]:not([data-disabled="false"]), [inert]')
    const all = [root, ...root.querySelectorAll("*")].filter(el => !el.closest("svg") || el.localName === "svg")
    const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.data.trim())
    const texts = all.filter(el => ownText(el) && vis(el) && !/^(script|style|template|noscript|option|textarea|select|title)$/.test(el.localName))
    const targets = all.filter(el => el.matches(TARGETS) && vis(el) && !disabled(el) && !el.closest('[aria-hidden="true"]'))
    const run = (rule, fn) => only.has(rule) && fn()

    run("button-size-mismatch", () => {
      const groups = new Map()
      for (const el of all) {
        if (!el.matches(CONTROLS) || !vis(el) || /absolute|fixed/.test(cs(el).position) || el.parentElement.closest(INSIDE)) continue
        let item = el
        for (let i = 0; i < 3 && item.parentElement !== root && item.parentElement.childElementCount === 1 && !/flex|grid/.test(cs(item.parentElement).display); i++) item = item.parentElement
        const key = el.closest(GROUPS) || item.parentElement
        groups.get(key)?.push(el) || groups.set(key, [el])
      }
      for (const list of groups.values()) {
        const lines = []
        for (const el of list.sort((a, b) => box(a).top - box(b).top)) {
          const r = box(el)
          const line = lines.find(l => l.some(o => Math.min(r.bottom, box(o).bottom) - Math.max(r.top, box(o).top) >= Math.min(r.height, box(o).height) / 2))
          line ? line.push(el) : lines.push([el])
        }
        for (const line of lines.filter(l => l.length > 1)) {
          const hs = line.map(el => Math.round(box(el).height))
          const common = hs.toSorted((a, b) => hs.filter(h => h === b).length - hs.filter(h => h === a).length || b - a)[0]
          const odd = line.find(el => Math.abs(box(el).height - common) > 1)
          if (odd) report("button-size-mismatch", "error", odd, `controls in one row have heights ${hs.join(", ")} px (data-size ${line.map(el => el.dataset.size || "default").join(", ")}); use one data-size for the row`)
        }
      }
    })

    run("multiple-primary", () => {
      const regions = new Map()
      for (const el of all) {
        if (!el.matches(PRIMARY) || (el.dataset.variant || "default") !== "default" || !vis(el)) continue
        const region = el.closest(REGIONS)
        if (region) regions.get(region)?.push(el) || regions.set(region, [el])
      }
      for (const [region, list] of regions) {
        list.slice(1).forEach(el => report("multiple-primary", "error", el, `${list.length} primary buttons in ${sel(region)}; keep one default-variant button, make the others outline, secondary, or ghost`))
      }
    })

    run("text-clipped", () => {
      const range = document.createRange()
      for (const el of texts) {
        let clip = el
        for (let i = 0; i < 3 && clip && cs(clip).overflowX === "visible" && cs(clip).overflowY === "visible"; i++) clip = clip.parentElement
        if (!clip || clip === document.body || clip === document.documentElement) continue
        const s = cs(clip)
        if (/auto|scroll/.test(s.overflowX + s.overflowY) || clip.clientWidth < 4 || clip.clientHeight < 4 || clip.closest('[data-slot="carousel"], [aria-roledescription="carousel"]')) continue
        const r = box(clip)
        const left = r.left + clip.clientLeft
        const top = r.top + clip.clientTop
        range.selectNodeContents(el)
        const t = range.getBoundingClientRect()
        if (!t.width || !t.height) continue
        const cutX = s.overflowX !== "visible" && (t.right > left + clip.clientWidth + 1 || t.left < left - 1)
        const cutY = s.overflowY !== "visible" && (t.bottom > top + clip.clientHeight + 3 || t.top < top - 3)
        if (!cutX && !cutY) continue
        if ((cutX && cs(clip).textOverflow === "ellipsis") || (cutY && cs(clip).webkitLineClamp !== "none" && cs(clip).webkitLineClamp)) {
          const named = el.closest('[title], [aria-label], [aria-describedby], [data-slot="tooltip-trigger"], [data-tooltip-trigger]')
          if (!named || !clip.contains(named) && !named.contains(clip)) report("text-clipped", "warn", el, "text ends in an ellipsis and has no title or tooltip; add a title attribute or a tooltip with the full text")
        } else {
          report("text-clipped", "error", el, `text is cut by ${clip === el ? "its own" : "a parent's"} overflow (${Math.round(t.width)}×${Math.round(t.height)} in ${clip.clientWidth}×${clip.clientHeight}); let it wrap, or use the truncate pattern with a title`)
        }
      }
    })

    run("horizontal-scroll", () => {
      const html = document.documentElement
      const vw = html.clientWidth
      if (html.scrollWidth <= vw + 1) return
      const wide = all.filter(el => {
        if (!vis(el) || (box(el).right + scrollX <= vw + 1 && box(el).left + scrollX >= -1)) return false
        for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) if (cs(p).overflowX !== "visible") return false
        return true
      })
      const top = wide.filter(el => !wide.includes(el.parentElement)).slice(0, 5)
      const what = `the page is ${html.scrollWidth} px wide in a ${vw} px viewport`
      if (!top.length) report("horizontal-scroll", "error", null, what)
      top.forEach(el => report("horizontal-scroll", "error", el, `${what}; this element spans ${Math.round(box(el).left + scrollX)} to ${Math.round(box(el).right + scrollX)} px. Use min-width: 0, flex-wrap, or an overflow-x: auto wrapper`))
    })

    run("small-target", () => {
      const coarse = options.coarse ?? matchMedia("(pointer: coarse)").matches
      const center = r => [r.left + r.width / 2, r.top + r.height / 2]
      const grow = new Map()
      const hitBox = el => {
        if (grow.has(el)) return grow.get(el)
        const r = box(el)
        let [l, t, rr, b] = [r.left, r.top, r.right, r.bottom]
        if (cs(el).position !== "static") {
          for (const p of ["::before", "::after"]) {
            const s = getComputedStyle(el, p)
            if (s.content === "none" || s.display === "none" || s.position !== "absolute") continue
            const v = k => Math.min(0, parseFloat(s[k]) || 0)
            ;[l, t, rr, b] = [Math.min(l, r.left + v("left")), Math.min(t, r.top + v("top")), Math.max(rr, r.right - v("right")), Math.max(b, r.bottom - v("bottom"))]
          }
        }
        const out = { left: l, top: t, right: rr, bottom: b, width: rr - l, height: b - t }
        grow.set(el, out)
        return out
      }
      const small = el => hitBox(el).width < 23.5 || hitBox(el).height < 23.5
      const hit = targets.filter(el => cs(el).display !== "inline" && !el.matches('[role="slider"], input[type="range"]') && !el.closest('[data-slot="slider"]'))
      for (const el of hit) {
        const r = hitBox(el)
        if (small(el)) {
          const [x, y] = center(r)
          const near = hit.find(o => {
            if (o === el || o.contains(el) || el.contains(o)) return false
            const q = hitBox(o)
            if (small(o)) return Math.hypot(...center(q).map((v, i) => v - [x, y][i])) < 23.5
            return Math.hypot(Math.max(q.left - x, 0, x - q.right), Math.max(q.top - y, 0, y - q.bottom)) < 11.75
          })
          if (near) report("small-target", "error", el, `target is ${Math.round(r.width)}×${Math.round(r.height)} px and ${sel(near)} is too close (WCAG 2.5.8 needs 24×24 px or 24 px spacing); use a larger data-size or add gap`)
        } else if (coarse && (r.width < 43.5 || r.height < 43.5)) {
          report("small-target", "warn", el, `target is ${Math.round(r.width)}×${Math.round(r.height)} px on a touch screen; 44×44 px is easier to hit (WCAG 2.5.5); use data-size="lg" or more padding`)
        }
      }
    })

    run("low-contrast", () => {
      for (const el of texts) {
        if (disabled(el) || el.closest("svg") || rgba(cs(el).color)[3] < 0.1) continue
        let bg = [255, 255, 255, 1]
        const layers = []
        let unknown = false
        for (let e = el; e; e = e.parentElement) {
          const s = cs(e)
          if (Number(s.opacity) < 1 || s.backgroundImage !== "none" || s.mixBlendMode !== "normal" || (s.filter !== "none" && e !== el)) {
            unknown = true
            break
          }
          const c = rgba(s.backgroundColor)
          if (c[3] > 0) layers.push(c)
          if (c[3] >= 1) break
        }
        if (unknown) continue
        if (layers.at(-1)?.[3] !== 1 && /dark/.test(cs(document.documentElement).colorScheme)) continue
        for (const c of layers.reverse()) bg = over(c, bg)
        const s = cs(el)
        const fg = over(rgba(s.color), bg)
        const size = parseFloat(s.fontSize)
        const large = size >= 24 || (size >= 18.66 && Number(s.fontWeight) >= 700)
        const need = large ? 3 : 4.5
        const got = ratio(fg, bg)
        if (got < need - 0.005) report("low-contrast", got < 3 - 0.005 ? "error" : "warn", el, `contrast ${got.toFixed(2)}:1 (${hex(rgba(s.color))} on ${hex(bg)}), WCAG AA needs ${need}:1; use --foreground or --muted-foreground on the kit backgrounds`)
      }
    })

    run("non-token-color", () => {
      const names = new Set()
      const scopes = new Set([document.documentElement])
      const scan = rules => {
        for (const r of rules) {
          const own = r.style ? [...r.style].filter(p => p.startsWith("--") && !p.startsWith("--tw-") && /#|\(/.test(r.style.getPropertyValue(p))) : []
          own.forEach(p => names.add(p))
          if (own.length && r.selectorText) {
            try {
              root.querySelectorAll(r.selectorText).forEach(e => scopes.add(e))
            } catch {}
          }
          if (r.cssRules) scan(r.cssRules)
        }
      }
      for (const sheet of document.styleSheets) {
        try {
          scan(sheet.cssRules)
        } catch {}
      }
      const sets = new Map()
      const probe = document.createElement("i")
      probe.hidden = true
      const tokensAt = scope => {
        if (sets.has(scope)) return sets.get(scope)
        const out = [[0, 0, 0], [255, 255, 255]]
        scope.append(probe)
        for (const n of names) {
          probe.style.color = "rgb(1 2 3)"
          probe.style.color = `var(${n})`
          const c = getComputedStyle(probe).color
          if (c !== "rgb(1, 2, 3)") out.push(rgba(c))
        }
        probe.remove()
        sets.set(scope, out)
        return out
      }
      const base = tokensAt(document.body)
      const scopeOf = el => {
        let e = el
        while (e && !scopes.has(e)) e = e.parentElement
        return e && e !== document.documentElement && e !== document.body ? e : null
      }
      const match = (c, list) => list.some(t => Math.abs(t[0] - c[0]) <= 2 && Math.abs(t[1] - c[1]) <= 2 && Math.abs(t[2] - c[2]) <= 2)
      const known = (c, el) => {
        if (c[3] === 0 || match(c, base)) return true
        const scope = scopeOf(el)
        return !!scope && !/^(input|select|textarea|img|br|hr)$/.test(scope.localName) && match(c, tokensAt(scope))
      }
      const seen = new Map()
      for (const el of all) {
        if (!vis(el) || el.closest("svg, img, video, canvas")) continue
        const s = cs(el)
        const parent = el.parentElement && cs(el.parentElement)
        const props = [["background-color", s.backgroundColor]]
        if (ownText(el) && s.color !== parent?.color) props.push(["color", s.color])
        for (const side of ["Top", "Right", "Bottom", "Left"]) if (parseFloat(s[`border${side}Width`]) > 0) props.push(["border-color", s[`border${side}Color`]])
        for (const [prop, value] of props) {
          const c = rgba(value)
          if (known(c, el)) continue
          const key = prop + hex(c)
          seen.get(key)?.els.push(el) || seen.set(key, { prop, c, els: [el] })
        }
      }
      for (const { prop, c, els } of seen.values()) {
        const el = els.find(e => !skipped(e, "non-token-color"))
        if (el) report("non-token-color", "warn", el, `${prop} ${hex(c)} on ${els.length} element${els.length > 1 ? "s" : ""} matches no --* token; use a kit token (--primary, --muted, --destructive, --chart-1 ...) or define a token for it`)
      }
    })

    run("missing-label", () => {
      const text = el => {
        let out = ""
        for (const n of el.childNodes) {
          if (n.nodeType === 3) out += n.data
          else if (n.nodeType === 1 && n.getAttribute("aria-hidden") !== "true" && cs(n).display !== "none") out += n.getAttribute("aria-label") || (n.localName === "img" ? n.alt : "") || (n.localName === "svg" ? n.querySelector("title")?.textContent || "" : text(n))
        }
        return out
      }
      const name = el => {
        const by = el.getAttribute("aria-labelledby")
        if (by) return by.split(/\s+/).map(id => document.getElementById(id)?.textContent || "").join(" ")
        if (el.getAttribute("aria-label")) return el.getAttribute("aria-label")
        if (el.localName === "img") return el.hasAttribute("alt") ? "alt" : ""
        if (el.labels?.length) return [...el.labels].map(text).join(" ")
        if (/^(submit|reset|button)$/.test(el.type) && el.localName === "input") return el.value || el.type
        if (/^(input|select|textarea)$/.test(el.localName)) return el.title || el.placeholder || ""
        return text(el) || el.title
      }
      for (const el of all) {
        if (!el.matches(NAMED) || !vis(el) || el.closest('[aria-hidden="true"]') || el.getAttribute("role") === "presentation") continue
        if (!name(el).trim()) report("missing-label", "error", el, el.localName === "img" ? "image has no alt attribute; add alt (empty for decoration)" : `${el.getAttribute("role") || el.localName} has no accessible name; add visible text, a <label>, or aria-label`)
      }
    })

    run("heading-order", () => {
      const hs = all.filter(el => /^h[1-6]$/.test(el.localName) || (el.getAttribute("role") === "heading" && el.hasAttribute("aria-level"))).filter(el => el.checkVisibility() && !el.closest('[aria-hidden="true"]'))
      let last = 0
      let h1 = 0
      for (const el of hs) {
        const level = Number(el.getAttribute("aria-level")) || Number(el.localName[1])
        if (level === 1 && ++h1 === 2) report("heading-order", "warn", el, "second h1 on the page; use one h1 for the page title and h2 for sections")
        if (last && level > last + 1) report("heading-order", "warn", el, `h${level} follows h${last}; do not skip heading levels`)
        last = level
      }
    })

    run("misaligned", () => {
      const rtl = cs(document.documentElement).direction === "rtl"
      for (const parent of all) {
        if (parent.childElementCount < 2 || !vis(parent) || /flex|grid/.test(cs(parent).display) && !/column/.test(cs(parent).flexDirection) && cs(parent).display.includes("flex")) continue
        if (/center|end|right/.test(cs(parent).alignItems + cs(parent).textAlign + cs(parent).justifyItems)) continue
        const kids = [...parent.children].filter(el => vis(el) && !/absolute|fixed/.test(cs(el).position) && !/inline|contents|table-cell/.test(cs(el).display) && cs(el).float === "none" && !/center|end/.test(cs(el).alignSelf + cs(el).justifySelf) && cs(el).marginInlineStart !== "auto")
        for (let i = 1; i < kids.length; i++) {
          const a = box(kids[i - 1])
          const b = box(kids[i])
          if (b.top < a.bottom - 0.5 || Math.min(a.right, b.right) <= Math.max(a.left, b.left)) continue
          const d = rtl ? Math.abs(a.right - b.right) : Math.abs(a.left - b.left)
          if (d >= 1 && d <= 7 && Math.abs(a.left + a.right - b.left - b.right) >= 2) report("misaligned", "warn", kids[i], `start edge is ${d.toFixed(1)} px off the sibling above (${sel(kids[i - 1])}); align both to the same edge or padding`)
        }
      }
    })

    run("empty-region", () => {
      const limit = Math.max(1200, innerHeight * 1.5)
      for (const parent of all) {
        const d = cs(parent).display
        if (!/grid|flex/.test(d) || d.includes("flex") && /column/.test(cs(parent).flexDirection) || !vis(parent)) continue
        const items = [...parent.children].filter(el => vis(el) && !/absolute|fixed|sticky/.test(cs(el).position) && box(el).width >= 120 && /normal|stretch|start/.test(cs(el).alignSelf === "auto" ? cs(parent).alignItems : cs(el).alignSelf))
        const rows = []
        for (const el of items) {
          const r = box(el)
          const row = rows.find(l => l.some(o => Math.min(r.bottom, box(o).bottom) - Math.max(r.top, box(o).top) > 0 && box(o).top === r.top))
          row ? row.push(el) : rows.push([el])
        }
        for (const row of rows.filter(l => l.length > 1)) {
          const bottom = Math.max(...row.map(el => box(el).bottom))
          const height = bottom - Math.min(...row.map(el => box(el).top))
          if (height < 160 || height > limit || row.some(el => el.matches('[data-slot="sidebar"], [data-slot="sidebar-wrapper"]') || el.querySelector('[data-slot="sidebar"]'))) continue
          const empty = row.map(el => {
            const s = cs(el)
            let end = box(el).top + parseFloat(s.borderTopWidth) + parseFloat(s.paddingTop)
            const range = document.createRange()
            for (const e of el.querySelectorAll("*")) {
              if (!vis(e) || cs(e).position === "sticky") continue
              const es = cs(e)
              let b = 0
              if (ownText(e)) {
                range.selectNodeContents(e)
                b = range.getBoundingClientRect().bottom
              } else if (/^(img|svg|canvas|video|input|select|textarea|button|hr|iframe|progress|meter)$/.test(e.localName) || rgba(es.backgroundColor)[3] > 0 || parseFloat(es.borderBottomWidth) > 0 || es.backgroundImage !== "none") b = box(e).bottom
              end = Math.max(end, b)
            }
            return bottom - end - parseFloat(s.paddingBottom) - parseFloat(s.borderBottomWidth)
          })
          const fullest = Math.min(...empty)
          row.forEach((el, i) => {
            if (empty[i] >= 96 && empty[i] >= height * 0.25 && fullest <= 32) report("empty-region", "warn", el, `${Math.round(empty[i])} px empty below the content while ${sel(row[empty.indexOf(fullest)])} fills the ${Math.round(height)} px row; move content into it, span it over fewer rows, or align the row to start`)
          })
        }
      }
    })

    return { findings }
  }

  function watchShift(options = {}) {
    const threshold = options.threshold ?? 1
    const els = [...document.querySelectorAll(options.selector || TARGETS)].filter(el => el.checkVisibility() && el.getBoundingClientRect().width > 0)
    const scroller = el => {
      for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
        const s = getComputedStyle(p)
        if (/fixed|sticky/.test(s.position)) return p
        if (/auto|scroll/.test(s.overflowX + s.overflowY)) return p
      }
      return null
    }
    const pos = (el, sc) => {
      const r = el.getBoundingClientRect()
      if (!sc) return [r.left + scrollX, r.top + scrollY]
      const q = sc.getBoundingClientRect()
      return [r.left - q.left + sc.scrollLeft, r.top - q.top + sc.scrollTop]
    }
    const base = new Map(els.map(el => {
      const sc = scroller(el)
      return [el, { sc, at: pos(el, sc) }]
    }))
    const moved = new Map()
    const measure = () => {
      for (const [el, { sc, at }] of base) {
        if (!el.isConnected || !el.checkVisibility()) continue
        const [x, y] = pos(el, sc)
        const d = Math.max(Math.abs(x - at[0]), Math.abs(y - at[1]))
        if (d >= threshold && d > (moved.get(el)?.d ?? 0)) moved.set(el, { d, dx: x - at[0], dy: y - at[1] })
      }
    }
    const ro = new ResizeObserver(measure)
    const seen = new Set()
    for (const el of els) for (let p = el; p && !seen.has(p); p = p.parentElement) seen.add(p) && ro.observe(p)
    let frame = requestAnimationFrame(function tick() {
      measure()
      frame = requestAnimationFrame(tick)
    })
    let score = null
    let po
    if (PerformanceObserver.supportedEntryTypes?.includes("layout-shift")) {
      score = 0
      po = new PerformanceObserver(list => list.getEntries().forEach(e => (score += e.value)))
      po.observe({ type: "layout-shift" })
    }
    return {
      stop() {
        measure()
        cancelAnimationFrame(frame)
        ro.disconnect()
        po?.takeRecords().forEach(e => (score += e.value))
        po?.disconnect()
        const findings = [...moved].map(([el, m]) => ({ rule: "layout-shift", severity: "error", selector: sel(el), message: `moved ${Math.round(m.dx)} px across and ${Math.round(m.dy)} px down during the interaction; reserve space for messages (min-height) or show them where they do not push controls` }))
        return { findings, score }
      },
    }
  }

  lint.watchShift = watchShift
  lint.rules = RULES
  window.clankerDesignLint = lint
})()
