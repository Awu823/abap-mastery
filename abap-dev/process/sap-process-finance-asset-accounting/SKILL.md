---
name: sap-process-finance-asset-accounting
version: 1.0
description: SAP Finance process knowledge for Asset Accounting — scope item J62 — fixed asset master data, acquisition, depreciation, on SAP S/4HANA Cloud Public Edition. Use when an FS describes fixed asset management, depreciation, asset acquisition/retirement, or explicitly "Asset Accounting"/"J62". Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP FI-AA consultant expert in Asset Accounting (scope item **J62**).

# Process Overview
Fixed Asset master data (chart of depreciation, asset class) → acquisition (posts to G/L, see [Skill: sap-process-finance-general-ledger]) → periodic depreciation run → retirement/disposal. Depreciation values are **ledger-dependent** (parallel accounting — different ledgers can carry different depreciation areas for the same asset), a common FS-underspecification point.

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| Fixed Asset (master) | `I_FIXEDASSET` / `I_MASTERFIXEDASSET` | FI-FIO-AA-ANA-2CL |
| Fixed Asset (time-dependent assignment) | `I_FIXEDASSETASSGMT` | FI-FIO-AA-ANA-2CL |
| Fixed Asset (ledger-dependent valuation) | `I_FIXEDASSETFORLEDGER` | FI-FIO-AA-ANA-2CL |
| Fixed Asset usage object | `I_FIXEDASSETUSAGEOBJECT` / `...PERIOD` / `...TOTAL` | FI-AA-2CL |

Integration: **API_FIXEDASSET** (OData V4, "Fixed Asset - Master Data"), **OData API: Fixed Asset – Post Asset Acquisition**.

# Common Configuration Touchpoints
- Chart of Depreciation / Depreciation Area assignment (ledger-dependent).
- Asset Class (determines G/L account determination for acquisition/depreciation postings).

# Related Processes
- [Skill: sap-process-finance-general-ledger] — every asset acquisition/depreciation/retirement posts a Journal Entry there.
- [Skill: sap-process-finance-financial-close] — this skill's fiscal-year closing is a **hard prerequisite** for G/L year-end closing — always model this dependency explicitly.
- Production/Manufacturing skills — production equipment as a fixed asset ties usage/depreciation to production cost accounting, if the FS's scope extends that far.

# Deep Dive
For functional-consulting depth (asset class as master-data template, parallel depreciation areas/accounting principles, asset acquisition posting options, depreciation run mechanics, asset retirement/transfer, legacy data transfer & mid-year go-live) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
