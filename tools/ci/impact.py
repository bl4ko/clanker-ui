import difflib
import fnmatch
import pathlib
import re
import sys
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[2]
ANCHOR = "scan(document.documentElement)"
SPLIT = {"clanker-ui.js": "js", "clanker-ui.css": "css", "tools/gen/kit.css": "css"}
KIT_SOURCES = {*SPLIT, "clanker-ui-chart.js", "clanker-ui-code.js", "clanker-ui-theme.js", "clanker-ui-themes.css", "clanker-ui-a11y.css", "clanker-ui-rhea.css"}
SERVED = [*KIT_SOURCES - set(SPLIT), "demo/demo.css", "demo/demo.js", "demo/assets/*", "docs/assets/*"]
SITE = ["docs/nav.json", "docs/templates/*"]
DOCS_ROUTE = re.compile(r"^/($|docs|view/|blocks/|404$)")


class Groups:
    def __init__(self, text):
        names, camel = [], {}
        for line in text.splitlines():
            name = line.split("\t")[0]
            n = name.removeprefix("js:")
            if n and n == name:
                names.append(n)
            if n:
                parts = n.split("-")
                camel[parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])] = n
        self.names = sorted(names, key=len, reverse=True)
        self.camel = sorted(camel.items(), key=lambda kv: (-len(kv[0]), kv[0]))

    def component(self, slot):
        return next((n for n in self.names if slot == n or slot.startswith(n + "-")), None)

    def part(self, attr):
        return None if attr == "slot" else next((n for n in self.names if attr.startswith(n + "-")), None)

    def named(self, name):
        return next((n for c, n in self.camel if name == c or name.startswith(c) and "A" <= name[len(c) : len(c) + 1] <= "Z"), None)


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


DECL = re.compile(r"^(?:export\s+)?(?:async\s+)?(?:function\s*\*?\s*([A-Za-z_$][\w$]*)|(const|let|var|class)\s+([A-Za-z_$][\w$]*))")
DEFINE = re.compile(r'^(define|partDefaults)\("([a-z0-9-]+)"')
FUNCTION = re.compile(r"=>|\bfunction\b|^\s+(?:(?:async|get|set|static)\s+)*\*?[A-Za-z_$][\w$]*\s*\([^()]*\)\s*\{", re.M)
IDENT = re.compile(r"(?<![\w$.])[A-Za-z_$][\w$]*")


class Stmt:
    def __init__(self, start, end, l0, l1, comp, id, name, code):
        self.start, self.end, self.l0, self.l1, self.comp, self.id, self.name, self.code = start, end, l0, l1, comp, id, name, code
        self.key = f"j:{comp}:{id}"
        self.fn = not name or not DECL.match(code.lstrip()).group(2) or bool(FUNCTION.search(code))


def js_spans(src, g):
    masked = mask_js(src)
    first = src.find("\n") + 1
    starts, depth, line_start = [], 0, True
    for i, c in enumerate(masked):
        if line_start and i >= first and depth == 0 and c not in " \n\t})]":
            starts.append(i)
        line_start = c == "\n"
        depth += (c in "([{") - (c in ")]}")
    if depth or not starts or starts[0] != first:
        raise ValueError("cannot split the kit script")
    out, core, prev, n = [], True, ("*", "core"), 0
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(src)
        line = src[s:].split("\n", 1)[0]
        decl, define = DECL.match(line), DEFINE.match(line)
        name = decl and (decl[1] or decl[3])
        if core:
            comp, id = "*", name or f"core+{k}"
            core = src[s:e].strip() != ANCHOR
        elif define:
            comp, id = g.component(define[2]) or "*", f"{define[1]}:{define[2]}"
        elif name:
            comp, id = g.named(name) or "*", name
        else:
            n += 1
            comp, id = prev[0], f"{prev[1]}+{n}"
        if name or define:
            prev, n = (comp, id), 0
        out.append(Stmt(s, e, src.count("\n", 0, s) + 1, src.count("\n", 0, e - 1) + 1, comp, id, name, masked[s:e]))
    if core:
        raise ValueError(f"no top-level {ANCHOR}")
    return out


