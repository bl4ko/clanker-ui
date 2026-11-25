# Roadmap

Work that waits for a trigger, not a date. When a trigger holds, open an issue; a breaking markup change needs one anyway (AGENTS.md "Scope until 1.0").

## Agents

| Item | Trigger | Reason |
| --- | --- | --- |
| `data-agent-confirm`, `data-agent-secret`, `data-agent-hidden` | A browser agent or a standard reads such hints | Mark destructive actions, secret fields, and noise for agents; without a reader they are dead markup. |
| Agent bridge: `snapshot`, `query`, `act` | An app needs agent control of kit state beyond the accessibility tree | One typed view of component state and actions instead of agents clicking through popups. |
| WebMCP | Ships without a flag in a stable browser | Forms and actions become tools for in-browser agents; the bridge above would back it. |

## Platform

| Item | Trigger | Reason |
| --- | --- | --- |
| CSS anchor positioning | Baseline Widely available | Replaces the JS `position()` of popups. |
| `appearance: base-select` | Baseline Widely available | A native select with styled items could replace the kit select popup, if it keeps Base UI parity. |
| `closedby` on `<dialog>` | Baseline Widely available | Native light dismiss replaces the kit backdrop-press code. |
| `interestfor` | Baseline Widely available | Native hover and focus triggers for tooltip and hover card. |
| `light-dark()` tokens | A decision on override semantics | An app `:root { --x }` override applies only in light today and would apply in both themes; that silently changes app theming. Saves about 40 lines per style. |
| Container queries in card or sidebar | shadcn adds them, or a bug needs one | New ones diverge from shadcn parity. |
| `:user-invalid` | shadcn styles it | It shows errors at other moments than the kit form validation (`aria-invalid`). |

## Tests

| Item | Trigger | Reason |
| --- | --- | --- |
| Required-parts lint rule | The catalog records the required parts of each component | Without that data the lint cannot flag a missing part, such as a dialog without `dialog-content`. |
| WAI-ARIA `checkPattern` helper | An ARIA regression gets past `tools/behavior gate` | The gate already checks recorded keys of 47 components. |
