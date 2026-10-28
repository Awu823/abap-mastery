# Deep Dive — sap-process-supplychain-atp (2LN)

Read this file when the FS requires real functional-consulting depth on Basic Available-to-Promise (checking rule/scope-of-check mechanics, backorder re-prioritization, the Basic vs Advanced ATP boundary) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Checking Rule vs. Checking Group — Two Independent Axes of "Scope of Check"

The **scope of check** (which stocks, receipts, and issues an availability check counts) is never set once — it is the *combination* of two separate configuration axes that a TS/FS often conflates into one:

- **Checking Rule** — assigned per calling process, not per material: **A** (sales order creation/quotation — the "promising" check, considers *future* supply: purchase orders, production orders, planned orders, shipping notifications), **B** (delivery creation/goods issue — the "execution" check, restricted mostly to physical/immediately-available stock), and **WS** (Web Shop Simulation — a custom rule for checking availability from an external Web shop before the S/4HANA Cloud order even exists). Rush orders (which auto-create their delivery on save) are checked with rule B from the start, not A.
- **Checking Group** — assigned per material (Sales: General/Plant view) — determines what type of requirement record the system creates when the material appears in a sales order/delivery.

Rule and group **work together**: the actual "Configure Scope of Availability Check" table is keyed by rule+group combination, not by either alone.

**Practitioner implication:** the classic confusing symptom "the sales order shows fully confirmed, but delivery creation still blocks it" is very often *not a bug* — it's rule A (optimistic, future-supply-aware) confirming at order time, followed by rule B (stricter, physical-stock-only) failing at delivery time because the promised production/PO receipt hasn't landed yet. Before opening an incident, check which rule ran at which step.

## 2. Scope of Availability Check & Check Horizon — What Counts, and How Far Ahead It Promises

**Scope of Availability Check** (config: `Configure Scope of Availability Check`) is the literal list of MRP elements the check nets against: which stock types (unrestricted-use, safety stock, stock in transfer, etc.), which receipt elements (purchase orders, production/planned orders, shipping notifications), and which issue elements (sales requirements, deliveries, reservations) are included. This is what the **Display Product Availability** app's "Show Scope of Check" button actually renders — a live view of exactly which MRP elements fed the last confirmation, which is the fastest way to explain *why* a specific date/quantity was confirmed instead of guessing.

