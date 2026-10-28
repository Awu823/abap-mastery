# Sources — Citation Trail (cds-data-model-analysis)

Research conducted 2026-07-17 for `artifacts/scratchpads/scratchpad_cds-data-model-analysis-skill.md`. `sap-docs-extend-mcp` down (404 route not found, confirmed 2026-07-15 same week — not retried); `cds-kb-mcp` not connected; live SAP read via `mcp__sap_bmw_dev__SAP` attempted but the session returned a SAML login redirect (expired auth) — no live-system fact is used in this skill. All grounding is from directly fetched public sources below.

## Primary sources fetched and used

1. **`https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/src/zdemo_abap_cds_ve_assoc.ddls.asddls`** (144 lines) and **`zdemo_abap_cds_ve_assoc_e.ddls.asddls`** (40 lines) — the CDS View Entities cheat sheet's own executable association example, fetched in full. Source of (all verbatim or near-verbatim):
   - association declaration syntax with cardinality + ON condition; `$projection.` prefix rule for renamed source fields;
   - cardinality semantics: `[min..max]`, min optional default 0, default-to-one when unspecified, min≠`*`, max≠`0`, "documenting the semantics of the data model", "a non-matching cardinality usually produces a warning";
   - the exact fan-out warning text: "The association _fli can modify the cardinality of the results set";
   - used-vs-exposed distinction incl. "It is up to the consumer... Only then, a join is performed";
   - "associations are internally transformed into joins", source=left side, left outer join default, the `coalesce` null-handling idiom;
   - path-expression attributes: filter conditions, explicit join type requiring `WHERE`, the `1:` cardinality override and its warning-silencing effect.

2. **`https://help.sap.com/doc/abapdocu_758_index_htm/7.58/en-US/abenddic_database_tables_forkey.htm`** ("DDIC - Foreign Keys", ABAP Keyword Documentation, AS ABAP 7.58 mirror) — fetched via curl (plain HTML, real content). Source of:
   - FK fields form the primary key of the check table; multiple FKs per table;
   - the no-enforcement quote: "The developer must consider this in writes made using ABAP SQL, since there is no automatic check";
   - FK cardinality `n:m` value semantics (`1`/`C` × `1`/`C`/`N`/`CN`), documentation-purpose except maintenance/help views; generic FK forcing `CN:m`;
   - FK field types (no key fields / key fields / key fields of a text table);
   - text-table mechanics: primary key = check table's + one `LANG` field, one text table per check table.
   - **Provenance caveat**: this is the Standard ABAP 7.58 mirror — the ABAP-Cloud (`abapdocu_cp`) equivalent page is linked by the Cloud-scoped cheat sheet `26_ABAP_Dictionary.md` under the same page name but renders as a JS shell and could not be fetched. The 26 cheat sheet (Cloud-scoped) itself confirms the FK concept applies in ABAP Cloud ("Note the concept of foreign keys..." with that link); exact Cloud-vs-758 wording differences are `[unverified]`.

3. **`https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/26_ABAP_Dictionary.md`** (1,237 lines) — "DDIC Database Tables" section read in full. Source of: primary key mandatory, key fields first + `NOT NULL`, `clnt` client-dependency convention, `curr`/`quan` reference-field requirement, `key`-field type restrictions (`string`/`rawstring` excluded).

## Checked but not used / dead ends (honesty trail)

- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/15_CDS_View_Entities.md` — 73-line stub; its real content is the executable example in `src/` (source #1 above), which is what was used.
- `https://help.sap.com/doc/abapdocu_cp_index_htm/CLOUD/en-US/...` (Cloud keyword-doc pages, both `?file=` and direct `.html` forms) — JS shell / client-side redirect, no fetchable body. Classic 7.58 mirror used instead, caveat recorded above.
- `mcp__sap_bmw_dev__SAP` read of `DDLS I_CURRENCY` — returned a SAML login form (session expired); no live released-view content was obtainable this session. The SKILL.md's discovery-procedure table therefore describes the *procedure* (read `key` elements + exposed associations from the view source) without quoting any specific I_* view's content.

## Original (non-cited) content, authored for this workspace

- The 5-step join-tree design procedure, the fan-out checklist, the worked inflated-total scenario (ORDERS/DELIVERIES), the data-probe SQL pattern, and the relationship-map/join-tree output format are reporting/design discipline authored for this skill — grounded in the verified mechanics above but not themselves quotes from any source. The text-table "every row twice on bilingual systems" implication is derived from the verified text-table structure (one row per language), not a quoted incident.
- No ABAP class, annotation, transaction, or statement name appears in this skill that was not directly observed in a fetched source this session or already established in this workspace's existing skills. Notably, `@ObjectModel.foreignKey.association` was deliberately OMITTED — commonly cited in the wild, but no fetchable primary source confirmed it this session.
