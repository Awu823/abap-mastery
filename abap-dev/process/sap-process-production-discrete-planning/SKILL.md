---
name: sap-process-production-discrete-planning
version: 1.0
description: SAP Production Planning process knowledge for Discrete Manufacturing — scope item BJ5 (Make-to-Stock Production - Discrete), planning side — MRP, Planned Order, BOM/Routing, Production Order creation/release, on SAP S/4HANA Cloud Public Edition. Use when an FS describes production planning, MRP run, BOM/routing maintenance, or production order creation for discrete/unit-based products. Paired with [Skill: sap-process-manufacturing-discrete-execution] (same scope item, execution side). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP PP consultant expert in discrete production planning (scope item **BJ5**, planning half).

# Process Overview
MRP run → **Planned Order** (proposal, not yet a real order) → convert to **Production Order** (released, cost-object, executable) → hands off to execution ([Skill: sap-process-manufacturing-discrete-execution]). Master data prerequisite: **BOM** (components) + **Routing/Bill of Operations** (operations/work centers) must exist before a Production Order can be created.

**Note:** SAP does not split BJ5 into a separate "planning" scope item vs. "execution" scope item — both live under the same BJ5. This skill and its execution-side pair intentionally split the SAME scope item's content by emphasis, not by SAP's own scoping.

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Planned Order | `I_PLANNEDORDER` | PP-VDM-2CL |
| Planned Order capacity | `I_PLANNEDORDERCAPACITY` | PP-VDM-2CL |
| Production Order (header) | `I_PRODUCTIONORDER` | PP-VDM-2CL |
| Production Order item | `I_PRODUCTIONORDERITEM` | PP-VDM-2CL |
| Bill of Operations (routing) group | `I_BILLOFOPERATIONSGROUP` | PP-VDM-MD-2CL |
| Manufacturing Bill of Operations | `I_MFGBILLOFOPERATIONS` | PP-VDM-MD-2CL |

Business events: `D_PRODUCTIONORDERCREATED`/`CHANGED`/`D_PRODUCTIONORDERRELEASEP` (app component `PP-SFC-2CL`).

BOM master data: see [Skill: sap-process-o2c-sell-from-stock]'s Data Model Grounding note on `I_SALESORDERBILLOFMATERIALTP_2` for the sales-BOM link if this is a make-to-order-adjacent scenario — BJ5 itself is make-to-**stock**, plain material BOM applies.

# Common Configuration Touchpoints
- MRP type/procurement type per material.
- Order type dependent parameters (Production Order).
- Production scheduling profile.

# Related Processes
- [Skill: sap-process-manufacturing-discrete-execution] — execution side of this exact scope item (confirmation, backflush, goods receipt).
- [Skill: sap-process-supplychain-atp] — component availability check uses the same 2LN mechanism at planned/production order creation.
- [Skill: sap-process-supplychain-inventory-mgmt] — component reservation/goods issue posts here.
- Finance skills (once built) — production order settlement/COGM feeds period-end closing.

# Deep Dive
For functional-consulting depth (planning strategy MTS/MTO/hybrid, MRP lot-sizing/safety-stock mechanics, BOM explosion/phantom assemblies, scheduling logic) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
