# Deep Dive — sap-process-projectsystem-resource-mgmt (1KC)

Read this file when the FS requires real functional-consulting depth on Resource Management (demand/assignment lifecycle, staffing capability tiers, external SAP Project and Resource Management integration, cost/revenue feed) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Two Parallel Object Models for "Staffing a Resource" — and Why 1KC Itself Is Retired

Before designing anything, resolve which of **two distinct staffing data models** the FS actually means — they use different apps, different objects, and different APIs:

- **Enterprise Projects (classic WBS)**: a WBS element raises a **Resource Demand** (entity `A_ProjDmndResourceDemand`, exposed via CDS `I_PROJECTDEMANDRESOURCEREQUEST` / `I_PROJDMNDRESOURCEREQUESTTP` — this skill's data model grounding), staffed via **Resource Assignment** (`A_ProjDmndResourceAssignment`) in the **Manage Project Demand** app.
- **Customer/Internal Projects ("Professional Services" work packages)**: a work package raises **Team Roles**, staffed via **Manage Team Resources** — a completely separate app, config switch, and business-catalog set (§4 below).

**Critical practitioner fact**: the literal scope item **1KC ("Advanced Resource Management - Project-Based Services")** — along with its sibling **2MV ("Basic Resource Management - Project-Based Services")** — has been **deprecated since SAP S/4HANA Cloud release 2208**; the corresponding apps (F0719, F1656) were removed. On any current release, there is no separate scope item left to "activate" for this — the successor capability is built directly into the Customer/Internal Project apps as the **"advanced resource management for projects"** configuration switch (§4), or into Enterprise Projects as the Resource Demand/Resource Assignment objects (§2) that are always available.

**Practitioner implication:** if an FS or an older TS says "activate scope item 1KC," treat that as stale terminology, not a valid instruction — there is nothing left to switch on by that name. Ask which project type (Enterprise vs. Customer/Internal) the requirement actually targets, and route to §2 or §4 accordingly. This skill's CDS views (`I_PROJECTDEMANDRESOURCEREQUEST`/`I_PROJDMNDRESOURCEREQUESTTP`) belong to the Enterprise Project / Resource Demand path only.

## 2. Resource Demand → Resource Assignment Lifecycle (Enterprise Projects)

A **Resource Demand** always carries: a **cost center** to be met, a **required activity type** (only activity types with an **hour-based unit of measure** are supported — a demand cannot be created against a piece-rate or other non-hour activity type), a **planned effort**, and **start/end dates** (defaulted from the assigned WBS element, but overridable).

**Status machine** (each stage gates which fields remain editable): `Created` (only demand name/ID/WBS mandatory; deletable only in this status) → `Request on Save` or `Request on WBS Element Release` (auto-transition triggers; all attributes now mandatory) → `Requested` (only planned effort, dates, and resource assignments still editable) → `Closed` (no further edits; auto-set when the WBS element is set to Completed, but reversible via "Revert to Requested"). Closing a demand does **not** disable the linked timesheet task — staffed resources can still post time within their assigned hours and the demand/WBS date window even after closure.

**Cost-center match rule** — a hard validation, not just a planning convention: for demand type **Direct Staffing**, the resource being assigned via `Update Resource Assignment` must have its **primary employment on the same cost center as the demand**; the API rejects a mismatch. This is a structural difference from **External Staffing**, where "the cost center of the assigned resources can differ from that of the demand" — because staffing decisions there are delegated entirely to the external system.

**Time recording integration**: once a resource is assigned to a demand, SAP S/4HANA Cloud Time and Attendance Management automatically provisions a corresponding task in **Manage My Timesheet**, pre-wired to the demand's WBS element/cost center/activity type. Resources *not* assigned to the demand must manually create their own timesheet task to post against it — an FS assuming "only staffed people can log time here" is wrong; unstaffed logging is just less convenient, not blocked.

**Demand monitoring**: the Manage Project Demand list view shows a **Planned / Staffed / Actual** micro-chart per demand — Planned = the demand's Planned Effort field; Staffed = sum of `ProjDmndRsceAssgmtQuantity` across assignments; Actual = effort posted to the demand's WBS element/cost center/activity type combination via time recording **or** direct activity allocation (not necessarily tied to a named assigned resource).

For the business rule that Direct Staffing performs **no hard availability check and no hard booking** (advisory planning, not a gate) and how that divergence between planned/staffed/actual effort ripples into cost/revenue calculation, see `[Skill: sap-process-projectsystem-customer-project]` §6 — not repeated here.

## 3. Direct Staffing vs. External Staffing — a One-Way Configuration Switch

**Direct Staffing** lets a project team member assign one or more resources directly while maintaining the demand in Manage Project Demand — no separate staffing process, no hard booking. If detailed resource-level planning isn't needed, a demand can stay at high-level (WBS + cost center + activity type only, no named resource).

**External Staffing** hands the actual assignment/availability decision to an external resource-management solution — either the resource management capability in **SAP Project and Resource Management** (comm scenario `SAP_COM_0A11`, §5) or a third-party system via the released OData API/BO interface **Project Demand** (`I_PROJECTDEMANDTP_2`). Once active, resource assignments can **only** be created/changed/deleted from the external side; S/4HANA Cloud Public Edition just displays what comes back.

**The switch itself — "Activate External Staffing for Enterprise Projects" — is irreversible.** Activating it automatically **migrates all existing Direct Staffing demands to External Staffing** (assignments are preserved but become read-only in S/4). There is no config path back.

The Create/Update/Delete Resource Assignment OData operations are explicitly scoped: relevant only for demand types **Direct Staffing** and **External Staffing** (not **Team Resource** — that uses separate Resource Assignment Distribution objects instead), and blocked entirely once the parent demand's status is `Closed`.

**Practitioner implication:** never propose "let's try External Staffing and switch back if it doesn't work" as a low-risk pilot — confirm with the client this is a one-way door before recommending activation, and confirm which external system (SAP PRM vs. a bespoke third-party consumer of `I_PROJECTDEMANDTP_2`) actually owns staffing afterward.

## 4. Professional-Services Staffing — the Customer/Internal Project Path (Work Packages, Team Roles)

Customer and Internal Projects staff **Team Roles** on a **work package**, not WBS-level Resource Demands, through the **Manage Team Resources** app. SAP S/4HANA Cloud offers **three mutually-exclusive staffing capability tiers**, set at system-configuration level:

1. **Decentralized staffing by a project manager** (default) — the PM plans and staffs directly, no separate resource-manager role.
2. **Centralized staffing** ("advanced resource management for projects") — PM and a resource manager collaborate: the PM can request resources/roles and let the resource manager staff them, or the PM can directly staff and manage staffed effort — but only if also assigned business catalog **Resource Management - Staff Customer Projects** (`SAP_CA_BC_RSH_CUSTPROJ_PSP_PC`) or **Staff Internal Projects** (`SAP_CA_BC_RSH_INTPROJ_PSP_PC`). This tier adds advanced search criteria and a unified resource-availability view.
3. **External staffing via SAP Project and Resource Management** — enabled through the **Commercial Project - Create, Update** API and the **Maintain Settings for Planning** configuration activity (§5). **Mutually exclusive with tier 2**: activating advanced resource management for projects blocks choosing the external system, and vice versa.

**Resource search** (in Manage Team Resources) filters on: **Delivery Organization** (restricted by intercompany rules if configured), **Cost Center**, **Include External Workers**, **Company Code** (defaults to the project's own), and **Service Cost Level**. Results surface: name, role, photo, **skills** (up to five entered per role, used for matching), employment type, previous roles held, and **availability** — computed from the person's weekly working hours (or **daily** working hours if advanced resource management is active) across the work package duration, per employment/cost center, flagging if an employment ends before the work package does.

**Team Role vs. Additional Resource — a resource-type mapping distinction**: Team Roles map to resource type **`0ACT`**, Additional Resources to **`0ADL`** — both require activity types set up with **Cost Center Category C (Professional Service)** and an **hour** unit of measure, assigned via the configuration activity **Map Resources to Resource Types**. Getting this mapping wrong at go-live is a common cause of a resource silently not appearing in the staffing value help.

**Billing Control Category** governs whether a planned resource/expense is billable: billable by default; marking an item non-billable means its revenue is ignored (cost-only) and any actual posting against it is **written off at billing time** by default — conversely, postings on an item that was never planned are treated as billable by default. The field is changeable only up to a point: for team resources, until staffing is **confirmed**; for additional resources/expenses, until the project reaches **In Execution**; and never once **actual time has been posted** against the item.

**Caution on rescheduling**: changing a work package's dates forces a choice between "Retain Total Efforts and Quantities" (redistribute the *planned* total evenly across new periods) and "Retain Efforts and Quantities for Common Months" (keep only the overlapping months, redistribute the rest) — but **already-staffed effort is not redistributed the same way**; SAP explicitly documents this as requiring manual staffing review after any date change when advanced resource management is active, since staffed hours can end up sitting in a period the work package no longer covers.

## 5. External Integration — SAP Project and Resource Management (BTP) and Scope Item 6JO

**SAP Project and Resource Management** is a **separate, separately-licensed BTP application** — not a module inside S/4HANA Cloud Public Edition. Integration is scoped under **Resource Management for Projects (6JO)** and uses two distinct communication scenarios with different jobs:

- **`SAP_COM_0A11`** (API integration) — the process-integration channel: replicates project header/work package/resource-demand data outbound, and syncs hard-booked assignments back inbound.
- **`SAP_COM_0840`** (UI integration) — exposes remote-app tiles (Manage Resource Requests, Staff Resource Requests, Manage Resource Utilization, My Resources, My Assignments, My Project Experience) in the S/4HANA Cloud Fiori launchpad, gated by business role templates (Project Manager - Professional Services, Resource Manager - Projects, Project Team Member) and matching business catalogs.

**Master-data prerequisite**: before any project replication can work, **cost centers and service organizations** (from S/4HANA Cloud) and **workforce person data** (from the HR system) must already be replicated into SAP Project and Resource Management — this is an environment/master-data dependency to flag before promising a working integration in a test system.

**Process flow**: PM plans team resources in S/4 (§4) → project/work-package/resource-demand data replicates out → resource requests appear for editing/publishing in SAP PRM → a resource manager staffs them there → once a **hard-booked assignment** exists, it syncs back into S/4HANA Cloud Public Edition immediately, **provided External Staffing is already active** in S/4 (§3).

**Practitioner implication:** don't conflate this BTP-app integration (6JO, work-package/Customer-Internal-Project data model, tiers 2/3 of §4) with the Enterprise-Project **External Staffing** resource-demand type of §2/§3 — an FS that says "integrate with an external resource management tool" needs a follow-up question on which project type (Enterprise vs. Customer/Internal) is in scope, because the comm scenario, the object replicated, and the configuration activity to flip are all different.

## 6. What Resource Management Feeds into Calculate Cost and Revenue

This skill does not re-derive the **Calculate Cost and Revenue** engine itself — see `[Skill: sap-process-projectsystem-customer-project]` §2 (contract types, `PCP0`/`PSP0` condition types) and §6 (the multi-resource average-rate fallback case) for that. What matters here is the **staffing-side data** the engine consumes and two divergence cases the sibling skill doesn't cover:

- **Cost derivation cascade** when a role/resource is planned: **Service Cost Level** assigned to the resource (if any) is tried first; if absent, the resource's **own cost center** (if available); if that's also absent, the **delivery organization's default cost center**. A planned cost that looks wrong after staffing is very often a master-data gap in this chain (no service cost level, no delivery-org default), not a calculation bug.
- **Single-resource divergence cases** (distinct from the sibling's multi-resource-average case): if a single staffed resource's effort is **less than** planned, standard pricing routines calculate cost/revenue for the *not-yet-staffed* remainder using the demand's own defaults; if a single staffed resource's effort is **greater than** planned, the *surplus* hours are still costed/priced using that **one resource's own rate and delivery organization** — averaging across resources is reserved strictly for the case where multiple distinct resources are staffed within the same period and their combined staffed effort exceeds the plan.

**Practitioner implication:** when a client disputes a planned cost/revenue number after staffing changes, walk the cascade and the specific divergence case (under-staffed / single-resource-over-staffed / multi-resource-over-staffed) before assuming custom logic is needed — three different, entirely standard rules could be producing the number.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
