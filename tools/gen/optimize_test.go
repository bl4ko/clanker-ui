package main

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

func optimizeFile(t *testing.T, css, kit string) string {
	t.Helper()
	lic, rest, _ := strings.Cut(css, "\n")
	rest, ok := strings.CutPrefix(rest, layerOrder)
	if !ok {
		t.Fatal("no layer order line")
	}
	body, ok := strings.CutSuffix(rest, kit)
	if !ok {
		t.Fatal("the file does not end with the kit CSS")
	}
	tree, err := parseCSS(body)
	if err != nil {
		t.Fatal(err)
	}
	if err := newGen(nil, nil, nil, nil).optimize(tree, kit, testTable(t)); err != nil {
		t.Fatal(err)
	}
	return lic + "\n" + layerOrder + strings.TrimSuffix(tree.String(), "\n") + "\n" + kit
}

var innerVar = regexp.MustCompile(`var\((--[\w-]+)\s*(?:,([^()]*))?\)`)

func substitute(value string, vars map[string]string) string {
	for innerVar.MatchString(value) {
		value = innerVar.ReplaceAllStringFunc(value, func(ref string) string {
			m := innerVar.FindStringSubmatch(ref)
			if v, ok := vars[m[1]]; ok {
				return v
			}
			return strings.TrimSpace(m[2])
		})
	}
	return strings.Join(strings.Fields(value), " ")
}

func TestOptimizeComposition(t *testing.T) {
	prop := func(name, more string) string {
		return "@property " + name + " {\n  syntax: \"*\";\n  inherits: false;" + more + "\n}\n"
	}
	null := "\n  initial-value: 0 0 #0000;"
	stack := "var(--tw-inset-shadow), var(--tw-inset-ring-shadow), var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow)"
	focus := "  [data-slot=\"button\"]:focus-visible {\n    --tw-ring-shadow: var(--tw-ring-inset,) 0 0 0 calc(3px + var(--tw-ring-offset-width)) var(--tw-ring-color, currentcolor);\n    box-shadow: " + stack + ";\n  }\n"
	head := "/*! lic */\n" + layerOrder + "@layer clanker.components {\n  [data-slot=\"button\"] {\n    --tw-duration: .1s;\n    transition-duration: .1s;\n"
	props := prop("--tw-shadow", null) + prop("--tw-ring-shadow", null) + prop("--tw-ring-inset", "") + prop("--tw-ring-color", "") + prop("--tw-ring-offset-width", "\n  initial-value: 0px;") +
		prop("--tw-ring-offset-shadow", null) + prop("--tw-inset-shadow", null) + prop("--tw-inset-ring-shadow", null) + prop("--tw-duration", "")
	in := head + "  }\n" + focus + "  [data-slot=\"button\"] {\n    animation: enter var(--tw-duration, .2s);\n  }\n}\n" + prop("--tw-gone", "") + props
	want := head + "    animation: enter var(--tw-duration, .2s);\n  }\n" + focus + "}\n" + props
	got := optimizeFile(t, in, "")
	if got != want {
		t.Fatalf("got:\n%s\nwant:\n%s", got, want)
	}
	tree, err := parseCSS(strings.SplitN(got, layerOrder, 2)[1])
	if err != nil {
		t.Fatal(err)
	}
	vars := map[string]string{"--tw-shadow": "0 4px 6px -1px #0000001a", "--tw-ring-offset-width": "0px"}
	for _, name := range []string{"--tw-ring-shadow", "--tw-ring-offset-shadow", "--tw-inset-shadow", "--tw-inset-ring-shadow"} {
		vars[name] = "0 0 #0000"
	}
	kit := ""
	for _, it := range tree.items[0].rule.items[1].rule.items {
		if p := declProp(it.decl); strings.HasPrefix(p, "--tw-") {
			vars[p] = strings.TrimSpace(strings.TrimPrefix(it.decl, p+":"))
		} else {
			kit = strings.TrimSpace(strings.TrimPrefix(it.decl, p+":"))
		}
	}
	both := "0 0 #0000, 0 0 #0000, 0 0 #0000, 0 0 0 calc(3px + 0px) currentcolor, 0 4px 6px -1px #0000001a"
	for _, boxShadow := range []string{stack, kit} {
		if got := substitute(boxShadow, vars); got != both {
			t.Errorf("shadow-md on a part with a kit ring: box-shadow %q, want %q", got, both)
		}
	}
}

func TestOptimizeMerge(t *testing.T) {
	dark, media := "  [data-slot=\"button\"]:is([data-theme=\"dark\"] *) {\n", "  @media (prefers-color-scheme: dark) {\n    [data-slot=\"button\"]:not([data-theme=\"light\"] *) {\n"
	badge := "  [data-slot=\"badge\"][data-a] {\n    padding: 1px;\n  }\n  [data-slot=\"badge\"][data-b] {\n    padding-left: 2px;\n  }\n  [data-slot=\"badge\"][data-a] {\n    padding-inline: 3px;\n  }\n}\n"
	head := "/*! lic */\n" + layerOrder + "@layer clanker.components {\n  [data-slot=\"button\"] {\n    color: red;\n"
	hover := "  }\n  [data-slot=\"button\"]:hover {\n    color: blue;\n  }\n"
	in := head + hover + "  [data-slot=\"button\"] {\n    margin: 0;\n  }\n" +
		dark + "    color: white;\n  }\n" + media + "      color: white;\n    }\n  }\n" +
		dark + "    margin-top: 1px;\n  }\n" + media + "      margin-top: 1px;\n    }\n  }\n" + badge
	want := head + "    margin: 0;\n" + hover +
		dark + "    color: white;\n    margin-top: 1px;\n  }\n" + media + "      color: white;\n      margin-top: 1px;\n    }\n  }\n" + badge
	if got := optimizeFile(t, in, ""); got != want {
		t.Errorf("got:\n%s\nwant:\n%s", got, want)
	}
}

func TestOptimizeCommitted(t *testing.T) {
	kit, err := readKit("kit.css")
	if err != nil {
		t.Fatal(err)
	}
	for _, s := range kitStyles {
		b, err := os.ReadFile(filepath.Join("../..", s.file))
		if err != nil {
			t.Fatal(err)
		}
		got := optimizeFile(t, string(b), kit)
		if dir := os.Getenv("OPTIMIZE_OUT"); dir != "" {
			if err := os.WriteFile(filepath.Join(dir, s.file), []byte(got), 0o644); err != nil {
				t.Fatal(err)
			}
		} else if got != string(b) {
			t.Errorf("%s: the optimizer changes the committed file; run the generator again", s.file)
		}
	}
}
