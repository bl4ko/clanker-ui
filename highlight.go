package main

import (
	"html"
	"html/template"
	"strings"
)

type hlToken struct {
	class string
	text  string
}

var (
	jsKeywords  = words("as async await break case catch class const continue debugger default delete do else export extends finally for from function get if import in instanceof let new of return set static super switch this throw try typeof var void while with yield")
	jsLiterals  = words("true false null undefined NaN Infinity")
	shKeywords  = words("if then else elif fi for in do done while until case esac function return export local set unset source")
	jsonLiteral = words("true false null")
)

func words(s string) map[string]bool {
	m := map[string]bool{}
	for _, w := range strings.Fields(s) {
		m[w] = true
	}
	return m
}

func highlightHTML(lang, src string) []template.HTML {
	var tokens []hlToken
	switch lang {
	case "html", "xml", "svg":
		tokens = tokHTML(src)
	case "css":
		tokens = tokCSS(src)
	case "js", "javascript", "mjs":
		tokens = tokJS(src)
	case "json":
		tokens = tokJSON(src)
	case "sh", "bash", "shell", "zsh", "console":
		tokens = tokSh(src)
	default:
		tokens = []hlToken{{"", src}}
	}
	lines := []template.HTML{""}
	for _, t := range tokens {
		for i, part := range strings.Split(t.text, "\n") {
			if i > 0 {
				lines = append(lines, "")
			}
			if part == "" {
				continue
			}
			text := html.EscapeString(part)
			if t.class != "" {
				text = `<span class="tk-` + t.class + `">` + text + "</span>"
			}
			lines[len(lines)-1] += template.HTML(text)
		}
	}
	return lines
}

type scanner struct {
	src    string
	i      int
	tokens []hlToken
}

func (s *scanner) emit(class string, end int) {
	if end <= s.i {
		return
	}
	text := s.src[s.i:end]
	if n := len(s.tokens); n > 0 && s.tokens[n-1].class == class {
		s.tokens[n-1].text += text
	} else {
		s.tokens = append(s.tokens, hlToken{class, text})
	}
	s.i = end
}

func (s *scanner) until(from int, stop string) int {
	if j := strings.Index(s.src[from:], stop); j >= 0 {
		return from + j + len(stop)
	}
	return len(s.src)
}

func (s *scanner) quoted(from int, quote byte, multiline bool) int {
	for j := from + 1; j < len(s.src); j++ {
		switch s.src[j] {
		case '\\':
			j++
		case quote:
			return j + 1
		case '\n':
			if !multiline {
				return j
			}
		}
	}
	return len(s.src)
}

func identByte(c byte, first bool) bool {
	return c == '_' || c == '$' || c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || !first && c >= '0' && c <= '9' || c >= 0x80
}

func (s *scanner) span(from int, ok func(byte) bool) int {
	j := from
	for j < len(s.src) && ok(s.src[j]) {
		j++
	}
	return j
}

func digit(c byte) bool { return c >= '0' && c <= '9' }

