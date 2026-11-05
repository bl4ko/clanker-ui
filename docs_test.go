package main

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"html/template"
	"io"
	"io/fs"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"testing"
	"testing/fstest"
	"time"
)

func docsOf(t *testing.T) *docsSite {
	t.Helper()
	d, err := loadDocs(os.DirFS("."))
	if err != nil {
		t.Fatal(err)
	}
	return d
}

func navHrefs(t *testing.T) []string {
	t.Helper()
	raw, err := os.ReadFile("docs/nav.json")
	if err != nil {
		t.Fatal(err)
	}
	var nav navConfig
	if err := json.Unmarshal(raw, &nav); err != nil {
		t.Fatal(err)
	}
	var out []string
	for _, item := range slices.Concat(nav.Header, nav.Sections, nav.MobileSections) {
		out = append(out, item.Href)
	}
	for _, g := range nav.Groups {
		for _, item := range g.Items {
			out = append(out, item.Href)
		}
	}
	slices.Sort(out)
	return slices.Compact(out)
}

func TestDocsLoadInBothModes(t *testing.T) {
	if s := newSite(""); s.docsErr != nil {
		t.Fatalf("embedded docs: %v", s.docsErr)
	}
	if _, err := newSite(".").site(); err != nil {
		t.Fatalf("docs from disk: %v", err)
	}
}

func TestEveryNavLinkResolves(t *testing.T) {
	h := newSite("").routes()
	hrefs := navHrefs(t)
	if len(hrefs) < 80 {
		t.Fatalf("nav has %d links", len(hrefs))
	}
	for _, href := range hrefs {
		rec := request(t, h, http.MethodGet, href)
		if to, ok := docRedirects[href]; ok {
			if rec.Code != http.StatusMovedPermanently || rec.Header().Get("Location") != to {
				t.Errorf("%s: status %d, Location %q", href, rec.Code, rec.Header().Get("Location"))
			}
			continue
		}
		if rec.Code != http.StatusOK {
			t.Errorf("%s: status %d", href, rec.Code)
		}
	}
}

func TestNavCoversGroupsAndOrder(t *testing.T) {
	d := docsOf(t)
	var groups []string
	for _, g := range d.nav.Groups {
		groups = append(groups, g.Title)
	}
	if want := []string{"Components", "Blocks", "Get Started", "Utilities", "clanker-ui"}; !slices.Equal(groups, want) {
		t.Errorf("groups %v, want %v", groups, want)
	}
	components := d.componentLinks("")
	if len(components) != 67 {
		t.Errorf("Components group has %d pages, want 67", len(components))
	}
	for i := 1; i < len(components); i++ {
		if strings.ToLower(components[i-1].Title) > strings.ToLower(components[i].Title) {
			t.Errorf("Components are not in alphabetical order at %q", components[i].Title)
		}
	}
	if d.order[0].Href != "/docs/components" {
		t.Errorf("first page in order is %s", d.order[0].Href)
	}
	v := d.view("docs", "/docs/components/button")
	if v.Prev == nil || v.Prev.Href != "/docs/components/bubble" || v.Next == nil || v.Next.Href != "/docs/components/button-group" {
		t.Errorf("button neighbours: %+v %+v", v.Prev, v.Next)
	}
}

var (
	idAttr   = regexp.MustCompile(`\sid="([^"]+)"`)
	hrefAttr = regexp.MustCompile(`\shref="([^"]+)"`)
)

func TestRenderedPages(t *testing.T) {
	h := newSite("").routes()
	d := docsOf(t)
	paths := []string{"/", "/view/button-demo", "/docs/components/accordion"}
	for _, href := range sortedKeys(d.pages) {
		paths = append(paths, href)
	}
	for _, path := range paths {
		rec := request(t, h, http.MethodGet, path)
		if rec.Code != http.StatusOK {
			t.Errorf("%s: status %d", path, rec.Code)
			continue
		}
		if got := rec.Header().Get("Cache-Control"); got != "no-cache" || rec.Header().Get("ETag") == "" {
			t.Errorf("%s: Cache-Control %q, ETag %q", path, got, rec.Header().Get("ETag"))
		}
		if got := rec.Header().Get("Content-Type"); got != contentTypes[".html"] {
			t.Errorf("%s: Content-Type %q", path, got)
		}
		html := rec.Body.String()
		for _, p := range htmlProblems(html) {
			t.Errorf("%s:%d: %s is not allowed", path, lineOf(html, p.offset), p.name)
		}
		seen := map[string]bool{}
		for _, m := range idAttr.FindAllStringSubmatch(html, -1) {
			if seen[m[1]] {
				t.Errorf("%s: duplicate id %q", path, m[1])
			}
			seen[m[1]] = true
		}
		for _, m := range hrefAttr.FindAllStringSubmatch(html, -1) {
			href := m[1]
			switch {
			case strings.HasPrefix(href, "#"):
				if href != "#" && !seen[href[1:]] {
					t.Errorf("%s: link %s has no target", path, href)
				}
			case strings.HasPrefix(href, "/"):
				target, _, _ := strings.Cut(href, "#")
				if to, ok := docRedirects[target]; ok {
					if rec := request(t, h, http.MethodGet, target); rec.Code != http.StatusMovedPermanently || rec.Header().Get("Location") != to {
						t.Errorf("%s: link %s: status %d, Location %q", path, href, rec.Code, rec.Header().Get("Location"))
					}
					target = to
				}
				if rec := request(t, h, http.MethodGet, target); rec.Code != http.StatusOK {
					t.Errorf("%s: link %s: status %d", path, href, rec.Code)
				}
			case strings.HasPrefix(href, "https://"), strings.HasPrefix(href, "data:,"):
			default:
				t.Errorf("%s: unexpected link %q", path, href)
			}
		}
	}
}

