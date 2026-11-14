package main

import (
	"errors"
	"regexp"
	"slices"
	"strings"
	"testing"
)

const buttonSource = `import { cva } from "class-variance-authority"

const buttonVariants = cva(
  "cn-button group/button inline-flex",
  {
    variants: {
      variant: {
        default: "cn-button-variant-default",
        outline: "cn-button-variant-outline",
      },
      size: {
        default: "h-8",
        "icon-sm": "size-7",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: Props) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

function Close({ ...props }: Props) {
  return (
    <ClosePrimitive data-slot="close" render={<Button variant="outline" className="cn-close" size="icon-sm" />} {...props}>
      <span className="sr-only">Close</span>
    </ClosePrimitive>
  )
}
`

func TestParseSource(t *testing.T) {
	s, err := parseSource("button", buttonSource)
	if err != nil {
		t.Fatal(err)
	}
	c := s.cvas["buttonVariants"]
	if c == nil || c.base != "cn-button group/button inline-flex" || !slices.Equal(c.keys, []string{"variant", "size"}) || c.defaults["size"] != "default" {
		t.Fatalf("cva: %+v", c)
	}
	if got := len(c.variants["size"]); got != 2 || c.variants["size"][1].value != "icon-sm" {
		t.Fatalf("size variants: %+v", c.variants["size"])
	}
	f := s.funcs["Button"]
	if f.defaults["variant"] != "default" || len(f.elems) != 1 || !f.elems[0].spreadAfter("data-slot") {
		t.Fatalf("Button: %+v", f)
	}
	r := s.funcs["Close"].elems[0].get("render")
	if r == nil || r.elem == nil || r.elem.tag != "Button" || r.elem.get("size").str != "icon-sm" {
		t.Fatalf("render prop: %+v", r)
	}
}

func TestRender(t *testing.T) {
	s, err := parseSource("button", buttonSource)
	if err != nil {
		t.Fatal(err)
	}
	styles := map[string]string{"cn-button": "rounded-lg border", "cn-button-variant-default": "bg-primary", "cn-button-variant-outline": "border-border", "cn-close": "absolute top-2"}
	g := newGen(map[string]*source{"button": s}, styles, nil, nil)
	g.physical = true
	g.component("button")
	var button, close *part
	for _, p := range g.parts {
		switch {
		case p.slot == "button" && p.context == "":
			button = p
		case p.slot == "close" && p.context == "":
			close = p
		}
	}
	if button == nil || close == nil {
		t.Fatalf("parts: %+v", g.parts)
	}
	if button.layers[0].cond != "" || !slices.Equal(button.layers[0].classes, []string{"rounded-lg", "border"}) {
		t.Errorf("button base layer: %+v", button.layers[0])
	}
	want := `:where(:is(:not([data-variant]), [data-variant="default"]))`
	if !slices.ContainsFunc(button.layers, func(l layer) bool { return l.cond == want && slices.Equal(l.classes, []string{"bg-primary"}) }) {
		t.Errorf("default variant layer missing: %+v", button.layers)
	}
	if !slices.Equal(button.groups, []string{"group/button"}) {
		t.Errorf("groups: %v", button.groups)
	}
	if layerText(close.layers) != "rounded-lg border inline-flex border-border size-7 absolute top-2" {
		t.Errorf("close layers: %q", layerText(close.layers))
	}
}

