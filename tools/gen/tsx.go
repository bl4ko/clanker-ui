package main

import (
	"fmt"
	"regexp"
	"strings"
)

type attr struct {
	name   string
	str    string
	isStr  bool
	expr   string
	spread bool
	elem   *elem
}

type elem struct {
	tag    string
	attrs  []attr
	fn     *function
	parent *elem
}

type function struct {
	name     string
	file     *source
	defaults map[string]string
	params   map[string]bool
	context  map[string]bool
	jsx      map[string]*elem
	elems    []*elem
}

type cvaDef struct {
	base     string
	keys     []string
	variants map[string][]variantValue
	defaults map[string]string
}

type variantValue struct {
	value   string
	classes string
}

type source struct {
	text    string
	name    string
	funcs   map[string]*function
	order   []string
	cvas    map[string]*cvaDef
	imports map[string]string
}

var (
	topLevel   = regexp.MustCompile(`(?m)^(?:export\s+)?(function|const|let|type|interface|import|export)\b`)
	funcHead   = regexp.MustCompile(`^(?:export\s+)?function\s+(\w+)\s*\(`)
	cvaHead    = regexp.MustCompile(`^const\s+(\w+)\s*=\s*cva\(`)
	paramDef   = regexp.MustCompile(`(\w+)\s*=\s*("[^"]*"|-?\d+(?:\.\d+)?|true|false)`)
	importLine = regexp.MustCompile(`(?m)^import\s*\{([^}]*)\}\s*from\s*"@/registry/bases/base/ui/([\w-]+)"`)
	jsxOpen    = regexp.MustCompile(`<([A-Za-z][\w.]*)[\s/>]`)
	jsxClose   = regexp.MustCompile(`</([A-Za-z][\w.]*)\s*>`)
	useRender  = regexp.MustCompile(`\buseRender\(`)
	nullishJSX = regexp.MustCompile(`^\w+\s*\?\?\s*<`)
	jsxDefault = regexp.MustCompile(`(\w+)\s*=\s*<`)
	hookVars   = regexp.MustCompile(`const\s*\{([^}]*)\}\s*=\s*(?:React\.)?use[A-Z]\w*\(`)
)

func parseSource(name, text string) (*source, error) {
	s := &source{text: text, name: name, funcs: map[string]*function{}, cvas: map[string]*cvaDef{}, imports: map[string]string{}}
	for _, m := range importLine.FindAllStringSubmatch(text, -1) {
		for _, id := range strings.Split(m[1], ",") {
			if id = strings.TrimSpace(id); id != "" && !strings.HasPrefix(id, "type ") {
				s.imports[id] = m[2]
			}
		}
	}
	starts := topLevel.FindAllStringIndex(text, -1)
	for i, st := range starts {
		end := len(text)
		if i+1 < len(starts) {
			end = starts[i+1][0]
		}
		chunk := text[st[0]:end]
		if m := funcHead.FindStringSubmatch(chunk); m != nil {
			f, err := parseFunction(s, m[1], chunk)
			if err != nil {
				return nil, fmt.Errorf("%s: %s: %w", name, m[1], err)
			}
			s.funcs[f.name] = f
			s.order = append(s.order, f.name)
		} else if m := cvaHead.FindStringSubmatchIndex(chunk); m != nil {
			c, err := parseCva(chunk[m[1]:])
			if err != nil {
				return nil, fmt.Errorf("%s: cva %s: %w", name, chunk[m[2]:m[3]], err)
			}
			s.cvas[chunk[m[2]:m[3]]] = c
		}
	}
	return s, nil
}

