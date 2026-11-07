import sys

sys.dont_write_bytecode = True

import argparse
import collections
import datetime
import hashlib
import html
import json
import math
import os
import pathlib
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SITE = "https://ui.shadcn.com"
LOCAL = "http://parity.invalid"
FONT = "*, *::before, *::after { font-family: Arial, Helvetica, sans-serif !important; }"
PROPS = [
    "display", "position", "top", "right", "bottom", "left", "width", "height", "min-width", "min-height", "max-width", "max-height",
    "padding-top", "padding-right", "padding-bottom", "padding-left", "margin-top", "margin-right", "margin-bottom", "margin-left",
    "border-top-width", "border-right-width", "border-bottom-width", "border-left-width", "border-top-style", "border-bottom-style",
    "border-top-color", "border-right-color", "border-bottom-color", "border-left-color",
    "border-top-left-radius", "border-top-right-radius", "border-bottom-right-radius", "border-bottom-left-radius",
    "background-color", "background-image", "color", "fill", "stroke", "font-size", "font-weight", "font-style", "line-height", "letter-spacing",
    "text-align", "text-transform", "text-decoration-line", "text-underline-offset", "white-space", "text-overflow", "vertical-align",
    "column-gap", "row-gap", "flex-direction", "flex-wrap", "flex-grow", "flex-shrink", "flex-basis", "align-items", "align-self", "justify-content",
    "grid-template-columns", "grid-template-rows", "grid-column-start", "grid-row-start",
    "box-shadow", "opacity", "visibility", "overflow-x", "overflow-y", "z-index", "isolation", "pointer-events", "cursor", "user-select",
    "translate", "transform", "scale", "rotate", "transform-origin", "outline-style", "outline-width", "outline-color", "outline-offset",
    "transition-property", "transition-duration", "animation-name", "animation-duration", "backdrop-filter", "filter",
    "list-style-type", "aspect-ratio", "object-fit", "content", "mask-image", "animation-iteration-count",
]
BACKDROP_PROPS = ["background-color", "backdrop-filter", "animation-name", "animation-duration", "opacity"]
PSEUDOS = ["::before", "::after"]
PSEUDO_PROPS = ["content", "position", "display", "width", "height", "top", "right", "bottom", "left", "background-color", "border-top-width", "border-top-color", "border-top-left-radius", "opacity", "transform", "translate"]
INTERACTIVE = "button, a[href], input, textarea, select, [role=button], [role=tab], [role=menuitem], [role=menuitemcheckbox], [role=menuitemradio], [role=option], [role=checkbox], [role=radio], [role=switch], [role=slider], [role=combobox], [tabindex]"
OPEN = {
    "tooltip": ("hover", '[data-slot="tooltip-trigger"]'),
    "hover-card": ("hover", '[data-slot="hover-card-trigger"]'),
    "context-menu": ("right", '[data-slot="context-menu-trigger"]'),
    "navigation-menu": ("hover", '[data-slot="navigation-menu-trigger"]'),
    "toast": ("click", '[data-slot="button"]'),
    "combobox": ("click", '[data-slot="combobox-trigger"], [data-slot="input-group-control"]'),
}
DEFAULT_OPEN = '[data-slot$="-trigger"]:not([data-slot="tabs-trigger"], [data-slot="sidebar-trigger"]), [aria-haspopup]:not([data-slot$="-sub-trigger"])'
BACKDROPS = {"dialog-overlay": "dialog-content", "alert-dialog-overlay": "alert-dialog-content", "sheet-overlay": "sheet-content", "drawer-overlay": "drawer-viewport"}
JS = (pathlib.Path(__file__).parent / "parity.js").read_text()
GEN = ""
STYLES = ["nova"]
SETTLE = "ms => window.__parity.settle(ms)"
NOVA_PAGE = "/preview/base/"
KIT_CLASSES = {"sr-only"}
STATE_ATTRS = ["disabled", "aria-disabled", "data-disabled", "data-open", "data-closed", "data-state", "data-highlighted", "data-checked", "data-unchecked", "aria-expanded", "aria-selected", "aria-pressed", "data-active", "data-pressed", "data-popup-open", "data-starting-style", "data-ending-style", "data-selected"]
EXCLUDED = {"chart"}


def log(*a):
    print(*a, flush=True)


class Parts:
    def __init__(self, data):
        self.logical = data.get("logical") or {}
        self.groups = data.get("groups") or {}
        self.by_slot = collections.defaultdict(list)
        self.slotless = []
        for p in data["parts"]:
            p["tokens"] = self.canon(p.get("tokens") or [])
            if p.get("own"):
                p["own"] = self.canon(p["own"])
            for v in p.get("variants") or []:
                v["tokens"] = self.canon(v.get("tokens") or [])
            if p.get("slot"):
                self.by_slot[p["slot"]].append(p)
            elif p.get("element_slot"):
                self.by_slot[p["element_slot"]].append({**p, "variants": None})
            elif m := PURE_SLOT.match(p.get("selector") or ""):
                self.by_slot[m.group(1)].append({**p, "variants": None})
                self.slotless.append(p)
            else:
                self.slotless.append(p)
        self.tokens = {s: set().union(*(set(p["tokens"]) for p in ps)) for s, ps in self.by_slot.items()}
        self.free = {}
        self.plain = {}
        self.contextual = collections.defaultdict(list)
        for p in data["parts"]:
            m = CONTEXT_SEL.match(p.get("selector") or "")
            if m:
                self.contextual[m.group(3)].append((m.group(1), bool(m.group(2)), set(self.canon(p.get("tokens") or []))))
        self.contexts = collections.defaultdict(list)
        for sl, ps in self.by_slot.items():
            f = set()
            for p in ps:
                if p.get("context"):
                    self.contexts[sl].append((set(SLOT_REF.findall(p["context"])), set(p["tokens"])))
                elif not p.get("marker") and not p.get("set"):
                    f |= set(p["tokens"])
            self.free[sl] = f
            self.plain[sl] = set().union(*(set(p["tokens"]) for p in ps if not p.get("context") and not p.get("marker") and not p.get("set") and (p.get("slot") or PURE_SLOT.match(p.get("selector") or ""))))
        self.variants = {}
        self.ancestor = collections.defaultdict(list)
        for s, ps in self.by_slot.items():
            vs = collections.defaultdict(dict)
            for p in ps:
                if p.get("marker") or p.get("context"):
                    continue
                for v in p.get("variants") or []:
                    if v.get("owner"):
                        owner = SLOT_REF.findall(v["owner"])
                        if owner and not v.get("default"):
                            self.ancestor[s].append((owner[0], v["attr"], v["value"], set(v.get("tokens") or [])))
                        continue
                    t = vs[v["attr"]].setdefault(v["value"], [set(), v.get("default", False)])
                    t[0].update(v.get("tokens") or [])
            self.variants[s] = vs
        self.base = {}
        for sl, ps in self.by_slot.items():
            b = set()
            for p in ps:
                if p.get("marker") or p.get("context") or p.get("element_slot"):
                    continue
                vt = set().union(*(set(v.get("tokens") or []) for v in p.get("variants") or []))
                b |= set(p["tokens"]) - vt
            self.base[sl] = b
        self.markers = collections.defaultdict(list)
        self.marker_all = {p["marker"]: set(p["tokens"]) for p in data["parts"] if p.get("marker")}
        for s, ps in self.by_slot.items():
            for p in ps:
                if (p.get("marker") or p.get("set")) and p.get("own"):
                    distinct = set(p["own"]) - self.free.get(s, set())
                    self.markers[s].append((p.get("marker"), distinct or set(p["own"]), p.get("set") or {}))
        for p in self.slotless:
            p["set"] = set(p["tokens"])
            p["component"] = p["from"].split("/")[0]
        self.source = {c: set(ts) for c, ts in (data.get("source_tokens") or {}).items()}
        self.slot_markers = collections.defaultdict(set)
        for p in data["parts"]:
            m = PURE_SLOT.match(p.get("selector") or "")
            for sl in {p.get("slot"), p.get("element_slot"), m and m.group(1)} - {None, ""}:
                self.slot_markers[sl] |= set(p.get("markers") or [])
        self.func_slots = collections.defaultdict(set)
        for p in data["parts"]:
            if p.get("from", "").count("/") != 1:
                continue
            m = PURE_SLOT.match(p.get("selector") or "")
            for sl in (p.get("slot"), p.get("element_slot"), m and m.group(1)):
                if sl:
                    self.func_slots[p["from"].split("/")[1]].add(sl)
        self.alias = {}
        for p in data["parts"]:
            sel = p.get("selector") or ""
            if p.get("slot") and sel.startswith(":is("):
                for other in SLOT_REF.findall(sel):
                    if other != p["slot"]:
                        self.alias[other] = p["slot"]

    def uses_marker(self, slot, marker):
        return marker in self.slot_markers.get(slot, set())

    def canon(self, toks):
        return list(dict.fromkeys(self.logical.get(t, t) for t in toks))

    def source_of(self, comps):
        return set().union(*(self.source.get(c, set()) for c in comps)) if comps else set()


