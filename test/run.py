import sys

sys.dont_write_bytecode = True

import argparse
import ast
import importlib.util
import os
import pathlib
import re
import time
import traceback

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIDTHS = {1280: 800, 390: 844}
WEBKIT_REFUSED_STYLE = "console.error: Refused to apply a stylesheet because its hash, its nonce, or 'unsafe-inline' does not appear in the style-src directive of the Content Security Policy."
WATCH = """
const watch = JSON.parse(sessionStorage.getItem("clanker-watch") || '{"violations":[],"selects":0,"errors":[]}')
const save = () => sessionStorage.setItem("clanker-watch", JSON.stringify(watch))
window.__clankerWatch = watch
addEventListener("error", e => {
  watch.errors.push(e.message || String(e.error))
  save()
})
document.addEventListener("securitypolicyviolation", e => {
  watch.violations.push(`${e.violatedDirective} blocked ${e.blockedURI || "inline"} at ${e.sourceFile || "?"}:${e.lineNumber || 0} ${e.sample || ""} on <${e.target?.localName ?? "document"}>`)
  save()
})
const create = Document.prototype.createElement
Document.prototype.createElement = function (name, ...rest) {
  if (String(name).toLowerCase() === "select") {
    watch.selects++
    save()
  }
  return create.call(this, name, ...rest)
}
"""


TODAY = """
(() => {
  const Real = Date
  const shift = new Real(2026, 9, 28, 12).getTime() - Real.now()
  function Pinned(...args) {
    if (!new.target) return new Pinned().toString()
    return args.length ? new Real(...args) : new Real(Real.now() + shift)
  }
  Pinned.prototype = Real.prototype
  Pinned.now = () => Real.now() + shift
  Pinned.parse = Real.parse
  Pinned.UTC = Real.UTC
  globalThis.Date = Pinned
})()
"""


RTL = """
document.addEventListener("readystatechange", () => {
  if (document.readyState === "interactive") document.documentElement.dir = "rtl"
})
"""


PAINT = """([ms, arg]) => {
  const sample = window.__clankerSample
  const probe = document.createElement("div")
  probe.setAttribute("aria-hidden", "true")
  Object.assign(probe.style, { position: "fixed", left: "-10px", top: "-10px", width: "1px", height: "1px", pointerEvents: "none" })
  document.body.append(probe)
  const frames = []
  const start = performance.now()
  let n = 0
  window.__clankerPaint = new Promise(resolve => {
    const observer = new ResizeObserver(() => {
      try {
        frames.push(sample(arg))
      } finally {
        if (performance.now() - start >= ms) {
          observer.disconnect()
          probe.remove()
          resolve(frames)
        }
      }
    })
    observer.observe(probe)
    const tick = () => {
      probe.style.width = `${++n % 2 + 1}px`
      if (performance.now() - start < ms + 100) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  })
}"""


A11Y = """() => new Promise((resolve, reject) => {
  if (document.querySelector('link[href="/clanker-ui-a11y.css"]')) return resolve()
  const link = document.createElement("link")
  link.rel = "stylesheet"
  link.href = "/clanker-ui-a11y.css"
  link.onload = () => resolve()
  link.onerror = () => reject(new Error("clanker-ui-a11y.css did not load"))
  document.head.append(link)
})"""


class Skip(Exception):
    pass


class Starved(Skip):
    pass


class T:
    Starved = Starved

    def __init__(self, page, engine, theme, width, out, module, name, reduced_motion, rtl, base_url):
        self.page = page
        self.base_url = base_url
        self.engine = engine
        self.theme = theme
        self.width = width
        self.mobile = width < 768
        self.reduced_motion = reduced_motion
        self.rtl = rtl
        self.out = out
        self.module = module
        self.name = name
        self.allowed = []
        self.shots = 0
        self.current = None

    def docs(self, path):
        response = self.page.goto(self.base_url + path, wait_until="load")
        if response is None or response.status not in (200, 304):
            raise AssertionError(f"{path} returned {response and response.status}")
        self.current = None
        return response

    def section(self, section_id):
        loc = self.page.locator(f"#{section_id}")
        loc.scroll_into_view_if_needed()
        self.current = loc
        return loc

    def shot(self, name=None, target=None):
        folder = self.out / self.engine / f"{self.theme}-{self.width}" / self.module
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name or self.name}.png"
        target = target or self.current or self.page
        element = target is not self.page
        if element:
            self.page.evaluate("() => document.querySelectorAll('[data-demo=header]').forEach(e => e.style.visibility = 'hidden')")
        try:
            target.screenshot(path=str(path), animations="disabled", caret="initial")
        finally:
            if element:
                self.page.evaluate("() => document.querySelectorAll('[data-demo=header]').forEach(e => e.style.visibility = '')")
        self.shots += 1
        return path

    def expect_console(self, pattern):
        self.allowed.append(re.compile(pattern, re.I))

    def settle(self, timeout=2000):
        self.page.wait_for_function(
            "() => document.getAnimations().every(a => a.playState !== 'running' || a.timeline !== document.timeline || a.effect?.getComputedTiming().endTime === Infinity || !a.effect?.target?.checkVisibility({ contentVisibilityAuto: true }))",
            timeout=timeout,
        )

    def paint(self, sample, action, arg=None, ms=800):
        self.page.evaluate(f"() => {{ window.__clankerSample = {sample} }}")
        self.page.evaluate(PAINT, [ms, arg])
        action()
        frames = self.page.evaluate("() => window.__clankerPaint")
        if os.environ.get("GITHUB_ACTIONS") and len(frames) < ms / 100:
            raise Starved(f"the runner painted {len(frames)} frames in {ms} ms; paint-sampled motion needs at least 10 frames per second")
        return frames

    def skip(self, reason):
        raise Skip(reason)

    def a11y(self):
        self.page.evaluate(A11Y)
        self.settle()


