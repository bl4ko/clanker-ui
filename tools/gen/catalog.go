package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"sort"
	"strconv"
	"strings"
)

const (
	catalogVersion = "0.1.0"
	catalogBaseUI  = "1.6.0"
	catalogSite    = "https://bl4ko.github.io/clanker-ui"
	catalogRepo    = "https://github.com/bl4ko/clanker-ui"
	catalogRaw     = "https://raw.githubusercontent.com/bl4ko/clanker-ui/main"
	catalogFile    = "skills/clanker-ui/references/clanker-ui.json"
	catalogSchema  = "skills/clanker-ui/references/clanker-ui.schema.json"
	catalogComps   = "skills/clanker-ui/references/components.md"
	catalogCompDir = "skills/clanker-ui/references/components"
	catalogEvents  = "skills/clanker-ui/references/events.md"
	catalogLLMs    = "docs/llms-full.txt"
	catalogExDir   = "tools/gen/examples"
)

type catalog struct {
	Schema      string         `json:"$schema"`
	Name        string         `json:"name"`
	Version     string         `json:"version"`
	Description string         `json:"description"`
	License     string         `json:"license"`
	Repository  string         `json:"repository"`
	Docs        string         `json:"docs"`
	Shadcn      string         `json:"shadcn"`
	BaseUI      string         `json:"baseUi"`
	CSP         string         `json:"csp"`
	CSPMeta     string         `json:"cspMeta"`
	Files       catFiles       `json:"files"`
	Groups      []catGroup     `json:"groups"`
	Global      catAttrs       `json:"globalAttributes"`
	Exports     []catExport    `json:"exports"`
	Components  []catComponent `json:"components"`
}

type catFiles struct {
	Note     string     `json:"note"`
	Readable catFileSet `json:"readable"`
	Bundle   catFileSet `json:"bundle"`
	Optional []catFile  `json:"optional"`
}

type catFileSet struct {
	CSS []string `json:"css"`
	JS  []string `json:"js"`
}

type catFile struct {
	File string `json:"file"`
	Use  string `json:"use"`
}

type catGroup struct {
	Name       string   `json:"name"`
	CSS        string   `json:"css"`
	JS         string   `json:"js,omitempty"`
	Components []string `json:"components"`
}

type catAttrs map[string]any

type catPart struct {
	Slot       string   `json:"slot"`
	Root       bool     `json:"root,omitempty"`
	KitAdds    bool     `json:"-"`
	JS         bool     `json:"js,omitempty"`
	Attributes catAttrs `json:"attributes,omitempty"`
	State      []string `json:"state,omitempty"`
}

type catEvent struct {
	Name       string   `json:"name"`
	Target     string   `json:"target"`
	Detail     []string `json:"detail"`
	Cancelable bool     `json:"cancelable,omitempty"`
	Notes      string   `json:"notes,omitempty"`
}

type catExport struct {
	Name      string `json:"name"`
	Module    string `json:"module"`
	Component string `json:"component,omitempty"`
	Signature string `json:"signature"`
	Notes     string `json:"notes,omitempty"`
}

type catComponent struct {
	Name           string     `json:"name"`
	Title          string     `json:"title"`
	Group          string     `json:"group"`
	Needs          []string   `json:"needs"`
	JS             bool       `json:"js"`
	Parts          []catPart  `json:"parts"`
	PartAttributes catAttrs   `json:"partAttributes"`
	Options        catAttrs   `json:"options"`
	KitAdds        []string   `json:"kitAdds"`
	Events         []catEvent `json:"events"`
	Exports        []string   `json:"exports"`
	Keyboard       []string   `json:"keyboard"`
	Example        string     `json:"example"`
	ExampleSource  string     `json:"exampleSource"`
	Docs           string     `json:"docs"`
	DocsMarkdown   string     `json:"docsMarkdown"`
	Readme         string     `json:"readme"`
	SameAs         string     `json:"sameAs,omitempty"`
	Script         string     `json:"script,omitempty"`
}

func catalogMain(args []string) error {
	fset := flag.NewFlagSet("catalog", flag.ExitOnError)
	root := fset.String("root", ".", "repository root")
	check := fset.Bool("check", false, "only check that the generated files are fresh")
	fset.Parse(args)
	files, _, err := buildCatalog(*root)
	if err != nil {
		return err
	}
	var stale []string
	for _, name := range sortedKeys(files) {
		path := filepath.Join(*root, name)
		if *check {
			if old, err := os.ReadFile(path); err != nil || !bytes.Equal(old, files[name]) {
				stale = append(stale, name)
			}
			continue
		}
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(path, files[name], 0o644); err != nil {
			return err
		}
		fmt.Println(path)
	}
	for _, name := range extraCompFiles(*root, files) {
		if *check {
			stale = append(stale, name)
		} else if err := os.Remove(filepath.Join(*root, name)); err != nil {
			return err
		}
	}
	if len(stale) > 0 {
		return fmt.Errorf("stale: %s (run go run ./tools/gen catalog)", strings.Join(stale, ", "))
	}
	return nil
}

func extraCompFiles(root string, files map[string][]byte) []string {
	found, _ := filepath.Glob(filepath.Join(root, catalogCompDir, "*.md"))
	var out []string
	for _, f := range found {
		name := catalogCompDir + "/" + filepath.Base(f)
		if files[name] == nil {
			out = append(out, name)
		}
	}
	return out
}

type mdSection struct {
	level       int
	title, slug string
	body        string
	comps       []string
}

var (
	mdHeading   = regexp.MustCompile(`^(#{1,6}) (.+)$`)
	mdCode      = regexp.MustCompile("`([^`]+)`")
	mdFence     = regexp.MustCompile("(?s)```html\n(.*?)\n[ \t]*```")
	mdJSFence   = regexp.MustCompile("(?s)```js\n(.*?)\n[ \t]*```")
	mdAnchor    = regexp.MustCompile(`\]\(#`)
	mdTextFence = regexp.MustCompile("(?s)```text\n(.*?)\n[ \t]*```")
	valueList   = regexp.MustCompile(`^[A-Za-z0-9./-]*(\|[A-Za-z0-9./-]*)+$`)
	attrCode    = regexp.MustCompile(`^(data-[a-z0-9-]+)(?:="([^"]*)")?$`)
	catDefine   = regexp.MustCompile(`define\("([a-z0-9-]+)"`)
	jsMadeSlot  = regexp.MustCompile(`"data-slot": *"([a-z0-9-]+)"|setAttribute\("data-slot", "([a-z0-9-]+)"\)|dataset\.slot = "([a-z0-9-]+)"`)
	jsEmit      = regexp.MustCompile(`emit\([^,()]*(?:\([^()]*\))?[^,()]*, *"([a-z-]+:[a-z-]+)"|"([a-z-]+:(?:open|close|change))"`)
	jsSetAttr   = regexp.MustCompile(`(?:setAttribute|toggleAttribute)\("(data-[a-z0-9-]+)"|dataset\.([a-zA-Z]+) *=[^=]`)
	keyWord     = regexp.MustCompile(`\b(Keyboard|Keys|Up|Down|Enter|Escape|Esc|Space|Arrow(?:Up|Down|Left|Right)?|arrows?|Home|End|Page ?Up|Page ?Down|Backspace|Delete|F6|Shift\+F10|Ctrl|Cmd|Alt\+[A-Za-z]+|Shift\+[A-Za-z]+|Tab)\b`)
	slugDrop    = regexp.MustCompile(`[^a-z0-9 _-]`)
)

var catalogTitleComps = map[string][]string{
	"Theme toggle and switch": {"theme"},
	"Stat tile and sparkline": {"chart"},
}

var catalogMirror = [][2]string{{"dropdown-menu", "context-menu"}, {"dropdown-menu", "menubar"}}

