package main

import (
	"fmt"
	"io/fs"
	"regexp"
	"slices"
	"strings"
)

var (
	customProp = regexp.MustCompile(`(?:^|[{;\s])(--[A-Za-z0-9_-]+)\s*:`)
	schemeName = regexp.MustCompile(`^[a-z]+$`)
)

func cssTop(src string) ([]string, error) {
	var out []string
	for i := 0; i < len(src); {
		if strings.ContainsRune(" \t\r\n", rune(src[i])) {
			i++
			continue
		}
		depth, j := 0, i
	scan:
		for ; j < len(src); j++ {
			switch c := src[j]; {
			case c == '"' || c == '\'':
				for j++; j < len(src) && src[j] != c; j++ {
					if src[j] == '\\' {
						j++
					}
				}
			case strings.HasPrefix(src[j:], "/*"):
				end := strings.Index(src[j+2:], "*/")
				if end < 0 {
					return nil, fmt.Errorf("css: open comment at byte %d", j)
				}
				j += end + 3
				if depth == 0 && i == j-end-3 {
					j++
					break scan
				}
			case c == '{':
				depth++
			case c == '}':
				if depth--; depth == 0 {
					j++
					break scan
				}
			case c == ';' && depth == 0:
				j++
				break scan
			}
		}
		if depth != 0 {
			return nil, fmt.Errorf("css: open block at byte %d", i)
		}
		out = append(out, src[i:min(j, len(src))])
		i = j
	}
	return out, nil
}

func cssBlock(rule string) (head, body string) {
	i := strings.IndexByte(rule, '{')
	if i < 0 || !strings.HasSuffix(rule, "}") {
		return strings.TrimSpace(rule), ""
	}
	return strings.TrimSpace(rule[:i]), rule[i+1 : len(rule)-1]
}

func rootDecls(tokens []string) map[string]string {
	out := map[string]string{}
	for _, layer := range tokens {
		_, body := cssBlock(layer)
		rules, err := cssTop(body)
		if err != nil {
			continue
		}
		for _, r := range rules {
			sel, decls := cssBlock(r)
			if strings.ReplaceAll(sel, " ", "") != ":root,:host" {
				continue
			}
			for _, d := range strings.Split(decls, ";") {
				if name, value, ok := strings.Cut(strings.TrimSpace(d), ":"); ok && strings.HasPrefix(name, "--") {
					out[strings.TrimSpace(name)] = strings.TrimSpace(value)
				}
			}
		}
	}
	return out
}

func docsStyleCSS(name string, base, style []byte, extra ...[]byte) ([]byte, error) {
	baseTop, err := cssTop(string(base))
	if err != nil {
		return nil, err
	}
	top, err := cssTop(string(style))
	if err != nil {
		return nil, err
	}
	scope := fmt.Sprintf(`@scope ([data-docs-style="%s"])`, name)
	var baseTokens, tokens []string
	props := map[string]bool{}
	baseAt := map[string]bool{}
	for _, r := range baseTop {
		head, body := cssBlock(r)
		switch {
		case head == "@layer clanker.tokens":
			baseTokens = append(baseTokens, r)
		case strings.HasPrefix(head, "@layer clanker."):
			for _, m := range customProp.FindAllStringSubmatch(body, -1) {
				props[m[1]] = true
			}
		case strings.HasPrefix(head, "@property") || strings.HasPrefix(head, "@keyframes"):
			baseAt[r] = true
		}
	}
	var b strings.Builder
	if strings.HasPrefix(top[0], "/*") {
		b.WriteString(top[0] + "\n")
		top = top[1:]
	}
	fmt.Fprintf(&b, "@layer clanker-docs-%s {\n@layer reset {\n%s {\n:not(svg, svg *), ::before, ::after, ::backdrop, ::placeholder, ::marker, ::file-selector-button { all: revert;", name, scope)
	for _, p := range slices.Sorted(func(yield func(string) bool) {
		for p := range props {
			if !yield(p) {
				return
			}
		}
	}) {
		fmt.Fprintf(&b, " %s: revert;", p)
	}
	b.WriteString(" }\n}\n}\n")
	own := len(top)
	for _, src := range extra {
		more, err := cssTop(string(src))
		if err != nil {
			return nil, err
		}
		top = append(top, more...)
	}
	for i, r := range top {
		head, body := cssBlock(r)
		switch {
		case strings.HasPrefix(head, "@property") || strings.HasPrefix(head, "@keyframes"):
			if i < own && !baseAt[r] {
				return nil, fmt.Errorf("docs style %s: %s is not in the default style", name, head)
			}
		case head == "@layer clanker.tokens":
			tokens = append(tokens, r)
		case strings.HasPrefix(head, "@layer") && body == "" && strings.HasSuffix(r, ";"):
			b.WriteString(r + "\n")
		case strings.HasPrefix(head, "@layer "):
			fmt.Fprintf(&b, "%s {\n%s {\n%s\n}\n}\n", head, scope, body)
		case i >= own:
		default:
			return nil, fmt.Errorf("docs style %s: %q is outside a layer", name, head)
		}
	}
	have, want := rootDecls(baseTokens), rootDecls(tokens)
	var add []string
	for _, k := range slices.Sorted(func(yield func(string) bool) {
		for k := range want {
			if !yield(k) {
				return
			}
		}
	}) {
		if have[k] != want[k] {
			add = append(add, k+": "+want[k]+";")
		}
	}
	if len(add) > 0 {
		fmt.Fprintf(&b, "@layer clanker.tokens {\n%s {\n:scope { %s }\n}\n}\n", scope, strings.Join(add, " "))
	}
	b.WriteString("}\n")
	return []byte(b.String()), nil
}

func (d *docsSite) hasScheme(name string) bool {
	css := string(d.assets["clanker-ui-themes.css"])
	return schemeName.MatchString(name) && (strings.Contains(css, `[data-scheme~="`+name+`"]`) || strings.Contains(css, `[data-scheme~=`+name+`]`))
}

func (d *docsSite) loadStyles(fsys fs.FS) error {
	d.previews = map[string]navItem{}
	for i, s := range d.catalog.Files.Styles {
		d.styles = append(d.styles, s.Name)
		if i == 0 || !schemeName.MatchString(s.Name) {
			continue
		}
		src, err := fs.ReadFile(fsys, s.CSS)
		if err != nil {
			return err
		}
		if d.assets["style-"+s.Name+".css"], err = docsStyleCSS(s.Name, d.assets["clanker-ui.css"], src, d.assets["examples.css"]); err != nil {
			return err
		}
	}
	if len(d.styles) == 0 {
		return nil
	}
	for _, g := range d.nav.Groups {
		for _, item := range g.Items {
			if item.Style == "" && item.Scheme == "" {
				continue
			}
			if item.Style != "" && (!slices.Contains(d.styles, item.Style) || item.Style == d.styles[0]) || item.Scheme != "" && !d.hasScheme(item.Scheme) {
				return fmt.Errorf("docs/nav.json: %s: unknown style %q or scheme %q", item.Href, item.Style, item.Scheme)
			}
			d.previews[item.Href] = item
		}
	}
	return nil
}
