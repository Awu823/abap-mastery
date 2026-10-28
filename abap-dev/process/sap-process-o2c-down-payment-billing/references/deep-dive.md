# Deep Dive — sap-process-o2c-down-payment-billing (7S7)

Read this file when the FS requires real functional-consulting depth on Advanced Down Payment Processing (ADP) — business logic, master-data/config setup, tax and collections nuance — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Two Down Payment Mechanisms — Don't Confuse ADP with the Older Milestone-Billing-Rule Approach

SAP S/4HANA Cloud Public Edition ships **two distinct** SD down-payment mechanisms, and an FS that just says "we need a down payment" doesn't tell you which one the target system actually has active:
- **Older mechanism** (scope item BKJ, "Down Payment Processing Using Milestone Billing Plans"): the down payment is expressed *inside an ordinary milestone billing plan* via **Billing Rule 4** (percentage of the total item amount) or **Billing Rule 5** (fixed value) on a billing plan date. This billing plan can **only be used for order-related billing**, never delivery-related — see "Down Payment Agreements in Sales Orders."
- **Newer ADP mechanism** (7S7 and its later extensions, e.g. 7Z1 "Sales Order Processing with Milestone Billing"): the down payment is expressed via dedicated **down-payment-relevant billing plan date categories 03** (percentage, maps internally to billing rule 4) or **04** (fixed amount, billing rule 5), on item categories **CBAO** (trading goods, delivery-relevant), **CTAX** (non-stock products, delivery-relevant), or **CTAD** (service products, *not* delivery-relevant). The system proposes **billing type DPR1** automatically, and a **down payment variant** field on the item must be set to **R** (down payment request) to enable it.

Critically: once ADP is activated for a given item category, **that item category can no longer be used for the older BKJ process** in new sales orders — this is a hard block, not a style preference, and the down payment variant field itself becomes non-editable once a subsequent delivery/billing document, a contract reference, or an ATP-based product substitution already exists on the item.

**Practitioner implication:** before writing a TS, check which scope item(s) are actually activated in the target system and which item category the client intends to reuse. Mixing the two mechanisms on the same item category is a go/no-go compatibility check to make explicit, not something to discover during testing.

## 2. Down Payment Request = Noted Item, Not Yet a Real Posting

When a down payment request (billing type **FAZ**, cancel type **FAS**) is posted to financial accounting, the system creates a special journal entry marked as a **noted item** — **special G/L indicator F** — that is explicitly a placeholder: it has **zero effect on the balance sheet or the P&L account**. It only signals "a down payment is expected." Because it's a noted item, standard AR open-item/reconciliation logic on the customer account does **not** show it as a real receivable — a report or FS requirement expecting "down payment requested" to already show up as outstanding AR is wrong until the customer actually pays.

Only when the customer pays does an AR accountant post the incoming payment (**Post Incoming Payments**), which clears the noted item and creates the **real** posting — **special G/L indicator A**, **posting key 19** — for the total amount **including tax**. From that point the amount is a liability (an obligation to deliver goods), not yet earned revenue; revenue recognition only happens later when the actual sale is settled (see [Skill: sap-process-finance-general-ledger] for how G/L account determination and journal entries work on the FI side of this).

**Practitioner implication:** never assume "down payment request created" implies "AR/cash increased." That transition only happens at the incoming-payment step. If an FS wants a KPI on "down payments outstanding vs. collected," the correct source is the noted item / down payment register status, not a plain G/L balance query.

## 3. Down Payment Clearing at Invoice Time — Settlement, Not Subtraction

At each subsequent invoice (partial or final) covering a down-payment-relevant item, the system inserts previously-received down payments as **clearing items underneath the billing items they relate to**. SAP Help is explicit that "no billing calculation in the sense of Billing Amount − Down Payment Amount = Remaining Amount is made" — the invoice's own total/tax lines stay at gross value; down payment clearing is a separate settlement instruction shown to the customer, not a line-item price reduction.

The **Down Payment Register** (a tab on every settlement-relevant invoice/preliminary invoice) gives a granular, per-item, editable table of which down payment requests/amounts are eligible for settlement against which sales-document item. By default it runs a "**maximum settlement per item**" auto-distribution: for each row it takes the smaller of (available unsettled down payment amount, total billing amount of that item), applied top to bottom — a billing clerk can manually reduce a proposed settlement to defer part of it to a future invoice (common on multi-milestone projects). Settlement only becomes final when the invoice **posts** to FI; saving without posting (or saving a preliminary invoice) merely **reserves** the amount, which blocks it from being settled against any other invoice item in the meantime.

