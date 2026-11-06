import difflib
import fnmatch
import pathlib
import re
import sys
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[2]
ANCHOR = "scan(document.documentElement)"
SPLIT = {"clanker-ui.js": "js", "clanker-ui.css": "css", "tools/gen/kit.css": "css"}
KIT_SOURCES = {"clanker-ui.js", "clanker-ui.css", "tools/gen/kit.css", "clanker-ui-chart.js", "clanker-ui-code.js", "clanker-ui-theme.js", "clanker-ui-themes.css", "clanker-ui-a11y.css"}
SERVED = ["clanker-ui-chart.js", "clanker-ui-code.js", "clanker-ui-theme.js", "clanker-ui-themes.css", "clanker-ui-a11y.css", "demo/demo.css", "demo/demo.js", "demo/assets/*", "docs/assets/*"]
SITE = ["docs/nav.json", "docs/templates/*"]
DOCS_ROUTE = re.compile(r"^/($|docs|view/|blocks/|404$)")


class Groups:
    def __init__(self, text):
        names, camel = [], {}
        for line in text.splitlines():
            name = line.split("\t")[0]
            if not name:
                continue
            n = name.removeprefix("js:")
            if n == name:
                names.append(n)
            parts = n.split("-")
            camel[parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])] = n
        self.names = sorted(names, key=len, reverse=True)
        self.camel = sorted(camel.items(), key=lambda kv: (-len(kv[0]), kv[0]))

    def component(self, slot):
        return next((n for n in self.names if slot == n or slot.startswith(n + "-")), None)

    def part(self, attr):
        return None if attr == "slot" else next((n for n in self.names if attr.startswith(n + "-")), None)

    def named(self, name):
        for c, n in self.camel:
            if name == c or name.startswith(c) and len(name) > len(c) and "A" <= name[len(c)] <= "Z":
                return n
        return None


def groups(root=ROOT):
    return Groups((pathlib.Path(root) / "tools/gen/groups.tsv").read_text())


REGEX_PREV = {"return", "typeof", "case", "do", "else", "in", "of", "new", "delete", "void", "throw", "yield", "await", "instanceof"}


def ident_start(c):
    return c == "_" or c == "$" or "a" <= c <= "z" or "A" <= c <= "Z"


def ident_part(c):
    return ident_start(c) or "0" <= c <= "9"


def mask_js(src):
    out = list(src)

    def blank(a, b):
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    stack, regex_ok, i, n = [], True, 0, len(src)
    while i < n:
        c = src[i]
        if stack and stack[-1] < 0:
            start = i
            while i < n and src[i] != "`" and not (src[i] == "$" and i + 1 < n and src[i + 1] == "{"):
                i += 2 if src[i] == "\\" else 1
            if i >= n:
                raise ValueError("unclosed template literal")
            blank(start, i)
            if src[i] == "`":
                out[i] = " "
                stack.pop()
                i += 1
                regex_ok = False
                continue
            out[i] = out[i + 1] = " "
            stack.append(0)
            i += 2
            regex_ok = True
            continue
        if c == "/" and src.startswith("*", i + 1):
            end = src.find("*/", i + 2)
            if end < 0:
                raise ValueError("unclosed comment")
            blank(i, end + 2)
            i = end + 2
        elif c == "/" and src.startswith("/", i + 1):
            end = src.find("\n", i)
            end = n if end < 0 else end
            blank(i, end)
            i = end
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                if src[j] == "\\":
                    j += 1
                if j < n and src[j] == "\n":
                    raise ValueError(f"line break in a string at {i}")
                j += 1
            if j >= n:
                raise ValueError(f"unclosed string at {i}")
            blank(i, j + 1)
            i = j + 1
            regex_ok = False
        elif c == "`":
            out[i] = " "
            stack.append(-1)
            i += 1
        elif c == "/" and regex_ok:
            j, cls = i + 1, False
            while j < n:
                d = src[j]
                if d == "\\":
                    j += 2
                    continue
                if d == "\n":
                    raise ValueError(f"line break in a regular expression at {i}")
                if d == "[":
                    cls = True
                elif d == "]":
                    cls = False
                elif d == "/" and not cls:
                    break
                j += 1
            j += 1
            while j < n and ident_part(src[j]):
                j += 1
            blank(i, j)
            i = j
            regex_ok = False
        elif ident_start(c) or "0" <= c <= "9":
            j = i
            while j < n and (ident_part(src[j]) or "0" <= c <= "9" and src[j] == "."):
                j += 1
            regex_ok = src[i:j] in REGEX_PREV
            i = j
        elif c == "{":
            if stack:
                stack[-1] += 1
            regex_ok = True
            i += 1
        elif c == "}":
            if stack and stack[-1] == 0:
                out[i] = " "
                stack.pop()
                regex_ok = False
                i += 1
                continue
            if stack:
                stack[-1] -= 1
            regex_ok = True
            i += 1
        elif c in ")]":
            regex_ok = False
            i += 1
        elif c in " \t\n\r":
            i += 1
        else:
            regex_ok = True
            i += 1
    if stack:
        raise ValueError("unclosed template literal")
    return "".join(out)


