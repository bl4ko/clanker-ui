import sys

sys.dont_write_bytecode = True

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
PIN = HERE / "refapp"
SITE = "https://ui.shadcn.com"
STYLES = ["nova", "vega", "maia", "lyra", "mira", "luma", "sera", "rhea"]
EXAMPLES = "apps/v4/registry/bases/base/examples/"
UI = "apps/v4/registry/bases/base/ui/"
WRAPPER = "apps/v4/registry/bases/base/components/example.tsx"
HELPERS = {"apps/v4/lib/ai.ts": "src/lib/ai.ts", "apps/v4/components/message-parts.tsx": "src/components/message-parts.tsx"}
IMPORT = re.compile(r'(?:\bfrom|^import)\s+"([^".][^"]*)"', re.M)
SHIMMED = {"next"}
STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"|`[^`]*`')
SHIMS = {
    "next-image.tsx": 'import * as React from "react"\n\nexport default function Image({ src, fill, priority, quality, placeholder, blurDataURL, unoptimized, loader, style, ...props }: any) {\n  return <img {...props} src={typeof src === "string" ? src : src?.src} loading={priority ? undefined : "lazy"} decoding="async" data-nimg={fill ? "fill" : "1"} style={{ color: "transparent", ...(fill ? { position: "absolute", height: "100%", width: "100%", inset: 0 } : {}), ...style }} />\n}\n',
    "next-link.tsx": 'import * as React from "react"\n\nexport default function Link({ href, prefetch, replace, scroll, shallow, locale, ...props }: any) {\n  return <a href={typeof href === "string" ? href : href?.pathname} {...props} />\n}\n',
}


def log(*a):
    print(*a, flush=True)


