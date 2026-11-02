package main

import (
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

const relativePlugin = `@plugin "../../poc/p.js";`

func isUnsafe(err error) bool {
	var u unsafeInput
	return errors.As(err, &u)
}

func TestUnsafeStylesheets(t *testing.T) {
	base := "@custom-variant data-open {\n  &:where([data-state=\"open\"]) { @slot; }\n}\n@utility no-scrollbar { scrollbar-width: none; }\n@property --x { syntax: \"*\"; inherits: false; }\n@theme inline { @keyframes a { from { height: 0; } } }\n@media (prefers-reduced-motion: reduce) { .shimmer { animation: none; } }\n"
	if err := checkCSS("tailwind.css", base, nil); err != nil {
		t.Fatalf("allowed input rejected: %v", err)
	}
	bad := map[string]string{
		"relative @plugin":       base + relativePlugin + "\n",
		"@plugin after a rule":   `@layer probe { [data-a] { @apply flex;}}@plugin"../p.js";@layer{[data-z]{color:red; } }`,
		"@plugin after a space":  `@layer probe { [data-a] { @apply flex;}}@plugin "../p.js";@layer{[data-z]{color:red; } }`,
		"@config with a comment": `@layer probe { [data-a] { @apply flex;}}@config/**/"../p.js";@layer{[data-z]{color:red; } }`,
		"upper case":             "@PLUGIN 'x';",
		"@import":                `@import "evil.css";`,
		"@import of a module":    `@import "tailwindcss";`,
		"@source":                `@source "../node_modules";`,
		"@reference":             `@reference "x.css";`,
		"@tailwind":              `@tailwind utilities;`,
		"escaped at-rule":        `@\70lugin "x";`,
		"remote url":             `a { background: url(https://evil.example/x.png); }`,
		"protocol-relative url":  `a { background: url("//evil.example/x.png"); }`,
		"image-set":              `a { background: image-set("x.png" 1x); }`,
		"@font-face":             `@font-face { font-family: x; }`,
		"plugin after a comment": "/* x */@plugin 'x';",
		"plugin inside a block":  "a { color: red; @plugin 'x'; }",
		"unclosed string":        "a { content: \"x; }",
	}
	for name, css := range bad {
		if err := checkCSS("in", css, nil); !isUnsafe(err) {
			t.Errorf("%s: got %v, want an unsafe input error", name, err)
		}
	}
	if err := checkCSS("in", `a { background: url(data:image/svg+xml,x) } b { filter: url(#f) }`, nil); err != nil {
		t.Errorf("data URI and fragment rejected: %v", err)
	}
	if err := checkCSS("in", importAnimate+"\n"+importTheme, generatedImports); err != nil {
		t.Errorf("generated imports rejected: %v", err)
	}
	if err := checkCSS("in", `@import "./tw-animate.css" layer(x);`, generatedImports); !isUnsafe(err) {
		t.Errorf("changed generated import accepted: %v", err)
	}
}

func TestUnsafeValuesAndClasses(t *testing.T) {
	globals := "@theme inline {\n  --radius-sm: calc(var(--radius) * 0.6);\n  --poc-a: 1 } @plugin \"../../poc/p.js\";\n  --color-background: var(--background);\n}\n"
	if _, err := themeCSS(globals, map[string]bool{"--background": true}); !isUnsafe(err) {
		t.Errorf("review marker in @theme inline: got %v", err)
	}
	for _, c := range []string{"a;b", "x}", "{y", "bg-[url(https://evil.example/x.png)]", "a/*", `[\70lugin]:x`} {
		if err := checkClass("t", c); !isUnsafe(err) {
			t.Errorf("class %q accepted", c)
		}
	}
	for _, c := range []string{"@container/card-header", "[&_svg:not([class*='size-'])]:size-4", `rtl:**:[.rdp-button\_next>svg]:rotate-180`, "content-['x']", "bg-[url(data:image/svg+xml,x)]"} {
		if err := checkClass("t", c); err != nil {
			t.Errorf("class %q rejected: %v", c, err)
		}
	}
	s, err := parseSource("x", "function X({ className, ...props }: Props) {\n  return <div data-slot=\"x\" className={cn(\"flex\", \"a;@plugin\", className)} {...props} />\n}\n")
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"x": s}, nil, nil, nil)
	g.component("x")
	if !isUnsafe(g.unsafeErr()) {
		t.Errorf("unsafe class in a .tsx file accepted: %+v", g.parts)
	}
}