func TestTwMerge(t *testing.T) {
	prim := map[string]string{"text-sm": "font-size", "text-[0.8rem]": "font-size", "px-2": "padding-inline", "pl-1": "padding-left", "hover:bg-a": "background-color", "bg-b": "background-color"}
	keep, dropped := twMerge([]string{"text-sm", "px-2", "hover:bg-a", "bg-b", "pl-1", "text-[0.8rem]"}, prim, nil)
	if !slices.Equal(keep, []string{"px-2", "hover:bg-a", "bg-b", "pl-1", "text-[0.8rem]"}) || !slices.Equal(dropped, []string{"text-sm"}) {
		t.Errorf("keep %v dropped %v", keep, dropped)
	}
	props := map[string][]string{"h-8": {"height"}, "size-6": {"width", "height"}, "px-2.5": {"padding-inline"}, "p-0": {"padding"}, "hover:h-8": {"height"}, "ring-1": {"--tw-ring-shadow", "box-shadow"}, "shadow-md": {"--tw-shadow", "box-shadow"}}
	if keep, _ := twMerge([]string{"shadow-md", "ring-1"}, map[string]string{"shadow-md": "--tw-shadow", "ring-1": "--tw-ring-shadow"}, props); len(keep) != 2 {
		t.Errorf("ring and shadow both stay: %v", keep)
	}
	compiled := "[data-cls=\"0\"] { --tw-leading: 1.375; line-height: 1.375; }\n[data-cls=\"1\"] { font-size: var(--text-sm); line-height: var(--tw-leading, 1.4); }\n"
	ps := propSets(compiled, []string{"leading-snug", "text-sm"})
	if keep, _ := twMerge([]string{"leading-snug", "text-sm"}, map[string]string{"leading-snug": "line-height", "text-sm": "font-size"}, ps); !slices.Equal(keep, []string{"text-sm"}) {
		t.Errorf("a later text size removes an earlier leading, like tailwind-merge: %v", keep)
	}
	props["size-auto"], props["w-full"] = []string{"width", "height"}, []string{"width"}
	if keep, _ := twMerge([]string{"size-auto", "w-full"}, map[string]string{"size-auto": "width", "w-full": "width"}, props); len(keep) != 2 {
		t.Errorf("size-auto stays before w-full: %v", keep)
	}
	keep, dropped = twMerge([]string{"h-8", "px-2.5", "hover:h-8", "size-6", "p-0"}, map[string]string{"h-8": "height", "size-6": "width", "px-2.5": "padding-inline", "p-0": "padding", "hover:h-8": "height"}, props)
	if !slices.Equal(keep, []string{"hover:h-8", "size-6", "p-0"}) || !slices.Equal(dropped, []string{"px-2.5", "h-8"}) {
		t.Errorf("shorthand merge: keep %v dropped %v", keep, dropped)
	}
	if got := variantChain("data-[side=left]:hover:bg-[a:b]"); got != "data-[side=left]:hover" {
		t.Errorf("variant chain %q", got)
	}
}

func TestPrimaries(t *testing.T) {
	compiled := "[data-cls=\"0\"]::after { content: var(--tw-content); position: absolute; }\n[data-cls=\"1\"]::after { content: var(--tw-content); border-width: 1px; }\n[data-cls=\"2\"] { --tw-content: \"x\"; content: var(--tw-content); }\n"
	got := primaries(compiled, []string{"after:absolute", "after:border", "content-['x']"})
	if got["after:absolute"] != "position" || got["after:border"] != "border-width" || got["content-['x']"] != "--tw-content" {
		t.Errorf("primaries: %v", got)
	}
}

func TestRTL(t *testing.T) {
	cases := map[string][]string{
		"ml-auto":                            {"ms-auto"},
		"right-2":                            {"end-2"},
		"-translate-x-1/2":                   {"-translate-x-1/2", "rtl:translate-x-1/2"},
		"border-ring":                        {"border-ring"},
		"data-[side=left]:right-1":           {"data-[side=left]:right-1"},
		"has-data-[icon=inline-end]:pr-2":    {"has-data-[icon=inline-end]:pe-2"},
		"text-left":                          {"text-start"},
		"data-[swipe-direction=left]:left-0": {"data-[swipe-direction=left]:left-0"},
		"data-[swipe-direction=right]:origin-right": {"data-[swipe-direction=right]:origin-right"},
		"origin-top-left": {"origin-top-left"},
	}
	for in, want := range cases {
		if got := rtlClasses(in); !slices.Equal(got, want) {
			t.Errorf("%s: got %v, want %v", in, got, want)
		}
	}
}

