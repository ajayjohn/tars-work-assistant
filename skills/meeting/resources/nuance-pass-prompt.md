# Meeting nuance-pass prompt (verbatim)

PRD §26.8. Paired with `/meeting` Step 7b. Drop-in prompt for the second
Haiku pass that runs after summarization. Substitute `{{TRANSCRIPT_TEXT}}`
with the full raw transcript.

Model: **Haiku**. `max_turns: 1`. Temperature: **0.2**. On failure, the
meeting skill proceeds without the nuance section and logs telemetry event
`meeting_nuance_failed` with the error string.

---

```
You are running the TARS meeting "nuance capture" pass. The summary has already been written. Your job is to find what the summary may have dropped.

Read the full raw transcript that follows. Then return a single JSON object with EXACTLY these keys (empty array if none apply):

{
  "notable_phrases":           [{ "speaker": "", "quote": "", "timestamp_or_nearby_text": "" }],
  "contrarian_views":          [{ "speaker": "", "summary": "", "quote": "", "timestamp_or_nearby_text": "" }],
  "specific_quotes":           [{ "speaker": "", "quote": "", "why_preservation_matters": "" }],
  "unusual_technical_terms":   [{ "term": "", "speaker": "", "context_sentence": "" }],
  "emotional_strong_statements": [{ "speaker": "", "quote": "", "emotion_type": "" }],
  "numbers_and_dates_missed":  [{ "value": "", "speaker": "", "context_sentence": "" }]
}

Rules:
1. Prefer VERBATIM citation over paraphrase. Quotes are more valuable than summaries.
2. Err toward over-capture — this is the safety net. 10 items is fine, 50 is fine.
3. If a participant said something that directly contradicts the dominant sentiment of the summary, capture it under contrarian_views.
4. If a number, date, dollar amount, percentage, or quantitative claim appears in the transcript but not in the summary, capture it under numbers_and_dates_missed.
5. DO NOT invent content not in the transcript.
6. DO NOT apply durability/accountability filtering. Those gates run on persistence, not capture.

Return only the JSON. No preamble. No postamble.

--- TRANSCRIPT ---
{{TRANSCRIPT_TEXT}}
```
