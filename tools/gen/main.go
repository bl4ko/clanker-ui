package main

import (
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"maps"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
)

const (
	shadcnSHA        = "b8d7baa15b1dca5716f13153e63795fc3d741f6b"
	tailwindVersion  = "4.3.3"
	twAnimateVersion = "1.4.0"
	twAnimateSHA512  = "7bziOlRqH0hJx80h/3mbicLW7o8qLsH5+RaLR2t+OHM3D0JlWGODQKQ4cxbK7WlvmUxpcj6Kgu6EKqjrGFe3QQ=="
	uiDir            = "apps/v4/registry/bases/base/ui"
)

var sourceFixes = []struct {
	re         *regexp.Regexp
	repl, kind string
	why        string
}{
	{regexp.MustCompile(`(^|:)data-activation-direction=(left|right):`), "${1}data-[activation-direction=${2}]:", "shadcn class fixed", "navigation-menu: data-activation-direction=left: is not a Tailwind variant; Base UI documents data-[activation-direction=left]:"},
	{regexp.MustCompile(`:not\(\[class\*='size-'\]\)`), ":not([class*='size-'],[data-slot])", "class adapted to the kit markup", "kit markup has no size classes; an icon with a data-slot gets its size from its own part"},
}

var ignoredMarkers = map[string]string{
	"cn-menu-target":      "",
	"cn-menu-translucent": "",
	"cn-font-heading":     "",
	"cn-logical-sides":    "",
	"cn-rtl-flip":         "rtl:rotate-180",
}

var kit = kitMap{
	alias: map[string]string{
		"dropdown-menu-checkbox-item-indicator": `:is([data-slot="dropdown-menu-checkbox-item-indicator"], [data-slot="dropdown-menu-item-indicator"])`,
		"dropdown-menu-radio-item-indicator":    `:is([data-slot="dropdown-menu-radio-item-indicator"], [data-slot="dropdown-menu-item-indicator"])`,
	},
	backdrop: map[string]string{"dialog-overlay": "dialog-content", "alert-dialog-overlay": "alert-dialog-content", "sheet-overlay": "sheet-content", "drawer-overlay": "drawer-viewport"},
}

