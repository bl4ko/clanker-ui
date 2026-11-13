import sys

sys.dont_write_bytecode = True

import argparse
import datetime
import hashlib
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


def drift_sig(f):
    num = (lambda s: re.sub(r"-?\d+(\.\d+)?", "#", str(s))) if f["class"] in ("timing", "geometry") else str
    return "|".join([str(E.step_no(f)), f["what"], f["class"], num(f["shadcn"]), num(f["ours"])])


def drift_try(browser, engine, sc, width, ref):
    try:
        run = record_one(browser, engine, sc, width, False, {})
    except Exception as e:
        return {"error": "".join(traceback.format_exception_only(e)).strip().splitlines()[0]}
    if (ref.get("clock"), ref.get("dates")) != (run.get("clock"), run.get("dates")):
        return {"dated": f"the live page shows other dates ({ref.get('dates')} recorded, {run.get('dates')} now): a new build day; record again to compare", "deploy": run.get("deploy")}
    busy = starved(run)
    found = [f for f in E.compare(sc, ref["rows"], run["rows"], engine) if E.failing(f) and not react_noise(sc, f) and not (busy and f["class"] == "timing")]
    return {"found": found, "busy": busy, "deploy": run.get("deploy")}


def drift_run(browser, engine, sc, width, ref):
    tries = [drift_try(browser, engine, sc, width, ref)]
    if tries[0].get("dated"):
        return {"tries": 1, "deploy": tries[0]["deploy"], "status": "stale", "reason": tries[0]["dated"], "differences": [], "unconfirmed": []}
    if tries[0].get("error") or tries[0]["found"] or tries[0]["busy"]:
        tries.append(drift_try(browser, engine, sc, width, ref))
    ok = [t for t in tries if not t.get("error")]
    out = {"tries": len(tries), "deploy": next((t["deploy"] for t in ok if t.get("deploy")), None)}
    if not ok:
        out["error"] = tries[-1]["error"]
        out["differences"] = [dict(E.diff("-", "run", "ok", tries[-1]["error"], "state", "broken", "the scenario could not run on the live page in any try"), sig="run")]
        out["unconfirmed"] = []
        out["status"] = "drift"
        return out
    sigs = [{drift_sig(f) for f in t["found"]} for t in ok]
    both = set.intersection(*sigs) if len(ok) == len(tries) else set()
    out["differences"] = [dict(f, sig=drift_sig(f)) for f in ok[0]["found"] if drift_sig(f) in both]
    seen = set(both)
    out["unconfirmed"] = []
    for t in ok:
        for f in t["found"]:
            s = drift_sig(f)
            if s not in seen:
                seen.add(s)
                out["unconfirmed"].append(dict(f, sig=s))
    out["busy"] = sorted({b for t in ok for b in t["busy"]})
    if len(ok) < len(tries):
        out["error"] = next(t["error"] for t in tries if t.get("error"))
    out["status"] = "drift" if out["differences"] else "noise" if out["unconfirmed"] or out.get("error") else "same"
    return out


def drift_table(diffs):
    rows = ["| Step | What | recorded | live now | Class | Severity |", "| --- | --- | --- | --- | --- | --- |"]
    for f in diffs:
        what = f["what"] + (f" (also steps {', '.join(f['also'][:8])})" if f.get("also") else "")
        note = f"<br>{esc(f['note'])}" if f.get("note") else ""
        rows.append(f"| {esc(f['step'])} | {esc(what)}{note} | {esc(f['shadcn'])} | {esc(f['ours'])} | {f['class']} | {f['severity']} |")
    return rows


def drift_section(c):
    name = c["component"]
    lines = [f"Live page: {c['url']}", f"Recorded {c['golden']['recorded']} on deploy {', '.join(c['golden']['deploy'] or ['?'])} (`@base-ui/react` {c['golden']['base_ui']}); live deploy {c.get('deploy') or '?'}.", ""]
    for key, r in c["runs"].items():
        if r["status"] != "drift":
            continue
        lines += [f"#### {key}", ""] + drift_table(r["differences"]) + [""]
    lines += [
        "Scenario: `test/behavior/scenarios/%s.json` (step numbers count from 1; 0 is the page at rest). Reference: `test/behavior/golden/%s.json`." % (name, name),
        "",
        "Next steps: open the live page and run the scenario steps by hand to confirm the change. A real upstream change: `tools/behavior record --only %s`, then `tools/behavior gate`, then port the change to the kit in one pull request. A false difference: fix the scenario or `tools/behavior`." % name,
    ]
    return lines


