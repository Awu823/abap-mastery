# CDS Analytical / General-Purpose Views — Deep Dive

Read this for version-gating on the newer CDS view entity features, the input-parameter-vs-WHERE-filter decision, and a worked aggregation+parameter report pattern the base SKILL.md and `cds-syntax-guide.md` don't cover. Nothing below duplicates the basic view/aggregate/parameter/join templates already in `references/cds-syntax-guide.md` — read that first for the plain templates. Sources/citation trail: [references/sources-deep-dive.md](sources-deep-dive.md).

## Version Safety on ABAP Cloud Targets

**`DEFINE VIEW ENTITY` itself, plain aggregate functions (`SUM`/`AVG`/`MIN`/`MAX`/`COUNT`), basic joins, and basic input parameters are baseline on any real ABAP Cloud target** — the CDS view entity statement was introduced at Release 780 (2020 Q3), which is older than any BTP ABAP Environment/S/4HANA Cloud system in active use today. Don't hedge on these. What's genuinely newer and worth checking against the target release:

| Feature | Introduced | Practical impact if unavailable |
|---|---|---|
| `DEFINE TABLE ENTITY` (CDS table entity — ABAP Cloud successor of DDIC database tables) | Release 914 (2502 / 2025 Q1) | Use a classic DDIC database table instead — this is genuinely recent, don't assume it's there on anything but a very current target |
| `$projection.reuse_exp` — reusing an element-list expression in another operand position of the same view | Release 784 (2105 / 2021 Q2) | Repeat the full expression at each use site instead of referencing it by alias |
| New cardinality syntax for joins (`{MANY\|ONE\|EXACT ONE} TO {MANY\|ONE\|EXACT ONE}`) | Release 791 (2302 / 2023 Q1) | Omit it — the join still works, you just lose the optimizer hint from declaring a known 1:1/1:N shape explicitly |
| `UNION` clause in CDS view entities (with nestable branches) | Release 783 (2102 / 2021 Q1) | Combine the result sets in ABAP instead (e.g., append two internal tables) rather than at the CDS layer |
| `DISTINCT` addition for `SELECT` in CDS view entities | Release 783 (2102 / 2021 Q1) | Deduplicate in ABAP after the fact |
| `EXCEPT`/`INTERSECT` set operators | Release 785 (2108 / 2021 Q3) | Express the set-difference/intersection logic as a `WHERE NOT IN (...)`-style subquery instead |
| CDS analytical projection view (`DEFINE TRANSIENT VIEW ENTITY AS PROJECTION ON ...` with `PROVIDER CONTRACT ANALYTICAL_QUERY`) | Release 786 (2111 / 2021 Q4) | Not available — model the report as a regular aggregated CDS view entity instead of a true analytical/OLAP query artifact |

If the target release is unusually old or unconfirmed and a TS depends on one of these, verify in ADT rather than assume.

## Typed Literals (missing from the base reference)

`cds-syntax-guide.md` doesn't show typed literals — real CDS source uses them for anything beyond a bare untyped string/number literal:

```cds
abap.int4'12345'    as SomeInt,      // typed numeric literal
abap.dats'20240101' as SomeDate,     // typed date literal

// A currency/quantity typed literal needs its reference-field annotation,
// same rule as an aggregated amount field (see cds-syntax-guide.md's Aggregate pitfall)
@Semantics.amount.currencyCode: 'CurrencyCode'
abap.curr'12.34' as SomeAmount,
```

Typed literals for CDS view entities were introduced at Release 783 (2102 / 2021 Q1) — same release as `UNION`/`DISTINCT` above.

## Reuse Expressions (`$projection.x`) — New Content

Introduced at 784/2105 (2021 Q2, see table above). Lets you reference a previously-defined element's expression elsewhere in the same element list instead of repeating it:

```cds
cast( net_amount as abap.dec(15,2) )        as ConvertedAmount,
$projection.ConvertedAmount * discount_rate as DiscountedAmount,
```

Decision cue: reach for this the moment the same computed value (a cast, a unit conversion, an arithmetic result) feeds two or more downstream expressions in the same view — it keeps the logic in one place instead of two copies that can silently drift apart during a later edit. On an older/unconfirmed target where this isn't available, repeat the full expression instead.

## Input Parameter vs. WHERE-Clause Filter (decision)

