package main

import (
	"encoding/json"
	"os/exec"
	"slices"
	"strings"
	"testing"
)

const propsSource = `function Cal({ className, classNames, ...props }: Props) {
  const local = props.mode === "range"
  return (
    <Picker
      data-slot="cal"
      className={cn("p-1", local && "ring-1", className)}
      classNames={{
        day: cn("size-8", props.showWeekNumber ? "rounded-l-md" : "rounded-l-none"),
      }}
      {...props}
    />
  )
}

function Row({ className, ...props }: Props) {
  return <div data-slot="row" className={cn("flex", props.dense ? "gap-1" : "gap-2", className)} {...props} />
}
`

func TestPropsMembers(t *testing.T) {
	s, err := parseSource("cal", propsSource)
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"cal": s}, nil, map[string]string{"cal/Cal/classNames.day": `[data-slot="cal-day"]`}, nil)
	g.physical = true
	g.component("cal")
	row := findPart(g, "row")
	yes := `:where([data-dense]:not([data-dense="false"]))`
	if row == nil || !hasLayer(row, yes, "gap-1") || !hasLayer(row, ":not("+yes+")", "gap-2") {
		t.Errorf("props.dense on the root: %+v", row)
	}
	var day *part
	for _, p := range g.parts {
		if p.sel == `[data-slot="cal-day"]` {
			day = p
		}
	}
	owner := `:where([data-slot="cal"][data-show-week-number]:not([data-show-week-number="false"]) *)`
	if day == nil || !hasLayer(day, owner, "rounded-l-md") || !hasLayer(day, ":not("+owner+")", "rounded-l-none") {
		t.Errorf("props.showWeekNumber in classNames: %+v", day)
	}
	notes := strings.Join(g.notes["unmapped construct"], "\n")
	if !strings.Contains(notes, "cal/Cal: local is not a prop, a context value, or a constant") {
		t.Errorf("unknown identifier without a note: %q", notes)
	}
}

const themesSource = `export const THEMES = [
  {
    name: "neutral",
    cssVars: {
      light: {
        background: "oklch(1 0 0)",
        "card-foreground": "oklch(0.145 0 0)",
        radius: "0.625rem",
      },
      dark: {
        background: "oklch(0.145 0 0)",
        border: "oklch(1 0 0 / 10%)",
      },
    },
  },
  {
    name: "stone",
    cssVars: { light: { background: "oklch(0.9 0 0)" }, dark: { background: "oklch(0.1 0 0)" } },
  },
]
`

func TestNeutralTheme(t *testing.T) {
	light, dark, err := parseTheme(themesSource, "neutral")
	if err != nil {
		t.Fatal(err)
	}
	if !slices.Equal(light, [][2]string{{"background", "oklch(1 0 0)"}, {"card-foreground", "oklch(0.145 0 0)"}, {"radius", "0.625rem"}}) || len(dark) != 2 {
		t.Errorf("neutral: %v %v", light, dark)
	}
	css := tokensCSS(light, dark)
	for _, want := range []string{"  :root {\n    color-scheme: light dark;\n    --background: oklch(1 0 0);\n    --card-foreground: oklch(0.145 0 0);\n    --radius: 0.625rem;\n  }", "  [data-theme=\"dark\"] {\n    color-scheme: dark;\n    --background: oklch(0.145 0 0);\n    --border: oklch(1 0 0 / 10%);\n  }", ":root:not([data-theme=\"light\"]) {\n      --background: oklch(0.145 0 0);"} {
		if !strings.Contains(css, want) {
			t.Errorf("tokens CSS has no %q:\n%s", want, css)
		}
	}
	theme, err := themeCSS("@theme inline {\n  --font-sans: var(--font-sans);\n  --radius-sm: calc(var(--radius) * 0.6);\n  --color-background: var(--background);\n  --color-surface: var(--surface);\n}\n", map[string]bool{"--background": true, "--radius": true})
	if err != nil || theme != "@theme inline {\n  --radius-sm: calc(var(--radius) * 0.6);\n  --color-background: var(--background);\n}\n" {
		t.Errorf("theme: %q %v", theme, err)
	}
	if _, _, err := parseTheme(strings.Replace(themesSource, `"oklch(0.145 0 0)",`, `"red; } @plugin 'x'; a {",`, 1), "neutral"); !isUnsafe(err) {
		t.Errorf("unsafe theme value accepted: %v", err)
	}
	if _, _, err := parseTheme(themesSource, "zinc"); err == nil {
		t.Error("missing theme accepted")
	}
}

