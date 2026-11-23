package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strconv"
	"strings"
	"sync"
	"testing"
)

var (
	catOnce     sync.Once
	catFilesOut map[string][]byte
	catOut      *catalog
	catErr      error
)

func testCatalog(t *testing.T) *catalog {
	t.Helper()
	catOnce.Do(func() { catFilesOut, catOut, catErr = buildCatalog("../..") })
	if catErr != nil {
		t.Fatal(catErr)
	}
	return catOut
}

func TestCatalogFresh(t *testing.T) {
	testCatalog(t)
	for name, want := range catFilesOut {
		got, err := os.ReadFile(filepath.Join("../..", name))
		if err != nil || !bytes.Equal(got, want) {
			t.Errorf("%s is not fresh: run go run ./tools/gen catalog", name)
		}
	}
	for _, name := range extraCompFiles("../..", catFilesOut) {
		t.Errorf("%s is not a catalog component: run go run ./tools/gen catalog", name)
	}
	again, _, err := buildCatalog("../..")
	if err != nil {
		t.Fatal(err)
	}
	for name := range catFilesOut {
		if !bytes.Equal(again[name], catFilesOut[name]) {
			t.Errorf("%s: two runs give different bytes", name)
		}
	}
}

func TestCatalogComponents(t *testing.T) {
	cat := testCatalog(t)
	g, err := readGroups("groups.tsv")
	if err != nil {
		t.Fatal(err)
	}
	var names []string
	for _, c := range cat.Components {
		names = append(names, c.Name)
		_, full, ok := strings.Cut(string(catFilesOut[c.Readme]), "\n## Full text\n\n#")
		if !ok {
			t.Errorf("%s: %s has no README full text", c.Name, c.Readme)
		}
		if strings.HasPrefix(c.ExampleSource, "README.md#") && !strings.Contains(full, "```html\n") {
			t.Errorf("%s: %s has no example", c.Name, c.Readme)
		}
		if c.Example == "" {
			t.Errorf("%s has no example", c.Name)
		}
		if !slices.ContainsFunc(c.Parts, func(p catPart) bool { return p.Root }) && !slices.Contains([]string{"direction", "chart", "theme", "sonner", "resizable"}, c.Name) {
			t.Errorf("%s has no root part", c.Name)
		}
	}
	if !slices.Equal(names, g.order) {
		t.Errorf("catalog components %v, want groups.tsv order %v", names, g.order)
	}
	js := readFile(t, "../../kit/clanker-ui.js") + readFile(t, "../../kit/clanker-ui-chart.js") + readFile(t, "../../kit/clanker-ui-code.js")
	var events []string
	for _, c := range cat.Components {
		for _, e := range c.Events {
			events = append(events, e.Name)
			comp, action, _ := strings.Cut(e.Name, ":")
			if !strings.Contains(js, `"`+e.Name+`"`) && !strings.Contains(js, ":"+action) {
				t.Errorf("%s: event %s is not in the kit JS", c.Name, e.Name)
			}
			if g.component(comp) != c.Name {
				t.Errorf("event %s is listed under %s", e.Name, c.Name)
			}
		}
	}
	for _, m := range regexp.MustCompile(`emit\([^,()]*, *"([a-z-]+:[a-z-]+)"`).FindAllStringSubmatch(js, -1) {
		if !slices.Contains(events, m[1]) {
			t.Errorf("kit event %s is not in the catalog", m[1])
		}
	}
}

func TestCatalogExamples(t *testing.T) {
	cat := testCatalog(t)
	g, err := readGroups("groups.tsv")
	if err != nil {
		t.Fatal(err)
	}
	for _, c := range cat.Components {
		for _, e := range exampleErrors(cat, g, c) {
			t.Errorf("%s example: %s", c.Name, e)
		}
	}
	for _, bad := range []struct{ from, to string }{
		{`data-slot="select-item"`, `data-slot="select-itemz"`},
		{`data-size="sm"`, `data-size="huge"`},
		{`data-value="apple" data-label`, `data-valu="apple" data-label`},
		{`data-slot="select-trigger"`, `data-slot="select-trigger" onclick="x()"`},
	} {
		for _, c := range cat.Components {
			if c.Name != "select" {
				continue
			}
			if !strings.Contains(c.Example, bad.from) {
				t.Fatalf("select example has no %s", bad.from)
			}
			c.Example = strings.Replace(c.Example, bad.from, bad.to, 1)
			if len(exampleErrors(cat, g, c)) == 0 {
				t.Errorf("the example check accepts %s", bad.to)
			}
		}
	}
}

