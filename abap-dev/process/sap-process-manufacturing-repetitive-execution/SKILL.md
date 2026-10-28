---
name: sap-process-manufacturing-repetitive-execution
version: 1.0
description: SAP Manufacturing process knowledge for Repetitive Manufacturing — scope item BJH (Make-to-Stock Production - Repetitive Manufacturing), execution side — lean confirmation, backflush against Product Cost Collector, reporting points, on SAP S/4HANA Cloud Public Edition. Use when an FS describes mass-production confirmation, flow manufacturing, or backflush without order-by-order tracking. Paired with [Skill: sap-process-production-repetitive-planning] (same scope item, planning side). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP PP-REM consultant expert in repetitive manufacturing shop-floor execution (scope item **BJH**, execution half).

# Process Overview
Confirmation in REM is intentionally **lean** compared to discrete/process order confirmation: no order number to confirm against — actual quantity is posted directly against the Planned Order/Production Version, backflushing components and posting activity costs straight to the **Product Cost Collector**. **Reporting points** (milestone control key on select operations) are the main configurable checkpoint, not full operation-by-operation confirmation. Event-Based Production Cost Posting with Product Cost Collectors is supported as an alternative real-time posting mode.

**Make-to-order REM variant exists** (valuated sales order stock) — if the FS ties a specific customer sales order to REM production (not pure make-to-stock), flag this explicitly; it changes the cost-object linkage (costs post to the sales order stock, not just the PCC).

# Data Model Grounding
Shares `I_PLANNEDORDER` with [Skill: sap-process-production-repetitive-planning] — no separate confirmation-specific CDS view was found this session (Open Item, same as the planning-side PCC view — re-search at TS time).

# Common Configuration Touchpoints
- Repetitive Manufacturing Profile (backflush behavior — see planning-side skill).
- Reporting point / control key per operation.

# Related Processes
- [Skill: sap-process-production-repetitive-planning] — planning side of this exact scope item; read that skill's "structurally different" note before designing this skill's confirmation logic.
- [Skill: sap-process-supplychain-inventory-mgmt] — backflush and finished-goods receipt post Material Documents there, same as discrete/process execution.
- Finance skills (once built) — PCC is a periodic cost object, settled differently from per-order discrete/process costing.

# Deep Dive
For functional-consulting depth (lean/decoupled confirmation, backflush BOM-source selection, reporting-point mechanics, confirmation processing types, period-based vs event-based cost posting, embedded EWM synchronous-posting constraint) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
