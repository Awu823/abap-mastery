---
description: Sử dụng workflow này khi cần phân tích tài liệu Functional Specification (FS) để tạo ra bản Technical Specification (TS) đầy đủ, chính xác và đủ chi tiết để workflow `/sap-dev-create-report` thực thi mà không cần tự thiết kế thêm.
argument-hint: <project> <fs-file-path> <package-name>
---

> **Claude Code note:** `[Skill: X]` below means invoke the `x` skill via the Skill tool (auto-discovered from `.claude/skills/x/`). Where a step needs an MCP tool not yet loaded, use `ToolSearch` first (see `sap-dev-rule.md` §9).

[ROLE & OBJECTIVE]
Act as an Expert SAP Solution Architect and Technical Analyst. Deeply read and analyze a Functional Specification (FS) document, then translate business logic, UI requirements, and data constraints into a Technical Specification (TS) strictly aligned with SAP ABAP Cloud and Clean Core architecture. The TS you produce is the ONLY input `/sap-dev-create-report` will read — it must be complete enough that create-report never has to guess or design on its own.

[INPUT DATA]
- Project: the target project name under `projects/` (rule §4). Resolve from the first argument or the user's prompt; if absent, ask ONE question before creating any file. The directory `projects/<project>/` must already exist (`/sap-project-init` otherwise). Read `projects/<project>/project.md` first — it supplies the default SAP system, package, and TR context. Every output path below lives under `projects/<project>/`.
- Functional Specification (FS): file(s) in `projects/<project>/fs_docs/`, or FS text pasted directly. Arguments: $ARGUMENTS

[GOVERNING RULES]
This workflow operates under the Iron Laws, Red Flags, and Token Efficiency rules in `sap-dev-rule.md` (§6-10). In particular: no TS handoff without passing the Verify Loop (Phase 5); progress updates use [Skill: caveman]; never re-print full drafts already saved to a file, reference the path instead.

[EXECUTION PROTOCOL — 6 PHASES]

## Phase 0 — Intake & Pre-processing

0.0 TASK LEDGER: Use [Skill: scratchpad] to create `projects/<project>/scratchpads/scratchpad_[ReportName].md` with the Ledger Format (TODO/DOING/DONE/FAILED) covering Phases 0-6. Update it immediately after each phase — it is the single source of truth for progress, not this conversation's history.

0.1 DOCUMENT PRE-PROCESSING: Dispatch `[Agent: consultant-executor]` with [Skill: document-markdown-converter] to convert binary FS files (PDF/DOCX/XLSX) in `projects/<project>/fs_docs/` into `projects/<project>/scratchpads/fs_markdown.md`. Skip if the FS is already plain text/Markdown. From here on, read `fs_markdown.md` only — never the original binary.

0.2 VISUAL EXTRACTION: If the FS contains images (UI mockups, flowcharts, Excel screenshots), dispatch `[Agent: consultant-executor]` with [Skill: fs-vision-extractor] to transcribe them into Markdown and append the result into `fs_markdown.md` under a clearly labeled heading (e.g. `## Extracted from Image: <name>`). Skip if the FS has no images.

0.3 DATA COMPLETENESS GATE (HARD GATE): Review `fs_markdown.md`. If the FS explicitly references fields/tables/requirements that live in an unprocessed image, an external link, or a table that failed conversion, STOP and ask the user to provide the missing information. Do not guess or use placeholder ranges (e.g. "Fields 1 to 39"). Do not proceed to Phase 1 until this gate passes.

## Phase 1 — Data Model Foundation (single dispatch — every later phase reuses this vocabulary)

1.0 DATA MODEL EXTRACTION + RELEASED CDS VALIDATION: Dispatch `[Agent: consultant-lead]` ONCE, naming all four sub-tasks in the same dispatch prompt to run in sequence inside that one agent — do not split into separate dispatches, (b)/(c) strictly need (a)'s output and (d) is cheap to run alongside them, so there is no parallelism to gain and only round-trip overhead to lose: (a) [Skill: fs-data-model-extractor] on `fs_markdown.md` → internal Data Model Draft (Base Views/Tables, Joins & Conditions, Key Fields, Hardcoded Filters, Output Fields); (b) [Skill: find-released-cds-view] on that draft → verify every source is a released Clean-Core-Level-A CDS view (S/4HANA Cloud Public), replacing any unreleased/internal table or view with the best released alternative matching grain and field coverage; (c) JOIN-TREE / RELATIONSHIP VALIDATION — when the model spans 2+ sources, run [Skill: cds-data-model-analysis]'s 5-step procedure on the draft: pin the report grain, each source's keys, every hop's link fields + cardinality (evidence-based, `[assumption]`-flagged where unverifiable), and the fan-out checklist — a to-many hop feeding a downstream aggregation must be restructured here, not discovered at build time; (d) PROCESS-DOMAIN SKILL CHECK — check whether any `sap-process-*` skill (business-process domain knowledge, `.claude/skills/sap-process-*/` — auto-discovered by description match against the FS content) is relevant to this FS's business domain, and invoke any that apply; if none apply, say so explicitly rather than skipping the check silently. Output: **Verified Data Model** — including the relationship map + join tree from (c) — the field/source vocabulary every later phase must reuse verbatim (identical field and view names) to avoid drift. Persist it as a `## Verified Data Model` section in `projects/<project>/scratchpads/scratchpad_[ReportName].md`, plus a `## Relevant Process-Domain Skill(s)` section naming exactly which `sap-process-*` skill(s) applied from (d) (or "None") — Phase 2's dispatched agents read this file, not conversation history, and reuse this list instead of re-discovering it themselves (this is the one and only domain-discovery pass — keeps token cost to one check instead of one per Phase-2 dispatch).

