COLOR = """expr => {
  const p = document.createElement("p")
  p.style.color = expr
  document.body.append(p)
  const c = getComputedStyle(p).color
  p.remove()
  return c
}"""

STYLE = """async (e, [p, s]) => {
  const running = e.getAnimations({ subtree: true }).filter(a => a.effect?.getComputedTiming().endTime !== Infinity)
  await Promise.all(running.map(a => a.finished.catch(() => {})))
  return getComputedStyle(e, s).getPropertyValue(p)
}"""


EXIT = "sel => { const e = document.querySelector(sel); return [e.open ?? e.matches(':popover-open'), Number(getComputedStyle(e).opacity)] }"


def no_flash(frames):
    started = False
    for shown, opacity in frames:
        if not shown:
            return
        if opacity < 1:
            started = True
        assert not (started and opacity == 1), f"exit animation flashes back to full opacity: {frames}"
    raise AssertionError(f"popup still open after the exit animation: {frames}")


def spike(t):
    response = t.page.goto(t.base_url + "/test/spike/index.html", wait_until="load")
    assert response is not None and response.status == 200, f"spike page returned {response and response.status}"
    t.page.wait_for_function("() => document.querySelector('[data-slot=dropdown-menu-content]')?.getAttribute('role') === 'menu'")


def color(t, expr):
    return t.page.evaluate(COLOR, expr)


def style(loc, prop, pseudo=None):
    return loc.evaluate(STYLE, [prop, pseudo])


def probe(t, name):
    return t.page.locator(f'[data-probe="{name}"]')


def near(a, b, tolerance=0.5):
    return abs(a - b) <= tolerance


def check_spike_button(t):
    spike(t)
    page = t.page
    section = t.section("button")
    outline = probe(t, "button-outline")
    box = outline.bounding_box()
    assert near(box["height"], 32)
    assert style(outline, "border-top-left-radius") == "10px"
    assert near(probe(t, "button-size-xs").bounding_box()["height"], 24)
    assert near(probe(t, "button-size-sm").bounding_box()["height"], 28)
    assert near(probe(t, "button-size-lg").bounding_box()["height"], 36)
    assert near(probe(t, "button-size-icon").bounding_box()["width"], 32)
    assert style(probe(t, "button-size-sm"), "border-top-left-radius") == "8px"
    default = probe(t, "button-default")
    assert style(default, "background-color") == color(t, "var(--primary)")
    destructive = probe(t, "button-destructive")
    assert style(destructive, "background-color") == color(t, "color-mix(in oklab, var(--destructive) 10%, transparent)" if t.theme == "light" else "color-mix(in oklab, var(--destructive) 20%, transparent)")
    assert style(destructive, "color") == color(t, "var(--destructive)")
    assert style(probe(t, "button-disabled-outline"), "opacity") == "0.5"
    default.hover()
    expected = color(t, "color-mix(in oklab, var(--primary) 80%, transparent)")
    page.wait_for_function("([e, c]) => getComputedStyle(e).backgroundColor === c", arg=[default.element_handle(), expected])
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    rest = outline.bounding_box()["y"]
    page.mouse.down()
    page.wait_for_function("([e, y]) => Math.abs(e.getBoundingClientRect().y - y - 1) < 0.01", arg=[outline.element_handle(), rest])
    page.mouse.up()
    page.wait_for_function("([e, y]) => Math.abs(e.getBoundingClientRect().y - y) < 0.01", arg=[outline.element_handle(), rest])
    trigger = probe(t, "dialog-trigger")
    assert trigger.get_attribute("aria-haspopup") == "dialog"
    tb = trigger.bounding_box()
    page.mouse.move(tb["x"] + 5, tb["y"] + 5)
    page.mouse.down()
    page.wait_for_timeout(250)
    assert style(trigger, "translate") in ("none", "0px")
    page.mouse.up()
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('[data-probe=dialog-content]').open")
    page.keyboard.press("Tab")
    outline.focus()
    assert outline.evaluate("e => e.matches(':focus-visible')")
    assert "3px" in style(outline, "box-shadow")
    assert style(outline, "border-top-color") == color(t, "var(--ring)" if t.theme == "light" else "var(--input)")
    t.shot(target=section)


def check_spike_card_and_field(t):
    spike(t)
    card = probe(t, "card")
    t.section("card")
    assert style(card, "border-top-left-radius") == "14px"
    assert "1px" in style(card, "box-shadow")
    assert style(card, "padding-top") == "16px" and style(card, "padding-bottom") == "0px"
    footer = probe(t, "card-footer")
    assert style(footer, "border-top-width") == "1px" and style(footer, "padding-top") == "16px"
    assert style(probe(t, "card-sm"), "padding-top") == "12px"
    assert style(probe(t, "card-sm-title"), "font-size") == "14px"
    action = probe(t, "card-action").bounding_box()
    title = probe(t, "card-title").bounding_box()
    assert near(action["y"], title["y"], 2) and (action["x"] > title["x"]) != t.rtl
    t.shot("card", probe(t, "card"))
    t.section("field")
    assert style(probe(t, "field-legend"), "font-size") == "16px"
    assert style(probe(t, "field-label"), "font-weight") == "500"
    assert style(probe(t, "field-group"), "row-gap") == "20px"
    assert style(probe(t, "field"), "flex-direction") == "column"
    assert style(probe(t, "field-horizontal"), "flex-direction") == "row"
    assert style(probe(t, "field-description-set"), "margin-top") == "-6px"
    line = probe(t, "field-separator-line").bounding_box()
    assert near(line["height"], 1)
    t.shot("field", probe(t, "field-group"))


