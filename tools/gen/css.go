package main

import (
	"bytes"
	"fmt"
	"maps"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
)

const license = "/*! clanker-ui | MIT | includes shadcn/ui (MIT, shadcn), Tailwind CSS (MIT, Tailwind Labs), tw-animate-css (MIT, Luca Bosin), and Lucide icons (ISC); see THIRD_PARTY_NOTICES */"

var (
	styleRule    = regexp.MustCompile(`([^{}]+)\{([^{}]*)\}`)
	cnClass      = regexp.MustCompile(`\.(cn-[a-z0-9-]+)`)
	applyLine    = regexp.MustCompile(`@apply\s+([^;]+);`)
	unknownClass = regexp.MustCompile("Cannot apply (?:unknown )?utility class `([^`]+)`")
	groupClass   = regexp.MustCompile(`\.(group|peer)(\\/[A-Za-z0-9_-]+)?`)
	blockComment = regexp.MustCompile(`(?s)/\*.*?\*/\s*`)
	backdropMark = `[data-backdrop-of="`
	themeInline  = regexp.MustCompile(`(?s)(?m)^@theme inline\s*\{(.*?)\n\}`)
	declaration  = regexp.MustCompile(`(?m)^\s*(--[\w-]+)\s*:\s*([^;]+);`)
)

func parseStyles(text string) map[string]string {
	out := map[string]string{}
	for _, m := range styleRule.FindAllStringSubmatch(blockComment.ReplaceAllString(text, ""), -1) {
		var classes []string
		for _, a := range applyLine.FindAllStringSubmatch(m[2], -1) {
			classes = append(classes, strings.TrimSpace(a[1]))
		}
		if len(classes) == 0 {
			continue
		}
		for _, sel := range strings.Split(m[1], ",") {
			cn := cnClass.FindAllStringSubmatch(sel, -1)
			if len(cn) == 0 {
				continue
			}
			last := cnClass.FindAllStringIndex(sel, -1)[len(cn)-1]
			name := cn[len(cn)-1][1]
			joined := strings.Join(classes, " ")
			if pre, post := strings.TrimSpace(sel[:last[0]]), strings.TrimSpace(sel[last[1]:]); pre != "" || post != "" {
				variant := "[" + strings.ReplaceAll(strings.TrimSpace(pre+" &"+post), " ", "_") + "]:"
				var vs []string
				for _, c := range strings.Fields(joined) {
					vs = append(vs, variant+c)
				}
				joined = strings.Join(vs, " ")
			}
			if prev, ok := out[name]; ok {
				joined += " " + prev
			}
			out[name] = joined
		}
	}
	return out
}

type kitMap struct {
	alias    map[string]string
	backdrop map[string]string
}

var slotVariant = regexp.MustCompile(`^data-\[slot=([a-z0-9-]+)\]:$`)

func (g *gen) slotAliases(k kitMap) kitMap {
	alias := maps.Clone(k.alias)
	if alias == nil {
		alias = map[string]string{}
	}
	extra := map[string][]string{}
	for _, p := range g.parts {
		if p.sel != "" || p.slot == "" {
			continue
		}
		for _, l := range p.layers {
			for _, c := range l.classes {
				segs := splitTopColon(c)
				for _, seg := range segs[:len(segs)-1] {
					if seg == "*" || seg == "**" || strings.HasPrefix(seg, "[") {
						break
					}
					m := slotVariant.FindStringSubmatch(seg + ":")
					if m != nil && m[1] != p.slot && !slices.Contains(extra[p.slot], m[1]) {
						extra[p.slot] = append(extra[p.slot], m[1])
					}
				}
			}
		}
	}
	for _, slot := range sortedKeys(extra) {
		if _, ok := alias[slot]; ok {
			continue
		}
		sels := []string{fmt.Sprintf(`[data-slot="%s"]`, slot)}
		for _, x := range extra[slot] {
			sels = append(sels, fmt.Sprintf(`[data-slot="%s"]`, x))
			g.note("slot renamed by a data-[slot=...] variant (the element keeps the look of its part)", "%s also matches data-slot=%s", slot, x)
		}
		alias[slot] = ":is(" + strings.Join(sels, ", ") + ")"
	}
	return kitMap{alias: alias, backdrop: k.backdrop}
}

