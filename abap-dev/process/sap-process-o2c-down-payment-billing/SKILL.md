---
name: sap-process-o2c-down-payment-billing
version: 1.0
description: SAP Order-to-Cash process knowledge for Advanced Down Payment Processing — "Sell from Stock with Down Payment Requests" (scope item 7S7) — milestone billing plan requesting a down payment before/alongside delivery, on SAP S/4HANA Cloud Public Edition. Use when an FS describes collecting an advance/deposit payment on a sales order, a milestone billing plan tied to a down payment request, or explicitly mentions "Down Payment", "7S7", "Advanced Down Payment Processing", "ADP". Complements the FS-analysis skills (domain grounding).
---

# ROLE

You are an SAP SD (Sales & Distribution) functional consultant with deep, current knowledge of Advanced Down Payment Processing (ADP) — SAP Best Practices scope item **7S7**, "Sell from Stock with Down Payment Requests" — on SAP S/4HANA Cloud Public Edition.

# Process Overview

7S7 is **not a standalone process** — it explicitly *extends* [Skill: sap-process-o2c-sell-from-stock] (BD9) with down-payment capability via a milestone billing plan. Always treat an FS's down-payment requirement as "BD9 + a billing plan," not as an unrelated new object.

Standard flow:
1. **Sales Order creation** with a **milestone billing plan** attached, containing at minimum a down-payment-request milestone (percentage or fixed amount) before the final invoice milestone.
2. **Down Payment Request** billing document created from the milestone — this is a request/reminder document, not itself an accounting-relevant invoice; it prompts the customer for the advance payment.
3. **Customer pays the down payment** — posted against the down payment request; tracked via the **Down Payment Register**.
4. **Delivery + Goods Issue** — same as the underlying BD9 flow.
5. **Final Billing** — delivery-related (7S7's original, current release) or order-related (added later — check release notes for which billing-relatedness variant is active in the target system, this has evolved across releases) billing document is created; the previously-collected down payment is automatically offset/cleared against it.

**Current-release caveat (verify against the target system's actual release before finalizing a TS):** SAP Help explicitly notes that in the first release of ADP, only the Sell-from-Stock-with-Down-Payment-Requests process (7S7) is supported, and that delivery-related billing was the only supported billing-relatedness until order-related billing support was added in a later release. Do not assume a capability is available without checking the release the target system is actually on.

# Data Model Grounding

Builds directly on [Skill: sap-process-o2c-sell-from-stock]'s data model (`I_SALESORDER`, `I_SALESORDERITEM`, `I_OUTBOUNDDELIVERY`, `I_BILLINGDOCUMENT`, etc.) plus the billing-plan-specific views already verified this session:

| Business Object | CDS View | App Component |
|---|---|---|
| Sales Order Billing Plan (header) | `I_SALESORDERBILLINGPLAN` | SD-SLS-SO-2CL |
| Sales Order Billing Plan (item/milestone) | `I_SALESORDERBILLINGPLANITEM` | SD-SLS-SO-2CL |

**Open item — not yet confirmed this session:** a dedicated CDS view for the Down Payment Request document itself / Down Payment Register was not found via `sap_search_objects` with the query terms tried (`DownPayment`, `DownPaymentRequest`). Do not assume a specific view name — re-search at TS time (try FI-side down payment terms, e.g. searching the Accounts Receivable / down payment clearing area, since the actual financial posting side of a down payment request may live under a Finance-module released view rather than an SD one) before naming a source in a TS's Data Model section.

# Common Configuration Touchpoints

- Billing plan type / milestone configuration for the down-payment milestone (percentage vs. fixed amount).
- Prerequisite: scope item 7S7 (or its successor for order-related billing, if active) must be activated before the billing-plan-for-ADP configuration becomes relevant — this is a system/scoping precondition, not just a config step, worth calling out explicitly if the FS assumes ADP already works in the target system.

# Integration Points

- Down payment requests interact with Accounts Receivable / Financial posting once paid — cross-reference `[Skill: sap-process-finance-general-ledger]` (once built) for the accounting side rather than treating this as a pure SD concern.
- No dedicated external API distinct from the base BD9 integration set was found this session — reuse [Skill: sap-process-o2c-sell-from-stock]'s Integration Points, and re-check `sap_accelerator_hub_search` at TS time specifically for down-payment/billing-plan-related APIs if the FS requires external system awareness of the down payment status.

# Practitioner Notes

> The following are practical/experience-based observations, not sourced from official SAP documentation — treat as a starting hypothesis to validate against the specific FS and client, not as a specification.

- **Practitioner note:** always confirm with the FS/client whether the down payment request is a *hard gate* (goods cannot ship until paid) or purely informational (delivery proceeds regardless, payment tracked separately) — standard SAP ADP does not enforce a shipping block by itself; that would be additional custom logic if the FS requires it.
- **Practitioner note:** because this scope item's billing-relatedness capability changed across releases (delivery-related first, order-related added later), always confirm the target system's actual release/feature scope before committing a TS to a specific billing-relatedness assumption — do not default to whichever variant is more familiar from a different project.
- **Practitioner note:** [placeholder — awaiting user's own field experience on 7S7-specific gotchas; fill in during review before treating this section as complete].

# Related Processes
- [Skill: sap-process-o2c-sell-from-stock] — this skill is strictly an extension of that base flow, not a standalone process.

# Deep Dive
For functional-consulting depth (ADP vs. the older milestone-billing-rule mechanism, noted-item vs. real posting, down payment clearing/settlement register, tax code deviation on down payments, delivery-block config, dunning/collections and credit exposure touchpoints) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources

Full citations (SAP Help URLs, API Release State repository query results): `references/sources.md` — read only when auditing a specific claim above, not needed for normal use of this skill.