class Explain(ast.NodeTransformer):
    def __init__(self, source):
        self.source = source

    def visit_Assert(self, node):
        if node.msg is not None:
            return node
        text = ast.get_source_segment(self.source, node.test) or "assertion"
        test = node.test
        if not (isinstance(test, ast.Compare) and len(test.ops) == 1):
            node.msg = ast.Constant(text)
            return node
        got, want = (ast.Name("_assert_got", ast.Load()), ast.Name("_assert_want", ast.Load()))
        stmts = [
            ast.Assign([ast.Name("_assert_got", ast.Store())], test.left),
            ast.Assign([ast.Name("_assert_want", ast.Store())], test.comparators[0]),
            ast.Assert(ast.Compare(got, test.ops, [want]), ast.Call(ast.Name("_explain", ast.Load()), [ast.Constant(text), ast.Constant(OPS.get(type(test.ops[0]), "")), got, want], [])),
        ]
        return [ast.copy_location(stmt, node) for stmt in stmts]


OPS = {ast.Eq: "", ast.NotEq: "not ", ast.Lt: "< ", ast.LtE: "<= ", ast.Gt: "> ", ast.GtE: ">= ", ast.Is: "is ", ast.IsNot: "is not ", ast.In: "in ", ast.NotIn: "not in "}


def explain(text, op, got, want):
    short = lambda v: (r if len(r := repr(v)) <= 400 else r[:400] + "...")
    return f"{text}\n    got:      {short(got)}\n    expected: {op}{short(want)}"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    source = path.read_text()
    mod._explain = explain
    tree = ast.fix_missing_locations(Explain(source).visit(ast.parse(source)))
    exec(compile(tree, str(path), "exec"), mod.__dict__)
    return mod


def discover(only):
    files = sorted((ROOT / "test").glob("*_test.py"))
    if only:
        files = [f for f in files if any(f.stem.startswith(o) for o in only)]
    modules = []
    for f in files:
        mod = load(f"clanker_{f.parent.name}_{f.stem}", f)
        checks = [(n.removeprefix("check_"), fn) for n, fn in vars(mod).items() if n.startswith("check_") and callable(fn)]
        modules.append((f.stem.removesuffix("_test"), checks, getattr(mod, "START", "/demo")))
    return modules


WEBKIT_NOISE = re.compile(r"(style-src-elem|style-src-attr) blocked inline at (\?|web-inspector://[^ ]*):\d+ .* on <(\w+)>")


def drop_webkit_noise(problems, selects):
    out = []
    dropped = 0
    for p in problems:
        m = WEBKIT_NOISE.fullmatch(p)
        directive, target = (m.group(1), m.group(3)) if m else ("", "")
        if directive == "style-src-elem" or (directive == "style-src-attr" and target == "select"):
            dropped += 1
        elif directive == "style-src-attr" and target == "document" and selects:
            selects -= 1
            dropped += 1
        else:
            out.append(p)
    kept = []
    for p in out:
        if dropped and p == WEBKIT_REFUSED_STYLE:
            dropped -= 1
        else:
            kept.append(p)
    return kept