DECL = re.compile(r"^(export\s+)?(?:async\s+)?(?:function\s*\*?\s*([A-Za-z_$][\w$]*)|(?:const|let|var|class)\s+([A-Za-z_$][\w$]*))")
DEFINE = re.compile(r'^(?:define|partDefaults)\("([a-z0-9-]+)"')


def js_spans(src, g):
    masked = mask_js(src)
    first = src.find("\n") + 1
    starts, depth, line_start = [], 0, True
    for i, c in enumerate(masked):
        if line_start and i >= first and depth == 0 and c not in " \n\t})]":
            starts.append(i)
        line_start = c == "\n"
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
    if depth or not starts or starts[0] != first:
        raise ValueError("cannot split the kit script")
    spans, core, prev = [], True, "*"
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(src)
        line = src[s:].split("\n", 1)[0]
        decl = DECL.match(line)
        if core:
            comp = "*"
            core = src[s:e].strip() != ANCHOR
        elif m := DEFINE.match(line):
            comp = g.component(m[1]) or "*"
        elif decl:
            comp = g.named(decl[2] or decl[3]) or "*"
        else:
            comp = prev
        prev = comp
        spans.append(Stmt(s, e, src.count("\n", 0, s) + 1, src.count("\n", 0, e - 1) + 1, comp, decl and (decl[2] or decl[3]), bool(decl and decl[1]), masked[s:e]))
    if core:
        raise ValueError(f"no top-level {ANCHOR}")
    return spans


TAGS = {"button", "input", "label", "table", "select", "dialog", "form", "textarea", "progress", "menu", "output", "item", "page", "part", "empty", "field", "message"}
LITERAL = re.compile(r"""["'`]([a-z][a-z0-9-]*)["'`=\]]""")
IDENT = re.compile(r"(?<![\w$])[A-Za-z_$][\w$]*")


class Stmt:
    def __init__(self, start, end, l0, l1, comp, name, exported, masked):
        self.start, self.end, self.l0, self.l1, self.comp, self.name, self.exported, self.masked = start, end, l0, l1, comp, name, exported, masked

    def ids(self):
        out = set()
        for m in IDENT.finditer(self.masked):
            k = m.start() - 1
            while k >= 0 and self.masked[k] in " \n":
                k -= 1
            if not (k >= 0 and self.masked[k] == "." and self.masked[k - 2 : k] != ".."):
                out.add(m[0])
        return out


def js_closure(stmts, hit):
    users = {}
    for i, st in enumerate(stmts):
        for name in st.ids():
            users.setdefault(name, set()).add(i)
    seen, todo = set(hit), list(hit)
    while todo:
        st = stmts[todo.pop()]
        for j in users.get(st.name, ()) if st.name else ():
            if j not in seen:
                seen.add(j)
                todo.append(j)
    return seen


SLOT = re.compile(r"""\[data-(slot|backdrop-of)\s*[~|^$*]?=\s*["']?([a-z0-9-]+)["']?\s*\]""")
PART = re.compile(r"\[data-([a-z0-9-]+)\s*[\]=~|^$*]")
GROUPED = ("not", "is", "where", "matches", "-webkit-any", "-moz-any")
NESTING = ("media", "supports", "layer", "container", "scope", "starting-style", "document")


def split_top(s, sep=","):
    parts, depth, cur = [], 0, []
    for c in s:
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        if c == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(c)
    return parts + ["".join(cur)]


def strip_grouped(sel):
    out, i = [], 0
    while i < len(sel):
        m = re.match(r":(" + "|".join(re.escape(x) for x in GROUPED) + r")\(", sel[i:])
        if m:
            depth, j = 1, i + len(m[0])
            while j < len(sel) and depth:
                depth += {"(": 1, ")": -1}.get(sel[j], 0)
                j += 1
            i = j
            continue
        out.append(sel[i])
        i += 1
    return "".join(out)


