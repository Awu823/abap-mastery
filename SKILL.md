---
name: abap-mastery
description: |
  Unified entry point for the merged SAP ABAP agent skills library. This skill aggregates and routes to the
  consolidated ABAP skill collection under abap-mastery/ (abap-dev, code-review, standalone) and extras/abap-only,
  which were merged from 12 GitHub ABAP skill repositories. Use this as the top-level router: when a request
  matches an ABAP topic (RAP, CDS, OData, ABAP Cloud, code review, clean ABAP, unit testing, ABAP SQL/AMDP,
  authorization/IAM, BAdI/enhancements, BTP ABAP Environment, business events, released classes, process
  knowledge, etc.), load the corresponding sub-skill by its directory. Triggers include "ABAP skill", "use abap
  skill", "merged abap skills", "list abap skills", or any request that should delegate to one of the
  sub-skills listed below.
---

# ABAP Skills Library (merged entry)

> Unified entry point for the merged SAP ABAP agent skills collection.
> **Name:** abap-mastery · **Location:** `abap-mastery/` + `extras/abap-only/` · **Total:** 107 SKILL.md + 15 slash commands
> **Source:** 12 GitHub repositories (see `sources/`) · **Index:** `SKILL_INDEX.md` · **Fixes:** `FIX_LOG.md`

## How to use

1. **Route by domain.** Match the request topic to a domain below, then load the specific sub-skill.
2. **Sub-skills are self-contained.** Each sub-skill directory holds its own `SKILL.md` (plus `references/`,
   `scripts/`, `examples/`). Load it directly rather than re-reading this file.
3. **Fall back to core.** `abap-dev/core/` holds the 17 foundational skills; most requests resolve there.
4. **Claude-specific commands.** `abap-dev/commands/` holds the 15 `/sap-*` slash commands referenced by
   abap-dev skills; in OpenCode/Cursor treat them as prompt templates.

## Domain index

### abap-dev/core/ — Foundational (17)
`abap` · `abap-cloud` · `abap-cloud-migration` · `abap-sql-amdp` · `abap-unit-testing` · `abapgit` ·
`atc-cloudification` · `authorization-iam` · `badi-enhancement` · `btp-abap-environment` ·
`btp-diagram-generator` · `cds-view-entities` · `odata` · `rap` · `rap-business-events` ·
`released-abap-classes` · `sap-fiori-url-generator`

### abap-dev/advanced/ — Advanced (13)
`abap-generative-ai` · `cds-analytical-views` · `cds-data-model-analysis` · `clean-abap` · `lean-abap` ·
`modern-abap-syntax` · `naming-convention` · `oo-design-patterns` · `rap-query-provider` ·
`sap-fiori-apps-reference` · `xdp-form-layout` · `z-api-fwk` · `z-excel-fwk`

### abap-dev/process/ — Business process knowledge (18)
`sap-process-finance-asset-accounting` · `sap-process-finance-financial-close` ·
`sap-process-finance-general-ledger` · `sap-process-manufacturing-discrete-execution` ·
`sap-process-manufacturing-process-execution` · `sap-process-manufacturing-repetitive-execution` ·
`sap-process-o2c-customer-returns` · `sap-process-o2c-down-payment-billing` · `sap-process-o2c-sell-from-stock` ·
`sap-process-production-discrete-planning` · `sap-process-production-process-planning` ·
`sap-process-production-repetitive-planning` · `sap-process-projectsystem-customer-project` ·
`sap-process-projectsystem-internal-project` · `sap-process-projectsystem-resource-mgmt` ·
`sap-process-supplychain-atp` · `sap-process-supplychain-inventory-mgmt` ·
`sap-process-supplychain-warehouse-mgmt`

### abap-dev/fs-analysis/ — Functional-spec analysis (6)
`find-released-cds-view` · `fs-data-model-extractor` · `fs-fiori-ui-elements-mapper` ·
`fs-integration-api-analyzer` · `fs-logic-behavior-translator` · `fs-vision-extractor`

### abap-dev/productivity/ — Workflow helpers (6)
`activation-guard` · `caveman` · `document-markdown-converter` · `grill-me` · `handoff` · `scratchpad`

### code-review/ — Code review & delivery gates (5)
`abap-code-review` · `abap-guardian` (alternative implementation) · `sap-adt-cli` · `sap-integration-wiki` ·
`sap-transport-gate`

### standalone/ — Self-contained repositories (4 repos, 28 skills)
- `abap-code-audit-zh/` (1) — Chinese ABAP code audit tool (Python, needs 3.8+/weasyprint/reportlab/rarfile)
- `claude-abap-skills/` (5) — `atc-remediation`, `clean-core-check`, `rap-bo-design`, `refactor`, `review` (needs SAP ABAP MCP)
- `sapcli-claude-plugin/` (2) — `abap-snippet`, `abap-system-info` (needs sapcli)
- `superclaude-for-sap/` (20) — on-premise S/4HANA workflow skills (needs 150+ MCP tools)

### extras/abap-only/ — ABAP subset from SAP-wide libraries (14)
- `efeumutaslan-sap-abap/` (11) — `sap-abap-advanced`, `sap-rap-comprehensive`, `sap-odata`,
  `sap-s4hana-extensibility`, `sap-security-authorization`, `sap-migration`, `sap-event-mesh`,
  `sap-gui-scripting`, `sap-fiori-testing`, `sap-testing-quality`, `sap-ui5-fiori`
- `secondsky-sap-abap/` (3) — `sap-abap`, `sap-abap-cds`, `sap-fiori-tools`

## Selection guidance

| Request focus | Load from |
|---|---|
| RAP BO / EML / draft / validations | `abap-dev/core/rap` |
| CDS view entity / annotations | `abap-dev/core/cds-view-entities` |
| CDS analytics / data-model analysis | `abap-dev/advanced/cds-analytical-views` |
| ABAP Cloud / clean core levels | `abap-dev/core/abap-cloud` |
| Code quality / clean ABAP | `abap-dev/advanced/clean-abap` or `code-review/abap-code-review` |
| Unit testing / test doubles | `abap-dev/core/abap-unit-testing` |
| OData V2/V4 service | `abap-dev/core/odata` |
| Authorization / IAM / DCL | `abap-dev/core/authorization-iam` |
| BAdI / enhancement | `abap-dev/core/badi-enhancement` |
| BTP ABAP Environment / Steampunk | `abap-dev/core/btp-abap-environment` |
| Business events / eventing | `abap-dev/core/rap-business-events` |
| Released classes lookup | `abap-dev/core/released-abap-classes` |
| ABAP SQL / AMDP / CTE | `abap-dev/core/abap-sql-amdp` |
| FS document → data model/UI/API/logic | `abap-dev/fs-analysis/*` |
| SAP process knowledge (Finance/SCM/PP…) | `abap-dev/process/sap-process-*` |
| Transport readiness / ADT CLI | `code-review/sap-transport-gate`, `code-review/sap-adt-cli` |
| abapGit workflow | `abap-dev/core/abapgit` |
| BTP architecture diagram | `abap-dev/core/btp-diagram-generator` |
