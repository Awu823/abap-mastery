# Sources — Deep-Dive Research Trail (`sap-fiori-apps-reference`)

Research conducted 2026-07-14 for the ABAP dev skill enrichment initiative (`artifacts/scratchpads/scratchpad_abap-dev-skill-enrichment.md`, Phase 2 batch 2 round 2). `sap-docs-extend-mcp` was confirmed down for this entire session. This skill has no cheat-sheet-repo match at all (it's a Fiori-Launchpad-URL utility, not an ABAP language topic) — research for this one was direct analysis of the skill's own bundled files plus live-URL checks, not `curl` against the SAP-samples repo.

## Sources examined

- `.claude/skills/sap-fiori-apps-reference/SKILL.md` — read in full.
- `.claude/skills/sap-fiori-apps-reference/references/AppList.json` (4,767,917 bytes, 5,236 entries) — loaded and analyzed in full with a Python script (not a sample): checked every entry's key set, counted missing `Semantic Object - Action` values, and counted/grouped duplicate `Semantic Object - Action` values across the whole file.
- `.claude/skills/sap-fiori-apps-reference/scripts/fiori-url-generator.py` — read in full; `find_app()`'s substring-first-match behavior verified by re-running its exact logic (case-insensitive `in` check over `App Name`, first hit wins, no scoring) against the file directly.
- `.claude/skills/sap-fiori-apps-reference/LICENSE.txt` — read in full; confirmed generic MIT boilerplate with no export-date information.
- `git log --follow --diff-filter=A -- .claude/skills/sap-fiori-apps-reference/references/AppList.json` — confirmed the only commit touching this file is this workspace's initial port commit (2026-07-04), not informative about the underlying SAP data's vintage.

## Quantified analysis results (exact figures)

```
Total apps: 5236
Missing Semantic Object-Action: 385 (7.4%)
Distinct Semantic Object-Action values shared by 2+ apps: 164
Total apps involved in a shared Semantic Object-Action: 426
```

Top shared values found (for illustration, not exhaustive):
- `*-analyzeSBKPIDetails`: 19 apps
- `WorkflowTask-displayInbox`: 18 apps
- `ClosingTaskList-analyze`: 8 apps
- `ApplicationJob-show`: 7 apps
- `SupplyNetworkKPI-drilldown`: 7 apps

Reproduced substring-collision example (verified by re-running `find_app`'s exact matching logic against the file): searching for the substring `"maintenance request"` matches 3 distinct apps — *Create Maintenance Request* (F1511A, `MaintenanceWorkRequest-create`), *Screen Maintenance Requests* (F4072, `MaintenanceWorkRequest-edit`), *My Maintenance Requests* (F4513, `MaintenanceWorkRequest-manage`). Confirmed the SKILL.md's own worked example (App ID F1511A) is factually accurate against the bundled data — the finding is about the matching strategy's fragility for other, less fortuitously-ordered search terms, not an error in the existing example.

## Attempted freshness cross-check (inconclusive, reported honestly)

Attempted to independently estimate the snapshot's vintage by checking whether the live SAP Fiori Apps Reference Library exposes a queryable static endpoint. `curl` against the base viewer URL returns HTTP 200 but only a UI5/SPA application shell — no data-bearing static API was found this way. Did not attempt a full browser-driven crawl of the live library, judged disproportionate effort for this task's scope. Reported as "currency unknown, cross-check attempted but inconclusive" rather than silently dropping the question or guessing a vintage.

## Live URL checks

This skill's `SKILL.md` and bundled files cite no live external URLs beyond the placeholder example domain (`https://myserver.com:44300`, illustrative non-resolvable example host — not a real endpoint needing a liveness check). No broken-URL findings for this skill.
