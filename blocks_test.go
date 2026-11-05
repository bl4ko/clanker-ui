package main

import (
	"encoding/json"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"slices"
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

type blockNode struct {
	tag      string
	attrs    map[string]string
	children []*blockNode
}

var (
	blockTag     = regexp.MustCompile(`<(/?)([a-zA-Z][a-zA-Z0-9-]*)((?:\s+[a-zA-Z:-]+(?:="[^"]*")?)*)\s*>`)
	blockAttr    = regexp.MustCompile(`([a-zA-Z:-]+)(?:="([^"]*)")?`)
	blockVoid    = map[string]bool{"meta": true, "link": true, "input": true, "img": true, "br": true, "hr": true, "source": true}
	blockSlotUse = regexp.MustCompile(`data-slot"?[=:]\s*"([a-z0-9-]+)"`)
	skillHead    = regexp.MustCompile("(?s)## 3\\. Write the head.*?```html\n.*?<head>\n(.*?)</head>")
)

func parseBlock(t *testing.T, name, src string) *blockNode {
	root := &blockNode{tag: "#root", attrs: map[string]string{}}
	stack := []*blockNode{root}
	for _, m := range blockTag.FindAllStringSubmatch(src, -1) {
		tag := strings.ToLower(m[2])
		if m[1] == "/" {
			if top := stack[len(stack)-1]; top.tag != tag {
				t.Fatalf("%s: </%s> closes <%s>", name, tag, top.tag)
			}
			stack = stack[:len(stack)-1]
			continue
		}
		n := &blockNode{tag: tag, attrs: map[string]string{}}
		for _, a := range blockAttr.FindAllStringSubmatch(m[3], -1) {
			n.attrs[a[1]] = a[2]
		}
		top := stack[len(stack)-1]
		top.children = append(top.children, n)
		if !blockVoid[tag] {
			stack = append(stack, n)
		}
	}
	if len(stack) != 1 {
		t.Fatalf("%s: <%s> is not closed", name, stack[len(stack)-1].tag)
	}
	return root
}

func (n *blockNode) walk(visit func(*blockNode) bool) {
	for _, c := range n.children {
		if visit(c) {
			c.walk(visit)
		}
	}
}

func (n *blockNode) has(name string) bool {
	_, ok := n.attrs[name]
	return ok
}

func footerButtons(footer *blockNode) []*blockNode {
	var out []*blockNode
	footer.walk(func(c *blockNode) bool {
		switch c.attrs["data-slot"] {
		case "button", "alert-dialog-cancel", "alert-dialog-action":
			out = append(out, c)
			return false
		case "dialog-content", "alert-dialog-content", "sheet-content", "drawer-content", "dropdown-menu-content":
			return false
		}
		return true
	})
	return out
}

func mainAction(b *blockNode) bool {
	v := b.attrs["data-variant"]
	return v == "" || v == "default" || v == "destructive" || b.attrs["data-slot"] == "alert-dialog-action"
}

func TestBlocksFollowTheSkill(t *testing.T) {
	skill := readText(t, "skills/clanker-ui/SKILL.md")
	m := skillHead.FindStringSubmatch(skill)
	if m == nil {
		t.Fatal("SKILL.md step 3 has no head example")
	}
	want := m[1]
	if !strings.HasPrefix(want, "  <meta charset=\"utf-8\">\n  "+blockCSPMeta+"\n") || !strings.Contains(want, "clanker-ui-a11y.min.css") {
		t.Fatalf("SKILL.md head must start with the charset and the CSP meta tag and load the a11y CSS:\n%s", want)
	}
	catalog := struct {
		Components []struct {
			Parts []struct {
				Slot string `json:"slot"`
			} `json:"parts"`
		} `json:"components"`
	}{}
	if err := json.Unmarshal([]byte(readText(t, "skills/clanker-ui/references/clanker-ui.json")), &catalog); err != nil {
		t.Fatal(err)
	}
	slots := map[string]bool{}
	for _, c := range catalog.Components {
		for _, p := range c.Parts {
			slots[p.Slot] = true
		}
	}
	title := regexp.MustCompile(`(?m)^  <title>[^<]*</title>\n`)
	d := docsOf(t)
	for name, b := range d.blocks {
		head := b.HTML[strings.Index(b.HTML, "<head>\n")+7 : strings.Index(b.HTML, "</head>")]
		exp := strings.Replace(want, "  <link rel=\"stylesheet\" href=\"/app.css\">\n", "", 1)
		if b.JS != "" {
			exp = strings.Replace(exp, `src="/app.js"`, `src="/`+name+`.js"`, 1)
		} else {
			exp = strings.Replace(exp, "  <script type=\"module\" src=\"/app.js\"></script>\n", "", 1)
		}
		if got := title.ReplaceAllString(head, ""); got != title.ReplaceAllString(exp, "") {
			t.Errorf("%s: <head> differs from SKILL.md step 3 (title and module aside):\n%s\nwant:\n%s", name, got, exp)
		}
		for _, s := range blockSlotUse.FindAllStringSubmatch(b.HTML+b.JS, -1) {
			if !slots[s[1]] {
				t.Errorf("%s: data-slot %q is not a part in references/clanker-ui.json", name, s[1])
			}
		}
		parseBlock(t, name, b.HTML).walk(func(n *blockNode) bool {
			if n.attrs["data-theme-set"] == "toggle" && (n.attrs["data-size"] != "icon" || n.attrs["data-variant"] != "ghost") {
				t.Errorf("%s: the theme toggle is %s %s, want ghost icon (design.md section 10)", name, n.attrs["data-variant"], n.attrs["data-size"])
			}
			slot := n.attrs["data-slot"]
			buttons := footerButtons(n)
			first := slot == "sheet-footer" || slot == "drawer-footer" || slot == "card-footer" || slot == "field" && n.attrs["data-orientation"] == "horizontal"
			if !first && slot != "dialog-footer" && slot != "alert-dialog-footer" || len(buttons) < 2 {
				return true
			}
			want, where := len(buttons)-1, "last"
			if first {
				want, where = 0, "first"
			}
			if at := slices.IndexFunc(buttons, mainAction); at >= 0 && at != want {
				t.Errorf("%s: %s puts the main action at %d of %d, want it %s (design.md section 4)", name, slot, at+1, len(buttons), where)
			}
			return true
		})
	}
}

func TestSkillShowsOneThemeToggle(t *testing.T) {
	toggle := regexp.MustCompile(`data-theme-set"?[=:]\s*"toggle"`)
	size := regexp.MustCompile(`data-size"?[=:]\s*"icon"`)
	err := filepath.WalkDir("skills/clanker-ui", func(path string, e fs.DirEntry, err error) error {
		if err != nil || e.IsDir() || !strings.HasSuffix(path, ".md") && !strings.HasSuffix(path, ".html") && !strings.HasSuffix(path, ".js") {
			return err
		}
		for i, line := range strings.Split(readText(t, path), "\n") {
			for _, part := range strings.Split(line, "<button")[1:] {
				if toggle.MatchString(part) && !size.MatchString(part) {
					t.Errorf("%s:%d: a theme toggle without data-size=\"icon\"", path, i+1)
				}
			}
			if strings.Contains(line, `"data-theme-set": "toggle"`) && !size.MatchString(line) {
				t.Errorf("%s:%d: a theme toggle without data-size \"icon\"", path, i+1)
			}
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
}
