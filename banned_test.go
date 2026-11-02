package main

import (
	"fmt"
	"go/parser"
	"go/token"
	"html"
	"maps"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"testing"
)

const licenseLine = "/*! clanker-ui | MIT | includes shadcn/ui (MIT, shadcn) and Lucide icons (ISC); see THIRD_PARTY_NOTICES */"

const generatedLicenseLine = "/*! clanker-ui | MIT | includes shadcn/ui (MIT, shadcn), Tailwind CSS (MIT, Tailwind Labs), tw-animate-css (MIT, Luca Bosin), and Lucide icons (ISC); see THIRD_PARTY_NOTICES */"

func htmlScanFiles(t *testing.T) []string {
	return slices.Concat(repoFiles(t, "demo/*.html", "test/spike/*.html", "test/behavior/fixtures/*.html", "test/split/*.html"), walkFiles(t, "docs", ".html"))
}

func cssScanFiles(t *testing.T) []string {
	return slices.Concat(repoFiles(t, "clanker-ui*.css", "dist/clanker-ui*.css", "demo/*.css", "test/spike/*.css", "tools/gen/*.css", "tools/gen/out/*.css", "test/behavior/fixtures/*.css"), walkFiles(t, "docs", ".css"))
}

func generatedCSS(t *testing.T) []string {
	return repoFiles(t, "tools/gen/out/*.css")
}

func plainCommentFiles(t *testing.T) []string {
	return slices.Concat(repoFiles(t, "demo/*.js", "demo/*.css", "test/*.py", "test/spike/*.css", "tools/gen/*.css", "tools/parity/*.py", "tools/parity/*.js", "tools/behavior/*.py", "test/behavior/fixtures/*.css", "test/behavior/fixtures/*.js", "test/split/*.js"), walkFiles(t, "docs", ".js", ".css"))
}

func TestScannedFiles(t *testing.T) {
	for name, files := range map[string][]string{
		"html security": htmlScanFiles(t),
		"remote css":    cssScanFiles(t),
		"generated css": generatedCSS(t),
		"no comments":   plainCommentFiles(t),
	} {
		want := map[string][]string{
			"html security": {"test/spike/index.html"},
			"remote css":    {"test/spike/page.css", "tools/gen/out/clanker-ui.generated.css", "tools/gen/out/spike.css"},
			"generated css": {"tools/gen/out/clanker-ui.generated.css", "tools/gen/out/spike.css"},
			"no comments":   {"test/spike/page.css", "tools/parity/parity.py", "tools/parity/parity.js"},
		}[name]
		for _, f := range want {
			if !slices.Contains(files, f) {
				t.Errorf("%s scan does not read %s", name, f)
			}
		}
	}
}

var fileLicenseLines = map[string]string{
	"clanker-ui.css":        "/*! clanker-ui | MIT | includes shadcn/ui (MIT, shadcn), Tailwind CSS (MIT, Tailwind Labs), tw-animate-css (MIT, Luca Bosin), and Lucide icons (ISC); see THIRD_PARTY_NOTICES */",
	"clanker-ui-themes.css": "/*! clanker-ui | MIT | includes shadcn/ui (MIT, shadcn) and editor palettes (MIT; Tokyo Night Apache-2.0); see THIRD_PARTY_NOTICES */",
	"clanker-ui.js":         "/*! clanker-ui | MIT | includes shadcn/ui (MIT, shadcn), Base UI (MIT, Material-UI SAS), Embla Carousel (MIT, David Jerleke), and Lucide icons (ISC); see THIRD_PARTY_NOTICES */",
}

func kitLicense(name string) string {
	base := filepath.Base(name)
	if strings.HasPrefix(filepath.ToSlash(name), "dist/") {
		switch base = strings.Replace(base, ".min.", ".", 1); {
		case base == "clanker-ui-themes.css" || base == "clanker-ui-a11y.css":
		case strings.HasSuffix(base, ".css"):
			base = "clanker-ui.css"
		case base != "clanker-ui-chart.js":
			base = "clanker-ui.js"
		}
	}
	if line, ok := fileLicenseLines[base]; ok {
		return line
	}
	return licenseLine
}

