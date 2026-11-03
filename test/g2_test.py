LISTEN = """names => {
  window.__g2 = []
  for (const name of names) document.addEventListener(name, event => {
    const detail = {}
    for (const [key, value] of Object.entries(event.detail || {})) if (!(value instanceof Node) && typeof value !== "function") detail[key] = value
    window.__g2.push([name, detail])
  })
}"""


def listen(page, *names):
    page.evaluate(LISTEN, list(names))


def events(page, name=None):
    found = page.evaluate("window.__g2")
    return [e for e in found if name is None or e[0] == name]


def wait(page, script, arg=None, timeout=3000):
    page.wait_for_function(script, arg=arg, timeout=timeout)


def active(page, script="e => e.textContent.trim()"):
    return page.evaluate(f"() => {{ const e = document.activeElement; return e ? ({script})(e) : null }}")


def is_open(loc):
    return loc.evaluate("e => e instanceof HTMLDialogElement ? e.open : e.matches(':popover-open')")


def box(loc):
    return loc.bounding_box()


def viewport(page):
    return page.evaluate("() => [document.documentElement.clientWidth, document.documentElement.clientHeight]")


def key(t, name):
    return {"ArrowLeft": "ArrowRight", "ArrowRight": "ArrowLeft"}.get(name, name) if t.rtl else name


def inline(t, b):
    if not t.rtl:
        return b
    width, height = viewport(t.page)
    return {**b, "x": width - b["x"] - b["width"]}


def px(t, x):
    return viewport(t.page)[0] - x if t.rtl else x


def keyboard_focus(page, loc):
    page.keyboard.press("Shift")
    loc.focus()


def away(page):
    width, height = viewport(page)
    page.mouse.move(3, height - 3, steps=6)


def check_dialog(t):
    page = t.page
    section = t.section("dialog")
    listen(page, "dialog:open", "dialog:close")
    trigger = section.get_by_role("button", name="Open Dialog")
    content = section.locator("#dialog-demo [data-slot=dialog-content]")
    assert trigger.get_attribute("aria-haspopup") == "dialog"
    assert trigger.get_attribute("aria-expanded") == "false"
    trigger.click()
    dialog = page.get_by_role("dialog", name="Edit profile")
    assert dialog.is_visible()
    assert content.get_attribute("data-state") == "open"
    assert trigger.get_attribute("aria-expanded") == "true"
    assert trigger.get_attribute("aria-controls") == content.get_attribute("id")
    assert page.evaluate("document.getElementById(document.querySelector('#dialog-demo dialog').getAttribute('aria-describedby')).textContent").startswith("Make changes")
    assert active(page, "e => e.id") == "dialog-name"
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") == "hidden"
    width, height = viewport(page)
    b = box(content)
    assert abs(b["x"] + b["width"] / 2 - width / 2) <= 2 and b["width"] <= width - 32 + 1, b
    t.settle()
    t.shot("dialog-open", page)
    page.keyboard.press("Shift+Tab")
    assert active(page, "e => e.dataset.slot") == "dialog-close"
    page.keyboard.press("Tab")
    assert active(page, "e => e.id") == "dialog-name"
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#dialog-demo dialog').open")
    assert content.get_attribute("data-state") == "closed"
    assert active(page) == "Open Dialog"
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") != "hidden"
    trigger.click()
    page.mouse.click(4, height - 4)
    wait(page, "() => !document.querySelector('#dialog-demo dialog').open")
    trigger.click()
    content.get_by_role("button", name="Save changes").click()
    wait(page, "() => !document.querySelector('#dialog-demo dialog').open")
    page.wait_for_selector("[data-slot=toast] >> text=Profile updated")
    page.evaluate("async () => (await import('/clanker-ui.js')).dialogOpen('dialog-demo')")
    assert is_open(content)
    content.locator(":scope > [data-slot=dialog-close]").click()
    wait(page, "() => !document.querySelector('#dialog-demo dialog').open")
    reasons = [e[1].get("reason") for e in events(page, "dialog:close")]
    assert reasons == ["escape", "outside", "submit", "close"], reasons
    assert len(events(page, "dialog:open")) == 4
    plain = section.get_by_role("button", name="No Close Button")
    plain.click()
    other = page.get_by_role("dialog", name="No Close Button")
    assert other.locator(":scope > [data-slot=dialog-close]").count() == 0
    page.keyboard.press("Escape")
    wait(page, "() => [...document.querySelectorAll('#dialog dialog')].every(d => !d.open)")
    section.get_by_role("button", name="Sticky Footer").click()
    sticky = page.get_by_role("dialog", name="Sticky Footer")
    sticky.locator("[data-slot=dialog-footer]").get_by_role("button", name="Close").click()
    wait(page, "() => [...document.querySelectorAll('#dialog dialog')].every(d => !d.open)")
    page.evaluate("() => document.addEventListener('dialog:close', e => e.preventDefault(), { once: true })")
    trigger.click()
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    assert is_open(content)
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#dialog-demo dialog').open")
    released = page.evaluate("""async () => {
      const { h, dialogOpen } = await import('/clanker-ui.js')
      const root = h('div', { 'data-slot': 'dialog' }, h('dialog', { 'data-slot': 'dialog-content' }, h('h2', { 'data-slot': 'dialog-title' }, 'Inserted later')))
      document.body.append(root)
      await new Promise(r => setTimeout(r, 0))
      const opened = dialogOpen(root)
      const named = root.querySelector('dialog').getAttribute('aria-labelledby') === root.querySelector('h2').id
      const locked = getComputedStyle(document.documentElement).overflow === 'hidden'
      root.remove()
      await new Promise(r => setTimeout(r, 50))
      return [opened, named, locked, getComputedStyle(document.documentElement).overflow !== 'hidden', !!root.querySelector('[data-slot=dialog-close]')]
    }""")
    assert released == [True, True, True, True, True], released
    t.shot()


def check_alert_dialog(t):
    page = t.page
    section = t.section("alert-dialog")
    listen(page, "alert-dialog:open", "alert-dialog:close")
    section.get_by_role("button", name="Show Dialog").first.click()
    dialog = page.get_by_role("alertdialog", name="Are you absolutely sure?")
    assert dialog.is_visible()
    assert active(page) == "Cancel"
    t.settle()
    t.shot("alert-dialog-open", page)
    width, height = viewport(page)
    page.mouse.click(4, height - 4)
    page.wait_for_timeout(250)
    assert dialog.is_visible()
    page.keyboard.press("Escape")
    wait(page, "() => !document.getElementById('alert-dialog-basic').open")
    assert active(page) == "Show Dialog"
    section.get_by_role("button", name="Show Dialog").first.click()
    dialog.get_by_role("button", name="Continue").click()
    page.wait_for_timeout(250)
    assert dialog.is_visible(), "the action is a plain button (shadcn AlertDialogAction)"
    dialog.get_by_role("button", name="Cancel").click()
    wait(page, "() => !document.getElementById('alert-dialog-basic').open")
    section.get_by_role("button", name="Show Dialog").nth(1).click()
    small = page.get_by_role("alertdialog", name="Allow accessory to connect?")
    t.settle()
    assert abs(box(small)["width"] - 320) <= 1
    buttons = small.locator("[data-slot=alert-dialog-footer] button")
    assert abs(box(buttons.nth(0))["width"] - box(buttons.nth(1))["width"]) <= 1
    small.get_by_role("button", name="Don't allow").click()
    wait(page, "() => !document.getElementById('alert-dialog-small').open")
    section.get_by_role("button", name="Share Project").click()
    media = page.locator("#alert-dialog-media")
    t.settle()
    m = inline(t, box(media.locator("[data-slot=alert-dialog-media]")))
    title = inline(t, box(media.locator("[data-slot=alert-dialog-title]")))
    if t.width >= 640:
        assert title["x"] >= m["x"] + m["width"], (m, title)
    else:
        assert title["y"] >= m["y"] + m["height"], (m, title)
    t.settle()
    t.shot("alert-dialog-media", page)
    page.keyboard.press("Escape")
    wait(page, "() => !document.getElementById('alert-dialog-media').open")
    section.get_by_role("button", name="Delete Chat").click()
    danger = page.locator("#alert-dialog-destructive")
    assert danger.get_by_role("button", name="Delete").get_attribute("data-variant") == "destructive"
    t.settle()
    t.shot("alert-dialog-destructive", page)
    danger.get_by_role("button", name="Delete").click()
    page.wait_for_timeout(250)
    assert danger.evaluate("e => e.open")
    danger.get_by_role("button", name="Cancel").click()
    wait(page, "() => !document.getElementById('alert-dialog-destructive').open")
    reasons = [e[1].get("reason") for e in events(page, "alert-dialog:close")]
    assert reasons == ["escape", "cancel", "cancel", "escape", "cancel"], reasons


def check_sheet(t):
    page = t.page
    section = t.section("sheet")
    listen(page, "sheet:open", "sheet:close")
    width, height = viewport(page)
    section.get_by_role("button", name="Open", exact=True).click()
    sheet = page.get_by_role("dialog", name="Edit profile")
    t.settle()
    b = box(sheet)
    assert abs(b["x"] + b["width"] - width) <= 1 and abs(b["height"] - height) <= 1, b
    assert abs(b["width"] - min(width * 0.75, 384 if width >= 640 else width)) <= 1, b
    t.shot("sheet-right", page)
    sheet.locator(":scope > [data-slot=sheet-close]").click()
    wait(page, "() => [...document.querySelectorAll('#sheet dialog')].every(d => !d.open)")
    assert active(page) == "Open"
    for side in ["Top", "Bottom", "Left", "Right"]:
        section.get_by_role("button", name=side, exact=True).click()
        content = section.locator("[data-demo~=preview]").nth(1).locator(f"dialog[data-side={side.lower()}]")
        t.settle()
        b = box(content)
        if side == "Top":
            assert abs(b["y"]) <= 1 and abs(b["width"] - width) <= 1, b
        elif side == "Bottom":
            assert abs(b["y"] + b["height"] - height) <= 1 and abs(b["width"] - width) <= 1, b
        elif side == "Left":
            assert abs(b["x"]) <= 1 and abs(b["height"] - height) <= 1, b
        else:
            assert abs(b["x"] + b["width"] - width) <= 1, b
        if side == "Left":
            t.shot("sheet-left", page)
        if side == "Bottom":
            t.shot("sheet-bottom", page)
        content.get_by_role("button", name="Cancel").click()
        wait(page, "() => [...document.querySelectorAll('#sheet dialog')].every(d => !d.open)")
    section.get_by_role("button", name="Open Sheet").click()
    plain = section.locator("[data-demo~=preview]").nth(2).locator("dialog")
    assert plain.is_visible()
    assert plain.locator(":scope > [data-slot=sheet-close]").count() == 0
    page.mouse.click(4, height - 4)
    wait(page, "() => [...document.querySelectorAll('#sheet dialog')].every(d => !d.open)")
    reasons = [e[1].get("reason") for e in events(page, "sheet:close")]
    assert reasons == ["close", "close", "close", "close", "close", "outside"], reasons


SHEET_FRAME = """() => {
  const c = document.querySelector('#sheet-demo [data-slot="sheet-content"]')
  const r = c.getBoundingClientRect()
  return [Math.round(r.x), +getComputedStyle(c).opacity, c.open, c.hasAttribute("data-starting-style"), c.hasAttribute("data-ending-style"), c.dataset.state, performance.now()]
}"""


def motion_time(frames, start, done):
    first = next((f for f in frames if start(f)), None)
    last = next((f for f in frames if first and f[-1] >= first[-1] and done(f)), None)
    assert first and last, ("the motion must start and end inside the sampled frames", frames[:3], frames[-3:])
    return last[-1] - first[-1]


def motion_retry(t, trigger, dialog, measure):
    page = t.page
    is_open = f"() => document.querySelector({dialog!r}).open"
    trigger.click()
    wait(page, is_open)
    t.settle()
    page.keyboard.press("Escape")
    wait(page, f"() => !({is_open})()")
    t.settle()
    for attempt in range(3):
        try:
            return measure()
        except (AssertionError, t.Starved):
            if attempt == 2:
                raise
            if page.evaluate(is_open):
                page.keyboard.press("Escape")
                wait(page, f"() => !({is_open})()")
            t.settle()


def check_sheet_motion(t):
    section = t.section("sheet")
    trigger = section.get_by_role("button", name="Open", exact=True)
    motion_retry(t, trigger, "#sheet-demo [data-slot=sheet-content]", lambda: sheet_motion(t, trigger))


def sheet_motion(t, trigger):
    page = t.page
    width, height = viewport(page)
    frames = t.paint(SHEET_FRAME, lambda: trigger.click(), ms=1200)
    shown = [f for f in frames if f[2]]
    assert shown, frames
    final = width - 384 if width >= 640 else width * 0.25
    end = shown[-1]
    assert end[1:6] == [1, True, False, False, "open"] and abs(end[0] - final) <= 1, (end, final)
    spent = motion_time(shown, lambda f: True, lambda f: f[1] == 1 and abs(f[0] - final) <= 1)
    assert spent <= 300, ("the sheet opens in 200 ms like shadcn", spent)
    if not t.reduced_motion:
        first = shown[0]
        assert first[1] < 0.2 and abs(first[0] - end[0]) >= 30, ("the sheet starts 2.5rem off and transparent", first, end)
        assert any(0.2 < f[1] < 0.95 for f in shown), shown
    content = page.locator("#sheet-demo [data-slot=sheet-content]")
    assert not content.evaluate("e => e.hasAttribute('data-starting-style')")
    frames = t.paint(SHEET_FRAME, lambda: content.locator(":scope > [data-slot=sheet-close]").click(), ms=1200)
    spent = motion_time(frames, lambda f: f[4] or not f[2], lambda f: not f[2] or f[1] <= 0.01)
    assert spent <= 300, ("the sheet closes in 200 ms like shadcn", spent)
    if not t.reduced_motion:
        ending = [f for f in frames if f[2] and f[4]]
        assert len(ending) >= 3 and ending[0][5] == "closed", frames
        assert min(f[1] for f in ending) < 0.2 and max(abs(f[0] - end[0]) for f in ending) >= 30, ending
    assert not frames[-1][2] and not frames[-1][4], frames[-1]
    assert content.evaluate("e => !e.open && !e.hasAttribute('data-ending-style') && !e.hasAttribute('data-starting-style')")


DRAWER_FRAME = """() => {
  const v = document.querySelector('#drawer-handle [data-slot="drawer-viewport"]')
  const p = v.querySelector('[data-slot="drawer-popup"]')
  const r = p.getBoundingClientRect()
  return [Math.round(r.y), v.open, p.hasAttribute("data-starting-style"), p.hasAttribute("data-ending-style"), v.hasAttribute("data-ending-style"), v.dataset.state, performance.now()]
}"""

TOUCH_SWIPE = """([sel, dy]) => {
  let probe
  try { probe = new Touch({ identifier: 1, target: document.body, clientX: 0, clientY: 0 }) } catch { return null }
  const c = document.querySelector(sel)
  const r = c.getBoundingClientRect()
  const x = r.left + r.width / 2, y = r.top + 30
  const touch = d => new Touch({ identifier: 3, target: c, clientX: x, clientY: y + d })
  const fire = (type, d, held) => c.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true, touches: held ? [touch(d)] : [], changedTouches: [touch(d)] }))
  fire("touchstart", 0, true)
  fire("touchmove", 8, true)
  fire("touchmove", dy, true)
  const popup = c.closest('[data-slot="drawer-popup"]')
  const mid = [popup.hasAttribute("data-swiping"), popup.style.getPropertyValue("--drawer-swipe-movement-y")]
  fire("touchend", dy, false)
  return mid
}"""


def tab_names(page, count, back=False):
    out = []
    for _ in range(count):
        page.keyboard.press("Shift+Tab" if back else "Tab")
        out.append(page.evaluate("() => { const e = document.activeElement; return e.getAttribute('aria-label') || e.textContent.trim() || e.id || e.dataset.slot }"))
    return out


def check_overlay_tab_order(t):
    page = t.page
    section = t.section("sheet")
    section.get_by_role("button", name="Open", exact=True).click()
    wait(page, "() => document.querySelector('#sheet-demo dialog').open")
    t.settle()
    first = page.evaluate("() => document.activeElement.id")
    assert first == "sheet-name", first
    assert tab_names(page, 5) == ["sheet-username", "Save changes", "Close", "Close", "sheet-name"], "Tab reaches every button in the sheet, also in WebKit"
    assert tab_names(page, 2, back=True) == ["Close", "Close"]
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#sheet-demo dialog').open")
    t.section("drawer")
    page.locator("#drawer-demo [data-drawer-trigger]").click()
    wait(page, "() => document.querySelector('#drawer-demo dialog').open")
    t.settle()
    assert tab_names(page, 5) == ["Decrease", "Increase", "Submit", "Cancel", "Decrease"], "Tab from the drawer popup moves through its buttons"
    assert tab_names(page, 1, back=True) == ["Cancel"]
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#drawer-demo dialog').open")
    page.locator("#drawer-demo [data-drawer-trigger]").click()
    wait(page, "() => document.querySelector('#drawer-demo dialog').open")
    t.settle()
    assert page.evaluate("() => document.activeElement.dataset.slot") == "drawer-popup"
    assert tab_names(page, 3, back=True) == ["Cancel", "Submit", "Increase"], "Shift+Tab from the drawer popup after a pointer open wraps to the last button like Base UI"
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#drawer-demo dialog').open")


TAB_WHERE = """() => {
  const a = document.activeElement
  if (!a) return null
  let d = a.id || a.localName
  if (a.shadowRoot?.activeElement) d += '>' + a.shadowRoot.activeElement.id
  if (a.localName === 'iframe') d += '>' + (a.contentDocument?.activeElement?.id || a.contentDocument?.activeElement?.localName)
  return d
}"""

TAB_LAB = """([kind, where]) => {
  const dialog = document.querySelector('#dialog-demo dialog')
  const host = where === 'page' ? document.querySelector('#dialog') : dialog.querySelector('[data-slot=field]')
  const wrap = document.createElement('div')
  wrap.id = 'tab-lab'
  const input = (id, attrs = {}) => {
    const e = document.createElement('input')
    e.id = id
    e.setAttribute('aria-label', id)
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v)
    return e
  }
  if (where !== 'first') wrap.append(input('pre'))
  if (kind === 'fieldset') {
    const set = document.createElement('fieldset')
    set.disabled = true
    set.append(input('in-set'))
    wrap.append(set)
  } else if (kind === 'editable' || kind === 'editable-link') {
    const box = document.createElement('div')
    box.id = 'editable'
    box.contentEditable = 'true'
    box.append('Edit ')
    if (kind === 'editable-link') {
      const link = document.createElement('a')
      link.href = '#editable'
      link.textContent = 'link'
      box.append(link)
    }
    wrap.append(box)
  } else if (kind === 'shadow') {
    const shadow = document.createElement('div')
    shadow.id = 'shadow'
    shadow.attachShadow({ mode: 'open' }).append(input('s1'), input('s2'))
    wrap.append(shadow)
  } else if (kind === 'date') wrap.append(input('date', { type: 'date' }))
  else if (kind === 'radio') for (const id of ['r1', 'r2', 'r3']) wrap.append(input(id, { type: 'radio', name: 'tab-lab-radio' }))
  else if (kind === 'positive') wrap.append(input('positive', { tabindex: '1' }))
  else if (kind === 'frame') {
    const frame = document.createElement('iframe')
    frame.id = 'frame'
    wrap.append(frame)
  }
  if (where !== 'last') wrap.append(input('post'))
  if (where === 'first') dialog.prepend(wrap)
  else if (where === 'last') dialog.append(wrap)
  else host.after(wrap)
  if (kind === 'frame') {
    const doc = wrap.querySelector('#frame').contentDocument
    for (const id of ['f1', 'f2']) {
      const e = doc.createElement('input')
      e.id = id
      doc.body.append(e)
    }
  }
}"""


def tab_walk(page, key, start, stop):
    page.focus(f"#{start}")
    seen = []
    for _ in range(10):
        page.keyboard.press(key)
        seen.append(page.evaluate(TAB_WHERE))
        if seen[-1] == stop:
            break
    return seen


def check_overlay_tab_native(t):
    page = t.page
    t.section("dialog")
    trigger = page.locator("#dialog-demo [data-dialog-trigger]")
    for kind in ("fieldset", "editable", "editable-link", "shadow", "date", "radio", "positive", "frame"):
        page.evaluate(TAB_LAB, [kind, "page"])
        native = [tab_walk(page, "Tab", "pre", "post"), tab_walk(page, "Shift+Tab", "post", "pre")]
        page.evaluate("() => document.getElementById('tab-lab').remove()")
        edges = kind in ("shadow", "date", "radio", "frame")
        fresh = []
        for key, start, stop in (("Tab", "pre", "post"), ("Shift+Tab", "post", "pre")) if edges else ():
            page.evaluate(TAB_LAB, [kind, "page"])
            fresh.append(tab_walk(page, key, start, stop))
            page.evaluate("() => document.getElementById('tab-lab').remove()")
        trigger.click()
        wait(page, "() => document.querySelector('#dialog-demo dialog').open")
        t.settle()
        page.evaluate(TAB_LAB, [kind, "middle"])
        trapped = [tab_walk(page, "Tab", "pre", "post"), tab_walk(page, "Shift+Tab", "post", "pre")]
        page.evaluate("() => document.getElementById('tab-lab').remove()")
        assert trapped == native, ("a modal keeps the browser Tab order between its edges", kind, trapped, native)
        if edges:
            first, last = page.evaluate("async () => { const { tabbables } = await import('/clanker-ui.js'); const s = tabbables(document.querySelector('#dialog-demo dialog')); return [s[0], s.at(-1)].map(a => a.id || a.localName) }")
            page.evaluate(TAB_LAB, [kind, "last"])
            tail = tab_walk(page, "Tab", "pre", first)
            page.evaluate("() => document.getElementById('tab-lab').remove()")
            page.evaluate(TAB_LAB, [kind, "first"])
            head = tab_walk(page, "Shift+Tab", "post", last)
            page.evaluate("() => document.getElementById('tab-lab').remove()")
            assert tail == fresh[0][:-1] + [first] and head == fresh[1][:-1] + [last], ("the modal edges keep the browser order and wrap like Base UI focus guards", kind, tail, head, fresh)
        page.keyboard.press("Escape")
        wait(page, "() => !document.querySelector('#dialog-demo dialog').open")
    trigger.click()
    wait(page, "() => document.querySelector('#dialog-demo dialog').open")
    t.settle()
    page.evaluate("""() => {
      const dialog = document.querySelector('#dialog-demo dialog')
      const tail = document.createElement('input')
      tail.id = 'tail'
      const plain = document.createElement('button')
      plain.id = 'plain'
      plain.textContent = 'Plain'
      dialog.append(tail, plain)
    }""")
    page.focus("#tail")
    for _ in range(3):
        page.keyboard.press("Tab")
        assert page.evaluate("() => document.querySelector('#dialog-demo dialog').contains(document.activeElement)"), ("Tab from the last field stays in the modal", page.evaluate(TAB_WHERE))
    first = page.evaluate("() => document.activeElement.id")
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Tab")
    assert page.evaluate("() => document.activeElement.id") == first
    page.evaluate("async () => (await import('/clanker-ui.js')).toast('In the modal', { id: 'tab-toast', timeout: 0 })")
    page.locator("[data-slot=toast]").filter(has_text="In the modal").wait_for()
    page.focus("#dialog-name")
    stops = []
    for _ in range(3):
        page.keyboard.press("Shift+Tab")
        stops.append(page.evaluate("() => [document.activeElement.closest('[data-slot=toast]') ? 'toast' : 'dialog', document.activeElement.getAttribute('aria-label') || document.activeElement.textContent.trim().slice(0, 20)]"))
    in_toast = any(where == "toast" for where, _ in stops)
    page.evaluate("async () => (await import('/clanker-ui.js')).toast.dismiss()")
    page.evaluate("() => { for (const id of ['tail', 'plain']) document.getElementById(id).remove() }")
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#dialog-demo dialog').open")
    assert in_toast, ("Shift+Tab reaches a toast in the modal", stops)


def drawer_open(page, root):
    page.locator(f"{root} [data-drawer-trigger]").first.click()
    wait(page, "s => document.querySelector(s + ' [data-slot=drawer-viewport]').open", root)


def drawer_closed(page, root):
    wait(page, "s => !document.querySelector(s + ' [data-slot=drawer-viewport]').open", root)