func TestMapChecks(t *testing.T) {
	src := `function Item({ className, ...props }: Props) {
  return (
    <div data-slot="item" className={cn("flex", className)} {...props}>
      <span className="size-4" />
      <span className="size-5" />
    </div>
  )
}
`
	s, err := parseSource("item", src)
	if err != nil {
		t.Fatal(err)
	}
	manual := map[string]string{"item/Item/span#1": "& > span:first-child", "item/Item/span#2": "& > span:last-child", "item/Gone": "[data-slot=\"gone\"]", "other/X": "x"}
	g := newGen(map[string]*source{"item": s}, nil, manual, nil)
	g.fps = map[string]string{"item/Item/span#1": fingerprint(`span className="size-4"`), "item/Item/span#2": fingerprint(`span className="size-4"`)}
	g.component("item")
	err = g.mapErr([]string{"item"})
	if err == nil {
		t.Fatal("no map error")
	}
	msg := err.Error()
	if !strings.Contains(msg, "item/Gone: matches no element") || strings.Contains(msg, "other/X") || !strings.Contains(msg, "item/Item/span#2: element fingerprint") || strings.Contains(msg, "item/Item/span#1:") {
		t.Errorf("map error: %s", msg)
	}
}

func TestPostprocessClasses(t *testing.T) {
	g := newGen(nil, nil, map[string]string{"calendar/Calendar/classNames.button_next": `[data-slot="calendar-button-next"]`, "calendar/Calendar/classNames.day": "&"}, nil)
	out := postprocess(":is(.rdp-button_next > svg), .rdp-day {\n}\n", nil, kitMap{}, g)
	if !strings.Contains(out, `:is([data-slot="calendar-button-next"] > svg), .rdp-day {`) {
		t.Errorf("rdp classes: %s", out)
	}
	tree, err := parseCSS("@layer a {\n  [data-slot=\"card-header\"].border-b { color: red; }\n  [data-slot=\"x\"] .sr-only, [data-x=\".y\"] { color: red; }\n}\n")
	if err != nil {
		t.Fatal(err)
	}
	g.classSelectors(tree)
	if got := g.notes["selector with a class that kit markup does not set"]; len(got) != 1 || !strings.HasPrefix(got[0], ".border-b in ") {
		t.Errorf("class selector notes: %v", got)
	}
	g = newGen(nil, map[string]string{"cn-chart": "flex [&_.recharts-layer]:outline-hidden"}, nil, nil)
	ls, _ := g.classes("cn-chart [&_.recharts-surface]:outline-hidden aspect-video")
	if layerText(ls) != "flex aspect-video" {
		t.Errorf("recharts classes kept: %q", layerText(ls))
	}
}

func TestMergeKeys(t *testing.T) {
	prim := map[string]string{"text-red": "color", "text-blue!": "color", "!text-green": "color", "hover:focus:bg-a": "background-color", "focus:hover:bg-b": "background-color", "*:hover:bg-c": "background-color", "hover:*:bg-d": "background-color"}
	keep, _ := twMerge([]string{"text-blue!", "text-red"}, prim, nil)
	if len(keep) != 2 {
		t.Errorf("an important class and a normal class both stay: %v", keep)
	}
	keep, _ = twMerge([]string{"!text-green", "text-blue!"}, prim, nil)
	if !slices.Equal(keep, []string{"text-blue!"}) {
		t.Errorf("two important classes conflict: %v", keep)
	}
	keep, _ = twMerge([]string{"hover:focus:bg-a", "focus:hover:bg-b"}, prim, nil)
	if !slices.Equal(keep, []string{"focus:hover:bg-b"}) {
		t.Errorf("modifier order does not matter: %v", keep)
	}
	keep, _ = twMerge([]string{"*:hover:bg-c", "hover:*:bg-d"}, prim, nil)
	if len(keep) != 2 {
		t.Errorf("order-sensitive modifiers keep their place: %v", keep)
	}
}

