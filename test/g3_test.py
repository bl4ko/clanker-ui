import re

START = "/demo?only=layout"


def g3_listen(page, selector, names):
    page.evaluate(
        """([selector, names]) => {
          window.__g3 = window.__g3 || []
          for (const el of document.querySelectorAll(selector)) for (const name of names) el.addEventListener(name, e => window.__g3.push([name, e.detail ?? null]))
        }""",
        [selector, names],
    )


def g3_events(page, clear=True):
    out = page.evaluate("() => { const e = window.__g3 || []; return e }")
    if clear:
        page.evaluate("() => { window.__g3 = [] }")
    return out


def g3_rect(locator):
    return locator.evaluate("e => { const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, r: r.right, b: r.bottom } }")


def g3_inline(t, locator):
    r = g3_rect(locator)
    return {**r, "x": -r["r"], "r": -r["x"]} if t.rtl else r


def g3_key(t, key):
    return {"ArrowLeft": "ArrowRight", "ArrowRight": "ArrowLeft"}.get(key, key) if t.rtl else key


def g3_style(locator, prop):
    return locator.evaluate("(e, p) => getComputedStyle(e).getPropertyValue(p)", prop)


def g3_keyboard(page):
    page.keyboard.press("Shift")


def g3_focused(page):
    return page.evaluate("() => { const a = document.activeElement; return a ? (a.id || a.textContent.trim()) : null }")


