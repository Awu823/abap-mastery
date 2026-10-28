---
description: Micro-workflow cho task SAP đơn lẻ (không cần chạy nguyên workflow lớn) — classify yêu cầu theo 4 loại (mutation nhỏ / đọc-tra cứu / tư vấn / review code), nạp đúng skill theo bảng routing §15, áp governance tối thiểu (TR+Package nếu mutation, activation-guard sau mỗi thay đổi), rồi thực hiện. Nếu prompt thiếu thông tin hoặc yêu cầu chưa rõ, tự chạy grill-me hỏi ngược lại user để làm rõ trước khi thực hiện. Dùng khi giao 1 việc nhỏ, sửa nhanh 1 object, hỏi cách làm, tra cứu, hoặc nhờ review 1 đoạn code.
argument-hint: <mô tả task đơn lẻ>
---

> **Claude Code note:** `[Skill: X]` below means invoke the `x` skill via the Skill tool (auto-discovered from `.claude/skills/x/`). Where a step needs an MCP tool not yet loaded, use `ToolSearch` first (`sap-dev-rule.md` §9).

[ROLE & OBJECTIVE]
Handle ONE small, self-contained SAP task end-to-end with the workspace's full skill/governance machinery, WITHOUT the ceremony of the big workflows (no multi-phase ledger, no verify-loop, no TS). This command is the deterministic entry point for `sap-dev-rule.md` §15's routing table.

[INPUT]
- Task: $ARGUMENTS
- If $ARGUMENTS is empty: ask the user for the task in one line — do not guess.

[EXECUTION — 5 steps, keep it light]

**Step 1 — Classify & declare.** Match the task against §15's four shapes (object mutation / system-or-content lookup / how-to consulting / snippet review). Multi-shape tasks take the union. Then print the mandatory declaration line FIRST:
`Skills: [<skill-1>, <skill-2>, …]` — or `Skills: none — <reason>` if genuinely nothing matches (rare; say why).
If classification reveals this is actually a multi-object build, a full FS→TS analysis, or a formal review — STOP and point the user to the proper workflow (`/sap-dev-create-*`, `/sap-dev-fs-analytic*`, `/sap-dev-code-review`, `/sap-dev-bug-fix`) instead of running a compressed imitation of it here.

**Step 2 — Clarity gate (grill-me).** Analyze the prompt against what the classified shape materially needs before any work starts:
- *Mutation*: exact object + exact intended change unambiguous? TR + Package known (from the prompt or the active project's `project.md` — §4)? new-object naming intent clear?
- *Lookup*: business context/grain specific enough to pick the right source (not just "tìm view cho customer")?
- *Consulting*: target system/release known when the answer is version-gated? the actual use case concrete enough that the answer won't be generic?
- *Snippet review*: focus area stated? if debugging — expected-vs-actual behavior described?

If ANY material item is missing or ambiguous → invoke [Skill: grill-me] and ask the user back NOW (1 round, 1-3 targeted questions, multiple-choice where possible — micro-task cap per §10), then WAIT for the answers before proceeding. Never fill a gap with an assumption (§6 — missing info means STOP, not improvise) and never bury the question mid-execution after work already started. If everything material is present, proceed silently — no ceremony for a gate that passes.

**Step 3 — Consult before acting.** Invoke each declared skill and actually read what it prescribes for this task type BEFORE producing anything. Skill content wins over background knowledge. Read a skill's `references/` deep files only when genuinely producing that object type (progressive disclosure — don't bulk-load).

**Step 4 — Execute with the governance floor (per shape):**
- *Mutation*: TR + Package already confirmed by Step 2's gate (§2 — never assume, never touch a TR itself); name per [Skill: naming-convention] (explicit user-given name wins); climb [Skill: lean-abap]'s ladder before writing code — build exactly what was asked; if a clearly smaller option gives the same effect, name it in one line and let the user choose, never silently swap; make the change via the session's SAP MCP tool; then [Skill: activation-guard] all 3 gates (§5) — activation log incl. warnings assessed, confirmed active, dependents unbroken. One object at a time; a second object = go back to Step 1's scope check.
- *Lookup*: read-only (§2). Cite where each fact came from (view source, MCP result, skill reference). Business data stays untouched.
- *Consulting*: answer FROM the consulted skill; cite version-gates from its deep-dive when the target release matters; anything the skill doesn't cover is `[unverified]`, said explicitly (§8).
- *Snippet review*: [Skill: abap] lint/Clean-ABAP pass + the domain skill + [Skill: lean-abap] excess check (each excess finding carries its same-effect proof); findings cite line + evidence, facts separated from severity judgment; no auto-rewrite of the user's code unless asked.

**Step 5 — Report.** [Skill: caveman] narration (§10): what was done, evidence (activation log / source cited / skill section referenced), and any open risk or `[assumption]`. When code was produced or modified, end with [Skill: lean-abap] §7's `Skipped/unchecked` + `Risk` footer. For mutations: Activated and Correct are two separate claims (§8) — state both, with the evidence for each. No walkthrough file, no ledger — if the result matters beyond this chat, say ONE line suggesting where it would be persisted and let the user decide.

[SCOPE GUARDS]
- All of `sap-dev-rule.md` still applies — this command lowers ceremony, never the rules (§2 consent/Z-Y-only/TR, §5 activation-guard, §6 iron laws, §8 reporting language are all in force).
- File outputs (if any) follow §4: they belong to ONE named project (`projects/<project>/<standard-subfolder>/`). If the task produces a file and the project is unknown, ask which project (or point to `/sap-project-init`) before writing. A micro task with no file output needs no project. When a project IS known, read its `projects/<project>/project.md` for default system/package/TR before asking the user for them.
- No object/logic invention beyond what the user asked (§6). Missing/ambiguous info is Step 2's job — the grill-me gate runs BEFORE execution; a gap discovered later mid-execution still means stop-and-ask, never an assumption.
- If ≥3 fix attempts fail on the same object, stop and escalate per §7 — a micro task that fights back is not micro anymore.
