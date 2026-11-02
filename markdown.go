package main

import (
	"fmt"
	"html"
	"regexp"
	"strconv"
	"strings"
	"unicode"
)

type tocEntry struct {
	Depth int
	ID    string
	Title string
}

type mdHooks struct {
	example    func(name string, attrs map[string]string) (string, error)
	components func(variant string) (string, error)
	code       func(lang, title, src string) (string, error)
	link       func(url string) string
}

type mdTag struct {
	Name  string
	Arg   string
	Attrs map[string]string
}

var (
	mdHeading   = regexp.MustCompile(`^(#{1,4})[ \t]+(.+?)[ \t]*$`)
	mdListItem  = regexp.MustCompile(`^([-*]|\d{1,9}[.)])( +|$)`)
	mdTableSep  = regexp.MustCompile(`^\|?[ \t]*:?-{3,}:?[ \t]*(\|[ \t]*:?-{3,}:?[ \t]*)*\|?[ \t]*$`)
	mdTagLine   = regexp.MustCompile(`^\{\{(example|components)((?:[ \t]+(?:"[^"]*"|[a-z]+="[^"]*"))*)[ \t]*\}\}$`)
	mdTagArg    = regexp.MustCompile(`"([^"]*)"|([a-z]+)="([^"]*)"`)
	mdFenceInfo = regexp.MustCompile(`^([a-z0-9+-]*)((?:[ \t]+[a-z]+="[^"]*")*)[ \t]*$`)
	mdSafeURL   = regexp.MustCompile(`^(https?://[^\s"'<>]+|mailto:[^\s"'<>]+|[A-Za-z0-9._~%/#?=&+-]+)$`)
	mdTags      = regexp.MustCompile(`<[^>]*>`)
	mdRootLink  = regexp.MustCompile(`\]\((/[^()\s]*)\)`)
)

func parseTag(line string) (mdTag, bool, error) {
	m := mdTagLine.FindStringSubmatch(strings.TrimSpace(line))
	if m == nil {
		if strings.HasPrefix(strings.TrimSpace(line), "{{") {
			return mdTag{}, false, fmt.Errorf("bad tag %q", strings.TrimSpace(line))
		}
		return mdTag{}, false, nil
	}
	tag := mdTag{Name: m[1], Attrs: map[string]string{}}
	args := 0
	for _, a := range mdTagArg.FindAllStringSubmatch(m[2], -1) {
		if a[2] != "" {
			tag.Attrs[a[2]] = a[3]
			continue
		}
		tag.Arg = a[1]
		args++
	}
	switch {
	case tag.Name == "example" && (args != 1 || tag.Arg == ""):
		return tag, true, fmt.Errorf("example tag needs one name: %q", line)
	case tag.Name == "components" && (args > 1 || len(tag.Attrs) > 0 || args == 1 && tag.Arg != "new"):
		return tag, true, fmt.Errorf(`components tag takes only "new": %q`, line)
	}
	return tag, true, nil
}

type fence struct {
	lang, title string
	lines       []string
}

func parseFence(lines []string, i int) (fence, int, error) {
	open := strings.TrimSpace(lines[i])
	ticks := len(open) - len(strings.TrimLeft(open, "`"))
	m := mdFenceInfo.FindStringSubmatch(open[ticks:])
	if m == nil {
		return fence{}, i, fmt.Errorf("bad code fence %q", open)
	}
	f := fence{lang: m[1]}
	for _, a := range mdTagArg.FindAllStringSubmatch(m[2], -1) {
		if a[2] != "title" {
			return f, i, fmt.Errorf("code fence attribute %q is not supported", a[2])
		}
		f.title = a[3]
	}
	for j := i + 1; j < len(lines); j++ {
		t := strings.TrimSpace(lines[j])
		if strings.HasPrefix(t, strings.Repeat("`", ticks)) && strings.Trim(t, "`") == "" {
			return f, j + 1, nil
		}
		f.lines = append(f.lines, lines[j])
	}
	return f, i, fmt.Errorf("code fence %q is not closed", open)
}

func isFence(line string) bool {
	return strings.HasPrefix(line, "```")
}

func mdLinks(src string, fn func(string) string) string {
	lines := strings.Split(src, "\n")
	for i := 0; i < len(lines); i++ {
		if isFence(lines[i]) {
			if _, end, err := parseFence(lines, i); err == nil {
				i = end - 1
				continue
			}
		}
		lines[i] = mdRootLink.ReplaceAllStringFunc(lines[i], func(m string) string {
			return "](" + fn(m[2:len(m)-1]) + ")"
		})
	}
	return strings.Join(lines, "\n")
}