CLOSE = """([trigger, content]) => {
  const el = document.querySelector(content)
  const height = () => (el.checkVisibility() ? el.getBoundingClientRect().height : 0)
  const start = height()
  document.querySelector(trigger).click()
  const animation = el.getAnimations().find(a => a.animationName)
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


def g3_close_motion(t, trigger, content, motion=True):
    page = t.page
    page.locator(trigger).scroll_into_view_if_needed()
    start, first, middle = page.evaluate(CLOSE, [trigger, content])
    assert start > 0
    if t.reduced_motion or not motion:
        assert first is None
    else:
        assert abs(first - start) <= 1 and 0.1 * start < middle < 0.9 * start, (start, first, middle)
    page.wait_for_function("sel => { const e = document.querySelector(sel); return !e.checkVisibility() || e.getBoundingClientRect().height === 0 }", arg=content)


G3_STATUS = """async slot => {
  const { h } = await import("/clanker-ui.js")
  const probe = value => { const p = h("span"); p.style.color = value; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c }
  const root = getComputedStyle(document.documentElement)
  const host = h("div")
  document.getElementById(slot).append(host)
  const items = []
  for (const variant of ["success", "warning", "info"]) {
    const el = slot === "alert"
      ? h("div", { "data-slot": "alert", "data-variant": variant, role: "alert" }, h("div", { "data-slot": "alert-title" }, "Title"), h("div", { "data-slot": "alert-description" }, "Text"))
      : h("span", { "data-slot": "badge", "data-variant": variant }, "Badge")
    host.append(el)
    const s = getComputedStyle(el)
    const title = el.querySelector('[data-slot="alert-title"]') ?? el
    const description = el.querySelector('[data-slot="alert-description"]')
    items.push({
      variant,
      defined: ["bg", "border", "text"].every(part => root.getPropertyValue(`--${variant}-${part}`).trim() !== ""),
      text: getComputedStyle(title).color,
      description: description ? getComputedStyle(description).color : null,
      background: s.backgroundColor,
      border: s.borderTopColor,
      borderWidth: s.borderTopWidth,
      tokens: { text: probe(`var(--${variant}-text)`), bg: probe(`var(--${variant}-bg)`), border: probe(`var(--${variant}-border)`) },
    })
  }
  host.remove()
  return { items, page: probe("var(--background)"), card: probe("var(--card)"), foreground: probe("var(--foreground)") }
}"""


def g3_status_colors(t, slot):
    page = t.page
    t.a11y()
    found = page.evaluate(G3_STATUS, slot)
    for item in found["items"]:
        v = item["variant"]
        assert item["defined"], (v, "status tokens are not on :root")
        assert (item["text"], item["background"], item["border"]) == (item["tokens"]["text"], item["tokens"]["bg"], item["tokens"]["border"]), item
        assert item["borderWidth"] == "1px", item
        text = page.evaluate(G3_CONTRAST, [item["text"], item["background"]])
        assert text >= 4.5, (slot, v, "text on background", text)
        edge = page.evaluate(G3_CONTRAST, [item["border"], found["page"]])
        assert edge >= 3, (slot, v, "border on page background", edge)
        if t.theme == "dark":
            card = page.evaluate(G3_CONTRAST, [item["border"], found["card"]])
            assert card >= 3, (slot, v, "border on card", card)
        if slot == "alert":
            assert item["description"] == found["foreground"], item
            assert page.evaluate(G3_CONTRAST, [item["description"], item["background"]]) >= 4.5, item


def check_accordion(t):
    page = t.page
    t.section("accordion")
    demo = page.locator("#accordion-demo")
    items = demo.locator('[data-slot="accordion-item"]')
    triggers = demo.locator('[data-slot="accordion-trigger"]')
    panels = demo.locator('[data-slot="accordion-content"]')
    assert items.count() == 3
    assert [items.nth(i).get_attribute("data-state") for i in range(3)] == ["open", "closed", "closed"]
    assert items.nth(0).get_attribute("data-open") == "" and items.nth(1).get_attribute("data-open") is None
    assert [panels.nth(i).get_attribute("hidden") for i in range(3)] == [None, "until-found", "until-found"]
    assert [triggers.nth(i).get_attribute("aria-expanded") for i in range(3)] == ["true", "false", "false"]
    assert triggers.nth(0).evaluate("e => e.parentElement.localName") == "h3"
    icons = triggers.nth(0).locator('[data-slot="accordion-trigger-icon"]')
    assert icons.count() == 2 and [icons.nth(i).get_attribute("data-lucide") for i in range(2)] == ["chevron-down", "chevron-up"]
    assert [icons.nth(i).is_visible() for i in range(2)] == [False, True]
    assert [triggers.nth(1).locator("svg").nth(i).is_visible() for i in range(2)] == [True, False]
    content = panels.nth(0)
    assert content.get_attribute("role") == "region"
    assert content.get_attribute("aria-labelledby") == triggers.nth(0).get_attribute("id")
    assert triggers.nth(0).get_attribute("aria-controls") == content.get_attribute("id")
    assert content.locator(":scope > div").count() == 1
    g3_listen(page, "#accordion-demo", ["accordion:change"])
    started = triggers.nth(1).evaluate("e => { e.click(); return e.closest('[data-slot=accordion-item]').querySelector('[data-slot=accordion-content]').getAnimations().map(a => a.animationName) }")
    assert started == ([] if t.reduced_motion else ["accordion-down"]), started
    page.wait_for_function("() => document.querySelector('#accordion-demo [data-slot=accordion-content]').getAttribute('hidden') === 'until-found'")
    assert [items.nth(i).get_attribute("data-state") for i in range(3)] == ["closed", "open", "closed"]
    assert g3_events(page) == [["accordion:change", {"value": "returns"}]]
    t.settle()
    assert panels.nth(1).evaluate("e => e.style.getPropertyValue('--accordion-panel-height')") == "auto"
    triggers.nth(1).click()
    page.wait_for_function("() => document.querySelectorAll('#accordion-demo [data-slot=accordion-content]')[1].getAttribute('hidden') === 'until-found'")
    assert g3_events(page) == [["accordion:change", {"value": ""}]]
    g3_keyboard(page)
    page.evaluate("() => document.activeElement.blur()")
    triggers.nth(1).focus()
    page.keyboard.press("Shift+Tab")
    assert triggers.nth(0).evaluate("e => e === document.activeElement && e.matches(':focus-visible')")
    for key in ["ArrowDown", "ArrowUp", "End", "Home"]:
        page.keyboard.press(key)
        assert page.evaluate("document.activeElement === document.querySelectorAll('#accordion-demo [data-slot=accordion-trigger]')[0]"), f"{key} keeps focus on the trigger, as in Base UI"
    page.keyboard.press("Enter")
    assert items.nth(0).get_attribute("data-state") == "open"
    page.keyboard.press("Space")
    assert items.nth(0).get_attribute("data-state") == "closed"
    page.wait_for_function("() => document.querySelector('#accordion-demo [data-slot=accordion-content]').getAttribute('hidden') === 'until-found'")
    assert g3_events(page) == [["accordion:change", {"value": "shipping"}], ["accordion:change", {"value": ""}]]
    found = panels.nth(2).evaluate("e => { e.removeAttribute('hidden'); e.dispatchEvent(new Event('beforematch', { bubbles: true })); return e.closest('[data-slot=accordion-item]').dataset.state }")
    assert found == "open" and panels.nth(2).get_attribute("hidden") is None and triggers.nth(2).get_attribute("aria-expanded") == "true"
    assert g3_events(page) == [["accordion:change", {"value": "support"}]]
    multi = page.locator("#accordion-multiple")
    g3_listen(page, "#accordion-multiple", ["accordion:change"])
    multi.locator('[data-slot="accordion-trigger"]').nth(1).click()
    assert [multi.locator('[data-slot="accordion-item"]').nth(i).get_attribute("data-state") for i in range(3)] == ["open", "open", "closed"]
    assert g3_events(page) == [["accordion:change", {"value": ["notifications", "privacy"]}]]
    multi.locator('[data-slot="accordion-content"]').nth(2).evaluate("e => { e.removeAttribute('hidden'); e.dispatchEvent(new Event('beforematch', { bubbles: true })) }")
    page.wait_for_function("() => document.querySelectorAll('#accordion-multiple [data-slot=accordion-item]')[2].dataset.state === 'open'")
    assert g3_events(page) == [["accordion:change", {"value": ["notifications", "privacy", "billing"]}]]
    fixed = page.locator("#accordion-disabled")
    g3_listen(page, "#accordion-disabled", ["accordion:change"])
    fixed_triggers = fixed.locator('[data-slot="accordion-trigger"]')
    fixed_triggers.nth(0).click()
    assert [fixed.locator('[data-slot="accordion-item"]').nth(i).get_attribute("data-state") for i in range(3)] == ["closed"] * 3
    assert g3_events(page) == [["accordion:change", {"value": ""}]]
    disabled = fixed_triggers.nth(1)
    assert disabled.get_attribute("aria-disabled") == "true" and disabled.get_attribute("tabindex") == "0"
    disabled.dispatch_event("click")
    assert fixed.locator('[data-slot="accordion-item"]').nth(1).get_attribute("data-state") == "closed"
    assert fixed.locator('[data-slot="accordion-content"]').nth(1).get_attribute("hidden") == "until-found"
    assert g3_events(page) == []
    fixed_triggers.nth(0).focus()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement === document.querySelectorAll('#accordion-disabled [data-slot=accordion-trigger]')[1]"), "like Base UI, a disabled trigger stays in the Tab order"
    page.keyboard.press("Enter")
    page.wait_for_timeout(100)
    assert fixed.locator('[data-slot="accordion-item"]').nth(1).get_attribute("data-state") == "closed" and g3_events(page) == []
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement === document.querySelectorAll('#accordion-disabled [data-slot=accordion-trigger]')[2]")
    page.keyboard.press("Enter")
    page.wait_for_function("() => document.querySelectorAll('#accordion-disabled [data-slot=accordion-item]')[2].dataset.state === 'open'")
    assert g3_events(page) == [["accordion:change", {"value": "email"}]]
    t.settle()
    t.shot("accordion", page.locator("#accordion"))


REOPEN = """async sel => {
  const trigger = document.querySelector(sel)
  const wait = ms => new Promise(r => setTimeout(r, ms))
  for (let i = 0; i < 4; i++) {
    trigger.click()
    await wait(60)
  }
}"""


def check_accordion_reopen_height(t):
    page = t.page
    t.section("accordion")
    trigger = '#accordion-demo [data-value="returns"] [data-slot="accordion-trigger"]'
    panel = '#accordion-demo [data-value="returns"] > [data-slot="accordion-content"]'
    page.locator(trigger).click()
    t.settle()
    full = page.evaluate("sel => document.querySelector(sel).getBoundingClientRect().height", panel)
    page.locator(trigger).click()
    page.wait_for_function("sel => document.querySelector(sel).getAttribute('hidden') === 'until-found'", arg=panel)
    page.evaluate(REOPEN, trigger)
    page.wait_for_function("sel => document.querySelector(sel).getAttribute('hidden') === 'until-found'", arg=panel)
    t.settle()
    frames = t.paint("sel => document.querySelector(sel).getBoundingClientRect().height", lambda: page.evaluate("sel => document.querySelector(sel).click()", trigger), panel, ms=700)
    t.settle()
    final = page.evaluate("sel => document.querySelector(sel).getBoundingClientRect().height", panel)
    assert abs(final - full) < 0.5, (final, full)
    assert max(frames) <= full + 0.5, frames
    below = [f for f in frames if f < full - 0.5]
    if not t.reduced_motion and below:
        step = below[-1] - below[-2] if len(below) > 1 else 0
        assert full - below[-1] <= max(4, step), ("the open animation ends with a jump", frames)
    assert page.evaluate("sel => document.querySelector(sel).style.getPropertyValue('--accordion-panel-height')", panel) == "auto"


def check_accordion_close_motion(t):
    t.section("accordion")
    g3_close_motion(t, '#accordion-demo [data-value="shipping"] [data-slot="accordion-trigger"]', '#accordion-demo [data-value="shipping"] > [data-slot="accordion-content"]')


def check_alert(t):
    page = t.page
    section = t.section("alert")
    alerts = section.locator('[data-slot="alert"]')
    assert alerts.count() == 9
    first = alerts.nth(0)
    assert first.get_attribute("role") == "alert"
    icon, title = g3_inline(t, first.locator("svg")), g3_inline(t, first.locator('[data-slot="alert-title"]'))
    box = g3_inline(t, first)
    assert abs(icon["x"] - box["x"] - 11) < 1.5, (icon, box)
    assert abs(title["x"] - icon["r"] - 8) < 1.5, (title, icon)
    assert g3_style(first, "border-top-width") == "1px"
    destructive = section.locator('[data-slot="alert"][data-variant="destructive"]')
    color = page.evaluate("() => { const p = document.createElement('p'); p.style.color = 'var(--destructive)'; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c }")
    assert g3_style(destructive, "color") == color
    plain = alerts.nth(5)
    assert abs(g3_inline(t, plain.locator('[data-slot="alert-title"]'))["x"] - g3_inline(t, plain)["x"] - 11) < 1.5
    action = section.locator('[data-slot="alert-action"]')
    host = g3_inline(t, alerts.nth(3))
    spot = g3_inline(t, action)
    assert abs(host["r"] - spot["r"] - 9) < 1.5 and abs(spot["y"] - host["y"] - 9) < 1.5, (host, spot)


def check_alert_status(t):
    section = t.section("alert")
    g3_status_colors(t, "alert")
    shown = section.locator("#alert-status [data-slot=alert]")
    assert [shown.nth(i).get_attribute("data-variant") for i in range(shown.count())] == ["success", "warning", "info"]
    t.shot("alert-status", section.locator("#alert-status"))


def check_aspect_ratio(t):
    page = t.page
    t.section("aspect-ratio")
    ratios = page.evaluate(
        """() => [...document.querySelectorAll('#aspect-ratio [data-slot=aspect-ratio]')].map(e => { const r = e.getBoundingClientRect(); return [e.dataset.ratio, r.width / r.height, getComputedStyle(e.firstElementChild).position] })"""
    )
    want = {"16/9": 16 / 9, "1/1": 1, "9/16": 9 / 16, "2.4": 2.4}
    assert len(ratios) == 4
    for ratio, value, pos in ratios:
        assert abs(value - want[ratio]) < 0.02, (ratio, value)
        assert pos == "absolute"
    img = page.locator("#aspect-ratio-wide img")
    assert abs(g3_rect(img)["h"] - g3_rect(page.locator("#aspect-ratio-wide [data-slot=aspect-ratio]"))["h"]) < 1


def check_avatar(t):
    page = t.page
    section = t.section("avatar")
    page.wait_for_function("() => [...document.querySelectorAll('#avatar [data-slot=avatar-image]')].every(i => i.dataset.status === 'loaded' || i.dataset.status === 'error')")
    first = section.locator('[data-slot="avatar"]').first
    assert first.locator("img").get_attribute("data-status") == "loaded"
    assert g3_style(first.locator("img"), "visibility") == "visible"
    assert g3_style(first.locator('[data-slot="avatar-fallback"]'), "visibility") == "hidden"
    broken = page.locator("#avatar-broken")
    assert broken.locator("img").get_attribute("data-status") == "error"
    assert g3_style(broken.locator("img"), "visibility") == "hidden"
    assert broken.locator('[data-slot="avatar-fallback"]').is_visible()
    assert broken.locator('[data-slot="avatar-fallback"]').inner_text() == "ER"
    size = lambda loc: round(g3_rect(loc)["w"])
    sizes = section.locator('[data-demo="preview"]').nth(4).locator('[data-slot="avatar"]')
    assert [size(sizes.nth(i)) for i in range(3)] == [24, 32, 40]
    badge, host = g3_inline(t, page.locator("#avatar-online")), g3_inline(t, page.locator("#avatar-online").locator(".."))
    assert abs(badge["r"] - host["r"]) < 1 and abs(badge["b"] - host["b"]) < 1 and round(badge["w"]) == 10
    group = section.locator('[data-slot="avatar-group"]').first.locator('[data-slot="avatar"]')
    a, b = g3_inline(t, group.nth(0)), g3_inline(t, group.nth(1))
    assert abs((a["r"] - b["x"]) - 8) < 1, (a, b)
    assert "0px 0px 0px 2px" in g3_style(group.nth(0), "box-shadow")
    g3_listen(page, "#avatar", ["avatar:change"])
    page.evaluate(
        """async () => {
          const { h } = await import('/clanker-ui.js')
          const holder = document.querySelector('#avatar [data-demo=preview]')
          holder.append(h('span', { 'data-slot': 'avatar', id: 'avatar-late' }, h('img', { 'data-slot': 'avatar-image', alt: '', src: 'data:image/png;base64,AAAA' }), h('span', { 'data-slot': 'avatar-fallback' }, 'NA')))
          holder.append(h('span', { 'data-slot': 'avatar', id: 'avatar-late-ok' }, h('img', { 'data-slot': 'avatar-image', alt: '', src: 'demo/assets/g3-avatar-4.svg?late' }), h('span', { 'data-slot': 'avatar-fallback' }, 'OK')))
        }"""
    )
    page.wait_for_function("() => window.__g3.length >= 2")
    events = sorted(e[1]["value"] for e in g3_events(page))
    assert events == ["error", "loaded"], events
    t.shot("avatar", section)
    trigger = page.locator("#avatar-dropdown [data-dropdown-menu-trigger]")
    assert g3_style(trigger, "border-top-left-radius") == "9999px" and round(g3_rect(trigger)["w"]) == 32
    trigger.click()
    menu = page.locator("#avatar-dropdown [data-slot=dropdown-menu-content]")
    menu.wait_for(state="visible")
    assert [i.inner_text() for i in menu.get_by_role("menuitem").all()] == ["Profile", "Billing", "Settings", "Log out"]
    g3_keyboard(page)
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Escape")
    menu.wait_for(state="hidden")
    assert trigger.evaluate("e => document.activeElement === e")


def check_badge(t):
    page = t.page
    section = t.section("badge")
    badges = section.locator('[data-slot="badge"]')
    first = badges.first
    assert round(g3_rect(first)["h"]) == 20
    assert g3_style(first, "border-radius") != "0px"
    variants = page.evaluate(
        """() => [...document.querySelectorAll('#badge [data-demo=preview]:first-of-type [data-slot=badge]')].map(b => [b.dataset.variant || 'default', getComputedStyle(b).backgroundColor, getComputedStyle(b).borderColor])"""
    )
    assert [v[0] for v in variants] == ["default", "secondary", "destructive", "outline", "ghost", "link"]
    assert len({v[1] for v in variants[:3]}) == 3
    assert variants[3][1] == "rgba(0, 0, 0, 0)" and variants[3][2] != "rgba(0, 0, 0, 0)"
    assert variants[4][1] == "rgba(0, 0, 0, 0)"
    icon = badges.nth(6).locator("svg")
    assert round(g3_rect(icon)["w"]) == 12
    spinner = section.locator('[data-slot="spinner"]').first
    assert spinner.get_attribute("aria-hidden") == "true" and spinner.get_attribute("role") == "none"
    assert g3_style(spinner, "width") == "12px"
    link = section.locator('a[data-slot="badge"]').first
    assert link.get_attribute("href") == "#badge"
    g3_keyboard(page)
    link.focus()
    t.settle()
    assert "0px 0px 0px 3px" in g3_style(link, "box-shadow")
    t.a11y()
    assert g3_style(link, "outline-style") == "solid"


def check_badge_status(t):
    page = t.page
    section = t.section("badge")
    g3_status_colors(t, "badge")
    shown = page.locator("#badge-status [data-slot=badge]")
    assert [shown.nth(i).get_attribute("data-variant") for i in range(shown.count())] == ["success", "warning", "info", "success"]
    link = page.locator("#badge-status a[data-slot=badge]")
    before = g3_style(link, "background-color")
    link.hover()
    assert g3_style(link, "background-color") == before
    assert "underline" in g3_style(link, "text-decoration-line")
    page.mouse.move(0, 0)
    t.shot("badge-status", page.locator("#badge-status"))


def check_breadcrumb(t):
    page = t.page
    section = t.section("breadcrumb")
    nav = page.locator("#breadcrumb-basic")
    assert nav.get_attribute("aria-label") == "breadcrumb"
    seps = nav.locator('[data-slot="breadcrumb-separator"]')
    assert seps.count() == 3
    for i in range(3):
        assert seps.nth(i).get_attribute("role") == "presentation"
        assert seps.nth(i).get_attribute("aria-hidden") == "true"
        assert seps.nth(i).locator("svg path").count() == 1
    assert round(g3_rect(seps.nth(0).locator("svg"))["w"]) == 14
    ellipsis = nav.locator('[data-slot="breadcrumb-ellipsis"]')
    assert ellipsis.locator(".sr-only").inner_text() == "More"
    menu_trigger = nav.locator("[data-dropdown-menu-trigger]")
    assert round(g3_rect(menu_trigger)["w"]) == 28 and menu_trigger.get_attribute("aria-haspopup") == "menu"
    menu_trigger.click()
    menu = page.get_by_role("menu").filter(has_text="Documentation").first
    menu.wait_for(state="visible")
    assert menu.get_by_role("menuitem").count() == 3
    t.settle()
    t.shot("breadcrumb-menu", page)
    page.keyboard.press("Escape")
    menu.wait_for(state="hidden")
    assert menu_trigger.evaluate("e => document.activeElement === e")
    dropdown = page.locator("#breadcrumb-dropdown [data-dropdown-menu-trigger]")
    dropdown.click()
    page.locator("#breadcrumb-dropdown [data-slot=dropdown-menu-content]").wait_for(state="visible")
    page.keyboard.press("Escape")
    page.locator("#breadcrumb-dropdown [data-slot=dropdown-menu-content]").wait_for(state="hidden")
    current = nav.locator('[data-slot="breadcrumb-page"]')
    assert current.get_attribute("aria-current") == "page" and current.get_attribute("role") == "link" and current.get_attribute("aria-disabled") == "true"
    link = nav.locator('[data-slot="breadcrumb-link"]').first
    before = g3_style(link, "color")
    link.hover()
    page.wait_for_timeout(250)
    assert g3_style(link, "color") != before
    xs = [g3_inline(t, nav.locator('[data-slot="breadcrumb-item"]').nth(i))["x"] for i in range(4)]
    assert xs == sorted(xs)
    slash = section.locator('nav[aria-label="Breadcrumb with slashes"] [data-slot="breadcrumb-separator"]').first
    assert slash.inner_text() == "/" and slash.locator("svg").count() == 0


def check_card(t):
    page = t.page
    section = t.section("card")
    card = page.locator("#card-demo")
    box = g3_inline(t, card)
    assert g3_style(card, "padding-top") == "16px" and g3_style(card, "border-top-width") == "0px" and "0px 0px 0px 1px" in g3_style(card, "box-shadow")
    title = g3_inline(t, card.locator('[data-slot="card-title"]'))
    action = g3_inline(t, card.locator('[data-slot="card-action"]'))
    assert abs(title["x"] - box["x"] - 16) < 1.5
    assert abs(box["r"] - action["r"] - 16) < 1.5 and action["x"] > title["r"] - 1
    assert abs(action["y"] - title["y"]) < 1.5
    small = page.locator("#card-small")
    assert g3_style(small, "padding-top") == "12px"
    assert abs(g3_inline(t, small.locator('[data-slot="card-title"]'))["x"] - g3_inline(t, small)["x"] - 12) < 1.5
    image = page.locator("#card-image")
    assert g3_style(image, "padding-top") == "0px"
    assert abs(g3_rect(image.locator("img"))["y"] - g3_rect(image)["y"]) < 1.5
    footer = page.locator("#card-small-footer")
    buttons = footer.locator('[data-slot="button"]')
    assert abs(g3_inline(t, buttons.nth(1))["r"] - g3_inline(t, footer)["r"] + 12) < 1.5
    t.shot("card", section)


def g3_carousel_wait(page, selector, index):
    page.wait_for_function(
        """([sel, index]) => {
          const root = document.querySelector(sel)
          const viewport = root.querySelector('[data-slot=carousel-content]')
          const item = root.querySelectorAll('[data-slot=carousel-item]')[index]
          const v = viewport.getBoundingClientRect(), r = item.getBoundingClientRect(), cs = getComputedStyle(item)
          if (root.dataset.orientation === 'vertical') return Math.abs(r.top + parseFloat(cs.paddingTop) - v.top) < 2
          return getComputedStyle(viewport).direction === 'rtl' ? Math.abs(v.right - (r.right - parseFloat(cs.paddingRight))) < 2 : Math.abs(r.left + parseFloat(cs.paddingLeft) - v.left) < 2
        }""",
        arg=[selector, index],
        timeout=10000,
    )


def check_carousel(t):
    page = t.page
    section = t.section("carousel")
    root = page.locator("#carousel-demo")
    assert root.get_attribute("role") == "region" and root.get_attribute("aria-roledescription") == "carousel"
    slides = root.locator('[data-slot="carousel-item"]')
    assert slides.count() == 5
    assert slides.nth(1).get_attribute("role") == "group" and slides.nth(1).get_attribute("aria-roledescription") == "slide" and slides.nth(1).get_attribute("aria-label") == "2 of 5"
    prev, nxt = root.locator('[data-slot="carousel-previous"]'), root.locator('[data-slot="carousel-next"]')
    assert prev.locator(".sr-only").inner_text() == "Previous slide" and nxt.locator(".sr-only").inner_text() == "Next slide"
    assert prev.is_disabled() and nxt.is_enabled()
    assert round(g3_rect(nxt)["w"]) == 28
    assert abs(g3_inline(t, root)["x"] - g3_inline(t, prev)["r"] - 20) < 1.5
    g3_listen(page, "#carousel-demo", ["carousel:change"])
    nxt.click()
    g3_carousel_wait(page, "#carousel-demo", 1)
    page.wait_for_function("() => window.__g3.length >= 1")
    assert g3_events(page) == [["carousel:change", {"value": 1, "count": 5}]]
    assert page.locator("#carousel-count").inner_text() == "Slide 2 of 5"
    assert prev.is_enabled()
    g3_keyboard(page)
    nxt.focus()
    page.keyboard.press(g3_key(t, "ArrowRight"))
    g3_carousel_wait(page, "#carousel-demo", 2)
    page.wait_for_function("() => window.__g3.length >= 1")
    page.keyboard.press(g3_key(t, "ArrowLeft"))
    g3_carousel_wait(page, "#carousel-demo", 1)
    page.wait_for_function("() => window.__g3.length >= 2")
    assert [e[1]["value"] for e in g3_events(page)] == [2, 1]
    for _ in range(4):
        page.keyboard.press(g3_key(t, "ArrowRight"))
        page.wait_for_timeout(80)
    g3_carousel_wait(page, "#carousel-demo", 4)
    page.wait_for_function("() => document.querySelector('#carousel-demo [data-slot=carousel-next]').disabled")
    t.settle()
    t.shot("carousel-end", section.locator('[data-demo~="preview"]').first)
    for _ in range(4):
        prev.click()
        page.wait_for_timeout(80)
    page.wait_for_function("() => document.querySelector('#carousel-demo [data-slot=carousel-previous]').disabled")
    page.wait_for_function("() => document.getElementById('carousel-count').textContent === 'Slide 1 of 5'")
    sizes = page.locator("#carousel-sizes")
    widths = sizes.locator('[data-slot="carousel-item"]').evaluate_all("els => els.map(e => e.getBoundingClientRect().width)")
    view = g3_rect(sizes.locator('[data-slot="carousel-content"]'))["w"]
    assert abs(sum(widths[:3]) - view - 4) < 2, (widths, view)
    vertical = page.locator("#carousel-vertical")
    assert vertical.get_attribute("data-orientation") == "vertical"
    vprev, vnext = vertical.locator('[data-slot="carousel-previous"]'), vertical.locator('[data-slot="carousel-next"]')
    assert g3_rect(vprev)["b"] < g3_rect(vertical)["y"] and g3_rect(vnext)["y"] > g3_rect(vertical)["b"]
    g3_listen(page, "#carousel-vertical", ["carousel:change"])
    vnext.focus()
    page.keyboard.press("ArrowDown")
    g3_carousel_wait(page, "#carousel-vertical", 1)
    page.wait_for_function("() => window.__g3.some(e => e[0] === 'carousel:change')")
    assert vertical.locator('[data-slot="carousel-content"] > div').evaluate("e => new DOMMatrix(getComputedStyle(e).transform).m42") < -10


def check_carousel_motion(t):
    if t.reduced_motion:
        t.skip("reduced motion moves the slide at once")
    page = t.page
    t.section("carousel")
    end = page.evaluate("""() => new Promise(resolve => {
      const root = document.getElementById('carousel-demo')
      const item = root.querySelector('[data-slot=carousel-item]')
      const start = performance.now()
      let last = item.getBoundingClientRect().left, end = 0
      root.querySelector('[data-slot=carousel-next]').click()
      const tick = now => {
        const at = item.getBoundingClientRect().left
        if (Math.abs(at - last) > 0.25) end = now - start
        last = at
        if (now - start < 1500) requestAnimationFrame(tick)
        else resolve(Math.round(end))
      }
      requestAnimationFrame(tick)
    })""")
    assert 600 <= end <= 900, f"the slide moves for {end} ms; Embla in shadcn moves for about 750 ms"


def check_carousel_disabled_focus(t):
    page = t.page
    t.section("carousel")
    root = page.locator("#carousel-demo")
    prev, nxt = root.locator('[data-slot="carousel-previous"]'), root.locator('[data-slot="carousel-next"]')
    nxt.click()
    g3_carousel_wait(page, "#carousel-demo", 1)
    page.wait_for_function("() => !document.querySelector('#carousel-demo [data-slot=carousel-previous]').disabled")
    g3_keyboard(page)
    prev.focus()
    page.keyboard.press(g3_key(t, "ArrowLeft"))
    page.wait_for_function("() => document.querySelector('#carousel-demo [data-slot=carousel-previous]').disabled")
    assert not nxt.evaluate("e => e === document.activeElement"), "like shadcn, focus does not move to the next button"
    page.keyboard.press("Tab")
    assert nxt.evaluate("e => e === document.activeElement"), "Tab continues from the disabled button"
    assert prev.get_attribute("data-disabled") == "" and nxt.get_attribute("data-disabled") is None


CAROUSEL_OFFSET = """(root, index) => {
  const viewport = root.querySelector('[data-slot=carousel-content]')
  const item = root.querySelectorAll('[data-slot=carousel-item]')[index]
  const v = viewport.getBoundingClientRect(), r = item.getBoundingClientRect(), cs = getComputedStyle(item)
  if (root.dataset.orientation === 'vertical') return r.top + parseFloat(cs.paddingTop) - v.top
  return getComputedStyle(viewport).direction === 'rtl' ? v.right - (r.right - parseFloat(cs.paddingRight)) : r.left + parseFloat(cs.paddingLeft) - v.left
}"""


def g3_carousel_offset(page, selector, index):
    return page.evaluate("([sel, index]) => (" + CAROUSEL_OFFSET + ")(document.querySelector(sel), index)", [selector, index])


def g3_scroll_rest(page, selector, index):
    return page.evaluate(
        """([sel, index]) => new Promise(resolve => {
          const offset = """ + CAROUSEL_OFFSET + """
          const root = document.querySelector(sel)
          let last = null
          let still = 0
          const tick = () => {
            const now = offset(root, index)
            still = now === last ? still + 1 : 0
            last = now
            if (still < 20) return requestAnimationFrame(tick)
            resolve(now)
          }
          requestAnimationFrame(tick)
        })""",
        [selector, index],
    )


def g3_drag(page, x, y, dx, dy, steps=10, interval=16, hold=0, check=None):
    page.mouse.move(x, y)
    page.mouse.down()
    for i in range(1, steps + 1):
        page.wait_for_timeout(interval)
        page.mouse.move(x + dx * i / steps, y + dy * i / steps)
    if hold:
        page.wait_for_timeout(hold)
    held = check() if check else None
    page.mouse.up()
    return held


def g3_carousel_drag_setup(page, selector):
    root = page.locator(selector)
    root.scroll_into_view_if_needed()
    viewport = root.locator('[data-slot="carousel-content"]')
    box = g3_rect(viewport)
    item = g3_rect(root.locator('[data-slot="carousel-item"]').first)
    vertical = root.get_attribute("data-orientation") == "vertical"
    rtl = root.evaluate("e => getComputedStyle(e).direction === 'rtl'")
    forward = (0, -1) if vertical else (1, 0) if rtl else (-1, 0)
    return box["x"] + box["w"] / 2, box["y"] + box["h"] / 2, item["h"] if vertical else item["w"], forward


CAROUSEL_LOOP = """async id => {
  const { h } = await import("/clanker-ui.js")
  const items = ["1", "2", "3"].map(n => h("div", { "data-slot": "carousel-item" }, h("div", { "data-slot": "card" }, h("div", { "data-slot": "card-content" }, n))))
  const host = h("div", { id, "data-slot": "carousel", "data-loop": true }, h("div", { "data-slot": "carousel-content" }, h("div", null, ...items)), h("button", { "data-slot": "carousel-previous" }), h("button", { "data-slot": "carousel-next" }))
  document.querySelector("#carousel [data-demo~=preview]").append(host)
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
}"""


def check_carousel_drag(t):
    page = t.page
    t.section("carousel")
    sel = "#carousel-demo"
    x, y, size, (fx, fy) = g3_carousel_drag_setup(page, sel)
    g3_listen(page, sel, ["carousel:change"])
    held = g3_drag(page, x, y, fx * 0.3 * size, 0, hold=300, check=lambda: g3_carousel_offset(page, sel, 0))
    assert abs(held + 0.3 * size) < 2, ("the slide follows the pointer", held, size)
    assert abs(g3_scroll_rest(page, sel, 0)) <= 1, "a slow drag under half a slide snaps back"
    assert g3_events(page) == []
    g3_drag(page, x, y, fx * 0.6 * size, 0, hold=300)
    assert abs(g3_scroll_rest(page, sel, 1)) <= 1, "a slow drag over half a slide snaps to the nearest slide"
    g3_drag(page, x, y, fx * 60, 0, steps=3)
    assert abs(g3_scroll_rest(page, sel, 2)) <= 1, "a fast short drag goes on to the next slide"
    assert [e[1]["value"] for e in g3_events(page)] == [1, 2]
    assert not page.locator(f'{sel} [data-slot="carousel-previous"]').is_disabled()


def check_carousel_drag_edge(t):
    page = t.page
    t.section("carousel")
    sel = "#carousel-demo"
    x, y, size, (fx, fy) = g3_carousel_drag_setup(page, sel)
    g3_listen(page, sel, ["carousel:change"])
    held = g3_drag(page, x, y, -fx * 100, 0, hold=300, check=lambda: g3_carousel_offset(page, sel, 0))
    assert 50 < held < 85, ("the first slide resists a drag past the edge (live Embla: 63 to 68 px for 100 px at a 320 px view)", held)
    if t.reduced_motion:
        frames = page.evaluate("s => new Promise(r => { const out = []; const tick = () => { out.push((" + CAROUSEL_OFFSET + ")(document.querySelector(s), 0)); if (out.length < 6) requestAnimationFrame(tick); else r(out) }; requestAnimationFrame(tick) })", sel)
        assert abs(frames[-1]) <= 1, ("with reduced motion the slide springs back at once", frames)
    assert abs(g3_scroll_rest(page, sel, 0)) <= 1, "the slide springs back after the release"
    assert g3_events(page) == []


def check_carousel_drag_click(t):
    page = t.page
    t.section("carousel")
    sel = "#carousel-demo"
    x, y, size, (fx, fy) = g3_carousel_drag_setup(page, sel)
    page.evaluate("s => { window.__clicks = 0; document.querySelector(s + ' [data-slot=carousel-content] > div').addEventListener('click', () => window.__clicks++) }", sel)
    g3_drag(page, x, y, fx * 30, 0, hold=300)
    g3_scroll_rest(page, sel, 0)
    assert page.evaluate("window.__clicks") == 0, "a drag over 10 px does not click"
    g3_drag(page, x, y, fx * 6, 0, steps=3, hold=300)
    g3_scroll_rest(page, sel, 0)
    assert page.evaluate("window.__clicks") == 1, "a move under 10 px still clicks"
    page.mouse.click(x, y)
    assert page.evaluate("window.__clicks") == 2


def check_carousel_drag_vertical(t):
    page = t.page
    t.section("carousel")
    sel = "#carousel-vertical"
    x, y, size, (fx, fy) = g3_carousel_drag_setup(page, sel)
    g3_listen(page, sel, ["carousel:change"])
    g3_drag(page, x, y, 0, fy * 0.6 * size, hold=300)
    assert abs(g3_scroll_rest(page, sel, 1)) <= 1
    assert [e[1]["value"] for e in g3_events(page)] == [1]


def check_carousel_drag_rtl(t):
    page = t.page
    t.section("direction")
    sel = "#direction-carousel"
    x, y, size, (fx, fy) = g3_carousel_drag_setup(page, sel)
    assert fx == 1
    g3_listen(page, sel, ["carousel:change"])
    g3_drag(page, x, y, 0.6 * size, 0, hold=300)
    assert abs(g3_scroll_rest(page, sel, 1)) <= 1, "in RTL a drag to the right goes to the next slide"
    assert [e[1]["value"] for e in g3_events(page)] == [1]


def check_carousel_touch(t):
    if t.engine != "chromium":
        t.skip("touch input needs the Chromium DevTools protocol")
    page = t.page
    t.section("carousel")
    sel = "#carousel-demo"
    x, y, size, (fx, fy) = g3_carousel_drag_setup(page, sel)
    g3_listen(page, sel, ["carousel:change"])
    cdp = page.context.new_cdp_session(page)

    def swipe(dx, dy):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
        for i in range(1, 9):
            page.wait_for_timeout(16)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + dx * i / 8, "y": y + dy * i / 8}]})
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

    before = page.evaluate("scrollY")
    swipe(0, -60)
    assert abs(g3_scroll_rest(page, sel, 0)) <= 1, "a vertical swipe leaves a horizontal carousel to the page"
    assert page.evaluate("scrollY") - before > 20, "the page scrolls"
    page.evaluate("() => new Promise(r => { let last = null, still = 0; const tick = () => { still = scrollY === last ? still + 1 : 0; last = scrollY; still < 10 ? requestAnimationFrame(tick) : r() }; tick() })")
    x, y, size, (fx, fy) = g3_carousel_drag_setup(page, sel)
    swipe(fx * 0.6 * size, 0)
    assert abs(g3_scroll_rest(page, sel, 1)) <= 1, "a swipe goes to the next slide"
    assert [e[1]["value"] for e in g3_events(page)] == [1]
    cdp.detach()


def check_carousel_loop(t):
    page = t.page
    t.section("carousel")
    page.evaluate(CAROUSEL_LOOP, "carousel-loop")
    sel = "#carousel-loop"
    root = page.locator(sel)
    prev, nxt = root.locator('[data-slot="carousel-previous"]'), root.locator('[data-slot="carousel-next"]')
    assert prev.is_enabled() and nxt.is_enabled(), "with loop both buttons stay enabled"
    g3_listen(page, sel, ["carousel:change"])
    prev.click()
    assert abs(g3_scroll_rest(page, sel, 2)) <= 1, "previous on the first slide goes to the last"
    path = page.evaluate("""s => new Promise(resolve => {
      const offset = """ + CAROUSEL_OFFSET + """
      const root = document.querySelector(s)
      const seen = []
      root.querySelector('[data-slot=carousel-next]').click()
      const start = performance.now()
      const tick = now => {
        seen.push(offset(root, 0))
        if (now - start < 900) requestAnimationFrame(tick)
        else resolve(seen)
      }
      requestAnimationFrame(tick)
    })""", sel)
    assert min(path) > -1 and abs(path[-1]) <= 1, ("next on the last slide brings the first slide in from the end side", path)
    x, y, size, (fx, fy) = g3_carousel_drag_setup(page, sel)
    g3_drag(page, x, y, -fx * 0.6 * size, 0, hold=300)
    assert abs(g3_scroll_rest(page, sel, 2)) <= 1, "a drag past the first slide goes on to the last"
    assert [e[1]["value"] for e in g3_events(page)] == [2, 0, 2]


def check_carousel_tab_focus(t):
    page = t.page
    t.docs("/test/behavior/fixtures/carousel.html")
    page.wait_for_function("() => document.querySelector('[data-slot=carousel-content] > div').style.transform")
    page.evaluate("""() => {
      const root = document.querySelector('[data-slot=carousel]')
      root.id = 'carousel-focus'
      const inside = document.createElement('button')
      inside.tabIndex = 0
      inside.textContent = 'Inside'
      root.querySelectorAll('[data-slot=carousel-item]')[2].querySelector('[data-slot=card-content]').append(inside)
    }""")
    sel = "#carousel-focus"
    g3_listen(page, sel, ["carousel:change"])
    page.locator("[data-behavior=sentinel]").first.focus()
    page.keyboard.press("Tab")
    state = page.evaluate("s => new Promise(r => requestAnimationFrame(() => { const v = document.querySelector(s + ' [data-slot=carousel-content]'); r([document.activeElement.textContent, v.scrollLeft, (" + CAROUSEL_OFFSET + ")(document.querySelector(s), 2)]) }))", sel)
    assert state[0] == "Inside" and state[1] == 0 and abs(state[2]) <= 1, ("like Embla (live: same in 3 engines), Tab into a slide jumps to it at once and resets the viewport scroll", state)
    assert [e[1]["value"] for e in g3_events(page)] == [2]


def check_carousel_runtime_options(t):
    page = t.page
    t.section("carousel")
    sel = "#carousel-demo"
    root = page.locator(sel)
    prev, nxt = root.locator('[data-slot="carousel-previous"]'), root.locator('[data-slot="carousel-next"]')
    page.evaluate("rtl => { document.documentElement.dir = rtl ? 'ltr' : 'rtl' }", t.rtl)
    nxt.click()
    assert abs(g3_scroll_rest(page, sel, 1)) <= 1, "after a dir change the carousel measures again and moves in the new direction"
    prev.click()
    assert abs(g3_scroll_rest(page, sel, 0)) <= 1
    assert prev.is_disabled()
    page.evaluate("s => document.querySelector(s).setAttribute('data-loop', '')", sel)
    page.wait_for_function("s => !document.querySelector(s + ' [data-slot=carousel-previous]').disabled", arg=sel)
    prev.click()
    assert abs(g3_scroll_rest(page, sel, 4)) <= 1, "data-loop set later takes effect"


def check_carousel_start_event(t):
    page = t.page
    t.section("carousel")
    events = page.evaluate("""async () => {
      const { h } = await import("/clanker-ui.js")
      const items = ["1", "2", "3"].map(n => h("div", { "data-slot": "carousel-item" }, n))
      const host = h("div", { "data-slot": "carousel" }, h("div", { "data-slot": "carousel-content" }, h("div", null, ...items)), h("button", { "data-slot": "carousel-previous" }), h("button", { "data-slot": "carousel-next" }))
      const out = []
      host.addEventListener("carousel:change", e => out.push(e.detail))
      document.querySelector("#carousel [data-demo~=preview]").append(host)
      const wait = () => new Promise(r => setTimeout(() => requestAnimationFrame(() => requestAnimationFrame(r)), 20))
      await wait()
      host.querySelector("[data-slot=carousel-content] > div").append(h("div", { "data-slot": "carousel-item" }, "4"))
      await wait()
      host.remove()
      return out
    }""")
    assert events == [{"value": 0, "count": 3}, {"value": 0, "count": 4}], ("carousel:change gives the snap count at start and after a new measure", events)


def check_carousel_resize(t):
    page = t.page
    t.section("carousel")
    sel = "#carousel-demo"
    nxt = page.locator(f'{sel} [data-slot="carousel-next"]')
    nxt.click()
    page.wait_for_timeout(80)
    nxt.click()
    assert abs(g3_scroll_rest(page, sel, 2)) <= 1
    page.evaluate("s => { document.querySelector(s).style.maxWidth = '15rem' }", sel)
    assert abs(g3_scroll_rest(page, sel, 2)) <= 1, "after a resize the carousel measures again and keeps the slide"


def check_carousel_double_next(t):
    page = t.page
    t.section("carousel")
    for selector, index in [("#carousel-demo", 2), ("#carousel-vertical", 2)]:
        button = page.locator(f'{selector} [data-slot="carousel-next"]')
        button.scroll_into_view_if_needed()
        box = button.bounding_box()
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.click(x, y)
        page.wait_for_timeout(50)
        page.mouse.click(x, y)
        offset = g3_scroll_rest(page, selector, index)
        assert abs(offset) <= 1, (selector, offset)
        t.shot(f"double-next-{selector[1:]}", page.locator(f'[data-demo~="preview"]:has({selector})'))


def check_collapsible(t):
    page = t.page
    section = t.section("collapsible")
    root = page.locator("#collapsible-demo")
    trigger = root.locator("[data-collapsible-trigger]")
    content = page.locator("#collapsible-more")
    assert root.get_attribute("data-state") == "closed"
    assert trigger.get_attribute("aria-expanded") == "false" and trigger.get_attribute("aria-controls") is None
    assert trigger.get_attribute("type") == "button"
    assert not content.is_visible() and page.locator("#collapsible-always").is_visible()
    assert round(g3_rect(trigger)["w"]) == 32
    g3_listen(page, "#collapsible-demo", ["collapsible:open", "collapsible:close"])
    started = trigger.evaluate("e => { e.click(); return document.getElementById('collapsible-more').getAnimations().map(a => a.animationName) }")
    assert started == [], started
    assert content.evaluate("e => e.hidden") is False
    assert [root.get_attribute("data-state"), trigger.get_attribute("data-state"), content.get_attribute("data-state")] == ["open", "open", "open"]
    assert trigger.get_attribute("aria-expanded") == "true" and trigger.get_attribute("aria-controls") == "collapsible-more"
    t.settle()
    assert content.is_visible()
    assert content.evaluate("e => e.style.overflow") == ""
    t.shot("collapsible-open", section.locator('[data-demo~="preview"]').first)
    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "false" and trigger.get_attribute("aria-controls") is None
    page.wait_for_function("() => document.getElementById('collapsible-more').hidden")
    assert g3_events(page) == [["collapsible:open", None], ["collapsible:close", None]]
    g3_keyboard(page)
    trigger.focus()
    page.keyboard.press("Enter")
    assert root.get_attribute("data-state") == "open"
    page.keyboard.press("Space")
    page.wait_for_function("() => document.getElementById('collapsible-more').hidden")
    assert g3_events(page) == [["collapsible:open", None], ["collapsible:close", None]]
    details = page.locator("#collapsible-settings")
    summary = details.locator("summary")
    g3_listen(page, "#collapsible-settings", ["collapsible:open", "collapsible:close"])
    assert details.get_attribute("data-state") == "closed" and details.evaluate("e => e.open") is False
    summary.click()
    assert details.evaluate("e => e.open") is True and details.get_attribute("data-state") == "open"
    assert round(g3_rect(summary)["h"]) == 28
    t.settle()
    summary.focus()
    page.keyboard.press("Enter")
    page.wait_for_function("() => !document.getElementById('collapsible-settings').open")
    assert g3_events(page) == [["collapsible:open", None], ["collapsible:close", None]]
    details.evaluate("e => { e.open = true }")
    page.wait_for_function("() => document.getElementById('collapsible-settings').dataset.state === 'open'")
    assert g3_events(page) == [["collapsible:open", None]]
    kept = page.evaluate("""async () => {
      const { h } = await import("/clanker-ui.js")
      const host = h("div", { "data-slot": "collapsible" }, h("button", { type: "button", "data-collapsible-trigger": true, "aria-controls": "collapsible-settings" }, "Toggle"))
      document.getElementById("collapsible").append(host)
      await new Promise(r => setTimeout(r, 20))
      const trigger = host.querySelector("button")
      const out = []
      for (let i = 0; i < 2; i++) {
        trigger.click()
        await new Promise(r => setTimeout(r, 20))
        out.push(trigger.getAttribute("aria-controls"))
      }
      host.remove()
      return out
    }""")
    assert kept == ["collapsible-settings", "collapsible-settings"], "an app-set aria-controls stays when the collapsible has no content part"
    tree = page.locator("#collapsible-tree")
    ui = tree.locator("details details")
    assert ui.evaluate("e => e.open") is False
    ui.locator("summary").click()
    assert ui.evaluate("e => e.open") is True
    assert tree.locator("details").first.evaluate("e => e.open") is True
    t.settle()
    t.shot("collapsible-details", section.locator('[data-demo~="preview"]').nth(1))


def g3_mirror(page, ltr_sel, rtl_sel, part, edge_ltr, edge_rtl, container='[data-slot="card"]'):
    return page.evaluate(
        """([l, r, part, el, er, container]) => {
          const pick = (root, sel) => document.querySelector(root).querySelector(sel)
          const a = pick(l, part), b = pick(r, part)
          const ca = a.closest(container).getBoundingClientRect(), cb = b.closest(container).getBoundingClientRect()
          const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect()
          return [el === 'left' ? ra.left - ca.left : ca.right - ra.right, er === 'right' ? cb.right - rb.right : rb.left - cb.left]
        }""",
        [ltr_sel, rtl_sel, part, edge_ltr, edge_rtl, container],
    )


def check_collapsible_close_motion(t):
    t.section("collapsible")
    g3_close_motion(t, "#collapsible-tree > details:first-child > summary", '#collapsible-tree > details:first-child > [data-slot="collapsible-content"]', motion=False)


def check_direction(t):
    page = t.page
    section = t.section("direction")
    assert page.locator("#direction-rtl").evaluate("e => getComputedStyle(e).direction") == "rtl"
    assert page.evaluate("async () => { const m = await import('/clanker-ui.js'); return [m.direction(document.querySelector('#direction-rtl [data-slot=card]')), m.direction()] }") == ["rtl", "rtl" if t.rtl else "ltr"]
    t.settle()
    ltr, rtl = "#direction-ltr", "#direction-rtl"
    for part, container in [
        ('[data-slot="alert"] > svg', '[data-slot="alert"]'),
        ('[data-slot="card-title"]', '[data-slot="card"]'),
        ('[data-slot="item-media"]', '[data-slot="item"]'),
        ('[data-slot="breadcrumb-item"]', '[data-slot="breadcrumb-list"]'),
        ('[data-slot="tabs-list"]', '[data-slot="tabs"]'),
        ('[data-slot="tabs-trigger"]', '[data-slot="tabs-list"]'),
        ('[data-slot="accordion-trigger"] > svg', '[data-slot="accordion-trigger"]'),
        ('[data-slot="card-footer"] [data-slot="button"] > svg', '[data-slot="card-footer"]'),
    ]:
        left = g3_mirror(page, ltr, rtl, part, "right", "left", container)
        start = g3_mirror(page, ltr, rtl, part, "left", "right", container)
        if part.endswith("> svg") and "accordion" in part:
            assert abs(left[0] - left[1]) < 1.5, (part, left)
        elif "button" in part:
            assert start[0] > 0 and start[1] > 0 and abs(start[0] - start[1]) < 40, (part, start)
        else:
            assert abs(start[0] - start[1]) < 1.5, (part, start)
    action = g3_mirror(page, ltr, rtl, '[data-slot="card-action"]', "right", "left")
    assert abs(action[0] - action[1]) < 1.5, action
    badge = g3_mirror(page, ltr, rtl, '[data-slot="avatar-badge"]', "right", "left", '[data-slot="avatar"]')
    assert badge == [0, 0] or (abs(badge[0]) < 1 and abs(badge[1]) < 1), badge
    flip = page.evaluate("() => [getComputedStyle(document.querySelector('#direction-ltr [data-slot=breadcrumb-separator] svg')).rotate, getComputedStyle(document.querySelector('#direction-rtl [data-slot=breadcrumb-separator] svg')).rotate]")
    assert flip == ["none", "180deg"], flip
    fill = page.evaluate(
        """() => ['#direction-ltr', '#direction-rtl'].map(s => {
          const bar = document.querySelector(s + ' [data-slot=progress]').getBoundingClientRect()
          const ind = document.querySelector(s + ' [data-slot=progress-indicator]').getBoundingClientRect()
          const shown = Math.min(ind.right, bar.right) - Math.max(ind.left, bar.left)
          return [shown / bar.width, ind.left < bar.left + 1 ? 'start-left' : 'start-right']
        })"""
    )
    assert abs(fill[0][0] - 0.3) < 0.02 and abs(fill[1][0] - 0.3) < 0.02, fill
    assert fill[0][1] == "start-left" and fill[1][1] == "start-right", fill
    g3_keyboard(page)
    rtl_tabs = page.locator('#direction-rtl [data-slot="tabs-trigger"]')
    rtl_tabs.first.focus()
    page.keyboard.press("ArrowLeft")
    assert rtl_tabs.nth(1).evaluate("e => e === document.activeElement") and rtl_tabs.first.get_attribute("aria-selected") == "true"
    page.keyboard.press("Enter")
    assert rtl_tabs.nth(1).get_attribute("aria-selected") == "true"
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Space")
    assert rtl_tabs.first.get_attribute("aria-selected") == "true"
    nav = page.locator("#direction-nav")
    links = nav.locator('[data-slot="pagination-link"]')
    assert g3_rect(links.first)["x"] > g3_rect(links.last)["x"]
    assert links.first.locator("svg").evaluate("e => getComputedStyle(e).rotate") == "180deg"
    car = page.locator("#direction-carousel")
    prev, nxt = car.locator('[data-slot="carousel-previous"]'), car.locator('[data-slot="carousel-next"]')
    assert g3_rect(prev)["x"] > g3_rect(car)["r"] and g3_rect(nxt)["r"] < g3_rect(car)["x"]
    assert prev.locator("svg").evaluate("e => getComputedStyle(e).rotate") == "180deg"
    g3_listen(page, "#direction-carousel", ["carousel:change"])
    nxt.click()
    g3_carousel_wait(page, "#direction-carousel", 1)
    page.wait_for_function("() => window.__g3.length >= 1")
    assert car.locator('[data-slot="carousel-content"] > div').evaluate("e => new DOMMatrix(getComputedStyle(e).transform).m41") > 10
    nxt.focus()
    page.keyboard.press("ArrowLeft")
    g3_carousel_wait(page, "#direction-carousel", 2)
    page.wait_for_function("() => window.__g3.length >= 2")
    prev.focus()
    page.keyboard.press("ArrowRight")
    g3_carousel_wait(page, "#direction-carousel", 1)
    page.wait_for_function("() => window.__g3.length >= 3")
    assert [e[1]["value"] for e in g3_events(page)] == [1, 2, 1]
    quote = page.locator("#direction-text blockquote")
    assert g3_style(quote, "border-right-width") == "2px" and g3_style(quote, "border-left-width") == "0px" and g3_style(quote, "padding-right") == "24px"
    bullets = page.locator("#direction-text ul")
    assert g3_style(bullets, "margin-right") == "24px" and g3_style(bullets, "margin-left") == "0px"
    group = page.locator("#direction-resizable")
    panels = group.locator('[data-slot="resizable-panel"]')
    assert g3_rect(panels.first)["x"] > g3_rect(panels.last)["x"]
    handle = group.locator('[data-slot="resizable-handle"]')
    handle.focus()
    page.keyboard.press("ArrowLeft")
    assert handle.get_attribute("aria-valuenow") == "35"
    page.keyboard.press("ArrowRight")
    assert handle.get_attribute("aria-valuenow") == "30"
    t.settle()
    t.shot("direction", section)


def check_empty(t):
    page = t.page
    section = t.section("empty")
    empty = section.locator('[data-slot="empty"]').first
    assert g3_style(empty, "text-align") == "center"
    media = empty.locator('[data-slot="empty-icon"]')
    assert round(g3_rect(media)["w"]) == 32 and round(g3_rect(media.locator("svg"))["w"]) == 16
    title = empty.locator('[data-slot="empty-title"]')
    assert g3_style(title, "font-size") == "14px"
    e, m = g3_rect(empty), g3_rect(media)
    assert abs((m["x"] + m["w"] / 2) - (e["x"] + e["w"] / 2)) < 1.5
    outline = section.locator('[data-slot="empty"][data-variant="outline"]').first
    assert g3_style(outline, "border-top-style") == "dashed" and g3_style(outline, "border-top-width") == "1px"
    assert g3_style(empty, "border-top-width") == "0px"
    assert g3_style(empty, "padding-top") == "24px"


def check_item(t):
    page = t.page
    section = t.section("item")
    basic = section.locator('[data-slot="item"]').first
    assert g3_style(basic, "padding-top") == "10px" and g3_style(basic, "border-top-width") == "1px"
    sizes = section.locator('[data-demo~="preview"]').nth(1).locator('[data-slot="item"]')
    assert [g3_style(sizes.nth(i), "padding-top") for i in (0, 3, 4)] == ["10px", "10px", "8px"]
    assert g3_style(sizes.nth(0), "border-top-color") == "rgba(0, 0, 0, 0)"
    assert g3_style(sizes.nth(2), "background-color") != "rgba(0, 0, 0, 0)"
    icon = section.locator('[data-slot="item-media"][data-variant="icon"]')
    assert round(g3_rect(icon)["w"]) == 16 and g3_style(icon, "border-top-width") == "0px"
    host = icon.locator("..")
    assert abs(g3_rect(icon)["y"] - g3_rect(host.locator('[data-slot="item-content"]'))["y"] - 2) < 1.5
    link = page.locator("#item-link")
    g3_keyboard(page)
    link.focus()
    t.settle()
    assert g3_style(link, "outline-style") == "none" and "0px 0px 0px 3px" in g3_style(link, "box-shadow")
    t.a11y()
    assert g3_style(link, "outline-style") == "solid"
    ring = page.evaluate("() => { const p = document.createElement('p'); p.style.color = 'var(--ring)'; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c }")
    assert g3_style(link, "border-top-color") == ring
    group = page.locator("#item-group")
    assert group.get_attribute("role") == "list"
    sep = group.locator('[data-slot="item-separator"]')
    assert sep.get_attribute("role") == "none" and round(g3_rect(sep)["h"]) == 1
    desc = section.locator('[data-slot="item-description"]').first
    assert g3_style(desc, "-webkit-line-clamp") == "2"


def check_pagination(t):
    page = t.page
    section = t.section("pagination")
    nav = page.locator("#pagination-demo")
    links = nav.locator('[data-slot="pagination-link"]')
    active = nav.locator('[aria-current="page"]')
    assert active.inner_text() == "2"
    assert g3_style(active, "border-top-width") == "1px"
    assert g3_style(links.nth(1), "border-top-color") == "rgba(0, 0, 0, 0)" and g3_style(active, "border-top-color") != "rgba(0, 0, 0, 0)"
    assert round(g3_rect(links.nth(1))["w"]) == 32 and round(g3_rect(links.nth(1))["h"]) == 32
    label = links.first.locator("span")
    assert label.is_visible() == (not t.mobile)
    assert links.first.get_attribute("aria-label") == "Go to previous page"
    ellipsis = nav.locator('[data-slot="pagination-ellipsis"]')
    assert ellipsis.get_attribute("aria-hidden") == "true" and round(g3_rect(ellipsis)["w"]) == 32
    g3_keyboard(page)
    active.focus()
    assert page.evaluate("document.activeElement.textContent") == "2"
    t.settle()
    assert g3_style(active, "outline-style") == "none" and "0px 0px 0px 3px" in g3_style(active, "box-shadow")
    t.a11y()
    assert g3_style(active, "outline-style") == "solid"
    links.nth(1).hover()
    page.wait_for_timeout(200)
    assert g3_style(links.nth(1), "background-color") != "rgba(0, 0, 0, 0)"


def check_progress(t):
    page = t.page
    section = t.section("progress")
    bar = page.locator("#progress-demo")
    attrs = lambda loc: loc.evaluate("e => ['role', 'aria-valuemin', 'aria-valuemax', 'aria-valuenow', 'aria-valuetext', 'data-state'].map(a => e.getAttribute(a))")
    assert attrs(bar) == ["progressbar", "0", "100", "66", "66%", "loading"]
    shown = lambda loc: loc.evaluate("e => { const b = e.getBoundingClientRect(), i = e.querySelector('[data-slot=progress-indicator]').getBoundingClientRect(); return Math.round((Math.min(i.right, b.right) - Math.max(i.left, b.left)) / b.width * 100) }")
    t.settle()
    assert shown(bar) == 66
    assert round(g3_rect(bar)["h"]) == 4
    page.locator("#progress-more").click()
    assert attrs(bar)[3:] == ["76", "76%", "loading"]
    t.settle()
    assert shown(bar) == 76
    for _ in range(3):
        page.locator("#progress-more").click()
    assert attrs(bar)[3:] == ["100", "100%", "complete"]
    assert page.locator("#progress-text").inner_text() == "100%"
    states = section.locator('[data-demo~="preview"]').nth(1).locator('[data-slot="progress"]')
    assert attrs(states.nth(1)) == ["progressbar", "0", "4", "3", "75%", "loading"]
    assert attrs(states.nth(2))[5] == "complete"
    assert attrs(states.nth(3)) == ["progressbar", "0", "100", None, None, "indeterminate"]
    page.evaluate("() => { document.querySelector('#progress [data-demo~=preview]:nth-of-type(2) [data-slot=progress]:last-child').dataset.value = '20' }")
    page.wait_for_function("() => document.querySelectorAll('#progress [data-slot=progress]')[4].getAttribute('aria-valuenow') === '20'")
    t.settle()
    t.shot("progress", section)


def check_progress_value_locale(t):
    page = t.page
    t.section("progress")
    out = page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const make = lang => h("div", { "data-slot": "progress", "data-value": "56", "aria-label": "Upload", lang }, h("span", { "data-slot": "progress-value" }))
          const bars = ["ar-u-nu-arab", "en-US", "de", "ar"].map(make)
          document.getElementById("progress").append(...bars)
          await new Promise(r => setTimeout(r, 30))
          const out = bars.map(b => [b.querySelector("[data-slot=progress-value]").textContent, b.getAttribute("aria-valuetext"), new Intl.NumberFormat(b.lang, { style: "percent" }).format(0.56)])
          for (const b of bars) b.remove()
          return out
        }"""
    )
    for text, valuetext, want in out:
        assert text == valuetext == want, out
    assert out[0][0].startswith("\u0665\u0666") and out[1][0] == "56%", out
    t.docs("/docs/components/progress")
    value = page.locator('[data-example="progress-rtl"] [data-slot="progress-value"]')
    value.wait_for()
    assert value.text_content() == out[0][2], value.text_content()


