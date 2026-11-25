import sys

sys.dont_write_bytecode = True

import argparse
import http.server
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import threading
import time

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SKILL = ROOT / "skills/clanker-ui"
DESIGN_LINT = SKILL / "references/design-lint.js"
MARKUP_LINT = SKILL / "references/markup-lint.js"
CSP = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', (SKILL / "SKILL.md").read_text())[1]
VIEWS = [(width, height, scheme) for width, height in ((1280, 800), (390, 844)) for scheme in ("light", "dark")]
ARMS = ("skill", "none")
KINDS = ("console", "csp", "design", "markup")
WATCH = 'document.addEventListener("securitypolicyviolation", e => (window.__evalCsp ??= []).push(`${e.violatedDirective} ${e.blockedURI || "inline"}`))'
SETTLE = "() => Promise.race([new Promise(r => setTimeout(r, 3000)), Promise.all(document.getAnimations().filter(a => a.timeline === document.timeline && a.effect?.getTiming().iterations !== Infinity).map(a => a.finished.catch(() => null)))])"
PREAMBLE = f"""You are in an empty project. The web root is `static/`; the UI kit files are in `static/vendor/clanker-ui/`.
Write `static/index.html`, `static/app.css`, and `static/app.js`. There is no build step and no network.
The server sends this Content-Security-Policy header: {CSP}
Do not ask questions. Finish the task.

"""


def kit_files():
    files = {f.name: f for d in (ROOT / "kit", ROOT / "kit/dist") for f in d.glob("clanker-ui*.*") if f.suffix in (".css", ".js")}
    if not any(name.endswith(".min.js") for name in files):
        sys.exit("kit/dist is empty: run go run ./tools/gen build")
    return files


def handler(root, kit):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def translate_path(self, path):
            local = super().translate_path(path)
            name = path.split("?")[0].removeprefix("/vendor/clanker-ui/")
            if not pathlib.Path(local).exists() and name in kit:
                return str(kit[name])
            return local

        def end_headers(self):
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def log_message(self, *args):
            pass

    return Handler


def score(root, browser, kit):
    root = pathlib.Path(root)
    result = {"dir": str(root), "missing": not (root / "index.html").is_file(), "views": []}
    if result["missing"]:
        result["errors"] = None
        return result
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler(root, kit))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        for width, height, scheme in VIEWS:
            context = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme)
            context.add_init_script(WATCH)
            context.add_init_script(path=str(DESIGN_LINT))
            if MARKUP_LINT.exists():
                context.add_init_script(path=str(MARKUP_LINT))
            page = context.new_page()
            console = []
            page.on("console", lambda m, out=console: m.type == "error" and "Content Security Policy" not in m.text and out.append(m.text))
            page.on("pageerror", lambda e, out=console: out.append(str(e)))
            page.goto(f"http://127.0.0.1:{server.server_port}/", wait_until="networkidle")
            page.evaluate(SETTLE)
            found = {
                "console": console,
                "csp": page.evaluate("() => window.__evalCsp ?? []"),
                "design": page.evaluate("() => clankerDesignLint().findings.filter(f => f.severity === 'error').map(f => `${f.rule} ${f.selector}`)"),
                "markup": page.evaluate("() => typeof clankerMarkupLint === 'function' ? clankerMarkupLint().findings.filter(f => f.severity === 'error').map(f => `${f.rule} ${f.selector}`) : []"),
            }
            result["views"].append({"width": width, "scheme": scheme, **found})
            context.close()
    finally:
        server.shutdown()
    result["counts"] = {k: sum(len(v[k]) for v in result["views"]) for k in KINDS}
    result["errors"] = sum(result["counts"].values())
    return result


def score_dirs(dirs):
    kit = kit_files()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            return [score(d, browser, kit) for d in dirs]
        finally:
            browser.close()


