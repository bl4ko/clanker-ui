RECORD = """names => {
  window.__g1 = []
  const plain = (k, v) => v instanceof Element ? (v.id || v.localName) : v instanceof FormData ? undefined : v
  for (const n of names) document.addEventListener(n, e => window.__g1.push([n, e.detail == null ? null : JSON.parse(JSON.stringify(e.detail, plain))]))
}"""

TOKEN = """n => {
  const p = document.createElement("p")
  p.style.color = `var(--${n})`
  document.body.append(p)
  const c = getComputedStyle(p).color
  p.remove()
  return c
}"""


def record(page, names):
    page.evaluate(RECORD, names)


def recorded(page, name=None):
    log = page.evaluate("() => window.__g1")
    return [d for n, d in log if n == name] if name else [n for n, d in log]


def clear_log(page):
    page.evaluate("() => { window.__g1.length = 0 }")


def token(page, name):
    return page.evaluate(TOKEN, name)


MIX = """([n, p]) => {
  const e = document.createElement("p")
  e.style.color = `color-mix(in oklab, var(--${n}) ${p}%, transparent)`
  document.body.append(e)
  const c = getComputedStyle(e).color
  e.remove()
  return c
}"""


def mix(page, name, percent):
    return page.evaluate(MIX, [name, percent])


def card_border(t):
    return mix(t.page, "primary", 20 if t.theme == "dark" else 30)


def invalid_border(t):
    return mix(t.page, "destructive", 50) if t.theme == "dark" else token(t.page, "destructive")


STYLE = """async (e, [p, s]) => {
  const running = e.getAnimations({ subtree: true }).filter(a => a.timeline === document.timeline && a.effect?.getComputedTiming().endTime !== Infinity)
  await Promise.all(running.map(a => a.finished.catch(() => {})))
  return getComputedStyle(e, s).getPropertyValue(p)
}"""


def style(loc, prop, pseudo=None):
    return loc.evaluate(STYLE, [prop, pseudo])


def settled_box(page, loc):
    page.wait_for_function("e => e.getAnimations().every(a => a.playState !== 'running' || a.timeline !== document.timeline || a.effect?.getComputedTiming().endTime === Infinity)", arg=loc.element_handle())
    return loc.bounding_box()


def focused(page):
    return page.evaluate("() => { const a = document.activeElement; return a ? (a.getAttribute('aria-label') || (a.getAttribute('role') === 'option' ? '' : a.id) || a.textContent.trim()) : null }")


def popover_open(loc):
    return loc.evaluate("e => e.matches(':popover-open')")


def wait_open(page, loc, state=True):
    loc.page.wait_for_function("([e, s]) => e.matches(':popover-open') === s", arg=[loc.element_handle(), state])


def outside(page):
    page.evaluate("() => document.body.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, composed: true }))")


def no_overflow(t, section_id):
    wide = t.page.evaluate(
        """id => [...document.querySelectorAll(`#${id} [data-demo~="preview"]`)].filter(p => p.scrollWidth > p.clientWidth + 1).map(p => [p.scrollWidth, p.clientWidth])""",
        section_id,
    )
    assert not wide, f"{section_id} previews overflow: {wide}"


def near(a, b, tolerance=0.5):
    return abs(a - b) <= tolerance


def key(t, name):
    return {"ArrowLeft": "ArrowRight", "ArrowRight": "ArrowLeft"}.get(name, name) if t.rtl else name


def side(t, prop):
    return prop.replace("left", "\0").replace("right", "left").replace("\0", "right") if t.rtl else prop


def inline(t, box):
    return {**box, "x": -box["x"] - box["width"]} if t.rtl else box


def ix(t, x):
    return -x if t.rtl else x


def keyboard_mode(page):
    page.keyboard.press("Shift")


def kfocus(page, loc):
    page.keyboard.press("Tab")
    loc.focus()


def check_button_group(t):
    page = t.page
    section = t.section("button-group")
    no_overflow(t, "button-group")
    outer = section.locator("[data-slot=button-group]").first
    assert outer.get_attribute("role") == "group"
    assert style(outer, "gap") == "8px"
    report = section.get_by_role("button", name="Report")
    assert style(report, side(t, "border-top-left-radius")) == "0px"
    assert style(report, side(t, "border-left-width")) == "0px"
    archive = section.get_by_role("button", name="Archive")
    assert style(archive, side(t, "border-top-right-radius")) == "0px"
    assert style(archive, side(t, "border-top-left-radius")) != "0px"
    minus = section.get_by_role("button", name="Decrease")
    vertical = section.locator("[data-orientation=vertical]").first
    assert style(vertical, "flex-direction") == "column"
    assert style(minus, "border-top-width") == "0px" and style(minus, "border-top-left-radius") == "0px"
    trigger = section.locator("[data-slot=select-trigger]")
    amount = section.get_by_label("Amount")
    assert style(amount, side(t, "border-left-width")) == "0px"
    assert style(amount, "flex-grow") == "1"
    sep = section.locator("[data-slot=button-group-separator]").first
    assert near(sep.bounding_box()["width"], 1)
    assert style(sep, "background-color") == token(page, "input")
    trigger.click()
    content = section.locator("[data-slot=select-content]")
    wait_open(page, content)
    content.get_by_role("option", name="€ Euro").click()
    wait_open(page, content, False)
    assert trigger.inner_text().strip() == "€"
    keyboard_mode(page)
    report.focus()
    if report.evaluate("e => e.matches(':focus-visible')"):
        assert style(report, "z-index") == "10"
    t.shot()
    more = section.get_by_role("button", name="More options")
    more.click()
    menu = section.locator("#button-group-more [data-slot=dropdown-menu-content]")
    wait_open(page, menu)
    label = menu.get_by_role("menuitem", name="Label As...")
    label.hover()
    sub = menu.locator("[data-slot=dropdown-menu-sub-content]")
    wait_open(page, sub)
    assert sub.get_by_role("menuitemradio", name="Personal").get_attribute("aria-checked") == "true"
    t.shot("button-group-menu", page)
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    wait_open(page, menu, False)
    copilot = section.get_by_role("button", name="Open Popover")
    copilot.click()
    popover = section.locator("#button-group-copilot [data-slot=popover-content]")
    wait_open(page, popover)
    assert style(popover, "display") == "grid"
    assert page.evaluate("() => document.activeElement.id") == "button-group-task"
    page.keyboard.press("Escape")
    wait_open(page, popover, False)
    assert copilot.evaluate("e => document.activeElement === e")
    follow = section.get_by_role("button", name="More follow options")
    follow.click()
    wait_open(page, section.locator("#button-group-follow [data-slot=dropdown-menu-content]"))
    page.keyboard.press("Escape")
    assert style(trigger, side(t, "border-top-right-radius")) == "0px"
    assert style(trigger, side(t, "border-top-left-radius")) != "0px"
    assert style(more, side(t, "border-top-left-radius")) == "0px" and style(more, side(t, "border-left-width")) == "0px"
    assert style(more, side(t, "border-top-right-radius")) != "0px"
    assert style(copilot, side(t, "border-top-left-radius")) == "0px"


def check_checkbox(t):
    page = t.page
    section = t.section("checkbox")
    no_overflow(t, "checkbox")
    record(page, ["checkbox:change"])
    box = page.locator("#checkbox-terms")
    assert box.evaluate("e => [e.localName, e.type, e.getAttribute('role'), e.tabIndex]") == ["button", "button", "checkbox", 0]
    assert box.get_attribute("aria-checked") == "false" and box.get_attribute("data-unchecked") == "" and box.get_attribute("data-checked") is None
    assert box.get_attribute("data-state") == "unchecked"
    assert box.locator("[data-slot=checkbox-indicator]").count() == 0
    hidden = box.locator("xpath=following-sibling::*[1]")
    assert hidden.evaluate("i => [i.localName, i.type, i.name, i.tabIndex, i.getAttribute('aria-hidden'), i.style.clipPath, i.style.position]") == ["input", "checkbox", "checkbox-terms", -1, "true", "inset(50%)", "absolute"]
    assert style(box, "border-top-color") == token(page, "input")
    section.locator("label[for=checkbox-terms]").click()
    assert box.is_checked() and box.get_attribute("data-checked") == "" and box.get_attribute("data-unchecked") is None
    assert hidden.is_checked() and box.get_attribute("data-state") == "checked"
    assert box.locator("[data-slot=checkbox-indicator][data-checked] svg").is_visible()
    assert style(box, "background-color") == token(page, "primary")
    assert recorded(page, "checkbox:change") == [{"checked": True, "value": True}]
    clear_log(page)
    page.locator("#checkbox-terms-2").focus()
    keyboard_mode(page)
    page.keyboard.press("Shift+Tab")
    assert focused(page) == "checkbox-terms"
    assert "0px 0px 0px 3px" in style(box, "box-shadow") and style(box, "outline-style") == "none"
    page.keyboard.press("Enter")
    assert box.is_checked()
    page.keyboard.press("Space")
    assert not box.is_checked() and box.get_attribute("data-state") == "unchecked" and not hidden.is_checked()
    assert box.locator("[data-slot=checkbox-indicator]").count() == 0
    assert style(box, "border-top-color") == token(page, "ring")
    page.keyboard.press("Space")
    assert box.is_checked()
    assert [d["checked"] for d in recorded(page, "checkbox:change")] == [False, True]
    mixed = page.locator("#checkbox-mixed")
    assert mixed.get_attribute("aria-checked") == "mixed" and mixed.get_attribute("data-state") == "indeterminate"
    assert mixed.get_attribute("data-indeterminate") == "" and mixed.get_attribute("data-checked") is None and mixed.get_attribute("data-unchecked") is None
    assert mixed.locator("[data-slot=checkbox-indicator][data-indeterminate] svg").count() == 1
    assert style(mixed, "background-color") == style(page.locator("#checkbox-invalid"), "background-color")
    mixed.click()
    assert mixed.get_attribute("data-state") == "checked" and mixed.get_attribute("data-indeterminate") is None
    assert not mixed.locator("xpath=following-sibling::input[1]").evaluate("i => i.indeterminate")
    disabled = page.locator("#checkbox-disabled")
    assert disabled.is_disabled() and disabled.get_attribute("aria-disabled") == "true" and disabled.get_attribute("disabled") is None
    assert disabled.get_attribute("data-disabled") == "" and disabled.get_attribute("tabindex") == "-1"
    assert disabled.locator("xpath=following-sibling::input[1]").is_disabled()
    disabled.click(force=True)
    section.locator("label[for=checkbox-disabled]").click(force=True)
    assert not disabled.is_checked()
    assert style(disabled, "opacity") == "0.5"
    assert style(section.locator("label[for=checkbox-disabled]"), "opacity") == "0.5"
    card = page.locator("#checkbox-card")
    section.get_by_text("You can enable or disable notifications at any time.").click()
    assert card.is_checked()
    label = section.locator("label[data-slot=field-label]:has(#checkbox-card)")
    assert style(label, "border-top-color") == card_border(t)
    invalid = page.locator("#checkbox-invalid")
    assert invalid.get_attribute("data-invalid") == ""
    assert style(invalid, "border-top-color") == invalid_border(t)
    page.locator("#checkbox-cds").check()
    assert page.locator("#checkbox-cds").get_attribute("data-state") == "checked"
    assert section.locator("input[name=desktop]").evaluate_all("l => l.filter(i => i.checked).map(i => i.value)") == ["external", "cds"]
    invalid.evaluate("e => e.removeAttribute('aria-invalid')")
    page.wait_for_function("e => !e.hasAttribute('data-invalid')", arg=invalid.element_handle())
    invalid.evaluate("e => e.setAttribute('data-checked', '')")
    page.wait_for_function("e => e.getAttribute('aria-checked') === 'true' && e.nextElementSibling.checked", arg=invalid.element_handle())
    t.shot()
    t.a11y()
    kfocus(page, box)
    assert style(box, "outline-width") == "3px" and style(box, "outline-style") == "solid"
    group = section.locator("[data-slot=checkbox-group]")
    assert style(group, "display") == "flex" and style(group, "gap") == "12px"