def composed(cls, parts, slot, names=(), parent=None, ancestors=()):
    for t in cls.split():
        host = t.removeprefix("cn-")
        if t.startswith("cn-") and host in parts.tokens and host != slot and component_of(host, names) not in ("", component_of(slot, names)) and not parts.uses_marker(slot, t):
            return host
    toks = set(parts.canon(cls.split())) - {t for t in cls.split() if t.startswith("lucide")}
    if len(toks) < 6:
        return None
    own = [parts.plain.get(slot, set())] + [t for ctx, child, t in parts.contextual.get(slot, []) if (ctx == parent if child else ctx in ancestors)]
    mine = max(len(o & toks) for o in own) / len(toks)
    if mine >= 0.5:
        return None
    best = None
    for other, own in parts.tokens.items():
        base = parts.base.get(other) or set()
        if other == slot or not own or len(base) < 6:
            continue
        score = len(own & toks) / len(toks)
        cover = len(base & toks) / len(base)
        if score >= 0.7 and cover >= 0.6 and score > mine + 0.1 and (best is None or score * cover > best[0]):
            best = (score * cover, other)
    return best and best[1]


def infer_attrs(cls, parts, slot, owners, page=None):
    toks = cls.split()
    attrs, hits = {}, []
    tokset = set(parts.canon(toks))
    if slot and slot in parts.tokens:
        found = {}
        for attr, values in parts.variants.get(slot, {}).items():
            marked = [v for v in values if any(t.startswith("cn-") and t.endswith(f"-{attr.removeprefix('data-')}-{v}") for t in toks)]
            if marked:
                found[attr] = marked[0]
                if not values[marked[0]][1]:
                    attrs[attr] = marked[0]
                continue
            best = None
            for value, (vt, is_default) in values.items():
                if not vt:
                    continue
                score = len(vt & tokset) / len(vt)
                key = (score, len(vt & tokset), not is_default)
                if score >= 0.6 and (best is None or key > best[0]):
                    best = (key, value, is_default)
            if best:
                found[attr] = best[1]
                if not best[2]:
                    attrs[attr] = best[1]
        for marker, mt, fixed in parts.markers.get(slot, []):
            if mt and len(mt & tokset) / len(mt) >= 0.6:
                if marker:
                    attrs[marker] = ""
                for k, v in fixed.items():
                    attrs.setdefault(k, found.get(k, v))
        return attrs, hits
    for p in parts.slotless:
        if not p["set"] or p["component"] not in owners and p["component"] != page:
            continue
        n = len(p["set"] & tokset)
        full = n == len(p["set"])
        if p["component"] not in owners and (not full or len(p["set"]) < 3):
            continue
        if n and (full or n / len(p["set"]) >= 0.6 and len(p["set"]) > 2):
            hits.append(p["from"])
            if m := PURE_SLOT.match(p.get("selector") or ""):
                attrs["data-slot"] = m.group(1)
    return attrs, hits


CLASS_ATTR = re.compile(r"\b(?:class(?:Name|Names)?|[a-z]\w*ClassNames?)\s*=\s*")
JSX_OPEN = re.compile(r"<([A-Za-z][\w.]*)")
SLOT_ATTR = re.compile(r'\bdata-slot\s*=\s*"([a-z0-9-]+)"')
RENDER_ATTR = re.compile(r"\brender\s*=\s*")
STRING_LIT = re.compile(r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'|`[^`]*`')


def brace_end(src, i):
    depth = 0
    j = i
    while j < len(src):
        c = src[j]
        if c in "\"'`":
            k = src.find(c, j + 1)
            if k < 0:
                return len(src)
            j = k
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return len(src)


CONST_STR = re.compile(r'\bconst\s+([A-Za-z_]\w*)\s*=\s*("(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'|`[^`]*`)\s*(?:;|\n|$)')
IDENT = re.compile(r"\b[A-Za-z_]\w*\b")


def literal_tokens(lit):
    return [t for t in lit[1:-1].split() if "${" not in t and "}" not in t]


def attr_tokens(code, i, consts):
    if i >= len(code):
        return []
    if code[i] in "\"'":
        j = code.find(code[i], i + 1)
        return code[i + 1:j].split() if j > 0 else []
    if code[i] != "{":
        return []
    expr = code[i:brace_end(code, i)]
    toks = [t for lit in STRING_LIT.findall(expr) for t in literal_tokens(lit)]
    for name in IDENT.findall(STRING_LIT.sub(" ", expr)):
        if name in consts:
            toks += literal_tokens(consts[name])
    return toks


def string_consts(code):
    return {m[1]: m[2] for m in CONST_STR.finditer(code)}


def example_sets(codes):
    out = set()
    for code in codes:
        consts = string_consts(code)
        for m in CLASS_ATTR.finditer(code):
            toks = attr_tokens(code, m.end(), consts)
            if toks:
                out.add(frozenset(toks))
    return sorted(out, key=lambda s: sorted(s))


def class_values(code, consts, depths=None, inner=None):
    out = []
    for m in CLASS_ATTR.finditer(code):
        if depths is not None and depths[m.start()]:
            continue
        if inner is not None and (m.group(0).split("=")[0].strip() != "className") != inner:
            continue
        toks = attr_tokens(code, m.end(), consts)
        if toks:
            out.append(frozenset(toks))
    return out


def brace_depths(text):
    depths, depth, i = [0] * (len(text) + 1), 0, 0
    while i < len(text):
        c = text[i]
        depths[i] = depth
        if c in "\"'`" and depth == 0:
            k = text.find(c, i + 1)
            k = len(text) - 1 if k < 0 else k
            for x in range(i, k + 1):
                depths[x] = depth
            i = k
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    return depths


def jsx_elements(code, consts=None):
    out = []
    consts = string_consts(code) if consts is None else consts
    for m in JSX_OPEN.finditer(code):
        i = m.start()
        if i > 0 and (code[i - 1].isalnum() or code[i - 1] in "_$)]"):
            continue
        j, end = m.end(), None
        while j < len(code):
            c = code[j]
            if c in "\"'`":
                k = code.find(c, j + 1)
                j = len(code) if k < 0 else k
            elif c == "{":
                j = brace_end(code, j) - 1
            elif c == ">":
                end = j
                break
            elif c == "<":
                break
            j += 1
        if end is None:
            continue
        attrs = code[m.end():end]
        depths = brace_depths(attrs)
        slot = next((sm.group(1) for sm in SLOT_ATTR.finditer(attrs) if not depths[sm.start()]), None)
        sets = class_values(attrs, consts, depths, False)
        inner_sets = class_values(attrs, consts, depths, True)
        for rm in RENDER_ATTR.finditer(attrs):
            if not depths[rm.start()] and rm.end() < len(attrs) and attrs[rm.end()] == "{":
                inner = attrs[rm.end() + 1:brace_end(attrs, rm.end()) - 1]
                first = next(iter(jsx_elements(inner, consts)), None)
                if first:
                    sets += first[2]
        out.append((m.group(1).split(".")[-1], slot, sets, inner_sets))
    return out


def example_suffix(toks, sets):
    best = (0, 0, 0)
    for s in sets:
        start = 0
        for i in range(len(toks) + 1):
            if i < len(toks) and toks[i] in s:
                continue
            if i - start > 0:
                best = max(best, (i - start, i == len(toks), -start))
            start = i + 1
    n, _, start = best
    return toks[-start:-start + n] if n else []


SLOT_REF = re.compile(r'\[data-slot="([a-z0-9-]+)"\]')
CONTEXT_SEL = re.compile(r'^:where\(\[data-slot="([a-z0-9-]+)"\]\) (> )?\[data-slot="([a-z0-9-]+)"\]$')
PURE_SLOT = re.compile(r'^\[data-slot="([a-z0-9-]+)"\]$')
RDP_PART = re.compile(r"^rdp-([a-z_]+)$")
RDP_MODIFIERS = {"today", "outside", "disabled", "hidden", "selected", "range_start", "range_middle", "range_end", "focused"}


def component_of(slot, names):
    best = ""
    for n in names:
        if (slot == n or slot.startswith(n + "-")) and len(n) > len(best):
            best = n
    return best


