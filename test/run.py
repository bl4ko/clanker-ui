import sys

sys.dont_write_bytecode = True

import argparse
import ast
import contextlib
import functools
import importlib.util
import io
import os
import pathlib
import re
import subprocess
import tempfile
import threading
import time
import traceback

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
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


RUNNING = """() => {
  const where = el => el.dataset?.slot ? `[data-slot="${el.dataset.slot}"]` : `<${el.localName}>`
  return [
    ...document.getAnimations()
      .filter(a => a.playState === "running" && a.timeline === document.timeline && a.effect?.getComputedTiming().endTime !== Infinity && a.effect?.target?.checkVisibility({ contentVisibilityAuto: true }))
      .map(a => `${a.animationName || a.transitionProperty || a.id || a.constructor.name} on ${where(a.effect.target)}${a.effect.pseudoElement || ""} at ${Math.round(a.currentTime)} of ${Math.round(a.effect.getComputedTiming().endTime)} ms`),
    ...[...document.querySelectorAll("[data-starting-style]")].filter(el => el.checkVisibility()).map(el => `starting style on ${where(el)}`),
  ]
}"""


class Skip(Exception):
    pass


class Starved(Skip):
    pass


class T:
    Starved = Starved

    def __init__(self, page, engine, theme, width, out, module, name, reduced_motion, rtl, base_url, shots=False):
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
        self.keep_shots = shots
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

    def shot(self, name=None, target=None, always=False):
        if not (self.keep_shots or always):
            return None
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
        try:
            self.page.wait_for_function(f"() => ({RUNNING})().length === 0", timeout=timeout)
        except PlaywrightTimeout:
            raise AssertionError(f"t.settle: animations still run after {timeout} ms: {'; '.join(self.page.evaluate(RUNNING))}") from None

    def paint(self, sample, action, arg=None, ms=800):
        if os.environ.get("GITHUB_ACTIONS"):
            ms *= 2
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
        text = ast.get_source_segment(self.source, node.test) or "assertion"
        msg = node.msg or ast.Constant(None)
        test = node.test
        if not (isinstance(test, ast.Compare) and len(test.ops) == 1):
            node.msg = ast.Call(ast.Name("_explain_msg", ast.Load()), [ast.Constant(text), msg], [])
            return node
        got, want = (ast.Name("_assert_got", ast.Load()), ast.Name("_assert_want", ast.Load()))
        stmts = [
            ast.Assign([ast.Name("_assert_got", ast.Store())], test.left),
            ast.Assign([ast.Name("_assert_want", ast.Store())], test.comparators[0]),
            ast.Assert(ast.Compare(got, test.ops, [want]), ast.Call(ast.Name("_explain", ast.Load()), [ast.Constant(text), ast.Constant(OPS.get(type(test.ops[0]), "")), got, want, msg], [])),
        ]
        return [ast.copy_location(stmt, node) for stmt in stmts]


OPS = {ast.Eq: "", ast.NotEq: "not ", ast.Lt: "< ", ast.LtE: "<= ", ast.Gt: "> ", ast.GtE: ">= ", ast.Is: "is ", ast.IsNot: "is not ", ast.In: "in ", ast.NotIn: "not in "}


def short(value, limit=400):
    r = value if isinstance(value, str) else repr(value)
    return r if len(r) <= limit else r[:limit] + "..."


def explain_msg(text, msg=None):
    if msg is None:
        return text
    return f"{text}\n    " + short(msg, 2000).replace("\n", "\n    ")


def explain(text, op, got, want, msg=None):
    return explain_msg(f"{text}\n    got:      {short(repr(got))}\n    expected: {op}{short(repr(want))}", msg)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    source = path.read_text()
    mod._explain = explain
    mod._explain_msg = explain_msg
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


