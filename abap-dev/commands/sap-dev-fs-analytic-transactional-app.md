---
description: Sử dụng workflow này khi cần phân tích tài liệu Functional Specification (FS) mô tả một Chức năng (Transactional App) xây MỚI HOÀN TOÀN — chưa có Z-table/CDS nào tồn tại — để tạo ra bản Technical Specification (TS) đầy đủ cho `/sap-dev-create-transactional-app` thực thi mà không cần tự thiết kế thêm, bao gồm cả tầng DDIC Foundation (table/domain/data element/number range) chứ không chỉ tầng RAP trên CDS có sẵn.
argument-hint: <project> <fs-file-path> <package-name>
---

> **Claude Code note:** `[Skill: X]` below means invoke the `x` skill via the Skill tool (auto-discovered from `.claude/skills/x/`). Where a step needs an MCP tool not yet loaded, use `ToolSearch` first (see `sap-dev-rule.md` §9).
>
> **Relationship to `/sap-dev-fs-analytic`:** same 6-phase design, same TS template, same governance — reused wholesale. The difference is scope: `/sap-dev-fs-analytic` assumes the FS's data already lives in an existing released CDS view (its Phase 1 only *finds and verifies* a source); this workflow assumes the FS describes brand-new business data with no existing table or view — its Phase 1 *designs* the new Z-table structure(s) from scratch, and its Phase 3 Coding Implementation Plan always includes a DDIC Foundation step group so `/sap-dev-create-transactional-app` never has to invent table structure on its own. Use this workflow when the FS describes a new custom entity/master-transaction data set (e.g. a new document type, a new master data record) with no pre-existing SAP table/CDS behind it; use `/sap-dev-fs-analytic` when the FS is a report/screen over data that already exists in a released CDS view.

[ROLE & OBJECTIVE]
Act as an Expert SAP Solution Architect and Technical Analyst. Deeply read and analyze a Functional Specification (FS) document describing a brand-new transactional business object, then translate its data structure, status/lifecycle rules, UI requirements, and actions into a Technical Specification (TS) strictly aligned with SAP ABAP Cloud, Clean Core, and RAP architecture. The TS you produce is the ONLY input `/sap-dev-create-transactional-app` will read — it must be complete enough (down to DDIC field/type/key level) that create-transactional-app never has to guess or design on its own.

[INPUT DATA]
- Project: the target project name under `projects/` (rule §4). Resolve from the first argument or the user's prompt; if absent, ask ONE question before creating any file. The directory `projects/<project>/` must already exist (`/sap-project-init` otherwise). Read `projects/<project>/project.md` first — it supplies the default SAP system, package, and TR context. Every output path below lives under `projects/<project>/`.
- Functional Specification (FS): file(s) in `projects/<project>/fs_docs/`, or FS text pasted directly. Arguments: $ARGUMENTS

[GOVERNING RULES]
This workflow operates under the Iron Laws, Red Flags, and Token Efficiency rules in `sap-dev-rule.md` (§6-10). In particular: no TS handoff without passing the Verify Loop (Phase 5); progress updates use [Skill: caveman]; never re-print full drafts already saved to a file, reference the path instead. A structural gap (an entity/field with no table, key, or type decided) is a HARD BLOCK — do not placeholder it; a business-value gap (e.g. an exact config value still pending from another app/team) may be recorded as `[assumption]`/`TBD` per `sap-dev-rule.md` §11 as long as it doesn't stop the build.

[EXECUTION PROTOCOL — 6 PHASES]

## Phase 0 — Intake & Pre-processing

0.0 TASK LEDGER: Use [Skill: scratchpad] to create `projects/<project>/scratchpads/scratchpad_[AppName].md` with the Ledger Format (TODO/DOING/DONE/FAILED) covering Phases 0-6. Update it immediately after each phase — it is the single source of truth for progress, not this conversation's history.

0.1 DOCUMENT PRE-PROCESSING: Dispatch `[Agent: consultant-executor]` with [Skill: document-markdown-converter] to convert binary FS files (PDF/DOCX/XLSX) in `projects/<project>/fs_docs/` into `projects/<project>/scratchpads/fs_markdown.md`. Skip if the FS is already plain text/Markdown. From here on, read `fs_markdown.md` only — never the original binary.

