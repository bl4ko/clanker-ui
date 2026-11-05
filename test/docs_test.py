import json
import re

START = "/docs/components/button"

LAYOUT = """() => {
  const box = selector => {
    const el = document.querySelector(selector)
    if (!el || getComputedStyle(el).display === "none") return null
    const r = el.getBoundingClientRect()
    return { x: Math.round(r.x * 10) / 10, y: Math.round(r.y * 10) / 10, w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 }
  }
  const items = [...document.querySelectorAll('[data-docs="sidebar"] [data-slot="sidebar-group"]')].map(group =>
    [...group.querySelectorAll('[data-slot="sidebar-menu-button"]')].slice(0, 2).map(a => a.getBoundingClientRect().top))
  const preview = document.querySelector('[data-docs="preview"]')
  const frame = document.querySelector('[data-docs="component-preview"]')
  return {
    header: box('[data-docs="header"]'),
    menu: box('[data-docs="menu-trigger"]'),
    nav: box('[data-docs="main-nav"]'),
    search: box('[data-docs="search-trigger"]'),
    sidebar: box('[data-docs="sidebar"]'),
    sidebarContent: box('[data-docs-sidebar-content]'),
    item: box('[data-docs="sidebar"] [aria-current="page"]'),
    article: box('[data-docs="article"]'),
    toc: box('[data-docs="toc-rail"]'),
    title: box('[data-docs="title"]'),
    preview: box('[data-docs="preview"]'),
    previewPadding: getComputedStyle(preview).paddingTop,
    frameRadius: getComputedStyle(frame).borderTopLeftRadius,
    sectionsGap: items[0].length > 1 ? Math.round(items[0][1] - items[0][0]) : null,
    groupGap: items[1]?.length > 1 ? Math.round(items[1][1] - items[1][0]) : null,
    scrollWidth: document.documentElement.scrollWidth,
  }
}"""


def run_once(t):
    if not (t.engine == "chromium" and t.theme == "light" and t.width == 1280):
        t.skip("HTTP check runs once per suite run")


def save(t, name, data):
    folder = t.out / t.engine / f"{t.theme}-{t.width}" / "docs"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.json").write_text(json.dumps(data, indent=2))


def check_docs_layout(t):
    page = t.page
    m = page.evaluate(LAYOUT)
    save(t, "layout", m)
    assert m["scrollWidth"] == t.width
    assert m["header"]["h"] == (64 if t.width >= 1024 else 56)
    assert m["preview"]["h"] == 288
    assert m["previewPadding"] == "40px"
    assert m["frameRadius"] == "18px"
    if t.width >= 1280:
        assert m["menu"] is None and m["nav"] is not None
        assert m["search"]["w"] == 256 and m["search"]["h"] == 32
        assert m["sidebar"]["w"] == 288
        assert m["sidebarContent"]["w"] == 224
        assert m["item"]["h"] == 30
        assert m["sectionsGap"] == 34 and m["groupGap"] == 32
        assert m["article"]["w"] == 640
        assert m["toc"]["w"] == 288
        main_left, main_right = (m["sidebar"]["x"] + 288, m["toc"]["x"]) if not t.rtl else (m["toc"]["x"] + 288, m["sidebar"]["x"])
        assert abs((m["article"]["x"] - main_left) - (main_right - m["article"]["x"] - 640)) <= 1
    else:
        assert m["menu"] is not None and m["nav"] is None and m["search"] is None
        assert m["sidebar"] is None and m["toc"] is None
        assert m["article"]["w"] == t.width - 16
    t.shot("button-page", page)


def check_docs_sidebar(t):
    if t.width < 1024:
        t.skip("the docs sidebar shows from 1024 px")
    page = t.page
    sidebar = page.locator('[data-docs="sidebar"]')
    assert [s.strip() for s in sidebar.locator('[data-active="true"]').all_inner_texts()] == ["Components", "Button"]
    assert [s.strip() for s in sidebar.locator('[aria-current="page"]').all_inner_texts()] == ["Button"]
    labels = [s.strip() for s in sidebar.locator('[data-slot="sidebar-group-label"]').all_inner_texts()]
    assert labels == ["Sections", "Components", "Blocks", "Get Started", "Utilities", "clanker-ui"]
    assert sidebar.locator('a[href="/docs"]').count() == 1
    styles = page.evaluate("""() => {
      const a = document.querySelector('[data-docs="sidebar"] [aria-current="page"]')
      const plain = document.querySelector('[data-docs="sidebar"] a[href="/docs/components/badge"]')
      const css = el => { const s = getComputedStyle(el); return [s.backgroundColor, s.borderTopColor, s.fontSize, s.fontWeight] }
      return { active: css(a), plain: css(plain) }
    }""")
    assert styles["active"][0] == styles["active"][1] and styles["active"][0] != "rgba(0, 0, 0, 0)"
    assert styles["plain"][0] == "rgba(0, 0, 0, 0)"
    assert abs(float(styles["active"][2].removesuffix("px")) - 12.8) < 0.01 and styles["active"][3] == "500"
    target = sidebar.locator('a[href="/docs/components/calendar"]')
    target.scroll_into_view_if_needed()
    target.hover()
    page.wait_for_function("""() => document.querySelector('link[rel="prefetch"][href="/docs/components/calendar"]')""", timeout=2000)


SECTION_MARKS = """() => [...document.querySelectorAll('[data-docs="sidebar"] a')]
  .filter(a => a.dataset.active === "true" || a.hasAttribute("aria-current"))
  .map(a => [a.closest('[data-slot="sidebar-group"]').querySelector('[data-slot="sidebar-group-label"]').textContent.trim(), a.getAttribute("href"), a.dataset.active ?? null, a.getAttribute("aria-current")])"""


def check_docs_section_active(t):
    if t.width < 1024:
        t.skip("the docs sidebar shows from 1024 px")
    page = t.page
    t.docs("/docs/components/typography")
    assert page.evaluate(SECTION_MARKS) == [["Sections", "/docs/typography", "true", "page"], ["Get Started", "/docs/typography", "true", "page"]]
    assert page.url == t.base_url + "/docs/typography", page.url


