---
description: Kết thúc phiên làm việc cho 1 project — ghi handoff, cập nhật "Current state" trong project.md, rồi sync repo projects để session mới (cùng hoặc khác device) tiếp tục được bằng /sap-resume.
argument-hint: <project> [topic]
---

[ROLE & OBJECTIVE]
Close out the current work on ONE project so a brand-new session — on this device or another — can resume without re-deriving anything. Sessions are per-device and are NOT synced; the project files are (rule §4 "Projects store"). Pure file + projects-git operation: no SAP system is touched.

[INPUT]
- Project: first argument (`$ARGUMENTS`). Missing → the active project of this session; still unknown → ask once.
- Topic: optional second argument (kebab-case). Absent → derive from the session's main purpose.

[EXECUTION — 4 steps]

**Step 1 — Write the handoff.** Invoke [Skill: handoff] → `projects/<project>/scratchpads/handoff_<topic>_<yyyymmdd>.md`. Same topic + same day → update that file instead of creating a second one.

**Step 2 — Refresh `project.md`.**
- Replace the `## Current state` block (create it right after the metadata table if missing). It is a SNAPSHOT, not a log: overwrite, ≤10 lines:
  ```markdown
  ## Current state
  <!-- Snapshot overwritten by /sap-handoff; read first by /sap-resume. Max 10 lines. -->
  - Updated: <yyyy-mm-dd> · <device/hostname>
  - Phase: <workflow + step, e.g. create-transactional-app step 4/7>
  - Done this session: <1 line>
  - Next: <the single next action, with TS/ledger section ref>
  - Blockers: <none | what/who>
  - Last handoff: scratchpads/handoff_<topic>_<yyyymmdd>.md
  ```
- Also update `Current TR`, `Status`, and `## Objects & Status` rows if they changed this session (evidence-based, §8).

**Step 3 — Sync.** Run the `/sap-sync` procedure (`.claude/commands/sap-sync.md`) for `<project>` with message `<project>: handoff <topic>`. No remote / push failed → say so explicitly: the other device will NOT see this handoff yet.

**Step 4 — Report** ([Skill: caveman]): handoff path, commit hash + pushed yes/no, and the exact line to type on the next session/device: `/sap-resume <project>`.

[SCOPE GUARDS]
- One project per run; multi-project sessions run it once per project.
- `## Current state` holds pointers, never full content — detail lives in the handoff file and the ledger.