func TestTSXErrors(t *testing.T) {
	if _, _, err := parseElement(`<a b="x`, 0); err == nil {
		t.Error("unclosed attribute string accepted")
	}
	if _, _, err := parseElement(`<a b=`, 0); err == nil {
		t.Error("attribute without a value accepted")
	}
	for src, want := range map[string]int{
		`{ "a\"}" }`:       10,
		`{ a /* } */ }`:    13,
		"{ a // }\n }":     11,
		`{ 'it\'s' }`:      11,
		"{ `${'}'}` + x }": 16,
	} {
		if got, err := matchFrom(src, 0); err != nil || got != want {
			t.Errorf("matchFrom(%q) = %d, %v; want %d", src, got, err, want)
		}
	}
}

func TestSourceTokens(t *testing.T) {
	s, err := parseSource("x", "import { Button } from \"@/registry/bases/base/ui/button\"\nfunction X({ className, ...props }: Props) {\n  return <div data-slot=\"x\" className={cn(\"cn-x pl-2\", 'flex')} {...props} />\n}\n")
	if err != nil {
		t.Fatal(err)
	}
	b, err := parseSource("button", "function Button() {\n  return <button data-slot=\"button\" className=\"h-8\" />\n}\n")
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"x": s, "button": b}, map[string]string{"cn-x": "mr-1"}, nil, nil)
	got := g.sourceTokens("x")
	for _, want := range []string{"cn-x", "pl-2", "ps-2", "flex", "mr-1", "me-1", "h-8"} {
		if !slices.Contains(got, want) {
			t.Errorf("source tokens have no %s: %v", want, got)
		}
	}
	m := g.logicalMap(got)
	if m["pl-2"] != "ps-2" || m["mr-1"] != "me-1" || m["ps-2"] != "" || m["flex"] != "" {
		t.Errorf("logical map: %v", m)
	}
}

func TestScopedGroups(t *testing.T) {
	srcs := map[string]string{
		"a": "function A({ className, ...props }: Props) {\n  return (\n    <div data-slot=\"a\" className=\"group flex\">\n      <span data-slot=\"a-icon\" className=\"group-hover:underline peer-checked:hidden group-data-[x=y]/named:block\" />\n    </div>\n  )\n}\n",
		"b": "function B({ className, ...props }: Props) {\n  return <div data-slot=\"b\" className=\"group flex\" />\n}\n",
		"c": "function C({ className, ...props }: Props) {\n  return (\n    <div role=\"group\" data-slot=\"c\" className=\"flex\">\n      <i data-slot=\"c-icon\" className=\"group-hover:underline\" />\n    </div>\n  )\n}\n",
	}
	sources := map[string]*source{}
	for name, text := range srcs {
		s, err := parseSource(name, text)
		if err != nil {
			t.Fatal(err)
		}
		sources[name] = s
	}
	g := newGen(sources, nil, nil, nil)
	g.physical = true
	for _, name := range []string{"a", "b", "c"} {
		g.component(name)
	}
	if p := findPart(g, "a-icon"); p == nil || layerText(p.layers) != "group-hover/kit-a:underline peer-checked:hidden group-data-[x=y]/named:block" {
		t.Errorf("unnamed group of a part with its own group: %+v", p)
	}
	if p := findPart(g, "c-icon"); p == nil || layerText(p.layers) != "group-hover:underline" {
		t.Errorf("role=\"group\" is no group class: %+v", p)
	}
	owners := g.groupOwners(kitMap{})
	if !slices.Equal(owners[`.group\/kit-a`], []string{`[data-slot="a"]`}) {
		t.Errorf("scoped owners: %v", owners)
	}
	if !slices.Equal(owners[".group"], []string{`[data-slot="a"]`, `[data-slot="b"]`}) {
		t.Errorf("unnamed owners for parts without their own group: %v", owners[".group"])
	}
}

