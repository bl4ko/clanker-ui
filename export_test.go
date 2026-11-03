package main

import (
	"html"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"testing"
	"testing/fstest"
)

type overlayFS struct {
	fs.FS
	extra fstest.MapFS
	hide  string
}

func (o overlayFS) Open(name string) (fs.File, error) {
	if name == o.hide {
		return nil, &fs.PathError{Op: "open", Path: name, Err: fs.ErrNotExist}
	}
	if _, ok := o.extra[name]; ok {
		return o.extra.Open(name)
	}
	return o.FS.Open(name)
}

var (
	cspMetaTag = regexp.MustCompile(`<meta http-equiv="Content-Security-Policy" content="([^"]*)">`)
	firstLoad  = regexp.MustCompile(`<(link|script|style)[\s>]`)
	sitemapLoc = regexp.MustCompile(`<loc>([^<]*)</loc>`)
	siteLink   = regexp.MustCompile(`https://bl4ko\.github\.io/clanker-ui(/[A-Za-z0-9._~/#-]*[A-Za-z0-9_~/-])?`)
)

const exportSiteURL = "https://bl4ko.github.io/clanker-ui/"

func exportTo(t *testing.T, fsys fs.FS, base string) string {
	t.Helper()
	out := filepath.Join(t.TempDir(), "site")
	if err := exportSite(fsys, out, base, exportSiteURL); err != nil {
		t.Fatal(err)
	}
	return out
}

func exportedFile(out, urlPath string) bool {
	if i := strings.IndexAny(urlPath, "?#"); i >= 0 {
		urlPath = urlPath[:i]
	}
	name := filepath.Join(out, filepath.FromSlash(urlPath))
	if strings.HasSuffix(urlPath, "/") {
		name = filepath.Join(name, "index.html")
	}
	info, err := os.Stat(name)
	return err == nil && !info.IsDir()
}

func TestExportSite(t *testing.T) {
	src := os.DirFS(".")
	d, err := loadDocs(os.DirFS("."))
	if err != nil {
		t.Fatal(err)
	}
	for _, base := range []string{"/clanker-ui/", "/clanker-ui", "/", ""} {
		t.Run("base="+base, func(t *testing.T) {
			prefix := strings.TrimRight(base, "/")
			out := exportTo(t, src, base)
			for href := range d.titles {
				if !exportedFile(out, href+"/") {
					t.Errorf("nav link %s has no %s", href, pageFile(href))
				}
			}
			for _, name := range []string{"index.html", "404.html", "sitemap.xml", "demo/index.html", "docs.md", "docs/components/button.md", "clanker-ui.css", "clanker-ui.js", "dist/clanker-ui.min.css", "clanker-ui.min.css", "assets/" + d.hash + "/docs.js"} {
				if _, err := os.Stat(filepath.Join(out, name)); err != nil {
					t.Errorf("%s is not exported", name)
				}
			}
			pages := 0
			err := filepath.WalkDir(out, func(name string, entry fs.DirEntry, err error) error {
				if err != nil || entry.IsDir() {
					return err
				}
				rel, _ := filepath.Rel(out, name)
				rel = filepath.ToSlash(rel)
				b, err := os.ReadFile(name)
				if err != nil {
					return err
				}
				if strings.Contains(string(b), "not ported yet") {
					t.Errorf("%s is a stub page", rel)
				}
				switch path.Ext(rel) {
				case ".html":
					pages++
					checkExportedPage(t, out, rel, string(b), prefix)
				case ".md":
					if strings.Contains(string(b), "](/") {
						t.Errorf("%s has a root-relative link, want %s links", rel, exportSiteURL)
					}
				}
				return nil
			})
			if err != nil {
				t.Fatal(err)
			}
			if pages < len(d.titles) {
				t.Errorf("%d HTML pages, want at least %d", pages, len(d.titles))
			}
			sitemap, _ := os.ReadFile(filepath.Join(out, "sitemap.xml"))
			locs := sitemapLoc.FindAllStringSubmatch(string(sitemap), -1)
			if len(locs) != len(d.pages)+2 {
				t.Errorf("sitemap has %d URLs, want %d (pages, home, demo)", len(locs), len(d.pages)+2)
			}
			for _, m := range locs {
				rest, ok := strings.CutPrefix(m[1], strings.TrimSuffix(exportSiteURL, "/"))
				href := strings.TrimSuffix(rest, "/")
				if !ok || !exportedFile(out, rest) || d.pages[href] == nil && href != "" && href != "/demo" {
					t.Errorf("sitemap URL %s is not a real exported page", m[1])
				}
			}
			if _, err := os.Stat(filepath.Join(out, "robots.txt")); !os.IsNotExist(err) {
				t.Errorf("robots.txt is exported: %v", err)
			}
			if len(d.refs) < 67 {
				t.Errorf("%d component reference files, want at least 67", len(d.refs))
			}
			for href, ref := range d.refs {
				b, err := os.ReadFile(filepath.Join(out, filepath.FromSlash(href+".md")))
				if err != nil || d.pages[href] == nil && string(b) != string(ref) || strings.Contains(string(b), "not ported yet") {
					t.Errorf("%s.md is not the page or the component reference: %v", href, err)
				}
			}
			for to, from := range exportExtras {
				want, err := fs.ReadFile(src, from)
				if err != nil {
					continue
				}
				if got, _ := os.ReadFile(filepath.Join(out, to)); string(got) != string(want) {
					t.Errorf("%s is not a copy of %s", to, from)
				}
			}
			checkSiteLinks(t, out)
		})
	}
}