def check_drawer(t):
    page = t.page
    section = t.section("drawer")
    listen(page, "drawer:open", "drawer:close", "drawer:release")
    width, height = viewport(page)
    trigger = section.get_by_role("button", name="Open Drawer").first
    viewport_el = page.locator("#drawer-demo [data-slot=drawer-viewport]")
    popup = viewport_el.locator(":scope > [data-slot=drawer-popup]")
    trigger.click()
    t.settle()
    mobile = width < 768
    dom = viewport_el.evaluate("""v => {
      const p = v.querySelector(':scope > [data-slot=drawer-popup]')
      return [v.localName, v.dataset.modal, v.matches(':modal'), p.dataset.slot, p.dataset.swipeDirection, p.dataset.swipeAxis, p.getAttribute('tabindex'), [...p.children].map(c => c.dataset.slot), p.lastElementChild.hasAttribute('data-drawer-content'), document.activeElement === p, document.getElementById(v.getAttribute('aria-labelledby'))?.textContent, document.getElementById(v.getAttribute('aria-describedby'))?.textContent, p.hasAttribute('role'), v.hasAttribute('role')]
    }""")
    handle = ["drawer-swipe-handle"] if mobile else []
    assert dom == ["dialog", "true", True, "drawer-popup", "down" if mobile else "right", "y" if mobile else "x", "-1", handle + ["drawer-content"], True, True, "Move Goal", "Set your daily activity goal.", False, False], ("the native dialog is the dialog with its name and description", dom)
    assert page.get_by_role("dialog", name="Move Goal").evaluate("e => e.dataset.slot") == "drawer-viewport"
    if t.engine == "chromium":
        cdp = page.context.new_cdp_session(page)
        nodes = cdp.send("Accessibility.getFullAXTree")["nodes"]
        cdp.detach()
        dialogs = [n.get("name", {}).get("value", "") for n in nodes if not n.get("ignored") and n.get("role", {}).get("value") == "dialog"]
        assert dialogs == ["Move Goal"], ("the browser tree has one named dialog", dialogs)
    assert trigger.evaluate("e => [e.getAttribute('aria-expanded'), e.hasAttribute('data-popup-open'), e.getAttribute('aria-controls') === document.querySelector('#drawer-demo [data-slot=drawer-viewport]').id]") == ["true", True, True]
    b = box(popup)
    if mobile:
        assert abs(b["y"] + b["height"] - height) <= 1 and abs(b["width"] - width) <= 1 and b["x"] == 0, b
    else:
        assert abs(b["x"] + b["width"] - width) <= 1 and abs(b["width"] - 384) <= 1 and abs(b["height"] - height) <= 1, b
    popup.get_by_role("button", name="Increase").click()
    assert page.locator("#drawer-goal").text_content() == "360"
    t.shot("drawer-open", page)
    page.keyboard.press("Escape")
    drawer_closed(page, "#drawer-demo")
    assert active(page) == "Open Drawer"
    assert trigger.get_attribute("aria-expanded") == "false"
    for keyboard in (False, True):
        if keyboard:
            trigger.focus()
            page.keyboard.press("Enter")
        else:
            page.evaluate("document.activeElement.blur()")
            trigger.click()
        t.settle()
        page.mouse.click(5, 5)
        drawer_closed(page, "#drawer-demo")
        wait(page, "() => document.activeElement.textContent.trim() === 'Open Drawer'")
        assert page.evaluate("document.activeElement.matches(':focus-visible')") is keyboard, ("a press on the backdrop closes the drawer; the trigger ring follows the open input like Base UI", keyboard)
    drawer_open(page, "#drawer-handle")
    hpopup = page.locator("#drawer-handle [data-slot=drawer-popup]")
    t.settle()
    hb = box(page.locator("#drawer-handle [data-slot=drawer-swipe-handle]"))
    pb = box(hpopup)
    assert abs(hb["y"] - pb["y"] - 1) <= 1 and abs(hb["height"] - 12) <= 0.5, (hb, pb)
    x, y = hb["x"] + hb["width"] / 2, hb["y"] + hb["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x, y + 10, steps=2)
    page.wait_for_timeout(200)
    page.mouse.move(x, y + 40, steps=3)
    mid = hpopup.evaluate("e => [e.hasAttribute('data-swiping'), e.closest('dialog').hasAttribute('data-swiping'), parseFloat(e.style.getPropertyValue('--drawer-swipe-movement-y')), parseFloat(e.closest('dialog').style.getPropertyValue('--drawer-swipe-progress'))]")
    assert mid[0] and mid[1] and 25 <= mid[2] <= 40 and 0 < mid[3] < 0.2, mid
    page.wait_for_timeout(300)
    page.mouse.up()
    t.settle()
    assert hpopup.evaluate("(e, y) => e.closest('dialog').open && !e.hasAttribute('data-swiping') && e.style.transform === '' && Math.abs(e.getBoundingClientRect().y - y) <= 1", pb["y"]), "a slow short swipe springs back"
    page.mouse.click(x, y)
    page.wait_for_timeout(100)
    assert len(events(page, "drawer:release")) == 1, "a plain click on the handle is not a swipe"
    cb = box(page.locator("#drawer-handle [data-slot=drawer-content]"))
    page.mouse.move(cb["x"] + cb["width"] / 2, cb["y"] + 40)
    page.mouse.down()
    page.mouse.move(cb["x"] + cb["width"] / 2, cb["y"] + 240, steps=4)
    assert not hpopup.evaluate("e => e.hasAttribute('data-swiping')"), "a mouse press in drawer-content selects text, it does not swipe"
    page.mouse.up()
    page.evaluate("""() => document.addEventListener("drawer:close", event => {
      const p = event.target.querySelector('[data-slot="drawer-popup"]')
      window.__dismiss = [p.hasAttribute("data-swipe-dismiss"), p.closest("dialog").hasAttribute("data-swipe-dismiss"), +p.style.getPropertyValue("--drawer-swipe-strength"), p.closest("dialog").style.getPropertyValue("--drawer-swipe-strength")]
    }, { once: true })""")
    page.evaluate("""async () => {
      const handle = document.querySelector('#drawer-handle [data-slot="drawer-swipe-handle"]')
      const r = handle.getBoundingClientRect()
      const x = r.left + r.width / 2, y = r.top + r.height / 2
      const fire = (type, dy, buttons) => handle.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true, pointerId: 12, pointerType: "mouse", isPrimary: true, button: 0, buttons, clientX: x, clientY: y + dy }))
      fire("pointerdown", 0, 1)
      for (const dy of [10, 35, 60]) {
        await new Promise(r => setTimeout(r, 16))
        fire("pointermove", dy, 1)
      }
      fire("pointerup", 60, 0)
    }""")
    dismiss = page.evaluate("window.__dismiss")
    assert dismiss and dismiss[0] and dismiss[1] and 0.1 <= dismiss[2] <= 1 and dismiss[3] == "1", ("a fast short swipe dismisses", dismiss)
    drawer_closed(page, "#drawer-handle")
    drawer_open(page, "#drawer-handle")
    t.settle()
    flick = page.evaluate("""async () => {
      const handle = document.querySelector('#drawer-handle [data-slot="drawer-swipe-handle"]')
      const popup = handle.closest('[data-slot="drawer-popup"]')
      const r = handle.getBoundingClientRect()
      const x = r.left + r.width / 2, y = r.top + r.height / 2
      const fire = (type, dy, buttons) => handle.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true, pointerId: 11, pointerType: "mouse", isPrimary: true, button: 0, buttons, clientX: x, clientY: y + dy }))
      let seen = null
      document.addEventListener("drawer:close", () => { seen = [+popup.style.getPropertyValue("--drawer-swipe-strength"), popup.closest("dialog").style.getPropertyValue("--drawer-swipe-strength")] }, { once: true })
      const pause = () => new Promise(r => setTimeout(r, 16))
      fire("pointerdown", 0, 1)
      for (const dy of [10, 100, 300]) {
        await pause()
        fire("pointermove", dy, 1)
      }
      fire("pointerup", 300, 0)
      return seen
    }""")
    assert flick and flick[0] < 1 and flick[1] == "1", ("a fast release shortens the popup exit, the backdrop keeps strength 1 like Base UI", flick)
    drawer_closed(page, "#drawer-handle")
    assert active(page) == "Open Drawer"
    drawer_open(page, "#drawer-handle")
    t.settle()
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x, y + 20, steps=2)
    page.wait_for_timeout(150)
    page.mouse.move(x, y + pb["height"] * 0.6, steps=8)
    page.wait_for_timeout(150)
    page.mouse.up()
    drawer_closed(page, "#drawer-handle")
    drawer_open(page, "#drawer-handle")
    t.settle()
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x, y + 20, steps=2)
    page.wait_for_timeout(200)
    page.mouse.move(x, y + pb["height"] * 0.7, steps=8)
    page.wait_for_timeout(300)
    page.mouse.move(x, y + pb["height"] * 0.7 - 30, steps=3)
    page.wait_for_timeout(300)
    page.mouse.up()
    drawer_closed(page, "#drawer-handle")
    touched = None
    if t.engine == "chromium":
        drawer_open(page, "#drawer-handle")
        t.settle()
        touched = page.evaluate(TOUCH_SWIPE, ["#drawer-handle [data-slot=drawer-content]", 400])
        assert touched == [True, "392px"], ("a touch swipe starts anywhere in the drawer, at the first move like Base UI", touched)
        drawer_closed(page, "#drawer-handle")
    for side, direction in [("Top", "up"), ("Right", "right"), ("Left", "left"), ("Bottom", "down")]:
        root = f"#drawer-{direction}"
        section.get_by_role("button", name=side, exact=True).click()
        wait(page, "s => document.querySelector(s + ' [data-slot=drawer-viewport]').open", root)
        t.settle()
        b = box(page.locator(f"{root} [data-slot=drawer-popup]"))
        if side == "Top":
            assert abs(b["y"]) <= 1 and abs(b["width"] - width) <= 1, b
        elif side == "Right":
            assert abs(b["x"] + b["width"] - width) <= 1 and abs(b["height"] - height) <= 1, b
        elif side == "Left":
            assert abs(b["x"]) <= 1 and abs(b["width"] - (384 if width >= 640 else width * 0.75)) <= 1, b
        else:
            assert abs(b["y"] + b["height"] - height) <= 1 and b["height"] <= height - 96 + 1, b
        if side == "Right":
            t.shot("drawer-right", page)
        page.locator(f"{root} [data-slot=drawer-footer]").get_by_role("button", name="Close").click()
        drawer_closed(page, root)
    section.get_by_role("button", name="Non Modal").click()
    nm = page.locator("#drawer-non-modal [data-slot=drawer-viewport]")
    wait(page, "() => document.querySelector('#drawer-non-modal [data-slot=drawer-viewport]').open")
    t.settle()
    assert nm.evaluate("v => [v.dataset.modal, v.matches(':modal'), getComputedStyle(v).pointerEvents, document.documentElement.style.overflow]") == ["false", False, "none", ""]
    nb = box(nm.locator("[data-slot=drawer-popup]"))
    hit = page.evaluate("([x, y]) => !document.elementFromPoint(x, y)?.closest('dialog')", [nb["x"] / 2, height / 2])
    assert hit, "the page outside a non-modal drawer takes pointer input"
    page.mouse.click(nb["x"] / 2, height / 2)
    page.wait_for_timeout(300)
    assert nm.evaluate("v => v.open"), "data-disable-pointer-dismissal keeps it open on an outside press"
    t.shot("drawer-non-modal", page)
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#drawer-non-modal [data-slot=drawer-viewport]').open")
    section.get_by_role("button", name="Edit Profile").click()
    expected = "drawer-responsive-dialog" if t.width >= 768 else "drawer-responsive-drawer"
    wait(page, "id => document.querySelector('#' + id + ' dialog').open", expected)
    if expected == "drawer-responsive-drawer":
        page.mouse.click(5, 5)
    else:
        page.keyboard.press("Escape")
    wait(page, "() => [...document.querySelectorAll('#drawer dialog')].every(d => !d.open)")
    reasons = [e[1].get("reason") for e in events(page, "drawer:close")]
    expected_reasons = ["escape", "outside", "outside", "swipe", "swipe", "swipe", "swipe"] + (["swipe"] if touched else []) + ["close", "close", "close", "close", "escape"] + (["outside"] if t.width < 768 else [])
    assert reasons == expected_reasons, reasons
    assert len(events(page, "drawer:release")) == 1


DRAWER_FLICK = """async ([plan, stationary, cancel]) => {
  const v = document.querySelector('#drawer-handle [data-slot="drawer-viewport"]')
  const p = v.querySelector('[data-slot="drawer-popup"]')
  const handle = p.querySelector('[data-slot="drawer-swipe-handle"]')
  const r = handle.getBoundingClientRect()
  const x = r.left + r.width / 2, y = r.top + r.height / 2
  const height = p.offsetHeight
  const spin = ms => { const t = performance.now(); while (performance.now() - t < ms) {} }
  const log = []
  const fire = (type, dy, buttons) => {
    const e = new PointerEvent(type, { bubbles: true, cancelable: true, pointerId: 13, pointerType: "mouse", isPrimary: true, button: 0, buttons, clientX: x, clientY: y + dy })
    handle.dispatchEvent(e)
    log.push([type, dy, e.timeStamp])
  }
  if (cancel) document.addEventListener("drawer:close", event => event.preventDefault(), { once: true })
  fire("pointerdown", 0, 1)
  for (const [ms, dy] of plan) {
    spin(ms)
    fire("pointermove", dy, 1)
  }
  if (stationary) {
    spin(5)
    fire("pointermove", plan.at(-1)[1], 1)
  }
  fire("pointerup", plan.at(-1)[1], 0)
  const released = performance.now()
  const state = [p.style.getPropertyValue("--drawer-swipe-strength"), p.hasAttribute("data-ending-style"), p.hasAttribute("data-swipe-dismiss"), v.open]
  const anims = Object.fromEntries(p.getAnimations().map(a => [a.transitionProperty, a.effect.getTiming().duration]))
  while (!cancel && v.open && performance.now() - released < 2000) await new Promise(r => requestAnimationFrame(r))
  return { log, height, state, anims, closed: v.open ? null : performance.now() - released }
}"""


def base_ui_strength(log, height, clamp=16, skip=False):
    moves = [e for e in log if e[0] == "pointermove"]
    start, begin = moves[0][1], moves[0][2]
    sample, velocity, offset, still = (0, begin), 0, 0, False
    for _, dy, time in moves:
        offset = dy - start
        if not skip:
            if time > sample[1]:
                velocity = (offset - sample[0]) / max(time - sample[1], clamp)
            sample = (offset, time)
        elif time > sample[1]:
            stationary = abs(offset - sample[0]) < 1
            if not (stationary and not still):
                velocity = (offset - sample[0]) / max(time - sample[1], clamp)
                sample = (offset, time)
            still = stationary
    up = log[-1][2]
    average = offset / max(up - begin, 50) if up > begin else 0
    if up - sample[1] <= 80 and offset != sample[0]:
        velocity = (offset - sample[0]) / max(up - sample[1], clamp)
    elif up - sample[1] > 80:
        velocity = 0
    v = velocity if velocity else average
    remaining = max(0, height - offset)
    if remaining <= 0 or v <= 0.2:
        return 1
    ms = min(360, max(80, remaining / min(4, max(0.2, v))))
    return 0.1 + (ms - 80) / 280 * 0.9


def check_drawer_swipe_release(t):
    page = t.page
    t.section("drawer")
    for _ in range(4):
        drawer_open(page, "#drawer-handle")
        t.settle()
        height = page.locator("#drawer-handle [data-slot=drawer-popup]").evaluate("e => e.offsetHeight")
        plan = [[20, 10], [20, 10 + height * 0.25], [20, 10 + height * 0.5], [5, 30 + height * 0.5]]
        run = page.evaluate(DRAWER_FLICK, [plan, False, False])
        fast = run["log"][-2][2] - run["log"][-3][2]
        if fast <= 10:
            break
        drawer_closed(page, "#drawer-handle")
    assert fast <= 10, ("the last move must come well before the 16 ms minimum sample time; the page was busy", fast)
    strength = float(run["state"][0])
    expected = base_ui_strength(run["log"], run["height"])
    assert abs(expected - base_ui_strength(run["log"], run["height"], clamp=4)) > 0.05, ("the move plan must tell 16 ms from 4 ms", expected)
    assert abs(strength - expected) < 1e-9, ("the release speed uses a 16 ms minimum sample time like Base UI 1.6.0", strength, expected, run["log"])
    assert run["state"][1:] == [True, True, True], run["state"]
    if not t.reduced_motion:
        assert run["anims"].get("opacity") == 400 and abs(run["anims"].get("transform", 0) - strength * 400) < 1, ("Base UI sets data-ending-style and reads the size before the strength: opacity keeps 400 ms, the transform takes the strength", strength, run["anims"])
        assert run["closed"] is not None and run["closed"] >= 380, ("the drawer unmounts after the 400 ms opacity transition like Base UI", run["closed"])
    drawer_closed(page, "#drawer-handle")
    wait(page, "() => document.activeElement?.matches('#drawer-handle > [data-drawer-trigger]')")
    drawer_open(page, "#drawer-handle")
    t.settle()
    run = page.evaluate(DRAWER_FLICK, [plan, True, False])
    strength = float(run["state"][0])
    expected = base_ui_strength(run["log"], run["height"])
    assert abs(expected - base_ui_strength(run["log"], run["height"], skip=True)) > 0.05, ("the move plan must tell a kept stationary sample from a skipped one", expected)
    assert abs(strength - expected) < 1e-9, ("a stationary last move sets the release speed to 0 like Base UI 1.6.0", strength, expected, run["log"])
    drawer_closed(page, "#drawer-handle")
    drawer_open(page, "#drawer-handle")
    t.settle()
    rest = box(page.locator("#drawer-handle [data-slot=drawer-popup]"))
    run = page.evaluate(DRAWER_FLICK, [plan, False, True])
    assert run["state"] == ["1", False, False, True], ("a cancelled swipe close removes the ending style and the strength", run["state"])
    wait(page, "y => Math.abs(document.querySelector('#drawer-handle [data-slot=drawer-popup]').getBoundingClientRect().y - y) <= 1", rest["y"])
    page.keyboard.press("Escape")
    drawer_closed(page, "#drawer-handle")


OVERLAY_STATE = """sel => {
  const d = document.querySelector(sel)
  const p = d.matches('[data-slot=drawer-viewport]') ? d.querySelector(':scope > [data-slot=drawer-popup]') : d
  return { open: d.open && d.dataset.state === 'open', swiping: p.hasAttribute('data-swiping') }
}"""


def check_overlay_outside_press(t):
    page = t.page
    width, height = viewport(page)
    overlays = [("dialog", "#dialog-demo", "dialog"), ("sheet", "#sheet-demo", "dialog"), ("drawer", "#drawer-demo", "[data-slot=drawer-viewport]")]
    for name, root, part in overlays:
        t.section(name)
        sel = f"{root} {part}"
        trigger = page.locator(f"{root} [data-{name}-trigger]").first

        def opened():
            if not page.evaluate(OVERLAY_STATE, sel)["open"]:
                trigger.click()
                wait(page, "s => document.querySelector(s).open", sel)
                t.settle()

        def state():
            page.wait_for_timeout(250)
            return page.evaluate(OVERLAY_STATE, sel)

        opened()
        page.mouse.move(5, 5)
        page.mouse.down()
        held = state()
        page.mouse.up()
        assert held["open"], (name, "a modal stays open while the outside press is held, like Base UI (close on click)")
        wait(page, "s => !document.querySelector(s).open", sel)
        for button in ("right",) + (() if t.engine == "firefox" else ("middle",)):
            opened()
            page.mouse.click(5, 5, button=button)
            assert state()["open"], (name, button, "only a main-button click outside closes a modal")
            page.evaluate("() => { const b = document.createElement('button'); document.body.append(b); b.click(); b.remove() }")
            assert state()["open"], (name, button, "a later script click outside does not close a modal after an outside press that gave no click")
        opened()
        b = box(page.locator(sel if name != "drawer" else f"{sel} > [data-slot=drawer-popup]"))
        cx, cy = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
        sx, sy, ex, ey = 5, 5, cx, cy
        if name == "drawer":
            sx, sy, ex, ey = (5, b["y"] - 5, width - 60, b["y"] + 20) if width < 768 else (b["x"] - 5, 5, b["x"] + 20, cy)
        page.mouse.move(sx, sy)
        page.mouse.down()
        page.mouse.move(ex, ey, steps=10)
        page.mouse.up()
        assert state()["open"], (name, "a press outside that ends in the popup across the swipe axis does not close")
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(5, 5, steps=10)
        page.mouse.up()
        assert state()["open"], (name, "a press in the popup that ends outside does not close")
        page.mouse.click(5, 5)
        wait(page, "s => !document.querySelector(s).open", sel)
        if t.engine == "chromium":
            opened()
            b = box(page.locator(sel if name != "drawer" else f"{sel} > [data-slot=drawer-popup]"))
            down = width < 768 or name != "drawer"
            sx, sy = (b["x"] + b["width"] / 2, max(5, b["y"] - 40)) if down else (max(5, b["x"] - 40), b["y"] + b["height"] / 2)
            if name != "drawer":
                sx, sy = 5, 5
            page.evaluate("() => { getSelection().removeAllRanges(); window.__touched = false; document.addEventListener('pointerdown', e => { if (e.pointerType === 'touch') window.__touched = true }, { capture: true, once: true }) }")
            cdp = page.context.new_cdp_session(page)
            cdp.send("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 1})
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": sx, "y": sy}]})
            for i in range(1, 11):
                cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": sx + (0 if down else 6 * i), "y": sy + (6 * i if down else 0)}]})
                page.wait_for_timeout(30)
            mid = page.evaluate(OVERLAY_STATE, sel)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            touched = page.evaluate("() => window.__touched")
            cdp.send("Emulation.setTouchEmulationEnabled", {"enabled": False})
            cdp.detach()
            assert touched, (name, "the touch drag reached the page")
            after = state()
            assert after["open"], (name, "a touch drag outside does not close a modal")
            if name == "drawer":
                assert mid["swiping"], "a touch that starts on the drawer backdrop swipes the drawer once it reaches the popup, like Base UI"
            page.keyboard.press("Escape")
            wait(page, "s => !document.querySelector(s).open", sel)
    t.section("drawer")
    sel = "#drawer-demo [data-slot=drawer-viewport]"
    page.locator("#drawer-demo [data-drawer-trigger]").click()
    wait(page, "s => document.querySelector(s).open", sel)
    t.settle()
    b = box(page.locator(f"{sel} > [data-slot=drawer-popup]"))
    down = width < 768
    sx, sy = (b["x"] + b["width"] / 2, max(5, b["y"] - 30)) if down else (max(5, b["x"] - 30), b["y"] + b["height"] / 2)
    page.mouse.move(sx, sy)
    page.mouse.down()
    for i in range(1, 9):
        page.mouse.move(sx + (0 if down else 8 * i), sy + (8 * i if down else 0))
        page.wait_for_timeout(30)
    mid = page.evaluate(OVERLAY_STATE, sel)
    page.mouse.up()
    assert mid["swiping"], ("a mouse press on the drawer backdrop swipes the drawer once the pointer reaches the popup, like Base UI", mid)
    page.wait_for_timeout(250)
    assert page.evaluate(OVERLAY_STATE, sel)["open"], "a short backdrop swipe leaves the drawer open, like Base UI"
    page.keyboard.press("Escape")
    wait(page, "s => !document.querySelector(s).open", sel)


def check_drawer_non_modal_outside(t):
    page = t.page
    t.section("drawer")
    drawer_build(page, {"data-modal": "false"}, True)
    sel = "#built [data-slot=drawer-viewport]"
    state = f"() => document.querySelector('{sel}').open && document.querySelector('{sel}').dataset.state === 'open'"

    def opened():
        page.locator("#built [data-drawer-trigger]").click()
        wait(page, state)
        t.settle()

    opened()
    page.mouse.move(5, 5)
    page.mouse.down()
    page.wait_for_timeout(250)
    held = page.evaluate(state)
    page.mouse.up()
    assert held, "a non-modal drawer closes on the mouse click outside, not on the press (Base UI intentional for mouse without a backdrop)"
    wait(page, f"() => !document.querySelector('{sel}').open")
    opened()
    page.mouse.click(5, 5, button="right")
    page.wait_for_timeout(250)
    assert page.evaluate(state), "a right click outside keeps a non-modal drawer open"
    if t.engine == "chromium":
        x, y = tap_spot(page)
        cdp = touch_outside(page, x, y)
        touched = page.evaluate(state)
        touch_end(cdp)
        assert touched, "a touch press outside keeps a non-modal drawer open until the tap ends (Base UI sloppy for touch)"
        wait(page, f"() => !document.querySelector('{sel}').open")
        page.evaluate("() => document.getElementById('tap-spot').remove()")
        opened()
        tap_spot(page)
        cdp = touch_outside(page, x, y, move=20)
        moved = page.evaluate(f"() => document.querySelector('{sel}').dataset.state")
        touch_end(cdp)
        page.evaluate("() => document.getElementById('tap-spot').remove()")
        assert moved == "closed", "a touch drag of more than 10 px outside closes a non-modal drawer during the move (Base UI sloppy for touch)"
    else:
        page.keyboard.press("Escape")
    wait(page, f"() => !document.querySelector('{sel}').open")


def tap_spot(page):
    page.evaluate("""() => {
      const spot = document.getElementById("tap-spot") ?? document.body.appendChild(document.createElement("div"))
      spot.id = "tap-spot"
      Object.assign(spot.style, { position: "fixed", left: "0px", top: "120px", width: "40px", height: "40px", zIndex: "2147483647" })
    }""")
    return 10, 140


def touch_outside(page, x, y, move=0, hold=150):
    cdp = page.context.new_cdp_session(page)
    cdp.send("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 1})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    for i in range(1, 5 if move else 1):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + move * i / 4, "y": y}]})
        page.wait_for_timeout(20)
    page.wait_for_timeout(hold)
    return cdp


def touch_end(cdp):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    cdp.send("Emulation.setTouchEmulationEnabled", {"enabled": False})
    cdp.detach()


def check_popup_outside_press(t):
    page = t.page
    width, height = viewport(page)
    x, y = 3, height - 3
    popups = [
        ("popover", "#popover-demo [data-popover-trigger]", "#popover-demo [data-slot=popover-content]", "mouse"),
        ("date-picker", "#date-picker-demo [data-date-picker-trigger]", "#date-picker-demo [data-date-picker-content]", "mouse"),
        ("navigation-menu", "#navigation-menu-demo [data-slot=navigation-menu-trigger]", "#navigation-menu-demo [data-slot=navigation-menu-trigger]", "both"),
        ("combobox", "#combobox-basic input", "#combobox-basic [data-slot=combobox-content]", "touch"),
        ("select", "#select-demo-trigger", "#select-demo [data-slot=select-content]", "none"),
        ("hover-card", "#hover-card-demo [data-hover-card-trigger]", "#hover-card-demo [data-slot=hover-card-content]", "none"),
        ("dropdown-menu", "#dropdown-menu-demo [data-dropdown-menu-trigger]", "#dropdown-menu-demo [data-slot=dropdown-menu-content]", "none"),
        ("context-menu", "#context-menu-demo [data-slot=context-menu-trigger]", "#context-menu-demo [data-slot=context-menu-content]", "none"),
        ("menubar", "#menubar-demo [data-slot=menubar-trigger]", "#menubar-demo [data-slot=menubar-content]", "none"),
    ]
    for name, trigger_sel, sel, intentional in popups:
        section = t.section(name)
        trigger = section.locator(trigger_sel).first
        state = f"() => {{ const e = document.querySelector({sel!r}); return e.matches('[aria-expanded]') ? e.getAttribute('aria-expanded') === 'true' : e.matches(':popover-open') && !e.hasAttribute('data-closed') }}"

        def opened():
            if name == "navigation-menu":
                keyboard_focus(page, trigger)
                page.keyboard.press("Enter")
            elif name == "hover-card":
                trigger.focus()
                page.keyboard.press("Shift+Tab")
                page.keyboard.press("Tab")
            elif name == "context-menu":
                trigger.click(button="right")
            else:
                trigger.click()
            wait(page, state)
            t.settle()
            away(page)

        def held():
            page.wait_for_timeout(250)
            return page.evaluate(state)

        def closed():
            wait(page, f"() => !({state})()")
            page.evaluate("() => document.activeElement?.blur()")
            page.wait_for_timeout(150)

        mouse = intentional in ("mouse", "both")
        opened()
        page.mouse.down()
        assert held() == mouse, (name, "an outside mouse press closes at the press only when Base UI uses sloppy for mouse")
        page.mouse.up()
        closed()
        if mouse:
            for button in ("right",) + (() if t.engine == "firefox" else ("middle",)):
                opened()
                page.mouse.click(x, y, button=button)
                assert held(), (name, button, "only a main-button click outside closes a popup with an intentional mouse press")
                page.mouse.click(x, y)
                closed()
            if name != "navigation-menu":
                opened()
                b = box(page.locator(sel))
                page.mouse.down()
                page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=8)
                page.mouse.up()
                assert held(), (name, "a press outside that ends in the popup does not close it")
                away(page)
                page.mouse.click(x, y)
                closed()
        if t.engine != "chromium":
            continue
        touch = intentional in ("touch", "both")
        opened()
        page.evaluate("""([x, y]) => {
          const spot = document.body.appendChild(document.createElement("button"))
          spot.id = "touch-spot"
          window.__spot = 0
          spot.addEventListener("click", () => window.__spot++)
          Object.assign(spot.style, { position: "fixed", left: `${x - 20}px`, top: `${y - 20}px`, width: "40px", height: "40px", zIndex: "2147483647" })
        }""", [x + 18, y - 40])
        cdp = touch_outside(page, x + 18, y - 40)
        pressed = page.evaluate(state)
        touch_end(cdp)
        assert pressed, (name, "a touch press outside does not close at the press (Base UI closes at the tap end or on the click)")
        closed()
        spot = page.evaluate("() => { document.getElementById('touch-spot').remove(); return window.__spot }")
        if name in ("dropdown-menu", "context-menu", "menubar"):
            assert spot == 0, (name, "the tap that closes a modal menu does not click the element below, as on live")
        opened()
        cdp = touch_outside(page, x - 2, y - 40, move=20)
        moved = page.evaluate(state)
        touch_end(cdp)
        assert moved == touch, (name, "a 20 px touch drag outside closes during the move only when Base UI uses sloppy for touch")
        if touch:
            page.wait_for_timeout(250)
            assert page.evaluate(state), (name, "a touch drag outside gives no click, so an intentional touch popup stays open")
            page.keyboard.press("Escape")
        closed()


def check_hover_popup_leave(t):
    page = t.page
    width, height = viewport(page)
    section = t.section("hover-card")
    trigger = section.locator("#hover-card-demo [data-hover-card-trigger]")
    content = section.locator("#hover-card-demo [data-slot=hover-card-content]")
    card = "() => document.querySelector('#hover-card-demo [data-slot=hover-card-content]').matches(':popover-open')"
    away(page)
    trigger.focus()
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Tab")
    wait(page, card)
    t.settle()
    b = box(content)
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=4)
    away(page)
    page.wait_for_timeout(400)
    assert page.evaluate(card), "a hover card opened by focus stays open when the pointer leaves the card, as in Base UI"
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=4)
    page.mouse.down()
    away(page)
    page.wait_for_timeout(400)
    held = page.evaluate(card)
    page.mouse.up()
    page.wait_for_timeout(300)
    assert [held, page.evaluate(card)] == [True, True], "a press in a focus-opened hover card, dragged outside, keeps it open, as on live"
    page.keyboard.press("Escape")
    wait(page, f"() => !({card})()")
    page.evaluate("() => document.activeElement?.blur()")
    trigger.hover()
    wait(page, card)
    t.settle()
    b = box(content)
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=4)
    away(page)
    wait(page, f"() => !({card})()", timeout=1500)
    section = t.section("navigation-menu")
    first = section.locator("#navigation-menu-demo").get_by_role("button", name="Getting started")
    expanded = "() => document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-trigger]').getAttribute('aria-expanded') === 'true'"
    for how in ("click", "key"):
        away(page)
        if how == "click":
            first.click()
        else:
            keyboard_focus(page, first)
            page.keyboard.press("Enter")
        wait(page, expanded)
        t.settle()
        away(page)
        page.wait_for_timeout(400)
        assert page.evaluate(expanded), (how, "a navigation menu opened by a click or a key stays open when the pointer leaves, as in Base UI")
        page.keyboard.press("Escape")
        wait(page, f"() => !({expanded})()")
    away(page)
    first.hover()
    wait(page, expanded)
    t.settle()
    link = section.locator("#navigation-menu-demo [data-slot=navigation-menu-viewport] [data-slot=navigation-menu-link]").first
    link.hover()
    page.mouse.down()
    page.mouse.move(width - 10, height - 10, steps=10)
    page.wait_for_timeout(300)
    held = page.evaluate(expanded)
    page.mouse.up()
    page.wait_for_timeout(400)
    after = page.evaluate(expanded)
    assert held, "a press on a link in a hovered navigation menu, dragged outside, keeps it open during the drag"
    assert after == (t.engine != "firefox"), ("after the release, live keeps it open in Chromium and WebKit and closes it in Firefox", after)
    if after:
        page.keyboard.press("Escape")
    wait(page, f"() => !({expanded})()")


def check_select_trigger_release_outside(t):
    page = t.page
    width, height = viewport(page)
    section = t.section("select")
    trigger = section.locator("#select-demo-trigger")
    opened = "() => document.querySelector('#select-demo [data-slot=select-content]').matches(':popover-open[data-open]')"
    b = box(trigger)
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    page.mouse.down()
    wait(page, opened)
    page.wait_for_timeout(100)
    page.mouse.move(width - 5, height - 5, steps=10)
    page.mouse.up()
    wait(page, f"() => !({opened})()", timeout=1500)


def check_drawer_nested_outside(t):
    page = t.page
    t.section("drawer")
    count = "() => [...document.querySelectorAll('[data-slot=drawer-viewport]')].filter(v => v.open && v.dataset.state === 'open').length"

    def nested():
        page.locator("#drawer-nested-1 > [data-drawer-trigger]").click()
        wait(page, f"() => ({count})() === 1")
        t.settle()
        page.locator("#drawer-nested-2 > [data-drawer-trigger]").click()
        wait(page, f"() => ({count})() === 2")
        drawer_settle(t)

    nested()
    page.mouse.move(5, 5)
    page.mouse.down()
    page.wait_for_timeout(250)
    held = page.evaluate(count)
    page.mouse.up()
    page.wait_for_timeout(250)
    assert [held, page.evaluate(count)] == [2, 1], ("a held press outside both drawers closes only the front drawer, after the release", held)
    page.mouse.click(5, 5, button="right")
    page.wait_for_timeout(250)
    assert page.evaluate(count) == 1, "a right click outside does not close the drawer"
    page.keyboard.press("Escape")
    wait(page, f"() => ({count})() === 0")