func TestDocsRoutesAndHeaders(t *testing.T) {
	h := newSite("").routes()
	d := docsOf(t)
	asset := "/assets/" + d.hash + "/clanker-ui.js"
	rec := request(t, h, http.MethodGet, asset)
	if rec.Code != http.StatusOK || rec.Header().Get("Cache-Control") != "public, max-age=31536000, immutable" || rec.Header().Get("Content-Type") != contentTypes[".js"] {
		t.Errorf("%s: status %d, Cache-Control %q, Content-Type %q", asset, rec.Code, rec.Header().Get("Cache-Control"), rec.Header().Get("Content-Type"))
	}
	body, _ := os.ReadFile("clanker-ui.js")
	if rec.Body.String() != string(body) {
		t.Error("hashed kit asset differs from clanker-ui.js")
	}
	checkSecurityHeaders(t, rec, asset)
	for _, path := range []string{"/assets/" + d.hash + "/main.go", "/assets/" + d.hash + "/nav.json", "/docs/nope", "/docs/components/nope", "/docs/nope.md", "/blocks.md", "/view/nope", "/nope"} {
		rec := request(t, h, http.MethodGet, path)
		if rec.Code != http.StatusNotFound {
			t.Errorf("%s: status %d, want 404", path, rec.Code)
		}
		checkSecurityHeaders(t, rec, path)
	}
	if rec := request(t, h, http.MethodGet, "/docs/"); rec.Code != http.StatusMovedPermanently || rec.Header().Get("Location") != "/docs" {
		t.Errorf("/docs/: status %d, Location %q", rec.Code, rec.Header().Get("Location"))
	}
	md := request(t, h, http.MethodGet, "/docs/components/button.md")
	if md.Code != http.StatusOK || md.Header().Get("Content-Type") != contentTypes[".md"] {
		t.Fatalf("button.md: status %d, Content-Type %q", md.Code, md.Header().Get("Content-Type"))
	}
	text := md.Body.String()
	if !strings.HasPrefix(text, "---\ntitle: Button\n") || strings.Contains(text, "{{") || strings.Count(text, "```html\n") != 16 {
		t.Errorf("button.md is not expanded: %.200q", text)
	}
	live := newSite(".").routes()
	if rec := request(t, live, http.MethodGet, "/assets/anything/docs.css"); rec.Code != http.StatusOK || rec.Header().Get("Cache-Control") != "no-store" {
		t.Errorf("live asset: status %d, Cache-Control %q", rec.Code, rec.Header().Get("Cache-Control"))
	}
}

func TestViewCSPDiffersOnlyInFrameAncestors(t *testing.T) {
	h := newSite("").routes()
	view := request(t, h, http.MethodGet, "/view/button-demo").Header().Get("Content-Security-Policy")
	docs := request(t, h, http.MethodGet, "/docs/components/button").Header().Get("Content-Security-Policy")
	if docs != csp {
		t.Errorf("docs CSP %q", docs)
	}
	if !slices.Contains(strings.Split(view, "; "), "frame-ancestors 'self'") {
		t.Errorf("view CSP %q has no frame-ancestors 'self'", view)
	}
	strip := func(policy string) []string {
		return slices.DeleteFunc(strings.Split(policy, "; "), func(d string) bool { return strings.HasPrefix(d, "frame-ancestors") })
	}
	if !slices.Equal(strip(view), strip(docs)) {
		t.Errorf("view CSP %q differs from %q in more than frame-ancestors", view, docs)
	}
}

func docsFS(t *testing.T, extra map[string]string) fstest.MapFS {
	t.Helper()
	m := fstest.MapFS{}
	for _, root := range []string{"docs"} {
		err := fs.WalkDir(os.DirFS("."), root, func(name string, d fs.DirEntry, err error) error {
			if err != nil || d.IsDir() {
				return err
			}
			b, err := os.ReadFile(name)
			m[name] = &fstest.MapFile{Data: b}
			return err
		})
		if err != nil {
			t.Fatal(err)
		}
	}
	for name := range kitFiles {
		b, err := os.ReadFile(name)
		if err != nil {
			t.Fatal(err)
		}
		m[name] = &fstest.MapFile{Data: b}
	}
	for name, body := range extra {
		if body == "" {
			delete(m, name)
			continue
		}
		m[name] = &fstest.MapFile{Data: []byte(body)}
	}
	return m
}

