# Setup details

## Other ways to get the files

- Single files: each kit file is also a release asset, for example `https://github.com/bl4ko/clanker-ui/releases/download/v<version>/clanker-ui.min.css`.
- A local checkout of the repository: copy the files from its root and from `dist/`.

Check each downloaded file against `SHA256SUMS` (also a release asset): `grep ' clanker-ui-<version>.zip$' SHA256SUMS | shasum -a 256 -c` (Linux: `sha256sum -c`). Optional: `gh attestation verify <file> -R bl4ko/clanker-ui`.

The modules import each other by relative path, so all kit files go in one directory.

## Groups of existing HTML

This command lists the groups, with their "Needs", of the `data-slot` parts in the HTML files of the current folder (use the path of `clanker-ui.json` in this directory):

```sh
grep -rhoE 'data-slot="[a-z0-9-]+"' --include='*.html' . | cut -d'"' -f2 | sort -u |
  jq -Rn --slurpfile c references/clanker-ui.json '[inputs] as $s | [$c[0].components[] | select(any(.parts[]; .slot as $p | $s | index($p))) | .group, .needs[]] | unique'
```

## File sets

- One-file set: `clanker-ui.min.css`, module `clanker-ui.min.js`, and `clanker-ui-core.min.js` next to it (`clanker-ui.min.js` imports it; copy both). `clanker-ui.min.css` has the chart CSS too; charts add only `clanker-ui-chart.min.js`.
- Readable set, for development: `clanker-ui.css` and module `clanker-ui.js` (charts: `clanker-ui-chart.js`). Core and group files exist only in the `.min` set (`dist/`).
- With group modules, do not add a separate `<script>` for the core; the `modulepreload` link only saves a round trip. Mixed sets throw "already defined".
- After the kit CSS and before `app.css`: the optional `clanker-ui-themes(.min).css`, then `clanker-ui-a11y(.min).css` (load it in every app; see the SKILL file sets). The theme script `clanker-ui-theme(.min).js` is a classic script before the modules ([theming.md](theming.md)).
- Every kit file has a `.min` version in `dist/`. Load all files from the same set.

## Exports

| Names | Readable set | `.min` set |
| --- | --- | --- |
| Core API (`h`, `svg`, `icon`, `define`, `emit`, `strings`, `theme`, `direction`, `isOpen`, ...) | `clanker-ui.js` | `clanker-ui.min.js` or `clanker-ui-core.min.js` |
| Component API (`toast`, `dialogOpen`, `calendarSetValue`, ...) | `clanker-ui.js` | `clanker-ui.min.js` or the group file |
| Charts (`chart`, `sparkline`, `statTile`) | `clanker-ui-chart.js` | `clanker-ui-chart.min.js` |

Group set:

```js
import { h, icon } from "/vendor/clanker-ui/clanker-ui-core.min.js"
import { toast, dialogOpen } from "/vendor/clanker-ui/clanker-ui-overlays.min.js"

document.querySelector("#save").addEventListener("click", () => toast.success("Saved", { description: "Your changes are saved." }))
document.addEventListener("select:change", event => console.log(event.detail.value))
```

The group files do not export the core API again. Each component file names the file of its exports.
