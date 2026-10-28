# Deep Dive — sap-process-o2c-customer-returns (BKP)

Read this file when the FS requires real functional-consulting depth on the Customer Returns flow (business logic, master data setup, document control) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Return Reason vs. Rejection Reason vs. Refund Code — three distinct "reasons" an FS can conflate

A Customer Return touches THREE separate "reason" concepts, and an FS that just says "capture the reason" is usually only thinking of one of them:
- **Return Order Reason** — entered at header level (config: "Define Order Reasons"), copied down into each item's **Return Reason** for return-order types where the header reason applies per item (e.g. lean returns). It's not just a reporting tag: it's also usable as an access-sequence criterion in **pricing** to help determine the customer's refund amount — the same condition technique used everywhere else in SD.
- **Rejection Reason** — only relevant when you decide NOT to accept a return item at all (as an alternative to simply deleting the line). Critical detail for B2B scenarios: if the returns order was created from (or is integrated with) an external buyer system, rejecting an item *without* a rejection reason breaks the loop back — the buyer's own returns purchase order item never learns the return was declined. Config: "Define Reasons for Rejection."
- **Refund Code** — a completely different axis, living on the compensation side (see §4): a percentage (e.g. "70% Refund") applied against the order item's net value, configured in pricing via "Define Returns Refund Codes." New codes can be added if the standard set doesn't cover the client's refund policy.

**Practitioner implication:** when an FS says "we need a return reason field," ask which of the three it actually means — a statistics/pricing-eligibility tag (Return Order Reason), a decline explanation that must sync back to an external buyer system (Rejection Reason), or a refund-percentage driver (Refund Code). Each maps to a different configuration object and a different downstream system effect; treating them as one field will misdesign the TS.

## 2. Logistical Follow-Up Activity — the single field that drives the entire downstream document chain

The **Logistical Follow-Up Activity** is not a status flag — it's the trigger for whatever happens next, and the system creates the corresponding follow-on document automatically the moment the activity is set (either directly on the returns order item, if the goods are already physically in hand, or later during product inspection in "Enter Inspection Results - From Warehouse"). A few of the ~20 standard codes and what they actually do:
- **0001 Receive into Plant** — creates a returns delivery; goods receipt posts to (non-)valuated returns stock (see §3). This is the default, most common case.
- **0002 Immediately Move to Free Available Stock** / **0003 Immediately Move to Scrap** — goods receipt posts straight to valuated unrestricted-use stock (or scrap), completing logistics in one step; requires the product already received and inspected.
- **0005 Ship to Supplier** — goods are received into your stock first, *then* the system creates a returns purchase order to the specified supplier once inspected (bridges into the supplier-return/procurement side).
- **0007 Direct Shipment to Supplier** — the customer ships straight to the supplier, **skipping your own warehouse entirely**; only a returns purchase order is created, no returns delivery at your site at all.
- **0008 Inspection at Customer Site** — an explicit deferral: no system action is taken until the customer-site inspection result is known, at which point you change the activity to whatever the result implies.
- **0021 Send Back to Customer** — creates an actual outbound delivery back to the customer; used when, after all, you decide not to keep the returned goods.
- **0026 In-House Repair (Service)** — creates an in-house repair object, bridging the returns process into the Customer Service module.

**Practitioner implication:** an FS describing "the returned item should ship straight to our supplier without ever entering our warehouse" is literally logistical follow-up activity **0007** — a configuration/master-data question (supplier assignment, return-to address determination), not a custom shipping-notification feature to build. Likewise "customer can ask for an in-house repair instead of a refund" is activity **0026**, which is a cross-module dependency (Customer Service) the TS must flag explicitly, not invent from scratch.

## 3. Valuated vs. Non-Valuated Returns Stock — legal ownership timing, not a stock-type checkbox

