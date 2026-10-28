# Sources — Deep-Dive Research Trail (rap-query-provider)

Research conducted 2026-07-14 for the ABAP dev skill enrichment initiative Phase 2 batch 2 (`artifacts/scratchpads/scratchpad_abap-dev-skill-enrichment.md`). `sap-docs-extend-mcp` was reported unavailable for this entire session (not retried) — fell back to `curl`-fetching the official SAP-samples cheat sheets directly, plus `WebSearch`/`WebFetch` for the class-library-specific gaps the cheat sheets didn't cover.

## Primary sources retrieved (curl, public GitHub raw content, no auth)

- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/36_RAP_Behavior_Definition_Language.md` (1,266 lines)
- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/08_EML_ABAP_for_RAP.md` (3,224 lines)
- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/33_ABAP_Release_News.md` (8,016 lines) — same release-news digest earlier pilots used; release-number claims below found by grepping for RAP/custom-entity terms and mapping each finding's line number to the nearest preceding `Release NNN (QQQQ)` header via a regex that also matches quarter-less headers (`Release (\S+?)(?:\s*\((\d+)\))?\s*</summary>`).
- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/19_ABAP_for_Cloud_Development.md` (285 lines) — checked for query-provider mentions; none found.

## Key negative finding — the cheat-sheet corpus does not cover this API at all

`grep -ni "IF_RAP_QUERY_PROVIDER\|QUERY_PROVIDER\|Query Provider\|Custom Entit"` across all four fetched files above returned **zero hits** for anything at the `IF_RAP_QUERY_PROVIDER` interface/method level (`get_paging`, `get_sort_elements`, `get_filter`, `cx_rap_query_provider`, etc.). The repo also has no dedicated cheat sheet for Custom Entities/Query Providers. This matches the pattern `abap-sql-amdp`'s sources file already documented: `33_ABAP_Release_News.md` tracks language/keyword/DDL changes, not class-library interface additions.

What the release-news file DOES cover is the **CDS custom entity DDL concept** itself (the entity type the interface operates on), which is where this deep-dive's version-safety table comes from instead.

## Verified release-number claims (CDS custom entity / DDL level)

| Finding | Line (Cloud section) | Nearest header | Release (quarter) |
|---|---|---|---|
| "CDS Custom Entities" origin — "used in the RAP framework to implement ABAP queries in CDS" | 2038 | line 2023 | 775 (1902 / 2019 Q1) |
| "CDS Custom Entity Extensions" (`EXTEND CUSTOM ENTITY`) | 970 | line 959 | 789 (2208 / 2022 Q3) |
| New cardinality syntax (`{MANY\|ONE\|EXACT ONE} TO ...`), applies to CDS custom entities among others | 865 | line 845 | 791 (2302 / 2023 Q1) |
| "Stricter Rules for Association ON Conditions in CDS Custom Entities" | 148 | line 137 | 916 (2508 / 2025 Q3) |

Quarter mapping applied the fixed formula: `02`→Q1, `05`→Q2, `08`→Q3, `11`→Q4.

## WebSearch / WebFetch attempts for the interface itself

- `WebSearch: "IF_RAP_QUERY_PROVIDER get_paging get_sort_elements get_filter method ABAP release"` — search-engine-synthesized summary describing `get_paging( )`/`get_sort_elements( )`/`get_filter( )` roughly as this skill's existing SKILL.md/template already document; explicitly stated it found no minimum-release information.
- `WebSearch: "IF_RAP_QUERY_REQUEST get_requested_elements CX_RAP_QUERY_PROVIDER attributes reason ABAP"` — surfaced `get_requested_elements( )` (for `$select`) and a `CX_RAP_QUERY_FILTER_NO_RANGE` exception class, both from search-result synthesis, not a quoted primary source.
- `WebFetch: https://help.sap.com/docs/abap-cloud/abap-rap/interface-if-rap-query-paging` and `.../interface-if-rap-query-provider` — both returned only the page's generic SPA shell, no body content. Confirmed via direct `curl -sL` too.
- `WebFetch: https://kernich.de/posts/custom-cds-views-with-unmanaged-queries-in-abap-rap/` — **succeeded** (independent technical blog, not SAP-official). Confirmed a reference table listing `$select` → `io_request->get_requested_elements( )`. Used only for the explicitly-caveated mention in `references/deep-dive.md`.

## Important negative/scoping finding

`IF_RAP_QUERY_PROVIDER`'s own release/version could not be independently confirmed this session from any source reached. The deep-dive's version-safety table therefore only asserts a **floor** (the interface cannot predate the CDS custom entity concept it implements against, 775/1902/2019 Q1) rather than an exact introduction release for the interface itself.

## Not independently verifiable this session

- The exact method name `get_requested_elements( )` and the exception class `CX_RAP_QUERY_FILTER_NO_RANGE` — plausible and corroborated by two independent search-derived sources, but not confirmed against SAP-official text.
- Decision-criteria content (count/filter/orderby edge cases) in `references/deep-dive.md` is reasoned from the documented mechanics already in this skill's own template/SKILL.md, not sourced from new external text.