@functools.cache
def impact_module():
    spec = importlib.util.spec_from_file_location("clanker_ci_impact", ROOT / "tools" / "ci" / "impact.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    recorder = impact_module().Recorder(context, page, engine, args.base_url) if args.impact else None
    problems = []
    page.on("console", lambda m: problems.append(f"console.{m.type}: {m.text}") if m.type in ("error", "warning", "assert") else None)
    page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    page.on("requestfailed", lambda r: problems.append(f"requestfailed: {r.url} {r.failure}"))
    page.on("response", lambda r: problems.append(f"http {r.status}: {r.url}") if r.status >= 400 else None)
    base_url = args.base_url.rstrip("/")
    t = T(page, engine, theme, width, args.out, module, name, args.reduced_motion, args.rtl, base_url, args.shots)
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
        frame = next((f for f in reversed(traceback.extract_tb(e.__traceback__)) if pathlib.Path(f.filename).parent == ROOT / "test" and pathlib.Path(f.filename).name != "run.py"), None)
        if frame:
            detail = f"{pathlib.Path(frame.filename).name}:{frame.lineno}: {detail}"
        if not isinstance(e, AssertionError):
            detail += "\n" + "".join(traceback.format_tb(e.__traceback__)[-3:])
        try:
            t.shot(f"{name}-failure", page, always=True)
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
    if recorder:
        print(f"impact [{engine} {theme} {width}] {module}.{name}\t{' '.join(sorted(recorder.finish()))}", flush=True)
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


HEAD = re.compile(r"(ok|skip|flaky|FAIL) +(\[(\w+) [^]]*\] \S+?)(?: \((\d+(?:\.\d+)?)s\))?(?:: (.*))?")
TOOK = re.compile(r"took (\d+(?:\.\d+)?)s")
NOT_STARTED = re.compile(r"\[(\w+)\] could not start: (.*)")


def indent(text):
    return "\n  " + text.replace("\n", "\n  ") if text else ""


def result_text(status, label, seconds, detail):
    if status == "fail":
        return f"FAIL {label}" + indent("\n".join(filter(None, [detail, f"took {seconds:.1f}s"])))
    if status == "flaky":
        return f"flaky {label} ({seconds:.1f}s)" + indent(detail)
    if status == "skip":
        return f"skip {label} ({seconds:.1f}s): {detail}"
    return f"ok   {label} ({seconds:.1f}s)"


def parse_result(lines):
    m = HEAD.fullmatch(lines[0])
    if not m:
        return None
    status = {"ok": "pass", "skip": "skip", "flaky": "flaky", "FAIL": "fail"}[m[1]]
    body = [line[2:] for line in lines[1:]]
    seconds = float(m[4] or 0)
    if status == "fail" and body and (took := TOOK.fullmatch(body[-1])):
        seconds = float(took[1])
        body = body[:-1]
    return status, m[2], m[3], seconds, m[5] if status == "skip" else "\n".join(body)


def annotation(kind, title, message):
    data = lambda s: s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return f"::{kind} title={data(title).replace(':', '%3A').replace(',', '%2C')}::{data(short(message, 4000))}"


class Tally:
    def __init__(self):
        self.counts = {}
        self.failures = []
        self.flaky = []
        self.times = []
        self.unavailable = {}

    def engine(self, engine):
        return self.counts.setdefault(engine, {"pass": 0, "fail": 0, "skip": 0, "flaky": 0})

    def add(self, engine, label, status, seconds, detail):
        counts = self.engine(engine)
        counts["pass" if status == "flaky" else status] += 1
        if status == "flaky":
            counts["flaky"] += 1
            self.flaky.append(label)
        if status == "fail":
            self.failures.append((label, detail))
        self.times.append((seconds, label))

    def summary(self, out, elapsed):
        print(f"\noutput: {out}")
        if self.times:
            print("slowest:")
            for seconds, label in sorted(self.times, reverse=True)[:10]:
                print(f"  {seconds:6.1f}s {label}")
        if self.flaky:
            print("flaky (passed on retry): " + ", ".join(self.flaky))
        for engine, c in self.counts.items():
            if engine not in self.unavailable:
                flaky = f" ({c['flaky']} flaky)" if c["flaky"] else ""
                print(f"{engine}: {c['pass']} passed{flaky}, {c['fail']} failed, {c['skip']} skipped")
        for engine, reason in self.unavailable.items():
            print(f"{engine}: NOT RUN ({reason})")
        print(f"{len(self.failures)} failures in {elapsed:.1f}s")
        return 1 if self.failures or len(self.unavailable) == len(self.counts) else 0


def attempt(engine, label, run, tally, retry=False, annotate=False):
    started = time.monotonic()
    status, detail = run()
    if status == "fail" and retry:
        first = detail
        status, detail = run()
        if status == "pass":
            status, detail = "flaky", first
        elif status == "skip":
            detail += " (the first run failed: " + first.splitlines()[0] + ")"
    seconds = time.monotonic() - started
    print(result_text(status, label, seconds, detail), flush=True)
    if annotate and status in ("fail", "flaky"):
        print(annotation("error" if status == "fail" else "warning", f"{'FAIL' if status == 'fail' else 'flaky'} {label}", detail), flush=True)
    tally.add(engine, label, status, seconds, detail)
    return status


def run_variants(variants, tally, retry=False, exitfirst=False, annotate=False):
    for engine, label, run in variants:
        if attempt(engine, label, run, tally, retry, annotate) == "fail" and exitfirst:
            return True
    return False


def selected(modules, widths, pattern):
    for width in widths:
        for module, checks, start in modules:
            for name, fn in checks:
                if not pattern or pattern.search(f"{module}.{name}"):
                    yield width, module, name, fn, start


def run_serial(args, engines, themes, widths, modules, pattern, tally):
    annotate = bool(os.environ.get("GITHUB_ACTIONS"))
    with sync_playwright() as pw:
        for engine in engines:
            tally.engine(engine)
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
                    tally.unavailable[engine] = str(e).splitlines()[0]
                    print(f"[{engine}] could not start: {tally.unavailable[engine]}", flush=True)
                    break
                variants = ((engine, f"[{engine} {theme} {width}] {module}.{name}", functools.partial(run_check, browser, args, engine, theme, width, module, name, fn, start)) for width, module, name, fn, start in selected(modules, widths, pattern))
                try:
                    if run_variants(variants, tally, args.retry, args.exitfirst, annotate):
                        return
                finally:
                    browser.close()


def child_args(args):
    out = ["--base-url", args.base_url, "--themes", args.themes, "--widths", args.widths, "--only", args.only, "--out", str(args.out)]
    if args.k:
        out += ["-k", args.k]
    return out + [f"--{name.replace('_', '-')}" for name in ("reduced_motion", "rtl", "headed", "shots", "retry", "exitfirst", "impact") if getattr(args, name)]


def run_parallel(args, engines, tally):
    lock = threading.Lock()
    procs = {}
    stopped = set()
    stop = threading.Event()

    def handle(group):
        print("\n".join(group), flush=True)
        if m := NOT_STARTED.fullmatch(group[0]):
            tally.unavailable[m[1]] = m[2]
            return
        result = parse_result(group)
        if result is None:
            return
        status, label, engine, seconds, detail = result
        tally.add(engine, label, status, seconds, detail)
        if status == "fail" and args.exitfirst and not stop.is_set():
            stop.set()
            for other, proc in procs.items():
                if other != engine and proc.poll() is None:
                    stopped.add(other)
                    proc.terminate()

    def child(engine):
        cmd = [sys.executable, "-I", "-u", str(pathlib.Path(__file__).resolve()), "--child", "--engines", engine] + child_args(args)
        with lock:
            if stop.is_set():
                return
            proc = procs[engine] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        group = []
        for line in proc.stdout:
            line = line.rstrip("\n")
            with lock:
                if group and line.startswith("  "):
                    group.append(line)
                    continue
                if group:
                    handle(group)
                group = [line]
                if line.startswith(("ok ", "skip ")):
                    handle(group)
                    group = []
        with lock:
            if group:
                handle(group)
        code = proc.wait()
        with lock:
            if code and engine not in stopped and not any(label.startswith(f"[{engine} ") for label, _ in tally.failures) and engine not in tally.unavailable:
                tally.failures.append((f"[{engine}] run.py", f"exit code {code}"))

    for engine in engines:
        tally.engine(engine)
    threads = [threading.Thread(target=child, args=(e,)) for e in engines]
    running = []
    for th in threads:
        while len([r for r in running if r.is_alive()]) >= args.jobs:
            time.sleep(0.2)
        th.start()
        running.append(th)
    for th in threads:
        th.join()


def list_checks(modules, pattern):
    names = [f"{module}.{name}" for _, module, name, _, _ in selected(modules, [0], pattern)]
    print("\n".join(names + [f"{len(names)} checks"]))
    return 0


def self_test():
    started = time.monotonic()
    count = 0

    def case(ok, message):
        nonlocal count
        assert ok, message
        count += 1

    refused = WEBKIT_REFUSED_STYLE
    quirks = [
        "style-src-attr blocked inline at ?:0  on <select>",
        "style-src-attr blocked inline at web-inspector://bootstrap.js:12  on <select>",
        "style-src-attr blocked inline at web-inspector://bootstrap.js:12  on <document>",
        "style-src-elem blocked inline at ?:0  on <document>",
    ]
    case(drop_webkit_noise(quirks + [refused] * 4, 1) == [], "WebKit select and screenshot reports must be dropped")
    kit = [
        "style-src-attr blocked inline at http://127.0.0.1:8141/clanker-ui.js:10  on <select>",
        "style-src-attr blocked inline at http://127.0.0.1:8141/clanker-ui.js:10  on <document>",
        "style-src-elem blocked inline at http://127.0.0.1:8141/clanker-ui.js:10  on <style>",
        "style-src-attr blocked inline at ?:0  on <div>",
        "script-src-elem blocked inline at ?:0  on <script>",
    ]
    case(drop_webkit_noise(kit + [refused] * len(kit), 5) == kit + [refused] * len(kit), "kit violations must stay")
    extra = "style-src-attr blocked inline at ?:0  on <document>"
    case(drop_webkit_noise([extra, extra], 1) == [extra], "document reports are bounded by the selects created by script")
    status, detail = verdict("skip", "desktop only", ["console.error: boom"], [])
    case(status == "fail" and "boom" in detail, "a skip must keep the console errors collected before it")
    case(verdict("skip", "desktop only", ["console.error: boom"], [re.compile("boom")]) == ("skip", "desktop only"), "allowed messages must not fail a skip")

    source = """
def motion(end, final):
    assert end[1:3] == [1, "open"] and abs(end[0] - final) <= 1, (end, final)
def named(x):
    assert x == 2, f"x is {x}"
def bare(items):
    assert len(items) > 3
def plain(x):
    assert x
"""
    scope = {"_explain": explain, "_explain_msg": explain_msg}
    exec(compile(ast.fix_missing_locations(Explain(source).visit(ast.parse(source))), "<self-test>", "exec"), scope)

    def message(fn, *a):
        try:
            fn(*a)
        except AssertionError as e:
            return str(e)
        return None

    case(message(scope["motion"], [936, 0, "open"], 896) == 'end[1:3] == [1, "open"] and abs(end[0] - final) <= 1\n    ([936, 0, \'open\'], 896)', "an assert with a tuple message shows its source and the values")
    case(message(scope["named"], 3) == "x == 2\n    got:      3\n    expected: 2\n    x is 3", "a compare with a message shows the values and the message")
    case(message(scope["bare"], [1]) == "len(items) > 3\n    got:      1\n    expected: > 3", "a bare compare shows the values")
    case(message(scope["plain"], 0) == "x", "a bare assert shows its source")
    case(message(scope["named"], 2) is None, "a passing assert raises nothing")

    label = "[chromium light 1280] g2.sheet_motion"
    ci = re.compile(r"^FAIL \[[^]]+\] ([a-z0-9_]+\.[a-z0-9_]+)$")
    text = result_text("fail", label, 12.34, "g2_test.py:294: AssertionError: x\n    got: 1")
    case(ci.match(text.splitlines()[0])[1] == "g2.sheet_motion", "the FAIL line keeps the format that ci.yml reads")
    case(parse_result(text.splitlines()) == ("fail", label, "chromium", 12.3, "g2_test.py:294: AssertionError: x\n    got: 1"), "a FAIL block parses back")
    for status, detail in (("pass", ""), ("skip", "desktop only: no menu"), ("flaky", "first failure")):
        case(parse_result(result_text(status, label, 3.25, detail).splitlines()) == (status, label, "chromium", 3.2, detail), f"a {status} line parses back")
    case(parse_result(["screenshots: /tmp"]) is None, "other lines do not parse")
    case(annotation("error", "FAIL [a] b.c: x,y", "50%\nnext") == "::error title=FAIL [a] b.c%3A x%2Cy::50%25%0Anext", "annotations escape their data")

    def fake(results):
        calls = []

        def run():
            calls.append(1)
            return results[len(calls) - 1]

        return run, calls

    quiet = io.StringIO()
    with contextlib.redirect_stdout(quiet):
        tally = Tally()
        run, calls = fake([("fail", "boom"), ("pass", "")])
        status = attempt("chromium", label, run, tally, retry=True)
        case(status == "flaky" and len(calls) == 2 and tally.counts["chromium"]["pass"] == 1 and tally.flaky == [label], "--retry: a pass on the second run counts as pass and is flaky")
        run, calls = fake([("fail", "boom"), ("fail", "boom again")])
        status = attempt("chromium", label, run, tally, retry=True)
        case(status == "fail" and len(calls) == 2 and tally.failures == [(label, "boom again")], "--retry: a second failure fails")
        run, calls = fake([("fail", "boom")])
        case(attempt("chromium", label, run, Tally()) == "fail" and len(calls) == 1, "without --retry a failure runs once")
        tally = Tally()
        runs = [fake([r]) for r in (("pass", ""), ("fail", "boom"), ("pass", ""))]
        stopped = run_variants([("firefox", f"[firefox light 1280] g1.c{i}", run) for i, (run, _) in enumerate(runs)], tally, exitfirst=True)
        case(stopped and [len(c) for _, c in runs] == [1, 1, 0] and tally.counts["firefox"] == {"pass": 1, "fail": 1, "skip": 0, "flaky": 0}, "--exitfirst stops after the first failure")
        runs = [fake([r]) for r in (("fail", "boom"), ("pass", ""))]
        case(not run_variants([("firefox", "[firefox light 1280] g1.c", run) for run, _ in runs], Tally()) and [len(c) for _, c in runs] == [1, 1], "without --exitfirst all checks run")
    lines = quiet.getvalue().splitlines()
    case(lines[0].startswith(f"flaky {label} (") and lines[1] == "  boom", "--retry prints a flaky line with the first failure")

    spec = importlib.util.spec_from_file_location("clanker_behavior_engine", ROOT / "tools" / "behavior" / "engine.py")
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)

    def motion(duration=200, opacity=1, size=(100, 40), close=None):
        return {"before": "hidden", "animations": [{"name": "enter", "duration": duration, "delay": 0, "easing": "ease"}], "paint_start": 0, "paint_end": duration, "dom_close": close, "end": {"visible": True, "opacity": opacity, "size": list(size)}}

    def compare(ours, ref=None, allowed=(), engine="chromium", step=None):
        sc = {"steps": [step or {"do": "click"}], "allowed": list(allowed)}
        rows = lambda m: [{"label": "start"}, {"label": "click trigger", "motion": {"popup": m}}]
        return [(f["what"], f["severity"], f.get("allowed")) for f in E.compare(sc, rows(ref or motion()), rows(ours), engine)]

    ms, px, op, slow = 20, 1, 0.02, 54
    case(compare(motion()) == [], "compare: the same motion gives no difference")
    case(compare(motion(200 + ms)) == [], "compare: a duration inside the tolerance gives no difference")
    case(compare(motion(200 + ms + 1)) == [("popup animation duration", "minor", None)], "compare: a duration just outside the tolerance is minor")
    case(compare(motion(350)) == [("popup animation duration", "visible", None)], "compare: a duration more than 100 ms off is visible")
    case(compare(motion(opacity=1 - op / 2)) == [], "compare: an end opacity inside the tolerance gives no difference")
    case(compare(motion(opacity=1 - op - 0.01)) == [("popup end opacity", "visible", None)], "compare: an end opacity outside the tolerance is visible")
    case(compare(motion(size=(100 + px, 40))) == [], "compare: an end size inside the tolerance gives no difference")
    case(compare(motion(size=(100 + px + 1, 40))) == [("popup end size", "minor", None)], "compare: an end size outside the tolerance is minor")
    case(compare(motion(size=(106, 40))) == [("popup end size", "visible", None)], "compare: an end size more than 4 px off is visible")
    case(compare(motion(close=slow), motion(close=0)) == [], "compare: a late close inside the frame tolerance gives no difference")
    case(compare(motion(close=slow + 1), motion(close=0)) == [("popup state change delay", "visible", None)], "compare: a late close outside the frame tolerance is visible")
    rule = {"match": "animation duration", "reason": "known", "steps": [1], "engines": ["chromium"], "platforms": [sys.platform]}
    case(compare(motion(350), allowed=[rule]) == [("popup animation duration", "visible", "known")], "compare: an allowed entry matches its step, engine, and platform")
    case(compare(motion(350), allowed=[dict(rule, steps=[2])])[0][2] is None, "compare: an allowed entry for another step does not match")
    case(compare(motion(350), allowed=[dict(rule, platforms=["other"])])[0][2] is None, "compare: an allowed entry for another platform does not match")
    case(compare(motion(350), allowed=[rule], engine="webkit")[0][2] is None, "compare: an allowed entry for another engine does not match")
    print(f"self-test: {count} checks passed in {time.monotonic() - started:.2f}s")
    return 0


