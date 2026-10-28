---
name: sap-process-supplychain-inventory-mgmt
version: 1.0
description: SAP Supply Chain process knowledge for Core Inventory Management (scope item BMC) — goods movements, material documents, stock types, physical inventory, on SAP S/4HANA Cloud Public Edition. Use when an FS describes stock levels, goods movement postings, stock transfer, physical inventory count, or explicitly "Inventory Management"/"BMC". Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP MM-IM (Inventory Management) consultant expert in Core Inventory Management (scope item **BMC**).

# Process Overview
Every physical stock change (goods receipt, goods issue, transfer posting, physical inventory adjustment) posts a **Material Document** — the accounting-relevant, value+quantity record of the movement. This is the layer every other O2C/Manufacturing/Returns process ultimately posts against for stock impact; it's downstream of Warehouse Management's Warehouse Task ([Skill: sap-process-supplychain-warehouse-mgmt]), not a duplicate of it.

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Material Document (header) — movement history | `I_MATERIALDOCUMENTHEADER_2` | MM-IM-VDM-SGM-2CL |
| Material Document (item) — movement history | `I_MATERIALDOCUMENTITEMTP` | MM-IM-GF-2CL |
| **Current stock balance** (point-in-time on-hand quantity) | `I_MATERIALSTOCK_2` | MM-IM-VDM-SGM-2CL |
| Stock balance time series | `I_MATERIALSTOCKTIMESERIES` | MM-IM-VDM-SGM-2CL |

**Do not confuse the two.** Material Document = movement/transaction history (what changed, when). Material Stock = current balance (how much is on hand right now). A report asking "how much stock is available" needs `I_MATERIALSTOCK_2`, NOT an aggregation of Material Documents — this gap was found via a real test case (dashboard FS) before this note was added, so treat the distinction as load-bearing, not cosmetic. `I_MATERIALSTOCK` (no suffix) is deprecated — use `I_MATERIALSTOCK_2`.

Business events: `D_MATERIALDOCUMENTCREATED_2`/`D_MATERIALDOCUMENTCANCELED_2` (header), `D_MATERIALDOCUMENTITEMCRTED_2`/`CANCLD_2` (item) — app component `MM-IM-GF-2CL`.

# Common Configuration Touchpoints
- Goods Movement Type / Reason Code (`I_GoodsMovementCode`, `I_GoodsMovementReasonCode`) — determines stock-type/account impact of a movement.
- Stock Determination Rule per movement type.

# Related Processes
- [Skill: sap-process-o2c-sell-from-stock] — goods issue at delivery reduces stock here; this skill supplies the resulting Material Document.
- [Skill: sap-process-o2c-customer-returns] — goods receipt from a return increases stock here (or into a quality/blocked area — see returns skill).
- [Skill: sap-process-supplychain-warehouse-mgmt] — Warehouse Task confirmation is what triggers the Material Document posting here; a report needing bin/physical-location detail needs that skill too, not just this one.
- [Skill: sap-process-manufacturing-discrete-execution] / [Skill: sap-process-manufacturing-process-execution] / [Skill: sap-process-manufacturing-repetitive-execution] — production goods receipt (finished goods in) and backflush component consumption (raw material out) all post here.

# Deep Dive
For functional-consulting depth (movement type & account determination, special stock indicators, physical inventory process, goods movement reversal, batch management & split valuation, stock transfer in-plant/cross-plant) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