SIDEBAR_FRAMES = """() => {
  if (window.__docsSampler || sessionStorage.getItem("docs-frames") === null) return
  window.__docsSampler = true
  let probe = null
  let n = 0
  const sample = () => {
    const el = document.querySelector("[data-docs-sidebar-content]")
    const raw = sessionStorage.getItem("docs-frames")
    if (!el || raw === null) return
    const frames = JSON.parse(raw)
    frames.push([location.pathname, el.scrollTop, document.querySelector('[data-docs="sidebar"] [aria-current="page"]')?.getAttribute("href") ?? null])
    sessionStorage.setItem("docs-frames", JSON.stringify(frames))
  }
  const observer = new ResizeObserver(sample)
  const tick = () => {
    if (!probe && document.body) {
      probe = document.createElement("div")
      probe.setAttribute("aria-hidden", "true")
      Object.assign(probe.style, { position: "fixed", left: "-10px", top: "-10px", width: "1px", height: "1px", pointerEvents: "none" })
      document.documentElement.append(probe)
      observer.observe(probe)
    }
    if (probe) probe.style.width = `${++n % 2 + 1}px`
    if (sessionStorage.getItem("docs-frames") !== null) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}"""


def active_visible(page):
    return page.evaluate("""() => {
      const box = document.querySelector("[data-docs-sidebar-content]").getBoundingClientRect()
      return [...document.querySelectorAll('[data-docs="sidebar"] [data-active="true"]')].some(a => {
        const r = a.getBoundingClientRect()
        return r.top >= box.top && r.bottom <= box.bottom
      })
    }""")


def check_docs_sidebar_scroll_restore(t):
    if t.width < 1024:
        t.skip("the docs sidebar shows from 1024 px")
    page = t.page
    content = page.locator("[data-docs-sidebar-content]")
    stored = content.evaluate("el => { el.scrollTop = 900; return el.scrollTop }")
    assert stored > 0
    page.wait_for_function("n => JSON.parse(sessionStorage.getItem('docs-sidebar-scroll') || '{}').scrollTop === n", arg=stored)
    href = page.evaluate("""() => {
      const box = document.querySelector("[data-docs-sidebar-content]").getBoundingClientRect()
      const middle = box.top + box.height / 2
      const links = [...document.querySelectorAll('[data-docs="sidebar"] a[href^="/docs/components/"]:not([aria-current])')]
      return links.find(a => a.getBoundingClientRect().top >= middle)?.getAttribute("href")
    }""")
    assert href
    page.evaluate("() => sessionStorage.setItem('docs-frames', '[]')")
    page.add_init_script(f"({SIDEBAR_FRAMES})()")
    page.evaluate(SIDEBAR_FRAMES)
    page.wait_for_function("() => JSON.parse(sessionStorage.getItem('docs-frames')).length >= 2")
    page.locator(f'[data-docs="sidebar"] a[href="{href}"]').first.click()
    page.wait_for_url("**" + href)
    page.wait_for_load_state("load")
    page.wait_for_function("h => JSON.parse(sessionStorage.getItem('docs-frames')).filter(f => f[0] === h).length >= 3", arg=href)
    frames = page.evaluate("() => { const f = JSON.parse(sessionStorage.getItem('docs-frames')); sessionStorage.removeItem('docs-frames'); return f }")
    old_frames = [f for f in frames if f[0] != href]
    new_frames = [f for f in frames if f[0] == href]
    assert old_frames and new_frames, frames
    assert {f[1] for f in frames} == {stored}, frames
    assert {f[2] for f in new_frames} == {href}, new_frames
    assert content.evaluate("el => el.scrollTop") == stored
    assert page.locator('[data-docs="sidebar"] [aria-current="page"]').first.get_attribute("href") == href
    t.docs("/docs/components/tooltip")
    assert active_visible(page)
    top = content.evaluate("el => el.scrollTop")
    assert top != stored
    page.reload(wait_until="load")
    assert content.evaluate("el => el.scrollTop") == top


def check_docs_scroll_fade(t):
    if t.width < 1024:
        t.skip("the docs sidebar shows from 1024 px")
    page = t.page
    result = page.evaluate("""async () => {
      const el = document.querySelector("[data-docs-sidebar-content]")
      const size = value => {
        const box = document.createElement("div")
        const probe = document.createElement("div")
        Object.assign(box.style, { position: "absolute", width: "200px", visibility: "hidden" })
        probe.style.width = value
        box.append(probe)
        document.body.append(box)
        const width = probe.getBoundingClientRect().width
        box.remove()
        return width
      }
      const read = () => { const s = getComputedStyle(el); return [size(s.getPropertyValue("--scroll-fade-t")), size(s.getPropertyValue("--scroll-fade-b")), s.maskImage || s.webkitMaskImage] }
      const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
      el.scrollTop = 0
      await frame()
      const top = read()
      el.scrollTop = el.scrollHeight / 2
      await frame()
      const middle = read()
      el.scrollTop = el.scrollHeight
      await frame()
      const end = read()
      return { timeline: CSS.supports("animation-timeline: scroll()"), top, middle, end, toc: getComputedStyle(document.querySelector('[data-docs="toc-scroller"]')).maskImage }
    }""")
    save(t, "scroll-fade", result)
    assert "linear-gradient" in result["top"][2]
    if result["timeline"]:
        assert result["top"][0] == 0 and result["top"][1] > 0
        assert result["middle"][0] > 0 and result["middle"][1] > 0
        assert result["end"][0] > 0 and result["end"][1] == 0
    else:
        assert result["top"][:2] == [0, 0] and result["middle"][:2] == [0, 0]


def check_scroll_fade_popup_closes(t):
    page = t.page
    frame = page.locator('[data-example="button-group-demo"]')
    frame.scroll_into_view_if_needed()
    content = frame.locator('[data-slot="dropdown-menu-content"]')
    content.evaluate("el => { el.classList.add('scroll-fade'); el.style.maxHeight = '7rem'; el.style.overflowY = 'auto' }")
    frame.locator("[data-dropdown-menu-trigger]").click()
    page.wait_for_function("""() => document.querySelector('[data-example="button-group-demo"] [data-slot="dropdown-menu-content"]').dataset.state === "open" """)
    result = content.evaluate("""el => ({ mask: getComputedStyle(el).maskImage || getComputedStyle(el).webkitMaskImage, scrollable: el.scrollHeight > el.clientHeight, timeline: el.getAnimations().some(a => a.timeline !== document.timeline) })""")
    assert result["scrollable"] and "linear-gradient" in result["mask"], result
    page.keyboard.press("Escape")
    page.wait_for_function("""() => {
      const el = document.querySelector('[data-example="button-group-demo"] [data-slot="dropdown-menu-content"]')
      return el.dataset.state === "closed" && !el.matches(":popover-open") && getComputedStyle(el).display === "none"
    }""", timeout=2000)


