import sys

sys.dont_write_bytecode = True

import argparse
import json
import pathlib
import re
import time
import urllib.request

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
STYLES = ["nova", "rhea", "luma", "lyra", "maia", "mira", "sera", "vega"]
WIDTHS = ((1280, 800), (390, 844))
DYNAMIC = ("hover", "active", "focus", "focus-visible", "focus-within")
FORCED = (["hover"], ["hover", "active"], ["focus", "focus-visible", "focus-within"])
SKIP = {"data-slot", "data-theme", "class", "id", "style", "href", "src"}
SELECTOR = re.compile(r"([^{};]+)\{")
CUSTOM = re.compile(r"[{;\s](--[\w-]+)\s*:")
KEYFRAMES = re.compile(r"@(keyframes\s+[\w-]+|font-face)\s*\{((?:[^{}]|\{[^{}]*\})*)\}")
ATTR = re.compile(r"""\[\s*([\w-]+)\s*(?:([~|^$*]?=)\s*(?:"([^"]*)"|'([^']*)'|([^\]\s]+)))?[^\]]*\]""")
NAME = re.compile(r"[\w-]+")
PSEUDO_ELEMENT = re.compile(r"::([\w-]+)")
COMBINATORS = " >+~\n\t"
GROUPS = ("core", "forms", "overlays", "layout", "chat", "chart")
TOKENS = {"--primary": "oklch(0.6 0.2 30)", "--primary-foreground": "oklch(0.2 0.1 200)", "--background": "oklch(0.9 0.05 100)", "--foreground": "oklch(0.3 0.1 300)", "--border": "oklch(0.5 0.2 150)", "--ring": "oklch(0.6 0.25 330)", "--destructive": "oklch(0.5 0.2 80)", "--muted": "oklch(0.8 0.1 250)", "--accent": "oklch(0.75 0.1 20)", "--radius": "1.1rem", "--spacing": "0.3rem", "--font-sans": "serif"}
APP_CSS = "[data-slot], [data-slot]::before, [data-slot]::after { letter-spacing: 0.03em; box-shadow: 0 0 0 2px red; translate: 1px 2px; border-style: dashed; outline-style: dotted; font-weight: 300; line-height: 1.9 }"


def css_text(root, style, a):
    base = "clanker-ui" + ("" if style == "nova" else "-" + style)
    if a.groups:
        return "\n".join((root / f"dist/{base}-{g}.min.css").read_text() for g in GROUPS)
    return (root / (f"dist/{base}.min.css" if a.min else base + ".css")).read_text()


def close(s, i):
    depth, q = 0, ""
    while i < len(s):
        c = s[i]
        if q:
            if c == "\\":
                i += 1
            elif c == q:
                q = ""
        elif c in "\"'":
            q = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(s) - 1


def split_top(s, seps):
    out, depth, q, start, i = [], 0, "", 0, 0
    while i < len(s):
        c = s[i]
        if q:
            if c == "\\":
                i += 1
            elif c == q:
                q = ""
        elif c in "\"'":
            q = c
        elif c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        elif depth == 0 and c in seps:
            out.append(s[start:i])
            start = i + 1
        i += 1
    out.append(s[start:])
    return [p.strip() for p in out if p.strip()]


def analyze(comp, out):
    g = {"slots": set(), "tags": set(), "tests": set(), "dyn": set()}
    i = 0
    while i < len(comp):
        c = comp[i]
        if c == "[":
            m = ATTR.match(comp, i)
            if not m:
                i += 1
                continue
            value = next((v for v in m.groups()[2:] if v is not None), None)
            if m[1] == "data-slot" and m[2] == "=":
                g["slots"].add(value)
            elif m[1] not in SKIP:
                g["tests"].add((m[1], m[2], value))
            i = m.end()
        elif comp.startswith("::", i):
            m = NAME.match(comp, i + 2)
            i = m.end() if m else i + 2
        elif c == ":":
            m = NAME.match(comp, i + 1)
            if not m:
                i += 1
                continue
            i = m.end()
            if i < len(comp) and comp[i] == "(":
                j = close(comp, i)
                args, i = comp[i + 1 : j], j + 1
                if m[0] not in ("is", "where", "not", "has"):
                    continue
                for alt in split_top(args, ","):
                    sub = [analyze(x, out) for x in split_top(alt, COMBINATORS)]
                    if m[0] == "has" or not sub:
                        out.extend(sub)
                        continue
                    out.extend(sub[:-1])
                    for k in g:
                        g[k] |= sub[-1][k]
            elif m[0] in DYNAMIC:
                g["dyn"].add(m[0])
        elif c.isalpha():
            m = NAME.match(comp, i)
            g["tags"].add(m[0])
            i = m.end()
        else:
            i += 1
    return g


