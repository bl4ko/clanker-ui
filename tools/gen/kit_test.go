package main

import (
	"os"
	"regexp"
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
	for _, s := range kitStyles {
		if !strings.HasSuffix(readRepo(t, s.file), "\n"+readRepo(t, "tools/gen/kit.css")) {
			t.Errorf("%s does not end with tools/gen/kit.css; do not edit it, run go run ./tools/gen -src \"$SHADCN_SRC\" -out clanker-ui.css", s.file)
		}
	}
}

func TestKitCSSAllInLayers(t *testing.T) {
	for _, s := range kitStyles {
		tree, err := parseCSS(readRepo(t, s.file))
		if err != nil {
			t.Fatal(err)
		}
		if r := strayRule(tree); r != "" {
			t.Errorf("%s: %q is outside @layer, @property, and @keyframes", s.file, r)
		}
	}
}

func TestKitStyles(t *testing.T) {
	nova, rhea := readRepo(t, "clanker-ui.css"), readRepo(t, "clanker-ui-rhea.css")
	if kitStyles[0].name != "nova" || kitStyles[0].file != "clanker-ui.css" {
		t.Errorf("the default style is %v, want nova in clanker-ui.css", kitStyles[0])
	}
	seen := map[string]string{}
	for _, s := range kitStyles {
		css := readRepo(t, s.file)
		if other, ok := seen[css]; ok || !strings.Contains(css, `[data-slot="code-block"]`) {
			t.Errorf("%s must be its own style with the same parts (same bytes as %q)", s.file, other)
		}
		seen[css] = s.file
		want := "\n    --radius: .625rem;\n"
		if s.name == "lyra" || s.name == "sera" {
			want = "\n    --radius: 0;\n"
		}
		if !strings.Contains(css, want) {
			t.Errorf("%s: no token %q (the shadcn create preview sets radius none for Lyra and Sera only)", s.file, strings.TrimSpace(want))
		}
	}
	for _, want := range []string{"--tw-ring-color: color-mix(in oklab, var(--ring) 30%, transparent)", "border-radius: calc(var(--radius) * 1.8)"} {
		if !strings.Contains(rhea, want) || strings.Count(nova, want) >= strings.Count(rhea, want) {
			t.Errorf("clanker-ui-rhea.css: want more %q than Nova (Rhea rules)", want)
		}
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

func TestHasVariantLimitedToRenderers(t *testing.T) {
	for _, s := range kitStyles {
		css := readRepo(t, s.file)
		for _, raw := range []string{`:has([data-variant=`, `:has( > [data-variant=`, `:has([data-size=`, `:has( > [data-size=`} {
			if strings.Contains(css, raw) {
				t.Errorf("%s has %q: kit buttons set data-variant and data-size, shadcn buttons do not; limit it to the parts that render the attribute", s.file, raw)
			}
		}
	}
}

func TestParseStylesSkipsComments(t *testing.T) {
	got := parseStyles(".style-x {\n  .cn-a {\n    @apply p-2;\n  }\n\n  /* .cn-b {\n    @apply -ml-1;\n  } */\n\n  .cn-a:has(> [data-slot=x]) {\n    @apply flex;\n  }\n}\n")
	if got["cn-a"] != "flex p-2" || got["cn-b"] != "" {
		t.Errorf("parseStyles = %v, want cn-a with the classes of its compound rule without the condition, like the shadcn style map, and no commented rule", got)
	}
}

func TestVegaCardContentFlex(t *testing.T) {
	b, err := os.ReadFile("../../clanker-ui-vega.css")
	if err != nil {
		t.Fatal(err)
	}
	css := string(b)
	i := strings.Index(css, "\n  [data-slot=\"card-content\"] {\n")
	if i < 0 {
		t.Fatal("no card-content rule in clanker-ui-vega.css")
	}
	rule := css[i : i+strings.Index(css[i:], "}")]
	for _, d := range []string{"display: flex;", "flex-direction: column;", "gap: calc(var(--spacing) * 3);"} {
		if !strings.Contains(rule, d) {
			t.Errorf("Vega card-content lacks %q, as in a shadcn install: %s", d, rule)
		}
	}
	if strings.Contains(css, `[data-slot="card-content"]:has( > [data-slot="questionnaire-choices"])`) {
		t.Error("Vega card-content keeps the :has() condition that the shadcn style map drops")
	}
}

func TestIconSizeTailwindOrder(t *testing.T) {
	b, err := os.ReadFile("../../clanker-ui-lyra.css")
	if err != nil {
		t.Fatal(err)
	}
	css := string(b)
	marker := strings.Index(css, "\n  [data-slot=\"marker\"] svg:not([class*=\"size-\"], [data-slot]) {")
	button := regexp.MustCompile(`\n  \[data-slot="button"\]:not\(:where\(\[data-size="xs"\]\)[^\n]*\) svg:not\(\[class\*="size-"\], \[data-slot\]\) \{`).FindStringIndex(css)
	if button == nil {
		t.Fatal("no default button icon rule in clanker-ui-lyra.css")
	}
	if marker < 0 || marker > button[0] {
		t.Errorf("Lyra: the 14 px marker icon rule (%d) must come before the 16 px button icon rule (%d), like Tailwind orders size-3.5 before size-4", marker, button[0])
	}
	if !iconSize.MatchString("[&_svg:not([class*='size-'],[data-slot])]:size-3.5") || iconSize.MatchString("data-[size=sm]:[&_svg:not([class*='size-'])]:size-3") {
		t.Error("iconSize matches only the plain icon size utility")
	}
}
