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


def wait_js(page, expr, timeout=20000):
    page.wait_for_function(expr, timeout=timeout)


def check_ai_reasoning_replay(t):
    page = t.page
    t.docs("/docs/ai-elements/reasoning")
    replay = page.locator("#reasoning-demo-replay")
    replay.click()
    assert replay.is_hidden()
    wait_js(page, """() => document.querySelector('#reasoning-demo [data-slot="trace-line"][data-status="running"]')?.textContent.includes('Thinking')""")
    wait_js(page, """() => document.querySelector('#reasoning-demo [data-slot="trace-collapsible"]')?.dataset.state === 'open' && document.querySelector('#reasoning-demo [data-slot="trace-collapsible-content"]').textContent.length > 0""")
    first = page.evaluate("""() => document.querySelector('#reasoning-demo [data-slot="trace-collapsible-content"]').textContent.length""")
    page.wait_for_function("""n => document.querySelector('#reasoning-demo [data-slot="trace-collapsible-content"]').textContent.length > n""", arg=first)
    wait_js(page, """() => document.querySelector('#reasoning-demo [data-slot="trace-title"]').textContent === 'Thought for 5s'""")
    state = page.evaluate("""() => { const c = document.querySelector('#reasoning-demo [data-slot="trace-collapsible"]'); return [c.dataset.state, c.querySelector('[data-slot="trace-line"]').hasAttribute('data-status'), c.querySelector('[data-slot="trace-collapsible-content"]').textContent.startsWith('The deploy log has three phases.')] }""")
    assert state[1] is False and state[2] is True, state
    wait_js(page, """() => document.querySelector('#reasoning-demo [data-slot="trace-collapsible"]').dataset.state === 'closed'""")
    wait_js(page, """() => !document.getElementById('reasoning-demo-replay').hidden""")
    assert page.locator("#reasoning-demo p").inner_text().startswith("Image optimization is the bottleneck.")
    assert page.locator('#reasoning-demo > [data-slot="message"]').count() == 2


def check_ai_reasoning_choice_wins(t):
    page = t.page
    t.docs("/docs/ai-elements/reasoning")
    page.locator("#reasoning-demo-replay").click()
    wait_js(page, """() => document.querySelector('#reasoning-demo [data-slot="trace-collapsible"]')?.dataset.state === 'open'""")
    trigger = page.locator('#reasoning-demo [data-slot="trace-collapsible-trigger"]')
    trigger.click()
    wait_js(page, """() => document.querySelector('#reasoning-demo [data-slot="trace-collapsible"]').dataset.state === 'closed'""")
    trigger.click()
    wait_js(page, """() => !document.getElementById('reasoning-demo-replay').hidden""")
    assert page.evaluate("""() => document.querySelector('#reasoning-demo [data-slot="trace-collapsible"]').dataset.state""") == "open"


def check_ai_chain_of_thought_replay(t):
    page = t.page
    t.docs("/docs/ai-elements/chain-of-thought")
    replay = page.locator("#chain-of-thought-demo-replay")
    replay.click()
    assert replay.is_hidden()
    summary = """document.querySelector('#chain-of-thought-demo [data-slot="message"]:not([data-align="end"]) [data-slot="trace-collapsible"]')"""
    wait_js(page, f"""() => {{ const s = {summary}; return s?.dataset.state === 'open' && s.querySelector('[data-slot="trace-line"]').dataset.status === 'running' && s.querySelector('[data-slot="trace-title"]').textContent === 'Researching' }}""")
    wait_js(page, f"""() => [...{summary}.querySelectorAll('[data-slot="trace-collapsible-content"] [data-slot="trace-line"][data-status="running"] [data-slot="trace-title"]')].some(e => e.textContent === 'Reading the build log for dpl_8Kx2')""")
    wait_js(page, f"""() => {summary}.querySelector(':scope > [data-slot="trace-collapsible-trigger"] [data-slot="trace-title"]').textContent === 'Researched in 3 steps'""")
    wait_js(page, f"""() => {summary}.dataset.state === 'closed'""")
    steps = page.evaluate(f"""() => [...{summary}.querySelectorAll(':scope > [data-slot="trace-collapsible-content"] > * > [data-slot="trace"] > [data-slot="trace-collapsible"]')].map(c => [c.querySelector('[data-slot="trace-title"]').textContent, c.dataset.state])""")
    assert steps == [["Read the build log for dpl_8Kx2", "open"], ["Searched the web for next.js image cache key", "closed"], ["Searched the code for cacheKey", "closed"]], steps
    wait_js(page, """() => !document.getElementById('chain-of-thought-demo-replay').hidden""")
    assert page.locator("#chain-of-thought-demo p").inner_text().endswith("Key it on the image directory instead.")


