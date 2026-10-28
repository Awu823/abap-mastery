# Deep Dive — sap-process-finance-financial-close (J58, period-end closing)

Read this file when the FS requires real functional-consulting depth on period-end/year-end closing mechanics (fiscal year/posting period control, the closing task sequence, cross-LOB dependencies, closing orchestration) — not needed for a quick skill-discovery pass; `SKILL.md` covers that.

## 1. Fiscal Year Variant & Posting Period Variant — Structural Mechanics of "When Is a Period"

Two distinct configuration objects, frequently conflated in an FS, actually answer two different questions. The **Fiscal Year Variant (FYV)** defines *how a fiscal year is structured*: how many regular posting periods (up to 12) and special/adjustment periods (up to 4, max 16 total including regulars) exist, and each period's start/end date — which can diverge from the calendar year entirely (a non-calendar FYV, e.g. April–March). An **Alternative Fiscal Year Variant** lets one ledger in a company code use a different FYV than another ledger (e.g. the group ledger stays on a calendar year while a local ledger follows a local statutory year) — the mapping is set per ledger via `Assign Fiscal Year Variants to Ledgers and Company Codes`, and each ledger's fiscal year periods are therefore not automatically congruent with another ledger's.

The **Posting Period Variant (PPV)**, in contrast, is what actually controls *which periods are open or closed for posting right now* — configured via `Define Variants for Open Posting Periods` and applied through the `Manage Posting Periods` app. A single PPV is commonly shared across multiple company codes specifically to simplify closing operations (one open/close action instead of one per company code). Changing the default FYV in a live productive system is explicitly flagged by SAP as a rare, carefully governed change, not a routine config toggle — treat any FS request to "change how our fiscal year works" as a major, sequenced project, not a quick SSCUI edit.

**Practitioner implication:** when an FS says "close period X," resolve the company code → PPV mapping and confirm which ledger's fiscal year is actually being addressed before writing the TS — with alternative fiscal year variants in play, "March" can mean different absolute date ranges in different ledgers of the same company code.

## 2. Posting Period Control — Opening/Closing Periods and Exceptional-Posting Authorization

The `Manage Posting Periods` app (F2293) opens/closes periods per PPV **and account type and account range** — meaning a period can be closed for vendor postings (account type `K`) while still open for G/L postings (account type `S`), or closed for most G/L accounts but left open for a narrow adjustment-account range. This granularity is *the* mechanism behind "block regular postings but still allow exception processing during close" — not a status flag to build.

Who is allowed to post into an otherwise-closed period is controlled separately, via an **Authorization Group** created in the `Manage Posting Period Variants` app and checked against the posting user's authorization — this is the actual answer to "who can post a late correction after the books are closed," not a custom authorization object. Note also that **CO/cost-accounting periods are opened and closed independently** of FI posting periods, via the separate `Manage Posting Periods – Cost Accounting` app — a frequent source of "why can I post to FI but the CO document fails" confusion during close, since the two locks don't move together automatically.

**Practitioner implication:** any FS describing a "close exception" workflow (e.g. "Finance can still post corrections for 3 days after close") should map to an authorization-group-gated adjustment period, not a custom override switch — and always check both the FI and the CO (cost accounting) posting-period status when diagnosing a "can't post" issue during close.

## 3. Period-End Closing Task Sequence — GR/IR Clearing, Accruals/Deferrals, Foreign Currency Valuation

A representative closing sequence, each step with its own standard app/job template, runs *before* a period is locked down:

- **GR/IR clearing account maintenance** — the `Clear GR/IR Clearing Account` app (ID MR11) clears quantity/value differences between goods receipt and invoice receipt for PO items where no further movement is expected, so the GR/IR suspense account doesn't carry stale balances forward; a machine-learning-assisted reconciliation service exists to help identify which open items are safe to clear at scale.
- **Accruals and deferrals** — the **Accrual Engine** posts periodic accrual/deferral amounts for expenses and revenues whose exact figure isn't known until period-end (manual accrual objects, or PO-based deferrals calculated automatically from goods/invoice receipt timing), with automatic reversal logic built in. An FS requirement like "the system should automatically accrue expense X at month-end" is describing Accrual Engine configuration (accrual item type, accrual object), not a custom periodic batch job.
- **Foreign Currency Valuation** — revalues open items and foreign-currency-denominated account balances at the period-end exchange rate. SAP's current guidance is to use **Advanced Valuation in Financial Accounting** rather than the classic FX valuation report/job for new implementations; note foreign currency valuation specifically requires the target posting period to already be open for the correction/valuation posting date, so sequencing (valuation before final period lock, not after) matters.

