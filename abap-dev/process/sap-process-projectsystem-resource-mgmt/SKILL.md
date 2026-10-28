---
name: sap-process-projectsystem-resource-mgmt
version: 1.0
description: SAP Project System process knowledge for Advanced Resource Management (scope item 1KC) — resource demand/request, staffing onto project WBS, on SAP S/4HANA Cloud Public Edition. Use when an FS describes staffing a project, resource demand/request, or explicitly "Resource Management"/"1KC". Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP PPM consultant expert in Advanced Resource Management (scope item **1KC**).

# Process Overview
A project WBS element ([Skill: sap-process-projectsystem-customer-project] / [Skill: sap-process-projectsystem-internal-project]) raises a **Resource Request** (demand: role/skill/quantity/duration) → staffing assigns a specific resource (person) against it. Can integrate with an external staffing system (see Related Processes).

**Correction note (found via deep-dive research):** the scope item **1KC** ("Advanced Resource Management - Project-Based Services") and its sibling **2MV** ("Basic Resource Management - Project-Based Services") have been **deprecated since SAP S/4HANA Cloud release 2208** — there is nothing left to "activate" under this scope-item name on a current release. This skill's underlying capability (Resource Demand/Resource Assignment on Enterprise Projects — the CDS views below) remains valid and current; only the scope-item framing is stale. For Customer/Internal Projects, the equivalent staffing capability is the "advanced resource management for projects" configuration switch inside those project apps, not a separate scope item — see `references/deep-dive.md` §1/§4 for the full picture.

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Project Demand Resource Request | `I_PROJECTDEMANDRESOURCEREQUEST` / `I_PROJDMNDRESOURCEREQUESTTP` | PPM-SCL-DMN |

# Common Configuration Touchpoints
- Resource request type / demand profile.

# Related Processes
- [Skill: sap-process-projectsystem-customer-project] / [Skill: sap-process-projectsystem-internal-project] — resource requests are raised against that WBS structure.
- Integration of an external system for resource staffing is a documented extension point if the FS requires a third-party staffing tool — do not assume it's in scope unless the FS states it.

# Deep Dive
For functional-consulting depth (Enterprise Project Resource Demand/Assignment lifecycle, Direct vs. External Staffing, Customer/Internal Project Team-Role staffing tiers, SAP Project and Resource Management integration, cost/revenue feed, and why scope item 1KC itself is deprecated since release 2208) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
