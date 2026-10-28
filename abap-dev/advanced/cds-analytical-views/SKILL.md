---
name: cds-analytical-views
version: 1.0
description: Help with general-purpose and analytical CDS view entity authoring — expressions, built-in functions, aggregates/GROUP BY, input parameters, joins, CASE, date/string functions, CDS table entities, and UI/value-help annotations for plain reporting views with no RAP BO involved. Use even for small single-prompt view tasks — "create a CDS view for a report", "CDS aggregate/join/input parameter", "tạo CDS view", "thêm field vào view", "viết view báo cáo", "sum/group by trong CDS", "thêm parameter vào view". For RAP composition trees use cds-view-entities; for CDS access control/DCL use authorization-iam.
---

# CDS Analytical / General-Purpose Views

Guide for authoring general-purpose and analytical CDS view entities — the surface `/sap-dev-create-report` exercises for read-only reports over existing data, with no RAP business object involved. For RAP composition-tree modeling (root/child/projection views, admin fields, association vs composition decisions) see [Skill: cds-view-entities] instead. Full copy-paste templates live in [references/cds-syntax-guide.md](references/cds-syntax-guide.md).

## Ground Rules

- Use CDS view entities (`define view entity`) — never legacy `define view` (DDIC-based) for new objects.
- Naming per [Skill: naming-convention]: `ZI_*` for reuse/analytical views (this skill's typical output).
- Read SAP data only via released `I_*` CDS views, never physical SAP tables (workspace rule §3).
- Put UI/value-help annotations in a metadata extension (`@Metadata.allowExtensions: true` + `annotate view`), not in the view body.
- Every view needs `@AccessControl.authorizationCheck:` (`#CHECK` + a DCL role, or `#NOT_REQUIRED` with justification) — writing the DCL itself is owned by [Skill: authorization-iam].

## CDS Table Entities

```cds
define table entity ztab_salesorder {
  key client    : abap.clnt;
  key order_uuid: sysuuid_x16;
      order_id  : abap.numc(10);
}
```

Alternative to a classic DDIC database table when you need a table defined directly in CDS. Release-dependent feature — verify `define table entity` is supported on the target system's release before emitting one; default to a classic DDIC table if unsure. Can also serve as the persistence layer for a RAP BDEF — see [Skill: cds-view-entities] for the RAP-composition angle on that choice.

## Expressions & Built-in Functions

Casts, CASE (simple/searched), arithmetic, string functions (`concat`/`substring`/`length`/`upper`), date/time functions (`dats_days_between`/`dats_add_days`/`tstmp_current_utctimestamp`), and session variables (`$session.user` etc.) — full list with syntax in [references/cds-syntax-guide.md](references/cds-syntax-guide.md). Prefer these over pulling raw fields into ABAP and computing there — push logic to the data layer when it's a pure per-row transformation.

## Aggregate Expressions

`count`/`sum`/`avg`/`min`/`max` + `group by`. Two pitfalls that cause activation errors or wrong output:
- Every non-aggregated, non-grouped field in the `SELECT` list breaks activation — either aggregate it or add it to `group by`.
- Amount/quantity fields being aggregated need their `@Semantics.amount.currencyCode`/`@Semantics.quantity.unitOfMeasure` reference-field pairing upstream — aggregating a bare amount across mixed currencies produces a number that's silently wrong, not an error.

## Input Parameters

`with parameters` + `$parameters.<name>` in the `WHERE` clause; invoked from ABAP SQL as `SELECT FROM zi_view( p_param = @lv_value )`. Use for filters that must be pushed to the database (date ranges, thresholds) rather than filtered in ABAP after the fact — full template in the reference file.

## Joins vs Associations (decision)

| Situation | Use |
|---|---|
| Need the related data as exposed, reusable path expression (OData/ABAP SQL callers can choose to follow it or not) | **Association** — lazily resolved, cheaper when unused. Syntax lives with the association/composition decision table in [Skill: cds-view-entities]'s reference (shared syntax, not duplicated here). |
| Need the related fields unconditionally flattened into this view's own result set (e.g., an analytical view that must always show `CustomerName` without a follow-on association hop) | **Join** — `inner`/`left outer`/`right outer`/`cross`, syntax in this skill's reference file. |

Prefer associations by default; reach for a join only when the consumer needs the fields flattened, not optional.

## UI / Value-Help Annotations

`@UI.headerInfo`, `@UI.facet`, `@UI.lineItem`, `@UI.selectionField`, `@Consumption.valueHelpDefinition` — always via a metadata extension (`annotate view ... with { ... }`), never inline in the view body. Full templates in the reference file. [Skill: odata] and `/sap-dev-create-report`'s Fiori-Elements-mapping step both assume this skill owns the CDS-side annotation syntax.

## Deep Dive

For version-gating on newer view-entity features (CDS table entities, reuse expressions, set operators, analytical projection views), the input-parameter-vs-WHERE-filter decision, a worked aggregation+parameter report pattern, and null-safe joins, read [references/deep-dive.md](references/deep-dive.md).

## Output Format

- Provide complete CDS source code when creating new views (start from the templates in `references/cds-syntax-guide.md`)
- State explicitly whether the view needs an input parameter, aggregation, or a join — don't add any of the three unless the requirement calls for it
- Follow `ZI_`/`ZC_` naming per [Skill: naming-convention]

## References

- [references/cds-syntax-guide.md](references/cds-syntax-guide.md) — basic view template, expressions/functions, aggregate expressions, input parameters, joins, UI/value-help annotations
- [SAP ABAP Cheat Sheets — CDS View Entities](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/15_CDS_View_Entities.md)
- [SAP Help — ABAP Data Models Guide](https://help.sap.com/docs/abap-cloud/abap-data-models/abap-data-models)
- [SAP Help — CDS Annotations](https://help.sap.com/doc/abapdocu_cp_index_htm/CLOUD/en-US/ABENCDS_ANNOTATIONS.html)