def check_docs_toc(t):
    if t.width < 1280:
        t.skip("On This Page shows from 1280 px")
    page = t.page
    toc = page.locator('[data-docs="toc"]')
    assert toc.locator("a").first.get_attribute("href") == "#installation"
    assert toc.locator('a[data-depth="3"]').count() == 2
    page.evaluate("() => document.getElementById('outline').scrollIntoView({ block: 'start' })")
    page.wait_for_function("""() => document.querySelector('[data-docs="toc"] a[href="#outline"]').dataset.active === "true" """, timeout=3000)
    assert toc.locator('a[data-active="true"]').count() == 1
    weight = toc.locator('a[href="#outline"]').evaluate("el => getComputedStyle(el).fontWeight")
    assert weight == "500"
    toc.locator('a[href="#rounded"]').click()
    page.wait_for_function("""() => document.querySelector('[data-docs="toc"] a[href="#rounded"]').dataset.active === "true" """, timeout=3000)
    top = page.evaluate("() => document.getElementById('rounded').getBoundingClientRect().top")
    assert 64 <= top <= 64 + 40, top
    assert page.url.endswith("#rounded")
    t.shot("toc", page)


SEARCH_CLOSED = """() => {
  const dialog = document.querySelector('[data-docs="search-dialog"]')
  return dialog.dataset.state !== "open" && !dialog.open && !dialog.contains(document.activeElement)
}"""


def search_open(page):
    return page.evaluate("""() => document.querySelector('[data-docs="search-dialog"]').dataset.state === "open" """)


def check_docs_search(t):
    page = t.page
    dialog = page.locator('[data-docs="search-dialog"]')
    page.keyboard.press("/")
    page.wait_for_function("""() => document.querySelector('[data-docs="search-dialog"]').dataset.state === "open" """)
    assert page.evaluate("() => document.activeElement?.dataset.slot") == "command-input"
    box = dialog.bounding_box()
    assert abs(box["y"] - 0.15 * page.viewport_size["height"]) <= 1
    assert box["width"] == (512 if t.width >= 640 else t.width - 32)
    page.keyboard.type("button")
    page.wait_for_function("""() => document.querySelector('#docs-search [data-slot="command-item"][data-selected="true"]')?.textContent.trim() === "Button" """)
    t.shot("search", page)
    page.keyboard.press("Escape")
    page.wait_for_function(SEARCH_CLOSED)
    page.keyboard.press("Meta+k")
    page.wait_for_function("""() => document.querySelector('[data-docs="search-dialog"]').dataset.state === "open" """)
    assert page.locator('#docs-search [data-slot="command-input"]').input_value() == ""
    page.keyboard.press("Escape")
    page.wait_for_function(SEARCH_CLOSED)
    page.keyboard.press("Control+k")
    page.wait_for_function("""() => document.querySelector('[data-docs="search-dialog"]').dataset.state === "open" """)
    page.keyboard.type("accordion")
    page.wait_for_function("""() => document.querySelector('#docs-search [data-slot="command-item"][data-selected="true"]')?.getAttribute("href") === "/docs/components/accordion" """)
    page.keyboard.press("Enter")
    page.wait_for_url("**/docs/components/accordion")
    page.wait_for_load_state("load")
    assert page.locator('[data-docs="title"]').inner_text() == "Accordion"
    assert not search_open(page)
    if t.width >= 768:
        page.locator('[data-docs="search-trigger"]').click()
        page.wait_for_function("""() => document.querySelector('[data-docs="search-dialog"]').dataset.state === "open" """)
        page.keyboard.press("Escape")


def check_docs_copy_page(t):
    if t.width < 640:
        t.skip("Copy Page shows from 640 px")
    page = t.page
    expected = page.request.get(t.base_url + "/docs/components/button.md").text()
    if t.engine == "chromium":
        page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=t.base_url)
    button = page.locator('[data-docs="copy-page-button"]')
    button.click()
    try:
        page.wait_for_function("""() => document.querySelector('[data-docs="copy-page-button"]').hasAttribute("data-copied")""", timeout=3000)
    except Exception:
        if t.engine == "chromium":
            raise
        t.skip(f"{t.engine} gives no clipboard write to headless pages")
    assert button.locator('[data-lucide="check"]').is_visible()
    if t.engine == "chromium":
        assert page.evaluate("() => navigator.clipboard.readText()") == expected
    page.wait_for_function("""() => !document.querySelector('[data-docs="copy-page-button"]').hasAttribute("data-copied")""", timeout=4000)
    page.locator('[data-docs="copy-page-menu"]').click()
    item = page.locator('[data-docs="copy-page-content"] [data-slot="dropdown-menu-item"]')
    item.wait_for(state="visible")
    assert item.get_attribute("href") == "/docs/components/button.md"
    assert item.get_attribute("target") == "_blank"
    assert item.inner_text().strip() == "View as Markdown"
    t.shot("copy-page-menu", page)
    page.keyboard.press("Escape")


def check_docs_markdown_route(t):
    run_once(t)
    request = t.page.request
    r = request.get(t.base_url + "/docs/components/button.md")
    assert r.status == 200
    assert r.headers["content-type"] == "text/markdown; charset=utf-8"
    text = r.text()
    assert text.startswith("---\ntitle: Button\ndescription: Displays a button or a component that looks like a button.\n---\n\n```html\n")
    assert "{{" not in text
    assert '```html\n<div class="flex flex-wrap items-center gap-2">\n  <button type="button" data-slot="button" data-variant="outline">Button</button>' in text
    assert text.count("```html") == 16
    assert "## API Reference" in text
    assert request.get(t.base_url + "/docs.md").status == 200
    accordion = request.get(t.base_url + "/docs/components/accordion.md").text()
    assert accordion.startswith("---\ntitle: Accordion\n") and "## API Reference" in accordion and "```html\n" in accordion and "not ported yet" not in accordion
    installation = request.get(t.base_url + "/docs/installation.md").text()
    assert "## Override the kit" in installation and "not ported yet" not in installation
    components = request.get(t.base_url + "/docs/components.md").text()
    assert "- [Accordion](/docs/components/accordion.md)" in components and "- [Typography](/docs/typography.md)" in components
    assert request.get(t.base_url + "/llms.txt").status == 200