def check_ai_task_replay(t):
    page = t.page
    t.docs("/docs/ai-elements/task")
    page.locator("#task-demo-replay").click()
    rows = """document.querySelectorAll('#task-demo [data-slot="message"]:not([data-align="end"]) [data-slot="message-content"] > [data-slot="trace"] > [data-slot="trace-collapsible"]')"""
    wait_js(page, f"""() => {{ const r = {rows}[0]; return r?.dataset.state === 'open' && r.querySelector('[data-slot="trace-line"]').dataset.status === 'running' && r.querySelector('[data-slot="trace-title"]').textContent === 'Finding the project files' }}""")
    wait_js(page, f"""() => {{ const lines = {rows}[0].querySelectorAll('[data-slot="trace-collapsible-content"] [data-slot="trace-line"]'); return lines.length === 2 && !lines[0].hasAttribute('data-status') && lines[0].textContent === 'Searched for generateMetadata' && lines[1].dataset.status === 'running' && lines[1].textContent === 'Reading app/layout.tsx' }}""")
    wait_js(page, f"""() => {rows}.length === 2 && {rows}[0].dataset.state === 'closed' && {rows}[1].dataset.state === 'open'""")
    wait_js(page, """() => !document.getElementById('task-demo-replay').hidden""")
    final = page.evaluate(f"""() => [...{rows}].map(r => [r.querySelector('[data-slot="trace-title"]').textContent, r.dataset.state, r.querySelector('[data-slot="trace-line"]').hasAttribute('data-status'), [...r.querySelectorAll('[data-slot="trace-collapsible-content"] [data-slot="trace-line"]')].map(l => l.textContent + (l.hasAttribute('data-status') ? '!' : ''))])""")
    assert final == [["Found the project files", "closed", False, ["Searched for generateMetadata", "Read app/layout.tsx", "Read app/page.tsx"]], ["Updated the page metadata", "closed", False, ["Edited app/layout.tsx", "Edited app/page.tsx"]]], final
    assert page.locator("#task-demo p").inner_text().startswith("Added Open Graph defaults")


def check_ai_plan_replay(t):
    page = t.page
    t.docs("/docs/ai-elements/plan")
    page.locator("#plan-demo-replay").click()
    plan = """document.querySelector('#plan-demo [data-slot="message"]:not([data-align="end"]) [data-slot="trace-collapsible"]')"""
    read = f"""() => {{ const p = {plan}; if (!p) return null; const line = p.querySelector('[data-slot="trace-line"]'); return [line.getAttribute('data-status'), line.querySelector('[data-slot="trace-description"]').textContent, [...p.querySelectorAll('[data-slot="trace-collapsible-content"] [data-slot="trace-line"]')].map(l => (l.getAttribute('data-status') ?? 'done') + ':' + l.querySelector('svg').dataset.lucide)] }}"""
    page.wait_for_function(f"""() => JSON.stringify(({read})()) === JSON.stringify(['running', '0 of 4 done', ['running:circle-dot', 'pending:circle', 'pending:circle', 'pending:circle']])""")
    page.wait_for_function(f"""() => JSON.stringify(({read})()) === JSON.stringify(['running', '1 of 4 done', ['done:circle-check', 'running:circle-dot', 'pending:circle', 'pending:circle']])""", timeout=5000)
    page.wait_for_function(f"""() => JSON.stringify(({read})()) === JSON.stringify([null, '4 of 4 done', ['done:circle-check', 'done:circle-check', 'done:circle-check', 'done:circle-check']])""", timeout=10000)
    wait_js(page, """() => !document.getElementById('plan-demo-replay').hidden""")
    assert page.locator("#plan-demo p").inner_text() == "Migrated Dialog and AlertDialog. The type checker passes."


