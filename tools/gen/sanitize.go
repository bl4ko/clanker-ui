package main

import (
	"fmt"
	"regexp"
	"slices"
	"strings"
)

var allowedAtRules = map[string]bool{
	"theme": true, "custom-variant": true, "utility": true, "property": true, "keyframes": true,
	"layer": true, "media": true, "supports": true, "container": true, "starting-style": true, "slot": true, "apply": true, "variant": true,
}

var (
	urlFunc  = regexp.MustCompile(`(?i)(-webkit-image-set|image-set|url|src)\(\s*(["']?)\s*([^"')\s]*)`)
	hexEsc   = regexp.MustCompile(`\\[0-9A-Fa-f]`)
	tokenKey = regexp.MustCompile(`^[a-z0-9-]+$`)
)

type unsafeInput struct {
	where, what string
}

func (e unsafeInput) Error() string {
	return fmt.Sprintf("unsafe input: %s: %s; the generator stops (only custom properties, plain rules, and @theme, @custom-variant, @utility, @variant, @apply, @slot, @property, @keyframes, @layer, @media, @supports, @container, @starting-style are allowed)", e.where, e.what)
}

func checkURLs(where, text string) error {
	for _, m := range urlFunc.FindAllStringSubmatch(text, -1) {
		fn, arg := strings.ToLower(m[1]), strings.ToLower(m[3])
		if fn == "url" && (strings.HasPrefix(arg, "data:") || strings.HasPrefix(arg, "#")) {
			continue
		}
		return unsafeInput{where, fmt.Sprintf("%s(%s...) loads a resource; only data: URIs and #fragments are allowed", fn, m[3])}
	}
	return nil
}

func checkCSS(where, src string, exact []string) error {
	start := true
	line := 1
	for i := 0; i < len(src); i++ {
		c := src[i]
		switch {
		case c == '\n':
			line++
		case c == '/' && i+1 < len(src) && src[i+1] == '*':
			end := strings.Index(src[i+2:], "*/")
			if end < 0 {
				return unsafeInput{fmt.Sprintf("%s:%d", where, line), "unclosed comment"}
			}
			line += strings.Count(src[i:i+2+end+2], "\n")
			i += end + 3
		case c == '"' || c == '\'':
			j := i + 1
			for j < len(src) && src[j] != c && src[j] != '\n' {
				if src[j] == '\\' {
					j++
				}
				j++
			}
			if j >= len(src) || src[j] != c {
				return unsafeInput{fmt.Sprintf("%s:%d", where, line), "unclosed string"}
			}
			i = j
			start = false
		case c == '{' || c == '}' || c == ';':
			start = true
		case c == ' ' || c == '\t' || c == '\r':
		case c < 0x20 && c != '\t' && c != '\n' && c != '\r':
			return unsafeInput{fmt.Sprintf("%s:%d", where, line), fmt.Sprintf("control byte 0x%02x outside a string or comment", c)}
		case c >= 0x80:
			return unsafeInput{fmt.Sprintf("%s:%d", where, line), "non-ASCII byte outside a string or comment (a byte order mark hides an at-rule)"}
		case c == '\\' && i+1 < len(src) && hexEsc.MatchString(src[i:i+2]):
			return unsafeInput{fmt.Sprintf("%s:%d", where, line), "hex escape outside a string"}
		case c == '@' && start:
			j := i + 1
			for j < len(src) && (isIdent(src[j]) || src[j] == '-' || src[j] == '\\') {
				j++
			}
			name := strings.ToLower(src[i+1 : j])
			at := fmt.Sprintf("%s:%d", where, line)
			if strings.Contains(name, "\\") {
				return unsafeInput{at, "escaped at-rule name @" + name}
			}
			if !allowedAtRules[name] {
				end := statementEnd(src, i)
				stmt := strings.TrimSpace(src[i:end])
				if (name == "import" || name == "source") && slices.Contains(exact, stmt) {
					i = end - 1
					start = false
					continue
				}
				return unsafeInput{at, fmt.Sprintf("@%s is not allowed (%s)", name, oneLine(trunc(stmt, 80)))}
			}
			start = false
			i = j - 1
		default:
			start = false
		}
	}
	return checkURLs(where, stripCSSComments(src))
}

func statementEnd(src string, i int) int {
	for j := i; j < len(src); j++ {
		switch src[j] {
		case '"', '\'':
			if k := strings.IndexByte(src[j+1:], src[j]); k >= 0 {
				j += k + 1
			}
		case ';':
			return j + 1
		case '{', '}':
			return j
		}
	}
	return len(src)
}

func stripCSSComments(src string) string {
	return blockComment.ReplaceAllString(src, " ")
}

func trunc(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}

func checkValue(where, v string) error {
	for _, bad := range []string{"{", "}", ";", "@", "\\", "/*", "*/", "<", ">"} {
		if strings.Contains(v, bad) {
			return unsafeInput{where, fmt.Sprintf("value %q has %q", trunc(v, 60), bad)}
		}
	}
	return checkURLs(where, v)
}

func checkClass(where, c string) error {
	for _, bad := range []string{"{", "}", ";", "/*", "*/"} {
		if strings.Contains(c, bad) {
			return unsafeInput{where, fmt.Sprintf("class %q has %q", trunc(c, 60), bad)}
		}
	}
	if hexEsc.MatchString(c) {
		return unsafeInput{where, fmt.Sprintf("class %q has a hex escape", trunc(c, 60))}
	}
	return checkURLs(where, c)
}