def check_docs_prev_next(t):
    page = t.page
    prev = page.locator('[data-docs="neighbours"] [data-docs="prev"]')
    nxt = page.locator('[data-docs="neighbours"] [data-docs="next"]')
    assert prev.get_attribute("href") == "/docs/components/bubble"
    assert nxt.get_attribute("href") == "/docs/components/button-group"
    assert prev.inner_text().strip() == "Previous" and nxt.inner_text().strip() == "Next"
    size = 28 if t.width >= 768 else 32
    assert prev.bounding_box()["width"] == size and prev.bounding_box()["height"] == size
    bottom = page.locator('[data-docs="bottom-nav"]')
    if t.width >= 640:
        assert [s.strip() for s in bottom.locator("a").all_inner_texts()] == ["Bubble", "Button Group"]
    else:
        assert not bottom.is_visible()
    nxt.click()
    page.wait_for_url("**/docs/components/button-group")
    page.wait_for_load_state("load")
    assert page.locator('[data-docs="neighbours"] [data-docs="prev"]').get_attribute("href") == "/docs/components/button"
    t.docs("/docs/components")
    assert page.locator('[data-docs="neighbours"] [data-docs="prev"]').count() == 0
    assert page.locator('[data-docs="neighbours"] [data-docs="next"]').get_attribute("href") == "/docs/components/accordion"


def check_docs_mobile_menu(t):
    if t.width >= 1024:
        t.skip("the menu button shows below 1024 px")
    page = t.page
    trigger = page.locator('[data-docs="menu-trigger"]')
    trigger.click()
    page.wait_for_function("""() => document.querySelector('[data-docs="menu"]').dataset.state === "open" """)
    t.settle()
    box = page.locator('[data-docs="menu"]').bounding_box()
    header = page.locator('[data-docs="header"]').bounding_box()
    view = page.viewport_size
    assert abs(box["y"] - (header["y"] + header["height"])) <= 14
    assert box["width"] >= view["width"] - 16 and box["y"] + box["height"] <= view["height"]
    bar = page.evaluate("""() => getComputedStyle(document.querySelector('[data-docs="hamburger"] > span')).rotate""")
    assert bar == "-45deg"
    labels = [s.strip() for s in page.locator('[data-docs="menu-label"]').all_inner_texts()]
    assert labels[:3] == ["Menu", "Sections", "Components"]
    t.shot("menu", page)
    link = page.locator('[data-docs="menu"] a[href="/docs/components/accordion"]')
    link.scroll_into_view_if_needed()
    link.click()
    page.wait_for_url("**/docs/components/accordion")
    page.wait_for_load_state("load")
    assert page.locator('[data-docs="menu"]').get_attribute("data-state") != "open"
    assert page.locator('[data-docs="title"]').inner_text() == "Accordion"


def check_docs_view_csp(t):
    run_once(t)
    request = t.page.request
    view = request.get(t.base_url + "/view/button-demo").headers["content-security-policy"]
    docs = request.get(t.base_url + "/docs/components/button").headers["content-security-policy"]
    assert "frame-ancestors 'self'" in view.split("; ")
    assert "frame-ancestors 'none'" in docs.split("; ")
    strip = lambda policy: [d for d in policy.split("; ") if not d.startswith("frame-ancestors")]
    assert strip(view) == strip(docs)
    assert request.get(t.base_url + "/view/nope").status == 404


def check_docs_view_page(t):
    page = t.page
    t.docs("/view/button-demo")
    assert page.locator('[data-slot="button"]').count() == 2
    assert page.locator('[data-docs="header"]').count() == 0
    t.shot("view", page)


def check_docs_view_code(t):
    page = t.page
    frame = page.locator('[data-example="button-demo"]')
    teaser = frame.locator('[data-docs="code-teaser"] [data-line]')
    assert teaser.count() == 3
    content = frame.locator('[data-slot="collapsible-content"]')
    assert not content.is_visible()
    frame.get_by_role("button", name="View Code").click()
    page.wait_for_function("""() => document.querySelector('[data-example="button-demo"] [data-docs="code"]').dataset.state === "open" """)
    assert content.is_visible() and not frame.locator('[data-docs="code-teaser"]').is_visible()
    assert page.evaluate("() => document.activeElement?.dataset.slot") == "code-block-content"
    code = frame.locator('[data-slot="code-block-content"]')
    assert code.inner_text().startswith('<div class="flex flex-wrap items-center gap-2">')
    assert frame.locator(".tk-t").count() > 0 and frame.locator(".tk-a").count() > 0
    assert code.evaluate("el => parseFloat(getComputedStyle(el).maxHeight)") == 288
    copy_box = frame.locator('[data-slot="code-block-copy-button"]').bounding_box()
    code_box = code.bounding_box()
    assert copy_box["x"] + copy_box["width"] > code_box["x"] + code_box["width"] - 40, (copy_box, code_box)
    if t.engine == "chromium":
        page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=t.base_url)
        frame.locator('[data-slot="code-block-copy-button"]').click()
        page.wait_for_function("""() => document.querySelector('[data-example="button-demo"] [data-slot="code-block-copy-button"]').hasAttribute("data-copied")""")
        source = page.request.get(t.base_url + "/docs/components/button.md").text().split("```html\n", 1)[1].split("\n```", 1)[0]
        assert page.evaluate("() => navigator.clipboard.readText()") == source
    t.shot("view-code", frame)


def check_docs_pages(t):
    page = t.page
    t.docs("/")
    assert page.locator('[data-docs="hero-title"]').is_visible()
    assert page.locator('[data-docs="footer"]').is_visible()
    t.shot("home", page)
    t.docs("/docs")
    assert page.locator('[data-docs="title"]').inner_text() == "Introduction"
    assert page.locator('[data-docs="neighbours"] [data-docs="next"]').get_attribute("href") == "/docs/installation"
    t.shot("introduction", page)
    t.docs("/docs/components")
    lists = page.locator('[data-docs="components-list"]')
    assert lists.nth(0).locator("a").count() == 2
    assert lists.nth(1).locator("a").count() == 67
    t.shot("components", page)
    t.docs("/docs/components/accordion")
    assert "not ported yet" not in page.locator('[data-docs="article"]').inner_text()
    assert page.locator('#accordion [data-docs="preview"] [data-slot="accordion"]').count() > 0
    assert page.locator('link[rel="alternate"][type="text/markdown"]').get_attribute("href") == "/docs/components/accordion.md"
    assert page.locator('link[rel="describedby"]').get_attribute("href") == "/llms.txt"
    t.docs("/docs/installation")
    assert page.locator('[data-docs="content"] h2', has_text="Override the kit").count() == 1
    t.docs("/docs/components/native-select")
    assert page.locator('[data-docs="copy-page-button"]').count() == 1
    assert page.locator('[data-docs="preview"] select[data-slot="native-select"]').count() == 5
    assert page.request.get(t.base_url + "/blocks").status == 404
    assert page.request.get(t.base_url + "/docs/nope").status == 404
    t.docs("/demo")
    assert page.locator("#button").count() == 1