class Converter:
    def __init__(self, parts, names, comp, examples=(), fallback=True):
        self.parts, self.names, self.comp = parts, names, comp
        self.examples, self.fallback = list(examples), fallback
        self.example_tokens = set().union(*self.examples) if self.examples else set()
        self.by_slot = collections.defaultdict(list)
        self.by_comp = collections.defaultdict(list)
        self.free_sets = list(self.examples)
        self.roots = collections.Counter()
        self.consumer = set()
        self.hits = collections.Counter()
        self.composed = collections.Counter()
        self.where = {}
        self.assign = {}
        self.modal = []
        self.kept = collections.defaultdict(set)
        self.kept_source = collections.defaultdict(set)
        self.unpinned = collections.defaultdict(set)

    def use(self, texts):
        self.by_slot, self.free_sets, self.by_comp = collections.defaultdict(list), [], collections.defaultdict(list)
        for text in texts:
            for tag, slot, sets, inner in jsx_elements(text or ""):
                slots = {slot} if slot else self.parts.func_slots.get(tag, set())
                for x in slots:
                    self.by_slot[x] += sets
                    self.by_comp[component_of(x, self.names)] += inner
                if not slots or tag[:1].isupper() and not self.parts.func_slots.get(tag) and slot not in self.parts.by_slot:
                    self.free_sets += sets + inner
        self.examples = example_sets([t for t in texts if t])
        self.example_tokens = set().union(*self.examples) if self.examples else set()
        self.fallback = not texts or not any(texts)
        self.roots["fallback" if self.fallback else "example"] += 1

    def sets_for(self, slot, orig=None):
        if not slot:
            return self.free_sets
        out = list(self.by_slot.get(slot, [])) + list(self.by_comp.get(component_of(slot, self.names), []))
        for other in (orig, self.parts.alias.get(slot)):
            if other:
                out += self.by_slot.get(other, [])
        return out

    def keep(self, toks, slot, owners, orig=None):
        plain = [t for t in toks if not t.startswith("cn-")]
        if not owners and not (slot and component_of(slot, self.names)):
            return plain
        src = self.parts.source_of(owners | ({component_of(slot, self.names)} if slot else set()))
        cands = self.sets_for(slot, orig)
        suffix = example_suffix(toks, cands)
        own = self.parts.tokens.get(slot, set()) if slot else set()
        if self.fallback:
            keep = [t for t in plain if t not in src and self.parts.logical.get(t, t) not in own]
        elif slot:
            keep = [t for t in suffix if not t.startswith("cn-")]
        else:
            ok = set(suffix)
            keep = [t for t in plain if t in ok or t not in src]
        keep += [t for t in plain if t in KIT_CLASSES and t not in keep]
        if slot:
            self.kept[slot] |= set(keep)
            self.kept_source[slot] |= {t for t in keep if t in src}
            self.unpinned[slot] |= {t for t in plain if t not in keep and t not in src}
        return keep

    def infer(self, root):
        chain = []

        def walk(n):
            if isinstance(n, str):
                return
            a = dict(n["a"])
            slot = a.get("data-slot")
            toks = set(self.parts.canon(a.get("class", "").split()))
            for owner, attr, value, vt in self.parts.ancestor.get(slot, []) if slot else []:
                hit = len(vt & toks)
                if not vt or hit < min(2, len(vt)) or hit / len(vt) < 0.75:
                    continue
                if value.startswith("!"):
                    value = {"!horizontal": "vertical", "!vertical": "horizontal"}.get(value, "")
                    if not value:
                        continue
                for anc in reversed(chain):
                    if dict(anc["a"]).get("data-slot") == owner:
                        if attr not in dict(anc["a"]):
                            self.assign.setdefault(anc["i"], {})[attr] = value
                        break
            chain.append(n)
            for c in n["c"]:
                walk(c)
            chain.pop()

        walk(root)

    def node(self, n, owners=frozenset(), parent=None, index=0, last=True, ancestors=frozenset(), portal=False):
        if isinstance(n, str):
            return html.escape(n, quote=False)
        attrs = dict(n["a"])
        for k, v in self.assign.get(n["i"], {}).items():
            attrs.setdefault(k, v)
        for a in ("src", "srcset"):
            if a in attrs:
                attrs[a] = re.sub(r"(^|,\s*)/(?!/)", lambda m: m.group(1) + SITE + "/", attrs[a])
        if "data-input-otp-container" in attrs:
            attrs["data-slot"] = "input-otp"
        elif "data-input-otp" in attrs and attrs.get("data-slot") == "input-otp":
            del attrs["data-slot"]
        cls = attrs.pop("class", "")
        slot = attrs.get("data-slot")
        rdp = [m.group(1) for c in cls.split() if (m := RDP_PART.match(c))]
        if rdp and not slot:
            part = next((r for r in rdp if r not in RDP_MODIFIERS), None)
            if part:
                slot = "calendar" if part == "root" else "calendar-" + part.replace("_", "-")
                if slot != "calendar":
                    attrs["data-slot"] = slot
            for r in rdp:
                if r in RDP_MODIFIERS:
                    attrs.setdefault("data-" + r.replace("_", "-"), "true")
        if slot in BACKDROPS:
            return ""
        if slot == "calendar" and "rdp-dropdowns" in json.dumps(n):
            attrs.setdefault("data-caption-layout", "dropdown")
        if slot == "carousel" and "rotate-90" in json.dumps(n):
            attrs.setdefault("data-orientation", "vertical")
        orig = slot
        host = composed(cls, self.parts, slot, self.names, dict(parent["a"]).get("data-slot") if parent else None, ancestors) if slot and slot not in self.parts.alias else None
        if host and slot == "button":
            attrs["data-" + host] = ""
            self.composed[(slot, "button with data-" + host)] += 1
        elif host:
            attrs["data-slot"] = host
            attrs["data-" + slot] = ""
            self.composed[(slot, host)] += 1
            slot = host
        comp = component_of(slot, self.names) if slot else ""
        if comp:
            owners = owners | {comp}
        if portal and not owners:
            owners = frozenset({self.comp})
        extra, hits = infer_attrs(cls, self.parts, self.parts.alias.get(slot, slot), owners, self.comp)
        if "data-slot" in extra and not slot:
            slot = extra["data-slot"]
            attrs["data-slot"] = slot
        keep = self.keep(cls.split(), slot, owners, orig if orig != slot else None)
        self.hits.update(hits)
        for h in hits:
            pa = dict(parent["a"]) if parent else {}
            where = f"{pa.get('data-slot') or (parent or {}).get('t', '?')} > {n['t']} (child {index + 1}{', last' if last else ''}; attrs {' '.join(k for k in attrs if k not in ('data-pid', 'id', 'style'))})"
            self.where.setdefault(h, collections.Counter())[where] += 1
        for k, v in extra.items():
            attrs.setdefault(k, v)
        self.consumer.update(keep)
        tag = n["t"]
        if slot in BACKDROPS.values():
            tag = "dialog"
            attrs["data-parity-modal"] = ""
            attrs.pop("open", None)
            self.modal.append(n["i"])
        attrs["data-pid"] = str(n["i"])
        if keep:
            attrs["class"] = " ".join(keep)
        out = "<" + tag + "".join(f' {k}="{html.escape(v)}"' if v != "" else f" {k}" for k, v in attrs.items()) + ">"
        if tag in ("input", "img", "br", "hr", "meta", "source", "col", "wbr") and not n.get("svg"):
            return out
        kids = [c for c in n["c"] if not isinstance(c, str)]
        below = ancestors | {slot} if slot else ancestors
        inner = "".join(self.node(c, owners, n, kids.index(c) if not isinstance(c, str) else 0, not isinstance(c, str) and c is kids[-1], below, portal) for c in n["c"])
        return out + inner + f"</{tag}>"


def inherited(style):
    out = []
    for k in ("font-size", "font-weight", "letter-spacing", "direction", "text-align"):
        if style.get(k):
            out.append(f"{k}: {style[k]}")
    lh, fs = style.get("line-height", ""), style.get("font-size", "")
    if lh.endswith("px") and fs.endswith("px"):
        out.append(f"line-height: {float(lh[:-2]) / float(fs[:-2]):.4f}")
    return "; ".join(out)


def page_html(conv, cap, sources=None):
    body = []
    for root in cap["roots"]:
        conv.infer(root["tree"])
    for k, root in enumerate(cap["roots"]):
        if sources is not None:
            conv.use(sources(cap.get("examples", [None] * len(cap["roots"]))[k]))
        w = root["box"]["w"]
        style = inherited(root["inh"])
        if root["kind"] == "preview":
            color = "; color: CanvasText" if cap.get("view") else ""
            body.append(f'<div data-parity-scope style="width: {w}px; {style}{color}">{conv.node(root["tree"])}</div>')
        else:
            body.append(f'<div data-parity-portal style="{style}; color: CanvasText">{conv.node(root["tree"], portal=True)}</div>')
    return ("<!doctype html><html lang=\"en\" data-theme=\"light\"><head><meta charset=\"utf-8\">"
            "<link rel=\"stylesheet\" href=\"/gen.css\"><link rel=\"stylesheet\" href=\"/consumer.css\"><link rel=\"stylesheet\" href=\"/font.css\">"
            "</head><body>" + "".join(body) + "</body></html>")


EXPAND = """() => { let n = 0; for (const b of document.querySelectorAll('button')) if (b.textContent.trim() === 'View Code') { b.click(); n++ } return n }"""
PREVIEW_CODES = """() => [...document.querySelectorAll('[data-slot="preview"]')].map(e => e.closest('[data-slot="component-preview"]')?.querySelector('[data-slot="code"]')?.textContent || "")"""
PREVIEW_TEXTS = """() => [...document.querySelectorAll('[data-slot="preview"]')].map(e => {
  const out = new Set()
  const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT)
  while (w.nextNode() && out.size < 20) { const t = w.currentNode.textContent.trim(); if (t.length >= 6) out.add(t) }
  return [...out]
})"""