func expandMarkdown(src string, expand func(mdTag) string) string {
	lines := strings.Split(strings.ReplaceAll(src, "\r\n", "\n"), "\n")
	var out []string
	for i := 0; i < len(lines); i++ {
		line := lines[i]
		if isFence(line) {
			if _, end, err := parseFence(lines, i); err == nil {
				out = append(out, lines[i:end]...)
				i = end - 1
				continue
			}
		}
		if tag, ok, err := parseTag(line); ok && err == nil {
			out = append(out, expand(tag))
			continue
		}
		out = append(out, line)
	}
	return strings.TrimRight(strings.Join(out, "\n"), "\n") + "\n"
}

type mdRenderer struct {
	hooks mdHooks
	ids   map[string]int
	toc   []tocEntry
	err   error
}

func renderMarkdown(src string, hooks mdHooks) (string, []tocEntry, error) {
	r := &mdRenderer{hooks: hooks, ids: map[string]int{}}
	var b strings.Builder
	if err := r.blocks(&b, strings.Split(strings.ReplaceAll(src, "\r\n", "\n"), "\n"), false); err != nil {
		return "", nil, err
	}
	if r.err != nil {
		return "", nil, r.err
	}
	return b.String(), r.toc, nil
}

func blank(line string) bool {
	return strings.TrimSpace(line) == ""
}

func (r *mdRenderer) startsBlock(line string) bool {
	t := strings.TrimSpace(line)
	if line != strings.TrimLeft(line, " \t") {
		return false
	}
	_, isTag, _ := parseTag(line)
	return isFence(line) || isTag || mdHeading.MatchString(line) || mdListItem.MatchString(line) || strings.HasPrefix(line, ">") || t == "---" || strings.HasPrefix(line, "|")
}

func (r *mdRenderer) blocks(b *strings.Builder, lines []string, tight bool) error {
	for i := 0; i < len(lines); {
		line := lines[i]
		trimmed := strings.TrimSpace(line)
		switch {
		case blank(line):
			i++
		case isFence(line):
			f, next, err := parseFence(lines, i)
			if err != nil {
				return err
			}
			out, err := r.hooks.code(f.lang, f.title, strings.Join(f.lines, "\n"))
			if err != nil {
				return err
			}
			b.WriteString(out)
			i = next
		case strings.HasPrefix(trimmed, "{{"):
			tag, _, err := parseTag(line)
			if err != nil {
				return err
			}
			var out string
			if tag.Name == "example" {
				out, err = r.hooks.example(tag.Arg, tag.Attrs)
			} else {
				out, err = r.hooks.components(tag.Arg)
			}
			if err != nil {
				return err
			}
			b.WriteString(out)
			i++
		case mdHeading.MatchString(line):
			m := mdHeading.FindStringSubmatch(line)
			r.heading(b, len(m[1]), m[2])
			i++
		case trimmed == "---" && line == trimmed:
			b.WriteString("<hr>\n")
			i++
		case strings.HasPrefix(line, "|") && i+1 < len(lines) && mdTableSep.MatchString(lines[i+1]):
			i = r.table(b, lines, i)
		case strings.HasPrefix(line, ">"):
			var inner []string
			for ; i < len(lines) && strings.HasPrefix(lines[i], ">"); i++ {
				inner = append(inner, strings.TrimPrefix(strings.TrimPrefix(lines[i], ">"), " "))
			}
			b.WriteString("<blockquote>\n")
			if err := r.blocks(b, inner, false); err != nil {
				return err
			}
			b.WriteString("</blockquote>\n")
		case mdListItem.MatchString(line):
			next, err := r.list(b, lines, i)
			if err != nil {
				return err
			}
			i = next
		case line != strings.TrimLeft(line, " \t"):
			return fmt.Errorf("unexpected indented line %q", line)
		default:
			var para []string
			for ; i < len(lines) && !blank(lines[i]) && (len(para) == 0 || !r.startsBlock(lines[i])); i++ {
				para = append(para, strings.TrimSpace(lines[i]))
			}
			text := r.inline(strings.Join(para, "\n"))
			if tight {
				b.WriteString(text)
			} else {
				b.WriteString("<p>" + text + "</p>\n")
			}
		}
	}
	return nil
}

func (r *mdRenderer) heading(b *strings.Builder, depth int, text string) {
	inner := r.inline(text)
	plain := html.UnescapeString(mdTags.ReplaceAllString(inner, ""))
	id := slug(plain)
	if n, ok := r.ids[id]; ok {
		r.ids[id] = n + 1
		id = fmt.Sprintf("%s-%d", id, n+1)
	}
	r.ids[id] = 0
	if depth == 2 || depth == 3 {
		r.toc = append(r.toc, tocEntry{Depth: depth, ID: id, Title: plain})
	}
	fmt.Fprintf(b, `<h%d id="%s"><a href="#%s"><span>%s</span><span aria-hidden="true">#</span></a></h%d>`+"\n", depth, id, id, inner, depth)
}

