package main

import (
	"bytes"
	"cmp"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"html/template"
	"io/fs"
	"log"
	"net/http"
	"path"
	"regexp"
	"slices"
	"strings"
)

const (
	contentRoot = "docs/content"
	githubURL   = "https://github.com/bl4ko/clanker-ui"
)

var (
	exampleName    = regexp.MustCompile(`^[a-z0-9]+(-[a-z0-9]+)*$`)
	previewHeights = []string{"auto", "10rem", "12rem", "14rem", "16rem", "18rem", "20rem", "24rem", "24.5rem", "26rem", "30rem", "32rem", "34rem", "300px", "435px", "450px", "560px", "600px", "650px"}
	docsAssets     = []string{"docs.css", "docs.js", "docs-sidebar.js", "examples.css", "fonts.css", "geist-latin.woff2", "geist-mono-latin.woff2"}
)

type navItem struct {
	Title       string `json:"title"`
	Href        string `json:"href"`
	New         bool   `json:"new,omitempty"`
	Hidden      bool   `json:"hidden,omitempty"`
	MobileOnly  bool   `json:"mobileOnly,omitempty"`
	Readme      string `json:"readme,omitempty"`
	Description string `json:"description,omitempty"`
	Style       string `json:"style,omitempty"`
	Scheme      string `json:"scheme,omitempty"`
}

type navGroup struct {
	Title string    `json:"title"`
	Items []navItem `json:"items"`
}

type navConfig struct {
	Header         []navItem  `json:"header"`
	Sections       []navItem  `json:"sections"`
	MobileSections []navItem  `json:"mobileSections"`
	Groups         []navGroup `json:"groups"`
}

type example struct {
	Name string
	HTML string
	Code string
	JS   string
	Demo bool
}

type docPage struct {
	Href        string
	Title       string
	Description string
	Source      string
	HTML        template.HTML
	TOC         []tocEntry
	Examples    []string
	Section     string
	Styles      []string
	Scripts     []string
	Wide        bool
	reserved    []string
}

type docsSite struct {
	nav          navConfig
	pages        map[string]*docPage
	examples     map[string]*example
	order        []navItem
	titles       map[string]string
	assets       map[string][]byte
	hash         string
	tmpl         *template.Template
	readme       map[string]string
	descriptions map[string]string
	refs         map[string][]byte
	urls         siteURLs
	catalog      catalogData
	components   map[string]*catalogComponent
	demo         map[string]*demoSection
	anchors      map[string]string
	sectionPage  map[string]string
	blocks       map[string]*block
	previews     map[string]navItem
	styles       []string
}

type siteURLs struct {
	base   string
	site   string
	static bool
}

func (u siteURLs) path(href string) string {
	p, rest := href, ""
	if i := strings.IndexAny(href, "?#"); i >= 0 {
		p, rest = href[:i], href[i:]
	}
	if u.static && !strings.HasSuffix(p, "/") && path.Ext(p) == "" {
		p += "/"
	}
	return p + rest
}

func (u siteURLs) url(href string) string {
	if !strings.HasPrefix(href, "/") || strings.HasPrefix(href, "//") {
		return href
	}
	return u.base + u.path(href)
}

func (u siteURLs) abs(href string) string {
	if u.site == "" || !strings.HasPrefix(href, "/") || strings.HasPrefix(href, "//") {
		return href
	}
	return u.site + u.path(href)
}

func loadDocs(fsys fs.FS) (*docsSite, error) {
	return loadDocsAt(fsys, siteURLs{})
}