func parseFunction(s *source, name, chunk string) (*function, error) {
	f := &function{name: name, file: s, defaults: map[string]string{}, params: map[string]bool{}, context: map[string]bool{}, jsx: map[string]*elem{}}
	open := strings.Index(chunk, "(")
	close, err := matchFrom(chunk, open)
	if err != nil {
		return nil, err
	}
	for _, m := range paramDef.FindAllStringSubmatch(chunk[open:close], -1) {
		f.defaults[m[1]] = strings.Trim(m[2], `"`)
	}
	for _, p := range destructured(chunk[open+1 : close-1]) {
		f.params[p] = true
	}
	for _, m := range jsxDefault.FindAllStringSubmatchIndex(chunk[:close], -1) {
		if e, _, err := parseElement(chunk, m[1]-1); err == nil {
			e.fn = f
			f.jsx[chunk[m[2]:m[3]]] = e
		}
	}
	body := chunk[close:]
	for _, m := range hookVars.FindAllStringSubmatch(body, -1) {
		for _, p := range destructured("{" + m[1] + "}") {
			if !f.params[p] {
				f.context[p] = true
			}
		}
	}
	var stack []*elem
	closeTags := func(text string) {
		for _, m := range jsxClose.FindAllStringSubmatch(text, -1) {
			for i := len(stack) - 1; i >= 0; i-- {
				if stack[i].tag == m[1] {
					stack = stack[:i]
					break
				}
			}
		}
	}
	for pos := 0; pos < len(body); {
		loc := jsxOpen.FindStringSubmatchIndex(body[pos:])
		hook := useRender.FindStringIndex(body[pos:])
		if hook != nil && (loc == nil || hook[0] < loc[0]) {
			e, next, err := parseUseRender(body, pos+hook[1]-1)
			if err != nil {
				return nil, err
			}
			e.fn = f
			f.elems = append(f.elems, e)
			pos = next
			continue
		}
		if loc == nil {
			break
		}
		start := pos + loc[0]
		if start > 0 && isIdent(body[start-1]) {
			pos = start + 1
			continue
		}
		e, next, err := parseElement(body, start)
		if err != nil {
			return nil, err
		}
		closeTags(body[pos:start])
		e.fn = f
		if len(stack) > 0 {
			e.parent = stack[len(stack)-1]
		}
		if !strings.HasSuffix(body[:next], "/>") {
			stack = append(stack, e)
		}
		f.elems = append(f.elems, e)
		pos = next
	}
	return f, nil
}

func destructured(params string) []string {
	params = strings.TrimSpace(params)
	i := strings.IndexByte(params, '{')
	if i < 0 {
		return nil
	}
	end, err := matchFrom(params, i)
	if err != nil {
		return nil
	}
	var out []string
	for _, item := range splitTop(params[i+1:end-1], ',') {
		if strings.HasPrefix(item, "...") {
			continue
		}
		item, _, _ = strings.Cut(item, "=")
		if _, alias, ok := strings.Cut(item, ":"); ok {
			item = alias
		}
		if item = strings.TrimSpace(item); identifier.MatchString(item) {
			out = append(out, item)
		}
	}
	return out
}

func parseUseRender(body string, open int) (*elem, int, error) {
	end, err := matchFrom(body, open)
	if err != nil {
		return nil, 0, err
	}
	cfg, err := parseObject(body[open+1 : end-1])
	if err != nil {
		return nil, 0, fmt.Errorf("useRender: %w", err)
	}
	e := &elem{tag: "div"}
	for _, kv := range cfg {
		switch kv[0] {
		case "defaultTagName":
			if t, ok := stringLiteral(kv[1]); ok {
				e.tag = t
			}
		case "props":
			call := kv[1]
			p := strings.IndexByte(call, '(')
			if p < 0 {
				continue
			}
			pend, err := matchFrom(call, p)
			if err != nil {
				return nil, 0, err
			}
			for _, arg := range splitTop(call[p+1:pend-1], ',') {
				if !strings.HasPrefix(arg, "{") {
					e.attrs = append(e.attrs, attr{name: arg, spread: true, expr: "..." + arg})
					continue
				}
				obj, err := parseObject(arg)
				if err != nil {
					return nil, 0, err
				}
				for _, p := range obj {
					a := attr{name: p[0], expr: p[1]}
					if v, ok := stringLiteral(p[1]); ok {
						a.str, a.isStr = v, true
					}
					e.attrs = append(e.attrs, a)
				}
			}
		case "state":
			obj, err := parseObject(kv[1])
			if err != nil {
				return nil, 0, err
			}
			for _, p := range obj {
				a := attr{name: "data-" + kebab(p[0]), expr: p[1]}
				if v, ok := stringLiteral(p[1]); ok {
					a.str, a.isStr = v, true
				}
				e.attrs = append(e.attrs, a)
			}
		}
	}
	return e, end, nil
}

func isIdent(c byte) bool {
	return c == '_' || c == '$' || c >= '0' && c <= '9' || c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z'
}

