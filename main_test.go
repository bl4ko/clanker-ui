package main

import (
	"io/fs"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"testing"
	"testing/fstest"
)

func request(t *testing.T, h http.Handler, method, path string, headers ...string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(method, path, nil)
	for i := 0; i+1 < len(headers); i += 2 {
		req.Header.Set(headers[i], headers[i+1])
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec
}

func checkSecurityHeaders(t *testing.T, rec *httptest.ResponseRecorder, path string) {
	t.Helper()
	want := map[string]string{
		"Content-Security-Policy":    csp,
		"X-Content-Type-Options":     "nosniff",
		"Referrer-Policy":            "no-referrer",
		"Cross-Origin-Opener-Policy": "same-origin",
	}
	for k, v := range want {
		if got := rec.Header().Get(k); got != v {
			t.Errorf("%s: %s = %q, want %q", path, k, got, v)
		}
	}
}

func TestCSPMatchesDesign(t *testing.T) {
	want := "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; require-trusted-types-for 'script'"
	if csp != want {
		t.Fatalf("csp = %q", csp)
	}
}

func TestServesEmbeddedFiles(t *testing.T) {
	h := newSite("").routes()
	var names []string
	err := fs.WalkDir(embedded, ".", func(name string, d fs.DirEntry, err error) error {
		if err == nil && !d.IsDir() && !strings.HasPrefix(filepath.Base(name), ".") {
			names = append(names, name)
		}
		return err
	})
	if err != nil {
		t.Fatal(err)
	}
	var disk []string
	for _, root := range []string{".", "demo", "dist", "docs", "skills/clanker-ui"} {
		err := filepath.WalkDir(root, func(name string, d fs.DirEntry, err error) error {
			if err != nil {
				return err
			}
			base := filepath.Base(name)
			if d.IsDir() {
				if root == "." && name != "." {
					return filepath.SkipDir
				}
				return nil
			}
			if strings.HasPrefix(base, ".") || strings.HasPrefix(base, "_") || root == "." && !strings.HasPrefix(base, "clanker-ui") {
				return nil
			}
			disk = append(disk, filepath.ToSlash(name))
			return nil
		})
		if err != nil {
			t.Fatal(err)
		}
	}
	slices.Sort(names)
	slices.Sort(disk)
	if !slices.Equal(names, disk) {
		t.Errorf("embedded files %v, want the kit, demo, docs, and skill files %v", names, disk)
	}
	for _, want := range []string{"clanker-ui.css", "clanker-ui-a11y.css", "clanker-ui.js", "clanker-ui-chart.js", "clanker-ui-code.js", "clanker-ui-theme.js", "clanker-ui-themes.css", "demo/index.html", "demo/demo.css", "demo/demo.js", "docs/nav.json", "docs/assets/docs.css", "docs/assets/docs.js", "docs/assets/docs-sidebar.js"} {
		if !slices.Contains(names, want) {
			t.Errorf("%s is not embedded", want)
		}
	}
	for _, name := range names {
		if strings.HasPrefix(name, "docs/") {
			continue
		}
		path := "/" + name
		if name == "demo/index.html" {
			path = "/demo"
		}
		if strings.HasPrefix(name, "dist/") {
			path = "/" + filepath.Base(name)
		}
		rec := request(t, h, http.MethodGet, path)
		if rec.Code != http.StatusOK {
			t.Errorf("%s: status %d", path, rec.Code)
			continue
		}
		want := contentTypes[filepath.Ext(name)]
		if got := rec.Header().Get("Content-Type"); want == "" || got != want {
			t.Errorf("%s: Content-Type %q, want %q", path, got, want)
		}
		body, err := os.ReadFile(name)
		if err != nil {
			t.Fatal(err)
		}
		if rec.Body.String() != string(body) {
			t.Errorf("%s: embedded body differs from %s", path, name)
		}
		if rec.Header().Get("ETag") == "" || rec.Header().Get("Cache-Control") != "no-cache" {
			t.Errorf("%s: missing ETag or Cache-Control", path)
		}
		checkSecurityHeaders(t, rec, path)
	}
	for _, path := range []string{"/docs/nav.json", "/docs/assets/docs.css", "/docs/templates/page.html", "/docs/content/index/page.md", "/docs/content/components/button/examples/button-demo.html"} {
		if rec := request(t, h, http.MethodGet, path); rec.Code == http.StatusOK {
			t.Errorf("%s: raw docs file served with 200", path)
		}
	}
}

func TestThemeBootFile(t *testing.T) {
	boot, err := os.ReadFile("clanker-ui-theme.js")
	if err != nil {
		t.Fatal(err)
	}
	module, err := os.ReadFile("clanker-ui.js")
	if err != nil {
		t.Fatal(err)
	}
	key := regexp.MustCompile(`const THEME_KEY = ("[^"]+")`).FindSubmatch(module)
	if key == nil {
		t.Fatal("clanker-ui.js has no THEME_KEY")
	}
	schemeKey := regexp.MustCompile(`const SCHEME_KEY = ("[^"]+")`).FindSubmatch(module)
	schemeValue := regexp.MustCompile(`const SCHEME_VALUE = (/.+/)\n`).FindSubmatch(module)
	if schemeKey == nil || schemeValue == nil {
		t.Fatal("clanker-ui.js has no SCHEME_KEY or SCHEME_VALUE")
	}
	src := string(boot)
	for _, want := range []string{"localStorage.getItem(" + string(key[1]) + ")", "localStorage.getItem(" + string(schemeKey[1]) + ")", string(schemeValue[1]) + ".test(s)", `"light"`, `"dark"`, "try {", "document.documentElement", ".dataset.theme = t", ".dataset.scheme = s", `.dataset.systemTheme = matchMedia("(prefers-color-scheme: dark)")`, `meta[name="theme-color"]:not([media])`, `"var(--background)"`, `removeAttribute("style")`} {
		if !strings.Contains(src, want) {
			t.Errorf("clanker-ui-theme.js does not contain %s", want)
		}
	}
	if regexp.MustCompile(`\b(import|export)\b`).MatchString(src) {
		t.Error("clanker-ui-theme.js must be a classic script")
	}
	page, err := os.ReadFile("demo/index.html")
	if err != nil {
		t.Fatal(err)
	}
	html := string(page)
	at := strings.Index(html, `<script src="clanker-ui-theme.js"></script>`)
	css := strings.LastIndex(html[:strings.Index(html, "</head>")], `<link rel="stylesheet"`)
	modules := strings.Index(html, `<script type="module"`)
	if at < 0 || css < 0 || modules < 0 || at < css || at > modules {
		t.Error("demo/index.html must load clanker-ui-theme.js in <head> after the stylesheets and before the modules")
	}
}

func TestSchemeLists(t *testing.T) {
	module, err := os.ReadFile("clanker-ui.js")
	if err != nil {
		t.Fatal(err)
	}
	css, err := os.ReadFile("clanker-ui-themes.css")
	if err != nil {
		t.Fatal(err)
	}
	listed := map[string]bool{}
	for _, name := range []string{"SCHEMES", "EDITOR_SCHEMES", "ACCENTS"} {
		line := regexp.MustCompile(`(?m)^const ` + name + ` = (\[.*\])$`).FindSubmatch(module)
		if line == nil {
			t.Fatalf("clanker-ui.js has no %s list", name)
		}
		for _, m := range regexp.MustCompile(`\["([a-z0-9-]*)", "[^"]+"\]`).FindAllSubmatch(line[1], -1) {
			listed[string(m[1])] = true
		}
	}
	ruled := map[string]bool{}
	for _, m := range regexp.MustCompile(`\[data-scheme~="([a-z0-9-]+)"\]`).FindAllSubmatch(css, -1) {
		ruled[string(m[1])] = true
	}
	for value := range listed {
		if value != "" && !ruled[value] {
			t.Errorf("scheme %q is in the picker lists but has no rule in clanker-ui-themes.css", value)
		}
	}
	for value := range ruled {
		if !listed[value] && value != "menu-bold" && !strings.HasPrefix(value, "radius-") {
			t.Errorf("clanker-ui-themes.css has a rule for %q, but the picker lists do not have it", value)
		}
	}
	doc, err := os.ReadFile("skills/clanker-ui/references/theming.md")
	if err != nil {
		t.Fatal(err)
	}
	for value := range ruled {
		if !strings.Contains(string(doc), "`"+value+"`") {
			t.Errorf("references/theming.md does not list the scheme %q", value)
		}
	}
}

func TestETagRevalidation(t *testing.T) {
	h := newSite("").routes()
	first := request(t, h, http.MethodGet, "/clanker-ui.js")
	again := request(t, h, http.MethodGet, "/clanker-ui.js", "If-None-Match", first.Header().Get("ETag"))
	if again.Code != http.StatusNotModified {
		t.Fatalf("status %d, want 304", again.Code)
	}
}

func TestHealthz(t *testing.T) {
	h := newSite("").routes()
	rec := request(t, h, http.MethodGet, "/healthz")
	if rec.Code != http.StatusNoContent || rec.Body.Len() != 0 {
		t.Fatalf("healthz: status %d body %q", rec.Code, rec.Body.String())
	}
	checkSecurityHeaders(t, rec, "/healthz")
	if rec := request(t, h, http.MethodPost, "/healthz"); rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("POST /healthz: status %d", rec.Code)
	}
}