def check_drawer_motion(t):
    page = t.page
    t.section("drawer")
    trigger = page.locator("#drawer-handle [data-drawer-trigger]")
    trigger.scroll_into_view_if_needed()
    motion_retry(t, trigger, "#drawer-handle [data-slot=drawer-viewport]", lambda: drawer_motion(t, trigger))


def drawer_motion(t, trigger):
    page = t.page
    width, height = viewport(page)
    frames = t.paint(DRAWER_FRAME, lambda: trigger.click(), ms=1200)
    shown = [f for f in frames if f[1]]
    assert shown, frames
    final = shown[-1]
    assert final[1:6] == [True, False, False, False, "open"], final
    rest = final[0]
    spent = motion_time(shown, lambda f: True, lambda f: abs(f[0] - rest) <= 1)
    assert spent <= 550, ("the drawer opens in 450 ms like shadcn", spent)
    if not t.reduced_motion:
        assert shown[0][0] >= rest + (height - rest) * 0.7, ("the popup starts below the screen", shown[0], rest)
        assert any(rest + 20 < f[0] < height - 20 for f in shown), shown
    popup = page.locator("#drawer-handle [data-slot=drawer-popup]")
    assert popup.evaluate("e => e.style.getPropertyValue('--drawer-swipe-movement-y') === '0px' && e.style.getPropertyValue('--nested-drawers') === '0'")
    frames = t.paint(DRAWER_FRAME, lambda: page.keyboard.press("Escape"), ms=1200)
    spent = motion_time(frames, lambda f: f[3] or not f[1], lambda f: not f[1] or f[0] >= height - 1)
    assert spent <= 550, ("the drawer closes in 400 ms like shadcn", spent)
    if not t.reduced_motion:
        ending = [f for f in frames if f[1] and f[3]]
        assert len(ending) >= 3 and ending[0][5] == "closed" and ending[0][4], frames[:4]
        assert max(f[0] for f in ending) > rest + 50, ("the dialog stays open while the popup slides out", ending[-1], rest)
    assert not frames[-1][1], frames[-1]
    assert popup.evaluate("e => !e.hasAttribute('data-ending-style') && !e.closest('dialog').hasAttribute('data-ending-style')")


DRAWER_STATE = """sel => {
  const v = sel.startsWith("#") && document.querySelector(sel)?.localName === "dialog" ? document.querySelector(sel) : document.getElementById(document.querySelector(sel + ' > [data-drawer-trigger]').getAttribute('aria-controls'))
  const p = v.querySelector(':scope > [data-slot="drawer-popup"]')
  const r = p.getBoundingClientRect()
  const vars = {}
  for (const n of ["--drawer-snap-point-offset", "--nested-drawers", "--drawer-height", "--drawer-frontmost-height", "--drawer-swipe-progress"]) vars[n] = p.style.getPropertyValue(n)
  return { id: v.id, open: v.open, top: Math.round(r.top), width: r.width, height: p.offsetHeight, attrs: ["data-snap-points", "data-expanded", "data-nested", "data-nested-drawer-open", "data-nested-drawer-swiping", "data-swiping"].filter(a => p.hasAttribute(a)), vars, backdrop: [v.style.getPropertyValue("--drawer-swipe-progress"), v.style.getPropertyValue("--drawer-overlay-min-opacity"), v.hasAttribute("data-snap-points")], host: v.parentElement.dataset.slot, content: +getComputedStyle(p.querySelector(':scope > [data-slot="drawer-content"]')).opacity }
}"""


