# Setup details

## Other ways to get the files

- Single files: each kit file is also a release asset, for example `https://github.com/bl4ko/clanker-ui/releases/download/v<version>/clanker-ui.min.css`.
- A clone of the repository: the kit files are in `kit/`. `kit/dist/` and the styles other than Nova are not in git. Run `go run ./tools/gen build` first (it needs the Tailwind CSS CLI and the network; see `AGENTS.md` in the repository), then copy the files from `kit/` and from `kit/dist/`.

Check each downloaded file against `SHA256SUMS` (also a release asset): `grep ' clanker-ui-<version>.zip$' SHA256SUMS | shasum -a 256 -c` (Linux: `sha256sum -c`). A release that `release.yml` built has a build provenance attestation: `gh attestation verify <file> -R bl4ko/clanker-ui`. v0.3.0 was released by hand and has none.

The modules import each other by relative path, so all kit files go in one directory.

## Updates

The first line of each release file is `/*! clanker-ui v<version> | ...`. An update replaces every kit file of the app with the file of the same name from one new release. A changed header alone is not an update, and a mix of two versions breaks the page ("already defined" or a missing export).

Renovate finds new releases from this header with a regex manager:

```json
{
  "customType": "regex",
  "managerFilePatterns": ["/(^|/)clanker-ui[^/]*\\.(css|js)$/"],
  "matchStrings": ["^/\\*! clanker-ui v(?<currentValue>\\d+\\.\\d+\\.\\d+\\S*) \\|"],
  "datasourceTemplate": "github-releases",
  "depNameTemplate": "bl4ko/clanker-ui",
  "extractVersionTemplate": "^v(?<version>.+)$"
}
```

- `config:recommended` ignores `**/vendor/**`. If the kit is in a `vendor/` directory, set `ignorePaths` without that entry.
- Renovate changes only the headers. A job on the Renovate pull request must replace the files: download `clanker-ui-<version>.zip` and `SHA256SUMS`, check the checksum, run `gh attestation verify <zip> -R bl4ko/clanker-ui --signer-workflow bl4ko/clanker-ui/.github/workflows/release.yml --source-ref refs/tags/v<version>`, and copy each file of the app from the zip root or `dist/`. Add the files that a copied module imports (`./clanker-ui-core.min.js`). Then commit to the pull request branch.
- Do not auto-merge a kit update. Run the app UI test and look at the app first. An app rule that auto-merges all minor updates comes after the presets; `automergeType: "pr-comment"` in the kit package rule stops the merge.

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
| Syntax colors (`codeBlockHighlight`) | `clanker-ui-code.js` | `clanker-ui-code.min.js` |

Group set:

```js
import { h, icon } from "/vendor/clanker-ui/clanker-ui-core.min.js"
import { toast, dialogOpen } from "/vendor/clanker-ui/clanker-ui-overlays.min.js"

document.querySelector("#save").addEventListener("click", () => toast.success("Saved", { description: "Your changes are saved." }))
document.addEventListener("select:change", event => console.log(event.detail.value))
```

The group files do not export the core API again. Each component file names the file of its exports.