def check_combobox(t):
    page = t.page
    section = t.section("combobox")
    no_overflow(t, "combobox")
    record(page, ["combobox:change", "combobox:open", "combobox:close"])
    root = page.locator("#combobox-basic")
    inp = root.locator("input[data-slot=input-group-control]")
    content = root.locator("[data-slot=combobox-content]")
    native = root.locator("input[aria-hidden=true]")
    items = root.locator("[data-slot=combobox-item]")
    trigger = root.locator("[data-combobox-trigger]")
    assert inp.get_attribute("role") == "combobox" and inp.get_attribute("aria-haspopup") == "listbox"
    assert inp.get_attribute("aria-expanded") == "false"
    assert inp.get_attribute("aria-controls") == root.locator("[data-slot=combobox-list]").get_attribute("id")
    assert root.locator("[data-slot=input-group]").get_attribute("data-combobox-input") == ""
    assert trigger.evaluate("e => [e.dataset.slot, e.dataset.size, e.tabIndex, e.getAttribute('aria-haspopup'), e.hasAttribute('data-placeholder')]") == ["input-group-button", "icon-xs", 0, "listbox", True]
    assert native.evaluate("i => [i.style.position, i.style.clipPath]") == ["fixed", "inset(50%)"]
    trigger.scroll_into_view_if_needed()
    tb = trigger.bounding_box()
    assert near(tb["width"], 24) and near(tb["height"], 24)
    page.mouse.move(tb["x"] + 12, tb["y"] + 12)
    page.mouse.down()
    wait_open(page, content)
    assert focused(page) == "Framework"
    assert [inp.get_attribute("data-pressed"), trigger.get_attribute("data-pressed"), trigger.get_attribute("aria-expanded"), inp.get_attribute("data-popup-side")] == ["", "", "true", "bottom"]
    assert style(trigger, "background-color") == (mix(page, "muted", 50) if t.theme == "dark" else "rgba(0, 0, 0, 0)")
    page.mouse.up()
    assert popover_open(content)
    page.keyboard.press("Escape")
    wait_open(page, content, False)
    assert inp.get_attribute("data-pressed") is None and trigger.get_attribute("data-pressed") is None
    clear_log(page)
    inp.click()
    wait_open(page, content)
    assert inp.get_attribute("aria-expanded") == "true"
    assert root.locator("[data-slot=combobox-item]:visible").count() == 5
    box = settled_box(page, content)
    anchor = inp.bounding_box()
    assert abs(box["y"] - (anchor["y"] + anchor["height"] + 6)) <= 1.5, (box, anchor)
    assert abs(inline(t, box)["x"] - inline(t, anchor)["x"]) <= 1 and abs(box["width"] - (anchor["width"] + 28)) <= 1, (box, anchor)
    t.settle()
    t.shot("combobox-open", page)
    inp.press_sequentially("x")
    assert root.locator("[data-slot=combobox-item]:visible").all_inner_texts() == ["Next.js", "Nuxt.js", "Remix"]
    for _ in range(3):
        page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    assert root.locator("[data-slot=combobox-item][data-highlighted]").count() == 0 and inp.get_attribute("aria-activedescendant") is None
    page.keyboard.press("ArrowUp")
    page.keyboard.press("ArrowUp")
    page.keyboard.press("ArrowUp")
    assert items.filter(has_text="Next.js").get_attribute("data-highlighted") == ""
    page.keyboard.press("ArrowUp")
    assert root.locator("[data-slot=combobox-item][data-highlighted]").count() == 0
    inp.fill("")
    inp.press_sequentially("re")
    assert root.locator("[data-slot=combobox-item]:visible").all_inner_texts() == ["Remix"]
    page.keyboard.press("ArrowDown")
    remix = items.filter(has_text="Remix")
    assert remix.get_attribute("data-highlighted") == ""
    assert inp.get_attribute("aria-activedescendant") == remix.get_attribute("id")
    page.keyboard.press("Enter")
    wait_open(page, content, False)
    assert inp.input_value() == "Remix"
    assert native.input_value() == "remix"
    assert remix.get_attribute("aria-selected") == "true" and remix.get_attribute("data-selected") == ""
    assert root.locator("[data-slot=combobox-item-indicator]").count() == 1 and remix.locator("[data-slot=combobox-item-indicator] svg").count() == 1
    assert recorded(page) == ["combobox:open", "combobox:change", "combobox:close"]
    assert recorded(page, "combobox:change") == [{"value": "remix"}]
    inp.fill("zzz")
    wait_open(page, content)
    assert content.get_attribute("data-empty") == "" and inp.get_attribute("data-list-empty") == "" and trigger.get_attribute("data-list-empty") == ""
    assert root.locator("[data-slot=combobox-empty]").is_visible()
    t.settle()
    t.shot("combobox-empty", page)
    page.keyboard.press("Escape")
    wait_open(page, content, False)
    assert inp.input_value() == "Remix" and trigger.get_attribute("data-placeholder") is None
    trigger.click()
    wait_open(page, content)
    assert root.locator("[data-slot=combobox-item]:visible").count() == 5
    assert remix.get_attribute("data-highlighted") == ""
    items.filter(has_text="Astro").click()
    wait_open(page, content, False)
    assert inp.input_value() == "Astro" and native.input_value() == "astro"
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == "Framework"
    inp.click()
    wait_open(page, content)
    outside(page)
    wait_open(page, content, False)
    inp.focus()
    keyboard_mode(page)
    if t.engine == "webkit":
        trigger.focus()
    else:
        page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.hasAttribute('data-combobox-trigger')")
    page.keyboard.press("Enter")
    wait_open(page, content)
    page.keyboard.press("Escape")
    wait_open(page, content, False)
    inp.focus()
    page.keyboard.press("Alt+ArrowDown")
    wait_open(page, content)
    assert items.filter(has_text="Astro").get_attribute("data-highlighted") == ""
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    wait_open(page, content, False)
    assert inp.input_value() == "Astro"

    multi = page.locator("#combobox-multiple")
    chip_input = multi.locator("[data-slot=combobox-chip-input]")
    chips = multi.locator("[data-slot=combobox-chip]")
    mcontent = multi.locator("[data-slot=combobox-content]")
    assert chips.all_inner_texts() == ["Next.js"]
    assert multi.locator("[data-slot=combobox-chips]").get_attribute("role") == "toolbar" and chips.first.evaluate("e => e.localName") == "div"
    clear_log(page)
    chip_input.click()
    wait_open(page, mcontent)
    chip_input.press_sequentially("as")
    assert multi.locator("[data-slot=combobox-item][data-highlighted]").inner_text() == "Astro"
    page.keyboard.press("Enter")
    assert chips.all_inner_texts() == ["Next.js", "Astro"]
    assert chip_input.input_value() == ""
    assert popover_open(mcontent)
    assert recorded(page, "combobox:change") == [{"value": ["next", "astro"]}]
    t.settle()
    t.shot("combobox-multiple", page)
    page.keyboard.press("Escape")
    wait_open(page, mcontent, False)
    page.keyboard.press("Backspace")
    assert chips.all_inner_texts() == ["Next.js"]
    page.keyboard.press(key(t, "ArrowLeft"))
    assert focused(page) == "Next.js"
    page.keyboard.press("Backspace")
    assert chips.count() == 0
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == "Frameworks"
    chip_input.press_sequentially("sv")
    page.keyboard.press("Enter")
    chip_input.press_sequentially("re")
    page.keyboard.press("Enter")
    assert chips.all_inner_texts() == ["SvelteKit", "Remix"]
    multi.get_by_role("button", name="Remove SvelteKit").click()
    assert chips.all_inner_texts() == ["Remix"]
    assert multi.locator("input[type=hidden]").evaluate_all("l => l.map(i => [i.name, i.value])") == [["frameworks", "remix"]]
    page.keyboard.press("Escape")

    clearable = page.locator("#combobox-clearable")
    cinput = clearable.locator("input[data-slot=input-group-control]")
    clear = clearable.locator("[data-slot=combobox-clear]")
    assert cinput.input_value() == "SvelteKit"
    assert clear.is_visible() and clear.get_attribute("data-visible") == "" and clear.get_attribute("data-size") == "icon-xs"
    assert not clearable.locator("[data-combobox-trigger]").is_visible()
    clear_log(page)
    clear.click()
    assert cinput.input_value() == "" and clear.count() == 0
    assert clearable.locator("[data-combobox-trigger]").is_visible()
    assert recorded(page, "combobox:change") == [{"value": ""}]

    groups = page.locator("#combobox-groups")
    ginput = groups.locator("input[data-slot=input-group-control]")
    ginput.click()
    ginput.fill("lon")
    assert groups.locator("[data-slot=combobox-item]:visible").all_inner_texts() == ["(GMT+0) London"]
    assert groups.locator("[data-slot=combobox-group]:visible").count() == 1
    assert groups.locator("[data-slot=combobox-separator]:visible").count() == 0
    assert groups.locator("[data-slot=combobox-item][data-highlighted]").inner_text() == "(GMT+0) London"
    ginput.fill("at")
    athens = groups.locator("[data-value='Europe/Athens']")
    assert athens.get_attribute("aria-disabled") == "true"
    assert groups.locator("[data-slot=combobox-item][data-highlighted]").count() == 0
    page.keyboard.press("Escape")

    popup = page.locator("#combobox-popup")
    ptrigger = popup.locator("[data-combobox-trigger]")
    pcontent = popup.locator("[data-slot=combobox-content]")
    ptrigger.click()
    wait_open(page, pcontent)
    assert ptrigger.get_attribute("aria-expanded") == "true"
    assert focused(page) == "Search countries"
    t.settle()
    t.shot("combobox-popup", page)
    page.keyboard.type("spa")
    assert popup.locator("[data-slot=combobox-item]:visible").all_inner_texts() == ["Spain"]
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    wait_open(page, pcontent, False)
    assert ptrigger.inner_text().strip() == "Spain"
    assert popup.locator("[data-slot=combobox-value]").get_attribute("data-placeholder") is None
    assert page.evaluate("document.activeElement.hasAttribute('data-combobox-trigger')")
    assert popup.locator("input[aria-hidden=true]").input_value() == "spain"

    disabled = page.locator("#combobox-disabled")
    assert disabled.locator("input[data-slot=input-group-control]").is_disabled()
    assert disabled.locator("[data-combobox-trigger]").is_disabled()
    invalid = section.locator("[data-slot=field][data-invalid=true] [data-slot=input-group]")
    assert style(invalid, "border-top-color") == token(page, "destructive")
    t.shot()


def check_combobox_filter_position(t):
    page = t.page
    root = page.locator("#combobox-basic")
    inp = root.locator("input[data-slot=input-group-control]")
    content = root.locator("[data-slot=combobox-content]")
    gaps = """() => {
      const c = document.querySelector("#combobox-basic [data-slot=combobox-content]").getBoundingClientRect()
      const a = document.querySelector("#combobox-basic [data-slot=input-group]").getBoundingClientRect()
      return [Math.round(c.top - a.bottom), Math.round(a.top - c.bottom), Math.round(c.height)]
    }"""
    for sampled in (False, True):
        if sampled:
            page.reload(wait_until="load")
        t.section("combobox")
        page.evaluate("""() => {
          window.__g1Errors = []
          addEventListener("error", e => window.__g1Errors.push(e.message))
          const group = document.querySelector("#combobox-basic [data-slot=input-group]")
          scrollTo({ top: Math.round(scrollY + group.getBoundingClientRect().bottom - (innerHeight - 110)), behavior: "instant" })
        }""")
        inp.click()
        wait_open(page, content)
        assert 109 < page.evaluate("() => innerHeight - document.querySelector('#combobox-basic [data-slot=input-group]').getBoundingClientRect().bottom") < 111
        before = settled_box(page, content)["height"]
        assert content.get_attribute("data-side") == "top"
        if sampled:
            frames = t.paint(gaps, lambda: inp.press_sequentially("n"), ms=500)
            detached = [f for f in frames if not (0 <= f[0] <= 12 or 0 <= f[1] <= 12)]
            assert not detached, frames
        else:
            inp.press_sequentially("n")
            page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r))))")
        assert content.get_attribute("data-side") == "top"
        assert content.bounding_box()["height"] < before
        assert root.locator("[data-slot=combobox-list]").evaluate("l => l.scrollHeight <= l.clientHeight + 1"), "the filtered list scrolls"
        assert page.evaluate("window.__g1Errors") == []
        page.keyboard.press("Escape")
        wait_open(page, content, False)
        inp.fill("")
        inp.click()
        wait_open(page, content)
        assert content.get_attribute("data-side") == "top"
        page.keyboard.press("Escape")


def check_field(t):
    page = t.page
    section = t.section("field")
    no_overflow(t, "field")
    vertical = page.locator("[data-slot=field]:has(> #field-card-name)")
    assert style(vertical, "flex-direction") == "column" and vertical.get_attribute("data-orientation") == "vertical"
    assert style(vertical, "gap") == "8px"
    horizontal = page.locator("[data-slot=field]:has(> #field-same-address)")
    assert style(horizontal, "flex-direction") == "row"
    responsive = page.locator("[data-slot=field]:has(> #field-name)")
    assert style(responsive, "flex-direction") == ("column" if t.mobile else "row")
    legend = section.locator("legend[data-slot=field-legend]").first
    assert style(legend, "font-size") == "16px"
    choice = page.locator("label[data-slot=field-label]:has(#field-vm)")
    choice.click()
    assert page.locator("#field-vm").is_checked()
    assert style(choice, "border-top-color") == card_border(t)
    other = page.locator("label[data-slot=field-label]:has(#field-kubernetes)")
    assert style(other, "border-top-color") != card_border(t)
    invalid_label = page.locator("label[for=field-email]")
    assert style(invalid_label, "color") == token(page, "destructive")
    sep = section.locator("[data-slot=field-separator-content]")
    assert style(sep, "background-color") == token(page, "background")
    keyboard_mode(page)
    thumb = page.get_by_label("Minimum price")
    thumb.focus()
    page.keyboard.press("End")
    assert page.locator("#field-price-min").inner_text() == page.locator("#field-price-max").inner_text()
    assert focused(page) == "Minimum price"
    month = page.locator("#field-exp-month")
    month.click()
    content = section.locator("[data-slot=select]:has(#field-exp-month) [data-slot=select-content]")
    wait_open(page, content)
    content.get_by_role("option", name="07", exact=True).click()
    wait_open(page, content, False)
    assert month.inner_text().strip() == "07"
    page.locator("#field-mfa").check()
    assert page.locator("#field-mfa").get_attribute("data-state") == "checked" and page.locator("#field-mfa").get_attribute("data-checked") == ""
    t.shot()


