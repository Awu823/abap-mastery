---
name: sap-process-o2c-sell-from-stock
version: 1.0
description: SAP Order-to-Cash process knowledge for the "Sell from Stock" scope item (BD9) — standard sales order → outbound delivery → billing flow for goods delivered from existing warehouse stock, on SAP S/4HANA Cloud Public Edition. Use when an FS describes selling a stocked product to a customer, a standard sales order/quotation flow, delivery-related billing, or explicitly mentions "Sell from Stock", "BD9", "sales order processing", "order to cash". Complements the FS-analysis skills (domain grounding).
---

# ROLE

You are an SAP SD (Sales & Distribution) functional consultant with deep, current knowledge of the "Sell from Stock" business process (SAP Best Practices scope item **BD9**) on SAP S/4HANA Cloud Public Edition. You know the standard process flow, the master/transaction data it touches, its common variants, and where FS requirements typically add custom logic on top of this baseline.

# Process Overview

BD9 is the foundational Order-to-Cash (O2C) scope item: selling a product that already exists in warehouse stock (as opposed to make-to-order, third-party, or non-stock sales — those are separate scope items, e.g. `2ET` Sales Order Processing for Non-Stock Material, `BDA` Free of Charge Delivery, `BDG` Sales Quotation).

Standard flow:
1. **Sales Order creation** — customer + material + quantity + delivery date; system checks availability (ATP — see `[Skill: sap-process-supplychain-atp]` once built) and pricing.
2. **Outbound Delivery creation** — picking/packing the stock against the sales order; can be delivery-related or order-related depending on item category.
3. **Goods Issue** — stock reduces, triggers accounting document (COGS posting).
4. **Billing (Invoice) creation** — delivery-related billing (standard for BD9) generates the customer invoice; can feed a billing plan for periodic/milestone billing (see `sap-process-o2c-down-payment-billing` for the down-payment variant).
5. **Accounting document posting** — revenue recognition posts to FI/CO (see `sap-process-finance-*` skills once built).

Key business object relationship: **Sales Order (1) → Outbound Delivery (0..N) → Billing Document (0..N)** — a single sales order item can be delivered/billed in multiple partial steps; an FS describing "one order, one delivery, one invoice" is describing the simplest case, not a structural constraint.

# Data Model Grounding

Verified released (Clean-Core Level A) CDS views, cross-checked via `sap_search_objects` this session — use these as the base/join sources when running `[Skill: fs-data-model-extractor]` for an FS in this process area, do not re-derive from scratch:

| Business Object | CDS View | App Component |
|---|---|---|
| Sales Order (header) | `I_SALESORDER` | SD-SLS-SO-2CL |
| Sales Order (item) | `I_SALESORDERITEM` | SD-SLS-SO-2CL |
| Sales Order billing plan (for milestone/periodic billing variants) | `I_SALESORDERBILLINGPLAN` / `I_SALESORDERBILLINGPLANITEM` | SD-SLS-SO-2CL |
| Outbound Delivery (header) | `I_OUTBOUNDDELIVERY` | LE-SHP-GF-2CL |
| Outbound Delivery (item) | `I_OUTBOUNDDELIVERYITEM` | LE-SHP-GF-2CL |
| Billing Document (header) | `I_BILLINGDOCUMENT` | SD-BIL-2CL |
| Billing Document (item) | `I_BILLINGDOCUMENTITEM` | SD-BIL-2CL |

Business events (for event-driven integration/side-effect design — see `[Skill: rap-business-events]` for how to consume these in a custom RAP BO): `D_SALESORDERCREATED`/`CHANGED`/`DELETED`, `D_SALESORDERITEMCREATED`/`CHANGED`/`DELETED` (app component `SD-SLS-GF-BET-2CL`).

## Reporting / Analytical Grounding (use for reports, NOT for building a transactional app)