def check_ai_tool_replay(t):
    page = t.page
    t.docs("/docs/ai-elements/tool")
    page.locator("#tool-demo-replay").click()
    trace = """document.querySelector('#tool-demo [data-slot="message"]:not([data-align="end"]) [data-slot="trace"]')"""
    wait_js(page, f"""() => {trace}?.querySelector(':scope > [data-slot="trace-line"][data-status="running"]')?.textContent === 'Running node --version'""")
    wait_js(page, f"""() => {trace}.querySelector(':scope > [data-slot="trace-collapsible"] [data-slot="trace-title"]')?.textContent === 'Ran node --version'""")
    wait_js(page, """() => !document.getElementById('tool-demo-replay').hidden""")
    rows = page.evaluate(f"""() => [...{trace}.children].map(c => [c.dataset.slot, c.querySelector('[data-slot="trace-title"]').textContent, c.querySelector('[data-slot="trace-line"]').getAttribute('data-status'), c.dataset.state, c.querySelector('code')?.textContent])""")
    assert rows == [["trace-collapsible", "Ran node --version", None, "closed", "v24.18.0"], ["trace-collapsible", "Ran npm --version", None, "closed", "11.6.2"], ["trace-collapsible", "Failed to run pnpm --version", "error", "closed", "command not found: pnpm"]], rows
    page.locator('#tool-demo [data-slot="message"]:not([data-align="end"]) [data-slot="trace-collapsible-trigger"]').nth(2).click()
    wait_js(page, f"""() => {trace}.children[2].dataset.state === 'open'""")
    assert page.locator("#tool-demo p").inner_text() == "Node 24 and npm 11 are installed. pnpm is not."


def check_ai_tool_sheet(t):
    page = t.page
    t.docs("/docs/ai-elements/tool")
    send = page.locator("#tool-sheet-send")
    assert page.locator('#tool-sheet > [data-slot="message"]').count() == 0
    send.click()
    wait_js(page, """() => document.querySelector('#tool-sheet [data-slot="trace-line"][data-status="running"]')?.textContent === 'Reading package.json'""")
    trigger = page.locator('#tool-sheet [data-sheet-trigger="tool-sheet-file"]')
    trigger.wait_for(state="visible")
    wait_js(page, """() => document.getElementById('tool-sheet-send').textContent === 'Reset' && !document.getElementById('tool-sheet-send').hidden""")
    assert page.locator('#tool-sheet [data-slot="message-content"] > p').inner_text() == "It uses ai 7 with @ai-sdk/react 4."
    trigger.click()
    wait_js(page, """() => document.querySelector('#tool-sheet-file [data-slot="sheet-content"]')?.dataset.state === 'open'""")
    assert page.locator('#tool-sheet-file [data-slot="sheet-title"]').inner_text() == "package.json"
    assert page.locator('#tool-sheet-file [data-slot="code-block-line"]').count() == 9
    t.settle()
    page.keyboard.press("Escape")
    wait_js(page, """() => document.querySelector('#tool-sheet-file [data-slot="sheet-content"]').dataset.state === 'closed'""")
    t.settle()
    send.click()
    assert page.locator('#tool-sheet > [data-slot="message"]').count() == 0 and send.inner_text() == "Send message"


def check_ai_tool_approval(t):
    page = t.page
    t.docs("/docs/ai-elements/tool")
    send = page.locator("#tool-approval-send")
    for approve, line, reply in [(True, "Ran rm -rf dist", "Removed the dist folder."), (False, "Denied rm -rf dist", "Okay, I left the dist folder in place.")]:
        send.click()
        wait_js(page, """() => document.querySelector('#tool-approval [data-slot="trace-line"][data-status="running"]')?.textContent.includes('Thinking')""")
        item = page.locator('#tool-approval [data-slot="item"]')
        item.wait_for(state="visible")
        assert page.evaluate("""() => [document.querySelector('#tool-approval [data-slot="trace-collapsible"]').dataset.state, document.querySelector('#tool-approval [data-slot="trace-title"]').textContent]""") == ["closed", "Thought"]
        assert send.inner_text() == "Reset"
        item.get_by_role("button", name="Approve" if approve else "Deny").click()
        assert item.count() == 0
        wait_js(page, f"""() => document.querySelectorAll('#tool-approval [data-slot="message"]:not([data-align="end"]) [data-slot="message-content"] > [data-slot="trace"]')[1]?.textContent.trim() === {line!r}""")
        wait_js(page, """() => !document.getElementById('tool-approval-send').hidden""")
        assert page.locator('#tool-approval [data-slot="message-content"] > p').inner_text() == reply
        send.click()
        assert page.locator('#tool-approval > [data-slot="message"]').count() == 0
