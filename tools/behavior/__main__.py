import sys

sys.dont_write_bytecode = True

import argparse
import datetime
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import time
import traceback
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("clanker_behavior_engine", HERE / "engine.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

PIN = next((line.split('"')[1] for line in (E.ROOT / "tools" / "gen" / "main.go").read_text().splitlines() if line.strip().startswith("shadcnSHA")), None)
PACKAGE = "https://raw.githubusercontent.com/shadcn-ui/ui/{ref}/apps/v4/package.json"
DPL = re.compile(r'data-dpl-id="(dpl_[A-Za-z0-9]+)"')


def base_ui_version(pw, ref):
    rq = pw.request.new_context()
    try:
        res = rq.get(PACKAGE.format(ref=ref), timeout=30000)
        if not res.ok:
            return None
        return json.loads(res.text()).get("dependencies", {}).get("@base-ui/react")
    except (PlaywrightError, ValueError):
        return None
    finally:
        rq.dispose()


def live_deploy(pw, path="/docs/components/base/button"):
    rq = pw.request.new_context()
    try:
        res = rq.get(E.SITE + path, timeout=60000)
        m = DPL.search(res.text()) if res.ok else None
        return m.group(1) if m else None
    except PlaywrightError:
        return None
    finally:
        rq.dispose()


def prerendered_day(ctx, url, clock):
    res = ctx.request.get(url, timeout=60000)
    if not res.ok:
        return None
    for tag in re.findall(r"<[^>]+>", res.text()):
        if f'{clock["mark"]}="true"' in tag:
            m = re.search(clock["date"] + r'="(\d{4})-(\d{2})-(\d{2})"', tag)
            if m:
                return tuple(int(x) for x in m.groups())
    return None


def open_live(browser, sc, width, hosts, reduced_motion):
    ctx = browser.new_context(viewport={"width": width, "height": E.WIDTHS[width]}, color_scheme="light", reduced_motion="reduce" if reduced_motion else "no-preference")
    url = sc.get("url") or f"{E.SITE}/docs/components/base/{sc.get('page', sc['name'])}"
    clock = (sc.get("dates") or {}).get("clock")
    day = prerendered_day(ctx, url, clock) if clock else None
    if clock and not day:
        raise E.StepError(f"no {clock['mark']} day in the prerendered page")
    ctx.add_init_script(E.pin_clock(*day) if day else E.TODAY)

    def route(r):
        url = r.request.url
        host = urlparse(url).hostname or ""
        if url.startswith("data:") or url.startswith("blob:") or host == E.SITE_HOST:
            r.continue_()
        else:
            hosts[host] = hosts.get(host, 0) + 1
            r.abort()

    ctx.route("**/*", route)
    page = ctx.new_page()
    root = sc.get("root", "[data-slot=preview]")
    res = page.goto(url, wait_until="domcontentloaded", timeout=90000)
    deploy = None
    try:
        m = DPL.search(res.text()) if res else None
        deploy = m.group(1) if m else None
    except PlaywrightError:
        pass
    page.wait_for_selector(root, state="attached", timeout=30000)
    page.wait_for_function(E.HYDRATED, arg=root, timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightError:
        pass
    page.add_style_tag(content=E.SHADCN_FONT)
    nth = sc.get("preview", 0)
    ok = page.evaluate(
        """([sel, n]) => {
          const p = document.querySelectorAll(sel)[n]
          if (!p) return false
          p.setAttribute("data-bh-preview", "")
          p.scrollIntoView({ block: "center" })
          return true
        }""",
        [root, nth],
    )
    if not ok:
        raise E.StepError(f"{root} {nth} not found on {url}")
    page.wait_for_timeout(sc.get("wait", 800))
    return ctx, page, url, deploy, ("%04d-%02d-%02d" % day if day else None)


def record_one(browser, engine, sc, width, reduced_motion, hosts):
    ctx = None
    try:
        ctx, page, url, deploy, clock = open_live(browser, sc, width, hosts, reduced_motion)
        run = E.run_side(page, sc, "shadcn", engine, "[data-bh-preview]")
        run["url"] = url
        run["deploy"] = deploy
        if clock:
            run["clock"] = clock
        return run
    finally:
        if ctx:
            try:
                ctx.close()
            except PlaywrightError:
                pass


def launch(pw, engine):
    opts = {"headless": True}
    if engine == "firefox":
        opts["firefox_user_prefs"] = {"layout.css.prefers-color-scheme.content-override": 1, "privacy.bounceTrackingProtection.mode": 0}
    return getattr(pw, engine).launch(**opts)


def react_noise(sc, f):
    i = E.step_no(f)
    step = sc["steps"][i - 1] if 0 < i <= len(sc["steps"]) else None
    return f["class"] == "timing" and not (step and (step.get("do") in E.INTENT or step.get("delays")))


def starved(run):
    out = []
    for i, r in enumerate(run["rows"]):
        for part, m in (r.get("motion") or {}).items():
            anims = [a for a in m.get("animations") or [] if not a["name"].startswith("transition ")]
            longest = max((a["duration"] for a in anims), default=0)
            start = m.get("dom_open") if m.get("dom_open") is not None else m.get("dom_close")
            cut = m.get("dom_gone") is not None and start is not None and m["dom_gone"] - start < longest
            if longest > 3 * E.FRAME and not cut and m.get("paint_start") is not None and m.get("paint_end") == m["paint_start"]:
                out.append(f"{i}. {r['label']}: {part} {anims[0]['name']} painted in one frame (the page was busy)")
    return out


def record(args):
    names = [n for n in args.only.split(",") if n] or E.scenario_names()
    engines = [e for e in args.engines.split(",") if e]
    widths = [int(w) for w in args.widths.split(",") if w]
    E.GOLDEN.mkdir(parents=True, exist_ok=True)
    failures = 0
    started = time.time()
    with sync_playwright() as pw:
        base_ui = base_ui_version(pw, PIN)
        if base_ui is None:
            print(f"warning: no @base-ui/react version from {PACKAGE.format(ref=PIN)}")
        for engine in engines:
            browser = launch(pw, engine)
            for name in names:
                sc = E.load_scenario(name)
                if sc.get("not_recorded"):
                    print(f"[{engine}] {name}: not recorded: {sc['not_recorded']}")
                    continue
                gold = E.load_golden(name) or {}
                h = E.scenario_hash(sc)
                if gold.get("scenario") != h:
                    gold = {}
                gold.update({"component": name, "scenario": h, "shadcn_pin": PIN, "url": sc.get("url") or f"{E.SITE}/docs/components/base/{sc.get('page', name)}", "root": sc.get("root", "[data-slot=preview]"), "preview": sc.get("preview", 0), "base_ui": base_ui})
                gold.setdefault("runs", {})
                gold.setdefault("blocked_hosts", {})
                for width in widths:
                    key = E.run_key(engine, width, args.reduced_motion)
                    t = time.time()
                    hosts = {}
                    try:
                        run = record_one(browser, engine, sc, width, args.reduced_motion, hosts)
                        unstable = []
                        if args.check:
                            again = record_one(browser, engine, sc, width, args.reduced_motion, {})
                            unstable = [E.summary_line(f) for f in E.compare(sc, run["rows"], again["rows"], engine) if E.failing(f) and not react_noise(sc, f)] + starved(run) + starved(again)
                        run["recorded"] = datetime.date.today().isoformat()
                        if unstable:
                            failures += 1
                            print(f"[{key}] {name}: UNSTABLE on the live page, not saved:")
                            for f in unstable[:20]:
                                print("    " + f)
                            continue
                        errors = [f"{r['label']}: {r['error']}" for r in run["rows"] if r.get("error")]
                        gold["runs"][key] = run
                        for hst, n in hosts.items():
                            gold["blocked_hosts"][hst] = max(gold["blocked_hosts"].get(hst, 0), n)
                        tag = f"{len(run['rows']) - 1} steps" + (f", {len(errors)} step errors" if errors else "")
                        print(f"[{key}] {name}: {tag}{', checked twice' if args.check else ''} ({time.time() - t:.0f}s)", flush=True)
                        for e in errors:
                            print("    step error: " + e)
                    except Exception as e:
                        failures += 1
                        print(f"[{key}] {name}: ERROR {''.join(traceback.format_exception_only(e)).strip()}", flush=True)
                        if args.verbose:
                            traceback.print_exc()
                gold["recorded"] = max((r.get("recorded", "") for r in gold["runs"].values()), default=None)
                gold["deploy"] = sorted({r.get("deploy") for r in gold["runs"].values() if r.get("deploy")}) or gold.get("deploy")
                gold["runs"] = dict(sorted(gold["runs"].items()))
                E.golden_path(name).write_text(dump_golden(gold))
            browser.close()
    print(f"recorded {len(names)} scenarios in {time.time() - started:.0f}s, {failures} problems")
    return 1 if failures else 0


def dump_golden(gold):
    c = lambda v: json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    head = [f'  {c(k)}: {c(v)}' for k, v in gold.items() if k != "runs"]
    runs = []
    for key, run in gold["runs"].items():
        meta = ", ".join(f"{c(k)}: {c(v)}" for k, v in run.items() if k != "rows")
        rows = ",\n".join(f"    {c(r)}" for r in run["rows"])
        runs.append(f'  {c(key)}: {{{meta}, "rows": [\n{rows}\n  ]}}')
    return "{\n" + ",\n".join(head + ['  "runs": {\n' + ",\n".join(runs) + "\n  }"]) + "\n}\n"


def stamp(args):
    with sync_playwright() as pw:
        deploy = live_deploy(pw)
        base_ui = base_ui_version(pw, PIN)
    print(f"live deploy {deploy}, @base-ui/react {base_ui} at {PIN}")
    for name in E.scenario_names():
        gold = E.load_golden(name)
        if not gold:
            continue
        if not gold.get("deploy"):
            gold["deploy"] = [deploy] if deploy else []
            gold["deploy_note"] = f"stamped {datetime.date.today().isoformat()} after the record; the deploy did not change since the record"
        if not gold.get("base_ui"):
            gold["base_ui"] = base_ui
        E.golden_path(name).write_text(dump_golden(gold))
    return 0


def status(args):
    with sync_playwright() as pw:
        deploy = live_deploy(pw)
        pinned = base_ui_version(pw, PIN)
        latest = base_ui_version(pw, "main")
    stale = []
    for name in E.scenario_names():
        gold = E.load_golden(name)
        why = []
        if not gold:
            why.append("no reference")
        else:
            if gold.get("scenario") != E.scenario_hash(E.load_scenario(name)):
                why.append("scenario changed")
            if gold.get("shadcn_pin") != PIN:
                why.append(f"pin {gold.get('shadcn_pin')} -> {PIN}")
            if gold.get("base_ui") != latest:
                why.append(f"@base-ui/react {gold.get('base_ui')} -> {latest} (main)")
            if deploy and deploy not in (gold.get("deploy") or []):
                why.append(f"deploy {', '.join(gold.get('deploy') or ['?'])} -> {deploy}")
        if why:
            stale.append(name)
            print(f"{name}: {'; '.join(why)}")
    print(f"live deploy {deploy}; @base-ui/react {pinned} at the pin, {latest} on main; {len(stale)} of {len(E.scenario_names())} references to record again")
    return 1 if stale else 0


def gate(args):
    engines = ["chromium", "webkit"] if args.quick else [e for e in args.engines.split(",") if e]
    widths = "1280" if args.quick else args.widths
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-I", str(E.ROOT / "test" / "run.py"), "--base-url", args.base_url, "--only", "behavior", "--themes", "light", "--widths", widths, "--engines", ",".join(engines), "--jobs", str(len(engines)), "--out", str(out)]
    if args.k:
        cmd += ["-k", args.k]
    queue = args.queue or os.environ.get("BEHAVIOR_QUEUE")
    if queue:
        cmd = ["sh", queue] + cmd
    with open(out / "gate.log", "w") as log:
        code = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
    print("\n".join(line for line in (out / "gate.log").read_text().splitlines() if re.match(r"(\w+: \d+ passed|\w+: NOT RUN|\d+ failures in )", line)))
    args.dir = str(out)
    report(args)
    return 1 if code else 0


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def report(args):
    out = pathlib.Path(args.dir)
    results = {}
    for f in sorted((out / "behavior").glob("*/*.json")):
        data = json.loads(f.read_text())
        results.setdefault(data["component"], {})[f.parent.name] = data
    if not results:
        print(f"no behavior results under {out / 'behavior'}")
        return 1
    lines = ["# Behavior parity with shadcn", ""]
    lines.append(f"Generated {datetime.datetime.now().isoformat(timespec='minutes')} from `{out}`. Reference: `test/behavior/golden/` (live `ui.shadcn.com`, shadcn pin `{PIN}`). Tolerances: delays and painted times {E.TOLERANCE['ms']} ms plus two frames, animation durations {E.TOLERANCE['ms']} ms, geometry {E.TOLERANCE['px']} px.")
    lines.append("")
    lines.append("Classes: focus, keyboard, state, ARIA, dismiss, timing, geometry. Severity: broken (the interaction fails, or focus or the popup is lost), visible (a user sees or hears a difference), minor (a small geometry or animation number, or a Base UI attribute that CSS can use; a wrong delay is always visible). A check fails on broken and visible differences; minor ones are listed only. The first divergent step is the likely root cause; later rows can follow from it.")
    lines.append("")
    runs_all = sorted({k for runs in results.values() for k in runs})
    lines += ["## Pass and fail per run", "", "| Component | " + " | ".join(runs_all) + " |", "| --- |" + " --- |" * len(runs_all)]
    for comp in sorted(results):
        lines.append(f"| {comp} | " + " | ".join(results[comp].get(k, {}).get("status", "-") for k in runs_all) + " |")
    passed = {k: sum(1 for c in results if results[c].get(k, {}).get("status") == "pass") for k in runs_all}
    lines.append("| passed | " + " | ".join(f"{passed[k]} of {sum(1 for c in results if k in results[c])}" for k in runs_all) + " |")
    lines.append("")
    total = {}
    rows = []
    for comp in sorted(results):
        runs = results[comp]
        primary = next((runs[k] for k in sorted(runs) if k.startswith("chromium") and k.endswith("1280")), None) or runs[sorted(runs)[0]]
        fs = [f for f in primary.get("differences", []) if not f.get("allowed")]
        n = {s: sum(1 for f in fs if f["severity"] == s) for s in E.SEVERITIES}
        for f in fs:
            total.setdefault(f["class"], {}).setdefault(f["severity"], 0)
            total[f["class"]][f["severity"]] += 1
        status = primary.get("status", "")
        rows.append(f"| [{comp}](#{comp}) | {status} | {n['broken']} | {n['visible']} | {n['minor']} | {', '.join(sorted(runs))} |")
    lines += ["## Totals (Chromium 1280 where present)", "", "| Class | broken | visible | minor |", "| --- | --- | --- | --- |"]
    for c in E.CLASSES:
        r = total.get(c, {})
        lines.append(f"| {c} | {r.get('broken', 0)} | {r.get('visible', 0)} | {r.get('minor', 0)} |")
    lines += ["", "## Components", "", "| Component | Status | broken | visible | minor | Runs |", "| --- | --- | --- | --- | --- | --- |"] + rows + [""]
    lines += ["## Differences by component and step", ""]
    for comp in sorted(results):
        runs = results[comp]
        keys = sorted(runs)
        primary_key = next((k for k in keys if k.startswith("chromium") and k.endswith("1280")), keys[0])
        primary = runs[primary_key]
        lines += [f"### {comp}", ""]
        if primary.get("note"):
            lines += [primary["note"], ""]
        if primary.get("error"):
            lines += [f"Run error: `{esc(primary['error'])}`", ""]
        if primary.get("first_divergence") is not None:
            lines += [f"First divergent step in {primary_key}: {primary['first_divergence']}.", ""]
        fs = sorted(primary.get("differences", []), key=lambda f: (bool(f.get("allowed")), E.SEVERITIES.index(f["severity"]), int(f["step"].split(".")[0]) if f["step"][0].isdigit() else 999))
        if not fs and not primary.get("error"):
            lines += [f"No differences in {primary_key}.", ""]
        if fs:
            lines += [f"Run {primary_key}.", "", "| Step | What | shadcn | ours | Class | Severity |", "| --- | --- | --- | --- | --- | --- |"]
            for f in fs:
                what = f["what"] + (f" (also steps {', '.join(f['also'][:8])})" if f.get("also") else "") + (" **first divergence**" if f.get("first") else " (after the first divergence)" if f.get("after_first") and f["severity"] != "minor" else "")
                note = f"<br>{esc(f['note'])}" if f.get("note") else ""
                lines.append(f"| {esc(f['step'])} | {esc(what)}{note} | {esc(f['shadcn'])} | {esc(f['ours'])} | {f['class']} | {'allowed: ' + esc(f['allowed']) if f.get('allowed') else f['severity']} |")
            lines.append("")
        base = {(f["what"], f["shadcn"], f["ours"]) for f in primary.get("differences", [])}
        extra = []
        for k in keys:
            if k == primary_key:
                continue
            if runs[k].get("error"):
                extra.append(f"| {k} | run error | {esc(runs[k]['error'])} | | |")
                continue
            for f in runs[k].get("differences", []):
                if (f["what"], f["shadcn"], f["ours"]) not in base:
                    extra.append(f"| {k} | {esc(f['step'])} | {esc(f['what'])} | {esc(f['shadcn'])} | {esc(f['ours'])} ({f['class']}, {f['severity']}) |")
            ours = {(f["what"], f["shadcn"], f["ours"]) for f in runs[k].get("differences", [])}
            gone = [f for f in primary.get("differences", []) if (f["what"], f["shadcn"], f["ours"]) not in ours]
            if gone and runs[k].get("status") != "skip":
                extra.append(f"| {k} | | {len(gone)} differences of {primary_key} do not occur | | |")
        if extra:
            lines += ["Other runs (differences that the run above does not have):", "", "| Run | Step | What | shadcn | ours |", "| --- | --- | --- | --- | --- |"] + extra + [""]
    path = out / "behavior-report.md"
    path.write_text("\n".join(lines) + "\n")
    print(path)
    return 0


def main():
    ap = argparse.ArgumentParser(prog="tools/behavior", description="Behavior parity with ui.shadcn.com: record references from the live site, or build a report from a test run")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="record test/behavior/golden/<component>.json from the live shadcn pages (needs the network)")
    r.add_argument("--only", default="", help="comma-separated scenario names")
    r.add_argument("--engines", default="chromium,firefox,webkit")
    r.add_argument("--widths", default="1280,390")
    r.add_argument("--reduced-motion", action="store_true")
    r.add_argument("--check", action="store_true", help="record each run twice and keep it only when both agree")
    r.add_argument("--verbose", action="store_true")
    p = sub.add_parser("report", help="write <dir>/behavior-report.md from the results of test/run.py --only behavior --out <dir>")
    p.add_argument("dir")
    g = sub.add_parser("gate", help="run the behavior module with test/run.py --jobs (one process per engine), then write the report")
    g.add_argument("--base-url", required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--engines", default="chromium,firefox,webkit")
    g.add_argument("--widths", default="1280,390")
    g.add_argument("--quick", action="store_true", help="Chromium and WebKit at 1280 only")
    g.add_argument("-k", default="", help="regex on check names, as in test/run.py")
    g.add_argument("--queue", default="", help="script that runs test/run.py in a shared queue (also BEHAVIOR_QUEUE)")
    sub.add_parser("stamp", help="write the live deploy id and the @base-ui/react version into reference files that have none (needs the network)")
    sub.add_parser("status", help="list references to record again: changed scenario, pin, @base-ui/react on shadcn main, or live deploy (needs the network)")
    args = ap.parse_args()
    return {"record": record, "report": report, "gate": gate, "stamp": stamp, "status": status}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
