package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"crypto/sha1"
	"crypto/sha512"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"strings"
)

const (
	novaFile    = "apps/v4/registry/styles/style-nova.css"
	globalsFile = "apps/v4/app/globals.css"
	twFile      = "packages/shadcn/src/tailwind.css"
	themesFile  = "apps/v4/registry/themes.ts"
	animateTgz  = "tw-animate-css.tgz"
	animateCSS  = "package/dist/tw-animate.css"
)

var fixedFiles = []string{novaFile, globalsFile, twFile, themesFile}

type pinned struct {
	files   map[string]string
	ui      []string
	animate string
}

func (p *pinned) read(rel string) (string, error) {
	s, ok := p.files[rel]
	if !ok {
		return "", fmt.Errorf("%s is not a pinned input", rel)
	}
	return s, nil
}

func blobSHA1(b []byte) string {
	h := sha1.New()
	fmt.Fprintf(h, "blob %d\x00", len(b))
	h.Write(b)
	return hex.EncodeToString(h.Sum(nil))
}

func parsePin(text string) (map[string]string, error) {
	out := map[string]string{}
	lines := strings.Split(strings.TrimRight(text, "\n"), "\n")
	if len(lines) == 0 || lines[0] != "commit\t"+shadcnSHA {
		return nil, fmt.Errorf("pin: first line must be \"commit\\t%s\" (the shadcnSHA constant)", shadcnSHA)
	}
	for i, line := range lines[1:] {
		path, sum, ok := strings.Cut(line, "\t")
		if !ok || path == "" || len(sum) != 40 || strings.Contains(path, "..") || strings.HasPrefix(path, "/") {
			return nil, fmt.Errorf("pin line %d: want <path><TAB><git blob sha1>", i+2)
		}
		if _, dup := out[path]; dup {
			return nil, fmt.Errorf("pin line %d: %s twice", i+2, path)
		}
		out[path] = sum
	}
	for _, f := range fixedFiles {
		if out[f] == "" {
			return nil, fmt.Errorf("pin: %s is missing", f)
		}
	}
	return out, nil
}

func formatPin(sums map[string]string) string {
	var b strings.Builder
	fmt.Fprintf(&b, "commit\t%s\n", shadcnSHA)
	for _, path := range sortedKeys(sums) {
		fmt.Fprintf(&b, "%s\t%s\n", path, sums[path])
	}
	return b.String()
}

func loadPinned(src, pinPath string) (*pinned, error) {
	text, err := os.ReadFile(pinPath)
	if err != nil {
		return nil, err
	}
	pin, err := parsePin(string(text))
	if err != nil {
		return nil, err
	}
	p := &pinned{files: map[string]string{}}
	for _, path := range sortedKeys(pin) {
		b, err := os.ReadFile(filepath.Join(src, filepath.FromSlash(path)))
		if err != nil {
			return nil, fmt.Errorf("pinned input: %w (download the inputs with: go run ./tools/gen fetch -src NEW_EMPTY_DIR)", err)
		}
		if got := blobSHA1(b); got != pin[path] {
			return nil, fmt.Errorf("%s: git blob %s, pin %s; the file is not the one at shadcn %s", path, got, pin[path], shadcnSHA)
		}
		p.files[path] = string(b)
		if name, ok := strings.CutPrefix(path, uiDir+"/"); ok {
			p.ui = append(p.ui, strings.TrimSuffix(name, ".tsx"))
		}
	}
	entries, err := os.ReadDir(filepath.Join(src, filepath.FromSlash(uiDir)))
	if err != nil {
		return nil, err
	}
	for _, e := range entries {
		if !strings.HasSuffix(e.Name(), ".tsx") {
			continue
		}
		if _, ok := pin[uiDir+"/"+e.Name()]; !ok {
			return nil, fmt.Errorf("%s/%s is not in the pin", uiDir, e.Name())
		}
	}
	tgz, err := os.ReadFile(filepath.Join(src, animateTgz))
	if err != nil {
		return nil, fmt.Errorf("%w (download the inputs with: go run ./tools/gen fetch -src NEW_EMPTY_DIR)", err)
	}
	files, err := untarAnimate(tgz)
	if err != nil {
		return nil, err
	}
	p.animate = files[animateCSS]
	return p, nil
}

func untarAnimate(data []byte) (map[string]string, error) {
	sum := sha512.Sum512(data)
	if got := base64.StdEncoding.EncodeToString(sum[:]); got != twAnimateSHA512 {
		return nil, fmt.Errorf("tw-animate-css: sha512 %s, want %s", got, twAnimateSHA512)
	}
	zr, err := gzip.NewReader(bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	tr := tar.NewReader(zr)
	out := map[string]string{}
	for {
		h, err := tr.Next()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return nil, err
		}
		if h.Name == animateCSS || h.Name == "package/LICENSE" {
			body, err := io.ReadAll(io.LimitReader(tr, 1<<20))
			if err != nil {
				return nil, err
			}
			out[h.Name] = string(body)
		}
	}
	if out[animateCSS] == "" {
		return nil, fmt.Errorf("tw-animate-css: %s is missing", animateCSS)
	}
	return out, nil
}

