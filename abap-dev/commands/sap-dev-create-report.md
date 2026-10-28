---
description: Sử dụng workflow này khi người dùng yêu cầu tạo mới report dựa trên ABAP RAP Model, đọc Technical Specification (TS) do `/sap-dev-fs-analytic` sinh ra và triển khai đúng theo Coding Implementation Plan trong TS — không tự thiết kế hay tự tìm kiếm thêm thông tin ngoài TS.
argument-hint: <project> <package> <transport-request> <ts-file-path>
---

> **Claude Code note:** `[Skill: X]` below means invoke the `x` skill via the Skill tool (auto-discovered from `.claude/skills/x/`). Where a step needs an MCP tool not yet loaded (e.g. an ADT/system-connection tool), use `ToolSearch` first (see `sap-dev-rule.md` §9).

[ROLE & OBJECTIVE]
Act as an Expert SAP ABAP Cloud Developer with SYSTEM EXECUTION PRIVILEGES. CREATE, VALIDATE, and ACTIVATE the complete ABAP RAP Model artifacts described in the TS's Coding Implementation Plan (§9). Use your equipped skills (rap, cds-view-entities, cds-analytical-views, abap, abap-cloud, naming-convention, abap-unit-testing) to guarantee ABAP Cloud syntax, Clean Core, and strict(2) compliance.

[INPUT DATA]
Project: [Tên dự án trong `projects/` — rule §4. Resolve từ argument đầu tiên hoặc prompt; thiếu thì hỏi ĐÚNG 1 câu trước khi tạo bất kỳ file nào. Đọc `projects/<project>/project.md` trước — nguồn context mặc định cho SAP system/Package/TR. Mọi output path bên dưới nằm dưới `projects/<project>/`.]
Package Name: [Điền tên Package]
Transport Request: [Điền TR, hoặc "Local Object"]
Technical Specification: [Đường dẫn tới TS_[ReportName].md sinh ra bởi /sap-dev-fs-analytic]
Additional Requirements: [Các yêu cầu thêm]
Arguments: $ARGUMENTS

[GOVERNING RULES]
This workflow operates under the Iron Laws, Red Flags, and Token Efficiency rules in `sap-dev-rule.md` (§6-10). In particular: NO OBJECT CREATION WITHOUT TS COVERAGE — if the TS's Coding Implementation Plan doesn't cover something you need, STOP, do not invent it; "Activated" ≠ "correct" — Phase 2 verifies correctness separately, and [Skill: activation-guard] verifies *activation itself* is genuinely clean and non-cascading before that; Validation Log / Activation Status updates use [Skill: caveman]; never re-print the full TS, quote only the row/section needed for the current step.

[EXECUTION PROTOCOL — 4 PHASES]

## Phase 0 — Input Validation Gate

0.0 VALIDATE INPUT, in order:
- The TS file exists and contains all 11 sections of the template, especially §9 Coding Implementation Plan with at least one row.
- Transport Request is a valid TR number or explicitly "Local Object".
- Package exists / is a valid target.
- Every source view listed in TS §9 is marked released/verified per TS §3.

If ANY check fails → 0.1. If all pass → 0.2.

0.1 GRILL-ME ON GAPS: Use [Skill: grill-me] (max 1-3 targeted questions) to collect exactly the missing information from 0.0. Do not proceed until 0.0 fully passes. If the gap is in the TS content itself (not just Package/TR), tell the user to re-run/patch `/sap-dev-fs-analytic` instead of improvising here.

0.2 TASK LEDGER: Use [Skill: scratchpad] (Ledger Format) to create `projects/<project>/scratchpads/scratchpad_[ReportName].md`, one row per object from TS §9 in the TS's specified order, status TODO/DOING/DONE/FAILED/REGRESSED. This ledger is the single source of truth for build progress — if the session is interrupted or context is compacted, re-read the ledger instead of re-deriving progress from memory.

0.3 TR BINDING: Extract the TR from [INPUT DATA]. Every tool call that creates or edits an SAP object must explicitly pass the transport/correction-number parameter matching this TR, to prevent an unwanted auto-generated TR. Verify the exact parameter name/tool signature available in your environment before first use (`sap-dev-rule.md` §9) — if the tool isn't loaded yet, use `ToolSearch` to find it; do not assume a hardcoded tool name.

## Phase 1 — Sequential RAP Build (per TS §9, in the TS's specified order)

For each row in TS §9, execute the matching step below in order. **Never build an object or logic absent from TS §9** — if something is missing, STOP and escalate via 0.1.

