import fnmatch
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def job(engine, id, only, k="", themes="", **extra):
    return {"engine": engine, "id": id, "only": only, "k": k, "themes": themes, **extra}


PR = [
    job("chromium", "behavior", "behavior", themes="light"),
    job("chromium", "foundation", "foundation"),
    job("chromium", "g1-docs", "g1,docs"),
    job("chromium", "g2a-split", "g2,split", r"^(g2\.[a-d]|split\.)"),
    job("chromium", "g2b-g5", "g2,g5", r"^(g2\.[e-n]|g5\.)"),
    job("chromium", "g2c", "g2", r"^g2\.[o-s]"),
    job("chromium", "g2d-g4a", "g2,g4", r"^(g2\.[t-z]|g4\.[a-c])"),
    job("chromium", "g3a-spike", "g3,spike", r"^(g3\.[a-c]|spike\.)"),
    job("chromium", "g3b-pages", "g3", r"^g3\.[d-z]", pages=True),
    job("chromium", "g4b", "g4", r"^g4\.[d-z]"),
    job("firefox", "behavior-a-g1-light", "behavior,g1", r"^(behavior\.[a-l]|g1\.)", "light"),
    job("firefox", "behavior-b-g4-light", "behavior,g4", r"^(behavior\.[m-z]|g4\.)", "light"),
    job("firefox", "g1-g4-dark", "g1,g4", themes="dark"),
    job("firefox", "foundation", "foundation"),
    job("firefox", "g3", "g3"),
    job("firefox", "g2a-split", "g2,split", r"^(g2\.d|split\.)"),
    job("firefox", "g2b", "g2", r"^g2\.[a-ce-n]"),
    job("firefox", "g2c-spike-docs", "g2,spike,docs", r"^(g2\.[o-s]|spike\.|docs\.)"),
    job("firefox", "g2d-g5", "g2,g5", r"^(g2\.[t-z]|g5\.)"),
    job("webkit", "behavior-docs-spike-split-pages-light", "behavior,docs,spike,split", themes="light", pages=True),
    job("webkit", "foundation-g2a-light", "foundation,g2", r"^(foundation\.|g2\.[a-d])", "light"),
    job("webkit", "g2b-g3-light", "g2,g3", r"^(g2\.[e-o]|g3\.)", "light"),
    job("webkit", "g4-g5-light", "g4,g5", themes="light"),
    job("webkit", "g1-g2c-light", "g1,g2", r"^(g1\.|g2\.[p-z])", "light"),
    job("chromium", "min-smoke", "foundation,g5,g1,g2,g3,g4", r"^(foundation\.|g5\.|g1\.select$|g2\.dialog$|g3\.carousel$|g4\.calendar$)", "light", kit="min"),
]

FULL = [
    job("webkit", "foundation-docs-spike-split-pages-dark", "foundation,docs,spike,split", themes="dark", pages=True),
    job("webkit", "g2a-g5-dark", "g2,g5", r"^(g2\.[a-d]|g5\.)", "dark"),
    job("webkit", "g2b-dark", "g2", r"^g2\.[e-z]", "dark"),
    job("webkit", "g1-g3a-dark", "g1,g3", r"^(g1\.|g3\.[a-c])", "dark"),
    job("webkit", "g3b-g4-dark", "g3,g4", r"^(g3\.[d-z]|g4\.)", "dark"),
    *[
        job("chromium", f"{mode}-{id}", only, k, "light", mode=mode)
        for mode in ("rtl", "reduced-motion")
        for id, only, k in [
            ("g2a-spike", "g2,spike", r"^(g2\.[a-n]|spike\.)"),
            ("g2b-g5", "g2,g5", r"^(g2\.[o-z]|g5\.)"),
            ("foundation-g1-docs", "foundation,g1,docs", ""),
            ("g3-g4", "g3,g4", ""),
        ]
    ],
    *[
        job("chromium", f"min-{id}", only, k, kit="min")
        for id, only, k in [
            ("foundation-docs", "foundation,docs", ""),
            ("g1", "g1", ""),
            ("g2a", "g2", r"^g2\.[a-d]"),
            ("g2b-g5", "g2,g5", r"^(g2\.[e-n]|g5\.)"),
            ("g2c", "g2", r"^g2\.[o-s]"),
            ("g2d-g4a", "g2,g4", r"^(g2\.[t-z]|g4\.[a-c])"),
            ("g3a-spike", "g3,spike", r"^(g3\.[a-c]|spike\.)"),
            ("g3b", "g3", r"^g3\.[d-z]"),
            ("g4b", "g4", r"^g4\.[d-z]"),
        ]
    ],
]

