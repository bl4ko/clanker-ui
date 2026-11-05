---
title: AI Elements
description: Patterns for agentic interfaces, built from clanker-ui components.
---

AI Elements are patterns for agentic interfaces. Each one is a composition of kit components that you copy into your page. There is nothing more to load: a pattern uses the parts, the CSS, and the JavaScript of its components, and adds no `data-slot` of its own.

A chat is a list of [Message](/docs/ai-elements/message) turns inside a [Message Scroller](/docs/components/message-scroller). The steps that an agent takes inside a turn are lines of a [Trace](/docs/components/trace), so every step has the same shape.

The patterns follow the [shadcn/ui AI Elements](https://ui.shadcn.com/docs/ai-elements). Where shadcn/ui uses the AI SDK, these pages show plain JavaScript that changes the markup: each example has the HTML of the finished state and a module that plays the steps again.

## Patterns

| Pattern | Use |
| --- | --- |
| [Message](/docs/ai-elements/message) | One turn. The person's message, and the agent's reply with its actions. |

## Load the files

A pattern needs the group files of its components. Most patterns use `chat` (Message, Bubble, Trace, Code Block, Message Scroller, Attachment) with `forms` (Input Group) and `overlays` (Dropdown Menu, Hover Card, Tooltip, Sheet). With three of these groups, load the one-file set (`clanker-ui.min.css` and `clanker-ui.min.js`); see [Installation](/docs/installation). The [catalog](/clanker-ui.json) lists the components of each pattern under `patterns`.

## From AI SDK Elements

The table of shadcn/ui maps each file of [AI SDK Elements](https://elements.ai-sdk.dev) to a pattern. The kit has no React wrappers, so there is no migration prompt: copy the markup of the pattern, and set its state attributes from your code.