SAP's own worked example: on a USD 150,000 sale, a partial invoice settles USD 60,000 of down payments but the down-payment amount exceeds that partial invoice's own item value by USD 15,000 — that excess carries forward and gets applied against the final invoice instead. Down payments do **not** have to align 1:1 with the invoice that originally requested them.

**Practitioner implication:** if an FS says "final invoice amount = total minus down payment," don't model that as document-level arithmetic. Describe it as down payment register settlement per item — a partial-invoice / multi-milestone scenario can legitimately carry left-over settlement amounts forward exactly as in the example above.

## 4. Tax Handling — the Down Payment's Tax Can Legitimately Differ from the Final Invoice's Tax

The amount actually cleared in a down payment's journal entry is **requested down payment amount + tax**, not net-only — this matters when reconciling why a "fully paid" down payment status corresponds to a gross, not net, cleared amount.

Because different countries (and EU member states specifically) disagree on whether down payments are even taxable, SAP provides a dedicated condition-technique override: condition type **TTX1**, key combination "Export Taxes Depending on the Billing Category," using **billing category P** (down payment request). A tax specialist (`SAP_BR_TAX_SPECIALIST`) can maintain a **different tax code for the down payment request (billing type FAZ) than for the corresponding clearing/settlement invoice** — e.g. a German seller can set tax code A0 (0% output tax) on the down payment request while the clearing invoice still carries a real output-tax code, since Germany doesn't require tax reporting at the down-payment stage for cross-border EU supply.

**Down Payments with Multi-Level Tax** (relevant for GST-style tax-on-tax regimes) is explicitly supported for both manual posting and the automatic down-payment-request/down-payment posting flows — but this must be checked and configured per country, never assumed to "just work" the same way everywhere. Separately, when a final invoice performs down payment clearing, the system **re-translates the down payment's tax amount into local currency at that point** rather than reusing the original request's translated figure — relevant whenever the down payment and the final invoice straddle an exchange-rate change.

**Practitioner implication:** never assume the down payment request's tax code/rate is simply copied onto the final invoice. Always ask whether the client's country requires a deviating down-payment tax treatment (including "not taxed at all") before designing tax logic as "copy from order."

## 5. The Delivery Block Is Real — Refine the "Is It a Hard Gate" Question

Standard ADP does **not automatically** block delivery — but that's only true when the delivery block is not configured. If date categories **03/04** are configured with a delivery block in the **Define Date Categories for Billing Plan Types** configuration activity, the system **automatically sets a delivery block on the schedule lines** of a down-payment-relevant item the moment such a billing plan date is created (and on any schedule line added later). The block is only removed automatically once the item's down payment status reaches **fully paid**; for delivery-relevant item categories (CBAO, CTAX), clearing the incoming payment removes it directly.

One config trap worth flagging explicitly: the **schedule line category's own delivery block setting takes priority over the billing plan type's block** — to make the billing-plan-type-level block actually take effect, the schedule line category's block must be manually removed. "I configured the block on the billing plan type but shipping proceeded anyway" is a classic symptom of this priority order, not a bug.

Down payment status is tracked at both **item level** and **header level** (values: Not relevant / Not paid / Partially paid / Fully paid), fully visible and auditable in the sales order's status log (Display/Change Sales Orders apps) — this is the correct source for "is this order's down payment still outstanding," not a custom Z-field.

**Practitioner implication:** "does the down payment block delivery" isn't a yes/no answer about ADP as a feature — it's a yes/no answer about two specific, independently-set config activities (date-category delivery block + schedule-line-category override) that must be checked in the target system before an FS's shipping-gate assumption gets written into a TS.

## 6. Dunning and Collections on a Request That's Legally "Non-Binding"

SAP Help explicitly frames a down payment request as **non-binding** — "an offer to the customer" that they aren't legally required to pay; if they decline, the request is simply canceled (billing type FAS) and the transaction doesn't proceed. This sits in tension with the fact that the *same* posted down payment request carries a **Due On** date and a **Payment Block** field, and is dunnable exactly like any other AR item: "the dunning program needs this information to be able to dun the down payment" (Post Customer Down Payment Requests). A separate **collection authorization** from the customer is what lets the down payment be **included automatically** rather than only reminded/dunned manually.

Down payments also feed **Credit Management exposure** — SD's credit-exposure data explicitly lists open sales orders "and down payments" as exposure components — so an overdue, unpaid down payment can raise a customer's credit exposure and contribute to a **credit block on new orders**, even though the request itself was "non-binding" when issued.

**Practitioner implication:** if an FS asks "should we dun customers who haven't paid their down payment," the standard dunning program already can (due date + dunning program treats it like any AR item) — the real design question to raise with the client is a **collections-policy** decision (do we want to dun a legally non-binding request?), not a technical gap to build.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
