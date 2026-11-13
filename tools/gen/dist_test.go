package main

import (
	"bytes"
	"encoding/json"
	"maps"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"sync"
	"testing"

	"github.com/evanw/esbuild/pkg/api"
)

var (
	distOnce sync.Once
	distRes  *distResult
	distErr  error
)

func testDist(t *testing.T) *distResult {
	t.Helper()
	distOnce.Do(func() { distRes, distErr = buildDist("../..") })
	if distErr != nil {
		t.Fatal(distErr)
	}
	return distRes
}

func testTable(t *testing.T) *groupTable {
	t.Helper()
	g, err := readGroups("groups.tsv")
	if err != nil {
		t.Fatal(err)
	}
	return g
}

func TestDistFresh(t *testing.T) {
	res := testDist(t)
	again, err := buildDist("../..")
	if err != nil {
		t.Fatal(err)
	}
	if !maps.EqualFunc(res.files, again.files, bytes.Equal) {
		t.Fatal("two dist runs give different bytes")
	}
	committed, _ := filepath.Glob("../../dist/clanker-ui*.min.*")
	if len(committed) == 0 {
		t.Fatal("dist/ has no generated files; run go run ./tools/gen dist")
	}
	for _, f := range committed {
		if _, ok := res.files[filepath.Base(f)]; !ok {
			t.Errorf("%s is not a dist output; run go run ./tools/gen dist", f)
		}
	}
	for name, want := range res.files {
		got, err := os.ReadFile(filepath.Join("../../dist", name))
		if err != nil || !bytes.Equal(got, want) {
			t.Errorf("dist/%s is old; run go run ./tools/gen dist", name)
		}
	}
}

func TestDistFiles(t *testing.T) {
	res := testDist(t)
	want := []string{"clanker-ui-a11y.min.css", "clanker-ui-chart.min.css", "clanker-ui-chart.min.js", "clanker-ui-chat.min.css", "clanker-ui-chat.min.js", "clanker-ui-code.min.js", "clanker-ui-core.min.css", "clanker-ui-core.min.js", "clanker-ui-forms.min.css", "clanker-ui-forms.min.js", "clanker-ui-layout.min.css", "clanker-ui-layout.min.js", "clanker-ui-overlays.min.css", "clanker-ui-overlays.min.js", "clanker-ui-theme.min.js", "clanker-ui-themes.min.css", "clanker-ui.min.css", "clanker-ui.min.js"}
	for _, st := range kitStyles[1:] {
		base := strings.TrimSuffix(st.file, ".css")
		want = append(want, base+".min.css")
		for _, g := range []string{"chart", "chat", "core", "forms", "layout", "overlays"} {
			want = append(want, base+"-"+g+".min.css")
		}
	}
	slices.Sort(want)
	if got := slices.Sorted(maps.Keys(res.files)); !slices.Equal(got, want) {
		t.Fatalf("dist files\n got %v\nwant %v", got, want)
	}
	for name, b := range res.files {
		src := "../../clanker-ui.js"
		switch {
		case name == "clanker-ui-chart.min.js" || name == "clanker-ui-code.min.js":
			src = "../../" + strings.Replace(name, ".min.", ".", 1)
		case name == "clanker-ui-theme.min.js":
			src = "../../clanker-ui-theme.js"
		case name == "clanker-ui-themes.min.css":
			src = "../../clanker-ui-themes.css"
		case name == "clanker-ui-a11y.min.css":
			src = "../../clanker-ui-a11y.css"
		case strings.HasSuffix(name, ".css"):
			src = "../../clanker-ui.css"
		}
		for _, st := range kitStyles[1:] {
			if base := strings.TrimSuffix(st.file, ".css"); name == base+".min.css" || strings.HasPrefix(name, base+"-") {
				src = "../../" + st.file
			}
		}
		orig, err := os.ReadFile(src)
		if err != nil {
			t.Fatal(err)
		}
		lic, _, _ := strings.Cut(string(orig), "\n")
		first, rest, _ := strings.Cut(string(b), "\n")
		if first != lic {
			t.Errorf("%s: first line %q, want the license line of %s", name, first, src)
		}
		if strings.Contains(rest, "/*") {
			t.Errorf("%s has a comment after the license line", name)
		}
		if !strings.HasSuffix(rest, "\n") || len(rest) > len(orig) {
			t.Errorf("%s: want a minified file that ends with a new line", name)
		}
	}
	for _, name := range []string{"clanker-ui-chart.min.js", "clanker-ui-code.min.js"} {
		if !strings.Contains(string(res.files[name]), `from"./clanker-ui-core.min.js"`) {
			t.Errorf("%s does not import ./clanker-ui-core.min.js", name)
		}
	}
}