func loadDocsAt(fsys fs.FS, urls siteURLs) (*docsSite, error) {
	d := &docsSite{urls: urls, pages: map[string]*docPage{}, examples: map[string]*example{}, assets: map[string][]byte{}, titles: map[string]string{}, readme: map[string]string{}, descriptions: map[string]string{}, refs: map[string][]byte{}}
	raw, err := fs.ReadFile(fsys, "docs/nav.json")
	if err != nil {
		return nil, err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&d.nav); err != nil {
		return nil, fmt.Errorf("docs/nav.json: %w", err)
	}
	for name := range kitFiles {
		if d.assets[name], err = fs.ReadFile(fsys, name); err != nil {
			return nil, err
		}
	}
	for _, name := range distFiles(fsys) {
		if d.assets[path.Base(name)], err = fs.ReadFile(fsys, name); err != nil {
			return nil, err
		}
	}
	for _, name := range docsAssets {
		if d.assets[name], err = fs.ReadFile(fsys, "docs/assets/"+name); err != nil {
			return nil, err
		}
	}
	if err := d.loadContent(fsys); err != nil {
		return nil, err
	}
	if err := d.loadCatalog(fsys); err != nil {
		return nil, err
	}
	if err := d.loadStyles(fsys); err != nil {
		return nil, err
	}
	if err := d.loadDemoAssets(fsys); err != nil {
		return nil, err
	}
	if err := d.loadBlocks(fsys); err != nil {
		return nil, err
	}
	d.hash = assetHash(d.assets)
	d.tmpl, err = template.New("").Funcs(template.FuncMap{"asset": d.assetURL, "url": d.urls.url, "csp": func() string { return cspMeta }}).ParseFS(fsys, "docs/templates/*.html")
	if err != nil {
		return nil, err
	}
	if err := d.buildOrder(); err != nil {
		return nil, err
	}
	if err := d.generatePages(fsys); err != nil {
		return nil, err
	}
	for _, href := range sortedKeys(d.pages) {
		if err := d.renderPage(d.pages[href]); err != nil {
			return nil, fmt.Errorf("%s: %w", href, err)
		}
	}
	return d, nil
}

func sortedKeys[V any](m map[string]V) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	slices.Sort(keys)
	return keys
}

func assetHash(assets map[string][]byte) string {
	h := sha256.New()
	for _, name := range sortedKeys(assets) {
		fmt.Fprintf(h, "%s\x00%d\x00", name, len(assets[name]))
		h.Write(assets[name])
	}
	return hex.EncodeToString(h.Sum(nil))[:12]
}

func (d *docsSite) assetURL(name string) (string, error) {
	if _, ok := d.assets[name]; !ok {
		return "", fmt.Errorf("unknown asset %q", name)
	}
	return d.urls.base + "/assets/" + d.hash + "/" + name, nil
}

func contentHref(dir string) string {
	if dir == "index" {
		return "/docs"
	}
	return "/docs/" + dir
}

func (d *docsSite) loadContent(fsys fs.FS) error {
	return fs.WalkDir(fsys, contentRoot, func(name string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if base := path.Base(name); name != contentRoot && (strings.HasPrefix(base, ".") || strings.HasPrefix(base, "_")) {
			if entry.IsDir() {
				return fs.SkipDir
			}
			return nil
		}
		if entry.IsDir() {
			return nil
		}
		rel := strings.TrimPrefix(name, contentRoot+"/")
		dir, base := path.Split(rel)
		dir = strings.TrimSuffix(dir, "/")
		switch {
		case base == "page.md":
			return d.loadPage(fsys, name, contentHref(dir))
		case path.Base(dir) == "examples" && (path.Ext(base) == ".html" || path.Ext(base) == ".js"):
			return d.loadExample(fsys, name)
		}
		return fmt.Errorf("%s: unexpected file in %s", name, contentRoot)
	})
}

func (d *docsSite) loadDemoAssets(fsys fs.FS) error {
	for name, rewrite := range map[string]bool{"demo.css": false, "demo.js": true} {
		b, err := fs.ReadFile(fsys, "demo/"+name)
		if errors.Is(err, fs.ErrNotExist) {
			continue
		}
		if err != nil {
			return err
		}
		if rewrite {
			b = bytes.ReplaceAll(b, []byte(`from "../clanker-ui`), []byte(`from "./clanker-ui`))
		}
		d.assets[name] = b
	}
	return nil
}

func (d *docsSite) loadPage(fsys fs.FS, name, href string) error {
	raw, err := fs.ReadFile(fsys, name)
	if err != nil {
		return err
	}
	front, body, err := frontMatter(string(raw))
	if err != nil {
		return fmt.Errorf("%s: %w", name, err)
	}
	if front["title"] == "" || front["description"] == "" {
		return fmt.Errorf("%s: front matter needs title and description", name)
	}
	d.pages[href] = &docPage{Href: href, Title: front["title"], Description: front["description"], Source: body}
	return nil
}