var catalogSameAs = map[string]string{"sonner": "toast"}

var catalogDocsPage = map[string]string{"theme": "theme-switch"}

var catalogOptionAttrs = []string{"data-variant", "data-size", "data-orientation", "data-side", "data-align", "data-spacing"}

var catalogGeneric = map[string]bool{
	"id": true, "class": true, "role": true, "type": true, "for": true, "href": true, "src": true, "alt": true, "title": true,
	"tabindex": true, "placeholder": true, "dir": true, "lang": true, "autocomplete": true, "inputmode": true, "rel": true,
	"target": true, "loading": true, "width": true, "height": true, "colspan": true, "rowspan": true, "scope": true,
	"label": true, "autofocus": true, "name": true, "value": true, "disabled": true, "required": true, "hidden": true,
	"open": true, "checked": true, "selected": true, "readonly": true, "multiple": true, "min": true, "max": true,
	"step": true, "maxlength": true, "minlength": true, "pattern": true, "method": true, "action": true, "novalidate": true,
	"datetime": true, "rows": true, "cols": true,
}

var catalogKitMade = []string{"checkbox-indicator", "radio-group-indicator", "dropdown-menu-checkbox-item-indicator", "dropdown-menu-radio-item-indicator"}

var catalogKitGlobal = map[string]bool{"data-system-theme": true, "data-keyboard": true}

var catalogDevSections = []string{"Docs site", "Demo and tests", "How parity with shadcn is tested", "Contributing", "Credits"}

func mdSlug(title string) string {
	s := strings.ToLower(strings.TrimSpace(title))
	s = slugDrop.ReplaceAllString(s, "")
	return strings.ReplaceAll(s, " ", "-")
}

func mdSections(src string) []mdSection {
	var out []mdSection
	var cur *mdSection
	var body strings.Builder
	fence := ""
	flush := func() {
		if cur != nil {
			cur.body = body.String()
			out = append(out, *cur)
		}
		body.Reset()
	}
	for _, line := range strings.Split(src, "\n") {
		trim := strings.TrimSpace(line)
		if strings.HasPrefix(trim, "```") {
			ticks := trim[:len(trim)-len(strings.TrimLeft(trim, "`"))]
			switch {
			case fence == "":
				fence = ticks
			case ticks == fence && strings.TrimLeft(trim, "`") == "":
				fence = ""
			}
		}
		if m := mdHeading.FindStringSubmatch(line); m != nil && fence == "" {
			flush()
			cur = &mdSection{level: len(m[1]), title: m[2], slug: mdSlug(m[2])}
			continue
		}
		body.WriteString(line)
		body.WriteByte('\n')
	}
	flush()
	return out
}

type htmlNode struct {
	tag        string
	attrs      [][2]string
	start, end int
	children   []*htmlNode
}

var (
	htmlTag  = regexp.MustCompile(`<(/?)([a-zA-Z][a-zA-Z0-9-]*)((?:\s+[^\s=>/"']+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>"']+))?)*)\s*(/?)>`)
	htmlAttr = regexp.MustCompile(`([^\s=>/"']+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>"']+)))?`)
	htmlVoid = map[string]bool{"input": true, "img": true, "br": true, "hr": true, "meta": true, "link": true, "source": true, "col": true, "area": true, "wbr": true, "base": true, "embed": true, "track": true, "path": true, "circle": true, "rect": true, "line": true}
)

func parseFragment(src string) []*htmlNode {
	root := &htmlNode{}
	stack := []*htmlNode{root}
	for _, m := range htmlTag.FindAllStringSubmatchIndex(src, -1) {
		closing := src[m[2]:m[3]] == "/"
		tag := strings.ToLower(src[m[4]:m[5]])
		if closing {
			for i := len(stack) - 1; i > 0; i-- {
				if stack[i].tag == tag {
					for _, n := range stack[i:] {
						n.end = m[1]
					}
					stack = stack[:i]
					break
				}
			}
			continue
		}
		n := &htmlNode{tag: tag, start: m[0], end: m[1]}
		for _, a := range htmlAttr.FindAllStringSubmatch(src[m[6]:m[7]], -1) {
			v := a[2] + a[3] + a[4]
			n.attrs = append(n.attrs, [2]string{strings.ToLower(a[1]), v})
		}
		parent := stack[len(stack)-1]
		parent.children = append(parent.children, n)
		if !htmlVoid[tag] && src[m[8]:m[9]] != "/" {
			stack = append(stack, n)
		}
	}
	for _, n := range stack[1:] {
		n.end = len(src)
	}
	return root.children
}

func (n *htmlNode) attr(name string) (string, bool) {
	for _, a := range n.attrs {
		if a[0] == name {
			return a[1], true
		}
	}
	return "", false
}

func walkNodes(nodes []*htmlNode, fn func(*htmlNode)) {
	for _, n := range nodes {
		fn(n)
		walkNodes(n.children, fn)
	}
}

type attrInfo struct {
	values map[string]bool
	list   bool
}

type attrSet map[string]*attrInfo

func (s attrSet) add(name, value string) {
	a := s[name]
	if a == nil {
		a = &attrInfo{values: map[string]bool{}}
		s[name] = a
	}
	if valueList.MatchString(value) {
		a.list = true
		for _, v := range strings.Split(value, "|") {
			a.values[v] = true
		}
		return
	}
	a.values[value] = true
}

func (s attrSet) addCode(code string, m []string) {
	if strings.Contains(code, "=") {
		s.add(m[1], m[2])
	} else {
		s.mention(m[1])
	}
}

func (s attrSet) mention(name string) {
	if s[name] == nil {
		s[name] = &attrInfo{values: map[string]bool{}}
	}
}

func (s attrSet) addEnum(name, value string) {
	s.add(name, value)
	s[name].list = true
}

func (s attrSet) json() catAttrs {
	out := catAttrs{}
	for name, a := range s {
		vals := sortedKeys(a.values)
		switch {
		case a.list || slices.Contains(catalogOptionAttrs, name) && len(vals) > 0 && !(len(vals) == 1 && vals[0] == ""):
			out[name] = vals
		case len(vals) == 0:
			out[name] = "any"
		case len(vals) == 1 && vals[0] == "":
			out[name] = "boolean"
		case boolWords(vals):
			out[name] = append([]string{"false", "true"}, func() []string {
				if a.values[""] {
					return []string{""}
				}
				return nil
			}()...)
		case allNumbers(vals):
			out[name] = "number"
		default:
			out[name] = "string"
		}
	}
	return out
}

func (s attrSet) idJSON() catAttrs {
	out := s.json()
	for name, v := range out {
		if v == "string" {
			out[name] = "id"
		}
	}
	return out
}

func boolWords(vals []string) bool {
	for _, v := range vals {
		if v != "" && v != "true" && v != "false" {
			return false
		}
	}
	return true
}

func allNumbers(vals []string) bool {
	for _, v := range vals {
		if v == "" {
			continue
		}
		if _, err := strconv.ParseFloat(v, 64); err != nil {
			return false
		}
	}
	return true
}

type compData struct {
	sections []mdSection
	parts    map[string]attrSet
	state    map[string]map[string]bool
	partAttr attrSet
	options  attrSet
	fence    string
}

func newCompData() *compData {
	return &compData{parts: map[string]attrSet{}, state: map[string]map[string]bool{}, partAttr: attrSet{}, options: attrSet{}}
}

func (d *compData) part(slot string) attrSet {
	if d.parts[slot] == nil {
		d.parts[slot] = attrSet{}
	}
	return d.parts[slot]
}

type catalogBuild struct {
	t          *groupTable
	data       map[string]*compData
	global     attrSet
	markup     map[string]bool
	defined    map[string]bool
	made       map[string]bool
	jsSet      map[string]bool
	cssSlots   map[string]bool
	jsEvents   map[string]bool
	listedPart map[string]bool
	named      map[string]bool
}