func exampleErrors(cat *catalog, g *groupTable, c catComponent) []string {
	var errs []string
	fail := func(f string, a ...any) { errs = append(errs, fmt.Sprintf(f, a...)) }
	byName := map[string]catComponent{}
	for _, o := range cat.Components {
		byName[o.Name] = o
	}
	partAttrs := catAttrs{}
	for _, o := range cat.Components {
		for k, v := range o.PartAttributes {
			partAttrs[k] = v
		}
	}
	if strings.Contains(c.Example, "<!--") || regexp.MustCompile(`(?i)<(script|style)\b`).MatchString(c.Example) {
		fail("has a comment, script, or style element")
	}
	walkNodes(parseFragment(c.Example), func(n *htmlNode) {
		slot, _ := n.attr("data-slot")
		var part *catPart
		owner := catComponent{}
		if slot != "" {
			o, ok := byName[g.component(slot)]
			if !ok {
				fail("unknown slot %q", slot)
				return
			}
			owner = o
			for i := range o.Parts {
				if o.Parts[i].Slot == slot {
					part = &o.Parts[i]
				}
			}
			if part == nil {
				fail("%q is not a part of %s", slot, o.Name)
				return
			}
		}
		for _, a := range n.attrs {
			name, value := a[0], a[1]
			if name == "style" || name == "srcdoc" || strings.HasPrefix(name, "on") {
				fail("<%s %s> is not allowed under the CSP", n.tag, name)
			}
			if !strings.HasPrefix(name, "data-") || name == "data-slot" || strings.HasPrefix(name, "data-string-") {
				continue
			}
			var spec any
			ok := false
			if part != nil {
				spec, ok = part.Attributes[name]
			}
			if !ok {
				spec, ok = cat.Global[name]
			}
			if !ok && part != nil {
				spec, ok = owner.Options[name]
			}
			if !ok {
				spec, ok = c.Options[name]
			}
			if !ok {
				spec, ok = partAttrs[name]
			}
			if !ok {
				fail("<%s data-slot=%q> has unknown attribute %s", n.tag, slot, name)
				continue
			}
			if vals, isList := spec.([]string); isList && !slices.Contains(vals, value) {
				fail("%s=%q, want one of %v", name, value, vals)
			}
		}
	})
	return errs
}

func TestCatalogSchema(t *testing.T) {
	testCatalog(t)
	var schema, doc any
	if err := json.Unmarshal([]byte(readFile(t, "../../"+catalogSchema)), &schema); err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(catFilesOut[catalogFile], &doc); err != nil {
		t.Fatal(err)
	}
	root := schema.(map[string]any)
	for _, e := range validate(root, root, doc, "$") {
		t.Error(e)
	}
	broken := map[string]any{}
	for k, v := range doc.(map[string]any) {
		broken[k] = v
	}
	broken["extra"] = true
	delete(broken, "csp")
	if len(validate(root, root, broken, "$")) != 2 {
		t.Error("the schema check does not find an extra and a missing field")
	}
}

func validate(root, s map[string]any, v any, path string) []string {
	if ref, ok := s["$ref"].(string); ok {
		def := root["$defs"].(map[string]any)[strings.TrimPrefix(ref, "#/$defs/")].(map[string]any)
		return validate(root, def, v, path)
	}
	var errs []string
	fail := func(f string, a ...any) { errs = append(errs, path+": "+fmt.Sprintf(f, a...)) }
	if c, ok := s["const"]; ok && c != v {
		fail("want %v", c)
	}
	if e, ok := s["enum"].([]any); ok && !slices.Contains(e, v) {
		fail("%v is not in %v", v, e)
	}
	if one, ok := s["oneOf"].([]any); ok {
		n := 0
		for _, o := range one {
			if len(validate(root, o.(map[string]any), v, path)) == 0 {
				n++
			}
		}
		if n != 1 {
			fail("matches %d of oneOf", n)
		}
	}
	if p, ok := s["pattern"].(string); ok {
		if str, _ := v.(string); !regexp.MustCompile(p).MatchString(str) {
			fail("%q does not match %s", str, p)
		}
	}
	switch s["type"] {
	case "object":
		obj, ok := v.(map[string]any)
		if !ok {
			fail("want object")
			return errs
		}
		props, _ := s["properties"].(map[string]any)
		for _, r := range anyList(s["required"]) {
			if _, ok := obj[r.(string)]; !ok {
				fail("missing %s", r)
			}
		}
		for k, val := range obj {
			if ps, ok := props[k].(map[string]any); ok {
				errs = append(errs, validate(root, ps, val, path+"."+k)...)
			} else if ap, ok := s["additionalProperties"].(map[string]any); ok {
				errs = append(errs, validate(root, ap, val, path+"."+k)...)
			} else if s["additionalProperties"] == false {
				fail("unknown field %s", k)
			}
		}
	case "array":
		arr, ok := v.([]any)
		if !ok {
			fail("want array")
			return errs
		}
		if it, ok := s["items"].(map[string]any); ok {
			for i, x := range arr {
				errs = append(errs, validate(root, it, x, fmt.Sprintf("%s[%d]", path, i))...)
			}
		}
	case "string":
		if _, ok := v.(string); !ok {
			fail("want string")
		}
	case "boolean":
		if _, ok := v.(bool); !ok {
			fail("want boolean")
		}
	}
	return errs
}