## Phase 2 — Domain Analysis (parallel via dedicated subagents)

2.A/2.B/2.C each take `fs_markdown.md` + the `## Verified Data Model` and `## Relevant Process-Domain Skill(s)` sections of the scratchpad ledger as read-only input and produce one independent draft. Dispatch all three via `[Agent: consultant-lead]` (parallel Task calls in one message, `subagent_type: consultant-lead`, no `isolation: "worktree"`); each dispatch prompt must name the one skill to invoke, the input path(s), and its own output path — read-only input, write only its own draft, no shared state. 2.B's dispatch prompt additionally names any `sap-process-*` skill(s) listed in `## Relevant Process-Domain Skill(s)` and instructs it to read that skill's `references/deep-dive.md` for functional-consulting depth (e.g. partner determination, pricing, planning strategy) before finalizing — this is where that depth changes business-logic correctness the most; 2.A/2.C may reference the same skill's base `SKILL.md` content (e.g. its Integration Points section) if directly relevant, but do not also read its `references/deep-dive.md` unless the FS's own UI/integration requirement genuinely needs that depth.

Threshold (starting heuristic — tighten once real dispatch-timing data exists): dispatch sequentially instead of in parallel only if the Verified Data Model lists fewer than ~15 output fields total AND `fs_markdown.md` is under ~2 pages — below that size, three parallel dispatches cost more in spin-up overhead than they save. At or above the threshold, always dispatch in parallel — the result is identical content either way, only faster.

2.A UI/UX ANALYSIS: [Skill: fs-fiori-ui-elements-mapper] → UI Layout Draft (Selection Fields, Line Items, Sorting/Grouping, Object Page Facets). Output: `projects/<project>/scratchpads/draft_ui_[ReportName].md`.

2.B BUSINESS LOGIC EXTRACTION: [Skill: fs-logic-behavior-translator] → Business Logic Draft (Report Type, CDS-level derived fields, Virtual Elements/ABAP-level complex logic, Actions/Determinations, Clean Core violations + released replacements, Authorization Check). This skill already mandates MCP-verified replacements for any unreleased API it flags — do not skip that check. Output: `projects/<project>/scratchpads/draft_logic_[ReportName].md`.

2.C INTEGRATION & API ANALYSIS: [Skill: fs-integration-api-analyzer] → Integration Draft (Integration Pattern, OData Service Model, API Style Compliance, Field Mapping Table, Security/Auth). If the FS has no integration/interface requirements, output exactly "N/A — FS has no integration requirements" rather than skipping the step silently. Output: `projects/<project>/scratchpads/draft_integration_[ReportName].md`.