def profile(texts):
    selectors, custom = set(), set()
    for text in texts:
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        custom.update(CUSTOM.findall(text))
        for prelude in SELECTOR.findall(text):
            if not prelude.lstrip().startswith("@"):
                selectors.update(split_top(prelude, ","))
    tests, dyn, pseudo = {}, {}, {}
    for sel in sorted(selectors):
        groups = []
        groups.extend(analyze(c, groups) for c in split_top(sel, COMBINATORS))
        near = {"^" + s for g in groups for s in g["slots"]} or {"*"}
        for g in groups:
            keys = g["slots"] or {"@" + t for t in g["tags"]} or near
            for t in g["tests"]:
                tests.setdefault(t, set()).update(keys)
            for d in g["dyn"]:
                dyn.setdefault(d, set()).update(keys)
        m = PSEUDO_ELEMENT.search(sel)
        if m and m[1] not in ("before", "after", "marker"):
            rest = (sel[: m.start()] + sel[m.end() :]).strip()
            if not rest or rest[-1] in COMBINATORS:
                rest += "*" if rest else "input,textarea,select"
            pseudo.setdefault("::" + m[1], set()).add(rest)
    tests.setdefault(("disabled", None, None), set()).update({"@button", "@input", "@select", "@textarea", "@fieldset"})
    tests.setdefault(("dir", "=", "rtl"), set()).add("@html")
    names = {}
    for (name, _, _), keys in tests.items():
        names.setdefault(name, set()).update(keys)
    order = sorted(tests, key=lambda t: (t[0], t[1] or "", t[2] or ""))
    return {
        "custom": sorted(custom),
        "pseudo": [[p, sorted(s)] for p, s in sorted(pseudo.items())],
        "tests": [[n, op, v, sorted(tests[(n, op, v)])] for n, op, v in order],
        "names": [[n, sorted(k)] for n, k in sorted(names.items())],
        "dyn": {p: sorted(k) for p, k in dyn.items()},
        "attrNames": sorted(set(names) | {"data-slot"}),
        "cap": 6,
        "tokens": TOKENS,
        "appCss": APP_CSS,
    }


def fixed_rules(text):
    return {m[1]: re.sub(r"\s+", "", m[2]) for m in KEYFRAMES.finditer(re.sub(r"/\*.*?\*/", "", text, flags=re.S))}


def pages(root):
    views = sorted({p.stem for p in (root / "docs/content").glob("**/examples/*.html")})
    blocks = sorted(p.stem for p in (root / "skills/clanker-ui/references/blocks").glob("*.html"))
    return ["/demo"] + ["/blocks/" + b for b in blocks] + ["/view/" + v for v in views]


def docs_pages(base):
    html = urllib.request.urlopen(base + "/docs").read().decode()
    return sorted(set(re.findall(r'href="(/docs[^"#?]*)"', html)))


