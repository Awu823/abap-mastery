# Deep Dive — sap-process-production-process-planning (BJ8, planning)

Read this file when the FS requires real functional-consulting depth on process-industry production planning (master recipe vs. routing, resource-based costing/scheduling, co-/by-product master data, planned-order-to-process-order conversion) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Master Recipe + Production Version — the Planning-Time Decisions That Predetermine Execution

The **Master Recipe** (its execution-time consequences are covered in [Skill: sap-process-manufacturing-process-execution]) specifies, at planning time: which resources are required, the operations/phases and their sequence, whether/how each phase is confirmed, which material components are cost-relevant, and whether a goods issue posts on last-phase confirmation. None of this is execution's to decide — it is authored during recipe maintenance, before the first process order ever exists.

The **Production Version** is the selector that ties one specific alternative BOM to one specific master recipe (or routing, for discrete) for a given lot-size range and validity period; MRP, product costing, and process order creation all read the production version to pick the right BOM+recipe pair. Practical gotcha: the **Convert to Process Order** action on a planned order only appears if a Master Recipe (not a Routing) is maintained as the task list type on that material's production version, and — for mass conversion specifically — the order-type-dependent parameters must specify automatic production-version selection. An FS assuming "the planner just clicks convert" should have both prerequisites checked as environment/master-data readiness items, not left implicit.

## 2. Resource vs. Work Center — the Cost Master Data Behind Every Phase

A **Resource** (not a Work Center) is process manufacturing's execution-means master data: it is plant-assigned, and its master record specifies a cost center (which rolls into a controlling area) so that phase activity can be valuated via activity types in cost center planning. Every phase automatically inherits the operation's resource as its **primary resource**; additional resources assigned to an operation/phase are **secondary resources** (e.g., personnel cost alongside a reaction chamber's primary equipment cost). Both primary and secondary resource costs flow to the product through activity types — an FS describing "we need to track labor cost separately from equipment cost for this step" is describing a primary/secondary resource split, not a new cost object to design.

## 3. Co-Products and By-Products Start as Planning-Time Master-Data Decisions

Whether a material behaves as a co-product or a by-product in execution is decided entirely by planning-time BOM/material-master setup, not by a switch at confirmation time:
- **Co-product**: the Co-product indicator is set on the material master (MRP or Costing view) of both the main product AND the co-product; the co-product is a BOM item of the main product with a NEGATIVE quantity; the Co-product indicator is also set on that BOM item.
- **By-product**: a negative-quantity BOM item just like a co-product, but the Co-product indicator must **not** be set — this is what tells the system not to create a separate order item for it and to valuate it purely from the material master's price control.

The header material's Costing 1 view carries the **apportionment structure** (source structure + equivalence numbers) that becomes the default settlement rule (PP1) copied onto every process order created against that recipe — get this wrong at the material-master level and every subsequent process order inherits the wrong cost split. Co-products can also have their own production version (referencing the header material's production version by key, via the "Other header mat." field) if their BOM/recipe assignment needs to differ.

**Practitioner implication:** an FS's "the by-product should also show separate actual costs" cannot be met by adjusting execution-side confirmation — it requires switching the material to a co-product (with all its master-data prerequisites) at the planning stage, which has wider cost-accounting consequences the FS author may not have considered; raise it before building anything (see [Skill: sap-process-manufacturing-process-execution] §4 for the execution-side consequence of this choice).

## 4. Planning Strategy Applies Unchanged — Master Recipe Doesn't Reset the Rules

The planning-strategy mechanics from [Skill: sap-process-production-discrete-planning] (Strategy Group 10/20/40/52 etc. on the material's MRP view) carry over to process manufacturing without modification. Make-to-Order (strategy 20), for instance, explicitly states that "it does not matter if the material has a BOM (internal production) or not" — the same holds whether the resulting executable order is a Production Order or a Process Order. Don't re-derive planning-strategy logic per manufacturing type; only the executable order type (Process Order vs. Production Order) and its master data (Master Recipe vs. Routing) differ.

## 5. Converting Planned Order to Process Order, and What "Released" Really Means

Planned orders convert to process orders individually (Convert action) or in bulk (Collective Conversion to / mass conversion) — gated by the production-version/task-list-type check in §1. **Co-products are explicitly excluded from mass and inline conversion** (a documented SAP restriction) — a joint-production process order must be created through the full order-creation flow, not the fast mass-conversion path, whenever the FS's scenario involves co-products.

Releasing a process order sets status **Released (REL)**; if only the FIRST operation is released while further operations remain unreleased, the order status instead becomes **Partially Released (PREL)** — relevant for FS scenarios describing phased/rolling release of a long recipe. A preliminary cost estimate for a process order can only be created **after** release, not before — if an FS expects a firm cost figure at planned-order stage, that expectation needs correcting to "estimate available only once released."

Where an external Manufacturing Execution System (MES) drives release/execution instead of S/4HANA Cloud itself, the order carries status **Released by MES (RMES)** — restricted the same way as **Distributed (DISB)** — and the `BD_CO_MES_INT_DISTRIBUTION` BAdI controls exactly which order-change data gets redistributed to that external MES after a change. An FS integration requirement phrased as "push order changes to the shop-floor system" maps to this BAdI plus the process-order change business events, not a bespoke outbound interface.

## 6. Resource-Based Scheduling: Why Process-Order Durations Aggregate Differently Than Discrete

In process industries, an order operation's capacity requirement is the **sum of its individual phases' durations** — three sequential 2-hour phases produce a 6-hour capacity requirement even if, physically, the phases could overlap and the wall-clock time is closer to 2 hours. This is a structurally different capacity model than discrete's single work-center-per-operation timing (see [Skill: sap-process-production-discrete-planning] §4 for the discrete scheduling defaults — backward scheduling by default, Order-Type-Dependent Parameters controlling forward/backward per order type — which otherwise apply unchanged here too). One additional edge case: if a work center carries more than one individual capacity in its master data, a **planned** order against it cannot be finitely scheduled correctly in the Capacity Scheduling Table app — it must first be converted to a **production** order (not a process order) to get the expected scheduling result; flag this as a known tool limitation if an FS's scenario involves multi-capacity work centers feeding process orders.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
