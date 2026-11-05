package main

import (
	"errors"
	"flag"
	"fmt"
	"maps"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"sort"
	"strings"

	"github.com/evanw/esbuild/pkg/api"
)

var (
	distGroups   = []string{"core", "forms", "overlays", "layout", "chat", "chart"}
	distJSGroups = []string{"core", "forms", "overlays", "layout", "chat"}
	distModules  = []string{"clanker-ui-chart.js", "clanker-ui-code.js"}
)

const (
	distCore    = "clanker-ui-core.min.js"
	distAll     = "clanker-ui.min.js"
	distCSS     = "clanker-ui.min.css"
	distAnchor  = "scan(document.documentElement)"
	distChartIn = `from "./clanker-ui.js"`
)

type groupTable struct {
	group  map[string]string
	needs  map[string][]string
	order  []string
	prefix map[string]string
	names  []string
	camel  []string
	byCase map[string]string
}

type jsStmt struct {
	start, end int
	line       int
	name, slot string
	exported   bool
	group      string
	ids        map[string]bool
}

type cssAlt struct {
	ctx      string
	selector string
	group    string
	props    []string
	index    int
}

type distResult struct {
	files    map[string][]byte
	js       string
	stmts    []jsStmt
	internal []string
	imports  map[string][]string
	cssBody  map[string]string
	alts     []cssAlt
}

func distMain(args []string) error {
	fset := flag.NewFlagSet("dist", flag.ExitOnError)
	root := fset.String("root", ".", "repository root with the readable kit files")
	out := fset.String("out", "", "output directory (default: <root>/dist)")
	table := fset.Bool("table", false, "print the Markdown table of the groups (README and docs) and stop")
	fset.Parse(args)
	if *table {
		t, err := readGroups(filepath.Join(*root, "tools", "gen", "groups.tsv"))
		if err != nil {
			return err
		}
		fmt.Print(t.markdown())
		return nil
	}
	dir := *out
	if dir == "" {
		dir = filepath.Join(*root, "dist")
	}
	names, err := writeDist(*root, dir)
	if err != nil {
		return err
	}
	for _, n := range names {
		fmt.Println(filepath.Join(dir, n))
	}
	if *out != "" {
		return nil
	}
	return catalogMain([]string{"-root", *root})
}

func writeDist(root, dir string) ([]string, error) {
	res, err := buildDist(root)
	if err != nil {
		return nil, err
	}
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, err
	}
	old, _ := filepath.Glob(filepath.Join(dir, "clanker-ui*.min.*"))
	for _, f := range old {
		if _, ok := res.files[filepath.Base(f)]; !ok {
			if err := os.Remove(f); err != nil {
				return nil, err
			}
		}
	}
	names := slices.Sorted(maps.Keys(res.files))
	for _, n := range names {
		if err := os.WriteFile(filepath.Join(dir, n), res.files[n], 0o644); err != nil {
			return nil, err
		}
	}
	return names, nil
}

func readGroups(path string) (*groupTable, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	t := &groupTable{group: map[string]string{}, needs: map[string][]string{}, prefix: map[string]string{}, byCase: map[string]string{}}
	for i, line := range strings.Split(strings.TrimRight(string(b), "\n"), "\n") {
		cols := strings.Split(line, "\t")
		if len(cols) < 2 || len(cols) > 3 || cols[0] == "" || !slices.Contains(distGroups, cols[1]) {
			return nil, fmt.Errorf("%s:%d: want <component><TAB><group>[<TAB><needs>] with a group of %v", path, i+1, distGroups)
		}
		if p, ok := strings.CutPrefix(cols[0], "js:"); ok {
			t.prefix[p] = cols[1]
			continue
		}
		if _, dup := t.group[cols[0]]; dup {
			return nil, fmt.Errorf("%s:%d: %s twice", path, i+1, cols[0])
		}
		t.group[cols[0]] = cols[1]
		t.order = append(t.order, cols[0])
		if len(cols) == 3 {
			for _, n := range strings.Split(cols[2], ",") {
				if !slices.Contains(distGroups, n) {
					return nil, fmt.Errorf("%s:%d: unknown group %q in needs", path, i+1, n)
				}
				t.needs[cols[0]] = append(t.needs[cols[0]], n)
			}
		}
	}
	t.names = slices.Clone(t.order)
	sort.SliceStable(t.names, func(a, b int) bool { return len(t.names[a]) > len(t.names[b]) })
	for _, n := range append(slices.Clone(t.order), slices.Collect(maps.Keys(t.prefix))...) {
		parts := strings.Split(n, "-")
		c := parts[0]
		for _, p := range parts[1:] {
			c += strings.ToUpper(p[:1]) + p[1:]
		}
		t.byCase[c] = n
		t.camel = append(t.camel, c)
	}
	sort.SliceStable(t.camel, func(a, b int) bool {
		return len(t.camel[a]) > len(t.camel[b]) || len(t.camel[a]) == len(t.camel[b]) && t.camel[a] < t.camel[b]
	})
	return t, nil
}

