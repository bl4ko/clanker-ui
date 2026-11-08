import fnmatch
import functools
import importlib.util
import json
import math
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("clanker_ci_impact", ROOT / "tools/ci/impact.py")
IMPACT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IMPACT)


def job(engine, id, only, k="", themes="", **extra):
    return {"engine": engine, "id": id, "only": only, "k": k, "themes": themes, **extra}


LINUX_JOBS = 32
MACOS_JOBS = 5
JOB_TARGET = 150
PAGES_EXTRA = 10
SEGMENT = 5
MIN_SHARD = 180
NO_DARK = {"behavior"}
NO_MODE = {"behavior", "split"}
SMOKE = job("chromium", "min-smoke", "foundation,g5,g1,g2,g3,g4", r"^(foundation\.|g5\.|g1\.select$|g2\.dialog$|g3\.carousel$|g4\.calendar$)", "light", kit="min")


@functools.cache
def durations():
    d = {}
    f = ROOT / "tools/ci/durations.tsv"
    for line in f.read_text().splitlines()[1:] if f.exists() else []:
        engine, mode, theme, check, secs = line.split("\t")
        d[(engine, mode, theme, check)] = float(secs)
    return d


def weight(d, engine, mode, theme, check):
    for key in ((engine, mode, theme, check), (engine, "base", theme, check), (engine, "base", "light", check)):
        if key in d:
            return d[key]
    return sorted(d.values())[len(d) // 2] if d else 5.0


def pages_weight(d, engine, theme):
    return sum(weight(d, engine, "base", theme, f"pages.{n}") for n in NAMES["pages"]) + PAGES_EXTRA


def cost(part):
    return sum(u[2] for u in part) + SEGMENT * sum(a[0] != b[0] for a, b in zip(part, part[1:]))


def fill(units, cap, mix=True):
    parts, cur, load = [], [], 0.0
    for u in units:
        if cur and u[0] != cur[-1][0] and not mix:
            parts.append(cur)
            cur, load = [], 0.0
        w = u[2] + (SEGMENT if cur and u[0] != cur[-1][0] else 0)
        if cur and load + w > cap and load + w - cap > cap - load:
            parts.append(cur)
            cur, load, w = [], 0.0, u[2]
        cur.append(u)
        load += w
    return parts + [cur] if cur else parts


def cut(units, n, mix=True):
    if not units:
        return [], 0
    lo, hi = sum(u[2] for u in units) / n, sum(u[2] for u in units) + SEGMENT * len(units)
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if len(fill(units, mid, mix)) <= n else (mid, hi)
    parts = fill(units, hi, mix)
    return parts, max(map(cost, parts))


def group(d, tier, engine, theme, mode="", kit="", skip=(), pages=False, jobs=0):
    mk = mode or kit or "base"
    units = [(None, f"{m}.{n}", weight(d, engine, mk, theme, f"{m}.{n}")) for m in sorted(NAMES) if m != "pages" and m not in skip for n in NAMES[m]]
    if pages:
        units.append((None, "pages", pages_weight(d, engine, theme)))
    return {"tier": tier, "engine": engine, "theme": theme, "mode": mode, "kit": kit, "mk": mk, "units": units, "jobs": jobs}


def all_groups(d):
    return [
        group(d, "pr", "chromium", "light", skip={"pages"}),
        group(d, "pr", "chromium", "dark", skip=NO_DARK),
        group(d, "pr", "firefox", "light", skip={"pages"}),
        group(d, "pr", "firefox", "dark", skip=NO_DARK),
        group(d, "pr", "webkit", "light", skip={"pages"}, pages=True, jobs=MACOS_JOBS),
        group(d, "full", "webkit", "dark", skip=NO_DARK, pages=True, jobs=MACOS_JOBS),
        group(d, "full", "chromium", "light", mode="rtl", skip=NO_MODE),
        group(d, "full", "chromium", "light", mode="reduced-motion", skip=NO_MODE),
        group(d, "full", "chromium", "light", kit="min", skip=NO_MODE),
        group(d, "full", "chromium", "dark", kit="min", skip=NO_MODE),
    ]


def emit(groups):
    out = []
    for g in groups:
        parts = cut(g["units"], g["jobs"])[0]
        for i, part in enumerate(parts):
            names = [u[1] for u in part]
            checks = [n for n in names if n != "pages"]
            only = ",".join(dict.fromkeys(n.split(".")[0] for n in checks))
            k = "^(" + "|".join(re.escape(n) for n in checks) + ")$" if checks else ""
            extra = {"mode": g["mode"]} if g["mode"] else {"kit": g["kit"]} if g["kit"] else {}
            out.append((g["tier"], job(g["engine"], f"{g['mk']}-{g['theme']}-{i + 1}of{len(parts)}", only, k, g["theme"], **({"pages": True} if "pages" in names else {}), **extra)))
    return out


CAP = {}


def matrix():
    groups = all_groups(durations())
    linux = [g for g in groups if not g["jobs"]]
    for g in linux:
        g["jobs"] = 1
    while sum(g["jobs"] for g in linux) < LINUX_JOBS:
        g = max((g for g in linux if g["jobs"] < len(g["units"])), key=lambda g: cut(g["units"], g["jobs"])[1])
        g["jobs"] += 1
    CAP.update({(g["engine"], g["theme"], g["mk"]): g["jobs"] for g in groups if g["tier"] == "pr"})
    pr = [j for tier, j in emit(groups) if tier == "pr"] + [job("chromium", "pages-light-dark", "", pages=True), SMOKE]
    return pr, [j for tier, j in emit(groups) if tier == "full"]


def reduced(selected):
    pages = any(n.startswith("pages.") for n in selected)
    groups = []
    for g in all_groups(durations()):
        g["units"] = [u for u in g["units"] if u[1] in selected or u[1] == "pages" and pages]
        g["jobs"] = 1
        if g["tier"] == "pr" and g["units"]:
            groups.append(g)
    for macos in (False, True):
        mine = [g for g in groups if (g["engine"] == "webkit") == macos]
        while mine and sum(g["jobs"] for g in mine) < (MACOS_JOBS if macos else LINUX_JOBS):
            g = max((g for g in mine if g["jobs"] < min(len(g["units"]), CAP[(g["engine"], g["theme"], g["mk"])])), key=lambda g: cut(g["units"], g["jobs"])[1], default=None)
            if not g or cut(g["units"], g["jobs"])[1] <= JOB_TARGET:
                break
            g["jobs"] += 1
    d = durations()
    smoke = [(None, n, weight(d, "chromium", "min", "light", n)) for m in sorted(NAMES) for n in (f"{m}.{x}" for x in NAMES[m]) if re.search(SMOKE["k"], n) and (m == "foundation" or n in selected)]
    smoke = {"tier": "pr", "engine": "chromium", "theme": "light", "mode": "", "kit": "min", "mk": "min-smoke", "units": smoke, "jobs": 1}
    while cut(smoke["units"], smoke["jobs"])[1] > JOB_TARGET and smoke["jobs"] < len(smoke["units"]):
        smoke["jobs"] += 1
    return [j for _, j in emit(groups + [smoke])] + [job("chromium", f"pages-{t}", "", themes=t, pages=True) for t in ("light", "dark") if pages]


def shards(jobs, n, mix=True, apart=(), coarse=False, min_secs=MIN_SHARD):
    d = durations()
    groups = {}
    for ji, j in enumerate(jobs):
        mk = j.get("mode") or j.get("kit") or "base"
        k = re.compile(j["k"]) if j.get("k") else None
        for theme in (j.get("themes") or "light,dark").split(","):
            units = [(m, f"{m}.{x}") for m in (j.get("only") or "").split(",") if m for x in NAMES[m] if not k or k.search(f"{m}.{x}")]
            for m, name in units + ([("pages", "pages")] if j.get("pages") else []):
                key = (j["engine"], j.get("mode") or "", j.get("kit") or "", theme, m if m in apart or m == "pages" else "")
                inst = 0
                while name in groups.setdefault((*key, inst), {}):
                    inst += 1
                groups[(*key, inst)][name] = (ji, pages_weight(d, j["engine"], theme) if name == "pages" else weight(d, j["engine"], mk, theme, name))
    seq = []
    for g in sorted((g for g in groups if groups[g]), key=lambda g: (-sum(w for _, w in groups[g].values()), g)):
        units = {}
        for name, (ji, w) in groups[g].items():
            units.setdefault((ji, name.split(".")[0]) if coarse else name, []).append((name, w))
        seq += [(g, tuple(x for x, _ in u), sum(w for _, w in u)) for u in units.values()]
    total = sum(u[2] for u in seq)
    n = max(1, min(n, math.ceil(total / min_secs))) if min_secs else n
    if coarse:
        bins = [[] for _ in range(min(n, len(seq)))]
        for u in sorted(seq, key=lambda u: -u[2]):
            min(bins, key=cost).append(u)
        parts = [sorted(b, key=seq.index) for b in bins]
    else:
        parts = cut(seq, n, mix)[0]
        if not mix:
            count = {}
            for part in parts:
                count[part[0][0]] = count.get(part[0][0], 0) + 1
            parts = [p for g, c in count.items() for p in cut([u for u in seq if u[0] == g], c)[0]]
    out = []
    for i, part in enumerate(sorted(parts, key=lambda p: -cost(p))):
        segs = []
        for g, names, _ in part:
            if segs and segs[-1][0] == g:
                segs[-1][1].extend(names)
            else:
                segs.append((g, list(names)))
        jobs_ = []
        for (engine, mode, kit, theme, kind, _), names in segs:
            checks = [x for x in names if x != "pages"]
            jobs_.append({"engine": engine, "only": ",".join(dict.fromkeys(x.split(".")[0] for x in checks)), "k": "^(" + "|".join(re.escape(x) for x in checks) + ")$" if checks else "", "themes": theme, "mode": mode, "kit": kit, "pages": not checks, "kind": kind})
        label = "+".join(dict.fromkeys("-".join(x for x in (s["kind"] if s["kind"] != "pages" else "", "pages" if s["pages"] else s["mode"] or s["kit"] or "base", s["themes"]) if x) for s in jobs_))
        out.append({"id": f"{jobs_[0]['engine'][0]}{i:02d}-{label}", "est": round(cost(part)), "apart": next((s["kind"] for s in jobs_ if s["kind"] in apart), ""), "segments": jobs_})
    if coverage([s for e in out for s in e["segments"]]) != coverage(jobs):
        sys.exit("shards change the check set")
    return out


PAGES = [job("chromium", "pages", "", pages=True), job("webkit", "pages-light", "", themes="light", pages=True)]

DOCS = ["*.md", "docs/*.md", "docs/*.txt", "skills/*", "LICENSE*", "THIRD_PARTY_NOTICES", ".github/ISSUE_TEMPLATE/*", ".github/workflows/release.yml", ".github/workflows/pages.yml", "renovate.json"]
TEST_DIRS = {"test/behavior/": "behavior", "test/split/": "split", "test/spike/": "spike", "test/lint/": "lint,pages", "skills/clanker-ui/references/design-lint.js": "lint,pages"}


def classify(files, read=None):
    modules, docs, reqs = set(), False, []
    kit = any(f in IMPACT.KIT_SOURCES for f in files)
    g = IMPACT.groups(ROOT) if read else None
    pages = {str(p.relative_to(ROOT)): p.read_text() for p in ROOT.glob("docs/content/**/page.md")} if read else {}
    for f in files:
        m = re.fullmatch(r"test/([a-z0-9]+)_test\.py", f)
        if f.endswith("_test.go") or f.startswith("dist/") and kit and read:
            continue
        if m:
            modules.add(m.group(1))
        elif any(f.startswith(d) for d in TEST_DIRS):
            modules.update(next(v for d, v in TEST_DIRS.items() if f.startswith(d)).split(","))
        elif read and (r := IMPACT.file_reqs(f, *read(f), g, pages)) is not None:
            reqs += r
        elif any(fnmatch.fnmatch(f, p) for p in DOCS) and not f.startswith("test/"):
            docs = True
        else:
            return "full", set(), []
    return ("impact" if reqs else "tests" if modules else "docs" if docs else "go"), modules, reqs


def select(reqs, modules, impact):
    known = set().union(*impact.values()) if impact else set()
    need = []
    for r in reqs:
        r = frozenset("site:docs" if k not in known and re.match(r"p:/(docs|view/)", k) else k for k in r)
        if len(r) == 1 and (k := next(iter(r))).startswith("j:") and k not in known:
            comp = k.split(":")[1]
            need += [frozenset({"c:" + comp})] + [frozenset({j}) for j in known if j.startswith(f"j:{comp}:")]
            if comp == "*" or "c:" + comp not in known:
                return None
            continue
        if not r <= known:
            return None
        need.append(r)
    names = {f"{m}.{n}" for m, ns in NAMES.items() for n in ns}
    return {n for n in names if n not in impact or n.split(".")[0] in modules or any(r <= impact[n] for r in need)}


def current_map():
    impact, source = IMPACT.read_impact(ROOT / "tools/ci/impact.tsv")
    if source and source == IMPACT.source_hash(ROOT, os.environ.get("PLAN_BASE", "HEAD^1")):
        return impact
    print("tools/ci/impact.tsv does not match the base tree: pull request tier", file=sys.stderr)
    return {}


def git_read(f):
    def show(rev):
        r = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{f}"], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    return show(os.environ.get("PLAN_BASE", "HEAD^1")), show("HEAD")


def plan(event, full_label, files, read=None, impact=None):
    if event != "pull_request":
        return "full", PR + FULL
    if full_label:
        return "full-ci", PR + FULL
    tier, modules, reqs = classify(files, read)
    if tier == "full":
        return tier, PR
    if tier == "impact":
        selected = select(reqs, modules, current_map() if impact is None else impact)
        if selected is None:
            return "full", PR
        jobs = reduced(selected)
        if any(f in IMPACT.KIT_SOURCES for f in files):
            jobs = [j for j in jobs if j["engine"] != "webkit"] + [j for j in PR if j["engine"] == "webkit"]
        docs = any(fnmatch.fnmatch(f, p) for f in files for p in DOCS if not f.startswith("test/"))
        return tier, jobs + (PAGES[:1] if docs and not any(j.get("pages") for j in jobs) else [])
    out = []
    if tier == "tests":
        for j in PR:
            only = [m for m in j["only"].split(",") if m in modules]
            if only:
                out.append({**j, "only": ",".join(only), "pages": False})
    if "pages" in modules:
        out += PAGES
    elif tier == "docs":
        out += PAGES[:1]
    return tier, out


def checks():
    names = {}
    for f in sorted((ROOT / "test").glob("*_test.py")):
        m = f.stem.removesuffix("_test")
        if m == "behavior":
            names[m] = [p.stem.replace("-", "_") for p in (ROOT / "test/behavior/scenarios").glob("*.json")]
        else:
            names[m] = re.findall(r"^def check_(\w+)", f.read_text(), re.M)
    return names


def coverage(jobs):
    seen = {}
    for j in jobs:
        k = re.compile(j["k"]) if j["k"] else None
        mods = [m for m in j["only"].split(",") if m]
        for theme in (j["themes"] or "light,dark").split(","):
            mode = j.get("mode") or j.get("kit") or "base"
            for m in mods + (["pages"] if j.get("pages") else []):
                for n in NAMES[m]:
                    if m == "pages" or not k or k.search(f"{m}.{n}"):
                        key = (j["engine"], theme, mode, f"{m}.{n}")
                        seen[key] = seen.get(key, 0) + 1
    return seen


def want(engines, themes, mode, skip):
    return {(e, t, mode, f"{m}.{n}") for e in engines for t in themes for m, ns in NAMES.items() if m not in skip for n in ns if not (m == "behavior" and t == "dark")}


def self_test():
    ok = True
    def check(name, cond):
        nonlocal ok
        print(("ok   " if cond else "FAIL ") + name)
        ok = ok and cond
    for jobs, wanted, name in [
        (PR, want(["chromium", "firefox"], ["light", "dark"], "base", {"pages"}) | want(["webkit"], ["light"], "base", {"pages"}) | want(["chromium", "webkit"], ["light"], "base", {m for m in NAMES if m != "pages"}) | want(["chromium"], ["dark"], "base", {m for m in NAMES if m != "pages"}), "pull request tier"),
        (PR + FULL, want(["chromium", "firefox", "webkit"], ["light", "dark"], "base", {"pages"}) | want(["chromium", "webkit"], ["light", "dark"], "base", {m for m in NAMES if m != "pages"}) | want(["chromium"], ["light"], "rtl", {"behavior", "split", "pages"}) | want(["chromium"], ["light"], "reduced-motion", {"behavior", "split", "pages"}) | want(["chromium"], ["light", "dark"], "min", {"behavior", "split", "pages"}), "full matrix"),
    ]:
        seen = coverage(jobs)
        smoke = coverage([j for j in jobs if j["id"] == "min-smoke"])
        extra = {k for k in seen if k not in wanted and k not in smoke}
        missing = wanted - set(seen)
        twice = {k for k, v in seen.items() if v - smoke.get(k, 0) > 1}
        check(f"{name}: every check runs once ({len(wanted)} runs)", not missing and not extra and not twice)
        for k in sorted(missing)[:5] + sorted(extra)[:5] + sorted(twice)[:5]:
            print("  ", k)
    check("macOS jobs on a pull request <= 5", sum(j["engine"] == "webkit" for j in PR) <= 5)
    check("unique job ids", len({(j["engine"], j["id"]) for j in PR + FULL + PAGES}) == len(PR + FULL + PAGES))
    check("README change is docs", classify(["README.md", "docs/content/index/page.md", "skills/clanker-ui/SKILL.md"])[:2] == ("docs", set()))
    check("kit change is full", classify(["README.md", "clanker-ui.js"])[0] == "full")
    check("ci.yml change is full", classify([".github/workflows/ci.yml"])[0] == "full")
    check("run.py change is full", classify(["test/run.py"])[0] == "full")
    check("plan change is full", classify(["tools/ci/plan.py"])[0] == "full")
    check("Go test change adds no browser job", plan("pull_request", False, ["tools/gen/catalog_test.go", "banned_test.go"]) == ("go", []))
    check("Go test and docs change is docs", plan("pull_request", False, ["tools/gen/catalog_test.go", "README.md"]) == ("docs", PAGES[:1]))
    check("Go test and kit change is full", classify(["tools/gen/catalog_test.go", "tools/gen/catalog.go"])[0] == "full")
    check("test change is tests", classify(["test/g2_test.py", "test/behavior/scenarios/select.json"])[:2] == ("tests", {"g2", "behavior"}))
    tier, jobs = plan("pull_request", False, ["test/g3_test.py"])
    check("g3 test change runs g3 in 3 engines only", tier == "tests" and {j["only"] for j in jobs} == {"g3"} and {j["engine"] for j in jobs} == {"chromium", "firefox", "webkit"} and not any(j["pages"] for j in jobs))
    check("docs change runs Chromium pages only", plan("pull_request", False, ["README.md"]) == ("docs", [PAGES[0]]) and PAGES[0]["engine"] == "chromium")
    check("pages test change runs pages in 2 engines", plan("pull_request", False, ["test/pages_test.py"]) == ("tests", PAGES))
    check("design lint change runs lint and pages", classify(["skills/clanker-ui/references/design-lint.js", "test/lint/bad.html"])[:2] == ("tests", {"lint", "pages"}))
    check("label runs all", plan("pull_request", True, ["README.md"])[1] == PR + FULL)
    check("schedule and dispatch run all", all(plan(e, False, [])[1] == PR + FULL for e in ("schedule", "workflow_dispatch")))
    js, css = (ROOT / "clanker-ui.js").read_text(), (ROOT / "clanker-ui.css").read_text()
    page = (ROOT / "docs/content/components/button/page.md").read_text()
    edits = {
        "carousel": ("clanker-ui.js", js.replace("function carouselChange(inst) {\n", "function carouselChange(inst) {\n  inst.x = 1\n", 1)),
        "core": ("clanker-ui.js", js.replace("\nconst SVG_NS", "\nconst coreX = 1\nconst SVG_NS", 1)),
        "token": ("clanker-ui.css", css.replace("    --radius: .625rem;\n", "    --radius: .5rem;\n", 1)),
        "button": ("clanker-ui.css", css.replace('  [data-slot="button"] {\n', '  [data-slot="button"] {\n    color: red;\n', 1)),
        "page": ("docs/content/components/button/page.md", page + "\nMore text.\n"),
        "title": ("docs/content/components/button/page.md", page.replace("title: Button", "title: Buttons", 1)),
    }
    new = {k: v for k, v in edits.values()}
    def reader(*names):
        texts = dict(edits[n] for n in names)
        return lambda f: ((ROOT / f).read_text() if (ROOT / f).exists() else None, texts.get(f, (ROOT / f).read_text() if (ROOT / f).exists() else None))
    check("self-test edits apply", all(t != (ROOT / f).read_text() for f, t in edits.values()))
    names = [f"{m}.{n}" for m, ns in NAMES.items() for n in ns]
    impact = {n: frozenset({"c:carousel"} if n.startswith("g3.carousel") else {"site:docs", "p:/docs/components/button", "c:button"} if n.startswith(("docs.", "pages.")) else {"c:button"}) for n in names if n != "g1.select"}
    def run(names_, files=None):
        return plan("pull_request", False, files or [edits[n][0] for n in names_], reader(*names_), impact)
    tier, jobs = run(["carousel"])
    sel = {n for n in names if n.startswith("g3.carousel") or n == "g1.select"}
    smoke = {k[3] for k in coverage([SMOKE])}
    got = coverage(jobs)
    base = {k: v for k, v in got.items() if k[2] != "min" and k[0] != "webkit"}
    wanted = {k for k in coverage(PR) if k[3] in sel and k[2] != "min" and k[0] != "webkit"}
    check("carousel change runs its checks once in each pull request variant, plus unmeasured checks", tier == "impact" and set(base) == wanted and set(base.values()) == {1})
    check("min-smoke keeps foundation and only the selected rest", {k[3] for k in got if k[2] == "min"} == {n for n in smoke if n.startswith("foundation.") or n in sel} and set(v for k, v in got.items() if k[2] == "min") == {1})
    check("carousel change needs fewer jobs", len(jobs) < len(PR))
    narrow = {**impact, "g3.carousel_motion": impact["g3.carousel_motion"] | {"j:carousel:carouselChange"}}
    check("measured JS statement selects only the checks that ran it", {k[3] for k in coverage(plan("pull_request", False, ["clanker-ui.js"], reader("carousel"), narrow)[1]) if k[2] != "min" and k[0] != "webkit"} == {"g3.carousel_motion", "g1.select"})
    check("core JS change is full", run(["core"]) == ("full", PR))
    check("token CSS change is full", run(["token"]) == ("full", PR))
    tier, jobs = run(["button"])
    check("button CSS change runs the checks that touch button", tier == "impact" and {k[3] for k in coverage(jobs) if k[2] != "min" and k[0] != "webkit"} == {n for n in names if not n.startswith("g3.carousel")})
    tier, jobs = run(["page"])
    check("docs page change runs docs and pages checks", tier == "impact" and {k[3].split(".")[0] for k in coverage(jobs) if k[2] != "min"} >= {"docs", "pages"} and any(j.get("pages") for j in jobs))
    check("front matter change counts for all docs pages", classify(["docs/content/components/button/page.md"], reader("title"))[2] == [frozenset({"site:docs"})])
    check("kit change with dist is impact", run(["carousel"], ["clanker-ui.js", "dist/clanker-ui.min.js"])[0] == "impact")
    check("dist change alone is full", run([], ["dist/clanker-ui.min.js"])[0] == "full")
    check("plan, impact map, or harness change with a kit change is full", all(run(["carousel"], ["clanker-ui.js", f])[0] == "full" for f in ("tools/ci/plan.py", "tools/ci/impact.py", "tools/ci/impact.tsv", "test/run.py")))
    check("unmeasured component is full", plan("pull_request", False, ["clanker-ui.js"], reader("carousel"), {n: frozenset({"c:button"}) for n in names})[0] == "full")
    check("label still runs all with a kit change", plan("pull_request", True, ["clanker-ui.js"], reader("carousel"), impact)[1] == PR + FULL)
    check("kit change keeps the WebKit pull request jobs", [j for j in run(["carousel"])[1] if j["engine"] == "webkit"] == [j for j in PR if j["engine"] == "webkit"])
    check("docs page change reduces WebKit", sum(j["engine"] == "webkit" for j in run(["page"])[1]) < sum(j["engine"] == "webkit" for j in PR))
    check("stale impact map is full", plan("pull_request", False, ["clanker-ui.js"], reader("carousel"), {}) == ("full", PR))
    head = IMPACT.source_hash(ROOT, "HEAD")
    check("impact map records the source tree", re.fullmatch(r"[0-9a-f]{16}", head) is not None and IMPACT.source_hash(ROOT, "no-such-rev") == "")
    linux = [j for j in PR + FULL if j["engine"] != "webkit"]
    k8s = shards(linux, 32)
    check("runner shards keep the check set and the count", len(k8s) <= 32 and coverage([x for e in k8s for x in e["segments"]]) == coverage(linux))
    ffj = [j for j in linux if j["engine"] == "firefox"]
    segs = [set(coverage([x])) for e in shards(ffj, 10, coarse=True) for x in e["segments"]]
    units = [{k for k in coverage([j]) if k[1] == t and k[3].startswith(m + ".")} for j in ffj for t in (j["themes"] or "light,dark").split(",") for m in j["only"].split(",")]
    check("coarse shards keep each module of a matrix job in one shard", all(sum(u <= s for s in segs) == 1 for u in units if u))
    wk = shards([j for j in PR + FULL if j["engine"] == "webkit"], 16, mix=False, apart=("behavior",))
    check("separate shards have one segment, behavior apart", len(wk) <= 16 and all(len(e["segments"]) == 1 for e in wk) and all((e["segments"][0]["only"] == "behavior") == (e["apart"] == "behavior") for e in wk))
    return 0 if ok else 1


NAMES = checks()
PR, FULL = matrix()

if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(self_test())
    files = [l for l in pathlib.Path(sys.argv[1]).read_text().splitlines() if l] if len(sys.argv) > 1 else []
    tier, jobs = plan(os.environ["EVENT"], os.environ.get("FULL_CI") == "true", files, git_read)
    with open(os.environ["GITHUB_OUTPUT"], "a") as out:
        out.write(f"matrix={json.dumps({'include': jobs})}\n")
        out.write(f"browser={'true' if jobs else 'false'}\n")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as out:
        out.write(f"Tier `{tier}`: {len(jobs)} browser jobs, {len(files)} changed files.\n")
    print(tier, len(jobs))
