<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# Phase 6: Token-efficiency audit (v3.3)

Research deliverable. No production code or skill content was modified. Each finding cites file:line and provides an estimated saving so AJ can decide which to apply.

Token estimates use 1.3 tokens / word as a conservative average for English markdown — actual tokenization will vary by ±15%.

---

## 1. Always-loaded surface (every session pays this)

| File | Words | ≈ Tokens | Notes |
|------|------:|--------:|-------|
| `CLAUDE.md` | 1,666 | 2,165 | Project-level instructions, always injected |
| `skills/core/SKILL.md` | 5,139 | 6,680 | Marked "always loaded" in CLAUDE.md skill table |
| SessionStart hook output | 0–400 | 0–520 | Banners only when conditions trip; idle case is empty |
| **Always-on baseline** | **6,805+** | **8,845+** | Before any skill is invoked |

For comparison, a fresh Claude Code session without TARS starts at roughly 2,500 tokens of system prompt. TARS triples that baseline. This is the largest single optimization target.

## 2. Per-skill load (paid only when invoked)

| Skill | Words | ≈ Tokens | Typical invocation frequency |
|-------|------:|--------:|------------------------------|
| `meeting` | 4,543 | 5,906 | Daily for users with recordings; tier-3 only |
| `welcome` | 4,188 | 5,444 | Once per vault (first run + relocate) |
| `learn` | 3,745 | 4,869 | A few times per week |
| `briefing` | 3,272 | 4,254 | Daily + weekly |
| `maintain` | 3,285 | 4,271 | Weekly cron + on-demand |
| `tasks` | 2,935 | 3,816 | Daily |
| `think` | 2,711 | 3,524 | A few times per week |
| `answer` | 2,276 | 2,959 | Multiple times per session |
| `lint` | 2,117 | 2,752 | Nightly cron + on-demand |
| `create` | 1,807 | 2,349 | A few times per week |
| `initiative` | 1,215 | 1,580 | Weekly |
| `communicate` | 835 | 1,086 | Daily |

**Frequency-weighted top consumers** (tokens × estimated weekly invocation count): `briefing` (≈30k/week), `answer` (≈30k/week), `tasks` (≈19k/week), `learn` (≈15k/week). Optimizing the always-loaded surface beats optimizing any single skill.

---

## 3. Findings

### Finding 1 — Duplication: MCP tools table appears in both CLAUDE.md and core skill
**Severity:** High (always-loaded path)
**Estimated saving:** ~250 words / 325 tokens

`CLAUDE.md` lines 40–58 and `skills/core/SKILL.md` lines 44–60 each render the full `mcp__tars_vault__*` tool inventory as a markdown table. The CLAUDE.md version lists 15 tools with one-line purposes; the core version has 14 tools with purpose + "Replaces" columns. They are 90% the same content.

**Recommendation:** keep the version in `skills/core/SKILL.md` (richer), reduce the CLAUDE.md version to a 3-line pointer:
```
All vault writes flow through the `tars-vault` MCP server's `mcp__tars_vault__*` tools.
The full inventory and purpose of each tool lives in `skills/core/SKILL.md` §Write interface.
Never invoke `obsidian-cli` directly from skill bodies.
```
Risk: low. Both files load on every session, so no information is lost.

### Finding 2 — Duplication: "Key constraints" / "Universal constraints"
**Severity:** High (always-loaded path)
**Estimated saving:** ~240 words / 312 tokens

`CLAUDE.md` lines 201–219 ("Key constraints") and `skills/core/SKILL.md` lines 552–569 ("Universal constraints") enumerate the same non-negotiable rules with slightly different wording. CLAUDE.md says "See `skills/core/SKILL.md` for full details" and then proceeds to list them anyway.