func TestKitLicense(t *testing.T) {
	for name, want := range map[string]string{
		"clanker-ui.css":                 generatedLicenseLine,
		"clanker-ui.js":                  fileLicenseLines["clanker-ui.js"],
		"dist/clanker-ui.min.css":        generatedLicenseLine,
		"dist/clanker-ui-forms.min.css":  generatedLicenseLine,
		"dist/clanker-ui-themes.min.css": fileLicenseLines["clanker-ui-themes.css"],
		"dist/clanker-ui-a11y.min.css":   licenseLine,
		"dist/clanker-ui-core.min.js":    fileLicenseLines["clanker-ui.js"],
		"dist/clanker-ui-chart.min.js":   licenseLine,
	} {
		if got := kitLicense(name); got != want {
			t.Errorf("%s: license %q, want %q", name, got, want)
		}
	}
}

var bannedJS = map[string]*regexp.Regexp{
	"innerHTML":                regexp.MustCompile(`\binnerHTML\b`),
	"outerHTML":                regexp.MustCompile(`\bouterHTML\b`),
	"insertAdjacentHTML":       regexp.MustCompile(`\binsertAdjacentHTML\b`),
	"document.write":           regexp.MustCompile(`\bdocument\s*\.\s*write(ln)?\b`),
	"eval":                     regexp.MustCompile(`\beval\s*\(`),
	"Function constructor":     regexp.MustCompile(`(^|[^.\w$])(new\s+)?Function\s*\(`),
	"global Function":          regexp.MustCompile(`\b(window|globalThis|self|top|parent|frames)\s*\.\s*Function\b`),
	"string timer":             regexp.MustCompile("\\bset(Timeout|Interval)\\s*\\(\\s*[\"'`]"),
	"createContextualFragment": regexp.MustCompile(`\bcreateContextualFragment\b`),
	"DOMParser":                regexp.MustCompile(`\b(DOMParser|parseFromString)\b`),
	"setHTML":                  regexp.MustCompile(`\bsetHTML(Unsafe)?\s*\(`),
	"parseHTMLUnsafe":          regexp.MustCompile(`\bparseHTMLUnsafe\b`),
	"srcdoc property":          regexp.MustCompile(`\.\s*srcdoc\b`),
	"javascript URL":           regexp.MustCompile(`(?i)javascript:`),
	"style attribute":          regexp.MustCompile(`(?i)setAttribute\s*\(\s*["'\x60]style["'\x60]`),
	"srcdoc or handler attr":   regexp.MustCompile(`(?i)setAttribute\s*\(\s*["'\x60](srcdoc|on[a-z]*)["'\x60]`),
	"setAttributeNS":           regexp.MustCompile(`(?i)setAttributeNS\s*\([^,()]*,\s*["'\x60](style|srcdoc|on[a-z]*)["'\x60]`),
	"script or style element":  regexp.MustCompile(`(?i)createElement(NS)?\s*\(\s*([^,()]*,\s*)?["'\x60](style|script)["'\x60]`),
	"dynamic import":           regexp.MustCompile(`(^|[^.\w$])import\s*\(`),
	"execScript":               regexp.MustCompile(`\bexecScript\b`),
	"execCommand":              regexp.MustCompile(`\bexecCommand\b`),
}

var (
	timerCall    = regexp.MustCompile(`\bset(Timeout|Interval)\s*\(\s*`)
	inlineFunc   = regexp.MustCompile(`^(async\s+)?(function\b|\([^()]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)`)
	timerIdent   = regexp.MustCompile(`^([A-Za-z_$][\w$]*)\s*[,)]`)
	externalTags = map[string]bool{"script": true, "link": true, "img": true, "iframe": true, "source": true, "video": true, "audio": true, "embed": true, "object": true, "track": true, "input": true}
	urlAttrs     = map[string]bool{"src": true, "href": true, "data": true, "srcset": true, "poster": true}
	cssImport    = regexp.MustCompile(`(?i)@import\b`)
	cssRemote    = regexp.MustCompile(`(?i)url\(\s*["']?(https?:)?//`)
	cssLegacy    = regexp.MustCompile(`(?i)(expression\s*\(|-moz-binding|(^|[\s;{])behavior\s*:)`)
)

