package main

import (
	"crypto/sha1"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"slices"
	"sort"
	"strings"
)

type layer struct {
	cond    string
	classes []string
	raw     []string
	attr    string
	value   string
	owner   string
	markers []string
}

type rendered struct {
	slot   string
	tag    string
	comp   *function
	fixed  bool
	layers []layer
	own    []layer
	groups []string
}

type part struct {
	key     string
	slot    string
	tag     string
	context string
	child   bool
	suffix  string
	marker  string
	sel     string
	eslot   string
	set     map[string]string
	layers  []layer
	groups  []string
	from    string
}

type gen struct {
	sources   map[string]*source
	styles    map[string]string
	style     string
	parts     []*part
	free      map[string][]*part
	notes     map[string][]string
	manual    map[string]string
	used      map[string]bool
	ignored   map[string]string
	defaulted map[[2]string][]string
	boxless   []string
	physical  bool
	kit       kitMap
	rootSlots map[*function]string
	rootSels  map[*function]string
	shadows   []shadow
	props     map[string][]string
	allProps  map[string][]string
	unmapped  []*part
	fps       map[string]string
	ownGroups map[string]bool
	noMarkers bool
	mapUsed   map[string]bool
	mapBad    []string
	unsafe    []error
	where     string
	renderers map[*function][]*elem
}

var (
	cvaCall      = regexp.MustCompile(`^(\w+)\(\s*(\{[\s\S]*\})?\s*\)$`)
	identifier   = regexp.MustCompile(`^[A-Za-z_$][\w$]*$`)
	boxlessTag   = regexp.MustCompile(`\.(Root|SubmenuRoot|Provider)$`)
	lineComment  = regexp.MustCompile(`(?m)^\s*//[^\n]*$`)
	classNameRef = regexp.MustCompile(`\bclassName\b`)
	upper        = regexp.MustCompile(`[A-Z]`)
)

func newGen(sources map[string]*source, styles map[string]string, manual map[string]string, ignored map[string]string) *gen {
	return &gen{sources: sources, styles: styles, free: map[string][]*part{}, notes: map[string][]string{}, manual: manual, used: map[string]bool{}, ignored: ignored, defaulted: map[[2]string][]string{}, rootSlots: map[*function]string{}, rootSels: map[*function]string{}, fps: map[string]string{}, mapUsed: map[string]bool{}, ownGroups: map[string]bool{}}
}

func (g *gen) note(kind, format string, args ...any) {
	msg := fmt.Sprintf(format, args...)
	if !slices.Contains(g.notes[kind], msg) {
		g.notes[kind] = append(g.notes[kind], msg)
	}
}

func (g *gen) lookup(s *source, tag string) *function {
	if f := s.funcs[tag]; f != nil {
		return f
	}
	if file, ok := s.imports[tag]; ok {
		if other := g.sources[file]; other != nil {
			return other.funcs[tag]
		}
		g.note("missing input", "%s imports %s from %s.tsx, which is not in the input set", s.name, tag, file)
	}
	return nil
}

func (g *gen) cva(s *source, name string) *cvaDef {
	if c := s.cvas[name]; c != nil {
		return c
	}
	if other := g.sources[s.imports[name]]; other != nil {
		return other.cvas[name]
	}
	return nil
}

func propsTarget(f *function) *elem {
	for _, e := range f.elems {
		if a := e.get("className"); a != nil && classNameRef.MatchString(a.expr) {
			return e
		}
	}
	for _, e := range f.elems {
		for _, a := range e.attrs {
			if a.spread {
				return e
			}
		}
	}
	return nil
}

func (g *gen) classes(raw string) ([]layer, []string) {
	var nova, structural, novaRaw, structRaw, groups, markers []string
	for _, tok := range strings.Fields(raw) {
		if err := checkClass("class in "+g.where, tok); err != nil {
			g.unsafe = append(g.unsafe, err)
			continue
		}
		if strings.Contains(tok, "recharts") {
			g.note("chart internals (the kit has its own SVG chart; no CSS)", "%s", tok)
			continue
		}
		orig := tok
		tok = g.scopeGroups(g.fix(tok))
		switch {
		case tok == "group" || tok == "peer":
			groups = append(groups, tok)
			if g.ownGroup(g.where, tok) {
				groups = append(groups, tok+"/kit-"+g.where)
			}
		case strings.HasPrefix(tok, "group/") || strings.HasPrefix(tok, "peer/"):
			groups = append(groups, tok)
		case strings.HasPrefix(tok, "cn-") && g.noMarkers:
			g.note("marker that the shadcn transform keeps (no style rule; like the installed file and the docs page)", "%s in %s", tok, g.where)
		case strings.HasPrefix(tok, "cn-"):
			markers = append(markers, tok)
			if repl, ok := g.ignored[tok]; ok {
				if repl != "" {
					structural = append(structural, strings.Fields(repl)...)
				}
				g.used[tok] = true
				continue
			}
			rule, ok := g.styles[tok]
			if !ok {
				g.note("marker without a style rule", "%s", tok)
				continue
			}
			g.used[tok] = true
			for _, c := range strings.Fields(rule) {
				if strings.Contains(c, "recharts") {
					g.note("chart internals (the kit has its own SVG chart; no CSS)", "%s", c)
					continue
				}
				fixed := g.scopeGroups(g.fix(c))
				nova = append(nova, g.logical(fixed)...)
				novaRaw = append(novaRaw, c)
			}
		default:
			structural = append(structural, g.logical(tok)...)
			structRaw = append(structRaw, orig)
		}
	}
	var out []layer
	if len(nova) > 0 {
		out = append(out, layer{classes: nova, raw: novaRaw, markers: markers})
	}
	if len(structural) > 0 {
		out = append(out, layer{classes: structural, raw: structRaw})
		if len(nova) == 0 {
			out[len(out)-1].markers = markers
		}
	}
	return out, groups
}

func (g *gen) fix(tok string) string {
	for _, f := range sourceFixes {
		if fixed := f.re.ReplaceAllString(tok, f.repl); fixed != tok {
			g.note(f.kind, "%s -> %s (%s)", tok, fixed, f.why)
			tok = fixed
		}
	}
	return tok
}

func (g *gen) logical(c string) []string {
	if g.physical {
		return []string{c}
	}
	out := rtlClasses(c)
	if len(out) != 1 || out[0] != c {
		g.note("physical class made logical (shadcn rtl transform)", "%s -> %s", c, strings.Join(out, " "))
	}
	return out
}