def check_form(t):
    page = t.page
    section = t.section("form")
    no_overflow(t, "form")
    record(page, ["form:invalid", "form:submit"])
    form = page.locator("#form-profile")
    assert form.evaluate("f => f.noValidate")
    form.locator("button[type=submit]").click()
    invalid = recorded(page, "form:invalid")
    assert len(invalid) == 1
    names = [e["name"] for e in invalid[0]["errors"]]
    assert names == ["username", "email", "plan", "stack", "notify", "code", "terms"], names
    assert focused(page) == "form-username"
    username = page.locator("#form-username")
    assert username.get_attribute("aria-invalid") == "true"
    described = username.get_attribute("aria-describedby").split()
    assert described[0] == "form-username-description" and len(described) == 2
    error = page.locator(f"#{described[1]}")
    assert error.inner_text() == "Username is required."
    assert error.get_attribute("data-slot") == "field-error" and error.get_attribute("role") == "alert"
    assert page.locator("[data-slot=field]:has(> #form-username)").get_attribute("data-invalid") == "true"
    plan = page.locator("#form-plan")
    assert plan.get_attribute("aria-invalid") == "true"
    assert page.locator(f"#{plan.get_attribute('aria-describedby')}").inner_text() == "Choose a plan."
    assert style(plan, "border-top-color") == invalid_border(t)
    stack = page.locator("#form-stack")
    assert stack.get_attribute("aria-invalid") == "true"
    assert page.locator(f"#{stack.get_attribute('aria-describedby')}").inner_text() == "Pick at least one framework."
    group = section.locator("[data-slot=radio-group]")
    assert group.get_attribute("aria-invalid") == "true"
    assert page.locator(f"#{group.get_attribute('aria-describedby')}").inner_text() == "Choose what to be notified about."
    assert page.locator(f"#{page.locator('#form-code').get_attribute('aria-describedby')}").inner_text() == "Enter the 6-digit code."
    assert page.locator(f"#{page.locator('#form-terms').get_attribute('aria-describedby')}").inner_text() == "You must accept the terms."
    assert page.locator("#form-result").inner_text() == "7 fields need attention."
    t.shot("form-invalid")
    username.fill("Bad Name")
    assert error.inner_text() == "Use lowercase letters, numbers, and underscores."
    username.fill("shadcn")
    assert username.get_attribute("aria-invalid") is None
    assert username.get_attribute("aria-describedby") == "form-username-description"
    assert error.is_hidden()
    page.locator("#form-email").fill("m@example.com")
    plan.click()
    content = section.locator("[data-slot=select]:has(#form-plan) [data-slot=select-content]")
    wait_open(page, content)
    content.get_by_role("option", name="Pro", exact=True).click()
    wait_open(page, content, False)
    assert plan.get_attribute("aria-invalid") is None
    stack.click()
    stack.press_sequentially("ne")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    page.keyboard.press("Escape")
    assert stack.get_attribute("aria-invalid") is None
    section.locator("label[for=form-notify-mentions]").click()
    assert group.get_attribute("aria-invalid") is None
    page.locator("#form-code").click()
    page.keyboard.type("123456")
    section.locator("label[for=form-terms]").click()
    assert section.locator("[aria-invalid=true]").count() == 0
    form.locator("button[type=submit]").click()
    submitted = recorded(page, "form:submit")
    assert len(submitted) == 1
    values = submitted[0]["values"]
    assert values == {"username": "shadcn", "email": "m@example.com", "plan": "pro", "stack": "next", "bio": "", "notify": "mentions", "code": "123456", "terms": "on"}, values
    assert page.locator("#form-result").inner_text().startswith("Submitted: ")
    assert page.url.endswith("/demo")
    assert page.locator("#form-terms").get_attribute("aria-checked") == "true"
    form.locator("button[type=reset]").click()
    page.wait_for_function("() => document.querySelector('#form-plan').hasAttribute('data-placeholder')")
    assert page.locator("#form-terms").get_attribute("aria-checked") == "false" and page.locator("#form-terms").get_attribute("data-unchecked") == ""
    assert section.locator("[data-slot=radio-group] [data-slot=radio-group-item][data-checked]").count() == 0
    assert plan.inner_text().strip() == "Select a plan"
    assert section.locator("#form-profile [data-slot=combobox-chip]").count() == 0
    assert page.locator("#form-code").input_value() == ""
    assert page.locator("#form-result").inner_text() == ""
    t.shot()


def check_form_blur(t):
    page = t.page
    section = t.section("form")
    email = page.locator("#form-email")
    email.focus()
    email.blur()
    assert email.get_attribute("aria-invalid") is None
    username = page.locator("#form-username")
    username.fill("Bad Name")
    assert username.get_attribute("aria-invalid") is None
    username.blur()
    assert username.get_attribute("aria-invalid") == "true"
    described = username.get_attribute("aria-describedby").split()
    assert page.locator(f"#{described[-1]}").inner_text() == "Use lowercase letters, numbers, and underscores."
    username.fill("bad_name")
    assert username.get_attribute("aria-invalid") is None
    page.locator("#form-items button[type=submit]").click()
    display = page.locator("#form-display")
    assert focused(page) == "form-display"
    message = page.locator(f"#{display.get_attribute('aria-describedby')}")
    assert message.get_attribute("data-slot") == "form-message"
    assert message.inner_text() == "Display name is required."
    assert page.locator("label[for=form-display]").get_attribute("data-error") == "true"
    assert style(page.locator("label[for=form-display]"), "color") == token(page, "destructive")
    display.fill("Rabbit")
    assert page.locator("label[for=form-display]").get_attribute("data-error") == "false"
    t.shot(target=section.locator("#form-items"))


def check_input(t):
    page = t.page
    section = t.section("input")
    no_overflow(t, "input")
    inp = section.get_by_label("Email").first
    assert near(inp.bounding_box()["height"], 32)
    assert style(inp, "font-size") == ("16px" if t.mobile else "14px")
    inp.focus()
    assert "0px 0px 0px 3px" in style(inp, "box-shadow") and style(inp, "outline-style") == "none"
    assert style(inp, "border-top-color") == token(page, "ring")
    inp.fill("hello")
    assert inp.input_value() == "hello"
    invalid = page.locator("#input-invalid")
    assert style(invalid, "border-top-color") == invalid_border(t)
    assert style(page.locator("#input-disabled"), "opacity") == "0.5"
    assert page.locator("#input-picture").get_attribute("type") == "file"
    t.shot()
    t.a11y()
    kfocus(page, inp)
    assert style(inp, "outline-width") == "3px"


def check_input_group(t):
    page = t.page
    section = t.section("input-group")
    no_overflow(t, "input-group")
    group = section.locator("[data-slot=input-group]").first
    inp = group.locator("input")
    assert group.get_attribute("role") == "group"
    assert group.locator("[data-slot=input-group-addon]").evaluate_all("l => l.map(a => [a.getAttribute('role'), a.dataset.align])") == [["group", "inline-start"], ["group", "inline-end"]]
    group.locator("[data-slot=input-group-addon]").first.click()
    assert focused(page) == "Search"
    assert "0px 0px 0px 3px" in style(group, "box-shadow") and style(group, "outline-style") == "none"
    assert style(group, "border-top-color") == token(page, "ring")
    assert style(inp, "outline-style") == "none"
    assert near(group.bounding_box()["height"], 32)
    info = section.get_by_role("button", name="Info")
    box = info.bounding_box()
    assert near(box["width"], 24) and near(box["height"], 24)
    auto = section.get_by_role("button", name="Auto", exact=True)
    assert near(auto.bounding_box()["height"], 24) and style(auto, "border-top-left-radius") == "7px"
    made = page.evaluate("""async () => {
      const { h } = await import("/clanker-ui.js")
      const b = h("button", { "data-slot": "button", "data-input-group-button": "" }, "Go")
      const addon = h("div", { "data-slot": "input-group-addon" }, b)
      const group = h("div", { "data-slot": "input-group" }, h("input", { "data-slot": "input-group-control", "aria-label": "Made" }), addon)
      document.getElementById("input-group").append(group)
      await new Promise(r => setTimeout(r, 0))
      const out = [b.type, b.dataset.variant, b.dataset.size, Math.round(b.getBoundingClientRect().height), getComputedStyle(b).backgroundColor, group.getAttribute("role"), addon.getAttribute("role"), addon.dataset.align]
      group.remove()
      return out
    }""")
    assert made == ["button", "ghost", "xs", 24, "rgba(0, 0, 0, 0)", "group", "group", "inline-start"], made
    area = section.locator("[data-slot=input-group]:has(textarea)").first
    assert area.bounding_box()["height"] > 60
    assert style(area, "flex-direction") == "column"
    show = section.get_by_role("button", name="Show")
    assert near(show.bounding_box()["height"], 32)
    bad = section.locator("[data-slot=input-group]:has([aria-invalid=true])")
    assert style(bad, "border-top-color") == token(page, "destructive")
    section.locator("[data-slot=input-group-addon]:has(> span[data-slot=input-group-text]:text-is('$'))").click()
    assert focused(page) == "Price"
    t.shot()
    t.a11y()
    kfocus(page, inp)
    assert style(group, "outline-width") == "3px" and style(group, "outline-style") == "solid"


def otp_state(root):
    return root.evaluate("r => [...r.querySelectorAll('[data-slot=input-otp-slot]')].map(s => [s.textContent, s.dataset.active === 'true', !!s.querySelector('[data-slot=input-otp-caret] > div')])")


def otp_active(root):
    return [i for i, s in enumerate(otp_state(root)) if s[1]]


def check_input_otp(t):
    page = t.page
    section = t.section("input-otp")
    no_overflow(t, "input-otp")
    record(page, ["input-otp:complete"])
    root = page.locator("#input-otp-demo")
    inp = root.locator("input")
    assert inp.get_attribute("autocomplete") == "one-time-code"
    root.locator("[data-slot=input-otp-slot]").nth(4).click(force=True)
    assert focused(page) == "One-time password"
    page.wait_for_function("r => r.querySelector('[data-active=true]')", arg=root.element_handle())
    assert otp_active(root) == [0] and otp_state(root)[0][2]
    line = root.locator("[data-slot=input-otp-caret] > div")
    assert near(line.bounding_box()["width"], 1) and near(line.bounding_box()["height"], 16)
    assert style(line, "animation-name") == ("none" if t.reduced_motion else "caret-blink")
    assert inp.evaluate("i => [getComputedStyle(i).position, getComputedStyle(i).color, i.dataset.inputOtp]") == ["absolute", "rgba(0, 0, 0, 0)", "true"]
    page.keyboard.type("123")
    page.wait_for_function("r => r.querySelectorAll('[data-slot=input-otp-slot]')[3].dataset.active === 'true'", arg=root.element_handle())
    assert [s[0] for s in otp_state(root)] == ["1", "2", "3", "", "", ""]
    t.settle()
    t.shot("input-otp-typing", root)
    page.keyboard.press("Backspace")
    assert inp.input_value() == "12"
    page.wait_for_function("r => r.querySelectorAll('[data-slot=input-otp-slot]')[2].dataset.active === 'true'", arg=root.element_handle())
    page.keyboard.press(key(t, "ArrowLeft"))
    page.wait_for_function("r => r.querySelectorAll('[data-slot=input-otp-slot]')[1].dataset.active === 'true'", arg=root.element_handle())
    assert otp_active(root) == [1]
    page.keyboard.type("9")
    assert inp.input_value() == "19"
    page.keyboard.type("8765")
    assert inp.input_value() == "198765"
    page.wait_for_function("r => r.querySelectorAll('[data-slot=input-otp-slot]')[5].dataset.active === 'true'", arg=root.element_handle())
    assert recorded(page, "input-otp:complete") == [{"value": "198765"}]
    page.keyboard.type("0")
    assert inp.input_value() == "198760"
    inp.blur()
    page.wait_for_function("r => !r.querySelector('[data-active=true]')", arg=root.element_handle())

    digits = page.locator("#input-otp-digits")
    assert digits.get_attribute("inputmode") == "numeric"
    digits.focus()
    page.keyboard.type("a1b2")
    assert digits.input_value() == "12"
    clear_log(page)
    digits.evaluate(
        """i => {
          i.setSelectionRange(0, i.value.length)
          const event = new Event("paste", { bubbles: true, cancelable: true })
          Object.defineProperty(event, "clipboardData", { value: { getData: type => (type === "text/plain" ? "98 76 54" : "") } })
          i.dispatchEvent(event)
        }"""
    )
    assert digits.input_value() == "987654"
    assert recorded(page, "input-otp:complete") == [{"value": "987654"}]
    alnum = page.locator("#input-otp-alnum")
    alnum.focus()
    page.keyboard.type("ab-12")
    assert alnum.input_value() == "ab12"
    four = page.locator("#input-otp-four input")
    four.focus()
    page.keyboard.type("123456")
    assert four.input_value() == "1236"
    controlled = page.locator("#input-otp-controlled input")
    controlled.focus()
    page.keyboard.type("42")
    assert page.locator("#input-otp-value").inner_text() == "You entered: 42"
    disabled = page.locator("#input-otp-disabled")
    assert disabled.locator("input").is_disabled()
    assert [s[0] for s in otp_state(disabled)] == ["1", "2", "3", "4", "5", "6"]
    slot = page.locator("#input-otp-invalid [data-slot=input-otp-slot]").first
    assert style(slot, "border-top-color") == token(page, "destructive")
    t.shot()
    assert style(disabled, "opacity") == "0.5"


def check_kbd(t):
    page = t.page
    section = t.section("kbd")
    no_overflow(t, "kbd")
    kbd = section.locator("[data-slot=kbd]").first
    box = kbd.bounding_box()
    assert near(box["height"], 20) and box["width"] >= 19.5
    assert style(kbd, "background-color") == token(page, "muted")
    assert style(kbd, "pointer-events") == "none"
    group = section.locator("[data-slot=kbd-group]").first
    assert style(group, "display") in ("flex", "inline-flex") and style(group, "gap") == "4px"
    inline = section.locator("p [data-slot=kbd-group]")
    assert style(inline, "display") == "inline-flex"
    t.shot()


def check_label(t):
    page = t.page
    section = t.section("label")
    no_overflow(t, "label")
    label = section.locator("label[for=label-terms]")
    assert style(label, "font-size") == "14px" and style(label, "font-weight") == "500"
    label.click()
    assert page.locator("#label-terms").is_checked()
    assert page.locator("#label-disabled").is_disabled()
    assert style(section.locator("label[for=label-disabled]"), "opacity") == "1"
    assert style(section.locator("label[for=label-disabled]"), "cursor") == "default"
    section.locator("label[for=label-email]").click()
    assert focused(page) == "label-email"
    t.shot()