func TestDocsContentErrors(t *testing.T) {
	page := "---\ntitle: Button\ndescription: Test.\n---\n\n"
	cases := map[string]map[string]string{
		"unknown example":        {"docs/content/components/button/page.md": page + "{{example \"button-nope\"}}\n"},
		"bad tag":                {"docs/content/components/button/page.md": page + "{{example button-demo}}\n"},
		"bad example attribute":  {"docs/content/components/button/page.md": page + "{{example \"button-demo\" height=\"9px\"}}\n"},
		"page without nav entry": {"docs/content/orphan/page.md": page},
		"missing front matter":   {"docs/content/components/button/page.md": "# Button\n"},
		"unknown front matter":   {"docs/content/components/button/page.md": "---\ntitle: A\ndescription: B\nlayout: x\n---\n"},
		"unclosed fence":         {"docs/content/components/button/page.md": page + "```html\n<p>x</p>\n"},
		"javascript link":        {"docs/content/components/button/page.md": page + "[x](javascript:alert(1))\n"},
		"duplicate example":      {"docs/content/index/examples/button-demo.html": "<p>x</p>"},
		"bad example name":       {"docs/content/components/button/examples/Button_X.html": "<p>x</p>"},
		"stray file":             {"docs/content/components/button/notes.txt": "x"},
		"nav item without title": {"docs/nav.json": `{"header":[{"title":"","href":"/"}],"sections":[],"mobileSections":[],"groups":[]}`},
	}
	for name, extra := range cases {
		if _, err := loadDocs(docsFS(t, extra)); err == nil {
			t.Errorf("%s: loadDocs accepted the content", name)
		}
	}
	if _, err := loadDocs(docsFS(t, nil)); err != nil {
		t.Fatalf("copy of the real content: %v", err)
	}
}

func TestEveryExampleTagExists(t *testing.T) {
	d := docsOf(t)
	tag := regexp.MustCompile(`\{\{example "([^"]+)"`)
	used := map[string]bool{}
	for _, p := range d.pages {
		for _, m := range tag.FindAllStringSubmatch(p.Source, -1) {
			used[m[1]] = true
			if d.examples[m[1]] == nil {
				t.Errorf("%s uses unknown example %q", p.Href, m[1])
			}
		}
	}
	for name, ex := range d.examples {
		if ex.HTML == "" {
			t.Errorf("example %s has no .html file", name)
		}
		if !used[name] {
			t.Errorf("example %s is not used on any page", name)
		}
	}
}

func render(t *testing.T, src string) (string, []tocEntry) {
	t.Helper()
	hooks := mdHooks{
		example: func(name string, _ map[string]string) (string, error) {
			return "<x-example>" + name + "</x-example>\n", nil
		},
		components: func(variant string) (string, error) { return "<x-list>" + variant + "</x-list>\n", nil },
		code: func(lang, title, src string) (string, error) {
			return "<pre data-lang=\"" + lang + "\" title=\"" + title + "\">" + template.HTMLEscapeString(src) + "</pre>\n", nil
		},
	}
	html, toc, err := renderMarkdown(src, hooks)
	if err != nil {
		t.Fatalf("%q: %v", src, err)
	}
	return html, toc
}

