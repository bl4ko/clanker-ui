START = "/demo?only=charts"

SECTIONS = ["chart", "chart-area", "chart-bar", "chart-line", "chart-pie", "chart-radar", "chart-radial", "chart-stat"]
MONTHS = ["January", "February", "March", "April", "May", "June"]
DESKTOP = [186, 305, 237, 73, 209, 214]
MOBILE = [80, 200, 120, 190, 130, 140]

LISTEN = """() => {
  window.__chartEvents = []
  for (const type of ["chart:active", "chart:legend", "chart:view"]) {
    document.addEventListener(type, e => window.__chartEvents.push({ type: e.type, id: e.target.id, detail: e.detail }))
  }
}"""

READ_TIP = """id => {
  const tip = document.querySelector(`#${id} [data-slot="chart-tooltip"]`)
  if (tip.hidden) return null
  const label = tip.querySelector('[data-slot="chart-tooltip-label"]')
  return {
    label: label ? label.textContent : null,
    items: [...tip.querySelectorAll('[data-slot="chart-tooltip-item"]')].map(i => [
      i.querySelector('[data-slot="chart-tooltip-name"]').textContent,
      i.querySelector('[data-slot="chart-tooltip-value"]').firstChild.textContent,
      i.hasAttribute("data-active"),
    ]),
  }
}"""

PROBE = """async ([id, width, data, options]) => {
  const { chart } = await import("/clanker-ui-chart.js")
  document.getElementById(id)?.remove()
  const box = document.createElement("div")
  box.id = id
  box.style.width = `${width}px`
  document.body.append(box)
  window.__chartProbe = chart(box, data, options)
  const plot = box.querySelector('[data-slot="chart-plot"]').getBoundingClientRect()
  const svg = box.querySelector('[data-slot="chart-svg"]')
  return { width: +svg.getAttribute("width"), height: +svg.getAttribute("height"), plot: [Math.floor(plot.width), Math.floor(plot.height)] }
}"""


INK_CONTRAST = """() => {
  const probe = document.createElement("canvas").getContext("2d", { willReadFrequently: true })
  const lum = color => {
    probe.clearRect(0, 0, 1, 1)
    probe.fillStyle = "#000"
    probe.fillStyle = color
    probe.fillRect(0, 0, 1, 1)
    const lin = c => (c / 255 <= 0.04045 ? c / 255 / 12.92 : ((c / 255 + 0.055) / 1.055) ** 2.4)
    const [r, g, b] = probe.getImageData(0, 0, 1, 1).data
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
  }
  const ratio = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
  const out = []
  for (const text of document.querySelectorAll('[data-slot="chart-svg"] text[data-part="label"][data-ink]')) {
    const root = text.closest('[data-slot="chart"]')
    const box = text.getBBox()
    const point = text.ownerSVGElement.createSVGPoint()
    point.x = box.x + box.width / 2
    point.y = box.y + box.height / 2
    const under = [...root.querySelectorAll('[data-part="slice"], [data-part="bar"], [data-part="arc"]')].find(m => m.isPointInFill(point))
    if (!under) continue
    const fill = lum(getComputedStyle(under).fill)
    const style = getComputedStyle(root)
    const chosen = lum(getComputedStyle(text).fill)
    const other = lum(style.getPropertyValue(text.dataset.ink === "light" ? "--chart-ink-dark" : "--chart-ink-light").trim())
    out.push({ chart: root.id, text: text.textContent, chosen: +ratio(chosen, fill).toFixed(2), other: +ratio(other, fill).toFixed(2) })
  }
  return out
}"""


def tip(page, cid):
    return page.evaluate(READ_TIP, cid)


def events(page, kind):
    return [e for e in page.evaluate("window.__chartEvents") if e["type"] == kind]


def svg_of(page, cid):
    return page.locator(f"#{cid} [data-slot='chart-svg']")


def box_of(page, cid):
    surface = svg_of(page, cid)
    surface.scroll_into_view_if_needed()
    return surface.bounding_box()


def card_of(page, cid):
    return page.locator(f"article:has(#{cid})")


def check_chart_render(t):
    page = t.page
    charts = page.evaluate(
        """() => [...document.querySelectorAll('[data-slot="chart"]')].map(c => {
          const s = c.querySelector('[data-slot="chart-svg"]')
          return {
            id: c.id || c.parentElement.parentElement.id,
            role: s.getAttribute("role"),
            tabindex: s.getAttribute("tabindex"),
            hidden: [...s.children].every(n => n.getAttribute("aria-hidden") === "true"),
            label: s.getAttribute("aria-label") || "",
            marks: s.querySelectorAll('[data-part="bar"], [data-part="line"], [data-part="area"], [data-part="slice"], [data-part="shape"], [data-part="arc"]').length,
            width: +s.getAttribute("width"),
            height: +s.getAttribute("height"),
            overflow: c.getBoundingClientRect().right > document.documentElement.clientWidth + 1,
          }
        })"""
    )
    assert len(charts) >= 50, len(charts)
    for c in charts:
        assert c["role"] == "application" and c["tabindex"] == "0" and c["hidden"], c
        assert len(c["label"]) > 20, c
        assert c["marks"] > 0, c
        assert c["width"] > 40 and c["height"] > 20, c
        assert not c["overflow"], c
    label = svg_of(page, "chart-bar-multiple").get_attribute("aria-label")
    assert label == "Bar chart, Visitors, January to June 2024. Desktop and Mobile, 6 points from January to June. Desktop from 73 to 305. Mobile from 80 to 200.", label
    pie = svg_of(page, "chart-pie-simple").get_attribute("aria-label")
    assert pie.startswith("Pie chart, Visitors by browser, January to June 2024. Chrome 275 (29.7%), Safari 200 (21.6%)"), pie
    assert page.locator("#chart-bar-default [data-slot='chart-legend']").is_hidden()
    assert page.locator("#chart-bar-multiple [data-slot='chart-legend']").is_visible()
    for sid in SECTIONS:
        t.section(sid)
        t.settle()
        t.shot(sid)


