---
name: sap-process-finance-financial-close
version: 1.0
description: SAP Finance process knowledge for Accounting and Financial Close — scope item J58, period-end closing emphasis — fiscal year/period closing sequence, cross-LOB closing dependencies, on SAP S/4HANA Cloud Public Edition. Use when an FS describes month-end/year-end close, posting period control, or closing checks across modules. Paired with [Skill: sap-process-finance-general-ledger] (same scope item, day-to-day posting emphasis). Complements the FS-analysis skills (domain grounding).
---

# ROLE
SAP FI consultant expert in period-end/year-end financial close (scope item **J58**, closing half).

# Process Overview
Closing has a **cross-LOB dependency order** — the single most important thing an FS about "closing" often omits: **Asset Accounting's fiscal year must close BEFORE General Ledger's year-end closing can proceed** (a hard system-enforced prerequisite check, not just a recommended sequence). Any TS involving period-end closing must model this ordering explicitly, not assume all LOBs close independently/in parallel.

Posting Period control (open/close per company code + period) is the mechanism that actually blocks/allows postings during close — this is the enforcement point, not a business-process document.

# Data Model Grounding
No dedicated "closing" CDS view beyond [Skill: sap-process-finance-general-ledger]'s `I_GLACCOUNTLINEITEM` — this skill is a control/sequencing layer over posting period configuration, not a separate transactional data model.

# Common Configuration Touchpoints
- **Manage Posting Periods** app — open/close per company code + period, the actual enforcement mechanism.
- Year-end closing prerequisite check: Asset Accounting fiscal year closed BEFORE G/L year-end close.

# Related Processes
- [Skill: sap-process-finance-general-ledger] — day-to-day posting emphasis of this exact scope item.
- [Skill: sap-process-finance-asset-accounting] — its fiscal-year closing is a hard prerequisite for this skill's G/L year-end closing — model the dependency, don't treat as independent/parallel.
- Manufacturing/Production skills — production order/PCC period-end settlement must complete before this skill's period closes.
- Project System skills (once built) — project WIP/revenue-recognition settlement is also a closing-dependency candidate.

# Deep Dive
For functional-consulting depth (fiscal year variant/posting period variant mechanics, posting period control and exceptional-posting authorization, the period-end closing task sequence, cross-LOB closing dependencies, Advanced Financial Closing orchestration) — see `references/deep-dive.md`. Read it when the FS needs real business-logic depth, not just process identification.

# Sources
Full citations: `references/sources.md` — read only when auditing a specific claim, not needed for normal use.