func main() {
	log.SetFlags(0)
	if len(os.Args) > 1 && os.Args[1] == "fetch" {
		fs := flag.NewFlagSet("fetch", flag.ExitOnError)
		src := fs.String("src", os.Getenv("SHADCN_SRC"), "new directory for the pinned inputs")
		pin := fs.String("pin", "tools/gen/pin.tsv", "git blob hashes of the pinned inputs")
		write := fs.Bool("write-pin", false, "write the pin file from the GitHub tree (to move the pin)")
		fs.Parse(os.Args[2:])
		if err := fetch(*src, *pin, *write); err != nil {
			log.Fatal(err)
		}
		return
	}
	if len(os.Args) > 1 && os.Args[1] == "utilities" {
		fs := flag.NewFlagSet("utilities", flag.ExitOnError)
		src := fs.String("src", os.Getenv("SHADCN_SRC"), "directory with the pinned inputs")
		pin := fs.String("pin", "tools/gen/pin.tsv", "git blob hashes of the pinned inputs")
		content := fs.String("content", "", "file whose class names become utilities")
		out := fs.String("out", "", "output CSS file")
		tailwind := fs.String("tailwind", "tailwindcss", "Tailwind CSS CLI (Homebrew tailwindcss runs @tailwindcss/cli on Node)")
		fs.Parse(os.Args[2:])
		if err := utilities(*src, *pin, *content, *out, *tailwind); err != nil {
			log.Fatal(err)
		}
		return
	}
	if len(os.Args) > 1 && os.Args[1] == "dist" {
		if err := distMain(os.Args[2:]); err != nil {
			log.Fatal(err)
		}
		return
	}
	if len(os.Args) > 1 && os.Args[1] == "catalog" {
		if err := catalogMain(os.Args[2:]); err != nil {
			log.Fatal(err)
		}
		return
	}
	var o options
	flag.StringVar(&o.src, "src", os.Getenv("SHADCN_SRC"), "directory with the pinned inputs (go run ./tools/gen fetch -src DIR)")
	flag.StringVar(&o.pin, "pin", "tools/gen/pin.tsv", "git blob hashes of the pinned inputs")
	flag.StringVar(&o.out, "out", "tools/gen/out/clanker-ui.generated.css", "output CSS file")
	flag.StringVar(&o.notes, "notes", "", "notes file (default: tools/gen/out/<name of -out>.notes.txt)")
	flag.StringVar(&o.kit, "kit", "tools/gen/kit.css", "hand-written kit CSS (plain CSS in kit layers), appended after the generated CSS when -out is set (skipped when the file does not exist; -kit \"\" turns it off)")
	list := flag.String("components", "", "comma-separated component files (default: all)")
	flag.StringVar(&o.tailwind, "tailwind", "tailwindcss", "Tailwind CSS CLI (Homebrew tailwindcss runs @tailwindcss/cli on Node)")
	flag.StringVar(&o.mapFile, "map", "tools/gen/map.tsv", "hand selectors for elements without a data-slot")
	flag.StringVar(&o.parts, "parts", "", "also write the parts as JSON to this file (for tools/parity)")
	flag.BoolVar(&o.physical, "physical", false, "keep physical classes (ml-, right-) instead of the shadcn rtl mapping")
	flag.BoolVar(&o.pretty, "pretty", false, "do not minify")
	flag.Parse()
	set := map[string]bool{}
	flag.Visit(func(f *flag.Flag) { set[f.Name] = true })
	o.kit = kitPath(set, o.kit)
	if o.src == "" {
		log.Fatal("set -src or SHADCN_SRC")
	}
	if *list != "" {
		o.components = strings.Split(*list, ",")
	}
	notes, err := run(o)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Print(notes)
}

type options struct {
	src, pin, out, notes, kit, tailwind, mapFile, parts string
	components                                          []string
	physical, pretty                                    bool
}

func (o options) notesPath() string {
	if o.notes != "" {
		return o.notes
	}
	return filepath.Join("tools", "gen", "out", strings.TrimSuffix(filepath.Base(o.out), ".css")+".notes.txt")
}

func checkTailwind(tailwind string) error {
	v, err := exec.Command(tailwind, "--help").CombinedOutput()
	if err != nil || !strings.Contains(string(v), "tailwindcss v"+tailwindVersion) {
		return fmt.Errorf("need tailwindcss v%s (brew install tailwindcss): %s", tailwindVersion, firstLine(string(v)))
	}
	return nil
}

func kitPath(set map[string]bool, kit string) string {
	if !set["out"] && !set["kit"] {
		return ""
	}
	return kit
}

func readKit(path string) (string, error) {
	if path == "" {
		return "", nil
	}
	b, err := os.ReadFile(path)
	if errors.Is(err, fs.ErrNotExist) {
		return "", nil
	}
	if err != nil {
		return "", err
	}
	if err := checkCSS(path, string(b), nil); err != nil {
		return "", err
	}
	if err := checkKit(path, string(b)); err != nil {
		return "", err
	}
	return string(b), nil
}

