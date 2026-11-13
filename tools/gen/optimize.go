package main

import (
	"fmt"
	"regexp"
	"slices"
	"strings"
)

type oCompound struct {
	pseudo string
	tag    string
	pos    map[string]bool
	neg    map[string]bool
	attr   map[string]string
	ors    []oOr
}

type oOr struct {
	raw      string
	branches []*oCompound
}

type oAlt struct {
	c    *oCompound
	spec [3]int
	rank int
}

type oRule struct {
	r    *cssRule
	alts []*oAlt
	ro   bool
}

type optimizer struct {
	rules  []*oRule
	byRule map[*cssRule]*oRule
}

var (
	twName    = regexp.MustCompile(`--tw-[\w-]+`)
	attrExact = regexp.MustCompile(`^\[([\w-]+)=["']?([^"'\]]*)["']?\]$`)
	attrHead  = regexp.MustCompile(`^\[([\w-]+)`)
)

func simpleSelectors(s string) []string {
	var out []string
	for i := 0; i < len(s); {
		j := i
		switch c := s[i]; {
		case c == '[':
			for j++; j < len(s) && s[j] != ']'; j++ {
				if s[j] == '"' || s[j] == '\'' {
					if q := strings.IndexByte(s[j+1:], s[j]); q >= 0 {
						j += q + 1
					}
				}
			}
			j++
		case c == ':':
			for j++; j < len(s) && (s[j] == ':' || s[j] == '-' || isIdentPart(s[j])); j++ {
			}
			if j < len(s) && s[j] == '(' {
				for depth := 0; j < len(s); j++ {
					if s[j] == '(' {
						depth++
					} else if s[j] == ')' {
						if depth--; depth == 0 {
							break
						}
					}
				}
				j++
			}
		default:
			for j++; j < len(s) && s[j] != '[' && s[j] != ':' && s[j] != '.' && s[j] != '#'; j++ {
			}
		}
		out = append(out, s[i:min(j, len(s))])
		i = j
	}
	return out
}

func newCompound() *oCompound {
	return &oCompound{pos: map[string]bool{}, neg: map[string]bool{}, attr: map[string]string{}}
}

func functional(tok string) (name, arg string, ok bool) {
	if !strings.HasPrefix(tok, ":") || !strings.HasSuffix(tok, ")") {
		return "", "", false
	}
	name, arg, ok = strings.Cut(tok[1:len(tok)-1], "(")
	return name, arg, ok
}

func normSimple(tok string) string {
	if m := attrExact.FindStringSubmatch(tok); m != nil {
		return "[" + m[1] + "=" + m[2] + "]"
	}
	return tok
}

func (c *oCompound) merge(sel string) {
	sel = strings.TrimSpace(sel)
	subj := subjectCompound(sel)
	if subj != sel {
		c.pos[":where("+sel+")"] = true
	}
	for _, tok := range simpleSelectors(subj) {
		c.add(tok)
	}
}

func (c *oCompound) add(tok string) {
	name, arg, fn := functional(tok)
	switch {
	case strings.HasPrefix(tok, "::"):
		c.pseudo += tok
	case tok == ":before" || tok == ":after":
		c.pseudo += ":" + tok
	case tok[0] == '[':
		c.pos[normSimple(tok)] = true
		if m := attrHead.FindStringSubmatch(tok); m != nil {
			c.pos["["+m[1]+"]"] = true
		}
		if m := attrExact.FindStringSubmatch(tok); m != nil {
			c.attr[m[1]] = m[2]
		}
	case fn && (name == "where" || name == "is"):
		alts := splitTop(arg, ',')
		if len(alts) == 1 {
			c.merge(alts[0])
			return
		}
		or := oOr{raw: ":where(" + arg + ")"}
		for _, a := range alts {
			b := newCompound()
			b.merge(a)
			or.branches = append(or.branches, b)
		}
		c.ors = append(c.ors, or)
	case fn && name == "not":
		for _, a := range notAlts(arg) {
			if s := simpleSelectors(a); len(s) == 1 && subjectCompound(a) == a && !strings.HasPrefix(a, "::") {
				if n, _, f := functional(a); !f || n != "not" {
					c.neg[normSimple(a)] = true
					continue
				}
			}
			c.pos[":not("+a+")"] = true
		}
	case tok[0] == ':' || tok[0] == '.' || tok[0] == '#':
		c.pos[tok] = true
	case tok != "*":
		c.tag = tok
	}
}

func notAlts(arg string) []string {
	var out []string
	for _, a := range splitTop(arg, ',') {
		if n, inner, ok := functional(a); ok && (n == "where" || n == "is") && len(simpleSelectors(a)) == 1 {
			out = append(out, notAlts(inner)...)
			continue
		}
		out = append(out, a)
	}
	return out
}

func disjoint(a, b *oCompound) bool {
	if a.pseudo != b.pseudo {
		return true
	}
	return disjointCore(a, b)
}

