# Deep Dive — sap-process-o2c-sell-from-stock (BD9)

Read this file when the FS requires real functional-consulting depth on the Sell from Stock flow (business logic, master data setup, document control) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Partner Determination — WHY 4 roles can differ, and when they must

A sales order plans **partner functions**, not just "the customer": **Sold-to Party (SP)**, **Ship-to Party (WE)**, **Bill-to Party (BP/RE)**, **Payer (PY/RG)**. These commonly diverge in real business:
- A retail chain's SP is head office; WE is the specific store receiving goods; PY is a shared-service AP center that pays all invoices centrally.
- The **Payer** can be configured as a *changeable* partner function directly on the sales order (override the master-data default) — an FS that says "customer can redirect the invoice to a different payer per order" is describing exactly this override, not a new feature to build.
- Partner determination is a **procedure** (config: access sequence resolving from customer master partner relationships, e.g. "preceding document → business partner relationship: sold-to → current partner"). A TS should reference "Partner Determination Procedure" as an FS-facing configuration concept, not assume it's hardcoded.
- Billing documents can mandate SP/PY/BP as **required** partner functions — if any is missing, the document is incomplete and cannot bill (ties to §3 Incompletion Log).

**Practitioner implication:** if an FS says "one customer field on the order," push back — ask which of the 4 roles it actually means, because pricing (customer pricing procedure comes from SP or PY depending on config), tax jurisdiction (often ship-to driven), and dunning/collections (payer-driven) all depend on getting the right one.

## 2. Pricing — Condition Technique (the mechanism behind "how does the system calculate price")

**Pricing Procedure** = an ordered sequence of **condition types** (price, discount, surcharge, freight, tax) + subtotals. It is *determined*, not fixed per document, via: **Sales Area** (Sales Org/Distribution Channel/Division) + **Customer Pricing Procedure** (from customer master) + **Document Pricing Procedure** (from sales document type). This 3-way determination is a common FS blind spot — "the system should just apply the customer's price list" implicitly assumes this determination already resolved to the right procedure; if the FS introduces a NEW pricing scenario (e.g. a new discount type), the TS needs a new condition type + its place in the procedure, not just a "price field."

Each condition type is found via an **access sequence** (search strategy: e.g. try customer+material specific price first, fall back to material-only price list). **Revenue Account Determination** reuses the same condition technique — an **account key** on each pricing condition type routes its value to a specific G/L account (see [Skill: sap-process-finance-general-ledger]) — this is *why* discounts/freight/tax can each post to different revenue/expense accounts automatically, not a manual mapping step.

**Practitioner implication:** "add a new discount" in an FS is a pricing-condition-type + access-sequence design question, not a database field — always ask what determines eligibility (customer group? material group? date range?) before designing.

## 3. Copy Control & Document Flow Integrity

**Item Category** + **Schedule Line Category** (derived from sales document type + item data, e.g. material item category group) control how a sales document behaves structurally (pricing-relevant? delivery-relevant? billing-relevant?). **Copying Control** (config: source doc type → target doc type, at header/item/schedule-line level) governs what carries over order→delivery→billing — including a **Pricing Type** setting (e.g. type "L" = redetermine tax/freight/internal price at copy time rather than blindly copying the source's frozen values) — an FS that implies "billing should use today's tax rate, not the order-date rate" is describing a pricing-type choice in copy control, not custom logic.

Copying control can also **restrict** (e.g. block creating a sales order with reference to an already-fully-invoiced contract) — relevant if an FS describes reference-document creation flows (quotation→order, contract→order).

## 4. Incompletion Log — the built-in "can't proceed" gate

Before a sales order/delivery/billing document can move forward (save, deliver, bill), SAP checks an **Incompletion Procedure**: a configured list of required fields (e.g. mandatory partner functions from §1, pricing conditions, delivery date). "List Incomplete Sales Documents" is a standard monitoring app for this. An FS's "the system should require field X before saving" is very likely describing incompletion procedure configuration, not a new validation to hand-build in a custom BAdI/RAP validation — check config first.

## 5. Credit Management touchpoint

Credit check evaluates a business partner's **total credit exposure** (open sales orders of credit-check-relevant document types, per **Credit Exposure Category**, e.g. category 100 = open sales orders) against a credit limit. A failed check sets a **credit block** on the order (visible via `TotalCreditCheckStatus`), which must be released before delivery. If an FS mentions "block risky customers automatically," this is Credit Management config (credit segment/scoring rules), not a custom status field to invent.

## 6. Material Master prerequisite (why BD9 can silently fail without it)

A material needs specific **views** maintained before it can even appear in a sales order flow: **Sales: General/Plant** view (sales org data, delivering plant) is what makes ATP's "Avail. check" field apply the *Sales* view's setting (vs. the **MRP** view's setting used by production-side checks — see [Skill: sap-process-production-discrete-planning]). A "material not found"/availability anomaly in testing is very often a missing Sales view on the material master, not a bug in the report/app being built — flag this as an environment-data prerequisite, not silently assume test data is complete.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