func repoFiles(t *testing.T, patterns ...string) []string {
	t.Helper()
	var out []string
	for _, p := range patterns {
		m, err := filepath.Glob(p)
		if err != nil {
			t.Fatal(err)
		}
		out = append(out, m...)
	}
	slices.Sort(out)
	return slices.Compact(out)
}

func walkFiles(t *testing.T, root string, exts ...string) []string {
	t.Helper()
	var out []string
	err := filepath.WalkDir(root, func(name string, d os.DirEntry, err error) error {
		if err == nil && !d.IsDir() && slices.Contains(exts, filepath.Ext(name)) {
			out = append(out, name)
		}
		return err
	})
	if err != nil {
		t.Fatal(err)
	}
	slices.Sort(out)
	return out
}

func readText(t *testing.T, name string) string {
	t.Helper()
	b, err := os.ReadFile(name)
	if err != nil {
		t.Fatal(err)
	}
	return string(b)
}

func lineOf(src string, offset int) int {
	return strings.Count(src[:offset], "\n") + 1
}

type finding struct {
	offset int
	name   string
}

func bannedJSUses(src string) []finding {
	var out []finding
	for name, re := range bannedJS {
		for _, loc := range re.FindAllStringIndex(src, -1) {
			out = append(out, finding{loc[0], name})
		}
	}
	for _, loc := range timerCall.FindAllStringIndex(src, -1) {
		if !timerTakesFunction(src, src[loc[1]:]) {
			out = append(out, finding{loc[0], "timer without a function"})
		}
	}
	slices.SortFunc(out, func(a, b finding) int { return a.offset - b.offset })
	return out
}

func timerTakesFunction(src, arg string) bool {
	if inlineFunc.MatchString(arg) {
		return true
	}
	m := timerIdent.FindStringSubmatch(arg)
	if m == nil {
		return false
	}
	id := regexp.QuoteMeta(m[1])
	return regexp.MustCompile(`\bfunction\s+` + id + `\s*\(|\b(const|let|var)\s+` + id + `\s*=\s*(async\s+)?(function\b|\([^()]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)`).MatchString(src)
}

func TestNoBannedAPIs(t *testing.T) {
	files := slices.Concat(repoFiles(t, "clanker-ui*.js", "dist/clanker-ui*.js", "demo/*.js", "test/behavior/fixtures/*.js", "test/split/*.js"), walkFiles(t, "docs", ".js"))
	if !slices.Contains(files, filepath.Join("docs", "assets", "docs.js")) || !slices.Contains(files, filepath.Join("test", "behavior", "fixtures", "toast.js")) {
		t.Fatal("docs JavaScript is not scanned")
	}
	for _, f := range files {
		src := readText(t, f)
		for _, u := range bannedJSUses(src) {
			t.Errorf("%s:%d uses %s", f, lineOf(src, u.offset), u.name)
		}
	}
}

