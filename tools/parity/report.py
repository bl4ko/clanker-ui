import sys

sys.dont_write_bytecode = True

import argparse
import json
import pathlib


def short(v):
    s = str(v).replace("rgba(", "(").replace(",1.00)", ")")
    return s if len(s) <= 40 else s[:37] + "..."


def pct(a, b):
    return f"{100 * a / max(b, 1):.1f}"


def prop_counts(path, parts, style="nova"):
    counts = {}
    if not path.exists():
        return counts
    seen = set()
    for r in json.loads(path.read_text()):
        if r.get("style", "nova") != style or r["part"] not in parts:
            continue
        key = (r["part"], r["prop"], r["scenario"], str(r["id"]), r["state"], r["theme"])
        if key in seen:
            continue
        seen.add(key)
        counts[(r["part"], r["prop"])] = counts.get((r["part"], r["prop"]), 0) + 1
    return counts


def cause_keys(path):
    lines = path.read_text().splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "| Key | Cause |"), None)
    if start is None:
        return set()
    keys = set()
    for line in lines[start + 2:]:
        if not line.strip().startswith("|"):
            break
        keys.add(line.strip().strip("|").split("|")[0].strip())
    return keys


def main():
    ap = argparse.ArgumentParser(description="Markdown summary of a tools/parity/parity.py run")
    ap.add_argument("out")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--strict", action="store_true", help="also fail when a (part, property) differs in more pairs than --known allows, a component has no measured part, or a cause key of --known is not in --causes")
    ap.add_argument("--style", default="nova", help="the shadcn style to report (previews in that style, measured against its kit CSS)")
    ap.add_argument("--known", default="", help="reviewed known differences: component<TAB>part<TAB>property<TAB>pairs<TAB>cause (default: known.tsv for nova, known-<style>.tsv for another style)")
    ap.add_argument("--causes", default=str(pathlib.Path(__file__).resolve().parents[2] / "DEVELOPMENT.md"), help="file with the '| Key | Cause |' table of the cause keys that --strict accepts in --known")
    ap.add_argument("--write-known", default="", help="write the differences of this run in the known.tsv format (causes from --known, else 'to check') to this file")
    args = ap.parse_args()
    args.known = args.known or str(pathlib.Path(__file__).with_name("known.tsv" if args.style == "nova" else f"known-{args.style}.tsv"))
    known, bad_causes = {}, []
    kp = pathlib.Path(args.known)
    cp = pathlib.Path(args.causes)
    causes = cause_keys(cp) if args.strict and cp.exists() else set()
    if kp.exists():
        for n, line in enumerate(kp.read_text().splitlines(), 1):
            f = line.split("\t")
            if len(f) == 5 and f[3].isdigit():
                known[(f[0], f[1], f[2])] = (int(f[3]), f[4])
                key = (f[4].split() or [""])[0]
                if args.strict and key not in causes:
                    bad_causes.append(f"{kp.name}:{n}: cause key {key!r} is not in the cause table of {cp.name}")
    seen_known, kept_lines, measured_known = set(), [], []
    out = pathlib.Path(args.out)
    rows, parts_lines = [], []
    tot = dict.fromkeys(("parts", "parts_equal", "pairs", "pairs_equal", "meaningful", "meaningful_equal", "measured", "equal"), 0)
    states = {}
    failures, sites = bad_causes, set()
    other = dict.fromkeys(("parts", "parts_equal", "pairs", "pairs_equal"), 0)
    other_comps, other_lines = [], []
    for f in sorted(out.glob("*.json")):
        if f.name.endswith((".rows.json", ".raw.json", ".pairs.json")) or f.name == "parts.json":
            continue
        s = json.loads(f.read_text())
        if "error" in s:
            rows.append(f"| {s['component']} | failed | | | {s['error'][:80]} |")
            failures.append(f"{s['component']}: {s['error'][:120]}")
            continue
        if args.style != "nova":
            if args.style not in (s.get("styles") or {}):
                continue
            s = {"component": s["component"], "site": s.get("site"), **s["styles"][args.style]}
        for k in tot:
            tot[k] += s.get(k, 0)
        o = s.get("other_style") or {}
        if o.get("pairs"):
            for k in other:
                other[k] += o.get(k, 0)
            other_comps.append(f"{s['component']} ({'+'.join(o['styles'])}: {o['parts_equal']}/{o['parts']} parts; Nova reference: {s.get('nova_page') or 'none'})")
            for d in o.get("differing_parts", []):
                other_lines.append(f"| {s['component']} | {d['part']} | {d['pairs'] - d['equal']}/{d['pairs']} | {', '.join(f'{k} {v}' for k, v in d['props'].items())} |")
        for k, v in s["by_state"].items():
            t = states.setdefault(k, [0, 0])
            t[0] += v[0]
            t[1] += v[1]
        site = s.get("site") or {}
        sites.add(f"{site.get('deployment', '?')} ({site.get('date', '?')[:10]})")
        st = ", ".join(f"{k} {pct(*v)}" for k, v in s["by_state"].items())
        top = "; ".join(f"{t['part']} {t['state']} {t['prop']}: {short(t['shadcn'])} vs {short(t['ours'])} ({t['count']})" for t in s["top"][: args.top])
        rows.append(f"| {s['component']} | {s['parts_equal']}/{s['parts']} | {s['pairs_equal']}/{s['pairs']} ({pct(s['pairs_equal'], s['pairs'])} %) | {pct(s['meaningful_equal'], s['meaningful'])} % | {st} | {top} |")
        for d in s["differing_parts"]:
            states_txt = ", ".join(f"{k} {v}" for k, v in sorted(d["states"].items()))
            props_txt = ", ".join(f"{k} {v}" for k, v in d["props"].items())
            parts_lines.append(f"| {s['component']} | {d['part']} | {d['pairs'] - d['equal']}/{d['pairs']} | {states_txt} | {props_txt} |")
        for slot, toks in sorted((s.get("kept_source") or {}).items()):
            kept_lines.append(f"| {s['component']} | {slot} | {' '.join(toks)} |")
        counts = prop_counts(out / f"{s['component']}.rows.json", {d["part"] for d in s["differing_parts"]}, args.style)
        for (part, prop), n in sorted(counts.items()):
            measured_known.append((s["component"], part, prop, n))
        if args.strict:
            if not s["parts"]:
                failures.append(f"{s['component']}: no measured part")
            worse = []
            for (part, prop), n in sorted(counts.items()):
                seen_known.add((s["component"], part, prop))
                allowed = known.get((s["component"], part, prop), (0, ""))[0]
                if n > allowed:
                    worse.append(f"{part} {prop} {n} pairs (known {allowed})")
            if worse:
                failures.append(f"{s['component']}: {len(worse)} (part, property) entries differ more than {kp.name} allows: {'; '.join(worse)}")
    print(f"Live site: {', '.join(sorted(sites)) or '?'}. Style: {args.style}.\n")
    print(f"Parts with no difference in any state: {tot['parts_equal']}/{tot['parts']} ({pct(tot['parts_equal'], tot['parts'])} %).")
    print(f"(part, state, theme) pairs with no difference: {tot['pairs_equal']}/{tot['pairs']} ({pct(tot['pairs_equal'], tot['pairs'])} %).")
    print(f"Values not at their initial value, equal: {tot['meaningful_equal']}/{tot['meaningful']} ({pct(tot['meaningful_equal'], tot['meaningful'])} %).")
    print(f"All values, equal: {tot['equal']}/{tot['measured']} ({pct(tot['equal'], tot['measured'])} %).")
    print("Pairs by state: " + ", ".join(f"{k} {v[0]}/{v[1]} ({pct(*v)} %)" for k, v in sorted(states.items())) + "\n")
    if other["pairs"] and args.style == "nova":
        print(f"Not in the totals: previews in a shadcn style that the kit does not have, or in another style than the rest of their page (style@measured): parts {other['parts_equal']}/{other['parts']}, pairs {other['pairs_equal']}/{other['pairs']}. Each style has its own report (--style). Pages: {', '.join(other_comps)}.\n")
    print("| Component | Equal parts | Equal pairs | Values | Pairs by state (%) | Top differences (shadcn vs ours, count) |")
    print("| --- | --- | --- | --- | --- | --- |")
    print("\n".join(rows))
    print("\n## Parts that differ\n")
    print("| Component | Part | Differing pairs | States | Properties (pairs) |")
    print("| --- | --- | --- | --- | --- |")
    print("\n".join(parts_lines))
    if other_lines and args.style == "nova":
        print("\n## Parts on previews in another shadcn style (not in the totals)\n")
        print("| Component | Part | Differing pairs | Properties (pairs) |")
        print("| --- | --- | --- | --- |")
        print("\n".join(other_lines))
    if kept_lines:
        print("\n## Kept classes that are also source classes (each is in the example file of its preview)\n")
        print("| Component | Part | Classes |")
        print("| --- | --- | --- |")
        print("\n".join(kept_lines))
    if args.write_known:
        lines = [f"{c}\t{p}\t{prop}\t{n}\t{known.get((c, p, prop), (0, 'to check'))[1]}" for c, p, prop, n in measured_known]
        pathlib.Path(args.write_known).write_text("\n".join(lines) + "\n")
    if args.strict:
        measured = {f.name[:-5] for f in out.glob("*.json")}
        stale = sorted(k for k in known if k not in seen_known and k[0] in measured)
        if stale:
            print(f"\n## Entries in {kp.name} that no longer differ\n")
            print("\n".join(f"- {c} {p} {prop}" for c, p, prop in stale))
    if not rows:
        failures.append(f"no component result in {out}")
    if failures:
        print("\n## Gate failed\n")
        print("\n".join(f"- {x}" for x in failures))
        sys.exit(1)


if __name__ == "__main__":
    main()
