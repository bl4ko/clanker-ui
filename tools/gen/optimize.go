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
	anc  string
	spec [3]int
	rank int
}

type oRule struct {
	r      *cssRule
	parent *cssRule
	layer  int
	conds  []string
	alts   []*oAlt
	order  int
	ro     bool
}

type oProp struct {
	initial string
	has     bool
	typed   bool
}

type optimizer struct {
	rules    []*oRule
	props    map[string]oProp
	skip     map[string]bool
	defs     map[string][]*oRule
	byRule   map[*cssRule]*oRule
	resolved int
	dead     int
}

var (
	twVar      = regexp.MustCompile(`var\(\s*(--tw-[\w-]+)`)
	attrExact  = regexp.MustCompile(`^\[([\w-]+)=["']?([^"'\]]*)["']?\]$`)
	attrHead   = regexp.MustCompile(`^\[([\w-]+)`)
	zeroCalc   = regexp.MustCompile(`calc\(((?:\d+\.?\d*|\.\d+)[a-z]+) \+ 0px\)`)
	spaces     = regexp.MustCompile(`\s+`)
	publicTw   = []string{"--tw-enter-", "--tw-exit-"}
	layerRanks = func() map[string]int {
		m := map[string]int{}
		list := strings.TrimSuffix(strings.TrimPrefix(strings.TrimSpace(layerOrder), "@layer "), ";")
		for i, n := range strings.Split(list, ",") {
			m[strings.TrimSpace(n)] = i + 1
		}
		return m
	}()
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

func implies(a, b *oCompound) bool {
	return a.pseudo == b.pseudo && impliesCore(a, b)
}

func impliesCore(a, b *oCompound) bool {
	if b.tag != "" && a.tag != b.tag {
		return false
	}
	for k := range b.pos {
		if !a.pos[k] {
			return false
		}
	}
	for k := range b.neg {
		if a.neg[k] {
			continue
		}
		if m := attrExact.FindStringSubmatch(k); m != nil {
			if v, ok := a.attr[m[1]]; ok && v != m[2] || a.neg["["+m[1]+"]"] {
				continue
			}
		}
		return false
	}
	for _, or := range b.ors {
		if slices.ContainsFunc(a.ors, func(o oOr) bool { return o.raw == or.raw }) {
			continue
		}
		if !slices.ContainsFunc(or.branches, func(br *oCompound) bool { return impliesCore(a, br) }) {
			return false
		}
	}
	return true
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
	var walk func(r *cssRule, layer string, conds []string)
	walk = func(r *cssRule, layer string, conds []string) {
		for _, it := range r.items {
			if it.rule == nil {
				continue
			}
			p := it.rule.prelude
			switch {
			case strings.HasPrefix(p, "@property "):
				o.property(it.rule)
			case strings.HasPrefix(p, "@keyframes"), strings.HasPrefix(p, "@font-face"):
				for _, m := range twVar.FindAllStringSubmatch(it.rule.String(), -1) {
					o.skip[m[1]] = true
				}
			case strings.HasPrefix(p, "@layer "):
				name := strings.TrimSpace(strings.TrimPrefix(p, "@layer "))
				if layer != "" {
					name = layer + "." + name
				}
				walk(it.rule, name, conds)
			case strings.HasPrefix(p, "@"):
				walk(it.rule, layer, append(slices.Clone(conds), p))
			default:
				or := &oRule{r: it.rule, parent: r, layer: layerRanks[layer], conds: conds, order: len(o.rules), ro: ro}
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
					or.alts = append(or.alts, &oAlt{c: c, anc: strings.TrimSpace(strings.TrimSuffix(a, subj)), spec: specificity(a), rank: rank})
				}
				o.rules = append(o.rules, or)
			}
		}
	}
	walk(root, "", nil)
}

func (o *optimizer) property(r *cssRule) {
	name := strings.TrimSpace(strings.TrimPrefix(r.prelude, "@property "))
	var p oProp
	inherits, syntax := true, ""
	for _, it := range r.items {
		k, v, _ := strings.Cut(it.decl, ":")
		v = strings.TrimSpace(v)
		switch strings.TrimSpace(k) {
		case "inherits":
			inherits = v != "false"
		case "initial-value":
			p.initial, p.has = v, true
		case "syntax":
			syntax = strings.Trim(v, `"'`)
		}
	}
	p.typed = syntax != "*"
	if syntax == "<length>" && p.initial == "0" {
		p.initial = "0px"
	}
	if inherits {
		o.skip[name] = true
	}
	o.props[name] = p
}

func declValue(d string) string {
	_, v, _ := strings.Cut(d, ":")
	return strings.TrimSpace(strings.TrimSuffix(strings.TrimSpace(v), "!important"))
}

