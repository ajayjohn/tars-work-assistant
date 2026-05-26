---
name: meeting
description: Process transcripts or rough meeting notes into journal entries, tasks, transcript archives, and memory proposals
triggers: ["process this meeting", "meeting transcript", "meeting notes", "rough notes from a call", "process this call"]
user-invocable: true
help:
  purpose: |-
    Turn a meeting transcript or rough notes into reviewed journal context,
    proposed tasks, proposed durable memory, and preserved evidence when
    available.
  use_cases:
    - "Process this meeting transcript"
    - "Here are rough notes from a call"
    - "Summarize this meeting and extract follow-ups"
  scope: meeting,transcript,rough-notes,journal,followthrough
---

# Meeting

Meeting processing is TARS' highest-value ingest workflow. It should support
perfect transcripts and imperfect executive inputs.

## Intake modes

| Mode | Use when | Confidence |
|---|---|---|
| Transcript | Raw transcript is available | high |
| Rough notes | User provides bullets or memory of the meeting | medium |
| Calendar-only gap | TARS sees a meeting but no notes/transcript | low, ask for one missing detail |

Do not block just because a transcript is unavailable. Create lower-confidence
meeting context only after user review.

## Required behavior

- Resolve date, title, participants, and source confidence.
- Scan for sensitive content before echoing or writing.
- Preserve transcript evidence when raw text exists.
- Run nuance capture when transcript text is substantial.
- Propose tasks and memory through review gates.
- Never persist unresolved names, tasks, memory, or sensitive content silently.

## References

- `references/intake.md`
- `references/transcript.md`
- `references/rough-notes.md`
- `references/persistence.md`
- `resources/nuance-pass-prompt.md`
- `references/legacy-full-protocol.md`