def check_input_otp_rtl(t):
    page = t.page
    t.section("input-otp")
    root = page.locator("#input-otp-demo")
    before = root.evaluate("r => { const d = r.dir; r.dir = 'rtl'; return d }")
    active = "([r, i]) => r.querySelectorAll('[data-slot=input-otp-slot]')[i].dataset.active === 'true'"
    root.locator("[data-slot=input-otp-slot]").nth(0).click(force=True)
    page.keyboard.type("123")
    page.wait_for_function(active, arg=[root.element_handle(), 3], timeout=5000)
    page.keyboard.press("Backspace")
    page.wait_for_function(active, arg=[root.element_handle(), 2], timeout=5000)
    page.keyboard.press("ArrowRight")
    page.wait_for_function(active, arg=[root.element_handle(), 1], timeout=5000)
    assert otp_active(root) == [1], f"ArrowRight moves to the previous slot in RTL: {otp_state(root)}"
    page.keyboard.press("ArrowLeft")
    page.wait_for_function(active, arg=[root.element_handle(), 2], timeout=5000)
    assert otp_active(root) == [2], f"ArrowLeft moves to the next slot in RTL: {otp_state(root)}"
    root.evaluate("(r, d) => { r.dir = d }", before)


def check_native_select(t):
    page = t.page
    section = t.section("native-select")
    no_overflow(t, "native-select")
    sel = section.get_by_label("Status")
    sel.select_option("done")
    assert sel.input_value() == "done"
    icon = section.locator("[data-slot=native-select-icon]").first
    sb = inline(t, sel.bounding_box())
    ib = inline(t, icon.bounding_box())
    assert abs(ib["x"] + ib["width"] - (sb["x"] + sb["width"] - 10)) <= 1 and near(ib["width"], 16), (sb, ib)
    assert abs((ib["y"] + ib["height"] / 2) - (sb["y"] + sb["height"] / 2)) <= 1
    assert near(sb["height"], 32)
    assert near(section.get_by_label("Size").bounding_box()["height"], 28)
    assert sel.get_attribute("data-size") == "default" and section.locator("[data-slot=native-select-wrapper]").first.get_attribute("data-size") == "default"
    assert section.get_by_label("Size").get_attribute("data-size") == "sm" and section.locator("[data-slot=native-select-wrapper]:has([data-size=sm])").get_attribute("data-size") == "sm"
    disabled = section.locator("[data-slot=native-select-wrapper]:has(select:disabled)")
    assert style(disabled, "opacity") == "0.5"
    assert style(section.get_by_label("Invalid role"), "border-top-color") == invalid_border(t)
    keyboard_mode(page)
    sel.focus()
    assert "0px 0px 0px 3px" in style(sel, "box-shadow") and style(sel, "border-top-color") == token(page, "ring")
    assert section.get_by_label("Department").locator("optgroup").count() == 2
    t.shot()
    t.a11y()
    kfocus(page, sel)
    assert style(sel, "outline-width") == "3px"


def check_radio_group(t):
    page = t.page
    section = t.section("radio-group")
    no_overflow(t, "radio-group")
    record(page, ["radio-group:change"])
    group = page.locator("#radio-group-demo")
    assert group.get_attribute("role") == "radiogroup"
    items = group.locator("[data-slot=radio-group-item]")
    assert items.evaluate_all("l => l.map(e => [e.localName, e.getAttribute('role'), e.tabIndex, e.hasAttribute('data-composite-item-active')])") == [["button", "radio", -1, False], ["button", "radio", 0, True], ["button", "radio", -1, False]]
    hidden = group.locator("input")
    assert hidden.evaluate_all("l => l.map(i => [i.type, i.name, i.value, i.tabIndex, i.getAttribute('aria-hidden'), i.style.position])") == [["radio", "radio-group-density", v, -1, "true", "fixed"] for v in ["default", "comfortable", "compact"]]
    comfortable = page.locator("#radio-group-comfortable")
    compact = page.locator("#radio-group-compact")
    assert comfortable.get_attribute("data-state") == "checked" and comfortable.get_attribute("data-checked") == ""
    assert comfortable.locator("[data-slot=radio-group-indicator][data-checked] > span").count() == 1
    assert compact.locator("[data-slot=radio-group-indicator]").count() == 0 and compact.get_attribute("data-unchecked") == ""
    section.locator("label[for=radio-group-compact]").click()
    assert compact.is_checked() and compact.get_attribute("data-state") == "checked"
    assert comfortable.get_attribute("data-state") == "unchecked" and comfortable.locator("[data-slot=radio-group-indicator]").count() == 0
    assert hidden.evaluate_all("l => l.map(i => i.checked)") == [False, False, True]
    assert style(compact, "background-color") == token(page, "primary")
    assert style(compact.locator("[data-slot=radio-group-indicator] > span"), "background-color") == token(page, "primary-foreground")
    kfocus(page, compact)
    assert "0px 0px 0px 3px" in style(compact, "box-shadow") and style(compact, "outline-style") == "none"
    page.keyboard.press("ArrowUp")
    assert focused(page) == "radio-group-comfortable" and comfortable.is_checked()
    assert comfortable.get_attribute("data-state") == "checked" and compact.get_attribute("data-state") == "unchecked"
    assert comfortable.get_attribute("tabindex") == "0" and compact.get_attribute("tabindex") == "-1"
    assert recorded(page, "radio-group:change") == [{"value": "compact"}, {"value": "comfortable"}]
    page.keyboard.press("End")
    page.keyboard.press("Home")
    assert focused(page) == "radio-group-comfortable" and comfortable.is_checked()
    page.locator("#radio-group-default").focus()
    page.keyboard.press("Enter")
    assert not page.locator("#radio-group-default").is_checked()
    page.keyboard.press("Space")
    assert page.locator("#radio-group-default").is_checked() and not comfortable.is_checked()
    page.keyboard.press(key(t, "ArrowRight"))
    assert focused(page) == "radio-group-comfortable" and comfortable.is_checked()
    page.locator("#radio-group-d2").focus()
    page.keyboard.press("ArrowDown")
    assert focused(page) == "radio-group-d3"
    page.keyboard.press("ArrowDown")
    assert focused(page) == "radio-group-d2"
    d1 = page.locator("#radio-group-d1")
    assert d1.is_disabled() and d1.get_attribute("data-disabled") == "" and d1.get_attribute("tabindex") == "-1"
    section.locator("label[for=radio-group-d1]").scroll_into_view_if_needed()
    section.locator("label[for=radio-group-d1]").click(force=True)
    assert not d1.is_checked()
    card = section.locator("label[data-slot=field-label]:has(#radio-group-pro)")
    card.click()
    assert page.locator("#radio-group-pro").is_checked()
    assert style(card, "border-top-color") == card_border(t)
    invalid = page.locator("#radio-group-i1")
    assert invalid.get_attribute("data-invalid") == ""
    assert style(invalid, "border-top-color") == invalid_border(t)
    t.shot()
    t.a11y()
    kfocus(page, compact)
    assert style(compact, "outline-width") == "3px"


def select_parts(page, root_id):
    root = page.locator(f"#{root_id}")
    return root, root.locator("[data-slot=select-trigger]"), root.locator("[data-slot=select-content]")


def check_select(t):
    page = t.page
    section = t.section("select")
    no_overflow(t, "select")
    record(page, ["select:change", "select:open", "select:close"])
    root, trigger, content = select_parts(page, "select-demo")
    native = root.locator("input[aria-hidden=true]")
    assert trigger.get_attribute("role") == "combobox"
    assert trigger.get_attribute("aria-haspopup") == "listbox"
    assert trigger.get_attribute("aria-expanded") == "false"
    assert trigger.get_attribute("aria-controls") == content.get_attribute("id")
    assert trigger.get_attribute("data-placeholder") == ""
    assert style(trigger, "color") == token(page, "muted-foreground")
    assert trigger.inner_text().strip() == "Select a fruit"
    assert native.get_attribute("name") == "fruit" and native.input_value() == ""
    assert native.evaluate("i => [i.style.position, i.style.clipPath, i.getBoundingClientRect().width]") == ["fixed", "inset(50%)", 1]
    assert trigger.get_attribute("data-size") == "default" and root.locator("[data-slot=select-value]").get_attribute("data-placeholder") == ""
    trigger.scroll_into_view_if_needed()
    tb = trigger.bounding_box()
    page.mouse.move(tb["x"] + 10, tb["y"] + tb["height"] / 2)
    page.mouse.down()
    wait_open(page, content)
    assert trigger.get_attribute("data-pressed") == "" and trigger.get_attribute("data-popup-open") == "" and trigger.get_attribute("data-popup-side") == "bottom"
    page.mouse.up()
    assert popover_open(content) and focused(page) == "Apple"
    assert content.get_attribute("data-align-trigger") == "true" and content.get_attribute("data-side") == "none"
    page.keyboard.press("Escape")
    wait_open(page, content, False)
    assert trigger.get_attribute("data-pressed") is None and trigger.get_attribute("data-popup-side") is None
    clear_log(page)
    trigger.click()
    wait_open(page, content)
    assert trigger.get_attribute("aria-expanded") == "true"
    assert content.get_attribute("role") == "listbox"
    assert focused(page) == "Apple"
    assert root.locator("[data-slot=select-group]").get_attribute("role") == "group"
    t.settle()
    t.shot("select-open", page)
    page.keyboard.press("ArrowDown")
    assert focused(page) == "Banana"
    page.keyboard.press("End")
    assert focused(page) == "Pineapple"
    page.keyboard.press("ArrowDown")
    assert focused(page) == "Pineapple"
    page.keyboard.press("Home")
    assert focused(page) == "Apple"
    page.keyboard.press("g")
    assert focused(page) == "Grapes"
    page.keyboard.press("Enter")
    wait_open(page, content, False)
    assert trigger.inner_text().strip() == "Grapes"
    assert trigger.get_attribute("data-placeholder") is None
    assert root.get_attribute("data-value") == "grapes" and native.input_value() == "grapes"
    assert focused(page) == "Fruit"
    assert trigger.get_attribute("aria-expanded") == "false"
    assert recorded(page) == ["select:open", "select:change", "select:close"]
    assert recorded(page, "select:change") == [{"value": "grapes"}]
    grapes = root.locator("[data-slot=select-item][data-value=grapes]")
    assert grapes.get_attribute("aria-selected") == "true" and grapes.get_attribute("data-state") == "checked" and grapes.get_attribute("data-selected") == ""
    assert root.locator("[data-slot=select-item-indicator]").count() == 1 and grapes.locator("[data-slot=select-item-indicator]").count() == 1
    assert grapes.evaluate("e => [...e.children].map(c => c.localName + ':' + c.dataset.slot)") == ["div:select-item-text", "span:select-item-indicator"]
    page.keyboard.press("Enter")
    wait_open(page, content)
    assert focused(page) == "Grapes"
    page.keyboard.press("ArrowUp")
    page.keyboard.press("Escape")
    wait_open(page, content, False)
    assert native.input_value() == "grapes" and focused(page) == "Fruit"
    page.wait_for_timeout(600)
    for name in ["Home", "End"]:
        page.keyboard.press(name)
    page.wait_for_timeout(100)
    assert not popover_open(content) and native.input_value() == "grapes"
    page.keyboard.press("b")
    page.wait_for_timeout(100)
    assert not popover_open(content) and native.input_value() == "banana" and focused(page) == "Fruit"
    assert recorded(page, "select:change")[-1] == {"value": "banana"}
    page.wait_for_timeout(800)
    page.keyboard.press("ArrowUp")
    wait_open(page, content)
    assert focused(page) == "Banana"
    assert root.locator("[data-slot=select-item][data-highlighted]").inner_text() == "Banana"
    page.keyboard.press("g")
    assert focused(page) == "Grapes"
    page.keyboard.press(" ")
    page.wait_for_timeout(100)
    assert popover_open(content) and focused(page) == "Grapes" and native.input_value() == "banana"
    page.wait_for_timeout(800)
    page.keyboard.press("ArrowUp")
    page.keyboard.press("ArrowUp")
    page.keyboard.press(" ")
    wait_open(page, content, False)
    assert native.input_value() == "banana"
    trigger.click()
    wait_open(page, content)
    root.get_by_role("option", name="Blueberry").hover()
    assert focused(page) == "Blueberry"
    root.get_by_role("option", name="Apple", exact=True).click()
    wait_open(page, content, False)
    assert native.input_value() == "apple"
    trigger.click()
    wait_open(page, content)
    outside(page)
    wait_open(page, content, False)
    assert native.input_value() == "apple"
    trigger.focus()
    page.keyboard.press("ArrowDown")
    wait_open(page, content)
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Tab")
    wait_open(page, content, False)
    assert native.input_value() == "apple"
    assert not root.evaluate("r => r.contains(document.activeElement)")
    trigger.scroll_into_view_if_needed()
    tb = trigger.bounding_box()
    page.mouse.move(tb["x"] + 10, tb["y"] + tb["height"] / 2)
    page.mouse.down()
    wait_open(page, content)
    t.settle()
    pick = root.get_by_role("option", name="Pineapple")
    pb = pick.bounding_box()
    page.mouse.move(pb["x"] + 20, pb["y"] + pb["height"] / 2, steps=5)
    page.mouse.up()
    wait_open(page, content, False)
    assert native.input_value() == "pineapple"

    aroot, atrigger, acontent = select_parts(page, "select-aligned")
    atrigger.evaluate("e => e.scrollIntoView({ block: 'center' })")
    atrigger.click()
    wait_open(page, acontent)
    t.settle()
    banana = aroot.get_by_role("option", name="Banana", exact=True)
    tb = atrigger.bounding_box()
    bb = banana.bounding_box()
    assert abs((tb["y"] + tb["height"] / 2) - (bb["y"] + bb["height"] / 2)) <= 2, (tb, bb)
    vb = atrigger.locator("[data-slot=select-value]").bounding_box()
    xb = banana.locator("[data-slot=select-item-text]").bounding_box()
    assert abs(inline(t, vb)["x"] - inline(t, xb)["x"]) <= 2 and abs(vb["y"] - xb["y"]) <= 2, (vb, xb)
    assert acontent.get_attribute("data-side") == "none" and acontent.get_attribute("data-align-trigger") == "true"
    assert style(acontent, "animation-name") == "none"
    t.shot("select-aligned", page)
    page.keyboard.press("Escape")
    wait_open(page, acontent, False)
    page.evaluate("t => scrollBy(0, t.getBoundingClientRect().bottom - (innerHeight - 12))", atrigger.element_handle())
    atrigger.click()
    wait_open(page, acontent)
    t.settle()
    low = atrigger.bounding_box()
    fb = settled_box(page, acontent)
    assert acontent.get_attribute("data-side") == "top" and abs(fb["y"] + fb["height"] + 4 - low["y"]) <= 1.5, (fb, low)
    page.keyboard.press("Escape")
    wait_open(page, acontent, False)
    atrigger.evaluate("e => e.scrollIntoView({ block: 'center' })")
    page.locator("#select-align").click()
    tb = atrigger.bounding_box()
    assert acontent.get_attribute("data-align-trigger") == "false"
    atrigger.click()
    wait_open(page, acontent)
    t.settle()
    cb = settled_box(page, acontent)
    assert acontent.get_attribute("data-side") == "bottom"
    assert abs(cb["y"] - (tb["y"] + tb["height"] + 4)) <= 1.5, (cb, tb)
    assert abs(cb["width"] - max(tb["width"], 144)) <= 1, (cb, tb)
    page.keyboard.press("Escape")
    wait_open(page, acontent, False)

    sroot, strigger, scontent = select_parts(page, "select-scrollable")
    strigger.click()
    wait_open(page, scontent)
    t.settle()
    box = settled_box(page, scontent)
    height = page.viewport_size["height"]
    assert box["y"] >= 9 and box["y"] + box["height"] <= height - 9, box
    cet = sroot.get_by_role("option", name="Central European Time")
    assert focused(page) == "Central European Time"
    vp = sroot.locator("[data-slot=select-viewport]").bounding_box()
    cb = cet.bounding_box()
    assert vp["y"] - 1 <= cb["y"] and cb["y"] + cb["height"] <= vp["y"] + vp["height"] + 1
    down = sroot.locator("[data-slot=select-scroll-down-button]")
    up = sroot.locator("[data-slot=select-scroll-up-button]")
    assert down.is_visible() or up.is_visible()
    t.shot("select-scrollable", page)
    page.keyboard.press("End")
    page.wait_for_function("e => !e.hidden", arg=up.element_handle())
    before = sroot.locator("[data-slot=select-viewport]").evaluate("v => v.scrollTop")
    up.hover()
    page.wait_for_function("([v, b]) => v.scrollTop < b - 20", arg=[sroot.locator("[data-slot=select-viewport]").element_handle(), before])
    page.mouse.move(0, 0)
    page.keyboard.press("Escape")
    wait_open(page, scontent, False)

    droot, dtrigger, dcontent = select_parts(page, "select-item-disabled")
    dtrigger.click()
    wait_open(page, dcontent)
    assert focused(page) == "Apple"
    assert droot.get_by_role("option", name="Banana", exact=True).get_attribute("aria-disabled") == "true"
    page.keyboard.press("ArrowDown")
    assert focused(page) == "Blueberry"
    page.keyboard.press("ArrowDown")
    assert focused(page) == "Pineapple"
    page.keyboard.press("Escape")
    wait_open(page, dcontent, False)
    assert page.locator("#select-disabled [data-slot=select-trigger]").is_disabled()
    assert style(page.locator("#select-disabled [data-slot=select-trigger]"), "opacity") == "0.5"
    assert style(page.locator("#select-invalid"), "border-top-color") == invalid_border(t)
    small = page.locator("#select-small [data-slot=select-trigger]")
    assert near(small.bounding_box()["height"], 28) and near(trigger.bounding_box()["height"], 32)
    assert small.inner_text().strip() == "Light"
    assert small.locator("[data-slot=select-value] svg").count() == 1
    groots, gtrigger, gcontent = select_parts(page, "select-groups")
    gtrigger.click()
    wait_open(page, gcontent)
    assert groots.locator("[data-slot=select-separator]").get_attribute("aria-hidden") == "true"
    assert groots.locator("[data-slot=select-label]").first.is_visible()
    t.settle()
    t.shot("select-groups", page)
    page.keyboard.press("Escape")
    wait_open(page, gcontent, False)
    t.shot()