def run_check(browser, args, engine, theme, width, module, name, fn, start):
    context = browser.new_context(
        viewport={"width": width, "height": WIDTHS[width]},
        color_scheme=theme,
        reduced_motion="reduce" if args.reduced_motion else "no-preference",
    )
    context.add_init_script(WATCH)
    context.add_init_script(TODAY)
    if args.rtl:
        context.add_init_script(RTL)
    page = context.new_page()
    problems = []
    page.on("console", lambda m: problems.append(f"console.{m.type}: {m.text}") if m.type in ("error", "warning", "assert") else None)
    page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    page.on("requestfailed", lambda r: problems.append(f"requestfailed: {r.url} {r.failure}"))
    page.on("response", lambda r: problems.append(f"http {r.status}: {r.url}") if r.status >= 400 else None)
    base_url = args.base_url.rstrip("/")
    t = T(page, engine, theme, width, args.out, module, name, args.reduced_motion, args.rtl, base_url)
    status, detail = "pass", ""
    try:
        response = page.goto(base_url + start, wait_until="load")
        if response is None or response.status != 200:
            raise AssertionError(f"{start} returned {response and response.status}")
        fn(t)
        if t.current is not None and t.shots == 0:
            t.shot()
    except Skip as e:
        status, detail = "skip", str(e)
    except Exception as e:
        status = "fail"
        detail = "".join(traceback.format_exception_only(e)).strip()
        frame = next((f for f in reversed(traceback.extract_tb(e.__traceback__)) if pathlib.Path(f.filename).parent == ROOT / "test"), None)
        if frame:
            detail = f"{pathlib.Path(frame.filename).name}:{frame.lineno}: {detail}"
        if not isinstance(e, AssertionError):
            detail += "\n" + "".join(traceback.format_tb(e.__traceback__)[-3:])
        try:
            t.shot(f"{name}-failure", page)
        except PlaywrightError:
            pass
    watch = {"violations": [], "selects": 0, "errors": []}
    try:
        if engine == "webkit":
            refused = problems.count(WEBKIT_REFUSED_STYLE)
            page.wait_for_function("n => (window.__clankerWatch?.violations.length ?? 0) >= n", arg=refused, timeout=1000)
    except PlaywrightError:
        pass
    try:
        watch = page.evaluate("() => window.__clankerWatch || { violations: [], selects: 0, errors: [] }")
        problems += watch["violations"] + [f"window error: {m}" for m in watch["errors"]]
    except PlaywrightError:
        pass
    context.close()
    if engine == "webkit":
        problems = drop_webkit_noise(problems, watch["selects"])
    return verdict(status, detail, problems, t.allowed)


def verdict(status, detail, problems, allowed):
    unexpected = [p for p in problems if not any(a.search(p) for a in allowed)]
    if unexpected:
        status = "fail"
        detail = (detail + "\n" if detail else "") + "\n".join(unexpected)
    return status, detail


def main():
    ap = argparse.ArgumentParser(description="clanker-ui browser checks")
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--engines", default="chromium,firefox,webkit")
    ap.add_argument("--themes", default="light,dark")
    ap.add_argument("--widths", default="1280,390")
    ap.add_argument("--only", default="", help="comma-separated test file prefixes, for example g1 or foundation")
    ap.add_argument("-k", default="", help="regex on check names")
    ap.add_argument("--out", default=os.environ.get("CLANKER_UI_OUT") or str(pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / "clanker-ui-shots"))
    ap.add_argument("--reduced-motion", action="store_true")
    ap.add_argument("--rtl", action="store_true", help="set dir=rtl on <html>")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    args.out = pathlib.Path(args.out)
    only = [o for o in args.only.split(",") if o]
    pattern = re.compile(args.k) if args.k else None
    modules = discover(only)
    if not modules:
        print("no test files found")
        return 1
    themes = [t for t in args.themes.split(",") if t]
    widths = [int(w) for w in args.widths.split(",") if w]
    results = {}
    unavailable = {}
    failures = []
    started = time.time()
    with sync_playwright() as pw:
        for engine in [e for e in args.engines.split(",") if e]:
            counts = {"pass": 0, "fail": 0, "skip": 0}
            for theme in themes:
                options = {"headless": not args.headed}
                if engine == "firefox":
                    options["firefox_user_prefs"] = {
                        "layout.css.prefers-color-scheme.content-override": 0 if theme == "dark" else 1,
                        "privacy.bounceTrackingProtection.mode": 0,
                    }
                try:
                    browser = getattr(pw, engine).launch(**options)
                except Exception as e:
                    unavailable[engine] = str(e).splitlines()[0]
                    print(f"[{engine}] could not start: {unavailable[engine]}")
                    break
                for width in widths:
                    for module, checks, start in modules:
                        for name, fn in checks:
                            if pattern and not pattern.search(f"{module}.{name}"):
                                continue
                            status, detail = run_check(browser, args, engine, theme, width, module, name, fn, start)
                            counts[status] += 1
                            label = f"[{engine} {theme} {width}] {module}.{name}"
                            if status == "fail":
                                failures.append((label, detail))
                                print(f"FAIL {label}\n  " + detail.replace("\n", "\n  "))
                            elif status == "skip":
                                print(f"skip {label}: {detail}")
                            else:
                                print(f"ok   {label}")
                browser.close()
            if engine not in unavailable:
                results[engine] = counts
    print(f"\nscreenshots: {args.out}")
    for engine, c in results.items():
        print(f"{engine}: {c['pass']} passed, {c['fail']} failed, {c['skip']} skipped")
    for engine, reason in unavailable.items():
        print(f"{engine}: NOT RUN ({reason})")
    print(f"{len(failures)} failures in {time.time() - started:.1f}s")
    return 1 if failures or not results else 0


if __name__ == "__main__":
    sys.exit(main())
