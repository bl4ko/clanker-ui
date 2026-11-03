package main

import (
	"bytes"
	"encoding/xml"
	"errors"
	"fmt"
	"html"
	"io/fs"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path"
	"regexp"
	"slices"
	"strings"
)

var (
	exportBasePath = regexp.MustCompile(`^(/[A-Za-z0-9._~-]+)*$`)
	exportTag      = regexp.MustCompile(`<[A-Za-z][^<>]*>`)
	tagURL         = regexp.MustCompile(`\s(href|src)="([^"]*)"`)
	relativeURL    = regexp.MustCompile(`^[A-Za-z0-9._~-][^:]*$`)
)

var exportExtras = map[string]string{
	"llms.txt":               "docs/llms.txt",
	"llms-full.txt":          "docs/llms-full.txt",
	"clanker-ui.json":        "skills/clanker-ui/references/clanker-ui.json",
	"clanker-ui.schema.json": "skills/clanker-ui/references/clanker-ui.schema.json",
}

const exportSkill = "skills/clanker-ui"

type exporter struct {
	fsys  fs.FS
	root  *os.Root
	h     http.Handler
	d     *docsSite
	urls  siteURLs
	pages []string
}

func exportOptions(base, siteURL string) (siteURLs, error) {
	base = strings.TrimRight(base, "/")
	if !exportBasePath.MatchString(base) || base != "" && path.Clean(base) != base {
		return siteURLs{}, fmt.Errorf("-base %q must be a URL path such as /clanker-ui or /", base)
	}
	u, err := url.Parse(siteURL)
	if err != nil || (u.Scheme != "https" && u.Scheme != "http") || u.Host == "" || u.RawQuery != "" || u.Fragment != "" || u.User != nil {
		return siteURLs{}, fmt.Errorf("-site-url %q must be a full http or https URL", siteURL)
	}
	return siteURLs{base: base, site: strings.TrimRight(siteURL, "/"), static: true}, nil
}

func exportSite(fsys fs.FS, out, base, siteURL string) error {
	urls, err := exportOptions(base, siteURL)
	if err != nil {
		return err
	}
	if entries, err := os.ReadDir(out); err == nil && len(entries) > 0 {
		return fmt.Errorf("%s is not empty", out)
	}
	if err := os.MkdirAll(out, 0o755); err != nil {
		return err
	}
	root, err := os.OpenRoot(out)
	if err != nil {
		return err
	}
	defer root.Close()
	d, err := loadDocsAt(fsys, urls)
	if err != nil {
		return err
	}
	e := &exporter{fsys: fsys, root: root, h: (&site{fsys: fsys, docs: d}).routes(), d: d, urls: urls}
	for _, step := range []func() error{e.docPages, e.files, e.demo, e.notFound, e.extras, e.sitemap} {
		if err := step(); err != nil {
			return err
		}
	}
	return nil
}

func (e *exporter) write(name string, body []byte) error {
	if dir := path.Dir(name); dir != "." {
		if err := e.root.MkdirAll(dir, 0o755); err != nil {
			return err
		}
	}
	return e.root.WriteFile(name, body, 0o644)
}

func (e *exporter) get(target string, want int) (*httptest.ResponseRecorder, error) {
	rec := httptest.NewRecorder()
	e.h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, target, nil))
	if rec.Code != want {
		return nil, fmt.Errorf("export %s: status %d, want %d", target, rec.Code, want)
	}
	return rec, nil
}

func (e *exporter) copy(target, name string) error {
	rec, err := e.get(target, http.StatusOK)
	if err != nil {
		return err
	}
	return e.write(name, rec.Body.Bytes())
}

func pageFile(href string) string {
	return strings.TrimPrefix(path.Join(href, "index.html"), "/")
}

func (e *exporter) docPages() error {
	hrefs := sortedKeys(e.d.titles)
	if !slices.Contains(hrefs, "/") {
		hrefs = append([]string{"/"}, hrefs...)
	}
	for _, href := range hrefs {
		if href == "/demo" {
			continue
		}
		if path.Clean(href) != href {
			return fmt.Errorf("docs/nav.json: href %q is not clean", href)
		}
		if _, ok := docRedirects[href]; ok {
			continue
		}
		if href != "/" && e.d.pages[href] == nil {
			continue
		}
		if err := e.copy(href, pageFile(href)); err != nil {
			return err
		}
		if href == "/" || e.d.pages[href] != nil {
			e.pages = append(e.pages, href)
		}
		if href == "/docs" || strings.HasPrefix(href, "/docs/") {
			if err := e.copy(href+".md", strings.TrimPrefix(href, "/")+".md"); err != nil {
				return err
			}
		}
	}
	for _, from := range sortedKeys(docRedirects) {
		if err := e.write(pageFile(from), e.redirect(docRedirects[from])); err != nil {
			return err
		}
	}
	return nil
}