func TestDirVariantsAndGlue(t *testing.T) {
	if !strings.Contains(glue, ":where(dialog[data-slot]:not([open]), [data-slot][popover]:not(:popover-open))") || strings.Contains(glue, ", [popover]:not(") {
		t.Errorf("the glue hides popovers that are not kit parts:\n%s", glue)
	}
	g := newGen(nil, nil, nil, nil)
	out := postprocess("a:where([dir=\"rtl\"], [dir=\"rtl\"] *) {}\nb:where(:dir(ltr), [dir=\"ltr\"]) {}\nc:where(:dir(rtl), [dir=rtl], [dir=rtl] *) {}\nd[dir=rtl] {}\n", nil, kitMap{}, g)
	if !strings.Contains(out, "a:where(:dir(rtl)) {}\nb:where(:dir(ltr)) {}\nc:where(:dir(rtl)) {}\nd[dir=rtl] {}") {
		t.Errorf("direction selectors:\n%s", out)
	}
	tailwind, err := exec.LookPath("tailwindcss")
	if err != nil {
		t.Skip("tailwindcss not installed")
	}
	css, stderr, err := compile(tailwind, t.TempDir(), importUtilities+"\n"+darkVariant+"@layer clanker.components { [data-a] { @apply rtl:rotate-180 ltr:hidden; } }\n", importUtilities)
	if err != nil {
		t.Fatalf("%v %s", err, stderr)
	}
	if !strings.Contains(css, ":where(:dir(rtl))") || !strings.Contains(css, ":where(:dir(ltr))") || strings.Contains(css, "[dir=rtl]") || strings.Contains(css, "[dir=\"rtl\"]") {
		t.Errorf("rtl and ltr must follow the nearest dir only:\n%s", css)
	}
}

func TestDrawerBackdrop(t *testing.T) {
	g := newGen(nil, nil, nil, nil)
	out := postprocess(kit.slot("drawer-overlay")+":where([data-open]) {\n}\n"+kit.slot("dialog-overlay")+" {\n}\n", nil, kit, g)
	if !strings.Contains(out, "[data-slot=\"drawer-viewport\"]:where([data-open])::backdrop {") || !strings.Contains(out, "[data-slot=\"dialog-content\"]::backdrop {") {
		t.Errorf("the drawer overlay is the backdrop of the drawer viewport (the Base UI drawer dialog):\n%s", out)
	}
}

func TestClassNamesParamsAndChildInstances(t *testing.T) {
	src := `function Cal({ className, classNames, captionLayout = "label", ...props }: Props) {
  return (
    <Picker
      captionLayout={captionLayout}
      className={cn("p-2", className)}
      classNames={{
        caption_label: cn("font-medium", captionLayout === "label" ? "text-sm" : "flex h-8"),
      }}
      {...props}
    />
  )
}

function Icon({ className, ...props }: Props) {
  return <span data-slot="icon" className={cn("size-4", className)} {...props} />
}

function Trigger({ className, children, ...props }: Props) {
  return (
    <button data-slot="trigger" className={cn("flex", className)} {...props}>
      {children}
      <Icon className="rotate-90" />
    </button>
  )
}
`
	s, err := parseSource("cal", src)
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"cal": s}, nil, map[string]string{"cal/Cal": `[data-slot="cal"]`, "cal/Cal/classNames.caption_label": `[data-slot="cal-caption"]`}, nil)
	g.physical = true
	g.component("cal")
	var caption *part
	for _, p := range g.parts {
		if p.sel == `[data-slot="cal-caption"]` {
			caption = p
		}
	}
	label := `:where([data-slot="cal"]:is(:not([data-caption-layout]), [data-caption-layout="label"]) *)`
	if caption == nil || !hasLayer(caption, label, "text-sm") || !hasLayer(caption, ":not("+label+")", "flex h-8") {
		t.Errorf("a classNames condition on a prop selects the attribute on the root: %+v", caption)
	}
	var icon *part
	for _, p := range g.parts {
		if p.slot == "icon" && p.context != "" {
			icon = p
		}
	}
	if icon == nil || (kitMap{}).selector(icon) != `:where([data-slot="trigger"]) > [data-slot="icon"]` {
		t.Errorf("an instance that is a direct child of the root is a child selector: %+v", icon)
	}
}