class Docs:
    def __init__(self, browser, args):
        self.ctx = browser.new_context(viewport={"width": 1280, "height": 800}, color_scheme="light", reduced_motion="no-preference")
        self.ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(SITE + "/") else r.abort())
        self.page = self.ctx.new_page()
        self.url = None
        self.meta = {}
        self.nova_page = None
        self.preview_styles = []

    def load(self, comp, view=None):
        path = view or f"/docs/components/base/{comp}"
        resp = self.page.goto(SITE + path, wait_until="networkidle", timeout=120000)
        if resp and not view and not self.meta:
            m = re.search(r'data-dpl-id="([\w-]+)"', resp.text())
            self.meta = {"deployment": m.group(1) if m else "", "etag": resp.headers.get("etag", ""), "age": resp.headers.get("age", ""), "url": resp.url}
        self.page.add_style_tag(content=FONT)
        scope = '[data-slot="preview"]'
        if view and view.startswith(NOVA_PAGE):
            scope = '[data-slot="example"]'
        elif view:
            self.page.evaluate("() => { for (const e of document.body.children) if (!['SCRIPT', 'STYLE', 'TEMPLATE', 'NEXTJS-PORTAL'].includes(e.tagName)) e.setAttribute('data-parity-view', '') }")
            scope = "[data-parity-view]"
        self.page.evaluate(JS, {"props": PROPS, "pseudoProps": PSEUDO_PROPS, "scope": scope})
        if self.page.evaluate(STOP_AUTOPLAY):
            self.page.evaluate(SETTLE, 1500)
        self.theme(False)
        self.page.mouse.move(1, 1)
        self.page.evaluate("() => window.__parity.mark()")

    def theme(self, dark):
        self.page.evaluate("d => { const h = document.documentElement; h.classList.toggle('dark', d); h.classList.toggle('light', !d); h.style.colorScheme = d ? 'dark' : 'light' }", dark)
        self.page.evaluate(SETTLE, 600)


class Ours:
    def __init__(self, browser, files, drop_slot=""):
        self.files = files
        self.ctx = browser.new_context(viewport={"width": 1280, "height": 800}, color_scheme="light", reduced_motion="no-preference")
        self.ctx.route("**/*", self.serve)
        self.page = self.ctx.new_page()
        self.scoped = None
        self.drop_slot = drop_slot
        self.dropped = 0
        self.errors = []
        self.page.on("console", lambda m: self.errors.append(f"{m.type}: {m.text}") if m.type in ("error",) else None)

    def serve(self, route):
        url = route.request.url
        if url.startswith(SITE + "/_next/image"):
            return route.continue_()
        if not url.startswith(LOCAL + "/"):
            return route.abort()
        name = url[len(LOCAL) + 1:].split("?")[0]
        body = self.files.get(name)
        if body is None:
            return route.fulfill(status=404, body="")
        ctype = "text/css" if name.endswith(".css") else "text/html"
        route.fulfill(status=200, body=body, headers={"content-type": ctype + "; charset=utf-8"})

    def load(self, name, active, hover=None, visible=False):
        self.page.goto(f"{LOCAL}/{name}", wait_until="load")
        if self.drop_slot:
            self.dropped = self.page.evaluate(DROP, self.drop_slot)
        self.page.evaluate(JS, {"props": PROPS, "pseudoProps": PSEUDO_PROPS, "scope": "[data-parity-scope], [data-parity-portal]", "ours": True})
        self.page.evaluate("() => { for (const d of document.querySelectorAll('dialog[data-parity-modal]')) d.showModal() }")
        self.page.evaluate("() => { const d = document.createElement('div'); d.id = 'parity-blank'; d.style.cssText = 'position:fixed;left:0;top:0;width:2px;height:2px;z-index:2147483647'; document.body.append(d) }")
        self.page.mouse.click(1, 1)
        self.page.evaluate("() => document.getElementById('parity-blank').remove()")
        if active and visible:
            self.page.keyboard.press("Shift")
        point = None if visible or not active else self.page.evaluate("""a => {
          const t = document.querySelector(`[data-pid="${a}"]`)
          if (!t || !t.getClientRects().length) return null
          const r = t.getBoundingClientRect()
          const x = r.x + Math.min(r.width / 2, 6), y = r.y + r.height / 2
          const hit = document.elementFromPoint(x, y)
          return hit && hit.closest('button, a[href], input, textarea, select, [tabindex], [contenteditable]') === t ? [x, y] : null
        }""", active)
        if point:
            self.page.mouse.move(*point)
            self.page.mouse.down()
            self.page.mouse.move(1, 1)
            self.page.mouse.up()
        if active:
            self.page.evaluate("a => { const t = document.querySelector(`[data-pid=\"${a}\"]`); if (t && document.activeElement !== t) t.focus({ preventScroll: true }) }", active)
        else:
            self.page.evaluate("() => document.activeElement?.blur?.()")
        self.theme(False)
        self.page.mouse.move(1, 1)
        if hover:
            at = self.page.evaluate("a => { const t = document.querySelector(`[data-pid=\"${a}\"]`); if (!t) return null; t.scrollIntoView({block: 'center', inline: 'center'}); const r = t.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2] }", hover)
            if at:
                self.page.mouse.move(*at)

    def theme(self, dark):
        self.page.evaluate("d => document.documentElement.dataset.theme = d ? 'dark' : 'light'", dark)
        self.page.evaluate("""m => {
          for (const [i, vars] of Object.entries(m || {})) {
            const e = i === "root" ? document.documentElement : document.querySelector(`[data-pid="${i}"]`)
            if (e) for (const [k, v] of Object.entries(vars)) e.style.setProperty(k, v)
          }
        }""", (self.scoped or {}).get("dark" if dark else "light"))
        self.page.evaluate(SETTLE, 600)


CAPTURE = """kind => {
  const P = window.__parity
  const roots = [...P.scopes().map(e => ["preview", e]), ...P.portals().map(e => ["portal", e])]
  return roots.map(([k, e]) => {
    const r = e.getBoundingClientRect()
    const cs = getComputedStyle(k === "preview" ? e : document.body)
    const inh = {}
    for (const p of ["color", "font-size", "font-weight", "line-height", "letter-spacing", "direction", "text-align"]) inh[p] = cs.getPropertyValue(p)
    return { kind: k, tree: P.serialize(e), box: { w: Math.round(r.width * 100) / 100, h: r.height }, inh }
  })
}"""
FIND = """([sel]) => {
  const P = window.__parity
  const seen = new Set()
  const out = []
  for (const s of P.scopes()) for (const e of s.querySelectorAll(sel)) {
    if (!e.getClientRects().length) continue
    const k = (e.getAttribute('data-slot') || '') + '|' + e.textContent.trim().slice(0, 40)
    if (seen.has(k)) continue
    seen.add(k)
    out.push(P.id(e))
  }
  return out
}"""
DIFF = """([before, roots]) => {
  const P = window.__parity
  const now = P.attrs(roots.map(i => P.el(i)).filter(Boolean))
  const out = []
  for (const [i, attrs] of Object.entries(now)) {
    const b = before[i] || {}
    for (const [k, v] of Object.entries(attrs)) if (b[k] !== v && k !== "class") out.push([Number(i), k, v])
    for (const k of Object.keys(b)) if (!(k in attrs) && k !== "class") out.push([Number(i), k, null])
  }
  return out
}"""
TOKENS = ["--" + t for t in ("background foreground card card-foreground popover popover-foreground primary primary-foreground secondary secondary-foreground muted muted-foreground accent accent-foreground destructive destructive-foreground border input ring radius chart-1 chart-2 chart-3 chart-4 chart-5 sidebar sidebar-foreground sidebar-primary sidebar-primary-foreground sidebar-accent sidebar-accent-foreground sidebar-border sidebar-ring").split()]
DROP = """slot => {
  const needle = `[data-slot="${slot}"]`
  let n = 0
  const walk = list => {
    for (let i = list.cssRules.length - 1; i >= 0; i--) {
      const r = list.cssRules[i]
      if (r.selectorText !== undefined && r.selectorText.includes(needle)) { list.deleteRule(i); n++; continue }
      if (r.cssRules) walk(r)
    }
  }
  for (const sheet of document.styleSheets) if ((sheet.href || "").endsWith("/gen.css")) walk(sheet)
  return n
}"""
SCOPED = """names => {
  const P = window.__parity
  const out = {}
  const rs = getComputedStyle(document.documentElement)
  out.root = {}
  for (const n of names) out.root[n] = rs.getPropertyValue(n).trim()
  const roots = [...P.scopes(), ...P.portals()]
  for (const r of roots) for (const e of r.querySelectorAll('[class*="theme-"]')) {
    if (![...e.classList].some(c => c.startsWith("theme-"))) continue
    const cs = getComputedStyle(e)
    const v = {}
    for (const n of names) v[n] = cs.getPropertyValue(n).trim()
    out[P.id(e)] = v
  }
  return out
}"""
SNAP = "roots => window.__parity.attrs(roots.map(i => window.__parity.el(i)).filter(Boolean))"
STOP_AUTOPLAY = """async () => {
  const roots = [...document.querySelectorAll('[data-slot="carousel-content"]')]
  for (const r of roots) {
    r.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, button: 0 }))
    document.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, button: 0 }))
  }
  const read = () => roots.map(r => getComputedStyle(r.firstElementChild || r).transform).join()
  let last = read()
  for (let i = 0, same = 0; i < 600 && same < 30; i++) {
    await new Promise(r => requestAnimationFrame(r))
    const now = read()
    same = now === last ? same + 1 : 0
    last = now
  }
  return roots.length
}"""
INITIALS = "tags => window.__parity.initials(tags)"
CENTER = "i => { const e = window.__parity.el(i); e.scrollIntoView({block: 'center', inline: 'center'}); const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2] }"