func run(o options) (string, error) {
	if !strings.HasSuffix(o.out, ".css") {
		return "", fmt.Errorf("-out must be a .css file: %s", o.out)
	}
	if err := checkTailwind(o.tailwind); err != nil {
		return "", err
	}
	p, err := loadPinned(o.src, o.pin)
	if err != nil {
		return "", err
	}
	in, err := pinnedInputs(p)
	if err != nil {
		return "", err
	}
	kitCSS, err := readKit(o.kit)
	if err != nil {
		return "", err
	}
	sources := map[string]*source{}
	var order []string
	var load func(n string) error
	load = func(n string) error {
		if sources[n] != nil {
			return nil
		}
		text, err := p.read(uiDir + "/" + n + ".tsx")
		if err != nil {
			return err
		}
		s, err := parseSource(n, text)
		if err != nil {
			return err
		}
		sources[n] = s
		deps := slices.Sorted(maps.Values(s.imports))
		for _, dep := range slices.Compact(deps) {
			if err := load(dep); err != nil {
				return err
			}
		}
		order = append(order, n)
		return nil
	}
	components := o.components
	if len(components) == 0 {
		components = p.ui
	}
	for _, c := range components {
		if err := load(c); err != nil {
			return "", err
		}
	}
	components = order
	nova, err := p.read(novaFile)
	if err != nil {
		return "", err
	}
	manual, fps, err := readMap(o.mapFile)
	if err != nil {
		return "", err
	}
	styles := parseStyles(nova)
	for _, cls := range sortedKeys(styles) {
		for _, c := range strings.Fields(styles[cls]) {
			if err := checkClass(novaFile+" ."+cls, c); err != nil {
				return "", err
			}
		}
	}
	g := newGen(sources, styles, manual, ignoredMarkers)
	g.fps = fps
	g.physical = o.physical
	g.kit = kit
	for _, c := range components {
		g.component(c)
	}
	if err := g.unsafeErr(); err != nil {
		return "", err
	}
	if err := g.mapErr(components); err != nil {
		return "", err
	}
	g.applyShadows()
	g.resolveConflicts()
	kit := g.slotAliases(kit)
	g.kit = kit
	out := filepath.Dir(o.out)
	if err := os.MkdirAll(out, 0o755); err != nil {
		return "", err
	}
	work, err := os.MkdirTemp("", "clanker-gen-")
	if err != nil {
		return "", err
	}
	defer os.RemoveAll(work)
	if err := in.writeAnimate(work); err != nil {
		return "", err
	}
	classes := g.allClasses()
	drop := map[string]bool{}
	var probe string
	for attempt := 0; ; attempt++ {
		compiled, stderr, err := compile(o.tailwind, work, in.preamble()+probeCSS(classes, drop))
		if err == nil {
			probe = compiled
			break
		}
		m := unknownClass.FindStringSubmatch(stderr)
		if m == nil || attempt > 100 {
			return "", fmt.Errorf("tailwindcss: %v\n%s", err, stderr)
		}
		drop[m[1]] = true
		g.note("not a Tailwind utility (dropped)", "%s", m[1])
	}
	g.props = propSets(probe, classes)
	in.components = g.emitComponents(kit, primaries(probe, classes), drop)
	css, stderr, err := compile(o.tailwind, work, in.css())
	if err != nil {
		return "", fmt.Errorf("tailwindcss: %v\n%s", err, stderr)
	}
	for cls := range g.styles {
		if !g.used[cls] && slices.Contains(components, owner(cls, p.ui)) {
			g.note("style rule not used by the source", "%s", cls)
		}
	}
	css = postprocess(css, g.groupOwners(kit), kit, g)
	tree, err := parseCSS(css)
	if err != nil {
		return "", fmt.Errorf("compiled CSS: %w", err)
	}
	g.note("fallback removed (every target browser has color-mix and @property)", "%d blocks", dropFallbacks(tree))
	g.defaultsPass(tree)
	g.classSelectors(tree)
	css = license + "\n" + tree.String()
	if !o.pretty {
		if css, err = minify(o.tailwind, work, css); err != nil {
			return "", err
		}
	}
	first, rest, _ := strings.Cut(css, "\n")
	css = first + "\n" + layerOrder + rest
	if kitCSS != "" {
		fmt.Fprintf(os.Stderr, "kit CSS appended: %s (%d bytes)\n", o.kit, len(kitCSS))
		g.note("kit CSS appended as it is", "%s, %d bytes", o.kit, len(kitCSS))
		css = strings.TrimSuffix(css, "\n") + "\n" + kitCSS
	}
	if err := os.WriteFile(o.out, []byte(css), 0o644); err != nil {
		return "", err
	}
	if o.parts != "" {
		if err := os.WriteFile(o.parts, g.partsJSON(kit, components), 0o644); err != nil {
			return "", err
		}
	}
	if filepath.Base(o.out) == "clanker-ui.css" && kitCSS != "" {
		if _, err := writeDist(filepath.Dir(o.out), filepath.Join(filepath.Dir(o.out), "dist")); err != nil {
			return "", fmt.Errorf("dist: %w", err)
		}
	}
	notes := g.report(components, len(css))
	if err := os.MkdirAll(filepath.Dir(o.notesPath()), 0o755); err != nil {
		return "", err
	}
	if err := os.WriteFile(o.notesPath(), []byte(notes), 0o644); err != nil {
		return "", err
	}
	return notes, nil
}

