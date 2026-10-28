# Deep Dive — sap-process-projectsystem-customer-project (J11)

Read this file when the FS requires real functional-consulting depth on Customer Project Management (billing element mechanics, contract-type-driven billing methods, revenue recognition, loss handling, settlement, resource staffing) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Billing Element & Project Account Assignment — the structural backbone

A WBS element only becomes revenue-capable once flagged as a **Billing Element** — a project structure node (project header or any WBS element) against which revenue can be planned and posted. Key structural rules an FS/TS must respect:
- **One billing-relevant sales order item per billing element by default.** A billing WBS element can only have one *pricing-and-billing-relevant* sales order item assigned unless the project was created with the **Multiple Sales Order Items Scenario** flag set to Yes — and that flag is fixed at project creation and cannot be changed afterward. If an FS describes "one WBS bills across several contracts/sales orders," this is an irreversible project-creation-time decision, not a later config fix; it also forces you to maintain profitability-segment attributes explicitly on cost/revenue postings (the automatic derivation no longer applies cleanly with N:1).
- **Billing elements cannot nest.** A billing element cannot exist inside another billing element's subtree, nor can a billing element contain another billing element beneath it — the tree membership is mutually exclusive. **Profit Center** and **Functional Area** are inherited identically across a billing element's entire subtree.
- **Free-of-charge (FOC) sales order items** are the exception to the one-item rule — they can be assigned to a billing *or* non-billing WBS element regardless of the Multiple Sales Order Items flag, and are considered at actual cost (not revenue) in the recognition process.
- **Revenue Recognition Key** is derived automatically from the assigned pricing/billing-relevant sales order item; if no such item exists yet, it can be maintained manually on the project (Project Control - Enterprise Projects app) or the billing WBS element (Project Planning app) — but once a sales order item is later assigned, its derived key must *match* the manually-maintained one, and the field can never be left blank again after first maintenance.

**Practitioner implication:** always ask, before a project is created, whether one billing WBS element will ever need to serve more than one billing sales order — this single flag cannot be retrofitted, so getting it wrong means recreating the project.

## 2. Contract Types Driving the Billing Method — Fixed Price, Periodic Service, T&E, Usage-Based

J11 customer projects derive their billing behavior from one of four **contract types** set at the billing element/work package level — this is the cloud equivalent of choosing "resource-related vs. milestone vs. periodic" billing:
- **Fixed Price** — billing follows a **billing plan** (often milestone-based) against a total contracted scope, independent of actual effort.
- **Periodic Service** — a recurring billing plan (e.g., a monthly retainer), typically time-based revenue recognition (1/12th per period, etc.).
- **Time & Expenses (T&E)** — the resource-related billing case: billing is generated off *actual* confirmed hours/expenses via an invoice simulation, not a pre-agreed plan.
- **Usage-Based** — shares the same recognition-key logic as T&E (SPNTM/SPTM families).

The **Calculate Cost and Revenue** engine plans cost and revenue per work package: planned *cost* is resolved from a cascade (delivery-organization default cost center → resource's own cost center, when no delivery org is specified the project's own cost center is used first) or from the resource's **Service Cost Level** if assigned; planned *revenue* (when the advanced/configurable revenue strategy is enabled via "Use Project Billing (New)") resolves in priority order: **project-specific price** (condition type `PCP0`) first, then **standard price** (`PSP0`, from the Manage Prices - Sales app). An FS asking for "a special negotiated rate for this customer's project" is a `PCP0` condition record, not a new price field.

**Milestone billing plan dates can be auto-generated from project milestones**: when a billing WBS element is account-assigned to an order-related-billing sales order item, the system proposes billing plan dates directly from the WBS element's milestones, and automatically removes the billing block on that plan line once the milestone's actual finish date is set. An FS describing "invoice automatically when milestone X finishes" is this standard integration, not custom logic.

**Practitioner implication:** before designing custom billing logic, map the FS's billing description to one of the four contract types first — most "unusual" billing asks are a standard contract type plus a **Billing Profile** configuration (activity type / material / service-vs-expense classification, including G/L-level exclusion of expense postings from billing) rather than net-new development. Cross-check with `[Skill: sap-process-o2c-sell-from-stock]` for how the underlying sales order/billing-plan mechanics (item category, copy control) behave once the WBS account assignment is in place.

## 3. Event-Based Revenue Recognition (EBRR) — POC method selection is per contract type, not universal

