# Deep Dive — sap-process-production-discrete-planning (BJ5, planning)

Read this file when the FS requires real functional-consulting depth on discrete production planning (MRP logic, BOM explosion, scheduling) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Planning Strategy — the decision that shapes everything else

Before any MRP/BOM/routing detail matters, the FS must answer: **how does customer demand connect to production supply?** This is the **Planning Strategy** (a **Requirements Type** combination from demand management + sales order management), and it decides the whole architecture:
- **Strategy 10 (Make-to-Stock)** — produce against a forecast/planned independent requirement; sales orders consume stock, not production directly.
- **Strategy 20 (Make-to-Order)** — production is triggered only once a specific sales order exists for the finished product; costs/stock are valuated per sales order (see [Skill: sap-process-o2c-sell-from-stock] for the sales-order side).
- **Strategy 40 (Planning with Final Assembly)** / **52 (Planning Without Final Assembly)** — hybrid: components/semi-finished stock is planned ahead (against a forecast), but the FINAL assembly step only happens once a real sales order exists — a common "reduce lead time without full MTS risk" pattern. Strategy 52 is a make-to-stock strategy from a *costing* perspective even though the physical trigger looks MTO-like — a subtlety that affects which Finance skill's costing logic applies.
- **S5 / B6 / 60 (Spare-part/MTO variants)** — narrower MTO variants for spare-part or planning-material scenarios.

**Practitioner implication:** an FS that says "produce this only when a customer orders it" is NOT automatically strategy 20 — check whether components are pre-planned (40/52) vs. the whole order is triggered from zero (20/S5). Getting this wrong changes the entire MRP/costing design, not just a flag.

## 2. MRP Mechanics — lot sizing, safety stock, net requirements

**Net Requirements Calculation**: for each material, MRP nets (stock + planned receipts) against (requirements), taking into account **safety stock** (methods: static, or dynamic e.g. range-of-coverage-based) and the **lot-sizing procedure** (e.g. lot-for-lot, fixed lot size with splitting, "Replenish to Maximum Stock Level" = lot size key `HB`). The chosen lot-sizing procedure directly determines HOW MANY planned orders MRP creates and their quantities — an FS asking "why does the system create 3 small orders instead of 1 big one" is a lot-sizing-procedure question, not a bug.

**MRP Area** — planning can be scoped narrower than a whole plant (e.g. per storage location or per subcontractor) via MRP Areas, each with its own lot size/safety stock parameters — relevant if the FS implies decentralized/segmented planning (e.g. a specific storage location plans independently).

## 3. BOM Explosion — phantom assemblies and dependent requirements

BOM explosion is not a flat parts list — it recursively determines **dependent requirements** for every component, and **Phantom Assemblies** (special procurement key `50` in the material master) are exploded straight through to their own sub-components WITHOUT creating a separate planned order/stock for the phantom item itself — the phantom is a bookkeeping/grouping construct in the BOM, not a real inventory stage. An FS describing "an assembly that never appears in stock, just groups components" is describing a phantom assembly, not a design gap.

**Explosion Types** (tied to special procurement keys) control additional behavior: switching off planning for certain sub-branches, direct production/procurement triggers. **Component scrap %** (consumption inflation per component) vs. **operation scrap %** (loss during a specific routing step) are distinct BOM/routing fields with different cost/quantity effects — don't conflate them in a TS.

**Storage Location Determination in BOM Explosion** has its own configurable strategy sequence (e.g. "components first, then phantom assemblies, then assemblies") for resolving which storage location backflush/goods-issue uses — relevant if the FS's plant has multiple storage locations for the same material.

## 4. Scheduling — why dates come out the way they do

The system default is **backward scheduling** from the order/planned-order finish date (working back through routing operation times) to derive **Basic Dates** (basic start/finish). **In-house production time** can be defined in the material master's Work Scheduling view as either lot-size-**dependent** (scales with quantity) or lot-size-**independent** (fixed regardless of quantity) — an FS assuming "lead time is always proportional to quantity" may be wrong for a specific material's setup.

**Order Type Dependent Parameters** (config per production order type) control whether that order type schedules forward or backward by default (backward is standard; forward scheduling is an explicit override, commonly used for expedite/replenishment order types) — if the FS implies "always schedule as early as possible from today," that's forward scheduling, a configuration choice per order type, not a universal default.

**Backward consumption**: sales orders/dependent requirements/reservations can consume planned independent requirements dated BEFORE the requirement's own date within a configured consumption window — relevant for reconciling "why did this forecast disappear before its date."

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
