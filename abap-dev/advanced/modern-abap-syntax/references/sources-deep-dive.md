# Sources — Deep-Dive Research Trail

Research conducted 2026-07-14 for the ABAP dev skill enrichment initiative (`artifacts/scratchpads/scratchpad_abap-dev-skill-enrichment.md`, Phase 1 pilot). `mcp-sap-docs`/`sap-docs-extend-mcp` (the intended primary source) was unreachable for the entire session (`Server sap-docs-extend-mcp unavailable`, retried multiple times, both `search` and `abap_feature_matrix` tools) — fell back to direct retrieval of the official SAP-samples cheat sheets via `curl`/GitHub API (public repo, no auth needed), which is the same upstream content those MCP tools wrap.

## Primary sources retrieved

- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/33_ABAP_Release_News.md` (8,016 lines) — official ABAP Keyword Documentation release-news digest, split into "ABAP for Cloud Development" (lines 32-2925) and "Standard ABAP" (2926+) sections. Used for every release-number claim below.
- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/05_Constructor_Expressions.md` (2,936 lines) — official syntax reference for VALUE/CORRESPONDING/NEW/CONV/EXACT/REF/CAST/COND/SWITCH/FILTER/LET/FOR/REDUCE. Used for the full `CORRESPONDING` addition table and worked examples.
- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/32_Performance_Notes.md` (2,531 lines) — official performance guidance; "Overusing Table Expressions" section (line 232) used for the field-symbol-caching trade-off.

## Verified release-number claims (line → release mapping done via a one-off script matching each finding to the nearest preceding `Release NNN (QQQQ)` header in `33_ABAP_Release_News.md`)

| Finding | Release (quarter) |
|---|---|
| `FINAL(...)` inline declaration (immutable variant, distinct from `DATA(...)`) | 789 (2208) |
| `CORRESPONDING` `DEFAULT` addition (with `MAPPING`) | 791 (2302) |
| Harmonization of table expressions and `READ TABLE` (new `TABLE KEY` variant) | 912 (2408) |
| `MOVE-CORRESPONDING`/`CORRESPONDING` `APPENDING BASE DEEP` additions for nested tables | 783 (2102) |
| `REDUCE` `NEXT` addition accepts compound assignment operators (`+=`, `-=`, `*=`, `/=`, `&&=`) | 781 (2008) |
| Object component selector (`->`) directly after a `VALUE`-based table expression — earlier restriction lifted | 767 (1702) |
| `CL_ABAP_CORRESPONDING=>CREATE_WITH_VALUE` method | 768 (1705) |

## Post-publication re-verification (2026-07-14, found during Phase 2 batch review)

A Phase 2 drafting agent flagged a methodology risk in the release-mapping script used here: it only matched release headers with a parenthesized quarter (`Release NNN (QQQQ)`), silently skipping headers like `Release 766` that have no quarter — a finding whose true nearest header was one of those would have been mis-attributed to an earlier, quarter-having header instead. Re-ran every release-number claim in the table above against a corrected script that also matches quarter-less headers: all 7 claims held up unchanged. The gap did not affect this file, but is noted here for anyone extending it later.

**Separately caught during the same review**: the calendar-quarter glosses (e.g. "2022 Q2") applied the wrong month→quarter mapping in 4 of the 7 table rows (the correct mapping for SAP's `YYMM` release codes is `02`→Q1, `05`→Q2, `08`→Q3, `11`→Q4 — Jan-Mar/Apr-Jun/Jul-Sep/Oct-Dec). Corrected in `references/deep-dive.md`: release 789 (2208) is 2022 **Q3** (was mislabeled Q2), release 791 (2302) is 2023 **Q1** (was Q2), release 783 (2102) is 2021 **Q1** (was Q2), release 781 (2008) is 2020 **Q3** (was Q2). The release numbers themselves were always correct — only the human-readable quarter gloss was wrong.

## Important negative finding (absence is the evidence)

`VALUE`, `COND`, `SWITCH`, `REDUCE`, `FILTER`, basic `CORRESPONDING`, and inline `DATA(...)`/`FIELD-SYMBOL(...)` declarations do **not** appear anywhere in `33_ABAP_Release_News.md`'s "ABAP for Cloud Development" section as introduction/origin entries — only their later refinements do (table above). The Cloud section's earliest release header is 767 (2017 Q1). Since these core constructs originate in classic ABAP 7.40 (2013), which predates the Cloud section's entire documented window, they are unconditionally baseline-available on every real ABAP Cloud target (BTP ABAP Environment, S/4HANA Cloud Public/Private Edition) — no such system runs a pre-2017 kernel. This is why `references/deep-dive.md` frames "which release is X available in" as the wrong question for the 8 core constructs, and reserves real version-risk framing for the newer refinements in the table above.