func important(d string) bool { return strings.HasSuffix(d, "!important") }

func wins(x *oRule, xa *oAlt, xd string, y *oRule, yd string) bool {
	if important(xd) != important(yd) {
		return important(xd)
	}
	return !important(xd) && beats(x, xa, y)
}

func (o *optimizer) index() {
	o.defs = map[string][]*oRule{}
	for _, r := range o.rules {
		seen := map[string]bool{}
		for _, it := range r.r.items {
			p := declProp(it.decl)
			if it.rule != nil || !strings.HasPrefix(p, "--tw-") {
				continue
			}
			if seen[p] {
				o.skip[p] = true
			}
			if !seen[p] {
				o.defs[p] = append(o.defs[p], r)
			}
			seen[p] = true
		}
	}
}

func (r *oRule) decl(prop string) (string, bool) {
	for i := len(r.r.items) - 1; i >= 0; i-- {
		if it := r.r.items[i]; it.rule == nil && declProp(it.decl) == prop {
			return it.decl, true
		}
	}
	return "", false
}

func before(x, y *oRule, xa, ya *oAlt) bool {
	return x.order < y.order && xa.rank >= 0 && xa.rank <= ya.rank
}

func beats(x *oRule, xa *oAlt, y *oRule) bool {
	if x.layer == 0 || y.layer == 0 {
		return false
	}
	if x.layer != y.layer {
		return x.layer > y.layer
	}
	for _, ya := range y.alts {
		if disjoint(xa.c, ya.c) {
			continue
		}
		switch c := slices.Compare(xa.spec[:], ya.spec[:]); {
		case c < 0, c == 0 && !before(y, x, ya, xa):
			return false
		}
	}
	return true
}

func impliesRule(r *oRule, a *oAlt, c *oRule, ca *oAlt) bool {
	for _, cond := range c.conds {
		if !slices.Contains(r.conds, cond) {
			return false
		}
	}
	return (ca.anc == "" || ca.anc == a.anc) && implies(a.c, ca.c)
}

func (o *optimizer) value(r *oRule, a *oAlt, v, prop, fallback string, hasFallback bool) (string, bool) {
	type cand struct {
		r *oRule
		a *oAlt
		d string
	}
	var cands, bases []cand
	for _, c := range o.defs[v] {
		d, _ := c.decl(v)
		for _, ca := range c.alts {
			if c == r && ca == a {
				bases = []cand{{c, ca, d}}
			} else if c != r && !disjoint(a.c, ca.c) {
				cands = append(cands, cand{c, ca, d})
			}
		}
	}
	base, ok := "", false
	if len(bases) == 0 {
		for _, c := range cands {
			if impliesRule(r, a, c.r, c.a) {
				bases = append(bases, c)
			}
		}
	}
	for _, b := range bases {
		if declValue(b.d) != declValue(bases[0].d) {
			return "", false
		}
	}
	switch p := o.props[v]; {
	case len(bases) > 0:
		base, ok = declValue(bases[0].d), true
	case p.has:
		base, ok = p.initial, true
	case hasFallback:
		base, ok = fallback, true
	}
	if !ok {
		return "", false
	}
	own, _ := r.decl(prop)
	for _, c := range cands {
		if declValue(c.d) == base {
			continue
		}
		if slices.ContainsFunc(bases, func(b cand) bool { return wins(b.r, b.a, b.d, c.r, c.d) }) {
			continue
		}
		if other, has := c.r.decl(prop); has && wins(c.r, c.a, other, r, own) {
			continue
		}
		return "", false
	}
	return base, true
}

func varRefs(value string) [][2]int {
	var out [][2]int
	for _, loc := range twVar.FindAllStringIndex(value, -1) {
		depth, j := 0, loc[0]+3
		for ; j < len(value); j++ {
			if value[j] == '(' {
				depth++
			} else if value[j] == ')' {
				if depth--; depth == 0 {
					break
				}
			}
		}
		if len(out) > 0 && loc[0] < out[len(out)-1][1] {
			continue
		}
		out = append(out, [2]int{loc[0], j + 1})
	}
	return out
}

func (o *optimizer) public(v string) bool {
	return o.skip[v] || slices.ContainsFunc(publicTw, func(p string) bool { return strings.HasPrefix(v, p) })
}

