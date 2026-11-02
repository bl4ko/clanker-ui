# Security policy

## Report a vulnerability

Do not open a public issue for a security problem. Use GitHub private vulnerability reporting:

1. Go to <https://github.com/bl4ko/clanker-ui/security/advisories/new> (the "Report a vulnerability" button on the Security tab).
2. Describe the problem, the affected files and version, and the steps or a small page that shows it.

You get an answer in the advisory. When a fix is ready, it is released and the advisory is published with credit to you, if you want it.

## Scope

- The kit files (`clanker-ui*.css`, `clanker-ui*.js`, `dist/`): for example a way to run script under the strict CSP with Trusted Types, an HTML injection through kit APIs, or a bypass of the kit security rules.
- The docs site and the dev server in this repository.

## Supported versions

Only the latest release gets security fixes. [CHANGELOG.md](CHANGELOG.md) lists the changes of each release, breaking changes first.
