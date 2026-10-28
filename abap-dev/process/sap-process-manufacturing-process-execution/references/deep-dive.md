# Deep Dive — sap-process-manufacturing-process-execution (BJ8, execution)

Read this file when the FS requires real functional-consulting depth on process-order shop-floor execution (phase confirmation, backflush, co-product goods receipt, MES/control-recipe boundaries) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. The Master Recipe Pre-Decides Confirmation Behavior — Don't Re-Design It

The **Master Recipe** specifies, at planning time, everything that governs how a phase gets confirmed: which resources are required, the operations/phases and their sequence, whether and how each phase is confirmed, which material components are required per phase (and whether each is cost-relevant), and — critically — whether a **goods issue is posted when the last phase is confirmed**. It also distinguishes recipe-level output categories such as intra materials, valuable materials, and remaining materials, with a costing choice (equivalence numbers vs. net-realizable-value method) for valuable materials. None of this belongs in custom ABAP: an FS asking "why doesn't backflush happen until the final step" or "why is this recovered material costed this way" is almost always describing an existing master-recipe setting, not a gap to fill with code.

**Practitioner implication:** before writing a single line of Behavior Pool logic for "custom confirmation rules," open the material's master recipe (Manage Master Recipes) and check the per-phase confirmation/costing flags — most "custom logic" requests for BJ8 dissolve into recipe maintenance, which is planning's responsibility (see [Skill: sap-process-production-process-planning]).

## 2. Three Confirmation Apps, Three Different Granularities — Match the FS Wording to the Right One

- **Confirm Process Order (CORK)** — order-level: confirms the WHOLE order in one shot; planned (not actual) values are posted for the phases. Fits "one-click complete the batch."
- **Confirm Process Order Phase (COR6N)** — phase-level: partial or final confirmation of ONE phase via a time ticket, with system-proposed defaults; fits operators reporting progress phase-by-phase.
- **Confirm Time Event – Process Order Phase (CORZ)** — event-level: records a raw time event (e.g., a start/stop signal) for a phase, independent of a full confirmation; the system can propose yield automatically for a "processing" record type. This is the closest current cloud equivalent to logging shop-floor timing signals without a full confirmation.

**Practitioner implication:** "operators log start and stop times without entering yield yet" maps to CORZ, not a custom timestamp field; "one confirmation per phase with quantities" maps to COR6N; "confirm the whole order at the end" maps to CORK. Picking the wrong one changes both the UI and the underlying OData/API surface the TS should integrate against.

## 3. Backflush: Indicator Precedence, and the Co-Product Restriction Most Builds Miss

The backflushing indicator can be set in three places, in ascending precedence: **Material Master** (MRP view: never / always / work-center-decides) → **Work Center** (only consulted if the material master says "work center decides") → **Routing/Recipe** component overview (always wins, regardless of the other two). Reproduce this precedence in the TS if an FS describes per-component backflush behavior that looks inconsistent across materials — it is very likely a recipe-level override, not a bug.

At confirmation, **Automatic Goods Receipt** (posting the produced material to stock without a manual GR step) is controlled by the operation's control key or the production scheduling profile — but SAP explicitly does **not** allow automatic GR for co-products, and automatic goods movements are blocked (written only as an error record) for serial-number-managed materials. An FS asking for "auto-post GR for every produced item including co-products" cannot be met as stated for the co-product line — flag this as a standard-system constraint, not something to silently work around in custom code.

## 4. Goods Receipt Structure for Co-/By-Products at Confirmation Time

A joint-production process order carries a separate order **item** for the main product and for each co-product (so actual costs/WIP/variance are visible at co-product level), but **not** for by-products (valued only via the material master's price control, posted as a goods issue with movement type 531, not a goods receipt). At GR time, all co-products are proposed by default, and the order-item-level credit posting is generated per co-product automatically — the confirmation step doesn't need custom multi-material GR logic; it is standard joint-production behavior once the co-/by-product master data is set up correctly upstream (see [Skill: sap-process-production-process-planning]'s co-/by-product master-data section for that setup).

## 5. Control Recipe / PI Sheet — What Actually Survives in S/4HANA Cloud Public Edition

Classic ECC PP-PI functionality (PI Sheet, Control Recipe, Process Message/Process Instruction Category, PI-PCS destination) did not surface anywhere in current SAP S/4HANA Cloud Public Edition documentation searched for this skill `[unverified beyond absence-of-evidence in this session's search — treat as a strong signal, not a certified statement of deprecation]`. The nearest cloud-native equivalents found are: (a) the CORZ time-event confirmation (§2) for capturing discrete process signals without a full control-recipe protocol, and (b) external MES integration via order status **Released by MES (RMES)** — which carries the same processing restrictions as **Distributed (DISB)** — plus the `BD_CO_MES_INT_DISTRIBUTION` BAdI, which controls exactly what order-change data gets redistributed to an external MES after the order changes.

**Practitioner implication:** if an FS literally says "PI sheet" or "control recipe," stop and ask whether the client means (a) genuinely classic on-premise PI-PCS terminology carried over from a legacy spec that needs re-scoping for Cloud, or (b) **SAP Digital Manufacturing** (a separate cloud service with its own POD/MES layer, not part of embedded BJ8) — these are architecturally different integration targets, and the TS depends entirely on which one it actually is.

## 6. Confirmation-Triggered Costing: Event-Based Is Current, Period-Based Is Deprecated, and PP5/PP6 Don't Apply to Process Orders

Actual costs for a process order are captured at confirmation (goods issue, activity/resource consumption) and flow into WIP and variance calculation. SAP's **event-based** cost posting (scope item 3F0) is the current model — WIP/variance/settlement react to each confirmation/goods-movement event; the older **period-based (BEI)** batch jobs (Calculate WIP, Calculate Variances, Settle) are explicitly documented as deprecated. An FS assuming "a month-end WIP batch job" as the only mechanism should be redirected to the event-based reports/apps unless the system is confirmed to still run BEI.

For co-product cost distribution specifically: settlement rule **PP1** (apportionment-structure-based) works for both production and process orders, but **PP5** and **PP6** (the "distribute by planned/actual delivery quantity" rules) are documented as applicable **only to production orders, not process orders**. If a BJ8 FS asks for automatic equivalence-number derivation from delivered quantities (the PP5/PP6 behavior), that specific mechanism is not available on a process order — the apportionment structure (PP1, maintained on the header material's Costing 1 view) is the mechanism actually available there, and equivalence numbers must be planned there or entered/adjusted manually on the order.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