func kebab(name string) string {
	return strings.TrimPrefix(upper.ReplaceAllStringFunc(name, func(s string) string { return "-" + strings.ToLower(s) }), "-")
}

func attrName(key string) string {
	return "data-" + kebab(key)
}

var (
	ctxOr      = regexp.MustCompile(`^context\.(\w+)\s*\|\|\s*(\w+)$`)
	orDefault  = regexp.MustCompile(`^(\w+)\s*(?:\?\?|\|\|)\s*"([^"]*)"$`)
	rawString  = regexp.MustCompile("^String\\.raw`([^`]*)`$")
	rdpDefault = regexp.MustCompile(`^defaultClassNames\.\w+$`)
	notFree    = map[string]bool{"className": true, "children": true, "render": true, "ref": true, "style": true, "props": true}
)

func (g *gen) evalCva(f *function, target *elem, c *cvaDef, args string, scope map[string]string, free map[string]bool, where string) ([]layer, []string, bool) {
	layers, groups := g.classes(c.base)
	bound := map[string]string{}
	if args != "" {
		obj, err := parseObject(args)
		if err != nil {
			g.note("unmapped construct", "%s: cva arguments %q", where, args)
		}
		for _, kv := range obj {
			bound[kv[0]] = kv[1]
		}
	}
	fixed := true
	for _, key := range c.keys {
		val := c.defaults[key]
		expr, ok := bound[key]
		ident, fallback := expr, ""
		if m := ctxOr.FindStringSubmatch(expr); m != nil {
			ident = m[2]
		}
		if m := orDefault.FindStringSubmatch(expr); m != nil {
			ident, fallback = m[1], m[2]
		}
		switch {
		case !ok:
		case identifier.MatchString(ident) && free[ident]:
			fixed = false
			b, found := g.bind(f, target, ident)
			if !found {
				b = binding{attr: attrName(key), self: true}
			}
			if d, ok := scope[ident]; ok {
				b.def = d
			}
			if b.def == "" {
				b.def = fallback
			}
			if b.def == "" {
				b.def = c.defaults[key]
			}
			for _, v := range c.variants[key] {
				cond := place(b, attrIs(b.attr, v.value, b.def))
				ls, gs := g.classes(v.classes)
				for _, l := range ls {
					l.cond = cond
					l.attr, l.value, l.owner = b.attr, v.value, b.owner
					layers = append(layers, l)
				}
				groups = append(groups, gs...)
			}
			continue
		case identifier.MatchString(ident):
			if s, ok := scope[ident]; ok {
				val = s
			} else if fallback != "" {
				val = fallback
			}
		default:
			if s, ok := stringLiteral(expr); ok {
				val = s
			} else {
				g.note("unmapped construct", "%s: cva value %s=%s", where, key, expr)
			}
		}
		for _, v := range c.variants[key] {
			if v.value == val {
				ls, gs := g.classes(v.classes)
				layers = append(layers, ls...)
				groups = append(groups, gs...)
			}
		}
	}
	return layers, groups, fixed
}

func (g *gen) classExpr(f *function, target *elem, a *attr, scope map[string]string, free map[string]bool) ([]layer, []string, bool) {
	if a == nil {
		return nil, nil, true
	}
	if a.isStr {
		l, gr := g.classes(a.str)
		return l, gr, true
	}
	expr := lineComment.ReplaceAllString(a.expr, "")
	args := []string{expr}
	if strings.HasPrefix(expr, "cn(") && strings.HasSuffix(expr, ")") {
		args = splitTop(expr[3:len(expr)-1], ',')
	}
	var layers []layer
	var groups []string
	fixed := true
	for _, arg := range args {
		l, gr, fx := g.classArg(f, target, arg, scope, free)
		layers, groups, fixed = append(layers, l...), append(groups, gr...), fixed && fx
	}
	return layers, groups, fixed
}

func (g *gen) classArg(f *function, target *elem, arg string, scope map[string]string, free map[string]bool) ([]layer, []string, bool) {
	where := f.file.name + "/" + f.name
	arg = strings.TrimSpace(arg)
	for strings.HasPrefix(arg, "(") {
		if end, err := matchFrom(arg, 0); err == nil && end == len(arg) {
			arg = strings.TrimSpace(arg[1 : len(arg)-1])
			continue
		}
		break
	}
	if m := rawString.FindStringSubmatch(arg); m != nil {
		l, gr := g.classes(m[1])
		return l, gr, true
	}
	if s, ok := stringLiteral(arg); ok {
		l, gr := g.classes(s)
		return l, gr, true
	}
	switch {
	case arg == "className":
		return nil, nil, true
	case rdpDefault.MatchString(arg):
		g.note("react-day-picker default class name (no CSS)", "%s: %s", where, arg)
		return nil, nil, true
	}
	if q, colon := ternary(arg); q > 0 {
		cond := arg[:q]
		yes, yg, _ := g.classArg(f, target, arg[q+1:colon], scope, free)
		no, ng, _ := g.classArg(f, target, arg[colon+1:], scope, free)
		y, err1 := g.applyCond(f, target, cond, false, yes, scope, free)
		n, err2 := g.applyCond(f, target, cond, true, no, scope, free)
		if err1 != nil || err2 != nil {
			g.note("unmapped construct", "%s: className argument %s (%v)", where, oneLine(arg), firstErr(err1, err2))
			return nil, nil, true
		}
		return append(y, n...), append(yg, ng...), false
	}
	if i := lastTop(arg, "&&"); i > 0 {
		val, vg, _ := g.classArg(f, target, arg[i+2:], scope, free)
		out, err := g.applyCond(f, target, arg[:i], false, val, scope, free)
		if err != nil {
			g.note("unmapped construct", "%s: className argument %s (%v)", where, oneLine(arg), err)
			return nil, nil, true
		}
		return out, vg, false
	}
	if strings.HasPrefix(arg, "{") {
		obj, err := parseObject(arg)
		if err == nil {
			var layers []layer
			var groups []string
			for _, kv := range obj {
				cls := kv[0]
				l, gr := g.classes(cls)
				out, err := g.applyCond(f, target, kv[1], false, l, scope, free)
				if err != nil {
					g.note("unmapped construct", "%s: class object entry %q: %s (%v)", where, cls, oneLine(kv[1]), err)
					continue
				}
				layers, groups = append(layers, out...), append(groups, gr...)
			}
			return layers, groups, false
		}
	}
	if m := cvaCall.FindStringSubmatch(arg); m != nil {
		if c := g.cva(f.file, m[1]); c != nil {
			keep := g.noMarkers
			g.noMarkers = false
			defer func() { g.noMarkers = keep }()
			return g.evalCva(f, target, c, m[2], scope, free, where)
		}
	}
	if identifier.MatchString(arg) {
		g.note("consumer class prop", "%s: %s", where, arg)
		return nil, nil, true
	}
	g.note("unmapped construct", "%s: className argument %s", where, oneLine(arg))
	return nil, nil, true
}

