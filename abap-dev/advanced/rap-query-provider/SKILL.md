---
name: rap-query-provider
version: 1.0
description: Help with implementing RAP Query Providers (IF_RAP_QUERY_PROVIDER) for Custom Entities in ABAP Cloud. Focuses on handling query options (paging, sorting, filtering) to avoid the "Query not fully covered by implementation" error. Triggers include "IF_RAP_QUERY_PROVIDER", "custom entity class", "select method", "get_sort_elements", "get_paging", "set_total_number_of_records", "Query not fully covered". Use even for a single error-fix ask — Vietnamese triggers: "custom entity", "viết query provider", "lỗi Query not fully covered", "paging/filter không chạy".
---

# RAP Query Provider & Custom Entity Implementation

Guide for implementing `IF_RAP_QUERY_PROVIDER` for Custom Entities. The full class template lives in [references/query-provider-template.md](references/query-provider-template.md) — read it when writing the class; this body explains the API and the error it exists to prevent.

## The "Query not fully covered by implementation" Error

With a Custom Entity, data retrieval is entirely delegated to your `select` method. OData clients (Fiori Elements) automatically send `$orderby`, `$top`/`$skip`, and `$filter`. If the client requests a capability your `select` method never retrieves from `io_request`, the OData runtime dumps:

> `Query not fully covered by implementation: Call to method if_rap_query_request~get_sort_elements missing.`

**The fix — and the safety net**: always call `io_request->get_sort_elements( )` and `io_request->get_paging( )` even when you don't use them. Retrieving the capability is what tells the framework it is "covered".

## Core Request & Response API

| Capability | Retrieve | Apply |
|---|---|---|
| **Paging** (`$top`/`$skip`) | `io_request->get_paging( )` → `get_offset( )`, `get_page_size( )` | SQL `OFFSET @lv_offset UP TO @lv_page_size ROWS`, or slice the internal table after sorting |
| **Sorting** (`$orderby`) | `io_request->get_sort_elements( )` — **mandatory call** | Build `abap_sortorder_tab` from the elements, `SORT lt_data BY (lt_sort_order)` |
| **Filtering** (`$filter`) | `io_request->get_filter( )` → `get_as_ranges( )` (recommended) or `get_as_sql_string( )` | Use ranges in WHERE clauses; filter-bar and value-help inputs arrive here |
| **Entity parameters** | `io_request->get_parameters( )` | For `with parameters ...` custom entities |
| **Data out** | — | `io_response->set_data( lt_data )` (the requested page only) |
| **Total count** (`$count`) | `io_request->is_total_numb_of_rec_requested( )` | `io_response->set_total_number_of_records( lv_total )` |

## Best Practices

1. **Safety net first**: call every `get_*` method up front (see template) — cheapest insurance against the runtime dump.
2. **Total count = full filtered dataset**, counted BEFORE paging is applied. Setting the page size instead breaks Fiori row counts and stops subsequent pages from loading.
3. **Deterministic fallback sort**: when the client sends no `$orderby`, sort by the entity's semantic key anyway — paging slices the table, and an unstable order makes pages overlap or skip rows between requests.
4. **Wrap in TRY...CATCH `cx_rap_query_provider`** — errors must flow through the OData pipeline, not dump.

## Deep Dive

For decision criteria on the edge cases the safety net alone doesn't resolve (skip the count when not requested, filtering on a field your source doesn't carry, why the fallback sort matters), version-gating for CDS custom entities, and when to reach for a Custom Entity at all vs. a plain CDS view, read [references/deep-dive.md](references/deep-dive.md).

## References

- [references/query-provider-template.md](references/query-provider-template.md) — complete class template with all four phases (retrieve → logic → sort/page → respond)
