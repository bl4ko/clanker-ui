# Icons

The kit has 242 [Lucide](https://lucide.dev/icons/) 1.63.0 icons. Write `<svg data-lucide="<name>"></svg>` or call `icon("<name>")`; the names are also in the `iconNames` export. An unknown name logs one `console.warn` per name and renders an empty `<svg>`; it does not throw.

## Names

`activity`, `archive`, `arrow-down`, `arrow-down-wide-narrow`, `arrow-left`, `arrow-left-right`, `arrow-right`, `arrow-up`, `arrow-up-down`, `arrow-up-narrow-wide`, `arrow-up-right`, `at-sign`, `award`, `badge-check`, `ban`, `banknote`, `bell`, `bell-off`, `bluetooth`, `bold`, `book-open`, `bookmark`, `bot`, `box`, `briefcase`, `bug`, `building`, `calculator`, `calendar`, `calendar-check`, `calendar-days`, `calendar-plus`, `camera`, `car`, `chart-area`, `chart-bar`, `chart-column`, `chart-line`, `chart-pie`, `check`, `chevron-down`, `chevron-left`, `chevron-right`, `chevron-up`, `chevrons-left`, `chevrons-right`, `chevrons-up-down`, `circle`, `circle-alert`, `circle-check`, `circle-check-big`, `circle-dashed`, `circle-dot`, `circle-fading-plus`, `circle-minus`, `circle-plus`, `circle-question-mark`, `circle-x`, `clock`, `cloud`, `cloud-download`, `cloud-upload`, `code`, `coins`, `contrast`, `copy`, `cpu`, `credit-card`, `database`, `dollar-sign`, `dot`, `download`, `ellipsis`, `ellipsis-vertical`, `euro`, `external-link`, `eye`, `eye-off`, `face-slightly-smiling`, `file`, `file-check`, `file-code`, `file-pen`, `file-plus`, `file-spreadsheet`, `file-text`, `flag`, `flask-conical`, `folder`, `folder-open`, `folder-plus`, `folder-search`, `funnel`, `gauge`, `gift`, `git-branch`, `git-commit-horizontal`, `globe`, `graduation-cap`, `grip-horizontal`, `grip-vertical`, `hammer`, `hard-drive`, `hash`, `headphones`, `heart`, `house`, `image`, `image-plus`, `inbox`, `info`, `italic`, `key`, `keyboard`, `landmark`, `laptop`, `layers`, `layout-dashboard`, `layout-grid`, `library`, `lightbulb`, `link`, `link-2`, `list`, `list-checks`, `list-filter`, `list-ordered`, `list-todo`, `loader`, `loader-circle`, `lock`, `lock-open`, `log-in`, `log-out`, `mail`, `mail-check`, `mail-open`, `map`, `map-pin`, `maximize-2`, `menu`, `message-circle`, `message-circle-dashed`, `message-square`, `mic`, `minimize-2`, `minus`, `monitor`, `moon`, `network`, `octagon-alert`, `octagon-x`, `package`, `palette`, `panel-left`, `panel-right`, `paperclip`, `pause`, `pencil`, `percent`, `phone`, `piggy-bank`, `plane`, `play`, `plug`, `plus`, `power`, `printer`, `qr-code`, `quote`, `receipt`, `redo-2`, `refresh-ccw`, `refresh-cw`, `rocket`, `rotate-ccw`, `rotate-ccw-clock`, `rotate-cw`, `route`, `router`, `save`, `search`, `send`, `server`, `settings`, `share`, `shield`, `shield-alert`, `shield-check`, `shopping-bag`, `shopping-cart`, `skip-forward`, `sliders-horizontal`, `smartphone`, `sparkles`, `square`, `square-check`, `square-pen`, `star`, `star-half`, `store`, `sun`, `table`, `tag`, `target`, `telescope`, `terminal`, `text-align-center`, `text-align-end`, `text-align-start`, `text-wrap`, `thermometer`, `thumbs-down`, `thumbs-up`, `ticket`, `timer`, `trash`, `trending-down`, `trending-up`, `triangle-alert`, `trophy`, `truck`, `underline`, `undo-2`, `upload`, `user`, `user-check`, `user-plus`, `user-round-x`, `user-x`, `users`, `utensils`, `video`, `volume-off`, `wallet`, `wifi`, `wifi-off`, `wrench`, `x`, `zap`, `zoom-in`, `zoom-out`

## Aliases

Old Lucide names that show the icon on the right:

`alert-circle` → `circle-alert`, `alert-octagon` → `octagon-alert`, `alert-triangle` → `triangle-alert`, `align-center` → `text-align-center`, `align-left` → `text-align-start`, `align-right` → `text-align-end`, `area-chart` → `chart-area`, `bar-chart-3` → `chart-column`, `bar-chart-horizontal` → `chart-bar`, `check-circle` → `circle-check-big`, `check-circle-2` → `circle-check`, `check-square-2` → `square-check`, `circle-help` → `circle-question-mark`, `download-cloud` → `cloud-download`, `edit` → `square-pen`, `file-edit` → `file-pen`, `filter` → `funnel`, `fork-knife` → `utensils`, `git-commit` → `git-commit-horizontal`, `help-circle` → `circle-question-mark`, `history` → `rotate-ccw-clock`, `home` → `house`, `layers-3` → `layers`, `line-chart` → `chart-line`, `loader-2` → `loader-circle`, `minus-circle` → `circle-minus`, `more-horizontal` → `ellipsis`, `more-vertical` → `ellipsis-vertical`, `pen-box` → `square-pen`, `pen-square` → `square-pen`, `pie-chart` → `chart-pie`, `plus-circle` → `circle-plus`, `sidebar` → `panel-left`, `smile` → `face-slightly-smiling`, `sort-asc` → `arrow-up-narrow-wide`, `sort-desc` → `arrow-down-wide-narrow`, `stars` → `sparkles`, `text` → `text-align-start`, `trash-2` → `trash`, `unlock` → `lock-open`, `upload-cloud` → `cloud-upload`, `user-x-2` → `user-round-x`, `verified` → `badge-check`, `wrap-text` → `text-wrap`, `x-circle` → `circle-x`, `x-octagon` → `octagon-x`

## Add an icon

Copy the icon node of a Lucide icon (lucide.dev: the icon page, or `lucide-static/icon-nodes.json`) and register it once, before or after the markup that uses it:

```js
import { registerIcons } from "/vendor/clanker-ui/clanker-ui.min.js"

registerIcons({
  "ship": [
    ["path", { d: "M12 2v2" }],
    ["path", { d: "M12 9.189V13" }],
    ["path", { d: "M19 12V6a2 2 0 00-2-2H7a2 2 0 00-2 2v6" }],
    ["path", { d: "M19.38 19A11.6 11.6 0 0021 13l-8.188-3.639a2 2 0 00-1.624 0L3 13.001a11.6 11.6 0 002.81 7.76" }],
    ["path", { d: "M2 20c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1s1.2 1 2.5 1c2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" }],
  ],
})
```

- Each node is a path `d` string or a `[tag, attrs]` pair. Tags: `path`, `circle`, `rect`, `line`, `polyline`, `polygon`, `ellipse`. Attributes: geometry, `fill`, `stroke*`, `fill-rule`, `clip-rule`, `opacity`, `transform`. Other tags or attributes throw a `TypeError`. The icon uses the Lucide frame: `viewBox="0 0 24 24"`, `stroke="currentColor"`, stroke width 2, `fill="none"`.
- Names are lowercase words joined by `-`. A name that the kit already has (or an alias) throws.
- The kit fills `<svg data-lucide>` elements with the new names that are already in the page. `iconNames` includes the new names.
- The kit builds the SVG with DOM calls, so this works under the strict CSP and Trusted Types. Do not inline SVG markup with `innerHTML`.