func TestDistCSSPartition(t *testing.T) {
	res := testDist(t)
	strip := func(b []byte) string {
		_, rest, _ := strings.Cut(string(b), "\n")
		rest, ok := strings.CutPrefix(rest, layerOrder)
		if !ok {
			t.Fatal("a CSS dist file does not start with the layer order")
		}
		return strings.TrimSuffix(rest, "\n")
	}
	var joined strings.Builder
	for _, g := range distGroups {
		joined.WriteString(strip(res.files["clanker-ui-"+g+".min.css"]))
	}
	if strip(res.files[distCSS]) != joined.String() {
		t.Error("the CSS group files in group order are not equal to clanker-ui.min.css")
	}
	src, err := os.ReadFile("../../clanker-ui.css")
	if err != nil {
		t.Fatal(err)
	}
	tree, err := parseCSS(string(src))
	if err != nil {
		t.Fatal(err)
	}
	n := 0
	var count func(items []cssItem)
	count = func(items []cssItem) {
		for _, it := range items {
			if it.rule == nil {
				continue
			}
			p := it.rule.prelude
			switch {
			case strings.HasPrefix(p, "@keyframes"), strings.HasPrefix(p, "@property"), strings.HasPrefix(p, "@font-face"):
			case strings.HasPrefix(p, "@"):
				count(it.rule.items)
			default:
				n += len(splitTop(p, ','))
			}
		}
	}
	count(tree.items)
	if n != len(res.alts) {
		t.Errorf("clanker-ui.css has %d selectors, the groups have %d", n, len(res.alts))
	}
	for _, a := range res.alts {
		if !slices.Contains(distGroups, a.group) {
			t.Errorf("%s: no group", a.selector)
		}
	}
}

func TestDistSelectorGroups(t *testing.T) {
	g := testTable(t)
	for sel, want := range map[string]string{
		`[data-slot=button]`: "core",
		`[data-slot=button]:where([data-input-group-button])`:                      "forms",
		`[data-slot=button]:where([data-calendar-day-button])`:                     "overlays",
		`[data-slot=popover-content][data-date-picker-content]`:                    "overlays",
		`[data-slot="sidebar"] [data-slot="button"]`:                               "core",
		`:where([data-slot=dialog-content]) > form:not([data-slot])`:               "overlays",
		`:where([data-slot=accordion-content]) > div`:                              "layout",
		`[data-backdrop-of="sheet-content"]::backdrop`:                             "overlays",
		`:is([data-slot="field-group"], [data-slot="checkbox-group"])`:             "forms",
		`[data-slot=calendar][data-button-variant=outline]`:                        "overlays",
		`[data-slot=field-label]:is(:where([data-slot=sidebar])[data-disabled] *)`: "forms",
		`*,:before`: "core",
		`:where([data-slot="button-group"] > :is([data-slot="dropdown-menu"], [data-slot="select"], [data-slot="combobox"], [data-slot="drawer"])) > [data-slot]:not([data-slot$="-content"])`: "forms",
		`:where([data-slot="button-group"] > :is([data-slot="dropdown-menu"], [data-slot="popover"])) > [data-slot]`:                                                                           "overlays",
		`:where([data-slot=field] > :is(*, [data-slot=dialog])) > div`:                                                                                                                         "forms",
		`:where([data-slot=sidebar]) :has([data-slot=calendar], [data-slot=tabs]) > div`:                                                                                                       "layout",
		`[data-slot="theme-switch"] span`: "core",
	} {
		got, err := g.selectorGroup(sel)
		if err != nil || got != want {
			t.Errorf("%s: got %q %v, want %q", sel, got, err, want)
		}
	}
	if _, err := g.selectorGroup(`[data-slot=nothing-here]`); err == nil {
		t.Error("a slot without a component must stop the run")
	}
	if _, err := g.selectorGroup(`:nth-child(2 of [data-slot=dialog]) > div`); err == nil {
		t.Error("a part selector in an unknown functional pseudo-class must stop the run")
	}
	if _, err := g.selectorGroup(`:where([data-slot=dialog],[data-slot=tabs])`); err == nil {
		t.Error("a subject with parts of two groups must stop the run")
	}
}

