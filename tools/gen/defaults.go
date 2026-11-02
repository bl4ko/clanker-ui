package main

import (
	"fmt"
	"regexp"
	"strings"
)

var attrTest = regexp.MustCompile(`\[(data-[a-z-]+)="?([^"\]]+)"?\]`)

func fnName(s string, open int) string {
	k := open
	for k > 0 && (isIdent(s[k-1]) || s[k-1] == '-') {
		k--
	}
	if k > 0 && s[k-1] == ':' {
		return s[k-1 : open]
	}
	return ""
}

func levelBounds(s string, i, j int) (int, byte, int, byte) {
	a, l, depth := 0, byte(0), 0
	for k := i - 1; k >= 0; k-- {
		c := s[k]
		switch {
		case c == ')' || c == ']':
			depth++
		case c == '(' || c == '[':
			if depth == 0 {
				a, l = k+1, '('
				k = -1
				continue
			}
			depth--
		case depth == 0 && c == ' ' && strings.IndexByte(",(", prevChar(s, k)) >= 0:
		case depth == 0 && strings.IndexByte(" >+~,", c) >= 0:
			a, l = k+1, c
			k = -1
			continue
		}
	}
	z, r := len(s), byte(0)
	depth = 0
	for k := j; k < len(s); k++ {
		c := s[k]
		switch {
		case c == '(' || c == '[':
			depth++
		case c == ')' || c == ']':
			if depth == 0 {
				return a, l, k, ')'
			}
			depth--
		case depth == 0 && c == ' ' && strings.IndexByte(",)", nextChar(s, k)) >= 0:
		case depth == 0 && strings.IndexByte(" >+~,", c) >= 0:
			return a, l, k, c
		}
	}
	return a, l, z, r
}

func prevChar(s string, k int) byte {
	for k--; k >= 0; k-- {
		if s[k] != ' ' {
			return s[k]
		}
	}
	return 0
}

func nextChar(s string, k int) byte {
	for k++; k < len(s); k++ {
		if s[k] != ' ' {
			return s[k]
		}
	}
	return 0
}

func compoundAround(s string, i, j int) (int, int) {
	for {
		a, l, z, r := levelBounds(s, i, j)
		if l != '(' && l != ',' || r != ')' && r != ',' {
			return a, z
		}
		open := enclosingOpen(s, a-1)
		if open < 0 {
			return a, z
		}
		fn := fnName(s, open)
		if fn != ":is" && fn != ":where" && fn != ":not" {
			return a, z
		}
		end, err := matchFrom(s, open)
		if err != nil {
			return a, z
		}
		i, j = open-len(fn), end
	}
}

func enclosingOpen(s string, k int) int {
	depth := 0
	for ; k >= 0; k-- {
		switch s[k] {
		case ')':
			depth++
		case '(':
			if depth == 0 {
				return k
			}
			depth--
		}
	}
	return -1
}

func stripHas(s string) string {
	for {
		i := strings.Index(s, ":has(")
		if i < 0 {
			return s
		}
		end, err := matchFrom(s, i+4)
		if err != nil {
			return s
		}
		s = s[:i] + s[end:]
	}
}

var slotIn = regexp.MustCompile(`\[data-slot="([a-z0-9-]+)"\]`)

func (g *gen) rewriteDefaults(sel string) string {
	if len(g.defaulted) == 0 {
		return sel
	}
	var b strings.Builder
	last := 0
	for _, m := range attrTest.FindAllStringSubmatchIndex(sel, -1) {
		attr, val := sel[m[2]:m[3]], sel[m[4]:m[5]]
		slots := g.defaulted[[2]string{attr, val}]
		if len(slots) == 0 {
			continue
		}
		a, z := compoundAround(sel, m[0], m[1])
		compound := stripHas(sel[a:z])
		if strings.Contains(compound, ":not(["+attr+"])") {
			continue
		}
		var hit, miss []string
		for _, sm := range slotIn.FindAllStringSubmatch(compound, -1) {
			if containsStr(slots, sm[1]) {
				hit = append(hit, sm[1])
			} else {
				miss = append(miss, sm[1])
			}
		}
		if len(hit) == 0 && (len(miss) > 0 || len(slots) != 1) {
			continue
		}
		repl := fmt.Sprintf(`:is([%s="%s"], :not([%s]))`, attr, val, attr)
		if len(hit) == 0 {
			hit = slots
		}
		if len(miss) > 0 || len(slotIn.FindAllString(compound, -1)) == 0 {
			var sels []string
			for _, h := range hit {
				sels = append(sels, g.kit.slot(h))
			}
			repl = fmt.Sprintf(`:is([%s="%s"], :where(%s):not([%s]))`, attr, val, strings.Join(sels, ", "), attr)
		}
		b.WriteString(sel[last:m[0]])
		b.WriteString(repl)
		last = m[1]
	}
	b.WriteString(sel[last:])
	return b.String()
}

func containsStr(list []string, s string) bool {
	for _, x := range list {
		if x == s {
			return true
		}
	}
	return false
}

func (g *gen) defaultsPass(r *cssRule) {
	for _, it := range r.items {
		if it.rule == nil {
			continue
		}
		if !strings.HasPrefix(it.rule.prelude, "@") {
			it.rule.prelude = g.rewriteDefaults(it.rule.prelude)
		}
		g.defaultsPass(it.rule)
	}
}