func TestBannedJSPatterns(t *testing.T) {
	banned := []string{
		`el.setAttribute("srcdoc", s)`,
		`el.setAttribute("onclick", "alert(1)")`,
		`el.setAttribute('OnLoad', f)`,
		`el.setAttribute('style', x)`,
		`el.setAttributeNS(null, "style", "color:red")`,
		`el.setAttributeNS(ns, "onclick", s)`,
		`document.createElement("style").textContent = css`,
		`document.createElement('script').src = url`,
		`document.createElementNS(svgNS, "script")`,
		`new (window.Function)("x")`,
		`window.Function("x")`,
		`globalThis.Function("x")`,
		`el.setHTMLUnsafe(s)`,
		`Document.parseHTMLUnsafe(s)`,
		`setTimeout("x()", 1)`,
		`const later = "alert(1)"; setTimeout(later)`,
		`setTimeout(String(x))`,
		`window.setInterval(code, 100)`,
		`new Function("x")`,
		`eval(s)`,
	}
	for _, s := range banned {
		if len(bannedJSUses(s)) == 0 {
			t.Errorf("not caught: %s", s)
		}
	}
	allowed := []string{
		`setTimeout(() => x(), 10)`,
		`const tick = () => {}; setTimeout(tick, 28)`,
		`function open() {}; state.timer = setTimeout(open, 200)`,
		`setTimeout(function () {}, 1)`,
		`setTimeout(async () => { await x() })`,
		`setTimeout(v => v, 1)`,
		`obj.Function(x)`,
		`myFunction(x)`,
		`el.setAttribute("aria-label", s)`,
		`el.setAttributeNS(xlink, "href", "#a")`,
		`document.createElement("canvas")`,
		`const styleSheet = h("div")`,
	}
	for _, s := range allowed {
		if u := bannedJSUses(s); len(u) != 0 {
			t.Errorf("false positive %v: %s", u, s)
		}
	}
}

type htmlAttr struct {
	name, value string
}

type htmlTag struct {
	name   string
	offset int
	attrs  []htmlAttr
	body   string
}

func isSpace(c byte) bool {
	return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f'
}

func isLetter(c byte) bool {
	return c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z'
}

func scanHTML(src string) (tags []htmlTag, comments []int) {
	i := 0
	for i < len(src) {
		lt := strings.IndexByte(src[i:], '<')
		if lt < 0 {
			break
		}
		i += lt
		if strings.HasPrefix(src[i:], "<!--") {
			comments = append(comments, i)
			end := strings.Index(src[i+4:], "-->")
			if end < 0 {
				break
			}
			i += end + 7
			continue
		}
		if i+1 >= len(src) || !isLetter(src[i+1]) {
			if i+1 < len(src) && strings.IndexByte("!?/", src[i+1]) >= 0 {
				if end := strings.IndexByte(src[i:], '>'); end >= 0 {
					i += end + 1
					continue
				}
			}
			i++
			continue
		}
		tag := htmlTag{offset: i}
		j := i + 1
		for j < len(src) && !isSpace(src[j]) && src[j] != '>' && src[j] != '/' {
			j++
		}
		tag.name = strings.ToLower(src[i+1 : j])
		i = j
		for i < len(src) {
			for i < len(src) && (isSpace(src[i]) || src[i] == '/') {
				i++
			}
			if i >= len(src) || src[i] == '>' {
				i++
				break
			}
			k := i + 1
			for k < len(src) && !isSpace(src[k]) && src[k] != '>' && src[k] != '/' && src[k] != '=' {
				k++
			}
			attr := htmlAttr{name: strings.ToLower(src[i:k])}
			i = k
			for i < len(src) && isSpace(src[i]) {
				i++
			}
			if i < len(src) && src[i] == '=' {
				i++
				for i < len(src) && isSpace(src[i]) {
					i++
				}
				if i < len(src) && (src[i] == '"' || src[i] == '\'') {
					end := strings.IndexByte(src[i+1:], src[i])
					if end < 0 {
						end = len(src) - i - 1
					}
					attr.value = src[i+1 : i+1+end]
					i += end + 2
				} else {
					k = i
					for k < len(src) && !isSpace(src[k]) && src[k] != '>' {
						k++
					}
					attr.value = src[i:k]
					i = k
				}
			}
			tag.attrs = append(tag.attrs, attr)
		}
		if tag.name == "script" || tag.name == "style" {
			i = min(i, len(src))
			end := strings.Index(strings.ToLower(src[i:]), "</"+tag.name)
			if end < 0 {
				end = len(src) - i
			}
			tag.body = src[i : i+end]
			i += end
		}
		tags = append(tags, tag)
	}
	return tags, comments
}