SCROLL_REST = """e => new Promise(resolve => {
  let last = null
  let still = 0
  const tick = () => {
    still = e.scrollTop === last ? still + 1 : 0
    last = e.scrollTop
    if (still < 20) requestAnimationFrame(tick)
    else resolve(e.scrollTop)
  }
  requestAnimationFrame(tick)
})"""


def check_select_keyboard_scroll(t):
    page = t.page
    t.section("select")
    root, trigger, content = select_parts(page, "select-scrollable")
    trigger.click()
    wait_open(page, content)
    t.settle()
    items = content.locator("[data-slot=select-item]")
    names = items.evaluate_all("els => els.map(e => e.textContent.trim())")
    rest = items.nth(4).bounding_box()
    page.mouse.move(rest["x"] + 30, rest["y"] + rest["height"] / 2)
    assert focused(page) == names[4]
    viewport = root.locator("[data-slot=select-viewport]")
    for key, want in (("End", names[-1]), ("Home", names[0]), ("End", names[-1]), ("ArrowUp", names[-2])):
        page.keyboard.press(key)
        viewport.evaluate(SCROLL_REST)
        assert focused(page) == want, (key, want, focused(page))
        assert page.evaluate("document.documentElement.hasAttribute('data-keyboard')"), key
    t.shot("select-keyboard-scroll", page)
    page.keyboard.press("Escape")
    wait_open(page, content, False)


def slider_point(root, fraction, vertical=False, rtl=False):
    root.scroll_into_view_if_needed()
    b = root.locator("[data-slot=slider-track]").bounding_box()
    if vertical:
        return b["x"] + b["width"] / 2, b["y"] + b["height"] - 6 - fraction * (b["height"] - 12)
    f = 1 - fraction if rtl else fraction
    return b["x"] + 6 + f * (b["width"] - 12), b["y"] + b["height"] / 2


def thumb_center(thumb):
    b = thumb.bounding_box()
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2


def check_slider(t):
    page = t.page
    section = t.section("slider")
    no_overflow(t, "slider")
    root = page.locator("#slider-demo")
    thumb = root.locator("input")
    page.evaluate("() => { window.__slider = []; document.getElementById('slider-demo').addEventListener('input', e => window.__slider.push(['input', e.target.value])); document.getElementById('slider-demo').addEventListener('change', e => window.__slider.push(['change', e.target.value])) }")
    assert root.get_attribute("role") == "group" and root.get_attribute("data-orientation") == "horizontal"
    shape = root.evaluate("""r => {
      const c = r.firstElementChild
      const parts = [c, ...c.children, c.firstElementChild.firstElementChild]
      return parts.map(e => [e.localName, e.dataset.slot ?? null, e.dataset.orientation ?? null]).concat([[r.querySelector('input').parentElement.dataset.slot, r.querySelector('input').parentElement.dataset.index]])
    }""")
    assert shape == [["div", None, "horizontal"], ["div", "slider-track", "horizontal"], ["div", "slider-thumb", "horizontal"], ["div", "slider-range", "horizontal"], ["slider-thumb", "0"]], shape
    assert thumb.evaluate("i => [i.getAttribute('aria-orientation'), i.getAttribute('aria-valuenow'), i.style.position, i.style.clipPath, i.getAttribute('data-slot')]") == ["horizontal", "75", "fixed", "inset(50%)", None]
    track = root.locator("[data-slot=slider-track]").bounding_box()
    assert near(track["height"], 4)
    tdiv = root.locator("[data-slot=slider-thumb]")
    tb = tdiv.bounding_box()
    assert near(tb["width"], 12) and near(tb["height"], 12)
    x, y = slider_point(root, 0.75, rtl=t.rtl)
    cx, cy = thumb_center(tdiv)
    assert abs(cx - x) <= 1 and abs(cy - y) <= 1, (cx, cy, x, y)
    rb = inline(t, root.locator("[data-slot=slider-range]").bounding_box())
    assert abs(rb["x"] + rb["width"] - ix(t, x)) <= 1, (rb, x)
    assert style(tdiv, "background-color") == "rgb(255, 255, 255)" and style(tdiv, "border-top-color") == token(page, "ring")
    keyboard_mode(page)
    thumb.focus()
    assert tdiv.evaluate("e => e.style.zIndex") == "1"
    page.keyboard.press(key(t, "ArrowRight"))
    assert thumb.input_value() == "76" and thumb.get_attribute("aria-valuenow") == "76"
    page.keyboard.press("Shift+" + key(t, "ArrowRight"))
    assert thumb.input_value() == "86"
    page.keyboard.press("PageDown")
    assert thumb.input_value() == "76"
    page.keyboard.press("Home")
    assert thumb.input_value() == "0"
    x0, _ = slider_point(root, 0, rtl=t.rtl)
    assert abs(thumb_center(tdiv)[0] - x0) <= 1
    page.keyboard.press("End")
    assert thumb.input_value() == "100"
    page.keyboard.press("ArrowDown")
    assert thumb.input_value() == "99"
    log = page.evaluate("() => window.__slider")
    assert ["input", "76"] in log and ["change", "76"] in log
    x, y = slider_point(root, 0.25, rtl=t.rtl)
    page.mouse.click(x, y)
    assert thumb.input_value() == "25"
    page.mouse.move(x, y)
    page.mouse.down()
    x2, _ = slider_point(root, 0.6, rtl=t.rtl)
    page.mouse.move(x2, y, steps=4)
    assert thumb.input_value() == "60"
    assert root.get_attribute("data-dragging") == "" and tdiv.get_attribute("data-dragging") == ""
    page.mouse.up()
    assert root.get_attribute("data-dragging") is None
    assert page.evaluate("() => window.__slider.at(-1)") == ["change", "60"]
    assert focused(page) == "Volume"

    rroot = page.locator("#slider-range")
    lo = rroot.get_by_label("Minimum")
    hi = rroot.get_by_label("Maximum")
    assert [lo.get_attribute("aria-valuetext"), hi.get_attribute("aria-valuetext")] == ["25 start range", "50 end range"]
    lo.focus()
    page.keyboard.press("End")
    assert [lo.input_value(), hi.input_value()] == ["50", "50"]
    assert focused(page) == "Minimum"
    page.keyboard.press("Home")
    assert [lo.input_value(), hi.input_value()] == ["0", "50"]
    x, y = slider_point(rroot, 0.45, rtl=t.rtl)
    page.mouse.click(x, y)
    assert [lo.input_value(), hi.input_value()] == ["0", "45"]
    rb = inline(t, rroot.locator("[data-slot=slider-range]").bounding_box())
    x0, _ = slider_point(rroot, 0, rtl=t.rtl)
    x1, _ = slider_point(rroot, 0.45, rtl=t.rtl)
    assert abs(rb["x"] - ix(t, x0)) <= 1 and abs(rb["x"] + rb["width"] - ix(t, x1)) <= 1, (rb, x0, x1)
    x, y = slider_point(rroot, 0.9, rtl=t.rtl)
    page.mouse.move(*slider_point(rroot, 0, rtl=t.rtl))
    page.mouse.down()
    page.mouse.move(x, y, steps=6)
    page.mouse.up()
    assert [lo.input_value(), hi.input_value()] == ["90", "90"]

    multi = page.locator("#slider-multiple input")
    multi.nth(2).focus()
    page.keyboard.press("Home")
    assert multi.evaluate_all("l => l.map(i => i.value)") == ["10", "20", "20"]
    assert focused(page) == "Third"
    assert multi.nth(2).get_attribute("aria-valuetext") is None

    vroot = page.locator("#slider-vertical")
    vthumb = vroot.locator("input")
    assert vthumb.get_attribute("aria-orientation") == "vertical"
    vtrack = vroot.locator("[data-slot=slider-track]").bounding_box()
    assert vtrack["height"] >= 159 and near(vtrack["width"], 4)
    off = vroot.evaluate(
        """r => {
          const before = r.dir
          r.dir = "rtl"
          const i = r.querySelector("[data-slot=slider-thumb]").getBoundingClientRect()
          const k = r.querySelector("[data-slot=slider-track]").getBoundingClientRect()
          r.dir = before
          return Math.abs(i.x + i.width / 2 - (k.x + k.width / 2))
        }"""
    )
    assert off <= 1, f"the vertical thumb is {off}px off the track in RTL"
    vthumb.focus()
    page.keyboard.press("ArrowUp")
    assert vthumb.input_value() == "51"
    page.keyboard.press("ArrowRight")
    assert vthumb.input_value() == "52"
    x, y = slider_point(vroot, 0.9, vertical=True)
    x, y = round(x), round(y)
    page.mouse.click(x, y)
    vt = vroot.locator("[data-slot=slider-track]").bounding_box()
    assert vthumb.input_value() == str(round((vt["y"] + vt["height"] - 6 - y) / (vt["height"] - 12) * 100)) and abs(int(vthumb.input_value()) - 90) <= 1
    vb = vroot.locator("[data-slot=slider-track]").bounding_box()
    vr = vroot.locator("[data-slot=slider-range]").bounding_box()
    assert abs(vr["y"] - y) <= 1 and abs(vr["y"] + vr["height"] - (vb["y"] + vb["height"])) <= 1, (vr, y, vb)
    assert abs(thumb_center(vroot.locator("[data-slot=slider-thumb]"))[1] - y) <= 1

    rtl = page.locator("#slider-rtl")
    rinput = rtl.locator("input")
    rinput.focus()
    page.keyboard.press("ArrowLeft")
    assert rinput.input_value() == "26"
    assert abs(thumb_center(rtl.locator("[data-slot=slider-thumb]"))[0] - slider_point(rtl, 0.26, rtl=True)[0]) <= 1
    x, y = slider_point(rtl, 0.8, rtl=True)
    page.mouse.click(x, y)
    assert rinput.input_value() == "80"

    disabled = page.locator("#slider-disabled")
    assert disabled.get_attribute("data-disabled") == ""
    assert disabled.evaluate("r => [...r.querySelectorAll('div')].every(d => d.hasAttribute('data-disabled'))")
    assert style(disabled.locator(":scope > div"), "opacity") == "0.5"
    x, y = slider_point(disabled, 0.9)
    page.mouse.click(x, y)
    assert disabled.locator("input").input_value() == "50"

    temp = page.get_by_label("Temperature low")
    temp.focus()
    page.keyboard.press(key(t, "ArrowRight"))
    assert page.locator("#slider-temperature-value").inner_text() == "0.4, 0.7"
    page.keyboard.press("PageUp")
    assert page.locator("#slider-temperature-value").inner_text() == "0.7, 0.7"
    t.shot()
    t.a11y()
    kfocus(page, thumb)
    assert style(tdiv, "outline-width") == "3px"