func (d *docsSite) loadExample(fsys fs.FS, name string) error {
	raw, err := fs.ReadFile(fsys, name)
	if err != nil {
		return err
	}
	ext := path.Ext(name)
	id := strings.TrimSuffix(path.Base(name), ext)
	if !exampleName.MatchString(id) {
		return fmt.Errorf("%s: example names use lower case words and dashes", name)
	}
	if _, ok := d.assets[id+".js"]; ok && ext == ".js" {
		return fmt.Errorf("%s: name is taken by an asset", name)
	}
	ex := d.examples[id]
	if ex == nil {
		ex = &example{Name: id}
		d.examples[id] = ex
	}
	text := strings.Trim(strings.ReplaceAll(string(raw), "\r\n", "\n"), "\n")
	switch {
	case ext == ".html" && ex.HTML == "":
		ex.HTML = d.siteRelative(text)
	case ext == ".js" && ex.JS == "":
		ex.JS = text
		d.assets[id+".js"] = raw
	default:
		return fmt.Errorf("%s: example %q exists twice", name, id)
	}
	return nil
}

func frontMatter(src string) (map[string]string, string, error) {
	src = strings.ReplaceAll(src, "\r\n", "\n")
	rest, ok := strings.CutPrefix(src, "---\n")
	if !ok {
		return nil, "", errors.New("page must start with front matter")
	}
	head, body, ok := strings.Cut(rest, "\n---\n")
	if !ok {
		return nil, "", errors.New("front matter is not closed")
	}
	out := map[string]string{}
	for _, line := range strings.Split(head, "\n") {
		key, value, ok := strings.Cut(line, ":")
		if !ok {
			return nil, "", fmt.Errorf("bad front matter line %q", line)
		}
		key = strings.TrimSpace(key)
		if key != "title" && key != "description" {
			return nil, "", fmt.Errorf("unknown front matter key %q", key)
		}
		out[key] = strings.Trim(strings.TrimSpace(value), `"`)
	}
	return out, strings.TrimLeft(body, "\n"), nil
}

func (d *docsSite) buildOrder() error {
	seen := map[string]bool{}
	all := slices.Concat(d.nav.Header, d.nav.Sections, d.nav.MobileSections)
	for _, g := range d.nav.Groups {
		all = append(all, g.Items...)
		for _, item := range g.Items {
			if !seen[item.Href] {
				seen[item.Href] = true
				d.order = append(d.order, item)
			}
		}
	}
	for _, item := range all {
		if item.Title == "" || !strings.HasPrefix(item.Href, "/") || strings.HasPrefix(item.Href, "//") || strings.ContainsAny(item.Href, "#?\\") {
			return fmt.Errorf("docs/nav.json: bad item %+v", item)
		}
		if _, ok := d.titles[item.Href]; !ok || d.titles[item.Href] == "" {
			d.titles[item.Href] = item.Title
		}
		if item.Readme != "" {
			d.readme[item.Href] = githubURL + "#" + item.Readme
		}
		if item.Description != "" {
			d.descriptions[item.Href] = item.Description
		}
	}
	for href := range d.pages {
		if _, ok := d.titles[href]; !ok {
			return fmt.Errorf("%s has no entry in docs/nav.json", href)
		}
	}
	return nil
}

