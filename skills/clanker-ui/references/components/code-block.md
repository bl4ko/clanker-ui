# Code Block (`code-block`)

Group `chat`. Needs `core`. CSS and JS.

| Part | Write | State |
| --- | --- | --- |
| `code-block` (root) | `data-size` `sm`; `data-variant` `default`, `destructive` |  |
| `code-block-content` | `data-language` string; `data-numbered` `false`, `true`; `data-start-line` number; `data-wrap` `false`, `true` |  |
| `code-block-download-button` | `data-filename` string |  |
| `code-block-line` | `data-variant` `added`, `highlighted`, `removed` |  |

Other parts: `code-block-actions`, `code-block-code`, `code-block-copy-button`, `code-block-footer`, `code-block-header`, `code-block-title`, `code-block-wrap-button`.

Kit adds: `code-block-line-content`.

Other options named in the docs: `data-timeout` any.

Events: `code-block:copy` `{ value }`; `code-block:wrap` `{ value }`; `code-block:download` `{ value, filename }`.

Exports (readable set: `clanker-ui-code.js`; `.min` set: `clanker-ui-code.min.js`):

- `codeBlockHighlight(code, language) → Node[][] | null`: In `clanker-ui-code.js`: one list of nodes per line for `code-block-line` rows, or `null` for an unknown language. See [Code Block](https://github.com/bl4ko/clanker-ui#code-block).

## Full text

### Code Block

```html
<div data-slot="code-block" data-size="sm" data-variant="destructive">
  <div data-slot="code-block-header">
    <div data-slot="code-block-title"><svg data-lucide="file-text"></svg>app.ts</div>
    <div data-slot="code-block-actions">
      <button data-slot="code-block-wrap-button" aria-label="Wrap lines"><svg data-lucide="text-wrap"></svg></button>
      <button data-slot="code-block-download-button" data-filename="app.ts"></button>
      <button data-slot="code-block-copy-button"></button>
    </div>
  </div>
  <pre data-slot="code-block-content" data-language="ts" data-numbered="true" data-start-line="14" data-wrap="true"><code data-slot="code-block-code">code</code></pre>
</div>
```

`data-numbered` splits text into `code-block-line` rows; write `<span data-slot="code-block-line" data-variant="added|removed|highlighted">` rows for diffs and highlighted lines. Copy uses the Clipboard API: `data-value` or the block text without line numbers; it shows a check for 2 s (`data-timeout`) and announces "Copied" (`strings.copied`). A copy button that leaves the page goes back to its copy state. The wrap button toggles `data-wrap` and `aria-pressed` (pressed text is `--foreground`). The download button saves `data-value` or the block text as `data-filename` (default: the last part of the title, else `code.txt`).

Syntax colors: load `clanker-ui-code.js` and set `data-language` on `code-block-content`. Languages: `ts`, `tsx`, `js`, `jsx`, `json`, `html`, `css`, `bash`, `yaml`, `go`, `python`, `diff`, `markdown`, `sql`, `ansi` (terminal colors; the escape codes go away), and the usual aliases (`typescript`, `javascript`, `sh`, `shell`, `zsh`, `yml`, `py`, `md`, `xml`, `svg`); other languages and text over 200 000 characters stay plain, as without the module. It colors plain text and plain rows when a block starts; rows with elements stay as they are. For text that changes, build the rows again:

```js
import { h } from "./clanker-ui.js"
import { codeBlockHighlight } from "./clanker-ui-code.js"

code.replaceChildren(...codeBlockHighlight(text, "ts").map(line =>
  h("span", { "data-slot": "code-block-line" }, h("span", { "data-slot": "code-block-line-content" }, line.length ? line : "\n"))))
```

Tokens are `<span data-token="…">` with `comment`, `keyword`, `string`, `constant`, `function`, `variable`, `tag`, `inserted`, `deleted`, or `bold`, colored by `--code-<token>`. The defaults are the GitHub Light and Dark colors of the shadcn highlighter, darkened or lightened to 4.5:1 on the block, its highlighted lines, and removed lines; each editor scheme sets its own (`clanker-ui-a11y.css` has the 4.5:1 changes).
