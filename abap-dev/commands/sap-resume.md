---
description: Bắt đầu / tiếp tục làm 1 project trong session mới (cùng hoặc khác device) — pull repo projects, đọc project.md + handoff mới nhất, tóm tắt trạng thái và bước tiếp theo, chờ user xác nhận rồi mới làm.
argument-hint: <project>
---

[ROLE & OBJECTIVE]
Rebuild working context for ONE project at the start of a session. Sessions are per-device and NOT synced; the project files are (rule §4 "Projects store"). Read-only except for `git pull` of the projects repo — no SAP mutation, no file writes.

[INPUT]
- Project: first argument (`$ARGUMENTS`). Missing → ask once; never guess.

[EXECUTION — 5 steps]

**Step 1 — Pull.** If `projects/.git` exists and has a remote: `git -C projects pull --ff-only`.
- Fails because histories diverged → STOP: unpushed work exists on another device or here. Tell the user to run `/sap-sync` where that work lives (or here), never force, never reset.
- Uncommitted local changes → report them (they are from an earlier session on THIS device); do not stash or discard.
- Offline / no remote → continue, but state clearly that the context may be stale.

**Step 2 — Read base context.** `projects/<project>/project.md`. Missing project dir → STOP (typo, or the project only exists on another device and was never synced).

**Step 3 — Locate the latest handoff.**
1. `Last handoff:` pointer in `## Current state`.
2. Fallback: Glob `handoff_*.md` with `path: projects/<project>/scratchpads` (always pass `path` — searches from the workspace root do not see `projects/`), pick the newest by the `_yyyymmdd` in the filename — NOT by mtime (git checkout resets mtimes).
3. None → say so; resume from `project.md` alone.

Read the handoff; if it has a Ledger Pointer, read that ledger and take its DONE / IN PROGRESS rows as the source of truth.

**Step 4 — Retitle the session** (rule §4): `mcp__ccd_session_mgmt__set_session_title` → `<project>_<purpose>`, purpose = short kebab-case of the handoff's Next step (e.g. `bmw-zbom_resume-bdef-validation`).

**Step 5 — Report + confirm** ([Skill: caveman]): phase, done, next step, blockers, current TR / package / SAP system from `project.md` (flag TBD or possibly expired TR per §2). Ask the user to confirm the next step before doing anything — then continue inside the matching workflow (`/sap-dev-*`, `/sap-task`) so its gates still apply.

[SCOPE GUARDS]
- Never re-run completed ledger steps on the strength of the handoff alone — verify against the ledger / system first (§12 evidence rule applies to handoffs too).