def check_chart_pointer(t):
    page = t.page
    page.evaluate(LISTEN)
    t.section("chart-bar")
    bars = page.locator("#chart-bar-default [data-part='bar']")
    bars.nth(1).hover()
    assert tip(page, "chart-bar-default") == {"label": "February", "items": [["Desktop", "305", False]]}, tip(page, "chart-bar-default")
    assert page.locator("#chart-bar-default [data-part='cursor']").get_attribute("data-active") == "", "cursor"
    assert bars.nth(1).get_attribute("data-active") == "", "active bar"
    t.shot("bar-hover", card_of(page, "chart-bar-default"))
    bars.nth(3).hover()
    assert tip(page, "chart-bar-default")["label"] == "April", tip(page, "chart-bar-default")
    active = events(page, "chart:active")
    assert active[0]["id"] == "chart-bar-default" and active[0]["detail"]["index"] == 1 and active[0]["detail"]["key"] == "desktop", active[0]
    assert active[0]["detail"]["row"] == {"month": "February", "desktop": 305, "mobile": 200}, active[0]
    assert active[-1]["detail"]["index"] == 3
    page.evaluate("() => document.activeElement?.blur()")
    page.keyboard.press("Escape")
    assert tip(page, "chart-bar-default") is None, tip(page, "chart-bar-default")
    assert page.locator("#chart-bar-default [data-part='cursor']").get_attribute("data-active") is None
    bars.nth(0).hover()
    assert tip(page, "chart-bar-default")["label"] == "January", tip(page, "chart-bar-default")
    page.mouse.move(2, 2)
    assert tip(page, "chart-bar-default") is None, tip(page, "chart-bar-default")
    assert events(page, "chart:active")[-1]["detail"] is None

    stacked = page.locator("#chart-bar-stacked [data-key='mobile'] [data-part='bar']").nth(1)
    stacked.scroll_into_view_if_needed()
    stacked.hover()
    data = tip(page, "chart-bar-stacked")
    assert data == {"label": "February", "items": [["Desktop", "305", False], ["Mobile", "200", True], ["Total", "505", False]]}, data

    t.section("chart-line")
    box = box_of(page, "chart-line-multiple")
    page.mouse.move(box["x"] + box["width"] * 0.55, box["y"] + box["height"] * 0.4)
    data = tip(page, "chart-line-multiple")
    assert data and data["label"] in MONTHS, data
    i = MONTHS.index(data["label"])
    assert data["items"] == [["Desktop", str(DESKTOP[i]), False], ["Mobile", str(MOBILE[i]), False]], data
    assert page.locator("#chart-line-multiple [data-part='crosshair']").get_attribute("data-active") == ""
    assert page.locator("#chart-line-multiple [data-part='active'] circle").count() == 2
    t.shot("line-hover", card_of(page, "chart-line-multiple"))

    t.section("chart-pie")
    box = box_of(page, "chart-pie-simple")
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(cx + 40 * 0.77, cy - 40 * 0.64)
    assert tip(page, "chart-pie-simple") == {"label": None, "items": [["Chrome", "275", False]]}, tip(page, "chart-pie-simple")
    assert page.locator("#chart-pie-simple [data-part='slice']").first.get_attribute("data-active") == ""
    t.shot("pie-hover", card_of(page, "chart-pie-simple"))
    box = box_of(page, "chart-pie-simple")
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(cx - 40 * 0.3, cy + 40 * 0.95)
    assert tip(page, "chart-pie-simple")["items"][0][0] == "Firefox", tip(page, "chart-pie-simple")

    t.section("chart-radar")
    box = box_of(page, "chart-radar-multiple")
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2 - 60)
    assert tip(page, "chart-radar-multiple") == {"label": "January", "items": [["Desktop", "186", False], ["Mobile", "80", False]]}, tip(page, "chart-radar-multiple")


def check_chart_keyboard(t):
    page = t.page
    page.evaluate(LISTEN)
    t.section("chart-bar")
    page.keyboard.press("Shift")
    surface = svg_of(page, "chart-bar-multiple")
    surface.focus()
    assert surface.evaluate("e => e.matches(':focus-visible')")
    assert surface.evaluate("e => getComputedStyle(e).outlineStyle") != "none"
    t.a11y()
    ring = surface.evaluate("e => { const s = getComputedStyle(e); return [s.outlineStyle, s.outlineWidth] }")
    assert ring == ["solid", "3px"], ring
    assert tip(page, "chart-bar-multiple") == {"label": "January", "items": [["Desktop", "186", True], ["Mobile", "80", False]]}
    page.keyboard.press("ArrowRight")
    assert tip(page, "chart-bar-multiple") == {"label": "February", "items": [["Desktop", "305", True], ["Mobile", "200", False]]}
    page.keyboard.press("ArrowDown")
    assert tip(page, "chart-bar-multiple")["items"][1] == ["Mobile", "200", True]
    page.keyboard.press("End")
    assert tip(page, "chart-bar-multiple") == {"label": "June", "items": [["Desktop", "214", False], ["Mobile", "140", True]]}
    page.keyboard.press("Home")
    assert tip(page, "chart-bar-multiple")["label"] == "January"
    assert page.locator("#chart-bar-multiple [data-slot='chart-live']").text_content() == "January: Desktop 186, Mobile 80"
    t.shot("bar-keyboard", card_of(page, "chart-bar-multiple"))
    page.keyboard.press("Escape")
    assert tip(page, "chart-bar-multiple") is None
    assert page.evaluate("document.activeElement === document.querySelector('#chart-bar-multiple [data-slot=chart-svg]')")
    page.keyboard.press("ArrowRight")
    assert tip(page, "chart-bar-multiple")["label"] == "February"
    page.keyboard.press("Tab")
    assert tip(page, "chart-bar-multiple") is None
    assert page.evaluate("document.activeElement.dataset.slot") == "chart-legend-item"
    keyed = [e["detail"]["index"] for e in events(page, "chart:active") if e["detail"]]
    assert keyed[:3] == [0, 1, 1], keyed

    t.section("chart-line")
    line = svg_of(page, "chart-line-multiple")
    line.focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    assert tip(page, "chart-line-multiple") == {"label": "March", "items": [["Desktop", "237", False], ["Mobile", "120", False]]}
    assert page.locator("#chart-line-multiple [data-part='crosshair']").get_attribute("data-active") == ""

    t.section("chart-pie")
    donut = svg_of(page, "chart-pie-donut")
    donut.focus()
    assert tip(page, "chart-pie-donut")["items"][0][:2] == ["Chrome", "275"]
    page.keyboard.press("ArrowRight")
    assert tip(page, "chart-pie-donut")["items"][0][:2] == ["Safari", "200"]
    page.keyboard.press("End")
    assert tip(page, "chart-pie-donut")["items"][0][:2] == ["Other", "90"]
    assert page.locator("#chart-pie-donut [data-slot='chart-live']").text_content() == "Other 90 (9.7%)"

    t.section("chart-radial")
    radial = svg_of(page, "chart-radial-stacked")
    radial.focus()
    assert tip(page, "chart-radial-stacked") == {"label": "January", "items": [["Desktop", "1,260", True], ["Mobile", "570", False]]}
    page.keyboard.press("ArrowRight")
    assert tip(page, "chart-radial-stacked")["items"][1] == ["Mobile", "570", True]
    t.shot("radial-keyboard", card_of(page, "chart-radial-stacked"))

    t.section("chart-radar")
    radar = svg_of(page, "chart-radar-default")
    radar.focus()
    page.keyboard.press("ArrowLeft")
    assert tip(page, "chart-radar-default") == {"label": "January", "items": [["Desktop", "186", False]]}
    page.keyboard.press("End")
    assert tip(page, "chart-radar-default")["label"] == "June"