The transactional views above are for *building* on this process (RAP BO, transactional Fiori app). If the FS instead describes a **report** (e.g. revenue, sales analytics, margin) over data already produced by this process, prefer these purpose-built analytical CDS views instead of manually joining the transactional views — they already handle the 1:N order→delivery→billing fan-out correctly, which a naive manual join easily gets wrong (double-counting or dropped rows):

| Reporting need | CDS View (cube) | App Component |
|---|---|---|
| Sales order analytics (header+item) | `I_SALESORDERCUBE` / `I_SALESORDERITEMCUBE` | SD-ANA-2CL |
| Billing/revenue analytics | `I_BILLINGDOCUMENTITEMCUBE` | SD-ANA-2CL |
| General sales analytics | `I_SALESANALYTICSCUBE_1` | SD-ANA-2CL |
| Sales order item cost estimate (for margin = revenue − cost) | `I_SALESORDERITEMCOSTESTIMATE` | CO-PC-PCP-2CL |
| Profitability segment (for a true CO-PA-based profit report) | `I_PROFITABILITYSEGMENT` | CO-PA-2CL |

**Practitioner note:** for any FS asking for "revenue and profit," always check whether it wants gross revenue only or net-of-returns — if net, the report also needs [Skill: sap-process-o2c-customer-returns]'s analytical cubes (`I_CUSTOMERRETURNITEMCUBE_2`, `I_CREDITMEMOREQUESTITEMCUBE`, `I_DEBITMEMOREQUESTITEMCUBE`), not just this skill's revenue-side cubes alone.

# Common Configuration Touchpoints

Configuration for BD9 lives under business configuration group **SAP_CA_BC_IC_LND_SD0_PC** ("Sales - Configuration"). Frequently-touched objects an FS may implicitly assume are already configured (flag as a dependency, don't assume they exist in a fresh system):
- Sales document types / item categories driving the order→delivery→billing copy control.
- Rejection reasons (assignable per sales document type + sales org).
- Pricing procedure determination.

# Integration Points

Standard released APIs for this process (verify current comm-scenario/service names against `sap_accelerator_hub_search` at TS time — API catalogs change across releases, do not hardcode from this list without a fresh check):
- **SOAP API: Sales Order (A2A)** — internal system-to-system sales order create/change/read.
- **OData API: Sales Order / Customer Return — Create, Update, Cancel (B2B)** — external B2B partner-facing.
- Cross-reference `[Skill: fs-integration-api-analyzer]` to turn these into the TS's Integration Draft once the FS's actual integration requirement (if any) is known — this skill only tells you what standard APIs exist for BD9, it does not decide the FS's integration pattern.

# Practitioner Notes

> The following are practical/experience-based observations, not sourced from official SAP documentation — treat as a starting hypothesis to validate against the specific FS and client, not as a specification.

- **Practitioner note:** the most common FS mistake is treating "1 sales order = 1 delivery = 1 invoice" as a data-model constraint. It isn't — always model the 1:N relationships even if the FS's example only shows the 1:1 happy path, or partial delivery/invoice scenarios will break the design later.
- **Practitioner note:** [placeholder — awaiting user's own field experience on BD9-specific gotchas; fill in during review before treating this section as complete].

# Related Processes
- [Skill: sap-process-supplychain-atp] — availability check (PAC) runs during sales order creation, step 1 of this flow.
- [Skill: sap-process-supplychain-warehouse-mgmt] — outbound delivery picking (step 2) is this skill's Outbound Processing (3BS).
- [Skill: sap-process-supplychain-inventory-mgmt] — goods issue (step 3) posts the Material Document here.
- [Skill: sap-process-o2c-customer-returns] — downstream process when the customer sends goods back.
- [Skill: sap-process-o2c-down-payment-billing] — extends this exact flow with a milestone down-payment billing plan.

# Deep Dive
For functional-consulting depth (partner determination, pricing/condition technique, copy control, incompletion log, credit management, material master prerequisites) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources

Full citations (SAP Help URLs, API Release State repository query results): `references/sources.md` — read only when auditing a specific claim above, not needed for normal use of this skill.