def check_switch(t):
    page = t.page
    section = t.section("switch")
    no_overflow(t, "switch")
    record(page, ["switch:change"])
    sw = page.locator("#switch-airplane")
    assert sw.evaluate("e => [e.localName, e.getAttribute('role'), e.dataset.size, e.tabIndex]") == ["button", "switch", "default", 0]
    assert sw.get_attribute("data-state") == "unchecked" and sw.get_attribute("data-unchecked") == ""
    thumb = sw.locator("[data-slot=switch-thumb]")
    assert thumb.get_attribute("data-unchecked") == ""
    hidden = sw.locator("xpath=following-sibling::*[1]")
    assert hidden.evaluate("i => [i.localName, i.type, i.tabIndex, i.getAttribute('aria-hidden'), i.style.position]") == ["input", "checkbox", -1, "true", "fixed"]
    box = sw.bounding_box()
    assert near(box["width"], 32) and near(box["height"], 18.4)
    assert style(sw, "background-color") == (mix(page, "input", 80) if t.theme == "dark" else token(page, "input"))
    tb = thumb.bounding_box()
    assert near(tb["width"], 16) and near(inline(t, tb)["x"] - inline(t, box)["x"], 1)
    section.locator("label[for=switch-airplane]").click()
    assert sw.is_checked() and sw.get_attribute("data-state") == "checked" and hidden.is_checked()
    assert thumb.get_attribute("data-checked") == ""
    assert style(sw, "background-color") == token(page, "primary")
    page.wait_for_function("([e, t, rtl]) => { const a = e.getBoundingClientRect(), b = t.getBoundingClientRect(); return Math.abs(rtl ? b.left - a.left - 1 : b.right - a.right + 1) < 0.6 }", arg=[sw.element_handle(), thumb.element_handle(), t.rtl])
    assert recorded(page, "switch:change") == [{"checked": True, "value": True}]
    kfocus(page, sw)
    assert "0px 0px 0px 3px" in style(sw, "box-shadow") and style(sw, "outline-style") == "none"
    page.keyboard.press("Space")
    assert not sw.is_checked() and sw.get_attribute("data-state") == "unchecked"
    page.keyboard.press("Enter")
    assert sw.is_checked()
    small = page.locator("#switch-small")
    sb = small.bounding_box()
    assert small.get_attribute("data-size") == "sm" and near(sb["width"], 24) and near(sb["height"], 14)
    disabled = page.locator("#switch-disabled")
    assert disabled.is_disabled() and disabled.get_attribute("data-disabled") == "" and disabled.get_attribute("tabindex") == "-1"
    section.locator("label[for=switch-disabled]").click(force=True)
    assert not disabled.is_checked()
    assert style(section.locator("label[for=switch-disabled]"), "opacity") == "0.5"
    card = section.locator("label[data-slot=field-label]:has(#switch-card)")
    card.click()
    assert page.locator("#switch-card").is_checked()
    assert style(card, "border-top-color") == card_border(t)
    t.shot()
    t.a11y()
    kfocus(page, sw)
    assert style(sw, "outline-width") == "3px"


def check_textarea(t):
    page = t.page
    section = t.section("textarea")
    no_overflow(t, "textarea")
    ta = section.get_by_label("Message").first
    assert ta.bounding_box()["height"] >= 64
    ta.fill("one\ntwo\nthree\nfour\nfive")
    assert ta.input_value().count("\n") == 4
    if t.engine == "chromium":
        assert ta.bounding_box()["height"] > 100
    ta.focus()
    assert "0px 0px 0px 3px" in style(ta, "box-shadow") and style(ta, "border-top-color") == token(page, "ring")
    assert style(page.locator("#textarea-invalid"), "border-top-color") == invalid_border(t)
    assert style(page.locator("#textarea-disabled"), "opacity") == "0.5"
    assert style(page.locator("#textarea-disabled"), "cursor") == "not-allowed"
    t.shot()
    t.a11y()
    kfocus(page, ta)
    assert style(ta, "outline-width") == "3px"


def check_toggle(t):
    page = t.page
    section = t.section("toggle")
    no_overflow(t, "toggle")
    record(page, ["toggle:change"])
    tg = page.locator("#toggle-bookmark")
    assert tg.get_attribute("aria-pressed") == "false" and tg.get_attribute("data-state") == "off" and tg.get_attribute("data-pressed") is None
    tg.click()
    assert tg.get_attribute("aria-pressed") == "true" and tg.get_attribute("data-state") == "on" and tg.get_attribute("data-pressed") == ""
    assert style(tg, "background-color") == token(page, "muted")
    kfocus(page, tg)
    page.keyboard.press("Space")
    assert tg.get_attribute("aria-pressed") == "false"
    page.keyboard.press("Enter")
    assert tg.get_attribute("aria-pressed") == "true"
    assert [d["pressed"] for d in recorded(page, "toggle:change")] == [True, False, True]
    assert "0px 0px 0px 3px" in style(tg, "box-shadow") and style(tg, "outline-style") == "none"
    underline = section.get_by_role("button", name="Toggle underline")
    assert underline.get_attribute("aria-pressed") == "true" and underline.get_attribute("data-pressed") == ""
    assert style(underline, "background-color") == token(page, "muted")
    heights = [section.get_by_role("button", name=n, exact=True).bounding_box()["height"] for n in ["Small", "Default", "Large"]]
    assert all(near(a, b) for a, b in zip(heights, [28, 32, 36])), heights
    disabled = section.get_by_role("button", name="Disabled")
    assert disabled.is_disabled() and style(disabled, "opacity") == "0.5" and disabled.get_attribute("data-disabled") == ""
    t.shot()
    t.a11y()
    kfocus(page, tg)
    assert style(tg, "outline-width") == "3px"


def check_toggle_group(t):
    page = t.page
    section = t.section("toggle-group")
    no_overflow(t, "toggle-group")
    record(page, ["toggle-group:change"])
    group = page.locator("#toggle-group-demo")
    bold = group.get_by_role("button", name="Toggle bold")
    italic = group.get_by_role("button", name="Toggle italic")
    underline = group.get_by_role("button", name="Toggle underline")
    assert group.get_attribute("role") == "group"
    assert bold.get_attribute("aria-pressed") == "false"
    assert [b.get_attribute("tabindex") for b in [bold, italic, underline]] == ["0", "-1", "-1"]
    bold.click()
    italic.click()
    assert bold.get_attribute("aria-pressed") == "true" and italic.get_attribute("data-state") == "on" and italic.get_attribute("data-pressed") == ""
    assert style(italic, "background-color") == token(page, "muted")
    bold.click()
    assert [d["value"] for d in recorded(page, "toggle-group:change")] == [["bold"], ["bold", "italic"], ["italic"]]
    assert group.get_attribute("data-spacing") == "2" and group.get_attribute("data-orientation") == "horizontal" and style(group, "column-gap") == "8px"
    assert [bold.get_attribute(a) for a in ["data-variant", "data-size", "data-spacing"]] == ["outline", "default", "2"]
    assert style(italic, side(t, "border-left-width")) == "1px" and style(italic, side(t, "border-top-left-radius")) == "10px"
    keyboard_mode(page)
    italic.focus()
    page.keyboard.press("ArrowDown")
    assert focused(page) == "Toggle italic"
    page.keyboard.press(key(t, "ArrowRight"))
    assert focused(page) == "Toggle underline"
    page.keyboard.press(key(t, "ArrowRight"))
    assert focused(page) == "Toggle bold"
    page.keyboard.press("End")
    assert focused(page) == "Toggle underline"
    assert underline.get_attribute("tabindex") == "0" and bold.get_attribute("tabindex") == "-1"
    page.keyboard.press("Space")
    assert underline.get_attribute("aria-pressed") == "true"

    single = page.locator("#toggle-group-single")
    items = single.locator("[data-slot=toggle-group-item]")
    assert items.evaluate_all("l => l.map(i => [i.getAttribute('role'), i.getAttribute('aria-checked')])") == [["radio", "false"], ["radio", "true"], ["radio", "false"]]
    assert items.nth(1).get_attribute("tabindex") == "0"
    clear_log(page)
    items.nth(0).click()
    assert items.evaluate_all("l => l.map(i => i.getAttribute('aria-checked'))") == ["true", "false", "false"]
    items.nth(0).click()
    assert items.evaluate_all("l => l.map(i => i.getAttribute('aria-checked'))") == ["false", "false", "false"]
    assert [d["value"] for d in recorded(page, "toggle-group:change")] == ["start", ""]

    vertical = page.locator("#toggle-group-vertical")
    assert style(vertical, "flex-direction") == "column" and style(vertical, "gap") == "4px"
    vitems = vertical.locator("button")
    assert vitems.evaluate_all("l => l.map(i => i.getAttribute('aria-pressed'))") == ["true", "true", "false"]
    vitems.nth(0).focus()
    page.keyboard.press("ArrowDown")
    assert focused(page) == "Toggle italic"
    page.keyboard.press("ArrowUp")
    assert focused(page) == "Toggle bold"
    spacing = page.locator("#toggle-group-spacing")
    assert style(spacing, "gap") == "8px"
    top = spacing.get_by_role("radio", name="Top")
    assert style(top, "background-color") == token(page, "muted")
    assert style(top, side(t, "border-left-width")) == "1px" and style(top, side(t, "border-top-left-radius")) != "0px"
    assert near(spacing.locator("button").first.bounding_box()["height"], 28)
    outlined = page.locator("#toggle-group-outline-vertical button")
    assert style(outlined.nth(1), "border-top-width") == "0px"
    for b in page.locator("#toggle-group-disabled button").all():
        assert b.is_disabled()
    weight = page.locator("#toggle-group-weight")
    weight.get_by_role("radio", name="Bold").click()
    assert page.locator("#toggle-group-weight-text code").inner_text() == "font-bold"
    t.shot()


FIXTURE = """async () => {
  const { h } = await import("/clanker-ui.js")
  const select = (name, value) => h("div", { "data-slot": "select", "data-name": name, "data-required": true, "data-value": value },
    h("button", { "data-slot": "select-trigger", id: `${name}-trigger` }, h("span", { "data-slot": "select-value" }, "Pick a plan")),
    h("div", { "data-slot": "select-content", "data-position": "popper" }, ["free", "pro", "team"].map(v => h("div", { "data-slot": "select-item", "data-value": v }, v.toUpperCase()))))
  const combobox = name => h("div", { "data-slot": "combobox", "data-name": name, "data-required": true },
    h("div", { "data-slot": "input-group" }, h("input", { "data-slot": "input-group-control", id: `${name}-input`, "aria-label": name })),
    h("div", { "data-slot": "combobox-content" }, h("div", { "data-slot": "combobox-list" }, ["red", "green"].map(v => h("div", { "data-slot": "combobox-item", "data-value": v }, v)))))
  const form = h("form", { id: "fx-form", onsubmit: e => e.preventDefault() }, select("plan"), select("tier", "pro"), combobox("color"), h("button", { id: "fx-submit" }, "Send"))
  document.body.prepend(form)
  await new Promise(r => setTimeout(r, 0))
}"""