func htmlProblems(src string) []finding {
	var out []finding
	tags, comments := scanHTML(src)
	for _, c := range comments {
		out = append(out, finding{c, "HTML comment"})
	}
	for _, tag := range tags {
		add := func(name string) { out = append(out, finding{tag.offset, name}) }
		hasSrc := false
		for _, a := range tag.attrs {
			value := strings.Map(func(r rune) rune {
				if r <= ' ' {
					return -1
				}
				return r
			}, strings.ToLower(html.UnescapeString(a.value)))
			switch {
			case a.name == "style":
				add("style attribute")
			case a.name == "srcdoc":
				add("srcdoc")
			case len(a.name) > 2 && strings.HasPrefix(a.name, "on"):
				add("inline event handler")
			}
			if strings.Contains(value, "javascript:") || strings.Contains(value, "vbscript:") {
				add("javascript: URL")
			}
			if externalTags[tag.name] && urlAttrs[a.name] && (strings.HasPrefix(value, "//") || strings.HasPrefix(value, "http:") || strings.HasPrefix(value, "https:") || strings.Contains(value, ",//") || strings.Contains(value, "http://") || strings.Contains(value, "https://")) {
				add("external resource")
			}
			hasSrc = hasSrc || a.name == "src"
		}
		switch {
		case tag.name == "style":
			add("<style> element")
		case tag.name == "script" && (!hasSrc || strings.TrimSpace(tag.body) != ""):
			add("inline script")
		}
	}
	slices.SortStableFunc(out, func(a, b finding) int { return a.offset - b.offset })
	return out
}

func TestNoInlineScriptOrStyleInHTML(t *testing.T) {
	files := htmlScanFiles(t)
	if len(files) < 10 || !slices.Contains(files, filepath.Join("test", "behavior", "fixtures", "index.html")) {
		t.Fatalf("only %d HTML files scanned", len(files))
	}
	for _, f := range files {
		src := readText(t, f)
		for _, p := range htmlProblems(src) {
			t.Errorf("%s:%d: %s is not allowed", f, lineOf(src, p.offset), p.name)
		}
	}
}

func TestHTMLScanner(t *testing.T) {
	src := "<!doctype html>\n" +
		`<a title="x>y" onclick="z">a</a>` + "\n" +
		`<div data-x='a>b' data-y=c style=color:red></div><b data-z=c>d style=x</b>` + "\n" +
		`<p class=a data-note="style=x onclick=y">b</p>` + "\n" +
		`<img alt=">" src=//evil.example/x.png>` + "\n" +
		`<script src="a.js">alert(1)</script>` + "\n" +
		`<a href=" JaVaScRiPt:alert(1)">x</a>` + "\n" +
		`<a href="&#106;avascript:x">y</a>` + "\n" +
		`<iframe title="a" srcdoc="<b>x</b>"></iframe>` + "\n" +
		"<style>p{}</style>\n" +
		"<script src=\"b.js\"></script>\n" +
		"<!-- c -->\n" +
		`<input value='>' ONMOUSEOVER=x>` + "\n"
	var got []string
	for _, p := range htmlProblems(src) {
		got = append(got, fmt.Sprintf("%d:%s", lineOf(src, p.offset), p.name))
	}
	want := []string{"2:inline event handler", "3:style attribute", "5:external resource", "6:inline script", "7:javascript: URL", "8:javascript: URL", "9:srcdoc", "10:<style> element", "12:HTML comment", "13:inline event handler"}
	if !slices.Equal(got, want) {
		t.Errorf("scanner found\n%v\nwant\n%v", got, want)
	}
}

