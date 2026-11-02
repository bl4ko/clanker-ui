package main

import (
	"fmt"
	"regexp"
	"strings"
)

type cssItem struct {
	decl string
	rule *cssRule
}

type cssRule struct {
	prelude string
	items   []cssItem
}

func parseCSS(src string) (*cssRule, error) {
	root := &cssRule{}
	stack := []*cssRule{root}
	var buf strings.Builder
	flush := func() {
		if t := strings.TrimSpace(buf.String()); t != "" {
			top := stack[len(stack)-1]
			top.items = append(top.items, cssItem{decl: t})
		}
		buf.Reset()
	}
	depth := 0
	for i := 0; i < len(src); i++ {
		c := src[i]
		switch {
		case c == '"' || c == '\'':
			j := i + 1
			for j < len(src) && src[j] != c {
				if src[j] == '\\' {
					j++
				}
				j++
			}
			buf.WriteString(src[i:min(j+1, len(src))])
			i = j
		case c == '/' && i+1 < len(src) && src[i+1] == '*':
			end := strings.Index(src[i+2:], "*/")
			if end < 0 {
				return nil, fmt.Errorf("unclosed comment")
			}
			i += end + 3
		case c == '(':
			depth++
			buf.WriteByte(c)
		case c == ')':
			depth--
			buf.WriteByte(c)
		case depth > 0:
			buf.WriteByte(c)
		case c == '{':
			r := &cssRule{prelude: strings.TrimSpace(buf.String())}
			buf.Reset()
			top := stack[len(stack)-1]
			top.items = append(top.items, cssItem{rule: r})
			stack = append(stack, r)
		case c == '}':
			flush()
			if len(stack) == 1 {
				return nil, fmt.Errorf("unbalanced }")
			}
			stack = stack[:len(stack)-1]
		case c == ';':
			flush()
		default:
			buf.WriteByte(c)
		}
	}
	flush()
	if len(stack) != 1 {
		return nil, fmt.Errorf("unclosed block")
	}
	return root, nil
}

func (r *cssRule) write(b *strings.Builder, indent string) {
	for _, it := range r.items {
		if it.rule == nil {
			fmt.Fprintf(b, "%s%s;\n", indent, it.decl)
			continue
		}
		fmt.Fprintf(b, "%s%s {\n", indent, it.rule.prelude)
		it.rule.write(b, indent+"  ")
		fmt.Fprintf(b, "%s}\n", indent)
	}
}

func (r *cssRule) String() string {
	var b strings.Builder
	r.write(&b, "")
	return b.String()
}

var lineBreak = regexp.MustCompile(`\s*\n\s*`)

func joinLines(r *cssRule) {
	for i := range r.items {
		if it := &r.items[i]; it.rule != nil {
			it.rule.prelude = lineBreak.ReplaceAllString(it.rule.prelude, " ")
			joinLines(it.rule)
		} else {
			it.decl = lineBreak.ReplaceAllString(it.decl, " ")
		}
	}
}

func strayRule(r *cssRule) string {
	for _, it := range r.items {
		s := it.decl
		if it.rule != nil {
			s = it.rule.prelude
		}
		if !strings.HasPrefix(s, "@layer ") && !strings.HasPrefix(s, "@property ") && !strings.HasPrefix(s, "@keyframes ") {
			return s
		}
	}
	return ""
}

func (g *gen) layerStray(r *cssRule) {
	var util *cssRule
	var keep, stray []cssItem
	for _, it := range r.items {
		switch {
		case it.rule != nil && it.rule.prelude == "@layer clanker.utilities":
			util = it.rule
			keep = append(keep, it)
		case it.rule != nil && strayRule(&cssRule{items: []cssItem{it}}) != "":
			stray = append(stray, it)
		default:
			keep = append(keep, it)
		}
	}
	if len(stray) == 0 {
		return
	}
	if util == nil {
		util = &cssRule{prelude: "@layer clanker.utilities"}
		keep = append(keep, cssItem{rule: util})
	}
	have := map[string]bool{}
	for _, it := range util.items {
		have[(&cssRule{items: []cssItem{it}}).String()] = true
	}
	for _, it := range stray {
		s := (&cssRule{items: []cssItem{it}}).String()
		if have[s] {
			g.note("rule outside a layer dropped (same rule in @layer clanker.utilities)", "%s", it.rule.prelude)
			continue
		}
		g.note("rule outside a layer moved into @layer clanker.utilities", "%s", it.rule.prelude)
		util.items = append(util.items, it)
	}
	r.items = keep
}

func declProp(d string) string {
	p, _, _ := strings.Cut(d, ":")
	return strings.TrimSpace(p)
}

const colorMixSupports = "@supports (color: color-mix(in lab, red, red))"

func isPropertyFallback(prelude string) bool {
	return strings.HasPrefix(prelude, "@supports") && strings.Contains(prelude, "margin-trim") && strings.Contains(prelude, "-moz-orient")
}

func dropFallbacks(r *cssRule) int {
	n := 0
	var out []cssItem
	for _, it := range r.items {
		if it.rule == nil {
			out = append(out, it)
			continue
		}
		if isPropertyFallback(it.rule.prelude) {
			n++
			continue
		}
		n += dropFallbacks(it.rule)
		if it.rule.prelude != colorMixSupports {
			out = append(out, it)
			continue
		}
		for _, inner := range it.rule.items {
			if inner.rule == nil {
				out = append(out, inner)
				continue
			}
			props := map[string]bool{}
			for _, d := range inner.rule.items {
				if d.rule == nil {
					props[declProp(d.decl)] = true
				}
			}
			for k := len(out) - 1; k >= 0; k-- {
				prev := out[k].rule
				if prev == nil || prev.prelude != inner.rule.prelude {
					continue
				}
				var keep []cssItem
				for _, d := range prev.items {
					if d.rule != nil || !props[declProp(d.decl)] {
						keep = append(keep, d)
					}
				}
				prev.items = keep
				if len(keep) == 0 {
					out = append(out[:k], out[k+1:]...)
				}
				break
			}
			out = append(out, inner)
			n++
		}
	}
	r.items = out
	return n
}

var (
	selectorClass = regexp.MustCompile(`\.(-?[A-Za-z_][\w-]*(?:\\.[\w-]*)*)`)
	bracketed     = regexp.MustCompile(`\[[^\]]*\]|"[^"]*"`)
)

func (g *gen) classSelectors(r *cssRule) {
	for _, it := range r.items {
		if it.rule == nil {
			continue
		}
		if p := it.rule.prelude; !strings.HasPrefix(p, "@") {
			for _, m := range selectorClass.FindAllStringSubmatch(bracketed.ReplaceAllString(p, "[]"), -1) {
				if m[1] == "sr-only" || m[1] == "shimmer" {
					continue
				}
				g.note("selector with a class that kit markup does not set", ".%s in %s", m[1], trunc(p, 120))
			}
		}
		g.classSelectors(it.rule)
	}
}