def run(cmd, cwd, env=None, check=True):
    log("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True)
    if check and r.returncode != 0:
        raise SystemExit(f"{' '.join(cmd)}: exit {r.returncode}\n{r.stdout[-4000:]}\n{r.stderr[-4000:]}")
    return r


def blob_sha1(b):
    return hashlib.sha1(b"blob %d\x00" % len(b) + b).hexdigest()


def pinned_examples(src, pin):
    tree = json.loads((src / "tree.json").read_text())["tree"]
    files = {t["path"]: t["sha"] for t in tree if t["path"].startswith(EXAMPLES) and t["path"].endswith("-example.tsx") and t["path"].count("/") == EXAMPLES.count("/") or t["path"] == WRAPPER}
    cache = src / "parity-examples"
    cache.mkdir(exist_ok=True)
    out = {}
    for path, sha in sorted(files.items()):
        dest = cache / ("registry-" + path.rsplit("/", 1)[1])
        if not dest.exists() or blob_sha1(dest.read_bytes()) != sha:
            subprocess.run(["curl", "-sSfL", "--proto", "=https", "--max-time", "60", "-o", str(dest), f"https://raw.githubusercontent.com/shadcn-ui/ui/{pin}/{path}"], check=True)
        if blob_sha1(dest.read_bytes()) != sha:
            raise SystemExit(f"{path}: git blob {blob_sha1(dest.read_bytes())}, tree {sha}")
        out[path.rsplit("/", 1)[1][:-4]] = dest
    return out


def raw(pin, path, dest):
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sSfL", "--proto", "=https", "--max-time", "120", "-o", str(dest), f"https://raw.githubusercontent.com/shadcn-ui/ui/{pin}/{path}"], check=True)
    return dest


def pin_versions(src, pin):
    lines = raw(pin, "pnpm-lock.yaml", src / "refapp-pin" / "pnpm-lock.yaml").read_text().splitlines()
    out, inside, name = {}, False, None
    for line in lines:
        if line.startswith("  ") and not line.startswith("   "):
            inside = line.strip() == "apps/v4:"
            continue
        if not inside:
            continue
        if line.startswith("      ") and not line.startswith("       "):
            name = line.strip().rstrip(":").strip("'")
        elif line.strip().startswith("version:") and name:
            v = line.split(":", 1)[1].strip().split("(")[0]
            if v.startswith("link:../../"):
                path = v.removeprefix("link:../../") + "/package.json"
                v = json.loads(raw(pin, path, src / "refapp-pin" / path).read_text())["version"]
            out[name] = v
    return out


def package_of(spec):
    parts = spec.split("/")
    return "/".join(parts[:2]) if spec.startswith("@") else parts[0]


def update_lock(apps, src, pin):
    versions = pin_versions(src, pin)
    app = apps[0]
    pkg = json.loads((app / "package.json").read_text())
    deps, dev = set(), set()
    for a in apps:
        p = json.loads((a / "package.json").read_text())
        deps |= set(p["dependencies"])
        dev |= set(p.get("devDependencies", {}))
        for f in (a / "src").rglob("*.ts*"):
            deps |= {package_of(m) for m in IMPORT.findall(f.read_text()) if not m.startswith(("@/", "node:"))}
    deps -= SHIMMED

    def version(name):
        if name.startswith("@tailwindcss/"):
            return versions["tailwindcss"]
        if name in versions:
            return versions[name]
        for a in apps:
            installed = a / "node_modules" / name / "package.json"
            if installed.exists():
                return json.loads(installed.read_text())["version"]
        return "latest"

    pkg["dependencies"] = {n: version(n) for n in sorted(deps)}
    pkg["devDependencies"] = {n: version(n) for n in sorted(dev)}
    (app / "package.json").write_text(json.dumps(pkg, indent=2) + "\n")
    (app / "pnpm-lock.yaml").unlink(missing_ok=True)
    run(["pnpm", "install"], app)
    pkg = json.loads((app / "package.json").read_text())
    for k in ("dependencies", "devDependencies"):
        pkg[k] = {n: json.loads((app / "node_modules" / n / "package.json").read_text())["version"] for n in pkg[k]}
    PIN.mkdir(exist_ok=True)
    (PIN / "package.json").write_text(json.dumps({"private": True, "dependencies": pkg["dependencies"], "devDependencies": pkg["devDependencies"]}, indent=2) + "\n")
    shutil.copy(app / "pnpm-workspace.yaml", PIN / "pnpm-workspace.yaml")
    (app / "package.json").write_text(json.dumps({**json.loads((app / "package.json").read_text()), **{k: pkg[k] for k in ("dependencies", "devDependencies")}}, indent=2) + "\n")
    run(["pnpm", "install"], app)
    shutil.copy(app / "pnpm-lock.yaml", PIN / "pnpm-lock.yaml")
    log(f"wrote {PIN / 'package.json'} and {PIN / 'pnpm-lock.yaml'}")


def strings(text, style):
    text = re.sub(r"\s+", " ", text.replace("@/registry/bases/base/", f"@/registry/base-{style}/"))
    out = {}
    for s in STRING.findall(text):
        k = " ".join(sorted(s[1:-1].split()))
        if k:
            out[k] = out.get(k, 0) + 1
    return out


def fetch_item(style, name, cache):
    f = cache / f"{name}.json"
    if not f.exists():
        with urllib.request.urlopen(f"{SITE}/r/styles/base-{style}/{name}.json", timeout=60) as r:
            f.write_bytes(r.read())
    return json.loads(f.read_text())


def check_registry(app, style, src, names, examples):
    cache = app / "registry"
    cache.mkdir(exist_ok=True)
    pinned = {n: src / UI / f"{n}.tsx" for n in names}
    pinned |= {n: p for n, p in examples.items()}
    tx = app / "registry-pin"
    shutil.copy(PIN / "transform.mjs", app / "transform.mjs")
    run(["node", "transform.mjs", str(src / f"apps/v4/registry/styles/style-{style}.css"), str(tx), *map(str, pinned.values())], app)
    drift = []
    for name in sorted(pinned):
        item = fetch_item(style, name, cache)
        files = [f for f in item.get("files", []) if f["path"].endswith(f"/{name}.tsx")]
        if len(files) != 1:
            drift.append(f"{name}: {len(files)} files")
            continue
        if strings((tx / pinned[name].name).read_text(), style) != strings(files[0]["content"], style):
            drift.append(name)
    return {"items": len(pinned), "drift": drift}


def write_shell(app, style, names):
    src = app / "src"
    pages = sorted(names)
    lines = ['import type { ComponentType } from "react"', ""]
    for i, n in enumerate(pages):
        lines.append(f'import P{i} from "@/components/{n}"')
    lines += ["", "export const pages: Record<string, ComponentType> = {"] + [f'  "{n}": P{i},' for i, n in enumerate(pages)] + ["}", ""]
    (src / "pages.tsx").write_text("\n".join(lines))
    (src / "main.tsx").write_text(
        'import { StrictMode } from "react"\nimport { createRoot } from "react-dom/client"\n\nimport "./index.css"\nimport { pages } from "./pages"\n\n'
        'const name = location.pathname.split("/").filter(Boolean).pop() ?? ""\nconst Page = pages[name]\n\n'
        f'document.body.classList.add("style-{style}")\n'
        'createRoot(document.getElementById("root")!).render(\n  <StrictMode>\n    {Page ? <Page /> : <ul>{Object.keys(pages).map((n) => <li key={n}><a href={`/preview/base/${n}`}>{n}</a></li>)}</ul>}\n  </StrictMode>\n)\n'
    )
    for f in ("App.tsx", "App.css"):
        (src / f).unlink(missing_ok=True)
    shims = src / "shims"
    shims.mkdir(exist_ok=True)
    for f, body in SHIMS.items():
        (shims / f).write_text(body)
    css = src / "index.css"
    text = css.read_text()
    variants = "".join(f"@custom-variant style-{s} (&:where(.style-{s} *));\n" for s in STYLES)
    if "@custom-variant style-" not in text:
        text = text.replace("@custom-variant dark", '@source "../node_modules/streamdown/dist/*.js";\n' + variants + "@custom-variant dark", 1)
        css.write_text(text)
    vite = app / "vite.config.ts"
    v = vite.read_text()
    if "next/image" not in v:
        v = v.replace('"@": resolve(import.meta.dirname, "./src"),', '"next/image": resolve(import.meta.dirname, "./src/shims/next-image.tsx"),\n      "next/link": resolve(import.meta.dirname, "./src/shims/next-link.tsx"),\n      "@": resolve(import.meta.dirname, "./src"),')
        vite.write_text(v)


def pin_packages(app):
    pkg = json.loads((app / "package.json").read_text())
    want = json.loads((PIN / "package.json").read_text())
    for k in ("dependencies", "devDependencies"):
        pkg[k] = want[k]
    (app / "package.json").write_text(json.dumps(pkg, indent=2) + "\n")
    shutil.copy(PIN / "pnpm-lock.yaml", app / "pnpm-lock.yaml")
    shutil.copy(PIN / "pnpm-workspace.yaml", app / "pnpm-workspace.yaml")


def build(style, args, src, pin, examples):
    out = pathlib.Path(args.out)
    app = out / style
    if app.exists():
        shutil.rmtree(app)
    env = dict(os.environ)
    cli = pin_versions(src, pin)["shadcn"]
    run(["pnpm", "dlx", f"shadcn@{cli}", "init", "-t", "vite", "-b", "base", "-p", style, "-n", style, "--no-monorepo", "--no-rtl", "-y"], out, env)
    cfg = json.loads((app / "components.json").read_text())
    if cfg.get("style") != f"base-{style}":
        raise SystemExit(f"{style}: components.json style {cfg.get('style')}")
    names = sorted(p.stem for p in (src / UI).glob("*.tsx"))
    items = names + sorted(examples)
    run(["pnpm", "exec", "shadcn", "add", "-y", "-o", *items], app, env)
    reg = check_registry(app, style, src, names, examples)
    if reg["drift"] and not args.allow_drift:
        raise SystemExit(f"{style}: the live registry differs from the shadcn pin {pin} for {', '.join(reg['drift'])} (--allow-drift to build anyway)")
    write_shell(app, style, [n for n, f in examples.items() if "export default" in f.read_text()])
    for path, dest in HELPERS.items():
        shutil.copy(raw(pin, path, src / "refapp-pin" / path), app / dest)
    if args.update_lock:
        return app
    pin_packages(app)
    run(["pnpm", "install", "--frozen-lockfile"], app, env)
    run(["pnpm", "exec", "vite", "build"], app, env)
    lock = (app / "pnpm-lock.yaml").read_text()
    manifest = {"style": style, "shadcn": pin, "cli": cli, "registry": reg, "date": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                "lock": hashlib.sha256(lock.encode()).hexdigest()[:16], "examples": sorted(examples)}
    (app / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    log(f"{style}: {len(examples) - 1} example pages, registry drift {len(reg['drift'])}, {app / 'dist'}")
    return app


def main():
    ap = argparse.ArgumentParser(description="Build the parity reference apps: a real shadcn install (Vite, Base UI) per style that renders the pinned example pages (needs the network)")
    ap.add_argument("--src", default=os.environ.get("SHADCN_SRC"), help="pinned shadcn inputs (go run ./tools/gen fetch)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--styles", default="nova")
    ap.add_argument("--allow-drift", action="store_true", help="build even when a live registry item differs from the pinned source")
    ap.add_argument("--update-lock", action="store_true", help="install and add only, then write refapp/package.json and refapp/pnpm-lock.yaml for all --styles (use all styles)")
    args = ap.parse_args()
    if not args.src:
        raise SystemExit("set --src or SHADCN_SRC")
    src = pathlib.Path(args.src)
    pin = next(l.split("\t")[1] for l in (HERE.parent / "gen/pin.tsv").read_text().splitlines() if l.startswith("commit\t"))
    examples = pinned_examples(src, pin)
    pathlib.Path(args.out).mkdir(parents=True, exist_ok=True)
    apps = []
    for style in args.styles.split(","):
        if style not in STYLES:
            raise SystemExit(f"{style}: not a shadcn style ({', '.join(STYLES)})")
        apps.append(build(style, args, src, pin, examples))
    if args.update_lock:
        update_lock(apps, src, pin)


if __name__ == "__main__":
    main()