def reads(page, ids, backdrop_ids=()):
    lst = [[i, None] for i in ids] + [[i, p] for i in ids for p in PSEUDOS] + [[i, "::backdrop"] for i in backdrop_ids]
    return page.evaluate("l => window.__parity.readAll(l)", lst)


def scenario_info(cap, names=None):
    meta, ids, overlays, portal_ids = {}, [], {}, set()

    def visit(n, inside, kind, parent=0, style="nova"):
        if isinstance(n, str):
            return
        a = dict(n["a"])
        slot = a.get("data-slot", "")
        inside = inside or bool(slot and slot != "preview" and (names is None or component_of(slot, names)))
        meta[n["i"]] = {"parent": parent, "slot": slot, "tag": n["t"], "style": style, "dis": bool(n.get("dis")) or "data-disabled" in a or a.get("aria-disabled") == "true",
                        "attrs": {k: v for k, v in a.items() if k in ("data-variant", "data-size", "data-orientation", "data-side", "role", "type")}, "cls": a.get("class", "")}
        if inside:
            ids.append(n["i"])
        if slot in BACKDROPS or slot in BACKDROPS.values():
            overlays[slot] = n["i"]
        if kind == "portal":
            portal_ids.add(n["i"])
        for c in n["c"]:
            visit(c, inside, kind, n["i"], style)

    for r, style in zip(cap["roots"], cap.get("styles") or [None] * len(cap["roots"])):
        visit(r["tree"], False, r["kind"], 0, style or "nova")
    return meta, ids, overlays, portal_ids


def label(meta, i):
    m = meta.get(i) or meta.get(str(i)) or {}
    base = m.get("slot")
    if not base:
        base, up = m.get("tag", "?"), m.get("parent", 0)
        while up:
            pm = meta.get(up) or meta.get(str(up)) or {}
            if pm.get("slot") and pm["slot"] != "preview":
                base += " in " + pm["slot"]
                break
            up = pm.get("parent", 0)
    extra = ",".join(f"{k.removeprefix('data-')}={v}" for k, v in sorted(m.get("attrs", {}).items()) if k in ("data-variant", "data-size", "data-orientation"))
    return base + (f"[{extra}]" if extra else "")


def pick_states(page, ids, meta, limit, only=None):
    pool = [i for i in ids if only is None or i in only]
    cands = page.evaluate("""([ids, sel]) => ids.filter(i => { const e = window.__parity.el(i); return e && e.matches(sel) && e.getClientRects().length && !e.matches(':disabled') && e.getAttribute('aria-disabled') !== 'true' && !e.hasAttribute('data-disabled') })""", [pool, INTERACTIVE])
    seen, out = set(), []
    for i in cands:
        m = meta[i]
        key = (m["slot"], m["tag"], tuple(sorted(m["attrs"].items())), " ".join(sorted(t for t in m["cls"].split() if not t.startswith("lucide"))))
        if key in seen:
            continue
        seen.add(key)
        out.append(i)
        if len(out) >= limit:
            break
    return out


def act(page, i, state):
    box = page.evaluate(CENTER, i)
    page.mouse.move(1, 1)
    page.evaluate(SETTLE, 400)
    if state == "hover":
        page.mouse.move(*box)
    elif state == "press":
        page.mouse.click(1, 1)
        box = page.evaluate(CENTER, i)
        page.mouse.move(*box)
        page.evaluate(SETTLE, 300)
        page.mouse.down()
    elif state == "focus":
        page.evaluate("() => document.activeElement?.blur?.()")
        page.keyboard.press("Shift")
        page.evaluate("i => window.__parity.el(i).focus({ preventScroll: true })", i)
    page.evaluate(SETTLE, 800)


def undo(page, state):
    page.mouse.move(1, 1)
    if state == "press":
        page.mouse.up()
    page.evaluate("() => document.activeElement?.blur?.()")
    page.evaluate(SETTLE, 400)


def open_trigger(docs, how, sel, n):
    found = docs.page.evaluate(FIND, [sel])
    if n >= len(found):
        return None
    box = docs.page.evaluate(CENTER, found[n])
    docs.page.evaluate(SETTLE, 300)
    if how == "hover":
        docs.page.mouse.move(*box)
        docs.page.wait_for_timeout(900)
    elif how == "right":
        docs.page.mouse.click(*box, button="right")
    else:
        docs.page.mouse.click(*box)
        docs.page.mouse.move(1, 1)
    docs.page.evaluate(SETTLE, 1500)
    docs.page.wait_for_timeout(250)
    return found[n]


def blob_sha1(b):
    return hashlib.sha1(b"blob %d\x00" % len(b) + b).hexdigest()


EXAMPLE_FN = re.compile(r"export\s+(?:default\s+)?function\s+(\w+)")
DEFINED_FN = re.compile(r"^(?:export\s+)?function\s+([A-Z]\w*)", re.M)
LOCAL_FN = re.compile(r"^function\s+([A-Z]\w*)", re.M)
STYLE_IMPORT = re.compile(r"@/styles/base-([a-z]+)/")
DOCS_EXAMPLES = "apps/v4/examples/base/"
BASE_EXAMPLES = ("apps/v4/registry/bases/base/examples/", "apps/v4/registry/bases/base/components/")
HELPERS = "apps/v4/components/"
HELPER_IMPORT = re.compile(r'from\s+"@/components/([a-z0-9-]+)"')


class Examples:
    helpers = {}

    def __init__(self, src, cache, pin):
        tree = json.loads((pathlib.Path(src) / "tree.json").read_text())
        top = lambda path, d: path.endswith(".tsx") and path.startswith(d) and path.count("/") == d.count("/")
        files = {t["path"]: t["sha"] for t in tree["tree"] if any(top(t["path"], d) for d in (DOCS_EXAMPLES, *BASE_EXAMPLES, HELPERS))}
        cache.mkdir(parents=True, exist_ok=True)

        def get(path):
            prefix = "" if path.startswith(DOCS_EXAMPLES) else "component-" if path.startswith(HELPERS) else "registry-"
            dest = cache / (prefix + path.rsplit("/", 1)[1])
            if not dest.exists():
                subprocess.run(["curl", "-sSfL", "--proto", "=https", "--proto-redir", "=https", "--max-time", "60", "-o", str(dest), f"https://raw.githubusercontent.com/shadcn-ui/ui/{pin}/{path}"], capture_output=True)
            body = dest.read_bytes() if dest.exists() else b""
            if blob_sha1(body) != files[path]:
                raise RuntimeError(f"{path}: git blob {blob_sha1(body)}, tree {files[path]}")
            return path, body.decode()

        with ThreadPoolExecutor(8) as pool:
            texts = dict(pool.map(get, sorted(p for p in files if not p.startswith(HELPERS))))
            wanted = {HELPERS + n + ".tsx" for t in texts.values() for n in HELPER_IMPORT.findall(t)} & set(files)
            self.helpers = {p.rsplit("/", 1)[1][:-4]: t for p, t in pool.map(get, sorted(wanted))}
        self.text = {p.rsplit("/", 1)[1][:-4]: t for p, t in texts.items() if p.startswith(DOCS_EXAMPLES)}
        self.nova = {p.rsplit("/", 1)[1][:-4]: t for p, t in texts.items() if not p.startswith(DOCS_EXAMPLES)}
        self.ui_fns = set()
        for f in sorted((pathlib.Path(src) / "apps/v4/registry/bases/base/ui").glob("*.tsx")):
            self.ui_fns |= set(DEFINED_FN.findall(f.read_text()))
        self.by_fn = collections.defaultdict(list)
        for name in sorted(self.text):
            for fn in EXAMPLE_FN.findall(self.text[name]):
                self.by_fn[fn].append(name)

    def style(self, name):
        if set(LOCAL_FN.findall(self.text.get(name, ""))) & self.ui_fns:
            return "own"
        styles = set(STYLE_IMPORT.findall(self.text.get(name, "")))
        if styles - {"nova"}:
            return "+".join(sorted(styles - {"nova"}))
        return "nova"

    def of(self, name):
        if name in self.text:
            return [self.text[name], *self.imported(self.text[name])]
        if name in self.nova:
            return [self.nova[name], self.nova.get("example", ""), *self.imported(self.nova[name])]
        return []

    def imported(self, text):
        return [self.helpers[n] for n in dict.fromkeys(HELPER_IMPORT.findall(text)) if n in self.helpers]

    def name_of_code(self, code):
        for fn in EXAMPLE_FN.findall(code or ""):
            names = self.by_fn.get(fn) or []
            if len(names) == 1:
                return names[0]
            if names:
                lines = {l.strip() for l in code.splitlines() if l.strip()}
                score = lambda n: (len(lines & {l.strip() for l in self.text[n].splitlines()}), -abs(len(self.text[n]) - len(code)))
                return max(names, key=score)
        return None

    def name_of_texts(self, texts):
        scores = collections.Counter({name: sum(t in body for t in texts) for name, body in self.text.items()})
        top = scores.most_common(2)
        if not top or top[0][1] < min(2, len(texts)) or top[0][1] == 0 or len(top) > 1 and top[1][1] == top[0][1]:
            return None
        return top[0][0]

    def style_of_code(self, code):
        name = self.name_of_code(code)
        return self.style(name) if name else "nova"


