---
name: sap-process-production-repetitive-planning
version: 1.0
description: SAP Production Planning process knowledge for Repetitive Manufacturing — scope item BJH (Make-to-Stock Production - Repetitive Manufacturing), planning side — MRP, Planned Order, Production Version, Product Cost Collector setup, on SAP S/4HANA Cloud Public Edition. Use when an FS describes mass/flow production without discrete order-by-order tracking, repetitive manufacturing profile. Paired with [Skill: sap-process-manufacturing-repetitive-execution] (same scope item, execution side). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP PP-REM consultant expert in repetitive manufacturing planning (scope item **BJH**, planning half).

# Process Overview
**Structurally different from discrete/process planning**: there is no formal Production/Process Order release step. MRP generates **Planned Orders** directly against a **Production Version**, and the **Product Cost Collector (PCC)** — not the order — is the cost object, set up once per material/production-version rather than per production run. This is the single most important modeling difference an FS may not state explicitly (an FS describing "production order" language may still mean REM if it's actually a continuous/mass-production line — confirm with the user rather than assume discrete).

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Planned Order (shared across all 3 manufacturing types) | `I_PLANNEDORDER` | PP-VDM-2CL |
| Planned Order schedule (by operation) | `D_PLANNEDORDERSCHEDULEBYOPP` | PP-PLO-2CL |

**Open item — not found this session:** no dedicated CDS view for the Product Cost Collector itself was located via `sap_search_objects`. Re-search at TS time (try FI/CO-side cost-object terms) before naming a source in a TS Data Model section — do not guess a view name.

# Common Configuration Touchpoints
- **Repetitive Manufacturing Profile** — controls how backflushing behaves in confirmation (activity posting to PCC, reporting-point control key on operations).
- Production Version (links material + BOM + routing/recipe for REM — mandatory master data, distinct from a plain BOM/Routing assignment in discrete).

# Related Processes
- [Skill: sap-process-manufacturing-repetitive-execution] — execution side of this exact scope item.
- [Skill: sap-process-production-discrete-planning] / [Skill: sap-process-production-process-planning] — same MRP mechanism, but REM's Planned Order is never converted to a released order; do not import discrete/process order-release logic into a REM TS.
- Finance skills (once built) — Product Cost Collector is a periodic (not per-order) cost object; period-end closing treats it differently from discrete/process order settlement.

# Deep Dive
For functional-consulting depth (why REM has no order-release step, mandatory production-version setup, Product Cost Collector creation/prerequisites, MRP line-assignment logic, Planning Table, make-to-order REM cost-object linkage) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