func (b *catalogBuild) markupElem(n *htmlNode) {
	slot, _ := n.attr("data-slot")
	comp := b.t.component(slot)
	if slot != "" && comp != "" {
		b.markup[slot] = true
	}
	for _, a := range n.attrs {
		name, value := a[0], a[1]
		if name == "data-slot" || b.global[name] != nil || catalogKitGlobal[name] || strings.HasPrefix(name, "data-string-") {
			continue
		}
		if pc := b.t.partComponent(strings.TrimPrefix(name, "data-")); strings.HasPrefix(name, "data-") && pc != "" && pc != comp && !strings.HasPrefix(comp, pc+"-") {
			b.data[pc].partAttr.add(name, value)
			continue
		}
		if comp == "" {
			continue
		}
		if !strings.HasPrefix(name, "data-") && (catalogGeneric[name] || strings.HasPrefix(name, "aria-")) {
			continue
		}
		b.data[comp].part(slot).add(name, value)
	}
}

func (b *catalogBuild) markupHTML(src string) {
	walkNodes(parseFragment(src), b.markupElem)
}

func buildCatalog(root string) (map[string][]byte, *catalog, error) {
	read := func(name string) (string, error) {
		bs, err := os.ReadFile(filepath.Join(root, name))
		return string(bs), err
	}
	t, err := readGroups(filepath.Join(root, "tools", "gen", "groups.tsv"))
	if err != nil {
		return nil, nil, err
	}
	readme, err := read("README.md")
	if err != nil {
		return nil, nil, err
	}
	css, err := read("clanker-ui.css")
	if err != nil {
		return nil, nil, err
	}
	var js strings.Builder
	for _, f := range []string{"clanker-ui.js", "clanker-ui-chart.js"} {
		s, err := read(f)
		if err != nil {
			return nil, nil, err
		}
		js.WriteString(s)
	}
	navRaw, err := read("docs/nav.json")
	if err != nil {
		return nil, nil, err
	}
	b := &catalogBuild{t: t, data: map[string]*compData{}, global: attrSet{}, markup: map[string]bool{}, defined: map[string]bool{}, made: map[string]bool{}, jsSet: map[string]bool{}, cssSlots: map[string]bool{}, jsEvents: map[string]bool{}, listedPart: map[string]bool{}, named: map[string]bool{}}
	for _, c := range t.order {
		b.data[c] = newCompData()
	}
	sections := mdSections(readme)
	for i, s := range sections {
		sections[i].comps = b.sectionComps(s)
		for _, c := range sections[i].comps {
			b.data[c].sections = append(b.data[c].sections, sections[i])
		}
	}
	if err := b.globals(sections); err != nil {
		return nil, nil, err
	}
	b.scanJS(js.String())
	if err := b.scanCSS(css); err != nil {
		return nil, nil, err
	}
	for _, s := range sections {
		b.scanSection(s)
	}
	for _, s := range sections {
		b.scanProse(s)
	}
	b.mirror()
	examples := map[string]string{}
	for _, c := range t.order {
		bs, err := os.ReadFile(filepath.Join(root, catalogExDir, c+".html"))
		if errors.Is(err, os.ErrNotExist) {
			continue
		}
		if err != nil {
			return nil, nil, err
		}
		examples[c] = strings.TrimRight(string(bs), "\n")
		walkNodes(parseFragment(examples[c]), func(n *htmlNode) {
			if s, _ := n.attr("data-slot"); s != "" {
				b.markup[s] = true
			}
		})
	}
	var nav struct {
		Groups []struct {
			Items []struct{ Title, Href string } `json:"items"`
		} `json:"groups"`
	}
	if err := json.Unmarshal([]byte(navRaw), &nav); err != nil {
		return nil, nil, fmt.Errorf("docs/nav.json: %w", err)
	}
	navTitle := map[string]string{}
	for _, g := range nav.Groups {
		for _, it := range g.Items {
			if p, ok := strings.CutPrefix(it.Href, "/docs/components/"); ok {
				navTitle[p] = it.Title
			}
		}
	}
	csp := ""
	for _, s := range sections {
		if s.title == "Use in a project" {
			if m := mdTextFence.FindStringSubmatch(s.body); m != nil {
				csp = strings.TrimSpace(m[1])
			}
		}
	}
	if !strings.Contains(csp, "require-trusted-types-for 'script'") {
		return nil, nil, fmt.Errorf("README.md: no CSP text fence with require-trusted-types-for in \"Use in a project\"")
	}
	events, err := b.events(sections)
	if err != nil {
		return nil, nil, err
	}
	exports := b.exports(sections)
	cat := &catalog{
		Schema:      "./clanker-ui.schema.json",
		Name:        "clanker-ui",
		Version:     catalogVersion,
		Description: firstParagraph(readme),
		License:     "MIT",
		Repository:  catalogRepo,
		Docs:        catalogSite + "/",
		Shadcn:      shadcnSHA,
		BaseUI:      catalogBaseUI,
		CSP:         csp,
		CSPMeta:     strings.Replace(csp, "; frame-ancestors 'none'", "", 1),
		Global:      b.global.json(),
		Exports:     exports,
	}
	cat.Files = catFiles{
		Note:     "Put all files in one directory of the static site. In the repository and in the release zip, the .min files are in dist/; the release also has each file as a separate asset. Use the readable set or the .min files, never both.",
		Readable: catFileSet{CSS: []string{"clanker-ui.css"}, JS: []string{"clanker-ui.js"}},
		Bundle:   catFileSet{CSS: []string{"clanker-ui.min.css"}, JS: []string{"clanker-ui-core.min.js", "clanker-ui.min.js"}},
		Optional: []catFile{
			{"clanker-ui-theme.js", "classic script before the module, for apps with a theme toggle, switch, or scheme picker (no flash of the wrong theme)"},
			{"clanker-ui-themes.css", "color schemes; after clanker-ui.css (min: clanker-ui-themes.min.css)"},
			{"clanker-ui-a11y.css", "accessibility layer; after the themes file (min: clanker-ui-a11y.min.css)"},
			{"clanker-ui-chart.js", "chart, sparkline, and stat tile module (min: clanker-ui-chart.min.js with clanker-ui-chart.min.css)"},
		},
	}
	for _, g := range distGroups {
		grp := catGroup{Name: g, CSS: "clanker-ui-" + g + ".min.css"}
		if slices.Contains(distJSGroups, g) || g == "chart" {
			grp.JS = "clanker-ui-" + g + ".min.js"
		}
		for _, c := range t.order {
			if t.group[c] == g {
				grp.Components = append(grp.Components, c)
			}
		}
		cat.Groups = append(cat.Groups, grp)
	}
	var errs []error
	for _, c := range t.order {
		comp, err := b.component(c, navTitle, events[c], exports, examples)
		errs = append(errs, err)
		cat.Components = append(cat.Components, comp)
	}
	if err := errors.Join(errs...); err != nil {
		return nil, nil, err
	}
	for i, c := range cat.Components {
		for _, o := range cat.Components {
			if catalogSameAs[c.Name] == o.Name {
				cat.Components[i].SameAs = o.Name
				cat.Components[i].JS = o.JS
				cat.Components[i].Exports = o.Exports
			}
		}
	}
	jsonOut, err := catalogJSON(cat)
	if err != nil {
		return nil, nil, err
	}
	files := map[string][]byte{catalogFile: jsonOut}
	files[catalogComps] = []byte(catalogIndex(cat))
	for _, c := range cat.Components {
		full := b.fullText(c.Name, sections)
		if full == "" {
			return nil, nil, fmt.Errorf("%s: no README section", c.Name)
		}
		files[c.Readme] = []byte(componentFile(cat, c, full))
	}
	files[catalogEvents] = []byte(eventsMarkdown(cat))
	files[catalogLLMs] = []byte(llmsFull(cat, sections))
	return files, cat, nil
}