def root_styles(roots, preview_styles, view_style=None):
    out, k = [], 0
    for r in roots:
        if r["kind"] != "preview":
            out.append(None)
            continue
        out.append(view_style or (preview_styles[k] if k < len(preview_styles) else "nova"))
        k += 1
    return out


def contains(n, i):
    if isinstance(n, str):
        return False
    return n["i"] == i or any(contains(c, i) for c in n["c"])


def measure_docs(comp, docs, args, examples):
    docs.load(comp)
    if docs.page.evaluate(EXPAND):
        docs.page.wait_for_timeout(500)
    docs.preview_styles, docs.preview_names = [], []
    for code, texts in zip(docs.page.evaluate(PREVIEW_CODES), docs.page.evaluate(PREVIEW_TEXTS)):
        name = examples.name_of_code(code) or examples.name_of_texts(texts)
        docs.preview_names.append(name)
        docs.preview_styles.append(examples.style(name) if name else "nova")
    docs.meta["date"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    views = [None]
    if not docs.page.evaluate("() => window.__parity.scopes().length"):
        views = docs.page.evaluate("() => [...new Set([...document.querySelectorAll('iframe[src^=\"/view/\"]')].map(f => f.getAttribute('src')))].slice(0, 2)") or [None]
    out = []
    for k, view in enumerate(views):
        name = view.rstrip("/").split("/")[-1] if view else None
        style = examples.style(name) if view else None
        out += measure_view(comp, docs, args, view, f"v{k + 1}-" if view else "", len(out), examples, style, name if name in examples.text else None)
    page = nova_page(comp, out, examples)
    if page:
        docs.nova_page = page
        out += measure_view(comp, docs, args, page, "nova-", len(out), examples, "nova", f"{comp}-example")
    return out


def nova_page(comp, results, examples):
    other = any(st != "nova" for r in results for st in r["cap"].get("styles") or [])
    return f"{NOVA_PAGE}{comp}-example?style=nova" if other and f"{comp}-example" in examples.nova else None


def root_names(roots, preview_names, view_name=None):
    out, k = [], 0
    for r in roots:
        if r["kind"] != "preview":
            out.append(None)
            continue
        out.append(view_name if view_name is not None else (preview_names[k] if k < len(preview_names) else None))
        k += 1
    return out


def measure_view(comp, docs, args, view, prefix, offset, examples, view_style=None, view_name=None):
    how, sel = OPEN.get(comp, ("click", DEFAULT_OPEN))
    docs.load(comp, view)
    triggers = docs.page.evaluate(FIND, [sel])
    plan = [("rest", None)] + [("open", n) for n in range(min(len(triggers), args.max_open))]
    out = []
    for kind, n in plan:
        hovered = None
        if kind == "open":
            docs.load(comp, view)
            trig = open_trigger(docs, how, sel, n)
            if not trig:
                continue
            hovered = trig if how == "hover" else None
        cap = {"roots": docs.page.evaluate(CAPTURE, "docs"), "active": docs.page.evaluate("() => window.__parity.active()"), "visible": docs.page.evaluate("() => !!document.activeElement?.matches(':focus-visible')"), "hover": hovered, "view": bool(view) and not view.startswith(NOVA_PAGE)}
        if kind == "open" and not any(r["kind"] == "portal" for r in cap["roots"]) and comp not in ("accordion", "collapsible", "toggle", "toggle-group"):
            continue
        styles = root_styles(cap["roots"], docs.preview_styles, view_style)
        opener = next((st for r, st in zip(cap["roots"], styles) if st and kind == "open" and contains(r["tree"], trig)), "nova")
        cap["styles"] = [st or opener for st in styles]
        names = root_names(cap["roots"], docs.preview_names if view is None else [], view_name if view is not None else None)
        opener_name = next((nm for r, nm in zip(cap["roots"], names) if nm and kind == "open" and contains(r["tree"], trig)), None)
        cap["examples"] = [nm if r["kind"] == "preview" else opener_name for r, nm in zip(cap["roots"], names)]
        meta, ids, overlays, portal_ids = scenario_info(cap, args.names)
        res = {"label": prefix + ("rest" if kind == "rest" else f"open-{len(out)}"), "cap": cap, "meta": meta, "ids": ids, "overlays": overlays, "docs": {}, "tokens": {}, "states": {}}
        for theme in ("light", "dark"):
            docs.theme(theme == "dark")
            res["docs"][theme] = reads(docs.page, ids)
            res["tokens"][theme] = docs.page.evaluate(SCOPED, TOKENS)
        res["initial_docs"] = docs.page.evaluate(INITIALS, sorted({m["tag"] for m in meta.values()}))
        docs.theme(False)
        roots = [r["tree"]["i"] for r in cap["roots"]]
        targets = [] if args.quick else pick_states(docs.page, ids, meta, args.max_states, portal_ids if kind == "open" else None)
        states = ("hover", "press", "focus") if kind == "rest" else ("hover", "focus")
        for i in targets:
            for state in states:
                for theme in ("light", "dark"):
                    docs.theme(theme == "dark")
                    if not docs.page.evaluate("i => !!window.__parity.el(i)?.isConnected", i):
                        continue
                    before = docs.page.evaluate(SNAP, roots)
                    act(docs.page, i, state)
                    diff = docs.page.evaluate(DIFF, [before, roots])
                    active = docs.page.evaluate("() => window.__parity.active()")
                    sub = list(dict.fromkeys([i] + [d[0] for d in diff]))
                    res["states"][f"{i}|{state}|{theme}"] = {"diff": diff, "active": active, "ids": sub, "docs": reads(docs.page, sub), "before": before}
                    undo(docs.page, state)
            docs.theme(False)
        out.append(res)
    return out


def page_style(cap):
    counts = collections.Counter(st for r, st in zip(cap["roots"], cap.get("styles") or []) if r["kind"] == "preview" and st in STYLES)
    return counts.most_common(1)[0][0] if counts else STYLES[0]


GROUP_CLASS = re.compile(r"\.(?:group|peer)\\/[\w-]+")


def group_owners(css, parts):
    owners = collections.defaultdict(list)
    for p in parts:
        for name, sels in p.groups.items():
            owners[name] += [s for s in sels if s not in owners[name]]

    def sub(m):
        sels = owners.get(m.group(0))
        return ":is(" + ", ".join([m.group(0), *sels]) + ")" if sels else m.group(0)

    return GROUP_CLASS.sub(sub, css)


def measure_ours(comp, results, ours, parts, names, gen_css, src, out, docs, sources):
    if isinstance(parts, Parts):
        parts = {STYLES[0]: parts}
    convs = {st: Converter(p, names, comp) for st, p in parts.items()}
    pages, used = {}, collections.Counter()
    for r in results:
        r["style"] = page_style(r["cap"])
        pages[r["label"]] = page_html(convs[r["style"]], r["cap"], sources.of)
        used[r["style"]] += 1
    conv = convs[used.most_common(1)[0][0] if used else STYLES[0]]
    consumer = set().union(*(c.consumer for c in convs.values()))
    content = out / "pages" / comp
    content.mkdir(parents=True, exist_ok=True)
    for name, body in pages.items():
        (content / f"{name}.html").write_text(body)
    (content / "classes.html").write_text("\n".join(sorted(consumer)) + "\n")
    consumer_css = content / "consumer.css"
    r = subprocess.run([GEN, "utilities", "-src", src, "-content", str(content / "classes.html"), "-out", str(consumer_css)], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"utilities: {r.stderr}")
    consumer_css.write_text(group_owners(consumer_css.read_text(), parts.values()))
    ours.files = {"consumer.css": consumer_css.read_text(), "font.css": FONT}
    ours.files.update({f"{k}.html": v for k, v in pages.items()})
    for res in results:
        ours.files["gen.css"] = gen_css[res["style"]]
        ov = res["overlays"]
        backdrop = [ov[c] for o, c in BACKDROPS.items() if o in ov and c in ov]
        ours.scoped = res["tokens"]
        ours.load(f"{res['label']}.html", res["cap"].get("active"), res["cap"].get("hover"), res["cap"].get("visible"))
        res["ours"] = {}
        for theme in ("light", "dark"):
            ours.theme(theme == "dark")
            res["ours"][theme] = reads(ours.page, res["ids"], backdrop)
        res["initial"] = {"docs": res.get("initial_docs") or {}, "ours": ours.page.evaluate(INITIALS, sorted({m["tag"] for m in res["meta"].values()}))}
        ours.theme(False)
        for key, st in res["states"].items():
            i, state, theme = key.split("|")
            i = int(i)
            ours.theme(theme == "dark")
            if not ours.page.evaluate("i => !!window.__parity.el(i)", i):
                continue
            if state == "focus" and st["active"] != i:
                st["skip"] = "live focus moved to another element"
                continue
            prev_sync = ours.page.evaluate("d => window.__parity.sync(d)", [st.get("before") or {}, STATE_ATTRS])
            prev = ours.page.evaluate("d => window.__parity.apply(d)", st["diff"])
            act(ours.page, i, state)
            if st["active"] and state != "focus":
                ours.page.evaluate("a => { const e = window.__parity.el(a); if (e && document.activeElement !== e) e.focus({ preventScroll: true }) }", st["active"])
                ours.page.evaluate(SETTLE, 400)
            st["ours"] = reads(ours.page, st["ids"])
            undo(ours.page, state)
            ours.page.evaluate("d => window.__parity.apply(d)", prev)
            ours.page.evaluate("d => window.__parity.apply(d)", prev_sync)
        ours.theme(False)
    return conv


COLOR = re.compile(r"rgba\((\d+),(\d+),(\d+),([\d.]+)\)")
QTY = re.compile(r"(?<![\w.#-])(-?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)(px|ms|s|deg|%|[a-z]+)?(?![\w.])")
MATRIX = re.compile(r"matrix(3d)?\(([^()]*)\)")
SKIP_PROPS = {"@x", "@y", "transform-origin"}
LOGICAL = {"start": "left", "end": "right"}
MOVING = {"transform", "translate", "rotate", "scale", "@w", "@h"}
TOL_PX = 0.5
TOL_UNITLESS = 0.01
TOL_ALPHA = 0.01
TOL_DE = 0.5
GEOMETRY = {"@w", "@h"}


def huge(v):
    m = re.fullmatch(r"(-?[\d.]+(?:e[+-]?\d+)?)px", str(v))
    return m is not None and float(m.group(1)) >= 1e4


def lab(rgb):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(c1, c2):
    l1, a1, b1 = lab(c1)
    l2, a2, b2 = lab(c2)
    cb = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    g = 0.5 * (1 - math.sqrt(cb ** 7 / (cb ** 7 + 25 ** 7)))
    a1p, a2p = a1 * (1 + g), a2 * (1 + g)
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dl, dc = l2 - l1, c2p - c1p
    dh = 0 if c1p * c2p == 0 else (h2p - h1p if abs(h2p - h1p) <= 180 else h2p - h1p - 360 if h2p > h1p else h2p - h1p + 360)
    dhp = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dh / 2))
    lb, cbp = (l1 + l2) / 2, (c1p + c2p) / 2
    if c1p * c2p == 0:
        hb = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hb = (h1p + h2p) / 2
    else:
        hb = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    t = 1 - 0.17 * math.cos(math.radians(hb - 30)) + 0.24 * math.cos(math.radians(2 * hb)) + 0.32 * math.cos(math.radians(3 * hb + 6)) - 0.2 * math.cos(math.radians(4 * hb - 63))
    sl = 1 + 0.015 * (lb - 50) ** 2 / math.sqrt(20 + (lb - 50) ** 2)
    sc, sh = 1 + 0.045 * cbp, 1 + 0.015 * cbp * t
    rt = -2 * math.sqrt(cbp ** 7 / (cbp ** 7 + 25 ** 7)) * math.sin(math.radians(60 * math.exp(-(((hb - 275) / 25) ** 2))))
    return math.sqrt((dl / sl) ** 2 + (dc / sc) ** 2 + (dhp / sh) ** 2 + rt * (dc / sc) * (dhp / sh))