func TestRejectsOtherPathsAndMethods(t *testing.T) {
	for _, dir := range []string{"", "."} {
		h := newSite(dir).routes()
		for _, path := range []string{"/main.go", "/go.mod", "/.git/config", "/wip/g1.js", "/test/run.py", "/demo/index.html", "/demo/../main.go", "/demo/assets/../../main.go", "/demo/x/y.js", "/clanker-ui.css.map", "/LICENSE", "/index.html", "/docs/nav.json", "/assets/x/main.go", "/assets/x/../main.go", "/view/../main.go"} {
			rec := request(t, h, http.MethodGet, path)
			if rec.Code == http.StatusOK {
				t.Errorf("dir %q: %s served with 200", dir, path)
			}
			checkSecurityHeaders(t, rec, path)
		}
		if rec := request(t, h, http.MethodPost, "/"); rec.Code != http.StatusMethodNotAllowed {
			t.Errorf("dir %q: POST / status %d", dir, rec.Code)
		}
		if rec := request(t, h, http.MethodHead, "/clanker-ui.css"); rec.Code != http.StatusOK || rec.Body.Len() != 0 {
			t.Errorf("dir %q: HEAD status %d body %d", dir, rec.Code, rec.Body.Len())
		}
	}
}

func TestDirModeIsLive(t *testing.T) {
	rec := request(t, newSite(".").routes(), http.MethodGet, "/clanker-ui.css")
	if rec.Code != http.StatusOK || rec.Header().Get("Cache-Control") != "no-store" || rec.Header().Get("ETag") != "" {
		t.Fatalf("status %d, Cache-Control %q, ETag %q", rec.Code, rec.Header().Get("Cache-Control"), rec.Header().Get("ETag"))
	}
}