func (d *docsSite) renderPage(p *docPage) error {
	hooks := mdHooks{
		example: func(name string, attrs map[string]string) (string, error) {
			ex := d.examples[name]
			if ex == nil {
				return "", fmt.Errorf("unknown example %q", name)
			}
			for key, value := range attrs {
				ok := key == "align" && slices.Contains([]string{"center", "start", "end"}, value) || key == "height" && slices.Contains(previewHeights, value) || key == "style" && slices.Contains(d.styles, value) || key == "scheme" && d.hasScheme(value)
				if !ok {
					return "", fmt.Errorf("example %q: bad attribute %s=%q", name, key, value)
				}
			}
			p.Examples = append(p.Examples, name)
			v := exampleView(ex, attrs)
			def := d.previews[p.Href]
			v.Style, v.Scheme = cmp.Or(attrs["style"], def.Style), cmp.Or(attrs["scheme"], def.Scheme)
			if len(d.styles) > 0 && v.Style == d.styles[0] {
				v.Style = ""
			}
			if v.Scheme != "" && !slices.Contains(p.Styles, "clanker-ui-themes.css") {
				p.Styles = append(p.Styles, "clanker-ui-themes.css")
			}
			if v.Style != "" && !slices.Contains(p.Styles, "style-"+v.Style+".css") {
				p.Styles = append(p.Styles, "style-"+v.Style+".css")
			}
			return d.exec("example", v)
		},
		block: func(name string) (string, error) {
			v, err := d.blockView(name)
			if err != nil {
				return "", err
			}
			p.Wide = true
			return d.exec("block", v)
		},
		reserved: p.reserved,
		components: func(variant string) (string, error) {
			links := d.componentLinks(variant)
			for i := range links {
				links[i].Href = d.urls.url(links[i].Href)
			}
			return d.exec("components-list", links)
		},
		link: d.urls.url,
		code: func(lang, title, src string) (string, error) {
			return d.exec("code", codeView{Lang: lang, Title: title, Lines: highlightHTML(lang, src)})
		},
	}
	html, toc, err := renderMarkdown(p.Source, hooks)
	if err != nil {
		return err
	}
	p.HTML, p.TOC = template.HTML(html), toc
	return nil
}

func (d *docsSite) exec(name string, data any) (string, error) {
	var b bytes.Buffer
	if err := d.tmpl.ExecuteTemplate(&b, name, data); err != nil {
		return "", err
	}
	return b.String(), nil
}

type codeView struct {
	Lang  string
	Title string
	Lines []template.HTML
}

type exampleData struct {
	Name    string
	Align   string
	Height  string
	Style   string
	Scheme  string
	Preview template.HTML
	Teaser  []template.HTML
	Code    codeView
	Script  *codeView
}

func exampleView(ex *example, attrs map[string]string) exampleData {
	lines := highlightHTML("html", ex.source())
	v := exampleData{
		Name:    ex.Name,
		Align:   attrs["align"],
		Height:  attrs["height"],
		Preview: template.HTML(ex.HTML),
		Teaser:  lines[:min(3, len(lines))],
		Code:    codeView{Lang: "html", Lines: lines},
	}
	if ex.Demo && v.Height == "" {
		v.Height = "demo"
	}
	if ex.JS != "" {
		v.Code.Title = ex.Name + ".html"
		v.Script = &codeView{Lang: "js", Title: ex.Name + ".js", Lines: highlightHTML("js", ex.JS)}
	}
	return v
}

func (ex *example) source() string {
	if ex.Code != "" {
		return ex.Code
	}
	return ex.HTML
}

type link struct {
	Title     string
	Href      string
	Active    bool
	Current   bool
	New       bool
	Value     string
	Keywords  string
	Component bool
}

type group struct {
	Title string
	Items []link
}

func (d *docsSite) componentLinks(variant string) []link {
	var out []link
	for _, g := range d.nav.Groups {
		if g.Title != "Components" {
			continue
		}
		for _, item := range g.Items {
			if item.Hidden || variant == "new" && !item.New {
				continue
			}
			out = append(out, link{Title: item.Title, Href: item.Href, New: item.New})
		}
	}
	return out
}

func (d *docsSite) markdown(p *docPage) string {
	var b strings.Builder
	fmt.Fprintf(&b, "---\ntitle: %s\ndescription: %s\n---\n\n", p.Title, p.Description)
	b.WriteString(expandMarkdown(mdLinks(p.Source, d.urls.abs), func(tag mdTag) string {
		if tag.Name == "components" {
			var list strings.Builder
			for _, l := range d.componentLinks(tag.Arg) {
				href := l.Href
				if to, ok := docRedirects[href]; ok {
					href = to
				}
				fmt.Fprintf(&list, "- [%s](%s)\n", l.Title, d.urls.abs(href+".md"))
			}
			return strings.TrimSuffix(list.String(), "\n")
		}
		if tag.Name == "block" {
			b := d.blocks[tag.Arg]
			out := "```html title=\"" + b.Name + ".html\"\n" + strings.TrimRight(b.HTML, "\n") + "\n```"
			if b.JS != "" {
				out += "\n\n```js title=\"" + b.Name + ".js\"\n" + strings.TrimRight(b.JS, "\n") + "\n```"
			}
			return out
		}
		ex := d.examples[tag.Arg]
		out := "```html\n" + ex.source() + "\n```"
		if ex.JS != "" {
			out += "\n\n```js\n" + ex.JS + "\n```"
		}
		return out
	}))
	return b.String()
}