func pinnedInputs(p *pinned) (inputs, error) {
	themes, err := p.read(themesFile)
	if err != nil {
		return inputs{}, err
	}
	light, dark, err := parseTheme(themes, "neutral")
	if err != nil {
		return inputs{}, err
	}
	globals, err := p.read(globalsFile)
	if err != nil {
		return inputs{}, err
	}
	shadcnTW, err := p.read(twFile)
	if err != nil {
		return inputs{}, err
	}
	variants := variantsCSS(shadcnTW)
	if err := checkCSS(twFile, variants, nil); err != nil {
		return inputs{}, err
	}
	if err := checkCSS("tw-animate-css/"+animateCSS, p.animate, nil); err != nil {
		return inputs{}, err
	}
	defined := map[string]bool{}
	for _, kv := range append(slices.Clone(light), dark...) {
		defined["--"+kv[0]] = true
	}
	theme, err := themeCSS(globals, defined)
	if err != nil {
		return inputs{}, err
	}
	return inputs{tokens: tokensCSS(light, dark), theme: theme, variants: variants, animateCSS: p.animate}, nil
}

func utilities(src, pinPath, content, out, tailwind string) error {
	if src == "" || content == "" || out == "" {
		return fmt.Errorf("set -src, -content, and -out")
	}
	if err := checkTailwind(tailwind); err != nil {
		return err
	}
	p, err := loadPinned(src, pinPath)
	if err != nil {
		return err
	}
	in, err := pinnedInputs(p)
	if err != nil {
		return err
	}
	abs, err := filepath.Abs(content)
	if err != nil {
		return err
	}
	work, err := os.MkdirTemp("", "clanker-gen-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(work)
	if err := in.writeAnimate(work); err != nil {
		return err
	}
	source := fmt.Sprintf("@source %q;", abs)
	css := layerOrder +
		importUtilities + "\n" + source + "\n" + in.preamble()
	compiled, stderr, err := compile(tailwind, work, css, importUtilities, source)
	if err != nil {
		return fmt.Errorf("tailwindcss: %v\n%s", err, stderr)
	}
	return os.WriteFile(out, []byte(compiled), 0o644)
}

func (g *gen) report(components []string, size int) string {
	var b strings.Builder
	fmt.Fprintf(&b, "shadcn %s, tailwindcss %s, tw-animate-css %s\n", shadcnSHA, tailwindVersion, twAnimateVersion)
	fmt.Fprintf(&b, "components: %s\n", strings.Join(components, ", "))
	fmt.Fprintf(&b, "parts: %d, compiled bytes: %d\n", len(g.parts), size)
	for _, kind := range sortedKeys(g.notes) {
		items := slices.Clone(g.notes[kind])
		slices.Sort(items)
		fmt.Fprintf(&b, "\n%s (%d)\n", kind, len(items))
		for _, it := range items {
			fmt.Fprintf(&b, "  %s\n", it)
		}
	}
	return b.String()
}

func owner(cls string, names []string) string {
	best := ""
	for _, n := range names {
		if (cls == "cn-"+n || strings.HasPrefix(cls, "cn-"+n+"-")) && len(n) > len(best) {
			best = n
		}
	}
	return best
}

func firstLine(s string) string {
	line, _, _ := strings.Cut(strings.TrimSpace(s), "\n")
	return line
}
