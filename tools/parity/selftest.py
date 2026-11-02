import sys

sys.dont_write_bytecode = True

import pathlib
import subprocess
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import parity


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    return ok


def tolerance_checks():
    c = parity.close
    return [
        check("opacity 0.5 vs 1 differs", not c("0.5", "1", "opacity")),
        check("opacity 0 vs 0.5 differs", not c("0", "0.5", "opacity")),
        check("opacity 0.4 vs 1 differs", not c("0.4", "1", "opacity")),
        check("opacity 0.5 vs 0.505 is equal", c("0.5", "0.505", "opacity")),
        check("duration 0.1s vs 0.6s differs", not c("0.1s", "0.6s", "transition-duration")),
        check("duration 0.15s vs 0.5s differs", not c("0.15s", "0.5s", "transition-duration")),
        check("duration 0.15s vs 0.16s differs", not c("0.15s", "0.16s", "transition-duration")),
        check("aspect-ratio 1 / 1 vs 1.5 / 1 differs", not c("1 / 1", "1.5 / 1", "aspect-ratio")),
        check("10px vs 10.4px is equal", c("10px", "10.4px", "width")),
        check("10px vs 10.6px differs", not c("10px", "10.6px", "width")),
        check("geometry 100 vs 100.4 is equal", c(100, 100.4, "@w")),
        check("geometry 100 vs 100.6 differs", not c(100, 100.6, "@w")),
        check("10px vs 10% differs", not c("10px", "10%", "width")),
        check("one sRGB step is equal", c("rgba(10,10,10,1.00)", "rgba(11,10,10,1.00)", "color")),
        check("white vs oklch(0.985 0 0) differs", not c("rgba(255,255,255,1.00)", "rgba(250,250,250,1.00)", "background-color")),
        check("black vs dark grey differs", not c("rgba(0,0,0,1.00)", "rgba(37,37,37,1.00)", "color")),
        check("alpha 0.50 vs 0.53 differs", not c("rgba(0,0,0,0.50)", "rgba(0,0,0,0.53)", "background-color")),
        check("alpha 0.10 vs 0.105 is equal", c("rgba(255,255,255,0.10)", "rgba(255,255,255,0.105)", "border-top-color")),
        check("alpha 0.10 vs 0.11 of white differs over black (delta E 0.5)", not c("rgba(255,255,255,0.10)", "rgba(255,255,255,0.11)", "border-top-color")),
        check("matrix translate 0.3px is equal", c("matrix(1, 0, 0, 1, 10, 0)", "matrix(1, 0, 0, 1, 10.3, 0)", "transform")),
        check("matrix scale 0.95 vs 0.96 differs", not c("matrix(0.95, 0, 0, 0.95, 0, 0)", "matrix(0.96, 0, 0, 0.96, 0, 0)", "transform")),
        check("shadow colors use delta E", not c("rgba(0,0,0,0.10) 0px 1px 2px 0px", "rgba(0,0,0,0.30) 0px 1px 2px 0px", "box-shadow")),
        check("huge radii are equal", c("3.35544e+07px", "1e+07px", "border-top-left-radius") and c("159981px", "159984px", "border-top-left-radius")),
        check("font-weight 500 vs 600 differs", not c("500", "600", "font-weight")),
    ]


PARTS = {
    "components": ["badge", "card"],
    "parts": [
        {"slot": "badge", "selector": "[data-slot=\"badge\"]", "from": "badge/Badge", "tokens": ["inline-flex", "h-5", "rounded-4xl", "bg-primary", "border-border"], "variants": [
            {"attr": "data-variant", "value": "default", "default": True, "tokens": ["bg-primary"]},
            {"attr": "data-variant", "value": "outline", "tokens": ["border-border"]}], "mapped": True},
        {"slot": "card", "selector": "[data-slot=\"card\"]", "from": "card/Card", "tokens": ["flex", "gap-4", "rounded-xl"], "markers": ["cn-card", "cn-badge"], "mapped": True},
    ],
    "source_tokens": {"badge": ["inline-flex", "h-5", "rounded-4xl", "bg-primary", "border-border", "pr-2", "pe-2", "size-3", "sr-only"], "card": ["flex", "gap-4", "rounded-xl", "w-full", "cn-badge"]},
}


