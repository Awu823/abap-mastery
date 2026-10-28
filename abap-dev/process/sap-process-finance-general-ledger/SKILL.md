---
name: sap-process-finance-general-ledger
version: 1.0
description: SAP Finance process knowledge for General Ledger Accounting — scope item J58 (Accounting and Financial Close), day-to-day posting emphasis — Journal Entry, G/L account line items, on SAP S/4HANA Cloud Public Edition. Use when an FS describes G/L postings, journal entries, account line items, or is the universal downstream target of a revenue/cost report. Paired with [Skill: sap-process-finance-financial-close] (same scope item, period-end emphasis). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP FI-GL consultant expert in General Ledger Accounting (scope item **J58**, day-to-day posting half).

# Process Overview
Every business transaction in every other LOB (O2C billing, Manufacturing settlement, Asset depreciation, Project System revenue recognition) ultimately posts a **Journal Entry** here — this skill is the universal downstream reference point for any report/build touching financial impact, not a process with its own separate document flow to trigger.

**Note:** J58 covers BOTH day-to-day posting (this skill) and period-end closing ([Skill: sap-process-finance-financial-close]) — same scope item, split by emphasis only, same pattern as the Manufacturing/Production skill pairs.

# Data Model Grounding
| Object | CDS View | App Component |
|---|---|---|
| G/L Account Line Item (Universal Journal) | `I_GLACCOUNTLINEITEM` | FI-GL-IS-2CL |
| G/L Account Line Item (raw) | `I_GLACCOUNTLINEITEMRAWDATA` | FI-GL-IS-2CL |

Business event: `D_JOURNALENTRYCREATED` (app component `AC-INT-2CL`).

Integration: **JournalEntryBulkChangeRequest_In** / **JournalEntryBulkClearingRequest_In** / **JournalEntryBulkLedgerCreationRequest_In** (SOAP, comm scenarios `SAP_COM_0002`/`SAP_COM_0241` — "Finance - Posting Integration").

**Correction note:** an earlier internal test draft used the name `I_JournalEntryItem`, which is NOT a verified released view — the correct verified view for reporting is `I_GLACCOUNTLINEITEM`. Always verify against this session's finding, not assumed naming conventions.

# Common Configuration Touchpoints
- Company Code G/L View (config object 106039) — controls split postings.
- Ledger group assignment.

# Related Processes
- [Skill: sap-process-finance-financial-close] — period-end emphasis of this exact scope item.
- [Skill: sap-process-finance-asset-accounting] — asset depreciation/acquisition postings land here.
- [Skill: sap-process-o2c-sell-from-stock] / [Skill: sap-process-o2c-customer-returns] — revenue/COGS/credit-memo postings land here; a "net revenue" report often needs BOTH the O2C analytical cubes AND this skill's G/L view depending on whether the FS wants SD-side or FI-side numbers (see O2C skills' Design Decisions note on Architecture A vs B).
- Manufacturing/Production skills — production order/PCC settlement lands here at period close.

# Deep Dive
For functional-consulting depth (document splitting's profit-center/segment derivation, parallel ledgers and accounting-principle assignment, automatic account determination, the Universal Journal/ACDOCA as single source of truth, journal entry posting workflow) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
