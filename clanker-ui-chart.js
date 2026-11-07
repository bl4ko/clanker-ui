/*! clanker-ui | MIT | includes shadcn/ui (MIT, shadcn) and Lucide icons (ISC); see THIRD_PARTY_NOTICES */
import { h, svg, icon, emit, uid, dismissable, rove, setRoving, stringFor } from "./clanker-ui.js"

const TAU = Math.PI * 2
const SLOTS = 8
const GAP = 2
const BAR_MAX = 24
const RADIUS = 4
const MAX_TICKS = 50
const TYPES = ["area", "bar", "line", "pie", "donut", "radar", "radial"]
const CURVES = ["monotone", "linear", "step"]
const INDICATORS = ["line", "dot", "dashed"]
const SCALES = ["category", "time"]
const DAY = 864e5
const TIME_STEPS = [["minute", 1, 6e4], ["minute", 5, 3e5], ["minute", 15, 9e5], ["minute", 30, 18e5], ["hour", 1, 36e5], ["hour", 3, 108e5], ["hour", 6, 216e5], ["hour", 12, 432e5], ["day", 1, DAY], ["day", 2, 2 * DAY], ["week", 1, 7 * DAY], ["month", 1, 30 * DAY], ["month", 3, 91 * DAY], ["month", 6, 182 * DAY], ...[1, 2, 5, 10, 20, 50, 100].map(n => ["year", n, n * 365 * DAY])]
const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/
const ISO_STAMP = /^\d{4}-\d{2}-\d{2}T/
const IDENT = /^[a-z][\w-]*$/i
const PROP_CHAR = /[^\p{L}\p{N}_-]/gu
const UNSAFE_COLOR = /[\\"']|(url|src)\(/i
const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
const LOCAL_CLOCK = {
  zone: undefined,
  parts(t) {
    const d = new Date(t)
    return { y: d.getFullYear(), mo: d.getMonth(), d: d.getDate(), h: d.getHours(), mi: d.getMinutes(), s: d.getSeconds(), ms: d.getMilliseconds(), wd: d.getDay() }
  },
  make(y, mo, d, h = 0, mi = 0) {
    const date = new Date(y, mo, d, h, mi)
    if (y >= 0 && y < 100) date.setFullYear(y)
    return date.getTime()
  },
}
const clocks = new Map()
const instances = new WeakMap()
const formats = new Map()
const mounted = new Set()
let paint = null
let themed = false

export function chart(element, data, options) {
  if (!(element instanceof Element)) throw new TypeError("clanker-ui chart: the first argument must be an element")
  instances.get(element)?.destroy()
  const slot = element.getAttribute("data-slot")
  if (slot && slot !== "chart") throw new TypeError(`clanker-ui chart: the element already has data-slot="${slot}"`)
  const s = {
    root: element,
    id: uid("chart"),
    rows: [],
    config: null,
    opts: {},
    hidden: new Set(),
    view: "chart",
    active: null,
    last: null,
    source: null,
    pointerFocus: false,
    geom: null,
    model: null,
    width: 0,
    height: 0,
    frame: 0,
    animate: true,
    release: null,
    destroyed: false,
    saved: [...element.childNodes],
    attrs: new Map(),
    props: new Set(),
  }
  chartIngest(s, data, options ?? {})
  chartMount(s)
  try {
    chartRebuild(s)
  } catch (err) {
    chartDestroy(s)
    throw err
  }
  const api = Object.freeze({
    update(next, more) {
      if (s.destroyed) throw new Error("clanker-ui chart: update() after destroy()")
      const saved = { rows: s.rows, config: s.config, opts: s.opts, view: s.view }
      chartHideTip(s)
      s.last = null
      try {
        chartIngest(s, next, more)
        chartRebuild(s)
      } catch (err) {
        Object.assign(s, saved)
        chartRebuild(s)
        throw err
      }
      return api
    },
    destroy() {
      chartDestroy(s)
    },
  })
  instances.set(element, api)
  return api
}

export function sparkline(element, data, options = {}) {
  return chart(element, data, { ...options, type: options.area ? "area" : "line", sparkline: true, legend: false })
}

export function statTile(element, options = {}) {
  if (!(element instanceof Element)) throw new TypeError("clanker-ui statTile: the first argument must be an element")
  instances.get(element)?.destroy()
  const t = { root: element, opts: { ...options }, spark: null, saved: [...element.childNodes], attrs: new Map(), labelId: uid("chart-stat"), destroyed: false }
  const api = Object.freeze({
    update(next) {
      if (t.destroyed) throw new Error("clanker-ui statTile: update() after destroy()")
      const saved = t.opts
      t.opts = { ...t.opts, ...next }
      try {
        chartStatRender(t)
      } catch (err) {
        t.opts = saved
        chartStatRender(t)
        throw err
      }
      return api
    },
    destroy() {
      if (t.destroyed) return
      t.destroyed = true
      t.spark?.destroy()
      t.root.replaceChildren(...t.saved)
      chartRestore(t.root, t.attrs)
      instances.delete(t.root)
    },
  })
  try {
    chartStatRender(t)
  } catch (err) {
    api.destroy()
    throw err
  }
  instances.set(element, api)
  return api
}

function chartIngest(s, data, options) {
  if (data != null) {
    if (Array.isArray(data)) s.rows = data
    else if (typeof data === "object") {
      if (data.rows !== undefined) {
        if (!Array.isArray(data.rows)) throw new TypeError("clanker-ui chart: data.rows must be an array")
        s.rows = data.rows
      }
      if (data.config !== undefined) s.config = data.config
    } else throw new TypeError("clanker-ui chart: data must be an array of rows or { rows, config }")
  }
  if (options && typeof options === "object") s.opts = { ...s.opts, ...options }
  const o = s.opts
  if (!TYPES.includes(o.type ?? "bar")) throw new TypeError(`clanker-ui chart: unknown type "${o.type}"`)
  if (!CURVES.includes(o.curve ?? "monotone")) throw new TypeError(`clanker-ui chart: unknown curve "${o.curve}"`)
  if (!INDICATORS.includes(o.tooltip?.indicator ?? "line")) throw new TypeError(`clanker-ui chart: unknown tooltip indicator "${o.tooltip.indicator}"`)
  if (o.domain != null && !(Array.isArray(o.domain) && o.domain.every(v => v == null || Number.isFinite(v)))) throw new TypeError("clanker-ui chart: domain must be [min, max] with finite numbers or null")
  const cartesian = ["area", "bar", "line"].includes(o.type ?? "bar")
  if (!SCALES.includes(o.scale ?? "category")) throw new TypeError(`clanker-ui chart: unknown scale "${o.scale}"`)
  if (o.scale === "time" && o.type !== "line" && o.type !== "area") throw new TypeError('clanker-ui chart: scale "time" needs type "line" or "area"')
  if (o.references != null) {
    if (!Array.isArray(o.references)) throw new TypeError("clanker-ui chart: references must be an array")
    if (o.references.length && !cartesian) throw new TypeError("clanker-ui chart: references need type bar, line, or area")
    for (const r of o.references) {
      if (!r || typeof r !== "object" || !(Number.isFinite(r.value) || (Number.isFinite(r.from) && Number.isFinite(r.to)))) throw new TypeError("clanker-ui chart: a reference needs a finite value, or a finite from and to")
      if (r.position != null && r.position !== "start" && r.position !== "end") throw new TypeError(`clanker-ui chart: unknown reference position "${r.position}"`)
      if (r.tone != null) chartColorValue(r.tone)
    }
  }
  if (options?.view !== undefined) {
    if (options.view !== "chart" && options.view !== "table") throw new TypeError(`clanker-ui chart: unknown view "${options.view}"`)
    s.view = options.view
  }
}

function chartMount(s) {
  const plot = h("div", { "data-slot": "chart-plot" })
  const surface = svg("svg", {
    "data-slot": "chart-svg",
    role: "application",
    tabindex: "0",
    onpointermove: e => chartPointer(s, e),
    onpointerdown: e => {
      s.pointerFocus = true
      chartPointer(s, e)
    },
    onpointerleave: e => {
      if (e.pointerType === "mouse" && s.source === "pointer") chartHideTip(s)
    },
    onkeydown: e => chartKey(s, e),
    onfocus: () => {
      const pointer = s.pointerFocus
      s.pointerFocus = false
      if (!pointer && !s.active && s.geom?.count) chartShowTip(s, s.last ?? { index: 0, sub: 0 }, "keyboard")
    },
    onblur: () => {
      s.pointerFocus = false
      if (s.source === "keyboard") chartHideTip(s)
    },
  })
  const tip = h("div", { "data-slot": "chart-tooltip", "aria-hidden": "true", hidden: true })
  const probe = h("span", { "data-slot": "chart-probe", "aria-hidden": "true", hidden: true })
  plot.append(surface, tip, probe)
  const table = h("div", { "data-slot": "chart-table", role: "region", tabindex: "0", hidden: true })
  const legend = h("div", {
    "data-slot": "chart-legend",
    role: "toolbar",
    onkeydown: e => rove(e, [...legend.querySelectorAll('[data-slot="chart-legend-item"]')], { orientation: "horizontal", typeahead: false }),
  })
  const toggle = h(
    "button",
    {
      type: "button",
      "data-slot": "chart-table-toggle",
      "aria-pressed": "false",
      onclick: () => {
        chartView(s, s.view === "table" ? "chart" : "table")
        void 0
      },
    },
    icon("table"),
  )
  const footer = h("div", { "data-slot": "chart-footer" }, legend, toggle)
  const live = h("div", { "data-slot": "chart-live", class: "sr-only", "aria-live": "polite", "aria-atomic": "true" })
  s.els = { plot, svg: surface, tip, probe, table, legend, toggle, footer, live }
  s.root.replaceChildren(plot, table, footer, live)
  s.ro = new ResizeObserver(entries => {
    if (!s.root.isConnected) {
      mounted.delete(s)
      chartHideTip(s)
      return
    }
    const back = !mounted.has(s)
    mounted.add(s)
    const box = entries.at(-1).contentRect
    const w = Math.floor(box.width)
    const hgt = Math.floor(box.height)
    if (!back && w === s.width && hgt === s.height) return
    s.width = w
    s.height = hgt
    chartSchedule(s)
  })
  s.ro.observe(plot)
  if (s.root.isConnected) mounted.add(s)
  if (!themed) {
    themed = true
    document.documentElement.addEventListener("theme:change", () => {
      for (const c of mounted) chartSchedule(c)
    })
  }
}

function chartIconNode(value) {
  if (typeof value === "string") return icon(value)
  if (typeof value === "function") return value()
  if (value instanceof Node) return value.cloneNode(true)
  return null
}

function chartAttr(s, name, value) {
  chartAttrOn(s.root, s.attrs, name, value)
}

function chartAttrOn(el, store, name, value) {
  if (!store.has(name)) store.set(name, el.getAttribute(name))
  if (value == null || value === false) el.removeAttribute(name)
  else el.setAttribute(name, value === true ? "" : String(value))
}

function chartRestore(el, store) {
  for (const [name, value] of store) {
    if (value === null) el.removeAttribute(name)
    else el.setAttribute(name, value)
  }
}

function chartProp(s, name, value) {
  s.props.add(name)
  s.root.style.setProperty(name, value)
}

function chartSchedule(s) {
  if (s.frame || s.destroyed) return
  s.frame = requestAnimationFrame(() => {
    s.frame = 0
    if (!s.destroyed) chartRender(s)
  })
}

function chartRebuild(s) {
  const m = chartModel(s)
  s.model = m
  const o = s.opts
  const { plot, tip, footer, toggle, legend } = s.els
  chartAttr(s, "data-slot", "chart")
  chartAttr(s, "data-type", m.type)
  chartAttr(s, "data-chart", s.id)
  chartAttr(s, "data-sparkline", m.sparkline)
  for (const name of s.props) s.root.style.removeProperty(name)
  s.props.clear()
  if (o.height != null) chartProp(s, "height", typeof o.height === "number" ? `${o.height}px` : String(o.height))
  for (const e of m.entities) chartProp(s, `--color-${e.key.replace(PROP_CHAR, "-")}`, e.color)
  tip.dataset.indicator = o.tooltip?.indicator ?? "line"
  toggle.hidden = o.table === false
  toggle.setAttribute("aria-label", stringFor(s.root, "tableView"))
  legend.setAttribute("aria-label", stringFor(s.root, "legend"))
  chartLegend(s, m)
  footer.hidden = legend.hidden && toggle.hidden
  chartTable(s, m)
  chartView(s, s.view, false)
  const box = plot.getBoundingClientRect()
  s.width = Math.floor(box.width)
  s.height = Math.floor(box.height)
  chartRender(s)
}

function chartModel(s) {
  const o = s.opts
  const type = o.type ?? "bar"
  const rows = s.rows.map((r, i) => (r === null || typeof r !== "object" ? { index: i + 1, value: chartNum(r) } : r))
  const first = rows[0] ?? {}
  const x = o.x ?? Object.keys(first).find(k => chartNum(first[k]) === null) ?? (Object.hasOwn(first, "index") ? "index" : null)
  const authored = s.config && typeof s.config === "object" ? s.config : null
  const plain = s.rows.some(r => r === null || typeof r !== "object")
  const config = plain ? { index: { label: "#" }, value: { label: stringFor(s.root, "value") }, ...authored } : authored
  const numeric = k => k !== x && rows.some(r => chartNum(r?.[k]) !== null)
  const wanted = [o.y].flat().filter(k => k != null).map(String)
  let keys = config ? Object.keys(config).filter(numeric) : []
  keys = [...keys, ...wanted.filter(k => !keys.includes(k) && numeric(k))]
  if (!keys.length) keys = Object.keys(first).filter(numeric)
  const byCategory = type === "pie" || type === "donut" || (type === "radial" && !o.stacked)
  const valueKey = byCategory ? (wanted[0] ?? keys[0] ?? null) : null
  const column = key => key === x || (byCategory && (key === valueKey || rows.some(r => Object.hasOwn(r, key))))
  const slots = new Map()
  for (const key of config ? Object.keys(config) : []) if (!column(key)) slots.set(key, slots.size)
  const entity = key => {
    if (!slots.has(key)) slots.set(key, slots.size)
    return chartEntity(config, key, slots.get(key))
  }
  let entities
  let series = []
  if (byCategory) {
    const cats = [...new Set(rows.map((r, i) => chartCategory(r, x, i)))]
    const known = config ? Object.keys(config).filter(k => cats.includes(k)) : []
    entities = [...known, ...cats.filter(c => !known.includes(c))].map(entity)
  } else {
    entities = keys.map(entity)
    series = wanted.length ? wanted.filter(k => keys.includes(k)) : keys
  }
  const clock = chartClock(o.timeZone)
  const isDate = x != null && rows.length > 0 && rows.every(r => chartDate(r?.[x], clock) !== null)
  const time = o.scale === "time"
  if (time && !isDate && rows.length) throw new TypeError('clanker-ui chart: scale "time" needs an ISO date or a Date in every x value')
  const times = time ? rows.map(r => chartDate(r[x], clock).getTime()) : null
  return {
    type,
    rows,
    x,
    config,
    entities,
    byKey: new Map(entities.map(e => [e.key, e])),
    series,
    valueKey,
    byCategory,
    isDate,
    time,
    times,
    clock,
    dateOnly: !times || times.every(t => {
      const p = clock.parts(t)
      return !p.h && !p.mi && !p.s && !p.ms
    }),
    references: (o.references ?? []).map(r => ({ ...r, band: !Number.isFinite(r.value), label: r.label == null ? "" : String(r.label), color: r.tone == null ? null : chartColorValue(r.tone) })),
    sparkline: !!o.sparkline,
    expand: o.stack === "expand" && (type === "area" || type === "bar"),
  }
}

function chartCategory(row, x, i) {
  const v = x == null ? i + 1 : row?.[x]
  return v == null ? "" : String(v)
}

function chartEntity(config, key, slot) {
  const entry = config && Object.hasOwn(config, key) ? config[key] : null
  return { key, label: chartLabel(config, key), icon: entry?.icon ?? null, color: chartColor(entry, slot) }
}

function chartLabel(config, key, fallback) {
  const entry = config && Object.hasOwn(config, key) ? config[key] : null
  return entry?.label != null ? String(entry.label) : (fallback ?? chartTitle(key))
}

function chartTitle(key) {
  const t = String(key)
  return t.charAt(0).toUpperCase() + t.slice(1)
}

function chartColor(entry, slot) {
  if (entry?.theme && typeof entry.theme === "object") return `light-dark(${chartColorValue(entry.theme.light)}, ${chartColorValue(entry.theme.dark)})`
  if (entry?.color != null) return chartColorValue(entry.color)
  if (slot >= SLOTS) throw new RangeError(`clanker-ui chart: more than ${SLOTS} series; fold the rest into "Other" or use small multiples`)
  return `var(--chart-${slot + 1})`
}

function chartColorValue(c) {
  if (typeof c === "number" && Number.isInteger(c) && c >= 1 && c <= SLOTS) return `var(--chart-${c})`
  if (typeof c === "string" && c && !UNSAFE_COLOR.test(c)) {
    if (CSS.supports("color", c)) return c
    if (IDENT.test(c)) return `var(--${c})`
  }
  throw new TypeError(`clanker-ui chart: unknown color ${JSON.stringify(c)}`)
}

function chartNum(v) {
  if (typeof v === "number") return Number.isFinite(v) ? v : null
  if (typeof v !== "string" || v.trim() === "") return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function chartClock(zone) {
  if (zone == null) return LOCAL_CLOCK
  let clock = clocks.get(zone)
  if (clock) return clock
  let fmt
  try {
    fmt = new Intl.DateTimeFormat("en-US", { timeZone: zone, hourCycle: "h23", weekday: "short", year: "numeric", month: "numeric", day: "numeric", hour: "numeric", minute: "numeric", second: "numeric" })
  } catch {
    throw new RangeError(`clanker-ui chart: unknown timeZone ${JSON.stringify(zone)}`)
  }
  const parts = t => {
    const o = {}
    for (const p of fmt.formatToParts(t)) o[p.type] = p.value
    return { y: Number(o.year), mo: Number(o.month) - 1, d: Number(o.day), h: Number(o.hour) % 24, mi: Number(o.minute), s: Number(o.second), ms: ((t % 1000) + 1000) % 1000, wd: WEEKDAYS.indexOf(o.weekday) }
  }
  const make = (y, mo, d, h = 0, mi = 0) => {
    const want = Date.UTC(y, mo, d, h, mi)
    let t = want
    for (let i = 0; i < 3; i++) {
      const p = parts(t)
      const diff = want - Date.UTC(p.y, p.mo, p.d, p.h, p.mi)
      if (!diff) break
      t += diff
    }
    return t
  }
  clock = { zone, parts, make }
  clocks.set(zone, clock)
  return clock
}

function chartDate(v, clock = LOCAL_CLOCK) {
  if (v instanceof Date) return Number.isNaN(v.getTime()) ? null : v
  if (typeof v !== "string") return null
  const m = ISO_DATE.exec(v)
  if (m) {
    const t = clock.make(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
    const p = clock.parts(t)
    return p.mo === Number(m[2]) - 1 && p.d === Number(m[3]) ? new Date(t) : null
  }
  if (!ISO_STAMP.test(v)) return null
  const d = new Date(v)
  return Number.isNaN(d.getTime()) ? null : d
}

function chartNumber(locale, options) {
  const key = `n|${locale}|${JSON.stringify(options)}`
  let fmt = formats.get(key)
  if (!fmt) {
    fmt = new Intl.NumberFormat(locale, options)
    formats.set(key, fmt)
  }
  return fmt
}

function chartDateFormat(locale, options) {
  const key = `d|${locale}|${JSON.stringify(options)}`
  let fmt = formats.get(key)
  if (!fmt) {
    fmt = new Intl.DateTimeFormat(locale, options)
    formats.set(key, fmt)
  }
  return fmt
}

function chartLocale(o) {
  if (o.locale != null) return o.locale
  try {
    return Intl.getCanonicalLocales(document.documentElement.lang || [])[0]
  } catch {
    return undefined
  }
}

function chartDigits(base, extra) {
  const own = extra && typeof extra === "object" ? extra : {}
  const out = { ...base, ...own }
  if (!Object.hasOwn(own, "maximumFractionDigits") && out.minimumFractionDigits > out.maximumFractionDigits) out.maximumFractionDigits = out.minimumFractionDigits
  if (!Object.hasOwn(own, "minimumFractionDigits") && out.maximumFractionDigits < out.minimumFractionDigits) out.minimumFractionDigits = out.maximumFractionDigits
  return out
}

function chartCompact(base) {
  const out = { ...base, notation: "compact", maximumFractionDigits: 1 }
  delete out.minimumFractionDigits
  return out
}

function chartFormats(s, m) {
  const o = s.opts
  const locale = chartLocale(o)
  const zone = o.timeZone == null ? {} : { timeZone: o.timeZone }
  const base = o.format && typeof o.format === "object" ? o.format : {}
  const compact = chartCompact(base)
  const value = typeof o.format === "function" ? v => String(o.format(v)) : v => chartNumber(locale, base).format(v)
  const percent = v => chartNumber(locale, { style: "percent", maximumFractionDigits: 1 }).format(v)
  const tick = (v, max) => {
    if (typeof o.tickFormat === "function") return String(o.tickFormat(v))
    if (m.expand) return chartNumber(locale, { style: "percent", maximumFractionDigits: 0 }).format(v)
    return chartNumber(locale, max >= 1000 ? compact : base).format(v)
  }
  const raw = i => (m.x == null ? i + 1 : m.rows[i]?.[m.x])
  const name = i => {
    const key = chartCategory(m.rows[i], m.x, i)
    return m.byKey.get(key)?.label ?? chartLabel(m.config, key, key)
  }
  const date = (i, options) => chartDateFormat(locale, { ...zone, ...options }).format(chartDate(raw(i), m.clock))
  const pick = (f, fallback) => (f && typeof f === "object" ? f : fallback)
  const xTick = i => {
    if (typeof o.xFormat === "function") return String(o.xFormat(raw(i), i))
    return m.isDate ? date(i, pick(o.xFormat, { month: "short", day: "numeric" })) : name(i)
  }
  const xLabel = i => {
    if (typeof o.labelFormat === "function") return String(o.labelFormat(raw(i), i))
    return m.isDate ? date(i, pick(o.labelFormat, m.dateOnly ? { month: "short", day: "numeric", year: "numeric" } : { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" })) : name(i)
  }
  const timeTick = (t, unit) => {
    const d = new Date(t)
    if (typeof o.xFormat === "function") return String(o.xFormat(d))
    if (o.xFormat && typeof o.xFormat === "object") return chartDateFormat(locale, { ...zone, ...o.xFormat }).format(d)
    const p = m.clock.parts(t)
    const midnight = !p.h && !p.mi
    const options =
      unit === "year" || (unit === "month" && !p.mo)
        ? { year: "numeric" }
        : unit === "month"
          ? { month: "short" }
          : (unit === "minute" || unit === "hour") && !midnight
            ? { hour: "numeric", minute: "2-digit" }
            : { month: "short", day: "numeric" }
    return chartDateFormat(locale, { ...zone, ...options }).format(d)
  }
  return { locale, value, percent, tick, xTick, xLabel, timeTick }
}

function chartWidth(text, font) {
  const ctx = chartPaint()
  ctx.font = font
  return ctx.measureText(String(text)).width
}

function chartPaint() {
  paint ??= document.createElement("canvas").getContext("2d", { willReadFrequently: true })
  return paint
}

function chartFit(text, max, font) {
  if (chartWidth(text, font) <= max) return text
  let t = text
  while (t.length > 1 && chartWidth(`${t}…`, font) > max) t = t.slice(0, -1)
  return `${t}…`
}

function chartInk(probe, color) {
  const fill = chartLuminance(probe, color)
  const contrast = ink => {
    const l = chartLuminance(probe, `var(--chart-ink-${ink})`)
    return (Math.max(l, fill) + 0.05) / (Math.min(l, fill) + 0.05)
  }
  return contrast("dark") > contrast("light") ? "dark" : "light"
}

function chartLuminance(probe, color) {
  probe.style.color = color
  const ctx = chartPaint()
  ctx.clearRect(0, 0, 1, 1)
  ctx.fillStyle = "#000"
  ctx.fillStyle = getComputedStyle(probe).color
  ctx.fillRect(0, 0, 1, 1)
  const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data
  const lin = c => {
    const v = c / 255
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
}

function chartRound(v) {
  return Math.round(v * 100) / 100
}

function chartTicks(lo, hi, count) {
  if (lo === hi) {
    if (lo === 0) hi = 1
    else if (lo > 0) lo = 0
    else hi = 0
  }
  const raw = (hi - lo) / Math.max(1, count)
  const mag = 10 ** Math.floor(Math.log10(raw))
  const f = raw / mag
  const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * mag
  const start = Math.floor(lo / step + 1e-9) * step
  const steps = Math.round((Math.ceil(hi / step - 1e-9) * step - start) / step)
  if (!(step > 0) || start + step === start || !(steps <= MAX_TICKS)) return { lo, hi, ticks: [lo, hi] }
  const digits = Math.max(0, Math.min(100, 1 - Math.floor(Math.log10(step))))
  const ticks = []
  for (let i = 0; i <= steps; i++) ticks.push(Number((start + i * step).toFixed(digits)))
  return { lo: ticks[0], hi: ticks.at(-1), ticks }
}

function chartTimeFloor(t, unit, step, clock) {
  const p = clock.parts(t)
  if (unit === "minute") return clock.make(p.y, p.mo, p.d, p.h, Math.floor(p.mi / step) * step)
  if (unit === "hour") return clock.make(p.y, p.mo, p.d, Math.floor(p.h / step) * step)
  if (unit === "day") return clock.make(p.y, p.mo, p.d)
  if (unit === "week") return clock.make(p.y, p.mo, p.d - ((p.wd + 6) % 7))
  if (unit === "month") return clock.make(p.y, Math.floor(p.mo / step) * step, 1)
  return clock.make(Math.floor(p.y / step) * step, 0, 1)
}

function chartTimeTicks(t0, t1, unit, step, clock) {
  const out = []
  const by = unit === "day" ? 1 : unit === "week" ? 7 : step
  let t = chartTimeFloor(t0, unit, step, clock)
  while (t <= t1 && out.length <= MAX_TICKS) {
    const p = clock.parts(t)
    if (t >= t0 && (unit !== "day" || (p.d - 1) % step === 0)) out.push(t)
    const next = unit === "minute" ? clock.make(p.y, p.mo, p.d, p.h, p.mi + by) : unit === "hour" ? clock.make(p.y, p.mo, p.d, p.h + by) : unit === "month" ? clock.make(p.y, p.mo + by, 1) : unit === "year" ? clock.make(p.y + by, 0, 1) : clock.make(p.y, p.mo, p.d + by)
    t = next > t ? next : t + 36e5
  }
  return out
}

function chartScale(lo, hi, count, fixed) {
  const t = chartTicks(lo, hi, count)
  if (!fixed) return t
  return { lo, hi, ticks: t.ticks.filter(v => v >= lo - 1e-9 && v <= hi + 1e-9) }
}

function chartPolar(cx, cy, r, a) {
  return [cx + r * Math.sin(a), cy - r * Math.cos(a)]
}

function chartPoint(cx, cy, r, a) {
  return chartPolar(cx, cy, r, a).map(chartRound).join(",")
}

function chartSegments(list) {
  const out = []
  let cur = []
  for (const p of list) {
    if (p) cur.push(p)
    else if (cur.length) {
      out.push(cur)
      cur = []
    }
  }
  if (cur.length) out.push(cur)
  return out
}

function chartCurve(p, curve) {
  if (!p.length) return ""
  const r = chartRound
  let d = `M${r(p[0].x)},${r(p[0].y)}`
  if (p.length === 1) return d
  if (curve === "linear" || p.length === 2) {
    for (let i = 1; i < p.length; i++) d += `L${r(p[i].x)},${r(p[i].y)}`
    return d
  }
  if (curve === "step") {
    for (let i = 0; i < p.length - 1; i++) d += `H${r((p[i].x + p[i + 1].x) / 2)}V${r(p[i + 1].y)}H${r(p[i + 1].x)}`
    return d
  }
  const n = p.length
  const dx = []
  const sl = []
  for (let i = 0; i < n - 1; i++) {
    dx[i] = p[i + 1].x - p[i].x
    sl[i] = dx[i] ? (p[i + 1].y - p[i].y) / dx[i] : 0
  }
  const t = [sl[0]]
  for (let i = 1; i < n - 1; i++) t[i] = sl[i - 1] * sl[i] <= 0 ? 0 : (3 * (dx[i - 1] + dx[i])) / ((2 * dx[i] + dx[i - 1]) / sl[i - 1] + (dx[i] + 2 * dx[i - 1]) / sl[i])
  t[n - 1] = sl[n - 2]
  for (let i = 0; i < n - 1; i++) {
    const k = dx[i] / 3
    d += `C${r(p[i].x + k)},${r(p[i].y + t[i] * k)},${r(p[i + 1].x - k)},${r(p[i + 1].y - t[i + 1] * k)},${r(p[i + 1].x)},${r(p[i + 1].y)}`
  }
  return d
}

function chartBarPath(b, radius) {
  const { x, y, w, h: hgt, dir } = b
  const r = chartRound
  const v = dir === "up" || dir === "down"
  const c = Math.max(0, Math.min(radius, v ? w / 2 : hgt / 2, v ? hgt : w))
  const a = `A${r(c)},${r(c)},0,0,1,`
  if (dir === "up") return `M${r(x)},${r(y + hgt)}V${r(y + c)}${a}${r(x + c)},${r(y)}H${r(x + w - c)}${a}${r(x + w)},${r(y + c)}V${r(y + hgt)}Z`
  if (dir === "down") return `M${r(x)},${r(y)}H${r(x + w)}V${r(y + hgt - c)}${a}${r(x + w - c)},${r(y + hgt)}H${r(x + c)}${a}${r(x)},${r(y + hgt - c)}Z`
  if (dir === "right") return `M${r(x)},${r(y)}H${r(x + w - c)}${a}${r(x + w)},${r(y + c)}V${r(y + hgt - c)}${a}${r(x + w - c)},${r(y + hgt)}H${r(x)}Z`
  return `M${r(x + w)},${r(y)}V${r(y + hgt)}H${r(x + c)}${a}${r(x)},${r(y + hgt - c)}V${r(y + c)}${a}${r(x + c)},${r(y)}Z`
}

function chartSector(cx, cy, ri, ro, a0, a1) {
  const P = (rad, a) => chartPoint(cx, cy, rad, a)
  if (a1 - a0 >= TAU - 1e-6) {
    const outer = `M${P(ro, 0)}A${ro},${ro},0,1,1,${P(ro, Math.PI)}A${ro},${ro},0,1,1,${P(ro, 0)}Z`
    return ri > 0 ? `${outer}M${P(ri, 0)}A${ri},${ri},0,1,0,${P(ri, Math.PI)}A${ri},${ri},0,1,0,${P(ri, 0)}Z` : outer
  }
  const large = a1 - a0 > Math.PI ? 1 : 0
  if (ri <= 0) return `M${chartRound(cx)},${chartRound(cy)}L${P(ro, a0)}A${ro},${ro},0,${large},1,${P(ro, a1)}Z`
  return `M${P(ro, a0)}A${ro},${ro},0,${large},1,${P(ro, a1)}L${P(ri, a1)}A${ri},${ri},0,${large},0,${P(ri, a0)}Z`
}

function chartArcBar(cx, cy, ri, ro, a0, a1, radius) {
  const sweep = a1 - a0
  if (sweep <= 0) return ""
  if (sweep >= TAU - 1e-6) return chartSector(cx, cy, ri, ro, a0, a0 + TAU)
  const c = Math.min(radius, (ro - ri) / 2, (sweep * ri) / 2)
  if (c < 0.5) return chartSector(cx, cy, ri, ro, a0, a1)
  const P = (rad, a) => chartPoint(cx, cy, rad, a)
  const eo = a1 - c / ro
  const ei = a1 - c / ri
  const large = a => (a - a0 > Math.PI ? 1 : 0)
  return `M${P(ro, a0)}A${ro},${ro},0,${large(eo)},1,${P(ro, eo)}Q${P(ro, a1)},${P(ro - c, a1)}L${P(ri + c, a1)}Q${P(ri, a1)},${P(ri, ei)}A${ri},${ri},0,${large(ei)},0,${P(ri, a0)}Z`
}

function chartArc(cx, cy, r, a0, a1) {
  const large = a1 - a0 > Math.PI ? 1 : 0
  return `M${chartPoint(cx, cy, r, a0)}A${r},${r},0,${large},1,${chartPoint(cx, cy, r, a1)}`
}

function chartRender(s) {
  const m = s.model
  const surface = s.els.svg
  if (!m || s.view === "table") return
  const W = s.width
  const H = s.height
  if (W < 8 || H < 8) {
    surface.replaceChildren()
    s.geom = null
    return
  }
  const f = chartFormats(s, m)
  const family = getComputedStyle(s.root).fontFamily
  const c = {
    s,
    m,
    f,
    W,
    H,
    font: { tick: `400 12px ${family}`, label: `500 12px ${family}` },
    keys: m.series.filter(k => !s.hidden.has(k)),
    ink: color => chartInk(s.els.probe, color),
  }
  const geom = m.type === "pie" || m.type === "donut" ? chartPie(c) : m.type === "radar" ? chartRadar(c) : m.type === "radial" ? chartRadial(c) : chartCartesian(c)
  surface.setAttribute("viewBox", `0 0 ${W} ${H}`)
  surface.setAttribute("width", String(W))
  surface.setAttribute("height", String(H))
  surface.toggleAttribute("data-animate", s.animate && s.opts.animate !== false)
  for (const node of geom.nodes) node.setAttribute("aria-hidden", "true")
  surface.replaceChildren(...geom.nodes)
  surface.setAttribute("aria-label", chartSummary(c))
  s.geom = geom
  s.animate = false
  if (s.active) {
    if (s.active.index < geom.count) chartShowTip(s, s.active, s.source)
    else chartHideTip(s)
  }
}

function chartCartesian(c) {
  const { s, m, f, W, H, font, keys } = c
  const o = s.opts
  const spark = m.sparkline
  const bar = m.type === "bar"
  const area = m.type === "area"
  const horizontal = bar && !!o.horizontal
  const stack = m.type === "line" ? false : m.expand ? "expand" : !!o.stack
  const curve = o.curve ?? "monotone"
  const joined = k => o.connectNulls === true || (Array.isArray(o.connectNulls) && o.connectNulls.includes(k))
  const n = m.rows.length
  const entity = k => m.byKey.get(k)
  const vals = keys.map(k => m.rows.map(r => chartNum(r?.[k])))
  const spans = vals.map(row => row.map(v => (v === null ? null : v >= 0 ? [0, v] : [v, 0])))
  if (stack) {
    for (let i = 0; i < n; i++) {
      let total = 0
      if (stack === "expand") for (const row of vals) total += Math.abs(row[i] ?? 0)
      let pos = 0
      let neg = 0
      for (let k = 0; k < vals.length; k++) {
        let v = vals[k][i] ?? 0
        if (stack === "expand") v = total ? v / total : 0
        if (!Number.isFinite(v >= 0 ? pos + v : neg + v)) spans[k][i] = null
        else if (v >= 0) {
          spans[k][i] = [pos, pos + v]
          pos += v
        } else {
          spans[k][i] = [neg + v, neg]
          neg += v
        }
      }
    }
  }
  let lo = Infinity
  let hi = -Infinity
  for (let k = 0; k < spans.length; k++) {
    for (let i = 0; i < n; i++) {
      const p = spans[k][i]
      if (!p) continue
      const pair = !stack && !bar ? [vals[k][i], vals[k][i]] : p
      lo = Math.min(lo, pair[0], pair[1])
      hi = Math.max(hi, pair[0], pair[1])
    }
  }
  if (!Number.isFinite(lo)) {
    lo = 0
    hi = 1
  }
  for (const r of m.references) {
    for (const v of r.band ? [r.from, r.to] : [r.value]) {
      lo = Math.min(lo, v)
      hi = Math.max(hi, v)
    }
  }
  if (o.zero ?? !spark) {
    lo = Math.min(lo, 0)
    hi = Math.max(hi, 0)
  }
  if (bar) {
    lo = Math.min(lo, 0)
    hi = Math.max(hi, 0)
  }
  const fixed = Array.isArray(o.domain)
  if (fixed) {
    if (o.domain[0] != null) lo = o.domain[0]
    if (o.domain[1] != null) hi = o.domain[1]
  }
  if (stack === "expand") {
    lo = Math.min(0, lo)
    hi = 1
  }
  if (hi === lo) hi = lo + 1
  const labels = !spark && !!o.labels
  const valueAxis = !spark && (o.valueAxis ?? !(bar && labels))
  const categoryAxis = !spark && o.categoryAxis !== false
  const grid = !spark && o.grid !== false
  const count = horizontal ? Math.max(2, Math.min(6, Math.floor((W - 80) / 72))) : Math.max(2, Math.min(6, Math.floor((H - 40) / 40)))
  const scale = spark ? { lo, hi, ticks: [] } : chartScale(lo, hi, count, fixed || stack === "expand")
  const maxAbs = Math.max(Math.abs(scale.lo), Math.abs(scale.hi))
  const tickText = scale.ticks.map(v => f.tick(v, maxAbs))
  const tickW = valueAxis ? tickText.reduce((a, t) => Math.max(a, chartWidth(t, font.tick)), 0) : 0
  const catText = m.time ? [] : m.rows.map((_, i) => f.xTick(i))
  const catW = horizontal && categoryAxis ? Math.min(W * 0.4, catText.reduce((a, t) => Math.max(a, chartWidth(t, font.tick)), 0)) : 0
  const labelText = []
  if (labels) {
    for (let i = 0; i < n; i++) {
      if (stack) {
        let total = 0
        for (const row of vals) total += row[i] ?? 0
        labelText.push([f.value(total)])
      } else labelText.push(vals.map(row => (row[i] == null ? "" : f.value(row[i]))))
    }
  }
  const labelW = labels ? labelText.flat().reduce((a, t) => Math.max(a, chartWidth(t, font.label)), 0) : 0
  const pad = spark ? 6 : 0
  let top = spark ? pad : 8
  let right = spark ? pad : 12
  let bottom = spark ? pad : 8
  let left = spark ? pad : 12
  if (horizontal) {
    if (categoryAxis) left = catW + 16
    if (valueAxis) bottom = 28
    if (labels) right = Math.max(right, labelW + 12)
  } else {
    if (valueAxis) left = tickW + 16
    if (categoryAxis) bottom = 28
    if (labels) top = 26
    if (labels && !bar) right = Math.max(right, labelW / 2 + 4)
  }
  const pl = left
  const pt = top
  const pw = Math.max(1, W - left - right)
  const ph = Math.max(1, H - top - bottom)
  const span = scale.hi / 2 - scale.lo / 2
  const v2p = horizontal ? v => pl + ((v / 2 - scale.lo / 2) / span) * pw : v => pt + ph - ((v / 2 - scale.lo / 2) / span) * ph
  const clen = horizontal ? ph : pw
  const cstart = horizontal ? pt : pl
  const band = clen / Math.max(1, n)
  const t0 = m.time ? m.times.reduce((a, t) => Math.min(a, t), Infinity) : 0
  const t1 = m.time ? m.times.reduce((a, t) => Math.max(a, t), -Infinity) : 0
  const tpos = t => (t1 === t0 ? cstart + clen / 2 : cstart + ((t - t0) / (t1 - t0)) * clen)
  const pos = bar ? i => cstart + band * (i + 0.5) : m.time ? i => tpos(m.times[i]) : i => (n === 1 ? cstart + clen / 2 : cstart + (clen * i) / (n - 1))
  const nodes = []
  const defs = svg("defs")
  nodes.push(defs)
  if (grid) {
    nodes.push(
      svg(
        "g",
        { "data-part": "grid" },
        scale.ticks.map(v => {
          const p = Math.round(v2p(v)) + 0.5
          return horizontal ? svg("line", { x1: p, x2: p, y1: pt, y2: pt + ph }) : svg("line", { x1: pl, x2: pl + pw, y1: p, y2: p })
        }),
      ),
    )
  }
  if (!spark && scale.lo < 0 && scale.hi > 0) {
    const p = Math.round(v2p(0)) + 0.5
    nodes.push(horizontal ? svg("line", { "data-part": "baseline", x1: p, x2: p, y1: pt, y2: pt + ph }) : svg("line", { "data-part": "baseline", x1: pl, x2: pl + pw, y1: p, y2: p }))
  }
  const refs = m.references.length ? chartReferences(c, nodes, { pl, pt, pw, ph, v2p, lo: scale.lo, hi: scale.hi, horizontal, labels: !spark }) : null
  if (valueAxis) {
    nodes.push(
      svg(
        "g",
        { "data-part": "axis", "data-axis": "value" },
        scale.ticks.map((v, i) => {
          if (!horizontal) return svg("text", { x: chartRound(pl - 8), y: chartRound(v2p(v)), dy: "0.35em", "text-anchor": "end" }, tickText[i])
          const w = chartWidth(tickText[i], font.tick)
          return svg("text", { x: chartRound(Math.min(Math.max(v2p(v), w / 2), W - w / 2)), y: chartRound(pt + ph + 20), "text-anchor": "middle" }, tickText[i])
        }),
      ),
    )
  }
  if (categoryAxis && n) {
    const out = []
    if (m.time) {
      for (const tk of chartTimeAxis(c, t0, t1, tpos, clen)) out.push(svg("text", { x: chartRound(tk.x), y: chartRound(pt + ph + 20), "text-anchor": "middle" }, tk.text))
    } else if (horizontal) {
      const step = Math.max(1, Math.ceil(16 / band))
      for (let i = 0; i < n; i += step) out.push(svg("text", { x: chartRound(pl - 8), y: chartRound(pos(i)), dy: "0.35em", "text-anchor": "end" }, chartFit(catText[i], catW, font.tick)))
    } else {
      const widths = catText.map(t => chartWidth(t, font.tick))
      const need = widths.reduce((a, w) => Math.max(a, w), 0) + (m.isDate ? 24 : 10)
      const spacing = bar ? band : n > 1 ? clen / (n - 1) : clen
      const step = Math.max(1, Math.ceil(need / spacing))
      for (let i = 0; i < n; i += step) {
        const w = widths[i]
        out.push(svg("text", { x: chartRound(Math.min(Math.max(pos(i), w / 2), W - w / 2)), y: chartRound(pt + ph + 20), "text-anchor": "middle" }, catText[i]))
      }
    }
    nodes.push(svg("g", { "data-part": "axis", "data-axis": "category" }, out))
  }
  const marksGroup = svg("g", { "data-part": "marks" })
  const marks = keys.map(() => [])
  const pts = []
  const cursor = svg("rect", { "data-part": "cursor", x: 0, y: 0, width: 0, height: 0 })
  const crosshair = svg("line", { "data-part": "crosshair", x1: 0, x2: 0, y1: pt, y2: pt + ph })
  const active = svg("g", { "data-part": "active" })
  const group = stack ? 1 : Math.max(1, keys.length)
  const thick = Math.max(1, Math.min(o.barSize ?? BAR_MAX, (band * 0.8 - (group - 1) * GAP) / group))
  const gw = group * thick + (group - 1) * GAP
  if (bar) {
    nodes.push(cursor)
    const ends = []
    for (let i = 0; i < n; i++) {
      let pk = -1
      let nk = -1
      for (let k = 0; k < vals.length; k++) {
        const v = vals[k][i] ?? 0
        if (v > 0) pk = k
        else if (v < 0) nk = k
      }
      ends.push([pk, nk])
    }
    keys.forEach((key, k) => {
      const e = entity(key)
      const g = svg("g", { "data-part": "series", "data-key": key, style: { "--c": e.color } })
      for (let i = 0; i < n; i++) {
        const p = spans[k][i]
        const v = vals[k][i]
        if (!p) {
          marks[k][i] = null
          continue
        }
        const neg = stack ? p[0] < 0 && p[1] <= 0 : v < 0
        const cross = pos(i) - gw / 2 + (stack ? 0 : k * (thick + GAP))
        const a = v2p(p[0])
        const b = v2p(p[1])
        const rounded = !stack || (neg ? ends[i][1] === k : ends[i][0] === k)
        const startGap = stack && (neg ? p[1] !== 0 : p[0] !== 0) ? GAP : 0
        let mark
        if (horizontal) {
          mark = neg ? { x: a, y: cross, w: b - a - startGap, h: thick, dir: "left" } : { x: a + startGap, y: cross, w: b - a - startGap, h: thick, dir: "right" }
        } else {
          mark = neg ? { x: cross, y: b + startGap, w: thick, h: a - b - startGap, dir: "down" } : { x: cross, y: b, w: thick, h: a - b - startGap, dir: "up" }
        }
        mark.w = Math.max(0, mark.w)
        mark.h = Math.max(0, mark.h)
        mark.el = null
        if (mark.w >= 0.5 && mark.h >= 0.5) {
          mark.el = svg("path", { d: chartBarPath(mark, rounded ? RADIUS : 0), "data-part": "bar", "data-dir": mark.dir })
          if (o.highlight != null && o.highlight !== i) mark.el.setAttribute("data-muted", "")
          if (o.diverging && (v ?? 0) < 0) mark.el.setAttribute("data-negative", "")
          g.append(mark.el)
        }
        marks[k][i] = mark
      }
      marksGroup.append(g)
    })
    nodes.push(marksGroup)
    if (labels) {
      const out = []
      for (let i = 0; i < n; i++) {
        const list = stack ? [0] : keys.map((_, k) => k)
        for (const k of list) {
          const text = labelText[i][stack ? 0 : k]
          if (!text) continue
          const w = chartWidth(text, font.label)
          let mark = marks[k]?.[i]
          let neg = (vals[k]?.[i] ?? 0) < 0
          if (stack) {
            let total = 0
            for (const row of vals) total += row[i] ?? 0
            neg = total < 0
            const endK = neg ? ends[i][1] : ends[i][0]
            mark = endK >= 0 ? marks[endK][i] : null
          }
          if (!mark) continue
          if (horizontal) {
            if (thick + GAP < 12) continue
            const y = chartRound(mark.y + mark.h / 2)
            if (!neg) {
              const x = mark.x + mark.w + 6
              if (x + w <= W - 2) out.push(svg("text", { x: chartRound(x), y, dy: "0.35em", "text-anchor": "start", "data-part": "label" }, text))
              else if (w + 12 <= mark.w) out.push(svg("text", { x: chartRound(mark.x + mark.w - 6), y, dy: "0.35em", "text-anchor": "end", "data-part": "label", "data-ink": c.ink(entity(keys[k]).color) }, text))
            } else if (mark.x - 6 - w >= 0) out.push(svg("text", { x: chartRound(mark.x - 6), y, dy: "0.35em", "text-anchor": "end", "data-part": "label" }, text))
          } else {
            if (w > (group > 1 ? thick + GAP * 4 : band) - 2) continue
            const x = chartRound(mark.x + mark.w / 2)
            out.push(svg("text", { x, y: chartRound(neg ? mark.y + mark.h + 16 : mark.y - 6), "text-anchor": "middle", "data-part": "label" }, text))
          }
        }
      }
      nodes.push(svg("g", { "data-part": "labels" }, out))
    }
  } else {
    const baseV = spark ? scale.lo : Math.min(Math.max(0, scale.lo), scale.hi)
    keys.forEach((_, k) => {
      pts.push(
        m.rows.map((_, i) => {
          const p = spans[k][i]
          if (!p) return null
          const v = vals[k][i] ?? 0
          const topV = stack ? (v >= 0 ? p[1] : p[0]) : v
          const bottomV = stack ? (v >= 0 ? p[0] : p[1]) : baseV
          return { x: pos(i), y: v2p(topV), y0: v2p(bottomV), v: vals[k][i] }
        }),
      )
    })
    nodes.push(crosshair)
    if (area) {
      keys.forEach((key, k) => {
        const e = entity(key)
        const g = svg("g", { "data-part": "series", "data-key": key, style: { "--c": e.color } })
        let fill = null
        if (o.gradient) {
          const id = `${s.id}-fill-${k}`
          defs.append(svg("linearGradient", { id, x1: 0, y1: 0, x2: 0, y2: 1, style: { "--c": e.color } }, svg("stop", { offset: "5%", "data-part": "stop-start" }), svg("stop", { offset: "95%", "data-part": "stop-end" })))
          fill = `url(#${id})`
        }
        for (const seg of chartSegments(joined(key) ? pts[k].filter(Boolean) : pts[k])) {
          const topPath = chartCurve(seg, curve)
          const bottomPath = chartCurve(seg.map(p => ({ x: p.x, y: p.y0 })).reverse(), curve).replace(/^M/, "L")
          const el = svg("path", { d: `${topPath}${bottomPath}Z`, "data-part": "area" })
          if (spark) el.setAttribute("data-muted", "")
          if (fill) {
            el.style.fill = fill
            el.setAttribute("data-gradient", "")
          }
          g.append(el)
        }
        marksGroup.append(g)
      })
    }
    keys.forEach((key, k) => {
      const e = entity(key)
      const g = svg("g", { "data-part": "series", "data-key": key, style: { "--c": e.color } })
      const dots = o.dots && !spark
      const last = spark ? pts[k].findLast(Boolean) : null
      for (const seg of chartSegments(joined(key) ? pts[k].filter(Boolean) : pts[k])) {
        const el = svg("path", { d: chartCurve(seg, curve), "data-part": "line", pathLength: "1" })
        if (spark) el.setAttribute("data-muted", "")
        g.append(el)
        if (seg.length === 1 && !dots && seg[0] !== last) g.append(svg("circle", { cx: chartRound(seg[0].x), cy: chartRound(seg[0].y), r: 4, "data-part": "dot", "data-muted": spark }))
      }
      if (dots) for (const p of pts[k]) if (p) g.append(svg("circle", { cx: chartRound(p.x), cy: chartRound(p.y), r: 4, "data-part": "dot" }))
      if (last) g.append(svg("circle", { cx: chartRound(last.x), cy: chartRound(last.y), r: 4, "data-part": "dot", "data-accent": "" }))
      marksGroup.append(g)
    })
    nodes.push(marksGroup)
    if (labels) {
      const out = []
      const used = []
      keys.forEach((_, k) => {
        const i = pts[k].findLastIndex(Boolean)
        if (i < 0 || vals[k][i] == null) return
        const p = pts[k][i]
        const text = f.value(vals[k][i])
        const w = chartWidth(text, font.label)
        const x = Math.min(Math.max(p.x, w / 2), W - w / 2)
        const y = p.y - 10
        if (used.some(u => Math.abs(u.y - y) < 14 && Math.abs(u.x - x) < (u.w + w) / 2 + 4)) return
        used.push({ x, y, w })
        out.push(svg("text", { x: chartRound(x), y: chartRound(y), "text-anchor": "middle", "data-part": "label" }, text))
      })
      nodes.push(svg("g", { "data-part": "labels" }, out))
    }
  }
  if (refs) nodes.push(...refs)
  nodes.push(active)
  const markAt = a => {
    const list = marks[a.sub] ?? []
    return list[a.index] ?? null
  }
  const deactivate = () => {
    cursor.removeAttribute("data-active")
    crosshair.removeAttribute("data-active")
    marksGroup.removeAttribute("data-hover")
    for (const el of marksGroup.querySelectorAll("[data-active]")) el.removeAttribute("data-active")
    active.replaceChildren()
  }
  return {
    nodes,
    count: keys.length ? n : 0,
    subs: bar ? Math.max(1, keys.length) : 1,
    stacked: !!stack,
    horizontal,
    snap: bar ? null : a => pos(a.index),
    row: a => a.index,
    hit(px, py) {
      if (!n || !keys.length) return null
      const along = horizontal ? py : px
      let index = bar ? Math.floor((along - cstart) / band) : n === 1 ? 0 : Math.round(((along - cstart) / clen) * (n - 1))
      if (m.time) {
        let best = Infinity
        for (let i = 0; i < n; i++) {
          const d = Math.abs(pos(i) - along)
          if (d < best) {
            best = d
            index = i
          }
        }
      }
      index = Math.max(0, Math.min(n - 1, index))
      let sub = 0
      if (bar && keys.length > 1) {
        if (stack) {
          const at = horizontal ? px : py
          let dist = Infinity
          keys.forEach((_, k) => {
            const mk = marks[k][index]
            if (!mk || !mk.el) return
            const c0 = horizontal ? mk.x : mk.y
            const c1 = horizontal ? mk.x + mk.w : mk.y + mk.h
            const d = at < c0 ? c0 - at : at > c1 ? at - c1 : 0
            if (d < dist) {
              dist = d
              sub = k
            }
          })
        } else {
          const offset = (horizontal ? py : px) - (pos(index) - gw / 2)
          sub = Math.max(0, Math.min(keys.length - 1, Math.floor(offset / (thick + GAP))))
        }
      }
      return { index, sub }
    },
    anchor(a) {
      if (bar) {
        const mk = markAt(a)
        if (!mk) return horizontal ? { x: v2p(0), y: pos(a.index) } : { x: pos(a.index), y: v2p(0) }
        return horizontal ? { x: mk.dir === "left" ? mk.x : mk.x + mk.w, y: mk.y + mk.h / 2 } : { x: mk.x + mk.w / 2, y: mk.dir === "down" ? mk.y + mk.h : mk.y }
      }
      let y = pt + ph
      for (const list of pts) if (list[a.index]) y = Math.min(y, list[a.index].y)
      return { x: pos(a.index), y }
    },
    tip(a) {
      let total = 0
      let size = 0
      const items = keys.map((key, k) => {
        const e = entity(key)
        const v = vals[k][a.index]
        total += v ?? 0
        size += Math.abs(v ?? 0)
        return { key, label: e.label, icon: e.icon, color: o.diverging && (v ?? 0) < 0 ? "var(--chart-negative)" : e.color, value: v == null ? "–" : f.value(v), active: bar && keys.length > 1 && k === a.sub, v }
      })
      if (stack === "expand") for (const it of items) it.extra = size ? f.percent((it.v ?? 0) / size) : null
      if (stack && keys.length > 1) items.push({ key: null, label: stringFor(s.root, "total"), value: f.value(total), total: true })
      return { label: f.xLabel(a.index), items, key: bar ? keys[a.sub] : null }
    },
    activate(a) {
      deactivate()
      if (bar) {
        if (horizontal) chartSet(cursor, { x: pl, y: pos(a.index) - band / 2, width: pw, height: band })
        else chartSet(cursor, { x: pos(a.index) - band / 2, y: pt, width: band, height: ph })
        cursor.setAttribute("data-active", "")
        const el = markAt(a)?.el
        if (el) {
          el.setAttribute("data-active", "")
          if (keys.length > 1 || n > 1) marksGroup.setAttribute("data-hover", "")
        }
        return
      }
      const x = chartRound(pos(a.index))
      chartSet(crosshair, { x1: x, x2: x })
      crosshair.setAttribute("data-active", "")
      keys.forEach((key, k) => {
        const p = pts[k][a.index]
        if (p) active.append(svg("circle", { cx: chartRound(p.x), cy: chartRound(p.y), r: 5, "data-part": "dot", "data-active": "", style: { "--c": entity(key).color } }))
      })
    },
    deactivate,
  }
}

function chartReferences(c, nodes, p) {
  const { m, font } = c
  const { pl, pt, pw, ph, v2p, horizontal } = p
  const bands = svg("g", { "data-part": "references" })
  const lines = svg("g", { "data-part": "references" })
  const labels = svg("g", { "data-part": "reference-labels" })
  const used = []
  const crisp = v => Math.round(v2p(v)) + 0.5
  const fits = b => b.x0 >= pl - 0.5 && b.x1 <= pl + pw + 0.5 && b.y0 >= pt - 0.5 && b.y1 <= pt + ph + 0.5 && !used.some(u => b.x0 < u.x1 && b.x1 > u.x0 && b.y0 < u.y1 && b.y1 > u.y0)
  for (const r of m.references) {
    const a = r.band ? Math.max(p.lo, Math.min(r.from, r.to)) : r.value
    const b = r.band ? Math.min(p.hi, Math.max(r.from, r.to)) : r.value
    if (a > p.hi || b < p.lo || a > b) continue
    const style = { "--r": r.color }
    const edges = r.band ? [r.from, r.to].filter(v => v >= p.lo && v <= p.hi) : [r.value]
    if (r.band) {
      const [u, v] = [v2p(a), v2p(b)].sort((x, y) => x - y)
      bands.append(horizontal ? svg("rect", { x: chartRound(u), y: pt, width: chartRound(v - u), height: ph, "data-part": "reference-band", style }) : svg("rect", { x: pl, y: chartRound(u), width: pw, height: chartRound(v - u), "data-part": "reference-band", style }))
    }
    for (const v of edges) {
      const q = crisp(v)
      lines.append(horizontal ? svg("line", { x1: q, x2: q, y1: pt, y2: pt + ph, "data-part": "reference-line", style }) : svg("line", { x1: pl, x2: pl + pw, y1: q, y2: q, "data-part": "reference-line", style }))
    }
    if (!p.labels || !r.label) continue
    const text = chartFit(r.label, Math.max(8, pw - 8), font.tick)
    const w = chartWidth(text, font.tick)
    const lo = Math.min(v2p(a), v2p(b))
    const hi = Math.max(v2p(a), v2p(b))
    const cands = []
    if (horizontal) {
      const ys = r.position === "start" ? [pt + ph - 4, pt + 15] : [pt + 15, pt + ph - 4]
      for (const y of ys) {
        if (r.band && hi - lo >= w + 8) cands.push([lo + 4, y, "start"])
        cands.push([hi + 4, y, "start"], [lo - 4, y, "end"])
      }
    } else {
      const xs = r.position === "start" ? [[pl + 4, "start"], [pl + pw - 4, "end"]] : [[pl + pw - 4, "end"], [pl + 4, "start"]]
      for (const [x, anchor] of xs) {
        if (r.band && hi - lo >= 18) cands.push([x, lo + 15, anchor])
        cands.push([x, lo - 4, anchor], [x, hi + 15, anchor])
      }
    }
    for (const [x, y, anchor] of cands) {
      const x0 = anchor === "end" ? x - w : x
      const box = { x0, x1: x0 + w, y0: y - 11, y1: y + 3 }
      if (!fits(box)) continue
      used.push(box)
      labels.append(svg("text", { x: chartRound(x), y: chartRound(y), "text-anchor": anchor, "data-part": "reference-label" }, text))
      break
    }
  }
  nodes.push(bands)
  return [lines, labels]
}

function chartTimeAxis(c, t0, t1, tpos, clen) {
  const { m, f, W, font } = c
  for (const [unit, step, ms] of TIME_STEPS) {
    if ((m.dateOnly && ms < DAY) || (t1 - t0) / ms > clen / 16) continue
    const ticks = chartTimeTicks(t0, t1, unit, step, m.clock).map(t => {
      const text = f.timeTick(t, unit)
      const w = chartWidth(text, font.tick)
      return { t, text, w, x: Math.min(Math.max(tpos(t), w / 2), W - w / 2) }
    })
    if (ticks.length && ticks.every((k, j) => !j || k.x - k.w / 2 - (ticks[j - 1].x + ticks[j - 1].w / 2) >= 24)) return ticks
  }
  const text = f.timeTick(t0, m.dateOnly ? "day" : "minute")
  const w = chartWidth(text, font.tick)
  return [{ t: t0, text, w, x: Math.min(Math.max(tpos(t0), w / 2), W - w / 2) }]
}

function chartSet(el, attrs) {
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(chartRound(v)))
}

function chartPie(c) {
  const { s, m, f, W, H, font } = c
  const o = s.opts
  const donut = m.type === "donut"
  const vk = m.valueKey
  const list = []
  m.rows.forEach((r, i) => {
    const key = chartCategory(r, m.x, i)
    if (s.hidden.has(key)) return
    list.push({ i, key, v: Math.max(0, chartNum(r?.[vk]) ?? 0), e: m.byKey.get(key) })
  })
  const total = list.reduce((a, d) => a + d.v, 0)
  const mode = o.labels === true ? "value" : o.labels || null
  const inside = o.labelPosition === "inside"
  const text = d => (mode === "percent" ? f.percent(total ? d.v / total : 0) : mode === "name" ? d.e.label : f.value(d.v))
  const lift = o.highlight != null ? 8 : 4
  let R = Math.min(W, H) / 2 - lift - 2
  if (mode && !inside) {
    const lw = list.reduce((a, d) => Math.max(a, chartWidth(text(d), font.label)), 0)
    R = Math.min(R, H / 2 - 20, W / 2 - lw - 16)
  }
  R = Math.max(8, R)
  const cx = W / 2
  const cy = H / 2
  const ri = donut ? R * (o.innerRadius ?? 0.6) : 0
  let acc = 0
  const slices = list.map(d => {
    const a0 = acc
    acc += total ? (d.v / total) * TAU : 0
    return { ...d, a0, a1: acc, el: null }
  })
  const nodes = []
  const g = svg("g", { "data-part": "slices" })
  if (!total) g.append(svg("path", { d: chartSector(cx, cy, ri, R, 0, TAU), "data-part": "track" }))
  for (const sl of slices) {
    if (sl.a1 - sl.a0 <= 0) continue
    const ro = R + (o.highlight === sl.i ? 8 : 0)
    sl.el = svg("path", { d: chartSector(cx, cy, ri, ro, sl.a0, sl.a1), "data-part": "slice", style: { "--c": sl.e.color } })
    if (o.highlight === sl.i) sl.el.setAttribute("data-highlight", "")
    g.append(sl.el)
  }
  nodes.push(g)
  if (mode && total) {
    const out = []
    const placed = { left: [], right: [] }
    for (const sl of slices) {
      if (!sl.el) continue
      const mid = (sl.a0 + sl.a1) / 2
      const t = text(sl)
      const w = chartWidth(t, font.label)
      if (inside) {
        const rm = donut ? (ri + R) / 2 : R * 0.62
        const sweep = sl.a1 - sl.a0
        const chord = sweep >= Math.PI ? rm * 2 : 2 * rm * Math.sin(sweep / 2)
        if (chord < w + 10 || R - ri < 16) continue
        const [x, y] = chartPolar(cx, cy, rm, mid)
        out.push(svg("text", { x: chartRound(x), y: chartRound(y), dy: "0.35em", "text-anchor": "middle", "data-part": "label", "data-ink": c.ink(sl.e.color) }, t))
      } else {
        const [x, y] = chartPolar(cx, cy, R + 10, mid)
        const sin = Math.sin(mid)
        const side = sin >= 0 ? placed.right : placed.left
        if (side.some(py => Math.abs(py - y) < 14)) continue
        side.push(y)
        out.push(svg("text", { x: chartRound(x), y: chartRound(y), dy: "0.35em", "text-anchor": sin > 0.15 ? "start" : sin < -0.15 ? "end" : "middle", "data-part": "label" }, t))
      }
    }
    nodes.push(svg("g", { "data-part": "labels" }, out))
  }
  if (donut && o.center) nodes.push(chartCenter(c, cx, cy, total, false))
  const visible = slices.filter(sl => sl.el)
  const deactivate = () => {
    g.removeAttribute("data-hover")
    for (const sl of visible) {
      sl.el.removeAttribute("data-active")
      sl.el.style.transform = ""
    }
  }
  return {
    nodes,
    count: visible.length,
    subs: 1,
    horizontal: false,
    snap: null,
    row: a => visible[a.index]?.i ?? a.index,
    hit(px, py) {
      const dx = px - cx
      const dy = py - cy
      const r = Math.hypot(dx, dy)
      if (r < ri - 2 || r > R + lift + 10) return null
      const a = (Math.atan2(dx, -dy) + TAU) % TAU
      const index = visible.findIndex(sl => a >= sl.a0 && a < sl.a1)
      return index < 0 ? null : { index, sub: 0 }
    },
    anchor(a) {
      const sl = visible[a.index]
      const [x, y] = chartPolar(cx, cy, donut ? (ri + R) / 2 : R * 0.7, (sl.a0 + sl.a1) / 2)
      return { x, y }
    },
    tip(a) {
      const sl = visible[a.index]
      return { label: null, key: sl.key, items: [{ key: sl.key, label: sl.e.label, icon: sl.e.icon, color: sl.e.color, value: f.value(sl.v), extra: total ? f.percent(sl.v / total) : null }] }
    },
    activate(a) {
      deactivate()
      const sl = visible[a.index]
      if (!sl) return
      const mid = (sl.a0 + sl.a1) / 2
      sl.el.setAttribute("data-active", "")
      if (visible.length > 1) {
        g.setAttribute("data-hover", "")
        if (!sl.el.hasAttribute("data-highlight")) sl.el.style.transform = `translate(${chartRound(Math.sin(mid) * 4)}px, ${chartRound(-Math.cos(mid) * 4)}px)`
      }
    },
    deactivate,
  }
}

function chartCenter(c, cx, cy, total, half) {
  const { s, m, f } = c
  const o = s.opts
  const spec = typeof o.center === "object" ? o.center : {}
  const value = spec.value ?? total
  const vk = m.valueKey
  const label = spec.label ?? (vk == null ? null : chartLabel(m.config, vk))
  const text = typeof value === "number" ? f.value(value) : String(value)
  const vy = half ? cy - 16 : label ? cy - 4 : cy
  return svg(
    "text",
    { "data-part": "center", "text-anchor": "middle" },
    svg("tspan", { x: chartRound(cx), y: chartRound(vy), dy: half ? "0" : "0.35em", "data-part": "center-value" }, text),
    label ? svg("tspan", { x: chartRound(cx), y: chartRound(half ? cy + 4 : cy + 22), dy: half ? "0" : "0.35em", "data-part": "center-label" }, label) : null,
  )
}

function chartRadar(c) {
  const { s, m, f, W, H, font, keys } = c
  const o = s.opts
  const n = m.rows.length
  const texts = m.rows.map((_, i) => f.xTick(i))
  const lw = texts.reduce((a, t) => Math.max(a, chartWidth(t, font.tick)), 0)
  const R = Math.max(8, Math.min(W / 2 - lw - 14, H / 2 - 24))
  const cx = W / 2
  const cy = H / 2
  const vals = keys.map(k => m.rows.map(r => chartNum(r?.[k])))
  let max = 0
  for (const row of vals) for (const v of row) if (v != null) max = Math.max(max, v)
  const scale = chartTicks(0, o.max ?? (max || 1), 4)
  const top = o.max ?? scale.hi
  const ang = i => (i / Math.max(1, n)) * TAU
  const rad = v => (Math.max(0, v ?? 0) / top) * R
  const gridType = o.grid === false ? "none" : o.grid ?? "polygon"
  const nodes = []
  if (gridType !== "none" && n) {
    const g = svg("g", { "data-part": "grid" })
    for (const v of scale.ticks.filter(t => t > 0 && t <= top)) {
      const r = rad(v)
      if (gridType === "circle") g.append(svg("circle", { cx, cy, r: chartRound(r) }))
      else g.append(svg("polygon", { points: m.rows.map((_, i) => chartPoint(cx, cy, r, ang(i))).join(" ") }))
    }
    for (let i = 0; i < n; i++) {
      const [x, y] = chartPolar(cx, cy, R, ang(i))
      g.append(svg("line", { x1: cx, y1: cy, x2: chartRound(x), y2: chartRound(y) }))
    }
    nodes.push(g)
  }
  nodes.push(
    svg(
      "g",
      { "data-part": "axis", "data-axis": "category" },
      texts.map((t, i) => {
        const a = ang(i)
        const [x, y] = chartPolar(cx, cy, R + 10, a)
        const sin = Math.sin(a)
        const cos = Math.cos(a)
        return svg("text", { x: chartRound(x), y: chartRound(y), dy: cos > 0.5 ? "0" : cos < -0.5 ? "0.71em" : "0.35em", "text-anchor": Math.abs(sin) < 0.15 ? "middle" : sin > 0 ? "start" : "end" }, t)
      }),
    ),
  )
  const spoke = svg("line", { "data-part": "crosshair", x1: cx, y1: cy, x2: cx, y2: cy })
  nodes.push(spoke)
  const marksGroup = svg("g", { "data-part": "marks" })
  const pts = keys.map((_, k) => m.rows.map((_, i) => chartPolar(cx, cy, rad(vals[k][i]), ang(i))))
  keys.forEach((key, k) => {
    const e = m.byKey.get(key)
    const g = svg("g", { "data-part": "series", "data-key": key, style: { "--c": e.color } })
    if (n) g.append(svg("path", { d: `M${pts[k].map(p => p.map(chartRound).join(",")).join("L")}Z`, "data-part": "shape", "data-fill": o.fill === false ? "none" : null }))
    if (o.dots) for (const p of pts[k]) g.append(svg("circle", { cx: chartRound(p[0]), cy: chartRound(p[1]), r: 4, "data-part": "dot" }))
    marksGroup.append(g)
  })
  nodes.push(marksGroup)
  const active = svg("g", { "data-part": "active" })
  nodes.push(active)
  const deactivate = () => {
    spoke.removeAttribute("data-active")
    active.replaceChildren()
  }
  return {
    nodes,
    count: keys.length ? n : 0,
    subs: 1,
    horizontal: false,
    snap: null,
    row: a => a.index,
    hit(px, py) {
      if (!n) return null
      const dx = px - cx
      const dy = py - cy
      if (Math.hypot(dx, dy) > R + lw + 18) return null
      const a = (Math.atan2(dx, -dy) + TAU) % TAU
      return { index: Math.round(a / (TAU / n)) % n, sub: 0 }
    },
    anchor(a) {
      let best = [cx, cy]
      let r = -1
      keys.forEach((_, k) => {
        const v = rad(vals[k][a.index])
        if (v > r) {
          r = v
          best = pts[k][a.index]
        }
      })
      return { x: best[0], y: best[1] }
    },
    tip(a) {
      return { label: f.xLabel(a.index), key: null, items: keys.map((key, k) => { const e = m.byKey.get(key); const v = vals[k][a.index]; return { key, label: e.label, icon: e.icon, color: e.color, value: v == null ? "–" : f.value(v) } }) }
    },
    activate(a) {
      deactivate()
      const [x, y] = chartPolar(cx, cy, R, ang(a.index))
      chartSet(spoke, { x2: x, y2: y })
      spoke.setAttribute("data-active", "")
      keys.forEach((key, k) => {
        const p = pts[k][a.index]
        active.append(svg("circle", { cx: chartRound(p[0]), cy: chartRound(p[1]), r: 5, "data-part": "dot", "data-active": "", style: { "--c": m.byKey.get(key).color } }))
      })
    },
    deactivate,
  }
}

function chartRadial(c) {
  const { s, m, f, W, H, font, keys } = c
  const o = s.opts
  const stacked = !!o.stacked
  const deg = Math.PI / 180
  const start = (o.startAngle ?? 0) * deg
  let end = (o.endAngle ?? 360) * deg
  if (end <= start) end = start + TAU
  const span = Math.min(TAU, end - start)
  const items = []
  if (stacked) keys.forEach(key => items.push({ key, e: m.byKey.get(key), v: Math.max(0, chartNum(m.rows[0]?.[key]) ?? 0), i: 0 }))
  else {
    m.rows.forEach((r, i) => {
      const key = chartCategory(r, m.x, i)
      if (!s.hidden.has(key)) items.push({ key, e: m.byKey.get(key), v: Math.max(0, chartNum(r?.[m.valueKey]) ?? 0), i })
    })
  }
  const sum = items.reduce((a, d) => a + d.v, 0)
  const peak = items.reduce((a, d) => Math.max(a, d.v), 0)
  const max = o.max ?? (stacked ? sum : peak > 0 ? chartTicks(0, peak, 4).hi : 0)
  const scaleMax = max > 0 ? max : 1
  let x0 = 0
  let x1 = 0
  let y0 = 0
  let y1 = 0
  const angles = []
  for (let t = 0; t <= 96; t++) angles.push(start + (span * t) / 96)
  for (let q = Math.ceil(start / (Math.PI / 2)); q * (Math.PI / 2) <= start + span; q++) angles.push(q * (Math.PI / 2))
  for (const a of angles) {
    const sx = Math.sin(a)
    const sy = -Math.cos(a)
    x0 = Math.min(x0, sx)
    x1 = Math.max(x1, sx)
    y0 = Math.min(y0, sy)
    y1 = Math.max(y1, sy)
  }
  const R = Math.max(8, Math.min((W - 8) / (x1 - x0), (H - 8) / (y1 - y0)))
  const cx = W / 2 - ((x0 + x1) / 2) * R
  const cy = H / 2 - ((y0 + y1) / 2) * R
  const rings = stacked ? 1 : Math.max(1, items.length)
  const inner = R * (o.innerRadius ?? (rings > 1 ? 0.3 : 0.7))
  const outer = R * (o.outerRadius ?? 1)
  const band = (outer - inner) / rings
  const thick = Math.max(2, Math.min(o.barSize ?? BAR_MAX, rings > 1 ? band * 0.8 : band))
  const ring = j => {
    const ro = rings > 1 ? inner + band * (j + 1) - (band - thick) / 2 : outer
    return [ro - thick, ro]
  }
  const nodes = []
  const defs = svg("defs")
  nodes.push(defs)
  if (o.grid) {
    const g = svg("g", { "data-part": "grid" })
    for (let j = 0; j <= rings; j++) g.append(svg("circle", { cx: chartRound(cx), cy: chartRound(cy), r: chartRound(rings > 1 ? inner + band * j : j ? outer : outer - thick) }))
    nodes.push(g)
  }
  if (o.track !== false) {
    const g = svg("g", { "data-part": "tracks" })
    for (let j = 0; j < rings; j++) {
      const [ri, ro] = ring(j)
      g.append(svg("path", { d: chartSector(cx, cy, ri, ro, start, start + (o.track === "full" ? TAU : span)), "data-part": "track" }))
    }
    nodes.push(g)
  }
  const marksGroup = svg("g", { "data-part": "marks", "data-stacked": stacked || null })
  const arcs = []
  let acc = start
  const lastK = stacked ? items.findLastIndex(d => d.v > 0) : -1
  items.forEach((d, j) => {
    const [ri, ro] = ring(stacked ? 0 : j)
    const a0 = stacked ? acc : start
    const a1 = a0 + Math.min(span, (span * d.v) / scaleMax)
    acc = a1
    const el = a1 - a0 > 1e-4 ? svg("path", { d: chartArcBar(cx, cy, ri, ro, a0, a1, !stacked || j === lastK ? RADIUS : 0), "data-part": "arc", style: { "--c": d.e.color } }) : null
    if (el) marksGroup.append(el)
    arcs.push({ ...d, ri, ro, a0, a1, el })
  })
  nodes.push(marksGroup)
  if (o.labels && !stacked) {
    const out = []
    arcs.forEach((d, j) => {
      if (!d.el) return
      const rm = (d.ri + d.ro) / 2
      const w = chartWidth(d.e.label, font.label)
      if (d.ro - d.ri < 12 || rm * (d.a1 - d.a0) < w + 16) return
      const id = `${s.id}-arc-${j}`
      defs.append(svg("path", { id, d: chartArc(cx, cy, rm, d.a0, Math.min(d.a1, d.a0 + TAU - 0.01)) }))
      out.push(svg("text", { "data-part": "label", "data-ink": c.ink(d.e.color), dy: "0.35em" }, svg("textPath", { href: `#${id}`, startOffset: 8 }, d.e.label)))
    })
    nodes.push(svg("g", { "data-part": "labels" }, out))
  }
  if (o.center) nodes.push(chartCenter(c, cx, cy, stacked || items.length !== 1 ? sum : items[0].v, span <= Math.PI + 1e-6))
  const deactivate = () => {
    marksGroup.removeAttribute("data-hover")
    for (const d of arcs) d.el?.removeAttribute("data-active")
  }
  return {
    nodes,
    count: arcs.length,
    subs: 1,
    horizontal: false,
    snap: null,
    row: a => arcs[a.index]?.i ?? 0,
    hit(px, py) {
      const dx = px - cx
      const dy = py - cy
      const r = Math.hypot(dx, dy)
      if (stacked) {
        const d0 = arcs[0]
        if (!d0 || r < d0.ri - 6 || r > d0.ro + 6) return null
        let a = (Math.atan2(dx, -dy) + TAU) % TAU
        while (a < start) a += TAU
        const index = arcs.findIndex(d => a >= d.a0 && a < d.a1)
        return index < 0 ? null : { index, sub: 0 }
      }
      const index = arcs.findIndex(d => r >= d.ri - GAP && r <= d.ro + GAP)
      return index < 0 ? null : { index, sub: 0 }
    },
    anchor(a) {
      const d = arcs[a.index]
      const [x, y] = chartPolar(cx, cy, d.ro, d.a1)
      return { x, y }
    },
    tip(a) {
      const d = arcs[a.index]
      if (stacked) return { label: m.x == null ? null : f.xLabel(0), key: d.key, items: arcs.map((it, k) => ({ key: it.key, label: it.e.label, icon: it.e.icon, color: it.e.color, value: f.value(it.v), active: arcs.length > 1 && k === a.index })) }
      return { label: null, key: d.key, items: [{ key: d.key, label: d.e.label, icon: d.e.icon, color: d.e.color, value: f.value(d.v), extra: o.max ? f.percent(d.v / scaleMax) : null }] }
    },
    activate(a) {
      deactivate()
      const d = arcs[a.index]
      if (!d?.el) return
      d.el.setAttribute("data-active", "")
      if (arcs.length > 1) marksGroup.setAttribute("data-hover", "")
    },
    deactivate,
  }
}

function chartSummary(c) {
  const { s, m, f, keys } = c
  const o = s.opts
  if (o.summary) return String(o.summary)
  const say = (key, params) => stringFor(s.root, key, params)
  const name = chartName(s, m)
  const head = o.label ? `${name}, ${o.label}.` : `${name}.`
  if (!m.rows.length) return `${head} ${say("noData")}`
  if (m.byCategory) {
    const parts = []
    let total = 0
    const rows = []
    m.rows.forEach((r, i) => {
      const key = chartCategory(r, m.x, i)
      if (s.hidden.has(key)) return
      const v = Math.max(0, chartNum(r?.[m.valueKey]) ?? 0)
      total += v
      rows.push([m.byKey.get(key).label, v])
    })
    if (!rows.length) return `${head} ${say("allHidden")}`
    for (const [label, v] of rows) parts.push(`${label} ${f.value(v)}${total && m.type !== "radial" ? ` (${f.percent(v / total)})` : ""}`)
    return `${head} ${parts.join(", ")}.`
  }
  if (!keys.length) return `${head} ${say("allHidden")}`
  if (m.type === "radial") return `${head} ${keys.map(k => `${m.byKey.get(k).label} ${f.value(chartNum(m.rows[0]?.[k]) ?? 0)}`).join(", ")}.`
  const n = m.rows.length
  const range = n === 1 ? say("onePoint", { x: f.xLabel(0) }) : say("points", { count: chartNumber(f.locale, {}).format(n), from: f.xLabel(0), to: f.xLabel(n - 1) })
  const per = keys.map(k => {
    const vs = m.rows.map(r => chartNum(r?.[k])).filter(v => v !== null)
    if (!vs.length) return say("noValues", { label: m.byKey.get(k).label })
    const lo = vs.reduce((a, v) => Math.min(a, v), Infinity)
    const hi = vs.reduce((a, v) => Math.max(a, v), -Infinity)
    const last = vs.at(-1)
    return m.sparkline ? say("sparklineRange", { low: f.value(lo), high: f.value(hi), latest: f.value(last) }) : say("seriesRange", { label: m.byKey.get(k).label, low: f.value(lo), high: f.value(hi) })
  })
  const refs = m.references.map(r => ` ${chartReferenceText(s, f, r)}.`).join("")
  if (m.sparkline) return `${head} ${range}, ${per.join("; ")}.${refs}`
  return `${head} ${new Intl.ListFormat(f.locale, { type: "conjunction" }).format(keys.map(k => m.byKey.get(k).label))}, ${range}. ${per.join(". ")}.${refs}`
}

function chartReferenceText(s, f, r) {
  const label = r.label || stringFor(s.root, "reference")
  return r.band ? stringFor(s.root, "referenceBand", { label, from: f.value(Math.min(r.from, r.to)), to: f.value(Math.max(r.from, r.to)) }) : stringFor(s.root, "referenceAt", { label, value: f.value(r.value) })
}

function chartName(s, m) {
  return stringFor(s.root, m.sparkline ? "sparkline" : `${m.type}Chart`)
}

function chartPointer(s, e) {
  if (s.view === "table" || !s.geom || s.destroyed) return
  const box = s.els.svg.getBoundingClientRect()
  const px = e.clientX - box.left
  const py = e.clientY - box.top
  const a = s.geom.hit(px, py)
  if (!a) {
    if (s.source === "pointer") chartHideTip(s)
    return
  }
  s.last = a
  chartShowTip(s, a, "pointer", { x: s.geom.snap ? s.geom.snap(a) : px, y: py })
}

function chartKey(s, e) {
  const g = s.geom
  if (!g || e.altKey || e.ctrlKey || e.metaKey) return
  if (e.key === "Escape") {
    if (!s.els.tip.hidden) {
      e.preventDefault()
      chartHideTip(s)
    }
    return
  }
  if (!g.count) return
  const next = chartStep(g, s.active ?? s.last, e.key)
  if (!next) return
  e.preventDefault()
  s.last = next
  chartShowTip(s, next, "keyboard")
}

function chartStep(g, a, key) {
  const keys = ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"]
  if (!keys.includes(key)) return null
  const n = g.count
  if (!a) return { index: key === "End" ? n - 1 : 0, sub: 0 }
  let { index, sub } = a
  if (key === "Home") index = 0
  else if (key === "End") index = n - 1
  else if (g.subs <= 1) index += key === "ArrowLeft" || key === "ArrowUp" ? -1 : 1
  else {
    const along = g.horizontal ? ["ArrowUp", "ArrowDown"] : ["ArrowLeft", "ArrowRight"]
    if (along.includes(key)) index += key === along[0] ? -1 : 1
    else if (g.horizontal) sub += key === "ArrowRight" ? 1 : -1
    else if (g.stacked) sub += key === "ArrowUp" ? 1 : -1
    else sub += key === "ArrowDown" ? 1 : -1
  }
  return { index: Math.max(0, Math.min(n - 1, index)), sub: Math.max(0, Math.min(g.subs - 1, sub)) }
}

function chartShowTip(s, a, source, point) {
  const g = s.geom
  if (!g || !a || a.index >= g.count) return
  const changed = !s.active || s.active.index !== a.index || s.active.sub !== a.sub
  const { tip, live } = s.els
  s.active = { index: a.index, sub: a.sub }
  s.source = source
  g.activate(s.active)
  const data = g.tip(s.active)
  chartTipContent(s, data)
  const opening = tip.hidden
  tip.hidden = false
  tip.dataset.state = "open"
  const at = point ?? g.anchor(s.active)
  if (opening) tip.style.transition = "none"
  chartPlaceTip(s, at.x, at.y)
  if (opening) {
    void tip.offsetWidth
    tip.style.transition = ""
  }
  s.release ??= dismissable(tip, () => chartHideTip(s), { ignore: [s.root] })
  if (source === "keyboard" && (changed || opening)) live.textContent = chartSpeak(data)
  if (changed) {
    const index = g.row(s.active)
    emit(s.root, "chart:active", { index, key: data.key ?? null, row: s.model.rows[index] ?? null })
  }
}

function chartTipContent(s, data) {
  const o = s.opts.tooltip ?? {}
  const kids = []
  if (!o.hideLabel && data.label) kids.push(h("div", { "data-slot": "chart-tooltip-label" }, data.label))
  kids.push(
    h(
      "div",
      { "data-slot": "chart-tooltip-items" },
      data.items.map(it =>
        h(
          "div",
          { "data-slot": "chart-tooltip-item", "data-active": it.active || null, "data-total": it.total || null },
          it.total || o.hideIndicator ? null : h("span", { "data-slot": "chart-tooltip-indicator", style: { "--c": it.color } }),
          it.icon ? chartIconNode(it.icon) : null,
          h("span", { "data-slot": "chart-tooltip-name" }, it.label),
          h("span", { "data-slot": "chart-tooltip-value" }, it.value, it.extra ? h("span", { "data-slot": "chart-tooltip-extra" }, it.extra) : null),
        ),
      ),
    ),
  )
  s.els.tip.replaceChildren(...kids)
}

function chartSpeak(data) {
  const items = data.items.map(it => `${it.label} ${it.value}${it.extra ? ` (${it.extra})` : ""}`).join(", ")
  return data.label ? `${data.label}: ${items}` : items
}

function chartPlaceTip(s, x, y) {
  const tip = s.els.tip
  const pw = s.width
  const ph = s.height
  const tw = tip.offsetWidth
  const th = tip.offsetHeight
  let left = x + 12
  if (left + tw > pw) left = x - 12 - tw
  if (left < 0) left = Math.max(0, Math.min(pw - tw, x - tw / 2))
  const top = Math.max(Math.min(0, ph - th), Math.min(y - th / 2, ph - th))
  tip.style.transform = `translate(${Math.round(left)}px, ${Math.round(top)}px)`
}

function chartHideTip(s) {
  s.release?.()
  s.release = null
  const tip = s.els?.tip
  if (tip && !tip.hidden) {
    tip.hidden = true
    tip.dataset.state = "closed"
  }
  s.geom?.deactivate()
  if (s.active) {
    s.active = null
    s.source = null
    if (!s.destroyed) emit(s.root, "chart:active", null)
  }
}

function chartLegend(s, m) {
  const legend = s.els.legend
  const keys = m.byCategory ? m.entities.map(e => e.key) : m.series
  const show = !m.sparkline && s.opts.legend !== false && keys.length >= 2
  legend.hidden = !show
  if (!show) {
    legend.replaceChildren()
    return
  }
  const shape = m.type === "line" ? "line" : "rect"
  const items = keys.map(key => {
    const e = m.byKey.get(key)
    return h(
      "button",
      { type: "button", "data-slot": "chart-legend-item", "data-key": key, "aria-pressed": String(!s.hidden.has(key)), onclick: () => chartToggle(s, key) },
      h("span", { "data-slot": "chart-legend-indicator", "data-shape": shape, style: { "--c": e.color } }),
      e.icon ? chartIconNode(e.icon) : null,
      h("span", { "data-slot": "chart-legend-label" }, e.label),
    )
  })
  legend.replaceChildren(...items)
  setRoving(items, items[0])
}

function chartToggle(s, key) {
  const visible = s.hidden.has(key)
  if (visible) s.hidden.delete(key)
  else s.hidden.add(key)
  for (const b of s.els.legend.querySelectorAll('[data-slot="chart-legend-item"]')) if (b.dataset.key === key) b.setAttribute("aria-pressed", String(visible))
  chartHideTip(s)
  s.last = null
  chartRender(s)
  emit(s.root, "chart:legend", { key, visible, hidden: [...s.hidden] })
}

function chartTable(s, m) {
  const f = chartFormats(s, m)
  const o = s.opts
  const caption = o.label ? `${o.label}` : chartName(s, m)
  const xName = o.xLabel ?? (m.x == null ? "#" : chartLabel(m.config, m.x))
  let cells
  if (m.byCategory) {
    const vk = m.valueKey
    const total = m.rows.reduce((a, r) => a + Math.max(0, chartNum(r?.[vk]) ?? 0), 0)
    cells = [[xName, vk == null ? stringFor(s.root, "value") : chartLabel(m.config, vk), stringFor(s.root, "share")]]
    m.rows.forEach((r, i) => {
      const v = chartNum(r?.[vk])
      cells.push([f.xLabel(i), v == null ? "–" : f.value(v), total && v != null ? f.percent(Math.max(0, v) / total) : "–"])
    })
  } else {
    cells = [[xName, ...m.series.map(k => m.byKey.get(k).label)]]
    m.rows.forEach((r, i) => cells.push([f.xLabel(i), ...m.series.map(k => (chartNum(r?.[k]) == null ? "–" : f.value(chartNum(r[k]))))]))
  }
  if (m.sparkline) cells = cells[0].map((_, c) => cells.map(row => row[c]))
  const table = h(
    "table",
    null,
    h("caption", { class: "sr-only" }, caption),
    h("thead", null, h("tr", null, cells[0].map(t => h("th", { scope: "col" }, t)))),
    h("tbody", null, cells.slice(1).map(row => h("tr", null, row.map((t, i) => (i === 0 ? h("th", { scope: "row" }, t) : h("td", null, t)))))),
  )
  s.els.table.setAttribute("aria-label", stringFor(s.root, "tableOf", { caption }))
  const refs = m.references.length
    ? h(
        "table",
        { "data-part": "references" },
        h("caption", { class: "sr-only" }, stringFor(s.root, "references")),
        h("thead", null, h("tr", null, h("th", { scope: "col" }, stringFor(s.root, "reference")), h("th", { scope: "col" }, stringFor(s.root, "value")))),
        h("tbody", null, m.references.map(r => h("tr", null, h("th", { scope: "row" }, r.label || stringFor(s.root, "reference")), h("td", null, r.band ? `${f.value(Math.min(r.from, r.to))}–${f.value(Math.max(r.from, r.to))}` : f.value(r.value))))),
      )
    : null
  s.els.table.replaceChildren(table, ...(refs ? [refs] : []))
}

function chartView(s, view, render = true) {
  s.view = view
  const isTable = view === "table"
  const { plot, table, legend, toggle } = s.els
  if (isTable && !plot.hidden) {
    const hgt = plot.offsetHeight
    if (hgt) table.style.height = `${hgt}px`
  }
  if (isTable) chartHideTip(s)
  plot.hidden = isTable
  table.hidden = !isTable
  legend.style.visibility = isTable ? "hidden" : ""
  toggle.setAttribute("aria-pressed", String(isTable))
  chartAttr(s, "data-view", view)
  if (!isTable && render) {
    const box = plot.getBoundingClientRect()
    s.width = Math.floor(box.width)
    s.height = Math.floor(box.height)
    chartRender(s)
  }
}

function chartDestroy(s) {
  if (s.destroyed) return
  chartHideTip(s)
  s.destroyed = true
  cancelAnimationFrame(s.frame)
  s.ro.disconnect()
  mounted.delete(s)
  s.root.replaceChildren(...s.saved)
  for (const name of s.props) s.root.style.removeProperty(name)
  if (s.root.getAttribute("style") === "") s.root.removeAttribute("style")
  chartRestore(s.root, s.attrs)
  instances.delete(s.root)
}

function chartStatRender(t) {
  const o = t.opts
  const el = t.root
  const locale = chartLocale(o)
  t.spark?.destroy()
  t.spark = null
  chartAttrOn(el, t.attrs, "data-slot", "chart-stat")
  chartAttrOn(el, t.attrs, "role", "group")
  chartAttrOn(el, t.attrs, "aria-labelledby", t.labelId)
  const value = chartNum(o.value)
  const base = o.format && typeof o.format === "object" ? o.format : {}
  const text = value == null ? String(o.value ?? "–") : typeof o.format === "function" ? String(o.format(value)) : chartNumber(locale, Math.abs(value) >= 10000 && !base.notation ? chartCompact(base) : base).format(value)
  const delta = chartNum(o.delta)
  const kids = [
    h("div", { "data-slot": "chart-stat-header" }, h("p", { id: t.labelId, "data-slot": "chart-stat-label" }, o.label ?? ""), o.icon ? chartIconNode(o.icon) : null),
    h("p", { "data-slot": "chart-stat-value" }, h("data", { value: value ?? "" }, text)),
  ]
  if (delta != null) {
    const direction = delta > 0 ? "up" : delta < 0 ? "down" : "flat"
    const good = o.goodWhen === "down" ? direction === "down" : direction === "up"
    const tone = direction === "flat" ? "neutral" : good ? "good" : "bad"
    const dText = typeof o.deltaFormat === "function" ? String(o.deltaFormat(delta)) : chartNumber(locale, chartDigits({ style: "percent", maximumFractionDigits: 1, signDisplay: "exceptZero" }, o.deltaFormat)).format(delta)
    kids.push(
      h(
        "p",
        { "data-slot": "chart-stat-delta", "data-direction": direction, "data-tone": tone },
        icon(direction === "up" ? "trending-up" : direction === "down" ? "trending-down" : "minus"),
        h("span", { "data-slot": "chart-stat-change" }, dText),
        o.period ? h("span", { "data-slot": "chart-stat-period" }, o.period) : null,
      ),
    )
  }
  const trend = Array.isArray(o.trend) && o.trend.length ? h("div") : null
  if (trend) kids.push(h("div", { "data-slot": "chart-stat-trend" }, trend))
  if (o.description) kids.push(h("p", { "data-slot": "chart-stat-description" }, o.description))
  el.replaceChildren(...kids)
  if (trend) t.spark = sparkline(trend, o.trend, { label: stringFor(el, "trendOf", { label: o.label ?? stringFor(el, "value") }), format: o.format, locale: o.locale, ...o.trendOptions })
}