func TestComponentsProp(t *testing.T) {
	src := `function Cal({ className, components, ...props }: Props) {
  return (
    <Picker
      className={cn("p-2", className)}
      components={{
        Chevron: ({ className, orientation, ...props }) => {
          if (orientation === "left") {
            return <IconPlaceholder lucide="ChevronLeftIcon" className={cn("cn-rtl-flip size-4", className)} {...props} />
          }
          return <IconPlaceholder lucide="ChevronDownIcon" className={cn("size-4", className)} {...props} />
        },
        WeekNumber: ({ children, ...props }) => {
          return (
            <td {...props}>
              <div className="flex size-(--cell-size) items-center">{children}</div>
            </td>
          )
        },
        Extra: ({ ...props }) => <span className="block" {...props} />,
        ...components,
      }}
      {...props}
    />
  )
}
`
	s, err := parseSource("cal", src)
	if err != nil {
		t.Fatal(err)
	}
	manual := map[string]string{"cal/Cal": `[data-slot="cal"]`, "cal/Cal/components.Chevron/IconPlaceholder#1": `:where([data-slot="cal-prev"]) > svg`, "cal/Cal/components.Chevron/IconPlaceholder#2": `:where([data-slot="cal-caption"]) > svg`, "cal/Cal/components.WeekNumber/div": `:where([data-slot="cal-week-number"]) > div`}
	g := newGen(map[string]*source{"cal": s}, nil, manual, map[string]string{"cn-rtl-flip": "rtl:rotate-180"})
	g.physical = true
	g.component("cal")
	got := map[string]string{}
	for _, p := range g.parts {
		if p.sel != "" {
			got[p.sel] = layerText(p.layers)
		}
	}
	if got[`:where([data-slot="cal-prev"]) > svg`] != "rtl:rotate-180 size-4" || got[`:where([data-slot="cal-caption"]) > svg`] != "size-4" || got[`:where([data-slot="cal-week-number"]) > div`] != "flex size-(--cell-size) items-center" {
		t.Errorf("components render functions: %v", got)
	}
	if notes := strings.Join(g.notes["unmapped element"], "\n"); !strings.Contains(notes, `cal/Cal/components.Extra/span: classes "block"`) {
		t.Errorf("an unmapped components element needs a note: %q", notes)
	}
}

func TestHasVariantAttribute(t *testing.T) {
	src := `function Bubble({ variant = "default", ...props }: Props) {
  return <div data-slot="bubble" data-variant={variant} {...props} />
}

function Button({ className, ...props }: Props) {
  return <button data-slot="button" className={cn("h-8", className)} {...props} />
}
`
	s, err := parseSource("bubble", src)
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"bubble": s}, nil, nil, nil)
	out := postprocess("[data-slot=\"message-footer\"]:is(:where([data-slot=\"message\"]):has([data-variant=\"ghost\"]) *) {\n}\n[data-slot=\"x\"]:has(> [data-variant]) {\n}\n", nil, kitMap{}, g)
	if !strings.Contains(out, `:has(:is([data-slot="bubble"])[data-variant="ghost"])`) || !strings.Contains(out, `:has(> [data-variant])`) {
		t.Errorf("has() of data-variant must not match kit buttons:\n%s", out)
	}
}

func TestFingerprintSeesMarkersAndAttributes(t *testing.T) {
	print := func(src string) string {
		e, _, err := parseElement(src, 0)
		if err != nil {
			t.Fatal(err)
		}
		return fingerprint(elemPrint(e))
	}
	base := print(`<IconPlaceholder lucide="ChevronLeftIcon" className={cn("cn-rtl-flip size-4", className)} />`)
	for _, other := range []string{
		`<IconPlaceholder lucide="ChevronRightIcon" className={cn("cn-rtl-flip size-4", className)} />`,
		`<IconPlaceholder lucide="ChevronLeftIcon" className={cn("size-4", className)} />`,
	} {
		if print(other) == base {
			t.Errorf("same fingerprint for %s", other)
		}
	}
}