func TestLicenseNotices(t *testing.T) {
	license := readText(t, "LICENSE")
	if !strings.HasPrefix(license, "MIT License\n\nCopyright (c) 2026 bl4ko\n\n") {
		t.Error("LICENSE must start with the MIT title and the line Copyright (c) 2026 bl4ko")
	}
	if n := strings.Count(license, "Copyright"); n != 1 {
		t.Errorf("LICENSE has %d copyright lines, want 1; third-party texts go to THIRD_PARTY_NOTICES", n)
	}
	text := readText(t, "THIRD_PARTY_NOTICES")
	for _, want := range []string{
		"Copyright (c) 2023 shadcn",
		"Copyright (c) 2019 Material-UI SAS",
		"Copyright (c) David Jerleke.",
		"Copyright (c) Tailwind Labs, Inc.",
		"tw-animate-css 1.4.0 (https://github.com/Wombosvideo/tw-animate-css) by Luca Bosin",
		"Copyright (c) 2025 Wombosvideo",
		"Copyright (c) 2026 Lucide Icons and Contributors",
		"Copyright (c) 2013-present Cole Bemis",
		"Copyright (c) 2021 Catppuccin.",
		"Copyright (c) 2018 Pavel Pertsev.",
		"Copyright (c) 2016-present Sven Greb",
		"Copyright (c) 2023 Dracula Theme.",
		"Copyright (c) mvllow.",
		"Copyright (c) 2011 Ethan Schoonover.",
		"Copyright (c) 2011-2022 GitHub Inc.",
		"Copyright (c) 2021 Tommaso Laurenzi.",
		"Copyright (c) 2019 sainnhe.",
		"Copyright (c) 2018 GitHub Inc.",
		"Apache License\n                           Version 2.0, January 2004",
		"Copyright (c) 2014-2026 Giampaolo Bellavite",
		"Copyright (c) 2022 Paco Coursey",
		"Copyright (c) 2021 Floating UI contributors",
		"Copyright (c) 2023 Emil Kowalski",
		"Copyright (c) 2024 Guilherme Rodz",
		"Copyright (c) 2018 Brian Vaughn",
		"Copyright (c) 2022 WorkOS",
		"Copyright (c) 2015-present recharts",
		"Copyright (c) 2021 Sasha Koss and Lesha Koss",
		"Copyright (c) 2025 Ronan Berder",
	} {
		if !strings.Contains(text, want) {
			t.Errorf("THIRD_PARTY_NOTICES has no %q", want)
		}
	}
	if n := strings.Count(text, "Permission is hereby granted"); n < 16 {
		t.Errorf("THIRD_PARTY_NOTICES has %d MIT texts, want at least 16", n)
	}
	for _, line := range slices.Concat([]string{licenseLine, generatedLicenseLine}, slices.Collect(maps.Values(fileLicenseLines))) {
		if !strings.HasSuffix(line, "; see THIRD_PARTY_NOTICES */") {
			t.Errorf("license line %q does not name THIRD_PARTY_NOTICES", line)
		}
	}
	for _, name := range []string{"shadcn/ui (MIT, shadcn)", "Tailwind CSS (MIT, Tailwind Labs)", "tw-animate-css (MIT, Luca Bosin)", "Lucide icons (ISC)"} {
		if !strings.Contains(generatedLicenseLine, name) {
			t.Errorf("generated license line does not name %s", name)
		}
	}
	for _, name := range []string{"Base UI (MIT, Material-UI SAS)", "Embla Carousel (MIT, David Jerleke)"} {
		if !strings.Contains(fileLicenseLines["clanker-ui.js"], name) {
			t.Errorf("clanker-ui.js license line does not name %s", name)
		}
	}
}

func TestNoRemoteOrLegacyCSS(t *testing.T) {
	for _, f := range cssScanFiles(t) {
		src := readText(t, f)
		for name, re := range map[string]*regexp.Regexp{"@import": cssImport, "remote url()": cssRemote, "legacy script hook": cssLegacy} {
			for _, loc := range re.FindAllStringIndex(src, -1) {
				t.Errorf("%s:%d uses %s", f, lineOf(src, loc[0]), name)
			}
		}
	}
}