func TestPostprocess(t *testing.T) {
	g := newGen(nil, nil, nil, nil)
	k := kitMap{backdrop: map[string]string{"dialog-overlay": "dialog-content"}}
	in := "[data-backdrop-of=\"dialog-content\"]:where([data-state=\"open\"]), [data-backdrop-of=\"dialog-content\"]:where([data-open]) {\n}\n" +
		"[data-slot=\"x\"]:is(:where(.group\\/field):hover *) {\n}\n"
	out := postprocess(in, map[string][]string{`.group\/field`: {`[data-slot="field"]`}}, k, g)
	want := license + "\n" +
		"[data-slot=\"dialog-content\"]:where([data-state=\"open\"])::backdrop, [data-slot=\"dialog-content\"]:where([data-open])::backdrop {\n}\n" +
		"[data-slot=\"x\"]:is(:where([data-slot=\"field\"]):hover *) {\n}\n"
	if out != want {
		t.Errorf("got\n%s\nwant\n%s", out, want)
	}
}

const constructSource = `import { cva } from "class-variance-authority"

const badgeVariants = cva("cn-badge inline-flex", {
  variants: {
    variant: {
      default: "bg-primary",
      outline: "border-border",
    },
  },
  defaultVariants: {
    variant: "default",
  },
})

function Badge({ className, variant = "default", render, ...props }: Props) {
  return useRender({
    defaultTagName: "span",
    props: mergeProps<"span">(
      {
        className: cn(badgeVariants({ variant }), className),
      },
      props
    ),
    render,
    state: {
      slot: "badge",
      variant,
    },
  })
}

function Panel({ className, variant = "sidebar", showOnHover = false, ...props }: Props) {
  const { orientation } = usePanel()
  return (
    <div data-slot="panel" data-variant={variant} className={cn("flex", showOnHover && "opacity-0", className)} {...props}>
      <div
        data-slot="panel-gap"
        className={cn(
          "w-4",
          variant === "floating" || variant === "inset" ? "p-2" : "p-0",
          { "mt-1": orientation === "vertical" },
          String.raw` + "`rtl:**:[.x\\_y]:rotate-180`" + `
        )}
      />
    </div>
  )
}
`

func constructGen(t *testing.T) *gen {
	t.Helper()
	s, err := parseSource("panel", constructSource)
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"panel": s}, map[string]string{"cn-badge": "rounded-full"}, nil, nil)
	g.physical = true
	g.component("panel")
	return g
}

func findPart(g *gen, slot string) *part {
	for _, p := range g.parts {
		if p.slot == slot && p.context == "" && p.marker == "" && p.sel == "" {
			return p
		}
	}
	return nil
}

func hasLayer(p *part, cond, classes string) bool {
	return slices.ContainsFunc(p.layers, func(l layer) bool { return l.cond == cond && strings.Join(l.classes, " ") == classes })
}

func TestUseRender(t *testing.T) {
	g := constructGen(t)
	p := findPart(g, "badge")
	if p == nil || p.tag != "span" {
		t.Fatalf("badge part: %+v", p)
	}
	if !hasLayer(p, ``, "rounded-full") || !hasLayer(p, `:where(:is(:not([data-variant]), [data-variant="default"]))`, "bg-primary") || !hasLayer(p, `:where([data-variant="outline"])`, "border-border") {
		t.Errorf("badge layers: %+v", p.layers)
	}
	if !slices.ContainsFunc(p.layers, func(l layer) bool { return l.attr == "data-variant" && l.value == "default" && l.cond != "" }) {
		t.Errorf("variant layer attr: %+v", p.layers)
	}
}

func TestConditions(t *testing.T) {
	g := constructGen(t)
	panel := findPart(g, "panel")
	if panel == nil || !hasLayer(panel, `:where([data-show-on-hover]:not([data-show-on-hover="false"]))`, "opacity-0") {
		t.Fatalf("boolean prop: %+v", panel)
	}
	gap := findPart(g, "panel-gap")
	if gap == nil {
		t.Fatalf("parts: %+v", g.parts)
	}
	yes := `:where(:where([data-slot="panel"][data-variant="floating"] *), :where([data-slot="panel"][data-variant="inset"] *))`
	if !hasLayer(gap, yes, "p-2") || !hasLayer(gap, ":not("+yes+")", "p-0") {
		t.Errorf("ternary on an ancestor prop: %+v", gap.layers)
	}
	if !hasLayer(gap, `:where([data-slot="panel"][data-orientation="vertical"] *)`, "mt-1") {
		t.Errorf("class object with a context value: %+v", gap.layers)
	}
	if !hasLayer(gap, "", `rtl:**:[.x\_y]:rotate-180`) {
		t.Errorf("String.raw: %+v", gap.layers)
	}
}

