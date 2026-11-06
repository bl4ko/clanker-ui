package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"testing"
)

func TestBlobSHA1(t *testing.T) {
	if got := blobSHA1([]byte("hello\n")); got != "ce013625030ba8dba906f756967f9e9ca394464a" {
		t.Errorf("git blob sha1 %s", got)
	}
}

func TestTreeFiles(t *testing.T) {
	tree := `{"sha":"x","tree":[{"path":"` + uiDir + `/button.tsx","type":"blob","sha":"aa"},{"path":"` + uiDir + `/sub/x.tsx","type":"blob","sha":"bb"},{"path":"` + uiDir + `","type":"tree","sha":"cc"},{"path":"` + docsRoot + `utils/shimmer.mdx","type":"blob","sha":"dd"},{"path":"` + docsRoot + `utils/meta.json","type":"blob","sha":"ee"},{"path":"` + styleFile("nova") + `","type":"blob","sha":"ff"},{"path":"` + stylesDir + `/other.css","type":"blob","sha":"gg"}],"truncated":false}`
	blobs, files, err := treeFiles([]byte(tree))
	if err != nil || blobs[uiDir+"/button.tsx"] != "aa" || !slices.Equal(files, append(slices.Clone(fixedFiles), uiDir+"/button.tsx", styleFile("nova"), docsRoot+"utils/shimmer.mdx")) {
		t.Errorf("tree: %v %v %v", blobs, files, err)
	}
	if _, _, err := treeFiles([]byte(strings.Replace(tree, `"truncated":false`, `"truncated":true`, 1))); err == nil || !strings.Contains(err.Error(), "truncated") {
		t.Errorf("truncated tree accepted: %v", err)
	}
}

func writeTgz(t *testing.T, files map[string]string) []byte {
	t.Helper()
	var buf bytes.Buffer
	zw := gzip.NewWriter(&buf)
	tw := tar.NewWriter(zw)
	for name, body := range files {
		tw.WriteHeader(&tar.Header{Name: name, Mode: 0o644, Size: int64(len(body))})
		tw.Write([]byte(body))
	}
	tw.Close()
	zw.Close()
	return buf.Bytes()
}

func pinnedDir(t *testing.T) (string, string) {
	t.Helper()
	dir := t.TempDir()
	files := map[string]string{
		styleFile("nova"): ".cn-button { @apply flex; }\n", styleFile("rhea"): ".cn-button { @apply flex; }\n", globalsFile: "@theme inline {\n}\n", twFile: "", themesFile: "",
		uiDir + "/button.tsx": "function Button() {}\n",
	}
	sums := map[string]string{}
	for path, body := range files {
		full := filepath.Join(dir, filepath.FromSlash(path))
		os.MkdirAll(filepath.Dir(full), 0o755)
		os.WriteFile(full, []byte(body), 0o644)
		sums[path] = blobSHA1([]byte(body))
	}
	os.WriteFile(filepath.Join(dir, animateTgz), writeTgz(t, map[string]string{animateCSS: "@keyframes enter { from { opacity: 0; } }\n"}), 0o644)
	pin := filepath.Join(dir, "pin.tsv")
	os.WriteFile(pin, []byte(formatPin(sums)), 0o644)
	return dir, pin
}

func TestLoadPinned(t *testing.T) {
	dir, pin := pinnedDir(t)
	_, err := loadPinned(dir, pin)
	if err == nil || !strings.Contains(err.Error(), "tw-animate-css: sha512") {
		t.Fatalf("a tw-animate-css tarball that is not the pinned one: %v", err)
	}
	os.Remove(filepath.Join(dir, animateTgz))
	if _, err := loadPinned(dir, pin); err == nil {
		t.Fatal("missing tarball accepted")
	}
	dir, pin = pinnedDir(t)
	os.WriteFile(filepath.Join(dir, filepath.FromSlash(uiDir), "button.tsx"), []byte("function Button() { /* changed */ }\n"), 0o644)
	if _, err := loadPinned(dir, pin); err == nil || !strings.Contains(err.Error(), "git blob") {
		t.Errorf("changed .tsx accepted: %v", err)
	}
	dir, pin = pinnedDir(t)
	os.WriteFile(filepath.Join(dir, filepath.FromSlash(uiDir), "_registry.ts"), []byte("x"), 0o644)
	if _, err := loadPinned(dir, pin); err != nil && strings.Contains(err.Error(), "not in the pin") {
		t.Errorf("a file that is not .tsx stops the run: %v", err)
	}
	os.WriteFile(filepath.Join(dir, filepath.FromSlash(uiDir), "extra.tsx"), []byte("x"), 0o644)
	if _, err := loadPinned(dir, pin); err == nil || !strings.Contains(err.Error(), "not in the pin") {
		t.Errorf("extra .tsx accepted: %v", err)
	}
	if _, err := parsePin("commit\tdeadbeef\n"); err == nil {
		t.Error("pin for another commit accepted")
	}
}

func TestPinFileMatchesCommit(t *testing.T) {
	b, err := os.ReadFile("pin.tsv")
	if err != nil {
		t.Fatal(err)
	}
	pin, err := parsePin(string(b))
	if err != nil {
		t.Fatal(err)
	}
	if len(pin) < 60 || pin[themesFile] == "" {
		t.Errorf("pin has %d files", len(pin))
	}
	if string(b) != formatPin(pin) {
		t.Error("pin.tsv is not sorted or has extra text")
	}
}

func TestUntarAnimate(t *testing.T) {
	data := writeTgz(t, map[string]string{animateCSS: "x"})
	if _, err := untarAnimate(data); err == nil || !strings.Contains(err.Error(), "sha512") {
		t.Errorf("unpinned tarball accepted: %v", err)
	}
}

func TestTailwindVersionPins(t *testing.T) {
	ci, err := os.ReadFile("../../.github/workflows/ci.yml")
	if err != nil {
		t.Fatal(err)
	}
	m := regexp.MustCompile(`(?m)^\s*TAILWIND_VERSION:\s*"?([^"\s]+)"?\s*$`).FindAllSubmatch(ci, -1)
	if len(m) != 1 || string(m[0][1]) != tailwindVersion {
		t.Errorf("TAILWIND_VERSION in ci.yml must be tailwindVersion %s (change both and the SHA-256): %q", tailwindVersion, m)
	}
	notices, err := os.ReadFile("../../THIRD_PARTY_NOTICES")
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(notices), "Tailwind CSS "+tailwindVersion+" (") {
		t.Errorf("THIRD_PARTY_NOTICES does not name Tailwind CSS %s", tailwindVersion)
	}
}