def converter_checks():
    parts = parity.Parts(PARTS)
    conv = parity.Converter(parts, PARTS["components"], "badge")
    conv.use(['<div className="flex gap-2"><Badge variant="outline" className={cn("rounded-full", on && "px-1")}>A</Badge><Card className="w-full" /></div>'])
    tree = {"i": 1, "t": "div", "a": [["class", "flex gap-2"]], "c": [
        {"i": 2, "t": "span", "a": [["data-slot", "badge"], ["class", "inline-flex h-5 pe-2 border-border cn-badge rounded-full px-1"]], "c": [
            {"i": 3, "t": "svg", "a": [["class", "lucide size-3"]], "c": []}, "A"]},
        {"i": 4, "t": "div", "a": [["data-slot", "card"], ["class", "flex gap-4 rounded-xl w-full"]], "c": []},
        {"i": 5, "t": "div", "a": [["data-slot", "card"], ["class", "flex gap-4 rounded-xl newer-upstream"]], "c": []},
    ]}
    out = conv.node(tree)
    fallback = parity.Converter(parts, PARTS["components"], "badge", [], True)
    kitconv = parity.Converter(parts, PARTS["components"], "badge")
    kitconv.use(['<Badge className="rounded-full">A</Badge>'])
    fb = fallback.node({"i": 6, "t": "span", "a": [["data-slot", "badge"], ["class", "inline-flex bg-primary my-example"]], "c": []})
    return [
        check("layout outside components keeps its classes", '<div data-pid="1" class="flex gap-2">' in out),
        check("badge keeps only the example className suffix", 'data-pid="2" class="rounded-full px-1"' in out),
        check("badge variant comes from its classes", 'data-variant="outline"' in out),
        check("definition classes of a slotless child are removed", '<svg data-pid="3" class="lucide">' in out),
        check("example class that is also a source class stays (card w-full)", 'data-pid="4" class="w-full"' in out and conv.kept_source["card"] == {"w-full"}),
        check("a class that is not in the pin is removed and listed", 'data-pid="5">' in out and conv.unpinned["card"] == {"newer-upstream"}),
        check("views without example code keep only classes that are not in the source", 'class="my-example"' in fb),
        check("the kit utility sr-only stays, also from a component definition", 'class="sr-only"' in kitconv.node({"i": 7, "t": "span", "a": [["data-slot", "badge"], ["class", "sr-only"]], "c": [{"i": 8, "t": "span", "a": [["class", "sr-only size-3"]], "c": ["x"]}]})),
    ]


def style_checks():
    ex = object.__new__(parity.Examples)
    ex.text = {"bubble-demo": 'import { Bubble } from "@/styles/base-rhea/ui/bubble"\nimport { Button } from "@/styles/base-nova/ui/button"\nexport function BubbleDemo() {}', "badge-demo": 'import { Badge } from "@/styles/base-nova/ui/badge"\nexport function BadgeDemo() {}'}
    ex.text["calendar-hijri"] = 'import { Button } from "@/styles/base-nova/ui/button"\nfunction Calendar() {}\nexport function CalendarHijri() {}'
    ex.text["drawer-swipe-handle"] = 'import { Drawer } from "@/styles/base-nova/ui/drawer"\nexport function DrawerSwipeHandle() {}'
    ex.ui_fns = {"Calendar", "Badge", "Bubble", "DrawerSwipeHandle"}
    ex.text["avatar-basic"] = 'export function AvatarDemo() {\n  return <Avatar />\n}'
    ex.text["avatar-demo"] = 'export default function AvatarDemo() {\n  return <AvatarBadge className="bg-green-600" />\n}'
    ex.by_fn = {"BubbleDemo": ["bubble-demo"], "BadgeDemo": ["badge-demo"], "CalendarHijri": ["calendar-hijri"], "DrawerSwipeHandle": ["drawer-swipe-handle"], "AvatarDemo": ["avatar-basic", "avatar-demo"]}
    tree = {"i": 1, "t": "div", "a": [], "c": [{"i": 2, "t": "button", "a": [], "c": ["x"]}]}
    return [
        check("a preview whose example imports a Rhea part is not Nova", ex.style_of_code("Copyimport { Bubble } from \"@/components/ui/bubble\"\n\nexport function BubbleDemo() {View Code") == "rhea"),
        check("a Nova example is Nova", ex.style_of_code("export function BadgeDemo() {") == "nova"),
        check("an example with its own copy of a component is not Nova", ex.style_of_code("export function CalendarHijri() {") == "own"),
        check("an example whose exported name is also a part name is Nova", ex.style_of_code("export function DrawerSwipeHandle() {") == "nova"),
        check("an example the tool does not know counts as Nova", ex.style_of_code("export function Other() {") == "nova"),
        check("two examples with one function name: the code picks the right file", ex.name_of_code('Copyexport function AvatarDemo() {\n  return <AvatarBadge className="bg-green-600" />\n}View Code') == "avatar-demo" and ex.name_of_code("export function AvatarDemo() {\n  return <Avatar />\n}") == "avatar-basic"),
        check("a preview without code is found by its texts", ex.name_of_texts(["export function BubbleDemo", "@/styles/base-rhea/ui/bubble"]) == "bubble-demo"),
        check("one common text is not enough", ex.name_of_texts(["import {", "unrelated text"]) is None),
        check("a text in two examples is not enough", ex.name_of_texts(["export function"]) is None),
        check("the trigger of a popup is found in its preview", parity.contains(tree, 2) and not parity.contains(tree, 3)),
        check("each preview gets the style of its own example, in page order", parity.root_styles([{"kind": "preview"}, {"kind": "portal"}, {"kind": "preview"}], ["nova", "rhea"]) == ["nova", None, "rhea"]),
        check("a view page gives its style to every preview", parity.root_styles([{"kind": "preview"}, {"kind": "preview"}], ["rhea"], "nova") == ["nova", "nova"]),
    ]