func TestTernaryAndAnd(t *testing.T) {
	if q, c := ternary(`a === "x" ? "p-1" : "p-2"`); q != 10 || c != 18 {
		t.Errorf("ternary %d %d", q, c)
	}
	if q, _ := ternary(`a?.b && "x"`); q != -1 {
		t.Errorf("optional chaining is not a ternary: %d", q)
	}
	if i := lastTop(`a && (b && c) && "x"`, "&&"); i != 14 {
		t.Errorf("lastTop %d", i)
	}
}

func TestRewriteDefaults(t *testing.T) {
	g := newGen(nil, nil, nil, nil)
	g.defaulted[[2]string{"data-variant", "legend"}] = []string{"field-legend"}
	g.defaulted[[2]string{"data-size", "default"}] = []string{"card"}
	cases := map[string]string{
		`[data-slot="field-legend"][data-variant="legend"]`:                       `[data-slot="field-legend"]:is([data-variant="legend"], :not([data-variant]))`,
		`[data-variant="legend"] + [data-slot="field-description"]`:               `:is([data-variant="legend"], :where([data-slot="field-legend"]):not([data-variant])) + [data-slot="field-description"]`,
		`[data-slot="x"]:is(:where([data-slot="card"])[data-size="default"] *)`:   `[data-slot="x"]:is(:where([data-slot="card"]):is([data-size="default"], :not([data-size])) *)`,
		`[data-slot="card"]:where(:is(:not([data-size]), [data-size="default"]))`: `[data-slot="card"]:where(:is(:not([data-size]), [data-size="default"]))`,
		`[data-slot="card"]:has([data-size="default"])`:                           `[data-slot="card"]:has(:is([data-size="default"], :where([data-slot="card"]):not([data-size])))`,
		`:is([data-slot="card"], [data-slot="item"])[data-size="default"]`:        `:is([data-slot="card"], [data-slot="item"]):is([data-size="default"], :where([data-slot="card"]):not([data-size]))`,
	}
	for in, want := range cases {
		if got := g.rewriteDefaults(in); got != want {
			t.Errorf("%s\n got %s\nwant %s", in, got, want)
		}
	}
}

func TestDropFallbacks(t *testing.T) {
	in := `@layer properties {
  @supports ((-webkit-hyphens: none) and (not (margin-trim: inline))) or ((-moz-orient: inline) and (not (color: rgb(from red r g b)))) {
    * { --tw-x: 0; }
  }
}
@layer c {
  .a { color: red; background-color: var(--x); }
  @supports (color: color-mix(in lab, red, red)) {
    .a { background-color: color-mix(in oklab, var(--x) 50%, transparent); }
  }
  .b { outline-color: var(--y); }
  @supports (color: color-mix(in lab, red, red)) {
    .b { outline-color: color-mix(in oklab, var(--y) 50%, transparent); }
  }
}
`
	tree, err := parseCSS(in)
	if err != nil {
		t.Fatal(err)
	}
	if n := dropFallbacks(tree); n != 3 {
		t.Errorf("dropped %d", n)
	}
	want := "@layer c {\n  .a {\n    color: red;\n  }\n  .a {\n    background-color: color-mix(in oklab, var(--x) 50%, transparent);\n  }\n  .b {\n    outline-color: color-mix(in oklab, var(--y) 50%, transparent);\n  }\n}\n"
	if got := tree.String(); got != want {
		t.Errorf("got\n%s\nwant\n%s", got, want)
	}
}

