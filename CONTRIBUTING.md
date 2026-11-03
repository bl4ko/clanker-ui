# Contributing

Thank you for your help. Bug reports with a small page that shows the problem are the most useful. For a difference from shadcn, give the component, the browser, and the shadcn page that shows the correct behavior.

## Setup

- [Go](https://go.dev) (the version in `go.mod`). The server and the generator use only the Go standard library and esbuild (Go API). No Node.js, npm, or pnpm is necessary.
- [uv](https://docs.astral.sh/uv/) for the browser tests (Playwright):

  ```sh
  uv run --no-project --with playwright playwright install chromium firefox webkit
  ```

- Optional: the Tailwind CSS CLI (`brew install tailwindcss`) for the generator tests that compile CSS. Without it, these tests skip.

## Run and test

```sh
DIR=. ADDR=127.0.0.1:8110 go run .
go vet ./... && go test ./...
uv run --no-project --with playwright python -I test/run.py --base-url http://127.0.0.1:8110 --only g1 -k select --themes light --jobs 3 --out out/run
uv run --no-project --with playwright python -I tools/behavior gate --quick --base-url http://127.0.0.1:8110 --out out/gate
```

- The dev server serves the demo at `/demo` and the docs at `/docs`. `DIR=.` reads the files from disk, so a change shows without a rebuild. It also serves the behavior fixtures.
- Without filters, `test/run.py` runs every check in Chromium, Firefox, and WebKit, in light and dark, at 1280 and 390 px. That takes about 5 hours (about half with `--jobs 3`). Use `--only <module>`, `-k <regex>`, `--engines`, `--themes`, and `--widths` for a smaller run, for example `--engines chromium --themes light --widths 1280 --only foundation,docs`. `--list` prints the names of the checks. `--jobs 3` runs the 3 engines in parallel.
- On Linux, run `--engines chromium,firefox`. CI runs WebKit on macOS, and the behavior references are recorded on macOS.
- For a fix in one component, run the tests of that component in all 3 engines. For a change in shared code, also run `foundation` and the group of the component.

## Rules

- Never edit `clanker-ui.css` or `dist/` by hand. The component CSS comes from `tools/gen` and the kit layer `tools/gen/kit.css`. After each change of a kit file, run `go run ./tools/gen dist`; `go test` fails when `dist/` is old.
- No comments in code, except the first-line license comment of each kit file.
- The security rules in [README.md](README.md#security-rules) apply to all kit, demo, and docs code: no `innerHTML`, no `eval`, no inline scripts or styles. `go test` checks them.
- Each fix has a check that fails when only that fix is removed.
- A difference from shadcn needs a reason. Match the live behavior of <https://ui.shadcn.com>, or add a narrow `allowed` entry with a short, true reason to the behavior scenario.
- Commits use [Conventional Commits](https://www.conventionalcommits.org) (`fix(select): ...`) and must be signed (`git commit -S`; GitHub must show "Verified").
- A pull request can merge only when the required checks `ci-result` and `gitleaks` pass.

The full reference for the generator, the parity tool, the behavior gate, the test runner, and the docs server is in [DEVELOPMENT.md](DEVELOPMENT.md).

## License

By contributing, you agree that your contribution is distributed under the MIT License of this project (see [LICENSE](LICENSE)).
