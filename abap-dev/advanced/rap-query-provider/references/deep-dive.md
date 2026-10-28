# RAP Query Provider — Deep Dive

Read this for what release actually gates a Custom Entity + `IF_RAP_QUERY_PROVIDER`, real decision criteria for the paging/sorting/filtering edge cases the template's comments gloss over, and when to reach for a Custom Entity at all. Sources/citation trail: [references/sources-deep-dive.md](sources-deep-dive.md).

## Version Safety

`IF_RAP_QUERY_PROVIDER` is a class-library interface, not a language keyword — the ABAP Release News digest (the source this workspace's other deep-dives use for release numbers) tracks BDL/CDS-DDL/statement changes, not interface introductions, so the interface's own exact release/quarter could not be independently confirmed this session `[unverified]`. What IS confirmed from that source is the entity type it operates on and its later refinements:

| Feature | Introduced | Practical impact if unavailable |
|---|---|---|
| CDS custom entities themselves — "CDS custom entities are used in the RAP framework to implement ABAP queries in CDS" | Release 775 (1902 / 2019 Q1) | No custom-entity/query-provider mechanism at all on that target — if the data genuinely comes from a real table, model it as a regular persistent CDS view entity instead |
| `EXTEND CUSTOM ENTITY` (add elements to an existing custom entity without touching its original definition) | Release 789 (2208 / 2022 Q3) | Add the new element directly to the original custom entity definition instead of via an extension |
| `{MANY\|ONE\|EXACT ONE} TO {MANY\|ONE\|EXACT ONE}` cardinality syntax for associations to/from a custom entity | Release 791 (2302 / 2023 Q1) | Use the older numeric cardinality syntax (`[0..*]`) — only the target cardinality is expressible, not source-and-target both |
| Stricter syntax rules for association `ON` conditions in CDS custom entities | Release 916 (2508 / 2025 Q3) | An association `ON` condition that compiled before may now raise a syntax error after a system upgrade — if an existing custom entity with associations suddenly fails activation, check the `ON` condition against current DDL rules before suspecting your query-provider class |

Since `IF_RAP_QUERY_PROVIDER` cannot exist before the CDS custom entity concept it implements against, 2019 Q1 is a hard floor — not itself a realistic risk on any current target. The 2025 Q3 tightening is the one worth actually checking if an existing custom entity starts failing activation.

## Decision: Skip the Count When the Client Didn't Ask For It

`io_request->is_total_numb_of_rec_requested( )` returning `false` isn't just a flag to check before calling `set_total_number_of_records` — treat it as a green light to skip computing the total altogether. If the "full filtered dataset" step in your `select` method is itself expensive (a join across several released CDS views, a per-row call to a remote API), materializing all of it just to `lines( )`-count it when nobody asked for `$count` wastes exactly the work you were trying to avoid by paging in the first place. Structure the method so the total-count path and the data-fetch path can short-circuit independently wherever the underlying source allows it (e.g., only run a `SELECT COUNT( * )` variant when the count is actually requested), rather than always fetching everything and conditionally reporting the count afterward.

## Decision: Filtering on a Field Your Data Source Doesn't Carry

`io_request->get_filter( )->get_as_ranges( )` hands you every field the client filtered on — including ones the value help/filter bar exposes but your `select` method's underlying source doesn't actually have (a computed field, a field from a join you don't perform, something only available after enrichment). Three ways to handle it, in order of preference:

1. **Push down what you can, apply the rest in ABAP** — split the range table into "supported" (goes into your `SELECT ... WHERE`) and "unsupported" (filter the result set in ABAP with `LOOP`/`FILTER` after fetch). Correct in all cases, but only safe when the pre-filter result set is bounded (a released CDS view with its own selective `WHERE`, not an unbounded scan).
2. **Reject via `cx_rap_query_provider`** — if the unsupported field is fundamental to keeping the query bounded and (1) would mean scanning an unbounded dataset, raising is safer than silently returning an incomplete or oversized result. The caller sees an OData error instead of something that looks correct but isn't.
3. **Silently ignore the unsupported field** — never do this as a default. It produces a result set that looks like it respected the filter but didn't, and nothing in the UI will visibly flag that.

## Decision: No `$orderby` Sent

The template's fallback-sort comment is correct, but the reason deserves more weight than a comment gives it: paging is **stateless per HTTP request** — `$skip`/`$top` is just an offset/count pair with no memory of a prior request's row order. If two consecutive page requests hit `select` with a different underlying row order (query plan variance, an internal table build order that isn't guaranteed stable across calls), rows can appear on two pages or vanish between them. The fallback sort by semantic key isn't a UI nicety — it's what makes paging *correct* in the absence of a client-supplied order, not just prettier.

## Selecting Only Requested Columns — Flagged as Unverified

`[unverified — could not confirm against the official interface documentation this session]`: the SAP Help Portal pages for `IF_RAP_QUERY_PROVIDER`/`IF_RAP_QUERY_REQUEST` render as a JS shell that couldn't be fetched (see sources file), and this API doesn't appear anywhere in the abap-cheat-sheets repo. An independent technical blog and search-engine synthesis (not an official SAP text) both describe `io_request->get_requested_elements( )` as returning the `$select`-requested field list. If your `select` method does expensive per-row work (a BAPI call, a nested-loop enrichment) for fields the client didn't ask for, checking this before doing that work would be a real optimization — but confirm the exact method name in ADT's interface browser before relying on it; this deep-dive cannot certify it against a primary source.

## When to Reach for a Custom Entity at All

Neither the SKILL.md body nor the template states the actual entry condition — both assume you've already decided a Custom Entity is right. Reach for `IF_RAP_QUERY_PROVIDER` + Custom Entity specifically when the data has **no real persistent CDS entity behind it**: an aggregation that doesn't fit a plain CDS view's aggregate expressions, rows assembled on the fly from an external API/RFC call, or a read-only combination of sources that doesn't map to one composition tree. If the data genuinely lives in a Z-table or is expressible as a released/local CDS view — even with joins/aggregates, see [Skill: cds-analytical-views] — model it as a normal CDS view entity instead: `$filter`/`$orderby`/`$top`/`$skip` handling comes free from the framework, instead of hand-rolling all three in a query-provider class.

## Decision Trade-offs

- Don't reach for rejection or silent-ignore by default when a filter field isn't supported — pushdown-then-ABAP-filter is correct in more cases and only gets expensive when the underlying source is genuinely unbounded; reserve rejection for exactly that case.
- The requested-elements optimization is worth the extra lookup only when the per-row cost is nontrivial (a remote call, a heavy computation) — for a cheap in-memory field, checking `get_requested_elements( )` first probably costs more than just computing it unconditionally.