func (t *groupTable) markdown() string {
	var b strings.Builder
	b.WriteString("| Group | Components | Needs |\n| --- | --- | --- |\n")
	for _, g := range distGroups {
		var comps, needs []string
		for _, c := range t.order {
			if t.group[c] != g {
				continue
			}
			comps = append(comps, c)
			if n := t.needs[c]; len(n) > 0 {
				needs = append(needs, c+": `"+strings.Join(n, "`, `")+"`")
			}
		}
		fmt.Fprintf(&b, "| `%s` | %s | %s |\n", g, strings.Join(comps, ", "), strings.Join(needs, "; "))
	}
	return b.String()
}

func (t *groupTable) rank(g string) int { return slices.Index(distGroups, g) }

func (t *groupTable) component(slot string) string {
	for _, n := range t.names {
		if slot == n || strings.HasPrefix(slot, n+"-") {
			return n
		}
	}
	return ""
}

func (t *groupTable) partComponent(attr string) string {
	if attr == "slot" {
		return ""
	}
	for _, n := range t.names {
		if strings.HasPrefix(attr, n+"-") {
			return n
		}
	}
	return ""
}

func (t *groupTable) nameGroup(name string) (string, bool) {
	for _, c := range t.camel {
		if name == c || strings.HasPrefix(name, c) && len(name) > len(c) && name[len(c)] >= 'A' && name[len(c)] <= 'Z' {
			n := t.byCase[c]
			if g, ok := t.prefix[n]; ok {
				return g, true
			}
			return t.group[n], true
		}
	}
	return "", false
}

func buildDist(root string) (*distResult, error) {
	t, err := readGroups(filepath.Join(root, "tools", "gen", "groups.tsv"))
	if err != nil {
		return nil, err
	}
	read := func(name string) (string, error) {
		b, err := os.ReadFile(filepath.Join(root, name))
		return string(b), err
	}
	res := &distResult{files: map[string][]byte{}, imports: map[string][]string{}, cssBody: map[string]string{}}
	css, err := read("clanker-ui.css")
	if err != nil {
		return nil, err
	}
	if err := t.distCSS(res, css); err != nil {
		return nil, fmt.Errorf("clanker-ui.css: %w", err)
	}
	for _, name := range []string{"clanker-ui-themes.css", "clanker-ui-a11y.css"} {
		src, err := read(name)
		if err != nil {
			return nil, err
		}
		lic, body, _ := strings.Cut(src, "\n")
		min, err := minifyCSS(body)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", name, err)
		}
		res.files[strings.TrimSuffix(name, ".css")+".min.css"] = []byte(lic + "\n" + min + "\n")
	}
	js, err := read("clanker-ui.js")
	if err != nil {
		return nil, err
	}
	if err := t.distJS(res, js); err != nil {
		return nil, fmt.Errorf("clanker-ui.js: %w", err)
	}
	for _, name := range distModules {
		mod, err := read(name)
		if err != nil {
			return nil, err
		}
		if strings.Count(mod, distChartIn) != 1 {
			return nil, fmt.Errorf("%s: want one import %s", name, distChartIn)
		}
		mod = strings.Replace(mod, distChartIn, `from "./`+distCore+`"`, 1)
		lic, body, _ := strings.Cut(mod, "\n")
		min, err := minifyJS(body)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", name, err)
		}
		res.files[strings.TrimSuffix(name, ".js")+".min.js"] = []byte(lic + "\n" + min + "\n")
	}
	boot, err := read("clanker-ui-theme.js")
	if err != nil {
		return nil, err
	}
	lic, body, _ := strings.Cut(boot, "\n")
	r := api.Transform(body, api.TransformOptions{Loader: api.LoaderJS, MinifyWhitespace: true, MinifyIdentifiers: true, MinifySyntax: true, Charset: api.CharsetUTF8, LegalComments: api.LegalCommentsNone, LogLevel: api.LogLevelSilent})
	if err := esbuildErr(r.Errors); err != nil {
		return nil, fmt.Errorf("clanker-ui-theme.js: %w", err)
	}
	res.files["clanker-ui-theme.min.js"] = []byte(lic + "\n" + string(r.Code))
	return res, nil
}

