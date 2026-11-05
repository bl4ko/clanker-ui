package main

import (
	"os"
	"strings"
	"testing"
)

func TestBlocksCarryTheStaticCSP(t *testing.T) {
	doc, err := os.ReadFile("skills/clanker-ui/references/csp.md")
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(doc), blockCSPMeta+"\n<meta name=\"referrer\" content=\"no-referrer\">") {
		t.Fatal("references/csp.md does not show the block CSP meta tag")
	}
	d := docsOf(t)
	if len(d.blocks) == 0 {
		t.Fatal("no blocks")
	}
	for name, b := range d.blocks {
		page := string(d.blockPage(b))
		metas := cspMetaTag.FindAllStringSubmatch(page, -1)
		if len(metas) != 1 || metas[0][1] != cspMeta {
			t.Errorf("%s: CSP meta tags %q, want one with %q", name, metas, cspMeta)
		}
		if i := strings.Index(page, blockCSPMeta); i < 0 || strings.Index(page, "<link") < i || strings.Index(page, "<script") < i {
			t.Errorf("%s: a link or script comes before the CSP meta", name)
		}
	}
}

func TestBlockWithoutCSPIsRejected(t *testing.T) {
	src, err := os.ReadFile(blocksDir + "/login.html")
	if err != nil {
		t.Fatal(err)
	}
	for name, body := range map[string]string{
		"no meta":  strings.Replace(string(src), blockCSPMeta+"\n  ", "", 1),
		"two meta": strings.Replace(string(src), "</head>", "  "+blockCSPMeta+"\n</head>", 1),
		"other":    strings.Replace(string(src), "connect-src 'self'", "connect-src *", 1),
	} {
		m := docsFS(t, map[string]string{blocksDir + "/x.html": body})
		if _, err := loadDocs(m); err == nil || !strings.Contains(err.Error(), "block x") {
			t.Errorf("%s: loadDocs error %v, want a block x error", name, err)
		}
	}
}