def same_color(x, y):
    ax, ay = float(x[3]), float(y[3])
    if abs(ax - ay) > TOL_ALPHA:
        return False
    cx, cy = [int(v) for v in x[:3]], [int(v) for v in y[:3]]
    for bg in (255, 0):
        px = [c * ax + bg * (1 - ax) for c in cx]
        py = [c * ay + bg * (1 - ay) for c in cy]
        if delta_e(px, py) > TOL_DE:
            return False
    return True


def tolerance(unit):
    if unit == "px":
        return TOL_PX
    if unit in ("s", "ms"):
        return 1e-9
    return TOL_UNITLESS


def quantities(v):
    out = []
    pos = 0
    for m in MATRIX.finditer(v):
        out += [(float(q), u or "") for q, u in QTY.findall(v[pos:m.start()])]
        args = [a.strip() for a in m.group(2).split(",")]
        moves = {12, 13, 14} if m.group(1) else {4, 5}
        for k, a in enumerate(args):
            out.append((float(a), "px" if k in moves else ""))
        pos = m.end()
    out += [(float(q), u or "") for q, u in QTY.findall(v[pos:])]
    return out


def skeleton(v):
    v = MATRIX.sub(lambda m: "matrix" + (m.group(1) or "") + "(" + ",".join("N" for _ in m.group(2).split(",")) + ")", v)
    return QTY.sub(lambda m: "N" + (m.group(2) or ""), v)


def close(a, b, prop=""):
    if a == b or huge(a) and huge(b):
        return True
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= (TOL_PX if prop in GEOMETRY else TOL_UNITLESS)
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    ca, cb = COLOR.findall(a), COLOR.findall(b)
    if len(ca) != len(cb) or not all(same_color(x, y) for x, y in zip(ca, cb)):
        return False
    ra, rb = COLOR.sub("C", a), COLOR.sub("C", b)
    if skeleton(ra) != skeleton(rb):
        return False
    qa, qb = quantities(ra), quantities(rb)
    return len(qa) == len(qb) and all(ua == ub and abs(x - y) <= tolerance(ua) for (x, ua), (y, ub) in zip(qa, qb))


def initial_of(init, tag, prop):
    return (init.get(tag) or {}).get(prop)


def compare_maps(docs, ours, meta, scen, state, theme, rows, pairs, overlays=(), initial=None, measured="nova"):
    ov_ids = {str(o): str(c) for o, c in overlays}
    init_docs, init_ours = (initial or {}).get("docs") or {}, (initial or {}).get("ours") or {}
    for dk, dv in docs.items():
        base, _, pseudo = str(dk).partition("::")
        if base in ov_ids:
            if pseudo:
                continue
            ok, props, lab_ = f"{ov_ids[base]}::backdrop", BACKDROP_PROPS, label(meta, int(base)) + " (::backdrop)"
        else:
            ok, props, lab_ = str(dk), None, label(meta, int(base)) + (f"::{pseudo}" if pseudo else "")
        ov = ours.get(ok)
        m = meta.get(int(base)) or {}
        st = "disabled" if state == "rest" and m.get("dis") else state
        tag = m.get("tag", "")
        plain = not pseudo and base not in ov_ids
        visible = not plain or dv.get("@visible") or (ov or {}).get("@visible")
        positioned = not m.get("slot") and str((ov or {}).get("position")) in ("absolute", "fixed") and dv.get("position") in ("absolute", "fixed")
        spinning = False
        up = int(base)
        while up and not spinning:
            spinning = any("infinite" in str((mm.get(str(up)) or {}).get("animation-iteration-count", "")) for mm in (docs, ours))
            up = (meta.get(up) or {}).get("parent", 0)
        no_outline = dv.get("outline-style") == "none" and (ov or {}).get("outline-style") == "none"
        sr_only = dv.get("position") == "absolute" and (ov or {}).get("position") == "absolute" and dv.get("width") == "1px" and (ov or {}).get("width") == "1px"
        key = (scen, base, lab_, st, theme)
        style = m.get("style", "nova")
        if style != measured:
            style += "@" + measured
        pr = pairs.setdefault(key, {"part": lab_, "state": st, "theme": theme, "scenario": scen, "style": style, "visible": bool(visible), "props": 0, "meaningful": 0, "equal": 0, "meaningful_equal": 0, "diffs": []})
        for prop, v in dv.items():
            if prop in SKIP_PROPS or props and prop not in props or spinning and prop in MOVING or positioned and prop in ("right", "bottom"):
                continue
            if no_outline and prop in ("outline-width", "outline-offset", "outline-color") or sr_only and prop in ("top", "right", "bottom", "left"):
                continue
            o = "<missing>" if ov is None else ov.get(prop, "<missing>")
            good = close(v, o, prop) or prop == "text-align" and LOGICAL.get(o) == v or prop == "user-select" and v == "auto" and o == "text"
            meaningful = not plain or prop.startswith("@") or v != initial_of(init_docs, tag, prop) or o != initial_of(init_ours, tag, prop)
            pr["props"] += 1
            pr["equal"] += good
            pr["meaningful"] += meaningful
            pr["meaningful_equal"] += good and meaningful
            if not good:
                pr["diffs"].append(prop)
                rows.append({"scenario": scen, "state": st, "theme": theme, "part": lab_, "id": base, "prop": prop, "shadcn": v, "ours": o, "style": style})


def compare(comp, results):
    rows, pairs = [], {}
    for res in results:
        meta = res["meta"]
        ov = res["overlays"]
        overlay_pairs = [(ov[o], ov[c]) for o, c in BACKDROPS.items() if o in ov and c in ov]
        initial = res.get("initial")
        measured = res.get("style", "nova")
        for theme in ("light", "dark"):
            compare_maps(res["docs"][theme], res["ours"][theme], meta, res["label"], "rest", theme, rows, pairs, overlay_pairs, initial, measured)
        for key, st in res["states"].items():
            if "ours" not in st:
                continue
            i, state, theme = key.split("|")
            only = {k: v for k, v in st["docs"].items() if k.split("::")[0] == i}
            compare_maps(only, st["ours"], meta, res["label"], state, theme, rows, pairs, (), initial, measured)
    return rows, pairs