def check_spike_dialog(t):
    spike(t)
    page = t.page
    t.section("dialog")
    probe(t, "dialog-trigger").click()
    content = probe(t, "dialog-content")
    page.wait_for_function("e => e.open && e.dataset.state === 'open'", arg=content.element_handle())
    t.settle()
    assert style(content, "border-top-left-radius") == "14px"
    assert style(content, "background-color") == color(t, "var(--popover)")
    assert style(content, "background-color", "::backdrop") == color(t, "color-mix(in oklab, #000 10%, transparent)")
    box = content.bounding_box()
    vw = page.viewport_size["width"]
    assert near(box["width"], min(384, vw - 32), 1)
    assert near(box["x"] + box["width"] / 2, vw / 2, 1)
    footer = probe(t, "dialog-footer").bounding_box()
    assert near(footer["y"] + footer["height"], box["y"] + box["height"], 1.5), (footer, box)
    close = content.locator(':scope > [data-slot="dialog-close"]')
    cb = close.bounding_box()
    assert near(cb["width"], 28) and near(cb["height"], 28)
    assert near(cb["y"] - box["y"], 8)
    assert near(cb["x"] - box["x"], 8) if t.rtl else near(box["x"] + box["width"] - cb["x"] - cb["width"], 8)
    t.shot("dialog-open", content)
    frames = t.paint(EXIT, lambda: page.keyboard.press("Escape"), '[data-probe="dialog-content"]', ms=400)
    no_flash(frames)
    page.wait_for_function("e => !e.open", arg=content.element_handle())
    assert content.get_attribute("data-state") == "closed"


def check_spike_dropdown_menu(t):
    spike(t)
    page = t.page
    t.section("dropdown-menu")
    probe(t, "menu-trigger").click()
    content = probe(t, "menu-content")
    page.wait_for_function("e => e.matches(':popover-open') && e.dataset.state === 'open' && e.dataset.side", arg=content.element_handle())
    t.settle()
    assert style(content, "border-top-left-radius") == "10px"
    assert style(content, "padding-top") == "4px"
    assert near(content.bounding_box()["width"], 160)
    assert style(content, "animation-name") == ("none" if t.reduced_motion else "enter")
    item = probe(t, "menu-item")
    assert near(item.bounding_box()["height"], 28)
    assert style(probe(t, "menu-label"), "font-size") == "12px"
    assert near(probe(t, "menu-separator").bounding_box()["height"], 1)
    assert style(probe(t, "menu-item-disabled"), "opacity") == "0.5"
    item.hover()
    page.wait_for_function("([e, c]) => getComputedStyle(e).backgroundColor === c", arg=[item.element_handle(), color(t, "var(--accent)")])
    sub_trigger = probe(t, "menu-sub-trigger")
    sub_trigger.hover()
    sub = probe(t, "menu-sub-content")
    page.wait_for_function("e => e.matches(':popover-open') && e.dataset.state === 'open'", arg=sub.element_handle())
    t.settle()
    assert style(sub_trigger, "background-color") == color(t, "var(--accent)")
    assert style(sub, "min-width") == "96px"
    assert "rgba(0, 0, 0, 0.1) 0px 10px 15px -3px" in style(sub, "box-shadow")
    chevron = sub_trigger.locator(":scope > svg").last
    cb, tb = chevron.bounding_box(), sub_trigger.bounding_box()
    assert cb["x"] < tb["x"] + 12 if t.rtl else cb["x"] + cb["width"] > tb["x"] + tb["width"] - 12
    t.shot("menu-open", content)
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    page.wait_for_function("e => !e.matches(':popover-open')", arg=content.element_handle())
    probe(t, "menu-trigger").click()
    page.wait_for_function("e => e.matches(':popover-open')", arg=content.element_handle())
    t.settle()
    frames = t.paint(EXIT, lambda: page.keyboard.press("Escape"), '[data-probe="menu-content"]', ms=400)
    no_flash(frames)
    probe(t, "menu-check-trigger").click()
    checks = probe(t, "menu-check-content")
    page.wait_for_function("e => e.matches(':popover-open')", arg=checks.element_handle())
    t.settle()
    visible = checks.evaluate("e => [...e.querySelectorAll('[data-slot=dropdown-menu-checkbox-item]')].map(i => [...i.querySelectorAll('svg')].some(s => s.getBoundingClientRect().width > 0))")
    assert visible == [True, False, False]
    indicator = probe(t, "menu-checkbox-item").locator('[data-slot$="indicator"]').bounding_box()
    row = probe(t, "menu-checkbox-item").bounding_box()
    assert near(indicator["x"] - row["x"], 8, 1) if t.rtl else near(row["x"] + row["width"] - indicator["x"] - indicator["width"], 8, 1)
    t.shot("checkboxes", checks)
    page.keyboard.press("Escape")