def check_progress_zero(t):
    page = t.page
    t.section("progress")
    page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const zero = h("div", { id: "progress-zero" })
          for (const value of ["0", null]) for (const offset of [0, 0.1, 0.25, 0.33, 0.5, 0.67, 0.75, 0.9]) for (const width of [200, 200.3, 200.5, 199.7]) {
            const bar = h("div", { "data-slot": "progress", "data-value": value, "aria-label": "Zero" })
            bar.style.width = `${width}px`
            const row = h("div", bar)
            row.style.padding = "1px 0"
            row.style.paddingInlineStart = `${offset}px`
            zero.append(row)
          }
          const control = h("div", { id: "progress-zero-control", "data-slot": "progress", "data-value": "50", "aria-label": "Half" })
          control.style.width = "200px"
          const box = h("div", zero, control)
          Object.assign(box.style, { position: "fixed", insetInlineStart: "0", top: "1rem", zIndex: "2147483647", width: "15rem", padding: "4px", background: "var(--background)" })
          document.body.append(box)
        }"""
    )
    page.wait_for_function("() => [...document.querySelectorAll('#progress-zero [data-slot=progress], #progress-zero-control')].every(e => e.querySelector('[data-slot=progress-indicator]'))")
    t.settle()
    zero, control = page.locator("#progress-zero"), page.locator("#progress-zero-control")
    shown = zero.screenshot(animations="disabled")
    half = control.screenshot(animations="disabled")
    page.evaluate("() => { for (const i of document.querySelectorAll('#progress-zero [data-slot=progress-indicator], #progress-zero-control [data-slot=progress-indicator]')) { i.style.transition = 'none'; i.style.visibility = 'hidden' } }")
    assert control.screenshot(animations="disabled") != half, "the control bar must change when its indicator is hidden"
    assert zero.screenshot(animations="disabled") == shown, "a bar at 0 or indeterminate shows part of its indicator"
    t.shot("progress-zero", zero)


def check_resizable(t):
    page = t.page
    section = t.section("resizable")
    group = page.locator("#resizable-demo")
    handle = group.locator(':scope > [data-slot="resizable-handle"]')
    panels = group.locator(':scope > [data-slot="resizable-panel"]')
    assert handle.get_attribute("role") == "separator" and handle.get_attribute("aria-orientation") == "vertical" and handle.get_attribute("aria-label") == "Resize"
    assert page.evaluate("() => [...document.querySelectorAll('[data-slot=resizable-panel-group]')].filter(g => g.hasAttribute('aria-orientation')).length") == 0
    assert g3_style(page.locator("#resizable-nested"), "flex-direction") == "column"
    assert handle.get_attribute("tabindex") == "0" and handle.get_attribute("aria-controls") == panels.first.get_attribute("id")
    assert [handle.get_attribute(a) for a in ("aria-valuenow", "aria-valuemin", "aria-valuemax")] == ["50", "20", "100"]
    width = lambda: round(g3_rect(panels.first)["w"] / (g3_rect(group)["w"] - 3) * 100)
    assert width() == 50
    hits = handle.evaluate("e => { const r = e.getBoundingClientRect(), y = r.top + r.height / 2; return [r.left - 1, r.right + 1].map(x => document.elementFromPoint(x, y) === e) }")
    assert hits == [True, True], hits
    g3_listen(page, "#resizable-demo", ["resizable:change"])
    g3_keyboard(page)
    handle.focus()
    t.settle()
    assert "0px 0px 0px 1px" in g3_style(handle, "box-shadow"), "the focused handle shows a ring"
    page.keyboard.press(g3_key(t, "ArrowRight"))
    t.settle()
    assert handle.get_attribute("aria-valuenow") == "55" and width() == 55
    page.keyboard.press("ArrowUp")
    assert handle.get_attribute("aria-valuenow") == "55"
    page.keyboard.press("Home")
    assert handle.get_attribute("aria-valuenow") == "20"
    page.keyboard.press(g3_key(t, "ArrowLeft"))
    assert handle.get_attribute("aria-valuenow") == "20"
    events = g3_events(page)
    assert [e[1]["value"] for e in events] == [[55, 45], [20, 80]], events
    box = g3_rect(handle)
    page.mouse.move(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
    page.mouse.down()
    room = g3_rect(group)["w"] - 3
    page.mouse.move(box["r"] - room * 0.3 if t.rtl else box["x"] + room * 0.3, box["y"] + box["h"] / 2, steps=5)
    page.mouse.up()
    assert abs(float(handle.get_attribute("aria-valuenow")) - 50) <= 1
    assert re.fullmatch(r"\d+\.\d{1,3}", handle.get_attribute("aria-valuenow")), "like the live handle (35.602), aria-valuenow keeps three decimals"
    assert handle.evaluate("e => e === document.activeElement")
    page.keyboard.press("End")
    assert handle.get_attribute("aria-valuenow") == "100"
    handle.dblclick()
    assert handle.get_attribute("aria-valuenow") == "50", "a double click resets the panel to its default size, as in shadcn"
    nested = page.locator("#resizable-nested")
    nh = nested.locator('[data-slot="resizable-handle"]')
    assert nh.get_attribute("aria-orientation") == "horizontal" and nh.get_attribute("aria-valuenow") == "25"
    nh.focus()
    page.keyboard.press("ArrowDown")
    assert nh.get_attribute("aria-valuenow") == "30"
    page.keyboard.press("ArrowRight")
    assert nh.get_attribute("aria-valuenow") == "30"
    grip = page.locator("#resizable-grip")
    gh = grip.locator('[data-slot="resizable-handle"]')
    assert gh.locator(":scope > div").count() == 1 and gh.locator(":scope > div > svg").count() == 0 and round(g3_rect(gh.locator(":scope > div"))["h"]) == 24
    gh.focus()
    page.keyboard.press("End")
    assert gh.get_attribute("aria-valuenow") == "60"
    page.keyboard.press("Home")
    assert gh.get_attribute("aria-valuenow") == "15"
    t.shot("resizable", section)


def check_scroll_area(t):
    page = t.page
    section = t.section("scroll-area")
    root = page.locator("#scroll-area-demo")
    viewport = root.locator('[data-slot="scroll-area-viewport"]')
    bar = root.locator('[data-slot="scroll-area-scrollbar"]')
    thumb = bar.locator('[data-slot="scroll-area-thumb"]')
    assert viewport.get_attribute("tabindex") == "0" and viewport.get_attribute("role") == "region"
    assert bar.count() == 1 and bar.get_attribute("aria-hidden") is None and bar.get_attribute("data-orientation") == "vertical"
    assert thumb.get_attribute("aria-hidden") is None and thumb.get_attribute("data-orientation") == "vertical"
    assert viewport.evaluate("e => e.scrollHeight > e.clientHeight * 3")
    ratio = viewport.evaluate("e => e.clientHeight / e.scrollHeight")
    track = bar.evaluate("e => e.clientHeight - 2")
    assert abs(g3_rect(thumb)["h"] - max(ratio * track, 18)) < 1.5
    assert round(g3_rect(bar)["w"]) == 10
    assert abs(g3_inline(t, bar)["r"] - g3_inline(t, root)["r"] + 1) < 1.5
    page.mouse.move(0, 0)
    page.wait_for_function("() => !document.querySelector('#scroll-area-demo [data-slot=scroll-area-scrollbar]').hasAttribute('data-hovering')")
    assert bar.get_attribute("data-state") is None and g3_style(bar, "visibility") == "visible"
    root.hover()
    assert bar.get_attribute("data-hovering") == ""
    t.settle()
    t.shot("scroll-area-hover", root)
    g3_keyboard(page)
    viewport.focus()
    t.settle()
    assert g3_style(viewport, "outline-style") == "none" and "0px 0px 0px 3px" in g3_style(viewport, "box-shadow")
    t.a11y()
    assert g3_style(viewport, "outline-style") == "solid"
    page.keyboard.press("End")
    page.wait_for_function("() => { const v = document.querySelector('#scroll-area-demo [data-slot=scroll-area-viewport]'); return v.scrollTop >= v.scrollHeight - v.clientHeight - 2 }")
    page.wait_for_function("() => { const b = document.querySelector('#scroll-area-demo [data-slot=scroll-area-scrollbar]').getBoundingClientRect(), t = b && document.querySelector('#scroll-area-demo [data-slot=scroll-area-thumb]').getBoundingClientRect(); return Math.abs(t.bottom - b.bottom + 1) < 2 }")
    page.wait_for_timeout(500)
    page.keyboard.press("Home")
    page.wait_for_function("() => document.querySelector('#scroll-area-demo [data-slot=scroll-area-viewport]').scrollTop === 0")
    page.wait_for_timeout(300)
    tb, bb = g3_rect(thumb), g3_rect(bar)
    page.mouse.move(tb["x"] + tb["w"] / 2, tb["y"] + 5)
    page.mouse.down()
    page.mouse.move(tb["x"] + tb["w"] / 2, tb["y"] + 5 + (bb["h"] - tb["h"]) / 2, steps=4)
    page.mouse.up()
    half = viewport.evaluate("e => e.scrollTop / (e.scrollHeight - e.clientHeight)")
    assert abs(half - 0.5) < 0.05, half
    page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
    page.evaluate("() => addEventListener('pointerdown', e => { const b = e.target.closest('[data-slot=scroll-area-scrollbar]'), t = b?.querySelector('[data-slot=scroll-area-thumb]'); if (b) window.__track = [e.clientY - b.getBoundingClientRect().top, b.offsetHeight, t.offsetHeight] }, { capture: true, once: true })")
    page.mouse.click(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] * 0.3)
    at, height, size = page.evaluate("window.__track")
    jump = viewport.evaluate("e => [e.scrollTop, e.scrollHeight - e.clientHeight]")
    want = (at - size / 2 - 2) / (height - size - 2) * jump[1]
    assert abs(jump[0] - want) < 1.5, ("a track click maps the pointer as Base UI does (2 px scrollbar padding; live 30 %: 422 px)", jump, want)
    page.mouse.click(bb["x"] + bb["w"] / 2, bb["b"] - 3)
    assert not viewport.evaluate("e => e === document.activeElement"), "like Base UI, a press on the scrollbar does not keep focus in the viewport"
    page.wait_for_function("() => { const v = document.querySelector('#scroll-area-demo [data-slot=scroll-area-viewport]'); return v.scrollTop >= v.scrollHeight - v.clientHeight - 2 }")
    before = viewport.evaluate("e => e.scrollTop")
    page.mouse.move(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] / 2)
    page.mouse.wheel(0, -200)
    page.wait_for_function("b => document.querySelector('#scroll-area-demo [data-slot=scroll-area-viewport]').scrollTop < b - 50", arg=before)
    horizontal = page.locator("#scroll-area-horizontal")
    hbar = horizontal.locator('[data-slot="scroll-area-scrollbar"][data-orientation="horizontal"]')
    vbar = horizontal.locator('[data-slot="scroll-area-scrollbar"]:not([data-orientation="horizontal"])')
    assert g3_style(hbar, "visibility") == "visible" and g3_style(vbar, "visibility") == "hidden"
    assert round(g3_rect(hbar)["h"]) == 10
    hv = horizontal.locator('[data-slot="scroll-area-viewport"]')
    hv.evaluate("e => { e.scrollLeft = getComputedStyle(e).direction === 'rtl' ? -e.scrollWidth : e.scrollWidth }")
    page.wait_for_function("() => document.querySelector('#scroll-area-horizontal [data-orientation=horizontal]').hasAttribute('data-scrolling')")
    assert vbar.get_attribute("data-scrolling") is None, "like Base UI, data-scrolling is set per axis"
    page.wait_for_function("() => { const b = document.querySelector('#scroll-area-horizontal [data-orientation=horizontal]').getBoundingClientRect(), t = document.querySelector('#scroll-area-horizontal [data-orientation=horizontal] [data-slot=scroll-area-thumb]').getBoundingClientRect(); return getComputedStyle(document.documentElement).direction === 'rtl' ? Math.abs(t.left - b.left - 1) < 2 : Math.abs(t.right - b.right + 1) < 2 }")
    t.shot("scroll-area", section)


def check_scroll_area_children(t):
    page = t.page
    t.section("scroll-area")
    result = page.evaluate("""async () => {
      const removed = []
      const unobserve = ResizeObserver.prototype.unobserve
      ResizeObserver.prototype.unobserve = function (target) {
        removed.push(target)
        return unobserve.call(this, target)
      }
      const viewport = document.querySelector("#scroll-area-demo [data-slot=scroll-area-viewport]")
      const thumb = document.querySelector("#scroll-area-demo [data-slot=scroll-area-thumb]")
      const extra = document.createElement("div")
      extra.style.height = "2000px"
      const before = thumb.getBoundingClientRect().height
      viewport.append(extra)
      await new Promise(r => setTimeout(r, 100))
      const grown = thumb.getBoundingClientRect().height
      extra.remove()
      await new Promise(r => setTimeout(r, 100))
      const after = thumb.getBoundingClientRect().height
      ResizeObserver.prototype.unobserve = unobserve
      return { shrank: grown < before - 1, restored: Math.abs(after - before) < 1, unobserved: removed.includes(extra) }
    }""")
    assert result == {"shrank": True, "restored": True, "unobserved": True}, result


def check_strings_layout(t):
    page = t.page
    t.section("carousel")
    out = page.evaluate("""async () => {
      const { h, strings } = await import("/clanker-ui.js")
      const host = h("div", { "data-string-previous-slide": "Nazaj", "data-string-next-slide": "Naprej", "data-string-slide-of": "{index} od {count}", "data-string-toggle-sidebar": "Stranska vrstica", "data-string-loading": "Nalagam", "data-string-resize": "Velikost", "data-string-more": "Več" },
        h("div", { "data-slot": "carousel" }, h("div", { "data-slot": "carousel-content" }, h("div", null, h("div", { "data-slot": "carousel-item" }, "A"), h("div", { "data-slot": "carousel-item" }, "B"))), h("button", { "data-slot": "carousel-previous" }), h("button", { "data-slot": "carousel-next" })),
        h("button", { "data-slot": "sidebar-trigger" }),
        h("span", { "data-slot": "spinner" }),
        h("div", { "data-slot": "resizable-panel-group" }, h("div", { "data-slot": "resizable-panel" }), h("div", { "data-slot": "resizable-handle" }), h("div", { "data-slot": "resizable-panel" })),
        h("nav", { "data-slot": "breadcrumb" }, h("span", { "data-slot": "breadcrumb-ellipsis" })))
      strings.breadcrumb = "drobtine"
      document.getElementById("carousel").append(host)
      await new Promise(r => setTimeout(r, 20))
      strings.breadcrumb = "breadcrumb"
      const out = {
        previous: host.querySelector("[data-slot=carousel-previous] .sr-only").textContent,
        next: host.querySelector("[data-slot=carousel-next] .sr-only").textContent,
        slide: host.querySelector("[data-slot=carousel-item]").getAttribute("aria-label"),
        toggle: host.querySelector("[data-slot=sidebar-trigger] .sr-only").textContent,
        loading: host.querySelector("[data-slot=spinner]").getAttribute("aria-label"),
        resize: host.querySelector("[data-slot=resizable-handle]").getAttribute("aria-label"),
        more: host.querySelector("[data-slot=breadcrumb-ellipsis] .sr-only").textContent,
        breadcrumb: host.querySelector("nav").getAttribute("aria-label"),
      }
      host.remove()
      return out
    }""")
    assert out == {"previous": "Nazaj", "next": "Naprej", "slide": "1 od 2", "toggle": "Stranska vrstica", "loading": "Nalagam", "resize": "Velikost", "more": "Več", "breadcrumb": "drobtine"}, out


def check_separator(t):
    page = t.page
    section = t.section("separator")
    horizontal = page.locator("#separator-horizontal")
    assert horizontal.get_attribute("role") == "none" and horizontal.get_attribute("data-orientation") == "horizontal"
    assert round(g3_rect(horizontal)["h"]) == 1 and abs(g3_rect(horizontal)["w"] - g3_rect(page.locator("#separator-demo"))["w"]) < 1
    vertical = page.locator('#separator-row [data-slot="separator"]').first
    assert round(g3_rect(vertical)["w"]) == 1 and round(g3_rect(vertical)["h"]) == 20
    border = page.evaluate("() => { const p = document.createElement('p'); p.style.color = 'var(--border)'; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c }")
    assert g3_style(vertical, "background-color") == border
    semantic = page.locator('#separator-list [data-slot="separator"]').first
    assert semantic.get_attribute("role") == "separator" and semantic.get_attribute("aria-orientation") is None
    tags = page.locator('#scroll-area-tags [data-slot="separator"]')
    assert tags.count() == 50 and tags.first.get_attribute("role") == "none"


def g3_sidebar_sheet(t):
    page = t.page
    main = page.locator("#sidebar-main")
    sidebar = main.locator(':scope > [data-slot="sidebar"]')
    container = sidebar.locator(':scope > [data-slot="sidebar-container"]')
    trigger = page.locator("#sidebar-main-trigger")
    assert not container.is_visible()
    assert trigger.get_attribute("aria-expanded") == "false"
    g3_listen(page, "#sidebar-main [data-slot=sidebar]", ["sidebar:open", "sidebar:close"])
    g3_keyboard(page)
    trigger.focus()
    page.keyboard.press("Enter")
    assert sidebar.get_attribute("data-mobile") == "open"
    assert container.get_attribute("role") == "dialog" and container.get_attribute("aria-modal") == "true"
    assert trigger.get_attribute("aria-expanded") == "true"
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") == "hidden"
    t.settle(3000)
    box = g3_inline(t, sidebar)
    assert box["x"] == (-390 if t.rtl else 0) and abs(box["w"] - 0.75 * 390) < 1, box
    assert abs(g3_rect(container)["w"] - (box["w"] - 1)) < 1, g3_rect(container)
    backdrop = page.evaluate("""([x]) => {
      const sheet = document.querySelector('#sidebar-main [data-slot=sidebar]')
      const hit = document.elementFromPoint(x, 400)
      const r = hit.getBoundingClientRect()
      return [hit.dataset.slot, getComputedStyle(hit).backgroundColor, [r.left, r.top, r.width, r.height].map(Math.round), sheet.matches(':popover-open'), document.elementFromPoint(x === 20 ? 370 : 20, 400).closest('[data-slot=sidebar]') === sheet]
    }""", [20 if t.rtl else 370])
    assert backdrop == ["sheet-overlay", "rgba(0, 0, 0, 0.1)", [0, 0, 390, 844], True, True], ("the backdrop covers the page beside the sheet", backdrop)
    on_top = page.evaluate("""async () => {
      const { toast } = await import("/clanker-ui.js")
      toast("Saved", { duration: Infinity })
      await new Promise(r => setTimeout(r, 400))
      const t = [...document.querySelectorAll('[data-slot=toast]')].at(-1)
      const r = t.getBoundingClientRect()
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)
      toast.dismiss()
      return !!hit && t.contains(hit)
    }""")
    assert on_top, "a toast shows above the open mobile sidebar"
    assert page.evaluate("() => document.getElementById('sidebar-main').querySelector('[data-slot=sidebar-container]').contains(document.activeElement)")
    labels = page.evaluate("() => [...document.querySelectorAll('#sidebar-main [data-slot=sidebar-group-label]')].map(e => getComputedStyle(e).opacity)")
    assert labels == ["1", "1"]
    t.shot("sidebar-sheet", page)
    for _ in range(30):
        page.keyboard.press("Tab")
        assert page.evaluate("() => document.getElementById('sidebar-main').querySelector('[data-slot=sidebar-container]').contains(document.activeElement)")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#sidebar-main [data-slot=sidebar]').hasAttribute('data-mobile')")
    assert sidebar.get_attribute("popover") is None and not container.is_visible() and page.locator("#sidebar-main [data-slot=sheet-overlay]").count() == 0
    assert page.evaluate("document.activeElement.id") == "sidebar-main-trigger"
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") != "hidden"
    assert trigger.get_attribute("aria-expanded") == "false"
    trigger.click()
    t.settle(3000)
    page.mouse.click(20 if t.rtl else 370, 400, button="right")
    page.wait_for_timeout(250)
    assert sidebar.get_attribute("data-mobile") == "open", "a right click on the backdrop keeps the sheet open, as the Base UI sheet"
    page.mouse.move(20 if t.rtl else 370, 400)
    page.mouse.down()
    page.wait_for_timeout(250)
    held = sidebar.get_attribute("data-mobile")
    page.mouse.up()
    assert held == "open", "the sheet closes on the click, not on the press, as the Base UI sheet"
    page.wait_for_function("() => !document.querySelector('#sidebar-main [data-slot=sidebar]').hasAttribute('data-mobile')")
    page.keyboard.press("ControlOrMeta+b")
    assert sidebar.get_attribute("data-mobile") == "open"
    page.keyboard.press("ControlOrMeta+b")
    page.wait_for_function("() => !document.querySelector('#sidebar-main [data-slot=sidebar]').hasAttribute('data-mobile')")
    assert g3_events(page) == [["sidebar:open", {"mobile": True}], ["sidebar:close", {"mobile": True}]] * 3
    floating = page.locator("#sidebar-floating")
    floating.locator('[data-slot="sidebar-trigger"]').click()
    fsheet = floating.locator(':scope > [data-slot="sidebar"]')
    t.settle(3000)
    box = g3_inline(t, fsheet)
    assert round(box["r"]) == (0 if t.rtl else 390) and abs(box["w"] - 0.75 * 390) < 1, box
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#sidebar-floating [data-slot=sidebar]').hasAttribute('data-mobile')")
    assert sidebar.get_attribute("data-state") == "expanded"
    assert page.locator("#sidebar-none").is_visible()


G3_CONTRAST = """([fg, bg]) => {
  const ctx = document.createElement("canvas").getContext("2d", { willReadFrequently: true })
  const rgb = color => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = bg; ctx.fillRect(0, 0, 1, 1); ctx.fillStyle = color; ctx.fillRect(0, 0, 1, 1); return [...ctx.getImageData(0, 0, 1, 1).data].slice(0, 3) }
  const lum = c => { const [r, g, b] = c.map(v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4 }); return 0.2126 * r + 0.7152 * g + 0.0722 * b }
  const a = lum(rgb(fg)), b = lum(rgb(bg))
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
}"""


def check_layout_focus_rings(t):
    page = t.page
    t.section("resizable")
    t.a11y()
    g3_keyboard(page)
    targets = [("#resizable [data-slot=resizable-handle]", "#resizable [data-slot=resizable-panel-group]")]
    if not t.mobile:
        targets.append(("#sidebar-main [data-slot=sidebar-menu-button]", "#sidebar-main [data-slot=sidebar-inner]"))
    for focus, surface in targets:
        el = page.locator(focus).first
        el.scroll_into_view_if_needed()
        el.focus()
        ring = el.evaluate("e => { const s = getComputedStyle(e); return [e.matches(':focus-visible'), s.outlineStyle, s.outlineColor] }")
        assert ring[0] and ring[1] == "solid", f"{focus} draws its focus ring as an outline, which forced colors keep: {ring}"
        back = page.locator(surface).first.evaluate("e => { for (let n = e; n; n = n.parentElement) { const c = getComputedStyle(n).backgroundColor; if (c !== 'rgba(0, 0, 0, 0)') return c } return getComputedStyle(document.body).backgroundColor }")
        ratio = page.evaluate(G3_CONTRAST, [ring[2], back])
        assert ratio >= 3, f"{focus} focus ring has {ratio:.2f}:1 on {back}"


def check_sidebar_sheet_mouse_focus(t):
    if not t.mobile:
        t.skip("the sheet is below 768 px")
    page = t.page
    t.section("sidebar")
    page.locator("#sidebar-main-trigger").click()
    page.wait_for_function("() => document.querySelector('#sidebar-main [data-slot=sidebar]').dataset.mobile === 'open'")
    t.settle(3000)
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#sidebar-main [data-slot=sidebar]').hasAttribute('data-mobile')")
    assert page.evaluate("document.activeElement.id") == "sidebar-main-trigger"


def check_sidebar(t):
    page = t.page
    section = t.section("sidebar")
    if t.mobile:
        g3_sidebar_sheet(t)
        t.shot("sidebar", section)
        return
    main = page.locator("#sidebar-main")
    sidebar = main.locator(':scope > [data-slot="sidebar"]')
    container = sidebar.locator(':scope > [data-slot="sidebar-container"]')
    trigger = page.locator("#sidebar-main-trigger")
    assert sidebar.get_attribute("data-state") == "expanded" and sidebar.get_attribute("data-collapsible") == ""
    assert round(g3_rect(container)["w"]) == 256
    assert trigger.get_attribute("aria-controls") == sidebar.get_attribute("id") and trigger.get_attribute("aria-expanded") == "true"
    assert trigger.locator(".sr-only").inner_text() == "Toggle Sidebar"
    badge = main.locator('[data-slot="sidebar-menu-badge"]').first
    button = badge.locator("xpath=preceding-sibling::*[1]")
    assert abs(g3_inline(t, badge)["r"] - g3_inline(t, button)["r"] + 4) < 1.5
    action = main.locator('[data-slot="sidebar-menu-action"][data-show-on-hover]')
    assert g3_style(action, "opacity") == "0"
    action.locator("..").hover()
    assert g3_style(action, "opacity") == "1"
    docs = main.locator('details[data-slot="collapsible"]')
    assert docs.evaluate("e => e.open") is True
    assert main.locator('[data-slot="sidebar-menu-sub-button"][data-active="true"]').is_visible()
    skeleton = main.locator('[data-slot="sidebar-menu-skeleton"]').first
    assert skeleton.locator('[data-slot="skeleton"]').count() == 2
    assert skeleton.evaluate("e => e.style.getPropertyValue('--skeleton-width')").endswith("%")
    rail = main.locator('[data-slot="sidebar-rail"]')
    assert rail.get_attribute("tabindex") == "-1" and rail.get_attribute("aria-label") == "Toggle Sidebar"
    g3_listen(page, "#sidebar-main [data-slot=sidebar]", ["sidebar:open", "sidebar:close"])
    trigger.click()
    assert sidebar.get_attribute("data-state") == "collapsed" and sidebar.get_attribute("data-collapsible") == "icon"
    assert trigger.get_attribute("aria-expanded") == "false"
    assert page.evaluate("localStorage.getItem('sidebar_state:sidebar-main')") == "false"
    assert g3_events(page) == [["sidebar:close", {"mobile": False}]]
    page.reload(wait_until="load")
    t.section("sidebar")
    assert sidebar.get_attribute("data-state") == "collapsed" and sidebar.get_attribute("data-collapsible") == "icon"
    t.settle(3000)
    assert round(g3_rect(container)["w"]) == 48
    home = main.locator('[data-slot="sidebar-menu-button"][data-tooltip="Home"]')
    assert round(g3_rect(home)["w"]) == 32
    assert g3_style(main.locator('[data-slot="sidebar-group-label"]').first, "opacity") == "0"
    home.hover()
    tip = page.locator('[data-slot="tooltip-content"][id^="sidebar-tooltip"]')
    tip.wait_for(state="visible")
    assert tip.inner_text() == "Home" and tip.get_attribute("role") == "tooltip"
    assert home.get_attribute("aria-describedby") == tip.get_attribute("id")
    assert g3_inline(t, tip)["x"] >= g3_inline(t, home)["r"]
    t.settle()
    t.shot("sidebar-collapsed", main)
    page.mouse.move(900, 20)
    assert tip.count() == 0
    g3_listen(page, "#sidebar-main [data-slot=sidebar]", ["sidebar:open", "sidebar:close"])
    page.locator("#sidebar-main-inset").click(position={"x": 400, "y": 300})
    page.keyboard.press("ControlOrMeta+b")
    assert sidebar.get_attribute("data-state") == "expanded"
    assert page.evaluate("localStorage.getItem('sidebar_state:sidebar-main')") == "true"
    t.settle(3000)
    rail.click(force=True)
    assert sidebar.get_attribute("data-state") == "collapsed"
    g3_keyboard(page)
    trigger.focus()
    page.keyboard.press("Enter")
    assert sidebar.get_attribute("data-state") == "expanded"
    assert g3_events(page) == [["sidebar:open", {"mobile": False}], ["sidebar:close", {"mobile": False}], ["sidebar:open", {"mobile": False}]]
    g3_listen(page, "#sidebar-main details", ["collapsible:close"])
    docs.locator("summary").click()
    page.wait_for_function("() => !document.querySelector('#sidebar-main details').open")
    floating = page.locator("#sidebar-floating")
    fsidebar = floating.locator('[data-slot="sidebar"]')
    fcontainer = fsidebar.locator('[data-slot="sidebar-container"]')
    assert g3_inline(t, fcontainer)["r"] <= g3_inline(t, floating)["r"] + 0.5 and g3_inline(t, fcontainer)["x"] > g3_inline(t, floating)["x"] + 100
    assert g3_style(fsidebar.locator('[data-slot="sidebar-inner"]'), "border-top-width") == "0px" and "0px 0px 0px 1px" in g3_style(fsidebar.locator('[data-slot="sidebar-inner"]'), "box-shadow")
    floating.locator('[data-slot="sidebar-trigger"]').click()
    assert fsidebar.get_attribute("data-collapsible") == "offcanvas"
    t.settle(3000)
    assert g3_inline(t, fcontainer)["x"] >= g3_inline(t, floating)["r"] - 1
    assert round(g3_rect(fsidebar.locator('[data-slot="sidebar-gap"]'))["w"]) == 0
    inset = page.locator("#sidebar-inset-demo")
    isidebar = inset.locator(':scope > [data-slot="sidebar"]')
    assert isidebar.get_attribute("data-state") == "collapsed" and isidebar.get_attribute("data-collapsible") == "icon"
    assert round(g3_rect(isidebar.locator(':scope > [data-slot="sidebar-container"]'))["w"]) == 66
    inset_main = inset.locator(':scope > [data-slot="sidebar-inset"]')
    assert g3_style(inset_main, "margin-top") == "8px" and g3_style(inset_main, "border-top-left-radius") != "0px"
    none = page.locator("#sidebar-none")
    assert none.is_visible() and round(g3_rect(none)["w"]) == 256
    t.settle(3000)
    t.shot("sidebar-expanded", main)
    t.shot("sidebar", section)


def check_sidebar_icon_group_label(t):
    page = t.page
    if t.mobile:
        t.skip("the icon mode is a desktop layout")
    out = page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const group = (label, n) => h("div", { "data-slot": "sidebar-group" },
            h("div", { "data-slot": "sidebar-group-label" }, label),
            h("ul", { "data-slot": "sidebar-menu" }, Array.from({ length: n }, (_, i) =>
              h("li", { "data-slot": "sidebar-menu-item" }, h("button", { "data-slot": "sidebar-menu-button", type: "button", "data-tooltip": `${label} ${i}` }, h("span", `${label} ${i}`))))))
          const wrap = h("div", { "data-slot": "sidebar-wrapper", id: "sidebar-icon-labels" },
            h("div", { "data-slot": "sidebar", "data-side": "left", "data-collapsible": "icon", "data-state": "collapsed" },
              h("div", { "data-slot": "sidebar-gap" }),
              h("div", { "data-slot": "sidebar-container" }, h("div", { "data-slot": "sidebar-inner" }, h("div", { "data-slot": "sidebar-content" }, group("One", 2), group("Two", 2))))),
            h("main", { "data-slot": "sidebar-inset" }))
          document.body.append(wrap)
          await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
          const last = wrap.querySelectorAll('[data-slot="sidebar-group"]')[0].querySelectorAll('[data-slot="sidebar-menu-button"]')[1]
          last.scrollIntoView({ block: "center" })
          const r = last.getBoundingClientRect()
          const hits = [0.5, 0.75, 0.9].map(f => last.contains(document.elementFromPoint(r.left + r.width / 2, r.top + r.height * f)))
          const state = wrap.querySelector('[data-slot="sidebar"]').getAttribute("data-collapsible")
          wrap.remove()
          return { hits, state, height: r.height }
        }"""
    )
    assert out["state"] == "icon" and out["height"] > 0, out
    assert out["hits"] == [True, True, True], ("the hidden label of the next group does not take clicks from the last menu button", out)