type gitTree struct {
	Tree []struct {
		Path string `json:"path"`
		Type string `json:"type"`
		Sha  string `json:"sha"`
	} `json:"tree"`
	Truncated bool `json:"truncated"`
}

func treeFiles(b []byte) (map[string]string, []string, error) {
	var t gitTree
	if err := json.Unmarshal(b, &t); err != nil {
		return nil, nil, fmt.Errorf("tree.json: %w", err)
	}
	if t.Truncated {
		return nil, nil, fmt.Errorf("tree.json: the GitHub tree is truncated; the file list is not complete")
	}
	blobs := map[string]string{}
	var files, docs []string
	for _, e := range t.Tree {
		if e.Type != "blob" {
			continue
		}
		blobs[e.Path] = e.Sha
		if name, ok := strings.CutPrefix(e.Path, uiDir+"/"); ok && !strings.Contains(name, "/") && strings.HasSuffix(name, ".tsx") {
			files = append(files, e.Path)
		}
		if docsFile(e.Path) {
			docs = append(docs, e.Path)
		}
	}
	slices.Sort(files)
	slices.Sort(docs)
	return blobs, slices.Concat(fixedFiles, files, docs), nil
}

func curl(url, dest string) error {
	if err := os.MkdirAll(filepath.Dir(dest), 0o755); err != nil {
		return err
	}
	out, err := exec.Command("curl", "-sSfL", "--proto", "=https", "--proto-redir", "=https", "--max-time", "60", "-o", dest, url).CombinedOutput()
	if err != nil {
		return fmt.Errorf("%s: %v %s", url, err, out)
	}
	return nil
}

func fetch(dir, pinPath string, writePin bool) error {
	if dir == "" {
		return fmt.Errorf("set -src")
	}
	if entries, _ := os.ReadDir(dir); len(entries) > 0 {
		return fmt.Errorf("%s is not empty", dir)
	}
	tree := filepath.Join(dir, "tree.json")
	if err := curl("https://api.github.com/repos/shadcn-ui/ui/git/trees/"+shadcnSHA+"?recursive=1", tree); err != nil {
		return err
	}
	b, err := os.ReadFile(tree)
	if err != nil {
		return err
	}
	blobs, files, err := treeFiles(b)
	if err != nil {
		return err
	}
	sums := map[string]string{}
	var manifest strings.Builder
	for _, f := range files {
		dest := filepath.Join(dir, filepath.FromSlash(f))
		if err := curl("https://raw.githubusercontent.com/shadcn-ui/ui/"+shadcnSHA+"/"+f, dest); err != nil {
			return err
		}
		body, err := os.ReadFile(dest)
		if err != nil {
			return err
		}
		got := blobSHA1(body)
		if want := blobs[f]; got != want {
			return fmt.Errorf("%s: git blob %s, tree %q", f, got, want)
		}
		sums[f] = got
		fmt.Fprintf(&manifest, "%s\t%s\t%d\n", f, got, len(body))
	}
	if err := os.WriteFile(filepath.Join(dir, "manifest.tsv"), []byte(manifest.String()), 0o644); err != nil {
		return err
	}
	if writePin {
		if err := os.WriteFile(pinPath, []byte(formatPin(sums)), 0o644); err != nil {
			return err
		}
	} else {
		text, err := os.ReadFile(pinPath)
		if err != nil {
			return err
		}
		if string(text) != formatPin(sums) {
			return fmt.Errorf("%s does not match the shadcn tree at %s; to move the pin, run fetch with -write-pin and review the diff", pinPath, shadcnSHA)
		}
	}
	tgz := filepath.Join(dir, animateTgz)
	if err := curl("https://registry.npmjs.org/tw-animate-css/-/tw-animate-css-"+twAnimateVersion+".tgz", tgz); err != nil {
		return err
	}
	data, err := os.ReadFile(tgz)
	if err != nil {
		return err
	}
	extracted, err := untarAnimate(data)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Join(dir, "tw-animate-css"), 0o755); err != nil {
		return err
	}
	for name, body := range extracted {
		if err := os.WriteFile(filepath.Join(dir, "tw-animate-css", filepath.Base(name)), []byte(body), 0o644); err != nil {
			return err
		}
	}
	fmt.Printf("fetched %d files at shadcn %s and tw-animate-css %s into %s\n", len(files), shadcnSHA, twAnimateVersion, dir)
	return nil
}
