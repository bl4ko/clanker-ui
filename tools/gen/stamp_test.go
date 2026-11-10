package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestStampReleaseFiles(t *testing.T) {
	dir := t.TempDir()
	if err := os.Mkdir(filepath.Join(dir, "dist"), 0o755); err != nil {
		t.Fatal(err)
	}
	var kit []string
	for _, pat := range []string{"../../clanker-ui*.css", "../../clanker-ui*.js", "../../dist/*"} {
		m, err := filepath.Glob(pat)
		if err != nil || len(m) == 0 {
			t.Fatalf("%s: %v", pat, err)
		}
		kit = append(kit, m...)
	}
	orig := map[string]string{}
	for _, src := range kit {
		b, err := os.ReadFile(src)
		if err != nil {
			t.Fatal(err)
		}
		dst := filepath.Join(dir, filepath.Base(src))
		if filepath.Base(filepath.Dir(src)) == "dist" {
			dst = filepath.Join(dir, "dist", filepath.Base(src))
		}
		if err := os.WriteFile(dst, b, 0o644); err != nil {
			t.Fatal(err)
		}
		orig[dst] = string(b)
	}
	other := filepath.Join(dir, "LICENSE")
	if err := os.WriteFile(other, []byte("MIT\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	names, err := stamp("1.2.3-rc.1", []string{dir, filepath.Join(dir, "dist")})
	if err != nil {
		t.Fatal(err)
	}
	if len(names) != len(kit) {
		t.Fatalf("stamped %d files, want %d", len(names), len(kit))
	}
	for f, before := range orig {
		b, err := os.ReadFile(f)
		if err != nil {
			t.Fatal(err)
		}
		want := "/*! clanker-ui v1.2.3-rc.1 | MIT | " + strings.TrimPrefix(before, "/*! clanker-ui | MIT | ")
		if string(b) != want {
			t.Errorf("%s: first line %q", f, strings.SplitN(string(b), "\n", 2)[0])
		}
	}
	if b, _ := os.ReadFile(other); string(b) != "MIT\n" {
		t.Errorf("LICENSE changed: %q", b)
	}
	if _, err := stamp("1.2.3", []string{dir}); err == nil {
		t.Error("a second stamp of the same files did not fail")
	}
}

func TestStampRejects(t *testing.T) {
	dir := t.TempDir()
	for _, v := range []string{"", "v0.3.0", "0.3", "0.3.0 ", "0.3.0+x"} {
		if _, err := stamp(v, []string{dir}); err == nil {
			t.Errorf("version %q: no error", v)
		}
	}
	if _, err := stamp("0.3.0", []string{dir}); err == nil {
		t.Error("a directory without kit files: no error")
	}
	f := filepath.Join(dir, "clanker-ui-x.css")
	if err := os.WriteFile(f, []byte("a{}\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := stamp("0.3.0", []string{dir}); err == nil {
		t.Error("a kit file without the license line: no error")
	}
	if b, _ := os.ReadFile(f); string(b) != "a{}\n" {
		t.Errorf("file changed after a failed stamp: %q", b)
	}
}