func TestPluginNeverRuns(t *testing.T) {
	tailwind, err := exec.LookPath("tailwindcss")
	if err != nil {
		t.Skip("tailwindcss not installed")
	}
	dir := t.TempDir()
	marker := filepath.Join(dir, "marker.txt")
	plugin := "require(\"fs\").writeFileSync(" + `"` + filepath.ToSlash(marker) + `"` + ", \"ran\");\nmodule.exports = function () {};\n"
	if err := os.WriteFile(filepath.Join(dir, "p.js"), []byte(plugin), 0o644); err != nil {
		t.Fatal(err)
	}
	control := filepath.Join(dir, "control.css")
	os.WriteFile(control, []byte(`@import "tailwindcss/utilities.css" source(none);`+"\n@plugin \"./p.js\";\n"), 0o644)
	cmd := exec.Command(tailwind, "--input", control, "--output", filepath.Join(dir, "control.out.css"))
	cmd.Dir = dir
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("control: tailwindcss failed: %v %s", err, out)
	}
	if _, err := os.Stat(marker); err != nil {
		t.Fatal("control: this tailwindcss does not run @plugin, so the test proves nothing")
	}
	os.Remove(marker)
	for _, input := range []string{
		"\uFEFF@plugin \"./p.js\";\n@layer probe { [data-a] { @apply flex; } }\n",
		"@layer probe { [data-a] { @apply flex; } }\n@plugin \"./p.js\";\n",
		"@theme inline {\n  --poc-a: 1 } @plugin \"./p.js\";\n}\n",
		"@layer probe { [data-a] { @apply flex;}}@config/**/\"./p.js\";\n",
	} {
		_, _, err := compile(tailwind, dir, `@import "tailwindcss/utilities.css" source(none);`+"\n"+input, `@import "tailwindcss/utilities.css" source(none);`)
		if !isUnsafe(err) {
			t.Errorf("compile ran %q: %v", input, err)
		}
		if _, err := os.Stat(marker); err == nil {
			t.Fatalf("the plugin ran for %q", input)
		}
	}
}

func TestKitLayer(t *testing.T) {
	if !strings.HasPrefix((inputs{}).css(), "@layer properties, clanker.tokens, clanker.themes, clanker.base, clanker.components, clanker.utilities;\n") {
		t.Error("the layer order has no clanker.themes between the tokens and the base")
	}
	dir := t.TempDir()
	path := filepath.Join(dir, "kit.css")
	if s, err := readKit(path); err != nil || s != "" {
		t.Errorf("missing kit file: %q %v", s, err)
	}
	good := "@layer clanker.base {\n  a { color: blue; }\n}\n@layer clanker.themes {\n  [data-theme=\"x\"] { --primary: red; }\n}\n@layer clanker.components {\n  [data-slot=\"theme-toggle\"] { color: red; }\n}\n@property --x { syntax: \"<length>\"; inherits: false; initial-value: 0px; }\n@keyframes clanker-x { from { opacity: 0; } }\n"
	os.WriteFile(path, []byte(good), 0o644)
	if s, err := readKit(path); err != nil || s != good {
		t.Errorf("kit file in kit layers is used as it is: %q %v", s, err)
	}
	for name, bad := range map[string]string{
		"rule outside a layer":  "[data-slot=\"a\"] { color: red; }\n",
		"layer of another name": "@layer other {\n  a { color: red; }\n}\n",
		"Tailwind @apply":       "@layer clanker.components {\n  a { @apply flex; }\n}\n",
		"old clanker.kit layer": "@layer clanker.kit {\n  a { color: red; }\n}\n",
	} {
		os.WriteFile(path, []byte(bad), 0o644)
		if _, err := readKit(path); err == nil {
			t.Errorf("kit file with a %s accepted", name)
		}
	}
	os.WriteFile(path, []byte("@import \"https://evil.example/x.css\";\n"), 0o644)
	if _, err := readKit(path); !isUnsafe(err) {
		t.Errorf("kit file with @import: %v", err)
	}
}

