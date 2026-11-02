package main

import (
	"fmt"
	"regexp"
	"strings"
)

type cnode struct {
	op   string
	args []*cnode
	text string
}

var condToken = regexp.MustCompile(`^\s*(\|\||&&|===|!==|==|!=|!|\(|\)|"[^"]*"|'[^']*'|[A-Za-z_$][\w$.]*|-?\d+(?:\.\d+)?)`)

func parseCond(src string) (*cnode, error) {
	var toks []string
	rest := src
	for strings.TrimSpace(rest) != "" {
		m := condToken.FindStringSubmatch(rest)
		if m == nil {
			return nil, fmt.Errorf("condition %q: unexpected %q", src, strings.TrimSpace(rest))
		}
		toks = append(toks, m[1])
		rest = rest[len(m[0]):]
	}
	p := &condParser{toks: toks}
	n, err := p.or()
	if err != nil {
		return nil, err
	}
	if p.i != len(toks) {
		return nil, fmt.Errorf("condition %q: extra %q", src, toks[p.i])
	}
	return n, nil
}

type condParser struct {
	toks []string
	i    int
}

func (p *condParser) peek() string {
	if p.i < len(p.toks) {
		return p.toks[p.i]
	}
	return ""
}

func (p *condParser) or() (*cnode, error) {
	return p.binary("||", "or", p.and)
}

func (p *condParser) and() (*cnode, error) {
	return p.binary("&&", "and", p.eq)
}

func (p *condParser) binary(tok, op string, next func() (*cnode, error)) (*cnode, error) {
	left, err := next()
	if err != nil {
		return nil, err
	}
	args := []*cnode{left}
	for p.peek() == tok {
		p.i++
		right, err := next()
		if err != nil {
			return nil, err
		}
		args = append(args, right)
	}
	if len(args) == 1 {
		return left, nil
	}
	return &cnode{op: op, args: args}, nil
}

func (p *condParser) eq() (*cnode, error) {
	left, err := p.unary()
	if err != nil {
		return nil, err
	}
	switch t := p.peek(); t {
	case "===", "==", "!==", "!=":
		p.i++
		right, err := p.unary()
		if err != nil {
			return nil, err
		}
		n := &cnode{op: "eq", args: []*cnode{left, right}}
		if strings.HasPrefix(t, "!") {
			n = &cnode{op: "not", args: []*cnode{n}}
		}
		return n, nil
	}
	return left, nil
}

func (p *condParser) unary() (*cnode, error) {
	switch t := p.peek(); {
	case t == "!":
		p.i++
		n, err := p.unary()
		if err != nil {
			return nil, err
		}
		return &cnode{op: "not", args: []*cnode{n}}, nil
	case t == "(":
		p.i++
		n, err := p.or()
		if err != nil {
			return nil, err
		}
		if p.peek() != ")" {
			return nil, fmt.Errorf("missing )")
		}
		p.i++
		return n, nil
	case t == "":
		return nil, fmt.Errorf("unexpected end")
	case t[0] == '"' || t[0] == '\'':
		p.i++
		return &cnode{op: "str", text: t[1 : len(t)-1]}, nil
	case t == "true" || t == "false":
		p.i++
		return &cnode{op: "bool", text: t}, nil
	default:
		p.i++
		return &cnode{op: "ident", text: t}, nil
	}
}

type cres struct {
	sel                string
	always, never      bool
	attr, value, owner string
}

type binding struct {
	attr, owner, def string
	self             bool
}

func truthy(v string) bool {
	return v != "" && v != "false" && v != "0" && v != "undefined" && v != "null"
}