func firstErr(errs ...error) error {
	for _, e := range errs {
		if e != nil {
			return e
		}
	}
	return nil
}

func (g *gen) applyCond(f *function, target *elem, cond string, negate bool, layers []layer, scope map[string]string, free map[string]bool) ([]layer, error) {
	n, err := parseCond(cond)
	if err != nil {
		return nil, err
	}
	if negate {
		n = &cnode{op: "not", args: []*cnode{n}}
	}
	c, err := g.evalCond(f, target, n, scope, free)
	if err != nil {
		return nil, err
	}
	if c.never {
		return nil, nil
	}
	out := make([]layer, 0, len(layers))
	for _, l := range layers {
		if !c.always {
			l.cond = c.sel + l.cond
			if c.attr != "" && l.attr == "" {
				l.attr, l.value, l.owner = c.attr, c.value, c.owner
			}
		}
		out = append(out, l)
	}
	return out, nil
}

func ternary(src string) (int, int) {
	depth, q, nested := 0, -1, 0
	for i := 0; i < len(src); i++ {
		switch c := src[i]; c {
		case '"', '\'':
			if j := strings.IndexByte(src[i+1:], c); j >= 0 {
				i += j + 1
			}
		case '`':
			if end, err := templateEnd(src, i); err == nil {
				i = end
			}
		case '(', '{', '[':
			depth++
		case ')', '}', ']':
			depth--
		case '?':
			if depth != 0 || i+1 < len(src) && (src[i+1] == '.' || src[i+1] == '?') || i > 0 && src[i-1] == '?' {
				continue
			}
			if q < 0 {
				q = i
			} else {
				nested++
			}
		case ':':
			if depth != 0 || q < 0 {
				continue
			}
			if nested > 0 {
				nested--
				continue
			}
			return q, i
		}
	}
	return -1, -1
}

func lastTop(src, tok string) int {
	depth, last := 0, -1
	for i := 0; i < len(src); i++ {
		switch c := src[i]; c {
		case '"', '\'':
			if j := strings.IndexByte(src[i+1:], c); j >= 0 {
				i += j + 1
			}
		case '`':
			if end, err := templateEnd(src, i); err == nil {
				i = end
			}
		case '(', '{', '[':
			depth++
		case ')', '}', ']':
			depth--
		default:
			if depth == 0 && strings.HasPrefix(src[i:], tok) {
				last = i
				i += len(tok) - 1
			}
		}
	}
	return last
}

func oneLine(s string) string {
	return strings.Join(strings.Fields(s), " ")
}

func propsOf(e *elem, scope map[string]string, free map[string]bool) map[string]string {
	out := map[string]string{}
	for _, a := range e.attrs {
		switch {
		case a.spread || a.name == "className":
		case a.isStr:
			out[a.name] = a.str
		case identifier.MatchString(a.expr):
			if v, ok := scope[a.expr]; ok {
				out[a.name] = v
				if free[a.expr] && !strings.HasPrefix(a.name, "data-") {
					out[a.name] = "?" + v
				}
			}
		default:
			if m := orDefault.FindStringSubmatch(a.expr); m != nil {
				v, ok := scope[m[1]]
				if !ok {
					v = m[2]
				}
				out[a.name] = v
				if free[m[1]] && !strings.HasPrefix(a.name, "data-") {
					out[a.name] = "?" + v
				}
			} else if q, c := ternary(a.expr); q > 0 {
				if no, ok := stringLiteral(strings.TrimSpace(a.expr[c+1:])); ok {
					if _, ok := stringLiteral(strings.TrimSpace(a.expr[q+1 : c])); ok {
						out[a.name] = "?" + no
					}
				}
			}
		}
	}
	return out
}

func (g *gen) renderFunc(f *function, incoming map[string]string, freeVars bool) (rendered, bool) {
	pt := propsTarget(f)
	if pt == nil {
		return rendered{}, false
	}
	scope := map[string]string{}
	free := map[string]bool{}
	for k, v := range f.defaults {
		scope[k] = v
	}
	if freeVars {
		for k := range f.params {
			if !notFree[k] {
				free[k] = true
			}
		}
	}
	for k, v := range incoming {
		if d, ok := strings.CutPrefix(v, "?"); ok {
			scope[k] = d
			free[k] = true
			continue
		}
		scope[k] = v
		delete(free, k)
	}
	r := g.render(pt, scope, free)
	if s, ok := incoming["data-slot"]; ok && pt.spreadAfter("data-slot") {
		r.slot = s
	} else if s, ok := incoming["data-slot"]; ok && pt.get("data-slot") == nil {
		r.slot = s
	}
	r.comp = f
	return r, true
}