func (o *optimizer) resolve() bool {
	changed := false
	for _, r := range o.rules {
		if r.ro {
			continue
		}
		for i, it := range r.r.items {
			if it.rule != nil || !strings.Contains(it.decl, "var(--tw-") {
				continue
			}
			prop, value := declProp(it.decl), declValue(it.decl)
			refs := varRefs(value)
			out := value
			for k := len(refs) - 1; k >= 0; k-- {
				ref := value[refs[k][0]:refs[k][1]]
				name, fallback, hasFallback := strings.Cut(ref[4:len(ref)-1], ",")
				name, fallback = strings.TrimSpace(name), strings.TrimSpace(fallback)
				if _, registered := o.props[name]; !registered || o.public(name) || len(o.defs[name]) > 0 && (o.props[name].typed || strings.HasPrefix(prop, "--tw-") && !o.public(prop)) {
					continue
				}
				val, ok := "", true
				for n, a := range r.alts {
					v, good := o.value(r, a, name, prop, fallback, hasFallback)
					if !good || n > 0 && v != val {
						ok = false
						break
					}
					val = v
				}
				if !ok || hasFallback && val != fallback && strings.Contains(val, "var(--tw-") {
					continue
				}
				head, tail := out[:refs[k][0]], out[refs[k][1]:]
				if head != "" && !strings.ContainsRune(" (,", rune(head[len(head)-1])) {
					val = " " + val
				}
				if tail != "" && !strings.ContainsRune(" ),", rune(tail[0])) {
					val += " "
				}
				out = head + val + tail
			}
			out = strings.TrimSpace(spaces.ReplaceAllString(zeroCalc.ReplaceAllString(out, "$1"), " "))
			if out == value || out == "" {
				continue
			}
			r.r.items[i].decl = prop + ": " + out
			o.resolved++
			changed = true
		}
	}
	return changed
}

func (o *optimizer) sweep() bool {
	readers := map[string][]*oRule{}
	for _, r := range o.rules {
		seen := map[string]bool{}
		for _, it := range r.r.items {
			if it.rule != nil {
				continue
			}
			for _, m := range twVar.FindAllStringSubmatch(it.decl, -1) {
				if !seen[m[1]] {
					readers[m[1]] = append(readers[m[1]], r)
				}
				seen[m[1]] = true
			}
		}
	}
	changed := false
	for v, rules := range o.defs {
		if _, registered := o.props[v]; !registered || o.public(v) {
			continue
		}
		for _, r := range rules {
			if r.ro || slices.ContainsFunc(readers[v], func(q *oRule) bool {
				return slices.ContainsFunc(q.alts, func(qa *oAlt) bool {
					return slices.ContainsFunc(r.alts, func(ra *oAlt) bool { return !disjoint(qa.c, ra.c) })
				})
			}) {
				continue
			}
			r.r.items = slices.DeleteFunc(r.r.items, func(it cssItem) bool { return it.rule == nil && declProp(it.decl) == v })
			o.dead++
			changed = true
		}
	}
	return changed
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

func optimizePass(tree, kit *cssRule, t *groupTable) [4]int {
	o := &optimizer{props: map[string]oProp{}, skip: map[string]bool{}, byRule: map[*cssRule]*oRule{}}
	o.collect(tree, t, false)
	o.collect(kit, t, true)
	for range 50 {
		o.index()
		r := o.resolve()
		o.index()
		if s := o.sweep(); !r && !s {
			break
		}
	}
	o.index()
	used := map[string]bool{}
	for _, r := range o.rules {
		for _, it := range r.r.items {
			if it.rule == nil {
				for _, m := range twVar.FindAllStringSubmatch(it.decl, -1) {
					used[m[1]] = true
				}
			}
		}
	}
	dropped := 0
	tree.items = slices.DeleteFunc(tree.items, func(it cssItem) bool {
		if it.rule == nil || !strings.HasPrefix(it.rule.prelude, "@property --tw-") {
			return false
		}
		v := strings.TrimSpace(strings.TrimPrefix(it.rule.prelude, "@property "))
		if used[v] || len(o.defs[v]) > 0 || o.public(v) {
			return false
		}
		dropped++
		return true
	})
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
	return [4]int{o.resolved, o.dead, dropped, merged}
}

func (g *gen) optimize(tree *cssRule, kitCSS string, t *groupTable) error {
	kit, err := parseCSS(kitCSS)
	if err != nil {
		return fmt.Errorf("kit CSS: %w", err)
	}
	var sum [4]int
	for range 20 {
		n := optimizePass(tree, kit, t)
		if n == [4]int{} {
			break
		}
		for i := range sum {
			sum[i] += n[i]
		}
	}
	g.note("Tailwind variable resolved (no other rule changes it on the same element)", "%d declarations", sum[0])
	g.note("Tailwind variable definition removed (nothing reads it on the same element)", "%d definitions", sum[1])
	g.note("@property removed (the variable has no definition and no read)", "%d rules", sum[2])
	g.note("rules with the same selector, or the same condition and part, merged (no rule between them sets a related property on the same element with the same specificity)", "%d rules", sum[3])
	return nil
}