func (g *gen) bind(f *function, target *elem, ident string) (binding, bool) {
	name := strings.TrimPrefix(ident, "context.")
	for _, e := range allElems(f) {
		for _, a := range e.attrs {
			if a.spread || a.isStr || strings.TrimSpace(a.expr) != ident && !strings.HasSuffix(strings.TrimSpace(a.expr), "|| "+name) {
				continue
			}
			attrName := a.name
			if !strings.HasPrefix(attrName, "data-") {
				if e.tag == "" || e.tag[0] < 'A' || e.tag[0] > 'Z' || attrName != "orientation" {
					continue
				}
				attrName = "data-orientation"
			}
			b := binding{attr: attrName, def: f.defaults[name]}
			if e == target || target != nil && sameElem(e, target) {
				b.self = true
				return b, true
			}
			owner := g.slotOf(f, e)
			if owner == "" {
				continue
			}
			b.owner = owner
			return b, true
		}
	}
	if f.params[name] {
		b := binding{attr: "data-" + kebab(name), def: f.defaults[name]}
		root := propsTarget(f)
		if root == nil || root == target || target != nil && sameElem(root, target) {
			b.self = true
			return b, true
		}
		b.owner = g.slotOf(f, root)
		if b.owner == "" {
			b.owner = g.rootSels[f]
		}
		return b, b.owner != ""
	}
	if f.context[name] || strings.HasPrefix(ident, "context.") {
		owner, provider := g.fileRoot(f.file)
		if owner == "" {
			return binding{}, false
		}
		b := binding{attr: "data-" + kebab(name), owner: owner}
		if provider != nil {
			b.def = provider.defaults[name]
		}
		return b, true
	}
	return binding{}, false
}

func (g *gen) bindProp(f *function, target *elem, ident string) (binding, bool) {
	name, ok := strings.CutPrefix(ident, "props.")
	if !ok || !identifier.MatchString(name) {
		return binding{}, false
	}
	b := binding{attr: "data-" + kebab(name)}
	root := propsTarget(f)
	if root == nil || root == target || target != nil && sameElem(root, target) {
		b.self = true
		return b, true
	}
	b.owner = g.slotOf(f, root)
	if b.owner == "" {
		b.owner = g.rootSels[f]
	}
	if b.owner == "" {
		g.note("unmapped construct", "%s/%s: %s has no element with a data-slot for data-%s; the condition is false", f.file.name, f.name, ident, kebab(name))
		return binding{}, false
	}
	g.note("prop read from props (markup sets the attribute)", "%s/%s: %s -> %s[%s]", f.file.name, f.name, ident, b.owner, b.attr)
	return b, true
}

func (g *gen) unknownIdent(f *function, ident string) {
	if f.params[ident] || notFree[ident] || strings.HasPrefix(ident, "props.") {
		return
	}
	g.note("unmapped construct", "%s/%s: %s is not a prop, a context value, or a constant; the condition is false", f.file.name, f.name, ident)
}

func sameElem(a, b *elem) bool {
	return a.tag == b.tag && len(a.attrs) > 0 && len(b.attrs) > 0 && a.attrs[0].name == b.attrs[0].name && a.attrs[0].expr == b.attrs[0].expr && a.attrs[0].str == b.attrs[0].str && a.fn == b.fn
}

func allElems(f *function) []*elem {
	var out []*elem
	var walk func(e *elem)
	walk = func(e *elem) {
		out = append(out, e)
		for _, a := range e.attrs {
			if a.elem != nil {
				walk(a.elem)
			}
		}
	}
	for _, e := range f.elems {
		walk(e)
	}
	return out
}

func (g *gen) slotOf(f *function, e *elem) string {
	if a := e.get("data-slot"); a != nil && a.isStr {
		return g.kit.slot(a.str)
	}
	if e == propsTarget(f) {
		if s := g.rootSlots[f]; s != "" {
			return g.kit.slot(s)
		}
	}
	return ""
}

func (g *gen) fileRoot(s *source) (string, *function) {
	for _, name := range s.order {
		f := s.funcs[name]
		if g.rootSlots[f] == s.name {
			return g.kit.slot(s.name), f
		}
	}
	return "", nil
}

func attrIs(attr, value, def string) string {
	if value == def && def != "" {
		return fmt.Sprintf(`:is(:not([%s]), [%s="%s"])`, attr, attr, value)
	}
	return fmt.Sprintf(`[%s="%s"]`, attr, value)
}