func TestMarkdownRenderer(t *testing.T) {
	cases := []struct{ src, want string }{
		{"Hello *world* and **bold** `<b>`.", "<p>Hello <em>world</em> and <strong>bold</strong> <code>&lt;b&gt;</code>.</p>\n"},
		{"snake_case_name and _em_", "<p>snake_case_name and <em>em</em></p>\n"},
		{"A [link](/docs) and [`code`](#x).", `<p>A <a href="/docs">link</a> and <a href="#x"><code>code</code></a>.</p>` + "\n"},
		{"<script>alert(1)</script>", "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>\n"},
		{"a\\*b\\* \\`c\\`", "<p>a*b* `c`</p>\n"},
		{"- one\n- two `x`", "<ul>\n<li>one</li>\n<li>two <code>x</code></li>\n</ul>\n"},
		{"1. one\n\n   ```sh\n   go test\n   ```\n2. two", "<ol>\n<li><p>one</p>\n<pre data-lang=\"sh\" title=\"\">go test</pre>\n</li>\n<li><p>two</p>\n</li>\n</ol>\n"},
		{"- a\n  - b", "<ul>\n<li>a<ul>\n<li>b</li>\n</ul>\n</li>\n</ul>\n"},
		{"| A | B |\n| --- | --- |\n| `x \\| y` | 2 |", "<div data-docs=\"table\" class=\"scroll-fade-x\"><table>\n<thead><tr><th>A</th><th>B</th></tr></thead>\n<tbody>\n<tr><td><code>x | y</code></td><td>2</td></tr>\n</tbody>\n</table></div>\n"},
		{"```css title=\"app.css\"\na { }\n```", "<pre data-lang=\"css\" title=\"app.css\">a { }</pre>\n"},
		{"> quote", "<blockquote>\n<p>quote</p>\n</blockquote>\n"},
		{"{{example \"button-demo\" align=\"start\"}}", "<x-example>button-demo</x-example>\n"},
		{"{{components \"new\"}}", "<x-list>new</x-list>\n"},
		{"---", "<hr>\n"},
	}
	for _, c := range cases {
		if got, _ := render(t, c.src); got != c.want {
			t.Errorf("%q\n got %q\nwant %q", c.src, got, c.want)
		}
	}
	html, toc := render(t, "## API Reference\n\n### Button\n\n## With `Icon`\n\n## API Reference\n\n#### Deep")
	want := []tocEntry{{2, "api-reference", "API Reference"}, {3, "button", "Button"}, {2, "with-icon", "With Icon"}, {2, "api-reference-1", "API Reference"}}
	if !slices.Equal(toc, want) {
		t.Errorf("toc %v, want %v", toc, want)
	}
	if !strings.Contains(html, `<h2 id="with-icon"><a href="#with-icon"><span>With <code>Icon</code></span><span aria-hidden="true">#</span></a></h2>`) {
		t.Errorf("heading markup: %s", html)
	}
	for _, bad := range []string{"[x](javascript:alert(1))", "[x](data:text/html,x)", "{{example}}", "{{components \"old\"}}", "```js\nx", "| a | b |\n| --- | --- |\n| 1 |", "    indented"} {
		if _, _, err := renderMarkdown(bad, mdHooks{example: func(string, map[string]string) (string, error) { return "", nil }, components: func(string) (string, error) { return "", nil }, code: func(string, string, string) (string, error) { return "", nil }}); err == nil {
			t.Errorf("accepted %q", bad)
		}
	}
	expanded := expandMarkdown("a\n{{example \"x\"}}\n```md\n{{example \"y\"}}\n```\n", func(tag mdTag) string { return "[" + tag.Arg + "]" })
	if expanded != "a\n[x]\n```md\n{{example \"y\"}}\n```\n" {
		t.Errorf("expanded %q", expanded)
	}
}

func TestHighlighter(t *testing.T) {
	join := func(lines []template.HTML) string {
		var b strings.Builder
		for i, l := range lines {
			if i > 0 {
				b.WriteString("\n")
			}
			b.WriteString(string(l))
		}
		return b.String()
	}
	cases := []struct{ lang, src, want string }{
		{"html", `<a href="/x">T&amp;</a>`, `<span class="tk-p">&lt;</span><span class="tk-t">a</span> <span class="tk-a">href</span>=<span class="tk-s">&#34;/x&#34;</span><span class="tk-p">&gt;</span>T<span class="tk-e">&amp;amp;</span><span class="tk-p">&lt;/</span><span class="tk-t">a</span><span class="tk-p">&gt;</span>`},
		{"html", "<!-- c\nd -->", `<span class="tk-c">&lt;!-- c</span>` + "\n" + `<span class="tk-c">d --&gt;</span>`},
		{"css", "a { color: #fff; --x: 1px }", `<span class="tk-t">a </span>{ <span class="tk-a">color</span>: <span class="tk-n">#fff</span>; <span class="tk-a">--x</span>: <span class="tk-n">1px</span> }`},
		{"js", `const a = f("x") // c`, `<span class="tk-k">const</span> a = <span class="tk-f">f</span>(<span class="tk-s">&#34;x&#34;</span>) <span class="tk-c">// c</span>`},
		{"json", `{"a": [1, true]}`, `{<span class="tk-a">&#34;a&#34;</span>: [<span class="tk-n">1</span>, <span class="tk-n">true</span>]}`},
		{"sh", "go test ./... # all\nX=1 run --flag $HOME", `<span class="tk-f">go</span> test ./... <span class="tk-c"># all</span>` + "\n" + `<span class="tk-v">X</span>=1 <span class="tk-f">run</span> <span class="tk-a">--flag</span> <span class="tk-v">$HOME</span>`},
		{"text", "<b>", "&lt;b&gt;"},
	}
	for _, c := range cases {
		if got := join(highlightHTML(c.lang, c.src)); got != c.want {
			t.Errorf("%s %q\n got %s\nwant %s", c.lang, c.src, got, c.want)
		}
	}
	for _, lang := range []string{"html", "css", "js", "json", "sh", "text"} {
		src := "a\n\n<b> \"x\" 'y' `z` /* c */ // d # e\n"
		lines := highlightHTML(lang, src)
		if len(lines) != 4 {
			t.Errorf("%s: %d lines, want 4", lang, len(lines))
		}
		text := regexp.MustCompile(`<[^>]*>`).ReplaceAllString(join(lines), "")
		if strings.NewReplacer("&lt;", "<", "&gt;", ">", "&#34;", `"`, "&#39;", "'", "&amp;", "&").Replace(text) != src {
			t.Errorf("%s: text changed: %q", lang, text)
		}
	}
}