def drawer_drag(page, handle, dy):
    hb = box(handle)
    x, y = hb["x"] + hb["width"] / 2, hb["y"] + hb["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x, y + (8 if dy > 0 else -8), steps=2)
    page.wait_for_timeout(150)
    page.mouse.move(x, y + dy, steps=8)
    page.wait_for_timeout(200)
    page.mouse.up()


def check_drawer_snap_points(t):
    page = t.page
    section = t.section("drawer")
    listen(page, "drawer:snap-point-change", "drawer:close")
    width, height = viewport(page)
    section.get_by_role("button", name="Open Snap Drawer").click()
    wait(page, "() => document.querySelector('#drawer-snap dialog').open")
    t.settle()
    ph = height - 96
    peek = ph - 496
    st = page.evaluate(DRAWER_STATE, "#drawer-snap")
    assert st["height"] == ph and st["attrs"] == ["data-snap-points"], st
    assert st["vars"]["--drawer-snap-point-offset"] == f"{peek}px" and abs(st["top"] - (height - 496)) <= 1, st
    assert st["backdrop"] == ["1", "", True], ("the backdrop rests at the 0.5 minimum at the first snap point", st)
    t.shot("drawer-snap", page)
    handle = page.locator("#drawer-snap [data-slot=drawer-swipe-handle]")
    drawer_drag(page, handle, -400)
    t.settle()
    st = page.evaluate(DRAWER_STATE, "#drawer-snap")
    assert st["vars"]["--drawer-snap-point-offset"] == "0px" and "data-expanded" in st["attrs"] and abs(st["top"] - 96) <= 1 and st["backdrop"][0] == "0", st
    drawer_drag(page, handle, 200)
    t.settle()
    st = page.evaluate(DRAWER_STATE, "#drawer-snap")
    assert st["vars"]["--drawer-snap-point-offset"] == f"{peek}px" and "data-expanded" not in st["attrs"] and st["open"], st
    drawer_drag(page, handle, 300)
    wait(page, "() => !document.querySelector('#drawer-snap dialog').open")
    snaps = [e[1]["snapPoint"] for e in events(page, "drawer:snap-point-change")]
    assert snaps == [1, "31rem", None, "31rem"], ("settle, swipe close, and reset as Base UI onSnapPointChange", snaps)
    assert [e[1]["reason"] for e in events(page, "drawer:close")] == ["swipe"]
    section.get_by_role("button", name="Open Snap Drawer").click()
    wait(page, "() => document.querySelector('#drawer-snap dialog').open")
    t.settle()
    st = page.evaluate(DRAWER_STATE, "#drawer-snap")
    assert st["vars"]["--drawer-snap-point-offset"] == f"{peek}px", ("a new open starts at the first snap point", st)
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#drawer-snap dialog').open")


NESTED_TOUCH = """([sel, dy]) => {
  try { new Touch({ identifier: 1, target: document.body, clientX: 0, clientY: 0 }) } catch { return null }
  const c = document.querySelector(sel)
  const r = c.getBoundingClientRect()
  const x = r.left + r.width / 2, y = r.top + 30
  const touch = d => new Touch({ identifier: 5, target: c, clientX: x + (dy.x ?? 0) * d, clientY: y + (dy.y ?? 0) * d })
  const fire = (type, d, held) => c.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true, touches: held ? [touch(d)] : [], changedTouches: [touch(d)] }))
  fire("touchstart", 0, true)
  fire("touchmove", 0.1, true)
  fire("touchmove", 1, true)
  window.__nested = [...document.querySelectorAll('[data-slot="drawer-popup"][data-nested-drawer-open]')].map(p => [p.hasAttribute("data-nested-drawer-swiping"), +p.style.getPropertyValue("--drawer-swipe-progress")])
  fire("touchcancel", 1, false)
  return window.__nested
}"""


def drawer_handle_drag(page, handle, dx, dy, slow=True):
    hb = box(handle)
    x, y = hb["x"] + hb["width"] / 2, hb["y"] + hb["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + (5 if dx > 0 else -5 if dx < 0 else 0), y + (5 if dy > 0 else -5 if dy < 0 else 0), steps=1 if not slow else 2)
    if slow:
        page.wait_for_timeout(150)
    page.mouse.move(x + dx, y + dy, steps=6 if slow else 2)
    if slow:
        page.wait_for_timeout(250)
    page.mouse.up()


def drawer_settle(t):
    wait(t.page, "() => !document.querySelector('[data-slot^=drawer][data-starting-style]')")
    t.settle()


def check_drawer_nested(t):
    page = t.page
    section = t.section("drawer")
    listen(page, "drawer:close")
    width, height = viewport(page)
    page.evaluate("() => document.querySelectorAll('[data-demo-responsive-drawer]').forEach(r => r.setAttribute('data-show-swipe-handle', ''))")
    first = section.locator("#drawer-nested-1 > [data-drawer-trigger]")
    first.click()
    wait(page, "() => document.querySelector('#drawer-nested-1 > dialog').open")
    drawer_settle(t)
    alone = page.evaluate(DRAWER_STATE, "#drawer-nested-1")
    assert alone["attrs"] == [] and alone["vars"]["--drawer-frontmost-height"] == f"{alone['height']}px" and alone["vars"]["--drawer-height"] == "initial", alone
    page.locator("#drawer-nested-2 > [data-drawer-trigger]").focus()
    page.keyboard.press("Enter")
    drawer_settle(t)
    root = page.evaluate(DRAWER_STATE, "#drawer-nested-1")
    child = page.evaluate(DRAWER_STATE, "#drawer-nested-2")
    assert child["open"] and child["host"] == "drawer-viewport", ("the child viewport moves out of the parent popup", child)
    assert page.evaluate("id => !document.querySelector('#drawer-nested-1 > dialog > [data-slot=drawer-popup]').contains(document.getElementById(id))", child["id"])
    assert child["attrs"] == ["data-nested"] and child["vars"]["--nested-drawers"] == "0" and child["vars"]["--drawer-frontmost-height"] == f"{child['height']}px", child
    assert child["backdrop"] == ["1", "0", False], ("a nested drawer shows no backdrop", child)
    assert root["attrs"] == ["data-nested-drawer-open"] and root["vars"]["--nested-drawers"] == "1", root
    assert root["vars"]["--drawer-height"] == f"{alone['height']}px" and root["vars"]["--drawer-frontmost-height"] == f"{child['height']}px", root
    assert root["content"] == 0 and child["content"] == 1, (root, child)
    assert root["width"] < child["width"] * 0.97, ("the parent scales down behind the nested drawer", root, child)
    t.shot("drawer-nested", page)
    phb = box(page.locator("#drawer-nested-1 > dialog > [data-slot=drawer-popup]"))
    vertical = page.evaluate("document.querySelector('#drawer-nested-1 > dialog > [data-slot=drawer-popup]').dataset.swipeAxis") == "y"
    hx, hy = (phb["x"] + phb["width"] / 2, phb["y"] + 3) if vertical else (phb["x"] + 3, phb["y"] + phb["height"] / 2)
    page.mouse.move(hx, hy)
    page.mouse.down()
    page.mouse.move(hx - (0 if vertical else 40), hy - (40 if vertical else 0), steps=4)
    swiping = page.evaluate("document.querySelector('#drawer-nested-1 > dialog > [data-slot=drawer-popup]').hasAttribute('data-swiping')")
    page.mouse.up()
    assert swiping is False, "a press on the parent behind a nested drawer does not swipe the parent"
    wait(page, "() => !!document.querySelector('#drawer-nested-2 > dialog') && !document.querySelector('#drawer-nested-2 > dialog').open")
    drawer_settle(t)
    page.locator("#drawer-nested-2 > [data-drawer-trigger]").click()
    drawer_settle(t)
    child = page.evaluate(DRAWER_STATE, "#drawer-nested-2")
    page.locator(f"#{child['id']} > [data-slot=drawer-popup] > [data-slot=drawer-content] > [data-slot=drawer-footer] > [data-slot=drawer] > [data-drawer-trigger]").click()
    drawer_settle(t)
    root = page.evaluate(DRAWER_STATE, "#drawer-nested-1")
    middle = page.evaluate(DRAWER_STATE, "#" + child["id"])
    third = page.evaluate(DRAWER_STATE, "#drawer-nested-3")
    assert root["vars"]["--nested-drawers"] == "2" and middle["vars"]["--nested-drawers"] == "1", (root, middle)
    assert middle["attrs"] == ["data-nested", "data-nested-drawer-open"] and third["attrs"] == ["data-nested"], (middle, third)
    assert root["width"] < middle["width"] < third["width"], (root, middle, third)
    axis = page.evaluate("id => document.getElementById(id).querySelector('[data-slot=drawer-popup]').dataset.swipeDirection", third["id"])
    handle = page.locator(f"#{third['id']} > [data-slot=drawer-popup] > [data-slot=drawer-swipe-handle]")
    hb = box(handle)
    x, y = (hb["x"] + 1 if axis == "right" else hb["x"] + hb["width"] / 2), hb["y"] + hb["height"] / 2
    dx, dy = (min(100, width - 1 - x), 0) if axis == "right" else (0, 100)
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx / 20, y + dy / 20, steps=2)
    page.wait_for_timeout(100)
    page.mouse.move(x + dx, y + dy, steps=5)
    nested = page.evaluate("() => [...document.querySelectorAll('[data-slot=drawer-popup][data-nested-drawer-open]')].map(p => [p.hasAttribute('data-nested-drawer-swiping'), +p.style.getPropertyValue('--drawer-swipe-progress')])")
    page.wait_for_timeout(300)
    page.mouse.up()
    assert len(nested) == 2 and all(s and 0 < p < 0.6 for s, p in nested), ("parents follow a nested swipe", nested)
    drawer_settle(t)
    assert page.evaluate("() => !document.querySelector('[data-nested-drawer-swiping]')")
    page.keyboard.press("Escape")
    wait(page, "() => !!document.querySelector('#drawer-nested-3 > dialog') && !document.querySelector('#drawer-nested-3 > dialog').open")
    drawer_settle(t)
    assert active(page) == "Open Third Drawer", ("focus returns to the nested trigger", active(page))
    middle = page.evaluate(DRAWER_STATE, "#" + child["id"])
    root = page.evaluate(DRAWER_STATE, "#drawer-nested-1")
    assert middle["attrs"] == ["data-nested"] and root["vars"]["--nested-drawers"] == "1", (middle, root)
    closed = page.evaluate("async () => { const { dialogClose, dialogOpen } = await import('/clanker-ui.js'); return [dialogClose('drawer-nested-2', 'api')] }")
    assert closed == [True], ("dialogClose takes the root of an open nested drawer", closed)
    wait(page, "() => !!document.querySelector('#drawer-nested-2 > dialog') && !document.querySelector('#drawer-nested-2 > dialog').open")
    drawer_settle(t)
    assert active(page) == "Open Nested Drawer", ("focus returns to the nested trigger", active(page))
    root = page.evaluate(DRAWER_STATE, "#drawer-nested-1")
    assert root["attrs"] == [] and root["vars"]["--nested-drawers"] == "0" and root["vars"]["--drawer-height"] == "initial" and root["content"] == 1, root
    opened = page.evaluate("async () => (await import('/clanker-ui.js')).dialogOpen(document.querySelector('#drawer-nested-2 > [data-drawer-trigger]'))")
    assert opened is True
    drawer_settle(t)
    page.locator(f"#{child['id']} > [data-slot=drawer-popup] > [data-slot=drawer-content] > [data-slot=drawer-footer] > [data-slot=drawer] > [data-drawer-trigger]").click()
    drawer_settle(t)
    close = """async cancel => {
      const seen = []
      const record = event => {
        seen.push([event.target.id, event.cancelable])
        if (cancel && event.target.id === "drawer-nested-1") event.preventDefault()
      }
      document.addEventListener("drawer:close", record)
      const { dialogClose } = await import("/clanker-ui.js")
      const result = dialogClose("drawer-nested-1", "api")
      document.removeEventListener("drawer:close", record)
      return [result, seen, [...document.querySelectorAll('#drawer dialog')].filter(d => d.open).length]
    }"""
    order = page.evaluate(close, True)
    assert order == [False, [["drawer-nested-1", True]], 3], ("a cancelled parent close keeps every drawer open", order)
    order = page.evaluate(close, False)
    assert order[:2] == [True, [["drawer-nested-1", True], ["drawer-nested-3", False], ["drawer-nested-2", False]]], ("the parent close event comes first, then the nested drawers close, the deepest first", order)
    wait(page, "() => [...document.querySelectorAll('#drawer dialog')].every(d => !d.open)")
    drawer_settle(t)
    state = page.evaluate("() => [document.querySelectorAll('dialog:modal').length, document.documentElement.style.overflow, document.querySelectorAll('[data-nested-drawer-open]').length, !!document.querySelector('#drawer-nested-3 > dialog'), !!document.querySelector('#drawer-nested-2 > dialog')]")
    assert state == [0, "", 0, True, True], ("no stale modal, scroll lock, or stack attribute", state)
    assert active(page) == "Open Drawer", active(page)
    page.evaluate("() => document.querySelectorAll('[data-demo-responsive-drawer]').forEach(r => r.toggleAttribute('data-show-swipe-handle', innerWidth < 768))")
    assert [e[1]["reason"] for e in events(page, "drawer:close")] == ["outside", "escape", "api", "api", "api", "api", "api"]


def drawer_snap_state(page, sel):
    return page.evaluate("""sel => {
      const v = document.querySelector(sel + ' dialog')
      const p = v.querySelector('[data-slot=drawer-popup]')
      return [p.style.getPropertyValue('--drawer-snap-point-offset'), p.hasAttribute('data-expanded'), v.style.getPropertyValue('--drawer-swipe-progress'), p.offsetHeight, Math.round(p.getBoundingClientRect().top)]
    }""", sel)


def check_drawer_snap_resize(t):
    page = t.page
    section = t.section("drawer")
    width, height = viewport(page)
    section.get_by_role("button", name="Open Snap Drawer").click()
    wait(page, "() => document.querySelector('#drawer-snap dialog').open")
    t.settle()
    before = drawer_snap_state(page, "#drawer-snap")
    assert before[0] == f"{height - 96 - 496}px", before
    page.set_viewport_size({"width": height, "height": width if width < height else 600})
    page.wait_for_timeout(700)
    t.settle()
    small = drawer_snap_state(page, "#drawer-snap")
    vh = page.evaluate("document.documentElement.clientHeight")
    ph = vh - 96
    assert small[3] == ph and small[0] == f"{max(0, ph - min(496, ph))}px" and not small[1], ("the snap offset follows a resize", small, vh)
    page.set_viewport_size({"width": width, "height": height})
    page.wait_for_timeout(700)
    t.settle()
    after = drawer_snap_state(page, "#drawer-snap")
    assert after == before, ("the snap point is right again after the rotation back", before, after)
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#drawer-snap dialog').open")


def check_drawer_snap_options(t):
    page = t.page
    t.section("drawer")
    listen(page, "drawer:snap-point-change", "drawer:close")
    width, height = viewport(page)
    ph = height - 96
    drawer_build(page, {"data-snap-points": "200px 0.5 1", "data-snap-to-sequential-points": "", "data-show-swipe-handle": ""}, False)
    page.locator("#built [data-drawer-trigger]").click()
    wait(page, "() => document.querySelector('#built dialog').open")
    t.settle()
    st = drawer_snap_state(page, "#built")
    assert st[0] == f"{ph - 200}px", ("a px snap point", st)
    handle = page.locator("#built [data-slot=drawer-swipe-handle]")
    drawer_handle_drag(page, handle, 0, -300, slow=False)
    t.settle()
    st = drawer_snap_state(page, "#built")
    assert st[0] == f"{round(ph - height * 0.5)}px" or abs(float(st[0][:-2]) - (ph - height * 0.5)) <= 1, ("sequential points stop at the next point, a fraction of the window", st)
    assert not st[1]
    drawer_handle_drag(page, handle, 0, -300, slow=False)
    t.settle()
    st = drawer_snap_state(page, "#built")
    assert st[0] == "0px" and st[1], ("the point 1 is expanded", st)
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#built dialog').open")
    snaps = [e[1]["snapPoint"] for e in events(page, "drawer:snap-point-change")]
    assert snaps == [0.5, 1, "200px"], ("settles and the reset on close send the event", snaps)
    drawer_build(page, {"data-snap-points": "31rem 1", "data-show-swipe-handle": ""}, False)
    page.locator("#built [data-drawer-trigger]").click()
    wait(page, "() => document.querySelector('#built dialog').open")
    t.settle()
    handle = page.locator("#built [data-slot=drawer-swipe-handle]")
    drawer_handle_drag(page, handle, 0, -80, slow=True)
    t.settle()
    assert drawer_snap_state(page, "#built")[0] == f"{ph - 496}px", "a slow short swipe settles on the same point"
    drawer_handle_drag(page, handle, 0, -80, slow=False)
    t.settle()
    st = drawer_snap_state(page, "#built")
    assert st[1] and st[0] == "0px", ("the release speed pushes a short fast swipe to the next point", st)
    drawer_handle_drag(page, handle, 0, 220, slow=True)
    t.settle()
    assert drawer_snap_state(page, "#built")[0] == f"{ph - 496}px"
    page.evaluate("() => document.addEventListener('drawer:close', e => e.preventDefault(), { once: true })")
    drawer_handle_drag(page, handle, 0, 400, slow=True)
    t.settle()
    st = drawer_snap_state(page, "#built")
    assert page.evaluate("document.querySelector('#built dialog').open") and st[0] == f"{ph - 496}px" and st[2] == "1" and not st[1], ("a cancelled close keeps the snap point", st)
    drawer_handle_drag(page, handle, 0, -20, slow=True)
    t.settle()
    assert drawer_snap_state(page, "#built")[0] == f"{ph - 496}px", "after a cancelled close a short swipe stays on the point"
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#built dialog').open")
    snaps = [e[1]["snapPoint"] for e in events(page, "drawer:snap-point-change")][3:]
    assert snaps == ["31rem", 1, "31rem", None, "31rem", "31rem", "31rem"], ("events as Base UI onSnapPointChange", snaps)
    drawer_build(page, {"data-snap-points": "31rem 1", "data-swipe-direction": "up", "data-show-swipe-handle": ""}, False)
    page.locator("#built [data-drawer-trigger]").click()
    wait(page, "() => document.querySelector('#built dialog').open")
    t.settle()
    st = drawer_snap_state(page, "#built")
    assert st[0] == f"-{ph - 496}px" and abs(st[4] - (496 - ph)) <= 1, ("an up drawer moves up by the offset", st)
    drawer_handle_drag(page, page.locator("#built [data-slot=drawer-swipe-handle]"), 0, 300, slow=True)
    t.settle()
    st = drawer_snap_state(page, "#built")
    assert st[1] and st[0] == "0px", ("a swipe down expands an up drawer", st)
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#built dialog').open")
    page.evaluate("() => document.getElementById('built').remove()")


def check_toast_dialog_focus(t):
    page = t.page
    section = t.section("dialog")
    page.evaluate("async () => (await import('/clanker-ui.js')).toast('Saved', { id: 'focus', timeout: 0, action: { label: 'Undo', onClick() {} } })")
    page.locator("[data-slot=toast]").wait_for()
    section.get_by_role("button", name="No Close Button").click()
    wait(page, "() => [...document.querySelectorAll('#dialog dialog')].some(d => d.open)")
    focus = page.evaluate("() => [document.activeElement.localName, document.activeElement.dataset.slot, !!document.activeElement.closest('[data-slot=toast-portal]')]")
    assert focus == ["dialog", "dialog-content", False], ("first focus never goes to a toast", focus)
    page.keyboard.press("Escape")
    wait(page, "() => [...document.querySelectorAll('#dialog dialog')].every(d => !d.open)")
    assert page.locator("[data-slot=toast]").count() == 1, "Escape closes the dialog, not the toast"
    page.evaluate("async () => (await import('/clanker-ui.js')).toast.close()")
    wait(page, "() => !document.querySelector('[data-slot=toast]')")


def check_toast_above_popover(t):
    page = t.page
    t.section("toast")
    assert not page.evaluate("document.querySelector('[data-slot=toast-viewport]').matches(':popover-open')"), "no toast, no open viewport"
    page.evaluate("""async () => {
      const { h } = await import("/clanker-ui.js")
      const cover = h("div", { popover: "manual", id: "cover" })
      Object.assign(cover.style, { position: "fixed", inset: "0", width: "100vw", height: "100vh", margin: "0", background: "rgb(0 0 0 / 0.2)" })
      document.body.append(cover)
      cover.showPopover()
    }""")
    page.evaluate("async () => (await import('/clanker-ui.js')).toast('Above the cover', { timeout: 0 })")
    item = page.locator("[data-slot=toast]")
    item.wait_for()
    page.wait_for_timeout(600)
    b = box(item)
    hit = page.evaluate("([x, y]) => document.elementFromPoint(x, y)?.closest('[data-slot=toast]') ? 'toast' : document.elementFromPoint(x, y)?.id", [b["x"] + b["width"] / 2, b["y"] + b["height"] / 2])
    assert hit == "toast", ("a new toast shows above a newer top-layer item", hit)
    page.evaluate("async () => { (await import('/clanker-ui.js')).toast.close(); document.getElementById('cover').remove() }")
    wait(page, "() => !document.querySelector('[data-slot=toast]')")
    page.wait_for_timeout(100)
    assert not page.evaluate("document.querySelector('[data-slot=toast-viewport]').matches(':popover-open')")


TOUCH_LISTENERS = """
(() => {
  const live = new Set()
  window.__touchListeners = live
  const add = EventTarget.prototype.addEventListener
  const remove = EventTarget.prototype.removeEventListener
  const capture = o => (typeof o === "object" ? !!o?.capture : !!o)
  EventTarget.prototype.addEventListener = function (type, fn, options) {
    if (this === document && type === "touchmove" && typeof options === "object" && options.passive === false) live.add([fn, capture(options)])
    return add.call(this, type, fn, options)
  }
  EventTarget.prototype.removeEventListener = function (type, fn, options) {
    if (this === document && type === "touchmove") for (const entry of [...live]) if (entry[0] === fn && entry[1] === capture(options)) live.delete(entry)
    return remove.call(this, type, fn, options)
  }
})()
"""


def check_drawer_touch_listener(t):
    page = t.page
    page.add_init_script(TOUCH_LISTENERS)
    page.reload(wait_until="load")
    section = t.section("drawer")
    count = lambda: page.evaluate("window.__touchListeners.size")
    assert count() == 0, "no scroll-blocking touch listener while no drawer is open"
    drawer_open(page, "#drawer-handle")
    assert count() == 1, count()
    page.keyboard.press("Escape")
    drawer_closed(page, "#drawer-handle")
    assert count() == 0, count()


def drawer_build(page, attrs, handle):
    page.evaluate(
        """async ([attrs, handle]) => {
          const { h } = await import("/clanker-ui.js")
          document.getElementById("built")?.remove()
          const root = h("div", { "data-slot": "drawer", id: "built", ...attrs },
            h("button", { type: "button", "data-slot": "button", "data-drawer-trigger": "" }, "Open built"),
            h("dialog", { "data-slot": "drawer-viewport" },
              h("div", { "data-slot": "drawer-popup" },
                handle ? h("div", { "data-slot": "drawer-swipe-handle", "aria-hidden": "true", "data-mine": "" }) : null,
                h("div", { "data-slot": "drawer-content" },
                  h("div", { "data-slot": "drawer-header" }, h("h2", { "data-slot": "drawer-title" }, "Built")),
                  h("div", { "data-slot": "drawer-footer" }, h("button", { type: "button", "data-slot": "button", id: "built-a" }, "First"), h("button", { type: "button", "data-slot": "button", "data-drawer-close": "" }, "Close"))))))
          document.querySelector("#drawer [data-demo~=preview]").append(root)
        }""",
        [attrs, handle],
    )


def check_drawer_options(t):
    page = t.page
    t.section("drawer")
    drawer_build(page, {}, True)
    page.locator("#built [data-drawer-trigger]").click()
    wait(page, "() => document.querySelector('#built dialog').open")
    assert page.locator("#built [data-slot=drawer-swipe-handle][data-mine]").count() == 1, "an author-written swipe handle stays"
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#built dialog').open")
    drawer_build(page, {"data-modal": "trap-focus", "data-swipe-direction": "right"}, False)
    page.locator("#built [data-drawer-trigger]").click()
    wait(page, "() => document.querySelector('#built dialog').open")
    t.settle()
    state = page.evaluate("() => { const v = document.querySelector('#built dialog'); return [v.dataset.modal, v.matches(':modal'), document.documentElement.style.overflow] }")
    assert state == ["trap-focus", False, ""], state
    page.locator("#built-a").focus()
    for _ in range(3):
        page.keyboard.press("Tab")
        assert page.evaluate("() => !!document.activeElement.closest('#built dialog')"), "focus stays in a trap-focus drawer"
    page.keyboard.press("Shift+Tab")
    assert page.evaluate("() => !!document.activeElement.closest('#built dialog')")
    width, height = viewport(page)
    page.mouse.click(10, height / 2)
    wait(page, "() => !document.querySelector('#built dialog').open")
    page.evaluate("() => document.getElementById('built').remove()")


def check_hide_after_rejected(t):
    page = t.page
    result = page.evaluate(
        """async () => {
          const { h, show, hide } = await import("/clanker-ui.js")
          const el = h("div", { popover: "manual" }, "x")
          document.body.append(el)
          show(el, { anchor: null, focus: null })
          await hide(el, { after: Promise.reject(new Error("animation failed")) })
          const out = [el.matches(":popover-open"), el.dataset.state]
          el.remove()
          return out
        }"""
    )
    assert result == [False, "closed"], ("a failed after promise still closes the element", result)


def check_popover(t):
    page = t.page
    section = t.section("popover")
    listen(page, "popover:open", "popover:close")
    trigger = section.locator("#popover-demo").get_by_role("button", name="Open Popover")
    content = section.locator("#popover-demo [data-slot=popover-content]")
    assert trigger.get_attribute("aria-haspopup") == "dialog"
    trigger.click()
    pop = page.get_by_role("dialog", name="Dimensions")
    assert pop.is_visible()
    assert trigger.get_attribute("aria-expanded") == "true"
    assert trigger.get_attribute("aria-controls") == content.get_attribute("id")
    t.settle()
    tb, cb = inline(t, box(trigger)), inline(t, box(content))
    width, height = viewport(page)
    assert cb["y"] >= tb["y"] + tb["height"] + 3, (tb, cb)
    if tb["x"] + cb["width"] < width - 8:
        assert abs(cb["x"] - tb["x"]) <= 1, (tb, cb)
    assert content.get_attribute("data-side") == "bottom" and content.get_attribute("data-align") == "start"
    assert active(page, "e => e.dataset.slot") == "popover-content"
    assert [trigger.get_attribute("data-popup-open"), trigger.get_attribute("data-pressed"), content.get_attribute("data-open")] == ["", "", ""]
    t.shot("popover-open", page)
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#popover-demo [data-slot=popover-content]').matches(':popover-open')")
    assert active(page) == "Open Popover"
    assert [trigger.get_attribute("data-popup-open"), trigger.get_attribute("data-pressed"), content.get_attribute("data-closed")] == [None, None, ""]
    trigger.click()
    away(page)
    page.mouse.down()
    page.mouse.up()
    wait(page, "() => !document.querySelector('#popover-demo [data-slot=popover-content]').matches(':popover-open')")
    for name in ["Start", "Center", "End"]:
        aligns = section.locator("[data-demo~=preview]").nth(1)
        button = aligns.get_by_role("button", name=name, exact=True)
        button.click()
        panel = aligns.locator(f"[data-slot=popover-content][data-align={name.lower()}]")
        t.settle()
        bb, pb = inline(t, box(button)), inline(t, box(panel))
        width, height = viewport(page)
        if name == "Start" and pb["x"] > 9:
            assert abs(pb["x"] - bb["x"]) <= 1, (bb, pb)
        if name == "End" and pb["x"] + pb["width"] < width - 9:
            assert abs(pb["x"] + pb["width"] - bb["x"] - bb["width"]) <= 1, (bb, pb)
        if name == "Center" and pb["x"] > 9 and pb["x"] + pb["width"] < width - 9:
            assert abs(pb["x"] + pb["width"] / 2 - bb["x"] - bb["width"] / 2) <= 1, (bb, pb)
        button.click()
        wait(page, "() => !document.querySelector('#popover [data-slot=popover-content]:popover-open')")
    form = section.locator("#popover-form")
    form.get_by_role("button", name="Open Popover").click()
    assert active(page, "e => e.id") == "popover-width"
    t.settle()
    t.shot("popover-form", page)
    page.keyboard.press("Tab")
    assert active(page, "e => e.id") == "popover-height"
    if t.engine == "webkit":
        section.get_by_role("button", name="Open modal popover").focus()
    else:
        page.keyboard.press("Tab")
    wait(page, "() => !document.querySelector('#popover-form [data-slot=popover-content]').matches(':popover-open')")
    modal = section.get_by_role("button", name="Open modal popover")
    modal.click()
    panel = page.locator("#popover [data-modal] [data-slot=popover-content]")
    t.settle()
    anchor = box(section.locator("[data-slot=popover-anchor]"))
    pb = box(panel)
    if panel.get_attribute("data-side") == "top":
        assert pb["y"] + pb["height"] <= anchor["y"] + 1, (anchor, pb)
    else:
        assert pb["y"] >= anchor["y"] + anchor["height"] - 1, (anchor, pb)
    width, height = viewport(page)
    if pb["x"] > 9 and pb["x"] + pb["width"] < width - 9:
        assert abs(pb["x"] + pb["width"] / 2 - anchor["x"] - anchor["width"] / 2) <= 1, (anchor, pb)
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") == "hidden"
    page.keyboard.press("Tab")
    assert panel.evaluate("p => p.contains(document.activeElement)")
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#popover [data-modal] [data-slot=popover-content]').matches(':popover-open')")
    reasons = [e[1].get("reason") for e in events(page, "popover:close")]
    assert reasons == ["escape", "outside", "trigger", "trigger", "trigger", "focus", "escape"], reasons


def check_tooltip(t):
    page = t.page
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    section = t.section("tooltip")
    listen(page, "tooltip:open", "tooltip:close")
    trigger = section.locator("#tooltip-demo").get_by_role("button", name="Hover")
    content = section.locator("#tooltip-demo [data-slot=tooltip-content]")
    assert content.get_attribute("id") in (trigger.get_attribute("aria-describedby") or "").split()
    trigger.hover()
    tip = page.get_by_role("tooltip", name="Add to library").first
    wait(page, "() => document.querySelector('#tooltip-demo [data-slot=tooltip-content]').matches(':popover-open')")
    assert content.get_attribute("data-side") == "top"
    t.settle()
    tb, cb = box(trigger), box(content)
    assert abs(tb["y"] - cb["y"] - cb["height"] - 4) <= 1 and abs(cb["x"] + cb["width"] / 2 - tb["x"] - tb["width"] / 2) <= 1, (tb, cb)
    arrow = content.locator("[data-slot=tooltip-arrow]")
    assert arrow.count() == 1
    ab = box(arrow)
    assert arrow.get_attribute("data-side") == "top" and arrow.evaluate("e => getComputedStyle(e).position") == "absolute"
    assert abs(ab["x"] + ab["width"] / 2 - tb["x"] - tb["width"] / 2) <= 1 and ab["y"] + ab["height"] > cb["y"] + cb["height"] + 3 and ab["y"] < cb["y"] + cb["height"], (tb, cb, ab)
    assert tip.is_visible()
    t.shot("tooltip-open", page)
    away(page)
    wait(page, "() => !document.querySelector('#tooltip-demo [data-slot=tooltip-content]').matches(':popover-open')")
    for side in ["left", "right", "bottom"]:
        button = section.get_by_role("button", name=side.capitalize(), exact=True)
        button.evaluate("b => new Promise(r => { b.scrollIntoView({ block: 'center', behavior: 'instant' }); requestAnimationFrame(() => requestAnimationFrame(r)) })")
        button.hover()
        panel = button.locator("xpath=..").locator("[data-slot=tooltip-content]")
        panel.evaluate("p => new Promise(r => { const tick = () => p.matches(':popover-open') ? r() : requestAnimationFrame(tick); tick() })")
        t.settle()
        bb, pb = box(button), box(panel)
        resolved = panel.get_attribute("data-side")
        flipped = side == "bottom" and resolved == "top" and viewport(page)[1] - bb["y"] - bb["height"] < pb["height"] + 4 + 5
        assert resolved == side or flipped or (side in ("left", "right") and resolved in ("left", "right")), (resolved, bb, pb, viewport(page))
        ab = box(panel.locator("[data-slot=tooltip-arrow]"))
        assert panel.locator("[data-slot=tooltip-arrow]").get_attribute("data-side") == resolved
        if resolved == "left":
            assert abs(bb["x"] - pb["x"] - pb["width"] - 4) <= 1 and ab["x"] + ab["width"] > pb["x"] + pb["width"] + 3, (bb, pb, ab)
        if resolved == "right":
            assert abs(pb["x"] - bb["x"] - bb["width"] - 4) <= 1 and ab["x"] < pb["x"] - 3, (bb, pb, ab)
        if resolved in ("left", "right") and abs(pb["y"] + pb["height"] / 2 - bb["y"] - bb["height"] / 2) <= 1:
            assert abs(ab["y"] + ab["height"] / 2 - bb["y"] - bb["height"] / 2) <= 1, (bb, ab)
        if resolved == "bottom":
            assert abs(pb["y"] - bb["y"] - bb["height"] - 4) <= 1 and ab["y"] < pb["y"] - 3, (bb, pb, ab)
            assert abs(ab["x"] + ab["width"] / 2 - bb["x"] - bb["width"] / 2) <= 1, (bb, ab)
            t.shot("tooltip-bottom", page)
        away(page)
        wait(page, "() => !document.querySelector('#tooltip [data-slot=tooltip-content]:popover-open')")
    away(page)
    wait(page, "() => !document.querySelector('#tooltip [data-slot=tooltip-content]:popover-open')")
    trigger.hover()
    wait(page, "() => document.querySelector('#tooltip-demo [data-slot=tooltip-content]').matches(':popover-open')")
    t.settle()
    tb, cb = box(trigger), box(content)
    above = content.get_attribute("data-side") == "top"
    edge = tb["y"] + 2 if above else tb["y"] + tb["height"] - 2
    gap = (cb["y"] + cb["height"] + tb["y"]) / 2 if above else (tb["y"] + tb["height"] + cb["y"]) / 2
    page.mouse.move(tb["x"] + tb["width"] / 2, edge, steps=2)
    page.mouse.move(tb["x"] + tb["width"] / 2, gap, steps=2)
    page.mouse.move(cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2, steps=3)
    page.wait_for_timeout(100)
    assert is_open(content)
    away(page)
    wait(page, "() => !document.querySelector('#tooltip-demo [data-slot=tooltip-content]').matches(':popover-open')")
    page.wait_for_timeout(350)
    keyboard_focus(page, trigger)
    wait(page, "() => document.querySelector('#tooltip-demo [data-slot=tooltip-content]').matches(':popover-open')")
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#tooltip-demo [data-slot=tooltip-content]').matches(':popover-open')")
    assert active(page) == "Hover"
    trigger.evaluate("e => e.blur()")
    trigger.hover()
    wait(page, "() => document.querySelector('#tooltip-demo [data-slot=tooltip-content]').matches(':popover-open')")
    page.mouse.down()
    page.mouse.up()
    wait(page, "() => !document.querySelector('#tooltip-demo [data-slot=tooltip-content]').matches(':popover-open')")
    away(page)
    page.wait_for_timeout(350)
    touched = trigger.evaluate("""e => {
      e.dispatchEvent(new PointerEvent('pointerover', { bubbles: true, pointerType: 'touch', isPrimary: true }))
      return new Promise(r => setTimeout(() => r(document.querySelector('#tooltip-demo [data-slot=tooltip-content]').matches(':popover-open')), 150))
    }""")
    assert touched is False
    delayed = section.locator("#tooltip-delay")
    delayed.get_by_role("button").hover()
    page.wait_for_timeout(300)
    assert not is_open(delayed.locator("[data-slot=tooltip-content]"))
    wait(page, "() => document.querySelector('#tooltip-delay [data-slot=tooltip-content]').matches(':popover-open')", timeout=2000)
    section.locator("#tooltip-disabled [data-tooltip-trigger]").hover()
    wait(page, "() => document.querySelector('#tooltip-disabled [data-slot=tooltip-content]').matches(':popover-open')")
    wait(page, "() => !document.querySelector('#tooltip-delay [data-slot=tooltip-content]').matches(':popover-open')")
    away(page)
    wait(page, "() => !document.querySelector('#tooltip [data-slot=tooltip-content]:popover-open')")
    assert len(events(page, "tooltip:open")) >= 8


def check_hover_card(t):
    page = t.page
    section = t.section("hover-card")
    listen(page, "hover-card:open", "hover-card:close")
    trigger = section.locator("#hover-card-demo [data-hover-card-trigger]")
    content = section.locator("#hover-card-demo [data-slot=hover-card-content]")
    trigger.hover()
    wait(page, "() => document.querySelector('#hover-card-demo [data-slot=hover-card-content]').matches(':popover-open')", timeout=1000)
    assert trigger.get_attribute("data-state") == "open"
    t.settle()
    tb, cb = box(trigger), box(content)
    assert abs(cb["y"] - tb["y"] - tb["height"] - 4) <= 1, (tb, cb)
    width, height = viewport(page)
    if cb["x"] > 6 and cb["x"] + cb["width"] < width - 6:
        assert abs(cb["x"] + cb["width"] / 2 - tb["x"] - tb["width"] / 2 - (-4 if t.rtl else 4)) <= 1, ("alignOffset 4, mirrored in RTL", tb, cb)
    assert trigger.get_attribute("data-popup-open") == "" and content.get_attribute("data-open") == ""
    t.shot("hover-card-open", page)
    page.mouse.move(tb["x"] + tb["width"] / 2, tb["y"] + tb["height"] + 2, steps=2)
    page.mouse.move(cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2, steps=4)
    page.wait_for_timeout(250)
    assert is_open(content)
    away(page)
    wait(page, "() => !document.querySelector('#hover-card-demo [data-slot=hover-card-content]').matches(':popover-open')", timeout=1500)
    delays = section.locator("#hover-card-delays")
    page.evaluate("""() => {
      window.__hc = {}
      for (const type of ["hover-card:open", "hover-card:close"]) document.getElementById("hover-card-delays").addEventListener(type, () => { window.__hc[type] = performance.now() })
    }""")
    started = page.evaluate("() => performance.now()")
    delays.locator("[data-hover-card-trigger]").hover()
    wait(page, "() => document.querySelector('#hover-card-delays [data-slot=hover-card-content]').matches(':popover-open')", timeout=3000)
    assert 550 <= page.evaluate("() => window.__hc['hover-card:open']") - started <= 1000
    left = page.evaluate("() => performance.now()")
    away(page)
    wait(page, "() => !document.querySelector('#hover-card-delays [data-slot=hover-card-content]').matches(':popover-open')", timeout=3000)
    assert page.evaluate("() => window.__hc['hover-card:close']") - left >= 250
    keyboard_focus(page, trigger)
    wait(page, "() => document.querySelector('#hover-card-demo [data-slot=hover-card-content]').matches(':popover-open')", timeout=1000)
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#hover-card-demo [data-slot=hover-card-content]').matches(':popover-open')")
    trigger.evaluate("e => e.blur()")
    touched = trigger.evaluate("""e => {
      e.dispatchEvent(new PointerEvent('pointerover', { bubbles: true, pointerType: 'touch', isPrimary: true }))
      return new Promise(r => setTimeout(() => r(document.querySelector('#hover-card-demo [data-slot=hover-card-content]').matches(':popover-open')), 200))
    }""")
    assert touched is False
    right = section.get_by_role("button", name="Right", exact=True)
    right.hover()
    panel = right.locator("xpath=..").locator("[data-slot=hover-card-content]")
    panel.evaluate("p => new Promise(r => { const tick = () => p.matches(':popover-open') ? r() : requestAnimationFrame(tick); tick() })")
    t.settle()
    rb, pb = box(right), box(panel)
    width, height = viewport(page)
    if rb["x"] + rb["width"] + pb["width"] + 12 < width:
        assert pb["x"] >= rb["x"] + rb["width"] + 3, (rb, pb)
    else:
        assert panel.get_attribute("data-side") == "left"
    away(page)
    wait(page, "() => !document.querySelector('#hover-card [data-slot=hover-card-content]:popover-open')", timeout=1500)
    assert len(events(page, "hover-card:open")) == len(events(page, "hover-card:close")) == 4


def check_dropdown_menu(t):
    page = t.page
    section = t.section("dropdown-menu")
    listen(page, "dropdown-menu:open", "dropdown-menu:close", "dropdown-menu:select", "dropdown-menu:change")
    trigger = section.locator("#dropdown-menu-demo").get_by_role("button", name="Open")
    content = section.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    open_js = "() => document.querySelector('#dropdown-menu-demo > [data-slot=dropdown-menu-content]').matches(':popover-open')"
    closed_js = "() => !document.querySelector('#dropdown-menu-demo > [data-slot=dropdown-menu-content]').matches(':popover-open')"
    assert trigger.get_attribute("aria-haspopup") == "menu"
    trigger.click()
    menu = page.get_by_role("menu", name="Open")
    assert menu.is_visible()
    assert trigger.get_attribute("aria-expanded") == "true"
    assert active(page, "e => e.getAttribute('role')") == "menu"
    assert content.get_by_role("menuitem", name="API").get_attribute("aria-disabled") == "true"
    t.settle()
    tb, cb = inline(t, box(trigger)), inline(t, box(content))
    width, height = viewport(page)
    if tb["x"] + cb["width"] <= width - 5:
        assert abs(cb["x"] - tb["x"]) <= 1, (tb, cb)
    else:
        assert abs(cb["x"] + cb["width"] - (width - 5)) <= 1, (tb, cb)
    assert abs(cb["y"] - tb["y"] - tb["height"] - 4) <= 1, (tb, cb)
    content.get_by_role("menuitem", name="Billing").hover()
    assert active(page) == "Billing⌘B"
    assert content.locator("[data-highlighted]").evaluate_all("els => els.map(e => e.textContent)") == ["Billing⌘B"]
    t.shot("dropdown-menu-open", page)
    page.keyboard.press("Escape")
    wait(page, closed_js)
    assert active(page) == "Open"
    page.keyboard.press("Enter")
    wait(page, open_js)
    assert active(page) == "Profile⇧⌘P"
    page.keyboard.press("ArrowDown")
    assert active(page) == "Billing⌘B"
    page.keyboard.press("End")
    assert active(page) == "Log out⇧⌘Q"
    page.keyboard.press("ArrowDown")
    assert active(page) == "Profile⇧⌘P"
    page.keyboard.press("ArrowUp")
    assert active(page) == "Log out⇧⌘Q"
    page.keyboard.press("ArrowUp")
    assert active(page) == "API"
    page.keyboard.press("ArrowUp")
    assert active(page) == "Support"
    page.keyboard.press("Home")
    assert active(page) == "Profile⇧⌘P"
    page.keyboard.press("t")
    assert active(page) == "Team"
    page.keyboard.press("ArrowDown")
    assert active(page) == "Invite users"
    page.keyboard.press(key(t, "ArrowRight"))
    sub = content.locator("[data-slot=dropdown-menu-sub-content]")
    assert is_open(sub)
    assert active(page) == "Email"
    invite = content.get_by_role("menuitem", name="Invite users")
    assert invite.get_attribute("aria-expanded") == "true"
    assert invite.get_attribute("data-popup-open") == "" and invite.get_attribute("data-highlighted") is None, "focus in the sub menu removes the highlight from its trigger (live Base UI)"
    assert sub.get_attribute("data-open") == "" and sub.get_attribute("data-side") in ("left", "right")
    t.settle()
    t.shot("dropdown-menu-submenu", page)
    page.keyboard.press(key(t, "ArrowLeft"))
    assert active(page) == "Invite users"
    wait(page, "() => !document.querySelector('#dropdown-menu-demo [data-slot=dropdown-menu-sub-content]').matches(':popover-open')")
    page.keyboard.press(key(t, "ArrowRight"))
    page.keyboard.press("Escape")
    assert active(page) == "Invite users"
    assert is_open(content)
    page.keyboard.press("Escape")
    wait(page, closed_js)
    assert active(page) == "Open"
    page.keyboard.press("ArrowUp")
    wait(page, open_js)
    assert active(page) == "Log out⇧⌘Q"
    page.keyboard.press("ArrowUp")
    page.keyboard.press("ArrowUp")
    page.keyboard.press("ArrowUp")
    assert active(page) == "GitHub"
    page.keyboard.press("Enter")
    wait(page, closed_js)
    assert active(page) == "Open"
    trigger.click()
    wait(page, open_js)
    t.settle()
    content.get_by_role("menuitem", name="Invite users").hover()
    wait(page, "() => document.querySelector('#dropdown-menu-demo [data-slot=dropdown-menu-sub-content]').matches(':popover-open')")
    t.settle()
    assert is_open(sub), page.evaluate("() => ({ active: document.activeElement?.textContent.slice(0, 20), keyboard: document.documentElement.hasAttribute('data-keyboard'), highlighted: [...document.querySelectorAll('#dropdown-menu-demo [data-highlighted]')].map(e => e.textContent.slice(0, 20)) })")
    email = content.get_by_role("menuitem", name="Email")
    ib, eb = inline(t, box(content.get_by_role("menuitem", name="Invite users"))), inline(t, box(email))
    page.mouse.move(px(t, ib["x"] + ib["width"] - 4), ib["y"] + ib["height"] / 2, steps=2)
    page.mouse.move(px(t, eb["x"] + 10), eb["y"] + eb["height"] / 2, steps=4)
    assert is_open(sub)
    email.click()
    wait(page, closed_js)
    trigger.click()
    wait(page, open_js)
    page.keyboard.press("Tab")
    wait(page, closed_js)
    selects = [e[1]["value"] for e in events(page, "dropdown-menu:select")]
    assert selects == ["GitHub", "Email"], selects
    reasons = [e[1]["reason"] for e in events(page, "dropdown-menu:close")]
    assert reasons == ["escape", "escape", "select", "select", "tab"], reasons
    checks = section.locator("#dropdown-menu-checkboxes")
    checks.get_by_role("button", name="Appearance").click()
    status = checks.get_by_role("menuitemcheckbox", name="Status Bar")
    panel = checks.get_by_role("menuitemcheckbox", name="Panel")
    assert status.get_attribute("aria-checked") == "true" and panel.get_attribute("aria-checked") == "false"
    assert status.locator("[data-slot=dropdown-menu-checkbox-item-indicator] > span[data-checked] > svg[data-lucide=check]").is_visible()
    assert panel.locator("[data-slot=dropdown-menu-checkbox-item-indicator] svg").count() == 0
    assert checks.get_by_role("menuitemcheckbox", name="Activity Bar").get_attribute("aria-disabled") == "true"
    t.settle()
    t.shot("dropdown-menu-checkboxes", page)
    panel.click()
    page.wait_for_timeout(200)
    assert is_open(checks.locator("[data-slot=dropdown-menu-content]")), "checkbox items keep the menu open, as in Base UI"
    panel = checks.locator("[data-slot=dropdown-menu-checkbox-item]").nth(2)
    assert panel.get_attribute("aria-checked") == "true" and panel.get_attribute("data-state") == "checked" and panel.get_attribute("data-checked") == ""
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#dropdown-menu-checkboxes [data-slot=dropdown-menu-content]').matches(':popover-open')")
    radios = section.locator("#dropdown-menu-radio")
    radios.get_by_role("button", name="Panel Position").click()
    radios.get_by_role("menuitemradio", name="Top").click()
    items = radios.locator("[data-slot=dropdown-menu-radio-item]")
    assert items.nth(0).get_attribute("aria-checked") == "true"
    assert items.nth(1).get_attribute("aria-checked") == "false"
    assert radios.locator("[data-slot=dropdown-menu-radio-group]").get_attribute("data-value") == "top"
    assert items.nth(0).locator("[data-slot=dropdown-menu-radio-item-indicator] svg[data-lucide=check]").count() == 1
    assert is_open(radios.locator("[data-slot=dropdown-menu-content]")), "radio items keep the menu open, as in Base UI"
    changes = [(e[1]["value"], e[1]["checked"]) for e in events(page, "dropdown-menu:change")]
    assert changes == [("Panel", True), ("top", True)], changes
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#dropdown-menu-radio [data-slot=dropdown-menu-content]').matches(':popover-open')")
    section.get_by_role("button", name="More options").click()
    t.settle()
    t.shot("dropdown-menu-icons", page)
    page.keyboard.press("Escape")


def check_context_menu(t):
    page = t.page
    section = t.section("context-menu")
    listen(page, "context-menu:open", "context-menu:close", "context-menu:select", "context-menu:change")
    area = section.locator("#context-menu-demo [data-slot=context-menu-trigger]")
    content = section.locator("#context-menu-demo > [data-slot=context-menu-content]")
    open_js = "() => document.querySelector('#context-menu-demo > [data-slot=context-menu-content]').matches(':popover-open')"
    closed_js = "() => !document.querySelector('#context-menu-demo > [data-slot=context-menu-content]').matches(':popover-open')"
    ab = box(area)
    x, y = ab["x"] + 40, ab["y"] + 30
    page.mouse.click(x, y, button="right")
    wait(page, open_js)
    assert area.get_attribute("data-state") == "open"
    t.settle()
    cb = box(content)
    assert abs(cb["x"] - x) <= 1 and abs(cb["y"] - y - 4) <= 1, (x, y, cb)
    assert area.get_attribute("data-popup-open") == "" and content.get_attribute("data-instant") == "click"
    assert content.get_by_role("menuitemcheckbox", name="Show Bookmarks").get_attribute("aria-checked") == "true"
    assert content.get_by_role("menuitemradio", name="Pedro Duarte").get_attribute("aria-checked") == "true"
    content.get_by_role("menuitem", name="More Tools").hover()
    wait(page, "() => document.querySelector('#context-menu-demo [data-slot=context-menu-sub-content]').matches(':popover-open')")
    t.settle()
    t.shot("context-menu-open", page)
    page.mouse.click(x - 20, y + 5, button="right")
    wait(page, open_js)
    t.settle()
    cb = box(content)
    assert abs(cb["x"] - x + 20) <= 1 and abs(cb["y"] - y - 9) <= 1, (x, y, cb)
    page.keyboard.press("Escape")
    wait(page, closed_js)
    assert area.get_attribute("data-state") == "closed"
    area.focus()
    page.keyboard.press("Shift+F10")
    wait(page, open_js)
    assert active(page) == "Back⌘["
    page.keyboard.press("ArrowDown")
    assert active(page) == "Forward⌘]"
    page.keyboard.press("ArrowDown")
    assert active(page) == "Reload⌘R"
    page.keyboard.press("ArrowDown")
    assert active(page) == "More Tools"
    page.keyboard.press(key(t, "ArrowRight"))
    assert active(page) == "Save Page..."
    page.keyboard.press(key(t, "ArrowLeft"))
    assert active(page) == "More Tools"
    page.keyboard.press("ArrowUp")
    page.keyboard.press("Enter")
    wait(page, closed_js)
    page.mouse.click(x, y, button="right")
    wait(page, open_js)
    content.get_by_role("menuitemcheckbox", name="Show Full URLs").click()
    page.wait_for_timeout(200)
    assert is_open(content) and content.get_by_role("menuitemcheckbox", name="Show Full URLs").get_attribute("aria-checked") == "true"
    content.get_by_role("menuitemradio", name="Colm Tuite").click()
    page.wait_for_timeout(200)
    assert is_open(content) and content.get_by_role("menuitemradio", name="Colm Tuite").get_attribute("aria-checked") == "true"
    page.keyboard.press("Escape")
    wait(page, closed_js)
    page.mouse.click(x, y, button="right")
    wait(page, open_js)
    away(page)
    page.mouse.down()
    page.mouse.up()
    wait(page, closed_js)
    area.evaluate("""a => {
      const r = a.getBoundingClientRect()
      a.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 9, pointerType: 'touch', isPrimary: true, clientX: r.left + 20, clientY: r.top + 20 }))
    }""")
    page.wait_for_timeout(400)
    assert not is_open(content)
    wait(page, open_js, timeout=1500)
    area.evaluate("a => a.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 9, pointerType: 'touch', isPrimary: true }))")
    page.keyboard.press("Escape")
    wait(page, closed_js)
    selects = [e[1]["value"] for e in events(page, "context-menu:select")]
    assert selects == ["Reload", "Show Full URLs", "colm"], selects
    changes = [(e[1]["value"], e[1]["checked"]) for e in events(page, "context-menu:change")]
    assert changes == [("Show Full URLs", True), ("colm", True)], changes
    second = section.locator("[data-slot=context-menu]").nth(1)
    sb = box(second.locator("[data-slot=context-menu-trigger]"))
    page.mouse.click(sb["x"] + 20, sb["y"] + 20, button="right")
    t.settle()
    t.shot("context-menu-icons", page)
    page.keyboard.press("Escape")


def check_menubar(t):
    page = t.page
    section = t.section("menubar")
    listen(page, "menubar:open", "menubar:close", "menubar:select", "menubar:change")
    bar = page.locator("#menubar-demo")
    file = bar.get_by_role("menuitem", name="File", exact=True)
    edit = bar.get_by_role("menuitem", name="Edit", exact=True)
    view = bar.get_by_role("menuitem", name="View", exact=True)
    profiles = bar.get_by_role("menuitem", name="Profiles", exact=True)
    tabindexes = bar.locator("[data-slot=menubar-trigger]").evaluate_all("els => els.map(e => e.tabIndex)")
    assert tabindexes == [0, -1, -1, -1], tabindexes
    assert file.get_attribute("aria-haspopup") == "menu"
    file.click()
    menu = page.get_by_role("menu", name="File", exact=True)
    assert menu.is_visible()
    assert file.get_attribute("aria-expanded") == "true"
    t.settle()
    fb, mb = inline(t, box(file)), inline(t, box(menu))
    assert abs(mb["y"] - (fb["y"] + fb["height"] + 8)) <= 1 and abs(mb["x"] - (fb["x"] - 4)) <= 1, (fb, mb)
    edit.hover()
    wait(page, "() => document.querySelectorAll('#menubar-demo [data-slot=menubar-content]:popover-open').length === 1 && document.querySelectorAll('#menubar-demo [data-slot=menubar-content]')[1].matches(':popover-open')")
    assert active(page, "e => e.dataset.slot + ' ' + e.getAttribute('aria-labelledby')") == "menubar-content " + edit.get_attribute("id")
    assert section.locator("[data-slot=menubar-content]").nth(1).get_attribute("data-instant") == "group"
    assert bar.locator("[data-slot=menubar-trigger]").evaluate_all("els => els.map(e => e.tabIndex)") == [-1, 0, -1, -1]
    t.settle()
    t.shot("menubar-open", page)
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#menubar-demo [data-slot=menubar-content]:popover-open')")
    assert active(page) == "Edit"
    file.focus()
    page.keyboard.press(key(t, "ArrowRight"))
    assert active(page) == "Edit"
    page.keyboard.press("End")
    assert active(page) == "Profiles"
    page.keyboard.press(key(t, "ArrowRight"))
    assert active(page) == "File"
    page.keyboard.press(key(t, "ArrowRight"))
    page.keyboard.press("ArrowDown")
    wait(page, "() => document.querySelectorAll('#menubar-demo [data-slot=menubar-content]')[1].matches(':popover-open')")
    assert active(page) == "Undo⌘Z"
    page.keyboard.press(key(t, "ArrowRight"))
    wait(page, "() => document.querySelectorAll('#menubar-demo [data-slot=menubar-content]')[2].matches(':popover-open')")
    assert active(page, "e => e.getAttribute('aria-labelledby')") == view.get_attribute("id")
    assert section.locator("[data-slot=menubar-content]").nth(1).get_attribute("data-closed") == ""
    wait(page, "() => !document.querySelectorAll('#menubar-demo [data-slot=menubar-content]')[1].matches(':popover-open')")
    page.keyboard.press(key(t, "ArrowLeft"))
    wait(page, "() => document.querySelectorAll('#menubar-demo [data-slot=menubar-content]')[1].matches(':popover-open')")
    assert active(page, "e => e.getAttribute('aria-labelledby')") == edit.get_attribute("id")
    page.keyboard.press("ArrowDown")
    assert active(page) == "Undo⌘Z"
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    assert active(page) == "Find"
    page.keyboard.press(key(t, "ArrowRight"))
    assert active(page) == "Search the web"
    t.settle()
    t.shot("menubar-submenu", page)
    page.keyboard.press(key(t, "ArrowLeft"))
    assert active(page) == "Find"
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    wait(page, "() => !document.querySelector('#menubar-demo [data-slot=menubar-content]:popover-open')")
    assert active(page) == "Edit"
    view.click()
    page.get_by_role("menuitemcheckbox", name="Bookmarks Bar").click()
    assert section.locator("[data-slot=menubar-checkbox-item]").nth(0).get_attribute("aria-checked") == "true"
    assert is_open(section.locator("[data-slot=menubar-content]").nth(2)), "checkbox items keep the menu open, as in Base UI"
    inset = section.locator("[data-slot=menubar-item][data-inset]").first
    assert inset.evaluate("e => getComputedStyle(e).paddingInlineStart") == "28px"
    profiles.hover()
    wait(page, "() => document.querySelectorAll('#menubar-demo [data-slot=menubar-content]')[3].matches(':popover-open')")
    page.get_by_role("menuitemradio", name="Luis").click()
    radios = section.locator("[data-slot=menubar-radio-item]")
    assert radios.nth(2).get_attribute("aria-checked") == "true"
    assert radios.nth(1).get_attribute("aria-checked") == "false"
    selects = [e[1]["value"] for e in events(page, "menubar:select")]
    assert selects == ["Cut", "Bookmarks Bar", "luis"], selects
    wait(page, "() => document.querySelectorAll('#menubar-demo [data-slot=menubar-content]')[3].matches(':popover-open')")
    t.settle()
    t.shot("menubar-radio", page)
    profiles.click()
    wait(page, "() => !document.querySelector('#menubar-demo [data-slot=menubar-content]:popover-open')")


def check_navigation_menu(t):
    page = t.page
    section = t.section("navigation-menu")
    listen(page, "navigation-menu:change", "navigation-menu:select")
    nav = section.locator("#navigation-menu-demo")
    first = nav.get_by_role("button", name="Getting started")
    icon = nav.get_by_role("button", name="With Icon")
    first_content = nav.locator("#" + first.get_attribute("aria-controls"))
    icon_content = nav.locator("#" + icon.get_attribute("aria-controls"))
    viewport_el = nav.locator("[data-slot=navigation-menu-viewport]")
    assert first.get_attribute("aria-expanded") == "false"
    assert first.get_attribute("aria-controls") == first_content.get_attribute("id")
    assert nav.get_by_role("link", name="Docs").get_attribute("aria-current") == "page"
    page.evaluate(
        """() => {
          const nav = document.getElementById("navigation-menu-demo")
          const indicator = document.createElement("div")
          indicator.dataset.slot = "navigation-menu-indicator"
          nav.querySelector("[data-slot=navigation-menu-list]").after(indicator)
          window.__navTimes = {}
          nav.querySelector("[data-slot=navigation-menu-trigger]").addEventListener("pointerover", () => (window.__navTimes.over ??= performance.now()))
          nav.addEventListener("navigation-menu:change", () => (window.__navTimes.open ??= performance.now()))
        }"""
    )
    first.hover()
    wait(page, "() => document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-trigger]').getAttribute('aria-expanded') === 'true'")
    times = page.evaluate("() => window.__navTimes")
    assert 40 <= times["open"] - times["over"] <= 250, times
    assert first_content.is_visible() and viewport_el.is_visible()
    wait(page, "() => !document.querySelector('#navigation-menu-demo [data-starting-style]')")
    t.settle()
    vb, cb, fb = inline(t, box(viewport_el)), inline(t, box(first_content)), inline(t, box(first))
    assert abs(vb["width"] - cb["width"]) <= 1 and abs(vb["height"] - cb["height"]) <= 1, (vb, cb)
    assert abs(vb["x"] - cb["x"]) <= 1.5 and abs(vb["y"] - cb["y"]) <= 1.5, (vb, cb)
    assert abs(vb["x"] - fb["x"]) <= 1 and abs(vb["y"] - fb["y"] - fb["height"] - 8) <= 1, (fb, vb)
    assert nav.locator("[data-slot=navigation-menu-indicator]").get_attribute("data-state") == "visible"
    t.shot("navigation-menu-open", page)
    icon.hover()
    wait(page, "e => e.dataset.state === 'open'", icon_content.element_handle())
    assert icon_content.get_attribute("data-activation-direction") == "right" and first_content.get_attribute("data-activation-direction") in ("right", None if t.reduced_motion else "right")
    assert first_content.get_attribute("data-closed") == "" and icon_content.get_attribute("data-open") == ""
    t.settle()
    assert first_content.is_hidden()
    t.shot("navigation-menu-switch", page)
    ib = box(icon_content)
    page.mouse.move(ib["x"] + 20, ib["y"] + 20)
    page.wait_for_timeout(250)
    assert icon.get_attribute("aria-expanded") == "true"
    away(page)
    wait(page, "e => e.dataset.state === 'closed'", icon_content.element_handle())
    t.settle()
    assert viewport_el.is_hidden()
    page.wait_for_timeout(350)
    first.focus()
    page.keyboard.press("Enter")
    assert first.get_attribute("aria-expanded") == "true"
    assert active(page) == "IntroductionRe-usable components built with plain HTML and CSS."
    page.keyboard.press("ArrowDown")
    assert active(page).startswith("Installation")
    page.keyboard.press("Escape")
    assert active(page) == "Getting started"
    assert first.get_attribute("aria-expanded") == "false"
    page.keyboard.press("Space")
    assert active(page).startswith("Introduction")
    page.keyboard.press("Shift+Tab")
    assert active(page) == "Getting started"
    page.keyboard.press("Tab")
    assert active(page).startswith("Introduction")
    page.keyboard.press("Shift+Tab")
    page.keyboard.press(key(t, "ArrowRight"))
    if t.width >= 768:
        assert active(page) == "Components"
        page.keyboard.press(key(t, "ArrowRight"))
    assert active(page) == "With Icon"
    page.keyboard.press("End")
    assert active(page) == "With Icon"
    page.keyboard.press(key(t, "ArrowRight"))
    assert active(page) == "Docs"
    assert first.get_attribute("aria-expanded") == "true"
    away(page)
    page.mouse.down()
    page.mouse.up()
    assert first.get_attribute("aria-expanded") == "false"
    first.evaluate("e => e.scrollIntoView({ block: 'center', behavior: 'instant' })")
    first.click()
    nav.get_by_role("link", name="Typography").click()
    assert first.get_attribute("aria-expanded") == "true", "links keep the menu open (Base UI closeOnClick is false)"
    page.keyboard.press("Escape")
    assert first.get_attribute("aria-expanded") == "false"
    values = [e[1]["value"] for e in events(page, "navigation-menu:change")]
    assert values == ["getting-started", "status", "", "getting-started", "", "getting-started", "", "getting-started", ""], values
    assert len(events(page, "navigation-menu:select")) == 1
    plain = section.locator("#navigation-menu-plain")
    products = plain.get_by_role("button", name="Products")
    products.evaluate("e => e.scrollIntoView({ block: 'center', behavior: 'instant' })")
    products.click()
    panel = plain.locator("[data-slot=navigation-menu-content]").first
    t.settle()
    pb, tb = inline(t, box(products)), inline(t, box(panel))
    if panel.get_attribute("data-side") == "top":
        assert abs(pb["y"] - tb["y"] - tb["height"] - 8) <= 1 and abs(tb["x"] - pb["x"]) <= 1, ("flipped above the trigger, 8 px", pb, tb)
    else:
        assert abs(tb["y"] - pb["y"] - pb["height"] - 8) <= 1 and abs(tb["x"] - pb["x"]) <= 1, (pb, tb)
    assert "0px 0px 0px 1px" in panel.evaluate("e => getComputedStyle(e).boxShadow")
    t.shot("navigation-menu-plain", page)
    page.keyboard.press("Escape")
    wait(page, "e => e.getAttribute('aria-expanded') === 'false'", products.element_handle())
    products.click()
    wait(page, "e => e.getAttribute('aria-expanded') === 'true'", products.element_handle())
    products.click()
    wait(page, "e => e.getAttribute('aria-expanded') === 'false'", products.element_handle())


def check_navigation_menu_active(t):
    page = t.page
    nav = t.section("navigation-menu").locator("#navigation-menu-demo")
    docs = nav.get_by_role("link", name="Docs")
    intro = nav.locator("[data-slot=navigation-menu-link]").first
    assert docs.get_attribute("aria-current") == "page" and intro.get_attribute("aria-current") is None
    page.evaluate(
        """() => {
          const links = document.querySelectorAll("#navigation-menu-demo [data-slot=navigation-menu-link]")
          links[links.length - 1].removeAttribute("data-active")
          links[0].setAttribute("data-active", "")
        }"""
    )
    wait(page, "() => { const links = document.querySelectorAll('#navigation-menu-demo [data-slot=navigation-menu-link]'); return !links[links.length - 1].hasAttribute('aria-current') && links[0].getAttribute('aria-current') === 'page' }")
    page.evaluate("() => { document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-link]').dataset.active = 'false' }")
    wait(page, "() => !document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-link]').hasAttribute('aria-current')")
    added = page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const link = h("a", { "data-slot": "navigation-menu-link", "data-variant": "trigger", href: "#navigation-menu", "data-active": "" }, "Blog")
          document.querySelector("#navigation-menu-demo [data-slot=navigation-menu-list]").append(h("li", { "data-slot": "navigation-menu-item" }, link))
          await new Promise(r => setTimeout(r, 0))
          return link.getAttribute("aria-current")
        }"""
    )
    assert added == "page"


def check_command(t):
    page = t.page
    section = t.section("command")
    listen(page, "command:select")
    cmd = section.locator("#command-demo")
    box_input = cmd.get_by_role("combobox")
    listbox = cmd.get_by_role("listbox")
    assert box_input.get_attribute("aria-expanded") == "true"
    assert box_input.get_attribute("aria-controls") == listbox.get_attribute("id")
    selected = lambda: cmd.locator("[data-slot=command-item][data-selected=true]").inner_text()
    assert selected() == "Calendar"
    assert box_input.get_attribute("aria-activedescendant") == cmd.get_by_role("option", name="Calendar").get_attribute("id")
    box_input.click()
    page.keyboard.press("ArrowDown")
    assert selected() == "Search Emoji"
    page.keyboard.press("ArrowDown")
    assert selected().startswith("Profile")
    page.keyboard.press("ArrowUp")
    assert selected() == "Search Emoji"
    page.keyboard.press("End")
    assert selected().startswith("Settings")
    page.keyboard.press("ArrowDown")
    assert selected().startswith("Settings")
    page.keyboard.press("Home")
    assert selected() == "Calendar"
    page.keyboard.press("Enter")
    page.keyboard.type("bil")
    assert cmd.locator("[data-slot=command-item]:not([hidden])").count() == 1
    assert selected().startswith("Billing")
    assert cmd.locator("[data-slot=command-group][data-heading=Suggestions]").is_hidden()
    assert cmd.locator("[data-slot=command-group]").first.get_attribute("data-heading") == "Settings"
    assert cmd.locator("[data-slot=command-separator]").is_hidden()
    assert cmd.locator("[data-slot=command-empty]").is_hidden()
    t.shot("command-filtered")
    page.keyboard.press("Enter")
    box_input.fill("smiley")
    assert selected() == "Search Emoji"
    box_input.fill("set")
    order = cmd.locator("[data-slot=command-item]:not([hidden])").evaluate_all("els => els.map(e => e.textContent.trim())")
    assert order[0].startswith("Settings"), order
    box_input.fill("zzz")
    assert cmd.locator("[data-slot=command-empty]").is_visible()
    assert box_input.get_attribute("aria-activedescendant") is None
    t.shot("command-empty")
    box_input.fill("")
    order = cmd.locator("[data-slot=command-item]").evaluate_all("els => els.map(e => e.textContent.trim().slice(0, 4))")
    assert order == ["Cale", "Sear", "Calc", "Prof", "Bill", "Sett"], order
    cmd.get_by_role("option", name="Profile").hover()
    assert selected().startswith("Profile")
    cmd.get_by_role("option", name="Calculator").click(force=True)
    assert selected().startswith("Profile")
    cmd.get_by_role("option", name="Billing").click()
    values = [e[1]["value"] for e in events(page, "command:select")]
    assert values == ["Calendar", "Billing⌘B", "Billing⌘B"], values
    page.keyboard.press("Meta+k")
    dialog = page.locator("#command-dialog dialog")
    wait(page, "() => document.querySelector('#command-dialog dialog').open")
    assert active(page, "e => e.dataset.slot") == "command-input"
    assert page.get_by_role("dialog", name="Command Palette").is_visible()
    t.settle()
    t.shot("command-dialog", page)
    page.keyboard.type("bil")
    page.keyboard.press("Enter")
    wait(page, "() => !document.querySelector('#command-dialog dialog').open")
    page.wait_for_selector("[data-slot=toast] >> text=Selected Billing")
    section.get_by_role("button", name="Open Menu").click()
    wait(page, "() => document.querySelector('#command-dialog dialog').open")
    assert dialog.locator("[data-slot=command-input]").input_value() == ""
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#command-dialog dialog').open")
    assert active(page) == "Open Menu"
    scroll = section.locator("[data-slot=command]").nth(2)
    scroll.get_by_role("combobox").click()
    page.keyboard.press("End")
    assert scroll.locator("[data-slot=command-list]").evaluate("l => l.scrollTop > 0")


def toasts_gone(page, timeout=3000):
    wait(page, "() => !document.querySelector('[data-slot=toast]')", timeout=timeout)


def toast_api(page):
    page.evaluate("async () => { const { toast } = await import('/clanker-ui.js'); window.__toast = toast }")


def check_sonner(t):
    page = t.page
    section = t.section("sonner")
    listen(page, "toast:open", "toast:close", "toast:action")
    region = page.locator("[data-slot=toast-portal] > [data-slot=toast-viewport]")
    assert region.count() == 1
    attrs = region.evaluate("e => ['role', 'aria-live', 'aria-atomic', 'aria-relevant', 'aria-label', 'tabindex'].map(n => e.getAttribute(n))")
    assert attrs == ["region", "polite", "false", "additions text", "Notifications", "-1"], attrs
    section.get_by_role("button", name="Show Toast").first.click()
    toast = page.locator("[data-slot=toast]").filter(has_text="Event has been created")
    toast.wait_for()
    assert toast.evaluate("e => [e.getAttribute('role'), e.getAttribute('tabindex'), e.getAttribute('aria-modal'), e.hasAttribute('data-type')]") == ["dialog", "0", "false", False]
    title = toast.locator("h2[data-slot=toast-title]")
    description = toast.locator("p[data-slot=toast-description]")
    assert title.inner_text() == "Event has been created"
    assert description.inner_text() == "Sunday, December 03, 2023 at 9:00 AM"
    assert toast.evaluate("e => [e.getAttribute('aria-labelledby'), e.getAttribute('aria-describedby')]") == [title.get_attribute("id"), description.get_attribute("id")]
    parts = toast.locator("[data-slot=toast-content]").evaluate("e => [...e.children].map(c => c.dataset.slot || c.localName)")
    assert parts == ["div", "toast-action", "toast-close"], parts
    assert toast.evaluate("e => [e, e.firstElementChild].every(n => [...n.childNodes].every(c => c.nodeType === 1))")
    assert "null" not in toast.text_content() and "undefined" not in toast.text_content()
    page.wait_for_timeout(600)
    cw, height = viewport(page)
    tb = inline(t, box(toast))
    assert abs(tb["x"] + tb["width"] - (cw - 16)) <= 1 and abs(tb["y"] + tb["height"] - (height - 16)) <= 1, tb
    if cw < 640:
        assert abs(tb["x"] - 16) <= 1, tb
    else:
        assert abs(tb["width"] - 384) <= 1, tb
    t.shot("sonner-toast", page)
    toast.get_by_role("button", name="Undo").click()
    page.locator("[data-slot=toast]").filter(has_text="Event restored").wait_for()
    wait(page, "() => ![...document.querySelectorAll('[data-slot=toast]')].some(e => e.textContent.includes('Sunday'))")
    page.evaluate("async () => (await import('/clanker-ui.js')).toast.dismiss()")
    toasts_gone(page)
    icons = {"Success": "circle-check", "Info": "info", "Warning": "triangle-alert", "Error": "octagon-x"}
    for name, lucide in icons.items():
        section.get_by_role("button", name=name, exact=True).click()
        item = page.locator(f"[data-slot=toast][data-type={name.lower()}]")
        item.wait_for()
        assert item.locator(f"[data-slot=toast-content] > span[data-slot=toast-icon] > svg[data-lucide={lucide}]").count() == 1
    section.get_by_role("button", name="Default", exact=True).click()
    plain = page.locator("[data-slot=toast]:not([data-type])")
    plain.wait_for()
    assert plain.locator("[data-slot=toast-icon]").count() == 0
    page.mouse.move(3, 3)
    page.wait_for_timeout(600)
    t.shot("sonner-types", page)
    page.evaluate("async () => (await import('/clanker-ui.js')).toast.dismiss()")
    toasts_gone(page)
    section.get_by_role("button", name="Promise").click()
    page.locator("[data-slot=toast][data-type=loading]").filter(has_text="Loading...").wait_for()
    page.locator("[data-slot=toast][data-type=success]").filter(has_text="Event has been created").wait_for(timeout=4000)
    assert page.locator("[data-slot=toast]").count() == 1
    page.evaluate("async () => (await import('/clanker-ui.js')).toast.dismiss()")
    toasts_gone(page)
    closes = [e[1]["reason"] for e in events(page, "toast:close")]
    assert closes[0] == "action", closes
    assert len(events(page, "toast:action")) == 1


def check_toast_types(t):
    page = t.page
    section = t.section("toast")
    for name in ["Default", "Success", "Info", "Warning", "Error"]:
        section.get_by_role("button", name=name, exact=True).click()
    page.wait_for_function("() => document.querySelectorAll('[data-slot=toast]').length === 5")
    page.mouse.move(3, 3)
    page.wait_for_timeout(600)
    found = page.evaluate(
        """() => {
          const probe = value => { const p = document.createElement("span"); p.style.color = value; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c }
          const out = {}
          for (const e of document.querySelectorAll('[data-slot="toast"]')) {
            const type = e.dataset.type ?? "default"
            const svg = e.querySelector('[data-slot="toast-icon"] > svg')
            out[type] = {
              title: !!e.querySelector('[data-slot="toast-title"]'),
              typed: [...e.querySelectorAll('[data-slot="toast-description"], [data-slot="toast-close"]')].every(p => p.dataset.type === e.dataset.type),
              role: e.getAttribute("role"),
              hidden: e.getAttribute("aria-hidden"),
              icon: svg ? [getComputedStyle(svg).width, getComputedStyle(svg).color === probe("var(--destructive)")] : null,
              limited: e.hasAttribute("data-limited") && e.inert,
            }
          }
          const alerts = [...document.querySelectorAll('[data-slot="toast-portal"] > .sr-only [role="alert"]')].map(a => a.textContent)
          return { out, alerts }
        }"""
    )
    out = found["out"]
    assert out["error"] == {"title": False, "typed": True, "role": "alertdialog", "hidden": "true", "icon": ["16px", True], "limited": False}, out["error"]
    assert out["warning"]["icon"] == ["16px", False] and out["warning"]["role"] == "dialog" and out["warning"]["hidden"] is None, out["warning"]
    assert out["default"]["icon"] is None and out["default"]["limited"] and out["success"]["limited"], out
    assert not out["info"]["limited"] and not out["warning"]["limited"], out
    assert found["alerts"] == ["The event could not be created."], found["alerts"]
    node = page.evaluate("""async () => {
      const { toast, h } = await import("/clanker-ui.js")
      const id = toast.add({ title: h("strong", null, "Node title"), description: "Urgent", priority: "high", timeout: 0 })
      const el = [...document.querySelectorAll('[data-slot="toast"]')].find(e => e.textContent.includes("Urgent"))
      const out = [el.querySelector('[data-slot="toast-title"] > strong')?.textContent, [...document.querySelectorAll('[data-slot="toast-portal"] > .sr-only [role="alert"]')].map(a => a.textContent)]
      toast.close(id)
      return out
    }""")
    assert node[0] == "Node title" and "Node titleUrgent" in node[1], ("a node title stays in the toast heading", node)
    t.shot("toast-types", page)
    page.evaluate("async () => (await import('/clanker-ui.js')).toast.close()")
    toasts_gone(page)
    section.get_by_role("button", name="Create Event").click()
    loading = page.locator("[data-slot=toast][data-type=loading]")
    loading.wait_for()
    assert loading.locator("[data-slot=toast-title]").count() == 0 and loading.locator("[data-slot=toast-description]").inner_text() == "Creating event…"
    assert (loading.locator("[data-slot=toast-icon] > svg").evaluate("e => getComputedStyle(e).animationName") != "none") != t.reduced_motion
    page.locator("[data-slot=toast][data-type=success]").filter(has_text="Event created.").wait_for(timeout=4000)
    section.get_by_role("button", name="Show Toast").click()
    demo = page.locator("[data-slot=toast]").filter(has_text="Event created").filter(has=page.locator("[data-slot=toast-title]"))
    demo.wait_for()
    demo.get_by_role("button", name="Undo").click()
    wait(page, "() => ![...document.querySelectorAll('[data-slot=toast]:not([data-ending-style])')].some(e => e.querySelector('[data-slot=toast-title]'))")
    page.evaluate("async () => (await import('/clanker-ui.js')).toast.close()")
    toasts_gone(page)


def check_toast(t):
    page = t.page
    section = t.section("toast")
    listen(page, "toast:open", "toast:close", "toast:action")
    toast_api(page)
    page.evaluate("() => window.__toast.add({ id: 'short', description: 'Short lived', timeout: 1500 })")
    item = page.locator("[data-slot=toast]").filter(has_text="Short lived")
    item.wait_for()
    page.wait_for_timeout(450)
    item.hover()
    page.wait_for_timeout(1800)
    assert item.count() == 1 and not item.evaluate("e => e.hasAttribute('data-ending-style')"), "hover must pause the timer"
    away(page)
    toasts_gone(page, 3500)
    page.evaluate("() => window.__toast.add({ id: 'again', description: 'Hover twice', timeout: 4000 })")
    again = page.locator("[data-slot=toast]").filter(has_text="Hover twice")
    again.wait_for()
    page.wait_for_timeout(2000)
    for _ in range(2):
        again.hover()
        away(page)
        page.wait_for_timeout(500)
    page.wait_for_timeout(2000)
    assert page.evaluate("() => !!document.querySelector('[data-slot=toast]:not([data-ending-style])')"), "Base UI 1.6.0 counts the time left from the full timeout after a resume"
    toasts_gone(page, 4000)
    page.evaluate("() => window.__toast.loading('Uploading', { id: 'up', duration: 300 })")
    loading = page.locator("[data-slot=toast][data-type=loading]")
    loading.wait_for()
    page.wait_for_timeout(700)
    assert loading.count() == 1, "a loading toast never closes on a timer"
    assert loading.locator("[data-slot=toast-close]").count() == 1, "Base UI renders the close button on every toast"
    page.evaluate("() => window.__toast.success('Uploaded', { id: 'up' })")
    done = page.locator("[data-slot=toast][data-type=success]").filter(has_text="Uploaded")
    done.wait_for()
    assert page.locator("[data-slot=toast]").count() == 1, page.locator("[data-slot=toast]").all_inner_texts()
    page.evaluate("() => window.__toast.dismiss('up')")
    toasts_gone(page)
    section.get_by_role("button", name="Show four toasts").click()
    away(page)
    page.wait_for_function("() => document.querySelectorAll('[data-slot=toast]').length === 4")
    page.wait_for_timeout(600)
    states = page.locator("[data-slot=toast]").evaluate_all("els => els.map(e => [e.style.getPropertyValue('--toast-index'), e.hasAttribute('data-limited'), e.inert, e.hasAttribute('data-expanded'), e.firstElementChild.hasAttribute('data-behind')])")
    assert states == [["0", False, False, False, False], ["1", False, False, False, True], ["2", False, False, False, True], ["3", True, True, False, True]], states
    texts = page.locator("[data-slot=toast] [data-slot=toast-title]").all_inner_texts()
    assert texts == ["Fourth notification", "Third notification", "Second notification", "First notification"], texts
    collapsed = page.locator("[data-slot=toast]").evaluate_all("els => els.slice(0, 3).map(e => { const r = e.getBoundingClientRect(); return [r.top, r.bottom, r.height] })")
    assert collapsed[0][0] > collapsed[1][0] > collapsed[2][0], collapsed
    assert abs(collapsed[1][2] - collapsed[0][2] * 0.9) <= 1.5 and abs(collapsed[0][0] - collapsed[1][0] - 12) <= 1.5, collapsed
    t.shot("toast-stack", page)
    page.locator("[data-slot=toast]").first.hover()
    wait(page, "() => document.querySelector('[data-slot=toast-viewport]').hasAttribute('data-expanded') && [...document.querySelectorAll('[data-slot=toast], [data-slot=toast-content]')].every(e => e.hasAttribute('data-expanded'))")
    page.wait_for_timeout(600)
    tops = page.locator("[data-slot=toast]").evaluate_all("els => els.slice(0, 3).map(e => { const r = e.getBoundingClientRect(); return [r.top, r.bottom] })")
    assert abs(tops[0][0] - tops[1][1] - 12) <= 1.5 and abs(tops[1][0] - tops[2][1] - 12) <= 1.5, tops
    assert page.locator("[data-slot=toast-close]").evaluate_all("els => els.slice(0, 3).map(e => e.getAttribute('aria-hidden'))") == ["false", "false", "false"]
    t.shot("toast-expanded", page)
    front = page.locator("[data-slot=toast]").first.element_handle()
    fb = front.bounding_box()
    x, y = fb["x"] + fb["width"] / 2, fb["y"] + fb["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 20, y, steps=3)
    assert front.evaluate("e => e.hasAttribute('data-swiping') && e.dataset.swipeDirection === 'right' && e.style.getPropertyValue('--toast-swipe-movement-x') !== '0px'")
    page.mouse.move(x + 80, y, steps=3)
    page.mouse.up()
    wait(page, "() => document.querySelectorAll('[data-slot=toast]:not([data-ending-style])').length === 3")
    assert front.evaluate("e => !e.isConnected || e.dataset.swipeDirection === 'right'")
    page.wait_for_timeout(700)
    second = page.locator("[data-slot=toast]:not([data-ending-style])").first.element_handle()
    sb = second.bounding_box()
    x, y = sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x - 30, y, steps=3)
    page.mouse.move(x - 100, y, steps=3)
    damped = second.evaluate("e => parseFloat(e.style.getPropertyValue('--toast-swipe-movement-x'))")
    assert -12 < damped < 0, damped
    page.mouse.up()
    page.wait_for_timeout(300)
    assert second.evaluate("e => e.isConnected && !e.hasAttribute('data-ending-style') && !e.hasAttribute('data-swiping')"), "a swipe toward a side that does not dismiss springs back"
    page.evaluate("() => window.__toast.dismiss()")
    toasts_gone(page)
    away(page)
    page.evaluate("() => { window.__acted = 0; window.__toast('Keep me', { id: 'keep', timeout: 0, action: { label: 'Stay', onClick: e => { window.__acted++; e.preventDefault() } } }) }")
    keep = page.locator("[data-slot=toast]").filter(has_text="Keep me")
    keep.wait_for()
    page.wait_for_timeout(450)
    assert keep.locator("[data-slot=toast-close]").get_attribute("aria-hidden") == "true"
    keep.get_by_role("button", name="Stay").click()
    page.wait_for_timeout(300)
    assert page.evaluate("window.__acted") == 1 and not keep.evaluate("e => e.hasAttribute('data-ending-style')"), "a prevented action keeps the toast"
    page.evaluate("() => { window.__undone = 0; window.__toast.add({ id: 'base', title: 'Base UI action', timeout: 0, actionProps: { children: 'Undo', onClick: () => window.__undone++ } }) }")
    base = page.locator("[data-slot=toast]").filter(has_text="Base UI action")
    base.wait_for()
    base.get_by_role("button", name="Undo").click()
    page.wait_for_timeout(300)
    assert page.evaluate("window.__undone") == 1 and not base.evaluate("e => e.hasAttribute('data-ending-style')"), "actionProps do not close the toast"
    section.get_by_role("button", name="Persistent").focus()
    page.keyboard.press("F6")
    wait(page, "() => document.activeElement && document.activeElement.dataset.slot === 'toast-viewport'")
    assert page.locator("[data-slot=toast-viewport]").evaluate("e => e.hasAttribute('data-expanded')")
    page.keyboard.press("Tab")
    assert active(page, "e => e.dataset.slot + ':' + e.textContent") == "toast:Base UI actionUndo", active(page, "e => e.dataset.slot + ':' + e.textContent")
    page.keyboard.press("Escape")
    wait(page, "() => document.activeElement && document.activeElement.textContent === 'Keep meStay'")
    page.wait_for_function("() => document.querySelectorAll('[data-slot=toast]').length === 1")
    page.keyboard.press("Shift+Tab")
    assert active(page) == "Persistent", active(page)
    away(page)
    page.locator("[data-slot=toast]").filter(has_text="Keep me").first.hover()
    page.locator("[data-slot=toast]").filter(has_text="Keep me").get_by_role("button", name="Close toast").click()
    toasts_gone(page)
    reasons = [e[1]["reason"] for e in events(page, "toast:close")]
    assert reasons == ["timeout", "timeout", "dismiss", "swipe", "dismiss", "dismiss", "dismiss", "escape", "close"], reasons
    assert len(events(page, "toast:action")) == 2


def check_menubar_icons(t):
    page = t.page
    t.section("menubar")
    bar = page.locator("#menubar-icons")
    assert bar.get_attribute("role") == "menubar"
    bar.get_by_role("menuitem", name="More", exact=True).click()
    menu = bar.locator("[data-slot=menubar-content]").nth(1)
    wait(page, "() => document.querySelectorAll('#menubar-icons [data-slot=menubar-content]')[1].matches(':popover-open')")
    assert menu.locator("svg[data-lucide=keyboard]").count() == 1
    page.keyboard.press(key(t, "ArrowLeft"))
    wait(page, "() => document.querySelectorAll('#menubar-icons [data-slot=menubar-content]')[0].matches(':popover-open')")
    assert bar.locator("[data-slot=menubar-content]").first.locator("svg[data-lucide=save]").count() == 1
    t.shot("menubar-icons", page)
    page.keyboard.press("Escape")


def check_menu_item_opens_dialog(t):
    page = t.page
    page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const menu = h("div", { "data-slot": "dropdown-menu" },
            h("button", { type: "button", "data-dropdown-menu-trigger": "", id: "md-trigger" }, "Actions"),
            h("div", { "data-slot": "dropdown-menu-content" },
              h("div", { "data-slot": "dropdown-menu-item", "data-dialog-trigger": "md-dialog", id: "md-item" }, "Delete"),
              ["New Tab", "New Window"].map(v => h("div", { "data-slot": "dropdown-menu-item" }, v))))
          const dialog = h("div", { "data-slot": "dialog", id: "md-dialog" },
            h("dialog", { "data-slot": "dialog-content" }, h("h2", { "data-slot": "dialog-title" }, "Confirm"), h("button", { type: "button", "data-dialog-close": "" }, "Cancel")))
          menu.addEventListener("dropdown-menu:select", e => (window.__mdSelect ??= []).push(e.detail.value))
          document.body.prepend(menu, dialog)
          await new Promise(r => setTimeout(r, 0))
        }"""
    )
    trigger = page.locator("#md-trigger")
    content = page.locator("#md-dialog dialog")
    for how in ("keyboard", "mouse"):
        if how == "keyboard":
            trigger.focus()
            page.keyboard.press("Enter")
            wait(page, "() => document.activeElement.id === 'md-item'")
            page.keyboard.press("Enter")
        else:
            trigger.click()
            page.locator("#md-item").click()
        wait(page, "() => document.querySelector('#md-dialog dialog').open")
        page.keyboard.press("Escape")
        wait(page, "() => !document.querySelector('#md-dialog dialog').open")
        assert page.evaluate("document.activeElement.id") == "md-trigger", (how, page.evaluate("document.activeElement.tagName"))
    assert content.get_attribute("data-state") == "closed"
    trigger.focus()
    page.keyboard.press("ArrowDown")
    wait(page, "() => document.activeElement.id === 'md-item'")
    page.keyboard.type("new w", delay=40)
    assert active(page) == "New Window"
    assert page.evaluate("window.__mdSelect ?? []") == ["Delete", "Delete"]
    page.keyboard.press("Escape")


