import json
import pathlib

START = "/test/lint/good.html"

HERE = pathlib.Path(__file__).resolve().parent
LINT_FILE = HERE.parent / "skills/clanker-ui/references/design-lint.js"
LINT = LINT_FILE.read_text()
KNOWN = {rule: list(selectors) for rule, selectors in json.loads((HERE / "lint/known.json").read_text()).items()}
MARKUP_FILE = HERE.parent / "skills/clanker-ui/references/markup-lint.js"
MARKUP_PAGE = "/test/lint/markup.html"
DEV_SCRIPT = '<script src="/skills/clanker-ui/references/markup-lint.js"></script>'

FORMS = '  <script type="module" src="/clanker-ui-forms.min.js"></script>\n'
CLASSES = '#card-content'
MUTATIONS = {
    "unknown-slot": [
        (('data-slot="card-title"', 'data-slot="card-heading"'), [("error", '#card-header > div[data-slot="card-heading"]')]),
        (('<main>', '<main>\n    <template><div data-slot="card-titel"></div></template>'), [("error", 'div[data-slot="card-titel"]')]),
    ],
    "part-outside-root": [(('<div data-slot="dialog" id="settings">', '<div id="settings">'), [("error", "#settings-content")])],
    "unknown-attr": [
        (('data-orientation="horizontal"', 'data-orientaton="horizontal"'), [("error", "#alerts-field")]),
        (('<div data-slot="card-title">', '<div data-slot="card-title" data-variant="outline">'), [("error", '#card-header > div[data-slot="card-title"]')]),
    ],
    "bad-value": [
        (('data-variant="outline"', 'data-variant="primary"'), [("error", "#open")]),
        (('data-orientation="horizontal"', 'data-orientation="horizontal" data-disabled'), [("error", "#alerts-field")]),
        (('data-dialog-trigger id="open"', 'data-dialog-trigger="nope" id="open"'), [("error", "#open")]),
        (('id="settings-content"', 'id="settings-content" data-side-offset="near"'), [("error", "#settings-content")]),
    ],
    "kit-added": [
        (('aria-label="Alerts"></button>', 'aria-label="Alerts"><span data-slot="switch-thumb"></span></button>'), [("error", '#alerts > span[data-slot="switch-thumb"]')]),
        (('id="settings-content"', 'id="settings-content" data-open'), [("error", "#settings-content")]),
    ],
    "missing-group": [
        (('  <script type="module" src="/clanker-ui-overlays.min.js"></script>\n', ""), [("error", "#settings")]),
        ((FORMS, FORMS + '  <link rel="modulepreload" href="/clanker-ui-chart.js">\n'), [("error", "html")] * 2),
        ((FORMS, FORMS + '  <link rel="modulepreload" href="/clanker-ui.min.js">\n'), [("error", "html")]),
    ],
    "unknown-class": [
        (('class="row"', 'class="row mt-4"'), [("error", CLASSES)]),
        (('class="row"', 'class="row md:flex"'), [("error", CLASSES)]),
        (('class="row"', 'class="row fancy"'), [("warn", CLASSES)]),
        (('class="row"', 'class="row autosave fullscreen-toggle step-2"'), [("warn", CLASSES)] * 3),
        (('class="row"', 'class="row top-bar text-block items-list left-panel"'), [("warn", CLASSES)] * 4),
        (('class="row"', 'class="row text-red-500 items-center p-1/2 text-2xl"'), [("error", CLASSES)] * 4),
        (('class="row"', 'class="row text-muted-foreground bg-primary border-input ring-ring/50"'), [("error", CLASSES)] * 4),
    ],
}
IGNORED = [
    ('<main>', '<main>\n    <template><div data-slot="select-item" data-value="x">X</div><dialog data-slot="dialog-content"></dialog></template>'),
    ('<main>', '<main>\n    <template><button type="button" data-slot="button" data-dialog-trigger="later"></button><div data-slot="dialog" id="later"></div></template>'),
    ('class="row"', 'class="row mt-4" data-lint-ignore="unknown-class"'),
    ('<div data-slot="card-title">', '<div data-slot="card-title" data-lint-ignore data-variant="outline">'),
]