Per step: GENERATE (draft per the row's spec) → check the name against [Skill: naming-convention] → VALIDATE (Lint via [Skill: abap], fix Critical/Major) → DEPLOY & ACTIVATE → [Skill: activation-guard] (all 3 gates must pass) → update the ledger row. On activation ERROR: read the exact system error (never guess), consult [Skill: abap-cloud], auto-correct and retry; on a chain of errors use [Skill: handoff] to pause and ask the user. On WARNING: resolve if it violates strict(2), otherwise report as unavoidable — never accept it just because activation returned "success". If Activation Guard's Gate 3 finds a previously-DONE row broke as a side effect of this step, mark that row `REGRESSED` (not a fresh `FAILED`), fix it before continuing forward, then re-run all 3 gates on it.

**Step 1 — Query Data (CDS Data Models):** [Skill: cds-view-entities] + [Skill: find-released-cds-view]. Re-verify sources are released (should already hold per TS §3/§9). If the view spans 2+ sources, first re-verify the TS's join tree against the actual object definitions with [Skill: cds-data-model-analysis] (keys, ON-condition completeness, cardinality, fan-out checklist) — a TS-vs-system mismatch found here goes back to the user/TS per the Iron Laws, never silently patched. Create the Interface View (`DEFINE ROOT VIEW ENTITY`), associations, `@AccessControl.authorizationCheck: #CHECK`, auxiliary views if needed. If TS §9 calls for aggregation, a join, or an input parameter in this view's query logic, also use [Skill: cds-analytical-views] for that part of the syntax. Execute: Lint → Push → Activate → [Skill: activation-guard]. If TS §9 specifies a Custom Entity (`CE_` prefix) instead of a standard CDS Interface View, use [Skill: rap-query-provider] to implement `IF_RAP_QUERY_PROVIDER` (paging/sorting/filtering) in place of the standard BDEF-driven read in this step and Step 3.

**Step 2 — Access Control (DCL):** [Skill: authorization-iam]. Create `DEFINE ROLE` with `pfcg_auth` per TS §10. Execute: Lint → Push → Activate → [Skill: activation-guard].

**Step 3 — Behavior Definition (Base):** [Skill: rap]. Managed/unmanaged per TS, draft handling if applicable, actions/determinations per TS §5/§7. Execute: Lint → Push → Activate → [Skill: activation-guard] (Gate 3 here specifically re-checks Step 1's Interface View is still clean under the new behavior).

**Step 4 — Class Implementation (Behavior Pool):** [Skill: rap] + [Skill: abap-sql-amdp] + [Skill: modern-abap-syntax]. Skip if Read-only. Implement exactly the logic documented in TS §5 — no additional logic beyond it. If TS §7 specifies a business event to raise on an action/determination, use [Skill: rap-business-events] to define and raise it here. Execute: Lint → Push → Activate → [Skill: activation-guard].

**Step 4.5 — Side-task (optional, non-blocking):** [Skill: abap-unit-testing] — generate a test class skeleton for the Step 4 class. In Claude Code, dispatch this via the Agent tool as a background/parallel task if the codebase warrants it; otherwise run inline right after Step 4 without blocking Step 5.

**Step 5 — Projection View & Metadata Extension:** [Skill: cds-view-entities] for the projection view itself; [Skill: cds-analytical-views] owns the `@UI`/value-help annotation syntax for the Metadata Extension. Create the projection (`AS PROJECTION ON`) with `@Search`, `@EndUserText`, `@Metadata.allowExtensions: true`. Do NOT put `@UI` annotations in the projection — generate the full Metadata Extension source and save it to `projects/<project>/metadata_extensions/ZMD_[ReportName].md`; tell the user to create the DDLX object manually in Eclipse ADT (the automated tool cannot create DDLX objects directly). Execute: Lint → Push → Activate → [Skill: activation-guard] (Projection View only).

**Step 6 — Projection Behavior:** [Skill: rap]. Skip if no Base BDEF. Execute: Lint → Push → Activate → [Skill: activation-guard].

**Step 7 — Service Definition & Binding:** [Skill: odata]. Create Service Definition, then Service Binding (OData V4 UI, per TS unless stated otherwise). Execute: Lint → Push → Activate → [Skill: activation-guard].

## Phase 2 — Manual Runtime Verify Loop (max 3 iterations)

2.0 Once all Phase-1 objects are activated and have passed [Skill: activation-guard] (no open Gate-3 ripple issues, no `REGRESSED` rows), derive 2-3 representative test filter values from TS §3-§5 (e.g. a known period/company code for a balance calculation) plus the exact expected result/logic for each. **No automated data-preview tool is assumed available** — ask the user to run the OData service (Fiori Preview / Postman / SEGW test) with these filters and paste back the actual result.

2.1 Evidence floor (`sap-dev-rule.md` §11): a bare "looks fine" is not a PASS. If the user's reply has no concrete data, ask again for the actual field values/payload before recording a result. Log each attempt in the Scratchpad ledger's Verify Attempts table.

2.2 Compare the pasted actual result against the TS-documented logic field by field, especially the "Complex Logic" entries from TS §5. PASS → Phase 3. MISMATCH → root-cause it (trace the actual-vs-expected diff to the specific object/field responsible — do not guess), fix, redeploy the affected object(s), and ask the user to re-test. After 3 mismatch iterations, STOP — write up the concrete unresolved discrepancy and ask the user rather than attempting a 4th blind fix (`sap-dev-rule.md` §7). If the user insists on accepting an unverified result, record it as "PASS — unverified, user-accepted", never as a plain PASS.

## Phase 3 — Walkthrough & Risk Report

3.0 Save `projects/<project>/walkthroughs/walkthrough_[ReportName].md`: what was built (object list from the ledger, all DONE), what was verified and how (cite the actual filter values and results from Phase 2 — never "should work"), and any known risks/manual steps outstanding (e.g. "Metadata Extension pending manual creation in ADT"). If a UI Service Binding (Step 7) was created, optionally use [Skill: sap-fiori-apps-reference] to generate the Fiori Launchpad URL from its Semantic Object/Action and include it in the walkthrough.

[OUTPUT FORMAT]
For each Phase-1 step, report in the chat using [Skill: caveman] style for the narration only (short, evidence-based, no filler) — the source code and log content below stay verbatim, never compressed (`sap-dev-rule.md` §10):
- The Object Name & Applied Skill (e.g., `ZC_MY_REPORT` — [Skill: cds-view-entities]).
- The exact validated ABAP/CDS source code (markdown, verbatim).
- SYSTEM EXECUTION RESULT: Validation Log (abaplint/Clean ABAP), Activation Status (Activated/Failed/Activated with Warnings), Auto-Correction Log if any, [Skill: activation-guard] gate results (Gate 1/2/3 pass, or the exact ripple/regression found) — verbatim.
