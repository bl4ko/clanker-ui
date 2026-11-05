package main

import (
	"os"
	"slices"
	"strings"
	"testing"
)

func TestParsePreviews(t *testing.T) {
	src := "<ComponentPreview styleName=\"base-nova\" name=\"a-demo\" />\n" +
		"<ComponentPreview\n  name=\"a-rtl\"\n  styleName=\"base-rhea\"\n  previewClassName=\"h-[800px] p-6\"\n  direction=\"rtl\"\n/>\n" +
		"```tsx\n<ComponentPreview name=\"in-fence\" />\n```\n" +
		"<ComponentPreviewTabs />\n<ComponentPreview name=\"a-jsx\" description={<b>x</b>} hideCode />\n"
	got, err := parsePreviews(src)
	want := []preview{{"a-demo", "base-nova"}, {"a-rtl", "base-rhea"}, {"a-jsx", ""}}
	if err != nil || !slices.Equal(got, want) {
		t.Errorf("previews %v %v", got, err)
	}
	if _, err := parsePreviews(`<ComponentPreview name="x"`); err == nil {
		t.Error("open tag accepted")
	}
}

func TestDocsKey(t *testing.T) {
	for in, want := range map[string]string{
		docsRoot + "components/base/card.mdx":  "components/card",
		docsRoot + "ai-elements/base/chat.mdx": "ai-elements/chat",
		docsRoot + "forms/index.mdx":           "forms",
		docsRoot + "utils/shimmer.mdx":         "utils/shimmer",
		docsRoot + "dark-mode/next.mdx":        "dark-mode/next",
	} {
		if got := docsKey(in); got != want || !docsFile(in) {
			t.Errorf("%s: %s", in, got)
		}
	}
	for _, p := range []string{docsRoot + "components/radix/card.mdx", docsRoot + "components/base/meta.json", docsRoot + "(root)/cli.mdx"} {
		if docsFile(p) {
			t.Errorf("%s is a docs input", p)
		}
	}
}

func TestDocsMap(t *testing.T) {
	inv, err := readInventory("../..")
	if err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile("docs-shadcn.tsv")
	if string(b) != formatInventory(inv) {
		t.Error("docs-shadcn.tsv is not in the generated format")
	}
	rows, err := readDocsMap("../..")
	if err != nil {
		t.Fatal(err)
	}
	b, _ = os.ReadFile("docs-map.tsv")
	if string(b) != formatDocsMap(rows) {
		t.Error("docs-map.tsv has trailing tabs or extra text")
	}
	o, err := loadOurs("../..")
	if err != nil {
		t.Fatal(err)
	}
	for _, msg := range checkDocsMap(inv, rows, o) {
		t.Error(msg)
	}
}

func TestCheckDocsMap(t *testing.T) {
	inv := []invItem{{"components/a", "A", "-"}, {"components/a#a-demo", "-", "base-nova"}, {"components/a#a-rtl", "-", "base-rhea"}, {"forms/x", "X", "-"}, {"forms/x#x-demo", "-", "new-york-v4"}}
	o := &oursSide{hrefs: map[string]bool{"/docs/components/a": true}, examples: map[string]bool{"a-demo": true}, sections: map[string]bool{"a": true}}
	good := []mapRow{{"components/a", "/docs/components/a", ""}, {"components/a#a-demo", "a-demo", ""}, {"components/a#a-rtl", "demo-a-1", ""}, {"forms/x", "-", "React only"}, {"forms/x#x-demo", "-", "React only"}}
	if bad := checkDocsMap(inv, good, o); len(bad) > 0 {
		t.Fatalf("good map: %v", bad)
	}
	for _, c := range []struct {
		rows []mapRow
		want string
	}{
		{slices.Delete(slices.Clone(good), 2, 3), "no row for components/a#a-rtl"},
		{append(slices.Clone(good), mapRow{"components/b", "-", "x"}), "not in tools/gen/docs-shadcn.tsv"},
		{[]mapRow{good[0], good[2], good[1], good[3], good[4]}, "rows follow the order"},
		{append([]mapRow{{"components/a", "/docs/components/b", ""}}, good[1:]...), "not in docs/nav.json"},
		{append([]mapRow{good[0], {"components/a#a-demo", "a-gone", ""}}, good[2:]...), "not an example"},
		{append([]mapRow{good[0], {"components/a#a-demo", "demo-b-0", ""}}, good[2:]...), "not an example"},
		{append([]mapRow{good[0], {"components/a#a-demo", "-", ""}}, good[2:]...), "without a reason"},
		{append([]mapRow{good[0], {"components/a#a-demo", "?", ""}}, good[2:]...), "needs a review"},
		{append(slices.Clone(good[:4]), mapRow{"forms/x#x-demo", "a-demo", ""}), "its page maps to -"},
	} {
		bad := checkDocsMap(inv, c.rows, o)
		if !strings.Contains(strings.Join(bad, "\n"), c.want) {
			t.Errorf("want %q, got %v", c.want, bad)
		}
	}
	synced := syncDocsMap(inv, good[:3])
	if len(synced) != 5 || synced[3].ours != "?" || synced[4].key != "forms/x#x-demo" {
		t.Errorf("sync %v", synced)
	}
	rep := docsReport(inv, good, true)
	for _, s := range []string{"components   pages   1/1   examples   2/2", "forms        pages   0/1   examples   0/1", "components/a#a-rtl base-rhea", "forms/x#x-demo - React only"} {
		if !strings.Contains(rep, s) {
			t.Errorf("report has no %q:\n%s", s, rep)
		}
	}
}
