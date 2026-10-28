---
name: sap-process-supplychain-atp
version: 1.0
description: SAP Supply Chain process knowledge for Basic Available-to-Promise (scope item 2LN) — product availability check (PAC) and backorder processing (BOP) on SAP S/4HANA Cloud Public Edition. Use when an FS mentions availability check, confirmed quantity/date on a sales order, stock reservation, or backorder processing, or explicitly "ATP"/"2LN". Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP SCM consultant expert in Basic ATP (scope item **2LN**).

# Process Overview
- **Product Availability Check (PAC)**: runs automatically when a sales order/delivery is created, checks stock + inbound supply at plant/storage-location level, returns a confirmed quantity/date.
- **Backorder Processing (BOP)**: re-runs confirmations across open orders when supply situation changes (e.g. new goods receipt), re-allocates scarce stock by priority rule.
- 2LN is a **cross-cutting check**, not a standalone document flow — it's invoked BY other processes (sales order creation, production order component check), it doesn't create its own business object.

# Data Model Grounding
| Object | CDS View | App Component | Note |
|---|---|---|---|
| ATP checking group (config lookup) | `I_ATPCHECKINGGROUP` / `I_ATPCHECKINGGROUPTEXT` | CA-ATP-2CL | Successor of deprecated `I_PRODAVAILABILITYCHECKGROUP*` — always use the new name |

**Open item:** no dedicated "ATP check result" CDS view was found this session — the actual confirmed-quantity/date fields typically surface as part of the calling document (`I_SALESORDERITEM` etc. from [Skill: sap-process-o2c-sell-from-stock]), not a separate ATP entity. Re-verify at TS time if the FS needs to read raw ATP results directly.

# Common Configuration Touchpoints
- ATP checking group assignment (per material/plant).
- Quantity distribution rules (scope of availability check, incl. component checks in production orders/planned orders).
- Backorder processing confirmation strategy (priority rules for re-allocation).

# Related Processes
- [Skill: sap-process-o2c-sell-from-stock] — PAC is the availability step inside BD9's sales-order-creation flow; this skill supplies the check mechanism itself.
- [Skill: sap-process-supplychain-inventory-mgmt] — ATP checks against the same stock this skill manages.
- [Skill: sap-process-production-discrete-planning] / [Skill: sap-process-production-process-planning] / [Skill: sap-process-production-repetitive-planning] — component availability check during production/planned order creation uses the same 2LN mechanism.

# Deep Dive
For functional-consulting depth (checking rule vs. checking group, scope of check & check horizon, transfer-of-requirements gate, confirmed quantity/date splitting, backorder processing & confirmation strategies, Basic ATP vs Advanced ATP boundary) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