def js_reqs(stmts, hit):
    users = {}
    for i, st in enumerate(stmts):
        for name in set(IDENT.findall(st.code)) - {st.name}:
            users.setdefault(name, set()).add(i)
    keys, seen, todo = set(), set(hit), list(hit)
    while todo:
        i = todo.pop()
        st = stmts[i]
        if st.comp == "*":
            return None
        if st.fn:
            keys.add(st.key)
            continue
        for j in users.get(st.name, set()) - seen:
            seen.add(j)
            todo.append(j)
    return [frozenset({k}) for k in sorted(keys)]


SLOT = re.compile(r"""\[data-(?:slot|backdrop-of)\s*[~|^$*]?=\s*["']?([a-z0-9-]+)["']?\s*\]""")
PART = re.compile(r"\[data-([a-z0-9-]+)\s*[\]=~|^$*]")
GROUPED = re.compile(r":(?:not|is|where|matches|-webkit-any|-moz-any)\(")


def strip_grouped(sel):
    while m := GROUPED.search(sel):
        depth, j = 1, m.end()
        while j < len(sel) and depth:
            depth += {"(": 1, ")": -1}.get(sel[j], 0)
            j += 1
        sel = sel[: m.start()] + sel[j:]
    return sel


def selector_req(prelude, g):
    reqs, depth, alts, cur = [], 0, [], ""
    for c in prelude + ",":
        depth += (c in "([") - (c in ")]")
        if c == "," and depth == 0:
            alts.append(cur)
            cur = ""
        else:
            cur += c
    for alt in map(strip_grouped, alts):
        slots = [g.component(s) for s in SLOT.findall(alt)]
        if not slots or None in slots:
            return None
        reqs.append(frozenset("c:" + c for c in slots + [g.part(a) for a in PART.findall(alt)] if c))
    return reqs


def css_spans(src, g):
    text = re.sub(r"/\*.*?\*/|\"[^\"\n]*\"|'[^'\n]*'", lambda m: re.sub(r"[^\n]" if m[0][0] == "/" else r"[{};]", "_", m[0]), src, flags=re.S)
    spans, stack, seg, line = [], [], 0, 1
    for i, c in enumerate(text):
        if c == "{":
            prelude = text[seg:i].strip()
            l0 = line - text[seg:i].lstrip().count("\n")
            if stack and stack[-1][0] != "group" or prelude.startswith("@") and not re.match(r"@(media|supports|layer|container|scope|starting-style)\b", prelude):
                stack.append(("leaf", l0, None))
            elif prelude.startswith("@"):
                stack.append(("group", l0, None))
            else:
                stack.append(("rule", l0, selector_req(prelude, g)))
            seg = i + 1
        elif c == "}":
            kind, l0, req = stack.pop()
            if kind == "rule":
                spans.append((l0, line, req))
            seg = i + 1
        elif c == ";":
            seg = i + 1
        elif c == "\n":
            line += 1
    if stack:
        raise ValueError("unbalanced braces")
    return spans


def changed_lines(old, new):
    a, b = old.splitlines(), new.splitlines()
    olds, news = set(), set()
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            olds.update(k + 1 for k in range(i1, i2) if a[k].strip())
            news.update(k + 1 for k in range(j1, j2) if b[k].strip())
    return olds, news


def line_reqs(kind, text, lines, g):
    if not lines:
        return []
    if kind == "js":
        stmts = js_spans(text, g)
        hit = {i for i, st in enumerate(stmts) for ln in lines if st.l0 <= ln <= st.l1}
        covered = {ln for st in stmts for ln in lines if st.l0 <= ln <= st.l1}
        return js_reqs(stmts, hit) if covered == lines else None
    spans, out = css_spans(text, g), []
    for ln in lines:
        hit = [r for l0, l1, r in spans if l0 <= ln <= l1]
        if not hit or None in hit:
            return None
        out += [x for r in hit for x in r]
    return out


