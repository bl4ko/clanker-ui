# AI Elements

Patterns for agent and chat pages, made only of kit components (no own `data-slot`, no extra file). Each docs page (https://bl4ko.github.io/clanker-ui/docs/ai-elements/) has the markup of the finished state and the module that changes it. `clanker-ui.json` lists the components of each pattern under `patterns`.

Rules for every pattern:

- An agent step (thinking, a command, a search, a subagent) is a `trace-line` in one `trace` per turn; a step with output is a `trace-collapsible`. Status: `data-status="running|error|pending"` on the line; no status when it is done.
- A question for the person (approve, deny, pick) is not a step: put it outside the `trace`, as an `item` with buttons.
- Change the state from code: set the attributes and the title text, open or close a step with `traceOpen()` and `traceClose()`, and add new parts with `h()`. The kit gives new markup its behavior.
- Text that streams in: append text nodes; never `innerHTML`.

| Need | Pattern | Built with |
| --- | --- | --- |
| A chat page: the thread that keeps the reading position while a reply streams | [Chat](https://bl4ko.github.io/clanker-ui/docs/ai-elements/chat/) | `message-scroller` (anchor on the person's turn), `message`, `bubble`, `input-group` |
| How much of the model's context window is used | [Context](https://bl4ko.github.io/clanker-ui/docs/ai-elements/context/) | `hover-card` on a `button`, `progress` |
| The files that the agent changed, as folders that open and close; a click selects a file | [File Tree](https://bl4ko.github.io/clanker-ui/docs/ai-elements/file-tree/) | `collapsible` (div root, ghost `sm` button trigger), `button` with `aria-current` |
| A source inside the sentence that it supports, with a card on hover and focus | [Inline Citation](https://bl4ko.github.io/clanker-ui/docs/ai-elements/inline-citation/) | `hover-card` (all `span` parts inside a `p`), `button` `secondary` `xs` |
| One turn: the person's bubble, the agent's reply, copy and feedback buttons | [Message](https://bl4ko.github.io/clanker-ui/docs/ai-elements/message/) | `message`, `bubble`, `tooltip`, `code-block` |
| Pick the model and the effort next to the field | [Model Selector](https://bl4ko.github.io/clanker-ui/docs/ai-elements/model-selector/) | two `dropdown-menu` radio groups (`data-close-on-click`) in the `input-group-addon` |
| The message field with attachments, model menus, and send | [Prompt Input](https://bl4ko.github.io/clanker-ui/docs/ai-elements/prompt-input/) | `input-group` with a `textarea`, `attachment`, `dropdown-menu` |
| The links that the agent used, after the reply ("Used 3 sources"); remove duplicate URLs | [Sources](https://bl4ko.github.io/clanker-ui/docs/ai-elements/sources/) | `trace-collapsible` with a nested `trace` of links |
| Prompts that the person sends in one click | [Suggestion](https://bl4ko.github.io/clanker-ui/docs/ai-elements/suggestion/) | outline `sm` `button` row with `scroll-fade-x` |
