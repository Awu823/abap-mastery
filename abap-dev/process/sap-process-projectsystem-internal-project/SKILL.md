---
name: sap-process-projectsystem-internal-project
version: 1.0
description: SAP Project System process knowledge for Internal Project Management (scope item 1A8) — Enterprise Project/WBS structure for internal (non-customer-billable) projects, on SAP S/4HANA Cloud Public Edition. Use when an FS describes an internal project, cost-collection-only WBS, or explicitly "Internal Project Management"/"1A8". Paired with [Skill: sap-process-projectsystem-customer-project] (same structure, customer-billable variant). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP PPM/PS consultant expert in Internal Project Management (scope item **1A8**).

# Process Overview
Same **Enterprise Project / WBS Element** structure as [Skill: sap-process-projectsystem-customer-project] (J11), but no customer billing leg — costs collect on the WBS for internal cost tracking/settlement only (e.g. settle to a cost center, or capitalize as an asset under construction). If an FS's project has ANY customer invoice/billing requirement, it is J11 territory, not 1A8 — confirm which before designing.

**Correction note:** SAP S/4HANA Cloud Public Edition does **not** support classic Internal Orders — WBS-based projects (this scope item) are the mandatory replacement, not one option among several. Do not propose an Internal Order as a settlement receiver in a TS; see `references/deep-dive.md` §1.

# Data Model Grounding
Shares the exact CDS views with [Skill: sap-process-projectsystem-customer-project]: `I_ENTERPRISEPROJECT`, `I_ENTERPRISEPROJECTELEMENT`/`_2`, `I_ENTERPRISEPROJECTROLE` (PPM-SCL-STR) — no separate internal-project-only view exists; the distinction is process/settlement configuration, not a different data model.

# Common Configuration Touchpoints
- Project profile configured for internal settlement (cost center / internal order / asset-under-construction receiver), not customer billing.

# Related Processes
- [Skill: sap-process-projectsystem-customer-project] — same structure, billable variant; check the FS carefully for which one actually applies.
- [Skill: sap-process-finance-asset-accounting] — if the internal project results in a capitalized asset (Asset Under Construction), settlement lands there.
- [Skill: sap-process-finance-general-ledger] — internal cost settlement posts there regardless of receiver type.

# Deep Dive
For functional-consulting depth (project profile choice — Overhead/Investment/Statistical/Revenue, WBS processing-status gating, budget availability control by activity group, settlement rule generation, overhead cost allocation via costing sheet, Asset Under Construction settlement) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