func TestDistSpecificity(t *testing.T) {
	for sel, want := range map[string][3]int{
		`[data-slot=button]`:                         {0, 1, 0},
		`[data-slot=button]:where([data-size=xs])`:   {0, 1, 0},
		`[data-slot=a]:not(:where(.x))`:              {0, 1, 0},
		`:is([data-slot=a],#b) > div::before`:        {1, 0, 2},
		`[data-slot=a]:hover:nth-child(2 of .x)`:     {0, 4, 0},
		`:where([data-slot=a]) [data-slot=b]:has(p)`: {0, 1, 1},
	} {
		if got := specificity(sel); got != want {
			t.Errorf("%s: %v, want %v", sel, got, want)
		}
	}
}

var distOrderAllowed = []struct {
	pair   *regexp.Regexp
	reason string
}{
	{regexp.MustCompile(`^\[data-slot="button"\]:where\(\[data-calendar-day-button\]\)\t\[data-slot="button"\]:where\(\[data-input-group-button\]\)`), "a button is a calendar day or an input group button, never both"},
	{regexp.MustCompile(`\t\[data-theme-set="toggle"\] (> svg\.lucide-contrast|\[data-lucide="sun"\])$`), "these theme toggle icons are only inside the core theme toggle button, not inside a part of another group"},
	{regexp.MustCompile(`^\[data-slot="attachment-media"\][^\t]* svg:not\(\[class\*="size-"\], \[data-slot\]\)\t\[data-slot="avatar-group-count"\][^\t]* > svg$`), "the avatar group count icon is a child of the count, not an icon in attachment media"},
}

func mentionedSlots(sel string) []string {
	var out []string
	for _, m := range slotAttr.FindAllStringSubmatch(removePseudo(sel, "not"), -1) {
		out = append(out, m[1])
	}
	return out
}

func mayMatchSame(a, b cssAlt) bool {
	sa, sb := subjectSlots(a.selector), subjectSlots(b.selector)
	switch {
	case len(sa) > 0 && len(sb) > 0:
		return sa[0] == sb[0]
	case len(sa) > 0:
		m := mentionedSlots(b.selector)
		return len(m) == 0 || slices.Contains(m, sa[0])
	case len(sb) > 0:
		m := mentionedSlots(a.selector)
		return len(m) == 0 || slices.Contains(m, sb[0])
	}
	ma, mb := mentionedSlots(a.selector), mentionedSlots(b.selector)
	if len(ma) == 0 || len(mb) == 0 {
		return true
	}
	for _, x := range ma {
		if slices.Contains(mb, x) {
			return true
		}
	}
	return false
}