func TestSpikeFilesOnlyInDirMode(t *testing.T) {
	for _, path := range []string{"/test/spike/index.html", "/test/spike/page.css"} {
		rec := request(t, newSite(".").routes(), http.MethodGet, path)
		if rec.Code != http.StatusOK {
			t.Errorf("dir mode: %s status %d", path, rec.Code)
		}
		checkSecurityHeaders(t, rec, path)
		if rec := request(t, newSite("").routes(), http.MethodGet, path); rec.Code == http.StatusOK {
			t.Errorf("embedded mode: %s served with 200", path)
		}
	}
	for _, path := range []string{"/test/run.py", "/test/spike/../run.py", "/tools/gen/main.go", "/tools/gen/kit.css"} {
		if rec := request(t, newSite(".").routes(), http.MethodGet, path); rec.Code == http.StatusOK {
			t.Errorf("dir mode: %s served with 200", path)
		}
	}
}

func TestSplitFixturesOnlyInDirMode(t *testing.T) {
	for _, path := range []string{"/test/split/core.html", "/test/split/chart.html", "/test/split/chart.js"} {
		rec := request(t, newSite(".").routes(), http.MethodGet, path)
		if rec.Code != http.StatusOK {
			t.Errorf("dir mode: %s status %d", path, rec.Code)
		}
		checkSecurityHeaders(t, rec, path)
		if rec := request(t, newSite("").routes(), http.MethodGet, path); rec.Code == http.StatusOK {
			t.Errorf("embedded mode: %s served with 200", path)
		}
	}
	if rec := request(t, newSite(".").routes(), http.MethodGet, "/test/split_test.py"); rec.Code == http.StatusOK {
		t.Error("dir mode: /test/split_test.py served with 200")
	}
}

func TestBehaviorFixturesOnlyInDirMode(t *testing.T) {
	for _, path := range []string{"/test/behavior/fixtures/index.html", "/test/behavior/fixtures/tooltip.html", "/test/behavior/fixtures/fixture.css", "/test/behavior/fixtures/toast.js"} {
		rec := request(t, newSite(".").routes(), http.MethodGet, path)
		if rec.Code != http.StatusOK {
			t.Errorf("dir mode: %s status %d", path, rec.Code)
		}
		checkSecurityHeaders(t, rec, path)
		if rec := request(t, newSite("").routes(), http.MethodGet, path); rec.Code == http.StatusOK {
			t.Errorf("embedded mode: %s served with 200", path)
		}
	}
	for _, path := range []string{"/test/behavior/scenarios/tooltip.json", "/test/behavior/golden/tooltip.json", "/tools/behavior/engine.py", "/test/behavior/fixtures/../scenarios/tooltip.json", "/test/behavior_test.py"} {
		if rec := request(t, newSite(".").routes(), http.MethodGet, path); rec.Code == http.StatusOK {
			t.Errorf("dir mode: %s served with 200", path)
		}
	}
}

