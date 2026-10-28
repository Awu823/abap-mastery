---
name: activation-guard
version: 1.0
description: After creating, editing, or deleting any SAP object (CDS view, DDIC object, BDEF, class, service definition/binding), verify it is genuinely active with zero unresolved errors/warnings AND that no other object depending on it broke as a side effect. Use immediately after every "Push → Activate" (or delete) step in any workflow that mutates SAP system objects, before marking that step DONE in a build ledger — this is what stops a chain reaction of activation failures propagating through Steps N+1, N+2...
---

# Activation Guard

## Why this exists

"Activated" is not "correct," and "correct in isolation" is not "correct in context." Two failure modes cause cascades across a sequential RAP/API build:

1. An object activates with a **warning that actually matters** (silently treated as "unavoidable" without real assessment), or the tool reports success while the object is still inconsistent server-side.
2. An object built **earlier** in the same ledger gets modified later (e.g. going back to fix Step 1's Interface View after Step 3's Behavior Definition already built on top of it) — and nobody re-checks whether that earlier, already-DONE object is still valid.

Either one produces exactly the symptom this skill exists to catch: object N looks fine, but N+1 or N-1 quietly breaks.

## When to run

Immediately after every DEPLOY & ACTIVATE (or DELETE) of any SAP object, in any workflow — `/sap-dev-create-report`, `/sap-dev-create-transactional-app`, `/sap-dev-api-inbound`, `/sap-dev-api-outbound`, `/sap-dev-bug-fix`, or any ad-hoc object change — before that workflow marks the corresponding ledger row DONE and moves on.

> Tool note: examples below use `mcp__sap_bmw_dev__SAP` as the connected ADT/system-execution tool. If a different MCP server is connected, use `ToolSearch` to find its equivalent action (`sap-dev-rule.md` §9) — the 3 gates below are the requirement, not the specific tool call syntax.

## Protocol — 3 gates, all must pass before DONE

### Gate 1 — Full Activation Log Capture (never trust a boolean)

- Capture the COMPLETE activation result — every message, not just top-line pass/fail.
  `SAP(action="edit", target="ACTIVATE", params={"object_url": "...", "object_name": "..."})`
- Classify every message:
  - **Error** → hard stop. Fix and retry Gate 1 before moving to Gate 2.
  - **Warning** → do NOT default to "unavoidable." Assess it against strict(2)/Clean Core (`sap-dev-rule.md`). Only accept it as unavoidable if fixing it is genuinely impossible or out of the TS/FS's scope — and say so explicitly, quoting the exact warning text. A warning dismissed without that assessment is an unverified claim per `sap-dev-rule.md` §8/§11.
- If any doubt remains about whether an error was fully cleared, re-run an explicit syntax check rather than re-trusting the activate response:
  `SAP(action="analyze", params={"type": "syntax_check", "object_url": "...", "content": "..."})`

### Gate 2 — Confirmed Active State (don't trust the tool's return message alone)

- A tool can report "success" while the object is still flagged inactive/revised server-side (e.g. a downstream inconsistency). Independently confirm:
  `SAP(action="analyze", params={"type": "inactive_objects"})`
- The object you just touched must NOT appear in that list. If it does, treat it exactly like a Gate 1 error — diagnose the real message behind it, fix, re-activate, re-run both gates.

### Gate 3 — Ripple / Cross-Impact Check (the gate most builds skip entirely)

This is what actually prevents "N+1 breaks because N changed."

- Get the list of objects that DEPEND ON (are downstream of / reference) the object you just touched — not what it depends on:
  - CDS view: `SAP(action="analyze", params={"type": "cds_impact", "cds_view": "<name>"})` or `SAP(action="read", target="CDS_DEPS <name>")`
  - Class/program: `SAP(action="analyze", params={"type": "callers", "object_uri": "..."})`
  - Broader multi-hop impact: `SAP(action="analyze", params={"type": "impact", "object_type": "...", "object_name": "...", "max_depth": 3})`
- **This matters most when the object you just touched is a fix/edit to something already built EARLIER in this same ledger.** Cross-check every dependent that is ALSO already in this ledger's scope: is it still active with no new error? Re-run Gate 1 + Gate 2 on each one that's downstream and already marked DONE.
- If a previously-DONE ledger row now fails because of this change, do not silently re-fix it and move on — mark it `REGRESSED` in the ledger first (see [Skill: scratchpad] Ledger Format), noting which step caused it, THEN fix it in dependency order, then flip it back to `DONE` only once it re-passes all 3 gates.
- If the connected tool has no impact/where-used capability for this object type, do not silently skip this gate — record in the ledger: "Ripple check unavailable for this object type via the connected tool; dependents not automatically re-verified" so the gap is visible, not hidden.

## Ledger integration

Only mark a ledger row `DONE` after all 3 gates pass. A regression found by Gate 3 goes to `REGRESSED`, not a fresh generic `FAILED` — the distinct status is what makes the cascade visible to a human skimming the ledger later, instead of looking like an unrelated new failure.

## What this replaces

Any workflow step that previously said just "Execute: Lint → Push → Activate" now reads "Execute: Lint → Push → Activate → [Skill: activation-guard]." A bare "Activated" claim without having run all 3 gates is not sufficient completion evidence.