class Guard:
    def __init__(self, a):
        self.a = a
        self.css = {}
        for style in a.styles:
            old, new = css_text(a.old, style, a), css_text(a.new, style, a)
            for m in a.mutate:
                s, find, repl = m.split("::", 2)
                if s == style:
                    new, n = re.subn(find, repl, new, count=1)
                    if n != 1:
                        raise SystemExit(f"mutation does not apply: {m}")
            self.css[f"old/{style}"], self.css[f"new/{style}"] = old, new
        self.cfg = profile(list(self.css.values()) + ([css_text(a.new, s, a) for s in STYLES] if a.docs else []))
        self.files = [{"style": s, "which": w, "href": f"/__guard/{w}/{s}.css"} for s in a.styles for w in ("old", "new")]
        self.js = (HERE / "guard.js").read_text()

    def static(self):
        out = []
        for style in self.a.styles:
            old, new = fixed_rules(self.css[f"old/{style}"]), fixed_rules(self.css[f"new/{style}"])
            out += [f"{style}: @{k} differs" for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
        return out

    def serve(self, route):
        key = route.request.url.split("/__guard/", 1)[1].removesuffix(".css")
        route.fulfill(status=200, content_type="text/css; charset=utf-8", body=self.css[key])

    def page(self, page, cdp, url):
        a, rec = self.a, {"page": url, "elements": 0, "sweeps": 0, "states": 0, "skipped": 0, "diffs": []}

        def add(phase, r, state=None):
            rec["sweeps"] += r["sweeps"]
            rec["elements"] = max(rec["elements"], r.get("elements", 0))
            rec["states"] += r.get("states", 1 if state else 0)
            rec["diffs"] += [{"phase": phase, **({"state": state} if state else {}), **d} for d in r["diffs"]]

        def sweep(configs):
            return page.evaluate("c => __guard.sweep(c)", configs)

        page.set_viewport_size({"width": 1280, "height": 800})
        page.emulate_media(color_scheme="light")
        page.goto(a.base_url + url, wait_until="load")
        page.wait_for_timeout(400)
        page.evaluate(self.js, self.cfg)
        rec["props"] = page.evaluate("f => __guard.load(f)", self.files + self.scoped(page, rec))
        for width, height in WIDTHS:
            page.set_viewport_size({"width": width, "height": height})
            for media in ("light", "dark"):
                page.emulate_media(color_scheme=media)
                page.wait_for_timeout(150)
                configs = [[s, t] for s in a.styles for t in ((None, "dark") if media == "light" else (None, "light"))]
                phase = f"{width}/{media}"
                base = sweep(configs)
                add(phase, base)
                if a.tier < 1:
                    continue
                main = width == 1280 and media == "light"
                small = base["elements"] <= a.big
                if main:
                    part, at = (configs if small else configs[:2]), 0
                    while True:
                        r = page.evaluate("([c, i, j]) => __guard.attrs(c, i, j)", [part, at, at + 25])
                        add(phase, r)
                        at += 25
                        if at >= r["total"]:
                            break
                    add(phase, page.evaluate("c => __guard.app(c)", part))
                if cdp:
                    self.forced(page, cdp, configs if small else configs[:2], phase, add, main and small and a.tier > 1)
                if main and a.tier > 1:
                    part = configs if small else configs[:2]
                    if not cdp:
                        self.real(page, part, phase, add, rec)
                    self.triggers(page, part, phase, add, rec)
        return rec

    def scoped(self, page, rec):
        a, files = self.a, []
        for path in page.evaluate("() => [...document.querySelectorAll('link[rel=\"stylesheet\"]')].map(l => new URL(l.href).pathname).filter(p => /\\/style-[\\w-]+\\.css$/.test(p))"):
            name = path.rsplit("/", 1)[1].removesuffix(".css")
            if not a.old_url:
                rec["scoped"] = "not compared"
                continue
            if f"old/{name}" not in self.css:
                old, new = (urllib.request.urlopen(u + path).read().decode() for u in (a.old_url, a.base_url))
                for m in a.mutate:
                    key, find, repl = m.split("::", 2)
                    if key == name:
                        new, n = re.subn(find, repl, new, count=1)
                        if n != 1:
                            raise SystemExit(f"mutation does not apply: {m}")
                self.css[f"old/{name}"], self.css[f"new/{name}"] = old, new
            files += [{"style": "nova", "which": w, "href": f"/__guard/{w}/{name}.css", "anchor": f"/{name}\\.css$"} for w in ("old", "new")]
        return files

    def forced(self, page, cdp, configs, phase, add, deep):
        root = cdp.send("DOM.getDocument", {"depth": 0})["root"]["nodeId"]
        ids = cdp.send("DOM.querySelectorAll", {"nodeId": root, "selector": "html, body, body *"})["nodeIds"]

        def force(nodes, classes):
            for n in nodes:
                cdp.send("CSS.forcePseudoState", {"nodeId": ids[n], "forcedPseudoClasses": classes})

        for classes in FORCED:
            c = page.evaluate("p => __guard.candidates(p)", classes)
            label = ":" + ":".join(classes)
            if c["all"]:
                force(c["all"], classes)
                add(phase, page.evaluate("c => __guard.sweep(c)", configs), label + " all")
                force(c["all"], [])
            for k, chain in enumerate(c["picked"] if deep else []):
                focus = "focus" in classes
                force(chain[1:], ["focus-within"] if focus else classes)
                force(chain[:1], classes)
                add(phase, page.evaluate("c => __guard.sweep(c)", configs), f"{label} #{k}")
                force(chain, [])

    def real(self, page, configs, phase, add, rec):
        page.evaluate("() => { __guard.swallow = e => { e.preventDefault(); e.stopImmediatePropagation() } }")
        for classes, sel in ((["focus", "focus-visible", "focus-within"], ":focus"), (["hover"], ":hover"), (["active"], ":active")):
            n = len(page.evaluate("p => __guard.candidates(p)", classes)["picked"])
            for k in range(n):
                down = False
                if sel == ":focus":
                    page.evaluate("k => __guard.picked[k].focus()", k)
                else:
                    point = page.evaluate("k => __guard.point(k)", k)
                    if point:
                        page.mouse.move(*point)
                        if sel == ":active":
                            page.evaluate("() => addEventListener('click', __guard.swallow, true)")
                            page.mouse.down()
                            down = True
                if page.evaluate("([k, s]) => __guard.is(k, s)", [k, sel]):
                    add(phase, page.evaluate("c => __guard.sweep(c)", configs), f"real {sel} #{k}")
                else:
                    rec["skipped"] += 1
                if down:
                    page.mouse.up()
                    page.evaluate("() => removeEventListener('click', __guard.swallow, true)")
                    page.keyboard.press("Escape")
            page.evaluate("() => document.activeElement && document.activeElement.blur()")
            page.mouse.move(0, 0)

    def triggers(self, page, configs, phase, add, rec):
        for k in range(page.evaluate("() => __guard.triggers()")):
            page.evaluate("k => { const e = __guard.picked[k]; if (e.isConnected && !(e.form && e.type === 'submit')) e.click() }", k)
            page.wait_for_timeout(250)
            add(phase, page.evaluate("c => __guard.sweep(c)", configs), f"click #{k}")
            page.keyboard.press("Escape")
            page.wait_for_timeout(150)
            page.evaluate("k => { const e = __guard.picked[k]; if (e.isConnected && e.getAttribute('aria-expanded') === 'true') e.click() }", k)
            page.wait_for_timeout(100)

    def run(self):
        a = self.a
        todo = [p for p in (docs_pages(a.base_url) if a.docs else pages(a.root)) if re.search(a.pages, p)]
        index, count = (int(x) for x in a.shard.split("/"))
        todo = todo[index - 1 :: count]
        out, failed = [], self.static()
        for line in failed:
            print("STATIC", line, flush=True)
        with sync_playwright() as p:
            browser = getattr(p, a.browser).launch()
            ctx = browser.new_context()
            ctx.route("**/__guard/**", self.serve)
            for url in todo:
                page = ctx.new_page()
                cdp = ctx.new_cdp_session(page) if a.browser == "chromium" else None
                if cdp:
                    cdp.send("DOM.enable")
                    cdp.send("CSS.enable")
                t = time.time()
                try:
                    rec = self.page(page, cdp, url)
                except PlaywrightError as e:
                    rec = {"page": url, "error": str(e).splitlines()[0], "diffs": []}
                rec["seconds"] = round(time.time() - t, 1)
                page.close()
                out.append(rec)
                bad = rec.get("error") or rec["diffs"]
                failed += [url] if bad else []
                print("FAIL" if bad else "ok", url, rec.get("error", ""), f'{rec.get("elements", 0)} el {rec.get("sweeps", 0)} sweeps {rec.get("states", 0)} states {rec.get("skipped", 0)} skipped {len(rec["diffs"])} diffs {rec["seconds"]}s', flush=True)
                for d in rec["diffs"][: a.show]:
                    print("  ", d["phase"], d.get("state", "base"), d["config"], d["n"], json.dumps(d["out"][:2]), flush=True)
            browser.close()
        if a.out:
            a.out.write_text(json.dumps({"browser": a.browser, "styles": a.styles, "tier": a.tier, "min": a.min, "groups": a.groups, "pages": out}, indent=1))
        print(f"{a.browser}: {len(todo)} pages, {sum(r.get('sweeps', 0) for r in out)} comparisons, {sum(r.get('states', 0) for r in out)} states, {len(failed)} failed", flush=True)
        if a.expect:
            seen = {(d["config"].split("/")[0], p[0]) for r in out for d in r["diffs"] for o in d["out"] for p in o["props"]}
            want = {tuple(e.split(":", 1)) for e in a.expect}
            missing, extra = sorted(want - seen), sorted({s for s, _ in seen} - {s for s, _ in want})
            print(f"expect: {len(want) - len(missing)} of {len(want)} found, missing {missing}, other styles with a difference {extra}", flush=True)
            return 1 if missing or extra or any("error" in r for r in out) else 0
        return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", type=pathlib.Path, required=True)
    ap.add_argument("--new", type=pathlib.Path, default=ROOT)
    ap.add_argument("--root", type=pathlib.Path, default=ROOT)
    ap.add_argument("--base-url", default="http://127.0.0.1:8110")
    ap.add_argument("--browser", default="chromium", choices=("chromium", "firefox", "webkit"))
    ap.add_argument("--styles", default=",".join(STYLES), type=lambda s: s.split(","))
    ap.add_argument("--pages", default=".")
    ap.add_argument("--shard", default="1/1")
    ap.add_argument("--tier", type=int, default=1, choices=(0, 1, 2))
    ap.add_argument("--big", type=int, default=1500)
    ap.add_argument("--min", action="store_true")
    ap.add_argument("--groups", action="store_true")
    ap.add_argument("--docs", action="store_true")
    ap.add_argument("--old-url")
    ap.add_argument("--mutate", action="append", default=[])
    ap.add_argument("--expect", action="append", default=[])
    ap.add_argument("--show", type=int, default=4)
    ap.add_argument("--out", type=pathlib.Path)
    a = ap.parse_args()
    if a.docs:
        a.styles = ["nova"]
    sys.exit(Guard(a).run())


if __name__ == "__main__":
    main()