def check_select_reinsert(t):
    page = t.page
    page.evaluate(FIXTURE)
    result = page.evaluate(
        """async () => {
          const tick = () => new Promise(r => setTimeout(r, 0))
          const form = document.getElementById("fx-form")
          const plan = form.querySelector('[data-name="plan"]')
          const tier = form.querySelector('[data-name="tier"]')
          const color = form.querySelector('[data-name="color"]')
          plan.querySelector('[data-value="free"]').click()
          color.querySelector('[data-value="red"]').click()
          for (const root of [plan, tier, color]) {
            const parent = root.parentNode, next = root.nextSibling
            root.remove()
            await tick()
            parent.insertBefore(root, next)
            await tick()
          }
          const kept = [plan.dataset.value, new FormData(form).getAll("color")]
          plan.querySelector('[data-value="team"]').click()
          const proxies = [plan, tier, color].map(r => r.querySelectorAll(':scope > input[aria-hidden="true"]').length)
          const data = new FormData(form)
          const values = [data.getAll("plan"), data.getAll("tier"), data.getAll("color")]
          form.reset()
          await new Promise(r => setTimeout(r, 30))
          const reset = new FormData(form)
          const label = el => el.querySelector('[data-slot="select-value"]').textContent.trim()
          return { kept, proxies, values, reset: [reset.getAll("plan"), reset.getAll("tier"), reset.getAll("color")], labels: [label(plan), label(tier)] }
        }"""
    )
    assert result == {
        "kept": ["free", ["red"]],
        "proxies": [1, 1, 1],
        "values": [["team"], ["pro"], ["red"]],
        "reset": [[""], ["pro"], [""]],
        "labels": ["Pick a plan", "PRO"],
    }, result


def check_select_required_native(t):
    page = t.page
    page.evaluate(FIXTURE)
    page.locator("#fx-submit").click()
    assert page.evaluate("document.activeElement.id") == "plan-trigger", page.evaluate("document.activeElement.outerHTML.slice(0, 120)")
    page.evaluate("() => document.querySelector('#fx-form [data-name=plan] [data-value=pro]').click()")
    page.locator("#fx-submit").click()
    assert page.evaluate("document.activeElement.id") == "color-input"
    assert page.evaluate("document.getElementById('fx-form').checkValidity()") is False
    assert page.evaluate("document.activeElement.id") == "color-input"


def check_select_trigger_toggle(t):
    page = t.page
    t.section("select")
    record(page, ["select:open", "select:close"])
    for root_id in ["select-demo", "select-groups"]:
        root, trigger, content = select_parts(page, root_id)
        trigger.evaluate("e => e.scrollIntoView({ block: 'center' })")
        clear_log(page)
        box = trigger.bounding_box()
        page.mouse.click(box["x"] + 8, box["y"] + box["height"] / 2)
        wait_open(page, content)
        t.settle()
        assert content.get_attribute("data-align-trigger") == ("true" if root_id == "select-demo" else "false")
        page.mouse.click(box["x"] + 8, box["y"] + box["height"] / 2)
        wait_open(page, content, False)
        page.wait_for_timeout(200)
        assert not popover_open(content), root_id
        assert recorded(page) == ["select:open", "select:close"], (root_id, recorded(page))


CHOICE_FORMS = """async () => {
  const { h } = await import("/clanker-ui.js")
  const tick = () => new Promise(r => setTimeout(r, 0))
  const box = (name, extra = {}) => h("button", { type: "button", "data-slot": "checkbox", "data-name": name, "data-checked": true, ...extra })
  const c1 = box("a"), c2 = box("news"), s1 = h("button", { type: "button", "data-slot": "switch", "data-name": "s", "data-checked": true })
  const r1 = h("div", { "data-slot": "radio-group", "data-name": "r", "data-value": "x" }, h("button", { type: "button", "data-slot": "radio-group-item", value: "x" }))
  const f1 = h("form", {}, c1, c2, s1, r1), f2 = h("form", {})
  document.body.append(f1, f2)
  await tick()
  const data = f => [...new FormData(f)].map(([k, v]) => `${k}=${v}`)
  const before = [data(f1), data(f2)]
  c2.remove()
  await tick()
  const removed = data(f1)
  f2.append(c1, s1, r1)
  await tick()
  const moved = [data(f1), data(f2), [c1, s1].map(b => b.nextElementSibling?.getAttribute("aria-hidden"))]
  f2.after(c2)
  f1.append(c2)
  await tick()
  const back = data(f1)
  c1.click()
  await tick()
  const clicked = [data(f2), c1.getAttribute("aria-checked")]
  f1.remove(); f2.remove()
  return { before, removed, moved, back, clicked }
}"""


def check_choice_forms(t):
    result = t.page.evaluate(CHOICE_FORMS)
    assert result["before"] == [["a=on", "news=on", "s=on", "r=x"], []], result
    assert result["removed"] == ["a=on", "s=on", "r=x"], result
    assert result["moved"] == [[], ["a=on", "s=on", "r=x"], ["true", "true"]], result
    assert result["back"] == ["news=on"], result
    assert result["clicked"] == [["s=on", "r=x"], "false"], result


OLD_INPUTS = """async () => {
  const { h } = await import("/clanker-ui.js")
  const old = h("input", { type: "checkbox", "data-slot": "checkbox", name: "old", checked: true })
  const sw = h("input", { type: "checkbox", "data-slot": "switch", name: "sw" })
  const form = h("form", {}, old, sw)
  document.body.append(form)
  await new Promise(r => setTimeout(r, 0))
  const events = []
  form.addEventListener("change", e => events.push(e.target === old ? "old" : e.target === sw ? "sw" : "other"))
  form.addEventListener("checkbox:change", () => events.push("checkbox:change"))
  const attrs = el => [el.getAttribute("role"), el.getAttribute("aria-checked"), el.dataset.state ?? null, el.nextElementSibling?.localName ?? null]
  const start = [attrs(old), attrs(sw), old.checked, form.querySelectorAll("input").length]
  old.click()
  sw.click()
  const after = [old.checked, sw.checked, events, form.querySelectorAll("input").length, [...new FormData(form)].map(([k, v]) => `${k}=${v}`)]
  form.remove()
  return { start, after }
}"""


def check_choice_old_input(t):
    result = t.page.evaluate(OLD_INPUTS)
    assert result["start"] == [[None, None, None, "input"], [None, None, None, None], True, 2], result
    assert result["after"] == [False, True, ["old", "sw"], 2, ["sw=on"]], result


MIXED_RESET = """async () => {
  const { h } = await import("/clanker-ui.js")
  const box = h("button", { type: "button", "data-slot": "checkbox", "data-name": "all", "data-indeterminate": true })
  const plain = h("button", { type: "button", "data-slot": "checkbox", "data-name": "one", "data-checked": true })
  const form = h("form", {}, box, plain)
  document.body.append(form)
  await new Promise(r => setTimeout(r, 0))
  box.click()
  plain.click()
  const clicked = [box.getAttribute("aria-checked"), plain.getAttribute("aria-checked")]
  form.reset()
  await new Promise(r => setTimeout(r, 30))
  const reset = [box.getAttribute("aria-checked"), box.hasAttribute("data-indeterminate"), box.nextElementSibling.indeterminate, plain.getAttribute("aria-checked")]
  form.remove()
  return { clicked, reset }
}"""


def check_choice_reset_mixed(t):
    result = t.page.evaluate(MIXED_RESET)
    assert result == {"clicked": ["true", "false"], "reset": ["mixed", True, True, "true"]}, result


SELECT_FIXTURE = """async () => {
  const { h } = await import("/clanker-ui.js")
  const root = h("div", { "data-slot": "select", id: "fx-select" },
    h("button", { "data-slot": "select-trigger", id: "fx-select-trigger" }, h("span", { "data-slot": "select-value" }, "Select a fruit")),
    h("div", { "data-slot": "select-content" }, ["", "apple", "banana"].map(v => h("div", { "data-slot": "select-item", "data-value": v }, v ? v[0].toUpperCase() + v.slice(1) : "Select a fruit"))))
  const before = h("button", { type: "button", id: "fx-before" }, "Before")
  document.getElementById("select").prepend(before, root)
  await new Promise(r => setTimeout(r, 0))
}"""


def check_select_open_state(t):
    page = t.page
    t.section("select")
    page.evaluate(SELECT_FIXTURE)
    trigger = page.locator("#fx-select-trigger")
    content = page.locator("#fx-select [data-slot=select-content]")
    placeholder = page.locator("#fx-select [data-slot=select-item][data-value='']")
    assert trigger.get_attribute("tabindex") == "0" and trigger.get_attribute("data-placeholder") == ""
    assert placeholder.get_attribute("aria-selected") == "true" and placeholder.get_attribute("data-selected") == ""
    assert placeholder.locator("[data-slot=select-item-indicator]").count() == 1
    trigger.evaluate("e => e.scrollIntoView({ block: 'center' })")
    box = trigger.bounding_box()
    page.mouse.click(box["x"] + 8, box["y"] + box["height"] / 2)
    wait_open(page, content)
    assert focused(page) == "Select a fruit" and not page.evaluate("document.activeElement.matches(':focus-visible')")
    page.keyboard.press("ArrowDown")
    assert focused(page) == "Apple"
    away = page.locator("#select [data-demo=description]").bounding_box()
    page.mouse.click(away["x"] + 2, away["y"] + away["height"] / 2)
    wait_open(page, content, False)
    page.wait_for_function("() => document.activeElement.id === 'fx-select-trigger'", timeout=3000)
    page.locator("#fx-before").focus()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "fx-select-trigger"
    box = trigger.bounding_box()
    page.mouse.click(box["x"] + 8, box["y"] + box["height"] / 2)
    wait_open(page, content)
    assert focused(page) == "Select a fruit" and page.evaluate("document.activeElement.matches(':focus-visible')")
    page.locator("#fx-select [data-slot=select-item][data-value=apple]").click()
    wait_open(page, content, False)
    assert page.evaluate("[document.activeElement.id, document.activeElement.matches(':focus-visible')]") == ["fx-select-trigger", True]
    page.keyboard.press("x")
    page.keyboard.press(" ")
    wait_open(page, content)
    page.keyboard.press("x")
    page.keyboard.press(" ")
    wait_open(page, content, False)


COMBO_FIXTURE = """async () => {
  const { h } = await import("/clanker-ui.js")
  const root = h("div", { "data-slot": "combobox", id: "fx-combo", "data-name": "fx" },
    h("div", { "data-slot": "input-group" }, h("input", { "data-slot": "input-group-control", id: "fx-combo-input", placeholder: "Select a framework" }),
      h("div", { "data-slot": "input-group-addon", "data-align": "inline-end" }, h("button", { type: "button", "data-slot": "combobox-clear" }), h("button", { type: "button", "data-slot": "input-group-button", "data-combobox-trigger": "" }))),
    h("div", { "data-slot": "combobox-content" }, h("div", { "data-slot": "combobox-empty" }, "No items found."),
      h("div", { "data-slot": "combobox-list", tabindex: "0" }, ["Next.js", "Nuxt.js", "Remix"].map(v => h("div", { "data-slot": "combobox-item", "data-value": v }, v)))))
  document.getElementById("combobox").prepend(root)
  await new Promise(r => setTimeout(r, 0))
}"""


def check_combobox_base_ui(t):
    page = t.page
    t.section("combobox")
    page.evaluate(COMBO_FIXTURE)
    root = page.locator("#fx-combo")
    inp = page.locator("#fx-combo-input")
    trigger = root.locator("[data-combobox-trigger]")
    content = root.locator("[data-slot=combobox-content]")
    assert trigger.get_attribute("aria-label") == "Show options" and trigger.get_attribute("tabindex") == "0"
    empty = root.locator("[data-slot=combobox-empty]")
    assert [empty.get_attribute(a) for a in ["role", "aria-live", "aria-atomic"]] == ["status", "polite", "true"]
    assert [content.get_attribute("tabindex"), root.locator("[data-slot=combobox-list]").get_attribute("tabindex")] == ["-1", "0"]
    inp.click()
    wait_open(page, content)
    dismiss = root.locator("[data-slot=input-group] > [role=button][aria-label=Dismiss]")
    assert dismiss.count() == 1 and dismiss.evaluate("e => [e.nextElementSibling.id, e.style.clipPath, e.style.position]") == ["fx-combo-input", "inset(50%)", "absolute"]
    inp.press_sequentially("r")
    y = page.evaluate("scrollY")
    for name, caret in [("Home", 0), ("End", 1)]:
        page.keyboard.press(name)
        page.wait_for_timeout(100)
        assert page.evaluate("scrollY") == y and inp.evaluate("i => i.selectionStart") == caret, name
    inp.fill("")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    wait_open(page, content, False)
    assert dismiss.count() == 0
    assert inp.input_value() == "Nuxt.js" and trigger.get_attribute("data-placeholder") is None
    assert root.locator("[data-slot=combobox-clear]").get_attribute("tabindex") == "-1"
    page.keyboard.press("Escape")
    page.wait_for_timeout(100)
    assert inp.input_value() == "" and root.locator("input[aria-hidden=true]").input_value() == "" and trigger.get_attribute("data-placeholder") == ""
    inp.click()
    wait_open(page, content)
    dismiss.dispatch_event("click")
    wait_open(page, content, False)
    multi = page.locator("#combobox-multiple")
    assert multi.locator("[data-slot=combobox-chip]").count() == 1
    multi.locator("[data-slot=combobox-chip-input]").focus()
    page.keyboard.press("Escape")
    page.wait_for_timeout(100)
    assert multi.locator("[data-slot=combobox-chip]").count() == 0 and multi.locator("input[aria-hidden=true]").evaluate_all("l => l.map(i => i.value).join()") == ""


def check_choice_disabled_focus(t):
    page = t.page
    t.section("checkbox")
    page.locator("#checkbox-terms").click()
    assert page.evaluate("document.activeElement.id") == "checkbox-terms"
    page.locator("#checkbox-disabled").click(force=True)
    assert page.evaluate("document.activeElement.id") == "checkbox-terms"
    t.section("switch")
    page.locator("#switch-airplane").click()
    page.locator("#switch-disabled").click(force=True)
    assert page.evaluate("document.activeElement.id") == "switch-airplane"