def check_chart_legend(t):
    page = t.page
    page.evaluate(LISTEN)
    t.section("chart-bar")
    legend = page.locator("#chart-bar-multiple").get_by_role("toolbar", name="Legend")
    items = legend.get_by_role("button")
    assert items.count() == 2
    assert [items.nth(i).get_attribute("aria-pressed") for i in range(2)] == ["true", "true"]
    assert [items.nth(i).get_attribute("tabindex") for i in range(2)] == ["0", "-1"]
    mobile = legend.get_by_role("button", name="Mobile")
    mobile.click()
    assert mobile.get_attribute("aria-pressed") == "false"
    assert page.locator("#chart-bar-multiple [data-key='mobile'] [data-part='bar']").count() == 0
    assert page.locator("#chart-bar-multiple [data-key='desktop'] [data-part='bar']").count() == 6
    assert "Mobile" not in svg_of(page, "chart-bar-multiple").get_attribute("aria-label")
    assert events(page, "chart:legend")[-1]["detail"] == {"key": "mobile", "visible": False, "hidden": ["mobile"]}
    t.shot("legend-hidden", card_of(page, "chart-bar-multiple"))
    legend.get_by_role("button", name="Desktop").focus()
    page.keyboard.press("ArrowRight")
    assert page.evaluate("document.activeElement.textContent") == "Mobile"
    assert [items.nth(i).get_attribute("tabindex") for i in range(2)] == ["-1", "0"]
    page.keyboard.press(" ")
    assert mobile.get_attribute("aria-pressed") == "true"
    assert page.locator("#chart-bar-multiple [data-key='mobile'] [data-part='bar']").count() == 6
    assert events(page, "chart:legend")[-1]["detail"] == {"key": "mobile", "visible": True, "hidden": []}
    tabs = page.evaluate(
        """async () => {
          const { chart } = await import("/clanker-ui-chart.js")
          const rows = [{ m: "x", a: 1, b: 2 }, { m: "y", a: 2, b: 1 }]
          const detached = document.createElement("div")
          detached.id = "chart-probe-detached"
          window.__chartDetached = chart(detached, rows, { x: "m" })
          document.body.append(detached)
          const hidden = document.createElement("div")
          hidden.hidden = true
          document.body.append(hidden)
          const view = chart(hidden, rows, { x: "m" })
          hidden.hidden = false
          const tabs = el => [...el.querySelectorAll('[data-slot="chart-legend-item"]')].map(i => i.tabIndex)
          const out = [tabs(detached), tabs(hidden)]
          view.destroy()
          hidden.remove()
          return out
        }"""
    )
    assert tabs == [[0, -1], [0, -1]], f"legend tab stops of charts made detached or hidden: {tabs}"
    page.locator("#chart-probe-detached [data-slot='chart-svg']").focus()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.closest('#chart-probe-detached [data-slot=chart-legend]') !== null"), "Tab does not reach the legend"
    page.evaluate("() => { window.__chartDetached.destroy(); document.getElementById('chart-probe-detached').remove() }")

    t.section("chart-pie")
    pie = page.locator("#chart-pie-donut-text")
    pie.get_by_role("button", name="Chrome").click()
    assert page.locator("#chart-pie-donut-text [data-part='slice']").count() == 4
    assert page.locator("#chart-pie-donut-text [data-part='center-value']").text_content() == "650"
    pie.get_by_role("button", name="Chrome").click()
    assert page.locator("#chart-pie-donut-text [data-part='center-value']").text_content() == "925"


def check_chart_table(t):
    page = t.page
    page.evaluate(LISTEN)
    t.section("chart-bar")
    root = page.locator("#chart-bar-multiple")
    toggle = root.get_by_role("button", name="Table view")
    assert toggle.get_attribute("aria-pressed") == "false"
    plot_height = page.evaluate("() => document.querySelector('#chart-bar-multiple [data-slot=chart-plot]').offsetHeight")
    toggle.click()
    assert toggle.get_attribute("aria-pressed") == "true"
    region = root.get_by_role("region", name="Visitors, January to June 2024 data")
    assert region.is_visible()
    assert root.locator("[data-slot='chart-plot']").is_hidden()
    assert root.get_attribute("data-view") == "table"
    assert page.evaluate("() => document.querySelector('#chart-bar-multiple [data-slot=chart-table]').offsetHeight") == plot_height
    table = region.get_by_role("table")
    assert table.locator("thead th").all_text_contents() == ["Month", "Desktop", "Mobile"]
    assert table.locator("tbody tr").count() == 6
    rows = [table.locator("tbody tr").nth(i).locator("th, td").all_text_contents() for i in range(6)]
    assert rows == [[m, str(d), str(v)] for m, d, v in zip(MONTHS, DESKTOP, MOBILE)], rows
    assert table.locator("tbody th").first.get_attribute("scope") == "row"
    assert events(page, "chart:view")[-1]["detail"] == {"view": "table"}
    t.shot("table", card_of(page, "chart-bar-multiple"))
    page.keyboard.press("Shift")
    toggle.focus()
    page.keyboard.press("Enter")
    assert toggle.get_attribute("aria-pressed") == "false"
    assert root.locator("[data-slot='chart-table']").is_hidden()
    assert page.locator("#chart-bar-multiple [data-part='bar']").count() == 12
    assert events(page, "chart:view")[-1]["detail"] == {"view": "chart"}

    t.section("chart-pie")
    pie = page.locator("#chart-pie-donut")
    pie.get_by_role("button", name="Table view").click()
    table = pie.get_by_role("table")
    assert table.locator("thead th").all_text_contents() == ["Browser", "Visitors", "Share"]
    assert table.locator("tbody tr").first.locator("th, td").all_text_contents() == ["Chrome", "275", "29.7%"]
    t.section("chart-stat")
    area = page.locator("#chart-stat-area")
    area.get_by_role("button", name="Table view").click()
    first = area.get_by_role("table").locator("tbody tr").first.locator("th, td").all_text_contents()
    assert first[0] == "Jun 1, 2024", first


