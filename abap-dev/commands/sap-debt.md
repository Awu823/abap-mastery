---
description: Gom mọi comment `shortcut:` (giới hạn cố ý đã chấp nhận, theo skill lean-abap) của 1 project — quét source Z-object trên SAP (read-only, qua MCP grep theo package) + drafts trong scratchpads/ — thành sổ nợ kỹ thuật `projects/<project>/system_analysis/debt-ledger.md`, giữ trạng thái/ghi chú cũ, đánh dấu RESOLVED khi shortcut biến mất. Dùng khi muốn xem/tổng hợp nợ kỹ thuật, trước release, hoặc định kỳ.
argument-hint: <project> [package-override]
---

> **Claude Code note:** `[Skill: X]` below means invoke the `x` skill via the Skill tool (auto-discovered from `.claude/skills/x/`). Where a step needs an MCP tool not yet loaded, use `ToolSearch` first (`sap-dev-rule.md` §9).

[ROLE & OBJECTIVE]
Build or refresh the technical-debt ledger of ONE project from every `shortcut:` comment defined by [Skill: lean-abap] §6. Strictly read-only on the SAP system — no object is edited, activated, or locked.

[INPUT]
- Project: first argument of $ARGUMENTS. Missing → ask ONE question (rule §4); never guess. Read `projects/<project>/project.md` first (SAP system / MCP tool, default package).
- Package(s): second argument if given, else the default package from `project.md`. Neither present → ask; do not scan an unspecified package.

[EXECUTION]

**Step 1 — Scan the SAP system (read-only).** Verify the session's SAP MCP tool exists and is authenticated (§9). Use its source-grep action at package level (e.g. `action: "grep"` with `packages: [...]`, `include_subpackages: true`, pattern `shortcut:`), raising `max_results` until the result is not truncated — a truncated scan is reported as truncated, never as complete. For each hit capture: object type + name, method/include if available, line, raw comment text. If the tool or connection is unavailable, say so and continue with Step 2 only, marking the ledger header `SAP scan: NOT RUN (<reason>)`.

**Step 2 — Scan local drafts.** Grep `shortcut:` with `path: projects/<project>/scratchpads` (rule §4 — searches from the workspace root do not see `projects/`). Hits in drafts whose object already appears in Step 1 with the same text are duplicates — keep the SAP row only. The rest are `draft` rows (not yet on the system).

**Step 3 — Parse.** Split each comment into `Limit` and `Upgrade when` on `; upgrade when`. A comment missing either part goes to the **Malformed** section, verbatim — do not invent the missing part.

**Step 4 — Merge with the existing ledger.** If `debt-ledger.md` exists, read it first. Row identity = object + normalized comment text. Existing rows keep their `First seen`, `Status`, and `Note`. Rows no longer found get `Status: RESOLVED (not found <today>)` — never delete a row. New rows get `Status: OPEN`, `First seen: <today>`.

**Step 5 — Write** `projects/<project>/system_analysis/debt-ledger.md` with the template below.

**Step 6 — Report** in chat ([Skill: caveman], rule §10): counts (OPEN / new / RESOLVED this run / malformed / draft-only), scan coverage (packages, truncated or not), and any row whose `Upgrade when` trigger the user may already have hit — stated as a question, not a conclusion (§8). Link the ledger file.

[OUTPUT TEMPLATE]
```
# Technical Debt Ledger: <project>

Last scan: <YYYY-MM-DD> · System: <MCP tool / system> · Packages: <list> (subpackages: yes/no)
SAP scan: <OK, N hits | TRUNCATED at N | NOT RUN (reason)> · Draft scan: <N hits>

## Open & Resolved Shortcuts
| # | Object | Type | Location (method / line) | Limit | Upgrade when | Source (SAP / draft) | First seen | Status | Note |
|---|---|---|---|---|---|---|---|---|---|

## Malformed (missing limit or trigger — fix the comment)
| Object | Location | Raw comment |
|---|---|---|
```

[SCOPE GUARDS]
- Read-only on SAP (§2). Fixing a shortcut is a separate task (`/sap-task` or a workflow) with its own TR + Package + [Skill: activation-guard].
- Only the ledger file is written — no edits to source drafts, TS, or `project.md`.
- Business data is never read; only source code.