def selector_req(prelude, g):
    reqs = []
    for alt in split_top(prelude):
        need = set()
        for kind, slot in SLOT.findall(strip_grouped(alt)):
            c = g.component(slot)
            if not c:
                return None
            need.add(c)
        for attr in PART.findall(strip_grouped(alt)):
            if c := g.part(attr):
                need.add(c)
        if not need:
            return None
        reqs.append(frozenset("c:" + c for c in need))
    return reqs


def css_spans(src, g):
    text = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m[0]), src, flags=re.S)
    line_at = [0] * (len(text) + 1)
    ln = 1
    for i, c in enumerate(text):
        line_at[i] = ln
        if c == "\n":
            ln += 1
    line_at[len(text)] = ln
    spans, stack, seg, i, n = [], [], 0, 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'":
            j = text.find(c, i + 1)
            i = (j if j >= 0 else n) + 1
            continue
        top = stack[-1] if stack else None
        if c == "{":
            prelude = text[seg:i].strip()
            p0 = seg + len(text[seg:i]) - len(text[seg:i].lstrip())
            if top and top["kind"] in ("leaf", "rule"):
                top["depth"] += 1
                if top["kind"] == "rule":
                    r = selector_req(prelude, g)
                    top["reqs"] = None if r is None or top["reqs"] is None else top["reqs"] + r
            elif prelude.startswith("@"):
                name = re.match(r"@([\w-]+)", prelude)
                kind = "group" if name and name[1] in NESTING else "leaf"
                stack.append({"kind": kind, "l0": line_at[p0], "l1": line_at[i], "reqs": [] if kind == "group" else None, "depth": 0})
            else:
                stack.append({"kind": "rule", "l0": line_at[p0], "reqs": selector_req(prelude, g), "depth": 0})
            seg = i + 1
        elif c == "}":
            if top and top["kind"] in ("leaf", "rule") and top["depth"]:
                top["depth"] -= 1
            elif top:
                stack.pop()
                if top["kind"] == "group":
                    spans.append((top["l0"], top["l1"], top["reqs"] or None))
                    spans.append((line_at[i], line_at[i], top["reqs"] or None))
                else:
                    spans.append((top["l0"], line_at[i], top["reqs"]))
                parent = stack[-1] if stack else None
                if parent and parent["kind"] == "group" and parent["reqs"] is not None:
                    parent["reqs"] = None if top["reqs"] is None else parent["reqs"] + top["reqs"]
            seg = i + 1
        elif c == ";":
            if not top or top["kind"] == "group":
                p0 = seg + len(text[seg:i]) - len(text[seg:i].lstrip())
                spans.append((line_at[p0], line_at[i], None))
                if top:
                    top["reqs"] = None
            seg = i + 1
        i += 1
    if stack:
        raise ValueError("unbalanced braces")
    return spans


def changed_lines(old, new):
    a, b = old.splitlines(), new.splitlines()
    olds, news = set(), set()
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        olds.update(k + 1 for k in range(i1, i2) if a[k].strip())
        news.update(k + 1 for k in range(j1, j2) if b[k].strip())
    return olds, news


def line_reqs(kind, text, lines, g):
    if not lines:
        return []
    if kind == "js":
        stmts = js_spans(text, g)
        hit = {i for i, st in enumerate(stmts) for ln in lines if st.l0 <= ln <= st.l1}
        if any(not any(st.l0 <= ln <= st.l1 for st in stmts) for ln in lines):
            return None
        closure = js_closure(stmts, hit)
        comps = {stmts[i].comp for i in closure}
        for i in closure:
            st = stmts[i]
            comps |= {c for s in LITERAL.findall(text[st.start : st.end]) if s not in TAGS and (c := g.component(s))}
        return None if "*" in comps else [frozenset({"c:" + c}) for c in sorted(comps)]
    spans = css_spans(text, g)
    out = []
    for ln in sorted(lines):
        hit = [r for l0, l1, r in spans if l0 <= ln <= l1]
        if not hit or any(r is None for r in hit):
            return None
        for r in hit:
            out += r
    return out


def page_of(path):
    m = re.fullmatch(r"docs/content/(.+?)/(?:page\.md|examples/[a-z0-9-]+\.(?:html|js))", path)
    if not m:
        return None
    return "/docs" if m[1] == "index" else "/docs/" + m[1]


