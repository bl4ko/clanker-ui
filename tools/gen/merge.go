package main

import (
	"fmt"
	"regexp"
	"slices"
	"strconv"
	"strings"
)

type rule struct {
	cond    string
	classes []string
}

var (
	probeRule = regexp.MustCompile(`([^{}@;]+)\{([^{}]*)\}`)
	probeID   = regexp.MustCompile(`\[data-cls="(\d+)"\]`)
)

func (g *gen) allClasses() []string {
	var out []string
	seen := map[string]bool{}
	for _, p := range g.parts {
		for _, l := range p.layers {
			for _, c := range l.classes {
				if !seen[c] {
					seen[c] = true
					out = append(out, c)
				}
			}
		}
	}
	return out
}

func probeCSS(classes []string, drop map[string]bool) string {
	var b strings.Builder
	b.WriteString("@layer probe {\n")
	for i, c := range classes {
		if !drop[c] {
			fmt.Fprintf(&b, "  [data-cls=\"%d\"] { @apply %s; }\n", i, c)
		}
	}
	b.WriteString("}\n")
	return b.String()
}

func primaries(compiled string, classes []string) map[string]string {
	out := map[string]string{}
	for _, m := range probeRule.FindAllStringSubmatch(compiled, -1) {
		first := ""
		for _, decl := range strings.Split(m[2], ";") {
			prop, val, ok := strings.Cut(strings.TrimSpace(decl), ":")
			if !ok || prop == "" || strings.TrimSpace(prop) == "content" && strings.TrimSpace(val) == "var(--tw-content)" {
				continue
			}
			first = strings.TrimSpace(prop)
			break
		}
		for _, id := range probeID.FindAllStringSubmatch(m[1], -1) {
			i, _ := strconv.Atoi(id[1])
			if _, ok := out[classes[i]]; !ok && first != "" {
				out[classes[i]] = first
			}
		}
	}
	return out
}

func propSets(compiled string, classes []string) map[string][]string {
	out := map[string][]string{}
	for _, m := range probeRule.FindAllStringSubmatch(compiled, -1) {
		var props []string
		for _, decl := range strings.Split(m[2], ";") {
			prop, val, ok := strings.Cut(strings.TrimSpace(decl), ":")
			prop = strings.TrimSpace(prop)
			if !ok || prop == "" || prop == "content" && strings.TrimSpace(val) == "var(--tw-content)" || prop == "--tw-leading" || prop == "--tw-font-weight" || prop == "--tw-tracking" {
				continue
			}
			props = append(props, prop)
		}
		for _, id := range probeID.FindAllStringSubmatch(m[1], -1) {
			i, _ := strconv.Atoi(id[1])
			for _, p := range props {
				if !slices.Contains(out[classes[i]], p) {
					out[classes[i]] = append(out[classes[i]], p)
				}
			}
		}
	}
	return out
}

var shorthands = map[string][]string{
	"padding":        {"padding-top", "padding-right", "padding-bottom", "padding-left", "padding-inline", "padding-block", "padding-inline-start", "padding-inline-end", "padding-block-start", "padding-block-end"},
	"padding-inline": {"padding-left", "padding-right", "padding-inline-start", "padding-inline-end"},
	"padding-block":  {"padding-top", "padding-bottom", "padding-block-start", "padding-block-end"},
	"margin":         {"margin-top", "margin-right", "margin-bottom", "margin-left", "margin-inline", "margin-block", "margin-inline-start", "margin-inline-end", "margin-block-start", "margin-block-end"},
	"margin-inline":  {"margin-left", "margin-right", "margin-inline-start", "margin-inline-end"},
	"margin-block":   {"margin-top", "margin-bottom", "margin-block-start", "margin-block-end"},
	"inset":          {"top", "right", "bottom", "left", "inset-inline", "inset-block", "inset-inline-start", "inset-inline-end", "inset-block-start", "inset-block-end"},
	"inset-inline":   {"left", "right", "inset-inline-start", "inset-inline-end"},
	"inset-block":    {"top", "bottom", "inset-block-start", "inset-block-end"},
	"gap":            {"row-gap", "column-gap"},
	"overflow":       {"overflow-x", "overflow-y"},
	"border-radius":  {"border-top-left-radius", "border-top-right-radius", "border-bottom-right-radius", "border-bottom-left-radius", "border-start-start-radius", "border-start-end-radius", "border-end-start-radius", "border-end-end-radius"},
	"border-width":   {"border-top-width", "border-right-width", "border-bottom-width", "border-left-width", "border-inline-width", "border-block-width", "border-inline-start-width", "border-inline-end-width"},
	"border-color":   {"border-top-color", "border-right-color", "border-bottom-color", "border-left-color", "border-inline-color", "border-block-color", "border-inline-start-color", "border-inline-end-color"},
}

func covers(later, earlier []string) bool {
	if len(earlier) == 0 || len(later) == 0 {
		return false
	}
	set := map[string]bool{}
	for _, p := range later {
		set[p] = true
		for _, l := range shorthands[p] {
			set[l] = true
		}
	}
	for _, p := range earlier {
		if !set[p] {
			return false
		}
	}
	return true
}

