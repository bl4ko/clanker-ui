package main

import (
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"embed"
	"encoding/hex"
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"net/http"
	"os"
	"path"
	"regexp"
	"slices"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

//go:embed clanker-ui* demo docs dist skills/clanker-ui
var embedded embed.FS

const csp = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; require-trusted-types-for 'script'"

var cspMeta = strings.Replace(csp, " frame-ancestors 'none';", "", 1)

var cspView = strings.Replace(csp, "frame-ancestors 'none'", "frame-ancestors 'self'", 1)

var kitFiles = map[string]bool{"clanker-ui.css": true, "clanker-ui-a11y.css": true, "clanker-ui.js": true, "clanker-ui-chart.js": true, "clanker-ui-theme.js": true, "clanker-ui-themes.css": true}

var distFile = regexp.MustCompile(`^clanker-ui[a-z0-9-]*\.min\.(css|js)$`)

var minKit = map[string]string{"clanker-ui.css": "dist/clanker-ui.min.css", "clanker-ui-themes.css": "dist/clanker-ui-themes.min.css", "clanker-ui-a11y.css": "dist/clanker-ui-a11y.min.css", "clanker-ui-theme.js": "dist/clanker-ui-theme.min.js"}

var minShims = map[string][]string{"clanker-ui.js": {"clanker-ui-core.min.js", "clanker-ui.min.js"}, "clanker-ui-chart.js": {"clanker-ui-chart.min.js"}}

var demoAsset = regexp.MustCompile(`^demo/(assets/)?[a-z0-9][a-z0-9-]*(\.[a-z0-9-]+)*\.(css|js|svg|png|jpg|webp|avif)$`)

var skillFile = regexp.MustCompile(`^skills/clanker-ui/(SKILL\.md|references/(components/)?[a-z0-9-]+(\.[a-z]+)?\.(md|json|js)|references/blocks/[a-z0-9-]+\.(html|js))$`)

var devFile = regexp.MustCompile(`^(test/spike/[a-z0-9-]+\.(html|css)|test/behavior/fixtures/[a-z0-9-]+\.(html|css|js)|test/split/[a-z0-9-]+\.(html|js)|test/lint/[a-z0-9-]+\.(html|css))$`)

var contentTypes = map[string]string{
	".css":  "text/css; charset=utf-8",
	".js":   "text/javascript; charset=utf-8",
	".html": "text/html; charset=utf-8",
	".md":   "text/markdown; charset=utf-8",
	".txt":  "text/plain; charset=utf-8",
	".json": "application/json",
	".svg":  "image/svg+xml",
	".png":  "image/png",
	".jpg":  "image/jpeg",
	".webp": "image/webp",
	".avif": "image/avif",
	".woff2": "font/woff2",
}

type site struct {
	fsys    fs.FS
	live    bool
	docs    *docsSite
	docsErr error
	mu      sync.Mutex
	liveSig string
}

func newSite(dir string) *site {
	return newKitSite(dir, "")
}

func newKitSite(dir, kit string) *site {
	var fsys fs.FS = embedded
	if dir != "" {
		fsys = os.DirFS(dir)
	}
	if kit == "min" {
		fsys = minFS{fsys}
	}
	s := &site{fsys: fsys, live: dir != ""}
	if !s.live {
		s.docs, s.docsErr = loadDocs(s.fsys)
	}
	return s
}

func distFiles(fsys fs.FS) []string {
	names, _ := fs.Glob(fsys, "dist/clanker-ui*.min.*")
	var out []string
	for _, name := range names {
		if distFile.MatchString(path.Base(name)) {
			out = append(out, name)
		}
	}
	return out
}

type minFS struct{ fs.FS }

func (m minFS) shim(name string) ([]byte, bool) {
	targets, ok := minShims[name]
	if !ok {
		return nil, false
	}
	src, _ := fs.ReadFile(m.FS, name)
	license, _, _ := strings.Cut(string(src), "\n")
	b := []byte(license + "\n")
	for _, t := range targets {
		b = fmt.Appendf(b, "export * from \"./%s\"\n", t)
	}
	return b, true
}

func (m minFS) Open(name string) (fs.File, error) {
	if t, ok := minKit[name]; ok {
		return m.FS.Open(t)
	}
	if b, ok := m.shim(name); ok {
		return &memFile{Reader: bytes.NewReader(b), name: name, size: int64(len(b))}, nil
	}
	return m.FS.Open(name)
}

func (m minFS) ReadFile(name string) ([]byte, error) {
	if t, ok := minKit[name]; ok {
		return fs.ReadFile(m.FS, t)
	}
	if b, ok := m.shim(name); ok {
		return b, nil
	}
	return fs.ReadFile(m.FS, name)
}

type memFile struct {
	*bytes.Reader
	name string
	size int64
}

func (f *memFile) Stat() (fs.FileInfo, error) { return f, nil }
func (f *memFile) Close() error               { return nil }
func (f *memFile) Name() string               { return path.Base(f.name) }
func (f *memFile) Size() int64                { return f.size }
func (f *memFile) Mode() fs.FileMode          { return 0o444 }
func (f *memFile) ModTime() time.Time         { return time.Time{} }
func (f *memFile) IsDir() bool                { return false }
func (f *memFile) Sys() any                   { return nil }

func (s *site) read(name string) ([]byte, error) {
	return fs.ReadFile(s.fsys, name)
}

func (s *site) site() (*docsSite, error) {
	if !s.live {
		return s.docs, s.docsErr
	}
	sig, err := sourceSignature(s.fsys)
	if err != nil {
		return nil, err
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.docs != nil && sig == s.liveSig {
		return s.docs, nil
	}
	d, err := loadDocs(s.fsys)
	if err != nil {
		return nil, err
	}
	s.docs, s.liveSig = d, sig
	return d, nil
}

func sourceSignature(fsys fs.FS) (string, error) {
	h := sha256.New()
	add := func(name string, info fs.FileInfo) {
		fmt.Fprintf(h, "%s\x00%d\x00%d\n", name, info.Size(), info.ModTime().UnixNano())
	}
	names := []string{"demo/index.html", "demo/demo.css", "demo/demo.js", exportExtras["clanker-ui.json"]}
	for name := range kitFiles {
		names = append(names, name)
	}
	names = append(names, distFiles(fsys)...)
	slices.Sort(names)
	for _, name := range names {
		if info, err := fs.Stat(fsys, name); err == nil {
			add(name, info)
		}
	}
	for _, root := range []string{"docs", blocksDir} {
		err := fs.WalkDir(fsys, root, func(name string, entry fs.DirEntry, err error) error {
			if err != nil || entry.IsDir() {
				return err
			}
			info, err := entry.Info()
			if err != nil {
				return err
			}
			add(name, info)
			return nil
		})
		if err != nil && !errors.Is(err, fs.ErrNotExist) {
			return "", err
		}
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

func main() {
	addr := flag.String("addr", env("ADDR", ":8080"), "listen address")
	dir := flag.String("dir", os.Getenv("DIR"), "serve the kit, demo, and docs from this directory instead of the embedded copy")
	kit := flag.String("kit", os.Getenv("KIT"), `"min": answer the readable kit file names with the dist/ minified files (test the minified kit)`)
	export := flag.String("export", "", "write the docs site as static files to this new directory")
	base := flag.String("base", "", `URL path of the exported site, for example /clanker-ui or /`)
	siteURL := flag.String("site-url", "", "full URL of the exported site, for sitemap.xml and the .md files")
	flag.Parse()
	if *export != "" {
		if *kit != "" {
			log.Fatal("-export writes the readable kit; remove -kit")
		}
		src := *dir
		if src == "" {
			src = "."
		}
		if err := exportSite(os.DirFS(src), *export, *base, *siteURL); err != nil {
			log.Fatal(err)
		}
		return
	}
	if *kit != "" && *kit != "min" {
		log.Fatalf("-kit must be empty or min, not %q", *kit)
	}
	s := newKitSite(*dir, *kit)
	if *kit == "min" && len(distFiles(s.fsys)) == 0 {
		log.Fatal("-kit min needs the dist/ files: go run ./tools/gen dist")
	}
	if _, err := s.site(); err != nil {
		log.Fatal(err)
	}
	server := &http.Server{
		Addr:              *addr,
		Handler:           s.routes(),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       60 * time.Second,
	}
	source := "embedded files"
	if *dir != "" {
		source = *dir
	}
	log.Printf("clanker-ui listening on %s, serving %s", *addr, source)
	log.Fatal(server.ListenAndServe())
}

func env(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func (s *site) routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusNoContent) })
	mux.HandleFunc("GET /{$}", s.home)
	mux.HandleFunc("GET /demo", s.demo)
	mux.HandleFunc("GET /docs", s.doc)
	mux.HandleFunc("GET /docs.md", s.doc)
	mux.HandleFunc("GET /docs/{path...}", s.doc)
	mux.HandleFunc("GET /assets/{hash}/{file}", s.asset)
	mux.HandleFunc("GET /view/{name}", s.view)
	mux.HandleFunc("GET /blocks/{file}", s.block)
	mux.HandleFunc("GET /", s.serve)
	return secure(mux)
}

var demoBlock = regexp.MustCompile(`(?m)^      <(?:section id="([a-z0-9-]+)" data-demo="[a-z]+"|h2 id="([a-z0-9-]+)" data-demo="category")>`)

func (s *site) demo(w http.ResponseWriter, r *http.Request) {
	only := r.URL.Query().Get("only")
	if only == "" {
		s.file(w, r, "demo/index.html")
		return
	}
	body, err := s.read("demo/index.html")
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	body, ok := demoOnly(body, strings.Split(only, ","))
	if !ok {
		http.Error(w, "unknown demo section", http.StatusBadRequest)
		return
	}
	cache := "no-cache"
	if s.live {
		cache = "no-store"
	}
	serveBytes(w, r, "index.html", contentTypes[".html"], body, cache)
}

func demoOnly(body []byte, only []string) ([]byte, bool) {
	var out []byte
	last, category, found := 0, "", 0
	for _, m := range demoBlock.FindAllSubmatchIndex(body, -1) {
		if m[4] >= 0 {
			category = string(body[m[4]:m[5]])
			if slices.Contains(only, category) {
				found++
			}
			continue
		}
		id := string(body[m[2]:m[3]])
		if slices.Contains(only, id) {
			found++
		} else if !slices.Contains(only, category) {
			out = append(append(out, body[last:m[1]-1]...), " hidden"...)
			last = m[1] - 1
		}
	}
	return append(out, body[last:]...), found == len(only)
}

func (s *site) serve(w http.ResponseWriter, r *http.Request) {
	name := strings.TrimPrefix(r.URL.Path, "/")
	if kitFiles[name] || demoAsset.MatchString(name) || (s.live && devFile.MatchString(name)) {
		s.file(w, r, name)
		return
	}
	if distFile.MatchString(name) {
		s.file(w, r, "dist/"+name)
		return
	}
	if skillFile.MatchString(name) {
		s.file(w, r, name)
		return
	}
	if from, ok := exportExtras[name]; ok {
		s.file(w, r, from)
		return
	}
	s.notFound(w, r)
}

func (s *site) file(w http.ResponseWriter, r *http.Request, name string) {
	body, err := s.read(name)
	if errors.Is(err, fs.ErrNotExist) {
		http.NotFound(w, r)
		return
	}
	if err != nil {
		log.Printf("read %s: %v", name, err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	cache := "no-cache"
	if s.live {
		cache = "no-store"
	}
	serveBytes(w, r, name, contentTypes[path.Ext(name)], body, cache)
}

func etag(body []byte) string {
	sum := sha256.Sum256(body)
	return `"` + hex.EncodeToString(sum[:16]) + `"`
}

var (
	gzipCache   sync.Map
	gzipEntries atomic.Int64
)

func compressible(contentType string) bool {
	return strings.HasPrefix(contentType, "text/") || strings.HasPrefix(contentType, "image/svg+xml")
}

func acceptsGzip(r *http.Request) bool {
	gzipQ, anyQ := -1.0, -1.0
	for _, part := range strings.Split(r.Header.Get("Accept-Encoding"), ",") {
		name, params, _ := strings.Cut(part, ";")
		q := 1.0
		for _, param := range strings.Split(params, ";") {
			if v, ok := strings.CutPrefix(strings.TrimSpace(param), "q="); ok {
				if f, err := strconv.ParseFloat(v, 64); err == nil {
					q = f
				}
			}
		}
		switch strings.ToLower(strings.TrimSpace(name)) {
		case "gzip":
			gzipQ = q
		case "*":
			anyQ = q
		}
	}
	if gzipQ >= 0 {
		return gzipQ > 0
	}
	return anyQ > 0
}

func gzipped(key string, body []byte) []byte {
	if v, ok := gzipCache.Load(key); ok {
		return v.([]byte)
	}
	var b bytes.Buffer
	zw, _ := gzip.NewWriterLevel(&b, gzip.BestCompression)
	zw.Write(body)
	zw.Close()
	if gzipEntries.Add(1) <= 1024 {
		gzipCache.Store(key, b.Bytes())
	}
	return b.Bytes()
}

func serveBytes(w http.ResponseWriter, r *http.Request, name, contentType string, body []byte, cache string) {
	h := w.Header()
	h.Set("Content-Type", contentType)
	h.Set("Cache-Control", cache)
	tag := etag(body)
	if compressible(contentType) {
		h.Add("Vary", "Accept-Encoding")
		if acceptsGzip(r) {
			body = gzipped(tag, body)
			h.Set("Content-Encoding", "gzip")
			tag = strings.TrimSuffix(tag, `"`) + `-gz"`
		}
	}
	if cache != "no-store" {
		h.Set("ETag", tag)
	}
	http.ServeContent(w, r, name, time.Time{}, bytes.NewReader(body))
}

func secure(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		h := w.Header()
		h.Set("Content-Security-Policy", csp)
		h.Set("X-Content-Type-Options", "nosniff")
		h.Set("Referrer-Policy", "no-referrer")
		h.Set("Cross-Origin-Opener-Policy", "same-origin")
		next.ServeHTTP(w, r)
	})
}
