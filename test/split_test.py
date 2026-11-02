import re

START = "/test/split/core.html"

PROPS = ["display", "position", "visibility", "opacity", "color", "background-color", "border-top-color", "border-top-width", "border-right-width", "border-bottom-width", "border-left-width", "border-top-left-radius", "border-top-right-radius", "border-bottom-right-radius", "border-bottom-left-radius", "top", "right", "bottom", "left", "min-width", "max-width", "padding-top", "padding-left", "margin-top", "margin-left", "width", "height", "gap", "font-size", "font-weight", "line-height", "box-shadow", "outline-style", "transform", "flex-direction", "justify-content", "align-items", "overflow-x", "cursor", "text-decoration-line", "z-index"]

ID_ATTRS = {"id", "for", "aria-controls", "aria-labelledby", "aria-describedby", "aria-activedescendant", "aria-owns", "aria-details", "popovertarget", "list", "form"}

SNAPSHOT = """([props, portal]) => [...document.querySelectorAll(portal ? "main *, [data-slot=toast-portal], [data-slot=toast-portal] *" : "main *")].map(e => {
  const s = getComputedStyle(e)
  return [e.localName, [...e.attributes].map(a => [a.name, a.value]), props.map(p => s.getPropertyValue(p))]
})"""

SETTLE = """async () => {
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
  const running = document.getAnimations().filter(a => a.timeline === document.timeline && a.playState === "running" && a.effect?.getComputedTiming().endTime !== Infinity)
  await Promise.race([Promise.all(running.map(a => a.finished.catch(() => {}))), new Promise(r => setTimeout(r, 3000))])
  for (const a of document.getAnimations()) {
    if (a.effect?.getComputedTiming().endTime === Infinity) {
      a.pause()
      a.currentTime = 0
    }
  }
  await new Promise(r => requestAnimationFrame(r))
}"""

FULL_HEAD = '  <link rel="stylesheet" href="../../clanker-ui.css">\n  <script type="module" src="../../clanker-ui.js"></script>\n'


def to_full(html):
    lines = [l for l in html.split("\n") if not re.search(r'href="\.\./\.\./clanker-ui-[a-z]+\.min\.(css|js)"|src="\.\./\.\./clanker-ui-[a-z]+\.min\.js"', l)]
    out = "\n".join(lines)
    assert "</head>" in out
    return out.replace("</head>", FULL_HEAD + "</head>", 1)


def full_kit(t):
    def page(route):
        response = route.fetch()
        body = response.text()
        if route.request.url.endswith(".js"):
            body = body.replace("../../clanker-ui-chart.min.js", "../../clanker-ui-chart.js")
            body = re.sub(r"\.\./\.\./clanker-ui-[a-z]+\.min\.js", "../../clanker-ui.js", body)
        else:
            body = to_full(body)
        headers = {k: v for k, v in response.headers.items() if k.lower() not in ("content-encoding", "content-length", "etag")}
        route.fulfill(status=response.status, headers=headers, body=body)

    t.page.route(re.compile(r".*/test/split/[a-z0-9-]+\.(html|js)$"), page)


def normalize(snapshot):
    out = []
    for tag, attrs, styles in snapshot:
        norm = []
        for name, value in attrs:
            if name in ID_ATTRS or name.startswith("aria-") and re.search(r"\d", value) and name not in ("aria-valuenow", "aria-valuemin", "aria-valuemax", "aria-valuetext", "aria-label", "aria-setsize", "aria-posinset", "aria-level", "aria-colcount", "aria-rowcount", "aria-colindex", "aria-rowindex"):
                value = re.sub(r"\d+", "N", value)
            norm.append((name, value))
        out.append((tag, sorted(norm), styles))
    return out


def load(t, group):
    response = t.page.goto(f"{t.base_url}/test/split/{group}.html", wait_until="load")
    assert response is not None and response.status == 200, f"{group}.html returned {response and response.status}"
    t.page.wait_for_function("() => document.readyState === 'complete'")
    t.page.mouse.move(0, 0)
    t.page.evaluate(SETTLE)
    t.page.evaluate(SETTLE)


def compare(t, group, interact=None):
    load(t, group)
    split = normalize(t.page.evaluate(SNAPSHOT, [PROPS, "overlays" in group]))
    split_result = interact(t) if interact else None
    full_kit(t)
    load(t, group)
    full = normalize(t.page.evaluate(SNAPSHOT, [PROPS, "overlays" in group]))
    full_result = interact(t) if interact else None
    assert len(split) == len(full), f"{group}: {len(split)} elements with the split files, {len(full)} with the full files"
    diffs = []
    for i, (a, b) in enumerate(zip(split, full)):
        if a[0] != b[0] or a[1] != b[1]:
            diffs.append(f"element {i} <{b[0]}>: attributes {a[1]} != {b[1]}")
            continue
        for p, x, y in zip(PROPS, a[2], b[2]):
            if x != y:
                diffs.append(f"element {i} <{b[0]} {dict(b[1]).get('data-slot', '')}>: {p} {x!r} != {y!r}")
    assert not diffs, f"{group}: {len(diffs)} differences between the split and the full files:\n" + "\n".join(diffs[:20])
    assert split_result == full_result, f"{group}: interaction {split_result} with the split files, {full_result} with the full files"
    return split_result


def select_option(t):
    trigger = t.page.locator('[data-slot="select-trigger"]').first
    before = trigger.inner_text()
    trigger.click()
    t.page.wait_for_function("() => document.querySelector('[data-slot=select-content]')?.hasAttribute('data-open')")
    t.page.locator('[data-slot="select-content"][data-open] [data-slot="select-item"]').nth(1).click()
    t.page.wait_for_function("() => !document.querySelector('[data-slot=select-content][data-open]')")
    return before, trigger.inner_text()