func minifyJS(src string) (string, error) {
	r := api.Transform(src, api.TransformOptions{Loader: api.LoaderJS, Format: api.FormatESModule, MinifyWhitespace: true, MinifyIdentifiers: true, MinifySyntax: true, Charset: api.CharsetUTF8, LegalComments: api.LegalCommentsNone, LogLevel: api.LogLevelSilent})
	if err := esbuildErr(r.Errors); err != nil {
		return "", err
	}
	return strings.TrimSuffix(string(r.Code), "\n"), nil
}

func minifyCSS(src string) (string, error) {
	r := api.Transform(src, api.TransformOptions{Loader: api.LoaderCSS, MinifyWhitespace: true, Charset: api.CharsetUTF8, LegalComments: api.LegalCommentsNone, LogLevel: api.LogLevelSilent})
	if err := esbuildErr(r.Errors); err != nil {
		return "", err
	}
	return strings.TrimSuffix(string(r.Code), "\n"), nil
}

func esbuildErr(msgs []api.Message) error {
	if len(msgs) == 0 {
		return nil
	}
	var parts []string
	for _, m := range msgs {
		where := ""
		if m.Location != nil {
			where = fmt.Sprintf("%d:%d: ", m.Location.Line, m.Location.Column)
		}
		parts = append(parts, where+m.Text)
	}
	return errors.New("esbuild: " + strings.Join(parts, "; "))
}

func (t *groupTable) distCSS(res *distResult, src string) error {
	lic, _, _ := strings.Cut(src, "\n")
	tree, err := parseCSS(src)
	if err != nil {
		return err
	}
	var parts map[string][]cssItem
	keyframes := map[string][]cssItem{}
	var kfOrder []string
	var walk func(items []cssItem, ctx []string) (map[string][]cssItem, error)
	walk = func(items []cssItem, ctx []string) (map[string][]cssItem, error) {
		out := map[string][]cssItem{}
		for _, it := range items {
			if it.rule == nil {
				if len(ctx) == 0 && strings.HasPrefix(it.decl, "@layer") {
					continue
				}
				return nil, fmt.Errorf("unexpected statement %q", trunc(it.decl, 80))
			}
			p := it.rule.prelude
			switch {
			case strings.HasPrefix(p, "@keyframes"):
				if len(ctx) != 0 {
					return nil, fmt.Errorf("nested %s", p)
				}
				name := strings.TrimSpace(strings.TrimPrefix(p, "@keyframes"))
				if _, dup := keyframes[name]; !dup {
					kfOrder = append(kfOrder, name)
				}
				keyframes[name] = append(keyframes[name], it)
			case strings.HasPrefix(p, "@property"), strings.HasPrefix(p, "@font-face"):
				out["core"] = append(out["core"], it)
			case strings.HasPrefix(p, "@"):
				sub, err := walk(it.rule.items, append(ctx, p))
				if err != nil {
					return nil, err
				}
				for _, g := range distGroups {
					if len(sub[g]) > 0 {
						out[g] = append(out[g], cssItem{rule: &cssRule{prelude: p, items: sub[g]}})
					}
				}
			default:
				var props []string
				for _, d := range it.rule.items {
					if d.rule == nil {
						props = append(props, declProp(d.decl))
					}
				}
				byGroup := map[string][]string{}
				for _, alt := range splitTop(p, ',') {
					alt = strings.TrimSpace(alt)
					g, err := t.selectorGroup(alt)
					if err != nil {
						return nil, err
					}
					byGroup[g] = append(byGroup[g], alt)
					res.alts = append(res.alts, cssAlt{ctx: strings.Join(ctx, " "), selector: alt, group: g, props: props, index: len(res.alts)})
				}
				for _, g := range distGroups {
					if sels := byGroup[g]; len(sels) > 0 {
						out[g] = append(out[g], cssItem{rule: &cssRule{prelude: strings.Join(sels, ","), items: it.rule.items}})
					}
				}
			}
		}
		return out, nil
	}
	parts, err = walk(tree.items, nil)
	if err != nil {
		return err
	}
	bodies := map[string]string{}
	for _, g := range distGroups {
		bodies[g] = compactCSS(parts[g])
	}
	for _, name := range kfOrder {
		use := regexp.MustCompile(`(?:^|[\s:,(])` + regexp.QuoteMeta(name) + `(?:$|[\s,;)}])`)
		var users []string
		for _, g := range distGroups {
			if use.MatchString(animationValues(bodies[g])) {
				users = append(users, g)
			}
		}
		g := "core"
		if len(users) == 1 {
			g = users[0]
		}
		parts[g] = append(parts[g], keyframes[name]...)
	}
	var full strings.Builder
	for _, g := range distGroups {
		min, err := minifyCSS(compactCSS(parts[g]))
		if err != nil {
			return fmt.Errorf("group %s: %w", g, err)
		}
		res.cssBody[g] = min
		res.files["clanker-ui-"+g+".min.css"] = []byte(lic + "\n" + layerOrder + min + "\n")
		full.WriteString(min)
	}
	res.files[distCSS] = []byte(lic + "\n" + layerOrder + full.String() + "\n")
	return nil
}