func checkSiteLinks(t *testing.T, out string) {
	t.Helper()
	err := filepath.WalkDir(out, func(name string, entry fs.DirEntry, err error) error {
		if err != nil || entry.IsDir() || !slices.Contains([]string{".txt", ".md", ".json"}, path.Ext(name)) {
			return err
		}
		b, err := os.ReadFile(name)
		for _, m := range siteLink.FindAllStringSubmatch(string(b), -1) {
			if m[1] != "" && !exportedFile(out, m[1]) {
				rel, _ := filepath.Rel(out, name)
				t.Errorf("%s: %s has no exported file", rel, m[0])
			}
		}
		return err
	})
	if err != nil {
		t.Fatal(err)
	}
}

func TestExportExtras(t *testing.T) {
	llms := []byte("# clanker-ui\n")
	src := overlayFS{os.DirFS("."), fstest.MapFS{"docs/llms.txt": {Data: llms}}, "docs/llms-full.txt"}
	out := exportTo(t, src, "/clanker-ui")
	if b, _ := os.ReadFile(filepath.Join(out, "llms.txt")); string(b) != string(llms) {
		t.Errorf("llms.txt = %q, want the docs/llms.txt source", b)
	}
	if _, err := os.Stat(filepath.Join(out, "llms-full.txt")); !os.IsNotExist(err) {
		t.Errorf("llms-full.txt is exported with no source: %v", err)
	}
	for _, name := range []string{"clanker-ui.json", "clanker-ui.schema.json", "skills/clanker-ui/SKILL.md", "skills/clanker-ui/references/clanker-ui.json"} {
		if _, err := os.Stat(filepath.Join(out, name)); err != nil {
			t.Errorf("%s is not exported: %v", name, err)
		}
	}
}

func checkExportedPage(t *testing.T, out, rel, page, prefix string) {
	t.Helper()
	metas := cspMetaTag.FindAllStringSubmatchIndex(page, -1)
	if len(metas) != 1 {
		t.Errorf("%s: %d CSP meta tags, want 1", rel, len(metas))
		return
	}
	policy := html.UnescapeString(page[metas[0][2]:metas[0][3]])
	if policy != cspMeta {
		t.Errorf("%s: CSP meta %q, want %q", rel, policy, cspMeta)
	}
	if strings.Contains(policy, "frame-ancestors") {
		t.Errorf("%s: CSP meta has frame-ancestors", rel)
	}
	if i := firstLoad.FindStringIndex(page); i == nil || i[0] < metas[0][1] {
		t.Errorf("%s: a link, script, or style comes before the CSP meta", rel)
	}
	for _, tag := range exportTag.FindAllString(page, -1) {
		for _, m := range tagURL.FindAllStringSubmatch(tag, -1) {
			u := html.UnescapeString(m[2])
			switch {
			case strings.HasPrefix(u, "#"), strings.HasPrefix(u, "data:"), strings.HasPrefix(u, "https://"), strings.HasPrefix(u, "mailto:"):
				continue
			case !strings.HasPrefix(u, prefix+"/") || strings.HasPrefix(u, "//"):
				t.Errorf("%s: %s=%q does not start with the base path %q", rel, m[1], u, prefix+"/")
			case !exportedFile(out, strings.TrimPrefix(u, prefix)):
				t.Errorf("%s: %s=%q has no exported file", rel, m[1], u)
			}
		}
	}
}

func TestExportOptions(t *testing.T) {
	for _, c := range []struct{ base, site string }{
		{"clanker-ui", exportSiteURL},
		{"/clanker ui", exportSiteURL},
		{"/../x", exportSiteURL},
		{`/x"`, exportSiteURL},
		{"/clanker-ui", ""},
		{"/clanker-ui", "bl4ko.github.io/clanker-ui"},
		{"/clanker-ui", "javascript:alert(1)"},
	} {
		if _, err := exportOptions(c.base, c.site); err == nil {
			t.Errorf("exportOptions(%q, %q) accepted", c.base, c.site)
		}
	}
	u, err := exportOptions("/clanker-ui/", exportSiteURL)
	if err != nil || u.base != "/clanker-ui" || u.site != "https://bl4ko.github.io/clanker-ui" {
		t.Errorf("exportOptions = %+v, %v", u, err)
	}
	for href, want := range map[string]string{"/": "/clanker-ui/", "/docs": "/clanker-ui/docs/", "/docs.md": "/clanker-ui/docs.md", "/demo#tabs": "/clanker-ui/demo/#tabs", "#x": "#x", "https://ui.shadcn.com": "https://ui.shadcn.com"} {
		if got := u.url(href); got != want {
			t.Errorf("url(%q) = %q, want %q", href, got, want)
		}
	}
	dir := t.TempDir()
	os.WriteFile(filepath.Join(dir, "keep"), nil, 0o644)
	if err := exportSite(os.DirFS("."), dir, "/", exportSiteURL); err == nil {
		t.Error("export into a non-empty directory was accepted")
	}
}

func TestServerPagesHaveCSPMeta(t *testing.T) {
	h := newSite("").routes()
	for _, p := range []string{"/", "/docs", "/docs/components/button", "/docs/components/accordion", "/docs/nope"} {
		rec := request(t, h, "GET", p)
		m := cspMetaTag.FindStringSubmatch(rec.Body.String())
		if m == nil || html.UnescapeString(m[1]) != cspMeta {
			t.Errorf("%s: no CSP meta equal to the header policy without frame-ancestors", p)
		}
		if got := rec.Header().Get("Content-Security-Policy"); got != csp {
			t.Errorf("%s: header CSP %q, want %q", p, got, csp)
		}
	}
}
