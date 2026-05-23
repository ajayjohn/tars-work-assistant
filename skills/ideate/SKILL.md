---
name: ideate
description: Open Collider semantic collision engine — generates genuinely non-obvious ideas by colliding project context with structurally distant knowledge domains
attribution: "Bisociation engine design based on Open Collider (github.com/CL-ML/open-collider)"
user-invocable: true
help:
  purpose: |-
    Generates non-obvious ideas using the Open Collider bisociation engine: collides your vault context (initiative notes, product notes, decisions, meeting notes) with structurally distant knowledge domains to produce ideas that vanilla brainstorming cannot reach. Validated at 62% originality preference (blind LLM-judge), 4–13× effect over baselines.

    Most executives reach this skill through /think discover → escalation. The /ideate command is a direct shortcut for returning users.
  use_cases:
    - "I need surprising angles for positioning [feature]"
    - "Non-obvious approaches to [challenge]"
    - "Ideate on [initiative name]"
    - "What haven't we thought of about [topic]?"
    - "/ideate quick [topic]"
    - "/ideate deep [topic]"
    - "/ideate deepen [project-slug]"
  scope: ideation,creativity,strategy,positioning,innovation,brainstorming
---

# Ideate: Open Collider semantic collision engine

Generates non-obvious ideas through bisociation — structured collision between the user's workspace context and structurally distant knowledge domains. Based on Arthur Koestler's bisociation theory; validated at 62% originality preference (blind LLM-judge), 4–13× geometric distance effect over baselines.

The core mechanism: rather than adding more same-domain context (which deepens convergence), inject material from structurally distant disciplines. Where trajectories from distant domains converge on the problem, genuinely non-obvious ideas emerge. Volume + rigor curation = consistently non-trivial output.

All vault reads/writes use `mcp__tars_vault__*` tools (see `skills/core/SKILL.md`). Idea generation uses parallel subagents via the Task tool — one subagent per (reference × domain) combo, each with an isolated context window. Wikilinks form via `mcp__tars_vault__format_wikilink`. Follow all universal constraints from core.

---

## Mode detection

Detect operating mode from the user's signal before anything else.

| Signal | Mode |
|--------|------|
| Called from `/think` discover escalation with a brief seed | `discovery-escalation` — skip to Phase 1 |
| `/ideate quick [topic]` or "quick ideas" | `quick` — 5 min, top 5–7 ideas, 2 domain families |
| `/ideate deep [topic]` or "deep ideation" | `deep` — 15 min, top 10–15 ideas, 4 domain families |
| `/ideate deepen [slug]` or "more ideas like the ones I loved" | `deepen` — iterate from prior session's loved ideas |
| `/ideate review [slug]` or "show my past ideas for X" | `review` — show saved ideas, no generation |
| `/ideate` with no topic, or topic but no prior project | `setup` → `quick` — interview for brief, then quick |

