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

# Design lint

[design-lint.js](design-lint.js) finds design mistakes that a person sees in a screenshot: buttons of two sizes in one row, two primary buttons, cut text, a page wider than the phone, small targets, low contrast, colors that are not kit tokens, missing labels, skipped headings, edges that are almost aligned, a card with a large empty area, and controls that move after an interaction. It is plain JavaScript without dependencies. It does not change the page.

The file is one expression that defines `window.clankerDesignLint`. Load it from the test, not from the page: the kit CSP blocks inline scripts, and the page does not need it. Two ways work under the kit CSP (with `require-trusted-types-for 'script'`) in Chromium, Firefox, and WebKit:

- `page.evaluate(source)` after each navigation (the whole file as the expression).
- `context.add_init_script(path=...)` (Node: `context.addInitScript({ path })`) once; every page in the context then has the lint.

Run it at 1280 and 390 px, in light and dark (`color_scheme`), after the page is ready (data loaded, animations done):

```python
import pathlib
from playwright.sync_api import sync_playwright

LINT = pathlib.Path("design-lint.js").read_text()

with sync_playwright() as p:
    for engine in (p.chromium, p.firefox, p.webkit):
        browser = engine.launch()
        for scheme in ("light", "dark"):
            for width, height in ((1280, 800), (390, 844)):
                page = browser.new_page(viewport={"width": width, "height": height}, color_scheme=scheme)
                page.goto("http://127.0.0.1:8300/", wait_until="load")
                page.evaluate(LINT)
                findings = page.evaluate("() => clankerDesignLint().findings")
                errors = [f for f in findings if f["severity"] == "error"]
                assert not errors, errors
                page.close()
        browser.close()
```

```js
import fs from "node:fs/promises"
import playwright from "playwright"

const source = await fs.readFile("design-lint.js", "utf8")
const { chromium } = playwright
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 390, height: 844 }, colorScheme: "dark" })
await page.goto("http://127.0.0.1:8300/")
await page.evaluate(source)
const { findings } = await page.evaluate(() => clankerDesignLint())
console.log(findings.filter(f => f.severity === "error"))
await browser.close()
```

`clankerDesignLint(options)` returns `{ findings: [{ rule, severity, selector, message }] }`. `severity` is `error` (fix it) or `warn` (look at the screenshot and decide). `selector` is a CSS path to the element (an `id` when it has one); `message` gives the measured values and the fix. Options:

| Option | Effect |
| --- | --- |
| `rules: ["low-contrast", ...]` | Run only these rules. `clankerDesignLint.rules` lists all. |
| `root: element` | Check only this element and its children (`horizontal-scroll` still measures the page). |
| `ignore: [selector, ...]` or `{ rule: [selector, ...], "*": [...] }` | Skip elements in these selectors, for all rules or for one rule. |
| `coarse: true` | Treat the pointer as touch (default: `matchMedia("(pointer: coarse)")`). Adds the 44 px `small-target` warnings. |

In the markup, `data-lint-ignore` skips the element and its children for all rules, and `data-lint-ignore="button-size-mismatch misaligned"` for the named rules. Use it only for an intended exception, such as a showcase of all button sizes.

Layout shift: `clankerDesignLint.watchShift(options?)` records the position of every visible interactive element (or `options.selector`). Do the interaction, wait for the result to show, then call `stop()`. It returns `{ findings, score }`: a `layout-shift` error for each element that moved by `options.threshold` px (default 1) or more, also when it moved back later. `score` is the sum of the browser `layout-shift` entries in Chromium; Firefox and WebKit do not have this entry type, so `score` is `null` there and the findings come from a `ResizeObserver` and an animation-frame check, which work in all three engines.

```python
page.evaluate("() => { window.watch = clankerDesignLint.watchShift() }")
page.fill("#email", "abc")
page.keyboard.press("Tab")
page.wait_for_selector('[data-slot="field-error"]')
result = page.evaluate("() => window.watch.stop()")
assert not result["findings"], result["findings"]
```