Both restrict rows; they are not interchangeable defaults. An input parameter is a **mandatory, named slot in the view's own signature** — `cds-syntax-guide.md`'s own consumption example (`SELECT FROM zi_salesorderbydate( p_date = @lv_date )`) shows every caller must supply it. A plain field is an **optional, freely composable filter** any caller applies (or doesn't) via `WHERE`/OData `$filter`/`@UI.selectionField`.

| Situation | Use |
|---|---|
| Value is supplied fresh by the caller on every invocation and must be baked into the `WHERE` clause before the database executes (a report's date range, a threshold picked on a selection screen) | **Input parameter** — pushes the filter to the database as part of the query plan, not as a post-fetch ABAP filter |
| Fixed business rule that applies regardless of who's calling (exclude deleted records, current fiscal year via `$session.system_date`) | **Plain `WHERE` clause, no parameter** — bake it into the view once; no caller can opt out and none needs to supply anything |
| Consumer needs to filter ad hoc on an ordinary field, optionally, combined freely with other filters (Fiori Elements list report filter bar, `@UI.selectionField`) | **Expose the field normally** — a parameter is a mandatory, singular slot; an exposed field is optional and stackable with other conditions |
| The value feeds an expression computed on every row before grouping (a conversion rate, a cutoff reused in several derived fields) | **Input parameter + `$projection.reuse_exp`** — see above, avoids repeating the parameter reference at each use site |

Don't reach for an input parameter just because "it's a filter" — if every consumer should be free to apply or skip the condition, it belongs on an exposed field, not in the parameter list.

## Worked Example: Aggregation + Input Parameter (common reporting pattern)

The pattern `/sap-dev-create-report` typically needs: a date-range-filtered summary, grouped by a business key, with a currency-aware sum. This combines both of `cds-syntax-guide.md`'s existing aggregate pitfalls (every non-aggregated field must be in `group by`; a summed amount needs its currency-reference annotation) into one realistic view:

```cds
@AccessControl.authorizationCheck: #CHECK
@EndUserText.label: 'Sales Order Summary by Customer'
define view entity ZI_SalesOrderSummary
  with parameters
    p_from_date : abap.dats,
    p_to_date   : abap.dats
  as select from zsalesorder
{
  key customer_id                                 as CustomerId,
      count( * )                                  as OrderCount,
      @Semantics.amount.currencyCode: 'CurrencyCode'
      sum( net_amount )                            as TotalNetAmount,
      currency_code                                as CurrencyCode,
      avg( cast( net_amount as abap.dec(15,2) ) )  as AvgOrderValue
}
group by
  customer_id,
  currency_code
where
      order_date >= $parameters.p_from_date
  and order_date <= $parameters.p_to_date
```

```abap
SELECT FROM zi_salesordersummary( p_from_date = @lv_from, p_to_date = @lv_to )
  FIELDS CustomerId, OrderCount, TotalNetAmount, CurrencyCode, AvgOrderValue
  INTO TABLE @DATA(lt_summary).
```

`currency_code` has to be in both the `SELECT` list and `group by` — it's neither aggregated nor a key, and it's the mandatory reference field for `sum( net_amount )`'s currency annotation. Leaving it out breaks activation (missing `group by` member); aggregating it instead of grouping by it would silently produce a wrong per-currency total.

## Null-Safe Joins with `coalesce`

`cds-syntax-guide.md`'s Joins section doesn't mention null handling. Any field pulled through a `left outer`/`right outer` join can be null on the unmatched side — wrap it before it reaches a UI or a further computation:

```cds
left outer join zcustomer as cust on so.customer_id = cust.customer_id
{
  ...
  coalesce( cust.customer_name, 'Unknown Customer' ) as CustomerName,
```

Decision cue: apply `coalesce` (or a `CASE ... WHEN ... IS NOT NULL`) to every outer-join field that feeds a display or a downstream expression — an unhandled null doesn't error, it just silently propagates as blank/initial.

## Set Operators for Combining Report Sources

Not in the base skill at all. `UNION` (783/2102, branches can nest, unlike DDIC-based views), `DISTINCT` (783/2102), `EXCEPT`/`INTERSECT` (785/2108) — see the version table above. Use case: a report combining two structurally-compatible sources (e.g., current-year live data and a prior-year archive table) into one result set.

Decision cue: default to `UNION ALL` semantics when duplicates across branches are structurally impossible (e.g., partitioned by year) — plain `UNION`/`DISTINCT` implies a dedup pass that costs more for no benefit in that case. Reach for `EXCEPT`/`INTERSECT` only for a genuine set-difference/intersection requirement (e.g., "customers who ordered in Q1 but not Q2") — it's a rare ask, not a general-purpose filtering tool.

## When a Plain Aggregated View Isn't Enough

For a genuine multi-dimensional OLAP-style consumption (measures/dimensions modeled explicitly for SAC/Analysis for Office, or an `InA - UI` OData service binding — see [Skill: odata]'s binding-type table), a **CDS analytical projection view** (`DEFINE TRANSIENT VIEW ENTITY AS PROJECTION ON ... PROVIDER CONTRACT ANALYTICAL_QUERY`, 786/2111+) is the purpose-built construct — not this skill's plain aggregated view entity pattern. For a typical Fiori Elements list report or analytical list page, the aggregated view entity shown above is the right level; don't reach for the analytical-projection-view construct unless the FS specifically calls for a query/cube-style analytical app.