func (g *gen) render(e *elem, scope map[string]string, free map[string]bool) rendered {
	f := e.fn
	if a := e.get("render"); a != nil && a.elem == nil && f.jsx[a.expr] != nil {
		c := *e
		c.attrs = slices.Clone(e.attrs)
		for i := range c.attrs {
			if !c.attrs[i].spread && c.attrs[i].name == "render" {
				c.attrs[i].elem = f.jsx[a.expr]
			}
		}
		e = &c
	}
	if a := e.get("render"); a != nil && a.elem != nil && g.lookup(f.file, e.tag) != nil {
		comp := g.lookup(f.file, e.tag)
		if r, ok := g.renderFunc(comp, g.passThrough(e, comp, propsOf(e, scope, free)), false); ok {
			inner := *a.elem
			inner.fn = f
			ir := g.render(&inner, scope, free)
			l, gr, _ := g.classExpr(f, e, e.get("className"), scope, free)
			r.layers = append(append(slices.Clone(r.layers), ir.layers...), l...)
			r.groups = append(append(slices.Clone(r.groups), ir.groups...), gr...)
			r.own = append(slices.Clone(ir.layers), l...)
			if ir.slot != "" {
				r.slot = ir.slot
			}
			if s, ok := literalSlot(e); ok {
				r.slot = s
			}
			r.fixed = true
			return r
		}
	}
	if a := e.get("render"); a != nil && a.elem != nil {
		inner := *a.elem
		inner.fn = f
		attrs := slices.Clone(inner.attrs)
		for _, x := range e.attrs {
			if !x.spread && x.name != "render" && x.name != "className" && inner.get(x.name) == nil {
				attrs = append(attrs, x)
			}
		}
		inner.attrs = attrs
		r := g.render(&inner, scope, free)
		l, gr, _ := g.classExpr(f, e, e.get("className"), scope, free)
		r.layers, r.groups = append(r.layers, l...), append(r.groups, gr...)
		r.own = append(r.own, l...)
		return r
	}
	if comp := g.lookup(f.file, e.tag); comp != nil {
		r, ok := g.renderFunc(comp, g.passThrough(e, comp, propsOf(e, scope, free)), false)
		if ok {
			l, gr, _ := g.classExpr(f, e, e.get("className"), scope, free)
			r.layers, r.groups = append(slices.Clone(r.layers), l...), append(slices.Clone(r.groups), gr...)
			r.own = l
			r.fixed = true
			return r
		}
	}
	r := rendered{}
	if a := e.get("data-slot"); a != nil && a.isStr {
		r.slot = a.str
	}
	if e.tag != "" && e.tag[0] >= 'a' && e.tag[0] <= 'z' {
		r.tag = e.tag
	} else if t, ok := primitiveTags[e.tag]; ok {
		r.tag = t
	}
	r.layers, r.groups, _ = g.classExpr(f, e, e.get("className"), scope, free)
	r.own = r.layers
	return r
}

var primitiveTags = map[string]string{"InputPrimitive": "input"}

func (g *gen) cvaKeys(comp *function) map[string]string {
	keys := map[string]string{}
	inner := propsTarget(comp)
	if inner == nil {
		return keys
	}
	a := inner.get("className")
	if a == nil {
		return keys
	}
	for _, m := range cvaRef.FindAllStringSubmatch(a.expr, -1) {
		if c := g.cva(comp.file, m[1]); c != nil {
			for _, k := range c.keys {
				keys[k] = c.defaults[k]
			}
		}
	}
	return keys
}

func (g *gen) passThrough(e *elem, comp *function, props map[string]string) map[string]string {
	if !slices.ContainsFunc(e.attrs, func(a attr) bool { return a.spread && a.name == "props" }) {
		return props
	}
	keys := g.cvaKeys(comp)
	for _, k := range sortedKeys(keys) {
		if _, set := props[k]; set || e.get(k) != nil || e.fn.params[k] {
			continue
		}
		def := keys[k]
		if d, ok := comp.defaults[k]; ok {
			def = d
		}
		props[k] = "?" + def
		g.note("variant passed through {...props}", "%s/%s renders %s; %s is free (default %q)", e.fn.file.name, e.fn.name, comp.name, k, def)
	}
	return props
}

func literalSlot(e *elem) (string, bool) {
	if a := e.get("data-slot"); a != nil && a.isStr {
		return a.str, true
	}
	return "", false
}

func sameLayers(a, b []layer) bool {
	return slices.EqualFunc(a, b, func(x, y layer) bool { return x.cond == y.cond && slices.Equal(x.classes, y.classes) })
}

func (g *gen) addPart(p *part) {
	for _, q := range g.parts {
		if q.slot == p.slot && q.context == p.context && q.suffix == p.suffix && q.sel == p.sel && q.marker == p.marker && q.tag == p.tag && sameLayers(q.layers, p.layers) {
			return
		}
	}
	g.parts = append(g.parts, p)
	if p.context == "" && p.suffix == "" && p.marker == "" && p.sel == "" {
		g.free[p.slot] = append(g.free[p.slot], p)
	}
}

func (g *gen) params(f *function) map[string]bool {
	free := map[string]bool{}
	for k := range f.params {
		if !notFree[k] {
			free[k] = true
		}
	}
	return free
}

func fingerprint(text string) string {
	sum := sha1.Sum([]byte(text))
	return hex.EncodeToString(sum[:4])
}

func elemPrint(e *elem) string {
	if e == nil {
		return ""
	}
	var b strings.Builder
	b.WriteString(e.tag)
	for _, a := range e.attrs {
		switch {
		case a.spread:
			fmt.Fprintf(&b, " {...%s}", a.name)
		case a.isStr:
			fmt.Fprintf(&b, " %s=%q", a.name, a.str)
		default:
			fmt.Fprintf(&b, " %s={%s}", a.name, strings.Join(strings.Fields(a.expr), " "))
		}
	}
	return b.String()
}

func (g *gen) mapped(key, rootSel, print string) (string, bool) {
	sel, ok := g.manual[key]
	if !ok {
		return "", false
	}
	if rootSel == "" && strings.Contains(sel, "&") {
		return "", false
	}
	g.mapUsed[key] = true
	if strings.Contains(key, "#") {
		if got := fingerprint(print); g.fps[key] != got {
			g.mapBad = append(g.mapBad, fmt.Sprintf("%s: element fingerprint %s, map.tsv has %q (the element order, its classes, or its attributes changed; check the selector)", key, got, g.fps[key]))
		}
	}
	return strings.ReplaceAll(sel, "&", ":where("+rootSel+")"), true
}

func (g *gen) mapErr(components []string) error {
	bad := slices.Clone(g.mapBad)
	for _, key := range sortedKeys(g.manual) {
		comp, _, _ := strings.Cut(key, "/")
		if slices.Contains(components, comp) && !g.mapUsed[key] {
			bad = append(bad, key+": matches no element in the source")
		}
	}
	if len(bad) == 0 {
		return nil
	}
	slices.Sort(bad)
	return fmt.Errorf("map.tsv:\n  %s", strings.Join(slices.Compact(bad), "\n  "))
}

func (g *gen) unsafeErr() error {
	if len(g.unsafe) == 0 {
		return nil
	}
	return errors.Join(g.unsafe...)
}

var cvaTarget = regexp.MustCompile(`^\[data-slot="([a-z0-9-]+)"\]\[(data-[a-z-]+)="([^"]+)"\]$`)