func TestExtraClassNameProps(t *testing.T) {
	src := `function Otp({ className, containerClassName, ...props }: Props) {
  return (
    <OTPInput
      data-slot="otp"
      containerClassName={cn("cn-otp flex items-center has-disabled:opacity-50", containerClassName)}
      className={cn("cn-otp-input disabled:cursor-not-allowed", className)}
      {...props}
    />
  )
}
`
	s, err := parseSource("otp", src)
	if err != nil {
		t.Fatal(err)
	}
	manual := map[string]string{"otp/Otp": `:where([data-slot="otp"]) input`, "otp/Otp/containerClassName": `[data-slot="otp"]`}
	g := newGen(map[string]*source{"otp": s}, map[string]string{"cn-otp": "gap-2", "cn-otp-input": "text-sm"}, manual, nil)
	g.physical = true
	g.component("otp")
	got := map[string]string{}
	for _, p := range g.parts {
		got[(kitMap{}).selector(p)] = layerText(p.layers)
	}
	if got[`[data-slot="otp"]`] != "flex items-center has-disabled:opacity-50" || got[`:where([data-slot="otp"]) input`] != "text-sm disabled:cursor-not-allowed" {
		t.Errorf("containerClassName goes to the container, className to the input; the shadcn transform keeps container markers: %v", got)
	}
}

func TestClassNamesMarkers(t *testing.T) {
	src := `import { buttonVariants } from "@/registry/bases/base/ui/button"

function Cal({ className, classNames, ...props }: Props) {
  return (
    <Picker
      className={cn("cn-cal p-2", className)}
      classNames={{
        dropdown_root: cn("cn-cal-dropdown-root relative", defaultClassNames.dropdown_root),
        button_next: cn(buttonVariants({ variant: "ghost" }), "p-0"),
      }}
      {...props}
    />
  )
}
`
	s, err := parseSource("cal", src)
	if err != nil {
		t.Fatal(err)
	}
	b, err := parseSource("button", `const buttonVariants = cva("cn-button inline-flex", {
  variants: { variant: { ghost: "cn-button-variant-ghost" } },
})
`)
	if err != nil {
		t.Fatal(err)
	}
	manual := map[string]string{"cal/Cal": `[data-slot="cal"]`, "cal/Cal/classNames.dropdown_root": `[data-slot="cal-dropdown-root"]`, "cal/Cal/classNames.button_next": `[data-slot="cal-next"]`}
	g := newGen(map[string]*source{"cal": s, "button": b}, map[string]string{"cn-cal": "bg-background", "cn-cal-dropdown-root": "border", "cn-button": "rounded-lg", "cn-button-variant-ghost": "hover:bg-muted"}, manual, nil)
	g.physical = true
	g.component("cal")
	got := map[string]string{}
	for _, p := range g.parts {
		got[(kitMap{}).selector(p)] = layerText(p.layers)
	}
	if got[`[data-slot="cal"]`] != "bg-background p-2" || got[`[data-slot="cal-dropdown-root"]`] != "relative" || !strings.Contains(got[`[data-slot="cal-next"]`], "rounded-lg") {
		t.Errorf("the shadcn transform replaces className and cva markers and keeps classNames markers: %v", got)
	}
}

func TestSlotAlias(t *testing.T) {
	s, err := parseSource("group", "function Group({ className, ...props }: Props) {\n  return <div data-slot=\"group\" className={cn(\"flex flex-col data-[slot=check-group]:gap-3\", className)} {...props} />\n}\n")
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"group": s}, nil, nil, nil)
	g.physical = true
	g.component("group")
	k := g.slotAliases(kitMap{})
	if got := k.slot("group"); got != `:is([data-slot="group"], [data-slot="check-group"])` {
		t.Errorf("a part renamed by data-[slot=...] keeps its look: %s", got)
	}
}

func TestSlotAliasIgnoresChildVariants(t *testing.T) {
	s, err := parseSource("group", "function Group({ className, ...props }: Props) {\n  return <div data-slot=\"group\" className={cn(\"flex *:data-[slot=item]:gap-1 [&>x]:data-[slot=y]:p-1\", className)} {...props} />\n}\n")
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"group": s}, nil, nil, nil)
	g.physical = true
	g.component("group")
	if got := g.slotAliases(kitMap{}).slot("group"); got != `[data-slot="group"]` {
		t.Errorf("a data-[slot] variant on a child is no rename: %s", got)
	}
}

