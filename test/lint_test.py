import json
import pathlib

START = "/test/lint/good.html"

HERE = pathlib.Path(__file__).resolve().parent
LINT_FILE = HERE.parent / "skills/clanker-ui/references/design-lint.js"
LINT = LINT_FILE.read_text()
KNOWN = {rule: list(selectors) for rule, selectors in json.loads((HERE / "lint/known.json").read_text()).items()}

BAD = {
    "button-size-mismatch": [("error", "#bad-size-sm")],
    "multiple-primary": [("error", "#bad-second-primary")],
    "text-clipped": [("error", "#bad-clip"), ("warn", "#bad-ellipsis")],
    "horizontal-scroll": [("error", "#bad-wide")],
    "small-target": [("error", "#bad-tiny"), ("error", "#bad-tiny-next")],
    "low-contrast": [("error", "#bad-faint"), ("warn", "#bad-dim")],
    "non-token-color": [("warn", "#bad-pink")],
    "missing-label": [("error", "#bad-icon-button"), ("error", "#bad-input"), ("error", "#bad-image")],
    "heading-order": [("warn", "#bad-h4"), ("warn", "#bad-h1")],
    "misaligned": [("warn", "#bad-nudge")],
    "empty-region": [("warn", "#printhub-side"), ("warn", "#printhub-stretched")],
}

def inject(t):
    t.page.evaluate(LINT)
    assert t.page.evaluate("() => typeof clankerDesignLint === 'function' && clankerDesignLint.rules.length") == len(BAD)


def lint(t, options=None):
    return t.page.evaluate("o => clankerDesignLint(o).findings", options or {})


def short(findings):
    return [(f["rule"], f["severity"], f["selector"]) for f in findings]


def shift(t, input_id, save_id):
    page = t.page
    page.evaluate("() => { window.__clankerShift = clankerDesignLint.watchShift() }")
    page.locator(input_id).fill("abc")
    page.keyboard.press("Tab")
    page.wait_for_function(f"() => document.activeElement?.matches('{save_id}') && document.querySelector('[data-slot=field-error]')?.checkVisibility()")
    page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
    return page.evaluate("() => window.__clankerShift.stop()")


def check_lint_good_page(t):
    t.page.context.add_init_script(path=str(LINT_FILE))
    t.docs(START)
    assert t.page.evaluate("() => clankerDesignLint.rules.length") == len(BAD)
    assert short(lint(t)) == []
    result = shift(t, "#good-email", "#good-shift-save")
    assert short(result["findings"]) == []
    assert (result["score"] is None) == (t.engine != "chromium")


def check_lint_bad_cases(t):
    t.docs("/test/lint/bad.html")
    inject(t)
    for rule, want in BAD.items():
        root = "body" if rule == "heading-order" else f"#bad-{rule}" if t.page.locator(f"#bad-{rule}").count() else "#printhub-empty-region"
        got = t.page.evaluate("([rule, root]) => clankerDesignLint({ rules: [rule], root: document.querySelector(root) }).findings", [rule, root])
        if rule == "empty-region" and t.mobile:
            want = []
        assert sorted((f["severity"], f["selector"]) for f in got) == sorted(want), (rule, short(got))
        assert all(f["message"] for f in got)
    coarse = t.page.evaluate("() => clankerDesignLint({ rules: ['small-target'], root: document.querySelector('#bad-small-target'), coarse: true }).findings")
    assert ("warn", "#bad-touch") in [(f["severity"], f["selector"]) for f in coarse]
    ignored = t.page.evaluate("() => clankerDesignLint({ rules: ['missing-label'], ignore: ['#bad-missing-label'] }).findings")
    assert ignored == []
    result = shift(t, "#bad-email", "#bad-shift-save")
    moved = [f["selector"] for f in result["findings"]]
    assert "#bad-shift-save" in moved and all(f["rule"] == "layout-shift" and f["severity"] == "error" for f in result["findings"]), moved
    if t.engine == "chromium":
        assert result["score"] > 0


def check_lint_demo(t):
    t.docs("/demo")
    t.page.wait_for_function("() => document.querySelectorAll('[data-slot=chart] svg').length > 0")
    inject(t)
    errors = [f for f in lint(t, {"ignore": KNOWN}) if f["severity"] == "error"]
    assert errors == [], short(errors)