def front_matter_lines(text):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return 0
    return next((i + 1 for i, l in enumerate(lines[1:], 1) if l == "---"), len(lines))


def docs_reqs(path, old, new, pages):
    href = page_of(path)
    if path.endswith("page.md"):
        olds, news = changed_lines(old or "", new or "")
        if not old or not new or any(l <= front_matter_lines(old) for l in olds) or any(l <= front_matter_lines(new) for l in news):
            return [frozenset({"site:docs"})]
        return [frozenset({"p:" + href})]
    ex = pathlib.PurePosixPath(path).stem
    reqs = [frozenset({"p:" + href}), frozenset({"p:/view/" + ex})]
    quoted = re.compile(r'\{\{\s*example\s+"' + re.escape(ex) + '"')
    for page, text in pages.items():
        if quoted.search(text):
            reqs.append(frozenset({"p:" + page_of(page)}))
    if path.endswith(".js"):
        reqs.append(frozenset({"f:" + path}))
    return reqs


def file_reqs(path, old, new, g, pages=None):
    if path in SPLIT:
        if old is None or new is None:
            return None
        try:
            olds, news = changed_lines(old, new)
            a, b = line_reqs(SPLIT[path], old, olds, g), line_reqs(SPLIT[path], new, news, g)
        except ValueError:
            return None
        return None if a is None or b is None else a + b
    if page_of(path):
        return docs_reqs(path, old, new, pages or {})
    if path == "demo/index.html":
        return [frozenset({"p:/demo"})]
    if any(fnmatch.fnmatch(path, p) for p in SITE):
        return [frozenset({"site:docs"})]
    if any(fnmatch.fnmatch(path, p) for p in SERVED):
        return [frozenset({"f:" + path})]
    return None


def resolve(path, root=ROOT):
    root = pathlib.Path(root)
    p = path.lstrip("/")
    m = re.fullmatch(r"assets/[^/]+/([^/]+)", p)
    base = m[1] if m else p.rsplit("/", 1)[-1]
    if m := re.fullmatch(r"blocks/([a-z0-9-]+)\.js", p):
        return "p:/blocks/" + m[1]
    for cand in ([p] if not m else []) + ["dist/" + base, "docs/assets/" + base, "demo/" + base, base]:
        if cand and (root / cand).is_file():
            return "f:" + cand
    hits = sorted(root.glob("docs/content/**/examples/" + base)) if base else []
    if hits:
        return "f:" + hits[0].relative_to(root).as_posix()
    return "u:" + path


def route(path):
    p = re.sub(r"(/index)?\.html$", "", path).rstrip("/") or "/"
    return p


def url_keys(path, document, root=ROOT):
    if document and not path.startswith("/test/"):
        r = route(path)
        return {"p:" + r} | ({"site:docs"} if DOCS_ROUTE.match(r) else set())
    return {resolve(path, root)}


class Coverage:
    def __init__(self, g, root=ROOT):
        self.g, self.root, self.cache = g, pathlib.Path(root), {}

    def table(self, name):
        if name not in self.cache:
            src = (self.root / name).read_text()
            units = [0]
            for ch in src:
                units.append(units[-1] + (2 if ord(ch) > 0xFFFF else 1))
            spans = [(units[st.start], units[st.end], st.comp, st.exported) for st in js_spans(src, self.g)]
            self.cache[name] = (units[-1], spans)
        return self.cache[name]

    def keys(self, name, length, starts, exported=False):
        total, spans = self.table(name)
        if length != total:
            return set()
        out, k = set(), 0
        for s in sorted(starts):
            while k < len(spans) and spans[k][1] <= s:
                k += 1
            if k < len(spans) and spans[k][0] <= s and spans[k][2] != "*" and (spans[k][3] or not exported):
                out.add(spans[k][2])
        return out


SLOTS = """(() => {
  let seen
  try { seen = new Set(JSON.parse(sessionStorage.getItem("clanker-impact") || "[]")) } catch { seen = new Set() }
  let dirty = false
  const save = () => {
    dirty = false
    try { sessionStorage.setItem("clanker-impact", JSON.stringify([...seen])) } catch {}
  }
  const shown = el => !el.closest("[hidden]")
  const add = el => {
    const s = el.getAttribute?.("data-slot")
    if (s && !seen.has(s)) {
      seen.add(s)
      if (!dirty) {
        dirty = true
        queueMicrotask(save)
      }
    }
  }
  new MutationObserver(records => {
    for (const r of records) {
      const roots = r.type === "childList" ? [...r.addedNodes] : r.attributeName === "hidden" || r.attributeName === "data-slot" ? [r.target] : []
      for (const n of roots) if (n.nodeType === 1 && shown(n)) {
        add(n)
        n.querySelectorAll("[data-slot]").forEach(e => shown(e) && add(e))
      }
    }
  }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-slot", "hidden"] })
  window.__clankerImpact = seen
})()"""
FINAL = '() => [...(window.__clankerImpact || []), ...[...document.querySelectorAll("[data-slot]")].filter(e => !e.closest("[hidden]")).map(e => e.dataset.slot)]'