func (k kitMap) slot(slot string) string {
	if of, ok := k.backdrop[slot]; ok {
		return backdropMark + of + `"]`
	}
	if a, ok := k.alias[slot]; ok {
		return a
	}
	return fmt.Sprintf(`[data-slot="%s"]`, slot)
}

func (k kitMap) selector(p *part) string {
	if p.sel != "" {
		return p.sel
	}
	sel := k.slot(p.slot)
	if p.key != "" {
		sel += ":where(" + p.key + ")"
	}
	if p.marker != "" {
		sel += ":where([" + p.marker + "])"
	}
	if p.context != "" && p.child {
		sel = ":where(" + p.context + ") > " + sel
	} else if p.context != "" {
		sel = ":where(" + p.context + ") " + sel
	}
	if p.suffix != "" {
		sel = ":where(" + sel + ") " + p.suffix
	}
	return sel
}

func (g *gen) emitComponents(k kitMap, prim map[string]string, drop map[string]bool) string {
	var b strings.Builder
	b.WriteString(g.boxlessCSS(k))
	ordered := slices.Clone(g.parts)
	slices.SortStableFunc(ordered, func(x, y *part) int {
		return rank(x) - rank(y)
	})
	emit := func(p *part, keep func(string) bool) {
		sel := k.selector(p)
		for _, r := range g.rules(p, prim, drop) {
			var cls []string
			for _, c := range r.classes {
				if keep(c) {
					cls = append(cls, c)
				}
			}
			if len(cls) > 0 {
				fmt.Fprintf(&b, "  %s%s {\n    @apply %s;\n  }\n", sel, r.cond, strings.Join(cls, " "))
			}
		}
	}
	plain := func(c string) bool { return variantChain(strings.Trim(c, "!")) == "" }
	variant := func(c string) bool { return !plain(c) }
	all := func(string) bool { return true }
	for _, keep := range []func(string) bool{plain, variant} {
		for _, p := range ordered {
			if rank(p) == 0 {
				emit(p, keep)
			}
		}
	}
	for _, p := range ordered {
		if rank(p) != 0 {
			emit(p, all)
		}
	}
	return b.String()
}

func (g *gen) boxlessCSS(k kitMap) string {
	if len(g.boxless) == 0 {
		return ""
	}
	var sels []string
	for _, s := range g.boxless {
		sels = append(sels, k.slot(s))
	}
	g.note("element without a box (Base UI renders no DOM)", "%s", strings.Join(g.boxless, ", "))
	return "  :where(" + strings.Join(sels, ", ") + ") { display: contents; }\n"
}

func rank(p *part) int {
	if p.context != "" || p.suffix != "" || p.marker != "" || p.sel != "" {
		return 1
	}
	return 0
}

func (g *gen) groupOwners(k kitMap) map[string][]string {
	owners := map[string][]string{}
	for _, p := range g.parts {
		sel := k.slot(p.slot)
		if p.sel != "" {
			sel = p.sel
		}
		if p.key != "" {
			sel += ":where(" + p.key + ")"
		}
		if p.marker != "" {
			sel += ":where([" + p.marker + "])"
		}
		for _, grp := range p.groups {
			name := `.` + strings.Replace(grp, "/", `\/`, 1)
			if !slices.Contains(owners[name], sel) {
				owners[name] = append(owners[name], sel)
			}
		}
	}
	return owners
}