def check_sidebar_rtl(t):
    page = t.page
    t.section("sidebar")
    page.evaluate("() => { for (const id of ['sidebar-main', 'sidebar-floating']) document.getElementById(id).dir = 'rtl' }")
    main = page.locator("#sidebar-main")
    sidebar = main.locator(':scope > [data-slot="sidebar"]')
    container = sidebar.locator(':scope > [data-slot="sidebar-container"]')
    trigger = page.locator("#sidebar-main-trigger")
    if t.mobile:
        trigger.click()
        t.settle(3000)
        box = g3_rect(sidebar)
        assert round(box["r"]) == 390 and abs(box["w"] - 0.75 * 390) < 1, box
        assert g3_style(sidebar, "border-left-width") == "1px" and g3_style(sidebar, "border-right-width") == "0px"
        page.keyboard.press("Escape")
        page.wait_for_function("() => !document.querySelector('#sidebar-main [data-slot=sidebar]').hasAttribute('data-mobile')")
        return
    t.settle(3000)
    frame = g3_rect(main)
    box = g3_rect(container)
    inset = g3_rect(main.locator(':scope > [data-slot="sidebar-inset"]'))
    assert abs(box["r"] - frame["r"]) <= 1 and inset["r"] <= box["x"] + 1, (frame, box, inset)
    assert g3_style(container, "border-left-width") == "1px" and g3_style(container, "border-right-width") == "0px"
    rail = g3_rect(main.locator('[data-slot="sidebar-rail"]'))
    assert abs(rail["x"] + rail["w"] / 2 - box["x"]) <= 1, (rail, box)
    assert g3_style(main.locator('[data-slot="sidebar-rail"]'), "cursor") == "e-resize"
    trigger.click()
    t.settle(3000)
    box = g3_rect(container)
    assert round(box["w"]) == 48 and abs(box["r"] - frame["r"]) <= 1, box
    home = main.locator('[data-slot="sidebar-menu-button"][data-tooltip="Home"]')
    home.hover()
    tip = page.locator('[data-slot="tooltip-content"][id^="sidebar-tooltip"]')
    tip.wait_for(state="visible")
    assert g3_rect(tip)["r"] <= g3_rect(home)["x"], (g3_rect(tip), g3_rect(home))
    floating = page.locator("#sidebar-floating")
    fcontainer = floating.locator('[data-slot="sidebar-container"]')
    fframe = g3_rect(floating)
    assert abs(g3_rect(fcontainer)["x"] - fframe["x"]) <= 1, (g3_rect(fcontainer), fframe)
    floating.locator('[data-slot="sidebar-trigger"]').click()
    t.settle(3000)
    assert g3_rect(fcontainer)["r"] <= fframe["x"] + 1, (g3_rect(fcontainer), fframe)
    t.shot("sidebar-rtl", main)