BAD = {
    "button-size-mismatch": [("error", "#bad-size-sm"), ("error", "#bad-toggle-sm"), ("error", "#bad-search-group"), ("error", "#bad-native-sm")],
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
        if rule == "empty-region":
            hints = {f["selector"]: f["message"].endswith("align the row to start") for f in got}
            assert hints == ({} if t.mobile else {"#printhub-side": False, "#printhub-stretched": True}), ("only a stretched item gets the align-to-start hint", hints)
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


def check_lint_blocks(t):
    for name in sorted(p.stem for p in (HERE.parent / "skills/clanker-ui/references/blocks").glob("*.html")):
        t.docs(f"/blocks/{name}")
        inject(t)
        found = [f for f in lint(t) if f["severity"] == "error" or f["rule"] in ("empty-region", "low-contrast")]
        assert found == [], (name, short(found))


def check_lint_board_recipe(t):
    recipes = (HERE.parent / "skills/clanker-ui/references/recipes.md").read_text()
    board = recipes.split("## Board (columns of cards)", 1)[1].split("```html\n", 1)[1].split("\n```", 1)[0]
    page = (HERE / "lint/good.html").read_text()
    assert "\n".join("      " + line if line else line for line in board.split("\n")) in page, "the board recipe is in test/lint/good.html"
    assert ".board { align-items: start; }" in (HERE / "lint/lint.css").read_text() and ".board { align-items: start; }" in recipes
    t.docs(START)
    columns = t.page.locator("#board-recipe .board > [data-slot=card]").evaluate_all("cards => cards.map(c => Math.round(c.getBoundingClientRect().height))")
    assert len(columns) == 3 and (t.mobile or columns[0] > columns[1]), ("each column is as high as its cards", columns)



def markup_page(t, mutation=None, dev=None):
    def handle(route):
        response = route.fetch()
        body = response.text()
        if mutation:
            assert mutation[0] in body, mutation
            body = body.replace(mutation[0], mutation[1], 1)
        if dev:
            body = body.replace("</title>", "</title>\n  " + dev, 1)
        route.fulfill(response=response, body=body)

    t.page.route("**" + MARKUP_PAGE, handle)
    t.docs(MARKUP_PAGE)
    t.page.unroute("**" + MARKUP_PAGE)
    t.page.wait_for_function("() => document.querySelector('#alerts')?.dataset.state")


def markup(t, options=None):
    return [(f["rule"], f["severity"], f["selector"]) for f in t.page.evaluate("o => clankerMarkupLint(o).findings", options or {})]


def check_markup_lint_good(t):
    t.page.context.add_init_script(path=str(MARKUP_FILE))
    markup_page(t)
    assert t.page.evaluate("() => clankerMarkupLint.rules") == list(MUTATIONS)
    assert t.page.evaluate("() => document.querySelector('#alerts').dataset.state") == "unchecked", "the kit ran before the lint"
    assert markup(t) == [], "the authored snapshot predates the kit module"
    for mutation in IGNORED:
        markup_page(t, mutation)
        assert markup(t) == [], ("data-lint-ignore", mutation)


def check_markup_lint_mutations(t):
    t.page.context.add_init_script(path=str(MARKUP_FILE))
    for rule, cases in MUTATIONS.items():
        for mutation, want in cases:
            markup_page(t, mutation)
            got = markup(t)
            assert got == [(rule, severity, selector) for severity, selector in want], (rule, mutation, got)
            assert all(f["message"] for f in t.page.evaluate("() => clankerMarkupLint().findings"))


def check_markup_lint_late(t):
    markup_page(t)
    t.page.evaluate(MARKUP_FILE.read_text())
    assert markup(t) == [("late-load", "error", "html")], "a lint injected after load has no authored snapshot"
    late = t.page.evaluate("() => clankerMarkupLint().findings[0].message")
    for script in (DEV_SCRIPT.replace("<script ", '<script type="module" '), DEV_SCRIPT.replace("<script ", "<script defer ")):
        logged = dev_page(t, script)
        assert logged == [("error", "clanker-ui markup: late-load html: " + late)], (script, logged)


def dev_page(t, script, mutation=None):
    logged = []
    listener = lambda m: m.text.startswith("clanker-ui markup:") and logged.append((m.type, m.text))
    t.page.on("console", listener)
    t.expect_console(r"^console\.(error|warning): clanker-ui markup: ")
    markup_page(t, mutation, script)
    t.page.wait_for_function("() => document.readyState === 'complete'")
    t.page.wait_for_timeout(100)
    t.page.remove_listener("console", listener)
    return logged


def check_markup_lint_dev(t):
    logged = dev_page(t, DEV_SCRIPT, MUTATIONS["unknown-class"][2][0])
    assert logged == [("warning", 'clanker-ui markup: unknown-class #card-content: class "fancy" matches no rule in the page stylesheets; add a rule in app.css or remove it')], logged


def check_markup_lint_blocks(t):
    t.page.context.add_init_script(path=str(MARKUP_FILE))
    for name in sorted(p.stem for p in (HERE.parent / "skills/clanker-ui/references/blocks").glob("*.html")):
        t.docs(f"/blocks/{name}")
        assert markup(t) == [], name