def check_toggle_tab(t):
    page = t.page
    t.section("toggle")
    tg = page.locator("#toggle-bookmark")
    assert tg.get_attribute("tabindex") == "0"
    page.evaluate("() => document.getElementById('toggle-bookmark').before(Object.assign(document.createElement('span'), { id: 'fx-before-toggle', tabIndex: 0 }))")
    page.locator("#fx-before-toggle").focus()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "toggle-bookmark"
    t.section("button")
    assert page.locator("#button button[data-slot=button]").evaluate_all("l => [...new Set(l.map(b => b.getAttribute('tabindex')))]") == ["0"]


def check_slider_pointer_focus(t):
    page = t.page
    t.section("slider")
    root = page.locator("#slider-demo")
    page.evaluate("() => document.getElementById('slider-demo').before(Object.assign(document.createElement('span'), { id: 'fx-before-slider', tabIndex: 0 }))")
    page.locator("#fx-before-slider").focus()
    page.keyboard.press("Tab")
    page.keyboard.press("Shift+Tab")
    box = root.bounding_box()
    page.mouse.click(box["x"] + box["width"] * 0.25, box["y"] + box["height"] / 2)
    assert page.evaluate("[document.activeElement.type, document.activeElement.matches(':focus-visible')]") == ["range", False]


def check_text_entry_size(t):
    page = t.page
    sizes = page.evaluate(
        """() => ['#native-select [data-slot=native-select]', '#command [data-slot=command-input]', '[data-slot=combobox-chip-input]', '#input [data-slot=input]', '#textarea [data-slot=textarea]']
          .map(s => getComputedStyle(document.querySelector(s)).fontSize)"""
    )
    entry = "16px" if t.width < 768 else "14px"
    assert sizes == ["14px", "14px", "14px", entry, entry], sizes


def check_forced_colors(t):
    page = t.page
    page.emulate_media(forced_colors="active")
    if not page.evaluate("matchMedia('(forced-colors: active)').matches"):
        t.skip("engine has no forced-colors emulation")
    t.a11y()
    keyboard_mode(page)
    t.section("switch")
    result = page.evaluate(
        """() => {
          const pick = (sel, prop = 'backgroundColor') => getComputedStyle(document.querySelector(sel))[prop]
          return {
            switchOn: [pick('#switch-default'), pick('#switch-default [data-slot=switch-thumb]')],
            switchOff: [pick('#switch-share'), pick('#switch-share [data-slot=switch-thumb]')],
            checkbox: [pick('#checkbox-terms-2'), pick('#checkbox-terms-2', 'color'), pick('#checkbox-terms-2 [data-slot=checkbox-indicator] svg', 'stroke')],
            slider: [pick('#slider [data-slot=slider-track]'), pick('#slider [data-slot=slider-range]')],
          }
        }"""
    )
    assert page.evaluate("document.querySelector('#switch-default').getAttribute('aria-checked') === 'true' && document.querySelector('#switch-share').getAttribute('aria-checked') === 'false'")
    assert result["switchOn"][0] != result["switchOn"][1] and result["switchOff"][0] != result["switchOff"][1], result
    assert result["checkbox"][0] != result["checkbox"][1], result
    assert result["slider"][0] != result["slider"][1], result
    t.shot("forced-colors", page.locator("#switch"))


def check_forced_colors_scheme(t):
    page = t.page
    t.a11y()
    for scheme, background in [("nord", "rgb(46, 52, 64)"), ("tokyonight-storm", "rgb(36, 40, 59)" if t.theme == "dark" else "rgb(225, 226, 231)")]:
        page.emulate_media(forced_colors="none")
        page.evaluate("async s => (await import('/clanker-ui.js')).theme.setScheme(s)", scheme)
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == background, scheme
        page.emulate_media(forced_colors="active")
        if not page.evaluate("matchMedia('(forced-colors: active)').matches"):
            t.skip("engine has no forced-colors emulation")
        t.section("switch")
        result = page.evaluate(
            """() => {
              const probe = document.body.appendChild(document.createElement("span"))
              probe.style.backgroundColor = "Canvas"
              probe.style.color = "CanvasText"
              const system = [getComputedStyle(probe).backgroundColor, getComputedStyle(probe).color]
              probe.style.backgroundColor = "rgb(1, 2, 3)"
              const forced = getComputedStyle(probe).backgroundColor !== "rgb(1, 2, 3)"
              probe.remove()
              const pick = (sel, pseudo) => getComputedStyle(document.querySelector(sel), pseudo).backgroundColor
              return {
                forced,
                system,
                body: [getComputedStyle(document.body).backgroundColor, getComputedStyle(document.body).color],
                switchOn: [pick('#switch-default'), pick('#switch-default [data-slot=switch-thumb]')],
                checkbox: [pick('#checkbox-terms-2'), getComputedStyle(document.querySelector('#checkbox-terms-2')).color],
                slider: [pick('#slider [data-slot=slider-track]'), pick('#slider [data-slot=slider-range]')],
              }
            }"""
        )
        assert not result["forced"] or result["body"] == result["system"], (scheme, result)
        assert result["switchOn"][0] != result["switchOn"][1] and result["checkbox"][0] != result["checkbox"][1] and result["slider"][0] != result["slider"][1], (scheme, result)
        t.shot(f"forced-colors-{scheme}", page.locator("#switch"))


def check_form_reset_cancelled(t):
    page = t.page
    page.evaluate(FIXTURE)
    result = page.evaluate(
        """async () => {
          const { h, calendarSetValue } = await import("/clanker-ui.js")
          const wait = () => new Promise(r => setTimeout(r, 30))
          const form = document.getElementById("fx-form")
          const day = h("div", { "data-slot": "calendar", "data-month": "2026-01", "data-value": "2026-01-10", "data-name": "day" })
          form.append(day)
          await wait()
          form.querySelector('[data-name="plan"] [data-value="team"]').click()
          form.querySelector('[data-name="color"] [data-value="red"]').click()
          calendarSetValue(day, "2026-01-20")
          const values = () => {
            const data = new FormData(form)
            return [data.getAll("plan"), data.getAll("color"), data.getAll("day"), form.querySelector('[data-name="plan"] [data-slot="select-value"]').textContent.trim()]
          }
          const before = values()
          form.addEventListener("reset", event => event.preventDefault(), { once: true })
          form.reset()
          await wait()
          const cancelled = values()
          form.reset()
          await wait()
          return { before, cancelled, reset: values() }
        }"""
    )
    assert result["before"] == [["team"], ["red"], ["2026-01-20"], "TEAM"], result
    assert result["cancelled"] == result["before"], ("a cancelled reset keeps the select, combobox, and calendar values", result)
    assert result["reset"] == [[""], [""], ["2026-01-10"], "Pick a plan"], result


def check_flag_false(t):
    page = t.page
    t.section("select")
    result = page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const wait = () => new Promise(r => setTimeout(r, 30))
          const select = h("div", { "data-slot": "select", "data-name": "fx-flag-select" },
            h("button", { "data-slot": "select-trigger" }, h("span", { "data-slot": "select-value" }, "Pick")),
            h("div", { "data-slot": "select-content", "data-position": "popper" }, h("div", { "data-slot": "select-item", "data-value": "a", "data-disabled": "false" }, "A")))
          const combo = multiple => h("div", { "data-slot": "combobox", "data-name": `fx-flag-${multiple}`, "data-multiple": multiple },
            h("div", { "data-slot": "input-group" }, h("input", { "data-slot": "input-group-control", "aria-label": "Flag" })),
            h("div", { "data-slot": "combobox-content" }, h("div", { "data-slot": "combobox-list" }, h("div", { "data-slot": "combobox-item", "data-value": "a", "data-disabled": "false" }, "A"), h("div", { "data-slot": "combobox-item", "data-value": "b" }, "B"))))
          const single = combo("false")
          const form = h("form", null, select, single)
          document.body.prepend(form)
          await wait()
          const item = select.querySelector("[data-slot=select-item]")
          const disabledAttr = [item.getAttribute("aria-disabled"), single.querySelector("[data-value=a]").getAttribute("aria-disabled")]
          item.click()
          single.querySelector("[data-value=a]").click()
          const data = new FormData(form)
          const out = { disabledAttr, select: data.getAll("fx-flag-select"), combo: data.getAll("fx-flag-false"), multi: single.querySelector("[data-slot=combobox-list]").getAttribute("aria-multiselectable") }
          form.remove()
          return out
        }"""
    )
    assert result == {"disabledAttr": [None, None], "select": ["a"], "combo": ["a"], "multi": None}, ('data-disabled="false" items can be chosen; data-multiple="false" is single', result)


def check_select_late_items(t):
    page = t.page
    t.section("select")
    result = page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const wait = () => new Promise(r => setTimeout(r, 30))
          const events = []
          const select = h("div", { "data-slot": "select", "data-name": "fx-late-select", "data-value": "b" },
            h("button", { "data-slot": "select-trigger" }, h("span", { "data-slot": "select-value" }, "Pick")),
            h("div", { "data-slot": "select-content", "data-position": "popper" }))
          const combo = h("div", { "data-slot": "combobox", "data-name": "fx-late-combo", "data-value": "b" },
            h("div", { "data-slot": "input-group" }, h("input", { "data-slot": "input-group-control", "aria-label": "Late" })),
            h("div", { "data-slot": "combobox-content" }, h("div", { "data-slot": "combobox-list" })))
          const form = h("form", null, select, combo)
          for (const n of ["change", "input", "select:change", "combobox:change"]) form.addEventListener(n, () => events.push(n))
          document.body.prepend(form)
          await wait()
          const label = () => [select.querySelector("[data-slot=select-value]").textContent.trim(), combo.querySelector("input[data-slot]").value]
          const values = () => { const d = new FormData(form); return [d.get("fx-late-select"), d.get("fx-late-combo")] }
          const early = [label(), values(), select.dataset.value]
          select.querySelector("[data-slot=select-content]").append(...["a", "b"].map(v => h("div", { "data-slot": "select-item", "data-value": v }, v.toUpperCase())))
          combo.querySelector("[data-slot=combobox-list]").append(...["a", "b"].map(v => h("div", { "data-slot": "combobox-item", "data-value": v }, v.toUpperCase())))
          await wait()
          const late = [label(), values()]
          let records = 0
          const mo = new MutationObserver(list => { records += list.filter(r => r.attributeName === "data-value").length })
          for (const el of [select, combo]) mo.observe(el, { attributes: true })
          select.dataset.value = "a"
          combo.dataset.value = "a"
          await wait()
          mo.disconnect()
          const changed = [label(), values(), select.querySelector("[aria-selected=true]")?.dataset.value, combo.querySelector("[aria-selected=true]")?.dataset.value]
          form.remove()
          return { early, late, changed, records, events }
        }"""
    )
    assert result["early"] == [["Pick", ""], ["", ""], "b"], result
    assert result["late"] == [["B", "B"], ["b", "b"]], ("items that arrive later select the authored data-value", result)
    assert result["changed"] == [["A", "A"], ["a", "a"], "a", "a"], ("a later data-value change selects the item", result)
    assert result["records"] < 10 and result["events"] == [], ("no mutation loop and no change event", result)


def check_choice_reenable(t):
    page = t.page
    t.section("checkbox")
    result = page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const wait = () => new Promise(r => setTimeout(r, 30))
          const box = h("button", { "data-slot": "checkbox" })
          const sw = h("button", { "data-slot": "switch" })
          const radio = h("button", { "data-slot": "radio-group-item", value: "a" })
          const host = h("div", null, box, sw, h("div", { "data-slot": "radio-group" }, radio))
          document.body.prepend(host)
          await wait()
          const out = []
          for (const el of [box, sw, radio]) {
            el.disabled = true
            await wait()
            const off = [el.disabled, el.getAttribute("aria-disabled"), el.hasAttribute("data-disabled")]
            el.click()
            const stays = el.getAttribute("aria-checked")
            el.disabled = false
            await wait()
            const on = [el.disabled, el.getAttribute("aria-disabled"), el.hasAttribute("data-disabled"), el.tabIndex]
            el.click()
            out.push([off, stays, on, el.getAttribute("aria-checked")])
            el.setAttribute("disabled", "")
            await wait()
            out.push([el.disabled, el.hasAttribute("disabled")])
          }
          host.remove()
          return out
        }"""
    )
    for name, (off, stays, on, checked), again in zip(["checkbox", "switch", "radio"], result[0::2], result[1::2]):
        assert off == [True, "true", True] and stays == "false", (name, "disabled = true disables", off, stays)
        assert on[:3] == [False, None, False] and on[3] == 0 and checked == "true", (name, "disabled = false enables again", on, checked)
        assert again == [True, False], (name, "the disabled attribute still disables", again)


def check_slider_programmatic(t):
    page = t.page
    t.section("slider")
    result = page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const frame = () => new Promise(r => requestAnimationFrame(() => setTimeout(r, 30)))
          const input = h("input", { type: "range", min: "0", max: "100", value: "20", "aria-label": "Volume" })
          const root = h("div", { "data-slot": "slider" }, input)
          document.getElementById("slider").prepend(root)
          await frame()
          const thumb = root.querySelector("[data-slot=slider-thumb]")
          const pos = () => thumb.style.getPropertyValue("--position")
          const start = pos()
          input.value = "80"
          input.dispatchEvent(new Event("input", { bubbles: true }))
          const value = [input.getAttribute("aria-valuenow"), pos() !== start, pos().includes("0.8 ")]
          input.disabled = true
          await frame()
          const disabled = [root.hasAttribute("data-disabled"), thumb.hasAttribute("data-disabled")]
          input.disabled = false
          input.max = "200"
          await frame()
          const after = [root.hasAttribute("data-disabled"), pos().includes("0.4 ")]
          root.remove()
          return { value, disabled, after }
        }"""
    )
    assert result == {"value": ["80", True, True], "disabled": [True, True], "after": [False, True]}, ("code changes update the slider", result)