def check_chart_update(t):
    page = t.page
    t.section("chart-stat")
    area = svg_of(page, "chart-stat-area")
    value = page.locator("#chart-stat-visitors [data-slot='chart-stat-value']")
    assert "30 points from Jun 1, 2024 to Jun 30, 2024" in area.get_attribute("aria-label")
    before = value.text_content()
    week = page.get_by_role("button", name="Last 7 days")
    week.click()
    assert week.get_attribute("aria-pressed") == "true"
    assert page.get_by_role("button", name="Last 30 days").get_attribute("aria-pressed") == "false"
    assert "7 points from Jun 24, 2024 to Jun 30, 2024" in area.get_attribute("aria-label")
    assert value.text_content() != before
    assert page.locator("#chart-stat-visitors [data-slot='chart-stat-period']").text_content() == "vs previous 7 days"
    t.shot("dashboard-7")
    page.get_by_role("button", name="Last 45 days").click()
    assert "45 points from May 17, 2024" in area.get_attribute("aria-label")
    result = page.evaluate(
        PROBE,
        ["chart-probe-update", 320, {"rows": [{"m": "a", "v": 1}, {"m": "b", "v": 3}], "config": {"v": {"label": "V"}}}, {"type": "bar", "x": "m"}],
    )
    assert result["width"] == 320
    after = page.evaluate(
        """() => {
          const box = document.getElementById("chart-probe-update")
          window.__chartProbe.update({ rows: [{ m: "a", v: 5 }, { m: "b", v: 2 }, { m: "c", v: 9 }] }, { type: "line", dots: true })
          const first = { type: box.dataset.type, dots: box.querySelectorAll('[data-part="dot"]').length, label: box.querySelector('[data-slot="chart-svg"]').getAttribute("aria-label") }
          window.__chartProbe.update(null, { type: "area", label: "Probe" })
          const second = { type: box.dataset.type, label: box.querySelector('[data-slot="chart-svg"]').getAttribute("aria-label") }
          window.__chartProbe.destroy()
          box.remove()
          return [first, second]
        }"""
    )
    assert after[0] == {"type": "line", "dots": 3, "label": "Line chart. V, 3 points from a to c. V from 2 to 9."}, after
    assert after[1] == {"type": "area", "label": "Area chart, Probe. V, 3 points from a to c. V from 2 to 9."}, after
    rollback = page.evaluate(
        """async () => {
          const { chart, statTile } = await import("/clanker-ui-chart.js")
          const box = document.createElement("div")
          const tile = document.createElement("div")
          box.style.width = "300px"
          document.body.append(box, tile)
          const attempt = fn => {
            try {
              fn()
              return "ok"
            } catch (e) {
              return e.name
            }
          }
          const rows = [{ m: "a", v: 1 }, { m: "b", v: 3 }]
          const view = chart(box, rows, { type: "bar", x: "m" })
          const nine = Object.fromEntries(["m", ...Array.from({ length: 9 }, (_, i) => `s${i}`)].map((k, i) => [k, i ? i : "a"]))
          const out = [
            attempt(() => view.update(null, { type: "scatter" })),
            box.dataset.type,
            attempt(() => view.update([nine])),
            box.querySelectorAll('[data-part="bar"]').length,
            attempt(() => view.update(null, { type: "line", curve: "linear" })),
            box.dataset.type,
          ]
          const stat = statTile(tile, { label: "Users", value: 5 })
          out.push(attempt(() => stat.update({ format: { style: "currency" } })), tile.querySelector('[data-slot="chart-stat-value"]').textContent)
          out.push(attempt(() => stat.update({ value: 7 })), tile.querySelector('[data-slot="chart-stat-value"]').textContent)
          const fresh = document.createElement("div")
          fresh.append("keep")
          out.push(attempt(() => statTile(fresh, { label: "X", value: 1, format: { style: "currency" } })), fresh.textContent, fresh.attributes.length)
          view.destroy()
          stat.destroy()
          box.remove()
          tile.remove()
          return out
        }"""
    )
    assert rollback == ["TypeError", "bar", "RangeError", 2, "ok", "line", "TypeError", "5", "ok", "7", "TypeError", "keep", 0], f"a failed update breaks the chart: {rollback}"


def check_chart_resize(t):
    page = t.page
    data = {"rows": [{"m": "a", "v": 1}, {"m": "b", "v": 3}], "config": {"v": {"label": "V"}}}
    result = page.evaluate(PROBE, ["chart-probe-resize", 360, data, {"type": "bar", "x": "m"}])
    assert result["width"] == 360 and [result["width"], result["height"]] == result["plot"], result
    page.evaluate("() => { document.getElementById('chart-probe-resize').style.width = '240px' }")
    page.wait_for_function("() => document.querySelector('#chart-probe-resize [data-slot=chart-svg]').getAttribute('width') === '240'")
    size = page.evaluate(
        """() => {
          const box = document.getElementById("chart-probe-resize")
          const plot = box.querySelector('[data-slot="chart-plot"]').getBoundingClientRect()
          const svg = box.querySelector('[data-slot="chart-svg"]')
          return [+svg.getAttribute("height"), Math.floor(plot.height), svg.getAttribute("viewBox")]
        }"""
    )
    assert size[0] == size[1] and size[2] == f"0 0 240 {size[0]}", size
    page.evaluate("() => { window.__chartProbe.destroy(); document.getElementById('chart-probe-resize').remove() }")
    t.section("chart-bar")
    surface = svg_of(page, "chart-bar-default")
    width = int(surface.get_attribute("width"))
    page.set_viewport_size({"width": t.width - 60, "height": 800})
    page.wait_for_function("w => +document.querySelector('#chart-bar-default [data-slot=chart-svg]').getAttribute('width') !== w", arg=width)
    assert page.locator("#chart-bar-default [data-part='bar']").count() == 6


def check_chart_destroy(t):
    page = t.page
    result = page.evaluate(
        """async () => {
          const { chart, statTile } = await import("/clanker-ui-chart.js")
          const box = document.createElement("div")
          box.className = "probe"
          box.append("placeholder")
          document.body.append(box)
          const rows = [{ m: "a", v: 1, w: 2 }, { m: "b", v: 3, w: 1 }]
          const view = chart(box, rows, { type: "line", x: "m", height: 200 })
          const before = { slot: box.dataset.slot, type: box.dataset.type, kids: box.children.length, height: box.style.height, color: box.style.getPropertyValue("--color-v") }
          box.querySelector('[data-slot="chart-svg"]').focus()
          const open = !box.querySelector('[data-slot="chart-tooltip"]').hidden
          const replaced = chart(box, rows, { type: "bar", x: "m" })
          const single = box.querySelectorAll('[data-slot="chart-svg"]').length
          let threwOld = false
          try { view.update(rows) } catch { threwOld = true }
          const drawn = box.querySelector('[data-slot="chart-svg"]')
          replaced.destroy()
          replaced.destroy()
          let threw = false
          try { replaced.update(rows) } catch { threw = true }
          const after = { attrs: [...box.attributes].map(a => a.name), text: box.textContent, kids: box.childNodes.length }
          const tile = document.createElement("div")
          document.body.append(tile)
          const stat = statTile(tile, { label: "X", value: 5, delta: 0.1, trend: [1, 2, 3] })
          const tileSlot = tile.dataset.slot
          const tileSpark = tile.querySelectorAll('[data-slot="chart"]').length
          const sparkDrawn = tile.querySelector('[data-slot="chart-svg"]')
          stat.destroy()
          let redraws = 0
          const watch = new MutationObserver(records => { redraws += records.length })
          for (const el of [drawn, sparkDrawn]) watch.observe(el, { subtree: true, childList: true, attributes: true, characterData: true })
          const tileAfter = [[...tile.attributes].map(a => a.name), tile.childNodes.length]
          const { theme } = await import("/clanker-ui.js")
          const mode = theme.get()
          theme.set(theme.resolved() === "dark" ? "light" : "dark")
          for (let i = 0; i < 3; i++) await new Promise(r => requestAnimationFrame(r))
          watch.takeRecords().forEach(() => redraws++)
          watch.disconnect()
          const themed = { box: [box.textContent, box.childNodes.length, [...box.attributes].map(a => a.name)], tile: [tile.childNodes.length, tile.attributes.length], redraws }
          theme.set(mode)
          box.remove()
          tile.remove()
          return { before, open, single, threwOld, threw, after, tileSlot, tileSpark, tileAfter, themed }
        }"""
    )
    assert result["before"] == {"slot": "chart", "type": "line", "kids": 4, "height": "200px", "color": "var(--chart-1)"}, result
    assert result["open"] and result["single"] == 1 and result["threwOld"] and result["threw"], result
    assert result["after"] == {"attrs": ["class"], "text": "placeholder", "kids": 1}, result
    assert result["tileSlot"] == "chart-stat" and result["tileSpark"] == 1 and result["tileAfter"] == [[], 0], result
    page.keyboard.press("Escape")
    shown = page.evaluate("() => [...document.querySelectorAll('[data-slot=chart-tooltip]')].filter(e => !e.hidden).length")
    assert shown == 0, f"{shown} chart tooltips stay open after destroy"
    assert result["themed"] == {"box": ["placeholder", 1, ["class"]], "tile": [0, 0], "redraws": 0}, f"destroyed charts must not redraw on theme:change: {result['themed']}"


