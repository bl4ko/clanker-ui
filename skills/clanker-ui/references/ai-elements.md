# AI Elements

Patterns for agent and chat pages, made only of kit components (no own `data-slot`, no extra file). Each docs page (https://bl4ko.github.io/clanker-ui/docs/ai-elements/) has the markup of the finished state and the module that changes it. `clanker-ui.json` lists the components of each pattern under `patterns`.

Rules for every pattern:

- An agent step (thinking, a command, a search, a subagent) is a `trace-line` in one `trace` per turn; a step with output is a `trace-collapsible`. Status: `data-status="running|error|pending"` on the line; no status when it is done.
- A question for the person (approve, deny, pick) is not a step: put it outside the `trace`, as an `item` with buttons.
- Change the state from code: set the attributes and the title text, open or close a step with `traceOpen()` and `traceClose()`, and add new parts with `h()`. The kit gives new markup its behavior.
- Text that streams in: append text nodes; never `innerHTML`.

| Need | Pattern | Built with |
| --- | --- | --- |
| One turn: the person's bubble, the agent's reply, copy and feedback buttons | [Message](https://bl4ko.github.io/clanker-ui/docs/ai-elements/message/) | `message`, `bubble`, `tooltip`, `code-block` |
