package main

import (
	"cmp"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"os"
	pathpkg "path"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
)

const (
	docsRoot      = "apps/v4/content/docs/"
	docsInventory = "tools/gen/docs-shadcn.tsv"
	docsMapFile   = "tools/gen/docs-map.tsv"
	docsInvHead   = "shadcn\ttitle\tstyle"
	docsMapHead   = "shadcn\tours\treason"
)

var docsDirs = []string{"components/base", "ai-elements/base", "utils", "forms", "dark-mode"}

var (
	demoSectionID = regexp.MustCompile(`<section id="([a-z0-9-]+)" data-demo="section">`)
	demoExample   = regexp.MustCompile(`^demo-([a-z0-9-]+)-[0-9]+$`)
	exampleID     = regexp.MustCompile(`^[a-z0-9]+(-[a-z0-9]+)*$`)
	mdxTitle      = regexp.MustCompile(`(?m)^title:\s*(.+?)\s*$`)
)

func docsFile(path string) bool {
	rest, ok := strings.CutPrefix(path, docsRoot)
	return ok && strings.HasSuffix(rest, ".mdx") && slices.Contains(docsDirs, pathpkg.Dir(rest))
}

func docsKey(path string) string {
	rest := strings.TrimSuffix(strings.TrimPrefix(path, docsRoot), ".mdx")
	dir, base := pathpkg.Split(rest)
	dir = strings.TrimSuffix(strings.TrimSuffix(dir, "/"), "/base")
	if base == "index" {
		return dir
	}
	return dir + "/" + base
}

type invItem struct {
	key, title, style string
}

func (it invItem) page() string {
	p, _, _ := strings.Cut(it.key, "#")
	return p
}

func (it invItem) isPage() bool {
	return !strings.Contains(it.key, "#")
}

type preview struct {
	name, style string
}

func previewAttrs(src string) (map[string]string, int) {
	attrs := map[string]string{}
	i := 0
	for i < len(src) {
		switch c := src[i]; {
		case c == ' ' || c == '\t' || c == '\n' || c == '\r':
			i++
		case strings.HasPrefix(src[i:], "/>"):
			return attrs, i + 2
		case c == '>':
			return attrs, i + 1
		default:
			j := i
			for j < len(src) && !strings.ContainsRune(" \t\r\n=/>", rune(src[j])) {
				j++
			}
			name := src[i:j]
			if j == i {
				return attrs, -1
			}
			i = j
			if i >= len(src) || src[i] != '=' {
				attrs[name] = "true"
				continue
			}
			i++
			if i >= len(src) {
				return attrs, -1
			}
			switch src[i] {
			case '"', '\'':
				end := strings.IndexByte(src[i+1:], src[i])
				if end < 0 {
					return attrs, -1
				}
				attrs[name] = src[i+1 : i+1+end]
				i += end + 2
			case '{':
				depth, k := 0, i
				for ; k < len(src); k++ {
					if src[k] == '{' {
						depth++
					} else if src[k] == '}' {
						if depth--; depth == 0 {
							break
						}
					}
				}
				if k >= len(src) {
					return attrs, -1
				}
				attrs[name] = src[i+1 : k]
				i = k + 1
			default:
				return attrs, -1
			}
		}
	}
	return attrs, -1
}

func parsePreviews(src string) ([]preview, error) {
	var out []preview
	var text strings.Builder
	fence := false
	for _, line := range strings.SplitAfter(strings.ReplaceAll(src, "\r\n", "\n"), "\n") {
		if strings.HasPrefix(strings.TrimSpace(line), "```") {
			fence = !fence
			text.WriteString("\n")
			continue
		}
		if fence {
			text.WriteString("\n")
		} else {
			text.WriteString(line)
		}
	}
	rest := text.String()
	for {
		i := strings.Index(rest, "<ComponentPreview")
		if i < 0 {
			return out, nil
		}
		rest = rest[i+len("<ComponentPreview"):]
		if rest == "" || !strings.ContainsRune(" \t\r\n/>", rune(rest[0])) {
			continue
		}
		attrs, n := previewAttrs(rest)
		if n < 0 {
			return nil, errors.New("ComponentPreview tag is not closed")
		}
		if attrs["name"] == "" {
			return nil, errors.New("ComponentPreview without a name")
		}
		out = append(out, preview{attrs["name"], attrs["styleName"]})
		rest = rest[n:]
	}
}