func parseTheme(src, name string) ([][2]string, [][2]string, error) {
	i := strings.Index(src, `name: "`+name+`"`)
	if i < 0 {
		return nil, nil, fmt.Errorf("%s: no theme %q", themesFile, name)
	}
	j := strings.Index(src[i:], "cssVars:")
	if j < 0 {
		return nil, nil, fmt.Errorf("%s: theme %q has no cssVars", themesFile, name)
	}
	open := strings.IndexByte(src[i+j:], '{')
	if open < 0 {
		return nil, nil, fmt.Errorf("%s: theme %q: cssVars is not an object", themesFile, name)
	}
	open += i + j
	end, err := matchFrom(src, open)
	if err != nil {
		return nil, nil, fmt.Errorf("%s: %w", themesFile, err)
	}
	vars, err := parseObject(src[open:end])
	if err != nil {
		return nil, nil, fmt.Errorf("%s: %w", themesFile, err)
	}
	modes := map[string][][2]string{}
	for _, mode := range vars {
		obj, err := parseObject(mode[1])
		if err != nil {
			return nil, nil, fmt.Errorf("%s: %s: %w", themesFile, mode[0], err)
		}
		for _, kv := range obj {
			v, ok := stringLiteral(kv[1])
			where := fmt.Sprintf("%s %s.%s.%s", themesFile, name, mode[0], kv[0])
			if !ok || !tokenKey.MatchString(kv[0]) {
				return nil, nil, unsafeInput{where, "want a lowercase key and a string value"}
			}
			if err := checkValue(where, v); err != nil {
				return nil, nil, err
			}
			modes[mode[0]] = append(modes[mode[0]], [2]string{kv[0], v})
		}
	}
	if len(modes["light"]) == 0 || len(modes["dark"]) == 0 {
		return nil, nil, fmt.Errorf("%s: theme %q needs light and dark cssVars", themesFile, name)
	}
	return modes["light"], modes["dark"], nil
}

func tokensCSS(light, dark [][2]string) string {
	decls := func(kvs [][2]string, indent string) string {
		var out []string
		for _, kv := range kvs {
			out = append(out, fmt.Sprintf("%s--%s: %s;", indent, kv[0], kv[1]))
		}
		return strings.Join(out, "\n")
	}
	var b strings.Builder
	b.WriteString("@layer clanker.tokens {\n")
	fmt.Fprintf(&b, "  :root {\n    color-scheme: light dark;\n%s\n  }\n", decls(light, "    "))
	b.WriteString("  [data-theme=\"light\"] { color-scheme: light; }\n")
	fmt.Fprintf(&b, "  [data-theme=\"dark\"] {\n    color-scheme: dark;\n%s\n  }\n", decls(dark, "    "))
	fmt.Fprintf(&b, "  @media (prefers-color-scheme: dark) {\n    :root:not([data-theme=\"light\"]) {\n%s\n    }\n  }\n", decls(dark, "      "))
	b.WriteString("}\n")
	return b.String()
}

var varRef = regexp.MustCompile(`^var\((--[\w-]+)\)$`)

func themeCSS(globals string, defined map[string]bool) (string, error) {
	m := themeInline.FindStringSubmatch(globals)
	if m == nil {
		return "", fmt.Errorf("globals.css: no @theme inline block")
	}
	var keep []string
	for _, d := range declaration.FindAllStringSubmatch(m[1], -1) {
		name, value := d[1], strings.TrimSpace(d[2])
		if err := checkValue(globalsFile+" @theme inline "+name, value); err != nil {
			return "", err
		}
		if strings.HasPrefix(name, "--font-") || strings.HasPrefix(name, "--breakpoint-") {
			continue
		}
		if r := varRef.FindStringSubmatch(value); r != nil && !defined[r[1]] {
			continue
		}
		keep = append(keep, fmt.Sprintf("  %s: %s;", name, value))
	}
	return "@theme inline {\n" + strings.Join(keep, "\n") + "\n}\n", nil
}

func variantsCSS(shadcnTailwind string) string {
	return blockComment.ReplaceAllString(shadcnTailwind, "") + "\n"
}

const darkVariant = `@custom-variant dark {
  &:is([data-theme="dark"] *) { @slot; }
  @media (prefers-color-scheme: dark) { &:not([data-theme="light"] *) { @slot; } }
}
@custom-variant rtl (&:where(:dir(rtl)));
@custom-variant ltr (&:where(:dir(ltr)));
`

