package main

import (
	"os"
	"path/filepath"
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

func TestOptimize(t *testing.T) {
	prop := func(name, more string) string {
		return "@property " + name + " {\n  syntax: \"*\";\n  inherits: false;" + more + "\n}\n"
	}
	in := "/*! lic */\n" + layerOrder + `@layer clanker.components {
  [data-slot="button"] {
    --tw-leading: 1;
    line-height: 1;
    --tw-shadow: 0 1px red;
    box-shadow: var(--tw-ring-shadow), var(--tw-shadow);
    --tw-duration: .1s;
    animation: enter var(--tw-duration, .2s)var(--tw-ease, ease)var(--tw-gone,);
    --tw-enter-scale: .95;
  }
  [data-slot="button"]:focus-visible {
    --tw-ring-shadow: 0 0 0 3px blue;
    box-shadow: var(--tw-ring-shadow), var(--tw-shadow);
  }
  [data-slot="button"][data-variant="ghost"] {
    --tw-shadow: 0 0 #0000;
  }
  [data-slot="badge"] {
    --tw-shadow: 0 2px red;
    box-shadow: var(--tw-ring-shadow), var(--tw-shadow);
  }
  [data-slot="card"] {
    --tw-shadow: 0 3px red;
    box-shadow: var(--tw-ring-shadow), var(--tw-shadow);
  }
}
` + prop("--tw-leading", "") + prop("--tw-shadow", "\n  initial-value: 0 0 #0000;") + prop("--tw-ring-shadow", "\n  initial-value: 0 0 #0000;") + prop("--tw-duration", "") + prop("--tw-ease", "") + prop("--tw-gone", "") + prop("--tw-enter-scale", "\n  initial-value: 1;")
	kit := "@layer clanker.components {\n  [data-x] > [data-slot=\"card\"] {\n    --tw-shadow: 0 4px red;\n  }\n}\n"
	want := "/*! lic */\n" + layerOrder + `@layer clanker.components {
  [data-slot="button"] {
    line-height: 1;
    --tw-shadow: 0 1px red;
    box-shadow: 0 0 #0000, var(--tw-shadow);
    animation: enter .1s ease;
    --tw-enter-scale: .95;
  }
  [data-slot="button"]:focus-visible {
    box-shadow: 0 0 0 3px blue, var(--tw-shadow);
  }
  [data-slot="button"][data-variant="ghost"] {
    --tw-shadow: 0 0 #0000;
  }
  [data-slot="badge"] {
    box-shadow: 0 0 #0000, 0 2px red;
  }
  [data-slot="card"] {
    --tw-shadow: 0 3px red;
    box-shadow: 0 0 #0000, var(--tw-shadow);
  }
}
` + prop("--tw-shadow", "\n  initial-value: 0 0 #0000;") + prop("--tw-enter-scale", "\n  initial-value: 1;")
	if got := optimizeFile(t, in+kit, kit); got != want+kit {
		t.Errorf("got:\n%s\nwant:\n%s", got, want+kit)
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
