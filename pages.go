package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"io/fs"
	"path"
	"regexp"
	"slices"
	"strconv"
	"strings"
)

type catalogData struct {
	Groups []struct {
		Name string `json:"name"`
		CSS  string `json:"css"`
		JS   string `json:"js"`
	} `json:"groups"`
	Exports []struct {
		Name      string `json:"name"`
		Module    string `json:"module"`
		Signature string `json:"signature"`
		Notes     string `json:"notes"`
	} `json:"exports"`
	Components []*catalogComponent `json:"components"`
}

type catalogComponent struct {
	Name  string   `json:"name"`
	Title string   `json:"title"`
	Group string   `json:"group"`
	Needs []string `json:"needs"`
	JS    bool     `json:"js"`
	Parts []struct {
		Slot       string         `json:"slot"`
		Root       bool           `json:"root"`
		Attributes map[string]any `json:"attributes"`
		State      []string       `json:"state"`
	} `json:"parts"`
	PartAttributes map[string]any `json:"partAttributes"`
	Options        map[string]any `json:"options"`
	KitAdds        []string       `json:"kitAdds"`
	Events         []struct {
		Name       string   `json:"name"`
		Target     string   `json:"target"`
		Detail     []string `json:"detail"`
		Cancelable bool     `json:"cancelable"`
		Notes      string   `json:"notes"`
	} `json:"events"`
	Exports       []string `json:"exports"`
	Keyboard      []string `json:"keyboard"`
	Example       string   `json:"example"`
	ExampleSource string   `json:"exampleSource"`
	Docs          string   `json:"docs"`
	Readme        string   `json:"readme"`
	SameAs        string   `json:"sameAs"`
	Script        string   `json:"script"`
	text          string
}

type demoItem struct {
	kind string
	text string
}

type demoPart struct {
	title string
	items []demoItem
}

type demoSection struct {
	id, title, description string
	parts                  []demoPart
}

var (
	demoSectionOpen = regexp.MustCompile(`^      <section id="([a-z0-9-]+)" data-demo="section">$`)
	demoChild       = regexp.MustCompile(`^        <[a-z]`)
	demoOpenTag     = regexp.MustCompile(`^<([a-z0-9]+)[^>]*?(?: data-demo="([^"]*)")?[^>]*>`)
	demoAttr        = regexp.MustCompile(` data-demo="[^"]*"`)
	inlineCode      = regexp.MustCompile(`(?s)<code>(.*?)</code>`)
	anyTag          = regexp.MustCompile(`<[^>]*>`)
	hashLink        = regexp.MustCompile(`\shref="#([a-z0-9-]+)"`)
	mdLink          = regexp.MustCompile(`\]\(([^()\s]+)\)`)
	compMdLink      = regexp.MustCompile(`^([a-z0-9-]+)\.md(#.*)?$`)
)

var docSections = map[string][]string{
	"/docs/components/chart":        {"chart", "chart-area", "chart-bar", "chart-line", "chart-pie", "chart-radar", "chart-radial"},
	"/docs/components/stat-tile":    {"chart-stat"},
	"/docs/components/theme-switch": {"theming"},
	"/docs/theming":                 {"theming", "themes"},
	"/docs/rtl":                     {"direction"},
}

var docStyles = map[string][]string{"themes": {"clanker-ui-themes.css"}}