var animationDecl = regexp.MustCompile(`(?:animation(?:-name)?|--animate-[\w-]+)\s*:([^;{}]*)`)

func animationValues(css string) string {
	var b strings.Builder
	for _, m := range animationDecl.FindAllStringSubmatch(css, -1) {
		b.WriteString(" " + m[1] + " ;")
	}
	return b.String()
}

func compactCSS(items []cssItem) string {
	var b strings.Builder
	var write func(items []cssItem)
	write = func(items []cssItem) {
		for _, it := range items {
			if it.rule == nil {
				b.WriteString(it.decl)
				b.WriteByte(';')
				continue
			}
			b.WriteString(it.rule.prelude)
			b.WriteByte('{')
			write(it.rule.items)
			b.WriteByte('}')
		}
	}
	write(items)
	return b.String()
}

func removePseudo(s string, names ...string) string {
	var b strings.Builder
	for i := 0; i < len(s); {
		hit := ""
		for _, n := range names {
			if strings.HasPrefix(s[i:], ":"+n+"(") {
				hit = n
				break
			}
		}
		if hit == "" {
			b.WriteByte(s[i])
			i++
			continue
		}
		j, depth := i+len(hit)+1, 0
		for ; j < len(s); j++ {
			if s[j] == '(' {
				depth++
			} else if s[j] == ')' {
				depth--
				if depth == 0 {
					break
				}
			}
		}
		i = j + 1
	}
	return b.String()
}

func subjectCompound(sel string) string {
	depth, start := 0, 0
	var quote byte
	for i := 0; i < len(sel); i++ {
		c := sel[i]
		switch {
		case quote != 0:
			if c == '\\' {
				i++
			} else if c == quote {
				quote = 0
			}
		case c == '"' || c == '\'':
			quote = c
		case c == '(' || c == '[':
			depth++
		case c == ')' || c == ']':
			depth--
		case depth == 0 && (c == ' ' || c == '>' || c == '+' || c == '~' || c == '\n' || c == '\t'):
			start = i + 1
		}
	}
	return sel[start:]
}

func outsideParens(s string) string {
	var b strings.Builder
	depth := 0
	for i := 0; i < len(s); i++ {
		switch s[i] {
		case '(':
			depth++
		case ')':
			depth--
		default:
			if depth == 0 {
				b.WriteByte(s[i])
			}
		}
	}
	return b.String()
}

