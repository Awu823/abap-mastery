---
name: sap-process-manufacturing-discrete-execution
version: 1.0
description: SAP Manufacturing process knowledge for Discrete Manufacturing — scope item BJ5 (Make-to-Stock Production - Discrete), execution/shop-floor side — order confirmation, component backflush, goods receipt of finished goods, on SAP S/4HANA Cloud Public Edition. Use when an FS describes shop-floor confirmation, production order execution, backflushing, or goods receipt from production. Paired with [Skill: sap-process-production-discrete-planning] (same scope item, planning side). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP PP-SFC consultant expert in discrete shop-floor execution (scope item **BJ5**, execution half).

# Process Overview
Released Production Order (from [Skill: sap-process-production-discrete-planning]) → shop-floor **Confirmation** (quantity produced, activities consumed) → component **backflush** (automatic goods issue of BOM components) → **goods receipt** of finished product into stock. Third-party shop-floor execution (external system doing the actual confirmation) is a separate variant, scope item **3W4**.

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Production Order Confirmation | `I_PRODUCTIONORDERCONFIRMATION` | PP-VDM-2CL |
| Production Order Component (for backflush) | `I_PRODUCTIONORDERCOMPONENT` | PP-VDM-2CL |

Integration: **OData API: Production Order Confirmation** (scope items 3W4/BJ5) — for external/third-party confirmation.

# Related Processes
- [Skill: sap-process-production-discrete-planning] — planning side of this exact scope item.
- [Skill: sap-process-supplychain-inventory-mgmt] — backflush (component out) and finished-goods receipt (product in) both post Material Documents there.
- [Skill: sap-process-supplychain-warehouse-mgmt] — if the plant uses embedded WM, goods receipt/backflush also generates Warehouse Tasks there.
- Finance skills (once built) — confirmation triggers actual-cost posting to the production order, later settled at period-end close.

# Deep Dive
For functional-consulting depth (confirmation mechanics/status machine, backflush indicator precedence, automatic goods receipt & serial-number restrictions, order status lifecycle, variance calculation & settlement, production order vs process order at execution) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