def drift_merge(out, dirs):
    (out / "components").mkdir(parents=True, exist_ok=True)
    slices = []
    for d in map(pathlib.Path, dirs):
        if not (d / "slices.json").exists():
            continue
        slices += json.loads((d / "slices.json").read_text())
        for f in sorted((d / "components").glob("*.json")):
            c = json.loads(f.read_text())
            dst = out / "components" / f.name
            if dst.exists():
                old = json.loads(dst.read_text())
                c["runs"] = {**old["runs"], **c["runs"]}
                c["deploy"] = c.get("deploy") or old.get("deploy")
                if old.get("skip") and not c.get("skip"):
                    c["skip"] = old["skip"]
            dst.write_text(json.dumps(c, indent=1, ensure_ascii=False) + "\n")
    if not slices:
        print(f"no drift results in {', '.join(dirs)}")
        return 2
    (out / "slices.json").write_text(json.dumps(slices, indent=1) + "\n")
    return drift_write(out)


def drift(args):
    if args.merge:
        return drift_merge(pathlib.Path(args.out), args.merge)
    names = [n for n in args.only.split(",") if n] or E.scenario_names()
    engines = [e for e in args.engines.split(",") if e]
    widths = [int(w) for w in args.widths.split(",") if w]
    out = pathlib.Path(args.out)
    (out / "components").mkdir(parents=True, exist_ok=True)
    started = time.time()
    with sync_playwright() as pw:
        deploy = live_deploy(pw)
        if not deploy:
            print(f"no deploy id from {E.SITE}: the live site did not answer; no report")
            return 2
        base_ui = base_ui_version(pw, "main")
        comps = {}
        for name in names:
            sc = E.load_scenario(name)
            gold = E.load_golden(name)
            path = out / "components" / f"{name}.json"
            c = comps[name] = {"component": name, "url": sc.get("url") or f"{E.SITE}/docs/components/base/{sc.get('page', name)}", "runs": json.loads(path.read_text())["runs"] if path.exists() else {}}
            if sc.get("not_recorded") or not gold:
                c["skip"] = sc.get("not_recorded") or "no reference"
                continue
            c["golden"] = {k: gold.get(k) for k in ("recorded", "deploy", "base_ui", "shadcn_pin")}
            if gold.get("scenario") != E.scenario_hash(sc):
                c["skip"] = "stale: the scenario changed after the record; record it again"
        for engine in engines:
            browser = launch(pw, engine)
            for name in names:
                c = comps[name]
                if c.get("skip"):
                    continue
                sc = E.load_scenario(name)
                sc["allowed"] = [a for a in sc.get("allowed", []) if "platforms" in a]
                gold = E.load_golden(name)
                for width in widths:
                    key = E.run_key(engine, width)
                    if key not in gold["runs"]:
                        continue
                    t = time.time()
                    r = c["runs"][key] = drift_run(browser, engine, sc, width, gold["runs"][key])
                    c["deploy"] = r.get("deploy") or c.get("deploy")
                    print(f"[{key}] {name}: {r['status']}" + (f", {len(r['differences'])} differences" if r["differences"] else "") + (f", {len(r['unconfirmed'])} unconfirmed" if r["unconfirmed"] else "") + (f", error {r['error']}" if r.get("error") else "") + f" ({r['tries']} tries, {time.time() - t:.0f}s)", flush=True)
                (out / "components" / f"{name}.json").write_text(json.dumps(c, indent=1, ensure_ascii=False) + "\n")
            browser.close()
    for c in comps.values():
        if c.get("skip"):
            (out / "components" / f"{c['component']}.json").write_text(json.dumps(c, indent=1, ensure_ascii=False) + "\n")
    slices = out / "slices.json"
    done = json.loads(slices.read_text()) if slices.exists() else []
    done.append({"generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "deploy": deploy, "base_ui_main": base_ui, "only": names if args.only else "all", "engines": engines, "widths": widths, "seconds": round(time.time() - started)})
    slices.write_text(json.dumps(done, indent=1) + "\n")
    return drift_write(out)


def drift_write(out):
    slices = json.loads((out / "slices.json").read_text())
    comps = {f.stem: json.loads(f.read_text()) for f in sorted((out / "components").glob("*.json"))}
    failed = [r for c in comps.values() for r in c["runs"].values() if r["status"] == "drift" and r["differences"][0]["sig"] == "run"]
    for c in comps.values():
        for r in c["runs"].values():
            if len(failed) > 10 and r in failed:
                r["status"] = "error"
        if c.get("skip"):
            c["status"] = "stale" if c["skip"].startswith("stale") else "skip"
            c["reason"] = c["skip"]
        else:
            st = {r["status"] for r in c["runs"].values()}
            c["status"] = "drift" if "drift" in st else "error" if "error" in st else "stale" if "stale" in st else "noise" if "noise" in st else "same" if st else "skip"
            c["reason"] = next((r["reason"] for r in c["runs"].values() if r.get("reason")), "")
        if c["status"] == "drift":
            sigs = sorted({f["sig"] for r in c["runs"].values() for f in r["differences"]})
            c["fingerprint"] = hashlib.sha256("\n".join(sigs).encode()).hexdigest()[:12]
            c["title"] = f"behavior drift: {c['component']}"
            c["marker"] = f"<!-- behavior-drift:{c['component']} -->"
            c["body"] = "\n".join([c["marker"], f"<!-- behavior-drift-fingerprint:{c['fingerprint']} -->", "", f"The live shadcn page of `{c['component']}` behaves differently from the committed reference. Each difference below occurred in two records in a row."] + [""] + drift_section(c)) + "\n"
    drifting = sorted(n for n, c in comps.items() if c["status"] == "drift")
    errors = sorted(n for n, c in comps.items() if c["status"] == "error")
    deploys = sorted({x["deploy"] for x in slices})
    keys = sorted({k for c in comps.values() for k in c["runs"]})
    seconds = sum(x["seconds"] for x in slices)
    result = {"generated": slices[-1]["generated"], "site": E.SITE, "deploy": deploys, "base_ui_main": slices[-1]["base_ui_main"], "shadcn_pin": PIN, "runs": keys, "seconds": seconds, "slices": slices, "drift": drifting, "errors": errors, "components": [comps[n] for n in sorted(comps)]}
    (out / "drift.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    lines = ["# Behavior drift of the live shadcn site", "", f"Generated {result['generated']} in {len(slices)} slices ({seconds} s): live `{E.SITE}` (deploy {', '.join(deploys)}, `@base-ui/react` {result['base_ui_main'] or '?'} on shadcn main) against `test/behavior/golden/` (shadcn pin `{PIN}`). Runs: {', '.join(keys)}.", ""]
    lines.append("A run that differs from its reference is recorded a second time. Drift is a broken or visible difference in both records; a difference in one record only is noise and does not fail. The React render time of click and key steps is not compared, and timing is not compared when a CSS animation painted in one frame (a busy page). A run whose live page shows other dates than the record (a new build day) is stale.")
    lines += ["", "| Component | Status | Runs with drift | Unconfirmed | Note |", "| --- | --- | --- | --- | --- |"]
    for n in sorted(comps):
        c = comps[n]
        runs = [k for k, r in c["runs"].items() if r["status"] == "drift"]
        unc = sum(len(r["unconfirmed"]) for r in c["runs"].values())
        lines.append(f"| {n} | {c['status']} | {', '.join(runs)} | {unc or ''} | {esc(c.get('reason', ''))} |")
    lines += ["", f"{len(drifting)} of {len(comps)} components drift; {sum(1 for c in comps.values() if c['status'] == 'stale')} stale." + (f" {len(failed)} runs could not run on the live page in two tries: the site or the network failed, so status `error`, not drift." if len(failed) > 10 else ""), ""]
    for n in drifting:
        lines += [f"## {n}", ""] + drift_section(comps[n]) + [""]
    noisy = [(n, k, r) for n in sorted(comps) for k, r in comps[n]["runs"].items() if r["unconfirmed"] or r.get("error") or r.get("busy")]
    if noisy:
        lines += ["## Noise (not drift)", "", "| Component | Run | Step | What | recorded | live now |", "| --- | --- | --- | --- | --- | --- |"]
        for n, k, r in noisy:
            for f in r["unconfirmed"]:
                lines.append(f"| {n} | {k} | {esc(f['step'])} | {esc(f['what'])} | {esc(f['shadcn'])} | {esc(f['ours'])} |")
            if r.get("error") and r["status"] != "error":
                lines.append(f"| {n} | {k} | - | run error in one try | | {esc(r['error'])} |")
            for b in r.get("busy") or []:
                lines.append(f"| {n} | {k} | - | busy page, timing not compared | | {esc(b)} |")
        lines.append("")
    (out / "drift.md").write_text("\n".join(lines))
    print(f"{out / 'drift.md'}\n{len(drifting)} components drift: {', '.join(drifting) or 'none'}" + (f"; {len(errors)} could not run: {', '.join(errors)}" if errors else "") + f" ({seconds}s in {len(slices)} slices)")
    return 2 if errors else 1 if drifting else 0


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
    d = sub.add_parser("drift", help="record the live pages again and compare them with test/behavior/golden/ without a change to it; write <out>/drift.md and <out>/drift.json; exit 1 on drift (needs the network)")
    d.add_argument("--out", required=True)
    d.add_argument("--only", default="", help="comma-separated scenario names")
    d.add_argument("--engines", default="chromium,firefox,webkit")
    d.add_argument("--widths", default="1280,390")
    d.add_argument("--merge", nargs="+", metavar="DIR", help="record nothing: add the results of other drift directories to --out and write the report")
    sub.add_parser("stamp", help="write the live deploy id and the @base-ui/react version into reference files that have none (needs the network)")
    sub.add_parser("status", help="list references to record again: changed scenario, pin, @base-ui/react on shadcn main, or live deploy (needs the network)")
    args = ap.parse_args()
    return {"record": record, "report": report, "gate": gate, "drift": drift, "stamp": stamp, "status": status}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