func catalogJSON(cat *catalog) ([]byte, error) {
	raw, err := json.MarshalIndent(cat, "", "  ")
	if err != nil {
		return nil, err
	}
	var out, item bytes.Buffer
	in := false
	for _, line := range strings.Split(string(raw), "\n") {
		switch {
		case !in && line == "    {":
			in = true
			item.Reset()
			item.WriteString(line)
		case in:
			item.WriteString(line)
			if strings.HasPrefix(line, "    }") {
				in = false
				body, comma := strings.CutSuffix(item.String(), ",")
				var c bytes.Buffer
				if err := json.Compact(&c, []byte(body)); err != nil {
					return nil, err
				}
				out.WriteString("    ")
				out.Write(c.Bytes())
				if comma {
					out.WriteByte(',')
				}
				out.WriteByte('\n')
			}
		default:
			out.WriteString(line)
			out.WriteByte('\n')
		}
	}
	return append(bytes.TrimRight(out.Bytes(), "\n"), '\n'), nil
}

func firstParagraph(readme string) string {
	for _, p := range strings.Split(readme, "\n\n") {
		p = strings.TrimSpace(p)
		if p != "" && !strings.HasPrefix(p, "#") {
			p = regexp.MustCompile(`\[([^\]]+)\]\([^)]+\)`).ReplaceAllString(p, "$1")
			return strings.Join(strings.Fields(p), " ")
		}
	}
	return ""
}

func (b *catalogBuild) mirror() {
	for _, m := range catalogMirror {
		src, dst := b.data[m[0]], b.data[m[1]]
		for slot, attrs := range src.parts {
			to := m[1] + strings.TrimPrefix(slot, m[0])
			for name, a := range attrs {
				for v := range a.values {
					dst.part(to).add(name, v)
				}
				if a.list {
					dst.part(to)[name].list = true
				}
			}
		}
		for name, a := range src.options {
			if dst.options[name] == nil {
				dst.options[name] = a
			}
		}
	}
}

func (b *catalogBuild) sectionComps(s mdSection) []string {
	if s.level < 3 || s.level > 4 {
		return nil
	}
	if c, ok := catalogTitleComps[s.title]; ok {
		return c
	}
	var out []string
	title := strings.ReplaceAll(s.title, " and ", ", ")
	for _, piece := range strings.Split(title, ",") {
		name := strings.ReplaceAll(strings.ToLower(strings.TrimSpace(piece)), " ", "-")
		if _, ok := b.t.group[name]; !ok {
			return nil
		}
		out = append(out, name)
	}
	return out
}

func (b *catalogBuild) globals(sections []mdSection) error {
	perPart := []string{"data-slot", "data-variant", "data-size", "data-state", "data-orientation", "data-disabled"}
	for _, s := range sections {
		if s.title != "Markup conventions" {
			continue
		}
		for _, row := range mdTable(s.body) {
			for _, code := range mdCode.FindAllStringSubmatch(row[0], -1) {
				m := attrCode.FindStringSubmatch(code[1])
				if m == nil || slices.Contains(perPart, m[1]) || catalogKitGlobal[m[1]] {
					continue
				}
				b.global.add(m[1], m[2])
			}
		}
	}
	if len(b.global) == 0 {
		return fmt.Errorf("README.md: no attribute table in \"Markup conventions\"")
	}
	b.global.addEnum("data-icon", "inline-start|inline-end")
	b.global["data-side"] = nil
	b.global.addEnum("data-side", "top|right|bottom|left|inline-start|inline-end")
	b.global["data-align"] = nil
	b.global.addEnum("data-align", "start|center|end")
	for _, n := range []string{"data-side-offset", "data-align-offset"} {
		b.global[n] = nil
		b.global.add(n, "0")
	}
	return nil
}

func mdTable(body string) [][]string {
	var rows [][]string
	for _, line := range strings.Split(body, "\n") {
		line = strings.TrimSpace(line)
		if !strings.HasPrefix(line, "|") || strings.HasPrefix(line, "| ---") {
			continue
		}
		line = strings.ReplaceAll(line, `\|`, "\x00")
		var cells []string
		for _, c := range strings.Split(strings.Trim(line, "|"), "|") {
			cells = append(cells, strings.TrimSpace(strings.ReplaceAll(c, "\x00", "|")))
		}
		rows = append(rows, cells)
	}
	if len(rows) > 0 {
		rows = rows[1:]
	}
	return rows
}

func (b *catalogBuild) scanJS(src string) {
	for _, m := range catDefine.FindAllStringSubmatch(src, -1) {
		b.defined[m[1]] = true
	}
	for _, m := range jsMadeSlot.FindAllStringSubmatch(src, -1) {
		b.made[m[1]+m[2]+m[3]] = true
	}
	for _, s := range catalogKitMade {
		b.made[s] = true
	}
	for _, m := range jsSetAttr.FindAllStringSubmatch(src, -1) {
		if m[1] != "" {
			b.jsSet[m[1]] = true
		} else {
			b.jsSet[attrName(m[2])] = true
		}
	}
	for _, m := range jsEmit.FindAllStringSubmatch(src, -1) {
		b.jsEvents[m[1]+m[2]] = true
	}
}

var cssAttrSel = regexp.MustCompile(`\[(data-[a-z0-9-]+)(?:([~|^$*]?=)["']?([^\]"']*)["']?)?\]`)

func (b *catalogBuild) scanCSS(src string) error {
	tree, err := parseCSS(src)
	if err != nil {
		return err
	}
	var walk func(items []cssItem)
	walk = func(items []cssItem) {
		for _, it := range items {
			if it.rule == nil {
				continue
			}
			p := it.rule.prelude
			if strings.HasPrefix(p, "@") {
				if !strings.HasPrefix(p, "@keyframes") {
					walk(it.rule.items)
				}
				continue
			}
			for _, sel := range splitTop(p, ',') {
				b.cssSelector(strings.TrimSpace(sel))
			}
			walk(it.rule.items)
		}
	}
	walk(tree.items)
	return nil
}

func dropContextArgs(s string) string {
	var b strings.Builder
	for i := 0; i < len(s); {
		loc := wherePart.FindStringIndex(s[i:])
		if loc == nil {
			b.WriteString(s[i:])
			break
		}
		start, open := i+loc[0], i+loc[1]
		depth, j := 1, open
		for ; j < len(s) && depth > 0; j++ {
			if s[j] == '(' {
				depth++
			} else if s[j] == ')' {
				depth--
			}
		}
		arg := s[open : j-1]
		b.WriteString(s[i:start])
		if subjectCompound(strings.TrimSpace(arg)) == strings.TrimSpace(arg) {
			b.WriteString(s[start:j])
		}
		i = j
	}
	return b.String()
}

func (b *catalogBuild) cssSelector(sel string) {
	comp := dropContextArgs(removePseudo(subjectCompound(sel), "not", "has"))
	var slots []string
	for _, m := range slotAttr.FindAllStringSubmatch(outsideParens(comp), -1) {
		slots = append(slots, m[1])
	}
	for _, slot := range slots {
		c := b.t.component(slot)
		if c == "" {
			continue
		}
		b.cssSlots[slot] = true
		d := b.data[c]
		if b.foreignContext(comp, c) {
			continue
		}
		for _, m := range cssAttrSel.FindAllStringSubmatch(comp, -1) {
			name := m[1]
			if name == "data-slot" {
				continue
			}
			if slices.Contains(catalogOptionAttrs, name) && m[2] == "=" {
				d.part(slot).addEnum(name, m[3])
				continue
			}
			if d.state[slot] == nil {
				d.state[slot] = map[string]bool{}
			}
			d.state[slot][name] = true
		}
	}
}