def check_chart_errors(t):
    result = t.page.evaluate(
        """async () => {
          const { chart } = await import("/clanker-ui-chart.js")
          const box = document.createElement("div")
          document.body.append(box)
          const attempt = fn => { try { fn(); return "ok" } catch (e) { return e.name } }
          const nine = Object.fromEntries(["x", ...Array.from({ length: 9 }, (_, i) => `s${i}`)].map((k, i) => [k, i ? i : "a"]))
          const other = document.createElement("div")
          other.dataset.slot = "card"
          const out = [
            attempt(() => chart(box, [], { type: "scatter" })),
            attempt(() => chart(box, [nine], { type: "bar", x: "x" })),
            attempt(() => chart(other, [])),
            attempt(() => chart(box, [{ x: "a", v: 1 }], { type: "line", x: "x", curve: "wiggly" })),
            attempt(() => chart(box, { rows: [{ x: "a", v: 1 }], config: { v: { color: "not a color!" } } }, { type: "bar", x: "x" })),
            attempt(() => chart(box, [{ x: "a", v: 1 }], { type: "bar", x: "x", view: "grid" })),
            attempt(() => chart("nope", [])),
          ]
          const leftover = [box.childNodes.length, box.attributes.length]
          const okay = attempt(() => chart(box, { rows: [{ x: "a", v: 1, w: 2 }], config: { v: { color: "chart-2" }, w: { theme: { light: "#000", dark: "#fff" } } } }, { type: "bar", x: "x" }))
          const colors = [box.style.getPropertyValue("--color-v"), box.style.getPropertyValue("--color-w")]
          box.remove()
          return { out, leftover, okay, colors }
        }"""
    )
    assert result["out"] == ["TypeError", "RangeError", "TypeError", "TypeError", "TypeError", "TypeError", "TypeError"], result
    assert result["leftover"] == [0, 0], result
    assert result["okay"] == "ok" and result["colors"] == ["var(--chart-2)", "light-dark(#000, #fff)"], result


def check_chart_stat(t):
    page = t.page
    t.section("chart-stat")
    revenue = page.locator("#chart-stat-revenue")
    assert revenue.get_attribute("data-slot") == "chart-stat"
    assert page.get_by_role("group", name="Total revenue").count() == 1
    assert revenue.locator("[data-slot='chart-stat-value']").text_content() == "$1,250.00"
    assert revenue.locator("[data-slot='chart-stat-value'] data").get_attribute("value") == "1250"
    delta = revenue.locator("[data-slot='chart-stat-delta']")
    assert [delta.get_attribute("data-direction"), delta.get_attribute("data-tone")] == ["up", "good"]
    assert delta.locator("[data-slot='chart-stat-change']").text_content() == "+12.5%"
    assert delta.locator("[data-slot='chart-stat-period']").text_content() == "vs last month"
    assert delta.locator("svg").get_attribute("data-lucide") == "trending-up"
    customers = page.locator("#chart-stat-customers [data-slot='chart-stat-delta']")
    assert [customers.get_attribute("data-direction"), customers.get_attribute("data-tone")] == ["down", "bad"]
    churn = page.locator("#chart-stat-churn [data-slot='chart-stat-delta']")
    assert [churn.get_attribute("data-direction"), churn.get_attribute("data-tone")] == ["up", "bad"]
    assert page.locator("#chart-stat-accounts [data-slot='chart-stat-value']").text_content() == "45.7K"
    good = "rgb(0, 99, 0)" if t.theme == "light" else "rgb(12, 163, 12)"
    assert page.evaluate("e => getComputedStyle(e).color", delta.element_handle()) == good
    spark = revenue.locator("[data-slot='chart-svg']")
    assert spark.get_attribute("aria-label") == "Sparkline, Total revenue trend. 12 points from 1 to 12, low $820.00, high $1,250.00, latest $1,250.00."
    plot = revenue.locator("[data-slot='chart-plot']")
    plot_height = plot.evaluate("e => e.offsetHeight")
    toggle = revenue.get_by_role("button", name="Table view")
    assert toggle.is_visible(), "sparkline table toggle"
    toggle.click()
    region = revenue.get_by_role("region", name="Total revenue trend data")
    assert region.is_visible() and plot.is_hidden(), "sparkline table view"
    assert region.evaluate("e => e.offsetHeight") == plot_height, region.evaluate("e => e.offsetHeight")
    head = region.locator("thead th").all_text_contents()
    assert head == ["#"] + [str(i) for i in range(1, 13)], head
    row = region.locator("tbody tr").first.locator("th, td").all_text_contents()
    assert row[0] == "Value" and row[1] == "$820.00" and row[-1] == "$1,250.00" and len(row) == 13, row
    t.shot("stat-table", page.locator("#chart-stat [data-demo='chart-kpis']").first)
    toggle.click()
    assert plot.is_visible() and region.is_hidden(), "sparkline back to chart view"
    box = box_of(page, "chart-stat-revenue")
    page.mouse.move(box["x"] + box["width"] - 2, box["y"] + box["height"] / 2)
    assert tip(page, "chart-stat-revenue") == {"label": "12", "items": [["Value", "$1,250.00", False]]}
    t.shot("stat-hover", page.locator("#chart-stat [data-demo='chart-kpis']").first)