func TestParseMap(t *testing.T) {
	m, fps, err := parseMap("a/B/svg\t& > svg\n\nc/D\t[data-slot=\"c\"] > div\ne/F/div#2\t-\t0a1b2c3d\n")
	if err != nil || m["a/B/svg"] != "& > svg" || m["c/D"] != `[data-slot="c"] > div` || fps["e/F/div#2"] != "0a1b2c3d" {
		t.Errorf("map %v %v %v", m, fps, err)
	}
	if _, _, err := parseMap("a\tx\na\ty\n"); err == nil {
		t.Error("duplicate key accepted")
	}
	if _, _, err := parseMap("only-key\n"); err == nil {
		t.Error("line without a selector accepted")
	}
	if _, _, err := parseMap("a/B/div#1\tx\n"); err == nil {
		t.Error("#n key without a fingerprint accepted")
	}
}

func TestSourceFix(t *testing.T) {
	g := newGen(nil, nil, nil, nil)
	if got := g.fix("data-starting-style:data-activation-direction=left:translate-x-[-50%]"); got != "data-starting-style:data-[activation-direction=left]:translate-x-[-50%]" {
		t.Errorf("fix: %s", got)
	}
	if got := g.fix("data-open:animate-in"); got != "data-open:animate-in" {
		t.Errorf("unchanged class changed: %s", got)
	}
}

const compositionSource = `import { cva } from "class-variance-authority"

const buttonVariants = cva("inline-flex", {
  variants: {
    variant: { default: "bg-primary", ghost: "bg-transparent" },
    size: { default: "h-8", xs: "h-6" },
  },
  defaultVariants: { variant: "default", size: "default" },
})

function Button({ className, variant = "default", size = "default", ...props }: Props) {
  return <ButtonPrimitive data-slot="button" className={cn(buttonVariants({ variant, size, className }))} {...props} />
}

const groupButtonVariants = cva("gap-2", {
  variants: { size: { xs: "h-6 px-1", sm: "h-8" } },
  defaultVariants: { size: "xs" },
})

function GroupButton({ className, variant = "ghost", size = "xs", ...props }: Props) {
  return <Button data-size={size} variant={variant} className={cn(groupButtonVariants({ size }), className)} {...props} />
}

function Close({ className, render = <Button variant="ghost" size="xs" />, ...props }: Props) {
  return <ClosePrimitive data-slot="close" render={render} className={cn("relative", className)} {...props} />
}

function Action({ className, variant, ...props }: Props) {
  return <Button data-slot="action" variant={variant ?? "ghost"} className={cn("ms-1", className)} {...props} />
}

function DialogAction({ className, ...props }: Props) {
  return <Button data-slot="dialog-action" className={cn("me-1", className)} {...props} />
}
`

func TestComposition(t *testing.T) {
	s, err := parseSource("button", compositionSource)
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"button": s}, nil, nil, nil)
	g.physical = true
	g.component("button")
	g.applyShadows()
	var marker, button *part
	for _, p := range g.parts {
		switch {
		case p.marker == "data-group-button":
			marker = p
		case p.slot == "button" && p.marker == "" && p.context == "":
			button = p
		}
	}
	if marker == nil || button == nil {
		t.Fatalf("parts: %+v", g.parts)
	}
	if marker.set["data-variant"] != "ghost" || marker.set["data-size"] != "xs" {
		t.Errorf("marker fixed props: %v", marker.set)
	}
	if !hasLayer(marker, "", "h-8") || !hasLayer(marker, `:where(:is(:not([data-size]), [data-size="xs"]))`, "h-6 px-1") {
		t.Errorf("marker layers: %+v", marker.layers)
	}
	if !hasLayer(button, `:where([data-size="xs"]):where(:not([data-group-button]))`, "h-6") {
		t.Errorf("button size is not shadowed for the part: %+v", button.layers)
	}
	close := findPart(g, "close")
	if close == nil || layerText(close.layers) != "inline-flex bg-transparent h-6 relative" {
		t.Errorf("JSX default render prop: %+v", close)
	}
}

