package main

import (
	"net/http"
	"os"
	"regexp"
	"slices"
	"strings"
	"testing"
)

func TestDocsStyleCSS(t *testing.T) {
	base := "/*! lic */\n@layer properties, clanker.tokens, clanker.components;\n@layer clanker.tokens {\n  :root, :host {\n    --spacing: .25rem;\n  }\n}\n@layer clanker.components {\n  [data-slot=\"b\"] { border-width: 1px; --b-gap: 1px; }\n}\n@keyframes spin { to { rotate: 1turn; } }\n"
	style := "/*! lic */\n@layer properties, clanker.tokens, clanker.components;\n@layer clanker.tokens {\n  :root, :host {\n    --spacing: .25rem;\n    --text-lg: 1.125rem;\n  }\n  [data-theme=\"dark\"] { --x: 1; }\n}\n@layer clanker.components {\n  [data-slot=\"b\"] { --tw-ring-shadow: 0 0 0 1px red; content: \"}\"; }\n}\n@keyframes spin { to { rotate: 1turn; } }\n"
	got, err := docsStyleCSS("rhea", []byte(base), []byte(style), []byte("@layer clanker.utilities {\n  .flex { display: flex; }\n}\n"))
	if err != nil {
		t.Fatal(err)
	}
	css := string(got)
	for _, want := range []string{
		"/*! lic */\n@layer clanker-docs-rhea {\n@layer reset {\n@scope ([data-docs-style=\"rhea\"]) {\n:not(svg, svg *), ::before, ::after, ::backdrop, ::placeholder, ::marker, ::file-selector-button { all: revert; --b-gap: revert; }",
		"@layer properties, clanker.tokens, clanker.components;\n@layer clanker.components {\n@scope ([data-docs-style=\"rhea\"]) {\n\n  [data-slot=\"b\"] { --tw-ring-shadow: 0 0 0 1px red; content: \"}\"; }\n\n}\n}\n",
		"@layer clanker.utilities {\n@scope ([data-docs-style=\"rhea\"]) {\n\n  .flex { display: flex; }\n\n}\n}\n",
		"@layer clanker.tokens {\n@scope ([data-docs-style=\"rhea\"]) {\n:scope { --text-lg: 1.125rem; }\n}\n}\n}\n",
	} {
		if !strings.Contains(css, want) {
			t.Errorf("docs style CSS has no %q:\n%s", want, css)
		}
	}
	if strings.Contains(css, "@keyframes") || strings.Contains(css, "--x: 1") || strings.Count(css, "--spacing") != 0 {
		t.Errorf("keyframes and tokens of the default style stay out:\n%s", css)
	}
	if _, err := docsStyleCSS("rhea", []byte(base), []byte(style+"@keyframes other { to { opacity: 0; } }\n")); err == nil || !strings.Contains(err.Error(), "@keyframes other") {
		t.Errorf("a keyframes rule that the default style does not have: %v", err)
	}
	if _, err := docsStyleCSS("rhea", []byte(base), []byte(style+".x { color: red; }\n")); err == nil {
		t.Error("a rule outside a layer must stop the docs style")
	}
}

var previewTag = regexp.MustCompile(`<div data-docs="preview"[^>]*>`)

func TestDocsPageStyles(t *testing.T) {
	d := docsOf(t)
	if len(d.styles) < 2 || d.styles[0] != "nova" || d.styles[1] != "rhea" || len(d.assets["style-rhea.css"]) == 0 {
		t.Fatalf("styles %v, style-rhea.css %d bytes", d.styles, len(d.assets["style-rhea.css"]))
	}
	if !slices.Equal(d.styles[1:], kitStyleNames) {
		t.Errorf("catalog styles %v, server kitStyleNames %v", d.styles[1:], kitStyleNames)
	}
	for _, s := range d.catalog.Files.Styles[1:] {
		if !kitFiles[s.CSS] || minKit[s.CSS] != "dist/"+strings.TrimSuffix(s.CSS, ".css")+".min.css" || len(d.assets["style-"+s.Name+".css"]) == 0 {
			t.Errorf("style %s: kit file %v, KIT=min file %q, docs style %d bytes", s.Name, kitFiles[s.CSS], minKit[s.CSS], len(d.assets["style-"+s.Name+".css"]))
		}
	}
	h := newSite("").routes()
	shadcn := map[string]string{"components/attachment": "blue", "components/bubble": "blue", "components/code-block": "", "components/drawer": "", "components/marker": "blue", "components/message": "blue", "components/message-scroller": "blue", "components/trace": "", "ai-elements/chat": "blue"}
	for _, name := range []string{"chain-of-thought", "checkpoint", "confirmation", "context", "file-tree", "inline-citation", "message", "model-selector", "plan", "prompt-input", "queue", "reasoning", "sources", "stack-trace", "subagent", "suggestion", "task", "terminal", "test-results", "tool"} {
		shadcn["ai-elements/"+name] = ""
	}
	shadcn["utils/scroll-fade"], shadcn["utils/shimmer"] = "", ""
	nova := map[string]int{"utils/scroll-fade": 1}
	for name, scheme := range shadcn {
		href := "/docs/" + name
		body := request(t, h, http.MethodGet, href).Body.String()
		tags := previewTag.FindAllString(body, -1)
		if len(tags) == 0 {
			t.Errorf("%s has no preview", href)
		}
		n := 0
		for _, tag := range tags {
			if !strings.Contains(tag, "data-docs-style") && !strings.Contains(tag, "data-scheme") {
				n++
				continue
			}
			if !strings.Contains(tag, ` data-docs-style="rhea"`) || scheme != "" && !strings.Contains(tag, ` data-scheme="`+scheme+`"`) || scheme == "" && strings.Contains(tag, "data-scheme") {
				t.Errorf("%s: preview %s, want style rhea and scheme %q like shadcn", href, tag, scheme)
			}
		}
		if n != nova[name] {
			t.Errorf("%s: %d Nova previews, want %d like shadcn", href, n, nova[name])
		}
		if !strings.Contains(body, "/style-rhea.css\"") || scheme != "" && !strings.Contains(body, "/clanker-ui-themes.css\"") {
			t.Errorf("%s does not load the Rhea preview CSS or the themes file", href)
		}
	}
	for _, href := range []string{"/docs/components/button", "/docs/components/dialog"} {
		body := request(t, h, http.MethodGet, href).Body.String()
		if strings.Contains(body, "data-docs-style") || strings.Contains(body, "style-rhea.css") {
			t.Errorf("%s is a Nova page", href)
		}
	}
}

func TestDocsPageStylesMinKit(t *testing.T) {
	d, err := loadDocs(minFS{os.DirFS(".")})
	if err != nil {
		t.Fatal(err)
	}
	if !d.hasScheme("blue") || len(d.assets["style-rhea.css"]) == 0 || d.previews["/docs/components/attachment"].Scheme != "blue" {
		t.Fatalf("minified kit: scheme blue %v, style-rhea.css %d bytes", d.hasScheme("blue"), len(d.assets["style-rhea.css"]))
	}
}