var (
	slotAttr     = regexp.MustCompile(`\[data-slot=["']?([a-z0-9-]+)["']?\]`)
	backdropAttr = regexp.MustCompile(`\[data-backdrop-of=["']?([a-z0-9-]+)["']?\]`)
	dataAttr     = regexp.MustCompile(`\[data-([a-z0-9-]+)[\]=~|^$*]`)
	wherePart    = regexp.MustCompile(`:(?:is|where)\(`)
)

func subjectSlots(sel string) []string {
	comp := removePseudo(subjectCompound(sel), "not", "has")
	var slots []string
	for _, m := range slotAttr.FindAllStringSubmatch(outsideParens(comp), -1) {
		slots = append(slots, m[1])
	}
	if len(slots) > 0 {
		return slots
	}
	for _, loc := range wherePart.FindAllStringIndex(comp, -1) {
		depth, j := 1, loc[1]
		for ; j < len(comp) && depth > 0; j++ {
			if comp[j] == '(' {
				depth++
			} else if comp[j] == ')' {
				depth--
			}
		}
		arg := comp[loc[1] : j-1]
		simple := true
		for _, a := range splitTop(arg, ',') {
			if subjectCompound(strings.TrimSpace(a)) != strings.TrimSpace(a) {
				simple = false
			}
		}
		if !simple {
			continue
		}
		for _, m := range slotAttr.FindAllStringSubmatch(arg, -1) {
			slots = append(slots, m[1])
		}
	}
	return slots
}

func noComponent(slot string) error {
	return fmt.Errorf("data-slot %q has no component in groups.tsv; add a line <component><TAB><group> to tools/gen/groups.tsv (groups: %s)", slot, strings.Join(distGroups, ", "))
}

func (t *groupTable) slotGroup(slot string) (string, error) {
	c := t.component(slot)
	if c == "" {
		return "", noComponent(slot)
	}
	return t.group[c], nil
}

func (t *groupTable) selectorGroup(sel string) (string, error) {
	slots := subjectSlots(sel)
	if len(slots) > 0 {
		g := ""
		for _, s := range slots {
			sg, err := t.slotGroup(s)
			if err != nil {
				return "", err
			}
			if g != "" && sg != g {
				return "", fmt.Errorf("selector subject has parts of two groups (%s, %s): %s", g, sg, trunc(sel, 160))
			}
			g = sg
		}
		comp := removePseudo(subjectCompound(sel), "not", "has")
		for _, m := range dataAttr.FindAllStringSubmatch(comp, -1) {
			if c := t.partComponent(m[1]); c != "" && t.rank(t.group[c]) > t.rank(g) {
				g = t.group[c]
			}
		}
		return g, nil
	}
	r, err := t.exprRank(sel)
	if err != nil {
		return "", err
	}
	return distGroups[max(r, 0)], nil
}

var bracketAttr = regexp.MustCompile(`^\[data-([a-z0-9-]+)(?:=["']?([a-z0-9-]+)["']?)?[\]~|^$*=]`)

func (t *groupTable) exprRank(s string) (int, error) {
	rank := -1
	raise := func(c string) {
		if c != "" && t.rank(t.group[c]) > rank {
			rank = t.rank(t.group[c])
		}
	}
	for i := 0; i < len(s); {
		switch s[i] {
		case '[':
			end := strings.IndexByte(s[i:], ']')
			if end < 0 {
				return 0, fmt.Errorf("unclosed [ in %s", trunc(s, 120))
			}
			if m := bracketAttr.FindStringSubmatch(s[i : i+end+1]); m != nil {
				switch {
				case m[1] == "slot" && m[2] != "" && strings.HasPrefix(s[i+len("[data-slot"):], "="):
					c := t.component(m[2])
					if c == "" {
						return 0, noComponent(m[2])
					}
					raise(c)
				case m[1] == "backdrop-of" && m[2] != "":
					raise(t.component(m[2]))
				default:
					raise(t.partComponent(m[1]))
				}
			}
			i += end + 1
		case ':':
			j := i + 1
			for j < len(s) && s[j] == ':' {
				j++
			}
			k := j
			for k < len(s) && (isIdentPart(s[k]) || s[k] == '-') {
				k++
			}
			if k >= len(s) || s[k] != '(' {
				i = k
				continue
			}
			depth, end := 0, k
			for ; end < len(s); end++ {
				if s[end] == '(' {
					depth++
				} else if s[end] == ')' {
					depth--
					if depth == 0 {
						break
					}
				}
			}
			arg := s[k+1 : end]
			switch name := s[j:k]; name {
			case "not":
			case "is", "where", "has":
				low := 0
				for n, alt := range splitTop(arg, ',') {
					r, err := t.exprRank(alt)
					if err != nil {
						return 0, err
					}
					if n == 0 || r < low {
						low = r
					}
				}
				if low > rank {
					rank = low
				}
			default:
				if strings.Contains(arg, "data-") {
					return 0, fmt.Errorf("cannot place a selector with data attributes in :%s(): %s", name, trunc(s, 160))
				}
			}
			i = end + 1
		default:
			i++
		}
	}
	return rank, nil
}

