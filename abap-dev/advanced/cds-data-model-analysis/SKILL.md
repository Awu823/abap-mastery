---
name: cds-data-model-analysis
version: 1.0
description: Analyze and design the data model BEHIND a complex report or CDS view — keys, foreign-key relationships, join/association conditions, cardinality, and fan-out/duplication risks across released I_* views and Z-tables, then design the join tree BEFORE any CDS syntax is written. Use whenever a report spans 2+ tables/views whose relationships are not pinned down, or the user asks how tables relate, which fields to join on, why a report shows duplicate rows or inflated totals — "join các bảng", "xác định key/foreign key", "quan hệ giữa các bảng", "duplicate rows in report", "cardinality", "phân tích cấu trúc CDS view", "build join tree". Syntax authoring stays with cds-analytical-views / cds-view-entities; finding the right released view is find-released-cds-view.
---

# CDS Data-Model Analysis (Keys, Relationships, Join Design)

The design step BEFORE authoring: given a report requirement spanning multiple tables/views, produce a verified relationship map (keys, join conditions, cardinality) and a join tree that cannot silently duplicate or drop rows. Syntax authoring is owned by [Skill: cds-analytical-views] (joins/aggregation/parameters) and [Skill: cds-view-entities] (RAP composition) — hand off to them once the model is decided.

## The 5-Step Join-Tree Design Procedure

Run these in order for any report touching 2+ sources; write the result down (TS §data-model or a scratchpad) before any CDS is authored.

1. **Anchor the grain.** Decide what ONE row of the report represents (e.g. "one billing document item per row"). The source whose primary key matches that grain is the root of the join tree. Every later decision is checked against this grain.
2. **Inventory each source's keys.** For each table/view involved: list its primary key fields (see "Reading Keys" below). A join is only safe to reason about once you know both sides' full keys.
3. **Pin each relationship.** For every pair to be connected: which fields link them, and what is the cardinality from the root side (to-one or to-many)? Prefer reading it off an existing artifact (exposed association with declared cardinality, DDIC foreign key) over inferring it; if inferred, verify with a data probe (see deep-dive) before trusting it.
4. **Check every to-many hop for fan-out.** Any `[0..*]`/`[1..*]` hop multiplies the root's rows. If the report aggregates amounts/quantities after such a hop, the totals are silently inflated — restructure (aggregate the many-side first in its own view, or push the many-side to a separate association the consumer follows on demand) rather than accept it.
5. **Choose join vs association per hop** — the decision table in [Skill: cds-analytical-views] (flattened-always → join; optional/reusable path → association). This skill decides the shape; that skill owns the syntax.

## Reading Keys and Relationships Off Existing Objects

| Artifact | Where the relationship info lives |
|---|---|
| Released `I_*` CDS view | `key` elements in the element list; exposed associations (name, target, cardinality `[..]`, ON condition) — read the view source via ADT/MCP. Finding the right view is [Skill: find-released-cds-view]'s job |
| Custom Z-table (DDIC) | `key` fields (always first, `NOT NULL`); DDIC foreign keys with check table + n:m cardinality; `curr`/`quan` fields' reference-field pairing |
| Custom Z CDS view | Same as I_* views; plus the base table's DDIC keys underneath |
| No artifact yet (new design) | The FS/TS defines the relationships — extract via [Skill: fs-data-model-extractor]; this skill then validates the extracted model (grain, cardinality, fan-out) before it enters the TS |

## Cardinality Quick Reference

- CDS association: `[min..max]` — `[1..1]` to-one, `[1..*]` to-many; **default when omitted is to-one (`[0..1]`)**. Declared cardinality is semantic documentation the compiler checks against usage — a to-many association used where a single value is expected produces the warning "the association can modify the cardinality of the results set" (that warning IS the fan-out alarm; never suppress it without running Step 4).
- DDIC foreign key: `n:m` notation (`1`, `C` on the FK side; `1`, `C`, `N`, `CN` on the check side) — documentation-only in most contexts. **DDIC foreign keys are NOT enforced by the database on ABAP SQL writes** — never assume referential integrity holds in a Z-table just because an FK is defined; a data probe is the only proof.

## Fan-Out / Duplication Checklist (run before finalizing any join tree)

- [ ] Every hop's cardinality is known and written down (not guessed).
- [ ] No amount/quantity aggregation happens downstream of an unaggregated to-many hop.
- [ ] To-many hops the report only sometimes needs are associations (consumer-side resolution), not flattening joins.
- [ ] LEFT OUTER hops: fields from the right side are null-guarded (`coalesce`) if used in expressions/filters.
- [ ] Composite-key joins name ALL shared key fields in the ON condition — a partial-key ON is the most common accidental fan-out.
- [ ] For Z-tables: FK integrity actually verified against data, not assumed from the DDIC definition.

## Deep Dive

For DDIC foreign-key mechanics (cardinality value semantics, text tables, why there's no DB-level enforcement), CDS association attributes in path expressions (filter conditions, join-type override, `1:` cardinality override), the exposed-vs-used association distinction with verified examples, worked fan-out scenarios, and the data-probe verification procedure, read [references/deep-dive.md](references/deep-dive.md).

## Output Format

- Deliver the relationship map as a table: source → target, link fields, cardinality, evidence (where each fact was read from — view source / DDIC / data probe / TS), fan-out risk (yes/no + mitigation).
- Deliver the join tree as an indented list from the root grain down, each hop annotated join-vs-association.
- State explicitly which relationships are verified vs `[assumption]` — an unverified cardinality is a design risk, not a footnote.

## References

- [references/deep-dive.md](references/deep-dive.md) — mechanics, worked examples, verification procedures
- [SAP ABAP Cheat Sheets — CDS View Entities](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/15_CDS_View_Entities.md) (its executable example `zdemo_abap_cds_ve_assoc` is the association ground truth used here)
- [ABAP Keyword Documentation — DDIC Foreign Keys](https://help.sap.com/doc/abapdocu_758_index_htm/7.58/en-US/abenddic_database_tables_forkey.htm)