def check_toast_in_modal(t):
    page = t.page
    t.section("dialog")
    listen(page, "dialog:close", "toast:action")
    page.locator("#dialog-demo [data-dialog-trigger]").click()
    content = page.locator("#dialog-demo dialog")
    wait(page, "() => document.querySelector('#dialog-demo dialog').open")
    t.settle()
    height = content.evaluate("e => e.getBoundingClientRect().height")
    page.evaluate("async () => { const { toast } = await import('/clanker-ui.js'); window.__acted = 0; toast('Saved', { id: 'modal', duration: Infinity, action: { label: 'Undo', onClick: () => window.__acted++ } }) }")
    action = page.locator("[data-slot=toast-action]")
    action.wait_for()
    page.wait_for_timeout(600)
    assert content.evaluate("e => e.getBoundingClientRect().height") == height, "the toaster must not change the dialog layout"
    assert page.evaluate("document.querySelector('[data-slot=toast-portal]').parentElement === document.querySelector('#dialog-demo dialog')")
    ab = box(action)
    hit = page.evaluate("([x, y]) => document.elementFromPoint(x, y)?.dataset.slot", [ab["x"] + ab["width"] / 2, ab["y"] + ab["height"] / 2])
    assert hit == "toast-action", hit
    t.shot("toast-in-modal", page)
    action.click()
    toasts_gone(page)
    assert page.evaluate("window.__acted") == 1
    assert content.evaluate("e => e.open"), "a click in a toast must not dismiss the modal"
    assert events(page, "dialog:close") == [] and len(events(page, "toast:action")) == 1
    page.evaluate("async () => (await import('/clanker-ui.js')).toast('Still here', { id: 'after', duration: Infinity })")
    still = page.locator("[data-slot=toast]").filter(has_text="Still here")
    still.wait_for()
    still.focus()
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('[data-slot=toast]')")
    assert content.evaluate("e => e.open"), "Escape in a toast closes the toast, not the modal"
    page.evaluate("async () => (await import('/clanker-ui.js')).toast('Still here', { id: 'after', duration: Infinity })")
    still.wait_for()
    content.locator("input, button").first.focus()
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#dialog-demo dialog').open")
    assert page.evaluate("document.querySelector('[data-slot=toast-portal]').parentElement === document.body")
    assert page.evaluate("document.querySelector('[data-slot=toast-viewport]').matches(':popover-open')")
    assert still.is_visible()
    page.evaluate("async () => (await import('/clanker-ui.js')).toast.dismiss()")