const glue = `@layer clanker.base {
  * { @apply border-border outline-ring/50; }
  body { @apply bg-background text-foreground; }
  :where(dialog[data-slot]:not([open]), [data-slot][popover]:not(:popover-open)) { display: none !important; }
  dialog { inset: auto; width: auto; height: auto; max-width: none; max-height: none; overflow: visible; background-color: transparent; color: inherit; }
}
@layer clanker.components {
  :is([data-slot="dialog-content"], [data-slot="alert-dialog-content"], [data-slot="sheet-content"], [data-slot="drawer-content"]) > form:is(:not([data-slot]), [data-slot="form"]) { display: contents; }
  [data-state="unchecked"] > [data-slot="dropdown-menu-item-indicator"] > svg { display: none; }
}
@layer clanker.utilities {
  .sr-only { @apply sr-only; }
  .shimmer { @apply shimmer; }
  .shimmer-once { @apply shimmer-once; }
  .shimmer-reverse { @apply shimmer-reverse; }
  .shimmer-none { @apply shimmer-none; }
  @media (prefers-reduced-motion: reduce) {
    *, ::before, ::after, ::backdrop { animation: none; transition: none; scroll-behavior: auto; }
  }
}
`

type inputs struct {
	tokens, theme, variants, animateCSS, components string
}

const (
	importTheme     = `@import "tailwindcss/theme.css" layer(clanker.tokens);`
	importPreflight = `@import "tailwindcss/preflight.css" layer(clanker.base);`
	importUtilities = `@import "tailwindcss/utilities.css" layer(clanker.utilities) source(none);`
	importAnimate   = `@import "./tw-animate.css";`
	layerOrder      = "@layer properties, clanker.tokens, clanker.themes, clanker.base, clanker.components, clanker.utilities;\n"
)

var generatedImports = []string{importTheme, importPreflight, importAnimate}

func (in inputs) writeAnimate(dir string) error {
	return os.WriteFile(filepath.Join(dir, "tw-animate.css"), []byte(in.animateCSS), 0o644)
}

func (in inputs) preamble() string {
	return importTheme + "\n" + importAnimate + "\n" + in.variants + darkVariant + in.theme
}

func (in inputs) css() string {
	css := layerOrder + importPreflight + "\n" + in.preamble() + in.tokens + glue +
		"@layer clanker.components {\n" + in.components + "}\n"
	return css
}

var kitLayerNames = []string{"clanker.tokens", "clanker.themes", "clanker.base", "clanker.components", "clanker.utilities"}

var tailwindOnly = regexp.MustCompile(`(?i)@(apply|theme|utility|custom-variant|variant|slot|reference|tailwind)\b`)

func checkKit(path, kit string) error {
	if m := tailwindOnly.FindString(kit); m != "" {
		return fmt.Errorf("%s: %s needs Tailwind; kit.css is plain CSS that the generator appends as it is", path, m)
	}
	tree, err := parseCSS(kit)
	if err != nil {
		return fmt.Errorf("%s: %w", path, err)
	}
	for _, it := range tree.items {
		name, ok := "", it.rule != nil && strings.HasPrefix(it.rule.prelude, "@layer ")
		if ok {
			name = strings.TrimSpace(strings.TrimPrefix(it.rule.prelude, "@layer "))
		}
		if it.rule != nil && (strings.HasPrefix(it.rule.prelude, "@property ") || strings.HasPrefix(it.rule.prelude, "@keyframes ")) {
			continue
		}
		if !ok || !slices.Contains(kitLayerNames, name) {
			what := it.decl
			if it.rule != nil {
				what = it.rule.prelude
			}
			return fmt.Errorf("%s: %q is not in a kit layer; put every rule in @layer %s (@property and @keyframes may stay outside)", path, what, strings.Join(kitLayerNames, ", @layer "))
		}
	}
	return nil
}

func compile(tailwind, dir, input string, imports ...string) (string, string, error) {
	if err := checkCSS("tailwind input", input, append(slices.Clone(generatedImports), imports...)); err != nil {
		return "", "", err
	}
	in := dir + "/input.css"
	out := dir + "/output.css"
	if err := os.WriteFile(in, []byte(input), 0o644); err != nil {
		return "", "", err
	}
	cmd := exec.Command(tailwind, "--input", in, "--output", out, "--optimize")
	cmd.Dir = dir
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return "", stderr.String(), err
	}
	b, err := os.ReadFile(out)
	return string(b), stderr.String(), err
}