**Non-valuated returns stock** (special stock type **E**) exists to reflect a legal requirement in several countries that ownership of returned goods stays with the customer until a deliberate decision is made to take it over — so the goods-receipt posting to it triggers **no FI posting at all**. This is the default outcome of the most common scenario: activity 0001 + refund control "Decide Later" (§4).

Ownership/valuation only gets triggered by one of two events:
1. **Issuing the refund itself** — a refund decision made while stock is still non-valuated immediately posts a goods movement transferring it into **valuated returns stock**; or
2. **Choosing a follow-up activity that itself signals ownership change** (0002, 0003, 0011, 0012, 0014, 0015, 0031) — these post directly to valuated stock, no intermediate step.

A **Suspend Product Valuation** indicator can decouple these two: settable only at returns-order-item *creation* (read-only afterward), it lets you approve an urgent refund/replacement without yet posting to valuated stock/FI — the actual valuation is deferred until the *final* logistical follow-up activity is confirmed at inspection. It is unavailable if refund control **I** (immediate) is chosen, if an ownership-changing follow-up activity is already selected, or if the receiving plant belongs to a different company code than the sales organization (cross-company-code stock movement always forces valuation).

A sharper, easy-to-miss nuance: **Valuation with Reference to Sales**. By default, the system valuates returned stock at the *current* price from the product master — but some countries legally require valuating the return at the *same* price/cost used in the original sale, so the cost-of-goods-sold reversal matches the original posting exactly. This is a per-item indicator (only available with a reference document, and only in "Manage Customer Returns - Version 2"), not a manual adjustment posting.

Cross-link: the underlying goods movement/material document mechanics belong to [Skill: sap-process-supplychain-inventory-mgmt]; the resulting FI/account-determination postings belong to [Skill: sap-process-finance-general-ledger].

**Practitioner implication:** "the credit/return should reverse the exact same cost as the original sale" in an FS is the Valuation-with-Reference-to-Sales indicator — but it only works if the returns order actually references the original sales order/invoice and a goods issue was posted for it; a returns order created without reference cannot use it.

## 4. Customer Compensation — Refund Type × Refund Control is a 2-dimensional decision, not one field

**Refund Type** answers WHAT the customer gets: **Credit Memo** (money, scaled by a Refund Code percentage — e.g. 70% of EUR 100 net value = EUR 70) or **Replacement Product** (a free-of-charge subsequent delivery — can even be a *different* product from a *different* supplying plant than the one that received the return, but restricted to available stock only; the system cannot create a replacement that needs procurement/manufacturing; sales-kit/BOM replacement is further restricted to specific item categories).

**Refund Control** is the orthogonal axis — WHEN/HOW the compensation is executed — with the same 3-value pattern for both refund types:
- **R "Decide Later"** — defer; no action taken now.
- **P "Create credit memo request" / "Create replacement order"** — starts the process (a credit memo request, or a free-of-charge order+delivery, gets created and is billed/released afterward).
- **I "Create credit memo" / "Immediate delivery"** — executes immediately: for a credit memo this requires the goods already marked as received; for a replacement, the system creates the FOC delivery *and* auto-posts its goods issue in one step.

**No Refund (N)** is an explicit decision, not the absence of one — settable upfront (e.g., known free-goods returns) or forced retroactively after certain follow-up activities: **Continue In-House Repair (Service) (0027)** cannot take "No Refund" live during inspection, so the process requires going back to the "Determine Refund" page afterward and selecting a rejection reason there. Even a committed "No Refund" is reversible later — a credit memo request or FOC delivery can still be created with reference to that returns order item.

Refund decisions can also be made **per inspection split** rather than for the whole item, when a single returns delivery item's quantity turns out to have mixed quality outcomes.

**Practitioner implication:** "auto-approve a full refund for defect-code returns but hold wrong-item returns for manual review" is a **refund-control default keyed off the return reason** (§1) — configure refund control **I** vs **R** per order reason and let the standard mechanism gate it, rather than designing a bespoke approval status machine.