def check_chart_palette(t):
    page = t.page
    contrast = page.evaluate(INK_CONTRAST)
    assert len(contrast) >= 10 and all(c["chosen"] >= c["other"] for c in contrast), contrast
    t.a11y()
    flip = "dark" if t.theme == "light" else "light"
    page.evaluate("async mode => (await import('/clanker-ui.js')).theme.set(mode)", flip)
    page.wait_for_function("c => getComputedStyle(document.querySelector('#chart-bar-default [data-part=bar]')).fill === c", arg="rgb(57, 135, 229)" if flip == "dark" else "rgb(42, 120, 214)")
    page.evaluate("async () => (await import('/clanker-ui.js')).theme.set('system')")
    page.wait_for_function("c => getComputedStyle(document.querySelector('#chart-bar-default [data-part=bar]')).fill === c", arg="rgb(42, 120, 214)" if flip == "dark" else "rgb(57, 135, 229)")
    colors = page.evaluate(
        """() => {
          const probe = document.createElement("span")
          probe.hidden = true
          document.body.append(probe)
          const out = []
          for (let i = 1; i <= 8; i++) {
            probe.style.color = `var(--chart-${i})`
            out.push(getComputedStyle(probe).color)
          }
          probe.remove()
          return out
        }"""
    )
    light = ["rgb(42, 120, 214)", "rgb(235, 104, 52)", "rgb(27, 175, 122)", "rgb(237, 161, 0)", "rgb(232, 123, 164)", "rgb(0, 131, 0)", "rgb(98, 80, 214)", "rgb(227, 73, 72)"]
    dark = ["rgb(57, 135, 229)", "rgb(217, 89, 38)", "rgb(25, 158, 112)", "rgb(201, 133, 0)", "rgb(213, 81, 129)", "rgb(0, 131, 0)", "rgb(144, 133, 233)", "rgb(230, 103, 103)"]
    assert colors == (light if t.theme == "light" else dark), colors
    bar = page.locator("#chart-bar-default [data-part='bar']").first
    assert page.evaluate("e => getComputedStyle(e).fill", bar.element_handle()) == colors[0]
    dot = page.locator("#chart-line-dots [data-part='dot']").first
    ring = page.evaluate("e => [getComputedStyle(e).strokeWidth, getComputedStyle(e).stroke, getComputedStyle(e).getPropertyValue('--chart-surface').trim()]", dot.element_handle())
    card = page.evaluate("() => { const p = document.createElement('p'); p.style.color = 'var(--card)'; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c }")
    assert ring[0] == "2px" and ring[1] == card, ring
    ink = [i.get_attribute("data-ink") for i in page.locator("#chart-pie-label-list text[data-part='label']").all()]
    assert ink == ["dark"] * 5, ink
    contrast = page.evaluate(INK_CONTRAST)
    assert len(contrast) >= 10 and all(c["chosen"] >= c["other"] for c in contrast), contrast
    other = "dark" if t.theme == "light" else "light"
    page.evaluate(
        """async () => {
          const { chart } = await import("/clanker-ui-chart.js")
          const box = document.createElement("div")
          box.id = "chart-probe-ink"
          box.style.width = "240px"
          document.body.append(box)
          window.__chartInk = chart(box, { rows: [{ k: "a", v: 1 }], config: { a: { label: "Navy", theme: { light: "#1e3a8a", dark: "#fde68a" } } } }, { type: "pie", x: "k", labels: "name", labelPosition: "inside" })
        }"""
    )
    label = "#chart-probe-ink text[data-part='label']"
    assert page.get_attribute(label, "data-ink") == ("light" if t.theme == "light" else "dark"), page.get_attribute(label, "data-ink")
    page.evaluate("async mode => (await import('/clanker-ui.js')).theme.set(mode)", other)
    flipped = "rgb(57, 135, 229)" if other == "dark" else "rgb(42, 120, 214)"
    page.wait_for_function("c => getComputedStyle(document.querySelector('#chart-bar-default [data-part=bar]')).fill === c", arg=flipped)
    page.wait_for_function("([sel, ink]) => document.querySelector(sel)?.getAttribute('data-ink') === ink", arg=[label, other])
    page.evaluate("async () => { (await import('/clanker-ui.js')).theme.set('system'); window.__chartInk.destroy(); document.getElementById('chart-probe-ink').remove() }")


def check_chart_motion(t):
    page = t.page
    probe = """async () => {
      const { chart } = await import("/clanker-ui-chart.js")
      const box = document.createElement("div")
      box.style.width = "300px"
      document.body.append(box)
      const view = chart(box, [{ m: "a", v: 1 }, { m: "b", v: 2 }], { type: "bar", x: "m" })
      const s = getComputedStyle(box.querySelector('[data-part="bar"]')).animationDuration
      view.destroy()
      box.remove()
      return parseFloat(s) * (s.endsWith("ms") ? 1 : 1000)
    }"""
    page.emulate_media(reduced_motion="no-preference")
    assert page.evaluate(probe) == 500
    page.emulate_media(reduced_motion="reduce")
    assert page.evaluate(probe) < 1


def check_chart_scale(t):
    page = t.page
    page.evaluate(
        """async () => {
          const { chart } = await import("/clanker-ui-chart.js")
          window.__chartTicks = null
          const box = document.createElement("div")
          box.style.width = "400px"
          document.body.append(box)
          setTimeout(() => {
            const out = []
            for (const [rows, options] of [
              [[{ m: "a", v: 1e17 }, { m: "b", v: 1e17 + 16 }], { x: "m", type: "line", zero: false }],
              [[{ m: "a", v: 5 }], { x: "m", type: "line", domain: [1e17, 1e17 + 16] }],
              [[{ m: "a", v: 1e17 }, { m: "b", v: 1e17 + 1024 }], { x: "m", type: "bar", zero: false }],
              [[{ m: "a", v: 0.1 }, { m: "b", v: 0.7 }], { x: "m", type: "line" }],
            ]) {
              const view = chart(box, rows, options)
              out.push([...box.querySelectorAll('[data-axis="value"] text')].map(e => e.textContent))
              view.destroy()
            }
            box.remove()
            window.__chartTicks = out
          }, 0)
        }"""
    )
    page.wait_for_function("() => window.__chartTicks !== null", timeout=5000)
    ticks = page.evaluate("window.__chartTicks")
    assert all(2 <= len(list) <= 50 for list in ticks[:3]), f"ticks for huge values with a tiny range: {ticks}"
    assert ticks[3] == ["0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7"] or ticks[3] == ["0", "0.2", "0.4", "0.6", "0.8"], ticks[3]
    result = page.evaluate(
        """async () => {
          const { chart } = await import("/clanker-ui-chart.js")
          const box = document.createElement("div")
          box.style.width = "600px"
          document.body.append(box)
          const rows = Array.from({ length: 200000 }, (_, i) => ({ m: `c${i}`, v: i % 97 }))
          const out = []
          for (const options of [{ type: "line" }, { type: "bar", horizontal: true, labels: true }]) {
            try {
              const view = chart(box, rows, { x: "m", ...options })
              out.push(box.querySelector('[data-slot="chart-svg"]').getAttribute("aria-label").endsWith(" to c199999. V from 0 to 96.") || box.querySelector('[data-slot="chart-svg"]').getAttribute("aria-label"))
              view.destroy()
            } catch (e) {
              out.push(`${e.name}: ${e.message}`)
            }
          }
          box.remove()
          return out
        }"""
    )
    assert result == [True, True], f"200,000 rows: {result}"