func parseElement(src string, start int) (*elem, int, error) {
	i := start + 1
	j := i
	for j < len(src) && (isIdent(src[j]) || src[j] == '.') {
		j++
	}
	e := &elem{tag: src[i:j]}
	i = j
	for i < len(src) {
		for i < len(src) && strings.ContainsRune(" \t\r\n", rune(src[i])) {
			i++
		}
		if i >= len(src) {
			break
		}
		switch {
		case strings.HasPrefix(src[i:], "/>"):
			return e, i + 2, nil
		case src[i] == '>':
			return e, i + 1, nil
		case src[i] == '{':
			end, err := matchFrom(src, i)
			if err != nil {
				return nil, 0, err
			}
			inner := strings.TrimSpace(src[i+1 : end-1])
			e.attrs = append(e.attrs, attr{name: strings.TrimPrefix(inner, "..."), spread: strings.HasPrefix(inner, "..."), expr: inner})
			i = end
		default:
			k := i
			for k < len(src) && (isIdent(src[k]) || src[k] == '-' || src[k] == ':') {
				k++
			}
			if k == i {
				return nil, 0, fmt.Errorf("unexpected %q in <%s>", src[i:min(i+20, len(src))], e.tag)
			}
			a := attr{name: src[i:k]}
			i = k
			if i < len(src) && src[i] == '=' {
				i++
				if i >= len(src) {
					return nil, 0, fmt.Errorf("attribute %s of <%s> has no value", a.name, e.tag)
				}
				switch src[i] {
				case '"', '\'':
					q := strings.IndexByte(src[i+1:], src[i])
					if q < 0 {
						return nil, 0, fmt.Errorf("attribute %s of <%s>: unclosed string", a.name, e.tag)
					}
					a.str, a.isStr = src[i+1:i+1+q], true
					i += q + 2
				case '{':
					end, err := matchFrom(src, i)
					if err != nil {
						return nil, 0, err
					}
					a.expr = strings.TrimSpace(src[i+1 : end-1])
					jsx := a.expr
					if m := nullishJSX.FindStringIndex(jsx); m != nil {
						jsx = jsx[m[1]-1:]
					}
					if strings.HasPrefix(jsx, "<") {
						if sub, _, err := parseElement(jsx, 0); err == nil {
							a.elem = sub
						}
					} else if v, ok := stringLiteral(a.expr); ok {
						a.str, a.isStr = v, true
					}
					i = end
				}
			} else {
				a.str, a.isStr = "true", true
			}
			e.attrs = append(e.attrs, a)
		}
	}
	return nil, 0, fmt.Errorf("unclosed <%s>", e.tag)
}

func matchFrom(src string, open int) (int, error) {
	closer := map[byte]byte{'(': ')', '{': '}', '[': ']'}
	stack := []byte{closer[src[open]]}
	for i := open + 1; i < len(src); i++ {
		c := src[i]
		switch {
		case c == '/' && i+1 < len(src) && src[i+1] == '/':
			if nl := strings.IndexByte(src[i:], '\n'); nl >= 0 {
				i += nl
			} else {
				i = len(src)
			}
			continue
		case c == '/' && i+1 < len(src) && src[i+1] == '*':
			end := strings.Index(src[i+2:], "*/")
			if end < 0 {
				return 0, fmt.Errorf("unclosed comment")
			}
			i += end + 3
			continue
		}
		switch c {
		case '"', '\'':
			end, err := stringEnd(src, i)
			if err != nil {
				return 0, err
			}
			i = end
		case '`':
			end, err := templateEnd(src, i)
			if err != nil {
				return 0, err
			}
			i = end
		case '(', '{', '[':
			stack = append(stack, closer[c])
		case ')', '}', ']':
			if c != stack[len(stack)-1] {
				return 0, fmt.Errorf("unbalanced %q at %d", c, i)
			}
			stack = stack[:len(stack)-1]
			if len(stack) == 0 {
				return i + 1, nil
			}
		}
	}
	return 0, fmt.Errorf("unbalanced from %d", open)
}

func stringEnd(src string, open int) (int, error) {
	for i := open + 1; i < len(src); i++ {
		switch src[i] {
		case '\\':
			i++
		case src[open]:
			return i, nil
		case '\n':
			return 0, fmt.Errorf("unclosed string")
		}
	}
	return 0, fmt.Errorf("unclosed string")
}

