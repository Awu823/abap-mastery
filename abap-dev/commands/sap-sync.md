---
description: Đồng bộ repo projects (store nằm ngoài workspace) — commit + pull --rebase + push. Chạy khi xong task / trước khi chuyển sang device khác. Chỉ đụng repo projects, không đụng repo workspace.
argument-hint: [project] [commit message]
---

[ROLE & OBJECTIVE]
Sync the **projects store** — `projects/` is a per-device junction to a separate git repo outside the workspace (rule §4 "Projects store"). Invoking this command IS the user's consent to commit + push THAT repo. Never touch the workspace repo from here.

[INPUT]
- Optional project: first argument (`$ARGUMENTS`) — limits the commit to `projects/<project>/`. Absent → sync all changes.
- Optional message: the rest of the arguments. Absent → derive a short summary from the changed paths.

[EXECUTION — 6 steps]

**Step 1 — Preflight.**
- `projects/.git` must exist (test the path directly — `git -C projects` on a plain folder would walk up to the WORKSPACE repo). Missing → STOP: point the user to README "Multi-device projects" / `.claude/scripts/link-projects.ps1`.
- `git -C projects remote get-url origin` — no remote → commit locally only (Steps 2-4), report "no remote", skip Steps 5-6.

**Step 2 — Show changes.** `git -C projects status --short [-- <project>/]`. Nothing to commit → skip to Step 5 (still pull + push pending commits).

**Step 3 — Secrets guard.** If any changed path looks like a secret not covered by `projects/.gitignore` (`*.env`, `ts24.env`, `*credential*`, `*secret*`, private keys) → STOP, list them, ask. Never commit them on your own.

**Step 4 — Commit.** `git -C projects add -A [-- <project>/]`, then commit with message `<project|multi>: <message>`.

**Step 5 — Pull.** `git -C projects pull --rebase`. Conflict → STOP: `git -C projects rebase --abort`, list the conflicting files, ask the user how to resolve. Never auto-resolve business documents, never force anything.

**Step 6 — Push.** `git -C projects push` (first push: `push -u origin HEAD`). Never `--force`.

**Report** ([Skill: caveman]): commit hash + file count, pushed yes/no, `git -C projects status -sb` first line as evidence (must show no ahead/behind).

[SCOPE GUARDS]
- Only the projects repo. Never `git add` / commit / push the workspace repo from this command.
- Never rewrite projects history (no amend of pushed commits, no rebase -i, no force-push).