PAGES = [job("chromium", "pages", "", pages=True), job("webkit", "pages-light", "", themes="light", pages=True)]

DOCS = ["*.md", "docs/*.md", "docs/*.txt", "skills/*", "LICENSE*", "THIRD_PARTY_NOTICES", ".github/ISSUE_TEMPLATE/*", ".github/workflows/release.yml", ".github/workflows/pages.yml", "renovate.json"]
TEST_DIRS = {"test/behavior/": "behavior", "test/split/": "split", "test/spike/": "spike"}


def classify(files):
    modules, docs = set(), False
    for f in files:
        m = re.fullmatch(r"test/([a-z0-9]+)_test\.py", f)
        if f.endswith("_test.go"):
            continue
        if m:
            modules.add(m.group(1))
        elif any(f.startswith(d) for d in TEST_DIRS):
            modules.add(next(v for d, v in TEST_DIRS.items() if f.startswith(d)))
        elif any(fnmatch.fnmatch(f, p) for p in DOCS) and not f.startswith("test/"):
            docs = True
        else:
            return "full", set()
    return ("tests" if modules else "docs" if docs else "go"), modules


def plan(event, full_label, files):
    if event == "push":
        return "main", PR
    if event != "pull_request":
        return "full", PR + FULL
    if full_label:
        return "full-ci", PR + FULL
    tier, modules = classify(files)
    if tier == "full":
        return tier, PR
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
    check("README change is docs", classify(["README.md", "docs/content/index/page.md", "skills/clanker-ui/SKILL.md"]) == ("docs", set()))
    check("kit change is full", classify(["README.md", "clanker-ui.js"])[0] == "full")
    check("ci.yml change is full", classify([".github/workflows/ci.yml"])[0] == "full")
    check("run.py change is full", classify(["test/run.py"])[0] == "full")
    check("plan change is full", classify(["tools/ci/plan.py"])[0] == "full")
    check("Go test change adds no browser job", plan("pull_request", False, ["tools/gen/catalog_test.go", "banned_test.go"]) == ("go", []))
    check("Go test and docs change is docs", plan("pull_request", False, ["tools/gen/catalog_test.go", "README.md"]) == ("docs", PAGES[:1]))
    check("Go test and kit change is full", classify(["tools/gen/catalog_test.go", "tools/gen/catalog.go"])[0] == "full")
    check("test change is tests", classify(["test/g2_test.py", "test/behavior/scenarios/select.json"]) == ("tests", {"g2", "behavior"}))
    tier, jobs = plan("pull_request", False, ["test/g3_test.py"])
    check("g3 test change runs g3 in 3 engines only", tier == "tests" and {j["only"] for j in jobs} == {"g3"} and {j["engine"] for j in jobs} == {"chromium", "firefox", "webkit"} and not any(j["pages"] for j in jobs))
    check("docs change runs Chromium pages only", plan("pull_request", False, ["README.md"]) == ("docs", [PAGES[0]]) and PAGES[0]["engine"] == "chromium")
    check("pages test change runs pages in 2 engines", plan("pull_request", False, ["test/pages_test.py"]) == ("tests", PAGES))
    check("label runs all", plan("pull_request", True, ["README.md"])[1] == PR + FULL)
    check("push to main runs the pull request tier", plan("push", False, [])[1] == PR)
    check("schedule and dispatch run all", all(plan(e, False, [])[1] == PR + FULL for e in ("schedule", "workflow_dispatch")))
    return 0 if ok else 1


NAMES = checks()

if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(self_test())
    files = [l for l in pathlib.Path(sys.argv[1]).read_text().splitlines() if l] if len(sys.argv) > 1 else []
    tier, jobs = plan(os.environ["EVENT"], os.environ.get("FULL_CI") == "true", files)
    with open(os.environ["GITHUB_OUTPUT"], "a") as out:
        out.write(f"matrix={json.dumps({'include': jobs})}\n")
        out.write(f"browser={'true' if jobs else 'false'}\n")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as out:
        out.write(f"Tier `{tier}`: {len(jobs)} browser jobs, {len(files)} changed files.\n")
    print(tier, len(jobs))