func (b *catalogBuild) foreignContext(compound, c string) bool {
	for _, m := range cssAttrSel.FindAllStringSubmatch(compound, -1) {
		if pc := b.t.partComponent(strings.TrimPrefix(m[1], "data-")); pc != "" && pc != c && !strings.HasPrefix(c, pc+"-") {
			return true
		}
	}
	return false
}

func (b *catalogBuild) scanSection(s mdSection) {
	if len(s.comps) == 0 {
		if s.title == "Parts that are other components (`asChild`)" {
			for _, m := range mdCode.FindAllStringSubmatch(stripFences(s.body), -1) {
				if am := attrCode.FindStringSubmatch(m[1]); am != nil {
					if pc := b.t.partComponent(strings.TrimPrefix(am[1], "data-")); pc != "" {
						b.listedPart[am[1]] = true
						b.data[pc].partAttr.add(am[1], am[2])
					}
				}
			}
			for _, m := range mdFence.FindAllStringSubmatch(s.body, -1) {
				b.markupHTML(m[1])
			}
		}
		return
	}
	for _, m := range mdFence.FindAllStringSubmatch(s.body, -1) {
		b.markupHTML(m[1])
		for _, c := range s.comps {
			if b.data[c].fence == "" && fenceExample(m[1], c, b.t) != "" {
				b.data[c].fence = m[1]
			}
		}
	}
	for _, line := range strings.Split(stripFences(s.body), "\n") {
		from := len(line)
		if loc := kitRenders.FindStringIndex(line); loc != nil {
			from = loc[0]
		}
		for _, loc := range mdCode.FindAllStringSubmatchIndex(line, -1) {
			code := line[loc[2]:loc[3]]
			if !strings.HasPrefix(code, "<") {
				continue
			}
			m := []string{"", code}
			if loc[0] > from {
				walkNodes(parseFragment(m[1]), func(n *htmlNode) {
					if slot, _ := n.attr("data-slot"); slot != "" {
						b.named[slot] = true
					}
				})
				continue
			}
			b.markupHTML(m[1])
		}
	}
	if len(s.comps) == 1 {
		for _, row := range mdTable(s.body) {
			if len(row) < 2 {
				continue
			}
			for _, code := range mdCode.FindAllStringSubmatch(row[0], -1) {
				if m := attrCode.FindStringSubmatch(code[1]); m != nil {
					b.data[s.comps[0]].part(s.comps[0]).addCode(code[1], m)
				}
			}
		}
	}
	text := stripFences(s.body)
	for _, loc := range regexp.MustCompile("`([a-z0-9-]+)` \\(").FindAllStringSubmatchIndex(text, -1) {
		slot := text[loc[2]:loc[3]]
		c := b.t.component(slot)
		if c == "" || !slices.Contains(s.comps, c) {
			continue
		}
		inner := parenBody(text[loc[1]:])
		for _, code := range mdCode.FindAllStringSubmatch(inner, -1) {
			if m := attrCode.FindStringSubmatch(code[1]); m != nil {
				b.data[c].part(slot).addCode(code[1], m)
			}
		}
	}
}

func stripFences(body string) string {
	var b strings.Builder
	fence := ""
	for _, line := range strings.Split(body, "\n") {
		trim := strings.TrimSpace(line)
		if strings.HasPrefix(trim, "```") {
			ticks := trim[:len(trim)-len(strings.TrimLeft(trim, "`"))]
			switch {
			case fence == "":
				fence = ticks
				continue
			case ticks == fence && strings.TrimLeft(trim, "`") == "":
				fence = ""
				continue
			}
		}
		if fence == "" {
			b.WriteString(line)
			b.WriteByte('\n')
		}
	}
	return b.String()
}

func parenBody(s string) string {
	depth, tick := 1, false
	for i := 0; i < len(s); i++ {
		switch s[i] {
		case '`':
			tick = !tick
		case '(':
			if !tick {
				depth++
			}
		case ')':
			if !tick {
				depth--
				if depth == 0 {
					return s[:i]
				}
			}
		}
	}
	return s
}

func (b *catalogBuild) lineComps(s mdSection, line string) []string {
	if m := b.mentioned(s, line); m != nil {
		return m
	}
	return s.comps
}

func (b *catalogBuild) mentioned(s mdSection, line string) []string {
	if len(s.comps) < 2 {
		return s.comps
	}
	found := map[string]bool{}
	for _, m := range mdCode.FindAllStringSubmatch(line, -1) {
		if strings.HasSuffix(m[1], "-") {
			return nil
		}
		if c := b.t.component(m[1]); slices.Contains(s.comps, c) {
			found[c] = true
		}
	}
	text := strings.ToLower(stripCode(line))
	lead := strings.TrimPrefix(strings.TrimSpace(text), "- ")
	for _, c := range s.comps {
		if strings.HasPrefix(lead, strings.ReplaceAll(c, "-", " ")+":") {
			return []string{c}
		}
	}
	comps := slices.Clone(s.comps)
	sort.SliceStable(comps, func(i, j int) bool { return len(comps[i]) > len(comps[j]) })
	for _, c := range comps {
		re := regexp.MustCompile(`\b` + strings.ReplaceAll(c, "-", "[ -]?"))
		if re.MatchString(text) {
			found[c] = true
			text = re.ReplaceAllString(text, " ")
		}
	}
	var out []string
	for _, c := range s.comps {
		if found[c] {
			out = append(out, c)
		}
	}
	return out
}

func (b *catalogBuild) sectionLines(s mdSection) []string {
	var out []string
	for _, line := range strings.Split(stripFences(s.body), "\n") {
		if strings.TrimSpace(line) != "" {
			out = append(out, line)
		}
	}
	return out
}

var (
	stateSentence = regexp.MustCompile(`(?i)\bkit (adds|sets|keeps|gives|writes|copies|renders|builds)\b|\b(gets|has|have)\b`)
	migration     = regexp.MustCompile(`→|^removed:|\bold\b`)
	kitRenders    = regexp.MustCompile(`(?i)\bkit (renders|adds|builds|creates)\b`)
	labelList     = regexp.MustCompile(`^[A-Z][a-z]+(?: [a-z]+)*(?: as [a-z]+(?: [a-z]+)*)?: ` + "`")
	oldCode       = regexp.MustCompile("(?:\\bold \\(?|\\bold\\) )`([^`]+)`|`([^`]+)` →")
)

func (b *catalogBuild) knownPartAttr(name string) string {
	stem := strings.TrimPrefix(name, "data-")
	pc := b.t.component(stem)
	if pc == "" || pc == stem {
		return ""
	}
	if b.listedPart[name] || b.cssSlots[stem] || b.defined[stem] || b.made[stem] || b.markup[stem] || b.named[stem] {
		return pc
	}
	return ""
}

func (b *catalogBuild) scanProse(s mdSection) {
	if len(s.comps) == 0 {
		return
	}
	for _, line := range b.sectionLines(s) {
		old := map[string]bool{}
		for _, m := range oldCode.FindAllStringSubmatch(line, -1) {
			old[m[1]+m[2]] = true
		}
		for _, sentence := range sentences(line) {
			comps := b.mentioned(s, sentence)
			if comps == nil {
				comps = b.lineComps(s, line)
			}
			state := stateSentence.MatchString(stripCode(sentence))
			list := labelList.MatchString(sentence)
			for _, m := range mdCode.FindAllStringSubmatch(sentence, -1) {
				am := attrCode.FindStringSubmatch(m[1])
				if am == nil || old[m[1]] {
					continue
				}
				name := am[1]
				if b.global[name] != nil || catalogKitGlobal[name] || name == "data-slot" || strings.HasPrefix(name, "data-string-") {
					continue
				}
				if pc := b.knownPartAttr(name); pc != "" {
					if !state {
						b.data[pc].partAttr.add(name, am[2])
					}
					continue
				}
				for _, c := range comps {
					d := b.data[c]
					if d.partAttr[name] != nil || b.authored(d, name) {
						continue
					}
					if state || am[2] == "" && !list && b.isState(d, name) {
						continue
					}
					if strings.Contains(m[1], "=") {
						d.options.add(name, am[2])
					} else {
						d.options.mention(name)
					}
				}
			}
		}
	}
}