func (d *docsSite) markdownFor(href string) ([]byte, bool) {
	if p := d.pages[href]; p != nil {
		return []byte(d.markdown(p)), true
	}
	return nil, false
}

type pageView struct {
	Kind        string
	Title       string
	Description string
	Header      []link
	Sidebar     []group
	Mobile      []group
	Search      []group
	Page        *docPage
	Prev, Next  *link
	Modules     []string
	Styles      []string
	Markdown    string
	Alternate   string
	GitHub      string
	Status      int
}

func (d *docsSite) view(kind, current string) *pageView {
	v := &pageView{Kind: kind, GitHub: githubURL, Status: http.StatusOK}
	for _, item := range d.nav.Header {
		v.Header = append(v.Header, link{Title: item.Title, Href: d.urls.url(item.Href), Current: item.Href == current})
	}
	sections := group{Title: "Sections"}
	for _, item := range d.nav.Sections {
		active := item.Href == current || item.Href != "/docs" && strings.HasPrefix(current, item.Href+"/")
		sections.Items = append(sections.Items, link{Title: item.Title, Href: d.urls.url(item.Href), Active: active, Current: item.Href == current, New: item.New})
	}
	v.Sidebar = append(v.Sidebar, sections)
	menu := group{Title: "Menu"}
	pages := group{Title: "Pages"}
	for _, item := range d.nav.Header {
		menu.Items = append(menu.Items, link{Title: item.Title, Href: d.urls.url(item.Href), Current: item.Href == current})
		pages.Items = append(pages.Items, link{Title: item.Title, Href: d.urls.url(item.Href), Value: "Navigation " + item.Title, Keywords: "nav, navigation, " + strings.ToLower(item.Title)})
	}
	mobileSections := group{Title: "Sections"}
	for _, item := range d.nav.MobileSections {
		mobileSections.Items = append(mobileSections.Items, link{Title: item.Title, Href: d.urls.url(item.Href), Current: item.Href == current, New: item.New})
	}
	v.Mobile = append(v.Mobile, menu, mobileSections)
	v.Search = append(v.Search, pages)
	for _, g := range d.nav.Groups {
		side, mobile, search := group{Title: g.Title}, group{Title: g.Title}, group{Title: g.Title}
		for _, item := range g.Items {
			if item.Hidden {
				continue
			}
			l := link{Title: item.Title, Href: d.urls.url(item.Href), Active: item.Href == current, Current: item.Href == current, New: item.New}
			if !item.MobileOnly {
				side.Items = append(side.Items, l)
			}
			mobile.Items = append(mobile.Items, l)
			component := strings.HasPrefix(item.Href, "/docs/components/")
			s := link{Title: item.Title, Href: d.urls.url(item.Href), Value: g.Title + " " + item.Title, Component: component}
			if component {
				s.Keywords = "component"
			}
			search.Items = append(search.Items, s)
		}
		v.Sidebar = append(v.Sidebar, side)
		v.Mobile = append(v.Mobile, mobile)
		v.Search = append(v.Search, search)
	}
	for i, item := range d.order {
		if item.Href != current {
			continue
		}
		if i > 0 {
			v.Prev = &link{Title: d.order[i-1].Title, Href: d.urls.url(d.order[i-1].Href)}
		}
		if i+1 < len(d.order) {
			v.Next = &link{Title: d.order[i+1].Title, Href: d.urls.url(d.order[i+1].Href)}
		}
		break
	}
	return v
}

func (d *docsSite) docView(href string) (*pageView, bool) {
	p := d.pages[href]
	if p == nil {
		return nil, false
	}
	v := d.view("docs", href)
	v.Title, v.Description, v.Page = p.Title, p.Description, p
	v.Markdown = d.urls.url(href + ".md")
	v.Alternate = v.Markdown
	v.Styles = p.Styles
	seen := map[string]bool{}
	for _, name := range p.Examples {
		if d.examples[name].JS != "" && !seen[name] {
			seen[name] = true
			v.Modules = append(v.Modules, name+".js")
		}
	}
	v.Modules = append(v.Modules, p.Scripts...)
	return v, true
}

