import datetime
import re

START = "/demo?only=chat,input"

RECORD = """names => {
  window.__g4 = []
  for (const name of names) document.addEventListener(name, e => window.__g4.push({ type: e.type, id: e.target.id || e.target.getAttribute("data-slot"), detail: JSON.parse(JSON.stringify(e.detail ?? null)) }), true)
}"""


def record(page, *names):
    page.evaluate(RECORD, list(names))


def recorded(page, kind=None):
    events = page.evaluate("window.__g4 || []")
    return [e for e in events if kind is None or e["type"] == kind]


def today(page):
    return datetime.date.fromisoformat(page.evaluate("() => { const t = new Date(); return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}` }"))


def add_months(day, months):
    index = day.year * 12 + day.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    last = (datetime.date(year + (month == 12), month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    return datetime.date(year, month, min(day.day, last))


def active_day(page):
    return page.evaluate("() => document.activeElement?.closest('td')?.dataset.day ?? null")


def style(page, selector, prop, pseudo=None):
    return page.evaluate("([s, p, x]) => getComputedStyle(document.querySelector(s), x)[p]", [selector, prop, pseudo])


def resolve(page, css):
    return page.evaluate("c => { const d = document.createElement('div'); d.style.color = c; document.body.append(d); const v = getComputedStyle(d).color; d.remove(); return v }", css)


def rect(page, selector):
    return page.evaluate("s => { const r = document.querySelector(s).getBoundingClientRect(); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: r.width, height: r.height } }", selector)


def inline(t, box):
    if not t.rtl:
        return box
    out = dict(box)
    if "left" in box:
        out["left"], out["right"] = -box["right"], -box["left"]
    if "x" in box:
        out["x"] = -box["x"] - box["width"]
    return out


def key(t, name):
    return {"ArrowLeft": "ArrowRight", "ArrowRight": "ArrowLeft"}.get(name, name) if t.rtl else name


def long_date(page, day):
    return page.evaluate("d => new Intl.DateTimeFormat('en', { year: 'numeric', month: 'long', day: 'numeric' }).format(new Date(d + 'T12:00:00'))", day.isoformat())


def keyboard_mode(page):
    page.keyboard.press("Shift")


def tab(t, shift=False):
    key = "Alt+Tab" if t.engine == "webkit" else "Tab"
    t.page.keyboard.press(f"Shift+{key}" if shift else key)


FADE = """([sel, edges]) => {
  const el = document.querySelector(sel)
  const style = getComputedStyle(el)
  const box = document.createElement("div")
  Object.assign(box.style, { position: "fixed", left: "0", top: "0", width: `${el.getBoundingClientRect().width}px`, height: `${el.getBoundingClientRect().height}px`, visibility: "hidden" })
  document.body.append(box)
  const size = value => {
    const probe = document.createElement("div")
    probe.style.width = value || "0px"
    box.append(probe)
    const width = probe.getBoundingClientRect().width
    probe.remove()
    return width
  }
  const out = Object.fromEntries(edges.map(edge => [edge, size(style.getPropertyValue(`--scroll-fade-${edge}`))]))
  box.remove()
  return { ...out, timeline: CSS.supports("animation-timeline: scroll()") }
}"""


def fade(page, sel, edges="se"):
    return page.evaluate(FADE, [sel, list(edges)])


def wait_fade(page, sel, edge, faded, edges="se"):
    page.wait_for_function(f"([sel, edges, edge, faded]) => {{ const f = ({FADE})([sel, edges]); return !f.timeline || (f[edge] > 0) === faded }}", arg=[sel, list(edges), edge, faded])


def ring_width(page, locator):
    return locator.evaluate("e => (getComputedStyle(e).boxShadow.match(/0px 0px 0px (\\d+(?:\\.\\d+)?)px/g) || []).map(m => parseFloat(m.split(' ')[3])).filter(n => n > 0)")


def pin(locator):
    locator.evaluate("e => e.scrollIntoView({ block: 'start', behavior: 'instant' })")


def check_attachment(t):
    page = t.page
    section = t.section("attachment")
    demo = section.locator("#attachment-demo")
    vertical = demo.locator("[data-slot=attachment][data-orientation=vertical]").first
    assert round(vertical.bounding_box()["width"]) == 120
    media = demo.locator("[data-slot=attachment-media][data-variant=image]").first
    box = media.bounding_box()
    assert abs(box["width"] - box["height"]) <= 1
    sizes = page.evaluate("() => [...document.querySelectorAll('#attachment-sizes [data-slot=attachment-media]')].map(m => Math.round(m.getBoundingClientRect().width))")
    assert sizes == [40, 32, 28], sizes
    uploading = page.evaluate("() => getComputedStyle(document.querySelector('#attachment-images [data-state=uploading] [data-slot=attachment-media]')).opacity")
    assert uploading == "0.6", uploading
    error = section.locator("[data-slot=attachment][data-state=error]")
    assert resolve(page, "color-mix(in oklab, var(--destructive) 30%, transparent)") == error.evaluate("e => getComputedStyle(e).borderTopColor")
    assert section.locator("[data-slot=attachment][data-state=idle]").evaluate("e => getComputedStyle(e).borderTopStyle") == "dashed"
    action = section.locator("[data-slot=attachment-action]").first
    assert action.get_attribute("type") == "button" and round(action.bounding_box()["height"]) == 24
    assert section.locator("#attachment-group [data-slot=attachment-group]").get_attribute("data-scroll-fade") is None
    link = section.locator("#attachment-images [data-slot=attachment-trigger]").first
    assert link.get_attribute("href") == "demo/assets/g4-workspace.svg" and link.get_attribute("aria-label") == "Open workspace.png"
    count = section.locator("#attachment-images [data-slot=attachment]").count()
    section.locator("#attachment-images [data-attachment-remove]").first.click()
    assert section.locator("#attachment-images [data-slot=attachment]").count() == count - 1
    trigger = section.locator("#attachment-preview")
    trigger.click()
    assert section.locator("#attachment-status").inner_text() == "Opened the preview of research-summary.pdf."
    keyboard_mode(page)
    section.locator("#attachment-copy-link").focus()
    page.keyboard.press("Enter")
    assert section.locator("#attachment-status").inner_text() == "Copied the link to research-summary.pdf."
    ring = section.locator("#attachment-trigger [data-slot=attachment]").evaluate("e => getComputedStyle(e).boxShadow")
    assert ring != "none", ring
    section.locator("#attachment-trigger [data-attachment-remove]").focus()
    tab(t)
    preview = section.locator("#attachment-preview")
    assert preview.evaluate("e => e === document.activeElement && e.matches(':focus-visible')")
    outline = preview.evaluate("e => [getComputedStyle(e).outlineStyle, getComputedStyle(e).outlineWidth]")
    assert outline[0] == "none", outline
    assert ring_width(page, section.locator("#attachment-trigger [data-slot=attachment]")) == [1]
    t.a11y()
    outline = preview.evaluate("e => [getComputedStyle(e).outlineStyle, getComputedStyle(e).outlineWidth]")
    assert outline == ["solid", "3px"], outline
    t.shot("attachment-states", section.locator("#attachment-states"))


def check_attachment_group_children(t):
    page = t.page
    t.section("attachment")
    result = page.evaluate("""async () => {
      const watched = new Set()
      const { observe, unobserve, disconnect } = ResizeObserver.prototype
      const owned = new WeakMap()
      ResizeObserver.prototype.observe = function (target, options) {
        watched.add(target)
        if (!owned.has(this)) owned.set(this, new Set())
        owned.get(this).add(target)
        return observe.call(this, target, options)
      }
      ResizeObserver.prototype.unobserve = function (target) {
        watched.delete(target)
        return unobserve.call(this, target)
      }
      ResizeObserver.prototype.disconnect = function () {
        for (const target of owned.get(this) ?? []) watched.delete(target)
        return disconnect.call(this)
      }
      const group = document.querySelector("#attachment-group [data-slot=attachment-group]")
      const parent = group.parentElement
      group.remove()
      await new Promise(r => setTimeout(r, 50))
      parent.append(group)
      await new Promise(r => setTimeout(r, 50))
      const child = group.lastElementChild
      child.remove()
      await new Promise(r => setTimeout(r, 100))
      Object.assign(ResizeObserver.prototype, { observe, unobserve, disconnect })
      return { kept: watched.has(child), attribute: group.hasAttribute("data-scroll-fade") }
    }""")
    assert result == {"kept": False, "attribute": False}, result


SHARED_RING = """async () => {
  document.documentElement.style.setProperty("--focus-ring", "rgb(1, 2, 3)")
  return true
}"""


def check_focus_ring_shared(t):
    page = t.page
    t.section("bubble")
    t.a11y()
    page.evaluate(SHARED_RING)
    keyboard_mode(page)
    targets = [
        ("#bubble-buttons button[data-slot=bubble-content]", "#bubble-buttons button[data-slot=bubble-content]"),
        ("#code-block-basic [data-slot=code-block-content]", "#code-block-basic [data-slot=code-block]"),
        ("#questionnaire-demo input[value=approvals]", "#questionnaire-demo [data-slot=questionnaire-choice][data-value=approvals]"),
        ("#calendar-demo select[data-kind=month]", "#calendar-demo [data-slot=calendar-dropdown-root]"),
    ]
    for focus, ring in targets:
        page.locator(focus).first.focus()
        page.wait_for_function("s => document.querySelector(s).getAnimations().every(a => a.playState !== 'running')", arg=ring)
        style = page.locator(ring).first.evaluate("e => { const s = getComputedStyle(e); return [s.outlineStyle, s.outlineWidth, s.outlineColor] }")
        assert style == ["solid", "3px", "rgb(1, 2, 3)"], (ring, style)


def check_bubble(t):
    page = t.page
    section = t.section("bubble")
    content = lambda variant: page.evaluate("v => getComputedStyle(document.querySelector(`#bubble-variants [data-slot=bubble]${v} > [data-slot=bubble-content]`)).backgroundColor", variant)
    assert page.evaluate("() => [...document.querySelectorAll('#bubble [data-slot=bubble]')].every(b => b.dataset.variant && b.dataset.align)")
    assert page.evaluate("() => [...document.querySelectorAll('#bubble [data-slot=bubble-reactions]')].every(r => ['top', 'bottom'].includes(r.dataset.side) && ['start', 'end'].includes(r.dataset.align))")
    assert content("[data-variant=default]") == resolve(page, "var(--primary)")
    assert content("[data-variant=muted]") == resolve(page, "var(--muted)")
    assert content("[data-variant=secondary]") == resolve(page, "var(--secondary)")
    tinted = content("[data-variant=tinted]")
    assert tinted not in (content("[data-variant=default]"), content("[data-variant=muted]"), "rgba(0, 0, 0, 0)"), tinted
    assert content("[data-variant=ghost]") == "rgba(0, 0, 0, 0)"
    destructive = page.evaluate("() => getComputedStyle(document.querySelector('#bubble-variants [data-variant=destructive] > [data-slot=bubble-content]')).color")
    assert destructive == resolve(page, "var(--destructive)")
    frame = inline(t, rect(page, "#bubble-demo"))
    end = inline(t, rect(page, "#bubble-demo > [data-slot=bubble][data-align=end]"))
    start = inline(t, rect(page, "#bubble-demo [data-slot=bubble-group] > [data-slot=bubble]"))
    assert abs(end["right"] - frame["right"]) <= 1 and abs(start["left"] - frame["left"]) <= 1
    assert end["width"] <= frame["width"] * 0.8 + 1
    reaction = rect(page, "#bubble-demo [data-slot=bubble-group] [data-slot=bubble-reactions]")
    bubble = rect(page, "#bubble-demo [data-slot=bubble-group] > [data-slot=bubble]:last-child [data-slot=bubble-content]")
    assert reaction["bottom"] > bubble["bottom"] and reaction["top"] < bubble["bottom"]
    top = rect(page, "#bubble-reactions [data-side=top]")
    above = rect(page, "#bubble-reactions [data-slot=bubble]:has([data-side=top]) > [data-slot=bubble-content]")
    assert top["top"] < above["top"]
    section.locator("#bubble-buttons button[data-slot=bubble-content]").first.click()
    assert section.locator("#bubble-status").inner_text() == "You picked: I forgot my password"
    keyboard_mode(page)
    section.locator("#bubble-buttons button[data-slot=bubble-content]").first.focus()
    tab(t)
    page.keyboard.press("Enter")
    assert section.locator("#bubble-status").inner_text() == "You picked: I need help with my subscription"
    focused = page.locator("#bubble-buttons button[data-slot=bubble-content]:focus")
    t.settle()
    assert ring_width(page, focused) == [3] and focused.evaluate("e => getComputedStyle(e).borderTopColor") == resolve(page, "var(--ring)")
    t.a11y()
    outline = page.evaluate("() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.outlineWidth] }")
    assert outline == ["solid", "3px"], outline
    toggle = section.locator("#bubble-more-toggle")
    before = len(section.locator("#bubble-more-text").inner_text())
    toggle.click()
    assert toggle.get_attribute("aria-expanded") == "true" and len(section.locator("#bubble-more-text").inner_text()) > before
    assert toggle.inner_text().startswith("Show less")
    section.locator("#bubble-run").click()
    assert section.locator("#bubble-run").is_disabled()
    t.shot("bubble-variants", section.locator("#bubble-variants"))


def check_calendar(t):
    page = t.page
    section = t.section("calendar")
    cal = section.locator("#calendar-demo")
    now = today(page)
    assert cal.locator("table[role=grid]").count() == 1
    heads = [h.strip() for h in cal.locator("[data-slot=calendar-weekday]").all_inner_texts()]
    assert heads == ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"], heads
    assert cal.locator("[data-slot=calendar-weekday]").first.get_attribute("aria-label") == "Monday"
    cell = cal.locator(f'td[data-day="{now.isoformat()}"]:not([data-outside])')
    assert cell.get_attribute("data-today") == "true" and cell.get_attribute("data-selected") == "true" and cell.get_attribute("aria-selected") == "true"
    assert cal.locator("input[type=hidden][name=date]").input_value() == now.isoformat()
    button = cell.locator("button")
    assert button.get_attribute("tabindex") == "0"
    label = button.get_attribute("aria-label")
    assert label.startswith("Today, ") and label.endswith(", selected"), label
    assert cal.locator("[data-calendar-day-button][tabindex='0']").count() == 1
    record(page, "calendar:change", "calendar:navigate")
    keyboard_mode(page)
    button.focus()
    page.keyboard.press(key(t, "ArrowRight"))
    assert active_day(page) == (now + datetime.timedelta(days=1)).isoformat()
    page.keyboard.press("ArrowDown")
    assert active_day(page) == (now + datetime.timedelta(days=8)).isoformat()
    page.keyboard.press("ArrowUp")
    page.keyboard.press(key(t, "ArrowLeft"))
    assert active_day(page) == now.isoformat()
    monday = now - datetime.timedelta(days=now.weekday())
    page.keyboard.press("Home")
    assert active_day(page) == monday.isoformat()
    page.keyboard.press("End")
    sunday = monday + datetime.timedelta(days=6)
    assert active_day(page) == sunday.isoformat()
    page.keyboard.press("PageDown")
    assert active_day(page) == add_months(sunday, 1).isoformat()
    page.keyboard.press("Shift+PageDown")
    ahead = min(add_months(add_months(sunday, 1), 12), datetime.date(now.year, 12, 31))
    assert active_day(page) == ahead.isoformat()
    caption = cal.locator("[role=status]").inner_text()
    assert str(ahead.year) in caption, caption
    page.keyboard.press("Shift+PageUp")
    page.keyboard.press("PageUp")
    picked = add_months(add_months(ahead, -12), -1)
    assert active_day(page) == picked.isoformat()
    page.keyboard.press("Enter")
    changes = recorded(page, "calendar:change")
    assert changes[-1]["detail"] == {"value": picked.isoformat(), "mode": "single", "source": "day"}, changes
    assert cal.locator("input[type=hidden][name=date]").input_value() == picked.isoformat()
    assert active_day(page) == picked.isoformat()
    assert len(recorded(page, "calendar:navigate")) >= 2
    t.shot("calendar-keyboard", cal)
    cal.locator("select[data-kind=month]").focus()
    cal.locator("select[data-kind=month]").select_option("0")
    assert "January" in cal.locator("[role=status]").inner_text()
    assert cal.locator("select[data-kind=month]").evaluate("s => document.activeElement === s")
    cal.locator("select[data-kind=year]").select_option("2025")
    assert cal.locator("[role=status]").inner_text() == "January 2025"
    cal.locator("[data-slot=calendar-button-next]").click()
    assert cal.locator("[role=status]").inner_text() == "February 2025"
    assert recorded(page, "calendar:navigate")[-1]["detail"] == {"value": "2025-02"}
    cal.locator("[data-slot=calendar-button-previous]").focus()
    page.keyboard.press("Enter")
    page.keyboard.press("Enter")
    assert cal.locator("[role=status]").inner_text() == "December 2024"
    assert cal.locator("[data-slot=calendar-button-previous]").evaluate("b => document.activeElement === b")


def check_calendar_range(t):
    page = t.page
    section = t.section("calendar")
    cal = section.locator("#calendar-range")
    assert cal.locator("[data-slot=calendar-month]").count() == 2
    assert cal.locator("table[role=grid]").first.get_attribute("aria-multiselectable") == "true"
    day = lambda d: cal.locator(f'td[data-day="{d}"]:not([data-outside])')
    assert day("2026-01-12").get_attribute("data-range-start") == "true"
    assert day("2026-01-20").get_attribute("data-range-middle") == "true"
    assert day("2026-02-11").get_attribute("data-range-end") == "true"
    assert day("2026-01-12").locator("button").evaluate("b => getComputedStyle(b).backgroundColor") == resolve(page, "var(--primary)")
    assert day("2026-01-20").locator("button").evaluate("b => getComputedStyle(b).backgroundColor") == resolve(page, "var(--muted)")
    record(page, "calendar:change")
    day("2026-01-05").locator("button").click()
    day("2026-01-20").locator("button").click()
    values = [e["detail"]["value"] for e in recorded(page, "calendar:change")]
    assert values == [{"from": "2026-01-05", "to": "2026-02-11"}, {"from": "2026-01-05", "to": "2026-01-20"}], values
    assert section.locator("#calendar-range-value").inner_text() == "Range: 2026-01-05 to 2026-01-20"
    day("2026-01-20").locator("button").click()
    assert recorded(page, "calendar:change")[-1]["detail"]["value"] == {"from": "2026-01-20", "to": "2026-01-20"}
    cell = day("2026-01-20")
    assert cell.get_attribute("data-range-start") == "true" and cell.get_attribute("data-range-end") == "true"
    t.shot("calendar-range", cal)
    now = today(page)
    page.evaluate("async d => (await import('/clanker-ui.js')).calendarSetMonth(document.getElementById('calendar-range'), d)", now.isoformat())
    tomorrow = (now + datetime.timedelta(days=1)).isoformat()
    if cal.locator(f'td[data-day="{tomorrow}"]').count():
        assert cal.locator(f'td[data-day="{tomorrow}"]').first.get_attribute("data-disabled") == "true"
    assert cal.locator("[data-slot=calendar-button-next]").get_attribute("aria-disabled") == "true"
    if not t.mobile:
        boxes = [inline(t, cal.locator("[data-slot=calendar-month]").nth(i).bounding_box()) for i in range(2)]
        assert boxes[1]["x"] > boxes[0]["x"] + boxes[0]["width"] - 1
    else:
        boxes = [cal.locator("[data-slot=calendar-month]").nth(i).bounding_box() for i in range(2)]
        assert boxes[1]["y"] > boxes[0]["y"] + boxes[0]["height"] - 1


def check_calendar_rules(t):
    page = t.page
    section = t.section("calendar")
    cal = section.locator("#calendar-multiple")
    day = lambda d: cal.locator(f'td[data-day="{d}"]:not([data-outside])')
    assert cal.locator("td[data-selected=true]").count() == 3
    assert cal.locator("[data-slot=calendar-button-previous]").get_attribute("aria-disabled") == "true"
    assert day("2026-03-07").locator("button").is_disabled()
    assert day("2026-03-07").get_attribute("data-disabled") == "true"
    record(page, "calendar:change")
    day("2026-03-04").locator("button").click()
    day("2026-03-10").locator("button").click()
    assert recorded(page, "calendar:change")[-1]["detail"]["value"] == ["2026-03-03", "2026-03-04", "2026-03-17"]
    keyboard_mode(page)
    day("2026-03-06").locator("button").focus()
    page.keyboard.press(key(t, "ArrowRight"))
    assert active_day(page) == "2026-03-09"
    page.keyboard.press("End")
    assert active_day(page) == "2026-03-13"
    page.keyboard.press("PageDown")
    assert active_day(page) == "2026-04-13"
    page.keyboard.press("PageDown")
    assert active_day(page) == "2026-04-30"
    assert cal.locator("[data-slot=calendar-button-next]").get_attribute("aria-disabled") == "true"
    booked = section.locator("#calendar-booked")
    assert booked.locator("td[data-day='2026-02-12'] button").is_disabled() and booked.locator("td[data-day='2026-02-26'] button").is_disabled()
    assert not booked.locator("td[data-day='2026-02-27'] button").is_disabled()
    booked.evaluate("e => e.setAttribute('dir', 'rtl')")
    booked.locator("td[data-day='2026-02-10'] button").focus()
    page.keyboard.press("ArrowRight")
    assert active_day(page) == "2026-02-09"
    t.shot("calendar-rules", section.locator("#calendar-multiple"))


def check_calendar_locale(t):
    page = t.page
    section = t.section("calendar")
    german = section.locator("#calendar-german")
    heads = [h.strip() for h in german.locator("[data-slot=calendar-weekday]").all_inner_texts()]
    assert heads == ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"], heads
    assert german.locator("[role=status]").inner_text() == "Dezember 2026"
    assert german.locator("select[data-kind=month] option").nth(11).inner_text().startswith("Dez")
    assert german.locator("select[data-kind=year]").count() == 0
    sunday = section.locator("#calendar-sunday")
    assert sunday.locator("[data-slot=calendar-weekday]").first.inner_text().strip() == "Su"
    assert sunday.locator("[data-slot=calendar-week]").count() == 6
    hidden = sunday.locator("td[data-hidden=true]")
    assert hidden.count() > 0 and hidden.locator("button").count() == 0
    assert hidden.first.evaluate("e => getComputedStyle(e).visibility") == "hidden"
    weeks = section.locator("#calendar-weeks")
    assert weeks.locator("[data-slot=calendar-week-number-header]").count() == 1
    numbers = [n.strip() for n in weeks.locator("[data-slot=calendar-week-number]").all_inner_texts()]
    assert numbers[0] == f"{datetime.date(2026, 1, 29).isocalendar().week:02d}" and numbers[1] == f"{datetime.date(2026, 2, 5).isocalendar().week:02d}", numbers
    assert weeks.locator("[data-slot=calendar-week-number]").first.get_attribute("scope") == "row"
    t.shot("calendar-locale", section.locator("#calendar-german"))


CALENDAR_EARLY = """async () => {
  const ui = await import("/clanker-ui.js")
  const form = ui.h("form", { id: "calendar-early-form", lang: "de" })
  document.getElementById("calendar").append(form)
  const early = ui.h("div", { "data-slot": "calendar", "data-month": "2026-12", "data-value": "2026-12-24" })
  ui.calendarSetValue(early, "2026-12-25")
  form.append(early)
  await new Promise(r => setTimeout(r, 50))
  const out = { caption: early.querySelector("[data-slot=calendar-caption-label]").textContent, value: ui.calendarGetValue(early) }
  form.reset()
  await new Promise(r => setTimeout(r, 50))
  out.reset = ui.calendarGetValue(early)
  form.remove()
  return out
}"""

CALENDAR_CAPTIONS = """async () => {
  const out = {}
  for (const lang of ["fa", "th", "ar-SA"]) {
    const el = document.createElement("div")
    el.setAttribute("data-slot", "calendar")
    el.setAttribute("data-lang", lang)
    el.setAttribute("data-month", "2026-10")
    document.getElementById("calendar").append(el)
    await new Promise(r => setTimeout(r, 20))
    const expected = new Intl.DateTimeFormat(lang, { month: "long", year: "numeric", calendar: "gregory" }).format(new Date(2026, 9, 15, 12))
    out[lang] = [el.querySelector("[data-slot=calendar-caption-label]").textContent, expected]
    el.remove()
  }
  return out
}"""


def check_calendar_lifecycle(t):
    page = t.page
    section = t.section("calendar")
    for lang, (caption, expected) in page.evaluate(CALENDAR_CAPTIONS).items():
        assert caption == expected, (lang, caption, expected)
    early = page.evaluate(CALENDAR_EARLY)
    assert early == {"caption": "Dezember 2026", "value": "2026-12-25", "reset": "2026-12-24"}, early
    booked = section.locator("#calendar-booked")
    booked.locator("td[data-day='2026-02-05'] button").click()
    page.evaluate("() => { const el = document.getElementById('calendar-booked'); window.__booked = [el, el.parentElement, el.nextSibling, el.querySelector('[role=status]')]; el.remove() }")
    page.wait_for_timeout(50)
    page.evaluate("() => { const [el, parent, next] = window.__booked; parent.insertBefore(el, next) }")
    page.wait_for_timeout(50)
    assert booked.locator("td[aria-selected=true]").get_attribute("data-day") == "2026-02-05"
    live = booked.locator("[role=status]")
    assert live.count() == 1 and live.get_attribute("aria-live") == "polite" and live.get_attribute("data-slot") == "calendar-caption-label"
    assert booked.locator("[data-slot=calendar-live]").count() == 0
    keyboard_mode(page)
    booked.locator("td[data-day='2026-02-05'] button").focus()
    page.keyboard.press(key(t, "ArrowRight"))
    page.keyboard.press("PageDown")
    assert active_day(page) == "2026-03-06"
    assert live.inner_text() == "March 2026"
    assert page.evaluate("() => document.querySelector('#calendar-booked [role=status]') === window.__booked[3]")


def check_date_picker_typed(t):
    page = t.page
    section = t.section("date-picker")
    field = section.locator("#date-picker-input-value")
    value = lambda: page.evaluate("async () => (await import('/clanker-ui.js')).calendarGetValue(document.querySelector('#date-picker-input [data-slot=calendar]'))")
    for text, expected in [("6/2/2025", "2025-06-02"), ("2025-6-3", "2025-06-03"), ("June 4, 2025", "2025-06-04"), ("jun 5 2025", "2025-06-05")]:
        field.fill(text)
        field.dispatch_event("change")
        assert value() == expected, (text, value())
        assert field.get_attribute("aria-invalid") is None
    for text in ["28.10.2026", "2/30/2025", "tomorrow", "6/2/25"]:
        field.fill(text)
        field.dispatch_event("change")
        assert value() == "2025-06-05", (text, value())
        assert field.get_attribute("aria-invalid") == "true" and field.input_value() == text
    field.fill("")
    field.dispatch_event("change")
    assert value() is None and field.get_attribute("aria-invalid") is None
    assert section.locator("#date-picker-input td[aria-selected=true]").count() == 0
    german = page.evaluate("""async () => {
      const ui = await import("/clanker-ui.js")
      const root = ui.h("div", { "data-slot": "date-picker", lang: "de" },
        ui.h("input", { "data-slot": "input", "data-date-picker-input": "", "aria-label": "Datum" }),
        ui.h("button", { type: "button", "data-slot": "button", "data-date-picker-trigger": "" }, "Datum"),
        ui.h("div", { "data-slot": "popover-content", "data-date-picker-content": "" }, ui.h("div", { "data-slot": "calendar" })))
      document.getElementById("date-picker").append(root)
      await new Promise(r => setTimeout(r, 20))
      const input = root.querySelector("input")
      const out = {}
      for (const text of ["28.10.2026", "1. Juni 2025", "3. März 2026"]) {
        input.value = text
        input.dispatchEvent(new Event("change", { bubbles: true }))
        out[text] = [ui.calendarGetValue(root.querySelector("[data-slot=calendar]")), input.value]
      }
      root.remove()
      return out
    }""")
    assert german == {"28.10.2026": ["2026-10-28", "28. Oktober 2026"], "1. Juni 2025": ["2025-06-01", "1. Juni 2025"], "3. März 2026": ["2026-03-03", "3. März 2026"]}, german


def check_strings_chat(t):
    page = t.page
    t.section("calendar")
    out = page.evaluate("""async () => {
      const { h, strings } = await import("/clanker-ui.js")
      const host = h("div", { "data-string-previous-month": "Prejšnji mesec", "data-string-today": "Danes, {date}", "data-string-selected": "{date}, izbrano", "data-string-week": "Teden {week}", "data-string-choose-year": "Izberi leto", "data-string-copy": "Kopiraj", "data-string-messages": "Sporočila", "data-string-scroll-to-end": "Na konec", "data-string-next": "Naprej", "data-string-question-of": "Vprašanje {current} od {total}", "data-string-pick-date": "Izberi datum" },
        h("div", { "data-slot": "calendar", "data-today": "2026-10-28", "data-value": "2026-10-28", "data-show-week-number": "", "data-caption-layout": "dropdown" }),
        h("div", { "data-slot": "code-block" }, h("button", { "data-slot": "code-block-copy-button" }), h("pre", { "data-slot": "code-block-content" }, "x")),
        h("div", { "data-slot": "message-scroller" }, h("div", { "data-slot": "message-scroller-viewport" }, h("div", { "data-slot": "message-scroller-content" })), h("button", { "data-slot": "message-scroller-button" })),
        h("form", { "data-slot": "questionnaire" }, h("div", { "data-slot": "questionnaire-progress" }), h("fieldset", { "data-slot": "questionnaire-item", name: "a" }), h("fieldset", { "data-slot": "questionnaire-item", name: "b" }), h("button", { "data-slot": "questionnaire-next" })),
        h("div", { "data-slot": "date-picker" }, h("button", { "data-slot": "button", "data-date-picker-trigger": "" }), h("div", { "data-slot": "popover-content", "data-date-picker-content": "" }, h("div", { "data-slot": "calendar" }))))
      strings.chooseMonth = "Izberi mesec"
      document.getElementById("calendar").append(host)
      await new Promise(r => setTimeout(r, 20))
      strings.chooseMonth = "Choose the Month"
      const cal = host.querySelector("[data-slot=calendar]")
      const out = {
        previous: cal.querySelector("[data-slot=calendar-button-previous]").getAttribute("aria-label"),
        day: cal.querySelector("td[data-day='2026-10-28'] button").getAttribute("aria-label").replace(/^(Danes, ).*(, izbrano)$/, "$1…$2"),
        week: cal.querySelector("[data-slot=calendar-week-number]").getAttribute("aria-label").replace(/\\d+/, "N"),
        month: cal.querySelector("[data-kind=month]").getAttribute("aria-label"),
        year: cal.querySelector("[data-kind=year]").getAttribute("aria-label"),
        copy: host.querySelector("[data-slot=code-block-copy-button]").getAttribute("aria-label"),
        messages: host.querySelector("[data-slot=message-scroller-viewport]").getAttribute("aria-label"),
        end: host.querySelector("[data-slot=message-scroller-button] .sr-only").textContent,
        next: host.querySelector("[data-slot=questionnaire-next]").textContent,
        progress: host.querySelector("[data-slot=questionnaire-progress]").textContent,
        pick: host.querySelector("[data-slot=date-picker-value]").textContent,
      }
      host.remove()
      return out
    }""")
    assert out == {"previous": "Prejšnji mesec", "day": "Danes, …, izbrano", "week": "Teden N", "month": "Izberi mesec", "year": "Izberi leto", "copy": "Kopiraj", "messages": "Sporočila", "end": "Na konec", "next": "Naprej", "progress": "Vprašanje 1 od 2", "pick": "Izberi datum"}, out


def check_calendar_form(t):
    page = t.page
    section = t.section("calendar")
    form = section.locator("#calendar-form")
    cal = form.locator("#calendar-large")
    hidden = cal.locator("input[type=hidden][name=stay]")
    assert hidden.input_value() == "2026-12-08/2026-12-18"
    size = cal.locator("td[data-day='2026-12-21'] button").bounding_box()
    assert round(size["width"]) == (44 if t.mobile else 48), size
    cal.locator("td[data-day='2026-12-21'] button").click()
    assert hidden.input_value() == "2026-12-08/2026-12-21"
    form.locator("button[type=submit]").click()
    assert section.locator("#calendar-form-value").inner_text() == "The form sent stay=2026-12-08/2026-12-21."
    form.locator("button[type=reset]").click()
    page.wait_for_function("() => document.querySelector('#calendar-large input[name=stay]').value === '2026-12-08/2026-12-18'")


def check_code_block(t):
    page = t.page
    section = t.section("code-block")
    block = section.locator("#code-block-header")
    copy = block.locator("[data-slot=code-block-copy-button]")
    assert copy.get_attribute("aria-label") == "Copy" and copy.evaluate("b => getComputedStyle(b).backgroundColor") == "rgba(0, 0, 0, 0)"
    if t.engine == "chromium":
        page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    record(page, "code-block:copy", "code-block:wrap")
    copy.evaluate("b => b.setAttribute('data-timeout', '1500')")
    copy.click()
    page.wait_for_function("() => document.querySelector('#code-block-header [data-slot=code-block-copy-button]').hasAttribute('data-copied')")
    assert copy.get_attribute("aria-label") == "Copied"
    assert copy.locator("svg.lucide-check").count() == 1
    assert copy.evaluate("b => b.nextElementSibling.getAttribute('aria-live') + '|' + b.nextElementSibling.textContent") == "polite|Copied"
    text = recorded(page, "code-block:copy")[0]["detail"]["value"]
    assert text.startswith("export function safeRedirect(next: string | undefined) {\n") and text.endswith("return next\n}"), repr(text)
    if t.engine == "chromium":
        assert page.evaluate("navigator.clipboard.readText()") == text
    page.wait_for_function("() => !document.querySelector('#code-block-header [data-slot=code-block-copy-button]').hasAttribute('data-copied')")
    assert copy.get_attribute("aria-label") == "Copy" and copy.locator("svg.lucide-copy").count() == 1
    numbered = section.locator("#code-block-actions [data-slot=code-block-content]")
    assert numbered.get_attribute("data-numbered") is not None and numbered.get_attribute("dir") == "ltr" and numbered.get_attribute("tabindex") == "0"
    lines = numbered.locator("[data-slot=code-block-line]")
    assert lines.count() == 6
    assert lines.nth(3).locator("[data-slot=code-block-line-content]").evaluate("e => e.textContent") == "\n"
    assert page.evaluate("() => getComputedStyle(document.querySelector('#code-block-actions [data-slot=code-block-line]'), '::before').content") in ("counter(line)", 'counter(line) / ""')
    wrap = section.locator("#code-block-actions [data-slot=code-block-wrap-button]")
    assert wrap.get_attribute("aria-pressed") == "false"
    assert numbered.evaluate("e => e.scrollWidth > e.clientWidth + 1")
    wrap.click()
    assert wrap.get_attribute("aria-pressed") == "true" and numbered.get_attribute("data-wrap") == "true"
    assert numbered.evaluate("e => e.scrollWidth <= e.clientWidth + 1")
    keyboard_mode(page)
    wrap.focus()
    page.keyboard.press("Space")
    assert wrap.get_attribute("aria-pressed") == "false" and numbered.get_attribute("data-wrap") is None
    assert [e["detail"]["value"] for e in recorded(page, "code-block:wrap")] == [True, False]
    copy2 = section.locator("#code-block-diff [data-slot=code-block-copy-button]")
    copy2.focus()
    page.keyboard.press("Enter")
    page.wait_for_function("() => (window.__g4 || []).filter(e => e.type === 'code-block:copy').length === 2")
    diff = recorded(page, "code-block:copy")[1]["detail"]["value"]
    assert diff.split("\n")[4] == "" and "+" not in diff and "−" not in diff, repr(diff)
    removed = page.evaluate("() => getComputedStyle(document.querySelector('#code-block-diff [data-variant=removed]'), '::after').content")
    assert removed == '"−"', removed
    start = section.locator("#code-block-lines [data-start-line]")
    assert start.evaluate("e => e.style.counterReset") == "line 13"
    basic = section.locator("#code-block-basic [data-slot=code-block-content]").first
    assert basic.get_attribute("data-scroll-fade") is None
    basic.focus()
    tab(t)
    tab(t, shift=True)
    assert basic.evaluate("e => document.activeElement === e && e.matches(':focus-visible')")
    frame = section.locator("#code-block-basic [data-slot=code-block]").first
    assert ring_width(page, frame) == [3] and frame.evaluate("e => getComputedStyle(e).borderTopColor") == resolve(page, "var(--ring)")
    t.a11y()
    ring = frame.evaluate("e => [getComputedStyle(e).outlineStyle, getComputedStyle(e).outlineWidth]")
    assert ring == ["solid", "3px"], ring
    floating = section.locator("#code-block-floating > [data-slot=code-block-actions]")
    page.mouse.move(0, 0)
    page.wait_for_function("() => getComputedStyle(document.querySelector('#code-block-floating > [data-slot=code-block-actions]')).opacity === '0'")
    section.locator("#code-block-floating").hover()
    page.wait_for_function("() => getComputedStyle(document.querySelector('#code-block-floating > [data-slot=code-block-actions]')).opacity === '1'")
    toggle = section.locator("#code-block-more-toggle")
    more = section.locator("#code-block-more-content")
    collapsed = more.bounding_box()["height"]
    toggle.click()
    assert toggle.get_attribute("aria-expanded") == "true" and more.get_attribute("data-collapsed") is None
    assert more.bounding_box()["height"] > collapsed
    destructive = section.locator("#code-block-small [data-variant=destructive]")
    assert destructive.evaluate("e => getComputedStyle(e).color") == resolve(page, "var(--destructive)")
    t.shot("code-block-lines", section.locator("#code-block-lines"))


def check_code_block_reinsert(t):
    page = t.page
    section = t.section("code-block")
    if t.engine == "chromium":
        page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    copy = section.locator("#code-block-header [data-slot=code-block-copy-button]")
    copy.click()
    page.wait_for_function("() => document.querySelector('#code-block-header [data-slot=code-block-copy-button]').hasAttribute('data-copied')")
    page.evaluate("() => { const b = document.querySelector('#code-block-header [data-slot=code-block-copy-button]'); window.__copy = [b, b.parentElement]; b.remove() }")
    page.wait_for_timeout(50)
    page.evaluate("() => { const [b, parent] = window.__copy; parent.append(b) }")
    page.wait_for_timeout(50)
    assert copy.get_attribute("aria-label") == "Copy" and copy.get_attribute("data-copied") is None
    assert copy.locator("svg.lucide-copy").count() == 1 and copy.locator("svg.lucide-check").count() == 0
    assert copy.evaluate("b => [...b.parentElement.children].filter(e => e.getAttribute('aria-live')).length") == 1
    assert copy.evaluate("b => b.nextElementSibling.getAttribute('aria-live') === 'polite' && b.nextElementSibling.textContent === ''")


def popup_open(page, root):
    return page.evaluate("s => document.querySelector(`${s} [data-date-picker-content]`).matches(':popover-open')", root)


def wait_popup(page, root, open=True):
    page.wait_for_function("([s, o]) => document.querySelector(`${s} [data-date-picker-content]`).matches(':popover-open') === o", arg=[root, open])


def check_date_picker(t):
    page = t.page
    section = t.section("date-picker")
    root = section.locator("#date-picker-demo")
    trigger = root.locator("[data-date-picker-trigger]")
    content = root.locator("[data-date-picker-content]")
    assert trigger.get_attribute("data-slot") == "button" and content.get_attribute("data-slot") == "popover-content"
    assert trigger.get_attribute("aria-haspopup") == "dialog" and trigger.get_attribute("aria-expanded") == "false"
    assert trigger.get_attribute("data-empty") == "true" and trigger.inner_text().strip() == "Pick a date"
    assert content.get_attribute("role") == "dialog"
    record(page, "date-picker:open", "date-picker:close", "calendar:change")
    trigger.click()
    wait_popup(page, "#date-picker-demo")
    assert trigger.get_attribute("aria-expanded") == "true" and content.get_attribute("data-state") == "open"
    now = today(page)
    assert page.evaluate("() => document.activeElement.getAttribute('data-slot')") == "calendar-button-previous"
    tab(t)
    assert page.evaluate("() => document.activeElement.getAttribute('data-slot')") == "calendar-button-next"
    tab(t)
    assert active_day(page) == now.isoformat()
    t.settle()
    box = inline(t, content.bounding_box())
    tbox = inline(t, trigger.bounding_box())
    assert box["y"] >= tbox["y"] + tbox["height"] and abs(box["x"] - tbox["x"]) <= 1, (box, tbox)
    assert content.evaluate("e => getComputedStyle(e).backgroundColor") == resolve(page, "var(--popover)")
    t.shot("date-picker-open", page)
    page.keyboard.press(key(t, "ArrowRight"))
    page.keyboard.press("Enter")
    wait_popup(page, "#date-picker-demo", False)
    tomorrow = now + datetime.timedelta(days=1)
    assert trigger.inner_text().strip() == long_date(page, tomorrow)
    assert trigger.get_attribute("data-empty") == "false" and trigger.get_attribute("aria-expanded") == "false"
    assert trigger.evaluate("b => document.activeElement === b")
    page.keyboard.press("Enter")
    wait_popup(page, "#date-picker-demo")
    assert page.evaluate("() => document.activeElement.getAttribute('data-slot')") == "calendar-button-previous"
    tab(t)
    tab(t)
    assert active_day(page) == tomorrow.isoformat()
    page.keyboard.press("Escape")
    wait_popup(page, "#date-picker-demo", False)
    assert trigger.evaluate("b => document.activeElement === b")
    assert [e["type"] for e in recorded(page) if e["type"].startswith("date-picker")] == ["date-picker:open", "date-picker:close", "date-picker:open", "date-picker:close"]
    trigger.click()
    wait_popup(page, "#date-picker-demo")
    section.locator("[data-demo=title]").click()
    wait_popup(page, "#date-picker-demo", False)
    rng = section.locator("#date-picker-range")
    rtrigger = rng.locator("[data-date-picker-trigger]")
    assert rtrigger.inner_text().strip() == "Jan 20, 2026 - Feb 09, 2026"
    rtrigger.click()
    wait_popup(page, "#date-picker-range")
    assert rng.locator("[data-slot=calendar-month]").count() == 2
    rng.locator("td[data-day='2026-01-25']:not([data-outside]) button").click()
    assert rtrigger.inner_text().strip() == "Jan 20, 2026 - Jan 25, 2026"
    assert popup_open(page, "#date-picker-range")
    t.shot("date-picker-range-open", page)
    page.keyboard.press("Escape")
    wait_popup(page, "#date-picker-range", False)
    presets = section.locator("#date-picker-presets")
    presets.locator("[data-date-picker-trigger]").click()
    wait_popup(page, "#date-picker-presets")
    preset = presets.locator("select[data-date-picker-preset]")
    assert preset.get_attribute("data-slot") == "native-select"
    preset.select_option("7")
    week = now + datetime.timedelta(days=7)
    assert presets.locator("[data-date-picker-trigger]").inner_text().strip() == long_date(page, week)
    assert presets.locator(f"td[data-day='{week.isoformat()}']:not([data-outside])").get_attribute("data-selected") == "true"
    t.shot("date-picker-presets-open", page)
    page.keyboard.press("Escape")
    wait_popup(page, "#date-picker-presets", False)


def check_date_picker_compositions(t):
    page = t.page
    section = t.section("date-picker")
    field = section.locator("#date-picker-input-value")
    assert field.input_value() == "June 1, 2025"
    record(page, "date-picker:open", "date-picker:close")
    field.fill("March 3, 2026")
    field.press("Tab")
    page.wait_for_function("() => document.querySelector('#date-picker-input td[data-day=\"2026-03-03\"]:not([data-outside])')?.dataset.selected === 'true'")
    assert field.input_value() == "March 3, 2026"
    field.focus()
    page.keyboard.press("ArrowDown")
    wait_popup(page, "#date-picker-input")
    assert page.evaluate("() => document.activeElement.getAttribute('data-slot')") == "calendar-button-previous"
    tab(t)
    tab(t)
    assert active_day(page) == "2026-03-03"
    t.shot("date-picker-input-open", page)
    page.keyboard.press(key(t, "ArrowRight"))
    page.keyboard.press("Enter")
    wait_popup(page, "#date-picker-input", False)
    assert field.input_value() == "March 4, 2026"
    assert section.locator("#date-picker-input [data-date-picker-trigger]").evaluate("b => document.activeElement === b")
    time = section.locator("#date-picker-time-value")
    assert time.input_value() == "10:30:00" and section.locator("label[for=date-picker-time-value]").inner_text() == "Time"
    section.locator("#date-picker-time [data-date-picker-trigger]").click()
    wait_popup(page, "#date-picker-time")
    assert section.locator("#date-picker-time [data-slot=calendar-dropdown]").count() == 2
    page.keyboard.press("Escape")
    wait_popup(page, "#date-picker-time", False)
    section.get_by_role("button", name="Schedule post").click()
    dialog = page.locator("#date-picker-dialog")
    page.wait_for_function("() => document.getElementById('date-picker-dialog').open")
    dialog.locator("[data-date-picker-trigger]").click()
    wait_popup(page, "#date-picker-dialog")
    t.shot("date-picker-dialog", page)
    dialog.locator("td[data-day='2026-11-15']:not([data-outside]) button").click()
    wait_popup(page, "#date-picker-dialog", False)
    assert dialog.locator("[data-date-picker-trigger]").evaluate("b => document.activeElement === b")
    assert page.evaluate("() => document.getElementById('date-picker-dialog').open")
    dialog.get_by_role("button", name="Save").click()
    page.wait_for_function("() => !document.getElementById('date-picker-dialog').open")
    assert section.locator("#date-picker-form-value").inner_text() == "Scheduled for 2026-11-15."
    rtl = section.locator("#date-picker-rtl")
    rtrigger = rtl.locator("[data-date-picker-trigger]")
    rtrigger.click()
    wait_popup(page, "#date-picker-rtl")
    t.settle()
    box = rtl.locator("[data-date-picker-content]").bounding_box()
    tbox = rtrigger.bounding_box()
    assert abs(box["x"] + box["width"] - tbox["x"] - tbox["width"]) <= 1, (box, tbox)
    assert rtl.locator("[data-slot=calendar]").evaluate("e => getComputedStyle(e).direction") == "rtl"
    t.shot("date-picker-rtl-open", page)
    page.keyboard.press("Escape")
    wait_popup(page, "#date-picker-rtl", False)
    assert [e["type"] for e in recorded(page)].count("date-picker:open") == 4

def check_marker(t):
    page = t.page
    section = t.section("marker")
    sep = "#marker-variants [data-variant=separator]"
    assert float(style(page, sep, "width", "::before").removesuffix("px")) > 10
    assert style(page, sep, "backgroundColor", "::after") == resolve(page, "var(--border)")
    assert style(page, "#marker-variants [data-variant=border]", "borderBottomWidth") == "1px"
    assert section.locator("#marker-demo [role=status] [data-slot=marker-content]").get_attribute("class") == "shimmer"
    assert style(page, "#marker-demo [data-slot=marker]", "color") == resolve(page, "var(--muted-foreground)")
    assert "underline" in style(page, "#marker-links a[data-slot=marker]", "textDecorationLine")
    assert section.locator("#marker-stacked").evaluate("e => getComputedStyle(e).flexDirection") == "column"
    section.locator("#marker-revert").click()
    assert section.locator("#marker-status-text").inner_text() == "You clicked the revert button."
    page.evaluate("() => { document.getElementById('marker-status-text').textContent = '' }")
    keyboard_mode(page)
    section.locator("#marker-links a[data-slot=marker]").focus()
    tab(t)
    assert page.evaluate("document.activeElement.id") == "marker-revert"
    page.keyboard.press("Enter")
    assert section.locator("#marker-status-text").inner_text() == "You clicked the revert button."


def check_message(t):
    page = t.page
    section = t.section("message")
    end = section.locator("#message-demo [data-slot=message][data-align=end]").first
    assert end.evaluate("e => getComputedStyle(e).flexDirection") == "row-reverse"
    with_footer = section.locator("#message-demo [data-slot=message]:has([data-slot=message-footer]) [data-slot=message-avatar]")
    assert with_footer.evaluate("e => getComputedStyle(e).translate") == "0px -32px"
    footer = section.locator("#message-demo [data-slot=message-footer]")
    assert footer.evaluate("e => getComputedStyle(e).justifyContent") == "flex-end"
    assert footer.evaluate("e => getComputedStyle(e).color") == resolve(page, "var(--muted-foreground)")
    avatar = section.locator("#message-demo [data-slot=message-avatar]").first.bounding_box()
    assert round(avatar["width"]) == 32 and round(avatar["height"]) == 32
    header = section.locator("#message-group [data-slot=message-header]")
    assert header.evaluate("e => getComputedStyle(e).paddingInlineStart") == "12px"
    empty = section.locator("#message-group [data-slot=message-avatar]").first.bounding_box()
    assert round(empty["width"]) == 32
    assert page.evaluate("() => [...document.querySelectorAll('#message [data-slot=message]')].every(m => ['start', 'end'].includes(m.dataset.align))")
    bubble = section.locator("#message-demo [data-slot=message][data-align=start] [data-slot=bubble]").first
    content = section.locator("#message-demo [data-slot=message][data-align=start] [data-slot=message-content]").first
    assert inline(t, bubble.bounding_box())["x"] - inline(t, content.bounding_box())["x"] <= 1
    like = section.locator("#message-actions [aria-label=Like]")
    like.click()
    assert like.get_attribute("aria-pressed") == "true"
    keyboard_mode(page)
    like.focus()
    page.keyboard.press("Space")
    assert like.get_attribute("aria-pressed") == "false"
    section.locator("#message-retry").click()
    assert "Delivered" in section.locator("#message-failed").inner_text()
    t.shot("message-actions", section.locator("#message-actions"))


SCROLLER = """sel => {
  const r = document.querySelector(sel)
  const v = r.querySelector('[data-slot=message-scroller-viewport]')
  return { top: v.scrollTop, max: v.scrollHeight - v.clientHeight, scrollable: r.getAttribute('data-scrollable'), buttons: Object.fromEntries([...r.querySelectorAll('[data-slot=message-scroller-button]')].map(b => [b.dataset.direction, { active: b.dataset.active, inert: b.inert, tab: b.tabIndex }])) }
}"""


def scroller(page, sel):
    return page.evaluate(SCROLLER, sel)


def wait_end(page, sel, active):
    page.wait_for_function("([sel, active]) => { const r = document.querySelector(sel); return r.querySelector('[data-slot=message-scroller-button][data-direction=end]').dataset.active === active }", arg=[sel, active], timeout=5000)


def still(page, sel):
    page.wait_for_function("""sel => new Promise(done => {
      const v = document.querySelector(sel + ' [data-slot=message-scroller-viewport]')
      let last = v.scrollTop
      let same = 0
      const tick = () => {
        if (v.scrollTop === last) same++
        else [last, same] = [v.scrollTop, 0]
        if (same > 5) done(true)
        else requestAnimationFrame(tick)
      }
      tick()
    })""", arg=sel)


def offset(page, sel, item):
    return page.evaluate("([sel, id]) => { const r = document.querySelector(sel); const v = r.querySelector('[data-slot=message-scroller-viewport]'); const i = r.querySelector(`[data-message-id='${id}']`); return i.getBoundingClientRect().top - v.getBoundingClientRect().top }", [sel, item])


def check_message_scroller(t):
    page = t.page
    section = t.section("message-scroller")
    main = "#message-scroller-main"
    viewport = section.locator(f"{main} [data-slot=message-scroller-viewport]")
    content = section.locator("#message-scroller-transcript")
    assert viewport.get_attribute("role") == "region" and viewport.get_attribute("aria-label") == "Conversation" and viewport.get_attribute("tabindex") == "0"
    assert content.get_attribute("role") == "log" and content.get_attribute("aria-relevant") == "additions"
    state = scroller(page, main)
    assert abs(state["top"] - state["max"]) <= 2, state
    assert state["buttons"]["end"] == {"active": "false", "inert": True, "tab": -1}, state
    button = section.locator(f"{main} [data-slot=message-scroller-button]")
    assert button.locator(".sr-only").inner_text() == "Scroll to end"
    record(page, "message-scroller:scrollable")
    viewport.hover()
    page.mouse.wheel(0, -400)
    wait_end(page, main, "true")
    state = scroller(page, main)
    assert "end" in state["scrollable"] and state["buttons"]["end"]["inert"] is False and state["buttons"]["end"]["tab"] == 0, state
    t.settle()
    t.shot("message-scroller-scrolled-up", section.locator("#message-scroller-chat"))
    button.click()
    wait_end(page, main, "false")
    page.wait_for_function("sel => { const v = document.querySelector(sel + ' [data-slot=message-scroller-viewport]'); return Math.abs(v.scrollTop - (v.scrollHeight - v.clientHeight)) <= 2 }", arg=main)
    assert page.evaluate("document.activeElement.getAttribute('data-slot')") == "message-scroller-viewport"
    assert [e["detail"]["end"] for e in recorded(page, "message-scroller:scrollable")][:2] == [True, False]
    keyboard_mode(page)
    viewport.focus()
    page.keyboard.press("PageUp")
    wait_end(page, main, "true")
    still(page, main)
    button.focus()
    page.keyboard.press("Enter")
    wait_end(page, main, "false")
    textarea = section.locator("#message-scroller-input")
    textarea.fill("Is the lockfile the only problem?")
    textarea.press("Enter")
    page.wait_for_function("() => document.querySelector('[data-message-id=u0]')")
    top = offset(page, main, "u0")
    assert 0 <= top <= 140, top
    assert content.get_attribute("aria-busy") == "true"
    page.wait_for_function("() => !document.getElementById('message-scroller-transcript').hasAttribute('aria-busy')", timeout=20000)
    assert section.locator("[data-message-id=a0] [data-slot=message-footer]").count() == 1
    assert section.locator("[data-message-id=a0] [data-slot=trace-collapsible-trigger] [data-slot=trace-icon]").count() == 2
    assert textarea.input_value() == "Can CI tell me which package changed?"
    page.wait_for_timeout(100)
    textarea.press("Enter")
    page.wait_for_function("() => document.querySelector('[data-message-id=a1] [data-slot=bubble-content]')", timeout=5000)
    viewport.hover()
    page.mouse.wheel(0, -300)
    page.wait_for_timeout(100)
    held = scroller(page, main)["top"]
    page.wait_for_function("() => !document.getElementById('message-scroller-transcript').hasAttribute('aria-busy')", timeout=20000)
    page.wait_for_timeout(100)
    after = scroller(page, main)
    assert abs(after["top"] - held) <= 4, (held, after)
    assert after["buttons"]["end"]["active"] == "true", after
    button.click()
    wait_end(page, main, "false")
    t.shot("message-scroller-chat", section.locator("#message-scroller-chat"))


FOLLOW = """async ([id, auto, early]) => {
  const ui = await import("/clanker-ui.js")
  document.getElementById(id)?.remove()
  const items = Array.from({ length: 20 }, (_, i) => ui.h("div", { "data-slot": "message-scroller-item", "data-message-id": `m${i}`, style: { height: "50px" } }, `Message ${i + 1}`, i === 19 ? ui.h("textarea", { "aria-label": "Reply" }) : null))
  const root = ui.h("div", { id, "data-slot": "message-scroller", "data-auto-scroll": auto ? "" : null, style: { height: "300px" } }, ui.h("div", { "data-slot": "message-scroller-viewport", "aria-label": id }, ui.h("div", { "data-slot": "message-scroller-content" }, items)))
  if (early) ui.messageScrollerScrollable(root)
  document.getElementById("message-scroller").append(root)
}"""

APPEND = """id => {
  const content = document.querySelector(`#${id} [data-slot=message-scroller-content]`)
  const item = document.createElement("div")
  item.setAttribute("data-slot", "message-scroller-item")
  item.style.height = "120px"
  item.textContent = "A new reply"
  content.append(item)
}"""

GAP = "id => { const v = document.querySelector(`#${id} [data-slot=message-scroller-viewport]`); return Math.round(v.scrollHeight - v.clientHeight - v.scrollTop) }"


def check_message_scroller_follow(t):
    page = t.page
    t.section("message-scroller")
    page.evaluate(FOLLOW, ["scroller-early", False, True])
    page.wait_for_function(f"id => ({GAP})(id) <= 2", arg="scroller-early", timeout=3000)
    page.evaluate(FOLLOW, ["scroller-follow", True, False])
    page.wait_for_function(f"id => ({GAP})(id) <= 2", arg="scroller-follow", timeout=3000)
    viewport = page.locator("#scroller-follow [data-slot=message-scroller-viewport]")
    viewport.scroll_into_view_if_needed()
    viewport.hover()
    page.mouse.wheel(0, 200)
    page.wait_for_timeout(200)
    page.evaluate(APPEND, "scroller-follow")
    page.wait_for_function(f"id => ({GAP})(id) <= 2", arg="scroller-follow", timeout=3000)
    page.locator("#scroller-follow textarea").focus()
    page.keyboard.type("one two")
    page.keyboard.press("Enter")
    page.keyboard.type("three")
    page.keyboard.press("ArrowUp")
    assert page.evaluate("document.activeElement.selectionStart") <= 7
    page.evaluate(APPEND, "scroller-follow")
    page.wait_for_function(f"id => ({GAP})(id) <= 2", arg="scroller-follow", timeout=3000)
    viewport.hover()
    page.mouse.wheel(0, -200)
    page.wait_for_timeout(200)
    page.evaluate(APPEND, "scroller-follow")
    page.wait_for_timeout(300)
    assert page.evaluate(GAP, "scroller-follow") > 100
    page.evaluate("() => { document.getElementById('scroller-early').remove(); document.getElementById('scroller-follow').remove() }")


def check_message_scroller_history(t):
    page = t.page
    section = t.section("message-scroller")
    sel = "#message-scroller-history"
    state = scroller(page, sel)
    assert abs(state["top"] - state["max"]) <= 2 and state["scrollable"] == "start", state
    assert state["buttons"]["start"]["active"] == "true" and state["buttons"]["end"]["active"] == "false", state
    visible = page.evaluate("async sel => (await import('/clanker-ui.js')).messageScrollerVisibility(document.querySelector(sel))", arg=sel)
    assert "h12-a" in visible["visibleMessageIds"], visible
    first = visible["visibleMessageIds"][0]
    before = offset(page, sel, first)
    section.locator("#message-scroller-load").click()
    page.wait_for_function("() => document.querySelector('[data-message-id=h1-q]')")
    page.wait_for_timeout(100)
    assert abs(offset(page, sel, first) - before) <= 2, (before, offset(page, sel, first))
    section.locator("#message-scroller-jump").click()
    page.wait_for_function("sel => { const r = document.querySelector(sel); const v = r.querySelector('[data-slot=message-scroller-viewport]'); const i = r.querySelector('[data-message-id=h1-q]'); return Math.abs(i.getBoundingClientRect().top - v.getBoundingClientRect().top - 16) <= 2 }", arg=sel, timeout=5000)
    section.locator("#message-scroller-latest").click()
    page.wait_for_function("sel => { const v = document.querySelector(sel + ' [data-slot=message-scroller-viewport]'); return Math.abs(v.scrollTop - (v.scrollHeight - v.clientHeight)) <= 2 }", arg=sel, timeout=5000)
    start = section.locator(f"{sel} [data-slot=message-scroller-button][data-direction=start]")
    start.click()
    page.wait_for_function("sel => document.querySelector(sel + ' [data-slot=message-scroller-viewport]').scrollTop <= 1", arg=sel, timeout=5000)
    page.wait_for_function("sel => document.querySelector(sel + ' [data-slot=message-scroller-button][data-direction=start]').dataset.active === 'false'", arg=sel, timeout=5000)
    t.shot("message-scroller-history", section.locator(sel))


def check_questionnaire(t):
    page = t.page
    section = t.section("questionnaire")
    form = section.locator("#questionnaire-demo")
    progress = form.locator("[data-slot=questionnaire-progress]")
    assert progress.inner_text() == "Question 1 of 3" and progress.get_attribute("role") == "progressbar" and progress.get_attribute("aria-valuenow") == "1"
    assert form.get_attribute("data-shortcuts") == "letters" and form.evaluate("f => f.noValidate")
    first = form.locator("fieldset[name=direction]")
    assert first.get_attribute("data-active") is not None and first.is_visible()
    assert not form.locator("fieldset[name=signals]").is_visible()
    assert not form.locator("[data-slot=questionnaire-previous]").is_visible() and not form.locator("[data-slot=questionnaire-skip]").is_visible()
    assert form.locator("[data-slot=questionnaire-next]").get_attribute("aria-keyshortcuts") == "Enter"
    shortcuts = [s.strip() for s in first.locator("[data-slot=questionnaire-choice-shortcut]").all_inner_texts()]
    assert shortcuts == ["A", "B", "C"], shortcuts
    assert first.locator("input[type=radio]").count() == 3
    record(page, "questionnaire:change", "questionnaire:status", "questionnaire:submit")
    form.locator("[data-slot=questionnaire-next]").click()
    error = first.locator("[data-slot=questionnaire-error]")
    assert error.is_visible() and error.get_attribute("role") == "alert" and error.inner_text() == "Choose an answer to continue."
    assert first.get_attribute("aria-invalid") == "true" and error.get_attribute("id") in first.get_attribute("aria-describedby")
    assert page.evaluate("document.activeElement.value") == "tool-calls"
    t.shot("questionnaire-invalid", form)
    page.keyboard.press("b")
    choice = first.locator("[data-slot=questionnaire-choice][data-value=approvals]")
    assert choice.get_attribute("data-checked") is not None and not error.is_visible()
    text = first.locator("[data-slot=questionnaire-input]")
    text.fill("A cost dashboard")
    assert choice.get_attribute("data-checked") is None and text.get_attribute("name") == "direction"
    first.locator("[data-slot=questionnaire-choice][data-value=handoffs]").click()
    assert text.get_attribute("name") is None and text.get_attribute("form") is None
    text.fill("A cost dashboard")
    assert text.get_attribute("name") == "direction" and text.evaluate("e => e.form?.id") == "questionnaire-demo"
    assert form.evaluate("f => new FormData(f).get('direction')") == "A cost dashboard"
    first.locator("[data-slot=questionnaire-choice][data-value=handoffs]").click()
    first.locator("input[value=handoffs]").focus()
    page.keyboard.press("Enter")
    second = form.locator("fieldset[name=signals]")
    page.wait_for_function("() => document.activeElement?.getAttribute('name') === 'signals'")
    assert progress.inner_text() == "Question 2 of 3" and second.get_attribute("data-multiple") is not None
    assert second.locator("input[type=checkbox]").count() == 4
    assert form.locator("[data-slot=questionnaire-skip]").is_visible() and form.locator("[data-slot=questionnaire-previous]").is_visible()
    page.keyboard.press("ArrowLeft")
    assert progress.inner_text() == "Question 1 of 3"
    page.keyboard.press("ArrowRight")
    assert progress.inner_text() == "Question 2 of 3"
    page.keyboard.press("a")
    page.keyboard.press("c")
    assert second.locator("[data-slot=questionnaire-choice][data-checked]").count() == 2
    page.keyboard.press("a")
    assert second.locator("[data-slot=questionnaire-choice][data-checked]").count() == 1
    form.locator("[data-slot=questionnaire-skip]").click()
    assert progress.inner_text() == "Question 3 of 3" and second.get_attribute("data-status") == "skipped"
    assert form.locator("[data-slot=questionnaire-submit]").is_visible() and not form.locator("[data-slot=questionnaire-next]").is_visible()
    third = form.locator("fieldset[name=timing]")
    third.locator("[data-slot=questionnaire-choice][data-value=now]").click()
    third.locator("input[value=now]").focus()
    page.keyboard.press("Control+Enter")
    page.wait_for_function("() => (window.__g4 || []).some(e => e.type === 'questionnaire:submit')")
    submit = recorded(page, "questionnaire:submit")[0]["detail"]
    assert submit["value"] == {"direction": "handoffs", "signals": [], "timing": "now"}, submit
    assert submit["status"] == {"direction": "answered", "signals": "skipped", "timing": "answered"}, submit
    assert section.locator("#questionnaire-result").inner_text() == "Agent plan saved. Direction: handoffs · Progress signals: None · Timing: now"
    changes = [e["detail"]["value"] for e in recorded(page, "questionnaire:change")]
    assert changes[:3] == ["signals", "direction", "signals"] and changes[-1] == "timing", changes
    statuses = [(e["detail"]["item"], e["detail"]["value"]) for e in recorded(page, "questionnaire:status")]
    assert ("signals", "skipped") in statuses and ("timing", "answered") in statuses, statuses
    t.shot("questionnaire-done", form)


def check_questionnaire_resume(t):
    page = t.page
    section = t.section("questionnaire")
    form = section.locator("#questionnaire-resume")
    progress = form.locator("[data-slot=questionnaire-progress]")
    assert progress.inner_text() == "Step 2 of 3" and progress.get_attribute("aria-valuetext") == "Step 2 of 3"
    detail = form.locator("fieldset[name=detail]")
    assert detail.is_visible() and detail.get_attribute("data-required") is None
    assert [s.strip() for s in detail.locator("[data-slot=questionnaire-choice-shortcut]:not([hidden])").all_inner_texts()] == ["1", "2"]
    assert detail.locator("[data-slot=questionnaire-choice][data-disabled]").count() == 1
    form.locator("[data-slot=questionnaire-next]").click()
    error = detail.locator("[data-slot=questionnaire-error]")
    assert error.is_visible() and error.inner_text() == "Pick a level of detail, or press Skip."
    page.keyboard.press("2")
    assert detail.locator("[data-value=complete]").get_attribute("data-checked") is not None
    detail.evaluate("f => f.focus()")
    page.keyboard.press("ArrowLeft")
    assert progress.inner_text() == "Step 1 of 3"
    assert form.locator("fieldset[name=prototype] [data-value=delegation]").get_attribute("data-checked") is not None
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    assert progress.inner_text() == "Step 3 of 3"
    section.locator("#questionnaire-toggle").click()
    assert progress.inner_text() == "Step 2 of 2"
    assert form.locator("[data-slot=questionnaire-submit]").is_visible()
    form.locator("[data-slot=questionnaire-submit]").click()
    assert section.locator("#questionnaire-resume-result").inner_text() == "Prototype: delegation · Detail: complete"
    section.locator("#questionnaire-toggle").click()
    assert progress.inner_text() == "Step 2 of 3"


QUESTIONNAIRE_ANSWERS = """async () => {
  const ui = await import("/clanker-ui.js")
  const form = ui.h("form", { id: "questionnaire-answers", "data-slot": "questionnaire", action: "#questionnaire" },
    ui.h("fieldset", { "data-slot": "questionnaire-item", name: "email", "data-required": "" },
      ui.h("legend", { "data-slot": "questionnaire-title" }, "Where should the report go?"),
      ui.h("div", { "data-slot": "questionnaire-choices" },
        ui.h("label", { "data-slot": "questionnaire-choice", "data-value": "none" }, "Do not send it"),
        ui.h("input", { type: "email", "data-slot": "questionnaire-input", "aria-label": "Email address" })),
      ui.h("p", { "data-slot": "questionnaire-error" })),
    ui.h("fieldset", { "data-slot": "questionnaire-item", name: "notes", "data-required": "" },
      ui.h("legend", { "data-slot": "questionnaire-title" }, "Notes"),
      ui.h("textarea", { "data-slot": "questionnaire-input", "aria-label": "Notes" }),
      ui.h("p", { "data-slot": "questionnaire-error" })),
    ui.h("div", { "data-slot": "questionnaire-actions" }, ui.h("button", { type: "button", "data-slot": "questionnaire-next" }), ui.h("button", { type: "submit", "data-slot": "questionnaire-submit" })))
  window.__answers = null
  form.addEventListener("submit", e => e.preventDefault())
  form.addEventListener("questionnaire:submit", e => { window.__answers = e.detail })
  document.getElementById("questionnaire").append(form)
}"""


def check_questionnaire_input_look(t):
    page = t.page
    t.section("questionnaire")
    page.evaluate(QUESTIONNAIRE_ANSWERS)
    looks = page.evaluate(
        """() => {
          const props = ["borderTopWidth", "borderTopColor", "borderTopLeftRadius", "backgroundColor", "boxShadow", "fontSize", "lineHeight", "color"]
          const read = (sel, pseudo) => { const cs = getComputedStyle(document.querySelector(sel), pseudo); return Object.fromEntries(props.map(p => [p, cs[p]])) }
          return {
            input: read('#input [data-slot="input"]'), answer: read('#questionnaire-answers input[data-slot="questionnaire-input"]'),
            textarea: read('[data-slot="textarea"]'), notes: read('#questionnaire-answers textarea[data-slot="questionnaire-input"]'),
            placeholder: [read('#input [data-slot="input"][placeholder]', "::placeholder").color, read('#questionnaire-demo input[data-slot="questionnaire-input"][placeholder]', "::placeholder").color],
            minHeight: getComputedStyle(document.querySelector('#questionnaire-answers textarea')).minHeight,
          }
        }"""
    )
    assert looks["answer"] == looks["input"], f"questionnaire inputs use the input look: {looks['answer']} vs {looks['input']}"
    assert looks["notes"] == looks["textarea"], f"questionnaire textareas use the textarea look: {looks['notes']} vs {looks['textarea']}"
    assert looks["placeholder"][0] == looks["placeholder"][1] and looks["minHeight"] == ("44px" if t.mobile else "0px"), looks
    email = page.locator("#questionnaire-answers input[type=email]")
    email.click()
    page.keyboard.type("not-an-email")
    page.locator("#questionnaire-answers [data-slot=questionnaire-next]").click()
    assert email.get_attribute("aria-invalid") == "true" and email.evaluate("e => document.activeElement === e"), "the invalid answer is focused"
    t.settle()
    edge = resolve(page, "var(--destructive)" if t.theme == "light" else "color-mix(in oklab, var(--destructive) 50%, transparent)")
    assert ring_width(page, email) == [3] and email.evaluate("e => getComputedStyle(e).borderTopColor") == edge
    t.a11y()
    ring = email.evaluate("e => [getComputedStyle(e).outlineStyle, getComputedStyle(e).outlineWidth, getComputedStyle(e).outlineColor, getComputedStyle(e).borderTopColor]")
    want = ["solid", "3px", resolve(page, "var(--focus-ring-invalid)"), edge]
    assert ring == want, f"a focused invalid answer shows the invalid focus ring: {ring} vs {want}"
    page.evaluate("() => document.getElementById('questionnaire-answers').remove()")


def check_questionnaire_answers(t):
    page = t.page
    t.section("questionnaire")
    page.evaluate(QUESTIONNAIRE_ANSWERS)
    form = page.locator("#questionnaire-answers")
    email = form.locator("input[type=email]")
    email.click()
    page.keyboard.type("not-an-email")
    assert email.get_attribute("name") == "email" and email.get_attribute("form") is None
    form.locator("[data-slot=questionnaire-next]").click()
    item = form.locator("fieldset[name=email]")
    error = item.locator("[data-slot=questionnaire-error]")
    assert item.get_attribute("data-active") is not None and item.get_attribute("aria-invalid") == "true"
    assert error.is_visible() and error.inner_text() == email.evaluate("e => e.validationMessage"), error.inner_text()
    assert page.evaluate("document.activeElement?.type") == "email"
    form.locator("[data-slot=questionnaire-choice][data-value=none]").click()
    email.fill("ops@example.com")
    assert email.evaluate("e => e.form?.id") == "questionnaire-answers" and item.get_attribute("aria-invalid") is None
    email.focus()
    page.keyboard.press("Enter")
    notes = form.locator("textarea")
    page.wait_for_function("() => document.querySelector('#questionnaire-answers fieldset[name=notes]').hasAttribute('data-active')")
    notes.click()
    page.keyboard.type("line one")
    page.keyboard.press("Enter")
    page.keyboard.type("line two")
    assert notes.input_value() == "line one\nline two", notes.input_value()
    assert notes.get_attribute("name") == "notes" and notes.get_attribute("aria-keyshortcuts") is None
    assert form.locator("fieldset[name=notes]").get_attribute("data-status") == "answered"
    assert page.evaluate("window.__answers") is None
    page.keyboard.press("Control+Enter")
    page.wait_for_function("() => window.__answers !== null")
    assert page.evaluate("window.__answers.value") == {"email": "ops@example.com", "notes": "line one\nline two"}
    t.shot("questionnaire-answers", form)
    page.evaluate("() => document.getElementById('questionnaire-answers').remove()")


def check_trace_reverse(t):
    page = t.page
    section = t.section("trace")
    if t.reduced_motion:
        t.skip("needs running height animations")
    pin(section.locator("#trace-demo"))
    ok = lambda h: 0 < h[0] < h[3] - 2 and h[0] - 3 <= h[1] < h[3] - 2 and h[1] - h[0] <= 0.25 * h[3] and 0 < h[2] <= h[1] + 1
    for _ in range(3):
        heights = page.evaluate(TRACE_REVERSE)
        if ok(heights):
            break
        t.settle()
        page.evaluate("""() => { if (document.querySelector("#trace-version [data-slot=trace-collapsible-content]").dataset.state === "open") document.querySelector("#trace-version [data-slot=trace-collapsible-trigger]").click() }""")
        t.settle()
    assert ok(heights), heights


TRACE_REVERSE = """() => new Promise(resolve => {
      const c = document.querySelector("#trace-version [data-slot=trace-collapsible-content]")
      const b = document.querySelector("#trace-version [data-slot=trace-collapsible-trigger]")
      const height = () => c.getBoundingClientRect().height
      b.click()
      setTimeout(() => requestAnimationFrame(() => {
        const middle = height()
        b.click()
        const reversed = height()
        requestAnimationFrame(() => requestAnimationFrame(() => resolve([middle, reversed, height(), c.scrollHeight])))
      }), 100)
    })"""


CLOSE = """([trigger, content]) => {
  const el = document.querySelector(content)
  const height = () => (el.checkVisibility() ? el.getBoundingClientRect().height : 0)
  const start = height()
  document.querySelector(trigger).click()
  const animation = el.getAnimations().find(a => a.transitionProperty === "height")
  if (!animation) return [start, null, null]
  const { delay, duration } = animation.effect.getComputedTiming()
  animation.pause()
  animation.currentTime = delay
  const first = height()
  animation.currentTime = delay + duration / 2
  const middle = height()
  animation.play()
  return [start, first, middle]
}"""


def check_trace_close_motion(t):
    page = t.page
    t.section("trace")
    trigger, content = "#trace-install > [data-slot=trace-collapsible-trigger]", "#trace-install > [data-slot=trace-collapsible-content]"
    page.locator(trigger).scroll_into_view_if_needed()
    start, first, middle = page.evaluate(CLOSE, [trigger, content])
    assert start > 0
    if t.reduced_motion:
        assert first is None
    else:
        assert abs(first - start) <= 1 and 0.1 * start < middle < 0.9 * start, (start, first, middle)
    page.wait_for_function("sel => !document.querySelector(sel).checkVisibility()", arg=content)


def check_trace(t):
    page = t.page
    section = t.section("trace")
    pin(section.locator("#trace-demo"))
    collapsible = section.locator("#trace-version")
    trigger = collapsible.locator("[data-slot=trace-collapsible-trigger]")
    body = collapsible.locator("[data-slot=trace-collapsible-content]")
    assert trigger.get_attribute("aria-expanded") == "false" and trigger.get_attribute("aria-controls") == body.get_attribute("id")
    assert body.is_hidden() and collapsible.get_attribute("data-state") == "closed"
    assert body.locator("[data-slot=trace-collapsible-content-inner]").count() == 1
    assert trigger.evaluate("b => b.lastElementChild.getAttribute('data-slot') === 'trace-icon' && !!b.lastElementChild.querySelector('svg.lucide-chevron-right')")
    record(page, "trace:open", "trace:close")
    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "true" and collapsible.get_attribute("data-state") == "open"
    t.settle()
    page.wait_for_function("() => document.querySelector('#trace-version [data-slot=trace-collapsible-content]').getBoundingClientRect().height > 0")
    assert body.is_visible()
    assert trigger.evaluate("b => getComputedStyle(b.lastElementChild).rotate") == "90deg"
    keyboard_mode(page)
    trigger.focus()
    page.keyboard.press("Enter")
    assert trigger.get_attribute("aria-expanded") == "false"
    page.wait_for_function("() => document.querySelector('#trace-version [data-slot=trace-collapsible-content]').hidden")
    page.keyboard.press("Space")
    assert trigger.get_attribute("aria-expanded") == "true"
    assert [e["type"] for e in recorded(page)] == ["trace:open", "trace:close", "trace:open"]
    install = section.locator("#trace-install")
    assert install.get_attribute("data-state") == "open" and install.locator("[data-slot=code-block][data-variant=destructive]").is_visible()
    assert install.locator("[data-slot=trace-collapsible-trigger]").evaluate("e => getComputedStyle(e).color") == resolve(page, "var(--destructive)")
    running = section.locator("#trace-status [data-status=running] [data-slot=trace-title]")
    assert running.evaluate("e => getComputedStyle(e).animationName") == ("none" if t.reduced_motion else "tw-shimmer")
    fill = running.evaluate("e => [getComputedStyle(e).webkitTextFillColor, getComputedStyle(e).backgroundImage.startsWith('linear-gradient'), getComputedStyle(e).color]")
    if t.reduced_motion:
        assert fill[0] == fill[2] and not fill[1], fill
    else:
        assert re.search(r"[/,] 0\)$", fill[0]) and fill[1], fill
    assert section.locator("#trace-status [data-status=pending]").evaluate("e => getComputedStyle(e).opacity") == "0.6"
    title = section.locator("#trace-status [data-slot=trace-line]").last.locator("[data-slot=trace-title]")
    assert title.evaluate("e => getComputedStyle(e).textOverflow") == "ellipsis"
    toggle = section.locator("#trace-pnpm-toggle")
    pin(section.locator("#trace-open"))
    toggle.click()
    assert section.locator("#trace-pnpm").get_attribute("data-state") == "open" and toggle.inner_text() == "Hide the pnpm output"
    t.settle()
    page.wait_for_timeout(100)
    toggle.click()
    assert section.locator("#trace-pnpm").get_attribute("data-state") == "closed" and toggle.inner_text() == "Show the pnpm output"
    t.settle()
    t.shot("trace-open", section.locator("#trace-open"))
    pin(section.locator("#trace-demo"))
    section.locator("#trace-replay").evaluate("b => b.click()")
    page.wait_for_function("() => document.getElementById('trace-thinking-line').dataset.status === 'running'")
    assert section.locator("#trace-demo-answer").is_hidden()
    assert section.locator("#trace-thinking").get_attribute("data-state") == "open"
    page.wait_for_function("() => !document.getElementById('trace-replay').disabled", timeout=10000)
    assert section.locator("#trace-demo-answer").is_visible()
    assert section.locator("#trace-thinking-line").get_attribute("data-status") is None
    assert section.locator("#trace-install [data-slot=trace-line]").get_attribute("data-status") == "error"
    assert section.locator("#trace-install").get_attribute("data-state") == "open"
    assert re.fullmatch(r"Thought for 5s", section.locator("#trace-thinking [data-slot=trace-title]").inner_text())


TRACE_MOTION = """async () => {
  const root = document.getElementById("trace-version")
  const trigger = root.querySelector(":scope > [data-slot=trace-collapsible-trigger]")
  const content = root.querySelector(":scope > [data-slot=trace-collapsible-content]")
  const attrs = el => ["data-open", "data-closed", "data-starting-style", "data-ending-style", "data-panel-open"].filter(a => el.hasAttribute(a)).join(" ")
  const snap = () => ({ root: attrs(root), trigger: attrs(trigger), content: attrs(content), hidden: content.hidden, height: content.getBoundingClientRect().height, size: content.style.getPropertyValue("--collapsible-panel-height") })
  const frame = () => new Promise(r => requestAnimationFrame(r))
  const settle = async () => {
    const start = performance.now()
    await frame()
    await frame()
    while (content.getAnimations().length && performance.now() - start < 3000) await frame()
    await frame()
    await frame()
  }
  const out = { closed: snap() }
  trigger.click()
  out.opening = snap()
  out.scrollHeight = content.scrollHeight
  out.transition = [getComputedStyle(content).transitionProperty, getComputedStyle(content).transitionDuration]
  await settle()
  out.open = snap()
  trigger.click()
  out.closing = snap()
  await settle()
  out.end = snap()
  return out
}"""


def check_trace_base_ui(t):
    page = t.page
    t.section("trace")
    pin(page.locator("#trace-demo"))
    m = page.evaluate(TRACE_MOTION)
    assert m["closed"] == {"root": "data-closed", "trigger": "", "content": "data-closed", "hidden": True, "height": 0, "size": m["closed"]["size"]}, m["closed"]
    opening = m["opening"]
    assert opening["root"] == "data-open data-starting-style" and opening["trigger"] == "data-starting-style data-panel-open" and opening["content"] == "data-open data-starting-style", opening
    assert opening["hidden"] is False and opening["height"] == 0 and opening["size"] == f"{m['scrollHeight']}px", (opening, m["scrollHeight"])
    assert m["transition"] == (["none", "0s"] if t.reduced_motion else ["height", "0.2s"]), m["transition"]
    assert m["open"] == {"root": "data-open", "trigger": "data-panel-open", "content": "data-open", "hidden": False, "height": m["open"]["height"], "size": "auto"}, m["open"]
    assert abs(m["open"]["height"] - m["scrollHeight"]) <= 1, m
    closing = m["closing"]
    assert closing["root"] == "data-closed data-ending-style" and closing["trigger"] == "data-ending-style" and closing["content"] == "data-closed data-ending-style", closing
    assert closing["size"] == f"{m['open']['height']}px" or abs(float(closing["size"].removesuffix("px")) - m["open"]["height"]) <= 0.5, closing
    assert m["end"] == {"root": "data-closed", "trigger": "", "content": "data-closed", "hidden": True, "height": 0, "size": m["end"]["size"]}, m["end"]


def check_calendar_day_button(t):
    page = t.page
    section = t.section("calendar")
    cal = section.locator("#calendar-booked")
    assert cal.get_attribute("data-mode") == "single"
    assert section.locator("#calendar-range").get_attribute("data-multiple-months") == "true" and cal.get_attribute("data-multiple-months") is None
    button = cal.locator("td[data-day='2026-02-10'] button")
    attrs = button.evaluate("b => ({ slot: b.dataset.slot, part: b.hasAttribute('data-calendar-day-button'), variant: b.dataset.variant, size: b.dataset.size, day: b.dataset.day, local: new Date(2026, 1, 10, 12).toLocaleDateString(document.documentElement.lang || 'en') })")
    assert attrs["slot"] == "button" and attrs["part"] and attrs["variant"] == "ghost" and attrs["size"] == "icon" and attrs["day"] == attrs["local"], attrs
    look = button.evaluate("b => { const s = getComputedStyle(b); return [s.position, s.display, s.flexDirection, s.aspectRatio, s.zIndex, s.isolation, s.borderTopLeftRadius] }")
    assert look == ["relative", "flex", "column", "1 / 1", "10", "isolate", "10px"], look
    assert cal.locator("[data-slot=calendar-day-button]").count() == 0
    selected = cal.locator("td[data-day='2026-02-03'] button")
    assert selected.get_attribute("data-selected-single") == "true" and button.get_attribute("data-range-start") is None
    rng = section.locator("#calendar-range")
    assert rng.locator("td[data-day='2026-01-05']:not([data-outside]) button").get_attribute("data-range-start") == "false"
    assert rng.locator("td[data-day='2026-01-12']:not([data-outside]) button").get_attribute("data-selected-single") == "false"
    assert cal.locator("td[data-outside]").first.get_attribute("data-month") == "2026-01"
    keyboard_mode(page)
    button.focus()
    assert cal.locator("td[data-focused]").evaluate_all("cells => cells.map(c => c.dataset.day + '=' + c.dataset.focused)") == ["2026-02-10=true"]
    focused = cal.locator("td[data-day='2026-02-10'] button")
    t.settle()
    assert ring_width(page, focused) == [3], focused.evaluate("b => getComputedStyle(b).boxShadow")
    page.keyboard.press(key(t, "ArrowRight"))
    assert cal.locator("td[data-focused]").evaluate_all("cells => cells.map(c => c.dataset.day)") == ["2026-02-11"]
    section.locator("[data-demo=title]").first.click()
    assert cal.locator("td[data-focused]").count() == 0


PENDING = """async () => {
  const ui = await import("/clanker-ui.js")
  const out = {}
  for (const [name, position, count] of [["end", null, 12], ["start", "start", 12], ["empty", null, 0]]) {
    const items = Array.from({ length: count }, (_, i) => ui.h("div", { "data-slot": "message-scroller-item", "data-message-id": `p${i}`, style: { height: "60px" } }, `Row ${i + 1}`))
    const viewport = ui.h("div", { "data-slot": "message-scroller-viewport", "aria-label": name }, ui.h("div", { "data-slot": "message-scroller-content" }, items))
    const root = ui.h("div", { "data-slot": "message-scroller", "data-default-scroll-position": position, style: { height: "200px" } }, viewport)
    const seen = []
    const observer = new MutationObserver(records => { for (const r of records) seen.push(`${r.target === root ? "root" : "viewport"}:${r.oldValue === null ? "set" : "removed"}`) })
    observer.observe(root, { attributes: true, attributeFilter: ["data-pending-scroll"], attributeOldValue: true, subtree: true })
    document.getElementById("message-scroller").append(root)
    await new Promise(r => setTimeout(r, 50))
    observer.disconnect()
    const content = viewport.firstElementChild
    const spacer = content.lastElementChild
    const atEnd = Math.abs(viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop) <= 2
    content.append(ui.h("div", { "data-slot": "message-scroller-item" }, "Late row"))
    await new Promise(r => setTimeout(r, 50))
    out[name] = {
      seen,
      now: [root.hasAttribute("data-pending-scroll"), viewport.hasAttribute("data-pending-scroll")],
      visibility: getComputedStyle(viewport).visibility,
      atEnd,
      spacer: [spacer.hasAttribute("data-message-scroller-spacer"), spacer.getAttribute("aria-hidden"), spacer.hidden, content.lastElementChild === spacer, content.querySelectorAll("[data-message-scroller-spacer]").length],
      anchor: content.firstElementChild?.getAttribute("data-scroll-anchor") ?? null,
    }
    root.remove()
  }
  const authored = document.createElement("div")
  authored.setAttribute("data-slot", "message-scroller")
  authored.setAttribute("data-pending-scroll", "")
  const viewport = document.createElement("div")
  viewport.setAttribute("data-slot", "message-scroller-viewport")
  viewport.setAttribute("data-pending-scroll", "")
  viewport.append(document.createElement("div"))
  viewport.firstChild.setAttribute("data-slot", "message-scroller-content")
  viewport.firstChild.append(ui.h("div", { "data-slot": "message-scroller-item" }, "Row"))
  authored.append(viewport)
  out.hidden = getComputedStyle(document.body.appendChild(authored).querySelector("[data-slot=message-scroller-viewport]")).visibility
  await new Promise(r => setTimeout(r, 50))
  out.authored = [authored.hasAttribute("data-pending-scroll"), viewport.hasAttribute("data-pending-scroll"), getComputedStyle(viewport).visibility]
  authored.remove()
  return out
}"""


def check_message_scroller_pending(t):
    page = t.page
    t.section("message-scroller")
    out = page.evaluate(PENDING)
    end = out["end"]
    assert end["seen"] == ["root:set", "viewport:set", "root:removed", "viewport:removed"], end
    assert end["now"] == [False, False] and end["visibility"] == "visible" and end["atEnd"], end
    assert out["start"]["seen"] == [] and out["start"]["now"] == [False, False], out["start"]
    assert out["empty"]["now"] == [False, False], out["empty"]
    for name in ("end", "start", "empty"):
        assert out[name]["spacer"] == [True, "true", True, True, 1], (name, out[name])
    assert end["anchor"] == "false", end
    assert out["authored"] == [False, False, "visible"], out


DEFAULTS = """async () => {
  const ui = await import("/clanker-ui.js")
  const host = ui.h("div", null,
    ui.h("div", { "data-slot": "message" }, ui.h("div", { "data-slot": "message-content" }, ui.h("div", { "data-slot": "bubble" }, ui.h("div", { "data-slot": "bubble-content" }, "Hi"), ui.h("div", { "data-slot": "bubble-reactions" }, "1")))),
    ui.h("div", { "data-slot": "marker" }, ui.h("span", { "data-slot": "marker-icon" }), ui.h("span", { "data-slot": "marker-content" }, "Marker")),
    ui.h("div", { "data-slot": "attachment" }, ui.h("div", { "data-slot": "attachment-media" })),
    ui.h("div", { "data-slot": "code-block" }, ui.h("pre", { "data-slot": "code-block-content" }, "x")),
    ui.h("div", { "data-slot": "trace" }, ui.h("span", { "data-slot": "trace-line" }, ui.h("span", { "data-slot": "trace-icon" }), ui.h("span", { "data-slot": "trace-title" }, "Step"))),
    ui.h("form", { "data-slot": "questionnaire" }, ui.h("fieldset", { "data-slot": "questionnaire-item", name: "a" }), ui.h("div", { "data-slot": "questionnaire-actions" }, ui.h("button", { type: "button", "data-slot": "questionnaire-previous" }), ui.h("button", { type: "button", "data-slot": "questionnaire-skip" }), ui.h("button", { type: "button", "data-slot": "questionnaire-next" }), ui.h("button", { type: "submit", "data-slot": "questionnaire-submit" }))),
    ui.h("div", { "data-slot": "message-scroller" }, ui.h("div", { "data-slot": "message-scroller-viewport" }, ui.h("div", { "data-slot": "message-scroller-content" })), ui.h("button", { "data-slot": "message-scroller-button" })))
  document.getElementById("message").append(host)
  await new Promise(r => setTimeout(r, 30))
  const read = (slot, names) => { const el = host.querySelector(`[data-slot=${slot}]`); return Object.fromEntries(names.map(n => [n, el.getAttribute(n)])) }
  const out = {
    message: read("message", ["data-align"]),
    bubble: read("bubble", ["data-variant", "data-align"]),
    reactions: read("bubble-reactions", ["data-align", "data-side"]),
    marker: read("marker", ["data-variant"]),
    markerIcon: read("marker-icon", ["aria-hidden"]),
    attachment: read("attachment", ["data-state", "data-size", "data-orientation"]),
    media: read("attachment-media", ["data-variant"]),
    codeBlock: read("code-block", ["data-variant", "data-size"]),
    traceIcon: read("trace-icon", ["aria-hidden"]),
    previous: read("questionnaire-previous", ["data-variant", "data-size"]),
    skip: read("questionnaire-skip", ["data-variant", "data-size"]),
    next: read("questionnaire-next", ["data-variant", "data-size"]),
    submit: read("questionnaire-submit", ["data-variant", "data-size"]),
    scrollerButton: read("message-scroller-button", ["data-direction", "data-variant", "data-size"]),
  }
  host.remove()
  return out
}"""


def check_g4_default_attributes(t):
    page = t.page
    t.section("message")
    out = page.evaluate(DEFAULTS)
    assert out == {
        "message": {"data-align": "start"},
        "bubble": {"data-variant": "default", "data-align": "start"},
        "reactions": {"data-align": "end", "data-side": "bottom"},
        "marker": {"data-variant": "default"},
        "markerIcon": {"aria-hidden": "true"},
        "attachment": {"data-state": "done", "data-size": "default", "data-orientation": "horizontal"},
        "media": {"data-variant": "icon"},
        "codeBlock": {"data-variant": "default", "data-size": "default"},
        "traceIcon": {"aria-hidden": "true"},
        "previous": {"data-variant": "outline", "data-size": "default"},
        "skip": {"data-variant": "outline", "data-size": "default"},
        "next": {"data-variant": "default", "data-size": "default"},
        "submit": {"data-variant": "default", "data-size": "default"},
        "scrollerButton": {"data-direction": "end", "data-variant": "secondary", "data-size": "icon-sm"},
    }, out


def check_questionnaire_choice_state(t):
    page = t.page
    section = t.section("questionnaire")
    form = section.locator("#questionnaire-demo")
    first = form.locator("fieldset[name=direction]")
    inputs = first.locator("[data-slot=questionnaire-choice-input]")
    read = "i => [i.dataset.type, i.dataset.shortcut, i.hasAttribute('data-unchecked'), i.required, i.closest('[data-slot=questionnaire-choice]').querySelector('[data-slot=questionnaire-choice-shortcut]').dataset.shortcut]"
    assert inputs.first.evaluate(read) == ["radio", "A", True, True, "A"]
    assert form.locator("fieldset[name=signals] [data-slot=questionnaire-choice-input]").first.evaluate(read) == ["checkbox", "A", True, False, "A"]
    first.locator("[data-slot=questionnaire-input]").fill("A cost dashboard")
    assert inputs.first.evaluate("i => i.required") is False
    first.locator("[data-slot=questionnaire-choice][data-value=handoffs]").click()
    handoffs = first.locator("input[value=handoffs]")
    assert handoffs.evaluate("i => [i.hasAttribute('data-checked'), i.hasAttribute('data-unchecked'), i.required]") == [True, False, True]


def check_calendar_rtl_chevron(t):
    page = t.page
    section = t.section("calendar")
    booked = section.locator("#calendar-booked")
    booked.evaluate("e => e.setAttribute('dir', 'rtl')")
    assert booked.locator("[data-slot=calendar-button-next] svg").evaluate("s => getComputedStyle(s).rotate") == "180deg"
    assert booked.locator("[data-slot=calendar-button-previous] svg").evaluate("s => getComputedStyle(s).rotate") == "180deg"


def check_marker_shimmer(t):
    page = t.page
    t.section("marker")
    assert style(page, "#marker-demo .shimmer", "animationName") == ("none" if t.reduced_motion else "tw-shimmer")
    assert style(page, "#marker-demo .shimmer", "backgroundClip") == "text"


def check_trace_shimmer_fallback(t):
    page = t.page
    section = t.section("trace")
    running = section.locator("#trace-status [data-status=running] [data-slot=trace-title]")
    t.a11y()
    running.evaluate("e => e.style.setProperty('--shimmer-color', 'oklch(from currentColor zz)')")
    fill = running.evaluate("e => [getComputedStyle(e).webkitTextFillColor, getComputedStyle(e).color]")
    assert fill[0] == fill[1] and fill[0] != "rgba(0, 0, 0, 0)", fill


def scroll_fade(t, section_id, sel, scroll):
    page = t.page
    t.section(section_id)
    page.locator(sel).first.scroll_into_view_if_needed()
    wait_fade(page, sel, "s", False)
    rest = fade(page, sel)
    assert rest["e"] > 0 and (rest["s"] == 0) == rest["timeline"], rest
    page.locator(sel).first.evaluate(scroll)
    wait_fade(page, sel, "s", True)
    end = fade(page, sel)
    assert end["s"] > 0 and (end["e"] == 0) == end["timeline"], end


def check_attachment_scroll_fade(t):
    scroll_fade(t, "attachment", "#attachment-group [data-slot=attachment-group]", "g => { g.scrollLeft = getComputedStyle(g).direction === 'rtl' ? -g.scrollWidth : g.scrollWidth }")


def check_code_block_scroll_fade(t):
    scroll_fade(t, "code-block", "#code-block-basic [data-slot=code-block-content]", "e => { e.scrollLeft = e.scrollWidth }")


PICKER_MIN = """async () => {
  const ui = await import("/clanker-ui.js")
  const root = ui.h("div", { id: "date-picker-min", "data-slot": "date-picker" },
    ui.h("button", { type: "button", "data-slot": "button", "data-variant": "outline", "data-date-picker-trigger": "" }, "Book"),
    ui.h("div", { "data-slot": "popover-content", "data-date-picker-content": "", "aria-label": "Choose date" }, ui.h("div", { "data-slot": "calendar", "data-min": "2026-10-28" })))
  document.getElementById("date-picker").append(root)
}"""


def check_date_picker_disabled_nav(t):
    page = t.page
    section = t.section("date-picker")
    page.evaluate(PICKER_MIN)
    root = section.locator("#date-picker-min")
    previous = root.locator("[data-slot=calendar-button-previous]")
    assert previous.get_attribute("aria-disabled") == "true" and previous.get_attribute("tabindex") == "-1"
    assert root.locator("[data-slot=calendar-button-next]").get_attribute("tabindex") is None
    for open_with in ("click", "Enter"):
        trigger = root.locator("[data-date-picker-trigger]")
        if open_with == "click":
            trigger.click()
        else:
            keyboard_mode(page)
            trigger.focus()
            page.keyboard.press("Enter")
        wait_popup(page, "#date-picker-min")
        assert page.evaluate("() => document.activeElement.getAttribute('data-slot')") == "calendar-button-next", open_with
        page.keyboard.press("Escape")
        wait_popup(page, "#date-picker-min", False)
    page.evaluate("() => document.getElementById('date-picker-min').remove()")


RANGE_FLAGS = """async () => {
  const ui = await import("/clanker-ui.js")
  const cal = ui.h("div", { "data-slot": "calendar", "data-mode": "range", "data-month": "2026-03" })
  document.getElementById("calendar").append(cal)
  await new Promise(r => setTimeout(r, 20))
  const flags = () => [...cal.querySelectorAll("[data-calendar-day-button]")].flatMap(b => ["data-range-start", "data-range-middle", "data-range-end"].map(a => b.getAttribute(a)))
  const empty = [...new Set(flags())]
  ui.calendarSetValue(cal, "2026-03-10/2026-03-12")
  const set = [...new Set(flags())].sort()
  cal.remove()
  return { empty, set }
}"""


def check_calendar_range_flags(t):
    page = t.page
    t.section("calendar")
    out = page.evaluate(RANGE_FLAGS)
    assert out == {"empty": [None], "set": ["false", "true"]}, out


WEEK_ATTRIBUTE = """async () => {
  const ui = await import("/clanker-ui.js")
  const out = {}
  for (const name of ["data-show-week-number", "data-week-numbers"]) {
    const cal = ui.h("div", { "data-slot": "calendar", "data-month": "2026-02", [name]: "" })
    document.getElementById("calendar").append(cal)
    await new Promise(r => setTimeout(r, 20))
    out[name] = [cal.querySelectorAll("[data-slot=calendar-week-number-header]").length, cal.querySelectorAll("[data-slot=calendar-week-number]").length > 0]
    cal.removeAttribute(name)
    await new Promise(r => setTimeout(r, 20))
    out[name].push(cal.querySelectorAll("[data-slot=calendar-week-number]").length)
    cal.remove()
  }
  return out
}"""


def check_calendar_show_week_number(t):
    page = t.page
    section = t.section("calendar")
    assert section.locator("#calendar-weeks").get_attribute("data-show-week-number") is not None
    out = page.evaluate(WEEK_ATTRIBUTE)
    assert out == {"data-show-week-number": [1, True, 0], "data-week-numbers": [0, False, 0]}, out


DEMO_RESET = """async () => {
  const ui = await import("/clanker-ui.js")
  const content = document.getElementById("message-scroller-transcript")
  const rows = () => content.querySelectorAll(":scope > [data-slot=message-scroller-item]").length
  const before = rows()
  content.append(ui.h("div", { "data-slot": "message-scroller-item" }, "Extra one"), ui.h("div", { "data-slot": "message-scroller-item" }, "Extra two"))
  await new Promise(r => setTimeout(r, 50))
  const added = rows()
  document.getElementById("message-scroller-reset").click()
  await new Promise(r => setTimeout(r, 50))
  return { before, added, after: rows(), spacers: content.querySelectorAll(":scope > [data-message-scroller-spacer]").length, last: content.lastElementChild.hasAttribute("data-message-scroller-spacer") }
}"""


def check_message_scroller_demo_reset(t):
    page = t.page
    t.section("message-scroller")
    out = page.evaluate(DEMO_RESET)
    assert out["added"] == out["before"] + 2 and out["after"] == out["before"] and out["spacers"] == 1 and out["last"], out


ROOT_DEFAULTS = """async () => {
  const ui = await import("/clanker-ui.js")
  const plain = ui.h("div", { "data-slot": "calendar", "data-month": "2026-02" })
  const authored = ui.h("div", { "data-slot": "calendar", "data-month": "2026-02", "data-caption-layout": "dropdown", "data-button-variant": "outline" })
  document.getElementById("calendar").append(plain, authored)
  await new Promise(r => setTimeout(r, 20))
  const read = el => ["data-mode", "data-caption-layout", "data-button-variant"].map(a => el.getAttribute(a)).concat([...el.querySelectorAll("[data-slot=calendar-button-previous], [data-slot=calendar-button-next]")].map(b => b.dataset.variant))
  const out = { plain: read(plain), authored: read(authored) }
  plain.setAttribute("data-button-variant", "secondary")
  await new Promise(r => setTimeout(r, 20))
  out.changed = read(plain)
  plain.remove()
  authored.remove()
  return out
}"""


def check_calendar_root_defaults(t):
    page = t.page
    section = t.section("calendar")
    out = page.evaluate(ROOT_DEFAULTS)
    assert out == {
        "plain": ["single", "label", "ghost", "ghost", "ghost"],
        "authored": ["single", "dropdown", "outline", "outline", "outline"],
        "changed": ["single", "label", "secondary", "secondary", "secondary"],
    }, out
    demo = section.locator("#calendar-demo")
    assert [demo.get_attribute("data-caption-layout"), demo.get_attribute("data-button-variant")] == ["dropdown", "ghost"]


CALENDAR_ARIA = """async () => {
  const ui = await import("/clanker-ui.js")
  const make = attrs => ui.h("div", { "data-slot": "calendar", "data-month": "2026-10", ...attrs })
  const single = make({ "data-caption-layout": "dropdown" })
  const range = make({ "data-mode": "range", "data-months": "2" })
  const named = ui.h("div", { "data-string-calendar-navigation": "Months" }, make({}))
  document.getElementById("calendar").append(single, range, named)
  await new Promise(r => setTimeout(r, 30))
  const grid = el => { const g = el.querySelector("[role=grid]"); return [g.getAttribute("aria-multiselectable"), g.getAttribute("aria-label"), g.getAttribute("aria-labelledby")] }
  const out = {
    single: grid(single),
    range: [...range.querySelectorAll("[role=grid]")].map(g => [g.getAttribute("aria-multiselectable"), g.getAttribute("aria-label")]),
    selects: [...single.querySelectorAll("select")].map(s => s.getAttribute("aria-describedby")),
    nav: [single.querySelector("nav").getAttribute("aria-label"), named.querySelector("nav").getAttribute("aria-label")],
  }
  single.remove(); range.remove(); named.remove()
  return out
}"""


def check_calendar_grid_aria(t):
    page = t.page
    t.section("calendar")
    out = page.evaluate(CALENDAR_ARIA)
    assert out == {
        "single": ["false", "October 2026", None],
        "range": [["true", "October 2026"], ["true", "November 2026"]],
        "selects": [None, None],
        "nav": ["Navigation bar", "Months"],
    }, out


CALENDAR_STATUS = """async () => {
  const ui = await import("/clanker-ui.js")
  const label = ui.h("div", { "data-slot": "calendar", "data-month": "2026-10" })
  const dropdown = ui.h("div", { "data-slot": "calendar", "data-month": "2026-10", "data-caption-layout": "dropdown", "data-months": "2" })
  document.getElementById("calendar").append(label, dropdown)
  await new Promise(r => setTimeout(r, 30))
  const read = el => [...el.querySelectorAll("[role=status]")].map(s => [s.getAttribute("aria-live"), s.getAttribute("data-slot"), s.parentElement.getAttribute("data-slot"), s.previousElementSibling?.getAttribute("data-slot") ?? null, s.className, s.textContent])
  const before = label.querySelector("[role=status]")
  const out = { label: read(label), dropdown: read(dropdown), live: label.querySelectorAll("[data-slot=calendar-live]").length + dropdown.querySelectorAll("[data-slot=calendar-live]").length }
  label.querySelector("[data-slot=calendar-button-next]").click()
  out.next = [label.querySelector("[role=status]") === before, before.textContent]
  label.remove(); dropdown.remove()
  return out
}"""


def check_calendar_caption_status(t):
    page = t.page
    t.section("calendar")
    out = page.evaluate(CALENDAR_STATUS)
    assert out == {
        "label": [["polite", "calendar-caption-label", "calendar-month-caption", None, "", "October 2026"]],
        "dropdown": [["polite", None, "calendar-dropdowns", "calendar-dropdown-root", "sr-only", "October 2026"], ["polite", None, "calendar-dropdowns", "calendar-dropdown-root", "sr-only", "November 2026"]],
        "live": 0,
        "next": [True, "November 2026"],
    }, out


CALENDAR_BOUNDS = """async () => {
  const ui = await import("/clanker-ui.js")
  const out = {}
  for (const layout of ["dropdown", "dropdown-years", "dropdown-months", "label"]) {
    const el = ui.h("div", { "data-slot": "calendar", "data-month": "2026-12", "data-caption-layout": layout, "data-week-start": "0" })
    document.getElementById("calendar").append(el)
    await new Promise(r => setTimeout(r, 30))
    const next = el.querySelector("[data-slot=calendar-button-next]")
    const years = [...el.querySelectorAll("select[data-kind=year] option")].map(o => o.value)
    const jan = el.querySelector("td[data-day='2027-01-01']")
    out[layout] = [next.getAttribute("aria-disabled"), next.getAttribute("tabindex"), years.length ? [years[0], years.at(-1)] : null, jan.getAttribute("data-hidden"), jan.childElementCount]
    el.remove()
  }
  return out
}"""


def check_calendar_year_bounds(t):
    page = t.page
    t.section("calendar")
    out = page.evaluate(CALENDAR_BOUNDS)
    assert out == {
        "dropdown": ["true", "-1", ["1926", "2026"], "true", 0],
        "dropdown-years": ["true", "-1", ["1926", "2026"], "true", 0],
        "dropdown-months": [None, None, None, None, 1],
        "label": [None, None, None, None, 1],
    }, out


DAY_LABELS = """async () => {
  const ui = await import("/clanker-ui.js")
  const en = ui.h("div", { "data-slot": "calendar", "data-month": "2026-10", "data-lang": "en" })
  const de = ui.h("div", { "data-slot": "calendar", "data-month": "2026-10", "data-lang": "de" })
  document.getElementById("calendar").append(en, de)
  await new Promise(r => setTimeout(r, 30))
  const label = (el, day) => el.querySelector(`td[data-day='${day}']:not([data-outside]) button`).getAttribute("aria-label")
  const days = [1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 31].map(d => `2026-10-${String(d).padStart(2, "0")}`)
  const out = { en: days.map(d => label(en, d)), de: label(de, "2026-10-01") }
  en.remove(); de.remove()
  return out
}"""


def check_calendar_day_label_ordinal(t):
    page = t.page
    t.section("calendar")
    out = page.evaluate(DAY_LABELS)
    weekdays = ["Thursday", "Friday", "Saturday", "Sunday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    numbers = ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "23rd", "31st"]
    assert out["en"] == [f"{w}, October {n}, 2026" for w, n in zip(weekdays, numbers)], out
    assert out["de"] == "Donnerstag, 1. Oktober 2026", out


FUTURE_MIN = """async () => {
  const ui = await import("/clanker-ui.js")
  const out = {}
  for (const [name, attrs] of [["min", { "data-today": "2026-12-31", "data-min": "2027-01-01" }], ["max", { "data-today": "2026-10-28", "data-max": "1920-06-30" }]]) {
    const el = ui.h("div", { "data-slot": "calendar", "data-caption-layout": "dropdown", ...attrs })
    document.getElementById("calendar").append(el)
    await new Promise(r => setTimeout(r, 30))
    const years = [...el.querySelectorAll("select[data-kind=year] option")].map(o => o.value)
    out[name] = {
      month: el.querySelector("[data-slot=calendar-month]").dataset.month,
      enabled: el.querySelectorAll("td:not([data-outside]) > [data-calendar-day-button]:not(:disabled)").length,
      months: el.querySelectorAll("select[data-kind=month] option:not(:disabled)").length,
      years: [years[0], years.at(-1)],
    }
    el.remove()
  }
  return out
}"""


def check_calendar_year_bounds_follow_limits(t):
    page = t.page
    t.section("calendar")
    out = page.evaluate(FUTURE_MIN)
    assert out["min"]["month"] == "2027-01" and out["min"]["enabled"] == 31 and out["min"]["months"] == 12 and out["min"]["years"] == ["2027", "2027"], out
    assert out["max"]["month"] == "1920-06" and out["max"]["enabled"] == 30 and out["max"]["years"] == ["1920", "1920"], out