func disjointCore(a, b *oCompound) bool {
	if a.tag != "" && b.tag != "" && a.tag != b.tag || a.tag != "" && b.neg[a.tag] || b.tag != "" && a.neg[b.tag] {
		return true
	}
	for k := range a.pos {
		if b.neg[k] {
			return true
		}
	}
	for k := range b.pos {
		if a.neg[k] {
			return true
		}
	}
	for n, v := range a.attr {
		if w, ok := b.attr[n]; ok && w != v {
			return true
		}
	}
	for _, pair := range [][2]*oCompound{{a, b}, {b, a}} {
		for _, or := range pair[0].ors {
			if !slices.ContainsFunc(or.branches, func(br *oCompound) bool { return !disjointCore(br, pair[1]) }) {
				return true
			}
		}
	}
	return false
}

func specificity(sel string) [3]int {
	var s [3]int
	add := func(o [3]int) {
		for i := range s {
			s[i] += o[i]
		}
	}
	maxOf := func(list string) [3]int {
		var best [3]int
		for _, a := range splitTop(list, ',') {
			if v := specificity(a); slices.Compare(v[:], best[:]) > 0 {
				best = v
			}
		}
		return best
	}
	arg := func(i int) (string, int) {
		depth, j := 1, i+1
		for ; depth > 0; j++ {
			switch sel[j] {
			case '(':
				depth++
			case ')':
				depth--
			}
		}
		return sel[i+1 : j-1], j
	}
	word := func(i int) int {
		for i < len(sel) && (isIdentPart(sel[i]) || sel[i] == '-') {
			i++
		}
		return i
	}
	for i := 0; i < len(sel); {
		c := sel[i]
		switch {
		case c == '#':
			s[0]++
			i = word(i + 1)
		case c == '.':
			s[1]++
			i = word(i + 1)
		case c == '[':
			s[1]++
			i += strings.IndexByte(sel[i:], ']') + 1
		case strings.HasPrefix(sel[i:], "::"):
			s[2]++
			i = word(i + 2)
			if i < len(sel) && sel[i] == '(' {
				_, i = arg(i)
			}
		case c == ':':
			j := word(i + 1)
			name := sel[i+1 : j]
			i = j
			if i >= len(sel) || sel[i] != '(' {
				if name == "before" || name == "after" {
					s[2]++
				} else {
					s[1]++
				}
				continue
			}
			a, end := arg(i)
			i = end
			switch name {
			case "where":
			case "is", "not", "has":
				add(maxOf(a))
			case "nth-child", "nth-last-child":
				s[1]++
				if _, of, ok := strings.Cut(a, " of "); ok {
					add(maxOf(of))
				}
			default:
				s[1]++
			}
		case isIdentStart(c):
			s[2]++
			i = word(i)
		default:
			i++
		}
	}
	return s
}

func (o *optimizer) collect(root *cssRule, t *groupTable, ro bool) {
	var walk func(r *cssRule)
	walk = func(r *cssRule) {
		for _, it := range r.items {
			if it.rule == nil {
				continue
			}
			p := it.rule.prelude
			switch {
			case strings.HasPrefix(p, "@property "), strings.HasPrefix(p, "@keyframes"), strings.HasPrefix(p, "@font-face"):
			case strings.HasPrefix(p, "@"):
				walk(it.rule)
			default:
				or := &oRule{r: it.rule, ro: ro}
				for _, a := range splitTop(p, ',') {
					c := newCompound()
					subj := subjectCompound(a)
					for _, tok := range simpleSelectors(subj) {
						c.add(tok)
					}
					rank := -1
					if g, err := t.selectorGroup(a); err == nil {
						rank = t.rank(g)
					}
					or.alts = append(or.alts, &oAlt{c: c, spec: specificity(a), rank: rank})
				}
				o.rules = append(o.rules, or)
			}
		}
	}
	walk(root)
}

func dedupeDecls(r *cssRule) {
	for _, it := range r.items {
		if it.rule != nil {
			dedupeDecls(it.rule)
		}
	}
	last := map[string]int{}
	for i, it := range r.items {
		if it.rule == nil {
			last[it.decl] = i
		}
	}
	i := -1
	r.items = slices.DeleteFunc(r.items, func(it cssItem) bool {
		i++
		return it.rule == nil && last[it.decl] != i
	})
}

func pruneEmpty(r *cssRule, top bool) {
	r.items = slices.DeleteFunc(r.items, func(it cssItem) bool {
		if it.rule == nil {
			return false
		}
		pruneEmpty(it.rule, false)
		return len(it.rule.items) == 0 && !(top && strings.HasPrefix(it.rule.prelude, "@layer "))
	})
}

var (
	propUnions = map[string]string{
		"top": "inset", "right": "inset", "bottom": "inset", "left": "inset",
		"width": "size", "height": "size", "min": "size", "max": "size", "inline": "size", "block": "size",
		"gap": "grid", "row": "grid", "column": "grid", "columns": "grid",
		"place": "align", "justify": "align",
		"line": "font", "white": "text", "word": "overflow",
	}
)

func propFamily(p string) string {
	if strings.HasPrefix(p, "--") {
		return p
	}
	f, _, _ := strings.Cut(strings.TrimPrefix(strings.TrimPrefix(p, "-webkit-"), "-moz-"), "-")
	if u, ok := propUnions[f]; ok {
		return u
	}
	return f
}

