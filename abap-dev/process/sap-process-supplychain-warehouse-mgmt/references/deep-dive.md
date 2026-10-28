# Deep Dive — sap-process-supplychain-warehouse-mgmt (3BR/3BS)

Read this file when the FS requires real functional-consulting depth on embedded Warehouse Management (putaway/removal logic, work grouping, resource distribution, HU/packing, exception handling) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Warehouse Process Type — the Router Behind Every Warehouse Task

Every Warehouse Task is stamped with a **Warehouse Process Type** (e.g. `S110` Putaway, `S115` Putaway from Production, `S210`/`S201` Picking variants) — this is the switch that decides which apps, storage-bin defaults, and downstream behavior apply to that task. It is not free-form: config activity **Define Warehouse Process Type** creates the types, **Assign Storage Bins to Warehouse Process Type** gives each one a default storage type/bin, and **Determine Warehouse Process Type** (two separate activities — one for general warehouse requests, one specifically for putaway after *synchronous* goods receipt) drives automatic determination, optionally narrowed by **Control Indicators for Determining Warehouse Process Types** that group products (e.g. hazardous vs. standard) into different routing buckets.

Why this matters: an FS describing "goods received from production should go through a different receiving flow than goods received from a vendor" is describing exactly `S110` vs. `S115` — a config-level process-type split with its own storage-bin assignment, not a bespoke routing table to build.

**Practitioner implication:** before scoping any custom "which flow does this task follow" logic, check whether it's just an unconfigured Warehouse Process Type / Control Indicator combination — this is almost always cheaper to configure than to code.

## 2. Putaway (3BR) — Storage Type Search Sequence & Putaway Strategy

Putaway destination-bin determination is a two-layer mechanism, not a single lookup: a **Storage Type Search Sequence** (an ordered list of candidate storage types, assigned via a **Putaway Control Indicator**) is evaluated in order, and within each storage type a **Putaway Rule** decides *how* to pick the actual bin. SAP ships several named putaway strategies with distinct behavior:
- **"Empty Storage Bin"** — builds a list of empty destination bins following the search sequence order.
- **"Addition to Existing Stock"** — finds bins that already hold the same stock, so a partial pallet gets topped up instead of opening a new bin.
- **"Near to Fixed Bin"** — for storage types that use fixed-bin picking, suggests reserve bins physically close to the product's picking fixed bin (config: **Storage Type Control: Near to Picking Fixed Bin** + **Define Search Scope for Each Level**), so replenishment travel distance stays short.
- **Bulk storage** is its own control layer (**Storage Type Control for Bulk Storage**, **Define Bulk Storage Indicators**, **Define Bulk Structures** for stack count/height/HU count) — relevant whenever the FS describes floor-stacked or lane-based storage rather than bin racking.

Three BAdIs cover the extensibility surface here: **Bin Filtering and Sorting: Empty Bins in Putaway**, **Bin Filtering and Sorting: Possible Bins Near Fixed Bins**, **Bin Filtering and Sorting: Possible Bins for Additional Stock**, plus **Storage Type Search Sequence and Putaway Rule Change** to override the sequence/rule itself under custom conditions. An FS asking for "smart" or "optimized" putaway logic maps onto one of these four BAdIs — not a new Z-table-driven algorithm.

**Practitioner implication:** decompose any "intelligent putaway" requirement into (a) which putaway rule applies per storage type, (b) the storage-type search-sequence order, and (c) whether a BAdI is genuinely needed versus simply re-sequencing existing config — in that order, before writing custom code.

## 3. Stock Removal (3BS) — Storage Type Search Sequence & Removal Rule

Outbound picking mirrors putaway's structure exactly, on the removal side: a **Storage Type Search Sequence for Stock Removal** (config: **Specify Storage Type Search Sequence**, **Determine Storage Type Search Sequence for Stock Removal**) combined with a **Stock Removal Rule** (config: **Specify Stock Removal Rules**) and a **Stock Removal Control Indicator** decide which bin the system proposes as the pick source. One named strategy is officially documented — **"Stock Removal Suggestion According to Quantity"** — which classifies candidate source bins by whether their storage type is set up for small or large quantities, then lets **BAdI Bin Filtering and Sorting: Available Quantities for Stock Removal** re-sort/filter that candidate list. A second BAdI, **Storage Type Search Sequence and Removal Rule Change**, overrides the sequence/rule wholesale under custom conditions; a third, **Change Requested Quantity for Stock Removal**, can convert the requested quantity to an alternative unit of measure or change the handling unit type mid-determination.

The product master's Warehouse view also plays a role here: a field on the product record lets you flag a preferred storage type/storage-type group for removal and **controls the sort order of stock during stock removal** — so a "always exhaust the bulk area before opening a new pallet position" or "propose the oldest goods-receipt-dated stock first" requirement is very likely a product-master/storage-type configuration decision, not hardcoded ABAP. `[unverified]` whether a specific strategy is literally labeled "FIFO" in this embedded WM's configuration UI — verify the exact strategy indicator name in the system before committing to that label in a TS.

**Practitioner implication:** treat "pick the right stock first" requirements the same way as putaway — check the storage-type-level removal rule and the product master's stock-removal sort field before assuming a custom sequencing algorithm is required.

## 4. Wave and Warehouse Order — Grouping Work Before the Floor Sees It