func TestEndToEnd(t *testing.T) {
	src := os.Getenv("SHADCN_SRC")
	if src == "" {
		t.Skip("set SHADCN_SRC to the pinned inputs")
	}
	root, err := filepath.Abs("../..")
	if err != nil {
		t.Fatal(err)
	}
	dir := t.TempDir()
	kit := filepath.Join(dir, "kit.css")
	kitText := "@layer clanker.components {\n  [data-slot=\"theme-toggle\"] { color: var(--primary); }\n}\n"
	os.WriteFile(kit, []byte(kitText), 0o644)
	var outs []string
	for i := range 3 {
		o := options{src: src, pin: filepath.Join(root, "tools/gen/pin.tsv"), out: filepath.Join(dir, "run"+string(rune('a'+i)), "clanker-ui.css"), notes: filepath.Join(dir, "notes.txt"), kit: kit, tailwind: "tailwindcss", mapFile: filepath.Join(root, "tools/gen/map.tsv"), components: []string{"button", "badge"}}
		if i == 2 {
			o.kit = filepath.Join(dir, "no-kit.css")
		}
		if _, err := run(o); err != nil {
			t.Fatal(err)
		}
		b, err := os.ReadFile(o.out)
		if err != nil {
			t.Fatal(err)
		}
		outs = append(outs, string(b))
	}
	if outs[0] != outs[1] {
		t.Error("two runs give different CSS")
	}
	css := outs[0]
	if !strings.HasPrefix(css, license+"\n") {
		t.Errorf("first line: %.120q", css)
	}
	if css != outs[2]+"\n"+kitText || strings.HasSuffix(outs[2], "\n") {
		t.Errorf("the output is the generated CSS, a new line, and kit.css as it is: %q", css[max(0, len(css)-200):])
	}
	if _, rest, _ := strings.Cut(css, "\n"); !strings.HasPrefix(rest, layerOrder) {
		t.Errorf("the second line is not the layer order with clanker.themes: %.200q", rest)
	}
	if !regexp.MustCompile(`@layer clanker\.utilities\{[^@]*\.shimmer\{[^}]*animation:tw-shimmer`).MatchString(css) || !strings.Contains(css, ".shimmer-none{") {
		t.Error("the shimmer utilities for markup are missing")
	}
	if !strings.Contains(css, "--primary:oklch(20.5% 0 0)") || !strings.Contains(css, "--foreground:oklch(14.5% 0 0)") {
		t.Error("default tokens are not the shadcn themes.ts neutral values")
	}
}

func TestByteOrderMark(t *testing.T) {
	for _, src := range []string{"\uFEFF@plugin \"./p.js\";\n", "a { color: red; }\n\uFEFF@config \"./p.js\";\n", "a {\u00a0color: red; }\n", "\f@plugin \"./p.js\";\n", "\v@plugin \"./p.js\";\n", "\x00@plugin \"./p.js\";\n"} {
		if err := checkCSS("bom.css", src, nil); !isUnsafe(err) {
			t.Errorf("non-ASCII outside a string accepted: %q %v", src, err)
		}
	}
	if err := checkCSS("ok.css", "a::after { content: \"\u2192\"; }\n/* \u00e9 */\n", nil); err != nil {
		t.Errorf("non-ASCII in a string or comment rejected: %v", err)
	}
}

func TestKitOnlyWithOut(t *testing.T) {
	def := "tools/gen/kit.css"
	if got := kitPath(map[string]bool{}, def); got != "" {
		t.Errorf("without -out the generated CSS must not include kit.css: %q", got)
	}
	if got := kitPath(map[string]bool{"out": true}, def); got != def {
		t.Errorf("with -out kit.css is appended: %q", got)
	}
	if got := kitPath(map[string]bool{"out": true, "kit": true}, ""); got != "" {
		t.Errorf("-kit \"\" turns it off: %q", got)
	}
}