**Recommendation:** in CLAUDE.md, replace the 15-item enumeration with a 3–5 line summary that names the categories (write interface, prefix, provider-agnostic, ask-don't-assume, durability/accountability tests) and points to the core skill for the full text. The full enumeration in `skills/core/SKILL.md` is the authoritative source.

Risk: low — every session loads both files. No information lost.

### Finding 3 — Routing tables overlap
**Severity:** Medium
**Estimated saving:** ~150 words / 195 tokens

`CLAUDE.md` lines 227–242 and `skills/core/SKILL.md` lines 159–184 both contain a routing table mapping intent → skill. CLAUDE.md's is shorter (15 rows) and core's is longer (25 rows). They serve the same purpose.

**Recommendation:** Drop the routing table from CLAUDE.md entirely; the one in `skills/core/SKILL.md` is more complete and core is always loaded. Leave a one-line pointer in CLAUDE.md.
Risk: low — same reasoning as above.

### Finding 4 — Stale documentation describing removed features
**Severity:** Medium (correctness, not token-efficiency)
**Estimated saving:** N/A — this is a quality regression, not bloat

Phase 4 removed the casual/standard engagement-mode bifurcation, but five files still describe casual mode as a live feature:

- `docs/CATALOG.md:69` — "engagement-mode toggle (`standard` vs `casual`)"
- `docs/GETTING-STARTED.md:47, 52, 75` — full "Engagement modes" section
- `docs/ARCHITECTURE.md:255, 260` — "Engagement modes (`standard` | `casual`)"
- `CHANGELOG.md:18, 23, 24, 34, 46` — v3.2.0 release notes describe casual mode in present tense
- `templates/personas/README.md` — already cleaned in P4

**Recommendation:** Defer to Phase 7 (release prep). The CHANGELOG entries for v3.2.0 should stay as-is (they correctly describe what shipped at the time); a new v3.3.0 entry should mark casual mode as removed. The `docs/` files need editing to describe the graceful-degradation tier model from Phase 4.

This is not a token-efficiency win, but it's the highest-impact quality issue uncovered by the audit.

### Finding 5 — Vault structure tree is verbose but high-value
**Severity:** Low (defensible bloat)
**Estimated saving:** ~150 words / 195 tokens IF compressed

`CLAUDE.md` lines 78–178 render the full vault directory tree with per-folder descriptions and file-level inline comments. ~100 lines, ~600 words.

**Recommendation:** Keep as-is. The agent uses this as a structural map when deciding where to write notes. Compressing it (e.g. dropping the inline file-level comments) would force more `Read` calls during routine work, which costs more tokens than the static text saves. Net negative if changed.

### Finding 6 — Self-evaluation rewrite (P5) added ~280 words to core skill
**Severity:** Low (intentional, value-positive)
**Estimated saving:** N/A — this is recently-added intentional content

The Phase 5 self-evaluation protocol added detailed detection signals, closing-question protocol, and deduplication rules to `skills/core/SKILL.md`. This is the largest recent addition to the always-loaded surface (~280 words / 365 tokens).

**Recommendation:** Keep as-is. The protocol's value depends on the agent following it precisely; abridging it risks the silent-write-mid-task regression that P5 was designed to prevent.

### Finding 7 — Banned phrases table
**Severity:** Low
**Estimated saving:** ~80 words / 105 tokens

`skills/core/SKILL.md` lines 119–134 list 12 banned phrases with a "Why" column. The "Why" column repeats "LLM marker" four times and "Corporate jargon" twice.

**Recommendation:** Group by category to remove the redundant "Why" repetition. Estimated saving is small but trivially safe.

### Finding 8 — Decision frameworks catalog
**Severity:** Low (rarely consulted)
**Estimated saving:** ~200 words / 260 tokens IF moved

`skills/core/SKILL.md` lines 499–533 catalog 12 decision frameworks (Working Backwards, Cynefin, Pre-Mortem, etc.). Only `/think` actively uses these; everything else loads them anyway because core is always-loaded.

**Recommendation:** Move the framework catalog to `skills/think/manifesto.md` (already loaded by `/think`). Leave a one-line pointer in core. Risk: low — only `/think` consults these by name.

### Finding 9 — Hooks output is appropriately conditional
**Severity:** Informational
**Estimated saving:** N/A — already optimal

`hooks/session-start.py` produces 0-token output when no banners trip. Banners only fire on actionable conditions (unexpanded env, worktree, install mismatch, stale registry, expiring CronCreate jobs, pending migrations). This is the right shape — don't change.

### Finding 10 — Persona seeding via templates/personas is efficient
**Severity:** Informational
**Estimated saving:** N/A

The seven persona templates (~250 words each) are read once during `/welcome` and then never again — their effects flow into `_system/config.md` as small `tars-*` properties. Zero ongoing token cost. No action needed.

---

## 4. Recommended action plan

If AJ wants to act on this audit, the highest-value, lowest-risk sequence is:

1. **Findings 1, 2, 3** (CLAUDE.md duplication) — single edit pass on `CLAUDE.md`. Estimated saving: ~640 words / **~830 tokens off every session baseline** (≈9% reduction in always-on surface).
2. **Finding 4** (stale docs) — bundle into Phase 7 release prep. Quality fix.
3. **Finding 8** (frameworks catalog move) — single edit pass across `skills/core/SKILL.md` and `skills/think/manifesto.md`. Estimated saving: ~260 tokens off every session baseline.
4. **Finding 7** (banned-phrases table) — trivial, ~105 tokens, defer or skip.

Total achievable saving on always-on surface (1+2+3+8+7): **~1,200 tokens per session**, or ~14% reduction.

## 5. Explicitly out of scope

The following were considered and rejected as either unsafe or net-negative:

- Compressing the vault structure tree (Finding 5) — would force more `Read` calls.
- Abridging the self-evaluation protocol (Finding 6) — would re-introduce the bug P5 fixed.
- Compressing routing rules / signal table — depends on precise wording for correct triage.
- Moving the universal constraints out of CLAUDE.md entirely — would require ordering guarantees on which file loads first.
- Compressing per-skill SKILL.md files — high blast radius, low frequency-weighted return.

## 6. Methodology notes

- Word counts via `wc -w`. Token estimates use 1.3 tokens/word.
- Frequency weighting is qualitative, based on typical executive-assistant workflows.
- Duplication identified by section-header matching and line-by-line comparison. Not exhaustive; further duplication may exist between sibling skills (e.g. `briefing` and `answer` both describe vault search; not yet examined).
- This audit covers v3.3 head as of commit `a6f16f4` (Phase 5 complete).