func (b *catalogBuild) authored(d *compData, name string) bool {
	for _, p := range d.parts {
		if p[name] != nil {
			return true
		}
	}
	return false
}

func (b *catalogBuild) isState(d *compData, name string) bool {
	if b.jsSet[name] {
		return true
	}
	for _, st := range d.state {
		if st[name] {
			return true
		}
	}
	return false
}

func fenceExample(src, comp string, t *groupTable) string {
	nodes := parseFragment(src)
	var keep []string
	for _, n := range nodes {
		owns := false
		walkNodes([]*htmlNode{n}, func(x *htmlNode) {
			if s, _ := x.attr("data-slot"); s != "" && t.component(s) == comp {
				owns = true
			}
		})
		if owns {
			keep = append(keep, dedent(src[lineStart(src, n.start):n.end]))
		}
	}
	return strings.Join(keep, "\n")
}

func lineStart(s string, i int) int {
	j := strings.LastIndexByte(s[:i], '\n') + 1
	if strings.TrimSpace(s[j:i]) == "" {
		return j
	}
	return i
}

func dedent(s string) string {
	lines := strings.Split(s, "\n")
	pad := len(lines[0]) - len(strings.TrimLeft(lines[0], " "))
	for i, l := range lines {
		if len(l)-len(strings.TrimLeft(l, " ")) >= pad {
			lines[i] = l[pad:]
		}
	}
	return strings.Join(lines, "\n")
}

var exampleList = regexp.MustCompile(`="([A-Za-z0-9./-]*)(\|[A-Za-z0-9./-]*)+"`)

func firstValues(s string) string {
	return exampleList.ReplaceAllString(s, `="$1"`)
}

func (b *catalogBuild) events(sections []mdSection) (map[string][]catEvent, error) {
	out := map[string][]catEvent{}
	seen := map[string]bool{}
	for _, s := range sections {
		if s.title != "Events" {
			continue
		}
		for _, row := range mdTable(s.body) {
			if len(row) != 3 {
				continue
			}
			var names []string
			for _, m := range mdCode.FindAllStringSubmatch(row[0], -1) {
				names = append(names, m[1])
			}
			targets := mdCode.FindAllStringSubmatch(row[1], -1)
			detail := []string{}
			if m := regexp.MustCompile("`\\{ ([^`]*) \\}`").FindStringSubmatch(row[2]); m != nil {
				for _, f := range splitTop(m[1], ',') {
					f, _, _ = strings.Cut(strings.TrimSpace(f), ":")
					detail = append(detail, strings.TrimSpace(f))
				}
			}
			for i, name := range names {
				prefix, _, ok := strings.Cut(name, ":")
				c := b.t.component(prefix)
				if !ok || c == "" {
					return nil, fmt.Errorf("README.md Events: %s has no component", name)
				}
				target := row[1]
				if len(targets) == len(names) {
					target = targets[i][1]
				} else if len(targets) == 1 {
					target = targets[0][1]
				}
				seen[name] = true
				notes := mdAnchor.ReplaceAllString(row[2], "]("+catalogRepo+"#")
				if notes == "—" || regexp.MustCompile("^`\\{ [^`]* \\}`$").MatchString(notes) {
					notes = ""
				}
				out[c] = append(out[c], catEvent{Name: name, Target: target, Detail: detail, Cancelable: strings.Contains(row[2], "cancelable"), Notes: notes})
			}
		}
	}
	if len(seen) == 0 {
		return nil, fmt.Errorf("README.md: no Events table")
	}
	var missing []string
	for name := range b.jsEvents {
		if !seen[name] {
			missing = append(missing, name)
		}
	}
	if len(missing) > 0 {
		sort.Strings(missing)
		return nil, fmt.Errorf("README.md Events table misses kit events: %s", strings.Join(missing, ", "))
	}
	return out, nil
}

func (b *catalogBuild) exports(sections []mdSection) []catExport {
	var out []catExport
	for _, s := range sections {
		if s.title != "Core exports" && s.title != "Component exports" {
			continue
		}
		for _, row := range mdTable(s.body) {
			if len(row) != 3 {
				continue
			}
			name := strings.Trim(row[0], "`")
			sig := strings.ReplaceAll(row[1], "`", "")
			e := catExport{Name: name, Module: "clanker-ui.js", Signature: sig, Notes: mdAnchor.ReplaceAllString(row[2], "]("+catalogRepo+"#")}
			if slices.Contains([]string{"chart", "sparkline", "statTile"}, name) {
				e.Module = "clanker-ui-chart.js"
				e.Component = "chart"
			} else {
				for _, c := range b.t.camel {
					if name == c || strings.HasPrefix(name, c) && len(name) > len(c) && name[len(c)] >= 'A' && name[len(c)] <= 'Z' {
						if n, ok := b.t.byCase[c]; ok {
							if _, comp := b.t.group[n]; comp {
								e.Component = n
								break
							}
						}
					}
				}
			}
			out = append(out, e)
		}
	}
	return out
}