**Check Horizon** governs a different question: *how far into the future* ATP is even allowed to promise against real receipts. It is maintained per material/plant (in working days, using the plant's factory calendar) and offers three behaviors for requirements landing beyond it:
- **Full Confirmation** — requirements beyond the horizon are confirmed in full immediately, without reserving any specific stock/receipt quantity; once the requirement moves inside the horizon it starts reserving for real (a suitable receipt, e.g. from MRP, must materialize or it over-confirms).
- **Zero Confirmation** — requirements beyond the horizon are not confirmed at all and stay back-ordered until a re-check (e.g. a BOP run, §5) picks them up once inside the horizon.
- **Ignore Check Horizon** — the horizon is switched off; confirmation is purely based on actual available stock/supply regardless of how far out the requirement sits.

**Practitioner implication:** an FS asking "orders more than 6 months out should confirm immediately, without blocking near-term stock for other customers" is describing **Full Confirmation** check-horizon behavior, not a custom date-comparison rule to hand-build. Conversely "far-future orders should just wait for backorder processing to pick them up" is **Zero Confirmation**. Map the FS wording to one of these three options before proposing any custom logic.

## 3. Transfer of Requirements — the Gate Before ATP Even Runs

Before checking rule/group/scope-of-check matter at all, the **Schedule Line Category** (auto-derived from the item's **Item Category** + the product's **MRP Type**, config-controlled — see [Skill: sap-process-o2c-sell-from-stock] for how item category itself is determined) decides, per schedule line, whether:
- the line is purely informational (e.g. a sales inquiry schedule line — no requirement, no check, ever);
- **requirements should be transferred and an availability check carried out** (typical for a standard sales order line);
- stock should be managed / goods issue posted (delivery-relevant lines);
- goods receipt should be posted (return-order lines).

This is a binary gate that happens *upstream* of the ATP configuration this skill otherwise covers.

**Practitioner implication:** "why does ATP never trigger for this document type/item" is very often a schedule-line-category setting (requirements-transfer flag off), not a missing checking group or a bug in a custom RAP validation — check this gate first, it's a five-minute config lookup versus hours of debugging a "missing" availability check.

## 4. Confirmed Quantity/Date Splitting — How a Shortfall Actually Surfaces

ATP never just returns yes/no. A sales order schedule line always carries **both** a requested pair (`RequestedQuantity` / `RequestedDeliveryDateTime`) and a confirmed pair (`ConfdOrderQtyByMatlAvailCheck` / `ConfirmedDeliveryDateTime`). When the requested quantity cannot be confirmed in full for the requested date, ATP **splits the item into additional schedule lines** — e.g. line 1 confirms today's available quantity on the requested date, line 2 confirms the remainder on a later date — rather than rejecting the line outright.

The standard **Sales Order Items - Backorders** app (App ID F5307) gives the vocabulary a TS should reuse instead of inventing new terms: every order item lands in exactly one of **Confirmed** (full quantity, requested date, no restriction), **Delayed** (full quantity eventually confirmed, but later than requested), **Partially Confirmed** (only part of the quantity confirmed, delayed or not), or **Unconfirmed** (nothing confirmed at all).

**Practitioner implication:** an FS stating "the system should reject the order if it can't be fully available" is describing a deliberate *departure* from standard behavior — standard ATP accepts the order and schedule-line-splits/backorders it, it does not reject. That rejection has to be built explicitly (e.g. an incompletion/validation rule keyed off the confirmation status), it is not a side effect you get for free from turning on ATP.

## 5. Backorder Processing (BOP) & Confirmation Strategies — Re-Fighting Over Scarce Stock

**Backorder Processing** re-runs the availability check across a *scoped set* of already-created requirements when the supply/demand picture has changed since they were first confirmed — a cancelled order freeing stock, an important customer increasing quantity, a late production order, or simply a periodic health-check that yesterday's confirmations are still realistic. A **BOP run** executes against a **Variant**, which assigns **Segments** (saved filter + priority definitions, e.g. "high-priority customer's open sales order items") to one of seven **Confirmation Strategies**:

| Strategy | What happens to its requirements |
|---|---|
| Win | Fully confirmed on the requested date — or an exception is raised if that's not possible |
| Gain | Keep at least their current confirmation, improve if possible — exception if even that can't be kept |
| Improve | Try to keep/improve, but may silently lose confirmation (no exception) |
| Redistribute | Can end up better, equal, or worse |
| Fill | Only get what's left after Win/Gain/Improve/Redistribute are satisfied — never gain, may lose |
| Lose | Deliberately give up their confirmed quantity so it can be reused |
| Skip | Frozen out of this run entirely (e.g. fixed-date/quantity flag set) |

Requirements are matched to strategies in a defined **evaluation sequence** (Lose is decided first, Win/Gain/Improve/Redistribute/Fill follow) that is *separate* from the **check sequence** used to actually distribute the physical stock (Win gets first claim on quantity, then Gain, Improve, Redistribute, Fill, Lose last) — this two-sequence design is the actual mechanism behind "give this customer priority over that one." For fast-moving materials, BOP uses an **optimistic, non-exclusive locking** approach (temporary quantity assignment sized to the confirmation strategy) instead of serializing on one exclusive lock per material, trading a small risk of over-confirmation for the ability to check many orders of a high-running material in parallel.

**Practitioner implication:** "reallocate stock away from low-priority customers toward a VIP account" is a BOP **segment + confirmation-strategy design** exercise (VIP segment → Win, everyone else → Fill/Redistribute/Lose), not a bespoke ABAP reallocation report. Also flag a genuine documentation nuance to verify per system: SAP's own Help groups Product Availability Check and Backorder Processing together under the "Order Promising (2LN)" landing page, yet the Backorder Processing page itself states BOP "is a function of Advanced Available-to-Promise (aATP)" — confirm with the customer's Signavio scope-item activation (2LN alone vs. 2LN + 1JW) whether the full segment/variant/confirmation-strategy BOP tooling described here is actually licensed and active before designing against it, rather than assuming every Basic-ATP tenant has it.

## 6. Basic ATP (2LN) vs. Advanced ATP (aATP, scope item 1JW) — Where the Boundary Actually Sits

Both live under the same "Availability Checks" capability umbrella in SAP Help, which is exactly why FS authors blur the line. What is **exclusively aATP** (scope item 1JW), not part of Basic ATP's 2LN grounding this skill provides:
- **Product Allocation (PAL)** — rationing scarce material to regions/customers/channels over a time period.
- **Alternative-Based Confirmation (ABC)** — proposing a substitute product/plant/storage location when the original request can't be met, including the **Third-Party Order Processing (TPOP)** flow that ABC can trigger automatically.
- **Substitutions** + **Object and Value Determination (OVD)** — the substitution-framework machinery ABC relies on.
- **Supply Protection (SUP)** — protecting a group's quantity against being consumed by another group's demand.
- **Release for Delivery** — manual post-processing of backorders on top of automated BOP.
- **Availability Change Log (ACL)** and **Activity Attributes for Business Process Scheduling (BPS)** — change-tracking and fine-grained scheduling duration/working-time attributes.

Concretely, the `I_ATPCheckingGroup` CDS view carries an `AdvancedATPIsActive` field — meaning aATP is switched on **per checking group**, not system-wide: one material's checking group can run plain Basic ATP while another's runs aATP, in the same client, at the same time.

**Practitioner implication:** the moment an FS says "if the primary plant is short, check a nearby plant automatically" or "ration this material by customer tier," that is aATP (1JW) territory, structurally outside what 2LN's Basic ATP can do — treat it as a scope/activation question to raise with the customer (is 1JW licensed and active for the relevant checking groups?) before attempting to fake it with Z logic bolted onto Basic ATP.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