func (s *site) docsOr500(w http.ResponseWriter) *docsSite {
	d, err := s.site()
	if err != nil {
		log.Printf("docs: %v", err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		return nil
	}
	return d
}

func (s *site) home(w http.ResponseWriter, r *http.Request) {
	d := s.docsOr500(w)
	if d == nil {
		return
	}
	v := d.view("home", "/")
	v.Title = "clanker-ui"
	v.Description = "A dependency-free port of shadcn/ui for plain HTML, CSS, and JavaScript."
	d.render(w, r, v)
}

var docRedirects = map[string]string{"/docs/components/typography": "/docs/typography"}

func (s *site) doc(w http.ResponseWriter, r *http.Request) {
	d := s.docsOr500(w)
	if d == nil {
		return
	}
	href := strings.TrimSuffix(r.URL.Path, "/")
	if href != r.URL.Path {
		if r.URL.RawQuery != "" {
			href += "?" + r.URL.RawQuery
		}
		w.Header().Set("Cache-Control", "no-cache")
		http.Redirect(w, r, href, http.StatusMovedPermanently)
		return
	}
	if to, ok := docRedirects[href]; ok {
		if r.URL.RawQuery != "" {
			to += "?" + r.URL.RawQuery
		}
		w.Header().Set("Cache-Control", "no-cache")
		http.Redirect(w, r, to, http.StatusMovedPermanently)
		return
	}
	if md, ok := strings.CutSuffix(href, ".md"); ok {
		body, ok := d.markdownFor(md)
		if !ok {
			d.notFound(w, r)
			return
		}
		serveBytes(w, r, md+".md", contentTypes[".md"], body, "no-cache")
		return
	}
	v, ok := d.docView(href)
	if !ok {
		d.notFound(w, r)
		return
	}
	d.render(w, r, v)
}

func (s *site) notFound(w http.ResponseWriter, r *http.Request) {
	if d := s.docsOr500(w); d != nil {
		d.notFound(w, r)
	}
}

func (d *docsSite) notFound(w http.ResponseWriter, r *http.Request) {
	v := d.view("not-found", r.URL.Path)
	v.Title = "Page not found"
	v.Description = "The page does not exist."
	v.Status = http.StatusNotFound
	d.render(w, r, v)
}

func (s *site) view(w http.ResponseWriter, r *http.Request) {
	d := s.docsOr500(w)
	if d == nil {
		return
	}
	ex := d.examples[r.PathValue("name")]
	if ex == nil {
		d.notFound(w, r)
		return
	}
	w.Header().Set("Content-Security-Policy", cspView)
	v := &pageView{Kind: "view", Title: ex.Name, Description: ex.Name, Status: http.StatusOK}
	v.Page = &docPage{HTML: template.HTML(ex.HTML)}
	if ex.JS != "" {
		v.Modules = []string{ex.Name + ".js"}
	}
	d.render(w, r, v)
}

func (s *site) asset(w http.ResponseWriter, r *http.Request) {
	d := s.docsOr500(w)
	if d == nil {
		return
	}
	name := r.PathValue("file")
	body, ok := d.assets[name]
	if !ok {
		http.NotFound(w, r)
		return
	}
	cache := "public, max-age=31536000, immutable"
	switch {
	case s.live:
		cache = "no-store"
	case r.PathValue("hash") != d.hash:
		cache = "no-cache"
	}
	serveBytes(w, r, name, contentTypes[path.Ext(name)], body, cache)
}

func (d *docsSite) render(w http.ResponseWriter, r *http.Request, v *pageView) {
	var b bytes.Buffer
	if err := d.tmpl.ExecuteTemplate(&b, "page", v); err != nil {
		log.Printf("render %s: %v", r.URL.Path, err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	if v.Status != http.StatusOK {
		h := w.Header()
		h.Set("Content-Type", contentTypes[".html"])
		h.Set("Cache-Control", "no-cache")
		w.WriteHeader(v.Status)
		w.Write(b.Bytes())
		return
	}
	serveBytes(w, r, "page.html", contentTypes[".html"], b.Bytes(), "no-cache")
}