0.2 VISUAL EXTRACTION: If the FS contains images (UI mockups, flowcharts, Excel screenshots), dispatch `[Agent: consultant-executor]` with [Skill: fs-vision-extractor] to transcribe them into Markdown and append the result into `fs_markdown.md` under a clearly labeled heading (e.g. `## Extracted from Image: <name>`). Skip if the FS has no images.

0.3 DATA COMPLETENESS GATE (HARD GATE): Review `fs_markdown.md`. If the FS explicitly references fields/entities/requirements that live in an unprocessed image, an external link, or a table that failed conversion, STOP and ask the user to provide the missing information. Do not guess or use placeholder ranges. Do not proceed to Phase 1 until this gate passes.

## Phase 1 — Data Model Foundation: Design the New Table Structure (single dispatch — every later phase reuses this vocabulary)

Unlike `/sap-dev-fs-analytic` (which only *looks up* an existing view), this phase *designs* the persistence layer from zero.

1.0 NEW TABLE DESIGN + RELEASED CDS VALIDATION: Dispatch `[Agent: consultant-lead]` ONCE, naming all four sub-tasks below in the same dispatch prompt to run in sequence inside that one agent — do not split into separate dispatches: (b) strictly needs (a)'s composition tree, (c) and (d) feed the same combined Verified Data Model output, so nothing here parallelizes and splitting them only adds round-trip overhead.

(a) ENTITY & TREE ANALYSIS: [Skill: fs-data-model-extractor] on `fs_markdown.md` → identify the composition tree (root entity + every child/sub-entity the FS describes, e.g. a header with line-item children), each entity's business key(s), and whether the FS implies versioning/sequencing (e.g. a document number + version, or a child row number scoped to its parent).

