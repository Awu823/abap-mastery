---
name: lean-abap
version: 1.0
description: Minimal-code discipline for ABAP Cloud — write the smallest change that delivers the exact same behavior, by climbing a reuse ladder (need it? → existing Z-object → released SAP content → declarative CDS/RAP feature → language built-in → minimum code) before writing anything, while never cutting authorization, validation, EML error handling, data-loss protection, or anything the TS/user asked for. Also defines the `shortcut:` comment convention for deliberate known limits (collected by /sap-debt) and the skipped/unchecked/risk reply footer. Use BEFORE drafting or modifying any ABAP class/method, CDS view, BDEF, behavior pool, or handler code, and when reviewing code for excess (hand-rolled reimplementations, unneeded abstractions, dead code). Triggers include "write/modify ABAP", "implement method", "viết code", "sửa code", "tối giản code", "code thừa", "rút gọn", "YAGNI", "shortcut comment", "lean".
---

# Lean ABAP

**Role:** The senior developer who writes the least code that fully solves the task.

**Core law:** fewer lines is a means, *same effect* is the requirement. A lean version that changes behavior, drops a safeguard, or moves DB work into ABAP is not lean — it is a regression.

## 1. Reach map — before writing anything

List every place the change must reach, then check what it could break:
- Callers / where-used of the method, class, or view being changed.
- Dependent layers: interface view → projection → DDLX → BDEF/projection BDEF → service definition/binding.
- Tests (ABAP Unit, CDS/OSQL test doubles) and any `shortcut:` already sitting on the touched code.

This list feeds [Skill: activation-guard] Gate 3 — draft it now, verify it after activation.

## 2. The ladder — stop at the first rung that delivers the requirement

| Rung | Question | Where to look |
|---|---|---|
| R0 | Is this needed at all? | TS Coding Implementation Plan / the user's request. Not there → do not build it (rule §6). In a TS-driven build R0 is already answered by the TS — never re-open it there. |
| R1 | Does this system already have it? | Existing Z-objects in the project package (MCP search/grep by name or pattern), shared helper classes, existing CDS fields/associations. |
| R2 | Does SAP ship it as released content? | [Skill: find-released-cds-view] (field/computed value already in an I_* view), [Skill: released-abap-classes] (UUID, JSON, time, mail, …), released BAdIs/APIs. |
| R3 | Can it be declarative instead of imperative? | CDS expression/CASE/association/annotation over virtual element or ABAP; RAP managed features (managed numbering, static field control `readonly`/`mandatory`, `etag master`, draft, `determine action`) over handler code; `@Consumption.valueHelpDefinition` over custom value-help code; `@Semantics`/`@ObjectModel` over formatting code. |
| R4 | Can a language built-in do it? | `VALUE`/`COND`/`SWITCH`/`REDUCE`/`FILTER`/`CORRESPONDING`/table expressions/string templates/built-in functions over hand-written loops — see [Skill: modern-abap-syntax]. |
| R5 | Only now: the minimum that works | No unused parameters/methods/attributes; no interface or factory with one implementation (unless the TS or an ABAP Unit seam needs it — [Skill: abap-unit-testing]); no config table for a value the TS fixes; no GoF pattern unless [Skill: oo-design-patterns] says it is warranted; no speculative "future-proof" branches. |

## 3. Same-effect check — the lean version must keep

- Identical output: same fields, values, messages (text + severity), and sort/aggregation results.
- Identical safeguards: everything in §4.
- Same or better performance class: never replace a JOIN/CDS pushdown with SELECT + LOOP to save lines; never add SELECT in LOOP; a shorter `READ`/`LOOP` must not turn a hashed/sorted access into a linear one.
- Same public contract: method signatures, view field names, and BDEF entity/action names stay stable unless the TS changes them.

If you cannot show all four, keep the longer version.

## 4. Never cut (governance floor — fewer lines never removes these)

- Authorization: `AUTHORITY-CHECK`, DCL, RAP `authorization master`/instance/global auth handlers ([Skill: authorization-iam]).
- Validation at trust boundaries: RAP validations, inbound API payload checks ([Skill: z-api-fwk]), user input.
- Error handling: EML `FAILED`/`REPORTED` population, RAP messages, `TRY…CATCH` with specific exception classes, framework error matrices.
- Data-loss protection: locks, ETag, save-sequence correctness, commit/rollback semantics.
- Clean Core: released APIs/CDS only, EML/released APIs for writes (rule §3).
- Anything the TS or the user explicitly asked for, and [Skill: activation-guard]'s 3 gates.

## 5. Bug fixes

Where-used first. Fix the root cause once in the shared code, not a patch at every caller. A fix that touches more than the root cause needs a reason in the reply.

## 6. `shortcut:` comments — deliberate, known limits

When you deliberately accept a limit (allowed by TS/user, or the minimum rung R5 implies one), mark it at the exact line:

```abap
" shortcut: <the limit>; upgrade when <trigger>
" shortcut: max 1 open order per customer assumed (TS §5); upgrade when multi-order per customer is required
```

```cds
// shortcut: currency conversion skipped, all amounts in company code currency; upgrade when foreign-currency postings appear
```

Rules:
- Both parts are mandatory — the limit AND the upgrade trigger. A trigger is an observable condition, not "later".
- Never use it to hide a §4 item (no `shortcut: no auth check`) — those are not cuttable.
- Never use it for unfinished work — that is a blocker to report, not a shortcut.
- One line, English (rule §13), placed directly above the affected statement.
- `/sap-debt <project>` collects every `shortcut:` into `projects/<project>/system_analysis/debt-ledger.md`.

## 7. Reply footer

Every chat answer that produces or modifies code ends with 1–2 lines:

```
Skipped/unchecked: <what you deliberately did not build or did not verify — or "none">
Risk: <what the user must know before relying on it — or "none">
```

Applies to the Manager's chat replies and to dev subagents' return messages. Not inserted into saved deliverables (TS, review reports, walkthroughs keep their own templates).

## 8. Where each mode applies

| Context | Behavior |
|---|---|
| TS-driven build (`/sap-dev-create-*`, API workflows, dev subagents) | Ladder R1–R5 on HOW only. WHAT is fixed by the TS — never cut, merge, or skip a TS object or field. If a TS object looks unnecessary, flag it to the Manager; do not drop it. |
| Single prompt / `/sap-task` | Build exactly what was asked. If a clearly smaller option delivers the same effect, name it in one line and let the user choose — never silently swap. |
| FS → TS analysis (`/sap-dev-fs-analytic*`) | Scope Challenge step (2.E): R0–R3 may challenge FS requirements before they enter the TS — the user decides each one in writing; nothing is dropped silently. |
| Code review (`/sap-dev-code-review`, snippet review) | Report excess against the ladder + the same-effect proof, and list existing `shortcut:` comments with whether their trigger is already met. Advisory only. |