def check_skeleton(t):
    page = t.page
    section = t.section("skeleton")
    sk = page.locator("#skeleton-avatar")
    assert g3_style(sk, "animation-name") == ("none" if t.reduced_motion else "pulse")
    muted = page.evaluate("() => { const p = document.createElement('p'); p.style.color = 'var(--muted)'; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c }")
    assert g3_style(page.locator("#skeleton-line-1"), "background-color") == muted
    assert g3_style(page.locator("#skeleton-line-1"), "border-top-left-radius") == "8px"
    assert round(g3_rect(sk)["w"]) == 48 and g3_style(sk, "border-top-left-radius") != "8px"
    assert section.locator('[data-slot="skeleton"]').count() >= 9


def check_spinner(t):
    page = t.page
    section = t.section("spinner")
    spinners = section.locator('[data-slot="spinner"]')
    first = spinners.first
    assert first.get_attribute("role") == "status" and first.get_attribute("aria-label") == "Loading" and first.get_attribute("aria-hidden") is None
    assert first.locator("path").count() == 1 and first.get_attribute("viewBox") == "0 0 24 24"
    assert g3_style(first, "animation-name") == "spin", "spinners keep turning under reduced motion"
    sizes = section.locator('[data-demo~="preview"]').nth(1).locator(':scope > svg[data-slot="spinner"]')
    assert [g3_style(sizes.nth(i), "width") for i in range(4)] == ["12px", "16px", "24px", "32px"]
    assert sizes.nth(3).get_attribute("aria-label") == "Loading page"
    quiet = section.locator('button [data-slot="spinner"]').first
    assert quiet.get_attribute("aria-hidden") == "true" and quiet.get_attribute("role") == "none"
    assert page.get_by_role("status", name="Loading").count() >= 4
    late = page.evaluate(
        """async () => {
          const { h } = await import('/clanker-ui.js')
          const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
          s.setAttribute('data-slot', 'spinner')
          document.querySelector('#spinner [data-demo~=preview]').append(s)
          await new Promise(r => setTimeout(r, 0))
          const out = [s.getAttribute('role'), s.childElementCount]
          s.remove()
          return out
        }"""
    )
    assert late == ["status", 1], late