func variantChain(class string) string {
	depth, last := 0, -1
	for i, r := range class {
		switch r {
		case '[', '(':
			depth++
		case ']', ')':
			depth--
		case ':':
			if depth == 0 {
				last = i
			}
		}
	}
	if last < 0 {
		return ""
	}
	return class[:last]
}

var orderSensitive = map[string]bool{"*": true, "**": true, "after": true, "backdrop": true, "before": true, "details-content": true, "file": true, "first-letter": true, "first-line": true, "marker": true, "placeholder": true, "selection": true}

func splitTopColon(chain string) []string {
	var out []string
	depth, last := 0, 0
	for i, r := range chain {
		switch r {
		case '[', '(':
			depth++
		case ']', ')':
			depth--
		case ':':
			if depth == 0 {
				out = append(out, chain[last:i])
				last = i + 1
			}
		}
	}
	return append(out, chain[last:])
}

func mergeChain(class string) string {
	imp := ""
	if strings.HasPrefix(class, "!") || strings.HasSuffix(class, "!") {
		imp = "!"
	}
	chain := variantChain(strings.Trim(class, "!"))
	if chain == "" {
		return imp
	}
	var sorted, run []string
	for _, m := range splitTopColon(chain) {
		if strings.HasPrefix(m, "[") || orderSensitive[m] {
			slices.Sort(run)
			sorted = append(append(sorted, run...), m)
			run = nil
			continue
		}
		run = append(run, m)
	}
	slices.Sort(run)
	return strings.Join(append(sorted, run...), ":") + imp
}

func groupKey(class string, prim map[string]string) (string, bool) {
	p, ok := prim[class]
	if !ok {
		return "", false
	}
	return mergeChain(class) + "|" + p, true
}

func twMerge(classes []string, prim map[string]string, props map[string][]string) ([]string, []string) {
	seen := map[string]string{}
	var keep, dropped []string
	for i := len(classes) - 1; i >= 0; i-- {
		c := classes[i]
		if k, ok := groupKey(c, prim); ok {
			if later, dup := seen[k]; dup && (props == nil || prim[c] == "font-size" || covers(props[later], props[c])) {
				dropped = append(dropped, c)
				continue
			}
			if _, dup := seen[k]; !dup {
				seen[k] = c
			}
		}
		chain := mergeChain(c)
		if slices.ContainsFunc(keep, func(d string) bool { return mergeChain(d) == chain && covers(props[d], props[c]) }) {
			dropped = append(dropped, c)
			continue
		}
		keep = append(keep, c)
	}
	slices.Reverse(keep)
	return keep, dropped
}

func (g *gen) rules(p *part, prim map[string]string, drop map[string]bool) []rule {
	var conds []string
	byCond := map[string][]string{}
	pos := map[string]map[string]int{}
	n := 0
	for _, l := range p.layers {
		if _, ok := byCond[l.cond]; !ok {
			conds = append(conds, l.cond)
			pos[l.cond] = map[string]int{}
		}
		for _, c := range l.classes {
			if !drop[c] {
				byCond[l.cond] = append(byCond[l.cond], c)
				pos[l.cond][c] = n
				n++
			}
		}
	}
	merged := map[string][]string{}
	for _, cond := range conds {
		m, dropped := twMerge(byCond[cond], prim, g.props)
		merged[cond] = m
		for _, d := range dropped {
			g.note("class removed like tailwind-merge", "%s: %s", p.slot+cond, d)
		}
	}
	var base []string
	moved := map[string][]string{}
	beaten := map[string]map[string]bool{}
	for _, c := range merged[""] {
		k, ok := groupKey(c, prim)
		var over []string
		for _, other := range conds {
			if other == "" || !ok {
				continue
			}
			later := false
			for _, x := range merged[other] {
				if kx, okx := groupKey(x, prim); okx && kx == k {
					if pos[other][x] > pos[""][c] {
						later = later || g.props == nil || prim[c] == "font-size" || covers(g.props[x], g.props[c])
					} else {
						if beaten[other] == nil {
							beaten[other] = map[string]bool{}
						}
						beaten[other][x] = true
						g.note("class removed like tailwind-merge", "%s: %s (a later base class wins)", p.slot+other, x)
					}
				}
			}
			if later {
				over = append(over, other)
			}
		}
		if len(over) == 0 {
			base = append(base, c)
			continue
		}
		not := ":not(" + strings.Join(over, ", ") + ")"
		moved[not] = append(moved[not], c)
		g.note("class removed like tailwind-merge", "%s: %s only where %s", p.slot, c, not)
	}
	var out []rule
	for _, cond := range conds {
		if cond == "" {
			out = append(out, rule{"", base})
			for _, not := range sortedKeys(moved) {
				out = append(out, rule{not, moved[not]})
			}
			continue
		}
		var keep []string
		for _, x := range merged[cond] {
			if !beaten[cond][x] {
				keep = append(keep, x)
			}
		}
		out = append(out, rule{cond, keep})
	}
	return out
}
