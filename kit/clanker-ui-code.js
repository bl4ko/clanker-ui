/*! clanker-ui | MIT | includes shadcn/ui (MIT, shadcn); see THIRD_PARTY_NOTICES */
import { h, define } from "./clanker-ui.js"

const MAX = 200000
const TOKEN_NAMES = { c: "comment", k: "keyword", s: "string", n: "constant", f: "function", v: "variable", t: "tag", i: "inserted", d: "deleted", h: "constant bold", b: "bold" }
const NUMBER = /(?<![\w$.])(?:0[xXbBoO][\da-fA-F_]+n?|(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][-+]?\d+)?n?)(?![\w$])/
const SCRIPT = [
  ["c", /\/\/.*|\/\*[\s\S]*?(?:\*\/|$)/],
  ["s", /"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?|`(?:\\[\s\S]|[^\\`])*`?/],
  ["t", /(?<=(?:^|[\n(=>{},?:&|]|\breturn)\s*<|<\/)[a-z][\w.:-]*/],
  ["n", /(?<=(?:^|[\n(=>{},?:&|]|\breturn)\s*<|<\/)[A-Z][\w.]*/],
  ["f", /[\w-]+(?==[{"'])/],
  ["k", /(?<![\w$.])(?:import|export|from|as|default|async|await|function|return|const|let|var|if|else|for|while|do|switch|case|break|continue|new|class|extends|implements|interface|type|enum|typeof|instanceof|in|of|try|catch|finally|throw|yield|delete|void|static|public|private|protected|readonly|declare|namespace|keyof|satisfies|abstract|override)(?![\w$]|\s*\??:)/],
  ["n", /(?<![\w$.])(?:true|false|null|undefined|NaN|Infinity|this|super)(?![\w$])|(?<=\bimport\s+)\*/],
  ["n", NUMBER],
  ["n", /(?<=\bconst\s+)[\w$]+|(?<=\bconst\s*[[{][^=;\]}]{0,200})[A-Za-z_$][\w$]*/],
  ["n", /(?<=:\s*|<)(?:string|number|boolean|any|unknown|never|void|object|bigint|symbol)(?![\w$])/],
  ["f", /(?<=:\s*)[A-Z][\w$]*|(?<=\b(?:new|extends|implements|interface|type|class|enum)\s+)[\w$]+|(?<=[\w$]<)[A-Z][\w$]*/],
  ["v", /(?<=\([^()]{0,120})[A-Za-z_$][\w$]*(?=[^()]{0,120}\)\s*=>)|[A-Za-z_$][\w$]*(?=\s*=>)|(?<=\bfunction\b[^(]{0,80}\([^()]{0,200})[A-Za-z_$][\w$]*(?=\s*[?:=,)}])/],
  ["f", /[A-Za-z_$][\w$]*(?=\s*(?:<[\w$\s,.[\]|&]{0,80}>\s*)?\()/],
  ["k", /=>|\.\.\.|[=!]==?|&&|\|\||\?\?|[-+*%]=?|(?<!<)\/(?!>)=?|=|!|\?(?![.?])|:(?=\s*(?:[A-Z][\w$]*|string|number|boolean|any|unknown|void|never)(?![\w$])(?!\s*[(.]))/],
]
const GRAMMARS = {
  js: SCRIPT,
  json: [
    ["c", /\/\/.*|\/\*[\s\S]*?(?:\*\/|$)/],
    ["n", /"(?:\\.|[^"\\\n])*"(?=\s*:)/],
    ["s", /"(?:\\.|[^"\\\n])*"?/],
    ["n", /-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|\b(?:true|false|null)\b/],
  ],
  html: [
    ["c", /<!--[\s\S]*?(?:-->|$)/],
    ["k", /<![A-Za-z][^>]*>?/],
    ["t", /(?<=<\/?)[A-Za-z][\w:.-]*/],
    ["f", /(?<=<[A-Za-z][^<>]{0,400}\s)[^\s"'<>/=]+(?=\s*=|[\s/>])/],
    ["s", /(?<==\s*)(?:"[^"]*"?|'[^']*'?)/],
    ["n", /&(?:#\d+|#x[\da-fA-F]+|\w+);/],
  ],
  css: [
    ["c", /\/\*[\s\S]*?(?:\*\/|$)/],
    ["s", /"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?/],
    ["k", /@[\w-]+|!important/],
    ["v", /--[\w-]+/],
    ["n", /[\w-]+(?=\s*:[^{};()]{0,200}[;})])/],
    ["f", /[.#][\w-]+(?=[^{};]{0,200}\{)|::?[\w-]+(?=[^{};]{0,200}\{)|\[[^\]\n]{0,200}\](?=[^{};]{0,200}\{)/],
    ["t", /(?<![\w-])[a-z][\w-]*(?=[^{};]{0,200}\{)/],
    ["n", /#[\da-fA-F]{3,8}(?![\w-])|-?(?:\d+\.?\d*|\.\d+)/],
    ["k", /(?<=\d)(?:%|[a-zA-Z]+)/],
    ["f", /[\w-]+(?=\()/],
    ["n", /(?<=:[^;{}]{0,200})[a-z][\w-]*/],
  ],
  sh: [
    ["c", /(?<![^\s;])#.*/],
    ["s", /"(?:\\[\s\S]|[^"\\])*"?|'[^']*'?/],
    ["v", /\$\{[^}\n]*\}?|\$(?:\w+|[@#?$!*-])/],
    ["k", /(?<![\w-])(?:if|then|else|elif|fi|for|in|do|done|while|until|case|esac|function|return|export|local|readonly|declare|unset|source|alias)(?![\w-])/],
    ["k", /(?<=(?:^|[\s;])[A-Za-z_]\w*)=|&&|\|\|?|>>?|<|;|&/],
    ["s", /(?<=(?:^|[\s;])[A-Za-z_]\w*=)[^\s;|&]+/],
    ["f", /(?<=(?:^|[\n|;&(]|\b(?:then|do|else))[ \t]*(?:\$[ \t]+)?)(?![\w./@+-]*=)[\w./@+-]+/],
    ["n", /(?<=\s)--?[\w-]+/],
    ["s", /(?<=(?:^|[\n|;&(])[ \t]*(?:\$[ \t]+)?[\w./@+-]+(?:[ \t]+[^\s|;&#]{1,200}){0,40}[ \t]+)[^\s|;&#'"$]+/],
  ],
  yaml: [
    ["c", /(?<![^\s])#.*/],
    ["s", /"(?:\\.|[^"\\\n])*"?|'(?:''|[^'\n])*'?/],
    ["t", /[\w.$/-]+(?=\s*:(?:[ \t]|\n|$))/],
    ["k", /^---|(?<=\n)(?:---|\.\.\.)|[|>][-+]?(?=[ \t]*(?:\n|$))|![\w!]*/],
    ["v", /[&*][\w-]+/],
    ["n", /(?<![\w.-])(?:true|false|null|yes|no|on|off|~|-?\d+(?:\.\d+)?)(?![\w.-])/],
    ["s", /(?<=:[ \t]+|(?:^|\n)[ \t]*-[ \t]+)[^\s#'"[{&*!|>][^\n#]*?(?=[ \t]+#|[ \t]*(?:\n|$))/],
  ],
  python: [
    ["c", /#.*/],
    ["s", /[rRbBuU]{0,2}(?:"""[\s\S]*?(?:"""|$)|'''[\s\S]*?(?:'''|$))/],
    ["k", /(?:[fF][rR]?|[rR][fF])(?=["'])/],
    ["n", /(?<=(?:^|\W)(?:[fF][rR]?|[rR][fF])(?:"[^"\n]{0,200}|'[^'\n]{0,200}))[{}]/],
    ["s", /(?<=(?:^|\W)(?:[fF][rR]?|[rR][fF]))(?:"(?:\\.|\{\{|[^"\\\n{])*"?|'(?:\\.|\{\{|[^'\\\n{])*'?)|(?<=(?:^|\W)(?:[fF][rR]?|[rR][fF])"[^"\n]{0,200}\})(?:[^"{\n]+"?|")|(?<=(?:^|\W)(?:[fF][rR]?|[rR][fF])'[^'\n]{0,200}\})(?:[^'{\n]+'?|')/],
    ["s", /[rRbBuU]{0,2}(?:"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?)/],
    ["k", /\b(?:and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b/],
    ["n", /\b(?:True|False|None|self|cls|str|int|float|bool|bytes|list|dict|set|tuple|object|type)\b/],
    ["n", NUMBER],
    ["f", /(?<=\b(?:def|class)\s+)\w+|@[\w.]+|\w+(?=\s*\()/],
    ["", /->/],
    ["k", /\*\*|\/\/|[-+*/%=<>!]=?/],
  ],
  go: [
    ["c", /\/\/.*|\/\*[\s\S]*?(?:\*\/|$)/],
    ["s", /"(?:\\.|[^"\\\n])*"?|`[^`]*`?|'(?:\\.|[^'\\\n])*'?/],
    ["k", /\b(?:break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var|bool|byte|complex64|complex128|error|float32|float64|int|int8|int16|int32|int64|rune|string|uint|uint8|uint16|uint32|uint64|uintptr|any)\b/],
    ["n", /\b(?:true|false|nil|iota)\b/],
    ["n", NUMBER],
    ["f", /(?<=\b(?:func\s+(?:\([^)]{0,100}\)\s*)?|type\s+))\w+|\w+(?=\s*(?:\[[^\]\n]*\])?\()/],
    ["k", /:=|<-|&&|\|\||[=!<>]=?|[-+*/%&|^]=?/],
  ],
  diff: [
    ["n", /(?<=^|\n)(?:diff|index|---|\+\+\+) .*/],
    ["f", /(?<=^|\n)@@.*/],
    ["i", /(?<=^|\n)[+>].*/],
    ["d", /(?<=^|\n)[-<].*/],
  ],
  markdown: [
    ["h", /(?<=^|\n)#{1,6}[ \t].*/],
    ["n", /```[\s\S]*?(?:\n```|$)|`[^`\n]+`/],
    ["b", /\*\*[^*\n]+\*\*|__[^_\n]+__/],
    ["s", /\[[^\]\n]*\](?=\()|(?<=\])\([^)\n]*\)/],
    ["v", /(?<=^|\n)[ \t]*(?:[-*+]|\d+\.)(?=[ \t])/],
    ["t", /(?<=^|\n)>.*/],
  ],
  sql: Object.assign([
    ["c", /--.*|\/\*[\s\S]*?(?:\*\/|$)/],
    ["s", /'(?:''|[^'])*'?/],
    ["k", /\b(?:select|from|where|and|or|not|null|is|in|as|on|join|left|right|inner|outer|full|cross|group|by|order|having|limit|offset|insert|into|values|update|set|delete|create|table|view|index|drop|alter|add|column|primary|key|foreign|references|default|unique|distinct|case|when|then|else|end|union|all|exists|like|between|asc|desc|returning|with|begin|commit|rollback|if|int|integer|bigint|text|varchar|boolean|timestamp|timestamptz|date|serial|uuid|jsonb?)\b/],
    ["n", /\b(?:true|false)\b|\b\d+(?:\.\d+)?\b/],
    ["f", /\w+(?=\s*\()/],
    ["k", /[=<>!]=?|[-+*/%]/],
  ], { flags: "i" }),
}
const ALIASES = Object.fromEntries("javascript=js mjs=js cjs=js jsx=js ts=js typescript=js tsx=js jsonc=json xml=html svg=html bash=sh shell=sh shellscript=sh zsh=sh console=sh yml=yaml py=python golang=go patch=diff md=markdown".split(" ").map(pair => pair.split("=")))
const compiled = new Map()
const ANSI_COLORS = { 1: "k", 2: "i", 3: "v", 4: "n", 5: "f", 6: "s", 7: "c" }

function ansi(text) {
  const out = []
  let color = "", bold = false, at = 0
  const push = part => part && out.push([[color && TOKEN_NAMES[color], bold && "bold"].filter(Boolean).join(" "), part])
  for (const m of text.matchAll(/\x1b\[([\d;]*)([@-~])|\n/g)) {
    push(text.slice(at, m.index))
    at = m.index + m[0].length
    if (m[0] === "\n") {
      color = ""
      bold = false
      out.push(["", "\n"])
    }
    if (m[2] !== "m") continue
    const codes = m[1] ? m[1].split(";").map(Number) : [0]
    for (let i = 0; i < codes.length; i++) {
      const c = codes[i]
      if (c === 0) [color, bold] = ["", false]
      else if (c === 1) bold = true
      else if (c === 22) bold = false
      else if (c === 39) color = ""
      else if (c === 38 || c === 48) i += codes[i + 1] === 5 ? 2 : 4
      else if (c % 60 >= 30 && c % 60 <= 37) color = ANSI_COLORS[c % 10] ?? ""
    }
  }
  push(text.slice(at))
  return out
}

function tokens(text, language) {
  const lang = String(language).toLowerCase()
  if (lang === "ansi") return ansi(text)
  const name = Object.hasOwn(ALIASES, lang) ? ALIASES[lang] : lang
  const rules = Object.hasOwn(GRAMMARS, name) ? GRAMMARS[name] : null
  if (!rules) return null
  let re = compiled.get(name)
  if (!re) compiled.set(name, re = new RegExp(rules.map(r => `(${r[1].source})`).join("|") + "|[\\w$]+|\\s+|[\\s\\S]", "gy" + (rules.flags ?? "")))
  const out = []
  re.lastIndex = 0
  for (let m; re.lastIndex < text.length && (m = re.exec(text));) {
    const part = m[0] || text[re.lastIndex++]
    const index = m[0] ? m.findIndex((group, i) => i && group !== undefined) : -1
    const type = index > 0 ? TOKEN_NAMES[rules[index - 1][0]] ?? "" : ""
    const last = out.at(-1)
    if (last?.[0] === type) last[1] += part
    else out.push([type, part])
  }
  return out
}

function lines(text, language) {
  const list = text.length > MAX ? null : tokens(text, language)
  if (!list) return null
  const out = [[]]
  for (const [type, value] of list) {
    value.split("\n").forEach((part, i) => {
      if (i) out.push([])
      if (part) out.at(-1).push(type ? h("span", { "data-token": type }, part) : part)
    })
  }
  return out
}

export function codeBlockHighlight(code, language) {
  return lines(String(code ?? ""), String(language ?? ""))
}

function paint(code) {
  const language = code.closest('[data-slot="code-block-content"]')?.getAttribute("data-language")
  if (!language) return
  const rows = [...code.querySelectorAll(':scope > [data-slot="code-block-line"]')]
  const targets = rows.length ? rows.map(row => row.querySelector(':scope > [data-slot="code-block-line-content"]') ?? row) : [code]
  if (targets.some(el => el.firstElementChild)) return
  const result = lines(rows.length ? targets.map(el => el.textContent === "\n" ? "" : el.textContent).join("\n") : code.textContent, language)
  if (!result) return
  if (rows.length) targets.forEach((el, i) => result[i]?.length && el.replaceChildren(...result[i]))
  else code.replaceChildren(...result.flatMap((line, i) => i ? ["\n", ...line] : line))
}

define("code-block-code", { init: paint })