def g3_table_rows(page):
    return page.evaluate("() => [...document.querySelectorAll('#table-data tbody tr')].map(r => [...r.cells].slice(1).map(c => c.textContent))")


def check_table(t):
    page = t.page
    section = t.section("table")
    invoices = page.locator("#table-invoices")
    assert g3_style(invoices, "caption-side") == "bottom"
    head = page.locator("#table-head-invoice")
    assert round(g3_rect(head)["h"]) == 40 and g3_style(head, "text-align") in ("start", "left")
    selected = invoices.locator('tr[data-state="selected"]')
    muted = page.evaluate("() => { const p = document.createElement('p'); p.style.color = 'var(--muted)'; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c }")
    assert g3_style(selected, "background-color") == muted
    assert g3_style(invoices.locator("tbody tr").first, "border-bottom-width") == "1px"
    assert g3_style(invoices.locator("tbody tr").last, "border-bottom-width") == "0px"
    footer = invoices.locator("tfoot")
    assert g3_style(footer, "font-weight") == "500"
    row = invoices.locator("tbody tr").nth(1)
    row.hover()
    page.wait_for_timeout(250)
    assert g3_style(row, "background-color") != "rgba(0, 0, 0, 0)"
    data = page.locator("#table-data")
    count = data.locator('[data-demo="table-footer"] p')
    assert len(g3_table_rows(page)) == 5 and count.inner_text() == "0 of 12 row(s) selected."
    prev, nxt = data.get_by_role("button", name="Previous"), data.get_by_role("button", name="Next")
    assert prev.is_disabled() and nxt.is_enabled()
    email = data.locator('th:has(button[data-sort-key="email"])')
    amount = data.locator('th:has(button[data-sort-key="amount"])')
    assert email.get_attribute("aria-sort") is None
    email.locator("button").click()
    assert email.get_attribute("aria-sort") == "ascending"
    assert g3_table_rows(page)[0][1] == "abe45@example.com"
    assert email.locator("svg").get_attribute("data-lucide") == "arrow-up"
    email.locator("button").click()
    assert email.get_attribute("aria-sort") == "descending" and g3_table_rows(page)[0][1] == "silas22@example.com"
    email.locator("button").click()
    assert email.get_attribute("aria-sort") is None and g3_table_rows(page)[0][1] == "ken99@example.com"
    g3_keyboard(page)
    amount.locator("button").focus()
    page.keyboard.press("Enter")
    assert amount.get_attribute("aria-sort") == "ascending" and g3_table_rows(page)[0][2] == "$95.00"
    page.keyboard.press("Space")
    assert amount.get_attribute("aria-sort") == "descending" and g3_table_rows(page)[0][2] == "$999.00"
    assert email.get_attribute("aria-sort") is None
    boxes = data.locator("tbody [data-slot=checkbox]")
    boxes.nth(0).check()
    assert data.locator("tbody tr").nth(0).get_attribute("data-state") == "selected"
    assert count.inner_text() == "1 of 12 row(s) selected."
    all_box = data.locator("thead [data-slot=checkbox]")
    assert all_box.get_attribute("aria-checked") == "mixed"
    all_box.check()
    assert count.inner_text() == "5 of 12 row(s) selected."
    assert all_box.get_attribute("aria-checked") == "true"
    boxes.nth(1).focus()
    page.keyboard.press("Space")
    assert count.inner_text() == "4 of 12 row(s) selected."
    nxt.click()
    assert data.locator('[data-demo="table-page"]').inner_text() == "Page 2 of 3"
    assert all_box.is_checked() is False and prev.is_enabled()
    nxt.click()
    assert nxt.is_disabled() and len(g3_table_rows(page)) == 2
    data.get_by_role("searchbox", name="Filter emails").fill("ken")
    assert len(g3_table_rows(page)) == 1 and count.inner_text() == "0 of 1 row(s) selected."
    assert data.locator('[data-demo="table-page"]').inner_text() == "Page 1 of 1"
    data.get_by_role("searchbox", name="Filter emails").fill("zzz")
    assert data.locator("tbody").inner_text().strip() == "No results."
    data.get_by_role("searchbox", name="Filter emails").fill("")
    assert count.inner_text() == "4 of 12 row(s) selected."
    assert email.locator("svg").get_attribute("data-lucide") == "arrow-up-down"
    t.shot("table", section)
    row = data.locator("tbody tr").first
    row.locator("[data-dropdown-menu-trigger]").click()
    menu = row.locator("[data-slot=dropdown-menu-content]")
    menu.wait_for(state="visible")
    assert menu.locator("[data-slot=dropdown-menu-label]").inner_text() == "Actions"
    t.settle()
    t.shot("table-row-actions", page)
    menu.get_by_role("menuitem", name="Copy payment ID").click()
    page.locator("[data-slot=toast]").filter(has_text="Payment ID copied").wait_for()
    menu.wait_for(state="hidden")
    assert row.locator("[data-dropdown-menu-trigger]").evaluate("e => document.activeElement === e")
    columns = data.get_by_role("button", name="Columns")
    columns.click()
    status = page.get_by_role("menuitemcheckbox", name="Status")
    assert status.get_attribute("aria-checked") == "true"
    status.click()
    assert [th.inner_text().strip() for th in data.locator("thead th").all()] == ["", "Email", "Amount", "Actions"]
    assert len(g3_table_rows(page)[0]) == 3
    assert status.evaluate("e => e.closest('[data-slot=dropdown-menu-content]').matches(':popover-open')"), "checkbox items keep the menu open, as in Base UI"
    page.get_by_role("menuitemcheckbox", name="Status").click()
    assert data.locator("thead th").count() == 5