func (g *gen) cvaParts(name string, s *source) {
	prefix := name + "/cva."
	for _, key := range sortedKeys(g.manual) {
		c := s.cvas[strings.TrimPrefix(key, prefix)]
		if !strings.HasPrefix(key, prefix) || c == nil {
			continue
		}
		sel, _ := g.mapped(key, "", "")
		m := cvaTarget.FindStringSubmatch(sel)
		if m == nil {
			g.mapBad = append(g.mapBad, key+": a cva key needs a selector [data-slot=\"part\"][data-attr=\"value\"]")
			continue
		}
		layers, groups := g.classes(c.base)
		g.addPart(&part{slot: name, sel: sel, eslot: m[1], set: map[string]string{m[2]: m[3]}, layers: layers, groups: groups, from: key})
		g.note("cva function used on another part (markup sets the attribute)", "%s -> %s", key, sel)
	}
}

func slottedAncestor(e *elem) (*elem, bool) {
	for a := e.parent; a != nil; a = a.parent {
		if _, ok := literalSlot(a); ok {
			return a, a == e.parent
		}
	}
	return nil, false
}

func (g *gen) component(name string) {
	g.where = name
	s := g.sources[name]
	defer g.cvaParts(name, s)
	for _, fname := range s.order {
		f := s.funcs[fname]
		if r, ok := g.renderFunc(f, nil, true); ok && r.slot != "" {
			g.rootSlots[f] = r.slot
		}
	}
	for _, fname := range s.order {
		f := s.funcs[fname]
		r, ok := g.renderFunc(f, nil, true)
		if !ok {
			if len(f.elems) == 0 || classNameRef.MatchString(fname) {
				g.note("function without a rendered part", "%s/%s", name, fname)
			}
			continue
		}
		pt := propsTarget(f)
		if boxlessTag.MatchString(pt.tag) && !strings.HasPrefix(pt.tag, "Collapsible") && r.slot != "" && len(r.layers) == 0 && !slices.Contains(g.boxless, r.slot) {
			g.boxless = append(g.boxless, r.slot)
		}
		key := name + "/" + fname
		if sel, ok := g.mapped(key, "", ""); ok && r.slot != "" {
			if sel != "-" {
				g.addPart(&part{slot: r.slot, sel: sel, eslot: r.slot, layers: r.layers, groups: r.groups, from: key})
				g.rootSels[f] = sel
			}
			g.note("manual mapping", "%s -> %s", key, sel)
			continue
		}
		if r.slot == "" {
			if len(r.layers) == 0 {
				continue
			}
			if sel, ok := g.mapped(key, "", ""); ok {
				if sel != "-" {
					g.addPart(&part{slot: name, sel: sel, layers: r.layers, groups: r.groups, from: key})
					g.rootSels[f] = sel
				}
				g.note("manual mapping", "%s -> %s", key, sel)
				continue
			}
			g.note("unmapped element", "%s: root element <%s> has classes but no data-slot", key, pt.tag)
			g.unmapped = append(g.unmapped, &part{from: key, layers: r.layers})
			continue
		}
		g.rootSels[f] = g.kit.slot(r.slot)
		if g.lookup(s, pt.tag) != nil && pt.get("data-slot") == nil && len(g.free[r.slot]) > 0 && g.free[r.slot][0].from != key {
			marker := "data-" + kebab(fname)
			g.rootSels[f] = g.kit.slot(r.slot) + ":where([" + marker + "])"
			own := g.shadowedVariants(s, pt, r.slot, marker)
			set := g.fixedProps(s, pt, f)
			g.addPart(&part{slot: r.slot, marker: marker, set: set, layers: append(own, r.own...), groups: r.groups, from: key})
			g.note("part rendered as another component", "%s renders %s; markup adds %s%s", key, pt.tag, marker, attrList(set))
			continue
		}
		g.addPart(&part{slot: r.slot, tag: r.tag, layers: r.layers, groups: r.groups, from: key})
	}
	for _, fname := range s.order {
		f := s.funcs[fname]
		pt := propsTarget(f)
		root, _ := g.renderFunc(f, nil, true)
		rootSel := g.rootSels[f]
		if rootSel == "" && root.slot != "" {
			rootSel = g.kit.slot(root.slot)
		}
		renamed := g.renamed(f, root.slot)
		rootSel = withSlots(g.kit, rootSel, renamed)
		rootCtx := withSlots(g.kit, g.rootSels[f], renamed)
		before := len(g.parts)
		count := map[string]int{}
		for _, e := range f.elems {
			if e != pt && e.get("className") != nil {
				count[e.tag]++
			}
		}
		seen := map[string]int{}
		owns := pt != nil && (pt.get("data-slot") != nil || g.lookup(s, pt.tag) == nil)
		for _, e := range f.elems {
			if owns {
				g.defaultedAttrs(f, e, root.slot, e == pt)
			}
			if e == pt {
				g.classNames(f, e, rootSel)
				g.componentsProp(f, e, rootSel)
				g.extraClassNames(f, e, rootSel)
				continue
			}
			r := g.render(e, f.defaults, g.params(f))
			from := name + "/" + fname + "/<" + e.tag + ">"
			if e.get("className") != nil {
				seen[e.tag]++
			}
			if len(r.layers) == 0 {
				continue
			}
			mkey := name + "/" + fname + "/" + e.tag
			if count[e.tag] > 1 {
				mkey += fmt.Sprintf("#%d", seen[e.tag])
			}
			if sel, ok := g.mapped(mkey, rootSel, elemPrint(e)); ok {
				if sel != "-" {
					g.addPart(&part{slot: root.slot, sel: sel, eslot: r.slot, layers: r.layers, groups: r.groups, from: mkey})
				}
				g.note("manual mapping", "%s -> %s", mkey, sel)
				continue
			}
			if r.slot == "" {
				if layerText(r.layers) == "sr-only" {
					g.note("markup utility class", "%s: class=\"sr-only\"", from)
					continue
				}
				g.note("unmapped element", "%s: no data-slot, classes %q", mkey, layerText(r.layers))
				g.unmapped = append(g.unmapped, &part{from: mkey, layers: r.layers})
				continue
			}
			frees := g.free[r.slot]
			if len(frees) == 0 {
				g.addPart(&part{slot: r.slot, tag: r.tag, layers: r.layers, groups: r.groups, from: from})
				continue
			}
			base := frees[0]
			if sameLayers(base.layers, r.layers) {
				continue
			}
			if r.fixed && r.comp != nil && base.from == r.comp.file.name+"/"+r.comp.name && !ownClasses(e) {
				g.note("instance with fixed variants", "%s renders %s with fixed props; markup sets them as data attributes", from, r.comp.name)
				continue
			}
			extra := r.layers
			if r.comp != nil && base.from == r.comp.file.name+"/"+r.comp.name {
				extra = r.own
			} else if len(r.layers) > len(base.layers) && sameLayers(base.layers, r.layers[:len(base.layers)]) {
				extra = r.layers[len(base.layers):]
			}
			if len(extra) == 0 {
				continue
			}
			ctx, child := rootCtx, pt != nil && e.parent == pt
			if anc, direct := slottedAncestor(e); anc != nil && anc != pt {
				slot, _ := literalSlot(anc)
				ctx, child = g.kit.slot(slot), direct
			}
			if ctx == "" {
				g.note("unmapped element", "%s: contextual part without an owner slot", from)
				continue
			}
			g.addPart(&part{slot: r.slot, context: ctx, child: child, layers: extra, groups: r.groups, from: from})
		}
		for _, p := range g.parts[before:] {
			if len(renamed) > 0 && (p.sel != "" && strings.Contains(p.sel, rootSel) || p.context != "" && p.context == rootCtx) {
				g.note("child element also written for the parts that render its component under another data-slot", "%s: %s", p.from, strings.Join(renamed, ", "))
			}
		}
	}
}

