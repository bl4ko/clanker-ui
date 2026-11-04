---
title: Blocks
description: Full pages built only from kit parts. Copy one, replace the sample content, and keep the structure.
---

Blocks are the shadcn blocks and examples as plain HTML. Each one is a whole page with the strict CSP, light and dark mode, and a layout for 1280 and 390 px. They use only kit parts and tokens: no app CSS. Agents find the same files in the skill, in `references/blocks/`.

| Block | Start from it for |
| --- | --- |
| [Dashboard](/docs/blocks/dashboard) | An app with a sidebar: key numbers, a chart, and a table. |
| [Data Table](/docs/blocks/data-table) | A list of records with a top header, filters, sorting, selection, and paging. |
| [Settings](/docs/blocks/settings) | Account and app settings in sections, each with its own save action. |
| [Form](/docs/blocks/form) | A page that creates or edits one record. |
| [Detail](/docs/blocks/detail) | A page that shows one record and its activity. |
| [Login](/docs/blocks/login) | Sign in. |
| [States](/docs/blocks/states) | Empty, loading, and error states. |

## Rules

- Start from the closest block, not from an empty page. Keep its structure: the shell, the page header, and the order of the sections.
- The page parts are on [Page](/docs/components/page), [Site Header](/docs/components/site-header), [Section Cards](/docs/components/section-cards), [Stat Grid](/docs/components/stat-grid), and [Data Table](/docs/components/data-table).
- The design rules for spacing, buttons, color, forms, and states are in the skill file [design.md](https://github.com/bl4ko/clanker-ui/blob/main/skills/clanker-ui/references/design.md).