Read `_system/config.md` once at start: get `tars-bluf-level`, `tars-default-analysis-mode`, user name, company, and industry (the executive's domain vocabulary for the translation principle).

Emit `TodoWrite` progress list at start:
1. Load context and construct brief          [in_progress]
2. Domain generation                         [pending]
3. Idea generation (parallel subagents)      [pending]
4. Scoring (5-axis)                          [pending]
5. Pre-curation (4 filters)                  [pending]
6. Executive review                          [pending]
7. Capture vault assets                      [pending]
8. Update domain history                     [pending]

---

## PHASE 0: Context loading and brief construction

**Goal**: Auto-populate 80% of the brief from vault context so the exec confirms and tweaks, not writes from scratch.

**If mode = `discovery-escalation`**: A brief seed was passed from `/think` discover (Sections 1–4 of the discovery output). Skip Steps 0b–0d. Use the discovery output as the brief draft and go directly to Step 0e for confirmation. Mark Step 1 complete in TodoWrite.

**If mode = `review`**: Skip Phase 0 entirely — go to PHASE 0-SHORTCUT: Review mode.

**If mode = `deepen`**: Skip Phase 0 — load the existing project and go to PHASE 0-SHORTCUT: Deepen mode.

### Step 0a: Check for existing project

```
mcp__tars_vault__search_by_tag(tags=["tars/ideation-project"], query=<topic keywords>, limit=5)
```

If a matching project exists at `contexts/ideation/<slug>/project.md`:
- Read it: `mcp__tars_vault__read_note(path="contexts/ideation/<slug>/project.md")`
- Extract: tars-objective, tars-constraints, tars-forbidden-topics, tars-domain-families, tars-session-count
- Ask: "Found existing ideation project [[<slug>]]. Continue this project with a new session, or start fresh? [Continue / Fresh]"
- If "Continue" and mode is quick/deep: treat as continuing project; domain families and forbidden topics carry forward

### Step 0b: Load vault context (3 parallel subagents — launch in one message)

**Subagent A — Initiative, product, and decision context**

```
mcp__tars_vault__search_by_tag(tags=["tars/initiative"], query=<topic keywords>, limit=8)
mcp__tars_vault__search_by_tag(tags=["tars/product"], query=<topic keywords>, limit=5)
mcp__tars_vault__search_by_tag(tags=["tars/decision"], query=<topic keywords>, limit=5)
For each matching result: mcp__tars_vault__read_note(path=<path>) — up to 5 reads total
Return JSON: {"initiatives": [...], "products": [...], "decisions": [...]}
```

**Subagent B — Competitor context and semantic search**

```
mcp__tars_vault__search_by_tag(tags=["tars/competitor"], limit=5)
mcp__tars_vault__semantic_search(query=<topic>, limit=5)
For each result above relevance threshold: mcp__tars_vault__read_note — up to 3 reads
Return JSON: {"competitors": [...], "context_artifacts": [...]}
```

**Subagent C — Recent journal and user model**

```
mcp__tars_vault__read_system_file(path="_system/config.md")
mcp__tars_vault__search_by_tag(tags=["tars/meeting"], query=<topic keywords>, limit=5)
For the 2 most relevant meeting notes: mcp__tars_vault__read_note
Return JSON: {"config": {...}, "recent_meetings": [...]}
```

### Step 0c: Construct brief draft

Using the three subagent results, synthesize the brief:

```json
{
  "slug": "<kebab-case-slug from topic>",
  "objective": "<single sentence: what are we ideating about and toward what end?>",
  "context": "<2-3 sentences of relevant background — cite specific vault sources>",
  "executive_domain": "<user's field and industry from config — used to calibrate translation>",
  "constraints": "<what must be respected: regulatory, brand, team capacity, timeline>",
  "what_makes_good_ideas": "<structural quality criteria — NOT topics. E.g.: 'Ideas that reframe the mechanism of value delivery.' Derived from tars-default-analysis-mode and user context.>",
  "forbidden_topics": ["<angles already explored in recent decisions/meetings>"],
  "reference_sources": ["<list of vault note paths found in Step 0b, ranked by relevance>"]
}
```

### Step 0d: Select reference texts

From `reference_sources`, select the most relevant:
- Quick mode: 2 reference texts
- Deep mode: 3 reference texts

Selection criteria: specificity to objective > recency > substantive length. Never select two notes about the same meeting or topic. Read each selected note fully:
```
mcp__tars_vault__read_note(path=<selected_path>)
```

### Step 0e: Present brief for confirmation

Present concisely. Do NOT ask the user to fill in a form — present a draft for rapid confirmation:

```
**Ideation brief — confirm before I begin**

Objective: [one sentence]

Context I'm working from:
[2-3 sentence synthesis — "(source: [[Note Name]])" inline for key facts]

Constraints I'll respect:
- [constraint — source]

Already explored (off-limits):
- [forbidden topic — source]

Reference material I'll use: [list of selected note names]
Mode: [quick / deep]

Confirm? [Yes / Edit objective / Change mode / Add constraints]
```

Wait for confirmation. Apply any edits to the brief before proceeding.

---

## PHASE 1: Domain generation

**Goal**: Generate structurally distant domain families with active-principle narratives that produce genuine bisociation — not surface analogy.

Update TodoWrite: Step 2 in_progress.

### Strategy selection

| Condition | Strategy |
|-----------|----------|
| New project, quick mode | fresh — 2 domain families |
| New project, deep mode | fresh — 4 domain families |
| Continuing project, no loved ideas | fresh — same count as mode |
| Continuing project, has loved ideas (deepen mode or deep mode iteration 2+) | deepen + refresh — 2 families each |

### Loading domain history (if continuing project)

```
mcp__tars_vault__read_note(path="contexts/ideation/<slug>/project.md")
```

Extract `tars-domain-families`: a list of entries, each with:
- `family_name`: parent discipline (e.g., "evolutionary biology")
- `sub_domains_used`: list of specific sub-specialties used in prior sessions
- `produced_loved`: boolean
- `mechanisms_extracted`: list of causal mechanism descriptions from loved ideas
- `last_used`: date

---

### Strategy A: Fresh domains

Generate N domain families that are **structurally distant** from the project domain. The goal is maximum structural distance — not surface distance. Two disciplines can share causal architecture despite having nothing in common on the surface.

Selection criteria:
- ZERO surface connection to the project domain or industry
- Studies systems with mechanisms that might structurally transfer: incentive structures, feedback loops, selection pressures, threshold dynamics, cascade effects, information asymmetry
- Has produced counter-intuitive mechanisms that surprised even practitioners in the field
- NOT already in `tars-domain-families` for this project (checked via domain history)

Do NOT select from: management, business strategy, economics, psychology (surface-similar to executive work). Good source categories: evolutionary biology, materials science, military logistics, culinary chemistry, epidemiology, ecological succession, theatrical direction, fluid dynamics, ethology, mycology, geomorphology, aviation failure analysis, glaciology, urban transit planning, marine navigation, immunology, animal husbandry, cryptography history, paleontology, acoustical engineering, mycorrhizal ecology, crystallography.

For each domain family, generate 2-3 specific sub-specialties. For each sub-specialty, write an **active principle narrative** in this exact format:

> "A [specific specialist role — not 'expert'; e.g., 'wildfire behavior analyst', not 'fire expert'] whose work reveals [specific counter-intuitive mechanism that runs against common sense]. [2-3 sentences developing the mechanism — what makes it work, why it is structurally non-obvious]. [Open question: how does this mechanism apply to (project objective, rephrased as an open question)?]"

Requirements:
- Name a specific specialist role (granular, not generic)
- Name a specific counter-intuitive mechanism (not just the field)
- 3–6 sentences total
- End with an open question aimed at the project
- The mechanism must be the kind that surprised the field when first discovered

Example (illustrative only — do not reuse): "A wildfire behavior analyst whose work reveals that the fastest way to stop a fire is to deliberately start another one ahead of it. Backburning exploits the fire's own oxygen hunger: by consuming fuel in the fire's path, you deny it the resources it needs to advance. The technique works only when you understand what the fire is chasing, not just where it is heading. How might [product/service] benefit from deliberately creating a smaller version of the problem it is trying to solve, in order to exhaust the conditions that feed the larger one?"

### Strategy B: Deepen

Load loved ideas from prior sessions:
```
mcp__tars_vault__search_by_tag(tags=["tars/ideation-idea"], query=<slug>, limit=20)
Filter to tars-flag: loved
For each: read tars-collision-domain and tars-collision-mechanism
```

For each domain family that produced loved ideas:
- Look up its `sub_domains_used` in the domain history
- Generate 2 new sub-specialties within that family that are NOT already in `sub_domains_used`
- Write a fresh active principle for each new sub-specialty

The new sub-specialties must explore a different angle from the one that produced the loved idea — same family, different mechanism.

### Strategy C: Refresh

From loved/liked ideas, extract the **causal mechanism** (not the surface domain label):

For each loved idea:
1. What is the underlying structural pattern? (e.g., not "epidemiology" but "a threshold above which adoption becomes self-sustaining without further push")
2. Find 1-2 entirely different disciplines that study the SAME structural pattern from a different angle — disciplines that have NOTHING in common with the original domain on the surface

Write active principles for the new disciplines using the same format as Strategy A.

---

## PHASE 2: Idea generation (parallel subagents — MANDATORY isolation)

**Goal**: Generate 20 ideas per (reference_text × domain_set) combo, each in a fully isolated context window.

Update TodoWrite: Step 3 in_progress.

### Why isolation is non-negotiable

Cross-contamination between domains — where one domain's framing leaks into another's generation — is the single largest source of decorative collisions (ideas that mention a domain for flavor but aren't actually driven by it). Isolation is structural, not just instructional.

### Construct reference texts

Each reference text is a compressed brief (~400 words max) containing:
- The objective (one sentence)
- 3-5 specific, named facts from the vault notes selected in Phase 0d
- 3-5 implicit assumptions that the project currently takes for granted (these become axiom inversions)
- The audience and desired outcome

In deep mode with fundamentally different sub-challenges (e.g., one reference for product positioning, one for internal alignment), construct reference texts to capture those differences.

### Construct domain sets

Distribute the generated domain families into sets:
- Quick mode: all families in one set (2 families × 2-3 sub-specialties)
- Deep mode: split families into 2-3 sets of 2 families each

### Combo table

| Mode | Reference texts | Domain sets | Total combos |
|------|----------------|-------------|-------------|
| Quick | 2 | 1 | 2 |
| Deep | 3 | 2-3 | 6-9 |

### Launch parallel subagents (all in one message)

Spawn one subagent per combo using multiple Task tool calls in a **single message**. Each subagent receives ONLY its reference text and its domain set — nothing else.

**Subagent prompt (fill in variables — do not modify the structure)**:

```
ISOLATED IDEATION CONTEXT. DO NOT load vault memory, calendar, or external sources.
Your only job: generate exactly 20 ideas.

---

PROJECT OBJECTIVE
{brief.objective}

EXECUTIVE'S DOMAIN AND VOCABULARY
{config.industry} / {config.company}
Ideas must read as if they were conceived natively in this domain. Never sound like a translation.

REFERENCE MATERIAL
{reference_text — compressed brief, max 400 words}

STYLE RULES (MANDATORY)
- Short, assertive sentences. No hedging ("might", "could", "perhaps" are banned).
- Each idea starts from the domain mechanism — the mechanism is the engine, not decoration.
- No fabricated statistics. No vague citations ("studies show"). If referencing a fact, name the researcher, organization, or documented event.
- Maximum 2 ideas on the same theme.
- Maximum 2 ideas using the same type of analogy.
- Each idea is a single refutable thesis — not a list, not a direction, not an observation.

LANGUAGE AND JARGON RULES (MANDATORY)
Phrase every idea in the executive's domain vocabulary, NOT in the source domain's vocabulary.

- Transfer the mechanism, not the terminology. The causal structure crosses domains; the field-specific labels stay behind.
- Generic structural terms are welcome and should be used freely: "threshold", "feedback loop", "selection pressure", "cascade", "equilibrium", "signal-to-noise ratio". These are broadly understood and add precision.
- Specialized source-domain terms (e.g., "parasitemia", "actomyosin cross-bridges", "phenotypic plasticity") must be replaced with a description of what they DO, expressed in plain language from the executive's domain.
- If a specialized term genuinely has no plain-language equivalent AND adds precision, you may use it once with a parenthetical: "(i.e., [5 words max explanation])". This is a last resort, not a default.
- Test: give the idea to someone who has never heard of the source domain. They should understand it fully without the parenthetical.
- Ideas must NOT follow the "In [source domain], X happens. Therefore your business should Y" pattern. That framing puts translation work on the executive. The translation belongs here, in the generation step.

OFF-LIMITS TOPICS (do not generate ideas that are variations of these)
{brief.forbidden_topics, one per line}

OFF-LIMITS FRAMEWORKS
{list of decision frameworks already applied to this topic from the workspace decisions}

BISOCIATION DOMAINS — your idea generation fuel
For each domain below, its active principle describes the specific mechanism you must use.
The mechanism must be structurally embedded in each idea you generate from it — not mentioned in passing.

{domain_set YAML — each entry: name, specialist, active_principle}

AXIOM INVERSIONS
These are implicit assumptions embedded in the reference material. Flip them.

{list 5+ assumption/inversion pairs extracted from reference_text and brief}

Generate at least 3 ideas from these inversions.

OUTPUT FORMAT
Exactly 20 ideas. No more, no fewer.

## Idea 1
[2-4 sentences. Assertive. Phrased in the executive's domain vocabulary. Domain mechanism is structurally embedded but linguistically transparent — no field jargon unless unavoidable with parenthetical.]

## Idea 2
[...]

(continue through Idea 20)
```

**Subagent output**: 20 ideas as text. After all subagents complete, pool all ideas. Tag each with: `{domain_name, reference_label, raw_text}`. Assign idea_ids: `{reference_label}-{domain_name_slug}-{N}`.

Update TodoWrite: Step 3 completed.

---

## PHASE 3: Scoring (5-axis evaluation)

**Goal**: Score every generated idea on all 5 axes. Retain those above threshold.

Update TodoWrite: Step 4 in_progress.

**Run as a single LLM scoring call** to allow calibration across ideas. If total ideas exceed 80 (deep mode with many combos), split into batches of 40 and run in parallel.

### Scoring prompt

```
You are a structural idea evaluator. Rate each idea's POTENTIAL if fully developed — not its current wording quality.
A rough thesis with strong structural potential scores higher than polished text with weak substance.
Rate each idea on ALL FIVE axes independently.

AXIS 1 — Structural originality (weight 0.25)
Does the THESIS represent a genuinely new formulation — not just new packaging?
5 = This thesis, in this exact formulation, forces reconceptualization. Encountering it changes how you see the problem.
3 = Known angle with new framing. Someone in the field would recognize the underlying idea.
1 = Reformulation of standard advice or conventional wisdom.

AXIS 2 — Resistance to objection (weight 0.20)
Does the core claim hold against the STRONGEST plausible counterargument?
5 = The best counterargument attacks an assumption, not the mechanism. Core survives.
3 = Substance is recoverable with more precise wording, but current form is vulnerable.
1 = A single obvious objection collapses the idea entirely.

AXIS 3 — Thesis density (weight 0.20)
Can this be formulated as a single, directly attackable thesis statement?
5 = The idea IS a precise thesis. You could make a bet against it or design an experiment.
3 = Implicit thesis is recoverable. Translation required but substance is there.
1 = Observation or anecdote. No extractable thesis.

AXIS 4 — Concrete grounding (weight 0.20)
Does the idea reference a named mechanism, researcher, company, historical event, or verified phenomenon?
5 = Grounding is in the idea text or obviously findable with basic research.
3 = Grounding is possible but requires non-trivial investigation.
1 = Pure abstraction. No data, no history, no named phenomenon.

AXIS 5 — Cognitive load (weight 0.15)
Does this idea FORCE the reader to stop and reconstruct their model?
5 = Creates productive dissonance. The reader resists it, then can't un-see it.
3 = Mildly counter-intuitive. Worth a second read but doesn't reframe.
1 = Expected. Confirms what the reader already thinks.

WEIGHTED AGGREGATE
score = (orig × 0.25) + (resist × 0.20) + (thesis × 0.20) + (ground × 0.20) + (cogn × 0.15)

THRESHOLD
Retain ideas with aggregate ≥ 4.2.
If fewer than 3 ideas pass 4.2: lower to 4.0 and recount.
If still fewer than 3 pass 4.0: retain the top 3 by score regardless, and note "below quality threshold" next to each.

IDEAS TO SCORE
{numbered list of all pooled ideas with idea_ids}

OUTPUT FORMAT
For each idea, one table row:
| idea_id | orig | resist | thesis | ground | cogn | aggregate |
|---------|------|--------|--------|--------|------|-----------|

Then list passing ideas:
✓ {idea_id} — Score {X.XX} — {1 sentence: what structural quality earns this score}

No other commentary.
```

Parse: extract all 5 axis scores and aggregate per idea. Record `strongest_objection` for each passing idea from the scoring rationale.

Update TodoWrite: Step 4 completed.

---

## PHASE 4: LLM pre-curation (4 filters)

**Goal**: Apply the 4 Open Collider curation filters to all above-threshold ideas before showing the executive. This step cannot be skipped — it is what separates bisociation-based ideas from clever-sounding analogy.

Update TodoWrite: Step 5 in_progress.

### Curation filter prompt

```
You are a rigorous idea curator. Apply each filter strictly and independently.
This is adversarial curation — your job is to catch hollow ideas, not validate them.

FILTER 1 — Real collision?
Test: mentally remove all references to the source domain from the idea text. Does the idea change substantially?
PASS: The domain mechanism is structurally embedded — without it, the idea either doesn't hold or becomes a different idea.
FAIL: The domain is decorative. The insight stands alone regardless of the domain mention.

Discrimination example:
  FAIL: "Like bees finding flowers, make the product easy to discover." Without "like bees" this is just "make it easy to discover."
  PASS: "Price the product the way epidemiologists price herd immunity: set the threshold just above the adoption rate needed to make the problem self-reinforcing, not the rate that maximizes short-term revenue." Without the epidemiology frame, this idea is not recoverable.

FILTER 2 — Verifiable?
Test: Does the idea reference a named researcher, named mechanism, named company, named historical event, or a verified scientific phenomenon?
PASS: At least one concrete anchor exists or is obviously findable.
FAIL: "Research shows", invented statistics, "some companies have found", unnamed "leading organizations."

FILTER 3 — Non-trivial?
Test: Would a standard "give me 10 ideas for [objective]" prompt produce this idea or something structurally equivalent?
PASS: This idea requires the structural collision — standard prompting doesn't reach it.
FAIL: Standard advice with a domain label attached. Remove the domain; the advice is unchanged and familiar.

FILTER 4 — Project voice?
Test: Does this idea match the brief's objective, tone, and intended audience?
PASS: A reader of the original brief would recognize this as relevant and correctly framed.
FAIL: Generic advice any project in any industry could use.

IDEAS TO CURATE
{list of above-threshold ideas with full text and idea_ids}

OUTPUT FOR EACH IDEA
idea_id: {id}
collision: PASS | FAIL — {1 sentence reason}
verifiable: PASS | FAIL — {1 sentence reason}
nontrivial: PASS | FAIL — {1 sentence reason}
voice: PASS | FAIL — {1 sentence reason}
final: COLLISION_IDEA | INSIGHT_WITHOUT_COLLISION | REJECT

Classification:
- COLLISION_IDEA: passes all 4 filters
- INSIGHT_WITHOUT_COLLISION: fails Filter 1 only (decorative domain) but passes Filters 2, 3, 4
- REJECT: fails Filter 2, 3, or 4
```

After curation:
- COLLISION_IDEAS: primary bucket
- INSIGHTS_WITHOUT_COLLISION: secondary bucket
- REJECT: discarded silently

Update TodoWrite: Step 5 completed.

---

## PHASE 5: Executive review

**Goal**: Present curated ideas in a format that respects the executive's time. Lead with the BLUF. Show collision mechanism and next step per idea. Make love/like/skip easy.

Update TodoWrite: Step 6 in_progress.

**Presentation count**: Quick mode → top 5–7 ideas; Deep mode → top 8–12 ideas. Rank by aggregate score within each bucket.

### Output format

Do NOT open with "Here are your ideas." Lead with a one-line BLUF about what the collision session surfaced.

```
**[One sentence: the most striking structural insight from this session — not a list of topics.]**

---

### Collision ideas
*(Domain mechanism is structurally embedded — the insight requires the collision)*

**[1]** [Idea text — 2-4 sentences. Assertive. Phrased in the executive's domain vocabulary. No hedging. No source-domain jargon unless unavoidable with a parenthetical.]

Source: [Domain name] — [1 sentence in plain language describing the structural mechanism from that field, expressed in terms the executive would recognize. No domain jargon here either.]
Objection: [The strongest real counterargument. Stated honestly, not softened.]
Score: [X.X/5]
Next step: [Concrete action. Verb + deliverable + timing + owner. E.g.: "Test the pricing threshold with 3 enterprise prospects before Q3. Owner: you."]

---

**[2]** [...]

---

### Insights without collision
*(Strong ideas that emerged from the process; domain mention is supplementary, not structural)*

**[1]** [Idea text]
Objection: [...]
Score: [X.X/5]
Next step: [...]

---

### Domains used
[Domain family names with one-line description of each]

---

**Flag your reactions** (reply with idea numbers):
- `love [N,N]` — directionally right, develop it → saved as priority idea
- `like [N,N]` — interesting, save for later → saved as candidate idea
- `skip` or `done` — session logged, no ideas saved
- `more about [N]` — expand this idea fully
- `another round` — run a follow-up session (triggers deepen/refresh strategy)
- `save all` — save everything as liked

You can combine: "love 2, like 1 4, skip 3 5 6"
```

### Handling "more about [N]"

Expand the idea fully:
- Trace the domain mechanism through the specific reference text that generated it
- Develop the thesis: what would need to be true for this to work?
- Name 2-3 falsifying conditions
- Suggest a concrete way to test the core claim before committing resources

Do NOT generate more ideas during expansion. Keep discovery mode focused.

Update TodoWrite: Step 6 completed when flags are received.

---

## PHASE 6: Capture (vault persistence)

**Only proceed after the executive provides a flag response.**

Update TodoWrite: Step 7 in_progress.

### Step 6a: Determine paths

```
project_slug = brief.slug
session_number = tars-session-count + 1 (from project note) or 1 if new project
date = today YYYY-MM-DD
project_path = "contexts/ideation/{slug}/project.md"
session_path = "contexts/ideation/{slug}/session-{N:03d}.md"
ideas_dir = "contexts/ideation/{slug}/ideas/"
journal_path = "journal/{YYYY-MM}/{date}-ideation-{slug}.md"
```

### Step 6b: Write ordering (mandatory — follows core write ordering)

**1. Create/update project note (entity first)**

If new project:
```
mcp__tars_vault__create_note(
  path="contexts/ideation/{slug}/project.md",
  frontmatter={
    tags: [tars/ideation-project],
    title: "{subject}",
    tars-slug: "{slug}",
    tars-objective: "{brief.objective}",
    tars-constraints: ["{brief.constraints}"],
    tars-forbidden-topics: ["{brief.forbidden_topics}"],
    tars-reference-source-types: ["{list of source types used}"],
    tars-domain-families: [],    (populated in Phase 7)
    tars-session-count: 1,
    tars-last-session: "{date}",
    tars-status: active,
    tars-created: "{date}",
    tars-modified: "{date}"
  },
  body: "## Objective\n{brief.objective}\n\n## Context\n{brief.context}\n\n## What makes a good idea\n{brief.what_makes_good_ideas}"
)
```

If continuing project:
```
mcp__tars_vault__update_frontmatter(path, property="tars-session-count", value={N})
mcp__tars_vault__update_frontmatter(path, property="tars-last-session", value="{date}")
mcp__tars_vault__update_frontmatter(path, property="tars-modified", value="{date}")
```
Then append idea themes from this session to tars-forbidden-topics.

**2. Create idea notes (loved and liked only — skipped = discarded)**

For each loved/liked idea:
```
idea_file = "idea-{session_N}-{sequence}-{first-3-words-slug}.md"
path = "contexts/ideation/{slug}/ideas/{idea_file}"

(all wikilinks via mcp__tars_vault__format_wikilink before use)

mcp__tars_vault__create_note(
  path=path,
  frontmatter={
    tags: [tars/ideation-idea],
    title: "{first 8 words of idea text}",
    tars-project: "[[{project-path}]]",
    tars-session: "[[{session-path}]]",   (forward reference — session written next)
    tars-score: {aggregate_score},
    tars-flag: loved | liked,
    tars-collision-domain: "{domain name or empty}",
    tars-collision-mechanism: "{1-sentence mechanism in exec vocabulary, or empty}",
    tars-has-collision: true | false,
    tars-challenge: "{strongest objection}",
    tars-next-step: "{concrete next step}",
    tars-combo: "{reference_label}×{domain_name}",
    tars-linked-initiative: "[[{initiative-path}]]" if found in Phase 0,
    tars-linked-product: "[[{product-path}]]" if found in Phase 0,
    tars-created: "{date}",
    tars-modified: "{date}"
  },
  body: "{full idea text}\n\n## Collision mechanism\n{mechanism explained}\n\n## Strongest objection\n{challenge}\n\n## Next step\n{next-step}"
)
```

**3. Write session note (lives in contexts/ideation/{slug}/, not journal)**

```
mcp__tars_vault__create_note(
  path="contexts/ideation/{slug}/session-{N:03d}.md",
  frontmatter={
    tags: [tars/ideation-session],
    title: "Ideation: {subject} — Session {N}",
    tars-project: "[[{slug}]]",
    tars-session-number: {N},
    tars-date: "{date}",
    tars-mode: quick | deep | deepen,
    tars-strategy: fresh | deepen | refresh | combined,
    tars-domains-used: ["{list of domain family names}"],
    tars-combos-run: {count},
    tars-ideas-generated: {raw total},
    tars-ideas-passing-score: {count passing threshold},
    tars-loved-count: {count},
    tars-liked-count: {count},
    tars-skip-count: {count},
    tars-created: "{date}"
  },
  body: "{full Phase 5 output — all presented ideas with scores, domain list, brief summary}"
)
```

**4. Write thin journal entry (daily activity pointer)**

```
mcp__tars_vault__create_note(
  path="journal/{YYYY-MM}/{date}-ideation-{slug}.md",
  frontmatter={
    tags: [tars/journal, tars/analysis],
    tars-date: "{date}",
    tars-created: "{date}"
  },
  body: "Ideation session [[{session-path}]]: {combos} combos, {ideas-generated} raw ideas, {loved} loved, {liked} liked. Domains: {domain-family-list}."
)
```

**5. Append to daily note**

```
mcp__tars_vault__append_note(
  path="journal/{YYYY-MM-DD}.md",
  content="- Ideation [[{subject} Session {N}]] — {combos} combos, {loved} loved, {liked} liked"
)
```

**6. Write changelog entry**

```
mcp__tars_vault__append_note(
  path="_system/changelog/{YYYY-MM-DD}.md",
  content="ideate: session {N} for {slug} — {combos} combos, {loved+liked} ideas saved"
)
```

### Step 6c: Optional task extraction

For each loved idea whose `tars-next-step` passes the accountability test (concrete owner, verifiable completion):

Present: "Idea [N] has a concrete next step: '[next step]'. Create as a task? [Yes / No]"

If yes: create task note per `/tasks` protocol, linked via `tars-initiative: [[{initiative-path}]]` if applicable.

Update TodoWrite: Step 7 completed.

---

## PHASE 7: Domain history update

**Goal**: Update `tars-domain-families` on the project note so deepen and refresh strategies work in future sessions.

Update TodoWrite: Step 8 in_progress.

### Domain family structure (per entry in tars-domain-families)

```yaml
- family_name: "Evolutionary biology"
  sub_domains_used:
    - "Phylogeography"
    - "Syndromic surveillance"
  produced_loved: true
  mechanisms_extracted:
    - "threshold dynamics: adoption becomes self-sustaining above a critical mass"
  last_used: "2026-05-23"
```

### Update logic

For each domain family used in this session:
1. Find or create the entry in the list
2. Add new sub-specialties to `sub_domains_used` (deduped)
3. Set `produced_loved: true` if any loved idea came from this family
4. Extract mechanism text from loved ideas in this family; append to `mechanisms_extracted`
5. Update `last_used`

```
mcp__tars_vault__update_frontmatter(
  path="contexts/ideation/{slug}/project.md",
  property="tars-domain-families",
  value=[...updated list...]
)
```

Also update `tars-forbidden-topics` on the project note with idea themes from this session — prevents recycling in future sessions:
```
mcp__tars_vault__update_frontmatter(
  path="contexts/ideation/{slug}/project.md",
  property="tars-forbidden-topics",
  value=[...existing + new themes from this session's ideas (all ideas, not just loved/liked)...]
)
```

### Summary for the executive

```
**Session saved.** {loved+liked} idea(s) added to contexts/ideation/{slug}/ideas/

Next session recommendation:
```
(choose one:)
- If loved ≥ 2: "Deepen will explore new sub-specialties in [{family names that produced loved ideas}]. Refresh will find new disciplines with the same structural mechanism as '{mechanism summary}'."
- If loved = 0-1: "Next session will use fresh domains — the families tried this session didn't produce strong collisions. A new set will scatter wider."

To continue: `/ideate deepen` or just tell me to run another round.
```

Update TodoWrite: Step 8 completed.

---

## PHASE 0-SHORTCUT: Review mode

When `/ideate review [subject]` or "show my past ideas for X":

```
mcp__tars_vault__search_by_tag(tags=["tars/ideation-idea"], query="{subject}", limit=30)
```

Group results by project and session. Present:

```
## Ideation ideas: [subject]

### [Project name] — [N] sessions, [M] loved, [K] liked

Session [N] ([date]) — [mode], [domains]:
  ★ [Loved idea — first sentence]  (score: X.X | next step: ...)
  ○ [Liked idea — first sentence]  (score: X.X)
  ...

[[Link to session note]] | [[Link to project brief]]
```

If no results: "No ideation ideas saved for this topic yet. Start a session? [/ideate quick {subject}]"

---

## PHASE 0-SHORTCUT: Deepen mode

When `/ideate deepen [slug]` or "more ideas like the ones I loved":

1. Load the most recent active ideation project (or match to `slug` if provided):
   ```
   mcp__tars_vault__search_by_tag(tags=["tars/ideation-project"], limit=5)
   Sort by tars-last-session descending
   ```
   If multiple projects, present top 3 for the exec to select.

2. Read the project note. Load `tars-domain-families`, `tars-forbidden-topics`, `tars-session-count`.

3. Load loved ideas from prior sessions:
   ```
   mcp__tars_vault__search_by_tag(tags=["tars/ideation-idea"], query="{slug}", limit=20)
   Filter to tars-flag: loved
   ```

4. Present confirmation: "Continuing [[{project-name}]] — Session {N+1}. {K} loved ideas from prior sessions. Deepen strategy will explore new sub-specialties in [{families with loved ideas}] and refresh will find disciplines with the same mechanism. [Confirm / Change mode]"

5. Skip Phase 0 entirely. Use existing project brief. Run Phase 1 with deepen + refresh strategies.

---

## Self-evaluation

After delivering primary output, apply standard self-evaluation from `skills/core/SKILL.md`.

Additional ideation-specific signals:
- "These are too obvious" → next session needs more distant domains or higher scoring threshold
- "I've seen these before" → forbidden_topics list is incomplete; load more prior session outputs
- User immediately loves 5+ ideas → note the domain families as highly productive; flag for deepen next time

Queue any signals for the standard closing. Do NOT interrupt the review flow to surface them.

---

## Context budgets

| Phase | Budget |
|-------|--------|
| Phase 0: context loading | 3 parallel subagents; max 10 entity reads total across all three |
| Phase 1: domain generation | Main agent only; no vault reads |
| Phase 2: idea generation | 1 Task subagent per combo; each reads nothing from vault |
| Phase 3: scoring | Main agent; works from Phase 2 results only |
| Phase 4: curation | Main agent; works from Phase 3 results only |
| Phase 6: capture | Sequential writes per write ordering |
| Phase 7: domain history | 1-2 frontmatter updates on project note |

---

## Absolute constraints

- NEVER skip the active-principle format for domain narratives — topic keywords alone do not produce bisociation
- NEVER run Phase 2 idea generation in the main agent context — always isolated subagents via Task tool
- NEVER skip any of the 5 scoring axes
- NEVER skip any of the 4 curation filters
- NEVER omit forbidden_topics from subagent prompts — recycling prior ideas is the enemy of bisociation
- NEVER save ideas to vault without exec flagging (love/like/skip), except when exec says "save all"
- NEVER omit the collision mechanism explanation from Phase 5 output
- NEVER omit the concrete next step from Phase 5 output
- NEVER hand-form wikilinks — always call `mcp__tars_vault__format_wikilink`
- NEVER begin domain generation before the brief is confirmed in Phase 0
- ALWAYS update domain history (Phase 7) before closing the session
- ALWAYS present scores as quality signal, not primary ranking — lead with the idea text
- ALWAYS allow the exec to request "more about [N]" before flagging
- ALWAYS write the journal entry and changelog regardless of whether ideas were saved
- ALWAYS translate source-domain jargon into the executive's domain vocabulary — ideas must read as natively conceived in the exec's field, not as translations from a foreign discipline