func TestPassThroughVariants(t *testing.T) {
	s, err := parseSource("button", compositionSource)
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"button": s}, nil, nil, nil)
	g.physical = true
	g.component("button")
	p := findPart(g, "dialog-action")
	if p == nil {
		t.Fatalf("parts: %+v", g.parts)
	}
	if !hasLayer(p, `:where([data-variant="ghost"])`, "bg-transparent") || !hasLayer(p, `:where(:is(:not([data-variant]), [data-variant="default"]))`, "bg-primary") || !hasLayer(p, `:where([data-size="xs"])`, "h-6") || !hasLayer(p, "", "me-1") {
		t.Errorf("variants passed through {...props} are free: %+v", p.layers)
	}
}

func TestEmitOrder(t *testing.T) {
	g := newGen(nil, nil, nil, nil)
	g.parts = []*part{
		{slot: "field", layers: []layer{{classes: []string{"flex", "*:w-full"}}}},
		{slot: "label", layers: []layer{{classes: []string{"w-fit"}}}},
	}
	css := g.emitComponents(kitMap{}, map[string]string{}, map[string]bool{})
	a, b, c := strings.Index(css, "@apply flex;"), strings.Index(css, "@apply w-fit;"), strings.Index(css, "@apply *:w-full;")
	if a < 0 || b < 0 || c < 0 || !(a < b && b < c) {
		t.Errorf("plain classes of every part come before variant classes:\n%s", css)
	}
}

func TestRulesOrder(t *testing.T) {
	g := newGen(nil, nil, nil, nil)
	cond := `:where([data-size="sm"])`
	p := &part{slot: "x", layers: []layer{{classes: []string{"rounded-lg"}}, {cond: cond, classes: []string{"rounded-md"}}, {classes: []string{"rounded-full"}}}}
	prim := map[string]string{"rounded-lg": "border-radius", "rounded-md": "border-radius", "rounded-full": "border-radius"}
	got := g.rules(p, prim, nil)
	if len(got) != 2 || !slices.Equal(got[0].classes, []string{"rounded-full"}) || got[1].cond != cond || len(got[1].classes) != 0 {
		t.Errorf("a later base class wins over an earlier variant class: %+v", got)
	}
	p.layers = []layer{{classes: []string{"rounded-lg"}}, {cond: cond, classes: []string{"rounded-md"}}}
	got = g.rules(p, prim, nil)
	if len(got) != 3 || got[1].cond != ":not("+cond+")" || !slices.Equal(got[2].classes, []string{"rounded-md"}) {
		t.Errorf("a later variant class wins where it applies: %+v", got)
	}
	g.props = map[string][]string{"size-6": {"width", "height"}, "w-full": {"width"}}
	p.layers = []layer{{classes: []string{"size-6"}}, {cond: cond, classes: []string{"w-full"}}}
	got = g.rules(p, map[string]string{"size-6": "width", "w-full": "width"}, nil)
	if len(got) != 2 || !slices.Equal(got[0].classes, []string{"size-6"}) || !slices.Equal(got[1].classes, []string{"w-full", "size-6"}) {
		t.Errorf("a later variant class that sets fewer properties does not remove the base class: %+v", got)
	}
	sizes := map[string]string{"flex": "display", "size-6": "width", "w-full": "width"}
	p.layers = []layer{{classes: []string{"flex"}}, {cond: cond, classes: []string{"size-6"}}, {classes: []string{"w-full"}}}
	got = g.rules(p, sizes, nil)
	if len(got) != 2 || !slices.Equal(got[0].classes, []string{"flex", "w-full"}) || !slices.Equal(got[1].classes, []string{"size-6", "w-full"}) {
		t.Errorf("a later base class that sets fewer properties does not remove the variant class: %+v", got)
	}
	p.layers = []layer{{classes: []string{"flex"}}, {cond: cond, classes: []string{"w-full"}}, {classes: []string{"size-6"}}}
	got = g.rules(p, sizes, nil)
	if len(got) != 2 || !slices.Equal(got[0].classes, []string{"flex", "size-6"}) || len(got[1].classes) != 0 {
		t.Errorf("a later base class that sets all properties of the variant class removes it: %+v", got)
	}
}