KIT_PROPS = ["marginTop", "marginBottom", "marginInlineStart", "lineHeight", "listStyleType", "paddingInlineStart", "paddingTop", "paddingBottom", "textDecorationLine", "fontWeight", "fontSize", "fontFamily", "fontStyle", "letterSpacing", "backgroundColor", "borderTopLeftRadius", "borderTopWidth", "color", "display", "gap", "whiteSpace"]

KIT_SNAPSHOT = """props => {
  const out = []
  for (const el of document.querySelectorAll('main section [data-slot], main section [data-slot] *')) {
    const cs = getComputedStyle(el)
    if (cs.display === "contents") {
      out.push(null)
      continue
    }
    out.push([el.closest('[data-slot]').getAttribute('data-slot') + (el.hasAttribute('data-slot') ? '' : ' > ' + el.localName), ...props.map(p => cs[p])])
  }
  return out
}"""


def check_docs_preview_keeps_kit_styles(t):
    page = t.page
    href = page.locator('link[href$="/docs.css"]').get_attribute("href")
    t.docs("/demo")
    page.evaluate("""() => {
      Object.assign(document.body.style, { fontSize: "16px", lineHeight: "1.5" })
      document.querySelector("main").setAttribute("data-docs", "content")
      for (const section of document.querySelectorAll("main section")) {
        const wrap = document.createElement("div")
        wrap.setAttribute("data-docs", "preview")
        Object.assign(wrap.style, { display: "block", height: "auto", padding: "0" })
        wrap.append(...section.childNodes)
        section.append(wrap)
      }
    }""")
    load = """href => new Promise((resolve, reject) => {
      const link = document.createElement("link")
      link.rel = "stylesheet"
      link.href = href
      link.onload = resolve
      link.onerror = reject
      document.head.append(link)
    })"""
    page.evaluate(load, "/clanker-ui.css")
    t.settle(5000)
    before = page.evaluate(KIT_SNAPSHOT, KIT_PROPS)
    page.evaluate(load, href)
    t.settle(5000)
    after = page.evaluate(KIT_SNAPSHOT, KIT_PROPS)
    assert len(before) == len(after) and len(before) > 1000
    changes = sorted({(a[0], prop, a[1 + i], b[1 + i]) for a, b in zip(before, after) if a and b for i, prop in enumerate(KIT_PROPS) if a[1 + i] != b[1 + i]})
    save(t, "kit-style-changes", changes)
    assert changes == [], f"{len(changes)} kit style changes, first: {changes[:5]}"


def check_docs_text_metrics(t):
    page = t.page
    m = page.evaluate("""() => {
      const cs = s => getComputedStyle(document.querySelector(s))
      const lines = [...document.querySelectorAll('[data-example="button-size"] [data-docs="code-teaser"] [data-line]')]
      const number = getComputedStyle(lines[1], "::before")
      return {
        p: cs('[data-docs="content"] > p').fontSize,
        h2: cs('[data-docs="content"] > h2').fontSize,
        preview: cs('[data-docs="preview"]').fontSize,
        pitch: Math.round((lines[2].getBoundingClientRect().top - lines[1].getBoundingClientRect().top) * 10) / 10,
        lineHeight: cs('[data-docs="code-teaser"] pre').lineHeight,
        teaser: Math.round(document.querySelector('[data-example="button-size"] [data-docs="code-teaser"] pre').getBoundingClientRect().height * 10) / 10,
        numberWidth: number.width,
        numberColor: number.color === getComputedStyle(document.documentElement).getPropertyValue("--code-number") || number.color,
        numberText: number.content,
        copied: lines.map(l => l.textContent).join("\\n").startsWith('<div class="flex flex-col'),
      }
    }""")
    save(t, "text-metrics", m)
    want = (18.9, 23.625) if t.width < 640 else (15, 18.75)
    assert abs(float(m["p"].removesuffix("px")) - want[0]) < 0.01 and abs(float(m["h2"].removesuffix("px")) - want[1]) < 0.01, (m["p"], m["h2"])
    assert m["preview"] == "16px"
    assert m["lineHeight"] == "24.5px" and m["pitch"] == 26.5
    assert m["teaser"] == 107.5
    assert m["numberWidth"] == "64px" and "counter(line)" in m["numberText"]
    assert m["copied"]


def check_scroll_fade_options(t):
    page = t.page
    result = page.evaluate("""async () => {
      const el = document.createElement("button")
      el.setAttribute("data-slot", "button")
      el.className = "scroll-fade"
      el.textContent = "x"
      document.body.append(el)
      const box = document.createElement("div")
      box.className = "scroll-fade"
      Object.assign(box.style, { height: "100px", overflowY: "auto" })
      box.style.setProperty("--scroll-fade-b-size", "10px")
      const inner = document.createElement("div")
      inner.style.height = "400px"
      box.append(inner)
      document.body.append(box)
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
      const probe = document.createElement("div")
      probe.style.width = getComputedStyle(box).getPropertyValue("--scroll-fade-b")
      document.body.append(probe)
      const bottom = probe.getBoundingClientRect().width
      box.style.setProperty("--scroll-fade-mask", "none")
      const mask = getComputedStyle(box).maskImage || getComputedStyle(box).webkitMaskImage
      const cs = getComputedStyle(el)
      const out = { timeline: CSS.supports("animation-timeline: scroll()"), transition: cs.transitionDuration, animation: cs.animationName, bottom, mask }
      el.remove(); box.remove(); probe.remove()
      return out
    }""")
    save(t, "scroll-fade-options", result)
    assert result["mask"] == "none"
    if result["timeline"]:
        assert result["bottom"] == 10
        assert "clanker-scroll-fade-start" in result["animation"]
    if t.reduced_motion:
        assert result["transition"].split(",")[0].strip() == "0s", result["transition"]
    else:
        assert result["transition"].split(",")[0].strip() != "0s", result["transition"]