func TestContextFromSlottedAncestor(t *testing.T) {
	src := `function Group({ className, ...props }: Props) {
  return <div data-slot="group" className={cn("flex", className)} {...props} />
}

function Input({ className, ...props }: Props) {
  return (
    <div data-slot="input-wrapper" className="p-1">
      <Group className="h-8!">
        <Inner data-slot="input" className={cn("outline-hidden", className)} {...props} />
      </Group>
    </div>
  )
}
`
	s, err := parseSource("cmd", src)
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"cmd": s}, nil, nil, nil)
	g.physical = true
	g.component("cmd")
	var got []string
	for _, p := range g.parts {
		if p.slot == "group" && p.context != "" {
			got = append(got, (kitMap{}).selector(p))
		}
	}
	if !slices.Equal(got, []string{`:where([data-slot="input-wrapper"]) > [data-slot="group"]`}) {
		t.Errorf("an instance outside the props element takes its nearest slotted ancestor: %v", got)
	}
}

func TestCvaOnAnotherPart(t *testing.T) {
	src := "const triggerStyle = cva(\"cn-trigger inline-flex h-9\")\n\nfunction Trigger({ className, ...props }: Props) {\n  return <button data-slot=\"menu-trigger\" className={cn(triggerStyle(), className)} {...props} />\n}\n"
	s, err := parseSource("menu", src)
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"menu": s}, map[string]string{"cn-trigger": "rounded-lg"}, map[string]string{"menu/cva.triggerStyle": `[data-slot="menu-link"][data-variant="trigger"]`}, nil)
	g.physical = true
	g.component("menu")
	var p *part
	for _, x := range g.parts {
		if x.from == "menu/cva.triggerStyle" {
			p = x
		}
	}
	if p == nil || p.sel != `[data-slot="menu-link"][data-variant="trigger"]` || p.eslot != "menu-link" || p.set["data-variant"] != "trigger" || layerText(p.layers) != "rounded-lg inline-flex h-9" {
		t.Errorf("cva function mapped to a part attribute: %+v", p)
	}
	if err := g.mapErr([]string{"menu"}); err != nil {
		t.Errorf("used cva key reported: %v", err)
	}
	var parts struct {
		Parts []jsonPart `json:"parts"`
	}
	json.Unmarshal(g.partsJSON(kitMap{}, []string{"menu"}), &parts)
	found := false
	for _, jp := range parts.Parts {
		if jp.From == "menu/cva.triggerStyle" {
			found = jp.Element == "menu-link" && jp.Set["data-variant"] == "trigger" && slices.Contains(jp.Own, "h-9")
		}
	}
	if !found {
		t.Errorf("parts.json gives the parity tool the part, its attribute, and its classes: %+v", parts.Parts)
	}
}

func TestChildrenOfARenamedPart(t *testing.T) {
	menu := `function SubTrigger({ className, children, ...props }: Props) {
  return (
    <Primitive.SubmenuTrigger data-slot="menu-sub-trigger" className={cn("flex", className)} {...props}>
      {children}
      <IconPlaceholder className="cn-rtl-flip ml-auto" />
    </Primitive.SubmenuTrigger>
  )
}

function SubTriggerAlias({ ...props }: Props) {
  return <SubTrigger data-slot="menu-sub-trigger-alias" {...props} />
}

function Fixed({ className, ...props }: Props) {
  return (
    <div {...props} data-slot="menu-fixed" className={cn("grid", className)}>
      <span className="size-4" />
    </div>
  )
}
`
	bar := `import { SubTriggerAlias, Fixed } from "@/registry/bases/base/ui/menu"

function BarSubTrigger({ className, ...props }: Props) {
  return <SubTriggerAlias data-slot="bar-sub-trigger" className={cn("gap-1", className)} {...props} />
}

function BarFixed({ className, ...props }: Props) {
  return <Fixed data-slot="bar-fixed" className={cn("gap-1", className)} {...props} />
}
`
	ms, err := parseSource("menu", menu)
	if err != nil {
		t.Fatal(err)
	}
	bs, err := parseSource("bar", bar)
	if err != nil {
		t.Fatal(err)
	}
	manual := map[string]string{"menu/SubTrigger/IconPlaceholder": "& > svg:last-child", "menu/Fixed/span": "& > span"}
	g := newGen(map[string]*source{"menu": ms, "bar": bs}, nil, manual, map[string]string{"cn-rtl-flip": "rtl:rotate-180"})
	g.physical = true
	g.component("menu")
	g.component("bar")
	sels := map[string]string{}
	for _, p := range g.parts {
		if p.sel != "" {
			sels[p.from] = p.sel
		}
	}
	if got := sels["menu/SubTrigger/IconPlaceholder"]; got != `:where(:is([data-slot="menu-sub-trigger"], [data-slot="bar-sub-trigger"], [data-slot="menu-sub-trigger-alias"])) > svg:last-child` {
		t.Errorf("a child element of a component also matches in the parts that render the component under another data-slot: %q", got)
	}
	if got := sels["menu/Fixed/span"]; got != `:where([data-slot="menu-fixed"]) > span` {
		t.Errorf("a data-slot before the props spread is not renamed: %q", got)
	}
}