func TestCommentRules(t *testing.T) {
	kit := repoFiles(t, "clanker-ui*.css", "clanker-ui*.js", "dist/clanker-ui*.css", "dist/clanker-ui*.js")
	for _, f := range kit {
		src := readText(t, f)
		first, rest, _ := strings.Cut(src, "\n")
		want := kitLicense(f)
		if first != want {
			t.Errorf("%s: first line must be the license line %q", f, want)
		}
		for _, line := range comments(f, "\n"+rest) {
			t.Errorf("%s:%d has a comment; only the first-line license is allowed", f, line)
		}
	}
	for _, f := range generatedCSS(t) {
		src := readText(t, f)
		first, rest, _ := strings.Cut(src, "\n")
		if first != generatedLicenseLine {
			t.Errorf("%s: first line must be the license line %q", f, generatedLicenseLine)
		}
		for _, line := range comments(f, "\n"+rest) {
			t.Errorf("%s:%d has a comment; only the first-line license is allowed", f, line)
		}
	}
	for _, f := range plainCommentFiles(t) {
		if slices.Contains(kit, f) {
			continue
		}
		for _, line := range comments(f, readText(t, f)) {
			t.Errorf("%s:%d has a comment", f, line)
		}
	}
	for _, f := range walkFiles(t, "docs", ".html", ".md") {
		src := readText(t, f)
		for _, marker := range []string{"<!--", "{{/*", "{{- /*"} {
			if i := strings.Index(src, marker); i >= 0 {
				t.Errorf("%s:%d has a comment", f, lineOf(src, i))
			}
		}
	}
	for _, f := range repoFiles(t, "*.go", "tools/gen/*.go") {
		file, err := parser.ParseFile(token.NewFileSet(), f, nil, parser.ParseComments)
		if err != nil {
			t.Fatal(err)
		}
		for _, g := range file.Comments {
			for _, c := range g.List {
				if !strings.HasPrefix(c.Text, "//go:") {
					t.Errorf("%s has a comment: %s", f, c.Text)
				}
			}
		}
	}
	for _, f := range repoFiles(t, ".gitignore") {
		for i, line := range strings.Split(readText(t, f), "\n") {
			if strings.HasPrefix(strings.TrimSpace(line), "#") {
				t.Errorf("%s:%d has a comment", f, i+1)
			}
		}
	}
}

func TestCommentScanner(t *testing.T) {
	js := "const a = \"// no\"\nconst b = 'it''s'\nconst re = /\\/\\*[/]x/g\nconst t = `${a /* in */}`\nconst d = a / 2 / 3\n// yes\nx = `a${`b${c}`}` /* yes */\n"
	if got := jsComments(js); !slices.Equal(got, []int{4, 6, 7}) {
		t.Errorf("js comments at %v, want [4 6 7]", got)
	}
	css := "a { content: \"/* no */\"; }\n/* yes */\nb { background: url(x.svg); }\n"
	if got := cssComments(css); !slices.Equal(got, []int{2}) {
		t.Errorf("css comments at %v, want [2]", got)
	}
	py := "x = \"# no\"\ny = '''\n# no\n'''\n# yes\nz = 1  # yes\n"
	if got := pyComments(py); !slices.Equal(got, []int{5, 6}) {
		t.Errorf("py comments at %v, want [5 6]", got)
	}
}

func comments(name, src string) []int {
	switch filepath.Ext(name) {
	case ".js":
		return jsComments(src)
	case ".css":
		return cssComments(src)
	case ".py":
		return pyComments(src)
	}
	return nil
}

func isIdent(c byte) bool {
	return c == '_' || c == '$' || c >= '0' && c <= '9' || c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z'
}

var regexKeywords = map[string]bool{"return": true, "typeof": true, "case": true, "do": true, "else": true, "in": true, "of": true, "new": true, "delete": true, "void": true, "throw": true, "yield": true, "await": true, "instanceof": true}