def check_docs_new_dot_has_text(t):
    page = t.page
    dots = page.evaluate("""() => [...document.querySelectorAll('[data-docs="new-dot"]')].map(d => [d.getAttribute("aria-hidden"), d.previousElementSibling?.matches(".sr-only") ? d.previousElementSibling.textContent : null])""")
    assert len(dots) >= 4
    assert all(d == ["true", "New"] for d in dots), dots
    if t.width >= 1024:
        link = page.locator('[data-docs="sidebar"] a[href="/docs/components/code-block"]')
        assert link.inner_text().replace("\n", "").strip() == "Code BlockNew"


def check_docs_theme_toggle(t):
    page = t.page
    dark = t.theme == "dark"
    toggle = page.locator('[data-docs="header"] [data-theme-set="toggle"]')
    is_dark = "getComputedStyle(document.documentElement).colorScheme === 'dark'"
    meta = "document.querySelector('meta[name=theme-color]').content === getComputedStyle(document.body).backgroundColor"
    assert toggle.get_attribute("aria-label") == "Dark mode" and toggle.get_attribute("aria-keyshortcuts") == "D"
    assert toggle.get_attribute("aria-pressed") == str(dark).lower()
    box = toggle.bounding_box()
    assert [box["width"], box["height"]] == [32, 32], box
    assert toggle.locator("svg.lucide-contrast").evaluate("s => [s.getBoundingClientRect().width, getComputedStyle(s.lastElementChild).fill !== 'none']") == [18, True]
    assert page.evaluate(meta)
    page.evaluate("document.activeElement?.blur()")
    page.keyboard.press("d")
    assert page.evaluate(is_dark) != dark and toggle.get_attribute("aria-pressed") == str(not dark).lower(), "D must toggle the theme on the docs site"
    assert page.evaluate(meta)
    toggle.click()
    assert page.evaluate(is_dark) == dark and page.evaluate("localStorage.getItem('clanker-ui-theme')") == ("dark" if dark else "light")
    page.reload(wait_until="load")
    assert page.evaluate(is_dark) == dark and page.evaluate(meta)


def check_docs_code_block_preview(t):
    page = t.page
    t.docs("/docs/components/code-block")
    page.wait_for_function("""() => document.querySelectorAll('#code-block-header [data-token]').length > 20""")
    got = page.evaluate("""() => {
      const pad = el => getComputedStyle(el).paddingInlineStart
      const demo = document.querySelector('#code-block-header [data-slot="code-block-content"]')
      const start = document.querySelector('#code-block-lines [data-start-line] [data-slot="code-block-code"]')
      const view = document.querySelector('[data-docs="code"] [data-slot="code-block-content"]')
      return [pad(demo), getComputedStyle(start).counterReset, pad(view)]
    }""")
    assert got == ["12px", "none", "0px"], got


def check_docs_component_demos(t):
    page = t.page
    t.docs("/docs/components/dialog")
    trigger = page.locator('#dialog [data-docs="preview"] [data-dialog-trigger]').first
    trigger.scroll_into_view_if_needed()
    trigger.click()
    page.wait_for_function("""() => document.querySelector('#dialog-demo dialog').open""")
    page.keyboard.press("Escape")
    page.wait_for_function("""() => !document.querySelector('#dialog-demo dialog').open""")
    t.docs("/docs/components/chart")
    page.wait_for_function("""() => document.querySelectorAll('#chart [data-docs="preview"] [data-slot="chart"] svg').length >= 10""")
    t.docs("/docs/components/table")
    page.wait_for_function("""() => document.querySelectorAll('#table-data tbody tr[data-id]').length === 5""")
    t.docs("/docs/components/stat-tile")
    page.wait_for_function("""() => document.querySelectorAll('#chart-stat [data-slot="chart-stat"]').length >= 7""")
    t.docs("/docs/components/sidebar")
    assert page.locator("#sidebar-main").count() == 1
    assert page.evaluate("""() => getComputedStyle(document.querySelector('[data-docs="sidebar-wrapper"]')).backgroundColor""") == "rgba(0, 0, 0, 0)"
    t.docs("/docs/components/icons")
    page.wait_for_function("""() => document.querySelectorAll('#icon-grid svg').length > 100""")


BLOCKS = ["dashboard", "data-table", "settings", "form", "detail", "login", "login-split", "card-grid", "overlay-form", "states"]

BLOCK_LAYOUT = """() => {
  const box = el => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), b: Math.round(r.bottom) } }
  const shown = el => el.getClientRects().length > 0
  return {
    scrollWidth: document.documentElement.scrollWidth,
    cards: [...document.querySelectorAll('[data-slot="section-cards"] > [data-slot="card"]')].map(card => ({
      card: box(card),
      footer: box(card.querySelector('[data-slot="card-footer"]')),
      title: parseFloat(getComputedStyle(card.querySelector('[data-slot="card-title"]')).fontSize),
    })),
    stats: [...document.querySelectorAll('[data-slot="stat-grid"] > *')].map(box),
    nav: [...document.querySelectorAll('[data-slot="page-nav"] > a')].filter(shown).map(box),
    hidden: [...document.querySelectorAll("[data-show-from], [data-hide-from]")].filter(shown).map(el => (el.dataset.showFrom ? "show-" + el.dataset.showFrom : "hide-" + el.dataset.hideFrom)),
  }
}"""


def check_blocks_render(t):
    page = t.page
    breakpoints = {"sm": 640, "md": 768, "lg": 1024, "xl": 1280}
    for name in BLOCKS:
        t.docs("/blocks/" + name)
        page.wait_for_function("() => document.querySelectorAll('[data-slot]').length > 20")
        t.settle()
        m = page.evaluate(BLOCK_LAYOUT)
        assert m["scrollWidth"] == t.width, (name, m["scrollWidth"])
        for key in m["hidden"]:
            kind, size = key.split("-")
            assert (t.width >= breakpoints[size]) == (kind == "show"), (name, key)
        t.shot(name, page)
    t.docs("/blocks/dashboard")
    m = page.evaluate(BLOCK_LAYOUT)
    cards = m["cards"]
    assert len(cards) == 4
    columns = len({c["card"]["x"] for c in cards})
    assert columns == (1 if t.mobile else 2), columns
    rows = {}
    for c in cards:
        rows.setdefault(c["card"]["y"], []).append(c)
    for row in rows.values():
        assert len({c["footer"]["y"] for c in row}) == 1 and len({c["card"]["h"] for c in row}) == 1, row
    assert all(c["title"] == (30 if c["card"]["w"] >= 250 else 24) for c in cards), cards
    t.docs("/blocks/detail")
    stats = page.evaluate(BLOCK_LAYOUT)["stats"][:4]
    assert len({s["y"] for s in stats}) == (2 if t.mobile else 1), stats
    t.docs("/blocks/settings")
    nav = page.evaluate(BLOCK_LAYOUT)["nav"]
    assert len({n["y"] for n in nav}) == (1 if t.mobile else len(nav)), nav


