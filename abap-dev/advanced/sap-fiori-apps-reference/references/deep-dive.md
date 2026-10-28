# SAP Fiori Apps Reference — Deep Dive

Read this for a quantified analysis of the bundled `references/AppList.json` snapshot run this session (ambiguity/gap rates, not guesses), a negative finding on the snapshot's currency, and decision criteria + a troubleshooting procedure the SKILL.md body is currently missing. Sources/citation trail: [references/sources-deep-dive.md](sources-deep-dive.md).

## Honest Scope Note

Like `atc-cloudification`, this is a config/data-lookup utility skill, not an ABAP-language topic — there is no ABAP release-gating to report and a "Version Safety" table would be manufactured content. Unlike `atc-cloudification`, though, this is **not** a "little to add" case: direct analysis of the bundled 5,236-entry snapshot this session turned up concrete, previously-undocumented ambiguity rates and a real limitation in the bundled script's matching logic, both below.

## Verified Finding: Snapshot Currency Is Unverifiable, Not Just Unstated

Checked all fields present in `references/AppList.json` (`App Name`, `App ID`, `UI Technology`, `Application Component`, `App Description`, `Semantic Object - Action`, `Technical Catalog`, `Technical Catalog Title`, `Transaction Codes`, `OData Service`, `OData V4 Service Group`) — **none of them is an export/vintage date**. `LICENSE.txt` has only a generic MIT copyright line, which is this workspace's own port year, not evidence of when the underlying SAP data was exported. `git log --follow --diff-filter=A` on the file shows only this workspace's initial commit (2026-07-04) — again the port date, not the source vintage.

Attempted an independent freshness cross-check against the live SAP Fiori Apps Reference Library (`fioriappslibrary.hana.ondemand.com`) — the site is reachable (HTTP 200) but is a client-rendered SPA with no exposed static search API found via `curl` in this session, so no independent vintage estimate could be established this way either.

**Conclusion, stated plainly rather than hedged**: the snapshot's currency is genuinely unknown. Don't imply it's "recent" just because the workspace itself is recent, and don't assume an app's absence from the snapshot means the app doesn't exist in the customer's real system — it may simply postdate this export. This directly informs the MCP-vs-offline decision rule below.

## Quantified Finding: How Often the Snapshot Is Ambiguous or Incomplete

Ran a direct analysis of all 5,236 entries in `AppList.json` this session (not a sample — the full file):

- **385 apps (7.4%) have no `Semantic Object - Action` value at all** (empty/`NaN`). The bundled script's `generate_url()` already raises a clear `ValueError` for this case, which is correct — the finding here is that this is a **common** failure mode (roughly 1 in 13 apps), not a rare edge case worth a passing mention. Expect to hit this regularly, especially for background-job/monitoring-style apps that have no launchable UI intent.
- **164 distinct `Semantic Object - Action` values are shared by 2 or more different apps** (426 apps total, ~8.1% of the snapshot). Concrete examples found: `WorkflowTask-displayInbox` is shared by 18 different "My Inbox"-variant apps; `*-analyzeSBKPIDetails` is shared by 19 different KPI-drilldown apps; `ApplicationJob-show` by 7 apps. This means a Semantic Object-Action pair alone does **not** uniquely identify which app will actually launch — the target Fiori Launchpad resolves it against whatever tile is assigned in the *user's own* catalog/role, which may not be the specific app this skill looked up by name.

## Decision Criteria: When a Single Semantic Object-Action Isn't Enough

The SKILL.md body treats "Semantic Object-Action found → URL is done" as the end state. Given the 8.1% collision rate above, add this check before presenting a generated URL as authoritative:

- If the resolved `Semantic Object - Action` is one of the ~164 shared values, **say so explicitly** to the user rather than presenting the URL as a guaranteed launch of the specific app they named — e.g., "this URL's intent (`WorkflowTask-displayInbox`) is shared by several inbox-style apps in the standard library; which one actually opens depends on what's assigned in your target system's catalog for this user/role."
- This is not a bug to "fix" in the generation logic (there's no way to disambiguate from the intent string alone — that's how FLP intent-based navigation is designed to work) — it's a caveat to surface, not silently omit.

## Verified Finding: `find_app()`'s Matching Strategy Is First-Match, Not Best-Match

`scripts/fiori-url-generator.py`'s `find_app()` (used by the single-shot `generate_url` CLI path) does a case-insensitive substring search and **returns the first app in file order whose `App Name` contains the search term** — there is no ranking, no exact-match preference, no scoring.

Reproduced concretely this session: searching `"maintenance request"` (the substring used internally when the SKILL.md's own worked example searches for the full name "Create Maintenance Request") matches **3 different apps**: *Create Maintenance Request* (F1511A), *Screen Maintenance Requests* (F4072), *My Maintenance Requests* (F4513). The SKILL.md's own worked example happens to get the right one only because *Create Maintenance Request* is first in file order for that term — this is coincidental positioning, not a guarantee the matching logic provides.

## Decision Criteria: Search Mode First, Generate Mode Only With a Confirmed Exact Name

Add this rule (missing from the current SKILL.md's Implementation Steps, which jump straight from "search" to "fetch full details for the matching App ID" without flagging that the underlying script's single-shot path skips this disambiguation):

- For anything **other than** an exact, already-confirmed full "App Name" string, always run search mode (`python3 scripts/fiori-url-generator.py search "<term>"`, or the MCP search tool) first and inspect the full candidate list — never feed a partial/keyword term straight into the single-shot generation path and trust the first hit.
- Only call the single-shot generation path once a specific candidate's exact `App Name` (or better, its `App ID`, fetched via detail lookup) has been confirmed from that candidate list.

## Decision Criteria: MCP vs. Offline Snapshot — What To Do When They Disagree

The SKILL.md body already says "prefer MCP when connected, snapshot only to cross-check or when offline" — it doesn't say what to do if the two sources give **different** answers for the same App ID (a real possibility precisely because the snapshot's vintage is unknown, per the finding above). Decision rule to add:

- Trust the MCP result as current — it reflects SAP's presently-published Fiori Apps Reference Library, whereas the snapshot's age is unverifiable.
- Treat a disagreement itself as a signal, not just a tiebreak: it means the app's configuration changed at some point between the snapshot's (unknown) vintage and now. Flag this to the user rather than silently picking MCP's answer — the reference library (either source) describes SAP's **standard-delivered** configuration; if the target system has copied/extended this app into a Z-catalog, neither source reflects that customization, and the generated URL should be spot-checked against the actual target system once, not assumed correct from the reference data alone.

## Troubleshooting: App Not Found / Ambiguous Result

Consolidating the two verified failure modes above into one procedure:

1. Run search mode first (or MCP search) — never jump straight to single-shot generation for a keyword/partial name.
2. If zero candidates: the app may genuinely not exist under that name, or the snapshot may simply be missing it (unverifiable vintage — see above). Don't conclude "this app doesn't exist" from the offline snapshot alone if an MCP server is reachable; try MCP before reporting a dead end.
3. If 2+ candidates: pick by matching the user's actual intent against `App Description`/`Application Component`, not just the shortest/first name match — and if the winning candidate's `Semantic Object - Action` turns out to be one of the ~164 shared values, surface that caveat per the decision rule above rather than presenting the URL as unambiguous.
4. If the candidate has no `Semantic Object - Action` (the 7.4% case): report plainly that this app cannot be launched via an FLP intent URL — don't guess a value or fall back to a transaction-code-based URL unless the user explicitly asks for that alternative launch mechanism.
