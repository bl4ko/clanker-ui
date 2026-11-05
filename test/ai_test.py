START = "/docs/ai-elements"


def check_ai_index(t):
    page = t.page
    links = page.locator('[data-docs="content"] table a[href^="/docs/ai-elements/"]')
    sidebar = page.locator('[data-docs="sidebar"] a[href^="/docs/ai-elements/"]')
    assert links.count() >= 1
    if t.width >= 1024:
        assert sidebar.count() == links.count()


def check_ai_message_feedback(t):
    page = t.page
    t.docs("/docs/ai-elements/message")
    like = page.locator("#message-pattern-like")
    dislike = page.locator("#message-pattern-dislike")
    like.click()
    assert like.get_attribute("aria-pressed") == "true" and dislike.get_attribute("aria-pressed") == "false"
    assert like.locator("svg").evaluate("s => getComputedStyle(s).fill") != "none"
    dislike.click()
    assert like.get_attribute("aria-pressed") == "false" and dislike.get_attribute("aria-pressed") == "true"
    assert like.locator("svg").evaluate("s => getComputedStyle(s).fill") == "none"
    dislike.click()
    assert dislike.get_attribute("aria-pressed") == "false"


def check_ai_message_copy(t):
    page = t.page
    t.docs("/docs/ai-elements/message")
    if t.engine == "chromium":
        page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=t.base_url)
    copy = page.locator("#message-pattern-copy")
    copy.click()
    page.wait_for_function("() => document.querySelector('#message-pattern-copy').getAttribute('aria-label') === 'Copied'")
    assert copy.locator("svg.lucide-check").count() == 1
    if t.engine == "chromium":
        text = page.evaluate("() => navigator.clipboard.readText()")
        assert text.startswith("Install Dialog") and "npx shadcn@latest add dialog" in text and text.rstrip().endswith("closes it."), text
    page.wait_for_function("() => document.querySelector('#message-pattern-copy').getAttribute('aria-label') === 'Copy'", timeout=4000)
    assert copy.locator("svg.lucide-copy").count() == 1