2.D RECONCILIATION: Read back each of the three draft files yourself (`sap-dev-rule.md` §12 — a dispatch's completion message is not sufficient evidence). To keep this cheap on context, read only each file's **Field Name Index** (the flat list at the very top of the file) first and cross-check those names against the Verified Data Model; open the full draft body only for a file whose Index shows a name that doesn't match, to get the context needed to resolve it. List any mismatch as a Conflict and resolve it (align naming, or return to Phase 1 if a field is genuinely missing) before proceeding to 2.E.

2.E SCOPE CHALLENGE ([Skill: lean-abap] rungs R0-R3 — the only place an FS requirement may be challenged): From the reconciled drafts, list FS requirements whose cost the stated business need does not justify, or that duplicate something already available — a standard SAP Fiori app / released CDS field / existing Z-object (R1-R2), or a declarative CDS/RAP feature that replaces custom logic the FS implies (R3). For each: FS reference, why challenged, smaller alternative, what the user loses if accepted. Present them to the user in ONE message and WAIT; record each decision (Keep / Replace with alternative / Cut) with the user's own words in TS §12. No challenge → write "None" in TS §12 and continue without asking. Never drop, merge, or shrink an FS requirement without an explicit written user decision — a challenge the user has not answered means Keep. `/sap-dev-create-report` later builds only what the TS says, so this is the last point where scope can shrink.

## Phase 3 — Architecture & Coding Implementation Plan (the phase create-report depends on most)

3.0 ARCHITECTURE BRAINSTORM: Only when the Business Logic Draft contains genuinely complex/ambiguous logic (e.g. multi-level fallback chains, period-anchor balance calculations, a real choice between CDS Virtual Element vs. Behavior Pool vs. Custom Entity + Query Provider), generate 2-3 candidate architectures with explicit trade-offs (Clean Core compliance / Performance / Maintainability), pick one, and state why. For straightforward reports with no such ambiguity, skip the multi-option comparison and go straight to the obvious design — do not manufacture false choices just to seem thorough.

3.1 CODING IMPLEMENTATION PLAN (the section `/sap-dev-create-report` depends on entirely): using [Skill: naming-convention] for every object name, produce a complete table of every object to be created:

| # | Object Name | Type | Purpose | Source/Base + Join/Association | Field Mapping (which TS output field(s) it delivers) | Corresponding create-report Step |
|---|---|---|---|---|---|---|

This table must cover 100% of what create-report's Steps 1-7 will need (Interface View, DCL, Behavior Definition, Behavior Pool Class, Projection View, Metadata Extension, Projection Behavior, Service Definition/Binding) — enough that create-report performs zero independent design or lookup.

## Phase 4 — Assemble TS

4.0 Merge every draft and the Coding Implementation Plan into the full TS using the template in [OUTPUT FORMAT] below.

## Phase 5 — Verify Loop (max 3 automatic iterations)

5.0 Cross-check the TS draft against `fs_markdown.md`:
- 100% of FS fields are present with exact names (no placeholders) — except fields the user explicitly cut in TS §12 (Scope Decisions); every 2.E challenge has a recorded user decision.
- Every field has documented source + derivation logic.
- Every row in the Coding Implementation Plan has a clear source/target and references no field absent from the Verified Data Model.

PASS → Phase 6. FAIL → fix the specific gap in the phase it belongs to, then re-run this gate. Log each attempt in the Scratchpad ledger's Verify Attempts table (see Scratchpad skill) so the 3-iteration cap is tracked, not just remembered. After 3 failed iterations, STOP — list the exact unresolved blockers and ask the user instead of continuing to guess (Red Flags, `sap-dev-rule.md` §7).

## Phase 6 — Handoff

6.0 Save the TS, mark the ledger fully DONE. If the session ends here before `/sap-dev-create-report` runs, use [Skill: handoff] to summarize state for the next session.

[OUTPUT FORMAT — CRITICAL]
Save the final TS as Markdown directly under `projects/<project>/technical_specifications/TS_[ReportName].md` (relative to workspace root). Do not add introductory or concluding remarks outside the template. Use CamelCase for `[ReportName]`.

```
# Technical Specification: [ReportName]

## 1. Tổng Quan (Overview)
[Mục đích report, đối tượng sử dụng, phạm vi nghiệp vụ — bám sát FS, 1 đoạn ngắn]

## 2. Tham Số & Layout
Package Name: [Target Package]
Transport Request: [Target Transport Request]
Report Type: [Read-only OR Transactional/Actionable — determined strictly from FS]

## 3. Data Model Architecture
- Base Views/Tables: [List all source views/tables with their specific purpose]
- Joins & Conditions: [Exact ON conditions]
- Key Fields: [List]
- Hardcoded Filters: [List]
- Output Fields: [MANDATORY: 100% of FS fields, each with its exact source/derivation logic]

## 4. UI & Layout (Fiori Elements)
- Selection Fields (Filters): [List, mark mandatory ones]
- Line Items: [100% of display fields in sequence, mapped to Output Fields above]
- Default Sorting/Grouping: [List]

## 5. Business Logic & Behavior
- Derived/Calculated Fields (CDS): [List]
- Complex Logic (Virtual Elements / ABAP): [List]
- Authorization Check: [chi tiết tập trung tại §10 — không liệt kê lại ở đây để tránh lệch 2 nơi]

## 6. Integration & API
[From Phase 2.C — or "N/A — FS has no integration requirements"]

## 7. Tính Năng & Hành Vi (Features & Actions)
[Buttons/links/actions and the logic each triggers, if the FS specifies any — otherwise "None"]

## 8. Print Form
[Brief description only if the FS requires printing. Note: handled by a separate print-form flow, out of scope for this report engine]

## 9. Coding Implementation Plan
[Full table from Phase 3.1]

## 10. Authorization Check
[Auth objects / PFCG / DCL requirements]

## 11. Additional Requirements
- [Naming conventions beyond the default, if the FS specifies any]
- [Extra UI/Action requirements, e.g. custom Excel export]

## 12. Scope Decisions (Scope Challenge — Phase 2.E)
| # | FS Reference | Challenge | Smaller Alternative | User Decision (Keep / Replace / Cut) + user's words |
|---|---|---|---|---|
[Or "None" — no FS requirement was challenged]
```
