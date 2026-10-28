---
name: sap-process-production-process-planning
version: 1.0
description: SAP Production Planning process knowledge for Process Industry Manufacturing — scope item BJ8 (Make-to-Stock Process Manufacturing), planning side — MRP, Planned Order, Master Recipe (Bill of Operations), Process Order creation/release, on SAP S/4HANA Cloud Public Edition. Use when an FS describes process/batch manufacturing (chemicals, food, pharma), recipe-based production planning. Paired with [Skill: sap-process-manufacturing-process-execution] (same scope item, execution side). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP PP-PI consultant expert in process-industry production planning (scope item **BJ8**, planning half).

# Process Overview
Same MRP → Planned Order → convert-to-order flow as discrete manufacturing ([Skill: sap-process-production-discrete-planning]), but the executable order is a **Process Order** (not Production Order) and master data is a **Master Recipe** (not Routing) — reflects continuous/batch process industries (chemicals, food, pharma) rather than discrete unit assembly. Batch management is typically active (see [Skill: sap-process-o2c-customer-returns]'s batch-characteristic references for the sales-side counterpart).

**Note:** BJ8 is not split by SAP into separate planning/execution scope items — same intentional emphasis-split as the BJ5 pair.

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Planned Order (shared with discrete) | `I_PLANNEDORDER` | PP-VDM-2CL |
| Process Order item | `I_PROCESSORDERITEMTP` | PP-PI-POR-2CL |
| Process Order operation | `I_PROCESSORDEROPERATIONTP` | PP-PI-POR-2CL |
| Process Order phase | `I_PROCESSORDERPHASETP` | PP-PI-POR-2CL |
| Process Order phase capacity | `I_PROCESSORDERPHASECAPACITYTP` | PP-PI-POR-2CL |

Business events: `D_PROCESSORDERCREATED`/`CHANGED`/`D_PROCESSORDERRELEASEP`/`D_PROCESSORDERGETMISSINGPARTSR` (app component `PP-PI-POR-2CL`).

# Common Configuration Touchpoints
- Master Recipe / Bill of Operations type for process industry.
- Process order type control parameters.

# Related Processes
- [Skill: sap-process-manufacturing-process-execution] — execution side of this exact scope item.
- [Skill: sap-process-production-discrete-planning] — same MRP/planned-order mechanism, different order type (Process vs Production Order) — don't conflate the two order types in a TS.
- [Skill: sap-process-supplychain-atp] / [Skill: sap-process-supplychain-inventory-mgmt] — same cross-links as the discrete-planning skill.

# Deep Dive
For functional-consulting depth (master recipe/production version planning decisions, resource vs. work center costing/capacity, co-/by-product master-data prerequisites and apportionment structures, planning strategy applicability, planned-order-to-process-order conversion and release mechanics, resource-based scheduling nuances) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
