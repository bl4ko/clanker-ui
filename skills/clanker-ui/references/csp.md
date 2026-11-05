# CSP and Trusted Types

clanker-ui runs under this policy and needs nothing more. Send it on every HTML response:

```text
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; require-trusted-types-for 'script'
```

The kit needs no `data:` URL; `img-src data:` is for app images. Add the hosts that your app needs (for example an API in `connect-src`). Do not add `'unsafe-inline'`, `'unsafe-eval'`, or a nonce for the kit.

## Static hosts (no headers)

When the host cannot send headers (for example GitHub Pages), put the policy in a meta tag right after `<meta charset>` and before every `<link>` and `<script>` (the head of `SKILL.md` step 3 and of every block). A meta policy does not apply to elements before it. Browsers ignore `frame-ancestors` in a meta tag and log a warning, so the meta policy leaves it out:

```html
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; require-trusted-types-for 'script'">
<meta name="referrer" content="no-referrer">
```

## Server examples

- Caddy: `header Content-Security-Policy "<policy>"` in the site block.
- nginx: `add_header Content-Security-Policy "<policy>" always;`
- Local test server without headers: `python3 -m http.server 8300 --bind 127.0.0.1 --directory static`. It cannot send the CSP header, so every page needs the meta tag above.
- Local test server with the header (Go standard library, `go run server.go static 127.0.0.1:8300`):

```go
package main

import (
	"net/http"
	"os"
)

const policy = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; require-trusted-types-for 'script'"

func main() {
	files := http.FileServer(http.Dir(os.Args[1]))
	http.ListenAndServe(os.Args[2], http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Security-Policy", policy)
		files.ServeHTTP(w, r)
	}))
}
```

## Code rules

The policy blocks inline code and string-to-code sinks. App code and markup must follow these rules:

- No inline `<script>` or `<style>` element, no `style=""` attribute, no `on*=""` handler attribute, no `javascript:` URL. Setting `element.style.x` from JavaScript is allowed.
- All scripts are external files from the same origin, loaded with `<script type="module" src>` (the theme file is a classic script).
- With `require-trusted-types-for 'script'`, these throw a `TypeError`: `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `DOMParser` with strings from code, `setHTMLUnsafe`, `createContextualFragment`, `srcdoc`, and script `src` from strings. `eval`, `new Function`, and string timers fail because `script-src` has no `'unsafe-eval'`.
- Build DOM with the kit helpers: `h(tag, attrs, ...children)`, `svg(tag, attrs, ...children)`, and `icon(name, attrs)`. Strings become text nodes; `on*` props must be functions; `style` must be an object.
- Do not add a Trusted Types policy for the kit. It needs none.

## Check

Open the page in a browser with the developer console. The console must show 0 errors, 0 `Content Security Policy` violations, and 0 `TrustedHTML` or `TrustedScript` errors. In an automated check, collect `console` messages of type `error` and `pageerror` events; both lists must be empty.