func buildInventory(files map[string]string) ([]invItem, error) {
	var paths []string
	for p := range files {
		if docsFile(p) {
			paths = append(paths, p)
		}
	}
	slices.SortFunc(paths, func(a, b string) int { return strings.Compare(docsKey(a), docsKey(b)) })
	var out []invItem
	for _, p := range paths {
		key := docsKey(p)
		title := ""
		if m := mdxTitle.FindStringSubmatch(files[p]); m != nil {
			title = strings.Trim(m[1], `"'`)
		}
		if title == "" || strings.ContainsAny(title, "\t\n") {
			return nil, fmt.Errorf("%s: no title", p)
		}
		out = append(out, invItem{key, title, "-"})
		previews, err := parsePreviews(files[p])
		if err != nil {
			return nil, fmt.Errorf("%s: %w", p, err)
		}
		seen := map[string]bool{}
		for _, pv := range previews {
			if seen[pv.name] {
				continue
			}
			seen[pv.name] = true
			if !exampleID.MatchString(pv.name) {
				return nil, fmt.Errorf("%s: example name %q", p, pv.name)
			}
			style := pv.style
			if style == "" {
				style = "-"
			}
			out = append(out, invItem{key + "#" + pv.name, "-", style})
		}
	}
	return out, nil
}

func formatInventory(items []invItem) string {
	var b strings.Builder
	b.WriteString(docsInvHead + "\n")
	for _, it := range items {
		fmt.Fprintf(&b, "%s\t%s\t%s\n", it.key, it.title, it.style)
	}
	return b.String()
}

func readTSV(path, head string, cols int) ([][]string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	lines := strings.Split(strings.TrimRight(string(raw), "\n"), "\n")
	if lines[0] != head {
		return nil, fmt.Errorf("%s: first line must be %q", path, head)
	}
	var out [][]string
	for i, line := range lines[1:] {
		f := strings.Split(line, "\t")
		if len(f) < cols-1 || len(f) > cols || f[0] == "" {
			return nil, fmt.Errorf("%s:%d: want %d tab-separated columns", path, i+2, cols)
		}
		for len(f) < cols {
			f = append(f, "")
		}
		out = append(out, f)
	}
	return out, nil
}

func readInventory(root string) ([]invItem, error) {
	rows, err := readTSV(filepath.Join(root, docsInventory), docsInvHead, 3)
	if err != nil {
		return nil, err
	}
	var out []invItem
	for _, r := range rows {
		out = append(out, invItem{r[0], r[1], r[2]})
	}
	return out, nil
}

type mapRow struct {
	key, ours, reason string
}

func readDocsMap(root string) ([]mapRow, error) {
	rows, err := readTSV(filepath.Join(root, docsMapFile), docsMapHead, 3)
	if err != nil {
		return nil, err
	}
	var out []mapRow
	for _, r := range rows {
		out = append(out, mapRow{r[0], r[1], r[2]})
	}
	return out, nil
}

func formatDocsMap(rows []mapRow) string {
	var b strings.Builder
	b.WriteString(docsMapHead + "\n")
	for _, r := range rows {
		if r.reason == "" {
			fmt.Fprintf(&b, "%s\t%s\n", r.key, r.ours)
		} else {
			fmt.Fprintf(&b, "%s\t%s\t%s\n", r.key, r.ours, r.reason)
		}
	}
	return b.String()
}

type oursSide struct {
	hrefs    map[string]bool
	examples map[string]bool
	sections map[string]bool
	styles   map[string]string
}