## 5. Quality Inspection in Returns — a lighter SD-owned check, distinct from the full QM inspection lot

FS documents routinely blur two separate inspection layers:
- **Returns "Product Inspection"** — an inspection code + comment, entered either directly in the returns order (if the goods are already physically at hand) or later via "Enter Inspection Results - From Warehouse." This is SD/logistics-owned and exists purely to feed the logistical-follow-up-activity and refund decisions (§2, §4).
- **Full Quality Management inspection lot** — stock type **Q**, processed via the "Record Usage Decision" app — only fires when the material master's QM view has an inspection type actually activated (type 01/04 for goods receipt) and, for direct warehouse-managed postings, "QM for Synch. GM" is enabled in config. This is the classic procurement-side QM flow and is **not automatically active just because a returns order exists**.

Two more nuances worth knowing:
- **Inspection Splits** — if a single returns delivery item's quantity has mixed quality (part good, part damaged), split it into inspection-split sub-items and inspect/refund each independently.
- **Automatic Inspection** — lets you pre-record the inspection code and next follow-up activity in the returns order *before* the goods are physically received (e.g., assessed from a customer photo or phone call); the system then auto-creates and completes the inspection document the moment goods receipt posts, skipping a manual re-inspection step entirely. Requires the feature activated in "Configure Returns Order Type for Standard Return," and only applies when the follow-up activity is 0001 and the product isn't yet marked received.

Cross-link: the physical putaway-to-quality-area warehouse-task mechanics, when the full QM inspection-lot path is genuinely in play, belong to [Skill: sap-process-supplychain-warehouse-mgmt].

**Practitioner implication:** if an FS says "returned goods must pass QM inspection before restocking," verify whether it means the lightweight SD inspection-code/follow-up-activity mechanism (the default — no extra master data needed) or a genuine QM inspection lot (needs QM views and an inspection type configured on the material). Building for the wrong one either under-engineers a compliance requirement or over-engineers a simple case.

## 6. Approval Workflow for Returns Orders — BAdI-gated, and not every activity change re-triggers it

Returns orders can be blocked from proceeding to the next logistical step until approved — either via a manual approval block on the document, or an automatic workflow triggered on release. Whether a given returns order actually *needs* approval (and why) is not hardcoded: it runs through the BAdI **Set Approval Request Reasons for Sales Documents (SD_APM_SET_APPROVAL_REASON)**, called every time a returns-and-refund clerk saves the document; it returns an **Approval Request Reason** (config: "Define/Assign Reasons for Approval Requests") that tells the approver why. Once a given reason is flagged for use in an *external* workflow, it can no longer be used by SAP's own internal "Manage Sales Document Workflows" app for the same purpose — the two paths are mutually exclusive per reason.

Approval blocks more than just the save step: while an item sits under an active approval workflow (or a manual approval block), the system will **not** auto-create the returns delivery for it — the same suppression applies to a plain delivery block. "Pending approval" therefore silently halts downstream logistics, not just a cosmetic status.

One nuance worth flagging to a client up front: **Inspection at Customer Site (0008)** is treated as an intermediate step, so changing away from it once the customer-site result comes back does **not** re-trigger a new approval request — even though the follow-up-activity value itself changed.

For external-system integration, the SOAP/OData actions `releaseApprovalRequest` / `rejectApprovalRequest` exist on the Customer Return entity, but this channel cannot combine an approval action with any other document change in the same `$batch` changeset, and it cannot send the order back for rework or withdraw a request — those remain internal-workflow-only capabilities.

**Practitioner implication:** "add an approval step before a return can proceed" in an FS is a BAdI + approval-reason configuration exercise (structurally identical to how BD9 sales orders handle approval — see [Skill: sap-process-o2c-sell-from-stock]), not a custom status field. If the FS's trigger condition is itself something like "return value over $500," that threshold logic is Z-code, but it belongs *inside* the BAdI implementation hooked into the standard mechanism, not a parallel custom workflow.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