func jsComments(src string) []int {
	const (
		code = iota
		single
		double
		template
		regex
		class
	)
	var out []int
	var stack []int
	mode, depth, line := code, 0, 1
	var prev byte
	word := ""
	add := func() {
		if len(out) == 0 || out[len(out)-1] != line {
			out = append(out, line)
		}
	}
	for i := 0; i < len(src); i++ {
		c := src[i]
		var next byte
		if i+1 < len(src) {
			next = src[i+1]
		}
		if c == '\n' {
			line++
		}
		switch mode {
		case single, double:
			if c == '\\' {
				i++
				if next == '\n' {
					line++
				}
			} else if (mode == single && c == '\'') || (mode == double && c == '"') {
				mode, prev, word = code, 'a', ""
			}
		case template:
			switch {
			case c == '\\':
				i++
				if next == '\n' {
					line++
				}
			case c == '`':
				mode, prev, word = code, 'a', ""
			case c == '$' && next == '{':
				stack = append(stack, depth)
				mode, depth, prev, word = code, 0, '{', ""
				i++
			}
		case regex, class:
			switch {
			case c == '\\':
				i++
			case c == '[':
				mode = class
			case c == ']' && mode == class:
				mode = regex
			case c == '/' && mode == regex:
				mode, prev, word = code, 'a', ""
			}
		default:
			switch {
			case c == '/' && next == '/':
				add()
				for i < len(src) && src[i] != '\n' {
					i++
				}
				line++
			case c == '/' && next == '*':
				add()
				i += 2
				for i < len(src) && !(src[i] == '*' && i+1 < len(src) && src[i+1] == '/') {
					if src[i] == '\n' {
						line++
					}
					i++
				}
				i++
			case c == '\'':
				mode = single
			case c == '"':
				mode = double
			case c == '`':
				mode = template
			case c == '/':
				if prev == 0 || strings.IndexByte("(,=:[!&|?{};+-*%<>~^", prev) >= 0 || (prev == 'a' && regexKeywords[word]) {
					mode = regex
				} else {
					prev, word = '/', ""
				}
			case c == '{':
				depth++
				prev, word = c, ""
			case c == '}':
				if depth == 0 && len(stack) > 0 {
					depth, stack = stack[len(stack)-1], stack[:len(stack)-1]
					mode = template
					continue
				}
				depth--
				prev, word = c, ""
			case c == ' ' || c == '\t' || c == '\n' || c == '\r':
			case isIdent(c):
				if prev != 'a' {
					word = ""
				}
				word += string(c)
				prev = 'a'
			default:
				prev, word = c, ""
			}
		}
	}
	return out
}

func cssComments(src string) []int {
	var out []int
	line := 1
	var quote byte
	for i := 0; i < len(src); i++ {
		c := src[i]
		if c == '\n' {
			line++
		}
		switch {
		case quote != 0:
			if c == '\\' {
				i++
			} else if c == quote {
				quote = 0
			}
		case c == '"' || c == '\'':
			quote = c
		case c == '/' && i+1 < len(src) && src[i+1] == '*':
			out = append(out, line)
			end := strings.Index(src[i+2:], "*/")
			if end < 0 {
				return out
			}
			line += strings.Count(src[i:i+2+end], "\n")
			i += end + 3
		}
	}
	return out
}

func pyComments(src string) []int {
	var out []int
	line := 1
	quote := ""
	for i := 0; i < len(src); i++ {
		c := src[i]
		if c == '\n' {
			line++
		}
		switch {
		case quote != "":
			if c == '\\' {
				i++
			} else if strings.HasPrefix(src[i:], quote) {
				i += len(quote) - 1
				quote = ""
			}
		case strings.HasPrefix(src[i:], `"""`) || strings.HasPrefix(src[i:], "'''"):
			quote = src[i : i+3]
			i += 2
		case c == '"' || c == '\'':
			quote = string(c)
		case c == '#':
			out = append(out, line)
			for i < len(src) && src[i] != '\n' {
				i++
			}
			line++
		}
	}
	return out
}