func TestDistCSSOrder(t *testing.T) {
	res := testDist(t)
	g := testTable(t)
	var bad []string
	used := map[int]bool{}
	for x, a := range res.alts {
		for _, b := range res.alts[x+1:] {
			if a.ctx != b.ctx || g.rank(a.group) <= g.rank(b.group) || specificity(a.selector) != specificity(b.selector) {
				continue
			}
			shared := false
			for _, p := range a.props {
				if slices.Contains(b.props, p) {
					shared = true
					break
				}
			}
			if !shared || !mayMatchSame(a, b) {
				continue
			}
			pair := a.selector + "\t" + b.selector
			if i := slices.IndexFunc(distOrderAllowed, func(e struct {
				pair   *regexp.Regexp
				reason string
			}) bool {
				return e.pair.MatchString(pair)
			}); i >= 0 {
				used[i] = true
				continue
			}
			bad = append(bad, a.group+" before "+b.group+": "+trunc(a.selector, 140)+" | "+trunc(b.selector, 140))
		}
	}
	if len(bad) > 0 {
		slices.Sort(bad)
		t.Errorf("group order changes the order of %d rule pairs that can set the same property on the same element:\n  %s", len(bad), strings.Join(bad, "\n  "))
	}
	for i, e := range distOrderAllowed {
		if !used[i] {
			t.Errorf("distOrderAllowed entry %q matches no pair; remove it", e.reason)
		}
	}
}

func TestDistJSPartition(t *testing.T) {
	res := testDist(t)
	first := strings.IndexByte(res.js, '\n') + 1
	var b strings.Builder
	end := first
	for _, st := range res.stmts {
		if st.start != end {
			t.Fatalf("line %d: statements are not contiguous", st.line)
		}
		b.WriteString(res.js[st.start:st.end])
		end = st.end
	}
	if res.js[:first]+b.String() != res.js {
		t.Fatal("the JS statements do not give clanker-ui.js again")
	}
	slots := map[string]string{}
	for _, st := range res.stmts {
		if st.slot == "" {
			continue
		}
		if g, dup := slots[st.slot]; dup && g != st.group {
			t.Errorf("slot %s is in %s and %s", st.slot, g, st.group)
		}
		slots[st.slot] = st.group
	}
	all := regexp.MustCompile(`(?m)^(?:define|partDefaults)\("([a-z0-9-]+)"`).FindAllStringSubmatch(res.js, -1)
	if len(all) != len(slots) {
		t.Errorf("clanker-ui.js has %d top-level define calls, the split has %d", len(all), len(slots))
	}
	g := testTable(t)
	for slot, grp := range slots {
		if c := g.component(slot); c != "" && g.group[c] != grp && g.group[c] != "chart" {
			t.Errorf("slot %s: JS group %s, CSS group %s", slot, grp, g.group[c])
		}
	}
}

func TestDistJSCrossGroup(t *testing.T) {
	g := testTable(t)
	src := "/*! x */\nconst a = 1\nexport function h() {}\nscan(document.documentElement)\nfunction dialogShow() {\n  return h()\n}\nfunction selectOpen() {\n  return dialogShow()\n}\n"
	err := g.distJS(&distResult{files: map[string][]byte{}, imports: map[string][]string{}}, src)
	if err == nil || !strings.Contains(err.Error(), "selectOpen uses dialogShow from overlays") {
		t.Errorf("a forms function that calls an overlays function must stop the run: %v", err)
	}
	src = "/*! x */\nconst a = 1\nscan(document.documentElement)\nfunction mysteryThing() {}\n"
	if err := g.distJS(&distResult{files: map[string][]byte{}, imports: map[string][]string{}}, src); err == nil {
		t.Error("a name without a component prefix must stop the run")
	}
	masked, err := maskJS("const r = /[/]x`/g\nconst s = `a${ {b: \"}\"}.b }c`\nconst d = a / 2 // }\n")
	if err != nil {
		t.Fatal(err)
	}
	if strings.ContainsAny(masked, "`\"") || strings.Count(masked, "/") != 1 || strings.Count(masked, "{") != 1 || strings.Count(masked, "}") != 1 || !strings.Contains(masked, "const d = a / 2") {
		t.Errorf("mask keeps text of strings, templates, regular expressions, or comments: %q", masked)
	}
}