def check_toast_timers(t):
    page = t.page
    page.evaluate("async () => { window.__ui = await import('/clanker-ui.js') }")
    for target in ("[data-slot=toast-action]", "[data-slot=toast-title]"):
        page.evaluate("() => window.__ui.toast('Press me', { id: 'press', duration: 1200, action: { label: 'Undo', onClick() {} } })")
        part = page.locator(target)
        part.wait_for()
        page.wait_for_timeout(450)
        pb = box(part)
        page.mouse.move(pb["x"] + 5, pb["y"] + 5)
        page.mouse.down()
        page.mouse.move(pb["x"] + 5, pb["y"] - 60, steps=6)
        page.mouse.move(300, 200, steps=6)
        page.mouse.up()
        wait(page, "() => !document.querySelector('[data-slot=toast]')", timeout=4000)
    page.evaluate("() => window.__ui.toast('Hidden page', { id: 'hidden', duration: 600 })")
    page.locator("[data-slot=toast]").wait_for()
    page.evaluate("() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange')) }")
    page.wait_for_timeout(1500)
    gone = page.locator("[data-slot=toast]").count() == 0
    page.evaluate("() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')) }")
    assert gone, "a hidden page does not pause the timers, as Base UI 1.6.0"
    page.evaluate("() => window.__ui.toast('Window blur', { id: 'blur', duration: 600 })")
    page.locator("[data-slot=toast]").wait_for()
    page.evaluate("() => window.dispatchEvent(new FocusEvent('blur'))")
    page.wait_for_timeout(1000)
    assert page.locator("[data-slot=toast]").count() == 1, "a window blur pauses the timers"
    page.evaluate("() => window.dispatchEvent(new FocusEvent('focus'))")
    wait(page, "() => !document.querySelector('[data-slot=toast]')", timeout=3000)


def check_toast_options(t):
    page = t.page
    result = page.evaluate(
        """async () => {
          const { toast } = await import("/clanker-ui.js")
          const thrown = []
          for (const options of [{ icon: "no-such-icon" }]) {
            try { toast("bad", options); thrown.push(false) } catch (e) { thrown.push(e.message) }
          }
          const records = toast.getToasts().length
          let hides = 0
          const original = HTMLElement.prototype.hidePopover
          HTMLElement.prototype.hidePopover = function () { if (this.dataset.slot === "toast-viewport") hides++; return original.call(this) }
          for (const n of [1, 2, 3]) toast(`Toast ${n}`, { duration: Infinity })
          HTMLElement.prototype.hidePopover = original
          const viewport = document.querySelector('[data-slot="toast-viewport"]')
          const id = toast.add({ title: "Draft", description: "One", timeout: 0 })
          const el = [...document.querySelectorAll('[data-slot="toast"]')].find(e => e.textContent.includes("Draft"))
          toast.update(id, { description: "Two" })
          toast.update(id, prev => ({ title: `${prev.title}!` }))
          const updated = [el.isConnected, el.querySelector('[data-slot="toast-title"]').textContent, el.querySelector('[data-slot="toast-description"]').textContent]
          toast.add({ id, title: "Again" })
          const upserted = [document.querySelectorAll('[data-slot="toast"]').length, el.isConnected, el.querySelector('[data-slot="toast-title"]').textContent]
          const portal = document.querySelector('[data-slot="toast-portal"]')
          toast.close()
          await new Promise(r => setTimeout(r, 700))
          portal.setAttribute("data-limit", "1")
          toast("First", { duration: Infinity })
          toast("Second", { duration: Infinity })
          const limited = [...document.querySelectorAll('[data-slot="toast"]')].map(e => e.hasAttribute("data-limited"))
          portal.removeAttribute("data-limit")
          toast.close()
          await new Promise(r => setTimeout(r, 700))
          return { thrown, records, hides, dir: viewport.hasAttribute("dir"), open: viewport.matches(":popover-open"), updated, upserted, limited }
        }"""
    )
    assert all(result["thrown"]) and "icon" in result["thrown"][0], result["thrown"]
    assert result["records"] == 0, result
    assert result["hides"] == 0, "a new toast must not hide and re-show the live region"
    assert not result["dir"] and not result["open"], ("the viewport hides when no toast shows", result)
    assert result["updated"] == [True, "Draft!", "Two"], result["updated"]
    assert result["upserted"] == [4, True, "Again"], result["upserted"]
    assert result["limited"] == [False, True], result["limited"]
    wait(page, "() => !document.querySelector('[data-slot=toast]')")


def check_overlay_button_types(t):
    page = t.page
    page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          window.__submits = 0
          const form = h("form", { id: "bt-form", onsubmit: e => { e.preventDefault(); window.__submits++ } },
            h("input", { id: "bt-input", name: "q" }),
            h("div", { "data-slot": "dialog", id: "bt-dialog" },
              h("button", { "data-dialog-trigger": "", id: "bt-dialog-trigger" }, "Open"),
              h("dialog", { "data-slot": "dialog-content" }, h("h2", { "data-slot": "dialog-title" }, "T"), h("button", { "data-dialog-close": "", id: "bt-close" }, "Cancel"))),
            h("button", { "data-dialog-trigger": "bt-dialog", id: "bt-ref" }, "By id"),
            h("div", { "data-slot": "popover" }, h("button", { "data-popover-trigger": "", id: "bt-popover" }, "Pop"), h("div", { "data-slot": "popover-content" }, "P")),
            h("div", { "data-slot": "dropdown-menu" }, h("button", { "data-dropdown-menu-trigger": "", id: "bt-menu" }, "Menu"), h("div", { "data-slot": "dropdown-menu-content" }, h("div", { "data-slot": "dropdown-menu-item" }, "A"))),
            h("div", { "data-slot": "menubar" }, h("div", { "data-slot": "menubar-menu" }, h("button", { "data-slot": "menubar-trigger", id: "bt-bar" }, "File"), h("div", { "data-slot": "menubar-content" }, h("div", { "data-slot": "menubar-item" }, "New")))),
            h("nav", { "data-slot": "navigation-menu", "data-viewport": "false" }, h("ul", { "data-slot": "navigation-menu-list" }, h("li", { "data-slot": "navigation-menu-item" }, h("button", { "data-slot": "navigation-menu-trigger", id: "bt-nav" }, "Docs"), h("div", { "data-slot": "navigation-menu-content" }, h("a", { "data-slot": "navigation-menu-link", href: "#x" }, "X"))))))
          document.body.prepend(form)
          await new Promise(r => setTimeout(r, 0))
        }"""
    )
    types = page.evaluate("() => ['bt-dialog-trigger', 'bt-close', 'bt-popover', 'bt-menu', 'bt-bar', 'bt-nav'].map(id => document.getElementById(id).type)")
    assert types == ["button"] * 6, types
    dialog = "() => document.querySelector('#bt-dialog dialog').open"
    page.locator("#bt-ref").click()
    wait(page, dialog)
    page.locator("#bt-close").click()
    wait(page, "() => !document.querySelector('#bt-dialog dialog').open")
    for trigger in ("#bt-dialog-trigger", "#bt-popover", "#bt-menu", "#bt-bar", "#bt-nav"):
        page.locator(trigger).click()
        page.keyboard.press("Escape")
        page.wait_for_timeout(250)
    assert page.evaluate("document.getElementById('bt-ref').type") == "button"
    page.locator("#bt-input").press("Enter")
    assert page.evaluate("window.__submits") == 1, page.evaluate("window.__submits")
    assert not page.evaluate(dialog)


def check_command_async(t):
    page = t.page
    page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const root = h("div", { "data-slot": "command", id: "ca" },
            h("input", { "data-slot": "command-input", "aria-label": "Search" }),
            h("div", { "data-slot": "command-list" }, h("div", { "data-slot": "command-empty" }, "No results"), h("div", { "data-slot": "command-item" }, "Banana")))
          root.addEventListener("command:select", e => (window.__picked = e.detail.value))
          document.body.prepend(root)
          await new Promise(r => setTimeout(r, 0))
          window.__add = async (where, ...items) => {
            const banana = [...root.querySelectorAll("[data-slot=command-item]")].find(e => e.textContent === "Banana")
            const nodes = items.map(([text, off]) => h("div", { "data-slot": "command-item", "data-disabled": off ? "" : null }, text))
            if (where === "before") banana.before(...nodes)
            else root.querySelector("[data-slot=command-list]").append(...nodes)
            await new Promise(r => setTimeout(r, 0))
          }
        }"""
    )
    root = page.locator("#ca")
    items = root.locator("[data-slot=command-item]")
    page.evaluate("() => window.__add('before', ['Aardvark'])")
    page.locator("#ca input").fill("zz")
    assert root.locator("[data-slot=command-empty]").is_visible()
    page.evaluate("() => window.__add('end', ['Zz archived', true], ['Zz apple'])")
    roles = items.evaluate_all("els => els.map(e => [e.textContent, e.getAttribute('role'), e.getAttribute('aria-disabled')])")
    assert sorted(roles) == [["Aardvark", "option", None], ["Banana", "option", None], ["Zz apple", "option", None], ["Zz archived", "option", "true"]], roles
    assert not root.locator("[data-slot=command-empty]").is_visible(), "the empty state must update when items arrive"
    assert root.locator("[data-slot=command-item][data-selected=true]").inner_text() == "Zz apple"
    page.keyboard.press("ArrowUp")
    page.keyboard.press("Enter")
    assert page.evaluate("window.__picked") == "Zz apple"
    page.locator("#ca input").fill("")
    order = items.all_inner_texts()
    assert order == ["Aardvark", "Banana", "Zz archived", "Zz apple"], order
    page.evaluate("() => document.querySelectorAll('#ca [data-slot=command-item]').forEach(e => e.remove())")
    page.wait_for_timeout(50)
    assert root.locator("[data-slot=command-empty]").is_visible()


def check_sheet_drawer_scroll(t):
    page = t.page
    t.section("sheet")
    for root, footer, label in (("#sheet-demo", "sheet-footer", "Save changes"), ("#drawer-demo", "drawer-footer", "Submit")):
        page.evaluate(
            """([root, footer]) => {
              const content = document.querySelector(`${root} dialog`)
              const anchor = content.querySelector(`[data-slot="${footer}"]`)
              const scroller = document.createElement("div")
              scroller.dataset.demo = "lorem"
              scroller.dataset.demoRow = ""
              for (let i = 0; i < 40; i++) {
                const row = document.createElement("p")
                row.textContent = `Row ${i}`
                scroller.append(row)
              }
              anchor.before(scroller)
            }""",
            [root, footer],
        )
        page.locator(f"{root} [data-sheet-trigger], {root} [data-drawer-trigger]").first.click()
        wait(page, "s => document.querySelector(s).open", f"{root} dialog")
        content = page.locator(f"{root} dialog [data-slot=drawer-popup]" if "drawer" in root else f"{root} dialog")
        t.settle()
        assert content.evaluate("e => e.getBoundingClientRect().bottom <= innerHeight + 1"), "the content box stays in the viewport"
        scroller = content.locator("[data-demo-row]")
        assert scroller.evaluate("e => e.scrollHeight > e.clientHeight + 100"), "a flex-item scroller holds long content, as in the shadcn examples"
        button = page.locator(f"{root} [data-slot={footer}] button").filter(has_text=label)
        button.scroll_into_view_if_needed()
        bb = box(button)
        assert 0 <= bb["y"] and bb["y"] + bb["height"] <= viewport(page)[1], bb
        t.shot(f"{root[1:]}-scrolled", page)
        button.click()
        wait(page, "s => !document.querySelector(s).open", f"{root} dialog")
        page.evaluate("() => document.querySelectorAll('[data-demo-row]').forEach(e => e.remove())")


