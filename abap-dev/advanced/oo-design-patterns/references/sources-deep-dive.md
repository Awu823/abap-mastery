# Sources — Deep-Dive Research Trail (oo-design-patterns)

Research conducted 2026-07-14 for the ABAP dev skill enrichment initiative Phase 2 (`artifacts/scratchpads/scratchpad_abap-dev-skill-enrichment.md`). `sap-docs-extend-mcp` unavailable for this entire session, not retried — fell back to `curl`-fetching the official SAP-samples cheat sheets directly, same method the Phase 1 pilot used.

## Primary sources retrieved

- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/34_OO_Design_Patterns.md` (13,498 lines) — the direct topical match named in the task brief. Read the table of contents in full, then the "Singleton" (line 11419), "Factory Method" (6878), "Constructor Injection" (339, under "ABAP Unit Test Double Injection Techniques"), "Strategy" (11965), and "State" (11633) sections in detail. Used for the Singleton and Factory skeletons directly; the Strategy/State skeleton in the deep-dive is a generic compression of the shared interface+concrete-class+context shape both sections independently confirm, not a verbatim copy of either worked example (both examples in the source are calculator/arithmetic demos; the deep-dive uses a pricing-strategy naming to match this workspace's domain instead, without changing the mechanics).
- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/33_ABAP_Release_News.md` (8,016 lines) — grepped for `RAP business event`, `RAP event`, `RAISE ENTITY EVENT`, and `FOR ENTITY EVENT`, using the same line-number-to-nearest-preceding-`Release NNN (QQQQ)`-header script as the other two drafts in this batch.

## Cross-checked against this workspace's existing files

- `.claude/skills/oo-design-patterns/SKILL.md` — read in full. This deep-dive deliberately does not expand any pattern beyond the 4 the SKILL.md body itself already flags as needing ABAP-specific realization notes (Singleton, Factory, Strategy/State, Observer) — the other 9 patterns in the SKILL.md's table are left untouched, per the task's explicit instruction not to turn this into a GoF cookbook.
- `.claude/skills/rap-business-events/SKILL.md` and its `references/event-code-examples.md` — read to confirm the exact `RAISE ENTITY EVENT zr_bo~event_name FROM VALUE #( ... )` and BDEF `event <name>;` syntax already verified and in use elsewhere in this workspace, rather than re-deriving/re-fetching it from the RAP cheat sheet a second time. **Self-caught error during drafting**: the first draft of the Observer section wrote `%tky = travel-%tky` in the `RAISE ENTITY EVENT ... FROM VALUE #( ... )` clause and `FOR ENTITY EVENT travel_created OF zr_travel` for the local handler method signature — both invented from memory/pattern-matching against EML's `%tky` convention rather than checked. Reading `event-code-examples.md` (lines 53–55 and 90–96) showed the actual verified syntax uses `%key = travel-%key` inside `RAISE ENTITY EVENT ... FROM VALUE #( ... )` (not `%tky`), and the handler method signature is `METHODS on_travel_created FOR ENTITY EVENT travel_created FOR Travel~travel_created.` (not `OF zr_travel`). Corrected in the deep-dive before finalizing — flagging here per the workspace's radical-honesty/no-fabrication rule and the explicit warning in this task's brief about exactly this failure mode.

## Verified release-number claims

| Finding | Release (quarter) |
|---|---|
| RAP Business Events — "native support for event-driven architecture" (origin of the capability, incl. `RAISE ENTITY EVENT`) | 789 (2208 / 2022 Q3) |
| `METHODS ... FOR ENTITY EVENT` / `FOR EVENTS OF` local event-handler-class additions, `CL_ABAP_BEHAVIOR_EVENT_HANDLER` | 792 (2305) |

## Manager correction (2026-07-14, applied before integrating into live content)

The draft version of this file (and `references/deep-dive.md`) originally labeled release 789/2208 as "2022 Q2", reusing a label already used elsewhere in the Phase-1 pilots at the time of drafting. A separate post-pilot review found the pilots' own `08`-suffix releases had been mislabeled (the correct SAP `YYMM`→quarter mapping is `02`→Q1, `05`→Q2, `08`→Q3, `11`→Q4 — a fixed formula). Corrected here and in `deep-dive.md`: 789 (2208) is 2022 **Q3** (was Q2). Release 792/2305 has no quarter label attached (correctly cited bare, as originally drafted).

## Why no Version Safety entries for Singleton/Factory/Strategy/State

`CREATE PRIVATE`, interfaces, class inheritance, and `CLASS-DATA` are core ABAP Objects constructs with no matching entries anywhere in `33_ABAP_Release_News.md`'s "ABAP for Cloud Development" section (grepped `CREATE PRIVATE`, found no "new addition"-style entry — it's foundational ABAP Objects syntax, older than the entire Cloud documentation window). Per the task's explicit instruction ("only if you found genuine release-gated findings — don't force one"), no table row was manufactured for these; the one genuine finding (RAP business events, above) is the only Version Safety content in this deep-dive, and it's tied directly to the Observer section rather than being a generic disclaimer.