var regexPrev = map[string]bool{"return": true, "typeof": true, "case": true, "do": true, "else": true, "in": true, "of": true, "new": true, "delete": true, "void": true, "throw": true, "yield": true, "await": true, "instanceof": true}

func isIdentStart(c byte) bool {
	return c == '_' || c == '$' || c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z'
}

func isIdentPart(c byte) bool { return isIdentStart(c) || c >= '0' && c <= '9' }

func maskJS(src string) (string, error) {
	out := []byte(src)
	blank := func(a, b int) {
		for k := a; k < b; k++ {
			if out[k] != '\n' {
				out[k] = ' '
			}
		}
	}
	var stack []int
	regexOK := true
	n := len(src)
	for i := 0; i < n; {
		c := src[i]
		if len(stack) > 0 && stack[len(stack)-1] < 0 {
			start := i
			for i < n && src[i] != '`' && !(src[i] == '$' && i+1 < n && src[i+1] == '{') {
				if src[i] == '\\' {
					i++
				}
				i++
			}
			if i >= n {
				return "", fmt.Errorf("unclosed template literal")
			}
			blank(start, i)
			if src[i] == '`' {
				out[i] = ' '
				stack = stack[:len(stack)-1]
				i++
				regexOK = false
				continue
			}
			out[i], out[i+1] = ' ', ' '
			stack = append(stack, 0)
			i += 2
			regexOK = true
			continue
		}
		switch {
		case c == '/' && i+1 < n && src[i+1] == '*':
			end := strings.Index(src[i+2:], "*/")
			if end < 0 {
				return "", fmt.Errorf("unclosed comment")
			}
			blank(i, i+end+4)
			i += end + 4
		case c == '/' && i+1 < n && src[i+1] == '/':
			end := strings.IndexByte(src[i:], '\n')
			if end < 0 {
				end = n - i
			}
			blank(i, i+end)
			i += end
		case c == '"' || c == '\'':
			j := i + 1
			for j < n && src[j] != c {
				if src[j] == '\\' {
					j++
				}
				if j < n && src[j] == '\n' {
					return "", fmt.Errorf("line break in a string at byte %d", i)
				}
				j++
			}
			if j >= n {
				return "", fmt.Errorf("unclosed string at byte %d", i)
			}
			blank(i, j+1)
			i = j + 1
			regexOK = false
		case c == '`':
			out[i] = ' '
			stack = append(stack, -1)
			i++
		case c == '/' && regexOK:
			j, class := i+1, false
			for j < n {
				d := src[j]
				if d == '\\' {
					j += 2
					continue
				}
				if d == '\n' {
					return "", fmt.Errorf("line break in a regular expression at byte %d", i)
				}
				if d == '[' {
					class = true
				} else if d == ']' {
					class = false
				} else if d == '/' && !class {
					break
				}
				j++
			}
			j++
			for j < n && isIdentPart(src[j]) {
				j++
			}
			blank(i, j)
			i = j
			regexOK = false
		case isIdentStart(c) || c >= '0' && c <= '9':
			j := i
			for j < n && (isIdentPart(src[j]) || c >= '0' && c <= '9' && src[j] == '.') {
				j++
			}
			regexOK = regexPrev[src[i:j]]
			i = j
		case c == '{':
			if len(stack) > 0 {
				stack[len(stack)-1]++
			}
			regexOK = true
			i++
		case c == '}':
			if len(stack) > 0 && stack[len(stack)-1] == 0 {
				out[i] = ' '
				stack = stack[:len(stack)-1]
				regexOK = false
				i++
				continue
			}
			if len(stack) > 0 {
				stack[len(stack)-1]--
			}
			regexOK = true
			i++
		case c == ')' || c == ']':
			regexOK = false
			i++
		case c == ' ' || c == '\t' || c == '\n' || c == '\r':
			i++
		default:
			regexOK = true
			i++
		}
	}
	if len(stack) != 0 {
		return "", fmt.Errorf("unclosed template literal")
	}
	return string(out), nil
}