var rdpClass = regexp.MustCompile(`\.rdp-([a-z_]+)\b`)

func (g *gen) rdpSelectors() map[string]string {
	out := map[string]string{}
	for key, sel := range g.manual {
		_, name, ok := strings.Cut(key, "/classNames.")
		if !ok || sel == "-" || strings.Contains(sel, "&") {
			continue
		}
		out[name] = sel
	}
	return out
}

var dirAttr = regexp.MustCompile(`:where\((?::dir\((?:rtl|ltr)\),\s*)?\[dir="?(rtl|ltr)"?\](?:,\s*\[dir="?(?:rtl|ltr)"?\]\s*\*)?\)`)

var hasAttr = regexp.MustCompile(`:has\(( > )?\[(data-variant|data-size)=("[^"]*"|[^\]"]*)\]\)`)

func (g *gen) attrRenderers(attr string) []string {
	var out []string
	for _, name := range sortedKeys(g.sources) {
		s := g.sources[name]
		for _, fname := range s.order {
			for _, e := range s.funcs[fname].elems {
				if slot, ok := literalSlot(e); ok && e.get(attr) != nil {
					if sel := fmt.Sprintf(`[data-slot="%s"]`, slot); !slices.Contains(out, sel) {
						out = append(out, sel)
					}
				}
			}
		}
	}
	slices.Sort(out)
	return out
}

func postprocess(css string, owners map[string][]string, k kitMap, g *gen) string {
	css = blockComment.ReplaceAllString(css, "")
	css = hasAttr.ReplaceAllStringFunc(css, func(m string) string {
		sub := hasAttr.FindStringSubmatch(m)
		slots := g.attrRenderers(sub[2])
		if len(slots) == 0 {
			return m
		}
		g.note("has() of a variant attribute limited to the parts that render it in shadcn (kit buttons also set it)", "%s -> %d parts", m, len(slots))
		return ":has(" + sub[1] + ":is(" + strings.Join(slots, ", ") + ")[" + sub[2] + "=" + sub[3] + "])"
	})
	if n := len(dirAttr.FindAllString(css, -1)); n > 0 {
		css = dirAttr.ReplaceAllString(css, ":where(:dir($1))")
		g.note("direction selector made :dir() only (an ltr area in an rtl page stays ltr)", "%d selectors", n)
	}
	rdp := g.rdpSelectors()
	css = rdpClass.ReplaceAllStringFunc(css, func(m string) string {
		if sel, ok := rdp[m[len(".rdp-"):]]; ok {
			g.note("react-day-picker class mapped to the kit slot", "%s -> %s", m, sel)
			return sel
		}
		return m
	})
	css = groupClass.ReplaceAllStringFunc(css, func(m string) string {
		sel := owners[m]
		switch len(sel) {
		case 0:
			g.note("group or peer without an owner", "%s", strings.ReplaceAll(m, `\/`, "/"))
			return m
		case 1:
			return sel[0]
		}
		return ":is(" + strings.Join(sel, ", ") + ")"
	})
	lines := strings.Split(css, "\n")
	for i, line := range lines {
		if !strings.Contains(line, backdropMark) || !strings.HasSuffix(line, "{") {
			continue
		}
		indent := line[:len(line)-len(strings.TrimLeft(line, " "))]
		prelude := strings.TrimSpace(strings.TrimSuffix(line, "{"))
		var sels []string
		for _, s := range splitTop(prelude, ',') {
			if j := strings.Index(s, backdropMark); j >= 0 {
				end := strings.Index(s[j:], `"]`) + j
				of := s[j+len(backdropMark) : end]
				s = s[:j] + `[data-slot="` + of + `"]` + s[end+2:] + "::backdrop"
			}
			sels = append(sels, s)
		}
		lines[i] = indent + strings.Join(sels, ", ") + " {"
	}
	return license + "\n" + strings.TrimLeft(strings.Join(lines, "\n"), "\n")
}
