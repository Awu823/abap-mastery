---
name: scratchpad
version: 1.0
description: Uses a persistent scratchpad file to plan, draft, and track complex or multi-step/multi-session work — including a status ledger and verify-loop attempt counters — before committing changes to the main codebase; use when a task is complex enough to need an explicit plan or may span multiple steps or be interrupted/compacted mid-way.
---

# Scratchpad

**Role:** Structured Thinker & Work Organizer

**Description:** Utilizes a persistent artifact or scratch file to meticulously plan, track, and draft work before committing changes to the main codebase.

## Instructions
1. Before starting a complex task, create or open a scratchpad file under the active project's `projects/<project>/scratchpads/` (rule §4 — fixed per-project location so any later session/agent can find it; workflows may specify an exact filename). If no project is resolved yet, resolve it first (argument → ask) — never write a project-less scratchpad.
2. Outline the step-by-step implementation plan within the scratchpad.
3. Draft code snippets, queries, or API payloads in the scratchpad for validation.
4. Use the scratchpad as a working memory space to keep track of variables, file paths, and intermediate states.
5. Only move code from the scratchpad to actual source files once confident in the logic.

## Ledger Format (multi-step / multi-session workflows)

When a workflow spans many steps or may be interrupted/compacted mid-way, use the scratchpad as a **progress ledger** instead of free-form notes. This is the single source of truth for "what's done" — re-read it instead of guessing from memory after a context reset.

```markdown
# Ledger: [ReportName]

| # | Item | Status | Notes/Evidence |
|---|------|--------|-----------------|
| 1 | Data Model Draft | DONE | ... |
| 2 | ZR_Invoice (Interface View) | DOING | activation pending |
| 3 | ZC_Invoice (Projection) | TODO | |
```

Status values: `TODO` (not started), `DOING` (in progress), `DONE` (completed + verified), `FAILED` (attempted, blocked — note why), `REGRESSED` (was DONE, then broken as a side effect of a later step — note which step caused it; see [Skill: activation-guard]). Update the row immediately when status changes; do not batch updates at the end.

## Verify-Loop Attempt Counter (for bounded retry gates, e.g. "max 3 iterations")

Any phase with a capped retry loop tracks its attempts in the same ledger file, in a separate table:

```markdown
## Verify Attempts

| Gate | Attempt # | Result | Evidence |
|------|-----------|--------|----------|
| TS Verify Loop | 1 | FAIL | field X missing source |
| TS Verify Loop | 2 | PASS | cross-checked against FS §4.2, all fields matched |
```

Increment `Attempt #` every time the gate re-runs — do not rely on remembering the count from conversation history, especially across a context compaction. When `Attempt #` reaches the workflow's stated cap without a PASS, stop and escalate per that workflow's rule; do not start another attempt without the user's explicit go-ahead.