var (
	jsDecl    = regexp.MustCompile(`^(export\s+)?(?:async\s+)?(?:function\s*\*?\s*([A-Za-z_$][\w$]*)|(?:const|let|var|class)\s+([A-Za-z_$][\w$]*))`)
	jsDestr   = regexp.MustCompile(`^(export\s+)?(const|let|var)\s*[{\[]`)
	jsDefine  = regexp.MustCompile(`^(?:define|partDefaults)\("([a-z0-9-]+)"`)
	jsExports = regexp.MustCompile(`(?m)^export\s+(?:async\s+)?(?:function\s*\*?\s*|const\s+|let\s+|class\s+)([A-Za-z_$][\w$]*)`)
)

func jsIdentifiers(masked string) map[string]bool {
	ids := map[string]bool{}
	for i := 0; i < len(masked); {
		c := masked[i]
		if c >= '0' && c <= '9' {
			for i < len(masked) && (isIdentPart(masked[i]) || masked[i] == '.') {
				i++
			}
			continue
		}
		if !isIdentStart(c) {
			i++
			continue
		}
		j := i
		for j < len(masked) && isIdentPart(masked[j]) {
			j++
		}
		k := i - 1
		for k >= 0 && (masked[k] == ' ' || masked[k] == '\n') {
			k--
		}
		member := k >= 0 && masked[k] == '.' && !(k >= 2 && masked[k-1] == '.' && masked[k-2] == '.')
		if !member {
			ids[masked[i:j]] = true
		}
		i = j
	}
	return ids
}

func splitJS(src string) ([]jsStmt, error) {
	masked, err := maskJS(src)
	if err != nil {
		return nil, err
	}
	first := strings.IndexByte(src, '\n') + 1
	var starts []int
	depth := 0
	lineStart := true
	for i := 0; i < len(masked); i++ {
		c := masked[i]
		if lineStart && i >= first && depth == 0 && c != ' ' && c != '\n' && c != '\t' && c != '}' && c != ')' && c != ']' {
			starts = append(starts, i)
		}
		lineStart = c == '\n'
		switch c {
		case '(', '[', '{':
			depth++
		case ')', ']', '}':
			depth--
		}
	}
	if depth != 0 {
		return nil, fmt.Errorf("unbalanced brackets")
	}
	if len(starts) == 0 || starts[0] != first {
		return nil, fmt.Errorf("no statement after the license line")
	}
	var out []jsStmt
	for k, s := range starts {
		e := len(src)
		if k+1 < len(starts) {
			e = starts[k+1]
		}
		line := src[s:]
		if nl := strings.IndexByte(line, '\n'); nl >= 0 {
			line = line[:nl]
		}
		st := jsStmt{start: s, end: e, line: strings.Count(src[:s], "\n") + 1, ids: jsIdentifiers(masked[s:e])}
		if jsDestr.MatchString(line) {
			return nil, fmt.Errorf("line %d: a top-level destructuring declaration cannot be split", st.line)
		}
		if m := jsDecl.FindStringSubmatch(line); m != nil {
			st.exported = m[1] != ""
			st.name = m[2] + m[3]
		}
		if m := jsDefine.FindStringSubmatch(line); m != nil {
			st.slot = m[1]
		}
		out = append(out, st)
	}
	return out, nil
}