def check_chart_rtl(t):
    page = t.page
    result = page.evaluate(
        """async () => {
          const { chart } = await import("/clanker-ui-chart.js")
          const wrap = document.createElement("div")
          wrap.dir = "rtl"
          wrap.style.width = "400px"
          const box = document.createElement("div")
          wrap.append(box)
          document.body.append(wrap)
          const rows = [{ m: "January", v: 186 }, { m: "February", v: 305 }, { m: "March", v: -237 }]
          chart(box, rows, { type: "bar", x: "m", horizontal: true, animate: false, height: 200 })
          await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
          const svg = box.querySelector('[data-slot="chart-svg"]')
          const left = Math.min(...[...svg.querySelectorAll('[data-part="bar"]')].map(b => b.getBBox().x))
          const ticks = [...svg.querySelectorAll('text[text-anchor="end"]:not([data-part])')].map(e => { const b = e.getBBox(); return [e.textContent, Math.round(b.x + b.width)] })
          const out = { svg: getComputedStyle(svg).direction, footer: getComputedStyle(box.querySelector('[data-slot="chart-footer"]')).direction, left: Math.round(left), ticks }
          wrap.remove()
          return out
        }"""
    )
    assert result["svg"] == "ltr" and result["footer"] == "rtl", f"the plot stays left to right, the footer follows the page: {result}"
    assert len(result["ticks"]) == 3 and all(right <= result["left"] for _, right in result["ticks"]), f"category labels stay left of the bars in RTL: {result}"


def check_chart_locale(t):
    result = t.page.evaluate(
        """async () => {
          const { chart, statTile } = await import("/clanker-ui-chart.js")
          const root = document.documentElement
          const lang = root.lang
          root.lang = "en_US"
          const box = document.createElement("div")
          const tile = document.createElement("div")
          document.body.append(box, tile)
          const out = {}
          try {
            const view = chart(box, [{ m: "a", v: 1234 }, { m: "b", v: 2 }], { x: "m" })
            out.chart = box.querySelector('[data-slot="chart-table"] td').textContent
            view.destroy()
          } catch (e) {
            out.chart = `${e.name}: ${e.message}`
          }
          try {
            const view = statTile(tile, { label: "Users", value: 12345 })
            out.stat = tile.querySelector('[data-slot="chart-stat-value"]').textContent
            view.destroy()
          } catch (e) {
            out.stat = `${e.name}: ${e.message}`
          }
          root.lang = lang
          box.remove()
          tile.remove()
          return out
        }"""
    )
    assert result == {"chart": "1,234", "stat": "12.3K"}, f"invalid <html lang>: {result}"


def check_chart_colors(t):
    result = t.page.evaluate(
        """async () => {
          const { chart } = await import("/clanker-ui-chart.js")
          const config = { a: { label: "A" }, b: { label: "B" }, c: { label: "C" } }
          const box = document.createElement("div")
          box.style.width = "300px"
          document.body.append(box)
          const color = () => box.style.getPropertyValue("--color-c")
          const out = {}
          const bar = chart(box, { rows: [{ m: "x", a: 1, b: 2, c: 3 }], config }, { x: "m" })
          out.bar = [color()]
          bar.update({ rows: [{ m: "x", a: 1, b: null, c: 3 }] })
          out.bar.push(color())
          bar.update({ rows: [{ m: "x", a: 1, c: 3 }] })
          out.bar.push(color())
          const pie = chart(box, { rows: [{ k: "a", v: 1 }, { k: "b", v: 2 }, { k: "c", v: 3 }], config: { v: { label: "V" }, ...config } }, { type: "pie", x: "k" })
          out.pie = [color()]
          pie.update({ rows: [{ k: "a", v: 1 }, { k: "c", v: 3 }] })
          out.pie.push(color())
          const spaced = chart(box, [{ m: "a", "page views": 3, "café": 1 }], { x: "m" })
          out.spaced = [box.style.getPropertyValue("--color-page-views"), box.style.getPropertyValue("--color-café")]
          spaced.destroy()
          const attempt = c => {
            try {
              chart(box, { rows: [{ m: "x", a: 1 }], config: { a: { color: c } } }, { x: "m" }).destroy()
              return "ok"
            } catch (e) {
              return e.name
            }
          }
          out.colors = ["var(--nope, url(https://example.invalid/x.png))", "var(--nope, URL(x.png))", "var(--nope, u\\\\72l(x.png))", "var(--nope, src('x.png'))", "var(--chart-2)", "light-dark(red, blue)", "oklch(0.6 0.1 200)"].map(attempt)
          box.remove()
          return out
        }"""
    )
    assert result["bar"] == ["var(--chart-3)"] * 3, f"series color shifts when a series has no data: {result}"
    assert result["pie"] == ["var(--chart-3)"] * 2, f"slice color shifts when a category has no row: {result}"
    assert result["spaced"] == ["var(--chart-1)", "var(--chart-2)"], f"--color-<key> for keys with other characters: {result}"
    assert result["colors"] == ["TypeError"] * 4 + ["ok"] * 3, f"colors that load resources: {result}"


