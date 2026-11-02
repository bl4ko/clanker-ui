package main

import "strings"

var rtlMappings = [][2]string{
	{"-ml-", "-ms-"}, {"-mr-", "-me-"}, {"ml-", "ms-"}, {"mr-", "me-"}, {"pl-", "ps-"}, {"pr-", "pe-"},
	{"-left-", "-start-"}, {"-right-", "-end-"}, {"left-", "start-"}, {"right-", "end-"},
	{"inset-l-", "inset-inline-start-"}, {"inset-r-", "inset-inline-end-"},
	{"rounded-tl-", "rounded-ss-"}, {"rounded-tr-", "rounded-se-"}, {"rounded-bl-", "rounded-es-"}, {"rounded-br-", "rounded-ee-"},
	{"rounded-l-", "rounded-s-"}, {"rounded-r-", "rounded-e-"},
	{"border-l-", "border-s-"}, {"border-r-", "border-e-"}, {"border-l", "border-s"}, {"border-r", "border-e"},
	{"text-left", "text-start"}, {"text-right", "text-end"},
	{"scroll-ml-", "scroll-ms-"}, {"scroll-mr-", "scroll-me-"}, {"scroll-pl-", "scroll-ps-"}, {"scroll-pr-", "scroll-pe-"},
	{"float-left", "float-start"}, {"float-right", "float-end"}, {"clear-left", "clear-start"}, {"clear-right", "clear-end"},
}

var rtlTranslate = [][2]string{{"-translate-x-", "translate-x-"}, {"translate-x-", "-translate-x-"}}

var rtlReverse = [][2]string{{"space-x-", "space-x-reverse"}, {"divide-x-", "divide-x-reverse"}}

var rtlSwap = [][2]string{{"cursor-w-resize", "cursor-e-resize"}, {"cursor-e-resize", "cursor-w-resize"}}

var rtlSideSlide = [][3]string{
	{"data-[side=inline-start]", "slide-in-from-right", "slide-in-from-end"},
	{"data-[side=inline-start]", "slide-out-to-right", "slide-out-to-end"},
	{"data-[side=inline-end]", "slide-in-from-left", "slide-in-from-start"},
	{"data-[side=inline-end]", "slide-out-to-left", "slide-out-to-start"},
}

func splitClass(c string) (variant, name, alpha string) {
	if !strings.ContainsAny(c, "/:") {
		return "", c, ""
	}
	last, depth := -1, 0
	for i := len(c) - 1; i >= 0; i-- {
		switch c[i] {
		case ']':
			depth++
		case '[':
			depth--
		case ':':
			if depth == 0 && last < 0 {
				last = i
			}
		}
		if last >= 0 {
			break
		}
	}
	rest := c
	if last >= 0 {
		variant, rest = c[:last], c[last+1:]
	}
	if s := strings.LastIndex(rest, "/"); s >= 0 {
		return variant, rest[:s], rest[s+1:]
	}
	return variant, rest, ""
}

func join(variant, name, alpha string) string {
	if alpha != "" {
		name += "/" + alpha
	}
	if variant != "" {
		return variant + ":" + name
	}
	return name
}

func rtlClasses(c string) []string {
	if strings.HasPrefix(c, "rtl:") || strings.HasPrefix(c, "ltr:") {
		return []string{c}
	}
	variant, value, alpha := splitClass(c)
	if value == "" {
		return []string{c}
	}
	rtlVariant := "rtl"
	if variant != "" {
		rtlVariant += ":" + variant
	}
	for _, m := range rtlTranslate {
		if strings.HasPrefix(value, m[0]) {
			return []string{c, join(rtlVariant, strings.Replace(value, m[0], m[1], 1), alpha)}
		}
	}
	for _, m := range rtlReverse {
		if strings.HasPrefix(value, m[0]) {
			return []string{c, rtlVariant + ":" + m[1]}
		}
	}
	for _, m := range rtlSwap {
		if value == m[0] {
			return []string{c, rtlVariant + ":" + m[1]}
		}
	}
	for _, m := range rtlSideSlide {
		if strings.Contains(variant, m[0]) && strings.HasPrefix(value, m[1]) {
			return []string{join(variant, strings.Replace(value, m[1], m[2], 1), alpha)}
		}
	}
	physicalSide := strings.Contains(variant, "data-[side=left]") || strings.Contains(variant, "data-[side=right]") || strings.Contains(variant, "data-[swipe-direction=left]") || strings.Contains(variant, "data-[swipe-direction=right]")
	for _, m := range rtlMappings {
		if physicalSide && (strings.HasPrefix(m[0], "-left-") || strings.HasPrefix(m[0], "-right-") || strings.HasPrefix(m[0], "left-") || strings.HasPrefix(m[0], "right-")) {
			continue
		}
		if !strings.HasPrefix(value, m[0]) || !strings.HasSuffix(m[0], "-") && value != m[0] {
			continue
		}
		return []string{join(variant, strings.Replace(value, m[0], m[1], 1), alpha)}
	}
	return []string{c}
}