class Recorder:
    shared = {}

    def __init__(self, context, page, engine, base_url, root=ROOT):
        if root not in self.shared:
            g = groups(root)
            self.shared[root] = (g, Coverage(g, root))
        self.g, self.coverage = self.shared[root]
        self.root, self.page = root, page
        split = urlsplit(base_url)
        self.origin, self.prefix = f"{split.scheme}://{split.netloc}", split.path.rstrip("/")
        self.slots, self.urls, self.after, self.load, self.length, self.script = set(), set(), set(), set(), None, None
        context.add_init_script(SLOTS)
        context.on("request", lambda r: self.urls.add((r.url, r.resource_type == "document")))
        self.cdp = None
        if engine == "chromium":
            self.cdp = context.new_cdp_session(page)
            self.start()
            for name in ("goto", "reload", "go_back", "go_forward"):
                setattr(page, name, self.wrap(getattr(page, name)))

    def wrap(self, navigate):
        def run(*args, **kwargs):
            self.flush()
            try:
                return navigate(*args, **kwargs)
            finally:
                self.loaded()
        return run

    def start(self):
        self.cdp.send("Profiler.enable")
        self.cdp.send("Profiler.startPreciseCoverage", {"callCount": True, "detailed": False})

    def take(self, into):
        try:
            res = self.cdp.send("Profiler.takePreciseCoverage")["result"]
        except Exception:
            return
        for script in res:
            if urlsplit(script["url"]).path.rsplit("/", 1)[-1] != "clanker-ui.js":
                continue
            for fn in script["functions"]:
                r = fn["ranges"][0]
                self.script = script["url"]
                if r["startOffset"] > 0 and r["count"] > 0:
                    into.add(r["startOffset"])

    def flush(self):
        if self.cdp:
            self.take(self.after)

    def loaded(self):
        if self.cdp:
            self.take(self.load)
            try:
                self.start()
            except Exception:
                pass

    def finish(self):
        self.flush()
        try:
            self.slots.update(self.page.evaluate(FINAL))
            if self.script:
                self.length = self.page.evaluate("u => fetch(u).then(r => r.text()).then(t => t.length)", self.script)
        except Exception:
            pass
        keys = set()
        for s in self.slots:
            c = self.g.component(s)
            keys.add("c:" + c if c else "s:" + s)
        for url, document in self.urls:
            u = urlsplit(url)
            if f"{u.scheme}://{u.netloc}" == self.origin and u.path.startswith(self.prefix):
                keys |= url_keys(u.path[len(self.prefix):] or "/", document, self.root)
        if self.length is not None:
            cov = self.coverage
            keys |= {"c:" + c for c in cov.keys("clanker-ui.js", self.length, self.after) | cov.keys("clanker-ui.js", self.length, self.load, exported=True)}
            keys |= {"l:" + c for c in cov.keys("clanker-ui.js", self.length, self.load)}
        return keys


def read_impact(path):
    impact = {}
    f = pathlib.Path(path)
    for line in f.read_text().splitlines()[1:] if f.exists() else []:
        check, _, keys = line.partition("\t")
        impact[check] = frozenset(keys.split())
    return impact


IMPACT = re.compile(r"^impact \[[^]]+\] (\S+)\t(.*)$", re.M)


def build(out, *dirs):
    acc = {}
    for d in dirs:
        for f in sorted(pathlib.Path(d).rglob("*.log")):
            for m in IMPACT.finditer(f.read_text(errors="replace")):
                acc.setdefault(m[1], set()).update(m[2].split())
    rows = [f"{c}\t{' '.join(sorted(k for k in keys if not k.startswith(('u:', 's:', 'l:'))))}\n" for c, keys in sorted(acc.items())]
    pathlib.Path(out).write_text("check\tcomponents\n" + "".join(rows))
    print(f"{len(rows)} checks, {len({k for keys in acc.values() for k in keys})} components")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"build": build}[cmd](*args)
