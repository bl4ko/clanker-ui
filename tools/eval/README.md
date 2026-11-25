# Agent eval

Measures whether the skill helps an agent build pages that are clean on errors and lint: console errors, CSP violations, and lint errors. It does not check that the task works. Manual only, never in CI: `run` spends model quota. Run it before and after a skill change, not on every pull request.

```sh
go run ./tools/gen build
uv run --no-project --with playwright python -I tools/eval selftest
uv run --no-project --with playwright python -I tools/eval run
uv run --no-project --with playwright python -I tools/eval score /tmp/clanker-eval-XXXX/login-toast-skill-1/static
```

- `run`: each task in `tasks/` runs `claude -p` in its own directory with the kit files in `static/vendor/clanker-ui/`, once per arm (`skill`: the skill in `.claude/skills/clanker-ui/`; `none`: no skill, `--disable-slash-commands`) and `--runs` times (default 2). Then it scores every `static/` and writes `report.json` and `report.md`. Options: `--tasks`, `--arms`, `--model`, `--timeout`.
- `score`: serves a web root with the CSP header of `SKILL.md` (kit files from `kit/` and `kit/dist/` when the root has none) and loads `index.html` in Chromium at 1280 and 390 px, light and dark. It counts console errors and page errors, CSP violations, `design-lint.js` errors, and `markup-lint.js` errors (the Markup column reads 0 until `references/markup-lint.js` exists). A CSP violation that the header and the meta tag both report counts once; a view that fails to load counts one `scorer` error. Lower is better; `missing` means no `index.html`.
- `selftest`: proves the scorer on `fixtures/good` (0 errors) and `fixtures/bad` (seeded errors of each kind). About 6 s; it needs Chromium, so it is not in the `go` CI job.
- The default output is a new temporary directory. Keep `--out` outside this repository and any directory with a `CLAUDE.md` or `AGENTS.md`: the agent reads them. User-level `CLAUDE.md` files and skills can leak into both arms; check `claude.json` in each run directory.