func (e *exporter) redirect(to string) []byte {
	target, canonical := html.EscapeString(e.urls.url(to)), html.EscapeString(e.urls.abs(to))
	return fmt.Appendf(nil, `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="%s">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="refresh" content="0; url=%s">
  <link rel="canonical" href="%s">
  <title>Moved - clanker-ui</title>
</head>
<body>
  <p>This page moved to <a href="%s">%s</a>.</p>
</body>
</html>
`, html.EscapeString(cspMeta), target, canonical, target, canonical)
}

func (e *exporter) files() error {
	for _, name := range sortedKeys(e.d.assets) {
		if err := e.copy("/assets/"+e.d.hash+"/"+name, "assets/"+e.d.hash+"/"+name); err != nil {
			return err
		}
	}
	for _, name := range sortedKeys(kitFiles) {
		if err := e.copy("/"+name, name); err != nil {
			return err
		}
	}
	for _, name := range distFiles(e.fsys) {
		if err := e.copy("/"+path.Base(name), path.Base(name)); err != nil {
			return err
		}
		if err := e.copy("/"+path.Base(name), name); err != nil {
			return err
		}
	}
	return e.write(".nojekyll", nil)
}

func (e *exporter) demo() error {
	src, err := fs.ReadFile(e.fsys, "demo/index.html")
	if err != nil {
		return err
	}
	charset := []byte(`<meta charset="utf-8">`)
	if !bytes.Contains(src, charset) {
		return errors.New("demo/index.html: no <meta charset> to put the CSP after")
	}
	meta := fmt.Appendf(nil, "%s\n  <meta http-equiv=\"Content-Security-Policy\" content=\"%s\">\n  <meta name=\"referrer\" content=\"no-referrer\">", charset, html.EscapeString(cspMeta))
	src = bytes.Replace(src, charset, meta, 1)
	src = exportTag.ReplaceAllFunc(src, func(tag []byte) []byte {
		return tagURL.ReplaceAllFunc(tag, func(attr []byte) []byte {
			m := tagURL.FindSubmatch(attr)
			if !relativeURL.Match(m[2]) {
				return attr
			}
			return fmt.Appendf(nil, ` %s="%s/%s"`, m[1], e.urls.base, m[2])
		})
	})
	if err := e.write("demo/index.html", src); err != nil {
		return err
	}
	e.pages = append(e.pages, "/demo")
	return fs.WalkDir(e.fsys, "demo", func(name string, entry fs.DirEntry, err error) error {
		if err != nil || entry.IsDir() || !demoAsset.MatchString(name) {
			return err
		}
		return e.copy("/"+name, name)
	})
}

func (e *exporter) notFound() error {
	rec, err := e.get("/404.html", http.StatusNotFound)
	if err != nil {
		return err
	}
	return e.write("404.html", rec.Body.Bytes())
}

func (e *exporter) extras() error {
	for _, to := range sortedKeys(exportExtras) {
		if err := e.copyFile(exportExtras[to], to); err != nil {
			return err
		}
	}
	err := fs.WalkDir(e.fsys, exportSkill, func(name string, entry fs.DirEntry, err error) error {
		if err != nil || entry.IsDir() {
			return err
		}
		return e.copyFile(name, name)
	})
	if errors.Is(err, fs.ErrNotExist) {
		return nil
	}
	return err
}

func (e *exporter) copyFile(from, to string) error {
	b, err := fs.ReadFile(e.fsys, from)
	if errors.Is(err, fs.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	return e.write(to, b)
}

func (e *exporter) sitemap() error {
	var b bytes.Buffer
	b.WriteString(xml.Header + `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">` + "\n")
	slices.Sort(e.pages)
	for _, href := range e.pages {
		b.WriteString("  <url><loc>")
		xml.EscapeText(&b, []byte(e.urls.abs(href)))
		b.WriteString("</loc></url>\n")
	}
	b.WriteString("</urlset>\n")
	return e.write("sitemap.xml", b.Bytes())
}
