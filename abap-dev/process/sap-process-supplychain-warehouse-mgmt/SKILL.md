---
name: sap-process-supplychain-warehouse-mgmt
version: 1.0
description: SAP Supply Chain process knowledge for embedded Warehouse Management — Inbound Processing (scope item 3BR) and Outbound Processing (scope item 3BS) — putaway/goods receipt and picking/goods issue via Warehouse Tasks, on SAP S/4HANA Cloud Public Edition. Use when an FS describes physical warehouse operations (putaway, picking, warehouse tasks, bin location), not just accounting-level stock. Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP EWM (embedded Warehouse Management) consultant expert in Warehouse Inbound/Outbound Processing.

# Process Overview
**Important:** there is no single "core WM" scope item — SAP splits it by direction:
- **Inbound Processing (3BR**, or **5HN** if synchronous goods receipt is needed**)**: goods receipt → putaway via Warehouse Task.
- **Outbound Processing (3BS)**: delivery → picking via Warehouse Task → goods issue.

Both operate at **Warehouse Task** granularity (the WM-level document), distinct from and synchronized with the Inventory Management-level Material Document ([Skill: sap-process-supplychain-inventory-mgmt]) — a report/build touching physical warehouse operations needs Warehouse Task data, not just Material Document.

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Warehouse Task | `I_EWM_WAREHOUSETASK_2` | SCM-EWM-WOP-2CL |

# Common Configuration Touchpoints
- Putaway/picking strategy configuration.
- Synchronous vs. asynchronous goods receipt posting between WM and Inventory Management.
- Warehouse Task exception codes (`I_EWM_WhseTaskExceptionCode_2`, released for extensibility).

# Related Processes
- [Skill: sap-process-o2c-sell-from-stock] — outbound delivery triggers Outbound Processing (3BS) picking here.
- [Skill: sap-process-o2c-customer-returns] — returns receipt uses Inbound Processing (3BR) putaway, including the sales-kit-return variant noted in that skill.
- [Skill: sap-process-supplychain-inventory-mgmt] — every WM goods movement posts a corresponding Material Document; a report needing accounting-level stock value should join through Inventory Management, not this skill's Warehouse Task view.
- [Skill: sap-process-manufacturing-discrete-execution] / [Skill: sap-process-manufacturing-process-execution] / [Skill: sap-process-manufacturing-repetitive-execution] — component staging/backflush at production integrates with WM via a dedicated Warehouse-Production-Integration scope item (3DV) if embedded WM is active.

# Deep Dive
For functional-consulting depth (warehouse process type determination, putaway/stock removal strategies and storage type search sequences, wave and warehouse order grouping, resource/queue work distribution, HU/packing, and confirmation exception handling incl. quality-inspection routing) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
