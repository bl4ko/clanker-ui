import { mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { basename, join } from "node:path"
import { createStyleMap, transformStyle } from "shadcn/utils"

const [, , css, out, ...files] = process.argv
const styleMap = createStyleMap(readFileSync(css, "utf8"))
mkdirSync(out, { recursive: true })
for (const f of files) {
  writeFileSync(join(out, basename(f)), await transformStyle(readFileSync(f, "utf8"), { styleMap }))
}
