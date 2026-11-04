package main

import (
	"bytes"
	"errors"
	"fmt"
	"html"
	"io/fs"
	"net/http"
	"path"
	"regexp"
	"strings"
)

const blocksDir = "skills/clanker-ui/references/blocks"

type block struct {
	Name string
	HTML string
	JS   string
}

var (
	blockName    = regexp.MustCompile(`^[a-z0-9]+(-[a-z0-9]+)*$`)
	blockVendor  = regexp.MustCompile(`"/vendor/clanker-ui/([a-z0-9.-]+)"`)
	blockCharset = []byte(`<meta charset="utf-8">`)
)

func (d *docsSite) loadBlocks(fsys fs.FS) error {
	d.blocks = map[string]*block{}
	entries, err := fs.ReadDir(fsys, blocksDir)
	if errors.Is(err, fs.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	for _, entry := range entries {
		ext := path.Ext(entry.Name())
		name := strings.TrimSuffix(entry.Name(), ext)
		if entry.IsDir() || !blockName.MatchString(name) || ext != ".html" && ext != ".js" {
			return fmt.Errorf("%s/%s: blocks are <name>.html with an optional <name>.js", blocksDir, entry.Name())
		}
		raw, err := fs.ReadFile(fsys, blocksDir+"/"+entry.Name())
		if err != nil {
			return err
		}
		b := d.blocks[name]
		if b == nil {
			b = &block{Name: name}
			d.blocks[name] = b
		}
		text := strings.ReplaceAll(string(raw), "\r\n", "\n")
		if ext == ".html" {
			b.HTML = text
		} else {
			b.JS = text
		}
	}
	for name, b := range d.blocks {
		if b.HTML == "" {
			return fmt.Errorf("%s/%s.js has no %s.html", blocksDir, name, name)
		}
		for _, m := range blockVendor.FindAllStringSubmatch(b.HTML+b.JS, -1) {
			if _, ok := d.assets[m[1]]; !ok {
				return fmt.Errorf("block %s: /vendor/clanker-ui/%s is not a kit file", name, m[1])
			}
		}
		script := `src="/` + name + `.js"`
		if (b.JS != "") != strings.Contains(b.HTML, script) {
			return fmt.Errorf("block %s: the page must load its module with %s exactly when %s.js exists", name, script, name)
		}
	}
	return nil
}

func (d *docsSite) blockURL(name string) string {
	return d.urls.url("/blocks/" + name)
}

func (d *docsSite) blockSource(b *block, src string) []byte {
	out := blockVendor.ReplaceAllStringFunc(src, func(m string) string {
		u, _ := d.assetURL(blockVendor.FindStringSubmatch(m)[1])
		return `"` + u + `"`
	})
	if b.JS != "" {
		out = strings.Replace(out, `src="/`+b.Name+`.js"`, `src="`+d.urls.base+`/blocks/`+b.Name+`.js"`, 1)
	}
	return []byte(out)
}

func (d *docsSite) blockPage(b *block) []byte {
	body := d.blockSource(b, b.HTML)
	meta := fmt.Appendf(nil, "%s\n  <meta http-equiv=\"Content-Security-Policy\" content=\"%s\">\n  <meta name=\"referrer\" content=\"no-referrer\">", blockCharset, html.EscapeString(cspMeta))
	return bytes.Replace(body, blockCharset, meta, 1)
}

type blockView struct {
	Name  string
	Title string
	URL   string
	HTML  codeView
	JS    *codeView
}

func (d *docsSite) blockView(name string) (blockView, error) {
	b := d.blocks[name]
	if b == nil {
		return blockView{}, fmt.Errorf("unknown block %q", name)
	}
	v := blockView{Name: name, Title: d.titles["/docs/blocks/"+name], URL: d.blockURL(name), HTML: codeView{Lang: "html", Title: name + ".html", Lines: highlightHTML("html", b.HTML)}}
	if b.JS != "" {
		v.JS = &codeView{Lang: "js", Title: name + ".js", Lines: highlightHTML("js", b.JS)}
	}
	return v, nil
}

func (s *site) block(w http.ResponseWriter, r *http.Request) {
	d := s.docsOr500(w)
	if d == nil {
		return
	}
	file := r.PathValue("file")
	if name, ok := strings.CutSuffix(file, ".js"); ok {
		if b := d.blocks[name]; b != nil && b.JS != "" {
			serveBytes(w, r, file, contentTypes[".js"], d.blockSource(b, b.JS), "no-cache")
			return
		}
		d.notFound(w, r)
		return
	}
	b := d.blocks[file]
	if b == nil {
		d.notFound(w, r)
		return
	}
	w.Header().Set("Content-Security-Policy", cspView)
	serveBytes(w, r, file+".html", contentTypes[".html"], d.blockPage(b), "no-cache")
}

func (e *exporter) blocks() error {
	for _, name := range sortedKeys(e.d.blocks) {
		if err := e.copy("/blocks/"+name, pageFile("/blocks/"+name)); err != nil {
			return err
		}
		if e.d.blocks[name].JS != "" {
			if err := e.copy("/blocks/"+name+".js", "blocks/"+name+".js"); err != nil {
				return err
			}
		}
	}
	return nil
}

func (d *docsSite) blockDocPage(href, name string) *docPage {
	desc := d.descriptions[href]
	if desc == "" {
		desc = d.titles[href] + "."
	}
	src := fmt.Sprintf("{{block %q}}\n\n## Use it\n\n1. Copy `%s.html`", name, name)
	if d.blocks[name].JS != "" {
		src += fmt.Sprintf(" and `%s.js`", name)
	}
	src += " into the app. The page loads the one-file set from `/vendor/clanker-ui/` ([Installation](/docs/installation)).\n2. Replace the sample content and keep the structure. The block uses only kit parts and needs no app CSS.\n3. Follow the [design rules](" + githubURL + "/blob/main/skills/clanker-ui/references/design.md) and check the page at 1280 and 390 px, in light and dark.\n"
	return &docPage{Href: href, Title: d.titles[href], Description: desc, Source: src}
}