func esbuildBundle(t *testing.T, dir, entry string) []string {
	t.Helper()
	r := api.Build(api.BuildOptions{EntryPoints: []string{filepath.Join(dir, entry)}, Bundle: true, Write: false, Format: api.FormatESModule, Metafile: true, LogLevel: api.LogLevelSilent, Outdir: filepath.Join(dir, "out")})
	if err := esbuildErr(r.Errors); err != nil {
		t.Fatalf("%s: %v", entry, err)
	}
	var meta struct {
		Outputs map[string]struct {
			Exports []string `json:"exports"`
		} `json:"outputs"`
	}
	if err := json.Unmarshal([]byte(r.Metafile), &meta); err != nil {
		t.Fatal(err)
	}
	var out []string
	for _, o := range meta.Outputs {
		for _, e := range o.Exports {
			if !strings.HasPrefix(e, "_") {
				out = append(out, e)
			}
		}
	}
	slices.Sort(out)
	return out
}

func TestDistJSLinks(t *testing.T) {
	res := testDist(t)
	dir := t.TempDir()
	for name, b := range res.files {
		if err := os.WriteFile(filepath.Join(dir, name), b, 0o644); err != nil {
			t.Fatal(err)
		}
	}
	var public []string
	for _, f := range []string{"../../clanker-ui.js", "../../clanker-ui-chart.js", "../../clanker-ui-code.js"} {
		b, err := os.ReadFile(f)
		if err != nil {
			t.Fatal(err)
		}
		for _, m := range jsExports.FindAllStringSubmatch(string(b), -1) {
			public = append(public, m[1])
		}
	}
	slices.Sort(public)
	line := func(names ...string) string {
		var b strings.Builder
		for _, n := range names {
			b.WriteString(`export * from "./` + n + "\"\n")
		}
		return b.String()
	}
	groups := []string{distCore, "clanker-ui-chart.min.js", "clanker-ui-code.min.js"}
	for _, g := range distJSGroups[1:] {
		groups = append(groups, "clanker-ui-"+g+".min.js")
	}
	os.WriteFile(filepath.Join(dir, "groups.js"), []byte(line(groups...)), 0o644)
	os.WriteFile(filepath.Join(dir, "all.js"), []byte(line(distAll, "clanker-ui-chart.min.js", "clanker-ui-code.min.js")), 0o644)
	for _, entry := range []string{"groups.js", "all.js"} {
		if got := esbuildBundle(t, dir, entry); !slices.Equal(got, public) {
			t.Errorf("%s exports\n got %v\nwant %v", entry, got, public)
		}
	}
	for g, names := range res.imports {
		if len(names) == 0 {
			t.Errorf("group %s imports nothing from the core", g)
		}
	}
	os.WriteFile(filepath.Join(dir, "assign.js"), []byte("import { _"+res.internal[0]+" as x } from \"./"+distCore+"\"\nx = 1\n"), 0o644)
	r := api.Build(api.BuildOptions{EntryPoints: []string{filepath.Join(dir, "assign.js")}, Bundle: true, Write: false, LogLevel: api.LogLevelSilent, Outdir: filepath.Join(dir, "out")})
	if len(r.Errors) == 0 {
		t.Error("esbuild does not stop on an assignment to an import")
	}
}

func TestDistGroupsTableInDocs(t *testing.T) {
	table := testTable(t).markdown()
	for _, f := range []string{"../../README.md", "../../docs/content/index/page.md"} {
		b, err := os.ReadFile(f)
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(b), table) {
			t.Errorf("%s has no current groups table; paste the output of go run ./tools/gen dist -table", f)
		}
	}
}

