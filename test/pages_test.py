from urllib.parse import urlsplit

START = "/"

COMPONENTS = ["button", "button-group", "accordion", "dialog", "tabs"]

PAGE_URLS = """() => {
  const meta = document.querySelector('meta[http-equiv="Content-Security-Policy"]')
  const urls = [...document.querySelectorAll("a[href], link[href], script[src], img[src]")].map(e => e.getAttribute("href") ?? e.getAttribute("src"))
  return { csp: meta?.content ?? null, first: meta === document.head.querySelector('meta[http-equiv="Content-Security-Policy"], link, script, style'), urls }
}"""


def base_path(t):
    return urlsplit(t.base_url).path.rstrip("/")


def origin(t):
    u = urlsplit(t.base_url)
    return f"{u.scheme}://{u.netloc}"


def export_only(t):
    href = t.page.locator('[data-docs="main"] a', has_text="Get Started").get_attribute("href")
    if not href.endswith("/"):
        t.skip("runs against the static export (go run . -export)")


def page_ok(t):
    info = t.page.evaluate(PAGE_URLS)
    assert info["csp"] is not None, f"{t.page.url} has no CSP meta"
    assert info["first"], f"{t.page.url}: a link, script, or style comes before the CSP meta"
    assert "frame-ancestors" not in info["csp"]
    assert "require-trusted-types-for 'script'" in info["csp"]
    base = base_path(t) + "/"
    bad = [u for u in info["urls"] if u.startswith("/") and not u.startswith(base)]
    assert bad == [], f"{t.page.url}: links without the base path {base}"
    relative = [u for u in info["urls"] if not u.startswith(("/", "#", "data:", "https://", "http://", "mailto:"))]
    assert relative == [], f"{t.page.url}: relative links"


def open_link(t, href):
    response = t.page.goto(origin(t) + href, wait_until="load")
    assert response is not None and response.status == 200, f"{href} returned {response and response.status}"
    page_ok(t)


def check_pages_home(t):
    export_only(t)
    page_ok(t)
    assert t.page.locator('[data-docs="hero-title"]').count() == 1


def check_pages_components(t):
    export_only(t)
    page = t.page
    open_link(t, page.locator('[data-docs="main"] a', has_text="View Components").get_attribute("href"))
    links = page.locator('[data-docs="components-list"] a')
    hrefs = {h.rstrip("/").rsplit("/", 1)[-1]: h for h in links.evaluate_all("ls => ls.map(l => l.getAttribute('href'))")}
    for name in COMPONENTS:
        assert name in hrefs, f"no link to {name} on the components page"
        open_link(t, hrefs[name])
        assert page.locator('[data-docs="main"] h1').count() == 1


def check_pages_theme_toggle(t):
    export_only(t)
    page = t.page
    open_link(t, page.locator('[data-docs="main"] a', has_text="Get Started").get_attribute("href"))
    is_dark = "() => getComputedStyle(document.documentElement).colorScheme === 'dark'"
    before = page.evaluate(is_dark)
    assert before == (t.theme == "dark")
    background = "() => getComputedStyle(document.body).backgroundColor"
    color = page.evaluate(background)
    page.locator('[data-docs="header"] [data-theme-set="toggle"]').click()
    page.wait_for_function(f"() => ({is_dark})() === {str(not before).lower()}")
    page.wait_for_function(f"c => ({background})() !== c", arg=color)
    page.reload(wait_until="load")
    assert page.evaluate(is_dark) == (not before)


def check_pages_search_dialog(t):
    export_only(t)
    page = t.page
    open_link(t, page.locator('[data-docs="main"] a', has_text="Get Started").get_attribute("href"))
    trigger = page.locator('[data-docs="search-trigger"]')
    if trigger.is_visible():
        trigger.click()
    else:
        page.keyboard.press("/")
    page.wait_for_function("""() => document.querySelector('[data-docs="search-dialog"]').open && document.activeElement?.dataset.slot === "command-input" """)
    page.keyboard.type("button")
    item = page.locator('#docs-search [data-slot="command-item"][data-selected="true"]')
    item.wait_for()
    href = item.get_attribute("href")
    assert href.startswith(base_path(t) + "/docs/components/button"), href
    page.keyboard.press("Enter")
    page.wait_for_url(f"**{href}")
    page.wait_for_load_state("load")
    page_ok(t)


def check_pages_demo(t):
    export_only(t)
    page = t.page
    open_link(t, page.locator('[data-docs="announcement"]').get_attribute("href"))
    page.wait_for_function("() => document.querySelectorAll('img').length > 0 && [...document.images].every(i => i.complete && i.naturalWidth > 0 || i.src.startsWith('data:'))")
    trigger = page.locator("#dialog [data-dialog-trigger]").first
    trigger.scroll_into_view_if_needed()
    trigger.click()
    page.wait_for_function("() => document.querySelector('#dialog dialog[data-slot=\"dialog-content\"]').open")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#dialog dialog[data-slot=\"dialog-content\"]').open")


def check_pages_not_found(t):
    export_only(t)
    t.expect_console(r"^(http 404: .*/404\.html|console\.error: Failed to load resource: .*404.*)$")
    response = t.page.goto(t.base_url + "/404.html", wait_until="load")
    assert response is not None and response.status in (200, 404)
    page_ok(t)
    assert t.page.locator('[data-docs="main"] h1').inner_text() == "Page not found"