func TestNullishDefaultProp(t *testing.T) {
	s, err := parseSource("button", compositionSource)
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"button": s}, nil, nil, nil)
	g.physical = true
	g.component("button")
	action := findPart(g, "action")
	if action == nil {
		t.Fatalf("parts: %+v", g.parts)
	}
	if !hasLayer(action, `:where(:is(:not([data-variant]), [data-variant="ghost"]))`, "bg-transparent") || !hasLayer(action, `:where([data-variant="default"])`, "bg-primary") || hasLayer(action, "", "bg-transparent") || !hasLayer(action, "", "ms-1") {
		t.Errorf("variant={variant ?? \"ghost\"} is a free variant with the default ghost: %+v", action.layers)
	}
}

func glueDecls(t *testing.T, layer, prelude string) []string {
	t.Helper()
	tree, err := parseCSS(glue)
	if err != nil {
		t.Fatal(err)
	}
	for _, l := range tree.items {
		if l.rule == nil || l.rule.prelude != "@layer "+layer {
			continue
		}
		for _, it := range l.rule.items {
			if it.rule != nil && it.rule.prelude == prelude {
				var out []string
				for _, d := range it.rule.items {
					out = append(out, d.decl)
				}
				return out
			}
		}
	}
	return nil
}

func TestDialogFormGlue(t *testing.T) {
	if glueDecls(t, "clanker.components", `[data-slot="dialog-content"] > form`) != nil {
		t.Error("the form glue also matches a form part (questionnaire)")
	}
	if got := glueDecls(t, "clanker.components", `:is([data-slot="dialog-content"], [data-slot="alert-dialog-content"], [data-slot="sheet-content"], [data-slot="drawer-content"]) > form:is(:not([data-slot]), [data-slot="form"])`); !slices.Equal(got, []string{"display: contents"}) {
		t.Errorf("the form glue for a plain form or a form part in overlay content: %v", got)
	}
}

func TestDialogReset(t *testing.T) {
	got := glueDecls(t, "clanker.base", "dialog")
	for _, want := range []string{"width: auto", "height: auto", "background-color: transparent", "color: inherit"} {
		if !slices.Contains(got, want) {
			t.Errorf("the dialog reset has no %q, so a kit <dialog> part (drawer viewport, top and bottom sheet) keeps the browser default: %v", want, got)
		}
	}
}

func TestPartsListMarkers(t *testing.T) {
	s, err := parseSource("x", "function X({ className, ...props }: Props) {\n  return <div data-slot=\"x\" className={cn(\"cn-x cn-rtl-flip flex\", className)} {...props} />\n}\n")
	if err != nil {
		t.Fatal(err)
	}
	g := newGen(map[string]*source{"x": s}, map[string]string{"cn-x": "gap-2"}, nil, map[string]string{"cn-rtl-flip": "rtl:rotate-180"})
	g.physical = true
	g.component("x")
	var parts struct {
		Parts []jsonPart `json:"parts"`
	}
	json.Unmarshal(g.partsJSON(kitMap{}, []string{"x"}), &parts)
	if len(parts.Parts) != 1 || !slices.Equal(parts.Parts[0].Markers, []string{"cn-x", "cn-rtl-flip"}) {
		t.Errorf("parts.json lists the cn-* markers of each part: %+v", parts.Parts)
	}
}