func (t *groupTable) assignJS(src string, stmts []jsStmt) error {
	anchor := -1
	for i, st := range stmts {
		if strings.TrimSpace(src[st.start:st.end]) == distAnchor {
			anchor = i
			break
		}
	}
	if anchor < 0 {
		return fmt.Errorf("no top-level %s line (the end of the core)", distAnchor)
	}
	prev := "core"
	for i := range stmts {
		st := &stmts[i]
		g := ""
		switch {
		case i <= anchor:
			g = "core"
		case st.slot != "":
			g = t.group[t.component(st.slot)]
			if g == "" {
				return fmt.Errorf("line %d: %w", st.line, noComponent(st.slot))
			}
		case st.name != "":
			var ok bool
			if g, ok = t.nameGroup(st.name); !ok {
				return fmt.Errorf("line %d: %s does not start with a component name; rename it or add a js: prefix to groups.tsv", st.line, st.name)
			}
		default:
			g = prev
		}
		if !slices.Contains(distJSGroups, g) {
			return fmt.Errorf("line %d: group %s has no JS file", st.line, g)
		}
		st.group = g
		prev = g
	}
	return nil
}

func (t *groupTable) distJS(res *distResult, src string) error {
	stmts, err := splitJS(src)
	if err != nil {
		return err
	}
	if err := t.assignJS(src, stmts); err != nil {
		return err
	}
	declared := map[string]string{}
	exported := map[string]bool{}
	for _, st := range stmts {
		if st.name == "" {
			continue
		}
		if _, dup := declared[st.name]; dup {
			return fmt.Errorf("line %d: %s is declared twice", st.line, st.name)
		}
		declared[st.name] = st.group
		exported[st.name] = st.exported
	}
	needs := map[string]map[string]bool{}
	var problems []string
	for _, st := range stmts {
		for id := range st.ids {
			g, ok := declared[id]
			if !ok || g == st.group {
				continue
			}
			if g != "core" {
				problems = append(problems, fmt.Sprintf("line %d (%s): %s uses %s from %s", st.line, st.group, label(st), id, g))
				continue
			}
			if needs[st.group] == nil {
				needs[st.group] = map[string]bool{}
			}
			needs[st.group][id] = true
		}
	}
	if len(problems) > 0 {
		slices.Sort(problems)
		return fmt.Errorf("a group uses code of another group; move the shared code into the core:\n  %s", strings.Join(problems, "\n  "))
	}
	internal := map[string]bool{}
	for _, set := range needs {
		for id := range set {
			if !exported[id] {
				internal[id] = true
			}
		}
	}
	res.js, res.stmts = src, stmts
	res.internal = slices.Sorted(maps.Keys(internal))
	lic, _, _ := strings.Cut(src, "\n")
	importLine := func(names []string) string {
		var parts []string
		for _, n := range names {
			if internal[n] {
				parts = append(parts, "_"+n+" as "+n)
			} else {
				parts = append(parts, n)
			}
		}
		return "import { " + strings.Join(parts, ", ") + ` } from "./` + distCore + `"` + "\n"
	}
	body := func(groups ...string) string {
		var b strings.Builder
		for _, st := range stmts {
			if slices.Contains(groups, st.group) {
				b.WriteString(src[st.start:st.end])
			}
		}
		return b.String()
	}
	emit := func(name, text string) error {
		min, err := minifyJS(text)
		if err != nil {
			return fmt.Errorf("%s: %w", name, err)
		}
		res.files[name] = []byte(lic + "\n" + min + "\n")
		return nil
	}
	core := body("core")
	if len(internal) > 0 {
		var parts []string
		for _, n := range res.internal {
			parts = append(parts, n+" as _"+n)
		}
		core += "export { " + strings.Join(parts, ", ") + " }\n"
	}
	if err := emit(distCore, core); err != nil {
		return err
	}
	all := map[string]bool{}
	for _, g := range distJSGroups[1:] {
		names := slices.Sorted(maps.Keys(needs[g]))
		res.imports[g] = names
		for _, n := range names {
			all[n] = true
		}
		if err := emit("clanker-ui-"+g+".min.js", importLine(names)+body(g)); err != nil {
			return err
		}
	}
	var public []string
	for _, st := range stmts {
		if st.group == "core" && st.exported {
			public = append(public, st.name)
			all[st.name] = true
		}
	}
	return emit(distAll, importLine(slices.Sorted(maps.Keys(all)))+"export { "+strings.Join(public, ", ")+" }\n"+body(distJSGroups[1:]...))
}

func label(st jsStmt) string {
	switch {
	case st.name != "":
		return st.name
	case st.slot != "":
		return `define("` + st.slot + `")`
	}
	return "statement"
}