func loadOurs(root string) (*oursSide, error) {
	o := &oursSide{hrefs: map[string]bool{}, examples: map[string]bool{}, sections: map[string]bool{}, styles: map[string]string{}}
	raw, err := os.ReadFile(filepath.Join(root, "docs/nav.json"))
	if err != nil {
		return nil, err
	}
	var nav struct {
		Header, Sections, MobileSections []struct{ Href string }
		Groups                           []struct {
			Items []struct{ Href, Style string }
		}
	}
	if err := json.Unmarshal(raw, &nav); err != nil {
		return nil, fmt.Errorf("docs/nav.json: %w", err)
	}
	for _, l := range slices.Concat(nav.Header, nav.Sections, nav.MobileSections) {
		o.hrefs[l.Href] = true
	}
	for _, g := range nav.Groups {
		for _, it := range g.Items {
			o.hrefs[it.Href] = true
			if it.Style != "" {
				o.styles[it.Href] = it.Style
			}
		}
	}
	err = filepath.WalkDir(filepath.Join(root, "docs/content"), func(p string, e fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !e.IsDir() && filepath.Base(filepath.Dir(p)) == "examples" && filepath.Ext(p) == ".html" {
			o.examples[strings.TrimSuffix(e.Name(), ".html")] = true
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	demo, err := os.ReadFile(filepath.Join(root, "demo/index.html"))
	if err != nil {
		return nil, err
	}
	for _, m := range demoSectionID.FindAllStringSubmatch(string(demo), -1) {
		o.sections[m[1]] = true
	}
	return o, nil
}

func (o *oursSide) hasExample(name string) bool {
	if o.examples[name] {
		return true
	}
	m := demoExample.FindStringSubmatch(name)
	return m != nil && o.sections[m[1]]
}

func checkDocsMap(inv []invItem, rows []mapRow, o *oursSide) []string {
	var bad []string
	byKey := map[string]mapRow{}
	for i, r := range rows {
		if _, dup := byKey[r.key]; dup {
			bad = append(bad, fmt.Sprintf("%s:%d: %s twice", docsMapFile, i+2, r.key))
		}
		byKey[r.key] = r
	}
	known := map[string]bool{}
	pageOurs := map[string]string{}
	for _, it := range inv {
		known[it.key] = true
		r, ok := byKey[it.key]
		if !ok {
			bad = append(bad, fmt.Sprintf("%s: no row for %s (go run ./tools/gen docs-coverage -src DIR -write adds it)", docsMapFile, it.key))
			continue
		}
		switch {
		case r.ours == "?":
			bad = append(bad, fmt.Sprintf("%s: %s needs a review (our page or example, or - with a reason)", docsMapFile, it.key))
		case r.ours == "-":
			if strings.TrimSpace(r.reason) == "" {
				bad = append(bad, fmt.Sprintf("%s: %s is - without a reason", docsMapFile, it.key))
			}
		case it.isPage():
			if !o.hrefs[r.ours] {
				bad = append(bad, fmt.Sprintf("%s: %s maps to %s, which is not in docs/nav.json", docsMapFile, it.key, r.ours))
			}
		case pageOurs[it.page()] == "-":
			bad = append(bad, fmt.Sprintf("%s: %s maps to %s, but its page maps to -", docsMapFile, it.key, r.ours))
		case !o.hasExample(r.ours):
			bad = append(bad, fmt.Sprintf("%s: %s maps to %s, which is not an example in docs/content or demo/index.html", docsMapFile, it.key, r.ours))
		}
		if it.isPage() {
			pageOurs[it.key] = r.ours
		}
	}
	for _, r := range rows {
		if !known[r.key] {
			bad = append(bad, fmt.Sprintf("%s: %s is not in %s (shadcn removed it?)", docsMapFile, r.key, docsInventory))
		}
	}
	if len(bad) == 0 && len(rows) == len(inv) {
		for i, r := range rows {
			if r.key != inv[i].key {
				bad = append(bad, fmt.Sprintf("%s:%d: %s; rows follow the order of %s, want %s here", docsMapFile, i+2, r.key, docsInventory, inv[i].key))
				break
			}
		}
	}
	return bad
}

func syncDocsMap(inv []invItem, rows []mapRow) []mapRow {
	byKey := map[string]mapRow{}
	for _, r := range rows {
		byKey[r.key] = r
	}
	var out []mapRow
	for _, it := range inv {
		r, ok := byKey[it.key]
		if !ok {
			r = mapRow{key: it.key, ours: "?"}
		}
		out = append(out, r)
	}
	return out
}

func docsReport(inv []invItem, rows []mapRow, styleOf map[string]string, verbose bool) string {
	byKey := map[string]mapRow{}
	for _, r := range rows {
		byKey[r.key] = r
	}
	type count struct{ pages, pagesOK, ex, exOK, shared int }
	var order []string
	totals := map[string]*count{}
	used := map[string]int{}
	for _, it := range inv {
		if r := byKey[it.key]; !it.isPage() && r.ours != "-" && r.ours != "?" && r.ours != "" {
			used[it.page()+" "+r.ours]++
		}
	}
	var gaps, styles []string
	for _, it := range inv {
		sec, _, _ := strings.Cut(it.key, "/")
		sec, _, _ = strings.Cut(sec, "#")
		c := totals[sec]
		if c == nil {
			c = &count{}
			totals[sec] = c
			order = append(order, sec)
		}
		r := byKey[it.key]
		ok := r.ours != "" && r.ours != "-" && r.ours != "?"
		if it.isPage() {
			c.pages++
			if ok {
				c.pagesOK++
			}
		} else {
			c.ex++
			if ok {
				c.exOK++
				if used[it.page()+" "+r.ours] > 1 {
					c.shared++
				}
			}
			if ours := "base-" + cmp.Or(styleOf[byKey[it.page()].ours], "nova"); ok && it.style != ours {
				styles = append(styles, fmt.Sprintf("  %s %s, ours %s", it.key, it.style, ours))
			}
		}
		if !ok {
			gaps = append(gaps, fmt.Sprintf("  %s %s %s", it.key, r.ours, r.reason))
		}
	}
	var b strings.Builder
	fmt.Fprintf(&b, "docs coverage at shadcn %s\n", shadcnSHA[:12])
	all := &count{}
	for _, sec := range order {
		c := totals[sec]
		fmt.Fprintf(&b, "%-12s pages %3d/%-3d examples %3d/%-3d shared %d\n", sec, c.pagesOK, c.pages, c.exOK, c.ex, c.shared)
		all.pages, all.pagesOK, all.ex, all.exOK, all.shared = all.pages+c.pages, all.pagesOK+c.pagesOK, all.ex+c.ex, all.exOK+c.exOK, all.shared+c.shared
	}
	fmt.Fprintf(&b, "%-12s pages %3d/%-3d examples %3d/%-3d shared %d\n", "total", all.pagesOK, all.pages, all.exOK, all.ex, all.shared)
	fmt.Fprintf(&b, "examples in another style than our page: %d\n%s", len(styles), strings.Join(append(styles, ""), "\n"))
	if verbose {
		fmt.Fprintf(&b, "items without a match: %d\n%s", len(gaps), strings.Join(append(gaps, ""), "\n"))
	}
	return b.String()
}

func docsCoverageMain(args []string) error {
	fset := flag.NewFlagSet("docs-coverage", flag.ExitOnError)
	root := fset.String("root", ".", "repository root")
	src := fset.String("src", "", "directory with the pinned inputs: check "+docsInventory+" against the shadcn docs")
	pin := fset.String("pin", "tools/gen/pin.tsv", "git blob hashes of the pinned inputs")
	write := fset.Bool("write", false, "with -src: write "+docsInventory+" and add a ? row to "+docsMapFile+" for each new item")
	verbose := fset.Bool("v", false, "list the items without a match")
	fset.Parse(args)
	inv, err := readInventory(*root)
	if err != nil && (*src == "" || !errors.Is(err, os.ErrNotExist)) {
		return err
	}
	if *src != "" {
		p, err := loadPinned(*src, *pin)
		if err != nil {
			return err
		}
		fresh, err := buildInventory(p.files)
		if err != nil {
			return err
		}
		if *write {
			if err := os.WriteFile(filepath.Join(*root, docsInventory), []byte(formatInventory(fresh)), 0o644); err != nil {
				return err
			}
			rows, err := readDocsMap(*root)
			if errors.Is(err, os.ErrNotExist) {
				err = nil
			}
			if err != nil {
				return err
			}
			if err := os.WriteFile(filepath.Join(*root, docsMapFile), []byte(formatDocsMap(syncDocsMap(fresh, rows))), 0o644); err != nil {
				return err
			}
		} else if formatInventory(fresh) != formatInventory(inv) {
			return fmt.Errorf("%s is not the shadcn docs at %s; run go run ./tools/gen docs-coverage -src DIR -write and review %s", docsInventory, shadcnSHA[:12], docsMapFile)
		}
		inv = fresh
	}
	rows, err := readDocsMap(*root)
	if err != nil {
		return err
	}
	o, err := loadOurs(*root)
	if err != nil {
		return err
	}
	fmt.Print(docsReport(inv, rows, o.styles, *verbose))
	if bad := checkDocsMap(inv, rows, o); len(bad) > 0 {
		return errors.New(strings.Join(bad, "\n"))
	}
	return nil
}
