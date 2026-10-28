# Sources — Deep-Dive Research Trail (`cds-analytical-views`)

Research conducted 2026-07-14 for the ABAP dev skill enrichment initiative (`artifacts/scratchpads/scratchpad_abap-dev-skill-enrichment.md`, Phase 2 batch 2). `sap-docs-extend-mcp` was confirmed down for this entire session (not retried) — fell back to `curl`-fetching the official SAP-samples cheat-sheet GitHub repo directly.

## Primary sources retrieved

- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/15_CDS_View_Entities.md` (74 lines) — this file turned out to be an index/pointer page, not a prose cheat sheet: it links to the actual demo CDS source files under the repo's `src/` folder rather than containing syntax text itself. Followed those links:
  - `src/zdemo_abap_cds_ve_sel.ddls.asddls` (237 lines) — operands/expressions/typed literals/session variables/input parameters demo. Source for the Typed Literals section and the `$parameters`/session-variable syntax confirmation.
  - `src/zdemo_abap_cds_ve_agg_exp.ddls.asddls` (63 lines) — aggregate expressions demo.
  - `src/zdemo_abap_cds_ve_joins.ddls.asddls` (132 lines) — joins demo. Source for the `coalesce()` null-handling pattern on outer-join fields.
  - `src/zdemo_abap_cds_ve_assoc.ddls.asddls` (144 lines) — associations demo. Read for completeness but **not used** in this deep-dive — association syntax is explicitly owned by `[Skill: cds-view-entities]` per this skill's own scope note; not duplicated here.
- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/33_ABAP_Release_News.md` (8,016 lines total; "ABAP for Cloud Development" section is lines 32–2925). Grepped for CDS-view-entity-related terms and mapped every finding's line number to its nearest preceding release header, using the quarter-tolerant regex (`Release\s+(\S+?)(?:\s*\((\d+)\))?\s*</summary>`). Verified with a one-off Python script; spot-checked several mappings by reading the surrounding `<details>` block directly.

## Verified release-number claims (CDS-view-entity-scoped only)

| Finding | Release (quarter) | Verified via |
|---|---|---|
| `DEFINE VIEW ENTITY` (CDS view entity) itself introduced | 780 (2005 / 2020 Q3) | Line 1638–1639: "A new kind of CDS view is available: the CDS view entity... defined with the statement DEFINE VIEW ENTITY." Confirmed no earlier mention exists. |
| `DEFINE TABLE ENTITY` (CDS table entity) introduced | 914 (2502 / 2025 Q1) | Line 277–278, header at line 261: "CDS Table Entities... A new kind of CDS entity is available: the CDS table entity... using the statement DEFINE TABLE ENTITY. CDS table entities are the ABAP Cloud successor of DDIC database tables." |
| `$projection.reuse_exp` (reusing expressions) | 784 (2105 / 2021 Q2) | Line 1323–1324, header at line 1312: "CDS View Entity, Reusing Expressions... using the syntax $projection.reuse_exp." |
| New cardinality syntax for joins (`{MANY\|ONE\|EXACT ONE} TO {MANY\|ONE\|EXACT ONE}`) | 791 (2302 / 2023 Q1) | Line 863, header at line 814: "New Cardinality Syntax for Joins... can also be used in SQL path expressions and CTE associations." |
| `UNION` clause in CDS view entities (nestable branches) | 783 (2102 / 2021 Q1) | Line 1414–1415, header at line 1403: "UNION clauses are now supported in CDS view entities... branches of union clauses can be nested within each other in CDS view entities." |
| `DISTINCT` addition for `SELECT` | 783 (2102 / 2021 Q1) | Line 1418–1419, same header block as UNION. |
| `EXCEPT`/`INTERSECT` set operators | 785 (2108 / 2021 Q3) | Line 1209–1211, header itself: "CDS View Entity, New Set Operators... EXCEPT, INTERSECT." |
| Typed literals for CDS view entities | 783 (2102 / 2021 Q1) | Line 1426–1427, same header block as UNION/DISTINCT: "Typed literals are now available for CDS view entities." |
| CDS analytical projection view (`DEFINE TRANSIENT VIEW ENTITY AS PROJECTION ON`, `PROVIDER CONTRACT ANALYTICAL_QUERY`) | 786 (2111 / 2021 Q4) | Line 1174–1175, header at line 1154: "CDS Analytical Projection Views... defined using DEFINE TRANSIENT VIEW ENTITY AS PROJECTION ON. The value for the provider contract must be set to ANALYTICAL_QUERY." |

Quarter glosses computed with the fixed `YYMM`→quarter formula (`02`→Q1, `05`→Q2, `08`→Q3, `11`→Q4) — double-checked each row against that formula before writing them into `deep-dive.md`.

**Manager re-verification (2026-07-14, before integration)**: re-checked every quarter label in this table against the fixed formula (`02`→Q1, `05`→Q2, `08`→Q3, `11`→Q4), given this initiative's history of quarter-label slips. All held up, including `780 (2005)` → 2020 Q2 (`05`→Q2, correctly labeled in the original draft).

## Deliberately excluded (scope discipline)

- Association filter-condition/cardinality-bracket syntax from `zdemo_abap_cds_ve_assoc.ddls.asddls` — owned by `[Skill: cds-view-entities]`.
- `STRING_AGG` aggregate function, `COUNT` without mandatory `DISTINCT`, `GROUPING`/`GROUPING SETS` — all confirmed tagged `ABAP_SQL` topic in the release news (not `ABAP_CDS`), i.e. ABAP SQL `SELECT` statement features, not CDS view entity DDL syntax — left out to avoid scope creep into `[Skill: abap-sql-amdp]`'s territory.
- `@Environment.systemField` input-parameter annotation (release 761, no quarter) — scoped out: specific to implicit client-ID passing into AMDP-backed CDS table functions, not the general/analytical view pattern this skill's typical output targets.

## Live-URL check (per the workspace's incident-4 lesson)

Checked every URL currently cited in `cds-analytical-views/SKILL.md`'s References section with `curl -o /dev/null -w "%{http_code}"`:

| URL | Status |
|---|---|
| `https://github.com/SAP-samples/abap-cheat-sheets/blob/main/15_CDS_View_Entities.md` | 200 |
| `https://help.sap.com/docs/abap-cloud/abap-data-models/abap-data-models` | 200 |
| `https://help.sap.com/doc/abapdocu_cp_index_htm/CLOUD/en-US/ABENCDS_ANNOTATIONS.html` | 200 |

All live — no fix needed for this skill.