def run_agent(task, arm, n, out, kit, args):
    work = out / f"{task.stem}-{arm}-{n}"
    vendor = work / "static/vendor/clanker-ui"
    vendor.mkdir(parents=True)
    for name, f in kit.items():
        shutil.copyfile(f, vendor / name)
    if arm == "skill":
        shutil.copytree(SKILL, work / ".claude/skills/clanker-ui")
    cmd = ["claude", "-p", "--output-format", "json", "--permission-mode", "acceptEdits", "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash",
           "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence"]
    if arm == "none":
        cmd.append("--disable-slash-commands")
    if args.model:
        cmd += ["--model", args.model]
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=work, input=PREAMBLE + task.read_text(), capture_output=True, text=True, timeout=args.timeout)
        code, stdout = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as e:
        code, stdout = "timeout", e.stdout or ""
    (work / "claude.json").write_text(stdout if isinstance(stdout, str) else stdout.decode())
    try:
        meta = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        meta = {}
    return {"task": task.stem, "arm": arm, "run": n, "exit": code, "seconds": round(time.monotonic() - started), "cost": meta.get("total_cost_usd"), "turns": meta.get("num_turns"), "dir": str(work / "static")}


def table(rows):
    lines = ["| Task | Arm | Run | Errors | Console | CSP | Design | Markup |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        s = r["score"]
        c = s.get("counts") or dict.fromkeys(KINDS, "-")
        lines.append(f"| {r.get('task', s['dir'])} | {r.get('arm', '')} | {r.get('run', '')} | {'missing' if s['missing'] else s['errors']} | {c['console']} | {c['csp']} | {c['design']} | {c['markup']} |")
    return "\n".join(lines)


def cmd_run(args):
    out = pathlib.Path(args.out or tempfile.mkdtemp(prefix="clanker-eval-")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    kit = kit_files()
    tasks = sorted((HERE / "tasks").glob("*.md"))
    if args.tasks:
        tasks = [t for t in tasks if t.stem in args.tasks.split(",")]
    rows = [run_agent(t, arm, n, out, kit, args) for t in tasks for arm in args.arms.split(",") for n in range(1, args.runs + 1)]
    for row, s in zip(rows, score_dirs([r["dir"] for r in rows])):
        row["score"] = s
    (out / "report.json").write_text(json.dumps(rows, indent=2))
    (out / "report.md").write_text(table(rows) + "\n")
    print(table(rows))
    print(f"\nreport: {out / 'report.json'}")


def cmd_score(args):
    rows = [{"score": s} for s in score_dirs(args.dirs)]
    print(json.dumps([r["score"] for r in rows], indent=2) if args.json else table(rows))


def cmd_selftest(_):
    good, bad = score_dirs([HERE / "fixtures/good", HERE / "fixtures/bad"])
    want = ["console", "csp", "design"] + (["markup"] if MARKUP_LINT.exists() else [])
    checks = [("good fixture has 0 errors", good["errors"] == 0, good.get("counts"))]
    checks += [(f"bad fixture has {k} errors in every view", all(v[k] for v in bad["views"]), bad.get("counts")) for k in want]
    for name, ok, counts in checks:
        print(("ok   " if ok else "FAIL ") + name + ("" if ok else f" {counts}"))
    if not all(ok for _, ok, _ in checks):
        print(json.dumps([good, bad], indent=2))
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(prog="tools/eval", description="Agent eval of the clanker-ui skill: run tasks with and without the skill, then score the pages.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="run the agent arms and score them (spends model quota)")
    run.add_argument("--tasks", help="comma-separated task names (tasks/<name>.md); default all")
    run.add_argument("--arms", default=",".join(ARMS))
    run.add_argument("--runs", type=int, default=2)
    run.add_argument("--model")
    run.add_argument("--timeout", type=int, default=1800, help="seconds per agent run")
    run.add_argument("--out", help="output directory; default a new temporary directory")
    run.set_defaults(fn=cmd_run)
    sc = sub.add_parser("score", help="score web roots (directories with index.html)")
    sc.add_argument("dirs", nargs="+")
    sc.add_argument("--json", action="store_true")
    sc.set_defaults(fn=cmd_score)
    sub.add_parser("selftest", help="prove the scorer separates the good and the bad fixture").set_defaults(fn=cmd_selftest)
    args = ap.parse_args()
    args.fn(args)


main()
