---
description: Show available TARS commands grouped by what you want to do
argument-hint: "[topic, optional]"
---

# /help

## Protocol
Read and follow `skills/core/SKILL.md` section "Help routing".

If an argument is supplied, scope the response to commands relevant to that topic.
Otherwise, list commands grouped by intent: capture, synthesize, produce, maintain, and set up. Include one "Recommended next workflow" based on `_system/maturity.yaml`; if deferred setup is incomplete, recommend `/welcome --continue-setup` or "continue TARS setup".

End with: "Tip: slash commands are shortcuts. You can also type natural-language requests like 'process everything in my inbox' or 'what should I focus on today.'"