func slug(text string) string {
	var b strings.Builder
	for _, c := range strings.ToLower(strings.TrimSpace(text)) {
		switch {
		case unicode.IsLetter(c) || unicode.IsDigit(c) || c == '_' || c == '-':
			b.WriteRune(c)
		case c == ' ':
			b.WriteRune('-')
		}
	}
	if b.Len() == 0 {
		return "section"
	}
	return b.String()
}

func splitRow(line string) []string {
	line = strings.TrimSpace(line)
	line = strings.TrimPrefix(line, "|")
	if strings.HasSuffix(line, "|") && !strings.HasSuffix(line, `\|`) {
		line = line[:len(line)-1]
	}
	var cells []string
	var cur strings.Builder
	for i := 0; i < len(line); i++ {
		switch {
		case line[i] == '\\' && i+1 < len(line) && line[i+1] == '|':
			cur.WriteByte('|')
			i++
		case line[i] == '|':
			cells = append(cells, strings.TrimSpace(cur.String()))
			cur.Reset()
		default:
			cur.WriteByte(line[i])
		}
	}
	return append(cells, strings.TrimSpace(cur.String()))
}

func (r *mdRenderer) table(b *strings.Builder, lines []string, i int) int {
	head := splitRow(lines[i])
	b.WriteString("<div data-docs=\"table\" class=\"scroll-fade-x\"><table>\n<thead><tr>")
	for _, cell := range head {
		b.WriteString("<th>" + r.inline(cell) + "</th>")
	}
	b.WriteString("</tr></thead>\n<tbody>\n")
	i += 2
	for ; i < len(lines) && strings.HasPrefix(lines[i], "|"); i++ {
		cells := splitRow(lines[i])
		if len(cells) != len(head) {
			r.fail(fmt.Errorf("table row has %d cells, header has %d: %q", len(cells), len(head), lines[i]))
		}
		b.WriteString("<tr>")
		for _, cell := range cells {
			b.WriteString("<td>" + r.inline(cell) + "</td>")
		}
		b.WriteString("</tr>\n")
	}
	b.WriteString("</tbody>\n</table></div>\n")
	return i
}

func (r *mdRenderer) list(b *strings.Builder, lines []string, i int) (int, error) {
	first := mdListItem.FindStringSubmatch(lines[i])
	ordered := first[1] != "-" && first[1] != "*"
	type item struct{ lines []string }
	var items []item
	loose := false
	for i < len(lines) {
		m := mdListItem.FindStringSubmatch(lines[i])
		if m == nil || (m[1] != "-" && m[1] != "*") == !ordered {
			break
		}
		width := len(m[0])
		if m[2] == "" {
			width++
		}
		it := item{lines: []string{lines[i][len(m[0]):]}}
		i++
		for i < len(lines) {
			line := lines[i]
			if blank(line) {
				j := i
				for j < len(lines) && blank(lines[j]) {
					j++
				}
				if j < len(lines) && indent(lines[j]) >= width {
					loose = true
					it.lines = append(it.lines, make([]string, j-i)...)
					i = j
					continue
				}
				if j < len(lines) && mdListItem.MatchString(lines[j]) {
					loose = true
				}
				break
			}
			if indent(line) >= width {
				it.lines = append(it.lines, line[width:])
			} else if mdListItem.MatchString(line) || r.startsBlock(line) {
				break
			} else {
				it.lines = append(it.lines, strings.TrimSpace(line))
			}
			i++
		}
		items = append(items, it)
		for i < len(lines) && blank(lines[i]) {
			if i+1 < len(lines) && mdListItem.MatchString(lines[i+1]) {
				i++
				continue
			}
			break
		}
	}
	tag := "ul"
	if ordered {
		tag = "ol"
		if start, _ := strconv.Atoi(strings.TrimRight(first[1], ".)")); start != 1 {
			tag = `ol start="` + strconv.Itoa(start) + `"`
		}
	}
	b.WriteString("<" + tag + ">\n")
	for _, it := range items {
		b.WriteString("<li>")
		if err := r.blocks(b, it.lines, !loose); err != nil {
			return i, err
		}
		b.WriteString("</li>\n")
	}
	b.WriteString("</" + strings.Fields(tag)[0] + ">\n")
	return i, nil
}

func indent(line string) int {
	n := 0
	for _, c := range line {
		switch c {
		case ' ':
			n++
		case '\t':
			n += 4
		default:
			return n
		}
	}
	return n
}