Two distinct grouping layers sit between "a delivery exists" and "a worker has a task in hand," and FS authors routinely conflate them:
- A **Wave** groups *warehouse request items* (inbound or outbound) by criteria such as activity area, route, or product, so they're released to Warehouse Task creation together — e.g. "all deliveries on Route X due to ship by 3pm." **Wave Templates** (app: Maintain Wave Templates) define the release method (Automatic/Immediate/Manual), a wave category usable as a filter for Warehouse Order Creation Rules, bin-denial handling behavior, and a full timing model — cutoff time, release time, picking/packing/staging completion times, each expressible as an absolute time or as N days before wave completion. A single warehouse request item can even be *split across waves* if quantity-dependent picking-location determination assigns its partial quantities to different picking areas.
- Once Warehouse Tasks exist, **Warehouse Order Creation Rules (WOCR)** group them into a **Warehouse Order** — the actual work package a warehouse worker executes (config: search sequence for warehouse order creation rules per activity area, falling back to default rule `DEF` if none matches).

So "batch outbound deliveries for a shipment cutoff" is a Wave Template timing question; "how do individual pick tasks get bundled into one worker's task list" is a WOCR question — these are two separate configuration decisions, not one.

**Practitioner implication:** when an FS says "group deliveries for the 3pm truck," ask whether it means wave release timing (Wave Template) or task bundling logic (WOCR) — the two are configured independently and solve different problems.

## 5. Resource & Queue Management — Distributing Work to People

**Resource Management** governs who does the work: a **Resource** (a warehouse worker, RF-logged-on or not) is assigned to a **Queue**, and Warehouse Orders are likewise assigned to queues via queue-determination criteria and access sequences — either manually by a warehouse manager or automatically by the system. When a resource requests system-guided work, the **Warehouse Order Selection** logic offers the most appropriate open order considering mode, Latest Start Date (LSD), the resource's assigned queues, and the bin-access types and HU-type groups assigned to the resource's **resource type**. Warehouse managers use the Warehouse Monitor to analyze resource workload, log off resources, reassign queues, and change an order's LSD or queue directly.

An FS requirement like "picker A should only see orders for the cold-storage zone" or "prioritize orders nearing their due time" is this queue-determination-criteria and resource-type configuration, not a custom worklist filter bolted onto an app.

**Practitioner implication:** zone/skill-based work restriction is a Resource Type + Queue assignment design question — check this before proposing a custom authorization- or filter-based solution.

## 6. Handling Units, Packing, and Confirmation Exceptions

**Handling Units (HUs)** are the physical-container thread running through the entire chain — sales order packing proposal → production → procurement → goods receipt → Warehouse Management → inventory → shipping — and packing itself happens directly inside the inbound/outbound delivery via the Pack function, supporting **multi-level (nested) packing**, unpacking, HU deletion/emptying, and automatic overflow handling (if a weight/volume limit is hit mid-pack, the system packs the maximum partial quantity and continues into the next available HU). One hard constraint to flag early in any FS: **once a delivery has been distributed to Warehouse Management, the delivery and its packed HUs can no longer be changed from the ERP delivery side** — further changes must go through Warehouse Management itself.

Operational exceptions at confirmation are handled through **exception codes**, not custom status fields — this is the direct answer to "what happens when a short-pick or damaged-goods situation occurs":
- `DIFS` — the exact requested quantity can't be picked (e.g. slightly over/under a cut-to-length item); confirms the reduced quantity **without** recording it in the Difference Analyzer.
- `DIFW` — stock in the bin is genuinely short (e.g. some goods are damaged); confirms the reduced quantity **and records** the difference in the Difference Analyzer for follow-up.
- `DIFD` — a putaway quantity reduction that also reduces the underlying inbound delivery item.
- `CHBD` / `CHBA` / `CHHU` — change destination bin / batch / destination HU when the planned target doesn't fit reality.
- `SPLT` — split one warehouse task into a partially-confirmed piece plus a new task for the remainder.
- `SKWO` — skip a warehouse order entirely (e.g. a blocked aisle), with the system re-offering it later.
- `CRID` — raise an ad-hoc warehouse-internal inspection lot mid-process.

When several warehouse tasks with matching attributes (same source bin/HU, same stock key) are confirmed together via **Combined Picking** on RF, denial exception codes (`BIDU`/`BIDF` full denial, `BIDP` partial denial) apply proportionally across the combined tasks rather than to a single one — worth knowing before assuming a "damaged goods on partial pick" scenario only ever touches one task.

Quality-managed products add a routing branch at goods receipt rather than a true "exception": if a product has QM inspection type `01`/`04` active, goods receipt automatically sets stock type **Q (Quality Inspection Warehouse)**, creates an inspection lot, and the putaway task routes the HU to a bin in the quality area (via the storage type search sequence configured for quality stock) instead of its normal final bin — only after a recorded **Usage Decision** does the system auto-create the follow-up task to the real final bin or to scrap. See [Skill: sap-process-supplychain-inventory-mgmt] for how stock type Q reads on the Inventory Management side once it lands there.

**Practitioner implication:** "handle damaged goods at receipt/pick" in an FS is answered by either (a) the product being QM-relevant and routing to the quality area automatically, or (b) a warehouse worker entering `DIFW`/`DIFD` at confirmation — treat a request for a bespoke "damage flag" field with suspicion until both of these are ruled out.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
