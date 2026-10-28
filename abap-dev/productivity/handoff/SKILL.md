---
name: handoff
version: 1.0
description: Summarizes current progress, outstanding tasks, and crucial context into a structured handoff note; use before context runs out or compaction occurs, or whenever work needs to transition seamlessly to another agent or a new session.
---

# Handoff

Preserve working state across a compaction or session boundary so the next agent/session can resume without re-deriving anything.

## Instructions

1. Review the current state of the task, including completed steps and remaining open items.
2. Generate a concise but comprehensive markdown summary containing:
   - **Current Status**: What has been achieved.
   - **WIP**: What is currently being worked on.
   - **Next Steps**: Explicit instructions for the next agent or session.
   - **Critical Context**: Important constraints, bugs encountered, or decisions made — including TR number, package, and system/connection in SAP workflows.
   - **Ledger Pointer**: If a [Skill: scratchpad] ledger exists for this work, give its exact path and state which rows are DONE / IN PROGRESS / REGRESSED. The ledger is the single source of truth — a handoff without it loses the most critical state.
3. Save the summary to `projects/<project>/scratchpads/handoff_<topic>_<yyyymmdd>.md`, where `<project>` is the active project of the work being handed off (rule §4: every output belongs to one project). If the work genuinely has no project yet, ask which project before writing. Then tell the user the path. Present inline instead only if the filesystem is unavailable.
4. Point `projects/<project>/project.md`'s `## Current state` snapshot (≤10 lines, template in `.claude/commands/sap-handoff.md`) at this file via its `Last handoff:` line, so `/sap-resume` finds it. Sessions are per-device and never synced — when the next session may run on another device, use `/sap-handoff <project>` instead, which also commits + pushes the projects repo.