def source_checks():
    parts = parity.Parts(PARTS)
    ex = object.__new__(parity.Examples)
    ex.text = {"badge-round": '<Badge className="rounded-full">A</Badge>'}
    ex.nova = {"badge-example": '<Badge className="px-1">B</Badge>', "example": '<div className="grid gap-4" />'}
    cap = {"roots": [
        {"kind": "preview", "box": {"w": 100}, "inh": {}, "tree": {"i": 1, "t": "span", "a": [["data-slot", "badge"], ["class", "inline-flex h-5 rounded-full"]], "c": ["A"]}},
        {"kind": "preview", "box": {"w": 100}, "inh": {}, "tree": {"i": 2, "t": "span", "a": [["data-slot", "badge"], ["class", "inline-flex h-5 rounded-4xl"]], "c": ["B"]}},
    ], "examples": ["badge-round", None]}
    conv = parity.Converter(parts, PARTS["components"], "badge")
    page = parity.page_html(conv, cap, ex.of)
    dcparts = parity.Parts({"components": ["dialog", "button"], "parts": [{"slot": "button", "selector": "[data-slot=\"button\"]", "from": "button/Button", "tokens": ["inline-flex", "rounded-lg", "border", "text-sm", "font-medium", "h-8", "px-2.5"], "mapped": True}, {"slot": "dialog-close", "selector": "[data-slot=\"dialog-close\"]", "from": "dialog/DialogClose", "tokens": [], "mapped": True}, {"selector": ":where([data-slot=\"dialog-content\"]) > [data-slot=\"dialog-close\"]", "element_slot": "dialog-close", "from": "dialog/DialogContent/DialogPrimitive.Close", "tokens": ["inline-flex", "rounded-lg", "border", "text-sm", "font-medium", "h-8", "px-2.5", "absolute"], "mapped": True}], "source_tokens": {}})
    otpparts = parity.Parts({"components": ["input-otp"], "parts": [{"selector": "[data-slot=\"input-otp\"]", "from": "input-otp/InputOTP/containerClassName", "tokens": ["flex", "items-center", "has-disabled:opacity-50"], "mapped": True}], "source_tokens": {}})
    odata = {"components": ["combobox", "input-group"], "parts": [{"slot": "input-group-button", "selector": "[data-slot=\"input-group-button\"]", "from": "combobox/ComboboxTrigger", "tokens": ["data-pressed:bg-transparent", "h-6"], "mapped": True}], "source_tokens": {"input-group": ["h-6"], "combobox": ["data-pressed:bg-transparent"]}}
    wrapper = parity.Converter(parts, PARTS["components"], "badge")
    wrapper.use(['<Example className="flex flex-col gap-4 rounded-xl inline-flex h-5"><Badge className="px-1">A</Badge><Card /></Example>'])
    wrapped = wrapper.node({"i": 10, "t": "div", "a": [["data-slot", "card"], ["class", "flex gap-4 rounded-xl"]], "c": [{"i": 11, "t": "span", "a": [["data-slot", "badge"], ["class", "inline-flex h-5 px-1"]], "c": ["A"]}]})
    adata = {"components": ["group"], "parts": [{"slot": "group", "selector": ':is([data-slot="group"], [data-slot="check-group"])', "from": "group/Group", "tokens": ["flex", "flex-col", "gap-5", "w-full", "data-[slot=check-group]:gap-3", "min-w-0"], "mapped": True}], "source_tokens": {"group": ["flex", "flex-col", "gap-5", "w-full", "min-w-0"]}}
    alias_out = parity.Converter(parity.Parts(adata), ["group"], "group").node({"i": 9, "t": "div", "a": [["data-slot", "check-group"], ["class", "flex flex-col gap-5 w-full min-w-0 data-[slot=check-group]:gap-3"]], "c": []})
    otp = parity.Converter(parts, PARTS["components"], "input-otp").node({"i": 3, "t": "div", "a": [["data-input-otp-container", "true"]], "c": [{"i": 4, "t": "input", "a": [["data-input-otp", "true"], ["data-slot", "input-otp"]], "c": []}]})
    return [
        check("a preview keeps only the classes of its own example file", 'data-pid="1" class="rounded-full"' in page),
        check("a preview without a known example keeps no definition class", 'data-pid="2">' in page),
        check("without a known example, classes of the part from another component file go too", parity.Converter(parity.Parts(odata), ["combobox", "input-group"], "combobox").keep(["data-pressed:bg-transparent", "my-x"], "input-group-button", {"input-group"}) == ["my-x"]),
        check("a wrapper className is no class set of a part (NB1)", 'data-pid="10">' in wrapped and 'data-pid="11" class="px-1"' in wrapped),
        check("a className from a const string counts like a literal (questionnaire itemClassName)", [sorted(x) for x in parity.jsx_elements('const itemClassName =\n  "data-active:animate-in motion-reduce:animate-none"\n\nfunction A() { return <QuestionnaireItem className={itemClassName} name="a" /> }')[0][2]] == [["data-active:animate-in", "motion-reduce:animate-none"]]),
        check("the render element of a part gives its className to that part", [sorted(x) for x in parity.jsx_elements('<Badge render={<button className="flex gap-1" />}>A</Badge>')[0][2]] == [["flex", "gap-1"]]),
        check("a part that map.tsv gives a slot takes the classNames of its function", "input-group-text" in parity.Parts({"components": ["input-group"], "parts": [{"selector": "[data-slot=\"input-group-text\"]", "from": "input-group/InputGroupText", "tokens": ["flex"], "mapped": True}], "source_tokens": {}}).func_slots["InputGroupText"]),
        check("a part with a map.tsv slot keeps its own markers (no composition)", parity.composed("cn-button cn-button-variant-ghost size-8 p-0", parity.Parts({"components": ["calendar", "button"], "parts": [{"slot": "button", "selector": "[data-slot=\"button\"]", "from": "button/Button", "tokens": ["h-8"], "mapped": True}, {"selector": "[data-slot=\"calendar-button-next\"]", "from": "calendar/Calendar/classNames.button_next", "tokens": ["size-8"], "markers": ["cn-button"], "mapped": True}], "source_tokens": {}}), "calendar-button-next", ["calendar", "button"]) is None),
        check("classNames-like props of a part count for all parts of its component (calendar modifiersClassNames)", [sorted(x) for x in parity.jsx_elements('<Calendar className="rounded-lg" modifiersClassNames={{ booked: "[&>button]:line-through opacity-100" }} />')[0][3]] == [["[&>button]:line-through", "opacity-100"]]),
        check("an example run in the middle of the classes stays (Base UI render merge)", parity.example_suffix(["inline-flex", "w-64", "font-normal", "[&_svg]:size-4"], [frozenset({"w-64", "font-normal"})]) == ["w-64", "font-normal"]),
        check("a slot whose own classes match better is no composition", parity.composed("flex gap-4 rounded-xl a b c", parity.Parts(PARTS), "card", PARTS["components"]) is None),
        check("a layout element of the page matches a slotless part of the page component only with all its classes (T19)", "data-slot" not in parity.infer_attrs("flex items-center justify-between", otpparts, None, set(), "input-otp")[0] and parity.infer_attrs("flex items-center has-disabled:opacity-50", otpparts, None, set(), "input-otp")[0].get("data-slot") == "input-otp"),
        check("classes of a contextual instance of a part do not block a composition elsewhere (dialog close as a button)", parity.composed("inline-flex rounded-lg border text-sm font-medium h-8 px-2.5", dcparts, "dialog-close", ["dialog", "button"], "questionnaire-actions", {"questionnaire"}) == "button"),
        check("a part inside the context of its contextual part is no composition (dialog X close)", parity.composed("inline-flex rounded-lg border text-sm font-medium h-8 px-2.5 absolute", dcparts, "dialog-close", ["dialog", "button"], "dialog-content", {"dialog-content"}) is None),
        check("a page layout element does not match a tiny slotless part of the page component (calendar weekdays: flex)", "data-slot" not in parity.infer_attrs("preview relative flex w-full justify-center p-10", parity.Parts({"components": ["calendar"], "parts": [{"selector": "[data-slot=\"calendar-weekdays\"]", "from": "calendar/Calendar/classNames.weekdays", "tokens": ["flex"], "mapped": True}], "source_tokens": {}}), None, set(), "calendar")[0]),
        check("each part takes only the classNames of its own JSX elements", sorted(map(sorted, wrapper.by_slot["badge"])) == [["px-1"]] and wrapper.by_slot["card"] == []),
        check("previews take their example names in page order", parity.root_names([{"kind": "preview"}, {"kind": "portal"}, {"kind": "preview"}], ["a", "b"]) == ["a", None, "b"]),
        check("a Nova example page uses its example and the example wrapper", ex.of("badge-example") == [ex.nova["badge-example"], ex.nova["example"]] and ex.of("unknown") == []),
        check("a slot that the generator aliases to a part is no composition", alias_out.startswith('<div data-slot="check-group"')),
        check("the input-otp container gets the input-otp slot, not its input", 'data-input-otp-container="true" data-slot="input-otp"' in otp and '<input data-input-otp="true" data-pid="4">' in otp),
    ]