def page_of(path):
    m = re.fullmatch(r"docs/content/(.+?)/(?:page\.md|examples/[a-z0-9-]+\.(?:html|js))", path)
    return m and ("/docs" if m[1] == "index" else "/docs/" + m[1])


def front_matter(text):
    lines = (text or "").splitlines()
    return next((i + 1 for i, l in enumerate(lines[1:], 1) if l == "---"), len(lines)) if lines[:1] == ["---"] else 0


def docs_reqs(path, old, new, pages):
    href = page_of(path)
    if path.endswith("page.md"):
        olds, news = changed_lines(old or "", new or "")
        head = not old or not new or min(olds, default=1e9) <= front_matter(old) or min(news, default=1e9) <= front_matter(new)
        return [frozenset({"site:docs" if head else "p:" + href})]
    ex = pathlib.PurePosixPath(path).stem
    quoted = re.compile(r'\{\{\s*example\s+"' + re.escape(ex) + '"')
    reqs = [frozenset({"p:" + p}) for p in [href, "/view/" + ex] + [page_of(f) for f, t in pages.items() if quoted.search(t)]]
    return reqs + ([frozenset({"f:" + path})] if path.endswith(".js") else [])


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


def url_keys(path, document, root=ROOT):
    if document and not path.startswith("/test/"):
        r = re.sub(r"(/index)?\.html$", "", path).rstrip("/") or "/"
        return {"p:" + r} | ({"site:docs"} if DOCS_ROUTE.match(r) else set())
    p = path.lstrip("/")
    if m := re.fullmatch(r"blocks/([a-z0-9-]+)\.js", p):
        return {"p:/blocks/" + m[1]}
    base = p.rsplit("/", 1)[-1]
    for cand in ([] if p.startswith("assets/") else [p]) + ["dist/" + base, "docs/assets/" + base, "demo/" + base, base]:
        if base and (pathlib.Path(root) / cand).is_file():
            return {"f:" + cand}
    hits = sorted(pathlib.Path(root).glob("docs/content/**/examples/" + base)) if base else []
    return {"f:" + hits[0].relative_to(root).as_posix() if hits else "u:" + path}


SLOTS = """(() => {
  let seen
  try { seen = new Set(JSON.parse(sessionStorage.getItem("clanker-impact") || "[]")) } catch { seen = new Set() }
  const save = () => { try { sessionStorage.setItem("clanker-impact", JSON.stringify([...seen])) } catch {} }
  const shown = el => !el.closest("[hidden]")
  const add = el => {
    const s = el.getAttribute?.("data-slot")
    if (s) seen.add(s)
  }
  new MutationObserver(records => {
    for (const r of records) {
      for (const n of r.type === "childList" ? r.addedNodes : [r.target]) if (n.nodeType === 1 && shown(n)) {
        add(n)
        n.querySelectorAll("[data-slot]").forEach(e => shown(e) && add(e))
      }
    }
    queueMicrotask(save)
  }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-slot", "hidden"] })
  window.__clankerImpact = seen
})()"""
FINAL = '() => [...(window.__clankerImpact || []), ...[...document.querySelectorAll("[data-slot]")].filter(e => !e.closest("[hidden]")).map(e => e.dataset.slot)]'


