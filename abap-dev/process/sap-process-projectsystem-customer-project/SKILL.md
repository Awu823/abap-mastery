---
name: sap-process-projectsystem-customer-project
version: 1.0
description: SAP Project System process knowledge for Customer Project Management (scope item J11) — Enterprise Project/WBS structure billed to an external customer, project-based services billing, on SAP S/4HANA Cloud Public Edition. Use when an FS describes a customer-facing project, WBS-based billing, professional services engagement, or explicitly "Customer Project Management"/"J11". Paired with [Skill: sap-process-projectsystem-internal-project] (same structure, internal-facing variant). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP PPM/PS consultant expert in Customer Project Management (scope item **J11**).

# Process Overview
**Enterprise Project** (root) with **WBS Elements** (structure) → time/expense/service recording against WBS → **project-based billing** to the customer (via a Sales Order referencing WBS, or the newer "Manage Billing Documents" process flow). Related scope items commonly co-occur: **J12** (Time Recording), **J13** (Service and Material Procurement), **J14** (Sales Order Processing - Project-Based Services), **4E9** (Project Billing).

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Enterprise Project (header) | `I_ENTERPRISEPROJECT` | PPM-SCL-STR |
| Enterprise Project Element (WBS) | `I_ENTERPRISEPROJECTELEMENT` / `_2` | PPM-SCL-STR |
| Enterprise Project Role (assignment) | `I_ENTERPRISEPROJECTROLE` | PPM-SCL-STR |

Business events: `D_ENTERPRISEPROJECTCREATED`/`CHANGED`/`DELETED` (app component `PPM-SCL-STR`).

**Public Cloud naming note:** this is "Enterprise Project Management" (EPPM) — the classic on-premise `I_WBSElement`/PS transaction-code model does NOT apply in Public Cloud; always use `I_ENTERPRISEPROJECTELEMENT`, not a classic PS view name.

# Common Configuration Touchpoints
- Project profile / WBS element type.
- Billing method assignment (sales-order-based vs. direct project billing).

# Related Processes
- [Skill: sap-process-o2c-sell-from-stock] — J14's Sales Order Processing links a sales order item to a WBS element for project-based billing; the sales order data model there applies.
- [Skill: sap-process-finance-general-ledger] — project revenue/cost postings land there; if using Event-Based Revenue Recognition (scope items 4GQ/4GR/1IL), that recognition timing differs from standard delivery-based O2C recognition — flag explicitly in a TS.
- [Skill: sap-process-projectsystem-resource-mgmt] — resource staffing onto this project's WBS.
- [Skill: sap-process-projectsystem-internal-project] — same Enterprise Project/WBS structure, internal (non-billable) variant.

# Deep Dive
For functional-consulting depth (billing element & project account assignment, contract-type-driven billing methods, Event-Based Revenue Recognition/POC keys, loss handling for onerous contracts, settlement vs. revenue recognition, resource staffing without a hard availability check) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