func place(b binding, test string) string {
	if b.self {
		return ":where(" + test + ")"
	}
	return ":where(" + b.owner + test + " *)"
}

func (g *gen) evalCond(f *function, target *elem, n *cnode, scope map[string]string, free map[string]bool) (cres, error) {
	switch n.op {
	case "bool":
		return cres{always: n.text == "true", never: n.text == "false"}, nil
	case "str":
		return cres{always: n.text != "", never: n.text == ""}, nil
	case "ident":
		name := strings.TrimPrefix(n.text, "context.")
		if b, ok := g.bindProp(f, target, n.text); ok {
			return cres{sel: place(b, fmt.Sprintf(`[%s]:not([%s="false"])`, b.attr, b.attr)), attr: b.attr, owner: b.owner}, nil
		}
		if v, ok := scope[name]; ok && !free[name] && !strings.HasPrefix(n.text, "context.") {
			return cres{always: truthy(v), never: !truthy(v)}, nil
		}
		if !free[name] && !f.context[name] && !strings.HasPrefix(n.text, "context.") {
			g.unknownIdent(f, n.text)
			return cres{never: true}, nil
		}
		b, ok := g.bind(f, target, n.text)
		if !ok {
			return cres{}, fmt.Errorf("no attribute for %s", n.text)
		}
		return cres{sel: place(b, fmt.Sprintf(`[%s]:not([%s="false"])`, b.attr, b.attr)), attr: b.attr, owner: b.owner}, nil
	case "eq":
		l, r := n.args[0], n.args[1]
		if l.op != "ident" {
			l, r = r, l
		}
		if l.op != "ident" || r.op != "str" && r.op != "bool" {
			return cres{}, fmt.Errorf("unsupported comparison")
		}
		name := strings.TrimPrefix(l.text, "context.")
		if b, ok := g.bindProp(f, target, l.text); ok {
			return cres{sel: place(b, attrIs(b.attr, r.text, b.def)), attr: b.attr, value: r.text, owner: b.owner}, nil
		}
		if v, ok := scope[name]; ok && !free[name] && !strings.HasPrefix(l.text, "context.") {
			return cres{always: v == r.text, never: v != r.text}, nil
		}
		if !free[name] && !f.context[name] && !strings.HasPrefix(l.text, "context.") {
			g.unknownIdent(f, l.text)
			return cres{never: true}, nil
		}
		b, ok := g.bind(f, target, l.text)
		if !ok {
			return cres{}, fmt.Errorf("no attribute for %s", l.text)
		}
		return cres{sel: place(b, attrIs(b.attr, r.text, b.def)), attr: b.attr, value: r.text, owner: b.owner}, nil
	case "not":
		c, err := g.evalCond(f, target, n.args[0], scope, free)
		if err != nil {
			return cres{}, err
		}
		if c.always || c.never {
			return cres{always: c.never, never: c.always}, nil
		}
		out := cres{sel: ":not(" + c.sel + ")"}
		if c.attr != "" && c.value != "" && !strings.HasPrefix(c.value, "!") {
			out.attr, out.value, out.owner = c.attr, "!"+c.value, c.owner
		}
		return out, nil
	case "and", "or":
		var sels []string
		for _, a := range n.args {
			c, err := g.evalCond(f, target, a, scope, free)
			if err != nil {
				return cres{}, err
			}
			if n.op == "and" && c.never || n.op == "or" && c.always {
				return c, nil
			}
			if c.sel != "" {
				sels = append(sels, c.sel)
			}
		}
		switch {
		case len(sels) == 0:
			return cres{always: n.op == "and", never: n.op == "or"}, nil
		case n.op == "and":
			return cres{sel: strings.Join(sels, "")}, nil
		case len(sels) == 1:
			return cres{sel: sels[0]}, nil
		}
		return cres{sel: ":where(" + strings.Join(sels, ", ") + ")"}, nil
	}
	return cres{}, fmt.Errorf("unsupported %s", n.op)
}