def marker_checks():
    data = {"components": ["button", "input-group"], "parts": [
        {"slot": "button", "selector": "[data-slot=\"button\"]", "from": "button/Button", "tokens": ["inline-flex", "bg-primary", "hover:bg-muted", "h-8", "h-6"], "variants": [
            {"attr": "data-variant", "value": "default", "default": True, "tokens": ["bg-primary"]},
            {"attr": "data-variant", "value": "ghost", "tokens": ["hover:bg-muted"]},
            {"attr": "data-size", "value": "default", "default": True, "tokens": ["h-8"]},
            {"attr": "data-size", "value": "xs", "tokens": ["h-6"]}], "mapped": True},
        {"slot": "button", "selector": "[data-slot=\"button\"]:where([data-input-group-button])", "marker": "data-input-group-button", "from": "input-group/InputGroupButton", "tokens": ["text-sm", "shadow-none"], "own": ["text-sm", "shadow-none"], "set": {"data-variant": "ghost", "data-size": "xs"}, "mapped": True}],
        "source_tokens": {"button": ["inline-flex", "bg-primary", "hover:bg-muted", "h-8", "h-6"], "input-group": ["text-sm", "shadow-none"]}}
    data["parts"][1]["own"] = ["text-sm", "shadow-none", "pl-1!", "ps-1!"]
    data["logical"] = {"pl-1!": "ps-1!"}
    cvadata = {"components": ["navigation-menu"], "parts": [
        {"slot": "navigation-menu-link", "selector": "[data-slot=\"navigation-menu-link\"]", "from": "navigation-menu/NavigationMenuLink", "tokens": ["gap-2", "p-2"], "mapped": True},
        {"selector": "[data-slot=\"navigation-menu-link\"][data-variant=\"trigger\"]", "element_slot": "navigation-menu-link", "from": "navigation-menu/cva.navigationMenuTriggerStyle", "tokens": ["inline-flex", "h-9", "w-max", "rounded-lg"], "own": ["inline-flex", "h-9", "w-max", "rounded-lg"], "set": {"data-variant": "trigger"}, "mapped": True}],
        "source_tokens": {"navigation-menu": ["gap-2", "p-2", "inline-flex", "h-9", "w-max", "rounded-lg"]}}
    parts = parity.Parts(data)
    physical, _ = parity.infer_attrs("inline-flex bg-primary text-sm pl-1!", parts, "button", set())
    ghost, _ = parity.infer_attrs("inline-flex text-sm shadow-none", parts, "button", set())
    primary, _ = parity.infer_attrs("inline-flex bg-primary h-6 text-sm shadow-none", parts, "button", set())
    return [
        check("an input-group button without variant classes gets the part default ghost", ghost.get("data-variant") == "ghost" and ghost.get("data-size") == "xs" and ghost.get("data-input-group-button") == ""),
        check("an input-group button with the Button default variant keeps it", primary.get("data-variant") == "default" and primary.get("data-size") == "xs"),
        check("a physical class and its logical form count as one token", "data-input-group-button" in physical),
        check("a cva style used on another part sets its attribute (navigation link as trigger)", parity.infer_attrs("gap-2 p-2 inline-flex h-9 w-max rounded-lg", parity.Parts(cvadata), "navigation-menu-link", set())[0].get("data-variant") == "trigger"),
    ]