func customProps(t *testing.T, css string) []string {
	t.Helper()
	tree, err := parseCSS(css)
	if err != nil {
		t.Fatal(err)
	}
	var out []string
	var walk func(items []cssItem)
	walk = func(items []cssItem) {
		for _, it := range items {
			if it.rule != nil {
				walk(it.rule.items)
				continue
			}
			if name, value, ok := strings.Cut(it.decl, ":"); ok && strings.HasPrefix(strings.TrimSpace(name), "--") {
				out = append(out, strings.TrimSpace(name)+":"+strings.TrimSpace(value))
			}
		}
	}
	walk(tree.items)
	slices.Sort(out)
	return out
}

func TestDistKeepsCustomPropertyText(t *testing.T) {
	res := testDist(t)
	for src, dst := range map[string]string{"clanker-ui.css": distCSS, "clanker-ui-themes.css": "clanker-ui-themes.min.css", "clanker-ui-a11y.css": "clanker-ui-a11y.min.css"} {
		b, err := os.ReadFile("../../" + src)
		if err != nil {
			t.Fatal(err)
		}
		want, got := customProps(t, string(b)), customProps(t, string(res.files[dst]))
		if !slices.Equal(got, want) {
			for i := range min(len(got), len(want)) {
				if got[i] != want[i] {
					t.Errorf("%s: custom property %q, source %q", dst, got[i], want[i])
					break
				}
			}
			t.Errorf("%s: %d custom properties, source %d", dst, len(got), len(want))
		}
	}
}

var docImport = regexp.MustCompile(`import\s*\{([^}]*)\}\s*from\s*"([^"]+)"`)

func TestDocsImportNames(t *testing.T) {
	exports := map[string][]string{}
	for _, f := range []string{"clanker-ui.js", "clanker-ui-chart.js", "clanker-ui-code.js"} {
		exports[f] = esbuildBundle(t, "../..", f)
	}
	mins, err := filepath.Glob("../../dist/*.min.js")
	if err != nil {
		t.Fatal(err)
	}
	for _, f := range mins {
		exports[filepath.Base(f)] = esbuildBundle(t, "../../dist", filepath.Base(f))
	}
	docs := []string{"../../README.md", "../../skills/clanker-ui/SKILL.md"}
	refs, _ := filepath.Glob("../../skills/clanker-ui/references/*.md")
	docs = append(docs, refs...)
	filepath.WalkDir("../../docs/content", func(p string, d os.DirEntry, err error) error {
		if err == nil && strings.HasSuffix(p, ".md") {
			docs = append(docs, p)
		}
		return err
	})
	n := 0
	oneFile := map[string]bool{}
	for _, f := range docs {
		b, err := os.ReadFile(f)
		if err != nil {
			t.Fatal(err)
		}
		for _, m := range docImport.FindAllStringSubmatch(string(b), -1) {
			file := filepath.Base(m[2])
			names, ok := exports[file]
			if !ok {
				t.Errorf("%s: import from unknown file %s", f, m[2])
				continue
			}
			for _, name := range strings.Split(m[1], ",") {
				name, _, _ = strings.Cut(strings.TrimSpace(name), " ")
				n++
				if file == distAll {
					oneFile[f+" "+name] = true
				}
				if !slices.Contains(names, name) {
					t.Errorf("%s: %s does not export %s", f, file, name)
				}
			}
		}
	}
	if n < 10 {
		t.Errorf("found %d imported names in the docs", n)
	}
	for _, f := range docs[:2] {
		for _, name := range []string{"h", "icon", "theme", "toast"} {
			if !oneFile[f+" "+name] {
				t.Errorf("%s: no import of %s from %s", f, name, distAll)
			}
		}
	}
	cat := testCatalog(t)
	for _, c := range cat.Components {
		readable, min := exportModules(cat, c)
		files := []string{readable}
		for _, m := range strings.Split(min, " or ") {
			files = append(files, strings.Trim(m, "`"))
		}
		for _, name := range c.Exports {
			for _, file := range files {
				if !slices.Contains(exports[file], name) {
					t.Errorf("components.md: %s names %s, which does not export %s", c.Name, file, name)
				}
			}
		}
	}
}
