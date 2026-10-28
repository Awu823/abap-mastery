---
description: Tạo mới một dự án trong projects/ — skeleton 6 thư mục con chuẩn + project.md metadata. Bắt buộc chạy trước khi bất kỳ workflow/task nào ghi output cho dự án đó (hook chặn ghi vào dự án chưa tồn tại — rule §4).
argument-hint: <project-name> [mô tả ngắn / SAP system / package / TR]
---

[ROLE & OBJECTIVE]
Create ONE new project workspace under `projects/` — the explicit project-creation step rule §4 requires. This is a pure filesystem operation: no SAP system is touched, no TR/Package is consumed.

[INPUT]
- Project name: first argument. Arguments: $ARGUMENTS
- If the name is missing: ask for it in one line — do not guess.

[EXECUTION — 5 steps]

**Step 1 — Validate the name.**
- kebab-case, lowercase, no diacritics, no spaces (`a-z`, `0-9`, `-` only).
- Recommended shape: `<customer>-<workstream>` (e.g. `bmw-zbom`, `nfg-zsd09`). A name without a customer prefix is allowed but confirm it's intentional.
- If `projects/<name>/` already exists → STOP and report; never overwrite, never "re-init" an existing project (its `project.md` is edited by hand instead).
- If `projects/` itself is missing on this device → STOP: the projects store is not linked yet (README "Multi-device projects", `.claude/scripts/link-projects.ps1`). Never create a plain `projects/` folder in its place.

**Step 2 — Gather metadata ([Skill: grill-me], max 1 round, all fields may be "TBD").**
From the remaining arguments or one short question round: mô tả 1 dòng, SAP system (MCP tool name + client, e.g. `mcp__sap_bmw_dev__SAP` — DEV client 080), default Package, current TR. Missing values are recorded as `TBD` — §2's TR+Package ask will fire later at build time; do not block project creation on them.

**Step 3 — Create the skeleton (Bash `mkdir -p`, then Write `project.md`).**
```
projects/<name>/
├── project.md
├── fs_docs/
├── technical_specifications/
├── scratchpads/
│   └── review/
├── walkthroughs/
├── metadata_extensions/
└── system_analysis/
```
`project.md` template (bilingual headers like the TS template; fill from Step 2):

```markdown
# Project: <name>

| Field | Value |
|---|---|
| Customer / Engagement | <customer or TBD> |
| Description | <1 dòng> |
| SAP system (MCP tool) | <e.g. mcp__sap_bmw_dev__SAP — DEV client 080, or TBD> |
| Default Package | <ZPKG or TBD> |
| Current TR | <TR number or TBD> |
| Status | active |
| Created | <yyyy-mm-dd> |

## Current state
<!-- Snapshot overwritten by /sap-handoff; read first by /sap-resume. Max 10 lines. -->
- Updated: <yyyy-mm-dd> · project created
- Next: <first workflow to run, e.g. /sap-dev-fs-analytic <name> ...>
- Last handoff: none

## Objects & Status
<!-- One row per SAP object this project owns; workflows update this as they build. -->
| Object | Type | Status | Notes |
|---|---|---|---|

## Key documents
<!-- Links to the project's own TS/walkthrough/analysis files as they appear. -->
```

**Step 4 — Rename this session (rule §4, mandatory).** Call `mcp__ccd_session_mgmt__set_session_title` with `<name>_<main purpose of this session>` — the project directory name verbatim, then a short kebab-case purpose (e.g. `bmw-zbom_project-setup`, `bmw-sd-apis_fs-analysis`). Applies even when the project is expected to have only this one session.

**Step 5 — Report.** [Skill: caveman] narration: project path created, metadata recorded vs TBD, session retitled to `<...>`. Remind: every workflow/task for this project now passes `<name>` as its first argument, `project.md` is the first file read at workflow start, and any NEW session for this project is titled `<name>_<purpose>`. The project exists only on this device until `/sap-sync <name>` pushes the projects repo.

[SCOPE GUARDS]
- Never create a project as a side effect of another workflow — that workflow must STOP and send the user here instead (rule §4).
- Never delete or rename an existing project directory from this command.