func templateEnd(src string, open int) (int, error) {
	for i := open + 1; i < len(src); i++ {
		switch {
		case src[i] == '\\':
			i++
		case src[i] == '`':
			return i, nil
		case strings.HasPrefix(src[i:], "${"):
			end, err := matchFrom(src, i+1)
			if err != nil {
				return 0, err
			}
			i = end - 1
		}
	}
	return 0, fmt.Errorf("unclosed template")
}

func stringLiteral(expr string) (string, bool) {
	expr = strings.TrimSpace(expr)
	if len(expr) < 2 {
		return "", false
	}
	q := expr[0]
	if (q != '"' && q != '\'' && q != '`') || expr[len(expr)-1] != q || strings.IndexByte(expr[1:len(expr)-1], q) >= 0 || q == '`' && strings.Contains(expr, "${") {
		return "", false
	}
	return expr[1 : len(expr)-1], true
}

func splitTop(src string, sep byte) []string {
	var out []string
	depth, last := 0, 0
	for i := 0; i < len(src); i++ {
		switch c := src[i]; c {
		case '"', '\'':
			if q := strings.IndexByte(src[i+1:], c); q >= 0 {
				i += q + 1
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
			if c == sep && depth == 0 {
				out = append(out, strings.TrimSpace(src[last:i]))
				last = i + 1
			}
		}
	}
	if rest := strings.TrimSpace(src[last:]); rest != "" {
		out = append(out, rest)
	}
	return out
}

func parseObject(src string) ([][2]string, error) {
	src = strings.TrimSpace(src)
	if !strings.HasPrefix(src, "{") || !strings.HasSuffix(src, "}") {
		return nil, fmt.Errorf("not an object: %.40q", src)
	}
	var out [][2]string
	for _, p := range splitTop(src[1:len(src)-1], ',') {
		k, v, ok := strings.Cut(p, ":")
		if !ok {
			out = append(out, [2]string{p, p})
			continue
		}
		k = strings.TrimSpace(k)
		if s, ok := stringLiteral(k); ok {
			k = s
		}
		out = append(out, [2]string{k, strings.TrimSpace(v)})
	}
	return out, nil
}

func parseCva(rest string) (*cvaDef, error) {
	end, err := matchFrom("("+rest, 0)
	if err != nil {
		return nil, err
	}
	args := splitTop(rest[:end-2], ',')
	c := &cvaDef{variants: map[string][]variantValue{}, defaults: map[string]string{}}
	base, ok := stringLiteral(args[0])
	if !ok {
		return nil, fmt.Errorf("base is not a string literal")
	}
	c.base = base
	if len(args) < 2 {
		return c, nil
	}
	cfg, err := parseObject(args[1])
	if err != nil {
		return nil, err
	}
	for _, kv := range cfg {
		switch kv[0] {
		case "variants":
			keys, err := parseObject(kv[1])
			if err != nil {
				return nil, err
			}
			for _, key := range keys {
				values, err := parseObject(key[1])
				if err != nil {
					return nil, err
				}
				c.keys = append(c.keys, key[0])
				for _, v := range values {
					cls, ok := stringLiteral(v[1])
					if !ok {
						return nil, fmt.Errorf("variant %s=%s is not a string literal", key[0], v[0])
					}
					c.variants[key[0]] = append(c.variants[key[0]], variantValue{v[0], cls})
				}
			}
		case "defaultVariants":
			defs, err := parseObject(kv[1])
			if err != nil {
				return nil, err
			}
			for _, d := range defs {
				c.defaults[d[0]], _ = stringLiteral(d[1])
			}
		default:
			return nil, fmt.Errorf("unsupported cva key %q", kv[0])
		}
	}
	return c, nil
}

func (e *elem) get(name string) *attr {
	for i := range e.attrs {
		if !e.attrs[i].spread && e.attrs[i].name == name {
			return &e.attrs[i]
		}
	}
	return nil
}

func (e *elem) spreadAfter(name string) bool {
	seen := false
	for _, a := range e.attrs {
		if !a.spread && a.name == name {
			seen = true
		}
		if a.spread && seen {
			return true
		}
	}
	return false
}