func (b *catalogBuild) component(c string, navTitle map[string]string, events []catEvent, exports []catExport, examples map[string]string) (catComponent, error) {
	d := b.data[c]
	page := c
	if p, ok := catalogDocsPage[c]; ok {
		page = p
	}
	title := navTitle[page]
	if title == "" {
		title = strings.ToUpper(c[:1]) + strings.ReplaceAll(c[1:], "-", " ")
	}
	comp := catComponent{
		Name:           c,
		Title:          title,
		Group:          b.t.group[c],
		Needs:          []string{},
		Events:         events,
		Exports:        []string{},
		Keyboard:       []string{},
		KitAdds:        []string{},
		Parts:          []catPart{},
		PartAttributes: d.partAttr.idJSON(),
		Docs:           catalogSite + "/docs/components/" + page + "/",
		DocsMarkdown:   catalogSite + "/" + catalogCompDir + "/" + c + ".md",
		Readme:         catalogCompDir + "/" + c + ".md",
	}
	if comp.Events == nil {
		comp.Events = []catEvent{}
	}
	if comp.Group != "core" {
		comp.Needs = append(comp.Needs, "core")
	}
	comp.Needs = append(comp.Needs, b.t.needs[c]...)
	for _, e := range exports {
		if e.Component == c || worksFor(exports, e.Component, c) {
			comp.Exports = append(comp.Exports, e.Name)
		}
	}
	slots := map[string]bool{}
	for s := range b.cssSlots {
		if b.t.component(s) == c {
			slots[s] = true
		}
	}
	for _, set := range []map[string]bool{b.defined, b.made, b.markup, b.named} {
		for s := range set {
			if b.t.component(s) == c {
				slots[s] = true
			}
		}
	}
	for s := range d.parts {
		slots[s] = true
	}
	for s := range d.state {
		slots[s] = true
	}
	names := sortedKeys(slots)
	sort.SliceStable(names, func(i, j int) bool { return names[i] == c && names[j] != c })
	for _, s := range names {
		p := catPart{Slot: s, Root: s == c, JS: b.defined[s], Attributes: catAttrs{}, State: []string{}}
		if b.made[s] && !b.markup[s] || slices.Contains(catalogKitMade, s) {
			p.KitAdds = true
			comp.KitAdds = append(comp.KitAdds, s)
		}
		if a := d.parts[s]; a != nil && !p.KitAdds {
			p.Attributes = a.json()
		}
		for name := range d.state[s] {
			if pc := b.t.partComponent(strings.TrimPrefix(name, "data-")); pc != "" && pc != c && b.data[pc].partAttr[name] != nil {
				continue
			}
			if d.parts[s] == nil || d.parts[s][name] == nil {
				p.State = append(p.State, name)
			}
		}
		if p.KitAdds {
			for name := range d.parts[s] {
				if !slices.Contains(p.State, name) {
					p.State = append(p.State, name)
				}
			}
		}
		sort.Strings(p.State)
		comp.Parts = append(comp.Parts, p)
		if p.JS || p.KitAdds {
			comp.JS = true
		}
	}
	if len(comp.Events) > 0 || len(comp.Exports) > 0 {
		comp.JS = true
	}
	opts := attrSet{}
	for name, a := range d.options {
		if !b.authored(d, name) {
			opts[name] = a
		}
	}
	comp.Options = opts.json()
	seen := map[string]bool{}
	for _, s := range d.sections {
		for _, line := range b.sectionLines(s) {
			if !slices.Contains(b.lineComps(s, line), c) {
				continue
			}
			for _, sentence := range sentences(line) {
				if keyWord.MatchString(stripCode(sentence)) && !seen[sentence] && !migration.MatchString(sentence) {
					seen[sentence] = true
					comp.Keyboard = append(comp.Keyboard, sentence)
				}
			}
		}
	}
	var scripts []string
	for _, s := range d.sections {
		for _, m := range mdJSFence.FindAllStringSubmatch(s.body, -1) {
			scripts = append(scripts, dedent(m[1]))
		}
	}
	comp.Script = strings.Join(scripts, "\n\n")
	switch {
	case examples[c] != "":
		comp.Example = examples[c]
		comp.ExampleSource = catalogExDir + "/" + c + ".html"
	case d.fence != "":
		comp.Example = firstValues(fenceExample(d.fence, c, b.t))
		comp.ExampleSource = "README.md#" + d.sections[0].slug
	default:
		return comp, fmt.Errorf("%s: no example; add an html fence to its README section or %s/%s.html", c, catalogExDir, c)
	}
	return comp, nil
}

func worksFor(exports []catExport, owner, c string) bool {
	for _, e := range exports {
		if e.Component == owner && strings.HasPrefix(e.Notes, "Works for ") && strings.Contains(e.Notes, "`"+c+"`") {
			return true
		}
	}
	return false
}

func stripCode(s string) string {
	return mdCode.ReplaceAllString(s, "")
}

func sentences(body string) []string {
	var out []string
	for _, para := range strings.Split(body, "\n") {
		para = strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(para), "- "))
		if para == "" || strings.HasPrefix(para, "|") {
			continue
		}
		start, tick := 0, false
		for i := 0; i < len(para); i++ {
			switch {
			case para[i] == '`':
				tick = !tick
			case !tick && para[i] == '.' && (i+1 == len(para) || para[i+1] == ' ') && (i+2 >= len(para) || para[i+2] < 'a' || para[i+2] > 'z'):
				if s := strings.TrimSpace(para[start : i+1]); s != "" {
					out = append(out, s)
				}
				start = i + 1
			}
		}
		if s := strings.TrimSpace(para[start:]); s != "" {
			out = append(out, s)
		}
	}
	return out
}

func attrText(v any) string {
	switch x := v.(type) {
	case []string:
		var q []string
		for _, s := range x {
			if s == "" {
				q = append(q, "(empty)")
			} else {
				q = append(q, "`"+s+"`")
			}
		}
		return strings.Join(q, ", ")
	case string:
		return x
	}
	return fmt.Sprint(v)
}

func attrsText(a catAttrs) string {
	var out []string
	for _, k := range sortedKeys(a) {
		out = append(out, "`"+k+"` "+attrText(a[k]))
	}
	return strings.Join(out, "; ")
}

func codeList(s []string) string {
	if len(s) == 0 {
		return ""
	}
	return "`" + strings.Join(s, "`, `") + "`"
}

func cell(s string) string {
	return strings.ReplaceAll(s, "|", `\|`)
}

const catalogLegend = "**Parts** lists each `data-slot`. **Write** = attributes you may author. **State** = attributes the kit sets; style on them, never write them. **Kit adds** = parts the kit creates; do not write them. **Part attributes** go on an element of another component (for example a `button`) to give it this component's behavior."

func globalsMarkdown(cat *catalog) string {
	return "Global attributes (any element): " + attrsText(cat.Global) + "; `data-string-<key>` (localized label override).\n\n"
}

func catalogIndex(cat *catalog) string {
	var b strings.Builder
	b.WriteString("# clanker-ui components\n\n")
	fmt.Fprintf(&b, "Generated from `%s` (same directory) by `go run ./tools/gen catalog`. Version %s, shadcn `%s`, Base UI %s.\n\n", filepath.Base(catalogFile), cat.Version, cat.Shadcn[:7], cat.BaseUI)
	b.WriteString("Read the file of each component: `components/<name>.md`, for example [components/button.md](components/button.md).\n\n")
	b.WriteString("## Groups\n\n")
	b.WriteString("Each group has `clanker-ui-<group>.min.css` and (except core CSS-only parts) `clanker-ui-<group>.min.js`. Load `core` always, then the group of each component and the groups in its **Needs**.\n\n")
	b.WriteString("| Group | Components |\n| --- | --- |\n")
	for _, g := range cat.Groups {
		fmt.Fprintf(&b, "| `%s` | %s |\n", g.Name, strings.Join(g.Components, ", "))
	}
	b.WriteString("\n")
	b.WriteString(globalsMarkdown(cat))
	b.WriteString("## Component files\n\n")
	b.WriteString("Each component has one file, `components/<name>.md`: group, needs, parts, attributes, events, exports, and the full text from the README. " + catalogLegend + "\n")
	return b.String()
}

func catalogMarkdown(cat *catalog) string {
	var b strings.Builder
	b.WriteString(globalsMarkdown(cat))
	b.WriteString("### Components\n\nPer component: " + catalogLegend + "\n\n")
	for _, c := range cat.Components {
		componentMarkdown(&b, cat, c, "####")
	}
	return strings.TrimRight(b.String(), "\n") + "\n"
}

func componentFile(cat *catalog, c catComponent, full string) string {
	var b strings.Builder
	c.Keyboard, c.Script, c.Docs = nil, "", ""
	componentMarkdown(&b, cat, c, "#")
	b.WriteString("## Full text\n\n")
	b.WriteString(full)
	return strings.TrimRight(b.String(), "\n") + "\n"
}

