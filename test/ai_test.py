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


def wait_text(page, selector, text, timeout=10000):
    page.wait_for_function("([s, t]) => [...document.querySelectorAll(s)].some(e => e.textContent.trim() === t)", arg=[selector, text], timeout=timeout)


def check_ai_queue_replay(t):
    page = t.page
    t.docs("/docs/ai-elements/queue")
    root = page.locator("#queue-demo")
    replay = page.locator("#queue-demo-replay")
    replay.click()
    assert replay.is_hidden()
    wait_text(page, "#queue-demo [data-slot=trace-title]", "4 to do")
    running = root.locator('[data-slot=trace-line][data-status="running"]')
    assert running.count() == 1 and running.locator("[data-slot=trace-title]").inner_text() == "Add a dark variant to the theme tokens"
    assert running.locator('svg[data-lucide="circle-dot"]').count() == 1
    wait_text(page, "#queue-demo [data-slot=trace-title]", "1 completed")
    assert root.locator("[data-slot=trace-title]", has_text="3 to do").count() == 1
    replay.wait_for(state="visible", timeout=10000)
    titles = root.locator(":scope > [data-slot=message] [data-slot=trace-collapsible-trigger] [data-slot=trace-title]").all_inner_texts()
    assert titles == ["4 completed"], titles
    assert root.locator('[data-slot=trace-line][data-status="running"]').count() == 0
    assert root.locator(":scope > [data-slot=message]").count() == 2
    assert root.locator("p").inner_text() == "Dark mode is in. The toggle is under Settings, Appearance."


def check_ai_subagent_replay(t):
    page = t.page
    t.docs("/docs/ai-elements/subagent")
    root = page.locator("#subagent-demo")
    replay = page.locator("#subagent-demo-replay")
    replay.click()
    assert replay.is_hidden()
    wait_text(page, "#subagent-demo [data-slot=trace-title]", "Running the research subagent")
    wait_text(page, "#subagent-demo [data-slot=trace-title]", "Running grep -rn cacheKey scripts")
    run = root.locator(":scope > [data-slot=message] > [data-slot=message-content] > [data-slot=trace] > [data-slot=trace-collapsible]")
    assert run.get_attribute("data-state") == "open"
    assert run.locator(":scope > [data-slot=trace-collapsible-trigger] [data-slot=trace-line]").get_attribute("data-status") == "running"
    wait_text(page, "#subagent-demo [data-slot=trace-title]", "Ran grep -rn cacheKey scripts")
    replay.wait_for(state="visible", timeout=10000)
    line = run.locator(":scope > [data-slot=trace-collapsible-trigger] [data-slot=trace-line]")
    assert line.get_attribute("data-status") is None and line.locator("[data-slot=trace-title]").inner_text() == "Ran the research subagent"
    assert run.locator("[data-slot=trace] [data-slot=trace-collapsible]").count() == 3
    assert root.locator('[data-status="running"]').count() == 0
    assert root.locator("p").count() == 2 and root.locator("p").last.inner_text().startswith("Image optimization reruns")


def confirmation_ask(t):
    page = t.page
    t.docs("/docs/ai-elements/confirmation")
    root = page.locator("#confirmation-demo")
    next_button = page.locator("#confirmation-demo-next")
    assert root.locator("[data-slot=message]").count() == 0 and next_button.inner_text() == "Send message"
    next_button.click()
    assert next_button.is_hidden()
    wait_text(page, "#confirmation-demo [data-slot=trace-title]", "Thinking")
    reasoning = root.locator("[data-slot=trace-collapsible]")
    assert reasoning.get_attribute("data-state") == "open"
    root.locator("[data-slot=item]").wait_for(timeout=10000)
    assert reasoning.locator("[data-slot=trace-title]").inner_text() == "Thought"
    page.wait_for_function("() => document.querySelector('#confirmation-demo [data-slot=trace-collapsible]').dataset.state === 'closed'")
    assert root.locator("[data-slot=item-title]").inner_text() == "Run rm -rf dist?"
    assert next_button.is_visible() and next_button.inner_text() == "Reset"
    return page, root, next_button


def check_ai_confirmation_approve(t):
    page, root, next_button = confirmation_ask(t)
    root.locator("[data-slot=item] button", has_text="Approve").click()
    assert root.locator("[data-slot=item]").count() == 0
    wait_text(page, "#confirmation-demo [data-slot=trace-title]", "Ran rm -rf dist")
    wait_text(page, "#confirmation-demo p", "Removed the dist folder.")
    line = root.locator("[data-slot=trace-line]", has_text="Ran rm -rf dist")
    assert line.get_attribute("data-status") is None
    next_button.wait_for(state="visible")
    assert next_button.inner_text() == "Reset"
    next_button.click()
    assert root.locator("[data-slot=message]").count() == 0 and next_button.inner_text() == "Send message"


def check_ai_confirmation_deny(t):
    page, root, next_button = confirmation_ask(t)
    root.locator("[data-slot=item] button", has_text="Deny").click()
    assert root.locator("[data-slot=item]").count() == 0
    line = root.locator("[data-slot=trace-line]", has_text="Denied rm -rf dist")
    assert line.count() == 1 and line.get_attribute("data-status") is None
    wait_text(page, "#confirmation-demo p", "Okay, I left the dist folder in place.")
    next_button.wait_for(state="visible")


def check_ai_checkpoint_restore(t):
    page = t.page
    t.docs("/docs/ai-elements/checkpoint")
    root = page.locator("#checkpoint-demo")
    next_button = page.locator("#checkpoint-demo-continue")
    assert next_button.is_hidden() and root.locator("[data-slot=message]").count() == 4
    page.get_by_role("button", name="Restore to Button renamed").click()
    assert root.locator("[data-slot=message]").count() == 2
    assert page.locator("#checkpoint-demo-restore").count() == 0
    assert next_button.is_visible()
    next_button.click()
    assert next_button.is_hidden()
    wait_text(page, "#checkpoint-demo p", "Updated the Button page to say Action.")
    assert root.locator("[data-slot=message]").count() == 4
    page.locator("#checkpoint-demo-restore").wait_for()
    assert next_button.is_hidden()