func anyList(v any) []any {
	l, _ := v.([]any)
	return l
}

func readFile(t *testing.T, name string) string {
	t.Helper()
	b, err := os.ReadFile(name)
	if err != nil {
		t.Fatal(err)
	}
	return string(b)
}

func TestCatalogReferences(t *testing.T) {
	cat := testCatalog(t)
	csp := readFile(t, "../../skills/clanker-ui/references/csp.md")
	for _, want := range []string{cat.CSP, cat.CSPMeta} {
		if !strings.Contains(csp, want) {
			t.Errorf("references/csp.md does not contain the catalog policy %q", want)
		}
	}
	full := string(catFilesOut[catalogLLMs])
	readme := readFile(t, "../../README.md")
	for _, c := range cat.Components {
		if !strings.Contains(full, "### "+c.Title+" (`"+c.Name+"`)") {
			t.Errorf("llms-full.txt has no heading for %s", c.Name)
		}
		if block := "```html\n" + c.Example + "\n```"; strings.HasPrefix(c.ExampleSource, "README.md#") && strings.Count(full, block) > strings.Count(readme, block) {
			t.Errorf("llms-full.txt repeats the README example of %s", c.Name)
		}
	}
	if strings.Contains(full, "Keyboard and focus:") {
		t.Error("llms-full.txt repeats the README keyboard lines")
	}
	for _, dev := range catalogDevSections {
		if strings.Contains(full, "\n## "+dev+"\n") {
			t.Errorf("llms-full.txt has the contributor section %q", dev)
		}
	}
}

var (
	skillName = regexp.MustCompile(`^[a-z0-9]+(-[a-z0-9]+)*$`)
	mdLink    = regexp.MustCompile(`\]\(([^)\s]+)\)`)
)