func (g *gen) target(e *elem) *function {
	s := e.fn.file
	if f := s.funcs[e.tag]; f != nil {
		return f
	}
	if other := g.sources[s.imports[e.tag]]; other != nil {
		return other.funcs[e.tag]
	}
	return nil
}

func (g *gen) renamedSlots(f *function, path map[*function]bool) []string {
	pt := propsTarget(f)
	if pt == nil || path[f] || pt.get("data-slot") != nil && !pt.spreadAfter("data-slot") {
		return nil
	}
	if g.renderers == nil {
		g.renderers = map[*function][]*elem{}
		for _, name := range sortedKeys(g.sources) {
			s := g.sources[name]
			for _, fname := range s.order {
				for _, e := range s.funcs[fname].elems {
					if t := g.target(e); t != nil {
						g.renderers[t] = append(g.renderers[t], e)
					}
				}
			}
		}
	}
	path[f] = true
	defer delete(path, f)
	var out []string
	for _, e := range g.renderers[f] {
		if slot, ok := literalSlot(e); ok {
			out = append(out, slot)
		}
		if e == propsTarget(e.fn) {
			out = append(out, g.renamedSlots(e.fn, path)...)
		}
	}
	return out
}

func (g *gen) renamed(f *function, slot string) []string {
	var out []string
	for _, s := range g.renamedSlots(f, map[*function]bool{}) {
		if s != slot {
			out = append(out, s)
		}
	}
	slices.Sort(out)
	return slices.Compact(out)
}

func withSlots(k kitMap, sel string, slots []string) string {
	if sel == "" || len(slots) == 0 {
		return sel
	}
	sels := []string{sel}
	for _, s := range slots {
		sels = append(sels, k.slot(s))
	}
	return ":is(" + strings.Join(sels, ", ") + ")"
}

func (g *gen) shadowedVariants(s *source, pt *elem, slot, marker string) []layer {
	comp := g.lookup(s, pt.tag)
	if comp == nil {
		return nil
	}
	inner := propsTarget(comp)
	if inner == nil {
		return nil
	}
	a := inner.get("className")
	if a == nil {
		return nil
	}
	var out []layer
	for _, m := range cvaRef.FindAllStringSubmatch(a.expr, -1) {
		c := g.cva(comp.file, m[1])
		if c == nil {
			continue
		}
		for _, key := range c.keys {
			if x := pt.get("data-" + kebab(key)); x == nil || x.isStr {
				continue
			}
			g.shadows = append(g.shadows, shadow{slot: slot, attr: attrName(key), marker: marker})
			g.note("variant attribute shadowed by a part", "%s %s is the part's own variant; %s keeps its default %s classes", marker, attrName(key), slot, key)
			for _, v := range c.variants[key] {
				if v.value == c.defaults[key] {
					ls, _ := g.classes(v.classes)
					out = append(out, ls...)
				}
			}
		}
	}
	return out
}

type shadow struct{ slot, attr, marker string }

var cvaRef = regexp.MustCompile(`\b(\w+Variants)\(`)

func (g *gen) applyShadows() {
	for _, sh := range g.shadows {
		for _, p := range g.parts {
			if p.slot != sh.slot || p.marker != "" || p.sel != "" {
				continue
			}
			for i := range p.layers {
				if p.layers[i].attr == sh.attr && p.layers[i].owner == "" && p.layers[i].cond != "" {
					p.layers[i].cond += ":where(:not([" + sh.marker + "]))"
				}
			}
		}
	}
}

func (g *gen) fixedProps(s *source, pt *elem, f *function) map[string]string {
	keys := map[string]string{}
	if comp := g.lookup(s, pt.tag); comp != nil {
		if inner := propsTarget(comp); inner != nil {
			if a := inner.get("className"); a != nil {
				for _, m := range cvaRef.FindAllStringSubmatch(a.expr, -1) {
					if c := g.cva(comp.file, m[1]); c != nil {
						for _, k := range c.keys {
							keys[k] = c.defaults[k]
						}
					}
				}
			}
		}
	}
	out := map[string]string{}
	for _, a := range pt.attrs {
		if a.spread || a.name == "className" || a.name == "render" || a.name == "data-slot" {
			continue
		}
		v := a.str
		if !a.isStr {
			d, ok := f.defaults[a.expr]
			if m := orDefault.FindStringSubmatch(a.expr); m != nil && !ok {
				d, ok = m[2], true
			}
			if !ok {
				continue
			}
			v = d
		}
		if strings.HasPrefix(a.name, "data-") {
			out[a.name] = v
		} else if def, ok := keys[a.name]; ok && v != def || !ok && (a.name == "variant" || a.name == "size") && a.isStr {
			out[attrName(a.name)] = v
		}
	}
	return out
}

func attrList(m map[string]string) string {
	var out []string
	for _, k := range sortedKeys(m) {
		out = append(out, fmt.Sprintf(`%s="%s"`, k, m[k]))
	}
	if len(out) == 0 {
		return ""
	}
	return " and " + strings.Join(out, " ")
}