def nova_page_checks():
    parts = parity.Parts(PARTS)
    ex = object.__new__(parity.Examples)
    ex.nova = {"bubble-example": "", "badge-example": "", "example": ""}
    rhea = [{"cap": {"styles": ["nova", "rhea"]}}]
    nova = [{"cap": {"styles": ["nova", "nova"]}}]
    conv = parity.Converter(parts, PARTS["components"], "badge", [], False)
    tree = {"i": 1, "t": "div", "a": [["data-slot", "example"], ["class", "flex flex-col gap-4 cn-example"]], "c": [
        {"i": 2, "t": "span", "a": [["data-slot", "badge"], ["class", "cn-badge inline-flex h-5 cn-badge-variant-outline"]], "c": ["A"]},
        {"i": 3, "t": "span", "a": [["data-slot", "badge"], ["class", "cn-badge inline-flex h-5 cn-badge-variant-default"]], "c": ["B"]}]}
    out = conv.node(tree)
    meta, ids, _, _ = parity.scenario_info({"roots": [{"kind": "preview", "tree": tree}]}, PARTS["components"])
    return [
        check("a page with a preview in another style is measured on its Nova example page", parity.nova_page("bubble", rhea, ex) == "/preview/base/bubble-example?style=nova"),
        check("a page with only Nova previews needs no Nova example page", parity.nova_page("badge", nova, ex) is None),
        check("a component without a Nova example page has none", parity.nova_page("card", rhea, ex) is None),
        check("a Nova example page scopes each example", "preview/base/" in parity.NOVA_PAGE),
        check("a cva marker class sets its variant", 'data-variant="outline" data-pid="2"' in out),
        check("a default cva marker sets no variant", 'data-slot="badge" data-pid="3">' in out),
        check("a slot that is no kit part keeps its layout classes", 'data-pid="1" class="flex flex-col gap-4"' in out),
        check("a slot that is no kit part is not measured, its parts are", 1 not in ids and 2 in ids and 3 in ids),
        check("a part rendered as another component (its root marker) gets that slot", parity.composed("cn-card cn-badge flex", parts, "badge", PARTS["components"]) == "card"),
        check("a marker in the part's own definition is no composition", parity.composed("cn-badge cn-card flex", parts, "card", PARTS["components"]) is None),
    ]


def report_checks():
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([sys.executable, "-I", str(pathlib.Path(__file__).with_name("report.py")), d, "--strict"], capture_output=True)
    return [check("report.py fails on a directory without component results", r.returncode == 1)]


def main():
    results = tolerance_checks() + converter_checks() + style_checks() + nova_page_checks() + marker_checks() + source_checks() + report_checks()
    failed = results.count(False)
    print(f"{len(results) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