func TestSkillFormat(t *testing.T) {
	dir := "../../skills/clanker-ui"
	src := readFile(t, dir+"/SKILL.md")
	front, body, ok := strings.Cut(strings.TrimPrefix(src, "---\n"), "\n---\n")
	if !strings.HasPrefix(src, "---\n") || !ok {
		t.Fatal("SKILL.md must start with YAML frontmatter between --- lines")
	}
	fields := map[string]string{}
	for _, line := range strings.Split(front, "\n") {
		if k, v, ok := strings.Cut(line, ":"); ok && !strings.HasPrefix(line, " ") {
			fields[k] = strings.TrimSpace(v)
		}
	}
	for k := range fields {
		if !slices.Contains([]string{"name", "description", "license", "compatibility", "metadata"}, k) {
			t.Errorf("frontmatter field %q is not portable", k)
		}
	}
	name := fields["name"]
	if len(name) == 0 || len(name) > 64 || !skillName.MatchString(name) || name != filepath.Base(dir) {
		t.Errorf("name %q: 1-64 chars of a-z, 0-9, single -, equal to the directory name", name)
	}
	if d := fields["description"]; len(d) == 0 || len(d) > 1024 || strings.HasPrefix(d, ">") || strings.HasPrefix(d, "|") {
		t.Errorf("description: 1-1024 characters on one line, got %d", len(d))
	}
	if n := strings.Count(body, "\n"); n >= 500 {
		t.Errorf("SKILL.md body has %d lines, want under 500", n)
	}
	err := filepath.WalkDir(dir, func(name string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		f, _ := filepath.Rel(dir, name)
		src := readFile(t, name)
		if n := strings.Count(src, "\n"); f != "SKILL.md" && n > 500 {
			t.Errorf("%s has %d lines, want at most 500", f, n)
		}
		if !strings.HasSuffix(f, ".md") {
			return nil
		}
		for _, m := range mdLink.FindAllStringSubmatch(src, -1) {
			link := m[1]
			if strings.HasPrefix(link, "http") || strings.HasPrefix(link, "#") {
				continue
			}
			if strings.Contains(link, "..") {
				t.Errorf("%s: link %s leaves the skill directory", f, link)
			}
			if _, err := os.Stat(filepath.Join(dir, filepath.Dir(f), link)); err != nil {
				t.Errorf("%s: link %s does not resolve", f, link)
			}
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, word := range []string{"Claude", "Codex", "Cursor", "Gemini", "allowed-tools", "model:"} {
		if strings.Contains(src, word) {
			t.Errorf("SKILL.md names %q; keep the skill provider-neutral", word)
		}
	}
}

func TestLLMsTxt(t *testing.T) {
	cat := testCatalog(t)
	src := readFile(t, "../../docs/llms.txt")
	lines := strings.Split(src, "\n")
	if lines[0] != "# clanker-ui" || !strings.HasPrefix(lines[2], "> ") {
		t.Fatal("llms.txt: want \"# clanker-ui\", a blank line, then a \"> \" summary")
	}
	var nav struct {
		Groups []struct {
			Items []struct{ Href string } `json:"items"`
		} `json:"groups"`
	}
	if err := json.Unmarshal([]byte(readFile(t, "../../docs/nav.json")), &nav); err != nil {
		t.Fatal(err)
	}
	pages := map[string]bool{"/docs": true, "/docs/components": true}
	for _, g := range nav.Groups {
		for _, it := range g.Items {
			pages[it.Href] = true
		}
	}
	for _, c := range cat.Components {
		page := strings.TrimSuffix(strings.TrimPrefix(c.Docs, strings.TrimSuffix(cat.Docs, "/")), "/")
		if !pages[page] {
			t.Errorf("%s: docs link %s is not a page in docs/nav.json", c.Name, c.Docs)
		}
		if c.DocsMarkdown != catalogSite+"/"+c.Readme {
			t.Errorf("%s: docsMarkdown %s is not the Pages copy of %s", c.Name, c.DocsMarkdown, c.Readme)
		}
	}
	links := regexp.MustCompile(`(?m)^- \[[^\]]+\]\(([^)]+)\)`).FindAllStringSubmatch(src, -1)
	if len(links) < 5 {
		t.Fatalf("llms.txt has %d links", len(links))
	}
	for _, m := range links {
		u := m[1]
		switch {
		case strings.HasPrefix(u, catalogRaw+"/"):
			if _, err := os.Stat(filepath.Join("../..", strings.TrimPrefix(u, catalogRaw+"/"))); err != nil {
				t.Errorf("llms.txt: %s is not a repo file", u)
			}
		case strings.HasPrefix(u, catalogRepo+"/tree/main/"), strings.HasPrefix(u, catalogRepo+"/blob/main/"):
			p := strings.TrimPrefix(strings.TrimPrefix(u, catalogRepo+"/tree/main/"), catalogRepo+"/blob/main/")
			if _, err := os.Stat(filepath.Join("../..", p)); err != nil {
				t.Errorf("llms.txt: %s is not in the repo", u)
			}
		case u == catalogRepo+"/releases", u == catalogRepo:
		case strings.HasPrefix(u, cat.Docs):
			p := "/" + strings.TrimPrefix(u, cat.Docs)
			page := strings.TrimSuffix(strings.TrimSuffix(p, ".md"), "/")
			switch {
			case p == "/llms-full.txt":
			case p == "/demo/":
			case strings.HasPrefix(p, "/skills/clanker-ui/"):
				if _, err := os.Stat(filepath.Join("../..", p)); err != nil {
					t.Errorf("llms.txt: %s is not a skill file", u)
				}
			case !pages[page]:
				t.Errorf("llms.txt: %s is not a docs page", u)
			default:
				dir := strings.TrimPrefix(strings.TrimPrefix(page, "/docs"), "/")
				if dir == "" {
					dir = "index"
				}
				if _, err := os.Stat(filepath.Join("../../docs/content", dir, "page.md")); err != nil {
					t.Errorf("llms.txt: %s is a pending page with no page.md", u)
				}
			}
		default:
			t.Errorf("llms.txt: unexpected link %s", u)
		}
	}
}

func TestCatalogExports(t *testing.T) {
	cat := testCatalog(t)
	src := map[string]string{"clanker-ui.js": readFile(t, "../../kit/clanker-ui.js"), "clanker-ui-chart.js": readFile(t, "../../kit/clanker-ui-chart.js"), "clanker-ui-code.js": readFile(t, "../../kit/clanker-ui-code.js")}
	declared := regexp.MustCompile(`(?m)^export\s+(?:async\s+)?(?:function\s*\*?\s*|const\s+|let\s+|class\s+)([A-Za-z_$][\w$]*)`)
	public := map[string]map[string]bool{}
	for f, s := range src {
		public[f] = map[string]bool{}
		for _, m := range declared.FindAllStringSubmatch(s, -1) {
			if !strings.HasPrefix(m[1], "_") {
				public[f][m[1]] = true
			}
		}
	}
	listed := map[string]bool{}
	for _, e := range cat.Exports {
		listed[e.Module+" "+e.Name] = true
		if !public[e.Module][e.Name] {
			t.Errorf("catalog export %s is not exported by %s", e.Name, e.Module)
		}
	}
	for f, names := range public {
		for n := range names {
			if !listed[f+" "+n] && f == "clanker-ui.js" {
				t.Errorf("%s exports %s, but the README export tables do not list it", f, n)
			}
		}
	}
}

func kitKeyboardComponents(t *testing.T, g *groupTable) map[string]bool {
	js := readFile(t, "../../kit/clanker-ui.js")
	lines := strings.Split(js, "\n")
	arrays := map[string][]string{}
	for _, m := range regexp.MustCompile(`(?m)^const (\w+) = \[([^\]]*)\]`).FindAllStringSubmatch(js, -1) {
		for _, v := range regexp.MustCompile(`"([a-z0-9-]+)"`).FindAllStringSubmatch(m[2], -1) {
			arrays[m[1]] = append(arrays[m[1]], v[1])
		}
	}
	loop := regexp.MustCompile(`^for \(const (\w+) of (\w+)\) \{$`)
	open := regexp.MustCompile(`^(\s*)define\(("[a-z0-9-]+"|\w+), \{$`)
	out := map[string]bool{}
	for _, slot := range arrays["dialogKinds"] {
		out[g.component(slot)] = true
	}
	loopVar, loopArr := "", ""
	for i, line := range lines {
		if m := loop.FindStringSubmatch(line); m != nil {
			loopVar, loopArr = m[1], m[2]
		}
		m := open.FindStringSubmatch(line)
		if m == nil {
			continue
		}
		var slots []string
		switch {
		case strings.HasPrefix(m[2], `"`):
			slots = []string{strings.Trim(m[2], `"`)}
		case m[2] == loopVar:
			slots = arrays[loopArr]
		}
		for _, l := range lines[i+1:] {
			if l == m[1]+"})" {
				break
			}
			if regexp.MustCompile(`^\s+keydown[(:]`).MatchString(l) {
				for _, s := range slots {
					out[g.component(s)] = true
				}
				break
			}
		}
	}
	return out
}

func TestCatalogKeyboard(t *testing.T) {
	cat := testCatalog(t)
	g, err := readGroups("groups.tsv")
	if err != nil {
		t.Fatal(err)
	}
	keys := kitKeyboardComponents(t, g)
	for _, want := range []string{"checkbox", "switch", "radio-group", "dialog", "sheet", "select", "tabs"} {
		if !keys[want] {
			t.Errorf("the kit keyboard scan misses %s", want)
		}
	}
	label := regexp.MustCompile(`^([A-Z][A-Za-z]*(?: [A-Za-z]+)*):`)
	for _, c := range cat.Components {
		if keys[c.Name] && c.SameAs == "" && len(c.Keyboard) == 0 {
			t.Errorf("%s: the kit handles keys, but the catalog has no keyboard line", c.Name)
		}
		for _, k := range c.Keyboard {
			lead := ""
			if m := label.FindStringSubmatch(k); m != nil {
				lead = strings.ToLower(m[1])
			}
			for _, o := range cat.Components {
				title := strings.ToLower(o.Title)
				if o.Name == c.Name || strings.HasPrefix(strings.ToLower(c.Title), title) {
					continue
				}
				if strings.HasPrefix(strings.ToLower(k), title+" ") || strings.HasPrefix(strings.ToLower(k), title+":") || lead != "" && strings.HasPrefix(title, lead) && !strings.HasPrefix(strings.ToLower(c.Title), lead) {
					t.Errorf("%s keyboard line is about %s: %s", c.Name, o.Name, k)
				}
			}
		}
	}
}

func TestCatalogKitAdds(t *testing.T) {
	cat := testCatalog(t)
	g, err := readGroups("groups.tsv")
	if err != nil {
		t.Fatal(err)
	}
	adds := map[string]bool{}
	for _, c := range cat.Components {
		for _, p := range c.Parts {
			for _, st := range p.State {
				if pc := g.partComponent(strings.TrimPrefix(st, "data-")); pc != "" && pc != c.Name && !strings.HasPrefix(c.Name, pc+"-") {
					t.Errorf("%s: part %s has the state %s of %s", c.Name, p.Slot, st, pc)
				}
			}
			if p.KitAdds != slices.Contains(c.KitAdds, p.Slot) {
				t.Errorf("%s: part %s and kitAdds disagree", c.Name, p.Slot)
			}
			if p.KitAdds {
				adds[p.Slot] = true
				if len(p.Attributes) > 0 {
					t.Errorf("%s: kit-added part %s has Write attributes %v", c.Name, p.Slot, p.Attributes)
				}
			}
		}
	}
	for _, s := range []string{"switch-thumb", "slider-thumb", "checkbox-indicator", "radio-group-indicator", "dropdown-menu-checkbox-item-indicator", "dropdown-menu-radio-item-indicator"} {
		if !adds[s] {
			t.Errorf("%s is not in kitAdds", s)
		}
	}
}

func TestCatalogReadOnlyAttrsAreWrite(t *testing.T) {
	cat := testCatalog(t)
	var js strings.Builder
	for _, f := range []string{"clanker-ui.js", "clanker-ui-chart.js", "clanker-ui-code.js"} {
		b, err := os.ReadFile(filepath.Join("../..", kitDir, f))
		if err != nil {
			t.Fatal(err)
		}
		js.Write(b)
	}
	src := js.String()
	found := false
	for _, c := range cat.Components {
		for _, p := range c.Parts {
			for _, st := range p.State {
				read := strings.Contains(src, `hasAttribute("`+st+`")`) || strings.Contains(src, `getAttribute("`+st+`")`)
				wrote := jsWroteAttr.MatchString(src) && slices.ContainsFunc(jsWroteAttr.FindAllStringSubmatch(src, -1), func(m []string) bool {
					return m[1] == st || m[2] == st || m[3] != "" && attrName(m[3]) == st
				})
				if read && !wrote {
					t.Errorf("%s: part %s lists %s as State, but the kit only reads it", c.Name, p.Slot, st)
				}
			}
			if p.Slot == "table-container" {
				_, found = p.Attributes["data-sticky-header"]
			}
		}
	}
	if !found {
		t.Error("table-container: data-sticky-header is not a Write attribute")
	}
}

func TestCatalogRegions(t *testing.T) {
	testCatalog(t)
	for name, mark := range map[string]string{"README.md": "<!-- catalog:groups -->", "docs/content/index/page.md": `{{catalog "groups"}}`, "docs/content/components/dropdown-menu/page.md": `{{catalog "events"}}`, "docs/content/components/calendar/page.md": `{{catalog "exports"}}`} {
		if !strings.Contains(string(catFilesOut[name]), mark+"\n") {
			t.Errorf("%s has no %s region", name, mark)
		}
	}
	gen := func(kind string) (string, error) { return "| " + kind + " |\n", nil }
	src := "a\n\n<!-- catalog:groups -->\n\n| hand edit |\n\n<!-- /catalog:groups -->\n\nb\n{{catalog \"events\"}}\n{{/catalog}}\n"
	out, err := fillRegions("x", src, gen)
	if want := "a\n\n<!-- catalog:groups -->\n\n| groups |\n\n<!-- /catalog:groups -->\n\nb\n{{catalog \"events\"}}\n\n| events |\n\n{{/catalog}}\n"; err != nil || out != want {
		t.Errorf("fillRegions:\n%q, %v\nwant\n%q", out, err, want)
	}
	if got, want := catalogMark.ReplaceAllString(out, ""), "a\n\n| groups |\n\nb\n| events |\n\n"; got != want {
		t.Errorf("marks not removed: %q, want %q", got, want)
	}
	for _, bad := range []string{"<!-- catalog:groups -->\n", "{{/catalog}}\n", "{{catalog \"events\"}}\n<!-- /catalog:events -->\n", "<!-- catalog:groups -->\n<!-- catalog:groups -->\n<!-- /catalog:groups -->\n"} {
		if _, err := fillRegions("x", bad, gen); err == nil {
			t.Errorf("fillRegions(%q) gives no error", bad)
		}
	}
}

func TestCatalogValuelessAttrsAreBoolean(t *testing.T) {
	cat := testCatalog(t)
	var js strings.Builder
	for _, f := range []string{"clanker-ui.js", "clanker-ui-chart.js", "clanker-ui-code.js"} {
		js.WriteString(readFile(t, filepath.Join("../..", kitDir, f)))
	}
	flags := map[string]bool{}
	for _, m := range jsFlagAttr.FindAllStringSubmatch(js.String(), -1) {
		flags[m[1]] = true
	}
	check := func(where string, attrs catAttrs) {
		for name, v := range attrs {
			if flags[name] && v == "any" {
				t.Errorf("%s: %s is a flag that the kit reads with flag(), but the catalog type is any, not boolean", where, name)
			}
		}
	}
	got := map[string]any{}
	for _, c := range cat.Components {
		check(c.Name+" options", c.Options)
		check(c.Name+" part attributes", c.PartAttributes)
		for _, p := range c.Parts {
			check(p.Slot, p.Attributes)
			for name, v := range p.Attributes {
				got[p.Slot+" "+name] = v
			}
		}
		for name, v := range c.Options {
			got[c.Name+" option "+name] = v
		}
	}
	for key, want := range map[string]any{"dropdown-menu-item data-inset": "boolean", "menubar-label data-inset": "boolean", "dropdown-menu-item data-disabled": "boolean", "table option data-label": "any"} {
		if fmt.Sprint(got[key]) != fmt.Sprint(want) {
			t.Errorf("%s: type %v, want %v", key, got[key], want)
		}
	}
}

func TestCatalogAuthoredAttrsAreNotState(t *testing.T) {
	cat := testCatalog(t)
	parts := map[string]*catPart{}
	byDocs := map[string]catComponent{}
	partAttrs := catAttrs{}
	for _, c := range cat.Components {
		byDocs[c.Docs] = c
		for k, v := range c.PartAttributes {
			partAttrs[k] = v
		}
		for i := range c.Parts {
			parts[c.Parts[i].Slot] = &c.Parts[i]
		}
	}
	write := func(c catComponent, p *catPart, name string) bool {
		if p != nil {
			if _, ok := p.Attributes[name]; ok {
				return true
			}
		}
		_, opt := c.Options[name]
		_, glob := cat.Global[name]
		_, pa := partAttrs[name]
		return opt || glob || pa
	}
	seen := map[string]bool{}
	fail := func(src, slot, name, f string) {
		if !seen[slot+" "+name] {
			seen[slot+" "+name] = true
			t.Errorf(f, strings.TrimPrefix(src, "../../"), name, slot)
		}
	}
	files, err := filepath.Glob("../../docs/content/*/*/examples/*.html")
	if err != nil {
		t.Fatal(err)
	}
	more, _ := filepath.Glob("examples/*.html")
	for _, f := range append(append(files, more...), "../../demo/index.html") {
		walkNodes(parseFragment(readFile(t, f)), func(n *htmlNode) {
			slot, _ := n.attr("data-slot")
			p := parts[slot]
			if p == nil || p.KitAdds {
				return
			}
			for _, a := range n.attrs {
				if slices.Contains(p.State, a[0]) {
					fail(f, slot, a[0], "%s: authors write %s on %s, but the catalog lists it as State")
				}
			}
		})
	}
	pages, err := filepath.Glob("../../docs/content/components/*/page.md")
	if err != nil {
		t.Fatal(err)
	}
	for _, f := range pages {
		c, ok := byDocs[catalogSite+"/docs/components/"+filepath.Base(filepath.Dir(f))+"/"]
		if !ok {
			continue
		}
		slot, table := c.Name, false
		for _, line := range strings.Split(readFile(t, f), "\n") {
			switch {
			case strings.HasPrefix(line, "### "):
				slot = strings.ReplaceAll(strings.ToLower(strings.TrimPrefix(line, "### ")), " ", "-")
			case strings.HasPrefix(line, "| Attribute |"):
				table = true
				continue
			case !strings.HasPrefix(line, "|"):
				table = false
			}
			p := parts[slot]
			if !table || strings.HasPrefix(line, "| ---") || p != nil && p.KitAdds {
				continue
			}
			for _, m := range mdCode.FindAllStringSubmatch(mdTable("|\n" + line)[0][0], -1) {
				if am := attrCode.FindStringSubmatch(m[1]); am != nil && (!write(c, p, am[1]) || p != nil && slices.Contains(p.State, am[1])) {
					fail(f, slot, am[1], "%s: the attribute table lists %s for %s, but the catalog has it as State or not at all")
				}
			}
		}
	}
}

var (
	repoFileURL = regexp.MustCompile("https://(?:cdn\\.jsdelivr\\.net/gh/bl4ko/clanker-ui@|raw\\.githubusercontent\\.com/bl4ko/clanker-ui/)[^/\\s]+/([^\\s`)\"'<>#?]+)")
	iconCount   = regexp.MustCompile(`(\d+) (?:\[Lucide\]\([^)]*\)|Lucide)(?: [0-9.]+)? icons`)
)

func TestDocsRepoFileURLs(t *testing.T) {
	var ignored []string
	for _, l := range strings.Split(readFile(t, "../../.gitignore"), "\n") {
		if strings.HasPrefix(l, "/") {
			ignored = append(ignored, strings.TrimPrefix(l, "/"))
		}
	}
	skip := func(p string) bool {
		return slices.ContainsFunc(ignored, func(g string) bool {
			return p == strings.TrimSuffix(g, "/") || strings.HasSuffix(g, "/") && strings.HasPrefix(p, g)
		})
	}
	found := 0
	err := filepath.WalkDir("../..", func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel("../..", path)
		rel = filepath.ToSlash(rel)
		if d.IsDir() {
			if rel == ".git" || rel != "." && skip(rel) {
				return filepath.SkipDir
			}
			return nil
		}
		if skip(rel) || !slices.Contains([]string{".md", ".txt", ".json", ".html"}, filepath.Ext(rel)) {
			return nil
		}
		b, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		for _, m := range repoFileURL.FindAllStringSubmatch(string(b), -1) {
			found++
			p := strings.TrimRight(m[1], ".,;:")
			if _, err := os.Stat(filepath.Join("../..", p)); err != nil || skip(p) {
				t.Errorf("%s: %s is not a file in git at that ref", rel, m[0])
			}
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if found < 3 {
		t.Fatalf("found %d repository file URLs", found)
	}
}

func TestDocsIconCount(t *testing.T) {
	js := readFile(t, "../../kit/clanker-ui.js")
	start := strings.Index(js, "const ICONS = {\n")
	end := strings.Index(js[max(start, 0):], "\n}\n")
	if start < 0 || end < 0 {
		t.Fatal("clanker-ui.js: no ICONS table")
	}
	want := strconv.Itoa(len(iconEntry.FindAllString(js[start:start+end], -1)))
	for _, name := range []string{"README.md", "skills/clanker-ui/references/icons.md"} {
		for _, m := range iconCount.FindAllStringSubmatch(readFile(t, "../../"+name), -1) {
			if m[1] != want {
				t.Errorf("%s: %q, but ICONS has %s icons", name, m[0], want)
			}
		}
	}
}

func TestAgentsCITriggers(t *testing.T) {
	ci := readFile(t, "../../.github/workflows/ci.yml")
	start := strings.Index(ci, "\non:\n")
	if start < 0 {
		t.Fatal("ci.yml: no on: block")
	}
	block := ci[start+5:]
	block = block[:strings.Index(block, "\n\n")]
	has := map[string]bool{}
	for _, m := range regexp.MustCompile(`(?m)^  ([a-z_]+):`).FindAllStringSubmatch(block, -1) {
		has[m[1]] = true
	}
	m := regexp.MustCompile(`(?m)^- CI on (.+?) skips`).FindStringSubmatch(readFile(t, "../../AGENTS.md"))
	if m == nil {
		t.Fatal("AGENTS.md: no \"- CI on ... skips\" line")
	}
	said := map[string]bool{"pull_request": strings.Contains(m[1], "pull request"), "push": strings.Contains(m[1], "push")}
	for k, v := range said {
		if v != has[k] {
			t.Errorf("AGENTS.md says CI runs on %q, but the ci.yml trigger %s is %v", m[1], k, has[k])
		}
	}
}

func TestCatalogSharedSectionText(t *testing.T) {
	testCatalog(t)
	full := func(name string) string {
		_, text, _ := strings.Cut(string(catFilesOut["skills/clanker-ui/references/components/"+name+".md"]), "\n## Full text\n\n")
		return text
	}
	for _, c := range []string{"kbd", "textarea"} {
		if strings.Contains(full(c), "dropzone") {
			t.Errorf("%s: full text has the dropzone code of input", c)
		}
	}
	if kbd := full("kbd"); strings.Contains(kbd, `data-slot="input"`) || strings.Contains(kbd, "aria-invalid") {
		t.Errorf("kbd: full text has the input lines:\n%s", kbd)
	}
	if !strings.Contains(full("input"), `<label data-slot="empty" data-variant="outline" class="dropzone">`) {
		t.Error("input: full text lacks the dropzone markup")
	}
	for _, c := range []string{"empty", "separator", "skeleton"} {
		if strings.Contains(full(c), `data-slot="aspect-ratio"`) {
			t.Errorf("%s: full text has the aspect-ratio bullet", c)
		}
	}
	if !strings.Contains(full("aspect-ratio"), `data-slot="aspect-ratio"`) {
		t.Error("aspect-ratio: full text lacks its bullet")
	}
}

var stateNotSetByKit = map[string]bool{
	"tooltip-content data-state=delayed-open": true,
	"navigation-menu-content data-motion":     true,
	"navigation-menu-link data-state":         true,
	"tabs-trigger data-active":                true,
	"sidebar-menu-button data-state":          true,
	"sidebar-menu-sub-button data-state":      true,
	"questionnaire-choice data-state":         true,
}

func TestCatalogStateValues(t *testing.T) {
	cat := testCatalog(t)
	filled := 0
	for _, c := range cat.Components {
		for _, p := range c.Parts {
			for _, name := range p.State {
				key := p.Slot + " " + name
				v, ok := p.StateVals[name]
				switch {
				case stateNotSetByKit[key] && ok:
					t.Errorf("%s: the README states values %v; remove it from stateNotSetByKit", key, v)
				case stateNotSetByKit[key]:
					continue
				case !ok:
					t.Errorf("%s: the README states no values for this State attribute (see kit/clanker-ui.js)", key)
					continue
				}
				filled++
				vals, list := v.([]string)
				for _, cv := range p.css[name] {
					switch {
					case cv == "" || v == "boolean" && (cv == "true" || cv == "false"):
					case stateNotSetByKit[key+"="+cv]:
						if slices.Contains(vals, cv) {
							t.Errorf("%s=%s: the README states it; remove it from stateNotSetByKit", key, cv)
						}
					case !list || !slices.Contains(vals, cv):
						t.Errorf("%s: the CSS styles %q, but the README values are %v", key, cv, v)
					}
				}
			}
		}
	}
	if filled < 130 {
		t.Errorf("%d State attributes have values, want at least 130", filled)
	}
	want := map[string]string{"drawer-popup data-swipe-axis": "[x y]", "dialog-content data-state": "[closed open]", "toast data-expanded": "boolean", "checkbox data-state": "[checked indeterminate unchecked]"}
	for _, c := range cat.Components {
		for _, p := range c.Parts {
			for name, v := range p.StateVals {
				if w, ok := want[p.Slot+" "+name]; ok && fmt.Sprint(v) != w {
					t.Errorf("%s %s: values %v, want %s", p.Slot, name, v, w)
				}
				delete(want, p.Slot+" "+name)
			}
		}
	}
	for key := range want {
		t.Errorf("%s: no state values", key)
	}
}