(b) NEW TABLE DESIGN (the step that replaces "find a released view"): for every entity in the tree from (a), design its full DDIC shape: field list with ABAP type/length, which fields are keys (including any composite/parent-FK keys for children), which fields need a fixed-value Domain (status, type, category fields), which need a dedicated Data Element (for label reuse), and whether the app needs a Number Range object (external/managed sequential numbering) vs. simple RAP-managed/BDEF numbering for a field. Flag draft-table need (draft-enabled if the FS implies save-later/edit-in-progress behavior, e.g. an "Edit" that doesn't commit immediately). [Skill: naming-convention] for every proposed name — but if the FS/user has already stated an explicit naming scheme (base name + node suffixes, e.g. `_H`/`_FG`/`_RM`), that explicit scheme wins over the skill's generic default.

(c) RELEASED CDS VALIDATION — reference/lookup data only: [Skill: find-released-cds-view] to verify every EXTERNAL reference the FS points to (e.g. Sales Order, Product, Plant, Batch, Profit Center — anything looked up from existing SAP master/transaction data rather than owned by this new app) resolves to a released Clean-Core-Level-A CDS view (S/4HANA Cloud Public). These become associations/value-help on the new Interface Views, never the base entity itself. Replace any unreleased/internal reference with the best released alternative matching grain and field coverage.

(d) PROCESS-DOMAIN SKILL CHECK: check whether any `sap-process-*` skill (business-process domain knowledge, `.claude/skills/sap-process-*/` — auto-discovered by description match against the FS content) is relevant to this FS's business domain, and invoke any that apply; if none apply, say so explicitly rather than skipping the check silently.

Output: **Verified Data Model** — (a) the New Table Design (entity → field → type/key/domain) and (b) the released reference views and the field they supply — the vocabulary every later phase must reuse verbatim (identical field/table/view names) to avoid drift. Persist it as a `## Verified Data Model` section in `projects/<project>/scratchpads/scratchpad_[AppName].md`, plus a `## Relevant Process-Domain Skill(s)` section naming exactly which `sap-process-*` skill(s) applied from (d) (or "None") — Phase 2's dispatched agents read this file, not conversation history, and reuse this list instead of re-discovering it themselves (this is the one and only domain-discovery pass — keeps token cost to one check instead of one per Phase-2 dispatch).

## Phase 2 — Domain Analysis (parallel via dedicated subagents)

2.A/2.B/2.C each take `fs_markdown.md` + the `## Verified Data Model` and `## Relevant Process-Domain Skill(s)` sections of the scratchpad ledger as read-only input and produce one independent draft. Dispatch all three via `[Agent: consultant-lead]` (parallel Task calls in one message, `subagent_type: consultant-lead`, no `isolation: "worktree"`); each dispatch prompt must name the one skill to invoke, the input path(s), and its own output path — read-only input, write only its own draft, no shared state. 2.B's dispatch prompt additionally names any `sap-process-*` skill(s) listed in `## Relevant Process-Domain Skill(s)` and instructs it to read that skill's `references/deep-dive.md` for functional-consulting depth (e.g. status/lifecycle conventions, numbering patterns, partner determination) before finalizing — this is where that depth changes business-logic correctness the most; 2.A/2.C may reference the same skill's base `SKILL.md` content if directly relevant, but do not also read its `references/deep-dive.md` unless the FS's own UI/integration requirement genuinely needs that depth.

Threshold (starting heuristic — tighten once real dispatch-timing data exists): dispatch sequentially instead of in parallel only if the Verified Data Model lists fewer than ~15 fields total across all new tables AND `fs_markdown.md` is under ~2 pages — below that size, three parallel dispatches cost more in spin-up overhead than they save. At or above the threshold, always dispatch in parallel — the result is identical content either way, only faster.

2.A UI/UX ANALYSIS: [Skill: fs-fiori-ui-elements-mapper] → UI Layout Draft (List Report Selection Fields/Line Items/Sorting, Object Page Facets per composition-tree node, toolbar buttons per facet with their enable/visibility condition). Output: `projects/<project>/scratchpads/draft_ui_[AppName].md`.

2.B BUSINESS LOGIC & LIFECYCLE EXTRACTION: [Skill: fs-logic-behavior-translator] → Business Logic Draft covering: **Status Machine** (every valid status value, every transition, the action/event that triggers it, and its precondition — if the FS implies a lifecycle at all), **Numbering** (which field, by which mechanism — Number Range vs. BDEF managed/early/late — and whether it's scoped per-parent, e.g. a child row counter that restarts per header), **Actions/Determinations/Validations** across the whole tree (not just the root), Clean Core violations + released replacements, Authorization Check needs (both DCL-level and any per-action custom Authorization Object the FS implies, e.g. "only role X can press button Y"). This skill already mandates MCP-verified replacements for any unreleased API it flags — do not skip that check. Output: `projects/<project>/scratchpads/draft_logic_[AppName].md`.

2.C INTEGRATION & API ANALYSIS: [Skill: fs-integration-api-analyzer] → Integration Draft (Integration Pattern, OData Service Model, API Style Compliance, Field Mapping Table, Security/Auth). If the FS has no integration/interface requirements, output exactly "N/A — FS has no integration requirements" rather than skipping the step silently. Output: `projects/<project>/scratchpads/draft_integration_[AppName].md`.

2.D RECONCILIATION: Read back each of the three draft files yourself (`sap-dev-rule.md` §12 — a dispatch's completion message is not sufficient evidence). To keep this cheap on context, read only each file's **Field Name Index** (the flat list at the very top of the file) first and cross-check those names against the Verified Data Model; open the full draft body only for a file whose Index shows a name that doesn't match, to get the context needed to resolve it. List any mismatch as a Conflict and resolve it (align naming, or return to Phase 1 if a field/entity is genuinely missing) before proceeding to 2.E.

2.E SCOPE CHALLENGE ([Skill: lean-abap] rungs R0-R3 — the only place an FS requirement may be challenged): From the reconciled drafts, list FS requirements whose cost the stated business need does not justify, or that duplicate something already available — a standard SAP Fiori app / released CDS field / existing Z-object (R1-R2), or a declarative CDS/RAP feature that replaces custom logic the FS implies (R3). For each: FS reference, why challenged, smaller alternative, what the user loses if accepted. Present them to the user in ONE message and WAIT; record each decision (Keep / Replace with alternative / Cut) with the user's own words in TS §12. No challenge → write "None" in TS §12 and continue without asking. Never drop, merge, or shrink an FS requirement without an explicit written user decision — a challenge the user has not answered means Keep. `/sap-dev-create-transactional-app` later builds only what the TS says, so this is the last point where scope can shrink.

## Phase 3 — Architecture & Coding Implementation Plan (the phase create-transactional-app depends on most)

3.0 ARCHITECTURE BRAINSTORM: always resolve these transactional-app-specific decisions explicitly (they don't exist in the read-only fs-analytic flow): numbering mechanism per key field (Number Range vs. managed/early/late numbering, and batch-safety if multiple child rows can be created in one request), draft-enabled vs. not, and — only when genuinely complex/ambiguous (e.g. a multi-branch status machine, a real choice between CDS Virtual Element vs. Behavior Pool vs. Custom Entity + Query Provider) — generate 2-3 candidate architectures with explicit trade-offs (Clean Core compliance / Performance / Maintainability), pick one, and state why. For straightforward pieces with no such ambiguity, skip the multi-option comparison and go straight to the obvious design.

3.1 CODING IMPLEMENTATION PLAN (the section `/sap-dev-create-transactional-app` depends on entirely): using [Skill: naming-convention] for every object name (TS-explicit names always win, see Phase 1.0(b)), produce a complete table of every object to be created:

| # | Object Name | Type | Purpose | Source/Base + Join/Association | Field Mapping (which TS output field(s) it delivers) | Corresponding create-transactional-app Step |
|---|---|---|---|---|---|---|

This table MUST include, in dependency order, every step group `/sap-dev-create-transactional-app` executes:
- **Step 0 — DDIC Foundation**: every Domain, Data Element, Structure, Number Range Object, Message Class, and DB Table (Persist + Draft) the New Table Design (Phase 1.0(b)) requires — this is the group `/sap-dev-fs-analytic`'s template never needs, and the one most often missed.
- **Step 1 — Interface View** (root + every child node).
- **Step 2 — DCL / Authorization Object** (custom Authorization Object row only if 2.B flagged per-action authorization).
- **Step 3 — Behavior Definition** (root + every child node, in one tree).
- **Step 3.5 — Supporting Class/Interface** (any helper/mapper/utility class the Behavior Pool will call — list it here explicitly so create-transactional-app builds it before the Behavior Pool, not after).
- **Step 4 — Behavior Pool Class** (root + child local handler classes).
- **Step 5 — Projection View & Metadata Extension** (root + every child node).
- **Step 6 — Projection Behavior**.
- **Step 7 — Service Definition & Binding**.
- **Step 8 — Fiori App Configuration** (only if the FS requires an App Descriptor / `manifest.json` level setting, e.g. frozen table columns — otherwise omit this row entirely, do not invent one).

This table must cover 100% of what create-transactional-app's Steps 0-8 will need — enough that create-transactional-app performs zero independent design or lookup.

## Phase 4 — Assemble TS

4.0 Merge every draft and the Coding Implementation Plan into the full TS using the template in [OUTPUT FORMAT] below.

## Phase 5 — Verify Loop (max 3 automatic iterations)

5.0 Cross-check the TS draft against `fs_markdown.md`:
- 100% of FS fields are present with exact names (no placeholders) — except fields the user explicitly cut in TS §12 (Scope Decisions); every 2.E challenge has a recorded user decision and each one has a concrete DDIC home (a field in a named New Table, with type/length/key decided — not just a bullet point).
- Every field has documented source + derivation logic (new-table input field, or released-view lookup).
- If the FS implies a status/lifecycle, the Status Machine is 100% specified: every state, every transition, its trigger and precondition — not just "some statuses."
- Every key field that isn't pure user input has an explicit numbering mechanism decided (Number Range / managed / early / late), including batch-safety if multiple rows can be created in one request.
- Every row in the Coding Implementation Plan has a clear source/target, references no field absent from the Verified Data Model, and Step 0 (DDIC Foundation) is present and complete if TS §3 defines any new table.

PASS → Phase 6. FAIL → fix the specific gap in the phase it belongs to, then re-run this gate. Log each attempt in the Scratchpad ledger's Verify Attempts table (see Scratchpad skill) so the 3-iteration cap is tracked, not just remembered. After 3 failed iterations, STOP — list the exact unresolved blockers and ask the user instead of continuing to guess (Red Flags, `sap-dev-rule.md` §7).

## Phase 6 — Handoff

6.0 Save the TS, mark the ledger fully DONE. If the session ends here before `/sap-dev-create-transactional-app` runs, use [Skill: handoff] to summarize state for the next session.

[OUTPUT FORMAT — CRITICAL]
Save the final TS as Markdown directly under `projects/<project>/technical_specifications/TS_[AppName].md` (relative to workspace root). Do not add introductory or concluding remarks outside the template. Use CamelCase for `[AppName]`.

```
# Technical Specification: [AppName]

## 1. Tổng Quan (Overview)
[Mục đích chức năng, đối tượng sử dụng, phạm vi nghiệp vụ — bám sát FS, 1 đoạn ngắn]

## 2. Tham Số & Layout
Package Name: [Target Package]
Transport Request: [Target Transport Request, hoặc "TBD" nếu user hoãn tới lúc code — không chặn TS]
Report Type: Transactional/Actionable — New Custom RAP Build (Managed, [draft-enabled/no draft])
Target Build Workflow: /sap-dev-create-transactional-app
Base object name: [Tên gốc + suffix theo từng node, vd _H/_FG/_RM]

## 3. Data Model Architecture
- **New Z-Table(s)** (Persist / Draft): [Mỗi entity trong cây composition — tên bảng, key, ghi chú]
- **Output Fields — 100% coverage** [MANDATORY, theo từng bảng: field / type / nguồn hoặc derivation logic]
- **Reference Data — Released CDS View** [Mỗi nhu cầu tra cứu bên ngoài → CDS view đã verify Level A]
- **Joins & Associations**: [Composition cha-con + association tới reference view, với ON condition]
- **Hardcoded Filters**: [List, hoặc "Không có"]

## 4. UI & Layout (Fiori Elements)
- List Report: Selection Fields, Line Items (thứ tự), Default Sorting, Toolbar (buttons + điều kiện enable)
- Object Page: Facet theo từng node trong cây, field layout, toolbar riêng mỗi facet nếu có
- [Mọi hành vi UI đặc biệt — freeze column, popup, v.v. — ghi rõ đây là cấu hình manifest.json/UI, không phải CDS annotation]

## 5. Business Logic & Behavior
- **Status Machine** [MANDATORY nếu có lifecycle]: bảng Action / Precondition / Kết quả — đầy đủ mọi state và transition
- **Numbering**: mỗi key field không phải user-input → cơ chế sinh số (Number Range / managed / early / late), scope (toàn cục hay theo từng parent), batch-safety nếu tạo nhiều dòng 1 lần
- Derived/Calculated Fields (CDS): [List]
- Complex Logic (Virtual Elements / ABAP / Supporting Class cần thiết): [List — nêu rõ class nào Behavior Pool sẽ gọi]
- Authorization Check: [chi tiết tập trung tại §10 — không liệt kê lại ở đây để tránh lệch 2 nơi]

## 6. Integration & API
[Từ Phase 2.C — hoặc "N/A — FS has no integration requirements"]

## 7. Tính Năng & Hành Vi (Features & Actions)
[Bảng: Nút | Vị trí | Điều kiện enable | Ghi chú — 100% action trong FS]

## 8. Print Form
[Brief description only if the FS requires printing — otherwise "Không áp dụng"]

## 9. Coding Implementation Plan
[Full table from Phase 3.1 — PHẢI đủ Step 0 (DDIC Foundation) → Step 8 (Fiori App Configuration, nếu có)]

## 10. Authorization Check
[Auth objects / PFCG / DCL requirements — baseline nếu FS chưa có chi tiết, nêu rõ đây là đề xuất]

## 11. Additional Requirements
- [Gap còn thiếu, `[assumption]`/`[Unverified]` cần xác nhận khi code, theo đúng Reality Filter — không suy đoán thành fact]
- [Naming conventions beyond the default, nếu FS có chỉ định]
- [Transport Request TBD nếu có — nêu rõ đây là quyết định hoãn của user, không phải thiếu sót TS]

## 12. Scope Decisions (Scope Challenge — Phase 2.E)
| # | FS Reference | Challenge | Smaller Alternative | User Decision (Keep / Replace / Cut) + user's words |
|---|---|---|---|---|
[Or "None" — no FS requirement was challenged]
```