func highlightWithin(t *testing.T, lang, src string) (lines []template.HTML) {
	t.Helper()
	done := make(chan struct{})
	var failure any
	go func() {
		defer close(done)
		defer func() { failure = recover() }()
		lines = highlightHTML(lang, src)
	}()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatalf("%s %q: the highlighter does not end", lang, src)
	}
	if failure != nil {
		t.Fatalf("%s %q: panic: %v", lang, src, failure)
	}
	return lines
}

func TestHighlighterEndsOnControlBytes(t *testing.T) {
	for _, c := range []struct{ lang, src string }{
		{"sh", "echo a\rb"},
		{"sh", "echo a\fb"},
		{"sh", "a\r\nb"},
		{"html", "<script>\xff\xfe</script>"},
		{"html", "<script>x</SCRIPT"},
		{"html", "<style>\xffa{}</style>"},
	} {
		highlightWithin(t, c.lang, c.src)
	}
}

func FuzzHighlight(f *testing.F) {
	for _, s := range []string{"a\rb", "x\f", "<script>\xff</script>", "<style>a{}</style>", "`x`", "$((1))", "a { b: #fff; --c: 1px }", `{"a": [1, true]}`} {
		f.Add(s)
	}
	tags := regexp.MustCompile(`<[^>]*>`)
	unescape := strings.NewReplacer("&lt;", "<", "&gt;", ">", "&#34;", `"`, "&#39;", "'", "&amp;", "&")
	f.Fuzz(func(t *testing.T, src string) {
		for _, lang := range []string{"html", "css", "js", "json", "sh"} {
			lines := highlightWithin(t, lang, src)
			parts := make([]string, len(lines))
			for i, l := range lines {
				parts[i] = string(l)
			}
			if text := unescape.Replace(tags.ReplaceAllString(strings.Join(parts, "\n"), "")); text != src {
				t.Fatalf("%s: text changed for %q", lang, src)
			}
		}
	})
}