Each of these is independently schedulable (Schedule Financial Closing Jobs / job templates) and independently sequenced — a TS that treats "period-end closing" as one monolithic job undersells how many distinct, separately-configured standard jobs actually need to be chained.

**Practitioner implication:** decompose any "run period-end closing" FS requirement into its constituent standard jobs (GR/IR clearing, accrual/deferral run, FX valuation, plus whichever LOB-specific settlement from §4 applies) before estimating effort or proposing custom orchestration — most of what looks like "closing logic to build" is actually standard job sequencing to configure.

## 4. Cross-LOB Closing Dependency — Production Settlement and Asset Depreciation Feed the Close

Closing is not independent per LOB — it has a real, system-relevant dependency order that an FS about "month-end close" frequently omits entirely:

- **Production/process order settlement**: **Work in Process (WIP) Calculation** and **Variance Calculation**, followed by **Actual Settlement**, are themselves period-end closing steps for production and process orders (and Product Cost Collectors in repetitive manufacturing) — see [Skill: sap-process-manufacturing-discrete-execution] / [Skill: sap-process-manufacturing-process-execution] / [Skill: sap-process-manufacturing-repetitive-execution]. Their settlement postings land in the same Universal Journal and period this skill controls, so they must complete before that G/L period can be considered truly closed. With **event-based production cost posting (3F0)** — SAP's recommended approach — most of these postings happen in real time as they're incurred rather than as a period-end batch, which reduces but does not eliminate this dependency; orders still run on the classic **period-based (BEI)** approach require the full WIP/variance/settlement sequence at period-end.
- **Asset Accounting fiscal year close**: as already flagged in `SKILL.md`, G/L year-end closing has a hard, system-enforced prerequisite check — **Asset Accounting's fiscal year must already be closed** before G/L year-end closing can proceed (see [Skill: sap-process-finance-asset-accounting]). The **depreciation posting run** itself can post into either of two open fiscal years, but must fully complete, per ledger, before that ledger's Asset Accounting fiscal-year-close job runs — and if a ledger uses an alternative fiscal year variant, this entire chain (depreciation run → AA fiscal-year close → G/L year-end close) must be tracked and executed per ledger, not once for the company code.

**Practitioner implication:** any closing-related TS must model this dependency chain explicitly — production/process order settlement → Asset Accounting fiscal-year close → this skill's G/L year-end close — rather than assuming all LOBs close independently or in parallel; missing this ordering is the single most common way a "close the books" FS turns out to be materially under-scoped.

## 5. Advanced Financial Closing (AFC) — Orchestrating the Close as Task Lists

SAP S/4HANA Cloud's original native closing-task apps (`Define Closing Tasks`, `Process Closing Tasks`, `Approve Closing Tasks`, plus their monitoring/change-log counterparts) are deprecated in favor of **SAP S/4HANA Cloud for advanced financial closing (AFC)** — a separate cloud service that models the entire close as **Task Lists**: templates of ordered, dependency-aware tasks (manual, automatic/job-triggering, or approval-gated), each with an owner and a due date, replacing the older transaction-based "Financial Closing cockpit" approach. Migration apps exist specifically to move existing task-list templates and configuration data from the deprecated native apps into AFC, and AFC now also supports cross-system/task-orchestration scenarios (e.g. coordinating a close across a source ERP and a Central Finance system) and third-party system integration.

An FS describing "the close should follow a defined sequence with owners, due dates, and an approval chain, visible on a status dashboard" is describing AFC task list / task group configuration — not a custom workflow app to design and build.

**Practitioner implication:** before proposing any custom closing-task-tracking tool or dashboard, confirm whether AFC is already in scope for the client's landscape — building a bespoke closing tracker duplicates a purpose-built SAP service and creates an unnecessary maintenance burden.

## Sources
Full citations for this deep-dive: `references/sources-deep-dive.md`.
