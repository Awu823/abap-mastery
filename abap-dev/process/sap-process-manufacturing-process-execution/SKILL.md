---
name: sap-process-manufacturing-process-execution
version: 1.0
description: SAP Manufacturing process knowledge for Process Industry Manufacturing — scope item BJ8 (Make-to-Stock Process Manufacturing), execution/shop-floor side — process order confirmation, phase-based backflush, batch-managed goods receipt, on SAP S/4HANA Cloud Public Edition. Use when an FS describes process-order confirmation, phase confirmation, or batch-managed production execution. Paired with [Skill: sap-process-production-process-planning] (same scope item, planning side). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP PP-PI consultant expert in process-industry shop-floor execution (scope item **BJ8**, execution half).

# Process Overview
Released Process Order → **phase confirmation** (process industry confirms by phase/operation, not a single order-level confirmation) → component backflush → **batch-managed** goods receipt of the produced material (batch determination/creation is typically mandatory in process industries). Third-party process-industry execution is a separate variant, scope item **3W3**.

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Process Order Confirmation | `I_PROCESSORDERCONFIRMATIONTP` | PP-SFC-EXE-CON-2CL |
| Process Order Component (for backflush) | `I_PROCESSORDERCOMPONENTTP` | PP-PI-POR-2CL |

Integration: **OData API: Process Order Confirmation** (scope items 3W3/BJ8) — for external/third-party confirmation.

Batch/characteristic grounding: reuse [Skill: sap-process-o2c-customer-returns]'s `I_BATCHCHARACTERISTICVALUETP_2`/`I_CLFNCHARACTERISTIC` references if the FS needs batch characteristic values on the produced material.

# Related Processes
- [Skill: sap-process-production-process-planning] — planning side of this exact scope item.
- [Skill: sap-process-supplychain-inventory-mgmt] — backflush + batch-managed goods receipt post Material Documents there.
- [Skill: sap-process-supplychain-warehouse-mgmt] — goods receipt into embedded WM if active for the plant.

# Deep Dive
For functional-consulting depth (master-recipe-driven confirmation behavior, CORK/COR6N/CORZ confirmation granularity, backflush indicator precedence and the co-product automatic-GR restriction, co-/by-product goods receipt structure, what replaced classic PI sheets/control recipes in S/4HANA Cloud, event-based vs. deprecated period-based variance/settlement) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