Each contract type is paired with a **Revenue Recognition Key** that determines exactly how/when Financial Accounting postings happen — this is not one universal "percentage of completion" formula:
- **Cost-based POC** (key family `SPFC`) — revenue recognized in proportion to actual cost incurred vs. planned cost (estimate at completion).
- **Quantity-based POC** (`SPFCQ`) — POC measured by *working hours*, not currency amounts — travel expense postings affect the `SPFC` POC calculation but are excluded from `SPFCQ`.
- **Revenue-based POC** (`SPFCR`) — the inverse: cost recognition follows the ratio of *billed* to *planned* revenue.
- **Completed-contract methods** (`SPFCCM`/`SPTCCM`) — both cost and revenue are fully deferred until completion; the only difference between the two keys is *when* "completion" triggers the clearing posting — at project end date (`SPFCCM`) vs. at the point the project status is manually set to Completed (`SPTCCM`), which can be a different fiscal period.
- **T&E-specific keys** — `SPTM` (cost as-incurred, revenue via invoice simulation) and `SPTMWP` (identical logic, plus enhanced WIP reporting: Product/Quantity dimensions on journal entries, distinct SLA line-item types for write-offs and for the T&E **revenue cap** — a negotiated invoice ceiling beyond which accrued revenue is capped even if actual hours exceed it).
- **Shared-risk T&E** (`SPTMSR`) — two work packages under one billing element with different sales rates (e.g., first 10h at full rate, overage at a reduced rate) blend into a single POC calculation across both.
- **No-revenue-recognition keys** (`NONREV`, and legacy equivalents `SPNFC`/`SPNPC`/`SPNTM`) — cost and revenue post as they occur, with zero deferral/accrual; SAP explicitly recommends `NONREV` as the comprehensive choice when no accrual is needed.

The trigger for real-time postings is the transactional event itself (time confirmation, billing document posting); the trigger for the *period-end revaluation* (clearing accrued vs. deferred balances, POC capped at 100%) is the **Run Revenue Recognition – Projects** closing app — cross-reference `[Skill: sap-process-finance-financial-close]` for how this fits into the broader period-end sequence, and `[Skill: sap-process-finance-general-ledger]` for the G/L accounts (Accrued Revenue, Deferred Revenue, Revenue Adjustment, Cost Adjustment) these postings hit.

**Practitioner implication:** "recognize revenue as we bill" — a very common simple-sounding FS ask — is *not* the platform default even for fixed price; the default `SPFC` key recognizes revenue as costs are incurred, potentially well ahead of billing. Getting revenue recognition timing right requires an explicit key choice, not an assumption from the billing behavior.

## 4. Loss Handling — onerous-contract accounting is opt-in, not automatic

When a fixed-price project's planned cost exceeds its planned revenue (an "onerous contract" under accounting standards), EBRR can create and consume an **imminent loss reserve**, either manually (Enter Manual Contract Accruals) or automatically. Automatic loss handling only fires for specific recognition keys — `SPFC` (cost-based POC, customer projects) or `EPMFC`/`EPMFR` (cost-/revenue-based POC, EPPM revenue-carrying projects) — via dedicated assignment rules (`COSTPOCL`, `EPMCCCL`) that must be explicitly configured at company-code + accounting-principle level; it does **not** apply to quantity-based, completed-contract, or T&E-family keys.

**Practitioner implication:** "warn/accrue automatically when a project is heading for a loss" in an FS maps to this feature, but only if the project's recognition key is one of the supported cost-/revenue-based POC keys — confirm the contract type and key first, or the automatic mechanism simply will not trigger.

## 5. Settlement vs. Revenue Recognition — two mechanisms for two different WBS roles

These are easy to conflate but serve different WBS elements within the *same* customer project:
- **Billing (revenue-carrying) WBS elements** post revenue directly through the EBRR flow described above — no settlement receiver is typically needed, because the sales-order/billing-document chain already carries the cost/revenue relationship.
- **Non-billing or statistical WBS elements** (e.g., an internal overhead work package inside an otherwise customer-billable project, or an investment-profile WBS element generating an Asset under Construction) need a **Settlement Rule** — combining an allocation structure and a settlement profile — to redistribute their costs to a receiver (cost center, asset, G/L account, another order), executed via the **Run Settlement - Actual** app. Note that a WBS element inside a billing element's subtree cannot itself carry a settlement rule — settlement and billing-element revenue flow are structurally exclusive within the same subtree.

Cross-reference `[Skill: sap-process-projectsystem-internal-project]` for the pure-internal (no customer revenue) case, where settlement is typically the *only* cost-closure mechanism — useful for contrasting with this skill's revenue-carrying flow when an FS mixes both inside one customer project.

**Practitioner implication:** don't assume "settlement" is just another word for "billing" — they close cost/revenue on structurally different WBS elements, and an FS that says "settle the project's revenue to the customer" is actually describing the billing/EBRR flow in §1–§3, not a settlement rule.

## 6. Resource Staffing — no hard availability check, unlike sales-order ATP

Unlike the sales order's hard, blocking **Availability Check (ATP)** (see `[Skill: sap-process-supplychain-atp]`), project **Resource Demands** of type **Direct Staffing** are explicitly *not* checked against the staffed resource's availability, and the system performs no hard booking — staffing here is advisory capacity planning, not a gate. **External Staffing** demands hand the actual assignment/availability logic to an external system (e.g., SAP Project and Resource Management via communication scenario `SAP_COM_0A11`) — see `[Skill: sap-process-projectsystem-resource-mgmt]` for the staffing mechanics themselves.

This directly affects cost/revenue calculation: planned, staffed, and actual effort can all diverge, and the "Calculate Cost and Revenue" engine has explicit fallback rules per divergence case — including the one scenario where it uses an *averaged* rate across resources (multiple resources staffed in the same period with staffed effort exceeding planned effort) rather than each resource's own exact rate.

**Practitioner implication:** an FS assuming "the system blocks assigning more people than planned or available" is describing a control that Direct Staffing does not enforce by default — flag it explicitly as a custom validation requirement if the client truly needs it, rather than assuming existing behavior already covers it.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