def check_blocks_section_cards_align(t):
    page = t.page
    t.docs("/blocks/dashboard")
    page.evaluate("""() => { const d = document.querySelector('[data-slot="section-cards"] [data-slot="card-description"]'); d.textContent = "A long label that wraps to a second line in a narrow card" }""")
    cards = page.evaluate(BLOCK_LAYOUT)["cards"]
    first_row = [c for c in cards if c["card"]["y"] == cards[0]["card"]["y"]]
    assert len({c["footer"]["y"] for c in first_row}) == 1, first_row
    assert len({c["footer"]["h"] for c in first_row}) == 1, first_row
    page.evaluate("""() => { document.querySelector('[data-slot="section-cards"] [data-slot="card-title"]').textContent = "$1,234,567,890.00 per quarter" }""")
    title = page.locator('[data-slot="section-cards"] [data-slot="card-title"]').first
    assert title.evaluate("el => el.scrollWidth <= el.clientWidth + 1 && el.getBoundingClientRect().right <= el.closest('[data-slot=card]').getBoundingClientRect().right")


def check_blocks_data_table(t):
    page = t.page
    t.docs("/blocks/data-table")
    rows = page.locator('#tasks tbody tr[data-status]:not([hidden])')
    assert rows.count() == 10
    assert page.locator("#task-page").inner_text() == "Page 1 of 2"
    page.locator("#task-filter").fill("zzz-no-task")
    page.locator("#task-empty").wait_for(state="visible")
    assert rows.count() == 0 and page.locator("#task-reset").is_visible()
    page.locator("#task-clear").click()
    page.locator("#task-empty").wait_for(state="hidden")
    assert rows.count() == 10 and page.locator("#task-filter").input_value() == ""
    page.locator('#tasks thead [data-slot="checkbox"]').click()
    assert page.locator('[data-slot="data-table-selection"]').inner_text() == "10 of 16 row(s) selected."
    status = page.locator('#tasks tbody tr:not([hidden]) [data-hide-from="sm"] [data-slot="text-stack"] > :last-child').first
    assert status.is_visible() == t.mobile and page.locator('th[data-column="status"]').is_visible() != t.mobile
    if not t.mobile:
        sort = page.locator('[data-sort="title"]')
        sort.click()
        assert page.locator('th:has([data-sort="title"])').get_attribute("aria-sort") == "ascending"
        titles = rows.evaluate_all("rows => rows.map(r => r.cells[2].querySelector('[title]').title)")
        assert titles == sorted(titles), titles
        sort.click()
        sort.click()
        assert page.locator('th:has([data-sort="title"])').get_attribute("aria-sort") == "none"
        assert page.locator('#tasks thead [data-sort] > svg').evaluate_all("icons => icons.map(i => i.dataset.lucide)") == ["chevrons-up-down"] * 3
    page.locator('[data-page="next"]').click()
    assert page.locator("#task-page").inner_text() == "Page 2 of 2" and rows.count() == 6


def check_blocks_login_validation(t):
    page = t.page
    t.docs("/blocks/login")
    button = page.get_by_role("button", name="Log in", exact=True)
    before = button.bounding_box()
    button.click()
    email = page.locator("#email")
    page.wait_for_function("() => document.querySelector('#email').getAttribute('aria-invalid') === 'true'")
    assert page.evaluate("() => document.activeElement.id") == "email"
    assert page.locator('[data-slot="field-error"]').first.inner_text() == "Enter your email address."
    email.fill("m@example.com")
    page.locator("#password").fill("correct horse")
    after = button.bounding_box()
    assert abs(after["x"] - before["x"]) < 1 and abs(after["width"] - before["width"]) < 1


def check_blocks_viewer(t):
    page = t.page
    if t.engine == "firefox":
        t.expect_console(r"Layout was forced before the page was fully loaded")
    t.docs("/docs/blocks/dashboard")
    frame = page.locator('[data-docs="block-frame"] iframe')
    assert frame.get_attribute("src").endswith("/blocks/dashboard")
    page.wait_for_function("""() => document.querySelector('[data-docs="block-frame"] iframe').contentDocument?.readyState === "complete" """)
    inner = page.frame_locator('[data-docs="block-frame"] iframe')
    inner.locator('[data-slot="section-cards"]').wait_for()
    if t.width >= 1024:
        page.get_by_role("radio", name="Mobile").or_(page.get_by_role("button", name="Mobile")).first.click()
        page.wait_for_function("""() => document.querySelector('[data-docs="block-frame"] iframe').getBoundingClientRect().width === 390""")
    page.get_by_role("tab", name="Code").click()
    titles = page.locator('[data-docs="block-tabs"] [data-slot="code-block-title"]').all_inner_texts()
    assert titles == ["dashboard.html", "dashboard.js"], titles
    md = page.request.get(t.base_url + "/docs/blocks/dashboard.md").text()
    assert '```html title="dashboard.html"' in md and '```js title="dashboard.js"' in md
    run_csp = page.request.get(t.base_url + "/blocks/dashboard").headers["content-security-policy"]
    assert "frame-ancestors 'self'" in run_csp.split("; ")


def check_blocks_form_fields(t):
    page = t.page
    t.docs("/blocks/form")
    status = page.locator("#project-status").bounding_box()
    field = page.locator("#project-status").locator("xpath=ancestor::*[@data-slot='field'][1]").bounding_box()
    budget = page.locator("#project-budget").locator("xpath=ancestor::*[@data-slot='field'][1]").bounding_box()
    assert abs(status["width"] - field["width"]) < 1, (status, field)
    assert (abs(field["y"] - budget["y"]) < 1) == (not t.mobile), (field, budget)
    page.get_by_role("button", name="Create project").click()
    page.wait_for_function("() => document.querySelector('#project-name').getAttribute('aria-invalid') === 'true'")
    after = page.locator("#project-budget").locator("xpath=ancestor::*[@data-slot='field'][1]").bounding_box()
    assert abs(after["x"] - budget["x"]) < 1 and abs(after["width"] - budget["width"]) < 1, (budget, after)