func spaceByte(c byte) bool { return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' }

func tokHTML(src string) []hlToken {
	s := &scanner{src: src}
	for s.i < len(src) {
		c := src[s.i]
		switch {
		case strings.HasPrefix(src[s.i:], "<!--"):
			s.emit("c", s.until(s.i+4, "-->"))
		case strings.HasPrefix(src[s.i:], "<!"):
			s.emit("k", s.until(s.i, ">"))
		case c == '<' && s.i+1 < len(src) && (identByte(src[s.i+1], true) || src[s.i+1] == '/'):
			s.tag()
		case c == '&':
			end := s.span(s.i+1, func(b byte) bool { return identByte(b, false) || b == '#' })
			if end < len(src) && src[end] == ';' {
				s.emit("e", end+1)
			} else {
				s.emit("", s.i+1)
			}
		default:
			end := s.i + 1
			for end < len(src) && src[end] != '<' && src[end] != '&' {
				end++
			}
			s.emit("", end)
		}
	}
	return s.tokens
}

func (s *scanner) tag() {
	src := s.src
	start := s.i + 1
	closing := src[start] == '/'
	if closing {
		start++
	}
	s.emit("p", start)
	nameEnd := s.span(s.i, func(b byte) bool { return identByte(b, false) || b == '-' || b == ':' })
	name := strings.ToLower(src[s.i:nameEnd])
	s.emit("t", nameEnd)
	for s.i < len(src) {
		c := src[s.i]
		switch {
		case spaceByte(c):
			s.emit("", s.span(s.i, spaceByte))
		case c == '>':
			s.emit("p", s.i+1)
			if !closing && (name == "script" || name == "style") {
				end := len(src) - s.i
				for j := s.i; j+len(name)+2 <= len(src); j++ {
					if src[j] == '<' && src[j+1] == '/' && strings.EqualFold(src[j+2:j+2+len(name)], name) {
						end = j - s.i
						break
					}
				}
				body := src[s.i : s.i+end]
				inner := tokJS
				if name == "style" {
					inner = tokCSS
				}
				for _, t := range inner(body) {
					s.tokens = append(s.tokens, t)
				}
				s.i += end
			}
			return
		case c == '/' && s.i+1 < len(src) && src[s.i+1] == '>':
			s.emit("p", s.i+2)
			return
		case c == '=':
			s.emit("", s.i+1)
		case c == '"' || c == '\'':
			s.emit("s", s.quoted(s.i, c, true))
		default:
			end := s.span(s.i, func(b byte) bool { return !spaceByte(b) && b != '=' && b != '>' && b != '/' && b != '"' && b != '\'' })
			if end == s.i {
				end++
			}
			class := "a"
			if s.i > 0 && src[s.i-1] == '=' {
				class = "s"
			}
			s.emit(class, end)
		}
	}
}

func tokCSS(src string) []hlToken {
	s := &scanner{src: src}
	depth := 0
	value := false
	statement := true
	for s.i < len(src) {
		c := src[s.i]
		switch {
		case strings.HasPrefix(src[s.i:], "/*"):
			s.emit("c", s.until(s.i+2, "*/"))
		case c == '"' || c == '\'':
			s.emit("s", s.quoted(s.i, c, false))
		case spaceByte(c):
			s.emit("", s.span(s.i, spaceByte))
		case c == '{':
			depth++
			value, statement = false, true
			s.emit("", s.i+1)
		case c == '}':
			depth--
			value, statement = false, true
			s.emit("", s.i+1)
		case c == ';':
			value, statement = false, true
			s.emit("", s.i+1)
		case c == '@':
			s.emit("k", s.span(s.i+1, func(b byte) bool { return identByte(b, false) || b == '-' }))
			statement = false
		case value:
			s.cssValue()
		case statement && depth > 0 && cssDeclaration(src[s.i:]):
			end := strings.IndexByte(src[s.i:], ':')
			s.emit("a", s.i+end)
			s.emit("", s.i+1)
			value, statement = true, false
		default:
			end := s.span(s.i, func(b byte) bool { return b != '{' && b != '}' && b != ';' && b != '"' && b != '\'' && b != '/' })
			if end == s.i {
				end++
			}
			s.emit("t", end)
			statement = false
		}
	}
	return s.tokens
}

func cssDeclaration(rest string) bool {
	colon := strings.IndexByte(rest, ':')
	if colon <= 0 {
		return false
	}
	for _, stop := range []string{"{", ";", "}"} {
		if j := strings.Index(rest, stop); j >= 0 && j < colon {
			return false
		}
	}
	name := strings.TrimSpace(rest[:colon])
	for i := 0; i < len(name); i++ {
		if !identByte(name[i], false) && name[i] != '-' {
			return false
		}
	}
	brace := strings.IndexByte(rest, '{')
	semi := strings.IndexAny(rest, ";}")
	return brace < 0 || semi >= 0 && semi < brace
}

func (s *scanner) cssValue() {
	src := s.src
	c := src[s.i]
	switch {
	case c == '#':
		s.emit("n", s.span(s.i+1, func(b byte) bool { return identByte(b, false) }))
	case digit(c) || (c == '.' || c == '-') && s.i+1 < len(src) && digit(src[s.i+1]):
		end := s.span(s.i+1, func(b byte) bool { return digit(b) || b == '.' })
		end = s.span(end, func(b byte) bool { return b >= 'a' && b <= 'z' || b == '%' })
		s.emit("n", end)
	case c == '-' && strings.HasPrefix(src[s.i:], "--"):
		s.emit("v", s.span(s.i+2, func(b byte) bool { return identByte(b, false) || b == '-' }))
	case c == '!':
		s.emit("k", s.span(s.i+1, func(b byte) bool { return identByte(b, false) }))
	case identByte(c, true) || c == '-':
		end := s.span(s.i+1, func(b byte) bool { return identByte(b, false) || b == '-' })
		if end < len(src) && src[end] == '(' {
			s.emit("f", end)
		} else {
			s.emit("", end)
		}
	default:
		s.emit("", s.i+1)
	}
}

func tokJS(src string) []hlToken {
	s := &scanner{src: src}
	regexOK := true
	for s.i < len(src) {
		c := src[s.i]
		switch {
		case strings.HasPrefix(src[s.i:], "//"):
			s.emit("c", s.span(s.i, func(b byte) bool { return b != '\n' }))
		case strings.HasPrefix(src[s.i:], "/*"):
			s.emit("c", s.until(s.i+2, "*/"))
		case c == '"' || c == '\'':
			s.emit("s", s.quoted(s.i, c, false))
			regexOK = false
		case c == '`':
			s.emit("s", s.quoted(s.i, c, true))
			regexOK = false
		case spaceByte(c):
			s.emit("", s.span(s.i, spaceByte))
		case digit(c) || c == '.' && s.i+1 < len(src) && digit(src[s.i+1]):
			s.emit("n", s.span(s.i, func(b byte) bool { return identByte(b, false) || b == '.' }))
			regexOK = false
		case identByte(c, true):
			end := s.span(s.i, func(b byte) bool { return identByte(b, false) })
			word := src[s.i:end]
			next := s.span(end, func(b byte) bool { return b == ' ' || b == '\t' })
			switch {
			case jsKeywords[word]:
				s.emit("k", end)
				regexOK = word != "this" && word != "super"
			case jsLiterals[word]:
				s.emit("n", end)
				regexOK = false
			case next < len(src) && src[next] == '(':
				s.emit("f", end)
				regexOK = false
			default:
				s.emit("", end)
				regexOK = false
			}
		case c == '/' && regexOK:
			end := s.regexEnd()
			s.emit("s", end)
			regexOK = false
		default:
			s.emit("", s.i+1)
			regexOK = !strings.ContainsRune(")]}", rune(c))
		}
	}
	return s.tokens
}

func (s *scanner) regexEnd() int {
	class := false
	for j := s.i + 1; j < len(s.src); j++ {
		switch s.src[j] {
		case '\\':
			j++
		case '[':
			class = true
		case ']':
			class = false
		case '\n':
			return j
		case '/':
			if !class {
				return s.span(j+1, func(b byte) bool { return b >= 'a' && b <= 'z' })
			}
		}
	}
	return len(s.src)
}

func tokJSON(src string) []hlToken {
	s := &scanner{src: src}
	for s.i < len(src) {
		c := src[s.i]
		switch {
		case c == '"':
			end := s.quoted(s.i, '"', false)
			next := s.span(end, spaceByte)
			if next < len(src) && src[next] == ':' {
				s.emit("a", end)
			} else {
				s.emit("s", end)
			}
		case digit(c) || c == '-':
			s.emit("n", s.span(s.i+1, func(b byte) bool { return digit(b) || strings.IndexByte(".eE+-", b) >= 0 }))
		case identByte(c, true):
			end := s.span(s.i, func(b byte) bool { return identByte(b, false) })
			if jsonLiteral[src[s.i:end]] {
				s.emit("n", end)
			} else {
				s.emit("", end)
			}
		default:
			s.emit("", s.i+1)
		}
	}
	return s.tokens
}

func tokSh(src string) []hlToken {
	s := &scanner{src: src}
	command := true
	for s.i < len(src) {
		c := src[s.i]
		switch {
		case c == '#' && (s.i == 0 || spaceByte(src[s.i-1])):
			s.emit("c", s.span(s.i, func(b byte) bool { return b != '\n' }))
		case c == '\n':
			s.emit("", s.i+1)
			command = s.i < 2 || src[s.i-2] != '\\'
		case c == ' ' || c == '\t' || c == '\\':
			s.emit("", s.i+1)
		case c == '\'':
			s.emit("s", s.until(s.i+1, "'"))
			command = false
		case c == '"':
			s.emit("s", s.quoted(s.i, '"', true))
			command = false
		case c == '$':
			end := s.i + 1
			switch {
			case end < len(src) && src[end] == '{':
				end = s.until(end, "}")
			case end < len(src) && src[end] == '(':
				end++
			default:
				end = s.span(end, func(b byte) bool { return identByte(b, false) })
			}
			s.emit("v", end)
			command = false
		case strings.IndexByte("|&;()<>", c) >= 0:
			s.emit("", s.i+1)
			command = c != ')' && c != '>' && c != '<'
		default:
			end := s.span(s.i, func(b byte) bool { return !spaceByte(b) && strings.IndexByte("|&;()<>'\"$", b) < 0 })
			if end == s.i {
				s.emit("", s.i+1)
				continue
			}
			word := src[s.i:end]
			switch {
			case shKeywords[word]:
				s.emit("k", end)
				command = word != "export" && word != "local"
			case strings.Contains(word, "=") && command && identByte(word[0], true):
				eq := strings.IndexByte(word, '=')
				s.emit("v", s.i+eq)
				s.emit("", end)
			case command:
				s.emit("f", end)
				command = false
			case strings.HasPrefix(word, "-"):
				s.emit("a", end)
			default:
				s.emit("", end)
			}
		}
	}
	return s.tokens
}