func TestProbeClassesKeepsUnknown(t *testing.T) {
	runs := 0
	unknown := map[string]bool{"easing-[ease]": true, "xs:w-full": true, "only-b": true}
	compile := func(css string) (string, string, error) {
		runs++
		for _, m := range regexp.MustCompile(`@apply ([^;]+);`).FindAllStringSubmatch(css, -1) {
			if unknown[m[1]] {
				return "", "Error: Cannot apply unknown utility class `" + m[1] + "`", errors.New("exit status 1")
			}
		}
		return css, "", nil
	}
	a := []string{"flex", "easing-[ease]", "p-2", "xs:w-full"}
	if _, drop, err := probeClasses("theme 1", a, compile); err != nil || runs != 3 || len(drop) != 2 {
		t.Errorf("the first style finds each unknown class with one run: %d runs, %v, %v", runs, drop, err)
	}
	runs = 0
	if css, drop, err := probeClasses("theme 1", append(a, "only-b"), compile); err != nil || runs != 2 || len(drop) != 3 || !drop["only-b"] || strings.Contains(css, "easing") {
		t.Errorf("the next style with the same Tailwind input starts with the known classes and finds its own: %d runs, %v, %v", runs, drop, err)
	}
	runs = 0
	if _, drop, err := probeClasses("theme 1", []string{"flex", "xs:w-full"}, compile); err != nil || runs != 1 || len(drop) != 1 {
		t.Errorf("a known class that the style does not have is not dropped: %d runs, %v, %v", runs, drop, err)
	}
	runs = 0
	if _, _, err := probeClasses("theme 2", a, compile); err != nil || runs != 3 {
		t.Errorf("another Tailwind input probes again: %d runs, %v", runs, err)
	}
	if _, _, err := probeClasses("theme 3", a, func(string) (string, string, error) { return "", "boom", errors.New("exit status 1") }); err == nil || !strings.Contains(err.Error(), "boom") {
		t.Errorf("another Tailwind error stops the run: %v", err)
	}
}

func TestStaleSourceFixes(t *testing.T) {
	gen := func(classes string) *gen {
		s, err := parseSource("x", "function X({ className, ...props }: Props) {\n  return <div data-slot=\"x\" className={cn(\""+classes+"\", className)} {...props} />\n}\n")
		if err != nil {
			t.Fatal(err)
		}
		return newGen(map[string]*source{"x": s}, map[string]string{}, nil, map[string]string{"cn-x-ignored": ""})
	}
	all := "flex data-activation-direction=left:translate-x-1 [&_svg:not([class*='size-'])]:size-4 cn-x-ignored"
	if err := gen(all).generate([]string{"x"}, true); err != nil {
		t.Errorf("every source fix and ignored marker matches: %v", err)
	}
	if err := gen("flex").generate([]string{"x"}, false); err != nil {
		t.Errorf("a run of some components does not check the fixes: %v", err)
	}
	err := gen("flex").generate([]string{"x"}, true)
	for _, want := range []string{"source fix 1 ", "source fix 2 ", "ignored marker cn-x-ignored matched nothing", "remove it from tools/gen/main.go"} {
		if err == nil || !strings.Contains(err.Error(), want) {
			t.Errorf("a fix or marker that matches nothing must stop the run with %q: %v", want, err)
		}
	}
}

func TestPortedComponents(t *testing.T) {
	groups, err := readGroups("groups.tsv")
	if err != nil {
		t.Fatal(err)
	}
	ui := append(slices.Clone(groups.order), "fake-upstream")
	ported, notPorted := portedComponents(ui, groups)
	if !slices.Equal(ported, groups.order) || !slices.Equal(notPorted, []string{"fake-upstream"}) {
		t.Errorf("only the components in groups.tsv are generated: ported %v, not ported %v", ported, notPorted)
	}
	if _, err := groups.slotGroup("fake-upstream-item"); err == nil || !strings.Contains(err.Error(), "add a line <component><TAB><group> to tools/gen/groups.tsv") {
		t.Errorf("the dist error names the groups.tsv fix: %v", err)
	}
}