func writeFiles(t *testing.T, files map[string]string) string {
	t.Helper()
	dir := t.TempDir()
	for name, body := range files {
		if err := os.MkdirAll(filepath.Join(dir, filepath.Dir(name)), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(dir, name), []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	return dir
}

func TestDistFilesServedFlat(t *testing.T) {
	dir := writeFiles(t, map[string]string{"dist/clanker-ui-core.min.js": "export const a=1\n", "dist/clanker-ui-forms.min.css": "a{b:c}\n", "dist/notes.txt": "x"})
	h := newSite(dir).routes()
	for path, body := range map[string]string{"/clanker-ui-core.min.js": "export const a=1\n", "/clanker-ui-forms.min.css": "a{b:c}\n"} {
		rec := request(t, h, http.MethodGet, path)
		if rec.Code != http.StatusOK || rec.Body.String() != body {
			t.Errorf("%s: status %d, body %q", path, rec.Code, rec.Body.String())
		}
		checkSecurityHeaders(t, rec, path)
	}
	for _, path := range []string{"/dist/clanker-ui-core.min.js", "/notes.txt", "/dist/notes.txt", "/clanker-ui-layout.min.js", "/clanker-ui-core.min.js.map"} {
		if rec := request(t, h, http.MethodGet, path); rec.Code == http.StatusOK {
			t.Errorf("%s served with 200", path)
		}
	}
}

func TestKitMinServesMinifiedFiles(t *testing.T) {
	files := map[string]string{}
	for name := range kitFiles {
		b, err := os.ReadFile(name)
		if err != nil {
			t.Fatal(err)
		}
		files[name] = string(b)
	}
	files["dist/clanker-ui.min.css"] = "min-css\n"
	files["dist/clanker-ui-rhea.min.css"] = "min-rhea\n"
	files["dist/clanker-ui-themes.min.css"] = "min-themes\n"
	files["dist/clanker-ui-a11y.min.css"] = "min-a11y\n"
	files["dist/clanker-ui-theme.min.js"] = "min-theme\n"
	files["dist/clanker-ui-core.min.js"] = "export const h=1\n"
	dir := writeFiles(t, files)
	license, _, _ := strings.Cut(files["clanker-ui.js"], "\n")
	chartLicense, _, _ := strings.Cut(files["clanker-ui-chart.js"], "\n")
	codeLicense, _, _ := strings.Cut(files["clanker-ui-code.js"], "\n")
	h := newKitSite(dir, "min").routes()
	for path, body := range map[string]string{
		"/clanker-ui.css":         "min-css\n",
		"/clanker-ui-rhea.css":    "min-rhea\n",
		"/clanker-ui-themes.css":  "min-themes\n",
		"/clanker-ui-a11y.css":    "min-a11y\n",
		"/clanker-ui.js":          license + "\nexport * from \"./clanker-ui-core.min.js\"\nexport * from \"./clanker-ui.min.js\"\n",
		"/clanker-ui-chart.js":    chartLicense + "\nexport * from \"./clanker-ui-chart.min.js\"\n",
		"/clanker-ui-code.js":     codeLicense + "\nexport * from \"./clanker-ui-code.min.js\"\n",
		"/clanker-ui-theme.js":    "min-theme\n",
		"/clanker-ui-core.min.js": "export const h=1\n",
	} {
		rec := request(t, h, http.MethodGet, path)
		if rec.Code != http.StatusOK || rec.Body.String() != body {
			t.Errorf("KIT=min %s: status %d, body %q", path, rec.Code, trunc(rec.Body.String(), 120))
		}
	}
	if rec := request(t, newSite(dir).routes(), http.MethodGet, "/clanker-ui.css"); rec.Body.String() != files["clanker-ui.css"] {
		t.Error("without KIT=min the readable clanker-ui.css must be served")
	}
	m := docsFS(t, nil)
	for name, body := range files {
		m[name] = &fstest.MapFile{Data: []byte(body)}
	}
	d, err := loadDocs(minFS{m})
	if err != nil {
		t.Fatal(err)
	}
	if string(d.assets["clanker-ui-core.min.js"]) != files["dist/clanker-ui-core.min.js"] || !strings.Contains(string(d.assets["clanker-ui.js"]), "export * from") {
		t.Error("KIT=min docs assets must hold the dist files and the clanker-ui.js shim")
	}
}

func trunc(s string, n int) string {
	if len(s) > n {
		return s[:n] + "..."
	}
	return s
}

func TestDemoNavTargetsExist(t *testing.T) {
	page, err := os.ReadFile("demo/index.html")
	if err != nil {
		t.Fatal(err)
	}
	html := string(page)
	start := strings.Index(html, `id="demo-nav"`)
	if start < 0 {
		t.Fatal(`demo/index.html has no id="demo-nav"`)
	}
	end := strings.Index(html[start:], "</nav>")
	if end < 0 {
		t.Fatal("the demo nav is not closed")
	}
	nav := html[start : start+end]
	links := regexp.MustCompile(`href="#([^"]+)"`).FindAllStringSubmatch(nav, -1)
	if len(links) < 65 {
		t.Fatalf("the demo nav has %d links, want one per component", len(links))
	}
	for _, m := range links {
		if !strings.Contains(html, `id="`+m[1]+`"`) {
			t.Errorf("nav link #%s has no target", m[1])
		}
	}
}

func TestDemoOnly(t *testing.T) {
	page, err := os.ReadFile("demo/index.html")
	if err != nil {
		t.Fatal(err)
	}
	html := string(page)
	h := newSite("").routes()
	if got, want := len(demoBlock.FindAllString(html, -1)), strings.Count(html, "\n      <section ")+strings.Count(html, `data-demo="category"`); got != want {
		t.Fatalf("the filter finds %d sections and categories, want %d", got, want)
	}
	rec := request(t, h, http.MethodGet, "/demo?only=forms,dialog")
	body := rec.Body.String()
	if rec.Code != http.StatusOK || rec.Header().Get("Content-Type") != contentTypes[".html"] {
		t.Fatalf("status %d, Content-Type %q", rec.Code, rec.Header().Get("Content-Type"))
	}
	checkSecurityHeaders(t, rec, "/demo?only=forms,dialog")
	if regexp.MustCompile(`(data-demo="(?:section|hero)") hidden>`).ReplaceAllString(body, "$1>") != html {
		t.Error("the filtered demo differs from demo/index.html in more than hidden attributes")
	}
	for id, hidden := range map[string]bool{"introduction": true, "button": false, "native-select": false, "dialog": false, "drawer": true, "chart-stat": true} {
		if got := strings.Contains(body, `<section id="`+id+`" data-demo="section" hidden>`) || strings.Contains(body, `<section id="`+id+`" data-demo="hero" hidden>`); got != hidden {
			t.Errorf("section %s hidden: %v, want %v", id, got, hidden)
		}
	}
	if strings.Contains(body, `data-demo="category" hidden`) {
		t.Error("a category heading is hidden")
	}
	for _, path := range []string{"/demo?only=nope", "/demo?only=forms,"} {
		if rec := request(t, h, http.MethodGet, path); rec.Code != http.StatusBadRequest {
			t.Errorf("%s: status %d, want 400", path, rec.Code)
		}
	}
	files, _ := filepath.Glob("test/*_test.py")
	for _, f := range files {
		src, err := os.ReadFile(f)
		if err != nil {
			t.Fatal(err)
		}
		for _, m := range regexp.MustCompile(`(?m)^START = "(/demo\?[^"]*)"`).FindAllStringSubmatch(string(src), -1) {
			if rec := request(t, h, http.MethodGet, m[1]); rec.Code != http.StatusOK {
				t.Errorf("%s START %s: status %d", f, m[1], rec.Code)
			}
		}
	}
}

func TestAccordionClosedPanelsHidden(t *testing.T) {
	page, err := os.ReadFile("demo/index.html")
	if err != nil {
		t.Fatal(err)
	}
	item := regexp.MustCompile(`<div data-slot="accordion-item"[^>]*>`)
	content := regexp.MustCompile(`<div data-slot="accordion-content"[^>]*>`)
	src := string(page)
	found := 0
	for _, loc := range item.FindAllStringIndex(src, -1) {
		tag := src[loc[0]:loc[1]]
		panel := content.FindString(src[loc[1]:])
		open := strings.Contains(tag, `data-state="open"`)
		hidden := strings.Contains(panel, `hidden="until-found"`)
		if open == hidden {
			t.Errorf("%s: panel %s; a closed item needs hidden=\"until-found\", an open one none", tag, panel)
		}
		found++
	}
	if found < 10 {
		t.Fatalf("only %d accordion items found", found)
	}
}