func (r *mdRenderer) fail(err error) {
	if r.err == nil {
		r.err = err
	}
}

func (r *mdRenderer) inline(s string) string {
	var b strings.Builder
	for i := 0; i < len(s); {
		c := s[i]
		switch {
		case c == '\\' && i+1 < len(s) && strings.IndexByte("\\`*_[]()#+-.!|<>{}", s[i+1]) >= 0:
			b.WriteString(html.EscapeString(s[i+1 : i+2]))
			i += 2
		case c == '`':
			n := 0
			for i+n < len(s) && s[i+n] == '`' {
				n++
			}
			end := findRun(s, i+n, n)
			if end < 0 {
				b.WriteString(strings.Repeat("`", n))
				i += n
				continue
			}
			code := strings.ReplaceAll(s[i+n:end], "\n", " ")
			if len(code) > 2 && code[0] == ' ' && code[len(code)-1] == ' ' {
				code = code[1 : len(code)-1]
			}
			b.WriteString("<code>" + html.EscapeString(code) + "</code>")
			i = end + n
		case c == '[':
			text, url, next, ok := linkAt(s, i)
			if !ok {
				b.WriteString("[")
				i++
				continue
			}
			if !mdSafeURL.MatchString(url) || strings.HasPrefix(url, "//") {
				r.fail(fmt.Errorf("link URL %q is not allowed", url))
			}
			for j := range len(text) {
				if _, _, _, nested := linkAt(text, j); text[j] == '[' && nested {
					r.fail(fmt.Errorf("link text %q has a link", text))
				}
			}
			if r.hooks.link != nil {
				url = r.hooks.link(url)
			}
			b.WriteString(`<a href="` + html.EscapeString(url) + `">` + r.inline(text) + "</a>")
			i = next
		case c == '*' && strings.HasPrefix(s[i:], "**"):
			end := strings.Index(s[i+2:], "**")
			if end <= 0 {
				b.WriteString("**")
				i += 2
				continue
			}
			b.WriteString("<strong>" + r.inline(s[i+2:i+2+end]) + "</strong>")
			i += end + 4
		case (c == '*' || c == '_') && emphasisOpens(s, i):
			end := emphasisClose(s, i)
			if end < 0 {
				b.WriteByte(c)
				i++
				continue
			}
			b.WriteString("<em>" + r.inline(s[i+1:end]) + "</em>")
			i = end + 1
		default:
			j := i + 1
			for j < len(s) && strings.IndexByte("\\`[*_", s[j]) < 0 {
				j++
			}
			b.WriteString(html.EscapeString(s[i:j]))
			i = j
		}
	}
	return b.String()
}

func findRun(s string, from, n int) int {
	for i := from; i < len(s); {
		if s[i] != '`' {
			i++
			continue
		}
		j := i
		for j < len(s) && s[j] == '`' {
			j++
		}
		if j-i == n {
			return i
		}
		i = j
	}
	return -1
}

func linkAt(s string, i int) (text, url string, next int, ok bool) {
	depth := 0
	for j := i; j < len(s); j++ {
		switch s[j] {
		case '\\':
			j++
		case '`':
			n := 0
			for j+n < len(s) && s[j+n] == '`' {
				n++
			}
			if end := findRun(s, j+n, n); end >= 0 {
				j = end + n - 1
			}
		case '[':
			depth++
		case ']':
			depth--
			if depth == 0 {
				if j+1 >= len(s) || s[j+1] != '(' {
					return "", "", 0, false
				}
				end := strings.IndexByte(s[j+2:], ')')
				if end < 0 {
					return "", "", 0, false
				}
				return s[i+1 : j], s[j+2 : j+2+end], j + 3 + end, true
			}
		}
	}
	return "", "", 0, false
}

func wordByte(c byte) bool {
	return c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c >= 0x80
}

func emphasisOpens(s string, i int) bool {
	if i+1 >= len(s) || s[i+1] == ' ' || s[i+1] == s[i] {
		return false
	}
	return s[i] == '*' || i == 0 || !wordByte(s[i-1])
}

func emphasisClose(s string, i int) int {
	for j := i + 2; j < len(s); j++ {
		if s[j] == '`' {
			n := 0
			for j+n < len(s) && s[j+n] == '`' {
				n++
			}
			if end := findRun(s, j+n, n); end >= 0 {
				j = end + n - 1
				continue
			}
		}
		if s[j] == s[i] && s[j-1] != ' ' && (s[i] == '*' || j+1 == len(s) || !wordByte(s[j+1])) {
			return j
		}
	}
	return -1
}
