---
description: Sử dụng workflow này khi cần chẩn đoán và sửa lỗi (bug) trên object SAP hiện có, dựa trên mock data do user cung cấp, đảm bảo phân tích root cause và đánh giá rủi ro trước khi sửa.
argument-hint: <project> <object-name> <observed-vs-expected-behavior>
---

> **Claude Code note:** `[Skill: X]`/"Load `X`" below means invoke the `x` skill via the Skill tool (auto-discovered from `.claude/skills/x/`).

# Workflow: Bug Fix & Troubleshooting
**Trigger Command:** `/sap-dev-bug-fix`

## Context & Core Constraints
- **No Live Business Data:** The Agent is connected to the DEV environment only. Testing and bug verification must rely on source code logic analysis or **Mock Data / Sample Data** provided manually by the User.
- **Cross-Impact Analysis (Mandatory):** Any logic/condition change must be evaluated for regression risks affecting other objects or business flows that reuse this component. If a risk is detected, the Agent **MUST report and request User approval** before making any code changes.
- **Governing Rules:** Operates under the Iron Laws, Red Flags, and Token Efficiency rules in `sap-dev-rule.md` (§6-10) — in particular, a root-caused fix is not a verified fix until Phase 4's unit test evidence exists, and it is not a *safe* fix until `[Skill: activation-guard]` confirms the edited object activated clean AND nothing that depends on it broke as a side effect; progress updates use `[Skill: caveman]`.
- **Project (rule §4):** resolve the target project under `projects/` from the first argument or the user's prompt; if absent, ask ONE question during Phase 1 before creating any file. Read `projects/<project>/project.md` first (SAP system, default package, current TR). All file outputs of this workflow live under `projects/<project>/`.

Arguments: $ARGUMENTS

---

## Skill Execution Sequence (Routing)

### Phase 1: Context Initialization & Mock Data Gathering
1. **Load `grill-me` & `scratchpad`**:
   - Initialize `scratchpad` to document the entire troubleshooting process.
   - Actively interview the User to gather 2 critical pieces of information:
     - (1) The name of the failing Object (CDS View, RAP BO, Class) or App.
     - (2) **Mock Data**: The incorrect input/output behavior observed by the User (e.g., "When passing SO Type = ZOR2, expected Output = 10 but got 0").

### Phase 2: Root Cause Analysis (RCA) & Impact Analysis
2. **Load `fs-data-model-extractor` (Trace mode) & `fs-logic-behavior-translator`**:
   - Starting from the reported Object, trace down the source code from the UI/Consumption layer to the Base/Database layer.
   - Pinpoint the exact line of code, JOIN condition, or logic block (e.g., CASE/WHEN) causing the issue by running a dry-run analysis with the provided Mock Data.
3. **Execute Impact Analysis**:
   - Check where else this View/Logic is being used. Evaluate if changing this logic poses a risk to other dependent Apps or reports.

### Phase 3: Solution Proposal & Risk Reporting (Halt for Approval)
- **Action:** The Agent MUST NOT modify the code immediately. It MUST present to the User:
  - (1) The root cause of the bug.
  - (2) A draft of the proposed code fix (snippet).
  - (3) A **Cross-Impact Report** detailing any potential risks.
- **HALT and wait for the User's explicit approval** of the proposed solution.

### Phase 4: Fix Implementation & Quality Assurance
4. **Load `cds-view-entities`, `cds-analytical-views`, `rap`, `modern-abap-syntax`, `oo-design-patterns` & `abap`**:
   - Implement the code changes based on the approved solution. Ensure the code uses modern ABAP syntax and strictly follows Clean ABAP principles (checked via `abap`). Apply an OO design pattern only if refactoring complex logic genuinely warrants one.
   - If the approved fix's root cause requires extending SAP standard behavior rather than editing a Z/Y object directly, also load `[Skill: badi-enhancement]` to find/implement the appropriate released BAdI instead of any other extension mechanism.
5. **Load `abap-unit-testing`**:
   - Create or update the Local Test Class (`cl_abap_unit_assert`) using Test Doubles and the Mock Data provided by the User.
   - **Note:** Creating an ABAP Unit Test using Mock Data is mandatory to compensate for the lack of real data in DEV and to prevent future regressions.
6. **Boundary, Activation & Ripple Check — `[Skill: activation-guard]`**:
   - Ensure NO Standard Objects were modified (Z/Y custom only).
   - Deploy and activate the edited object(s) yourself using your system-execution tool — do not just hand the user a to-do list. Run all 3 `[Skill: activation-guard]` gates: full activation log (no unresolved Error, every Warning explicitly assessed against strict(2)/Clean Core, never dismissed just because activation returned "success"), confirmed active state (not sitting inactive server-side), and — the gate that matters most for a fix touching an object other things already depend on — the ripple/cross-impact check against every consumer identified in the Phase 3 Cross-Impact Report. Re-verify each of those consumers is still active with no new error, not just the object you directly edited.
   - Only after all 3 gates pass on the edited object AND every impacted consumer, report the final object list with confirmed Activation Status per object (never "should be fine, please activate").

## Output Format

Report chat progress in `[Skill: caveman]` style (short, evidence-based) — narration only. Save a Fix Report to `projects/<project>/walkthroughs/walkthrough_bugfix_[ObjectName].md` in full detail, NOT caveman-compressed (`sap-dev-rule.md` §10): the root cause, the approved fix applied, the ABAP Unit Test evidence (not "should work"), the Cross-Impact Report, the `[Skill: activation-guard]` gate results for the edited object and every re-checked consumer, and the exact list of objects with their confirmed Activation Status.
