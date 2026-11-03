# Automated check

Serve the page with the CSP from [csp.md](csp.md), then run a check with Playwright for Python:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    errors = []
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:8300/", wait_until="load")
    page.get_by_role("button", name="Open").click()
    page.wait_for_selector('[data-slot="dialog-content"][data-open]')
    page.keyboard.press("Escape")
    page.wait_for_selector('[data-slot="dialog-content"]:not([open])', state="attached")
    assert not errors, errors
```

- Open popups have `data-open` (and `data-state="open"`); closed ones have `data-closed`. A `<dialog>` keeps `open` until its exit animation ends, so wait for the attribute, not for a fixed time.
- Toasts appear as `[data-slot="toast"]` inside `[data-slot="toast-viewport"]`.
- All events and their `detail` fields: [events.md](events.md).