func jsxElems(text string) []*elem {
	var out []*elem
	for pos := 0; pos < len(text); {
		loc := jsxOpen.FindStringIndex(text[pos:])
		if loc == nil {
			break
		}
		start := pos + loc[0]
		if start > 0 && isIdent(text[start-1]) {
			pos = start + 1
			continue
		}
		e, next, err := parseElement(text, start)
		if err != nil {
			pos = start + 1
			continue
		}
		out = append(out, e)
		pos = next
	}
	return out
}

func (g *gen) componentsProp(f *function, e *elem, rootSel string) {
	a := e.get("components")
	if a == nil || a.isStr {
		return
	}
	obj, err := parseObject(a.expr)
	if err != nil {
		g.note("unmapped construct", "%s/%s: components %v", f.file.name, f.name, err)
		return
	}
	for _, kv := range obj {
		if strings.HasPrefix(kv[0], "...") {
			continue
		}
		elems := jsxElems(kv[1])
		count := map[string]int{}
		for _, x := range elems {
			if x.get("className") != nil {
				count[x.tag]++
			}
		}
		seen := map[string]int{}
		for _, x := range elems {
			ca := x.get("className")
			if ca == nil {
				continue
			}
			x.fn = f
			seen[x.tag]++
			l, gr, _ := g.classExpr(f, x, ca, f.defaults, g.params(f))
			if len(l) == 0 {
				continue
			}
			key := f.file.name + "/" + f.name + "/components." + kv[0] + "/" + x.tag
			if count[x.tag] > 1 {
				key += fmt.Sprintf("#%d", seen[x.tag])
			}
			sel, ok := g.mapped(key, rootSel, elemPrint(x))
			if !ok {
				g.note("unmapped element", "%s: classes %q", key, layerText(l))
				g.unmapped = append(g.unmapped, &part{from: key, layers: l})
				continue
			}
			if sel != "-" {
				g.addPart(&part{slot: f.file.name, sel: sel, layers: l, groups: gr, from: key})
			}
			g.note("manual mapping", "%s -> %s", key, sel)
		}
	}
}

func (g *gen) extraClassNames(f *function, e *elem, rootSel string) {
	for _, a := range e.attrs {
		if a.spread || !strings.HasSuffix(a.name, "ClassName") || a.name == "className" {
			continue
		}
		g.noMarkers = true
		l, gr, _ := g.classExpr(f, e, &a, f.defaults, g.params(f))
		g.noMarkers = false
		if len(l) == 0 {
			continue
		}
		key := f.file.name + "/" + f.name + "/" + a.name
		sel, ok := g.mapped(key, rootSel, "")
		if !ok {
			g.note("unmapped element", "%s: classes %q", key, layerText(l))
			g.unmapped = append(g.unmapped, &part{from: key, layers: l})
			continue
		}
		if sel != "-" {
			g.addPart(&part{slot: f.file.name, sel: sel, layers: l, groups: gr, from: key})
		}
		g.note("manual mapping", "%s -> %s", key, sel)
	}
}

func (g *gen) classNames(f *function, e *elem, rootSel string) {
	a := e.get("classNames")
	if a == nil || a.isStr {
		return
	}
	obj, err := parseObject(a.expr)
	if err != nil {
		g.note("unmapped construct", "%s/%s: classNames %v", f.file.name, f.name, err)
		return
	}
	for _, kv := range obj {
		if strings.HasPrefix(kv[0], "...") {
			continue
		}
		g.noMarkers = true
		l, gr, _ := g.classExpr(f, nil, &attr{name: kv[0], expr: kv[1]}, f.defaults, g.params(f))
		g.noMarkers = false
		if len(l) == 0 {
			continue
		}
		key := f.file.name + "/" + f.name + "/classNames." + kv[0]
		sel, ok := g.mapped(key, rootSel, kv[1])
		if !ok {
			g.note("unmapped element", "%s: classes %q", key, layerText(l))
			g.unmapped = append(g.unmapped, &part{from: key, layers: l})
			continue
		}
		if sel != "-" {
			g.addPart(&part{slot: f.file.name, sel: sel, layers: l, groups: gr, from: key})
		}
		g.note("manual mapping", "%s -> %s", key, sel)
	}
}

func (g *gen) defaultedAttrs(f *function, e *elem, rootSlot string, isRoot bool) {
	slot := rootSlot
	if !isRoot {
		slot = ""
		if a := e.get("data-slot"); a != nil && a.isStr {
			slot = a.str
		}
	}
	if slot == "" {
		return
	}
	for _, a := range e.attrs {
		if a.spread || a.isStr || !identifier.MatchString(a.expr) {
			continue
		}
		def, ok := f.defaults[a.expr]
		if !ok || def == "false" || def == "true" {
			continue
		}
		name := a.name
		if name == "orientation" && e.tag != "" && e.tag[0] >= 'A' && e.tag[0] <= 'Z' {
			name = "data-orientation"
		}
		if !strings.HasPrefix(name, "data-") || name == "data-slot" {
			continue
		}
		key := [2]string{name, def}
		if !slices.Contains(g.defaulted[key], slot) {
			g.defaulted[key] = append(g.defaulted[key], slot)
			g.note("attribute the source always sets", "%s on %s defaults to %q; CSS treats a missing attribute as %q", name, slot, def, def)
		}
	}
}

func ownClasses(e *elem) bool {
	if e.get("className") != nil {
		return true
	}
	a := e.get("render")
	return a != nil && a.elem != nil && a.elem.get("className") != nil
}

func layerText(ls []layer) string {
	var out []string
	for _, l := range ls {
		out = append(out, strings.Join(l.classes, " "))
	}
	return strings.Join(out, " ")
}

func (g *gen) resolveConflicts() {
	for slot, ps := range g.free {
		if len(ps) < 2 {
			continue
		}
		tags := map[string]bool{}
		for _, p := range ps {
			tags[p.tag] = true
		}
		if len(tags) == len(ps) && !tags[""] {
			for _, p := range ps {
				p.key = p.tag
			}
			g.note("slot shared by several parts", "%s: told apart by element (%s)", slot, strings.Join(sortedKeys(tags), ", "))
			continue
		}
		var from []string
		for _, p := range ps {
			from = append(from, p.from)
		}
		g.note("slot shared by several parts", "%s: cannot tell apart %s; later rules win", slot, strings.Join(from, ", "))
	}
}

func sortedKeys[V any](m map[string]V) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

type jsonVariant struct {
	Owner   string   `json:"owner,omitempty"`
	Attr    string   `json:"attr"`
	Value   string   `json:"value"`
	Default bool     `json:"default,omitempty"`
	Tokens  []string `json:"tokens"`
}

