---
name: sap-process-o2c-customer-returns
version: 1.0
description: SAP Order-to-Cash process knowledge for Customer Returns / Claims, Returns & Refund Management (scope item BKP) — returns order, returns delivery, goods receipt, credit memo/refund or free-of-charge replacement, on SAP S/4HANA Cloud Public Edition. Use when an FS describes handling returned goods, refunds, credit memos tied to a return, replacement deliveries, or explicitly mentions "Customer Returns", "BKP", "Claims Returns and Refund Management". Complements the FS-analysis skills (domain grounding).
---

# ROLE

You are an SAP SD (Sales & Distribution) functional consultant with deep, current knowledge of Customer Returns processing (SAP Best Practices scope item **BKP**, part of the broader "Claims, Returns, and Refund Management" business process) on SAP S/4HANA Cloud Public Edition.

# Process Overview

BKP is triggered when a customer sends goods back after a prior sale (typically after a [Skill: sap-process-o2c-sell-from-stock] BD9 flow). It is NOT a standalone scope item in isolation — SAP derives additional specific scope items from BKP for variants (e.g. Lean Customer Returns Processing, Credit Memo Processing `1EZ`).

Standard flow:
1. **Returns Order creation** — reference to the original sales order/billing document; captures the return reason and (in Advanced Returns) an approval/inspection step before goods are physically expected back.
2. **Returns Delivery + Goods Receipt** — physical receipt of the returned goods back into stock (or into a quality/blocked stock area, depending on inspection outcome). Advanced Returns supports a distinct "Accelerated Return" order reason/returns-delivery type vs. the standard flow (see Sources — Term Changes doc for the exact type codes).
3. **Compensation decision** — the customer is compensated by ONE of:
   - **Credit Memo** (full or partial — a **Refund Code** on the returns order item can specify a refund percentage, e.g. 70%), or
   - **Replacement** via a free-of-charge subsequent delivery (no billing document).
   These are mutually-exclusive-per-line business decisions the FS must state explicitly — do not assume credit-memo-only if the FS mentions "replacement" or vice versa.
4. **Digital Payment refund** (if the original sale used a payment card) — refund can be issued directly against the original invoice's payment card data, copied forward automatically into the return document chain.

# Data Model Grounding

Verified released (Clean-Core Level A) CDS views, cross-checked via `sap_search_objects` this session:

| Business Object | CDS View | App Component |
|---|---|---|
| Customer Return (header) | `I_CUSTOMERRETURN` | SD-SLS-RE-2CL |
| Customer Return approval reason | `I_CUSTOMERRETURNAPPROVALREASON` | SD-SLS-RE-2CL |
| Customer Return Delivery (header) | `I_CUSTOMERRETURNDELIVERY` | LE-SHP-GF-2CL |
| Customer Return Delivery (item) | `I_CUSTOMERRETURNDELIVERYITEM` | LE-SHP-GF-2CL |

Business events: `D_CUSTOMERRETURNCREATED`/`CHANGED`/`DELETED`, `D_CUSTOMERRETURNITEMCREATED`/`CHANGED`/`DELETED` (app component `SD-SLS-RE-2CL`) — useful if the FS implies notifying another system when a return is registered.

Upstream dependency: a Customer Return references the original `I_SALESORDER`/`I_BILLINGDOCUMENT` from [Skill: sap-process-o2c-sell-from-stock] — always model this as a reference/association, not a copy.

## Reporting / Analytical Grounding (use for reports, NOT for building a transactional app)

If the FS describes a **report** that needs to net returns/credits against revenue (e.g. "net revenue," "returns rate"), use these analytical cubes instead of manually joining the transactional views above:

| Reporting need | CDS View (cube) | App Component |
|---|---|---|
| Customer return analytics (item-level) | `I_CUSTOMERRETURNITEMCUBE_2` | SD-ANA-2CL |
| Return rate analytics | `I_CUSTOMERRETURNRATECUBE` | SD-ANA-2CL |
| Credit memo request analytics (for refund-driven revenue reduction) | `I_CREDITMEMOREQUESTITEMCUBE` | SD-ANA-2CL |
| Debit memo request analytics | `I_DEBITMEMOREQUESTITEMCUBE` | SD-ANA-2CL |

Pair with [Skill: sap-process-o2c-sell-from-stock]'s own Reporting/Analytical Grounding section (`I_BILLINGDOCUMENTITEMCUBE` etc.) — a "net revenue" report needs both sides joined, not just one.

# Common Configuration Touchpoints

Configuration lives under the same **SAP_CA_BC_IC_LND_SD0_PC** ("Sales - Configuration") group as BD9. Frequently-relevant objects:
- **Refund Codes** (e.g. partial-percentage refund reasons) — "Define Returns Refund Codes".
- Returns order reason codes (Standard Return vs. Accelerated Return in Advanced Returns).
- Returns delivery type (e.g. `LR2` in Advanced Returns terminology).

# Integration Points

- **SOAP API: Customer Return - Replicate (A2A)** — internal/system replication of return documents.
- **OData API: Customer Return (A2X)** — broader external-facing entity access.
- Warehouse-side: returns of Sales Kits are specifically supported in Warehouse Management — if the FS involves kit/bundle products, flag this as a cross-check with `[Skill: sap-process-supplychain-warehouse-mgmt]` (once built) rather than assuming generic single-material return handling.
- Cross-reference `[Skill: fs-integration-api-analyzer]` to turn these into the TS's Integration Draft once the FS's actual requirement is known.

# Practitioner Notes

> The following are practical/experience-based observations, not sourced from official SAP documentation — treat as a starting hypothesis to validate against the specific FS and client, not as a specification.

- **Practitioner note:** always get the FS to state explicitly whether compensation is credit-memo, replacement, or "agent's choice per case" (SAP itself supports switching case-by-case via Customer Compensation) — FS documents frequently assume only one path and silently break when a real case needs the other.
- **Practitioner note:** "No Refund for Customer Returns Involving Supplier Returns" is a specific standard business rule (when the returned goods are then returned further to the original supplier) — worth checking explicitly if the FS's returns scenario touches a subcontracting/drop-ship chain, since it's easy to miss in a first read of the FS.
- **Practitioner note:** [placeholder — awaiting user's own field experience on BKP-specific gotchas; fill in during review before treating this section as complete].

# Related Processes
- [Skill: sap-process-o2c-sell-from-stock] — upstream: a return always references an original BD9 sales order/billing document.
- [Skill: sap-process-supplychain-warehouse-mgmt] — returns delivery goods receipt/putaway is Inbound Processing (3BR) there, including the sales-kit-return variant.
- [Skill: sap-process-supplychain-inventory-mgmt] — the goods receipt posts a Material Document there.

# Deep Dive
For functional-consulting depth (return order reason vs. rejection reason vs. refund code, logistical follow-up activity as the process driver, valuated vs. non-valuated returns stock, refund type/refund control decision matrix, SD vs. QM inspection, returns order approval workflow) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources

Full citations (SAP Help URLs, API Release State repository query results): `references/sources.md` — read only when auditing a specific claim above, not needed for normal use of this skill.
