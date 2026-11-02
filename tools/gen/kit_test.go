package main

import (
	"os"
	"strings"
	"testing"
)

func readRepo(t *testing.T, name string) string {
	t.Helper()
	b, err := os.ReadFile("../../" + name)
	if err != nil {
		t.Fatal(err)
	}
	return string(b)
}

func TestKitCSSEndsWithKit(t *testing.T) {
	if !strings.HasSuffix(readRepo(t, "clanker-ui.css"), "\n"+readRepo(t, "tools/gen/kit.css")) {
		t.Error("clanker-ui.css does not end with tools/gen/kit.css; do not edit clanker-ui.css, run go run ./tools/gen -src \"$SHADCN_SRC\" -out clanker-ui.css")
	}
}

func TestKitCSSAllInLayers(t *testing.T) {
	tree, err := parseCSS(readRepo(t, "clanker-ui.css"))
	if err != nil {
		t.Fatal(err)
	}
	if s := strayRule(tree); s != "" {
		t.Errorf("clanker-ui.css: %q is outside @layer, @property, and @keyframes", s)
	}
}

func TestLayerStray(t *testing.T) {
	tree, err := parseCSS("@layer clanker.utilities { @media (x) { .a { b: c; } } }\n@media (x) { .a { b: c; } }\n@media (y) { .d { e: f; } }\n@property --p { syntax: \"*\"; inherits: false; }\n")
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(nil, nil, nil, nil)
	g.layerStray(tree)
	want := "@layer clanker.utilities {\n  @media (x) {\n    .a {\n      b: c;\n    }\n  }\n  @media (y) {\n    .d {\n      e: f;\n    }\n  }\n}\n@property --p {\n  syntax: \"*\";\n  inherits: false;\n}\n"
	if got := tree.String(); got != want || strayRule(tree) != "" {
		t.Errorf("got\n%s", got)
	}
}