def check_chart_marks(t):
    result = t.page.evaluate(
        """async () => {
          const { chart, sparkline } = await import("/clanker-ui-chart.js")
          const box = document.createElement("div")
          box.style.width = "300px"
          document.body.append(box)
          const out = {}
          const expand = chart(box, { rows: [{ m: "x", a: 60, b: -20 }] }, { x: "m", type: "bar", stack: "expand" })
          box.querySelector('[data-slot="chart-svg"]').focus()
          out.expand = [...box.querySelectorAll('[data-slot="chart-tooltip-item"]')].map(i => i.textContent)
          expand.destroy()
          const dots = () => [...box.querySelectorAll('[data-part="dot"]')].map(d => [d.getAttribute("r"), Math.round(d.getBBox().width)])
          chart(box, [{ m: "Jan", v: 5 }], { x: "m", type: "line" })
          out.one = dots()
          chart(box, [{ m: "a", v: 1 }, { m: "b", v: null }, { m: "c", v: 2 }, { m: "d", v: 3 }], { x: "m", type: "area" })
          out.gap = dots()
          sparkline(box, [3])
          out.spark = [...box.querySelectorAll('[data-part="dot"]')].map(d => d.hasAttribute("data-accent"))
          const pie = chart(box, { rows: [{ k: "a", v: 1 }, { k: "b", v: 2 }] }, { type: "pie", x: "k" })
          for (const item of box.querySelectorAll('[data-slot="chart-legend-item"]')) item.click()
          out.empty = box.querySelector('[data-slot="chart-svg"]').getAttribute("aria-label")
          pie.destroy()
          box.remove()
          return out
        }"""
    )
    assert result["expand"] == ["A6075%", "B-20-25%", "Total40"], f"expand tooltip with negatives: {result}"
    assert result["one"] == [["4", 8]], f"one-row line chart: {result}"
    assert result["gap"] == [["4", 8]], f"isolated point between gaps: {result}"
    assert result["spark"] == [True], f"one-point sparkline: {result}"
    assert result["empty"] == "Pie chart. All series are hidden.", f"pie with every slice hidden: {result}"


def check_chart_lifecycle(t):
    page = t.page
    t.a11y()
    page.evaluate(
        """async () => {
          const { chart } = await import("/clanker-ui-chart.js")
          const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
          const box = document.createElement("div")
          box.style.width = "300px"
          document.body.append(box)
          chart(box, { rows: [{ k: "a", v: 1 }, { k: "b", v: 2 }] }, { type: "pie", x: "k", labels: true, labelPosition: "inside" })
          await frame()
          const surface = box.querySelector('[data-slot="chart-svg"]')
          surface.focus()
          const tip = box.querySelector('[data-slot="chart-tooltip"]')
          const open = !tip.hidden
          box.remove()
          await frame()
          let renders = 0
          const replace = surface.replaceChildren
          surface.replaceChildren = function (...nodes) {
            renders++
            return replace.apply(this, nodes)
          }
          window.__chartLifecycle = { box, surface, open, closed: tip.hidden, count: () => renders }
          return true
        }"""
    )
    other = "dark" if t.theme == "light" else "light"
    page.evaluate("async mode => (await import('/clanker-ui.js')).theme.set(mode)", other)
    page.wait_for_function("c => getComputedStyle(document.querySelector('#chart-bar-default [data-part=bar]')).fill === c", arg="rgb(57, 135, 229)" if other == "dark" else "rgb(42, 120, 214)")
    result = page.evaluate(
        """async () => {
          const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
          await frame()
          const c = window.__chartLifecycle
          const detached = c.count()
          document.body.append(c.box)
          await frame()
          const back = [c.count(), c.surface.querySelectorAll('[data-part="slice"]').length]
          c.box.remove()
          return { open: c.open, closed: c.closed, detached, back }
        }"""
    )
    page.evaluate("async () => (await import('/clanker-ui.js')).theme.set('system')")
    assert result["open"] and result["closed"], f"tooltip of a removed chart stays open: {result}"
    assert result["detached"] == 0, f"removed chart re-renders on theme change: {result}"
    assert result["back"][0] >= 1 and result["back"][1] == 2, f"re-inserted chart does not catch up: {result}"


def check_chart_strings(t):
    result = t.page.evaluate(
        """async () => {
          const { chart, statTile } = await import("/clanker-ui-chart.js")
          const { strings } = await import("/clanker-ui.js")
          const saved = { ...strings }
          Object.assign(strings, {
            barChart: "Stolpični grafikon",
            legend: "Legenda",
            total: "Skupaj",
            value: "Vrednost",
            share: "Delež",
            tableOf: "Podatki: {caption}",
            points: "{count} točk od {from} do {to}",
            seriesRange: "{label} od {low} do {high}",
            trendOf: "Trend: {label}",
          })
          const box = document.createElement("div")
          const tile = document.createElement("div")
          box.style.width = "300px"
          box.dataset.stringTableView = "Tabela"
          document.body.append(box, tile)
          const out = {}
          try {
            const view = chart(box, [{ m: "a", d: 1, e: 2 }, { m: "b", d: 3, e: 4 }], { x: "m", type: "bar", stack: true, locale: "sl" })
            const surface = box.querySelector('[data-slot="chart-svg"]')
            surface.focus()
            out.summary = surface.getAttribute("aria-label")
            out.legend = box.querySelector('[data-slot="chart-legend"]').getAttribute("aria-label")
            out.toggle = box.querySelector('[data-slot="chart-table-toggle"]').getAttribute("aria-label")
            out.total = [...box.querySelectorAll('[data-slot="chart-tooltip-name"]')].at(-1).textContent
            out.table = box.querySelector('[data-slot="chart-table"]').getAttribute("aria-label")
            view.destroy()
            const stat = statTile(tile, { label: "Prihodki", value: 5, trend: [1, 2] })
            out.trend = tile.querySelector('[data-slot="chart-svg"]').getAttribute("aria-label")
            out.cells = [...tile.querySelectorAll('[data-slot="chart-table"] :is(th, td)')].map(c => c.textContent)
            stat.destroy()
          } finally {
            Object.assign(strings, saved)
            box.remove()
            tile.remove()
          }
          return out
        }"""
    )
    assert result == {
        "summary": "Stolpični grafikon. D in E, 2 točk od a do b. D od 1 do 3. E od 2 do 4.",
        "legend": "Legenda",
        "toggle": "Tabela",
        "total": "Skupaj",
        "table": "Podatki: Stolpični grafikon",
        "trend": "Sparkline, Trend: Prihodki. 2 točk od 1 do 2, low 1, high 2, latest 2.",
        "cells": ["#", "1", "2", "Vrednost", "1", "2"],
    }, f"chart strings: {result}"


def check_chart_impossible_date(t):
    page = t.page
    result = page.evaluate(
        """async () => {
          const { chart } = await import("/clanker-ui-chart.js")
          const out = {}
          for (const [name, days] of Object.entries({ impossible: ["2026-02-30", "2026-03-01"], text: ["nope", "2026-03-01"], leap: ["2024-02-29", "2024-03-01"] })) {
            const box = document.createElement("div")
            document.body.append(box)
            const view = chart(box, days.map((d, i) => ({ d, v: i + 1 })), { x: "d", type: "line", locale: "en-US" })
            out[name] = box.querySelector('[data-slot="chart-svg"]').getAttribute("aria-label")
            view.destroy()
            box.remove()
          }
          return out
        }"""
    )
    assert result == {
        "impossible": "Line chart. V, 2 points from 2026-02-30 to 2026-03-01. V from 1 to 2.",
        "text": "Line chart. V, 2 points from nope to 2026-03-01. V from 1 to 2.",
        "leap": "Line chart. V, 2 points from Feb 29, 2024 to Mar 1, 2024. V from 1 to 2.",
    }, ("an impossible ISO date counts as no date, not as a rolled-over day", result)
