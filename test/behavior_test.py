import importlib.util
import json
import os
import pathlib

_spec = importlib.util.spec_from_file_location("clanker_behavior_engine", pathlib.Path(__file__).resolve().parent.parent / "tools" / "behavior" / "engine.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

START = "/test/behavior/fixtures/index.html"

HOSTED_SKIP = {("chromium", "drawer", None), ("chromium", "carousel", 390)}


def behavior(t, name):
    sc = E.load_scenario(name)
    gold = E.load_golden(name)
    key = E.run_key(t.engine, t.width, t.reduced_motion, t.rtl)
    folder = t.out / "behavior" / f"{t.engine}-{t.theme}-{t.width}{'-reduced-motion' if t.reduced_motion else ''}{'-rtl' if t.rtl else ''}"
    result = {"component": name, "run": key, "theme": t.theme, "note": sc.get("note")}
    if t.theme == "dark":
        t.skip("behavior does not depend on the theme; the light run compares it")
    if os.environ.get("GITHUB_ACTIONS") and ({(t.engine, name, None), (t.engine, name, t.width)} & HOSTED_SKIP):
        t.skip("the Chromium touch swipe does not move this component on GitHub-hosted runners: https://github.com/bl4ko/clanker-ui/issues/7")
    if gold is None or sc.get("not_recorded"):
        t.skip(sc.get("not_recorded") or f"no reference: run tools/behavior record --only {name}")
    if gold.get("scenario") != E.scenario_hash(sc):
        raise AssertionError(f"test/behavior/golden/{name}.json is for another version of the scenario: run tools/behavior record --only {name}")
    ref = gold["runs"].get(key)
    if ref is None:
        t.skip(f"no reference for {key}: run tools/behavior record --only {name} with this engine and width")
    fixture = sc.get("fixture", name)
    if isinstance(fixture, dict):
        fixture = fixture.get(str(t.width), fixture.get("default", name))
    t.docs(f"/test/behavior/fixtures/{fixture}.html")
    t.page.wait_for_function("() => document.readyState === 'complete'")
    t.page.wait_for_timeout(sc.get("wait_ours", 200))
    ours = E.run_side(t.page, sc, "ours", t.engine, "[data-behavior=preview]", ref["anchor"][0], ref.get("dates"))
    found = E.compare(sc, ref["rows"], ours["rows"], t.engine)
    open_ = sorted([f for f in found if E.failing(f)], key=lambda f: (E.SEVERITIES.index(f["severity"]), E.step_no(f)))
    first = E.first_divergence(found)
    result.update({"status": "fail" if open_ else "pass", "first_divergence": first, "differences": found, "anchor": {"shadcn": ref["anchor"], "ours": ours["anchor"]}, "rows": ours["rows"]})
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    t.shot(name, t.page)
    if open_:
        counts = {s: sum(1 for f in open_ if f["severity"] == s) for s in E.SEVERITIES}
        minor = sum(1 for f in found if not f.get("allowed") and f["severity"] == "minor")
        head = f"{len(open_)} differences from shadcn ({', '.join(f'{n} {s}' for s, n in counts.items() if n)}; {minor} minor not counted); first divergence at step {first}"
        raise AssertionError(head + "\n" + "\n".join(E.summary_line(f) for f in open_[:12]) + (f"\n... {len(open_) - 12} more in {folder / (name + '.json')}" if len(open_) > 12 else ""))


def _check(name):
    def check(t):
        behavior(t, name)

    check.__name__ = "check_" + name.replace("-", "_")
    return check


for _name in E.scenario_names():
    globals()["check_" + _name.replace("-", "_")] = _check(_name)