def check_blocks_csp_meta(t):
    page = t.page
    for name in BLOCKS:
        t.docs("/blocks/" + name)
        metas = page.evaluate("""() => [...document.querySelectorAll('meta[http-equiv="Content-Security-Policy"]')].map(m => m.content)""")
        assert len(metas) == 1 and "require-trusted-types-for 'script'" in metas[0] and "frame-ancestors" not in metas[0], (name, metas)


def check_blocks_form_edit(t):
    page = t.page
    t.docs("/blocks/form")
    assert page.locator("#project-danger").is_hidden()
    t.docs("/blocks/form?id=web")
    page.wait_for_function("() => document.querySelector('[data-summary=duration]').textContent === '10 weeks'")
    assert page.locator("#project-title").inner_text() == "Website redesign"
    assert page.locator("#project-status").inner_text().strip() == "Active"
    assert page.locator('[data-summary="weekly"]').inner_text() == "$4,800"
    trigger = page.locator("#project-timeline")
    field = trigger.locator("xpath=ancestor::*[@data-slot='field'][1]")
    assert abs(trigger.bounding_box()["width"] - field.bounding_box()["width"]) < 1
    page.locator("#project-budget").fill("60000")
    assert page.locator('[data-summary="budget"]').inner_text() == "$60,000"
    page.get_by_role("button", name="Delete project").click()
    page.wait_for_selector('#project-danger [data-slot="alert-dialog-content"][data-open]')
    page.keyboard.press("Escape")
    page.wait_for_selector('#project-danger [data-slot="alert-dialog-content"]:not([data-open])', state="attached")


def check_blocks_card_grid(t):
    page = t.page
    t.docs("/blocks/card-grid")
    cards = page.locator('#books > [data-slot="card"]:not([hidden])')
    assert cards.count() == 12
    if t.mobile:
        page.locator("#shelf-select [data-slot=select-trigger]").click()
        page.get_by_role("option", name="Read (6)").click()
    else:
        page.get_by_role("tab", name="Read 6").click()
    page.wait_for_function("() => document.querySelectorAll('#books > [data-slot=card]:not([hidden])').length === 6")
    assert cards.evaluate_all("cs => cs.every(c => c.dataset.status === 'read')")
    columns = len({round(b["x"]) for b in cards.evaluate_all("cs => cs.map(c => c.getBoundingClientRect().toJSON())")})
    assert columns == (2 if t.mobile else 6), columns
    page.locator("#shelf-filter").fill("zzz")
    page.locator("#shelf-empty").wait_for(state="visible")
    page.locator("#shelf-clear").click()
    page.wait_for_function("() => document.querySelectorAll('#books > [data-slot=card]:not([hidden])').length === 12")
    page.locator("#shelf-sort [data-slot=select-trigger]").click()
    page.get_by_role("option", name="Title").click()
    titles = cards.evaluate_all("cs => cs.map(c => c.dataset.title)")
    assert titles == sorted(titles), titles
    for cover in page.locator('#books [data-slot="cover"]').all()[:4]:
        assert cover.evaluate("c => [...c.children].filter(e => e.localName === 'span').every(s => s.scrollWidth <= s.clientWidth + 1)")


def check_blocks_overlay_form(t):
    page = t.page
    t.docs("/blocks/overlay-form")
    page.get_by_role("button", name="Write a review").click()
    page.wait_for_selector("#review-dialog [data-slot=dialog-content][data-open]")
    t.settle()
    page.get_by_role("button", name="Post review").click()
    errors = page.locator("#review-form [data-slot=field-error]:visible")
    assert errors.all_inner_texts() == ["Choose a rating from 1 to 5 stars.", "Write a short headline.", "Write your review."], errors.all_inner_texts()
    gap = page.evaluate("""() => { const h = document.querySelector('#review-form [data-slot=dialog-header]').getBoundingClientRect(); const g = document.querySelector('#review-form > [data-slot=field-group]').getBoundingClientRect(); return g.top - h.bottom }""")
    assert abs(gap - 16) < 1, gap
    page.locator("label[for=rating-4]").click()
    page.locator("#review-title").fill("Worth the hype")
    page.locator("#review-text").fill("The middle drags, but the ending is earned.")
    page.get_by_role("button", name="Post review").click()
    page.wait_for_selector("#review-dialog [data-slot=dialog-content]:not([data-open])", state="attached")
    assert page.locator("#reviews [data-slot=item-title]").first.inner_text() == "Worth the hype"
    assert page.locator("#reviews [data-slot=rating]").first.get_attribute("aria-label") == "4 of 5 stars"
    page.get_by_role("button", name="Edit details").click()
    page.wait_for_selector("#edit-book [data-slot=sheet-content][data-open]")
    t.settle()
    m = page.evaluate("""() => { const b = document.querySelector('#edit-book [data-slot=sheet-body]'); const f = document.querySelector('#edit-book [data-slot=sheet-footer]').getBoundingClientRect(); return { overflow: getComputedStyle(b).overflowY, footer: f.bottom, height: innerHeight } }""")
    assert m["footer"] <= m["height"] + 1 and m["overflow"] == "auto", m
    page.locator("#book-title").fill("Project Hail Mary (2nd ed.)")
    page.get_by_role("button", name="Save changes").click()
    page.wait_for_function("() => document.querySelector('[data-slot=page-title]').textContent === 'Project Hail Mary (2nd ed.)'")


def check_blocks_login_split(t):
    page = t.page
    t.docs("/blocks/login-split")
    aside = page.locator('[data-slot="page-aside"]')
    assert aside.is_visible() == (t.width >= 1024)
    link = page.get_by_role("link", name="Forgot your password?")
    muted = page.evaluate("""() => { const p = document.createElement('p'); p.style.color = 'var(--muted-foreground)'; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c }""")
    assert link.evaluate("a => getComputedStyle(a).color") == muted
    toggle = page.locator('[data-theme-set="toggle"]')
    brand = page.locator('[data-slot="brand"]')
    assert abs(toggle.bounding_box()["y"] + toggle.bounding_box()["height"] / 2 - brand.bounding_box()["y"] - brand.bounding_box()["height"] / 2) < 2
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_function("() => document.querySelector('#email').getAttribute('aria-invalid') === 'true'")
    assert page.evaluate("() => document.activeElement.id") == "email"
