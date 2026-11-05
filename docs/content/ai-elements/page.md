---
title: AI Elements
description: Patterns for agentic interfaces, built from clanker-ui components.
---

AI Elements are patterns for agentic interfaces. Each one is a composition of kit components that you copy into your page. There is nothing more to load: a pattern uses the parts, the CSS, and the JavaScript of its components, and adds no `data-slot` of its own.

A [Chat](/docs/ai-elements/chat) is a list of [Message](/docs/ai-elements/message) turns inside a [Message Scroller](/docs/components/message-scroller). The steps that an agent takes inside a turn are lines of a [Trace](/docs/components/trace), so every step has the same shape.

The patterns follow the [shadcn/ui AI Elements](https://ui.shadcn.com/docs/ai-elements). Where shadcn/ui uses the AI SDK, these pages show plain JavaScript that changes the markup: each example has the HTML of the finished state and a module that plays the steps again.

## Patterns

| Pattern | Use |
| --- | --- |
| [Chain of Thought](/docs/ai-elements/chain-of-thought) | A summary that expands into the steps an agent took. |
| [Chat](/docs/ai-elements/chat) | The thread. Message Scroller keeps your place while the reply streams. |
| [Context](/docs/ai-elements/context) | How much of the context window the conversation has used. |
| [File Tree](/docs/ai-elements/file-tree) | The files the agent changed, as a folder tree. |
| [Inline Citation](/docs/ai-elements/inline-citation) | A source in the sentence that opens on hover. |
| [Message](/docs/ai-elements/message) | One turn. The person's message, and the agent's reply with its actions. |
| [Model Selector](/docs/ai-elements/model-selector) | Two menus. One picks the model the agent runs, the other picks how hard it thinks. |
| [Plan](/docs/ai-elements/plan) | The steps the agent plans to take, and how far it has got. |
| [Prompt Input](/docs/ai-elements/prompt-input) | A message field with attachments and a send button. |
| [Reasoning](/docs/ai-elements/reasoning) | The agent's thinking as it streams. |
| [Sources](/docs/ai-elements/sources) | The links the agent used for a reply. |
| [Suggestion](/docs/ai-elements/suggestion) | A short prompt you can send to the agent in one click. |
| [Task](/docs/ai-elements/task) | The steps the agent takes, as it takes them. |
| [Tool](/docs/ai-elements/tool) | A tool call the agent makes, from input to output. |

## Load the files

A pattern needs the group files of its components. Most patterns use `chat` (Message, Bubble, Trace, Code Block, Message Scroller, Attachment) with `forms` (Input Group) and `overlays` (Dropdown Menu, Hover Card, Tooltip, Sheet). With three of these groups, load the one-file set (`clanker-ui.min.css` and `clanker-ui.min.js`); see [Installation](/docs/installation). The [catalog](/clanker-ui.json) lists the components of each pattern under `patterns`.

## From AI SDK Elements

The table of shadcn/ui maps each file of [AI SDK Elements](https://elements.ai-sdk.dev) to a pattern. The kit has no React wrappers, so there is no migration prompt: copy the markup of the pattern, and set its state attributes from your code.
