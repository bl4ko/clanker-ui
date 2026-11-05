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


def check_ai_sources_replay(t):
    page = t.page
    t.docs("/docs/ai-elements/sources")
    replay = page.locator("#sources-demo-replay")
    thread = page.locator("#sources-demo-thread")
    assert thread.locator('[data-slot="trace-collapsible"]').count() == 1
    replay.click()
    assert replay.is_hidden()
    assert thread.locator('[data-slot="message"]').count() == 1
    assert thread.locator('[data-slot="trace"]').count() == 0
    page.wait_for_function("() => document.querySelectorAll('#sources-demo-thread p').length === 1")
    page.wait_for_function("() => !document.getElementById('sources-demo-replay').hidden", timeout=5000)
    t.settle()
    text = thread.locator("p").inner_text()
    assert text.startswith("Run pnpm create astro@latest") and text.endswith("installs the dependencies."), text
    collapsible = thread.locator('[data-slot="trace-collapsible"]')
    assert collapsible.count() == 1 and collapsible.get_attribute("data-state") == "open"
    assert collapsible.locator('[data-slot="trace-collapsible-trigger"] [data-slot="trace-title"]').inner_text() == "Used 3 sources"
    links = collapsible.locator("a[href]")
    assert [links.nth(i).get_attribute("href") for i in range(links.count())] == ["https://docs.astro.build/en/install-and-setup/", "https://www.npmjs.com/package/create-astro", "https://pnpm.io/cli/create"]
    assert links.first.get_attribute("target") == "_blank" and links.first.locator(".sr-only").inner_text() == " (opens in a new tab)"
    collapsible.locator('[data-slot="trace-collapsible-trigger"]').click()
    t.settle()
    assert collapsible.get_attribute("data-state") == "closed"


def check_ai_file_tree_select(t):
    page = t.page
    t.docs("/docs/ai-elements/file-tree")
    tree = page.locator("#file-tree-demo")
    current = tree.locator('[aria-current="true"]')
    assert current.count() == 1 and current.inner_text() == "button.tsx"
    selected_bg = current.evaluate("b => getComputedStyle(b).backgroundColor")
    page_file = tree.locator('[data-slot="button"]', has_text="page.tsx")
    assert page_file.evaluate("b => getComputedStyle(b).backgroundColor") != selected_bg
    page_file.click()
    assert current.count() == 1 and current.inner_text() == "page.tsx"
    page.mouse.move(0, 0)
    assert page_file.evaluate("b => getComputedStyle(b).backgroundColor") == selected_bg
    assert tree.locator('[data-slot="button"]', has_text="button.tsx").get_attribute("aria-current") is None
    folder = tree.locator("[data-collapsible-trigger]", has_text="app")
    folder.click()
    t.settle()
    assert folder.get_attribute("aria-expanded") == "true"
    assert current.count() == 1 and current.inner_text() == "page.tsx"


def check_ai_file_tree_folders(t):
    page = t.page
    t.docs("/docs/ai-elements/file-tree")
    tree = page.locator("#file-tree-demo")
    folder = tree.locator("[data-collapsible-trigger]", has_text="components")
    chevron = folder.locator('svg[data-lucide="chevron-right"]')
    assert folder.get_attribute("aria-expanded") == "true"
    assert chevron.evaluate("s => getComputedStyle(s).rotate") == "90deg"
    assert folder.evaluate("b => getComputedStyle(b).backgroundColor") == "rgba(0, 0, 0, 0)"
    folder.click()
    t.settle()
    assert folder.get_attribute("aria-expanded") == "false"
    assert chevron.evaluate("s => getComputedStyle(s).rotate") in ("none", "0deg")
    assert tree.locator('[data-slot="button"]', has_text="login-form.tsx").is_hidden()
    folder.focus()
    page.keyboard.press("Enter")
    t.settle()
    assert folder.get_attribute("aria-expanded") == "true"
    assert tree.locator('[data-slot="button"]', has_text="login-form.tsx").is_visible()


def check_ai_inline_citation_card(t):
    if t.mobile:
        t.skip("hover cards open on hover and focus, not touch")
    page = t.page
    t.docs("/docs/ai-elements/inline-citation")
    preview = page.locator('[data-example="inline-citation-demo"] [data-docs="preview"]')
    assert preview.locator("p").count() == 3
    triggers = preview.locator("p [data-hover-card-trigger]")
    assert [triggers.nth(i).inner_text() for i in range(triggers.count())] == ["nextjs.org", "react.dev", "react.dev", "nextjs.org", "developer.mozilla.org"]
    triggers.nth(1).hover()
    content = preview.locator('[data-slot="hover-card-content"]').nth(1)
    page.wait_for_function("el => el.dataset.state === 'open'", arg=content.element_handle())
    assert content.locator(".font-medium").inner_text() == "<Suspense>"
    assert content.evaluate("e => getComputedStyle(e).display") == "flex"
    assert content.locator("a").get_attribute("href") == "https://react.dev/reference/react/Suspense"
    page.mouse.move(0, 0)
    page.wait_for_function("el => el.dataset.state !== 'open'", arg=content.element_handle())