def check_navigation_menu_rtl(t):
    page = t.page
    if t.mobile:
        t.skip("desktop navigation menu")
    t.section("navigation-menu")
    before = page.evaluate("() => { const d = document.documentElement.dir; document.documentElement.dir = 'rtl'; return d }")
    for nav, part in (("#navigation-menu-plain", "navigation-menu-content"), ("#navigation-menu-demo", "navigation-menu-viewport")):
        trigger = page.locator(f"{nav} [data-slot=navigation-menu-trigger]").first
        keyboard_focus(page, trigger)
        page.keyboard.press("Enter")
        wait(page, "s => document.querySelector(s).getAttribute('aria-expanded') === 'true'", f"{nav} [data-slot=navigation-menu-trigger]")
        wait(page, "s => !document.querySelector(s).querySelector('[data-starting-style]')", nav)
        t.settle()
        edges = page.evaluate(
            """([nav, part]) => {
              const root = document.querySelector(nav)
              const el = [...root.querySelectorAll(`[data-slot="${part}"]`)].find(e => e.checkVisibility())
              return [Math.round(root.querySelector("[data-slot=navigation-menu-trigger]").getBoundingClientRect().right), Math.round(root.getBoundingClientRect().right), Math.round(el.getBoundingClientRect().right)]
            }""",
            [nav, part],
        )
        assert abs(edges[2] - edges[0]) <= 2, (nav, edges)
        t.shot(f"{nav[1:]}-rtl", page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(250)
    page.evaluate("d => { document.documentElement.dir = d }", before)


def check_navigation_menu_reinsert(t):
    page = t.page
    t.section("navigation-menu")
    trigger = page.locator("#navigation-menu-demo [data-slot=navigation-menu-trigger]").first
    keyboard_focus(page, trigger)
    page.keyboard.press("Enter")
    wait(page, "() => document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-positioner]').matches(':popover-open')")
    page.evaluate(
        """async () => {
          const root = document.getElementById("navigation-menu-demo")
          const parent = root.parentNode, next = root.nextSibling
          root.remove()
          await new Promise(r => setTimeout(r, 30))
          parent.insertBefore(root, next)
          await new Promise(r => setTimeout(r, 30))
        }"""
    )
    assert page.evaluate("() => !document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-positioner]').matches(':popover-open')"), "re-inserted menu must not show an empty viewport"
    keyboard_focus(page, trigger)
    page.keyboard.press("Enter")
    wait(page, "() => document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-trigger]').getAttribute('aria-expanded') === 'true'")
    page.keyboard.press("Escape")


def tip_of(button):
    return button.locator("xpath=..").locator("[data-slot=tooltip-content]")


def tip_open(page, loc, open=True):
    loc.evaluate("(p, open) => new Promise(r => { const tick = () => p.matches(':popover-open') === open ? r() : requestAnimationFrame(tick); tick() })", open)


def check_tooltip_instant(t):
    page = t.page
    section = t.section("tooltip")
    first = section.get_by_role("button", name="Top", exact=True)
    second = section.get_by_role("button", name="Bottom", exact=True)
    away(page)
    page.wait_for_timeout(450)
    first.hover()
    tip_open(page, tip_of(first))
    assert tip_of(first).get_attribute("data-instant") is None and first.get_attribute("data-popup-open") == ""
    second.hover()
    tip_open(page, tip_of(second))
    tip_open(page, tip_of(first), False)
    assert tip_of(second).get_attribute("data-instant") == "delay", "moving between triggers opens the next tooltip at once (Base UI provider group)"
    assert tip_of(second).locator("[data-slot=tooltip-arrow]").get_attribute("data-instant") == "delay"
    assert first.get_attribute("data-popup-open") is None
    page.keyboard.press("Escape")
    assert tip_of(second).get_attribute("data-instant") == "dismiss"
    first.hover()
    tip_open(page, tip_of(first))
    assert tip_of(first).get_attribute("data-instant") == "delay", "a tooltip that opens within 400 ms after another closed opens at once"
    away(page)
    page.wait_for_timeout(500)
    keyboard_focus(page, second)
    tip_open(page, tip_of(second))
    assert tip_of(second).get_attribute("data-instant") == "focus"
    second.evaluate("e => e.blur()")
    tip_open(page, tip_of(second), False)


def check_tooltip_scroll(t):
    page = t.page
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    t.section("tooltip")
    trigger = page.locator("#tooltip-demo [data-tooltip-trigger]")
    content = page.locator("#tooltip-demo [data-slot=tooltip-content]")
    trigger.hover()
    tip_open(page, content)
    page.evaluate("() => window.scrollBy(0, 3)")
    page.wait_for_timeout(300)
    assert is_open(content), "like Base UI, a page scroll keeps the tooltip open"
    tb, cb = box(trigger), box(content)
    assert abs(tb["y"] - cb["y"] - cb["height"] - 4) <= 1, (tb, cb)
    away(page)
    tip_open(page, content, False)


def check_menu_base_ui_dom(t):
    page = t.page
    section = t.section("dropdown-menu")
    trigger = section.locator("#dropdown-menu-demo [data-dropdown-menu-trigger]")
    content = section.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    keyboard_focus(page, trigger)
    page.keyboard.press("Enter")
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    assert trigger.get_attribute("data-popup-open") == "" and trigger.get_attribute("data-pressed") == ""
    assert [content.get_attribute(a) for a in ("data-open", "data-closed", "data-instant", "data-side", "data-align")] == ["", None, "click", "bottom", "start"]
    label = content.locator("[data-slot=dropdown-menu-label]")
    assert label.get_attribute("role") == "presentation" and label.locator("xpath=..").get_attribute("aria-labelledby") == label.get_attribute("id")
    assert content.locator("[data-slot=dropdown-menu-separator]").evaluate_all("els => els.map(e => e.dataset.orientation)") == ["horizontal"] * 4
    variants = content.locator("[data-slot=dropdown-menu-item]").evaluate_all("els => [...new Set(els.map(e => e.dataset.variant))]")
    assert variants == ["default"], variants
    highlighted = lambda: content.locator("[data-highlighted]").evaluate_all("els => els.map(e => e.textContent.trim())")
    assert highlighted() == ["Profile⇧⌘P"]
    page.keyboard.press("ArrowDown")
    assert highlighted() == ["Billing⌘B"]
    look = highlight_look(page, content.get_by_role("menuitem", name="Billing"))
    assert look["outline"] == "none" and look["accent"], ("the default kit highlights like shadcn: accent background, no outline", look)
    page.keyboard.press("Escape")
    assert content.get_attribute("data-instant") == "dismiss" and content.get_attribute("data-closed") == "" and content.get_attribute("data-open") is None
    assert trigger.get_attribute("data-popup-open") is None and trigger.get_attribute("data-pressed") is None
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    checks = section.locator("#dropdown-menu-checkboxes")
    checks.get_by_role("button", name="Appearance").click()
    items = checks.locator("[data-slot=dropdown-menu-checkbox-item]")
    wait(page, "e => e.matches(':popover-open')", checks.locator("[data-slot=dropdown-menu-content]").element_handle())
    status, panel = items.nth(0), items.nth(2)
    assert [status.get_attribute("data-checked"), status.get_attribute("data-unchecked"), panel.get_attribute("data-checked"), panel.get_attribute("data-unchecked")] == ["", None, None, ""]
    mark = status.locator(":scope > [data-slot=dropdown-menu-checkbox-item-indicator]:first-child > span[data-checked][aria-hidden=true] > svg[data-lucide=check]")
    assert mark.count() == 1 and panel.locator(":scope > [data-slot=dropdown-menu-checkbox-item-indicator] > *").count() == 0
    t.settle()
    sb, mb = box(status), box(mark)
    assert abs(inline(t, sb)["x"] + sb["width"] - inline(t, mb)["x"] - mb["width"] - 8) <= 1, (sb, mb)
    page.keyboard.press("Escape")
    radios = section.locator("#dropdown-menu-radio")
    radios.get_by_role("button", name="Panel Position").click()
    bottom = radios.get_by_role("menuitemradio", name="Bottom")
    wait(page, "e => e.matches(':popover-open')", radios.locator("[data-slot=dropdown-menu-content]").element_handle())
    assert bottom.locator(":scope > [data-slot=dropdown-menu-radio-item-indicator] svg[data-lucide=check]").count() == 1
    assert bottom.locator("svg[data-lucide=circle]").count() == 0
    page.keyboard.press("Escape")
    t.section("context-menu")
    area = page.locator("#context-menu-demo [data-slot=context-menu-trigger]")
    ctx = page.locator("#context-menu-demo > [data-slot=context-menu-content]")
    ab = box(area)
    page.mouse.click(ab["x"] + 30, ab["y"] + 20, button="right")
    wait(page, "e => e.matches(':popover-open')", ctx.element_handle())
    bookmarks = ctx.get_by_role("menuitemcheckbox", name="Show Bookmarks")
    assert bookmarks.locator(":scope > span:first-child > span[data-checked] > svg[data-lucide=check]").count() == 1
    assert ctx.get_by_role("menuitemradio", name="Pedro Duarte").locator(":scope > span:first-child svg[data-lucide=check]").count() == 1
    people = ctx.locator("[data-slot=context-menu-label]")
    assert people.get_attribute("role") == "presentation" and ctx.locator("[data-slot=context-menu-radio-group]").get_attribute("aria-labelledby") == people.get_attribute("id")
    assert area.get_attribute("data-pressed") == ""
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", ctx.element_handle())
    assert area.get_attribute("data-popup-open") is None and area.get_attribute("data-pressed") is None
    t.section("menubar")
    bar = page.locator("#menubar-demo")
    assert [bar.get_attribute(a) for a in ("role", "aria-orientation", "data-orientation", "data-modal")] == ["menubar", "horizontal", "horizontal", ""]
    page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          const group = document.querySelectorAll("#menubar-demo [data-slot=menubar-radio-group]")[0]
          group.prepend(h("div", { "data-slot": "menubar-label", "data-inset": "" }, "Profiles"))
          await new Promise(r => setTimeout(r, 0))
        }"""
    )
    bar.get_by_role("menuitem", name="Profiles", exact=True).click()
    menu = bar.locator("[data-slot=menubar-content]").nth(3)
    wait(page, "e => e.matches(':popover-open')", menu.element_handle())
    mlabel = menu.locator("[data-slot=menubar-label]")
    assert mlabel.get_attribute("role") == "presentation" and menu.locator("[data-slot=menubar-radio-group]").get_attribute("aria-labelledby") == mlabel.get_attribute("id")
    assert mlabel.evaluate("e => getComputedStyle(e).paddingInlineStart") == "28px"
    benoit = menu.get_by_role("menuitemradio", name="Benoit")
    t.settle()
    bb, ib = box(benoit), box(benoit.locator(":scope > span:first-child svg[data-lucide=check]"))
    assert abs(inline(t, ib)["x"] - inline(t, bb)["x"] - 6) <= 1, (bb, ib)
    page.keyboard.press("Escape")


def check_menu_modal(t):
    page = t.page
    page.evaluate(
        """async () => {
          const { h } = await import("/clanker-ui.js")
          window.__outside = 0
          document.body.append(h("button", { type: "button", id: "mm-outside", style: { position: "fixed", left: "8px", bottom: "8px", zIndex: "40" }, onclick: () => window.__outside++ }, "Outside"))
        }"""
    )
    section = t.section("dropdown-menu")
    listen(page, "dropdown-menu:select")
    trigger = section.locator("#dropdown-menu-demo [data-dropdown-menu-trigger]")
    content = section.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    outside = page.locator("#mm-outside")
    trigger.click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") == "hidden", "a modal menu locks page scroll"
    ob = box(outside)
    page.mouse.click(ob["x"] + ob["width"] / 2, ob["y"] + ob["height"] / 2)
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    assert page.evaluate("window.__outside") == 0, "the first outside click only closes a modal menu"
    wait(page, "e => document.activeElement === e", trigger.element_handle(), timeout=1000)
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") != "hidden"
    page.mouse.click(ob["x"] + ob["width"] / 2, ob["y"] + ob["height"] / 2)
    assert page.evaluate("window.__outside") == 1
    tb = box(trigger)
    page.mouse.move(tb["x"] + tb["width"] / 2, tb["y"] + tb["height"] / 2)
    page.mouse.down()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    billing = content.get_by_role("menuitem", name="Billing")
    bb = box(billing)
    page.mouse.move(bb["x"] + 12, bb["y"] + bb["height"] / 2, steps=6)
    page.mouse.up()
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    assert [e[1]["value"] for e in events(page, "dropdown-menu:select")] == ["Billing"]
    page.evaluate("() => { document.getElementById('dropdown-menu-demo').dataset.modal = 'false' }")
    trigger.click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") != "hidden"
    page.mouse.click(ob["x"] + ob["width"] / 2, ob["y"] + ob["height"] / 2)
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    assert page.evaluate("window.__outside") == 2


def check_menu_safe_polygon(t):
    page = t.page
    if t.mobile:
        t.skip("the sub menu flips over the menu at 390 px")
    section = t.section("dropdown-menu")
    trigger = section.locator("#dropdown-menu-demo [data-dropdown-menu-trigger]")
    content = section.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    sub = content.locator("[data-slot=dropdown-menu-sub-content]")
    invite = content.get_by_role("menuitem", name="Invite users")
    team = content.get_by_role("menuitem", name="New Team")
    trigger.click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    invite.evaluate("""e => {
      window.__subTimes = {}
      e.addEventListener("pointermove", () => (window.__subTimes.move ??= performance.now()))
      new MutationObserver(() => { if (e.hasAttribute("data-popup-open")) window.__subTimes.open ??= performance.now() }).observe(e, { attributes: true })
    }""")
    invite.hover()
    wait(page, "e => e.matches(':popover-open')", sub.element_handle())
    times = page.evaluate("() => window.__subTimes")
    assert 90 <= times["open"] - times["move"] <= 400, ("a sub menu opens 100 ms after the pointer rests on its trigger", times)
    sub_closed = "e => e.dataset.state === 'closed'"
    for attempt in ("land", "stop", "slow", "leave"):
        invite.hover()
        wait(page, "e => e.matches(':popover-open') && e.dataset.state === 'open'", sub.element_handle())
        page.wait_for_timeout(150)
        cb, ib, nb, sb = box(content), box(invite), box(team), box(sub)
        edge = cb["x"] + cb["width"] if not t.rtl else cb["x"]
        inward = -1 if not t.rtl else 1
        start = (edge + inward * 10, ib["y"] + ib["height"] - 6)
        page.mouse.move(*start)
        if attempt == "land":
            target = sb["x"] + 10 if not t.rtl else sb["x"] + sb["width"] - 10
            page.mouse.move(target, sb["y"] + sb["height"] - 8, steps=8)
            page.wait_for_timeout(150)
            assert is_open(sub) and team.get_attribute("data-highlighted") is None, "the pointer crosses New Team on its way into the sub menu"
            assert invite.get_attribute("data-highlighted") is None and invite.get_attribute("data-popup-open") == "", "the sub trigger loses the highlight while the pointer is in the sub menu"
        elif attempt == "stop":
            page.mouse.move(edge + inward * 8, nb["y"] + 8, steps=2)
            wait(page, sub_closed, sub.element_handle(), timeout=1000)
            page.wait_for_timeout(100)
            assert team.get_attribute("data-highlighted") is None and active(page, "e => e.dataset.slot") == "dropdown-menu-content", "after the sub menu closes, the menu keeps focus and nothing is highlighted until the next move"
            page.mouse.move(edge + inward * 12, nb["y"] + 10, steps=2)
            wait(page, "e => e.hasAttribute('data-highlighted')", team.element_handle())
        elif attempt == "slow":
            for i in range(1, 11):
                page.mouse.move(start[0] - inward * i * 0.3, start[1] + i)
                page.wait_for_timeout(25)
            wait(page, sub_closed, sub.element_handle(), timeout=500)
        else:
            outside = cb["x"] - 40 if not t.rtl else cb["x"] + cb["width"] + 40
            page.mouse.move(outside, start[1])
            page.wait_for_timeout(15)
            assert sub.get_attribute("data-state") == "closed", "a pointer that leaves the sub trigger away from the sub menu closes it at once"
    page.keyboard.press("Escape")


def check_navigation_menu_motion(t):
    page = t.page
    if t.mobile:
        t.skip("desktop navigation menu")
    section = t.section("navigation-menu")
    nav = section.locator("#navigation-menu-demo")
    first = nav.get_by_role("button", name="Getting started")
    second = nav.get_by_role("button", name="Components")
    positioner = nav.locator("[data-slot=navigation-menu-positioner]")
    popup = nav.locator("[data-slot=navigation-menu-popup]")
    away(page)
    positioner.evaluate("""e => {
      window.__instantAtOpen = null
      new MutationObserver(() => { if (e.hasAttribute("data-open") && window.__instantAtOpen === null) window.__instantAtOpen = e.hasAttribute("data-instant") && getComputedStyle(e).transitionProperty === "none" }).observe(e, { attributes: true })
    }""")
    first.hover()
    wait(page, "e => e.matches(':popover-open')", positioner.element_handle())
    assert page.evaluate("window.__instantAtOpen") is True, "the first open places the positioner without a transition"
    assert nav.get_attribute("data-open") == "" and nav.locator("[data-slot=navigation-menu-list]").get_attribute("data-open") == ""
    assert first.get_attribute("data-popup-open") == "" and popup.get_attribute("data-side") == "bottom" and popup.get_attribute("data-align") == "start"
    wait(page, "e => !e.hasAttribute('data-instant') && !document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-popup]').hasAttribute('data-starting-style')", positioner.element_handle())
    t.settle()
    w0 = box(popup)["width"]
    x0 = box(positioner)["x"]
    sample = """() => { const p = document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-popup]'); const r = p.getBoundingClientRect(); const old = document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-content][data-ending-style]'); return [r.width, p.parentElement.getBoundingClientRect().left, old ? getComputedStyle(old).position : null] }"""
    frames = t.paint(sample, lambda: second.hover(), ms=700)
    t.settle()
    w1 = box(popup)["width"]
    x1 = box(positioner)["x"]
    sb, pb = inline(t, box(second)), inline(t, box(positioner))
    assert abs(pb["x"] - sb["x"]) <= 1 and abs(w1 - w0) > 20, (sb, pb, w0, w1)
    if not t.reduced_motion:
        widths = [f[0] for f in frames]
        lefts = [f[1] for f in frames]
        assert any(min(w0, w1) + 2 < w < max(w0, w1) - 2 for w in widths), ("the popup size animates", w0, w1, widths)
        assert any(min(x0, x1) + 2 < x < max(x0, x1) - 2 for x in lefts), ("the positioner moves to the new trigger", x0, x1, lefts)
        assert "absolute" in [f[2] for f in frames], "the old content leaves out of the flow"
    assert popup.evaluate("e => getComputedStyle(e).getPropertyValue('--popup-width').trim()") == "auto"
    away(page)
    wait(page, "e => !e.matches(':popover-open')", positioner.element_handle())
    assert nav.get_attribute("data-open") is None


def check_dialog_pointer_focus(t):
    page = t.page
    section = t.section("alert-dialog")
    trigger = section.get_by_role("button", name="Show Dialog").first
    dialog = "() => document.getElementById('alert-dialog-basic').dataset.state === 'open'"
    closed = "() => !document.getElementById('alert-dialog-basic').open"
    trigger.click()
    wait(page, dialog)
    assert active(page, "e => [e.dataset.slot, e.matches(':focus-visible')]") == ["alert-dialog-cancel", False], "a pointer open shows no focus ring on a button (WebKit native showModal shows one)"
    page.keyboard.press("Escape")
    wait(page, closed)
    keyboard_focus(page, trigger)
    page.keyboard.press("Enter")
    wait(page, dialog)
    assert active(page, "e => [e.dataset.slot, e.matches(':focus-visible')]") == ["alert-dialog-cancel", True], "a keyboard open shows the focus ring"
    page.keyboard.press("Escape")
    wait(page, closed)
    t.section("dialog")
    page.locator("#dialog-demo [data-dialog-trigger]").click()
    wait(page, "() => document.querySelector('#dialog-demo dialog').dataset.state === 'open'")
    assert active(page, "e => [e.id, e.matches(':focus-visible')]") == ["dialog-name", True], "a text field keeps its focus ring, as in Base UI"
    page.keyboard.press("Escape")


def check_command_dom(t):
    page = t.page
    section = t.section("command")
    cmd = section.locator("#command-demo")
    wrapper = cmd.locator(":scope > [data-slot=command-input-wrapper]")
    group = wrapper.locator(":scope > [data-slot=input-group][role=group]")
    assert group.locator(":scope > [data-slot=command-input] + [data-slot=input-group-addon][data-align=inline-start] > svg[data-lucide=search]").count() == 1
    assert abs(box(group)["height"] - 32) <= 0.5
    items = cmd.locator("[data-slot=command-item]")
    assert items.evaluate_all("els => els.every(e => e.lastElementChild.matches('svg[data-lucide=check]'))")
    calendar, profile = items.nth(0), cmd.get_by_role("option", name="Profile")
    check = lambda item: item.locator(":scope > svg[data-lucide=check]").evaluate("e => [getComputedStyle(e).opacity, getComputedStyle(e).display]")
    assert check(calendar) == ["0", "block"] and check(profile)[1] == "none"
    calendar.evaluate("e => e.dataset.checked = 'true'")
    assert check(calendar)[0] == "1"
    calendar.evaluate("e => delete e.dataset.checked")
    heading = cmd.locator("[data-slot=command-group-heading]").first
    assert heading.get_attribute("cmdk-group-heading") == "" and heading.evaluate("e => [getComputedStyle(e).fontSize, getComputedStyle(e).fontWeight]") == ["12px", "500"]
    dialog = section.locator("#command-dialog dialog")
    assert dialog.get_attribute("data-command-dialog") == "" and dialog.locator(":scope > [data-slot=dialog-close]").count() == 0
    section.get_by_role("button", name="Open Menu").click()
    wait(page, "() => document.querySelector('#command-dialog dialog').dataset.state === 'open'")
    t.settle()
    db = box(dialog)
    assert abs(db["y"] - viewport(page)[1] / 3) <= 1, db
    page.keyboard.press("Escape")


def check_alert_dialog_slots(t):
    page = t.page
    section = t.section("alert-dialog")
    probe = """(e, value) => { const p = document.createElement('span'); p.style.color = value; e.append(p); const c = getComputedStyle(p).color; p.remove(); return c }"""
    section.get_by_role("button", name="Show Dialog").first.click()
    basic = page.locator("#alert-dialog-basic")
    wait(page, "() => document.getElementById('alert-dialog-basic').dataset.state === 'open'")
    cancel, action = basic.locator("[data-slot=alert-dialog-cancel]"), basic.locator("[data-slot=alert-dialog-action]")
    assert cancel.get_attribute("data-variant") == "outline" and cancel.inner_text() == "Cancel" and action.inner_text() == "Continue"
    edge = "var(--input)" if t.theme == "dark" else "var(--border)"
    assert cancel.evaluate("e => getComputedStyle(e).borderTopColor") == basic.evaluate(probe, edge)
    assert action.evaluate("e => getComputedStyle(e).backgroundColor") == basic.evaluate(probe, "var(--primary)")
    page.keyboard.press("Escape")
    wait(page, "() => !document.getElementById('alert-dialog-basic').open")
    section.get_by_role("button", name="Delete Chat").click()
    danger = page.locator("#alert-dialog-destructive")
    wait(page, "() => document.getElementById('alert-dialog-destructive').dataset.state === 'open'")
    assert active(page) == "Settings", "Base UI focuses the first tabbable element, here the link in the description"
    delete = danger.locator("[data-slot=alert-dialog-action][data-variant=destructive]")
    assert delete.evaluate("e => getComputedStyle(e).color") == danger.evaluate(probe, "var(--destructive)"), "a destructive action is red"
    tint = 20 if t.theme == "dark" else 10
    assert delete.evaluate("e => getComputedStyle(e).backgroundColor") == danger.evaluate(probe, f"color-mix(in oklab, var(--destructive) {tint}%, transparent)")
    page.keyboard.press("Escape")


NAV_SIZES = """() => {
  const root = document.getElementById("navigation-menu-demo")
  const pos = root.querySelector("[data-slot=navigation-menu-positioner]")
  const pop = pos.querySelector("[data-slot=navigation-menu-popup]")
  const open = [...pos.querySelectorAll("[data-slot=navigation-menu-content]")].filter(c => c.dataset.state === "open")
  const c = open[0]
  return { count: open.length, popup: [pop.offsetWidth, pop.offsetHeight], content: c ? [c.offsetWidth, c.offsetHeight] : null, position: c ? getComputedStyle(c).position : null, ending: c ? c.hasAttribute("data-ending-style") : null, vars: [parseFloat(pos.style.getPropertyValue("--positioner-width")), parseFloat(pos.style.getPropertyValue("--positioner-height"))] }
}"""


def nav_sizes_match(page):
    s = page.evaluate(NAV_SIZES)
    assert s["count"] == 1 and s["position"] == "static" and s["ending"] is False, s
    assert abs(s["popup"][0] - s["content"][0]) <= 1 and abs(s["popup"][1] - s["content"][1]) <= 1, s
    assert abs(s["vars"][0] - s["content"][0]) <= 1 and abs(s["vars"][1] - s["content"][1]) <= 1, s
    return s


def check_navigation_menu_sizes(t):
    page = t.page
    if t.mobile:
        t.skip("desktop navigation menu")
    section = t.section("navigation-menu")
    nav = section.locator("#navigation-menu-demo")
    first = nav.get_by_role("button", name="Getting started")
    second = nav.get_by_role("button", name="Components")
    positioner = nav.locator("[data-slot=navigation-menu-positioner]")
    away(page)
    first.hover()
    wait(page, "e => e.matches(':popover-open')", positioner.element_handle())
    t.settle()
    fb, sb = box(first), box(second)
    page.mouse.move(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2)
    page.wait_for_timeout(40)
    page.mouse.move(fb["x"] + fb["width"] / 2, fb["y"] + fb["height"] / 2)
    page.wait_for_timeout(50)
    page.mouse.move(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2)
    page.wait_for_timeout(40)
    page.mouse.move(fb["x"] + fb["width"] / 2, fb["y"] + fb["height"] / 2)
    page.wait_for_timeout(600)
    t.settle()
    assert first.get_attribute("aria-expanded") == "true"
    nav_sizes_match(page)
    away(page)
    page.wait_for_timeout(180)
    first.hover()
    page.wait_for_timeout(700)
    t.settle()
    assert first.get_attribute("aria-expanded") == "true", "hover back during the exit animation opens it again"
    nav_sizes_match(page)
    page.evaluate("""async () => {
      const { h } = await import("/clanker-ui.js")
      const c = [...document.querySelectorAll("#navigation-menu-demo [data-slot=navigation-menu-content]")].find(c => c.dataset.state === "open")
      c.append(h("div", { id: "nav-grow", style: { height: "120px" } }))
    }""")
    page.wait_for_timeout(500)
    t.settle()
    nav_sizes_match(page)
    page.evaluate("() => document.getElementById('nav-grow').remove()")
    away(page)
    wait(page, "e => !e.matches(':popover-open')", positioner.element_handle())
    first.focus()
    page.keyboard.press("Enter")
    wait(page, "() => document.activeElement?.dataset.slot === 'navigation-menu-link'")
    second.hover()
    wait(page, "e => e.getAttribute('aria-expanded') === 'true'", second.element_handle())
    page.keyboard.press("Escape")
    wait(page, "e => e.getAttribute('aria-expanded') === 'false'", second.element_handle())
    assert active(page) == "Components", "Escape after a hover switch focuses the open trigger, as in Base UI"


LOCKED = "() => getComputedStyle(document.documentElement).overflow === 'hidden'"


def check_menu_scroll_lock(t):
    page = t.page
    section = t.section("dropdown-menu")
    trigger = section.locator("#dropdown-menu-demo [data-dropdown-menu-trigger]")
    content = section.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    opened = "e => e.matches(':popover-open')"
    closed = "e => !e.matches(':popover-open')"
    for how in ("remove", "hide", "hidePopover", "escape"):
        trigger.click()
        wait(page, opened, content.element_handle())
        assert page.evaluate(LOCKED), how
        if how == "remove":
            page.evaluate("""async () => {
              const root = document.getElementById("dropdown-menu-demo")
              const parent = root.parentNode, next = root.nextSibling
              root.remove()
              await new Promise(r => setTimeout(r, 50))
              parent.insertBefore(root, next)
              await new Promise(r => setTimeout(r, 50))
            }""")
        elif how == "hide":
            page.evaluate("async () => (await import('/clanker-ui.js')).hide(document.querySelector('#dropdown-menu-demo > [data-slot=dropdown-menu-content]'))")
        elif how == "hidePopover":
            page.evaluate("() => document.querySelector('#dropdown-menu-demo > [data-slot=dropdown-menu-content]').hidePopover()")
        else:
            page.keyboard.press("Escape")
        wait(page, closed, content.element_handle())
        page.wait_for_timeout(50)
        assert not page.evaluate(LOCKED), ("the page scroll lock stays after", how)


def check_tooltip_hover_card_settings(t):
    page = t.page
    page.evaluate("""async () => {
      const { h } = await import("/clanker-ui.js")
      const provider = h("div", { "data-slot": "tooltip-provider", "data-delay": "0" },
        h("div", { "data-slot": "hover-card", id: "set-hc" },
          h("button", { type: "button", "data-slot": "button", "data-hover-card-trigger": "" }, "Card"),
          h("div", { "data-slot": "hover-card-content" }, "Card body")))
      const card = h("div", { "data-slot": "hover-card", id: "set-hc2", "data-close-delay": "300", "data-delay": "10" },
        h("button", { type: "button", "data-slot": "button", "data-hover-card-trigger": "" }, "Card 2"),
        h("div", { "data-slot": "hover-card-content" },
          h("div", { "data-slot": "tooltip", id: "set-tip" },
            h("button", { type: "button", "data-slot": "button", "data-tooltip-trigger": "" }, "Tip"),
            h("div", { "data-slot": "tooltip-content" }, "tip"))))
      document.body.append(h("div", { id: "set-wrap", style: { position: "fixed", left: "20px", top: "80px", zIndex: "60", display: "flex", gap: "60px" } }, provider, card))
      window.__set = {}
      for (const [id, kind] of [["set-hc", "hover-card"], ["set-tip", "tooltip"]]) {
        const el = document.getElementById(id)
        for (const type of ["open", "close"]) el.addEventListener(`${kind}:${type}`, e => { if (e.target === el) window.__set[`${id}:${type}`] = performance.now() })
      }
      await new Promise(r => setTimeout(r, 50))
    }""")
    away(page)
    page.wait_for_timeout(100)
    card = page.locator("#set-hc [data-hover-card-trigger]")
    start = page.evaluate("() => performance.now()")
    card.hover()
    wait(page, "() => window.__set['set-hc:open']", timeout=3000)
    took = page.evaluate("() => window.__set['set-hc:open']") - start
    assert 550 <= took <= 1000, ("a tooltip provider delay does not reach a hover card", took)
    away(page)
    page.wait_for_timeout(500)
    page.locator("#set-hc2 [data-hover-card-trigger]").hover()
    wait(page, "() => document.querySelector('#set-hc2 [data-slot=hover-card-content]').matches(':popover-open')", timeout=3000)
    t.settle()
    tip = page.locator("#set-tip [data-tooltip-trigger]")
    tip.hover()
    wait(page, "() => window.__set['set-tip:open']")
    cb, pb = box(page.locator("#set-hc2 [data-slot=hover-card-content]")), box(tip)
    corner = cb["x"] + 3 if pb["x"] + pb["width"] / 2 > cb["x"] + cb["width"] / 2 else cb["x"] + cb["width"] - 3
    left = page.evaluate("() => performance.now()")
    page.mouse.move(corner, cb["y"] + cb["height"] - 3, steps=2)
    wait(page, "() => window.__set['set-tip:close']", timeout=3000)
    took = page.evaluate("() => window.__set['set-tip:close']") - left
    assert took < 200, ("a hover card close delay does not reach a tooltip", took)
    away(page)


def check_tooltip_trigger_state(t):
    page = t.page
    page.evaluate("""async () => {
      const { h } = await import("/clanker-ui.js")
      const tip = h("div", { "data-slot": "tooltip", id: "ts-tip" },
        h("button", { type: "button", "data-slot": "toggle", "aria-pressed": "false", "data-tooltip-trigger": "" }, "B"),
        h("div", { "data-slot": "tooltip-content" }, "Bold"))
      const group = h("div", { "data-slot": "toggle-group", "data-type": "single", id: "ts-group" },
        h("div", { "data-slot": "tooltip" },
          h("button", { type: "button", "data-slot": "toggle-group-item", "data-value": "a", "data-tooltip-trigger": "" }, "A"),
          h("div", { "data-slot": "tooltip-content" }, "Item A")),
        h("button", { type: "button", "data-slot": "toggle-group-item", "data-value": "b" }, "B"))
      document.body.append(h("div", { id: "ts-wrap", style: { position: "fixed", left: "20px", top: "120px", zIndex: "60", display: "flex", gap: "40px" } }, tip, group))
      await new Promise(r => setTimeout(r, 50))
    }""")
    toggle = page.locator("#ts-tip [data-slot=toggle]")
    item = page.locator("#ts-group [data-value=a]")
    for el in (toggle, item):
        el.click()
        away(page)
        page.wait_for_timeout(200)
        el.hover()
        wait(page, "e => e.hasAttribute('data-popup-open')", el.element_handle())
        away(page)
        wait(page, "e => !e.hasAttribute('data-popup-open')", el.element_handle())
        page.wait_for_timeout(200)
        attrs = el.evaluate("e => [e.dataset.state, e.hasAttribute('data-pressed') || e.getAttribute('aria-checked') === 'true' || e.getAttribute('aria-pressed') === 'true']")
        assert attrs == ["on", True], ("a tooltip does not change the trigger state", attrs)
    value = page.evaluate("async () => { const g = document.getElementById('ts-group'); return [...g.querySelectorAll('[data-slot=toggle-group-item]')].filter(e => e.dataset.state === 'on').map(e => e.dataset.value) }")
    assert value == ["a"], value


def check_menu_trigger_click_listener(t):
    page = t.page
    section = t.section("dropdown-menu")
    trigger = section.locator("#dropdown-menu-demo [data-dropdown-menu-trigger]")
    content = section.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    bar = page.locator("#menubar-demo [data-slot=menubar-trigger]").first
    page.evaluate("""() => {
      window.__clicks = []
      document.querySelector("#dropdown-menu-demo [data-dropdown-menu-trigger]").addEventListener("click", () => window.__clicks.push("menu"))
      document.querySelector("#menubar-demo [data-slot=menubar-trigger]").addEventListener("click", () => window.__clicks.push("bar"))
      document.addEventListener("click", e => { if (e.target.closest?.("#dropdown-menu-demo, #menubar-demo")) window.__clicks.push("document") })
    }""")
    trigger.click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    trigger.focus()
    page.keyboard.press("Enter")
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    page.keyboard.press("Escape")
    t.section("menubar")
    bar.click()
    wait(page, "() => document.querySelector('#menubar-demo [data-slot=menubar-content]').matches(':popover-open')")
    page.keyboard.press("Escape")
    assert page.evaluate("window.__clicks") == ["menu", "document", "menu", "document", "bar", "document"], ("app click listeners on a trigger run, as in Base UI", page.evaluate("window.__clicks"))


HIGHLIGHT = """(e, token) => {
  const canvas = document.createElement("canvas")
  canvas.width = canvas.height = 1
  const ctx = canvas.getContext("2d", { willReadFrequently: true })
  const paint = colors => { ctx.clearRect(0, 0, 1, 1); for (const c of ["#fff", ...colors]) { ctx.fillStyle = c; ctx.fillRect(0, 0, 1, 1) } return [...ctx.getImageData(0, 0, 1, 1).data].slice(0, 3) }
  const lum = c => { const [r, g, b] = c.map(v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4 }); return 0.2126 * r + 0.7152 * g + 0.0722 * b }
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return +((Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05)).toFixed(2) }
  const layers = []
  for (let n = e; n; n = n.parentElement) layers.unshift(getComputedStyle(n).backgroundColor)
  const s = getComputedStyle(e)
  const ring = paint([...layers, s.outlineColor])
  const probe = document.body.appendChild(document.createElement("span"))
  probe.style.color = `var(${token})`
  const accent = getComputedStyle(probe).color
  probe.remove()
  return { slot: e.dataset.slot, outline: s.outlineStyle === "none" ? "none" : `${s.outlineStyle} ${s.outlineWidth} ${s.outlineOffset}`, inside: ratio(ring, paint(layers)), outside: ratio(ring, paint(layers.slice(0, -1))), accent: paint(layers).join() === paint([...layers.slice(0, -1), accent]).join() }
}"""


def highlight_look(page, loc, token="--accent"):
    page.wait_for_function("e => e.getAnimations().every(a => a.playState !== 'running' || a.timeline !== document.timeline)", arg=loc.element_handle())
    return loc.evaluate(HIGHLIGHT, token)


def assert_pointer_look(page, loc, token="--accent"):
    look = highlight_look(page, loc, token)
    assert look["outline"] == "none" and look["accent"], look


def assert_keyboard_look(page, loc):
    look = highlight_look(page, loc)
    assert look["outline"] == "solid 2px -2px" and look["inside"] >= 3 and look["outside"] >= 3, look


def check_keyboard_highlight(t):
    page = t.page
    t.a11y()
    focus = page.locator(":focus")
    t.section("dropdown-menu")
    menu = page.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    page.locator("#dropdown-menu-demo").get_by_role("button", name="Open").click()
    item = menu.get_by_role("menuitem", name="Billing")
    item.hover()
    assert_pointer_look(page, item)
    page.keyboard.press("ArrowDown")
    assert_keyboard_look(page, focus)
    t.shot("dropdown-menu-keyboard", page)
    ib = item.bounding_box()
    page.mouse.move(ib["x"] + 12, ib["y"] + ib["height"] / 2)
    assert_pointer_look(page, item)
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", menu.element_handle())
    t.section("context-menu")
    area = page.locator("#context-menu-demo [data-slot=context-menu-trigger]")
    ab = area.bounding_box()
    page.mouse.click(ab["x"] + 40, ab["y"] + 30, button="right")
    context = page.locator("#context-menu-demo > [data-slot=context-menu-content]")
    wait(page, "e => e.matches(':popover-open')", context.element_handle())
    item = context.get_by_role("menuitem").first
    item.hover()
    assert_pointer_look(page, item)
    page.keyboard.press("ArrowDown")
    assert_keyboard_look(page, focus)
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", context.element_handle())
    t.section("menubar")
    file = page.locator("#menubar-demo").get_by_role("menuitem", name="File", exact=True)
    file.click()
    item = page.get_by_role("menu", name="File", exact=True).get_by_role("menuitem").first
    item.hover()
    assert_pointer_look(page, item)
    page.keyboard.press("ArrowDown")
    assert_keyboard_look(page, focus)
    page.keyboard.press("Escape")
    wait(page, "e => document.activeElement === e", file.element_handle())
    assert_keyboard_look(page, file)
    page.keyboard.press("ArrowRight")
    assert_keyboard_look(page, focus)
    t.section("select")
    select = page.locator("#select-demo")
    content = select.locator("[data-slot=select-content]")
    select.locator("[data-slot=select-trigger]").click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    assert_pointer_look(page, focus)
    item = content.get_by_role("option", name="Banana")
    item.hover()
    assert_pointer_look(page, item)
    page.keyboard.press("ArrowDown")
    assert_keyboard_look(page, focus)
    t.shot("select-keyboard", page)
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    t.section("combobox")
    combobox = page.locator("#combobox-basic")
    content = combobox.locator("[data-slot=combobox-content]")
    combobox.locator("input[data-slot=input-group-control]").click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    item = combobox.locator("[data-slot=combobox-item]").nth(1)
    item.hover()
    assert item.get_attribute("data-highlighted") == ""
    assert_pointer_look(page, item)
    page.keyboard.press("ArrowDown")
    assert_keyboard_look(page, combobox.locator("[data-slot=combobox-item][data-highlighted]"))
    t.shot("combobox-keyboard", page)
    page.keyboard.press("Escape")
    t.section("command")
    command = page.locator("#command-demo")
    selected = command.locator("[data-slot=command-item][data-selected=true]")
    command.get_by_role("combobox").click()
    assert_pointer_look(page, selected, "--muted")
    command.get_by_role("option", name="Search Emoji").hover()
    assert selected.inner_text() == "Search Emoji"
    assert_pointer_look(page, selected, "--muted")
    page.keyboard.press("ArrowDown")
    assert_keyboard_look(page, selected)
    t.shot("command-keyboard", command)
    page.evaluate("() => document.activeElement.blur()")
    assert highlight_look(page, selected)["outline"] == "none", "no indicator when focus is outside the command"
    if t.mobile:
        return
    t.section("navigation-menu")
    trigger = page.locator("#navigation-menu-demo [data-slot=navigation-menu-trigger]").first
    keyboard_focus(page, trigger)
    page.keyboard.press("Enter")
    wait(page, "e => e.getAttribute('aria-expanded') === 'true'", trigger.element_handle())
    t.settle()
    page.keyboard.press("ArrowDown")
    wait(page, "() => document.activeElement?.dataset.slot === 'navigation-menu-link'")
    link = page.locator("#navigation-menu-demo [data-slot=navigation-menu-link]:focus")
    assert_keyboard_look(page, link)
    t.shot("navigation-menu-keyboard", page)
    link.hover()
    assert_pointer_look(page, link, "--muted")


def check_keyboard_modality_keys(t):
    page = t.page
    t.a11y()
    keyboard = lambda: page.evaluate("document.documentElement.hasAttribute('data-keyboard')")
    t.section("dropdown-menu")
    menu = page.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    page.locator("#dropdown-menu-demo").get_by_role("button", name="Open").click()
    item = menu.get_by_role("menuitem", name="Billing")
    item.hover()
    for combo in ["Control+c", "Meta+c", "Alt+x", "Shift", "Meta"]:
        page.keyboard.press(combo)
        assert not keyboard(), combo
    for key in ["ArrowDown", "Unidentified"]:
        page.evaluate("k => document.body.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true }))", key)
        assert not keyboard(), f"untrusted {key}"
    assert_pointer_look(page, item)
    page.keyboard.press("ArrowDown")
    assert keyboard()
    assert_keyboard_look(page, page.locator(":focus"))
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", menu.element_handle())


def check_forced_colors_focus(t):
    page = t.page
    t.a11y()
    page.emulate_media(forced_colors="active")
    if not page.evaluate("matchMedia('(forced-colors: active)').matches"):
        t.skip("engine has no forced-colors emulation")
    t.section("dropdown-menu")
    trigger = page.locator("#dropdown-menu [data-slot=dropdown-menu-trigger], #dropdown-menu [data-dropdown-menu-trigger]").first
    keyboard_focus(page, trigger)
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowDown")
    styles = page.evaluate("() => { const a = document.activeElement, n = a.nextElementSibling; return [a.dataset.slot, getComputedStyle(a).outlineStyle, getComputedStyle(n).outlineStyle, getComputedStyle(a).outlineColor !== getComputedStyle(n).outlineColor] }")
    assert styles[0].endswith("-item") and styles[1] == "solid" and styles[2] == "solid" and styles[3], styles
    page.keyboard.press("Escape")


def check_alert_dialog_action(t):
    page = t.page
    section = t.section("alert-dialog")
    dialog = page.locator("#alert-dialog-basic")
    action = dialog.locator("[data-slot=alert-dialog-action]")
    section.get_by_role("button", name="Show Dialog").first.click()
    wait(page, "() => document.getElementById('alert-dialog-basic').open")
    action.click()
    page.wait_for_timeout(250)
    assert dialog.evaluate("e => e.open"), "Continue is a plain button and leaves the alert dialog open, as in shadcn"
    page.mouse.click(4, 4)
    page.wait_for_timeout(150)
    assert dialog.evaluate("e => e.open") and active(page, "e => e.tagName") == "BODY", "a press outside an alert dialog moves focus out of it, as in Base UI"
    action.evaluate("e => e.setAttribute('data-alert-dialog-close', '')")
    action.click()
    wait(page, "() => !document.getElementById('alert-dialog-basic').open")
    action.evaluate("e => e.removeAttribute('data-alert-dialog-close')")


def check_menu_disabled_keys(t):
    page = t.page
    t.section("dropdown-menu")
    trigger = page.locator("#dropdown-menu-demo [data-dropdown-menu-trigger]")
    content = page.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    listen(page, "dropdown-menu:select")
    keyboard_focus(page, trigger)
    page.keyboard.press("Enter")
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    page.keyboard.press("End")
    page.keyboard.press("ArrowUp")
    assert active(page) == "API", "keys reach disabled items, as in Base UI menus"
    assert active(page, "e => e.getAttribute('aria-disabled') + ' ' + e.hasAttribute('data-highlighted')") == "true true"
    page.keyboard.press("Enter")
    page.wait_for_timeout(100)
    assert is_open(content) and not events(page, "dropdown-menu:select"), "a disabled item does not run"
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    t.section("menubar")
    file = page.locator("#menubar-demo").get_by_role("menuitem", name="File", exact=True)
    menu = page.locator("#menubar-demo [data-slot=menubar-content]").first
    keyboard_focus(page, file)
    page.keyboard.press("Enter")
    wait(page, "e => e.matches(':popover-open')", menu.element_handle())
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    assert active(page) == "New Incognito Window"
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", menu.element_handle())


def check_menubar_switch(t):
    page = t.page
    t.section("menubar")
    bar = page.locator("#menubar-demo")
    file, edit, view, profiles = (bar.get_by_role("menuitem", name=n, exact=True) for n in ("File", "Edit", "View", "Profiles"))
    contents = bar.locator("[data-slot=menubar-content]")
    opened = "e => e.matches(':popover-open')"
    none_open = "() => !document.querySelector('#menubar-demo [data-slot=menubar-content]:popover-open')"
    keyboard_focus(page, file)
    page.keyboard.press("Enter")
    wait(page, opened, contents.nth(0).element_handle())
    page.keyboard.press(key(t, "ArrowRight"))
    wait(page, opened, contents.nth(1).element_handle())
    assert active(page, "e => e.dataset.slot + ' ' + e.getAttribute('aria-labelledby')") == "menubar-content " + edit.get_attribute("id"), "ArrowRight in an open menu focuses the next popup, as in Base UI"
    assert contents.nth(1).locator("[data-highlighted]").count() == 0
    page.keyboard.press("ArrowDown")
    assert active(page) == "Undo⌘Z"
    page.keyboard.press("Escape")
    wait(page, none_open)
    view.click()
    wait(page, opened, contents.nth(2).element_handle())
    profiles.hover()
    wait(page, opened, contents.nth(3).element_handle())
    edit.click()
    wait(page, none_open)
    wait(page, "e => document.activeElement === e", edit.element_handle(), timeout=1000)
    assert edit.get_attribute("aria-expanded") == "false", "a click on another trigger while a menu is open closes the menus"
    description = page.locator("#menubar [data-demo=description]")
    description.evaluate("e => e.scrollIntoView({ block: 'center', behavior: 'instant' })")
    edit.click()
    wait(page, opened, contents.nth(1).element_handle())
    tb = box(description)
    page.mouse.click(tb["x"] + 4, tb["y"] + tb["height"] / 2)
    wait(page, none_open)
    wait(page, "e => document.activeElement === e", edit.element_handle(), timeout=1000)


def check_navigation_menu_keys(t):
    page = t.page
    section = t.section("navigation-menu")
    nav = section.locator("#navigation-menu-demo")
    first = nav.get_by_role("button", name="Getting started")
    icon = nav.get_by_role("button", name="With Icon")
    first_content = nav.locator("#" + first.get_attribute("aria-controls"))
    page.evaluate("""() => {
      window.__fade = []
      const content = document.querySelector("#navigation-menu-demo [data-slot=navigation-menu-content]")
      const sample = () => { if (!content.hidden) window.__fade.push(Number(getComputedStyle(content).opacity)); if (window.__fade.length < 30) requestAnimationFrame(sample) }
      requestAnimationFrame(sample)
    }""")
    first.hover()
    wait(page, "() => window.__fade.length >= 30", timeout=5000)
    if not t.reduced_motion:
        fade = page.evaluate("() => window.__fade")
        assert fade and min(fade) < 0.5, ("the first open fades the content in from its starting style, as in shadcn", fade[:8])
    page.evaluate("""() => {
      window.__sw = {}
      const nav = document.getElementById("navigation-menu-demo")
      const icon = [...nav.querySelectorAll("[data-slot=navigation-menu-trigger]")].find(e => e.textContent.trim() === "With Icon")
      icon.addEventListener("pointerover", () => (window.__sw.over ??= performance.now()))
      nav.addEventListener("navigation-menu:change", () => (window.__sw.change ??= performance.now()))
    }""")
    icon.hover()
    wait(page, "() => window.__sw.change")
    times = page.evaluate("() => window.__sw")
    assert times["change"] - times["over"] >= 40, ("a switch waits for the open delay, as in Base UI", times)
    if t.width < 500 and not t.rtl:
        t.settle()
        fit = page.evaluate("""() => {
          const nav = document.getElementById("navigation-menu-demo")
          const r = [...nav.querySelectorAll("[data-slot=navigation-menu-trigger]")].find(e => e.textContent.trim() === "With Icon").getBoundingClientRect()
          const w = nav.querySelector("[data-slot=navigation-menu-positioner]").getBoundingClientRect().width
          const vw = document.documentElement.clientWidth
          return [vw - 5 - (r.left + w), r.right - w - 5]
        }""")
        want = "end" if fit[0] < 0 and fit[1] >= 0 else "start"
        assert nav.locator("[data-slot=navigation-menu-positioner]").get_attribute("data-align") == want, ("the popup flips to end alignment only when start overflows and end fits, as in Base UI", fit)
    away(page)
    wait(page, "() => !document.querySelector('#navigation-menu-demo [data-slot=navigation-menu-positioner]:popover-open')")
    keyboard_focus(page, first)
    page.keyboard.press("ArrowDown")
    wait(page, "e => e.getAttribute('aria-expanded') === 'true'", first.element_handle())
    assert active(page).startswith("Introduction"), "ArrowDown on a closed trigger opens it and focuses the first link"
    assert first.get_attribute("data-pressed") == ""
    page.keyboard.press("End")
    assert active(page).startswith("Introduction"), "End does not move focus in the content"
    assert nav.locator("[data-slot=navigation-menu-focus-guard]").count() == 3 and first.evaluate("e => e.nextElementSibling?.dataset.edge") == "trigger", "focus guards around the popup and after the open trigger, as in Base UI"
    for _ in range(5):
        page.keyboard.press("Tab")
        if not active(page, "e => !!e.closest('[data-slot=navigation-menu-content]')"):
            break
    assert active(page) == ("Components" if t.width >= 768 else "With Icon"), "Tab out of the panel goes to the next trigger (Base UI focus guards)"
    page.keyboard.press("Shift+Tab")
    assert active(page).startswith("Typography"), "Shift+Tab from the next trigger goes to the last link of the open panel"
    for _ in range(4):
        page.keyboard.press("Shift+Tab")
        if active(page) == "Getting started":
            break
    assert active(page) == "Getting started" and first.get_attribute("aria-expanded") == "true"
    page.keyboard.press("ArrowDown")
    wait(page, "() => document.activeElement?.closest('[data-slot=navigation-menu-content]')")
    page.keyboard.press("Escape")
    wait(page, "e => e.getAttribute('aria-expanded') === 'false'", first.element_handle())
    assert active(page) == "Getting started"
    page.keyboard.press("Enter")
    wait(page, "() => document.activeElement?.closest('[data-slot=navigation-menu-content]')")
    page.keyboard.press("Shift+Tab")
    assert active(page) == "Getting started"
    page.keyboard.press("Enter")
    wait(page, "e => e.getAttribute('aria-expanded') === 'false'", first.element_handle())
    page.keyboard.press("ArrowDown")
    wait(page, "() => document.activeElement?.closest('[data-slot=navigation-menu-content]')")
    page.keyboard.press("Escape")
    wait(page, "e => e.getAttribute('aria-expanded') === 'false'", first.element_handle())
    assert active(page) == "Getting started" and first.get_attribute("data-pressed") is None
    page.keyboard.press("End")
    assert active(page) == "Getting started", "Home and End do not move focus between triggers, as in Base UI"
    page.keyboard.press("Home")
    assert active(page) == "Getting started"
    assert first_content.get_attribute("data-state") == "closed"


def check_popover_outside_focus(t):
    page = t.page
    section = t.section("popover")
    trigger = section.locator("#popover-demo [data-popover-trigger]")
    content = section.locator("#popover-demo [data-slot=popover-content]")
    description = section.locator("[data-demo=description]")
    description.evaluate("e => e.scrollIntoView({ block: 'center', behavior: 'instant' })")
    trigger.click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    tb = box(description)
    page.mouse.click(tb["x"] + 4, tb["y"] + tb["height"] / 2)
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    wait(page, "() => document.activeElement?.matches('#popover-demo [data-popover-trigger]')", timeout=1000)
    assert not trigger.evaluate("e => e.matches(':focus-visible')"), "an outside press returns focus to the trigger without a ring, as in Base UI"


def check_focus_return_ring(t):
    page = t.page
    section = t.section("dialog")
    trigger = section.locator("#dialog-demo [data-dialog-trigger]")
    dialog = section.locator("#dialog-demo [data-slot=dialog-content]")
    keyboard_focus(page, trigger)
    page.keyboard.press("Enter")
    wait(page, "e => e.open", dialog.element_handle())
    t.settle()
    page.mouse.click(4, 4)
    wait(page, "e => !e.open", dialog.element_handle())
    wait(page, "e => document.activeElement === e", trigger.element_handle(), timeout=1000)
    assert trigger.evaluate("e => e.matches(':focus-visible')"), "a dialog opened from the keyboard returns a visible focus, as in Base UI"
    page.keyboard.press("Enter")
    wait(page, "e => e.open", dialog.element_handle())
    t.settle()
    dialog.locator("[data-slot=dialog-close]").click()
    wait(page, "e => !e.open", dialog.element_handle())
    wait(page, "e => document.activeElement === e", trigger.element_handle(), timeout=1000)
    page.wait_for_timeout(100)
    assert not trigger.evaluate("e => e.matches(':focus-visible')"), "a pointer press on the close button returns focus without a ring"
    trigger.click()
    wait(page, "e => e.open", dialog.element_handle())
    t.settle()
    page.mouse.click(4, 4)
    wait(page, "e => !e.open", dialog.element_handle())
    wait(page, "e => document.activeElement === e", trigger.element_handle(), timeout=1000)
    page.wait_for_timeout(100)
    assert not trigger.evaluate("e => e.matches(':focus-visible')"), "a pointer open and an outside press return focus without a ring"
    section = t.section("alert-dialog")
    alert_trigger = section.get_by_role("button", name="Show Dialog").first
    keyboard_focus(page, alert_trigger)
    page.keyboard.press("Enter")
    wait(page, "() => document.getElementById('alert-dialog-basic').open")
    page.locator("#alert-dialog-basic").get_by_role("button", name="Cancel").click()
    wait(page, "() => !document.getElementById('alert-dialog-basic').open")
    wait(page, "e => document.activeElement === e", alert_trigger.element_handle(), timeout=1000)
    assert alert_trigger.evaluate("e => e.matches(':focus-visible')"), "a press on the focused Cancel keeps the keyboard ring for the trigger"
    section = t.section("sheet")
    sheet_trigger = section.locator("[data-sheet-trigger]").first
    sheet = page.locator("#" + sheet_trigger.get_attribute("aria-controls"))
    keyboard_focus(page, sheet_trigger)
    page.keyboard.press("Enter")
    wait(page, "e => e.open", sheet.element_handle())
    t.settle()
    width, height = viewport(page)
    sb = box(sheet)
    page.mouse.click(4 if sb["x"] + sb["width"] / 2 > width / 2 else width - 4, height // 2)
    wait(page, "e => !e.open", sheet.element_handle())
    wait(page, "e => document.activeElement === e", sheet_trigger.element_handle(), timeout=1500)
    assert sheet_trigger.evaluate("e => e.matches(':focus-visible')"), "a sheet opened from the keyboard returns a visible focus after an outside press"
    t.section("dropdown-menu")
    menu_trigger = page.locator("#dropdown-menu-demo [data-dropdown-menu-trigger]")
    content = page.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    menu_trigger.click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    assert not page.evaluate("() => document.activeElement.matches(':focus-visible')"), "a pointer open focuses the menu without a ring"
    menu_trigger.click()
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    wait(page, "e => document.activeElement === e", menu_trigger.element_handle(), timeout=1000)
    assert not menu_trigger.evaluate("e => e.matches(':focus-visible')"), "a menu opened and closed with the pointer returns focus without a ring"
    menu_trigger.click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    content.get_by_role("menuitem", name="Profile").click()
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    wait(page, "e => document.activeElement === e", menu_trigger.element_handle(), timeout=1000)
    assert not menu_trigger.evaluate("e => e.matches(':focus-visible')"), "an item click after a pointer open returns focus without a ring"
    keyboard_focus(page, menu_trigger)
    page.keyboard.press("Enter")
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    wait(page, "e => document.activeElement === e && e.matches(':focus-visible')", menu_trigger.element_handle(), timeout=1000)
    menu_trigger.click()
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    content.get_by_role("menuitem", name="Profile").click()
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    wait(page, "e => document.activeElement === e", menu_trigger.element_handle(), timeout=1000)
    assert menu_trigger.evaluate("e => e.matches(':focus-visible')"), "a trigger with a ring before a pointer open gets the ring back after an item click, as live in all engines"
    section = t.section("alert-dialog")
    alert_trigger = section.get_by_role("button", name="Show Dialog").first
    alert_trigger.click()
    wait(page, "() => document.getElementById('alert-dialog-basic').open")
    page.keyboard.press("Escape")
    wait(page, "() => !document.getElementById('alert-dialog-basic').open")
    wait(page, "e => document.activeElement === e", alert_trigger.element_handle(), timeout=1000)
    assert alert_trigger.evaluate("e => e.matches(':focus-visible')"), "Escape returns a visible focus"


def check_button_tab_order(t):
    page = t.page
    section = t.section("dialog")
    assert page.evaluate("() => [...document.querySelectorAll('button[data-slot=button]:not([tabindex])')].length") == 0, "kit buttons have tabindex 0, as Base UI buttons"
    trigger = section.locator("#dialog-demo [data-dialog-trigger]")
    keyboard_focus(page, trigger)
    page.keyboard.press("Enter")
    wait(page, "() => document.activeElement?.id === 'dialog-name'")
    order = []
    for _ in range(5):
        page.keyboard.press("Tab")
        order.append(active(page, "e => e.id || e.getAttribute('data-slot') + ':' + e.textContent.trim()"))
    assert order == ["dialog-username", "button:Cancel", "button:Save changes", "dialog-close:Close", "dialog-name"], order
    page.keyboard.press("Escape")
    form = t.section("questionnaire").locator("#questionnaire-demo")
    previous = form.locator("[data-slot=questionnaire-previous]")
    assert previous.get_attribute("tabindex") == "-1"
    form.locator("fieldset[name=direction] [data-slot=questionnaire-choice]").first.click()
    form.locator("[data-slot=questionnaire-next]").click()
    wait(page, "e => !e.hidden", previous.element_handle())
    assert previous.get_attribute("tabindex") == "0", "a questionnaire button that shows again keeps tabindex 0, so Safari Tab reaches it"


def check_hover_card_blur(t):
    page = t.page
    section = t.section("hover-card")
    trigger = section.locator("#hover-card-demo [data-hover-card-trigger]")
    content = section.locator("#hover-card-demo [data-slot=hover-card-content]")
    page.evaluate("""() => {
      window.__hb = {}
      const root = document.getElementById("hover-card-demo")
      root.querySelector("[data-hover-card-trigger]").dataset.closeDelay = "1000"
      root.addEventListener("focusout", () => (window.__hb.out ??= performance.now()))
      root.addEventListener("hover-card:close", () => (window.__hb.close ??= performance.now()))
    }""")
    keyboard_focus(page, trigger)
    wait(page, "e => e.matches(':popover-open')", content.element_handle(), timeout=2000)
    page.keyboard.press("Shift+Tab")
    wait(page, "() => window.__hb.close")
    took = page.evaluate("() => window.__hb.close - window.__hb.out")
    assert took < 500, ("focus leaving the trigger closes the card at once, not after the 1000 ms close delay, as in Base UI", took)


def check_command_list_focus(t):
    page = t.page
    section = t.section("command")
    root = section.locator("#command-demo")
    listbox = root.locator("[data-slot=command-list]")
    assert listbox.get_attribute("tabindex") == "-1"
    item = root.get_by_role("option", name="Billing")
    item.click()
    assert active(page, "e => e.dataset.slot") == "command-list", "a pointer press on an item focuses the list, as in cmdk"
    assert listbox.get_attribute("aria-activedescendant") == item.get_attribute("id")
    page.keyboard.press("ArrowDown")
    selected = root.locator("[data-slot=command-item][data-selected=true]")
    assert selected.inner_text().startswith("Settings") and listbox.get_attribute("aria-activedescendant") == selected.get_attribute("id")


def check_menu_hide_others(t):
    page = t.page
    section = t.section("context-menu")
    area = section.locator("#context-menu-demo [data-slot=context-menu-trigger]")
    content = section.locator("#context-menu-demo [data-slot=context-menu-content]")
    area.click(button="right")
    wait(page, "e => e.matches(':popover-open')", content.element_handle())
    assert area.evaluate("e => !!e.closest('[aria-hidden=true]')"), "a modal context menu hides the rest of the page from assistive tech, as in Base UI"
    assert not content.evaluate("e => !!e.closest('[aria-hidden=true]')")
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", content.element_handle())
    assert not area.evaluate("e => !!e.closest('[aria-hidden=true]')")
    t.section("dropdown-menu")
    trigger = page.locator("#dropdown-menu-demo [data-dropdown-menu-trigger]")
    menu = page.locator("#dropdown-menu-demo > [data-slot=dropdown-menu-content]")
    trigger.click()
    wait(page, "e => e.matches(':popover-open')", menu.element_handle())
    assert not page.evaluate("() => !!document.querySelector('#dialog-demo')?.closest('[aria-hidden=true]')"), "a dropdown menu does not hide the page; Base UI does that only for the context menu"
    page.keyboard.press("Escape")
    wait(page, "e => !e.matches(':popover-open')", menu.element_handle())
    t.section("menubar")
    view = page.locator("#menubar-demo").get_by_role("menuitem", name="View", exact=True)
    view.click()
    wait(page, "() => document.querySelector('#menubar-demo [data-slot=menubar-content]:popover-open')")
    assert not page.evaluate("() => !!document.querySelector('#dialog-demo')?.closest('[aria-hidden=true]')"), "a menubar menu does not hide the page"
    page.keyboard.press("Escape")
    wait(page, "() => !document.querySelector('#menubar-demo [data-slot=menubar-content]:popover-open')")


def check_menu_parent_close(t):
    page = t.page
    t.section("dialog")
    result = page.evaluate("""async () => {
      const { h, dialogOpen, hide } = await import('/clanker-ui.js')
      const frames = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 50))))
      const hiddenCount = () => document.querySelectorAll('[aria-hidden=true]:not([data-slot=focus-guard])').length
      const locked = () => getComputedStyle(document.documentElement).overflow === 'hidden'
      const menus = id => [
        h('div', { 'data-slot': 'context-menu' }, h('div', { 'data-slot': 'context-menu-trigger', tabindex: '0', id: id + '-area' }, 'Area'), h('div', { 'data-slot': 'context-menu-content', id: id + '-ctx' }, h('div', { 'data-slot': 'context-menu-item' }, 'One'))),
        h('div', { 'data-slot': 'dropdown-menu' }, h('button', { type: 'button', 'data-slot': 'button', 'data-dropdown-menu-trigger': '', id: id + '-trigger' }, 'Menu'), h('div', { 'data-slot': 'dropdown-menu-content', id: id + '-dd' }, h('div', { 'data-slot': 'dropdown-menu-item' }, 'Two'))),
      ]
      const right = el => { const r = el.getBoundingClientRect(); el.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, button: 2, clientX: r.left + 5, clientY: r.top + 5 })) }
      let base = 0
      const out = {}
      const dialog = h('div', { 'data-slot': 'dialog' }, h('dialog', { 'data-slot': 'dialog-content' }, h('h2', { 'data-slot': 'dialog-title' }, 'Parent'), ...menus('pc')))
      document.body.append(dialog)
      await frames()
      dialogOpen(dialog)
      await frames()
      base = hiddenCount()
      right(document.getElementById('pc-area'))
      await frames()
      out.dialogOpened = document.getElementById('pc-ctx').matches(':popover-open') && hiddenCount() > base && locked()
      hide(dialog.querySelector('dialog'))
      await frames()
      await new Promise(r => setTimeout(r, 400))
      out.dialogClosed = [!document.getElementById('pc-ctx').matches(':popover-open'), hiddenCount() === base, !locked()]
      dialog.remove()
      const box = h('div', {}, ...menus('hc'))
      document.body.append(box)
      await frames()
      base = hiddenCount()
      right(document.getElementById('hc-area'))
      await frames()
      out.boxOpened = document.getElementById('hc-ctx').matches(':popover-open') && hiddenCount() > base && locked()
      box.hidden = true
      await frames()
      await new Promise(r => setTimeout(r, 400))
      out.boxClosed = [!document.getElementById('hc-ctx').matches(':popover-open'), hiddenCount() === base, !locked()]
      box.hidden = false
      await frames()
      document.getElementById('hc-trigger').click()
      await frames()
      out.ddOpened = document.getElementById('hc-dd').matches(':popover-open') && locked()
      box.hidden = true
      await frames()
      await new Promise(r => setTimeout(r, 400))
      out.ddClosed = [!document.getElementById('hc-dd').matches(':popover-open'), !locked()]
      box.remove()
      return out
    }""")
    assert result["dialogOpened"] and result["boxOpened"] and result["ddOpened"], result
    assert result["dialogClosed"] == [True, True, True], ("closing a dialog closes the menus in it first: no aria-hidden and no scroll lock stay", result)
    assert result["boxClosed"] == [True, True, True], ("a context menu whose container gets hidden closes and gives the page back", result)
    assert result["ddClosed"] == [True, True], ("a dropdown menu whose container gets hidden closes and unlocks scroll", result)


def check_popup_collision(t):
    page = t.page
    result = page.evaluate("""async () => {
      const { position } = await import("/clanker-ui.js")
      const rtl = getComputedStyle(document.body).direction === "rtl"
      const vw = document.documentElement.clientWidth
      const make = css => { const e = document.createElement("div"); Object.assign(e.style, { position: "fixed", ...css }); document.body.append(e); return e }
      const pop = css => { const e = make(css); e.setAttribute("popover", "manual"); e.showPopover(); return e }
      const anchor = make({ left: rtl ? "20px" : `${vw - 60}px`, top: "120px", width: "40px", height: "20px" })
      const floating = pop({ width: "200px", height: "50px", padding: "0", border: "0" })
      let stop = position(floating, anchor, { side: "bottom", align: "start", sideOffset: 4, alignOffset: 0, collisionPadding: 5 })
      const a = anchor.getBoundingClientRect(), f = floating.getBoundingClientRect()
      const align = { align: floating.dataset.align, edge: rtl ? Math.abs(f.left - a.left) : Math.abs(f.right - a.right) }
      stop()
      const middle = make({ left: `${vw / 2 - 20}px`, top: "120px", width: "40px", height: "28px" })
      const wide = pop({ width: `${Math.round(vw / 2 - 10)}px`, height: "60px", padding: "0", border: "0" })
      stop = position(wide, middle, { side: rtl ? "left" : "right", align: "start", sideOffset: 0, alignOffset: 4, collisionPadding: 5 })
      const m = middle.getBoundingClientRect(), w = wide.getBoundingClientRect()
      const side = { side: wide.dataset.side, top: Math.abs(w.top - m.bottom), start: rtl ? Math.abs(w.right - (m.right - 4)) : Math.abs(w.left - (m.left + 4)) }
      stop()
      for (const e of [anchor, floating, middle, wide]) e.remove()
      return { align, side }
    }""")
    assert result["align"]["align"] == "end" and result["align"]["edge"] <= 1, ("start alignment that overflows flips to end, as in Base UI", result)
    assert result["side"]["side"] == "bottom" and result["side"]["top"] <= 1 and result["side"]["start"] <= 1, ("a side popup with no room on either side goes below, as in Base UI", result)


def check_drawer_detached(t):
    page = t.page
    page.add_init_script(TOUCH_LISTENERS)
    page.reload(wait_until="load")
    section = t.section("drawer")
    start = section.get_by_role("button", name="Open Drawer").first
    for attrs in [{}, {"data-modal": "trap-focus"}]:
        drawer_build(page, attrs, False)
        page.locator("#built [data-drawer-trigger]").click()
        wait(page, "() => document.querySelector('#built dialog').open")
        assert page.evaluate("window.__touchListeners.size") == 1
        page.evaluate("() => document.getElementById('built').remove()")
        page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        assert page.evaluate("window.__touchListeners.size") == 0, ("an open drawer that leaves the document drops its touch listener", attrs)
        if t.engine == "chromium":
            cdp = page.context.new_cdp_session(page)
            doc = cdp.send("Runtime.evaluate", {"expression": "document"})["result"]["objectId"]
            listeners = [l for l in cdp.send("DOMDebugger.getEventListeners", {"objectId": doc})["listeners"] if l["type"] == "touchmove" and not l["passive"]]
            cdp.detach()
            assert listeners == [], listeners
        start.focus()
        page.keyboard.press("Tab")
        assert page.evaluate("() => document.activeElement !== document.querySelector('#drawer [data-drawer-trigger]') && document.activeElement !== document.body"), ("Tab still moves focus after an open drawer left the document", attrs, active(page, "e => e.outerHTML.slice(0, 80)"))


def check_toast_detached(t):
    page = t.page
    section = t.section("toast")
    toast_api(page)
    page.evaluate("() => window.__toast.add({ title: 'Detached', timeout: 300 })")
    page.locator("[data-slot=toast]").filter(has_text="Detached").wait_for()
    page.evaluate("() => document.querySelectorAll('[data-slot=toast-portal]').forEach(e => e.remove())")
    page.wait_for_timeout(800)
    start = section.get_by_role("button").first
    start.focus()
    page.evaluate("() => { window.__f6 = null; addEventListener('keydown', e => { if (e.key === 'F6') window.__f6 = e.defaultPrevented }, { once: true }) }")
    page.keyboard.press("F6")
    result = page.evaluate("() => [window.__f6, document.querySelectorAll('[data-slot=toast-portal]').length, window.__toast.getToasts().length]")
    assert result == [False, 0, 0], ("toasts that left the document do not capture F6 or bring back a portal", result)
    assert start.evaluate("e => e === document.activeElement"), "F6 leaves focus where it was"
    page.evaluate("() => window.__toast.add({ title: 'Again' })")
    page.locator("[data-slot=toast]").filter(has_text="Again").wait_for()
    assert page.locator("[data-slot=toast-portal]").count() == 1
