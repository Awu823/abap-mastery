# CDS Data-Model Analysis — Deep Dive

Mechanics and verification procedures behind the SKILL.md's 5-step procedure. Sources/citation trail: [sources-deep-dive.md](sources-deep-dive.md).

## DDIC Foreign Keys — What They Do and Don't Guarantee

Verified against the ABAP Keyword Documentation (758 mirror; the Cloud documentation links the same page):

- A foreign key consists of one or more foreign key fields of a *foreign key table*; those fields form the **primary key of the check table**. A table can have multiple foreign keys.
- **The load-bearing caveat**: *"A foreign key table usually only contains entries where the content of the foreign key also occurs exactly once as content of the primary key in the check table. The developer must consider this in writes made using ABAP SQL, since there is no automatic check."* — a DDIC FK is a semantic declaration plus (classic-UI) input-check hook, **not** a database constraint. For join design this means: a Z-table's FK tells you the *intended* relationship, and nothing about whether the data actually honors it. Orphaned FK values surface as dropped rows (inner join) or null-filled rows (left outer join) — pick the join type against the *actual* data quality, verified by probe (below), not the declared intent.
- **FK cardinality `n:m`** (documentation-purpose except in maintenance/help views):
  - `n` (FK-table side): `1` = exactly one check-table row must exist per FK-table record; `C` = FK-table records may exist without a check-table row.
  - `m` (check-table side): `1` = exactly one FK-table row per check-table row; `C` = at most one; `N` = at least one; `CN` = any number.
  - Reading rule for join design: `m` tells you the to-many direction. `:CN`/`:N` means joining check-table → FK-table fans out; `:1`/`:C` means it doesn't.
- **Text tables**: an FK whose fields are typed "key fields of a text table" makes the FK table a text table of the check table — its primary key must match the check table's plus one `LANG` language key. Join-design implication: a text-table hop is to-many by structure (one row per language); always filter the language key (`$session.system_language` in CDS) or the hop duplicates every row per maintained language — the classic "why does my report show every row twice" bug on bilingual systems.
- Foreign key fields have a declared *type* (`no key fields/candidates` / `key fields/candidates` / `key fields of a text table`) — the first two are documentation-only, but they tell you whether the FK participates in the FK table's own identity, which matters when deciding if a hop can ever fan out in the reverse direction.

## CDS Associations — Cardinality, Exposure, and the Fan-Out Alarm

Verified verbatim against the SAP-authored executable example (`zdemo_abap_cds_ve_assoc(_e).ddls.asddls`):

- Syntax: `association [1..1] to zdemo_abap_carr as _carr on _flsch.carrid = _carr.carrid` — cardinality `[min..max]`, min optional (default 0), `[0..1]` is the default when nothing is specified ("If the cardinality is not specified, it is to one by default"). Minimum cannot be `*`, maximum cannot be `0`.
- Cardinality is *"a means of documenting the semantics of the data model"* — but not inert: *"Maximum values greater than 1 can lead to syntax errors or warnings. Generally, a non-matching cardinality usually produces a warning."* The example's own comment documents the exact warning text for a to-many association used in a single-value position: **"The association _fli can modify the cardinality of the results set."** Treat that warning as a design signal (Step 4 of the SKILL.md procedure), never as noise to suppress.
- **Used vs. exposed** (drives whether a join happens at all):
  - *Used* (fields of the target added to the element list): a join IS performed — the target fields are flattened into every result row. This is where fan-out materializes.
  - *Exposed* (association itself in the element list, no target fields): NO join is performed — *"It is up to the consumer... to request fields... Only then, a join is performed."* Exposed associations are the zero-cost option for relationships the report only sometimes needs.
- On the database, *"associations are internally transformed into joins"* — the association source is the LEFT side, target the RIGHT side, and by default a **left outer join** is performed when a path expression requests data. Hence the demo's own `coalesce(_carr1.url, 'NULL')` — left-outer null handling is the consumer's job.
- **Path-expression attributes** `assoc[ ... ]` override per use site: filter conditions (`_carr2[left outer where $projection.carrier = 'LH'].url` — with an explicit join type, `WHERE` is mandatory), and the **`1:` cardinality override** (`_fli[1:$projection.connection_id = connid].fldate`) which declares this specific use resolves to one row, silencing the fan-out warning. Only use `1:` when the filter genuinely pins a single row — using it to hide a real to-many is exactly the silent-duplication bug this skill exists to prevent.
- ON-condition fields referencing renamed elements of the source need the `$projection.` prefix (`on $projection.carrier = _carr3.carrid`).

## Worked Fan-Out Scenario (the inflated-total bug)

Grain: one row per sales order (root `ORDERS`, key `order_id`). Requirement: show order total + number of delivery items. `DELIVERIES` relates `[1..*]` (one order, many delivery items).

- **Wrong**: flatten-join `DELIVERIES` onto `ORDERS`, then `sum(orders.net_amount)` grouped by customer. Every order with 3 delivery items now contributes its `net_amount` **3 times** — no error, no warning at the SQL layer, just wrong totals. This is Step 4's target failure mode: aggregation downstream of an unaggregated to-many hop.
- **Right, option A (pre-aggregate the many side)**: a first view aggregates `DELIVERIES` to order grain (`count(*) as delivery_item_count` grouped by `order_id` — now to-one), then the report view joins that at `[1..1]`.
- **Right, option B (association, consumer-side)**: expose `_Deliveries` as an association; the report view shows order data and the consumer (Fiori Elements table, follow-up view) resolves the association only where needed — no flattening, no inflation.
- Choosing A vs B is the join-vs-association decision in [Skill: cds-analytical-views]'s table — A when the count must appear on every row unconditionally, B when it's drill-down detail.

## Verification Procedures (evidence before design)

Per workspace rule §2/§8: relationship facts get evidence, not guesses.

1. **Read the artifact** (preferred): view source via ADT or the read-tool of whichever SAP MCP server the session has (rule §9 — verify the tool exists first). `key` elements, association declarations with cardinality and ON conditions, DDIC FK definitions. Record WHERE each fact was read.
2. **Data probe** (when cardinality is inferred or FK integrity matters): count the link-field combinations on the many side, e.g. `SELECT link_field, COUNT(*) ... GROUP BY link_field HAVING COUNT(*) > 1` via the Data Preview/query tool — a to-one hypothesis dies on the first duplicate. For FK integrity: probe for FK values with no check-table match (candidates for join-type surprises). Business data stays read-only (rule §2).
3. **When neither is possible** (no system access, view not yet built): mark the relationship `[assumption]` in the output map, and say what probe would confirm it. An `[assumption]`-marked cardinality in the TS is acceptable; a silently guessed one is not.

## Boundaries With Neighboring Skills (do not duplicate)

- Join/aggregation/parameter/annotation **syntax** → [Skill: cds-analytical-views]. This file names constructs only to explain the analysis; the templates live there.
- Association vs composition semantics inside a RAP composition tree, admin fields, draft tables → [Skill: cds-view-entities].
- Finding WHICH released `I_*` view serves a business field → [Skill: find-released-cds-view]; this skill starts where that one ends (you have candidate views, now pin their keys/relationships).
- Extracting the required data model FROM an FS document → [Skill: fs-data-model-extractor]; this skill validates/hardens what that extraction produced (grain, cardinality, fan-out) before it enters the TS.
