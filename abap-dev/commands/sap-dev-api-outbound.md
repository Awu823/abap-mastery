---
description: Sử dụng workflow này khi có yêu cầu tạo mới một API Outbound (SAP gọi hệ thống bên ngoài) sử dụng framework Z_API_FWK để đảm bảo cấu trúc thiết kế, logging tự động, chuẩn hóa.
argument-hint: <project> <api-name>
---

> **Claude Code note:** `[Skill: X]` below means invoke the `x` skill via the Skill tool (auto-discovered from `.claude/skills/x/`). Where a step needs an MCP tool not yet loaded, use `ToolSearch` first (see `sap-dev-rule.md` §9).

[ROLE & OBJECTIVE]
Act as an Expert SAP Integration Architect & ABAP Cloud Developer. Design, implement, and validate an OUTBOUND API integration that adheres strictly to the `Z_API_FWK` framework.

[INPUT DATA]
- Project: [Tên dự án trong `projects/` — rule §4. Resolve từ argument đầu tiên hoặc prompt; thiếu thì hỏi ĐÚNG 1 câu (gộp vào 0.1 nếu đang grill). Đọc `projects/<project>/project.md` trước (SAP system, package, TR mặc định). Mọi output path bên dưới nằm dưới `projects/<project>/`.]
- Package Name: [Điền tên Package]
- Transport Request: [Điền TR]
- Trigger Point: [RAP Action, Report, or Batch Job]
- Outbound Endpoint Details: [URL, Method, Auth]
- Request/Response Structure: [Cấu trúc dữ liệu gửi và nhận]
- Success/Failure Handling: [Xử lý khi thành công hoặc thất bại, luồng tiếp theo]
- Arguments: $ARGUMENTS

[GOVERNING RULES]
This workflow operates under the Iron Laws, Red Flags, and Token Efficiency rules in `sap-dev-rule.md` (§6-10). In particular: activation success is not completion evidence — Phase 2 below verifies with a real outbound call, and [Skill: activation-guard] verifies activation itself is genuinely clean and hasn't broken anything downstream before that; progress/log output uses [Skill: caveman].

**Framework usage contract: [Skill: z-api-fwk]** is the canonical source for how `Z_API_FWK` works (the `ZCL_API_FWK->execute_api` call surface, config-driven `comm_scenario`/`service_id`/`comm_system_id` destination resolution, `method`/`content_type`/`mapping_camel` serialization rules, dynamic-request precedence, response camelCase→underscore deserialization, the `ZCX_API_FWK` exception matrix, and logging). Consult it — specifically its `references/outbound-guide.md` — at the build step below INSTEAD of re-reading the `Z_API_FWK` package source. If observed system behavior ever contradicts the skill, trust the system, then propose a skill patch (rule §14).

[EXECUTION PROTOCOL — CRITICAL]
After generating the ABAP code for each step: GENERATE -> VALIDATE (LINTING) -> DEPLOY & ACTIVATE -> [Skill: activation-guard] (all 3 gates must pass before the step counts as done). All outbound calls MUST go through `ZCL_API_FWK=>execute_api`.

## Phase 0 — Input Validation Gate

0.0 VALIDATE INPUT: check Package, TR, Trigger Point, Endpoint Details, Request/Response structure, and Success/Failure Handling are all present and concrete (not placeholders). Missing/vague → 0.1, else → 0.2.

0.1 GRILL-ME ON GAPS: [Skill: grill-me] (max 1-3 targeted questions).

0.2 PLANNING & DRAFTING: [Skill: scratchpad] + [Skill: fs-integration-api-analyzer] — check the SAP Accelerator Hub for an existing standard API before assuming a custom one is needed; analyze trigger points, data extraction logic, payload structure, response handling. Save to `projects/<project>/scratchpads/scratchpad_outbound_[API_Name].md` (doubles as the build ledger — TODO/DOING/DONE/FAILED/REGRESSED per step).

## Phase 1 — Build

Step 1 — Data Dictionary Objects: [Skill: abap-cloud] + [Skill: naming-convention]. Create DDLS/TABL/TTYP representing the Request payload and expected Response. Execute: Lint → Push → Activate → [Skill: activation-guard].

Step 2 — Outbound Integration Logic: [Skill: z-api-fwk] (read `references/outbound-guide.md` for the exact `execute_api` call patterns, `ty_dynamic_request` precedence over config, and response-deserialization rules) + [Skill: rap], [Skill: abap], [Skill: modern-abap-syntax], [Skill: oo-design-patterns], [Skill: naming-convention]. If triggered by RAP, implement the behavior action (e.g. `FOR MODIFY`) using Modern ABAP Syntax. Gather business data, construct the request payload/headers via `zif_api_fwk_types=>ty_dynamic_request`, call `NEW zcl_api_fwk( )->execute_api( EXPORTING iv_api_id = ... is_dynamic_request_value = ... IMPORTING es_logger = ... CHANGING c_response_data = ... )` (always pass the business document number as the transaction number for log traceability), parse `es_logger`/response, update the business object status, catch `ZCX_API_FWK` per the skill's exception matrix, return explicit Reported messages. Execute: Lint → Push → Activate → [Skill: activation-guard] (Gate 3 re-checks Step 1's DDIC objects and, if this is a RAP-triggered action, the underlying Behavior Definition/Pool are still clean).

Step 3 — Framework Configuration: instruct the user to configure the Outbound API via Fiori App `ZUI_API_CONFIG_O4` (config header fields per [Skill: z-api-fwk]: `api_id`, `direction='O'`, `comm_scenario`/`service_id`/`comm_system_id`, `method`, `content_type`, `mapping_camel`, `uri_path`, `log_enable`). Communication scenario/arrangement/system creation itself → [Skill: btp-abap-environment]. Never write config tables directly (rule §3).

## Phase 2 — Manual Integration Verify Loop (max 3 iterations)

2.0 Ask the user to actually trigger the outbound call (via the real RAP action/report/batch job) against the real or sandboxed target endpoint, and report back what the target system received/logged plus the resulting SAP object status.

2.1 Evidence floor (`sap-dev-rule.md` §11): a bare "looks fine" is not a PASS — ask again for the actual target-system response/log before recording a result. Log each attempt in the Scratchpad ledger's Verify Attempts table.

2.2 Compare against the Success/Failure Handling spec from [INPUT DATA]. PASS → Phase 3. MISMATCH → root-cause the actual request/response (do not guess), fix, redeploy, ask the user to re-test. After 3 mismatch iterations, STOP and report the concrete unresolved discrepancy (`sap-dev-rule.md` §7). If the user insists on accepting an unverified result, record it as "PASS — unverified, user-accepted", never as a plain PASS.

## Phase 3 — Walkthrough

Save `projects/<project>/walkthroughs/walkthrough_outbound_[API_Name].md`: objects built, the actual Phase 2 call evidence (payload sent + target response — never "should work"), and any outstanding risks.

[OUTPUT FORMAT]
Per step, narrate in [Skill: caveman] style (short, evidence-based); the source code and results below stay verbatim, never compressed (`sap-dev-rule.md` §10): Object Name & Applied Skill (e.g., `ZR_MY_OUTBOUND` — [Skill: rap]); the validated ABAP source code (markdown, verbatim); SYSTEM EXECUTION RESULT (Validation Log, Activation Status, [Skill: activation-guard] gate results).