func gunzip(t *testing.T, body []byte) string {
	t.Helper()
	r, err := gzip.NewReader(bytes.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	out, err := io.ReadAll(r)
	if err != nil {
		t.Fatal(err)
	}
	return string(out)
}

func TestGzip(t *testing.T) {
	for _, dir := range []string{"", "."} {
		h := newSite(dir).routes()
		d := docsOf(t)
		for _, path := range []string{"/docs/components/button", "/docs/components/button.md", "/", "/demo", "/clanker-ui.css", "/assets/" + d.hash + "/clanker-ui.js"} {
			plain := request(t, h, http.MethodGet, path)
			packed := request(t, h, http.MethodGet, path, "Accept-Encoding", "br, gzip;q=0.8")
			if plain.Code != http.StatusOK || packed.Code != http.StatusOK {
				t.Fatalf("dir %q %s: status %d and %d", dir, path, plain.Code, packed.Code)
			}
			if plain.Header().Get("Content-Encoding") != "" || !strings.Contains(plain.Header().Get("Vary"), "Accept-Encoding") {
				t.Errorf("dir %q %s: identity response: Content-Encoding %q, Vary %q", dir, path, plain.Header().Get("Content-Encoding"), plain.Header().Get("Vary"))
			}
			if packed.Header().Get("Content-Encoding") != "gzip" || !strings.Contains(packed.Header().Get("Vary"), "Accept-Encoding") {
				t.Errorf("dir %q %s: gzip response: Content-Encoding %q, Vary %q", dir, path, packed.Header().Get("Content-Encoding"), packed.Header().Get("Vary"))
				continue
			}
			if packed.Body.Len() >= plain.Body.Len() {
				t.Errorf("dir %q %s: gzip body %d is not smaller than %d", dir, path, packed.Body.Len(), plain.Body.Len())
			}
			if gunzip(t, packed.Body.Bytes()) != plain.Body.String() {
				t.Errorf("dir %q %s: gzip body differs from the identity body", dir, path)
			}
			checkSecurityHeaders(t, packed, path)
			tag := packed.Header().Get("ETag")
			if packed.Header().Get("Cache-Control") == "no-store" {
				continue
			}
			if tag == "" || tag == plain.Header().Get("ETag") || !strings.HasSuffix(tag, `-gz"`) {
				t.Errorf("dir %q %s: gzip ETag %q, identity ETag %q", dir, path, tag, plain.Header().Get("ETag"))
			}
			if rec := request(t, h, http.MethodGet, path, "Accept-Encoding", "gzip", "If-None-Match", tag); rec.Code != http.StatusNotModified {
				t.Errorf("dir %q %s: If-None-Match with the gzip ETag: status %d", dir, path, rec.Code)
			}
		}
		for _, enc := range []string{"gzip;q=0", "identity", "br"} {
			if rec := request(t, h, http.MethodGet, "/docs", "Accept-Encoding", enc); rec.Header().Get("Content-Encoding") != "" {
				t.Errorf("dir %q: Accept-Encoding %q gave Content-Encoding %q", dir, enc, rec.Header().Get("Content-Encoding"))
			}
		}
	}
}

func TestDocsNits(t *testing.T) {
	if _, err := loadDocs(docsFS(t, map[string]string{"docs/content/components/.DS_Store": "x", "docs/content/_draft/page.md": "x"})); err != nil {
		t.Errorf("dotfiles and _ files must be skipped: %v", err)
	}
	if got, _ := render(t, "0. zero\n1. one"); !strings.HasPrefix(got, `<ol start="0">`) {
		t.Errorf("ordered list from 0: %q", got)
	}
	if got, _ := render(t, "3. three"); !strings.HasPrefix(got, `<ol start="3">`) {
		t.Errorf("ordered list from 3: %q", got)
	}
	none := mdHooks{example: func(string, map[string]string) (string, error) { return "", nil }, components: func(string) (string, error) { return "", nil }, code: func(string, string, string) (string, error) { return "", nil }}
	for _, bad := range []string{"[a [b](/x) c](/y)", "[x](//evil.example/y)"} {
		if _, _, err := renderMarkdown(bad, none); err == nil {
			t.Errorf("accepted %q", bad)
		}
	}
	raw, err := os.ReadFile("docs/nav.json")
	if err != nil {
		t.Fatal(err)
	}
	nav := strings.Replace(string(raw), `{"title": "Home", "href": "/"}`, `{"title": "Home", "href": "//evil.example/"}`, 1)
	if nav == string(raw) {
		t.Fatal("nav.json has no Home item")
	}
	if _, err := loadDocs(docsFS(t, map[string]string{"docs/nav.json": nav})); err == nil {
		t.Error("nav.json accepted a protocol-relative href")
	}
	h := newSite("").routes()
	if rec := request(t, h, http.MethodGet, "/docs/components/?q=1"); rec.Code != http.StatusMovedPermanently || rec.Header().Get("Location") != "/docs/components?q=1" {
		t.Errorf("trailing slash redirect: status %d, Location %q", rec.Code, rec.Header().Get("Location"))
	}
	if rec := request(t, h, http.MethodGet, "/docs/components/typography?q=1"); rec.Code != http.StatusMovedPermanently || rec.Header().Get("Location") != "/docs/typography?q=1" || rec.Header().Get("Cache-Control") != "no-cache" {
		t.Errorf("typography redirect: status %d, Location %q, Cache-Control %q", rec.Code, rec.Header().Get("Location"), rec.Header().Get("Cache-Control"))
	}
	old := request(t, h, http.MethodGet, "/assets/000000000000/docs.css")
	if old.Code != http.StatusOK || old.Header().Get("Cache-Control") != "no-cache" {
		t.Errorf("asset with an old hash: status %d, Cache-Control %q", old.Code, old.Header().Get("Cache-Control"))
	}
}

func TestLiveModeReloadsOnlyAfterAChange(t *testing.T) {
	dir := t.TempDir()
	for name, file := range docsFS(t, nil) {
		target := filepath.Join(dir, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(target, file.Data, 0o644); err != nil {
			t.Fatal(err)
		}
	}
	s := newSite(dir)
	first, err := s.site()
	if err != nil {
		t.Fatal(err)
	}
	if again, _ := s.site(); again != first {
		t.Error("DIR mode loads all docs again without a change")
	}
	page := filepath.Join(dir, "docs", "content", "index", "page.md")
	if err := os.WriteFile(page, []byte("---\ntitle: Changed\ndescription: Changed.\n---\n\nNew text.\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	later := time.Now().Add(2 * time.Second)
	if err := os.Chtimes(page, later, later); err != nil {
		t.Fatal(err)
	}
	changed, err := s.site()
	if err != nil {
		t.Fatal(err)
	}
	if changed == first || changed.pages["/docs"].Title != "Changed" {
		t.Error("DIR mode does not show a changed page")
	}
}

func TestOneActiveSection(t *testing.T) {
	d := docsOf(t)
	for _, href := range navHrefs(t) {
		var active []string
		for _, l := range d.view("docs", href).Sidebar[0].Items {
			if l.Active {
				active = append(active, l.Title)
			}
		}
		if len(active) > 1 {
			t.Errorf("%s: Sections items %v are active", href, active)
		}
	}
}

func readmeAnchors(t *testing.T) map[string]bool {
	t.Helper()
	raw, err := os.ReadFile("README.md")
	if err != nil {
		t.Fatal(err)
	}
	out, fence := map[string]bool{}, false
	for _, line := range strings.Split(string(raw), "\n") {
		if strings.HasPrefix(line, "```") {
			fence = !fence
		}
		if !fence && strings.HasPrefix(line, "#") {
			out[slug(strings.TrimLeft(line, "#"))] = true
		}
	}
	return out
}

func TestEveryDocsPageIsReal(t *testing.T) {
	d := docsOf(t)
	anchors := readmeAnchors(t)
	h := newSite("").routes()
	generated := 0
	for _, href := range sortedKeys(d.titles) {
		if !strings.HasPrefix(href, "/docs") || docRedirects[href] != "" {
			continue
		}
		p := d.pages[href]
		if p == nil {
			t.Errorf("%s: no page", href)
			continue
		}
		body := request(t, h, http.MethodGet, href).Body.String()
		md := request(t, h, http.MethodGet, href+".md").Body.String()
		if strings.Contains(body, "not ported yet") || strings.Contains(md, "not ported yet") {
			t.Errorf("%s: page is a stub", href)
		}
		if c := d.components[href]; c != nil && p.Section != "" {
			generated++
			for _, want := range []string{"## Installation", "## Usage", "## API Reference", "{{example "} {
				if !strings.Contains(p.Source, want) {
					t.Errorf("%s: generated page has no %q", href, want)
				}
			}
			if !strings.Contains(body, `<div data-docs="content" id="`+p.Section+`">`) || !strings.Contains(body, "/demo.js\"></script>") {
				t.Errorf("%s: page does not host the demo section %s", href, p.Section)
			}
		}
	}
	if generated < 60 {
		t.Errorf("%d generated component pages with a demo, want at least 60", generated)
	}
	for href, u := range d.readme {
		anchor := strings.TrimPrefix(u, githubURL+"#")
		if !anchors[anchor] {
			t.Errorf("%s: README has no heading for #%s", href, anchor)
		}
	}
	install := d.pages["/docs/installation"]
	if install == nil || !strings.Contains(install.Source, "## Override the kit") || strings.Contains(install.Source, "## Markup conventions") {
		t.Error("/docs/installation does not have the README section and its subsections")
	}
}

var discoveryLink = regexp.MustCompile(`<link rel="(alternate" type="text/markdown|describedby)" href="([^"]+)">`)

func TestDocsPagesLinkMarkdownAndLLMs(t *testing.T) {
	d := docsOf(t)
	h := newSite("").routes()
	for _, href := range sortedKeys(d.titles) {
		if !strings.HasPrefix(href, "/docs") || docRedirects[href] != "" {
			continue
		}
		got := map[string]string{}
		for _, m := range discoveryLink.FindAllStringSubmatch(request(t, h, http.MethodGet, href).Body.String(), -1) {
			got[m[1]] = m[2]
		}
		if got["describedby"] != "/llms.txt" || got[`alternate" type="text/markdown`] != href+".md" {
			t.Errorf("%s: discovery links %v", href, got)
		}
		md := request(t, h, http.MethodGet, href+".md")
		if md.Code != http.StatusOK {
			t.Errorf("%s.md: status %d", href, md.Code)
		}
		if ref, ok := d.refs[href]; ok && d.pages[href] == nil && md.Body.String() != string(ref) {
			t.Errorf("%s.md is not the component reference", href)
		}
	}
	if rec := request(t, h, http.MethodGet, "/llms.txt"); rec.Code != http.StatusOK || rec.Header().Get("Content-Type") != contentTypes[".txt"] {
		t.Errorf("/llms.txt: status %d, Content-Type %q", rec.Code, rec.Header().Get("Content-Type"))
	}
	components := request(t, h, http.MethodGet, "/docs/components.md").Body.String()
	if n, want := strings.Count(components, ".md)\n"), len(d.componentLinks(""))+len(d.componentLinks("new")); n != want {
		t.Errorf("components.md has %d .md links, want %d", n, want)
	}
	if !strings.Contains(components, "- [Typography](/docs/typography.md)") {
		t.Error("components.md does not follow the typography redirect")
	}
}

func TestDocsFontsSelfHosted(t *testing.T) {
	h := newSite("").routes()
	d := docsOf(t)
	page := request(t, h, http.MethodGet, "/docs/components/button").Body.String()
	css, _ := os.ReadFile("docs/assets/fonts.css")
	for _, font := range []string{"geist-latin.woff2", "geist-mono-latin.woff2"} {
		url := "/assets/" + d.hash + "/" + font
		rec := request(t, h, http.MethodGet, url)
		if rec.Code != http.StatusOK || rec.Header().Get("Content-Type") != "font/woff2" || rec.Header().Get("Content-Encoding") != "" || !strings.HasPrefix(rec.Body.String(), "wOF2") {
			t.Errorf("%s: status %d, Content-Type %q, Content-Encoding %q", url, rec.Code, rec.Header().Get("Content-Type"), rec.Header().Get("Content-Encoding"))
		}
		if !strings.Contains(page, `<link rel="preload" href="`+url+`" as="font" type="font/woff2" crossorigin>`) {
			t.Errorf("page does not preload %s", font)
		}
		if !strings.Contains(string(css), `src: url("`+font+`") format("woff2");`) {
			t.Errorf("fonts.css has no @font-face for %s", font)
		}
	}
	for _, want := range []string{`--font-sans: "Geist", "Geist Fallback";`, `--font-mono: "Geist Mono", "Geist Mono Fallback";`} {
		if !strings.Contains(string(css), want) {
			t.Errorf("fonts.css has no %s", want)
		}
	}
	for name := range kitFiles {
		if b, _ := os.ReadFile(name); strings.Contains(string(b), "Geist") {
			t.Errorf("%s names Geist; the fonts are for the docs site only", name)
		}
	}
	notices, _ := os.ReadFile("THIRD_PARTY_NOTICES")
	if !strings.Contains(string(notices), "Copyright 2024 The Geist Project Authors") || !strings.Contains(string(notices), "SIL OPEN FONT LICENSE Version 1.1") {
		t.Error("THIRD_PARTY_NOTICES has no Geist OFL notice")
	}
}

func TestDocsMapTargets(t *testing.T) {
	d := docsOf(t)
	raw, err := os.ReadFile("tools/gen/docs-map.tsv")
	if err != nil {
		t.Fatal(err)
	}
	page := map[string]string{}
	for _, line := range strings.Split(strings.TrimSpace(string(raw)), "\n")[1:] {
		f := strings.Split(line, "\t")
		key, ours := f[0], f[1]
		item, name, isExample := strings.Cut(key, "#")
		switch {
		case ours == "-" || ours == "?":
		case !isExample:
			if d.pages[ours] == nil {
				t.Errorf("%s: %s is not a docs page", key, ours)
			}
			page[item] = ours
		case d.pages[page[item]] == nil:
			t.Errorf("%s: %s, but the page of %s has no match", key, ours, item)
		case !strings.Contains(d.pages[page[item]].Source, `{{example "`+ours+`"`):
			t.Errorf("%s: %s is not an example on %s (shadcn %s)", key, ours, page[item], name)
		}
	}
}

var (
	docsExampleRoot = regexp.MustCompile(`\[data-docs="(?:component-preview|preview|view)"\]`)
	docsOwnPart     = regexp.MustCompile(`\[data-docs="(?:code|code-block|code-teaser)"\]`)
	docsKitTarget   = regexp.MustCompile(`\[data-slot|(?:^|[\s>+~(])(?:pre|code|span|div|button|svg|a|p)\b`)
	docsNotGroup    = regexp.MustCompile(`:not\([^()]*(?:\([^()]*\)[^()]*)*\)`)
)

func TestDocsCSSLeavesExamplePartsAlone(t *testing.T) {
	css := regexp.MustCompile(`(?s)/\*.*?\*/`).ReplaceAllString(readText(t, "docs/assets/docs.css"), "")
	for _, m := range regexp.MustCompile(`([^{}]+)\{`).FindAllStringSubmatch(css, -1) {
		sel := strings.TrimSpace(m[1])
		if strings.HasPrefix(sel, "@") {
			continue
		}
		plain := docsNotGroup.ReplaceAllString(sel, "")
		loc := docsExampleRoot.FindStringIndex(plain)
		if loc == nil {
			continue
		}
		for _, rest := range docsAlternatives(plain[loc[1]:]) {
			if docsKitTarget.MatchString(rest) && !docsOwnPart.MatchString(rest) {
				t.Errorf("docs.css styles kit parts inside an example: %s", sel)
				break
			}
		}
	}
}

func docsAlternatives(sel string) []string {
	i := strings.Index(sel, ":is(")
	if i < 0 {
		return []string{sel}
	}
	depth, start, end := 0, i+4, -1
	var parts []string
	for j := i + 3; j < len(sel) && end < 0; j++ {
		switch sel[j] {
		case '(':
			depth++
		case ')':
			depth--
			if depth == 0 {
				parts = append(parts, sel[start:j])
				end = j
			}
		case ',':
			if depth == 1 {
				parts = append(parts, sel[start:j])
				start = j + 1
			}
		}
	}
	if end < 0 {
		return []string{sel}
	}
	var out []string
	for _, p := range parts {
		out = append(out, docsAlternatives(sel[:i]+" "+strings.TrimSpace(p)+sel[end+1:])...)
	}
	return out
}

func TestExampleClassesHaveRules(t *testing.T) {
	docsCSS := readText(t, "docs/assets/docs.css")
	for _, h := range previewHeights {
		if !strings.Contains(docsCSS, `[data-docs="preview"][data-height="`+h+`"] { height: `+h+`; }`) {
			t.Errorf("docs.css has no rule for the preview height %s", h)
		}
	}
	css := readText(t, "docs/assets/examples.css")
	esc := regexp.MustCompile(`[^A-Za-z0-9_-]`)
	class := regexp.MustCompile(`\sclass="([^"]*)"`)
	files, _ := filepath.Glob("docs/content/*/*/examples/*.html")
	more, _ := filepath.Glob("docs/content/*/examples/*.html")
	for _, f := range append(files, more...) {
		for _, m := range class.FindAllStringSubmatch(readText(t, f), -1) {
			for _, c := range strings.Fields(m[1]) {
				if !strings.Contains(css, "."+esc.ReplaceAllString(c, `\$0`)) {
					t.Errorf("%s: class %s has no rule in docs/assets/examples.css (go run ./tools/gen utilities, DEVELOPMENT.md Docs site)", f, c)
				}
			}
		}
	}
}