def check_tabs(t):
    page = t.page
    section = t.section("tabs")
    root = page.locator("#tabs-demo")
    tabs = root.locator('[data-slot="tabs-trigger"]')
    panels = root.locator('[data-slot="tabs-content"]')
    assert root.locator('[data-slot="tabs-list"]').get_attribute("role") == "tablist"
    assert root.locator('[data-slot="tabs-list"]').get_attribute("aria-orientation") == "horizontal"
    assert [tabs.nth(i).get_attribute("aria-selected") for i in range(4)] == ["true", "false", "false", "false"]
    assert [tabs.nth(i).get_attribute("tabindex") for i in range(4)] == ["0", "-1", "-1", "-1"]
    assert tabs.first.get_attribute("role") == "tab" and tabs.first.get_attribute("aria-controls") == panels.first.get_attribute("id")
    assert panels.first.get_attribute("role") == "tabpanel" and panels.first.get_attribute("aria-labelledby") == tabs.first.get_attribute("id")
    assert panels.first.is_visible() and not panels.nth(1).is_visible()
    assert round(g3_rect(root.locator('[data-slot="tabs-list"]'))["h"]) == 32
    g3_listen(page, "#tabs-demo", ["tabs:change"])
    tabs.nth(1).click()
    assert tabs.nth(1).get_attribute("data-state") == "active" and panels.nth(1).is_visible() and not panels.first.is_visible()
    tabs.nth(1).click()
    assert g3_events(page) == [["tabs:change", {"value": "analytics"}]]
    g3_keyboard(page)
    tabs.nth(1).focus()
    selected = lambda: [tabs.nth(i).get_attribute("aria-selected") for i in range(4)].index("true")
    focused = lambda: tabs.evaluate_all("l => l.indexOf(document.activeElement)")
    page.keyboard.press(g3_key(t, "ArrowRight"))
    assert (focused(), selected()) == (2, 1), "an arrow key moves focus only, as in Base UI"
    page.keyboard.press("Enter")
    assert selected() == 2
    page.keyboard.press("End")
    assert (focused(), selected()) == (3, 2)
    page.keyboard.press("Space")
    assert selected() == 3
    page.keyboard.press(g3_key(t, "ArrowRight"))
    assert (focused(), selected()) == (0, 3)
    page.keyboard.press("Enter")
    page.keyboard.press(g3_key(t, "ArrowLeft"))
    page.keyboard.press("Home")
    page.keyboard.press("ArrowDown")
    assert (focused(), selected()) == (0, 0)
    assert [e[1]["value"] for e in g3_events(page)] == ["reports", "settings", "overview"]
    assert g3_style(tabs.nth(0), "outline-style") == ("none" if t.engine == "firefox" else "solid"), "Base UI focuses in a microtask: Firefox keeps the ring state of the scripted focus"
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.getAttribute('role')") == "tabpanel"
    ring = page.evaluate("() => { const s = getComputedStyle(document.activeElement); return [document.activeElement.matches(':focus-visible'), s.outlineStyle] }")
    assert ring == [True, "none"], ring
    t.a11y()
    ring = page.evaluate("() => { const s = getComputedStyle(document.activeElement); return [document.activeElement.matches(':focus-visible'), s.outlineStyle, s.outlineWidth] }")
    assert ring == [True, "solid", "3px"], ring
    icons = page.locator("#tabs-icons")
    it = icons.locator('[data-slot="tabs-trigger"]')
    assert it.nth(2).is_disabled() and round(g3_rect(it.first.locator("svg"))["w"]) == 16
    it.nth(1).focus()
    page.keyboard.press("ArrowRight")
    assert it.nth(0).evaluate("e => e === document.activeElement") and it.nth(1).get_attribute("aria-selected") == "false"
    page.keyboard.press("Enter")
    assert it.nth(0).get_attribute("aria-selected") == "true"
    line = page.locator("#tabs-line")
    lt = line.locator('[data-slot="tabs-trigger"]')
    t.settle()
    assert lt.first.evaluate("e => getComputedStyle(e, '::after').opacity") == "1"
    assert lt.nth(1).evaluate("e => getComputedStyle(e, '::after').opacity") == "0"
    assert g3_style(line.locator('[data-slot="tabs-list"]'), "background-color") == "rgba(0, 0, 0, 0)"
    vertical = page.locator("#tabs-vertical")
    vt = vertical.locator('[data-slot="tabs-trigger"]')
    assert vertical.locator('[data-slot="tabs-list"]').get_attribute("aria-orientation") == "vertical"
    assert g3_rect(vt.nth(1))["y"] > g3_rect(vt.nth(0))["y"]
    vt.first.focus()
    page.keyboard.press("ArrowRight")
    assert vt.first.get_attribute("aria-selected") == "true"
    page.keyboard.press("ArrowDown")
    assert vt.nth(1).evaluate("e => e === document.activeElement") and vt.first.get_attribute("aria-selected") == "true"
    page.keyboard.press("Enter")
    assert vt.nth(1).get_attribute("aria-selected") == "true"
    assert vertical.locator('[data-slot="tabs-content"][data-value="password"]').is_visible()
    root.evaluate("e => e.dataset.activation = 'automatic'")
    tabs.nth(0).focus()
    page.keyboard.press(g3_key(t, "ArrowRight"))
    assert (focused(), selected()) == (1, 1), "data-activation=automatic selects on focus"
    t.shot("tabs", section)


G3_TABS = """async () => {
  const { h } = await import("/clanker-ui.js")
  const names = ["Overview", "Analytics", "Reports", "Notifications", "Settings", "Billing", "Members"]
  const tabs = (id, variant) => h("div", { id, "data-slot": "tabs", "data-default-value": "overview" },
    h("div", { "data-slot": "tabs-list", "data-variant": variant }, names.map(n => h("button", { "data-slot": "tabs-trigger", "data-value": n.toLowerCase() }, n, h("span", { "data-slot": "badge", "data-variant": "secondary" }, "12")))),
    names.map(n => h("div", { "data-slot": "tabs-content", "data-value": n.toLowerCase() }, n)))
  const grid = h("div", tabs("tabs-wide-grid"))
  Object.assign(grid.style, { display: "grid", gridTemplateColumns: "1fr" })
  const host = h("div", { id: "tabs-wide" }, tabs("tabs-wide-default"), tabs("tabs-wide-line", "line"), grid)
  Object.assign(host.style, { display: "flex", flexDirection: "column", gap: "1rem", width: "300px" })
  document.getElementById("tabs").append(host)
}"""