func componentMarkdown(b *strings.Builder, cat *catalog, c catComponent, heading string) {
	fmt.Fprintf(b, "%s %s (`%s`)\n\n", heading, c.Title, c.Name)
	needs := "none"
	if len(c.Needs) > 0 {
		needs = "`" + strings.Join(c.Needs, "`, `") + "`"
	}
	js := "CSS only"
	if c.JS {
		js = "CSS and JS"
	}
	fmt.Fprintf(b, "Group `%s`. Needs %s. %s.", c.Group, needs, js)
	if c.Docs != "" {
		fmt.Fprintf(b, " Docs: %s.", c.Docs)
	}
	b.WriteString("\n\n")
	if c.SameAs != "" {
		fmt.Fprintf(b, "Same component as `%s`: use its markup, events, and API.\n\n", c.SameAs)
	}
	var rows, other, kit []string
	for _, p := range c.Parts {
		name := "`" + p.Slot + "`"
		if p.Root {
			name += " (root)"
		}
		switch {
		case len(p.Attributes) > 0 || len(p.State) > 0:
			if p.KitAdds {
				name += " (kit adds)"
			}
			rows = append(rows, fmt.Sprintf("| %s | %s | %s |\n", name, cell(attrsText(p.Attributes)), codeList(p.State)))
		case p.KitAdds:
			kit = append(kit, name)
		default:
			other = append(other, name)
		}
	}
	if len(rows) > 0 {
		b.WriteString("| Part | Write | State |\n| --- | --- | --- |\n" + strings.Join(rows, "") + "\n")
	}
	if len(other) > 0 {
		fmt.Fprintf(b, "Other parts: %s.\n\n", strings.Join(other, ", "))
	}
	if len(kit) > 0 {
		fmt.Fprintf(b, "Kit adds: %s.\n\n", strings.Join(kit, ", "))
	}
	if len(c.PartAttributes) > 0 {
		fmt.Fprintf(b, "Part attributes: %s.\n\n", attrsText(c.PartAttributes))
	}
	if len(c.Options) > 0 {
		fmt.Fprintf(b, "Other options named in the docs: %s.\n\n", attrsText(c.Options))
	}
	if len(c.Events) > 0 {
		var ev []string
		for _, e := range c.Events {
			s := "`" + e.Name + "`"
			if len(e.Detail) > 0 {
				s += " `{ " + strings.Join(e.Detail, ", ") + " }`"
			}
			if e.Cancelable {
				s += " (cancelable)"
			}
			ev = append(ev, s)
		}
		fmt.Fprintf(b, "Events: %s.\n\n", strings.Join(ev, "; "))
	}
	if len(c.Exports) > 0 {
		fmt.Fprintf(b, "Exports (readable set: `%s`; `.min` set: %s):\n\n", readableModule(c.Group), minModules(c.Group))
		for _, name := range c.Exports {
			for _, e := range cat.Exports {
				if e.Name == name {
					fmt.Fprintf(b, "- `%s`", e.Signature)
					if e.Notes != "" {
						fmt.Fprintf(b, ": %s", e.Notes)
					}
					b.WriteString("\n")
				}
			}
		}
		b.WriteString("\n")
	}
	if len(c.Keyboard) > 0 {
		b.WriteString("Keyboard and focus:\n\n")
		for _, k := range c.Keyboard {
			fmt.Fprintf(b, "- %s\n", k)
		}
		b.WriteString("\n")
	}
	if !strings.HasPrefix(c.ExampleSource, "README.md#") {
		fmt.Fprintf(b, "```html\n%s\n```\n\n", c.Example)
	}
	if c.Script != "" {
		fmt.Fprintf(b, "```js\n%s\n```\n\n", c.Script)
	}
}

var mdLocalLink = regexp.MustCompile(`\]\(#([^)\s]+)\)`)

func (b *catalogBuild) componentText(s mdSection, c string) string {
	var blocks []string
	fence := false
	for _, line := range strings.SplitAfter(s.body, "\n") {
		trim := strings.TrimSpace(line)
		if len(blocks) == 0 || !fence && trim != "" && line[0] != ' ' && line[0] != '\t' {
			blocks = append(blocks, "")
		}
		blocks[len(blocks)-1] += line
		if strings.HasPrefix(trim, "```") {
			fence = !fence
		}
	}
	var out strings.Builder
	for _, blk := range blocks {
		first, _, _ := strings.Cut(blk, "\n")
		switch {
		case strings.HasPrefix(first, "```html"):
			if len(s.comps) > 1 && !strings.Contains(blk, `data-slot="`+c) {
				continue
			}
		case strings.HasPrefix(first, "```"):
		case strings.HasPrefix(first, "- Changed with the move to Base UI"), !slices.Contains(b.lineComps(s, first), c):
			continue
		}
		out.WriteString(blk)
	}
	return out.String()
}

func (b *catalogBuild) fullText(c string, sections []mdSection) string {
	files := map[string]string{}
	for _, s := range sections {
		if len(s.comps) > 0 {
			files[s.slug] = s.comps[0]
		}
	}
	link := func(m string) string {
		slug := mdLocalLink.FindStringSubmatch(m)[1]
		if f, ok := files[slug]; ok {
			return "](" + f + ".md)"
		}
		return "](" + catalogRepo + "#" + slug + ")"
	}
	var out strings.Builder
	for i := 0; i < len(sections); i++ {
		if !slices.Contains(sections[i].comps, c) {
			continue
		}
		top := sections[i].level
		for j := i; j < len(sections) && (j == i || sections[j].level > top); j++ {
			s := sections[j]
			fmt.Fprintf(&out, "%s %s\n%s", strings.Repeat("#", 3+s.level-top), s.title, mdLocalLink.ReplaceAllStringFunc(b.componentText(s, c), link))
			i = j
		}
	}
	return out.String()
}

func eventsMarkdown(cat *catalog) string {
	var b strings.Builder
	b.WriteString("# clanker-ui events\n\n")
	fmt.Fprintf(&b, "Generated from `%s` (same directory) by `go run ./tools/gen catalog`.\n\n", filepath.Base(catalogFile))
	b.WriteString("All events are bubbling, composed `CustomEvent`s named `<component>:<action>`. Listen on the root or on `document`, and read `event.detail`. A cancelable event stops the default action when a listener calls `event.preventDefault()`. Components that wrap a native control (slider, native select, input, the hidden input of checkbox, switch, and radio) also fire the native `input` and `change` events.\n\n")
	b.WriteString("```js\ndocument.addEventListener(\"select:change\", event => console.log(event.target, event.detail.value))\n```\n\n")
	b.WriteString("| Event | Component | Target | `detail` | Notes |\n| --- | --- | --- | --- | --- |\n")
	for _, c := range cat.Components {
		for _, e := range c.Events {
			d := "none"
			if len(e.Detail) > 0 {
				d = "`" + strings.Join(e.Detail, "`, `") + "`"
			}
			fmt.Fprintf(&b, "| `%s` | `%s` | `%s` | %s | %s |\n", e.Name, c.Name, e.Target, d, cell(e.Notes))
		}
	}
	return b.String()
}

func llmsFull(cat *catalog, sections []mdSection) string {
	var b strings.Builder
	fmt.Fprintf(&b, "# clanker-ui\n\n> %s\n\n", cat.Description)
	fmt.Fprintf(&b, "Version %s. Docs: %s. Source: %s. Catalog: %s/%s. Agent skill: %s/tree/main/skills/clanker-ui.\n\n", cat.Version, cat.Docs, cat.Repository, catalogRaw, catalogFile, cat.Repository)
	skip := false
	skipLevel := 0
	for _, s := range sections {
		if s.level == 1 {
			continue
		}
		if skip && s.level > skipLevel {
			continue
		}
		skip = slices.Contains(catalogDevSections, s.title)
		skipLevel = s.level
		if skip {
			continue
		}
		fmt.Fprintf(&b, "%s %s\n%s", strings.Repeat("#", s.level), s.title, s.body)
	}
	b.WriteString("\n## Component reference\n\n")
	short := *cat
	short.Components = nil
	for _, c := range cat.Components {
		c.Keyboard, c.Exports, c.Script = nil, nil, ""
		short.Components = append(short.Components, c)
	}
	b.WriteString(catalogMarkdown(&short))
	return b.String()
}

func readableModule(group string) string {
	if group == "chart" {
		return "clanker-ui-chart.js"
	}
	return "clanker-ui.js"
}

func minModules(group string) string {
	switch group {
	case "core":
		return "`" + distCore + "`"
	case "chart":
		return "`clanker-ui-chart.min.js`"
	}
	return "`" + distAll + "` or `clanker-ui-" + group + ".min.js`"
}