def state_key(scen, st):
    return "open" if "open-" in scen and st == "rest" else st


def part_stats(pairs):
    by_state = collections.defaultdict(lambda: [0, 0])
    by_part = {}
    for p in pairs:
        st = state_key(p["scenario"], p["state"])
        by_state[st][0] += not p["diffs"]
        by_state[st][1] += 1
        bp = by_part.setdefault(p["part"], {"pairs": 0, "equal": 0, "states": collections.Counter(), "props": collections.Counter()})
        bp["pairs"] += 1
        bp["equal"] += not p["diffs"]
        if p["diffs"]:
            bp["states"][st] += 1
            bp["props"].update(p["diffs"])
    differing = [{"part": k, "pairs": v["pairs"], "equal": v["equal"], "states": dict(v["states"]), "props": dict(v["props"].most_common(8))} for k, v in sorted(by_part.items()) if v["equal"] < v["pairs"]]
    return by_state, by_part, differing


def style_summary(rows, pairs, style):
    own = [p for p in pairs.values() if p.get("style", "nova") == style]
    visible = [p for p in own if p["visible"]]
    totals = {k: sum(p[k] for p in own) for k in ("props", "equal", "meaningful", "meaningful_equal")}
    by_state, by_part, differing = part_stats(visible)
    groups = collections.defaultdict(list)
    keys = {(p["scenario"], p["state"], p["theme"], p["part"]) for p in visible}
    for r in rows:
        if r.get("style", "nova") == style and (r["scenario"], r["state"], r["theme"], r["part"]) in keys:
            groups[(r["part"], r["state"], r["prop"])].append(r)
    top = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    return {"equal": totals["equal"], "measured": totals["props"], "meaningful_equal": totals["meaningful_equal"], "meaningful": totals["meaningful"],
            "pairs_equal": sum(not p["diffs"] for p in visible), "pairs": len(visible), "parts": len(by_part), "parts_equal": sum(v["equal"] == v["pairs"] for v in by_part.values()),
            "by_state": {k: v for k, v in sorted(by_state.items())}, "differing_parts": differing,
            "top": [{"part": k[0], "state": k[1], "prop": k[2], "count": len(v), "themes": sorted({x["theme"] for x in v}), "shadcn": v[0]["shadcn"], "ours": v[0]["ours"]} for k, v in top[:40]]}


def summarize(comp, rows, pairs):
    other = [p for p in pairs.values() if p["visible"] and p.get("style", "nova") not in STYLES]
    _, other_parts, other_differing = part_stats(other)
    out = {"component": comp, **style_summary(rows, pairs, "nova")}
    out["styles"] = {st: style_summary(rows, pairs, st) for st in STYLES[1:] if any(p.get("style") == st for p in pairs.values())}
    return {**out,
            "other_style": {"styles": sorted({p["style"] for p in other}), "pairs": len(other), "pairs_equal": sum(not p["diffs"] for p in other), "parts": len(other_parts), "parts_equal": sum(v["equal"] == v["pairs"] for v in other_parts.values()), "differing_parts": other_differing}}


def recompare(out):
    for f in sorted(out.glob("*.pairs.json")):
        comp = f.name.removesuffix(".pairs.json")
        summary = json.loads((out / f"{comp}.json").read_text())
        rows = json.loads((out / f"{comp}.rows.json").read_text())
        pairs = {tuple(p["key"]): p for p in json.loads(f.read_text())}
        keep = [r for r in rows if not close(r["shadcn"], r["ours"], r["prop"])]
        if len(keep) == len(rows):
            continue
        for r in rows:
            if close(r["shadcn"], r["ours"], r["prop"]):
                for p in pairs.values():
                    if p["scenario"] == r["scenario"] and p["state"] == r["state"] and p["theme"] == r["theme"] and p["part"] == r["part"] and str(p["key"][1]) == str(r["id"]) and r["prop"] in p["diffs"]:
                        p["diffs"].remove(r["prop"])
                        p["equal"] += 1
                        p["meaningful_equal"] += 1
        new = summarize(comp, keep, pairs)
        summary.update({k: v for k, v in new.items() if k != "component"})
        (out / f"{comp}.json").write_text(json.dumps(summary, indent=1))
        (out / f"{comp}.rows.json").write_text(json.dumps(keep))
        f.write_text(json.dumps([{**p, "key": list(k)} for k, p in pairs.items()]))
        log(f"{comp}: {len(rows) - len(keep)} values now equal")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--recompare":
        return recompare(pathlib.Path(sys.argv[2]))
    ap = argparse.ArgumentParser(description="Appearance parity of the generated CSS with ui.shadcn.com (needs the network)")
    ap.add_argument("--src", default=os.environ.get("SHADCN_SRC"), help="pinned shadcn inputs (go run ./tools/gen fetch)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--engine", default="chromium")
    ap.add_argument("--max-open", type=int, default=3)
    ap.add_argument("--max-states", type=int, default=8)
    ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--quick", action="store_true", help="rest and open only, no hover, press, or focus")
    ap.add_argument("--drop-slot", default="", help="self-test: remove every generated rule for this data-slot before measuring")
    ap.add_argument("--examples", default="", help="cache of the pinned apps/v4/examples/base files (default: <src>/parity-examples)")
    args = ap.parse_args()
    if not args.src:
        raise SystemExit("set --src or SHADCN_SRC")
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    gen = out / "gen"
    global GEN
    GEN = str(out / "gen-bin")
    STYLES[:] = [s["name"] for s in json.loads((ROOT / "skills/clanker-ui/references/clanker-ui.json").read_text())["files"]["styles"]]
    cmds = [["go", "build", "-o", GEN, "./tools/gen"], [GEN, "-src", args.src, "-kit", "", "-out", str(gen / "clanker-ui.generated.css"), "-notes", str(gen / "notes.txt"), "-parts", str(out / "parts.json")]]
    cmds += [[GEN, "-src", args.src, "-kit", "", "-style", st, "-out", str(gen / f"clanker-ui-{st}.generated.css"), "-notes", str(gen / f"notes-{st}.txt"), "-parts", str(gen / f"parts-{st}.json")] for st in STYLES[1:]]
    for cmd in cmds:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(r.stderr)
    gen_css = {STYLES[0]: (gen / "clanker-ui.generated.css").read_text()} | {st: (gen / f"clanker-ui-{st}.generated.css").read_text() for st in STYLES[1:]}
    data = json.loads((out / "parts.json").read_text())
    parts = {STYLES[0]: Parts(data)} | {st: Parts(json.loads((gen / f"parts-{st}.json").read_text())) for st in STYLES[1:]}
    names = data["components"]
    comps = [c for c in (args.only.split(",") if args.only else names) if c and c not in EXCLUDED]
    args.names = names
    examples = Examples(args.src, pathlib.Path(args.examples or pathlib.Path(args.src) / "parity-examples"), data["shadcn"])
    with sync_playwright() as pw:
        browser = getattr(pw, args.engine).launch()
        for comp in comps:
            t0 = time.time()
            docs, ours = Docs(browser, args), Ours(browser, {}, args.drop_slot)
            try:
                results = measure_docs(comp, docs, args, examples)
                conv = measure_ours(comp, results, ours, parts, names, gen_css, args.src, out, docs, examples)
                rows, pairs = compare(comp, results)
                summary = summarize(comp, rows, pairs)
                summary.update({"engine": args.engine, "site": docs.meta, "browser": browser.version, "scenarios": [r["label"] for r in results],
                                "examples": {"roots_with_example": conv.roots["example"], "roots_without": conv.roots["fallback"]},
                                "kept_source": {k: sorted(v) for k, v in sorted(conv.kept_source.items()) if v},
                                "unpinned": {k: sorted(v) for k, v in sorted(conv.unpinned.items()) if v},
                                "nova_page": docs.nova_page, "drop_slot": args.drop_slot, "dropped_rules": ours.dropped,
                                "slotless_hits": {k: {"count": v, "where": dict(conv.where.get(k, {}))} for k, v in conv.hits.items()}, "composed": {f"{a} as {b}": n for (a, b), n in conv.composed.items()}, "errors": ours.errors})
                (out / f"{comp}.json").write_text(json.dumps(summary, indent=1))
                (out / f"{comp}.rows.json").write_text(json.dumps(rows))
                (out / f"{comp}.pairs.json").write_text(json.dumps([{**p, "key": list(k)} for k, p in pairs.items()]))
                if args.keep_raw:
                    (out / f"{comp}.raw.json").write_text(json.dumps(results))
                log(f"{comp}: parts {summary['parts_equal']}/{summary['parts']}, pairs {summary['pairs_equal']}/{summary['pairs']}, values {summary['meaningful_equal']}/{summary['meaningful']}, {len(results)} scenarios, {time.time() - t0:.0f}s")
            except Exception as e:
                log(f"{comp}: FAILED {type(e).__name__}: {str(e)[:300]}")
                (out / f"{comp}.json").write_text(json.dumps({"component": comp, "engine": args.engine, "error": f"{type(e).__name__}: {e}"}))
            finally:
                docs.ctx.close()
                ours.ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