def dialog_escape(t):
    trigger = t.page.locator("[data-alert-dialog-trigger]").first
    trigger.click()
    t.page.wait_for_function("() => document.querySelector('[data-slot=alert-dialog-content]')?.matches('[open]')")
    t.page.keyboard.press("Escape")
    t.page.wait_for_function("() => !document.querySelector('[data-slot=alert-dialog-content][open]')")
    return trigger.evaluate("e => e === document.activeElement")


def tabs_arrow(t):
    selected = t.page.locator('[data-slot="tabs-trigger"][aria-selected="true"]').first
    value = selected.get_attribute("data-value")
    selected.focus()
    t.page.keyboard.press("ArrowRight")
    t.page.keyboard.press("Enter")
    t.page.evaluate(SETTLE)
    return value, t.page.evaluate("() => document.activeElement.getAttribute('data-value')"), t.page.evaluate("() => document.activeElement.getAttribute('aria-selected')")


def calendar_next(t):
    button = t.page.locator('[data-slot="calendar-button-next"]').first
    root = t.page.locator('[data-slot="calendar"]', has=button).first
    before = root.locator('[data-slot="calendar-month-caption"]').first.inner_text()
    button.click()
    t.page.evaluate(SETTLE)
    return before, root.locator('[data-slot="calendar-month-caption"]').first.inner_text()


def chart_drawn(t):
    return t.page.evaluate("""() => [
      document.querySelector('[data-slot=chart]')?.getAttribute('data-type'),
      document.querySelector('[data-slot=chart] svg[role=application]') !== null,
      document.querySelectorAll('[data-slot=chart] rect').length > 0,
      document.querySelector('[data-slot=chart-stat]')?.getAttribute('role'),
    ]""")


def check_core(t):
    compare(t, "core")
    assert t.page.evaluate("() => document.querySelector('main [data-slot=button]').type") == "button"


def payment_radius(t):
    return t.page.evaluate("""() => {
      const s = getComputedStyle(document.querySelector('#split-payment [data-slot=select-trigger]'))
      return [s.borderTopLeftRadius, s.borderTopRightRadius, s.borderBottomRightRadius, s.borderBottomLeftRadius]
    }""")


def check_forms(t):
    before, after = compare(t, "forms", select_option)
    assert before != after, f"the select keeps {before!r} after a choice"
    load(t, "forms")
    tl, tr, br, bl = payment_radius(t)
    assert tl != "0px" and bl != "0px" and tr == "0px" and br == "0px", f"a select at the start of a button group with core and forms only: radii {[tl, tr, br, bl]}"


def check_forms_needs(t):
    compare(t, "forms-needs")


def toasts(t):
    t.page.wait_for_function("() => document.querySelectorAll('[data-slot=toast]').length === 2")
    t.page.evaluate(SETTLE)
    return t.page.evaluate("() => [...document.querySelectorAll('[data-slot=toast-title]')].map(e => e.textContent)")


def check_overlays_needs(t):
    titles = compare(t, "overlays-needs", toasts)
    assert sorted(titles) == ["Event created", "Saved"], titles


def check_layout_needs(t):
    if t.engine == "webkit" and t.width == 390:
        t.skip("https://github.com/bl4ko/clanker-ui/issues/2")
    compare(t, "layout-needs")
    assert t.page.locator('[data-slot="sidebar"]').count() > 0


def check_chat_needs(t):
    compare(t, "chat-needs")
    assert t.page.locator('[data-slot="date-picker"]').count() > 0 and t.page.locator('[data-slot="questionnaire"]').count() > 0


def check_overlays(t):
    assert compare(t, "overlays", dialog_escape), "focus does not go back to the alert dialog trigger after Escape"


def check_layout(t):
    before, after, selected = compare(t, "layout", tabs_arrow)
    assert after != before and selected == "true", f"ArrowRight and Enter on tab {before!r} give {after!r} (aria-selected {selected})"


def check_chat(t):
    before, after = compare(t, "chat", calendar_next)
    assert before != after, f"the calendar keeps {before!r} after the next month button"


def check_chart(t):
    assert compare(t, "chart", chart_drawn) == ["bar", True, True, "group"]


PAGES = {"core": [], "forms": [], "overlays": [], "layout": [], "chat": [], "chart": [], "forms-needs": ["overlays"], "overlays-needs": ["forms"], "layout-needs": ["overlays"], "chat-needs": ["forms", "overlays", "layout"]}


def check_fixtures_load_only_their_group(t):
    for page, needs in PAGES.items():
        load(t, page)
        files = t.page.evaluate("() => performance.getEntriesByType('resource').map(r => new URL(r.name).pathname).filter(p => p.startsWith('/clanker-ui'))")
        allowed = "|".join(["core", page.removesuffix("-needs")] + needs)
        assert files and all(re.fullmatch(rf"/clanker-ui-({allowed})\.min\.(css|js)", f) for f in files), f"{page}.html loads files of other groups: {files}"


def check_double_load_stops(t):
    errors = []
    t.page.on("pageerror", lambda e: errors.append(str(e)))
    t.expect_console("the kit is loaded twice")
    load(t, "twice")
    t.page.wait_for_function("() => document.querySelector('#twice-switch').getAttribute('role') === 'switch'")
    assert any("the kit is loaded twice" in e for e in errors), f"a second core must stop with an error: {errors}"
    t.page.click("#twice-switch")
    t.page.evaluate(SETTLE)
    assert t.page.get_attribute("#twice-switch", "aria-checked") == "true", "one click must toggle the switch one time (one core)"