class Recorder:
    shared = {}

    def __init__(self, context, page, engine, base_url, root=ROOT):
        if root not in self.shared:
            g = groups(root)
            src = (pathlib.Path(root) / "clanker-ui.js").read_text()
            units = [0]
            for ch in src:
                units.append(units[-1] + (2 if ord(ch) > 0xFFFF else 1))
            self.shared[root] = (g, units[-1], [(units[st.start], units[st.end], st) for st in js_spans(src, g)])
        self.g, self.total, self.stmts = self.shared[root]
        self.root, self.page = root, page
        split = urlsplit(base_url)
        self.origin, self.prefix = f"{split.scheme}://{split.netloc}", split.path.rstrip("/")
        self.slots, self.urls, self.ran, self.script = set(), set(), set(), None
        context.add_init_script(SLOTS)
        context.on("request", lambda r: self.urls.add((r.url, r.resource_type == "document")))
        self.cdp = None
        if engine == "chromium":
            self.cdp = context.new_cdp_session(page)
            self.start()
            for name in ("goto", "reload", "go_back", "go_forward"):
                setattr(page, name, self.wrap(getattr(page, name)))

    def start(self):
        try:
            self.cdp.send("Profiler.enable")
            self.cdp.send("Profiler.startPreciseCoverage", {"callCount": True, "detailed": False})
        except Exception:
            pass

    def wrap(self, navigate):
        def run(*args, **kwargs):
            self.flush()
            try:
                return navigate(*args, **kwargs)
            finally:
                self.start()
        return run

    def flush(self):
        try:
            res = self.cdp.send("Profiler.takePreciseCoverage")["result"] if self.cdp else []
        except Exception:
            return
        for script in res:
            if urlsplit(script["url"]).path.rsplit("/", 1)[-1] == "clanker-ui.js":
                self.script = script["url"]
                self.ran |= {f["ranges"][0]["startOffset"] for f in script["functions"] if f["ranges"][0]["startOffset"] > 0 and f["ranges"][0]["count"] > 0}

    def finish(self):
        self.flush()
        length = None
        try:
            self.slots.update(self.page.evaluate(FINAL))
            if self.script:
                length = self.page.evaluate("u => fetch(u).then(r => r.text()).then(t => t.length)", self.script)
        except Exception:
            pass
        keys = {"c:" + c if (c := self.g.component(s)) else "s:" + s for s in self.slots}
        for url, document in self.urls:
            u = urlsplit(url)
            if f"{u.scheme}://{u.netloc}" == self.origin and u.path.startswith(self.prefix):
                keys |= url_keys(u.path[len(self.prefix) :] or "/", document, self.root)
        if length == self.total:
            keys |= {st.key for a, b, st in self.stmts if st.comp != "*" and any(a <= s < b for s in self.ran)}
        return keys


def ranges(idx):
    out, idx = [], sorted(idx)
    for i in idx:
        if out and out[-1][1] == i - 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return ",".join(f"{a}" if a == b else f"{a}-{b}" for a, b in out)


def read_impact(path):
    f = pathlib.Path(path)
    if not f.exists():
        return {}
    head, *rows = f.read_text().splitlines()
    names = head.split("\t")[1].split()
    impact = {n: set() for n in names}
    for row in rows:
        idx, keys = row.split("\t")
        for part in idx.split(","):
            a, _, b = part.partition("-")
            for i in range(int(a), int(b or a) + 1):
                impact[names[i]].update(keys.split())
    return {n: frozenset(k) for n, k in impact.items()}


IMPACT = re.compile(r"^impact \[[^]]+\] (\S+)\t(.*)$", re.M)


def build(out, *dirs):
    acc = {}
    for d in dirs:
        for f in sorted(pathlib.Path(d).rglob("*.log")):
            for m in IMPACT.finditer(f.read_text(errors="replace")):
                acc.setdefault(m[1], set()).update(k for k in m[2].split() if not k.startswith(("u:", "s:")))
    names = sorted(acc)
    sets = {}
    for i, n in enumerate(names):
        for k in acc[n]:
            sets.setdefault(k, set()).add(i)
    rows = {}
    for k, idx in sets.items():
        rows.setdefault(ranges(idx), []).append(k)
    text = "checks\t" + " ".join(names) + "\n" + "".join(f"{idx}\t{' '.join(sorted(ks))}\n" for idx, ks in sorted(rows.items(), key=lambda r: sorted(r[1])[0]))
    pathlib.Path(out).write_text(text)
    print(f"{len(names)} checks, {len(sets)} keys, {len(rows)} rows, {len(text)} bytes")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"build": build}[cmd](*args)