type jsonPart struct {
	Slot     string            `json:"slot,omitempty"`
	Sel      string            `json:"selector"`
	Marker   string            `json:"marker,omitempty"`
	Tag      string            `json:"tag,omitempty"`
	Context  string            `json:"context,omitempty"`
	From     string            `json:"from"`
	Tokens   []string          `json:"tokens"`
	Own      []string          `json:"own,omitempty"`
	Variants []jsonVariant     `json:"variants,omitempty"`
	Mapped   bool              `json:"mapped"`
	Element  string            `json:"element_slot,omitempty"`
	Set      map[string]string `json:"set,omitempty"`
	Markers  []string          `json:"markers,omitempty"`
}

func rawTokens(ls []layer) []string {
	var out []string
	for _, l := range ls {
		for _, t := range l.raw {
			if !slices.Contains(out, t) {
				out = append(out, t)
			}
		}
	}
	return out
}

func bothTokens(ls []layer) []string {
	out := rawTokens(ls)
	for _, l := range ls {
		for _, t := range l.classes {
			if !slices.Contains(out, t) {
				out = append(out, t)
			}
		}
	}
	return out
}

func (g *gen) partsJSON(k kitMap, components []string) []byte {
	var out []jsonPart
	for _, p := range g.parts {
		jp := jsonPart{Slot: p.slot, Sel: k.selector(p), Marker: p.marker, Tag: p.tag, Context: p.context, From: p.from, Tokens: bothTokens(p.layers), Mapped: true}
		for _, l := range p.layers {
			for _, m := range l.markers {
				if !slices.Contains(jp.Markers, m) {
					jp.Markers = append(jp.Markers, m)
				}
			}
		}
		if p.sel != "" {
			jp.Slot = ""
			jp.Element = p.eslot
		}
		if p.marker != "" || p.set != nil {
			var base []layer
			for _, l := range p.layers {
				if l.cond == "" {
					base = append(base, l)
				}
			}
			jp.Own = bothTokens(base)
			jp.Set = p.set
		}
		for _, l := range p.layers {
			if l.attr == "" {
				continue
			}
			i := slices.IndexFunc(jp.Variants, func(v jsonVariant) bool { return v.Attr == l.attr && v.Value == l.value && v.Owner == l.owner })
			if i < 0 {
				jp.Variants = append(jp.Variants, jsonVariant{Owner: l.owner, Attr: l.attr, Value: l.value, Default: strings.Contains(l.cond, ":not(["+l.attr+"])")})
				i = len(jp.Variants) - 1
			}
			for _, t := range bothTokens([]layer{l}) {
				if !slices.Contains(jp.Variants[i].Tokens, t) {
					jp.Variants[i].Tokens = append(jp.Variants[i].Tokens, t)
				}
			}
		}
		out = append(out, jp)
	}
	for _, u := range g.unmapped {
		out = append(out, jsonPart{From: u.from, Tokens: bothTokens(u.layers)})
	}
	sourceTokens := map[string][]string{}
	var all []string
	for _, c := range components {
		sourceTokens[c] = g.sourceTokens(c)
		all = append(all, sourceTokens[c]...)
	}
	b, _ := json.MarshalIndent(map[string]any{"shadcn": shadcnSHA, "style": g.style, "components": components, "parts": out, "source_tokens": sourceTokens, "logical": g.logicalMap(all), "groups": g.groupOwners(k)}, "", " ")
	return append(b, '\n')
}

func (g *gen) logicalMap(tokens []string) map[string]string {
	out := map[string]string{}
	if g.physical {
		return out
	}
	for _, t := range tokens {
		if l := rtlClasses(g.fix(t)); len(l) == 1 && l[0] != t {
			out[t] = l[0]
		}
	}
	return out
}

func (g *gen) ownGroup(name, kind string) bool {
	key := name + "|" + kind
	if v, ok := g.ownGroups[key]; ok {
		return v
	}
	found := false
	if s := g.sources[name]; s != nil {
		for _, loc := range stringLit.FindAllStringIndex(s.text, -1) {
			if strings.HasSuffix(s.text[:loc[0]], "role=") {
				continue
			}
			for _, tok := range strings.Fields(s.text[loc[0]+1 : loc[1]-1]) {
				if tok == kind || slices.Contains(strings.Fields(g.styles[tok]), kind) {
					found = true
				}
			}
		}
	}
	g.ownGroups[key] = found
	return found
}

func (g *gen) scopeGroups(tok string) string {
	segs := splitTopColon(tok)
	changed := false
	for i, seg := range segs[:len(segs)-1] {
		for _, kind := range []string{"group", "peer"} {
			if strings.HasPrefix(seg, kind+"-") && !topLevelSlash(seg) && g.ownGroup(g.where, kind) {
				segs[i] = seg + "/kit-" + g.where
				changed = true
			}
		}
	}
	if !changed {
		return tok
	}
	scoped := strings.Join(segs, ":")
	g.note("unnamed group or peer scoped to its own component", "%s -> %s", tok, scoped)
	return scoped
}

func topLevelSlash(s string) bool {
	depth := 0
	for _, r := range s {
		switch r {
		case '[', '(':
			depth++
		case ']', ')':
			depth--
		case '/':
			if depth == 0 {
				return true
			}
		}
	}
	return false
}

var stringLit = regexp.MustCompile("\"(?:[^\"\\\\\n]|\\\\.)*\"|'(?:[^'\\\\\n]|\\\\.)*'|`[^`]*`")

func (g *gen) sourceTokens(name string) []string {
	seen := map[string]bool{}
	var visit func(n string)
	add := func(tok string) {
		fixed := g.fix(tok)
		for _, t := range append([]string{tok, fixed}, rtlClasses(fixed)...) {
			seen[t] = true
		}
	}
	files := map[string]bool{}
	visit = func(n string) {
		s := g.sources[n]
		if s == nil || files[n] {
			return
		}
		files[n] = true
		for _, lit := range stringLit.FindAllString(s.text, -1) {
			for _, tok := range strings.Fields(lit[1 : len(lit)-1]) {
				add(tok)
				if rule, ok := g.styles[tok]; ok {
					for _, c := range strings.Fields(rule) {
						add(c)
					}
				}
			}
		}
		for _, dep := range s.imports {
			visit(dep)
		}
	}
	visit(name)
	return sortedKeys(seen)
}