| Rule | Severity | What it finds | Why | Fix |
| --- | --- | --- | --- | --- |
| `button-size-mismatch` | error | Buttons, inputs, and select triggers in one row (the same flex or grid line, or a toolbar, button group, or footer) with different heights. | A row of controls with two heights looks broken. | One `data-size` for the row: `sm` buttons with `data-size="sm"` inputs and select triggers. Icon buttons: `icon` with default, `icon-sm` with `sm`. |
| `multiple-primary` | error | Two or more default-variant buttons in one dialog, card, footer, toolbar, button group, form, or popover. | The user cannot see the main action. | Keep one button without `data-variant`; give the others `outline`, `secondary`, or `ghost`. |
| `text-clipped` | error, warn | Text cut by `overflow: hidden` or `clip` without an ellipsis (error); an ellipsis without a `title`, `aria-label`, or tooltip (warn). | Cut text hides content without a sign. | Let the text wrap (`min-width: 0`, `overflow-wrap`), or truncate with `text-overflow: ellipsis` and a `title` or a `tooltip`. |
| `horizontal-scroll` | error | The page is wider than the viewport; names up to five elements that end outside it. | Phones scroll sideways and cut the layout. | `min-width: 0` on flex and grid children, `flex-wrap: wrap`, one column below `40rem`, or a `scroll-area` or `overflow-x: auto` wrapper for wide tables and code. |
| `small-target` | error, warn | An interactive element under 24×24 px with another target nearer than 24 px (error, WCAG 2.5.8); under 44×44 px with a touch pointer (warn, WCAG 2.5.5). Inline links in text, sliders, and disabled controls are exempt. An absolute `::before` or `::after` with negative insets counts as hit area. | Small targets close together cause wrong clicks. | `data-size="icon"` or larger, a `gap` of `0.5rem` or more, or a larger hit area. |
| `low-contrast` | error, warn | Text contrast from the computed colors (`oklch`, `color-mix`, `light-dark`, alpha layers) under WCAG AA: 4.5:1, or 3:1 for large text. Under 3:1 is an error, from 3:1 to AA a warning. Disabled controls are exempt; text on images or gradients is skipped. | Users cannot read it. | `--foreground` or `--muted-foreground` on `--background`, `--card`, `--muted`; `--primary-foreground` on `--primary`. Do not lower the opacity of text. |
| `non-token-color` | warn | A text, background, or border color that matches no `--*` custom property in scope (alpha variants of a token match). One finding per color, with the number of elements. | Hard-coded colors break dark mode and themes. | Use a kit token, or define an app token in `:root` and in dark mode and use it. |
| `missing-label` | error | Buttons, links, inputs, selects, and ARIA widgets without an accessible name; images without `alt`. | Screen readers announce "button" only. | Visible text, `<label for>`, `field-label`, or `aria-label` on icon buttons; `alt=""` for decoration. |
| `heading-order` | warn | A heading level that skips a level (h2 to h4), and a second h1. | The outline of the page is broken for assistive technology. | One h1; the next level for each nested section. Style with classes, not with the level. |
| `misaligned` | warn | Stacked siblings whose start edges differ by 1 to 7 px. Centered and end-aligned stacks are exempt. | Almost-aligned edges look like a mistake. | The same `margin` and `padding` on both, or the same container padding. |
| `empty-region` | warn | A card or column in a grid or flex row with 96 px or more (and 25 % or more of the row) empty below its content while a neighbor fills the row. | A short card next to a tall one leaves a hole. | Move content into it, stack two cards in the column, `align-items: start` with less height, or one column. |
| `layout-shift` | error | From `watchShift()`: interactive elements that moved during the interaction. | Controls that jump make the user click the wrong one (for example an error message that shows on blur and pushes the Save button). | Keep the space for messages (`min-height`), or show them where they do not push controls (beside the field, a `toast`). |

Known results on kit parts (shadcn values that the kit keeps for parity): `low-contrast` warnings for `kbd` and muted text on `--muted` (4.35:1), the destructive button and badge (3.99:1), and the status badges and alerts; a `low-contrast` error for `trace-description` (2.71:1); a `small-target` error for `sidebar-menu-action` (20 px) from the `md` breakpoint.
