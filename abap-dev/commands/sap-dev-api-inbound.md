---
description: Sử dụng workflow này khi có yêu cầu tạo mới một API Inbound (Hệ thống bên ngoài gọi vào SAP). Workflow đảm bảo tuân thủ kiến trúc của Z_API_FWK, xử lý logging tự động và thiết kế handler class chuẩn mực.
argument-hint: <project> <api-name>
---

> **Claude Code note:** `[Skill: X]` below means invoke the `x` skill via the Skill tool (auto-discovered from `.claude/skills/x/`). Where a step needs an MCP tool not yet loaded, use `ToolSearch` first (see `sap-dev-rule.md` §9).

[ROLE & OBJECTIVE]
Act as an Expert SAP Integration Architect & ABAP Cloud Developer. Design, implement, and validate an INBOUND API integration that adheres strictly to the `Z_API_FWK` framework.

[INPUT DATA]
- Project: [Tên dự án trong `projects/` — rule §4. Resolve từ argument đầu tiên hoặc prompt; thiếu thì hỏi ĐÚNG 1 câu (gộp vào 0.1 nếu đang grill). Đọc `projects/<project>/project.md` trước (SAP system, package, TR mặc định). Mọi output path bên dưới nằm dưới `projects/<project>/`.]
- Package Name: [Điền tên Package]
- Transport Request: [Điền TR]
- Business Data Requirements (Request/Response): [Cấu trúc dữ liệu nhận vào và trả về]
- Existing Communication Objects: [Có hay chưa]
- API Design Details (Method, Auth, Headers, Params): [Chi tiết API]
- Success/Failure Criteria: [Định nghĩa thành công/thất bại và luồng xử lý]
- Arguments: $ARGUMENTS

[GOVERNING RULES]
This workflow operates under the Iron Laws, Red Flags, and Token Efficiency rules in `sap-dev-rule.md` (§6-10). In particular: activation success is not completion evidence — Phase 3 below verifies with a real inbound call, and [Skill: activation-guard] verifies activation itself is genuinely clean and hasn't broken anything downstream before that; progress/log output uses [Skill: caveman].

**Framework usage contract: [Skill: z-api-fwk]** is the canonical source for how `Z_API_FWK` works (object map, `ZIF_API_INBOUND_HANDLER` contract, the single `Z_API_INBOUND_HTTP` dispatcher + `x-api-id` routing, config header fields, logging behavior, the 400/404/405/500 framework error matrix, JSON/XML utils). Consult it — specifically its `references/inbound-guide.md` — at the build steps below INSTEAD of re-reading the `Z_API_FWK` package source. If observed system behavior ever contradicts the skill, trust the system, then propose a skill patch (rule §14).

[EXECUTION PROTOCOL — CRITICAL]
After generating the ABAP code for each step: GENERATE -> VALIDATE (LINTING) -> DEPLOY & ACTIVATE -> [Skill: activation-guard] (all 3 gates must pass before the step counts as done). All errors MUST be caught using `CX_ROOT` or `ZCX_API_FWK` and returned explicitly.

## Phase 0 — Input Validation Gate

0.0 VALIDATE INPUT: check Package, TR, Request/Response data structure, API Design Details, and Success/Failure Criteria are all present and concrete (not placeholders). Missing/vague → 0.1, else → 0.2.

0.1 GRILL-ME ON GAPS: [Skill: grill-me] (max 1-3 targeted questions) to fill exactly the gaps found in 0.0.

0.2 PLANNING & DRAFTING: [Skill: scratchpad] + [Skill: fs-integration-api-analyzer] — check the SAP Accelerator Hub for an existing standard API before assuming a custom one is needed; if custom is required, draft the architecture, map the JSON/XML payload to ABAP Dictionary structures, define HTTP/error-handling logic. Save to `projects/<project>/scratchpads/scratchpad_inbound_[API_Name].md` (this doubles as the build ledger — TODO/DOING/DONE/FAILED/REGRESSED per step).

## Phase 1 — Build

Step 1 — Data Dictionary Objects: [Skill: abap-cloud] + [Skill: naming-convention]. Create DDLS/TABL/TTYP for Request/Response payloads. Execute: Lint → Push → Activate → [Skill: activation-guard].

Step 2 — Handler Class: [Skill: z-api-fwk] (read `references/inbound-guide.md` for the `ZIF_API_INBOUND_HANDLER` handler template, `handle_request` signature/return contract, and binary/base64 payload behavior) + [Skill: abap], [Skill: released-abap-classes], [Skill: modern-abap-syntax], [Skill: oo-design-patterns], [Skill: naming-convention]. Create a global class (e.g. `ZCL_IB_[API_NAME]`) implementing `ZIF_API_INBOUND_HANDLER`. Apply OO patterns (e.g. Strategy) for multiple payload types. Implement `handle_request`: parse payload (e.g. `xco_cp_json` or `zcl_api_fwk=>json_to_abap`), execute core business logic (EML), catch all exceptions (`cx_static_check`, `cx_root`) and return explicit HTTP status/error messages per the skill's error matrix. Execute: Lint → Push → Activate → [Skill: activation-guard] (Gate 3 re-checks Step 1's DDIC objects are still clean under this class's usage).

Step 3 — Framework Configuration: instruct the user to configure the API via Fiori App `ZUI_API_CONFIG_O4` (config header fields per [Skill: z-api-fwk]: `api_id` = the `x-api-id` value the partner sends, `direction='I'`, `inbound_class` = the new handler, `active`, `log_enable`), mapping the API ID to the new Handler Class. Never write config tables directly (rule §3).

## Phase 2 — Unit Test (mandatory, not sufficient alone)

[Skill: abap-unit-testing]: generate unit tests for the Handler Class using mock data, covering both success and error paths. This proves the class logic in isolation — it does not prove the live endpoint works end-to-end, which is why Phase 3 exists.

## Phase 3 — Manual Integration Verify Loop (max 3 iterations)

3.0 Ask the user to send a real (or sandboxed) inbound call to the new endpoint — from the actual external system or a tool like Postman impersonating it — using a representative payload, and report back the actual HTTP response and the resulting SAP object/state.

3.1 Evidence floor (`sap-dev-rule.md` §11): a bare "looks fine" is not a PASS — ask again for the actual response/payload before recording a result. Log each attempt in the Scratchpad ledger's Verify Attempts table.

3.2 Compare against the Success/Failure Criteria from [INPUT DATA]. PASS → Phase 4. MISMATCH → root-cause it (trace the actual request/response, do not guess), fix, redeploy, ask the user to re-test. After 3 mismatch iterations, STOP and report the concrete unresolved discrepancy to the user (`sap-dev-rule.md` §7). If the user insists on accepting an unverified result, record it as "PASS — unverified, user-accepted", never as a plain PASS.

## Phase 4 — Walkthrough

Save `projects/<project>/walkthroughs/walkthrough_inbound_[API_Name].md`: objects built, unit test results, the actual Phase 3 call evidence (payload + response — never "should work"), and any outstanding risks.

[OUTPUT FORMAT]
Per step, narrate in [Skill: caveman] style (short, evidence-based); the source code and results below stay verbatim, never compressed (`sap-dev-rule.md` §10): Object Name & Applied Skill (e.g., `ZCL_IB_CREATE_SO` — [Skill: abap]); the validated ABAP source code (markdown, verbatim); SYSTEM EXECUTION RESULT (Validation Log, Activation Status, [Skill: activation-guard] gate results).