func (d *docsSite) loadCatalog(fsys fs.FS) error {
	raw, err := fs.ReadFile(fsys, exportExtras["clanker-ui.json"])
	if errors.Is(err, fs.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	if err := json.Unmarshal(raw, &d.catalog); err != nil {
		return fmt.Errorf("catalog: %w", err)
	}
	d.components = map[string]*catalogComponent{}
	for _, c := range d.catalog.Components {
		i := strings.Index(c.Docs, "/docs/")
		if i < 0 {
			return fmt.Errorf("catalog: docs URL %q has no /docs/", c.Docs)
		}
		href := strings.TrimSuffix(c.Docs[i:], "/")
		ref, err := fs.ReadFile(fsys, c.Readme)
		if err != nil {
			return fmt.Errorf("catalog: %w", err)
		}
		d.refs[href] = ref
		_, c.text, _ = strings.Cut(strings.ReplaceAll(string(ref), "\r\n", "\n"), "\n## Full text\n\n")
		d.components[href] = c
	}
	return nil
}

func parseDemo(src []byte) map[string]*demoSection {
	out := map[string]*demoSection{}
	var sec *demoSection
	var child []string
	flush := func() {
		if sec != nil && len(child) > 0 {
			sec.add(strings.TrimRight(strings.Join(child, "\n"), " \n"))
		}
		child = nil
	}
	for _, line := range strings.Split(strings.ReplaceAll(string(src), "\r\n", "\n"), "\n") {
		if m := demoSectionOpen.FindStringSubmatch(line); m != nil {
			flush()
			sec = &demoSection{id: m[1], parts: []demoPart{{}}}
			out[sec.id] = sec
			continue
		}
		if sec == nil {
			continue
		}
		if line == "      </section>" {
			flush()
			sec = nil
			continue
		}
		if demoChild.MatchString(line) {
			flush()
		}
		child = append(child, line)
	}
	return out
}

func (s *demoSection) add(src string) {
	m := demoOpenTag.FindStringSubmatch(strings.TrimSpace(src))
	if m == nil {
		return
	}
	part := &s.parts[len(s.parts)-1]
	switch tag, kind := m[1], m[2]; {
	case tag == "h3" && kind == "title":
		s.title = htmlText(src)
	case tag == "p" && kind == "description":
		s.description = htmlInline(src)
	case kind == "subtitle":
		if part.title == "" && len(part.items) == 0 {
			part.title = htmlInline(src)
		} else {
			s.parts = append(s.parts, demoPart{title: htmlInline(src)})
		}
	case tag == "p" && kind == "caption":
		part.items = append(part.items, demoItem{"note", htmlInline(src)})
	case tag == "pre" && kind == "code":
		part.items = append(part.items, demoItem{"code", htmlText(src)})
	default:
		part.items = append(part.items, demoItem{"html", dedent(src)})
	}
}

func htmlText(s string) string {
	return strings.TrimSpace(html.UnescapeString(anyTag.ReplaceAllString(s, "")))
}

func htmlInline(s string) string {
	s = strings.ReplaceAll(s, `</kbd><kbd data-slot="kbd">`, "+")
	s = inlineCode.ReplaceAllStringFunc(s, func(m string) string {
		return "`" + html.UnescapeString(inlineCode.FindStringSubmatch(m)[1]) + "`"
	})
	return strings.Join(strings.Fields(htmlText(s)), " ")
}

var mdLinkText = regexp.MustCompile(`\[([^\]]*)\]\([^()]*\)`)

func plainText(md string) string {
	return strings.ReplaceAll(mdLinkText.ReplaceAllString(md, "$1"), "`", "")
}

func dedent(s string) string {
	lines := strings.Split(s, "\n")
	for len(lines) > 0 && strings.TrimSpace(lines[0]) == "" {
		lines = lines[1:]
	}
	for len(lines) > 0 && strings.TrimSpace(lines[len(lines)-1]) == "" {
		lines = lines[:len(lines)-1]
	}
	cut := -1
	for _, l := range lines {
		if strings.TrimSpace(l) == "" {
			continue
		}
		if n := len(l) - len(strings.TrimLeft(l, " ")); cut < 0 || n < cut {
			cut = n
		}
	}
	for i, l := range lines {
		if len(l) >= cut && cut > 0 {
			lines[i] = l[cut:]
		}
	}
	return strings.Join(lines, "\n")
}

func demoCode(src string) string {
	m := demoOpenTag.FindStringSubmatch(src)
	if m != nil && slices.Contains(strings.Fields(m[2]), "preview") {
		inner := strings.TrimSuffix(src[len(m[0]):], "</"+m[1]+">")
		if strings.TrimSpace(inner) != "" {
			src = inner
		}
	}
	return demoAttr.ReplaceAllString(dedent(src), "")
}

type readmeSection struct {
	level int
	slug  string
	start int
}

type readmeDoc struct {
	lines    []string
	sections []readmeSection
}

func parseReadme(src string) readmeDoc {
	doc := readmeDoc{lines: strings.Split(strings.ReplaceAll(src, "\r\n", "\n"), "\n")}
	fence := false
	for i, line := range doc.lines {
		if strings.HasPrefix(line, "```") {
			fence = !fence
		}
		if m := mdHeading.FindStringSubmatch(line); m != nil && !fence {
			doc.sections = append(doc.sections, readmeSection{len(m[1]), slug(m[2]), i})
		}
	}
	return doc
}

func (r readmeDoc) section(anchor string, stops map[string]bool) string {
	for i, s := range r.sections {
		if s.slug != anchor {
			continue
		}
		end := len(r.lines)
		for _, next := range r.sections[i+1:] {
			if next.level <= s.level || stops[next.slug] {
				end = next.start
				break
			}
		}
		body := r.lines[s.start+1 : end]
		out := make([]string, 0, len(body))
		fence := false
		for _, line := range body {
			if strings.HasPrefix(line, "```") {
				fence = !fence
			}
			if m := mdHeading.FindStringSubmatch(line); m != nil && !fence {
				line = strings.Repeat("#", max(2, len(m[1])-s.level+1)) + " " + m[2]
			}
			out = append(out, line)
		}
		return strings.Trim(strings.Join(out, "\n"), "\n")
	}
	return ""
}

func firstParagraph(md string) string {
	for _, para := range strings.Split(md, "\n\n") {
		para = strings.TrimSpace(para)
		if para == "" || strings.HasPrefix(para, "#") || strings.HasPrefix(para, "```") || strings.HasPrefix(para, "|") || strings.HasPrefix(para, "-") || strings.HasPrefix(para, ">") {
			continue
		}
		return strings.Join(strings.Fields(plainText(para)), " ")
	}
	return ""
}

func titleWords(slot string) string {
	words := strings.Split(slot, "-")
	for i, w := range words {
		switch w {
		case "otp", "rtl", "id":
			words[i] = strings.ToUpper(w)
		case "":
		default:
			words[i] = strings.ToUpper(w[:1]) + w[1:]
		}
	}
	return strings.Join(words, " ")
}

func attrValues(v any) string {
	switch x := v.(type) {
	case []any:
		var q []string
		for _, s := range x {
			q = append(q, fmt.Sprintf("%q", s))
		}
		return "`" + strings.Join(q, " | ") + "`"
	case string:
		switch x {
		case "id":
			return "Element id"
		case "any":
			return "Any value"
		}
		return strings.ToUpper(x[:1]) + x[1:]
	}
	return fmt.Sprint(v)
}

func codeJoin(names []string) string {
	var q []string
	for _, n := range names {
		q = append(q, "`"+n+"`")
	}
	switch len(q) {
	case 0:
		return ""
	case 1:
		return q[0]
	case 2:
		return q[0] + " and " + q[1]
	}
	return strings.Join(q[:len(q)-1], ", ") + ", and " + q[len(q)-1]
}

func (d *docsSite) sectionsFor(href string) []string {
	if ids, ok := docSections[href]; ok {
		return ids
	}
	if strings.HasPrefix(href, "/docs/components/") || !strings.Contains(strings.TrimPrefix(href, "/docs/"), "/") {
		if _, ok := d.demo[path.Base(href)]; ok {
			return []string{path.Base(href)}
		}
	}
	return nil
}

func (d *docsSite) generatePages(fsys fs.FS) error {
	demo, err := fs.ReadFile(fsys, "demo/index.html")
	if err != nil && !errors.Is(err, fs.ErrNotExist) {
		return err
	}
	d.demo = parseDemo(demo)
	readmeSrc, err := fs.ReadFile(fsys, exportExtras["llms-full.txt"])
	if err != nil && !errors.Is(err, fs.ErrNotExist) {
		return err
	}
	readme := parseReadme(string(readmeSrc))
	d.anchors, d.sectionPage = map[string]string{}, map[string]string{}
	stops := map[string]bool{}
	for _, href := range sortedKeys(d.components) {
		if anchor, ok := strings.CutPrefix(d.components[href].ExampleSource, "README.md#"); ok {
			stops[anchor] = true
			if _, ok := d.anchors[anchor]; !ok {
				d.anchors[anchor] = href
			}
		}
	}
	hrefs := sortedKeys(d.titles)
	for _, href := range hrefs {
		if u := d.readme[href]; u != "" {
			anchor := strings.TrimPrefix(u, githubURL+"#")
			stops[anchor] = true
			if _, ok := d.anchors[anchor]; !ok {
				d.anchors[anchor] = href
			}
		}
	}
	for _, own := range []bool{true, false} {
		for _, href := range hrefs {
			for _, id := range d.sectionsFor(href) {
				if _, taken := d.sectionPage[id]; !taken && (path.Base(href) == id) == own {
					d.sectionPage[id] = href
				}
			}
		}
	}
	for _, href := range hrefs {
		if !strings.HasPrefix(href, "/docs/") || d.pages[href] != nil || docRedirects[href] != "" {
			continue
		}
		if name, ok := strings.CutPrefix(href, "/docs/blocks/"); ok && d.blocks[name] != nil {
			d.pages[href] = d.blockDocPage(href, name)
			continue
		}
		if p := d.generatePage(href, readme, stops); p != nil {
			d.pages[href] = p
		}
	}
	return nil
}

func (d *docsSite) fixLinks(md string) string {
	return mdLink.ReplaceAllStringFunc(md, func(m string) string {
		u := mdLink.FindStringSubmatch(m)[1]
		anchor, readmeLink := strings.CutPrefix(u, githubURL+"#")
		if !readmeLink {
			anchor, readmeLink = strings.CutPrefix(u, "#")
		}
		switch {
		case readmeLink:
			if href, ok := d.anchors[anchor]; ok {
				return "](" + href + ")"
			}
			return "](" + githubURL + "#" + anchor + ")"
		case compMdLink.MatchString(u):
			name := compMdLink.FindStringSubmatch(u)[1]
			for href, c := range d.components {
				if c.Name == name {
					return "](" + href + ")"
				}
			}
		case !strings.Contains(u, ":") && !strings.HasPrefix(u, "/"):
			return "](" + githubURL + "/blob/main/" + u + ")"
		}
		return m
	})
}

func (d *docsSite) siteRelative(src string) string {
	return exportTag.ReplaceAllStringFunc(src, func(tag string) string {
		return tagURL.ReplaceAllStringFunc(tag, func(attr string) string {
			m := tagURL.FindStringSubmatch(attr)
			if !relativeURL.MatchString(m[2]) {
				return attr
			}
			return fmt.Sprintf(` %s="%s"`, m[1], d.urls.url("/"+m[2]))
		})
	})
}

func (d *docsSite) demoHTML(src, own string) string {
	src = d.siteRelative(src)
	return hashLink.ReplaceAllStringFunc(src, func(attr string) string {
		id := hashLink.FindStringSubmatch(attr)[1]
		if _, ok := d.demo[id]; !ok {
			return attr
		}
		if href := d.sectionPage[id]; href != own {
			if href == "" {
				return fmt.Sprintf(` href="%s#%s"`, d.urls.url("/demo"), id)
			}
			return fmt.Sprintf(` href="%s"`, d.urls.url(href))
		}
		return attr
	})
}

type pageWriter struct {
	d        *docsSite
	href     string
	b        strings.Builder
	page     *docPage
	sections []*demoSection
	count    int
	keys     []string
}

func (w *pageWriter) line(format string, args ...any) {
	fmt.Fprintf(&w.b, format+"\n\n", args...)
}

func (w *pageWriter) example(sec *demoSection, html []string) {
	name := "demo-" + sec.id + "-" + strconv.Itoa(w.count)
	w.count++
	if w.d.examples[name] == nil {
		var preview, code []string
		for _, h := range html {
			preview = append(preview, w.d.demoHTML(h, w.href))
			code = append(code, w.d.demoHTML(demoCode(h), w.href))
		}
		w.d.examples[name] = &example{Name: name, HTML: dedent(strings.Join(preview, "\n")), Code: strings.Join(code, "\n\n"), Demo: true}
	}
	for _, m := range idAttrs.FindAllStringSubmatch(w.d.examples[name].HTML, -1) {
		w.page.reserved = append(w.page.reserved, m[1])
	}
	w.line("{{example %q}}", name)
}

func (w *pageWriter) items(sec *demoSection, items []demoItem, code bool) {
	var run []string
	end := func() {
		if len(run) > 0 {
			w.example(sec, run)
			run = nil
		}
	}
	for _, it := range items {
		switch it.kind {
		case "html":
			run = append(run, it.text)
		case "note":
			end()
			w.line("%s", it.text)
		case "code":
			end()
			if code {
				lang := "js"
				if strings.HasPrefix(it.text, "<") {
					lang = "html"
				}
				w.line("```%s\n%s\n```", lang, it.text)
			}
		}
	}
	end()
}

var idAttrs = regexp.MustCompile(`\sid="([^"]+)"`)

func (d *docsSite) generatePage(href string, readme readmeDoc, stops map[string]bool) *docPage {
	c := d.components[href]
	w := &pageWriter{d: d, href: href, page: &docPage{Href: href, Title: d.titles[href]}}
	for _, id := range d.sectionsFor(href) {
		if sec := d.demo[id]; sec != nil {
			w.sections = append(w.sections, sec)
			w.page.reserved = append(w.page.reserved, id)
			w.page.Styles = append(w.page.Styles, docStyles[id]...)
		}
	}
	text := ""
	switch {
	case c != nil:
		text = c.text
		if i := strings.Index(text, "\n"); strings.HasPrefix(text, "#") && i >= 0 {
			text = text[i+1:]
		}
		text = strings.Trim(text, "\n")
		for _, line := range strings.Split(text, "\n") {
			if m := mdHeading.FindStringSubmatch(line); m != nil && len(m[1]) > 3 {
				text = strings.Replace(text, line, "### "+m[2], 1)
			}
		}
	case d.readme[href] != "":
		text = readme.section(strings.TrimPrefix(d.readme[href], githubURL+"#"), stops)
	}
	text = d.fixLinks(text)
	if c == nil && text == "" && len(w.sections) == 0 {
		return nil
	}
	switch {
	case d.descriptions[href] != "":
		w.page.Description = d.descriptions[href]
	case len(w.sections) > 0 && w.sections[0].description != "":
		w.page.Description = plainText(w.sections[0].description)
	case firstParagraph(text) != "":
		w.page.Description = firstParagraph(text)
	default:
		w.page.Description = w.page.Title + "."
	}
	code := text == ""
	if len(w.sections) > 0 {
		first := w.sections[0]
		w.page.Section = first.id
		w.items(first, first.parts[0].items, code)
	}
	if c != nil {
		d.usage(w, c, text)
	} else if text != "" {
		if len(w.sections) > 0 && !strings.HasPrefix(text, "#") {
			w.line("## Usage")
		}
		w.line("%s", text)
	}
	for i, sec := range w.sections {
		parts := sec.parts
		if i == 0 {
			parts = parts[1:]
			if len(parts) > 0 {
				w.line("## Examples")
			}
		} else {
			w.line("## %s", sec.title)
			if sec.description != "" {
				w.line("%s", sec.description)
			}
		}
		for _, part := range parts {
			if part.title != "" {
				w.line("### %s", part.title)
			}
			w.items(sec, part.items, code)
		}
	}
	if c != nil {
		d.apiReference(w, c)
	}
	w.page.Source = strings.TrimRight(w.b.String(), "\n") + "\n"
	if len(w.sections) > 0 {
		w.page.Styles = append(w.page.Styles, "demo.css")
		w.page.Scripts = []string{"demo.js"}
	}
	return w.page
}

func (d *docsSite) groupFiles(c *catalogComponent) []string {
	groups := slices.Compact(append(append([]string{"core"}, c.Needs...), c.Group))
	var css, js []string
	for _, g := range d.catalog.Groups {
		if slices.Contains(groups, g.Name) {
			css = append(css, g.CSS)
			if c.JS && g.JS != "" {
				js = append(js, g.JS)
			}
		}
	}
	return append(css, js...)
}

func (d *docsSite) usage(w *pageWriter, c *catalogComponent, text string) {
	name := strings.ToLower(c.Title)
	w.line("## Installation")
	switch {
	case c.Group == "chart":
		w.line("Load `clanker-ui.css` and `clanker-ui.js`, and import the chart functions from `clanker-ui-chart.js`.")
	case c.JS:
		w.line("Load `clanker-ui.css` and `clanker-ui.js`.")
	default:
		w.line("Load `clanker-ui.css`. The %s needs no JavaScript.", name)
	}
	w.line("With the minified group files, load %s.", codeJoin(d.groupFiles(c)))
	w.line("## Usage")
	if c.SameAs != "" {
		for href, other := range d.components {
			if other.Name == c.SameAs {
				w.line("%s uses the markup, events, and API of [%s](%s).", c.Title, other.Title, href)
			}
		}
	}
	if !strings.Contains(text, "```html") && c.Example != "" {
		w.line("```html\n%s\n```", c.Example)
	}
	if !strings.Contains(text, "```js") && c.Script != "" {
		w.line("```js\n%s\n```", c.Script)
	}
	var kept []string
	for _, blk := range textBlocks(text) {
		lead := strings.TrimPrefix(blk, "- ")
		moved := false
		for _, k := range c.Keyboard {
			if strings.HasPrefix(lead, k) && !strings.HasPrefix(blk, "```") {
				moved = true
			}
		}
		if moved {
			w.keys = append(w.keys, "- "+strings.TrimRight(lead, "\n"))
		} else {
			kept = append(kept, blk)
		}
	}
	for _, k := range c.Keyboard {
		if !strings.Contains(text, k) {
			w.keys = append(w.keys, "- "+k)
		}
	}
	if text = strings.Trim(strings.Join(kept, ""), "\n"); text != "" {
		w.line("%s", text)
	}
}

func textBlocks(text string) []string {
	var blocks []string
	fence := false
	for _, line := range strings.SplitAfter(text, "\n") {
		trim := strings.TrimSpace(line)
		if len(blocks) == 0 || !fence && trim != "" && line[0] != ' ' && line[0] != '\t' {
			blocks = append(blocks, "")
		}
		blocks[len(blocks)-1] += line
		if strings.HasPrefix(trim, "```") {
			fence = !fence
		}
	}
	return blocks
}

func cellText(s string) string {
	return strings.ReplaceAll(s, "|", `\|`)
}

func (d *docsSite) apiReference(w *pageWriter, c *catalogComponent) {
	w.line("## API Reference")
	root := c.Name
	var other []string
	for _, p := range c.Parts {
		if p.Root {
			root = p.Slot
		}
		if len(p.Attributes) == 0 && len(p.State) == 0 {
			if !slices.Contains(c.KitAdds, p.Slot) {
				other = append(other, p.Slot)
			}
			continue
		}
		title := titleWords(p.Slot)
		if rest, ok := strings.CutPrefix(p.Slot, c.Name); ok {
			title = strings.TrimSpace(c.Title + " " + titleWords(strings.TrimPrefix(rest, "-")))
		}
		w.line("### %s", title)
		by := "You"
		if slices.Contains(c.KitAdds, p.Slot) {
			w.line("The kit adds the `%s` part.", p.Slot)
		}
		var rows []string
		for _, k := range sortedKeys(p.Attributes) {
			rows = append(rows, fmt.Sprintf("| `%s` | %s | %s |", k, cellText(attrValues(p.Attributes[k])), by))
		}
		for _, k := range p.State {
			rows = append(rows, fmt.Sprintf("| `%s` | | The kit |", k))
		}
		w.line("| Attribute | Values | Set by |\n| --- | --- | --- |\n%s", strings.Join(rows, "\n"))
	}
	if len(other) > 0 {
		w.line("Other parts: %s.", codeJoin(other))
	}
	if len(c.KitAdds) > 0 {
		w.line("The kit adds these parts. Do not write them: %s.", codeJoin(c.KitAdds))
	}
	attrTable := func(title, intro string, attrs map[string]any) {
		if len(attrs) == 0 {
			return
		}
		w.line("### %s", title)
		w.line("%s", intro)
		var rows []string
		for _, k := range sortedKeys(attrs) {
			rows = append(rows, fmt.Sprintf("| `%s` | %s |", k, cellText(attrValues(attrs[k]))))
		}
		w.line("| Attribute | Values |\n| --- | --- |\n%s", strings.Join(rows, "\n"))
	}
	attrTable("Part Attributes", "Put these attributes on an element of another component, for example a `button`, to give it this behavior.", c.PartAttributes)
	attrTable("Other Attributes", "The usage text above also names these attributes.", c.Options)
	if len(c.Events) > 0 {
		w.line("### Events")
		var rows []string
		for _, e := range c.Events {
			target := e.Target
			if target == "root" {
				target = root
			}
			detail := e.Notes
			if detail == "" && len(e.Detail) > 0 {
				detail = "`{ " + strings.Join(e.Detail, ", ") + " }`"
				if e.Cancelable {
					detail += ", cancelable"
				}
			}
			rows = append(rows, fmt.Sprintf("| `%s` | `%s` | %s |", e.Name, target, cellText(detail)))
		}
		w.line("| Event | Target | Detail |\n| --- | --- | --- |\n%s", strings.Join(rows, "\n"))
	}
	if len(c.Exports) > 0 {
		w.line("### JavaScript")
		module := "clanker-ui.js"
		var list []string
		for _, name := range c.Exports {
			for _, e := range d.catalog.Exports {
				if e.Name == name {
					module = e.Module
					item := "- `" + e.Signature + "`"
					if e.Notes != "" {
						item += ": " + e.Notes
					}
					list = append(list, item)
				}
			}
		}
		w.line("Import these functions from `%s`.", module)
		w.line("%s", strings.Join(list, "\n"))
	}
	if len(w.keys) > 0 {
		w.line("## Keyboard and Accessibility")
		w.line("%s", strings.Join(w.keys, "\n"))
	}
}