func (o *optimizer) leaves(r *cssRule, out []*oRule) []*oRule {
	if l := o.byRule[r]; l != nil {
		return append(out, l)
	}
	for _, it := range r.items {
		if it.rule != nil {
			out = o.leaves(it.rule, out)
		}
	}
	return out
}

func commute(b, t *oRule) bool {
	conflict, same := false, false
	for _, x := range b.r.items {
		for _, y := range t.r.items {
			px, py := declProp(x.decl), declProp(y.decl)
			same = same || px == py
			if fx, fy := propFamily(px), propFamily(py); x.decl != y.decl && (fx == fy || fx == "all" || fy == "all") {
				conflict = true
			}
		}
	}
	if !conflict && !same {
		return true
	}
	for _, ba := range b.alts {
		for _, ta := range t.alts {
			if ba.spec != ta.spec {
				continue
			}
			if ba.rank < 0 || ta.rank < 0 || ba.rank > ta.rank || conflict && !disjoint(ba.c, ta.c) {
				return false
			}
		}
	}
	return true
}

func (o *optimizer) movable(parent *cssRule, i, j int) bool {
	moved := o.leaves(parent.items[j].rule, nil)
	for k := i + 1; k < j; k++ {
		for _, t := range o.leaves(parent.items[k].rule, nil) {
			if slices.ContainsFunc(moved, func(b *oRule) bool { return !commute(b, t) }) {
				return false
			}
		}
	}
	return true
}

func (o *optimizer) mergeEqual(parent *cssRule) int {
	n := 0
	last := map[string]int{}
	for j := 0; j < len(parent.items); j++ {
		b := parent.items[j].rule
		if b == nil {
			clear(last)
			continue
		}
		key := strings.TrimSpace(b.prelude)
		if o.byRule[b] == nil {
			if !strings.HasPrefix(key, "@media ") && !strings.HasPrefix(key, "@supports ") && !strings.HasPrefix(key, "@container ") {
				continue
			}
			var slots []string
			for _, l := range o.leaves(b, nil) {
				for _, x := range subjectSlots(l.r.prelude) {
					if !slices.Contains(slots, x) {
						slots = append(slots, x)
					}
				}
			}
			slices.Sort(slots)
			key += "\x00" + strings.Join(slots, ",")
		}
		i, ok := last[key]
		if !ok || !o.movable(parent, i, j) {
			last[key] = j
			continue
		}
		a := parent.items[i].rule
		a.items = append(a.items, b.items...)
		parent.items = slices.Delete(parent.items, j, j+1)
		j--
		n++
	}
	for _, it := range parent.items {
		if it.rule != nil && o.byRule[it.rule] == nil {
			n += o.mergeEqual(it.rule)
		}
	}
	return n
}

func dropProperties(tree *cssRule, kitCSS string) int {
	used := map[string]bool{}
	for _, m := range twName.FindAllString(kitCSS, -1) {
		used[m] = true
	}
	var walk func(r *cssRule)
	walk = func(r *cssRule) {
		for _, it := range r.items {
			if it.rule == nil {
				for _, m := range twName.FindAllString(it.decl, -1) {
					used[m] = true
				}
			} else if !strings.HasPrefix(it.rule.prelude, "@property ") {
				walk(it.rule)
			}
		}
	}
	walk(tree)
	n := len(tree.items)
	tree.items = slices.DeleteFunc(tree.items, func(it cssItem) bool {
		return it.rule != nil && strings.HasPrefix(it.rule.prelude, "@property --tw-") && !used[strings.TrimSpace(strings.TrimPrefix(it.rule.prelude, "@property "))]
	})
	return n - len(tree.items)
}

func optimizePass(tree, kit *cssRule, kitCSS string, t *groupTable) [2]int {
	o := &optimizer{byRule: map[*cssRule]*oRule{}}
	o.collect(tree, t, false)
	o.collect(kit, t, true)
	dropped := dropProperties(tree, kitCSS)
	dedupeDecls(tree)
	pruneEmpty(tree, true)
	for _, r := range o.rules {
		if !r.ro {
			o.byRule[r.r] = r
		}
	}
	merged := 0
	for _, it := range tree.items {
		if it.rule != nil && strings.HasPrefix(it.rule.prelude, "@layer ") {
			for n := -1; n != 0; merged += n {
				n = o.mergeEqual(it.rule)
			}
		}
	}
	dedupeDecls(tree)
	return [2]int{dropped, merged}
}

func (g *gen) optimize(tree *cssRule, kitCSS string, t *groupTable) error {
	kit, err := parseCSS(kitCSS)
	if err != nil {
		return fmt.Errorf("kit CSS: %w", err)
	}
	var sum [2]int
	for range 20 {
		n := optimizePass(tree, kit, kitCSS, t)
		if n == [2]int{} {
			break
		}
		for i := range sum {
			sum[i] += n[i]
		}
	}
	g.note("@property removed (the variable has no definition and no read)", "%d rules", sum[0])
	g.note("rules with the same selector, or the same condition and part, merged (no rule between them sets a related property on the same element with the same specificity)", "%d rules", sum[1])
	return nil
}