def main():
    ap = argparse.ArgumentParser(description="clanker-ui browser checks")
    ap.add_argument("--base-url")
    ap.add_argument("--engines", default="chromium,firefox,webkit")
    ap.add_argument("--themes", default="light,dark")
    ap.add_argument("--widths", default="1280,390")
    ap.add_argument("--only", default="", help="comma-separated test file prefixes, for example g1 or foundation")
    ap.add_argument("-k", default="", help="regex on check names")
    ap.add_argument("--out", default=os.environ.get("CLANKER_UI_OUT") or str(pathlib.Path(tempfile.gettempdir()) / "clanker-ui-run"))
    ap.add_argument("--reduced-motion", action="store_true")
    ap.add_argument("--rtl", action="store_true", help="set dir=rtl on <html>")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--shots", action="store_true", help="save screenshots of passing checks too (a failure always saves <check>-failure.png)")
    ap.add_argument("--jobs", type=int, default=1, help="run up to N engines in parallel, one process each")
    ap.add_argument("--retry", action="store_true", help="run a failed check once more at once; a pass then prints flaky and counts as pass")
    ap.add_argument("--exitfirst", action="store_true", help="stop after the first failure")
    ap.add_argument("--impact", action="store_true", help="print the components that each check touches (tools/ci/impact.py)")
    ap.add_argument("--list", action="store_true", help="print the selected check names and their count, then exit")
    ap.add_argument("--self-test", action="store_true", help="test the runner and the behavior comparison without a browser, then exit")
    ap.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    args.out = pathlib.Path(args.out)
    only = [o for o in args.only.split(",") if o]
    pattern = re.compile(args.k) if args.k else None
    modules = discover(only)
    if not modules:
        print("no test files found")
        return 1
    if args.list:
        return list_checks(modules, pattern)
    if not args.base_url:
        ap.error("--base-url is required")
    engines = [e for e in args.engines.split(",") if e]
    themes = [t for t in args.themes.split(",") if t]
    widths = [int(w) for w in args.widths.split(",") if w]
    tally = Tally()
    started = time.time()
    if args.jobs > 1 and len(engines) > 1 and not args.child:
        run_parallel(args, engines, tally)
    else:
        run_serial(args, engines, themes, widths, modules, pattern, tally)
    if args.child:
        return 1 if tally.failures else 0
    return tally.summary(args.out, time.time() - started)


if __name__ == "__main__":
    sys.exit(main())