def check_tabs_overflow(t):
    page = t.page
    t.section("tabs")
    page.evaluate(G3_TABS)
    host = page.locator("#tabs-wide")
    page.wait_for_function("() => document.querySelectorAll('#tabs-wide [role=tablist]').length === 3")
    edge = g3_rect(host)
    for id in ["tabs-wide-default", "tabs-wide-line", "tabs-wide-grid"]:
        root = page.locator(f"#{id}")
        tabs_list = root.locator("[data-slot=tabs-list]")
        box = g3_rect(tabs_list)
        assert box["x"] >= edge["x"] - 0.5 and box["r"] <= edge["r"] + 0.5, (id, box, edge)
        assert g3_rect(root)["w"] <= edge["w"] + 0.5, (id, g3_rect(root), edge)
        size = tabs_list.evaluate("e => ({ sw: e.scrollWidth, cw: e.clientWidth, sh: e.scrollHeight, ch: e.clientHeight, oh: e.offsetHeight, y: getComputedStyle(e).overflowY })")
        assert size["sw"] > size["cw"] and size["oh"] == size["ch"], (id, size)
        assert size["sh"] <= size["ch"] or size["y"] == "hidden", (id, size)
        squeezed = root.locator("[data-slot=tabs-trigger]").evaluate_all("els => els.filter(e => e.scrollWidth > e.clientWidth + 0.5).map(e => e.textContent)")
        assert squeezed == [], (id, squeezed)
    line = page.locator("#tabs-wide-line [data-slot=tabs-list]")
    assert line.evaluate("e => e.scrollHeight <= e.clientHeight"), "the line underline is clipped"
    reach = """e => { const l = e.closest('[data-slot=tabs-list]').getBoundingClientRect(), r = e.getBoundingClientRect(); return Math.min(r.left - l.left, l.right - r.right) }"""
    triggers = page.locator("#tabs-wide-default [data-slot=tabs-trigger]")
    g3_keyboard(page)
    triggers.first.focus()
    for i in range(1, 7):
        page.keyboard.press(g3_key(t, "ArrowRight"))
        assert page.evaluate("() => document.activeElement.dataset.value") == triggers.nth(i).get_attribute("data-value")
        gap = page.evaluate(f"() => ({reach})(document.activeElement)")
        assert gap >= 2, (i, gap)
    page.keyboard.press("Home")
    assert page.evaluate(f"() => ({reach})(document.activeElement)") >= 2
    page.keyboard.press("End")
    assert page.evaluate(f"() => ({reach})(document.activeElement)") >= 2
    page.locator("#tabs-wide-line").scroll_into_view_if_needed()
    spot = page.evaluate(
        """() => {
          const l = document.querySelector("#tabs-wide-line [data-slot=tabs-list]").getBoundingClientRect()
          const t = [...document.querySelectorAll("#tabs-wide-line [data-slot=tabs-trigger]")].find(e => { const r = e.getBoundingClientRect(); return Math.min(r.right, l.right) - Math.max(r.left, l.left) > 10 && (r.right > l.right + 1 || r.left < l.left - 1) })
          const r = t.getBoundingClientRect()
          return { value: t.dataset.value, x: (Math.max(r.left, l.left) + Math.min(r.right, l.right)) / 2, y: r.top + r.height / 2 }
        }"""
    )
    page.mouse.click(spot["x"], spot["y"])
    clicked = page.locator(f"#tabs-wide-line [data-slot=tabs-trigger][data-value={spot['value']}]")
    assert clicked.get_attribute("aria-selected") == "true", spot
    assert clicked.evaluate(reach) >= 2
    assert g3_style(page.locator("#tabs-vertical [data-slot=tabs-list]"), "overflow-x") == "visible"
    t.shot("tabs-overflow", host)


G3_TABS_SELECTED = """async () => {
  const { h } = await import("/clanker-ui.js")
  const names = ["Overview", "Analytics", "Reports", "Notifications", "Settings", "Billing", "Members"]
  const tabs = (id, value) => h("div", { id, "data-slot": "tabs", "data-default-value": value },
    h("div", { "data-slot": "tabs-list" }, names.map(n => h("button", { "data-slot": "tabs-trigger", "data-value": n.toLowerCase() }, n, h("span", { "data-slot": "badge", "data-variant": "secondary" }, "12")))),
    names.map(n => h("div", { "data-slot": "tabs-content", "data-value": n.toLowerCase() }, n)))
  const later = h("div", { id: "tabs-selected-later", hidden: true }, tabs("tabs-selected-hidden", "members"))
  const scaled = h("div", tabs("tabs-selected-scaled", "overview"))
  Object.assign(scaled.style, { transform: "scale(0.5)", transformOrigin: "top" })
  const host = h("div", { id: "tabs-selected" }, h("input", { id: "tabs-selected-before", "aria-label": "Before" }), tabs("tabs-selected-load", "members"), later, scaled)
  Object.assign(host.style, { display: "flex", flexDirection: "column", gap: "1rem", width: "300px" })
  document.getElementById("tabs").append(host)
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
}"""


G3_REACH = """e => {
  const list = e.closest("[data-slot=tabs-list]"), l = list.getBoundingClientRect(), r = e.getBoundingClientRect()
  return Math.min(r.left - l.left, l.right - r.right) / (l.width / list.offsetWidth)
}"""


def check_tabs_overflow_selected(t):
    page = t.page
    t.section("tabs")
    page.evaluate(G3_TABS_SELECTED)
    selected = lambda id: page.locator(f"#{id} [data-slot=tabs-trigger][data-state=active]")
    load = selected("tabs-selected-load")
    assert load.get_attribute("data-value") == "members"
    assert load.evaluate(G3_REACH) >= 2, ("selected tab out of view at load", load.evaluate(G3_REACH))
    page.evaluate("async () => { document.getElementById('tabs-selected-later').hidden = false; await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))) }")
    late = selected("tabs-selected-hidden")
    assert late.evaluate(G3_REACH) >= 2, ("selected tab out of view after show", late.evaluate(G3_REACH))
    stop = "() => { const a = document.activeElement; return [a.dataset.slot ?? a.id, a.dataset.value ?? a.getAttribute('role')] }"
    page.locator("#tabs-selected-before").focus()
    page.keyboard.press("Tab")
    assert page.evaluate(stop) == ["tabs-trigger", "members"], page.evaluate(stop)
    page.keyboard.press("Tab")
    assert page.evaluate(stop) == ["tabs-content", "members"], page.evaluate(stop)
    page.keyboard.press("Shift+Tab")
    assert page.evaluate(stop) == ["tabs-trigger", "members"], page.evaluate(stop)
    page.keyboard.press("Shift+Tab")
    assert page.evaluate(stop) == ["tabs-selected-before", None], page.evaluate(stop)
    triggers = page.locator("#tabs-selected-scaled [data-slot=tabs-trigger]")
    g3_keyboard(page)
    triggers.first.focus()
    for i in range(1, 7):
        page.keyboard.press(g3_key(t, "ArrowRight"))
        gap = page.evaluate(f"() => ({G3_REACH})(document.activeElement)")
        assert gap >= 2, ("scaled list", i, gap)
    t.shot("tabs-overflow-selected", page.locator("#tabs-selected"))


G3_TABS_LATE = """async () => {
  const { h } = await import("/clanker-ui.js")
  const names = ["one", "two", "three"]
  const fill = value => h("div", { "data-fill": value, style: { height: "600px" } }, value)
  const root = h("div", { id: "tabs-late", "data-slot": "tabs", "data-default-value": "one" },
    h("div", { "data-slot": "tabs-list" }, names.map(n => h("button", { "data-slot": "tabs-trigger", "data-value": n }, n))),
    names.map(n => h("div", { "data-slot": "tabs-content", "data-value": n }, fill(n))))
  root.addEventListener("tabs:change", event => {
    const panel = root.querySelector(`[data-slot=tabs-content][data-value="${event.detail.value}"]`)
    panel.replaceChildren()
    queueMicrotask(() => panel.replaceChildren(fill(event.detail.value)))
  })
  document.documentElement.style.overflowAnchor = "none"
  document.body.append(root)
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
  scrollTo(0, document.documentElement.scrollHeight)
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
}"""

G3_FRAMES = "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"


def check_tabs_change_scroll(t):
    page = t.page
    page.evaluate(G3_TABS_LATE)
    top = page.evaluate("() => scrollY")
    assert top > 600
    two = page.locator("#tabs-late [data-slot=tabs-trigger][data-value=two]")
    box = g3_rect(two)
    assert 0 < box["y"] and box["b"] < page.viewport_size["height"], box
    page.mouse.click(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
    page.evaluate(G3_FRAMES)
    assert two.get_attribute("aria-selected") == "true"
    assert page.locator("#tabs-late [data-fill=two]").count() == 1
    assert page.evaluate("() => scrollY") == top
    if t.engine == "firefox":
        return
    two.focus()
    page.keyboard.press(g3_key(t, "ArrowRight"))
    page.keyboard.press("Enter")
    page.evaluate(G3_FRAMES)
    assert page.locator("#tabs-late [data-slot=tabs-trigger][data-value=three]").get_attribute("aria-selected") == "true"
    assert page.evaluate("() => scrollY") == top


def check_layout_overflow(t):
    page = t.page
    ids = ["accordion", "alert", "aspect-ratio", "avatar", "badge", "breadcrumb", "card", "carousel", "collapsible", "direction", "empty", "item", "pagination", "progress", "resizable", "scroll-area", "separator", "sidebar", "skeleton", "spinner", "table", "tabs"]
    outside = page.evaluate(
        """ids => {
          const out = []
          const clipped = (el, stop) => {
            for (let p = el.parentElement; p && p !== stop; p = p.parentElement) {
              const s = getComputedStyle(p)
              if (s.overflowX !== 'visible' || s.position === 'fixed') return true
            }
            return false
          }
          for (const id of ids) {
            const section = document.getElementById(id)
            for (const el of section.querySelectorAll('*')) {
              const r = el.getBoundingClientRect()
              if (!r.width || !r.height || getComputedStyle(el).position === 'fixed') continue
              if ((r.right > innerWidth + 0.5 || r.left < -0.5) && !clipped(el, section)) out.push(id + ' ' + (el.id || el.dataset.slot || el.tagName) + ' ' + Math.round(r.left) + '..' + Math.round(r.right))
            }
          }
          return out
        }""",
        ids,
    )
    assert outside == [], outside[:10]


def check_carousel_loop_false(t):
    page = t.page
    t.section("carousel")
    disabled = page.evaluate("""async () => {
      const { h } = await import("/clanker-ui.js")
      const items = ["1", "2", "3"].map(n => h("div", { "data-slot": "carousel-item" }, n))
      const host = h("div", { "data-slot": "carousel", "data-loop": "false" }, h("div", { "data-slot": "carousel-content" }, h("div", null, ...items)), h("button", { "data-slot": "carousel-previous" }), h("button", { "data-slot": "carousel-next" }))
      document.querySelector("#carousel [data-demo~=preview]").append(host)
      await new Promise(r => setTimeout(() => requestAnimationFrame(() => requestAnimationFrame(r)), 20))
      const out = [host.querySelector("[data-slot=carousel-previous]").disabled, host.querySelector("[data-slot=carousel-next]").disabled]
      host.remove()
      return out
    }""")
    assert disabled == [True, False], ('data-loop="false" does not loop', disabled)


def check_tabs_shared_panel(t):
    page = t.page
    result = page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const tabs = h("div", { "data-slot": "tabs", "data-default-value": "all" },
            h("div", { "data-slot": "tabs-list" }, ["all", "paid", "overdue"].map(v => h("button", { "data-slot": "tabs-trigger", "data-value": v }, v))),
            h("div", { "data-slot": "tabs-content", id: "shared-panel" }, "rows"))
          document.body.prepend(tabs)
          await new Promise(r => setTimeout(r, 0))
          const panel = tabs.querySelector('[data-slot="tabs-content"]')
          const triggers = [...tabs.querySelectorAll('[data-slot="tabs-trigger"]')]
          const state = () => [panel.hidden, panel.getAttribute("role"), panel.getAttribute("aria-labelledby") === tabs.querySelector('[aria-selected="true"]').id]
          const before = [...state(), triggers.map(b => b.getAttribute("aria-controls"))]
          triggers[2].click()
          const after = [...state(), tabs.querySelector('[aria-selected="true"]').dataset.value]
          tabs.remove()
          return { before, after }
        }"""
    )
    assert result["before"] == [False, "tabpanel", True, ["shared-panel"] * 3], result
    assert result["after"] == [False, "tabpanel", True, "overdue"], result


def check_pagination_disabled(t):
    page = t.page
    result = page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const nav = h("nav", { "data-slot": "pagination", "aria-label": "pagination" }, h("ul", { "data-slot": "pagination-content" },
            h("li", { "data-slot": "pagination-item" }, h("a", { "data-slot": "pagination-link", "data-pagination-previous": "", "data-size": "default", href: "#page-0", "aria-disabled": "true" }, "Previous")),
            h("li", { "data-slot": "pagination-item" }, h("a", { "data-slot": "pagination-link", href: "#page-2" }, "2"))))
          document.body.prepend(nav)
          await new Promise(r => setTimeout(r, 0))
          const [prev, next] = nav.querySelectorAll("a")
          const hash = location.hash
          prev.click()
          const out = [getComputedStyle(prev).opacity, getComputedStyle(prev).pointerEvents, location.hash === hash, getComputedStyle(next).opacity]
          nav.remove()
          return out
        }"""
    )
    assert result == ["0.5", "none", True, "1"], result


def check_alert_action_room(t):
    result = t.page.evaluate(
        """async () => {
          const { h, icon } = await import("/clanker-ui.js")
          const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
          const out = []
          for (const width of [358, 640]) {
            for (const [label, size] of [["Enable", "xs"], ["View incident", "sm"]]) {
              const host = h("div", { style: { width: width + "px" } },
                h("div", { "data-slot": "alert" }, icon("circle-alert"),
                  h("div", { "data-slot": "alert-title" }, "Elevated error rates on the payments API in the eu-west region"),
                  h("div", { "data-slot": "alert-description" }, "Card payments can fail or take longer than usual while we investigate."),
                  h("div", { "data-slot": "alert-action" }, h("button", { type: "button", "data-slot": "button", "data-size": size, "data-variant": "outline" }, label))))
              document.body.prepend(host)
              await frame()
              const alert = host.firstChild
              const box = s => alert.querySelector(s).getBoundingClientRect()
              const action = box('[data-slot="alert-action"]')
              const hit = r => r.left < action.right && r.right > action.left && r.top < action.bottom && r.bottom > action.top
              out.push([width, label, hit(box('[data-slot="alert-title"]')), hit(box('[data-slot="alert-description"]')), getComputedStyle(alert).paddingInlineEnd])
              host.remove()
            }
          }
          return out
        }"""
    )
    for width, label, title, description, pad in result:
        assert not title and not description, (width, label, title, description, pad)
        if label == "Enable":
            assert pad == "72px", (width, pad)


def check_tabs_value_from_code(t):
    result = t.page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const task = () => new Promise(r => setTimeout(r, 0))
          const tabs = h("div", { "data-slot": "tabs", "data-value": "paid" },
            h("div", { "data-slot": "tabs-list" }, ["all", "paid", "overdue"].map(v => h("button", { "data-slot": "tabs-trigger", "data-value": v }, v))),
            ["all", "paid", "overdue"].map(v => h("div", { "data-slot": "tabs-content", "data-value": v }, v)))
          const events = []
          tabs.addEventListener("tabs:change", e => events.push(e.detail.value))
          document.body.prepend(tabs)
          await task()
          const active = () => [tabs.querySelector('[aria-selected="true"]')?.dataset.value, [...tabs.querySelectorAll('[data-slot="tabs-content"]')].filter(p => !p.hidden).map(p => p.dataset.value).join(), tabs.dataset.value]
          const out = { init: active() }
          tabs.dataset.value = "overdue"
          await task()
          out.code = active()
          tabs.dataset.value = "nope"
          await task()
          out.unknown = active()
          tabs.querySelector('[data-value="all"]').click()
          out.click = active()
          out.events = events
          tabs.remove()
          return out
        }"""
    )
    assert result["init"] == ["paid", "paid", "paid"], result
    assert result["code"] == ["overdue", "overdue", "overdue"], result
    assert result["unknown"][:2] == ["overdue", "overdue"], result
    assert result["click"] == ["all", "all", "all"], result
    assert result["events"] == ["all"], result
