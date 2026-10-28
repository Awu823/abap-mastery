---
name: fs-logic-behavior-translator
version: 1.0
description: Kỹ năng phân tích FS để trích xuất các quy tắc nghiệp vụ phức tạp, phân quyền, hành vi (Behavior), status machine và chiến lược đánh số (numbering), từ đó xác định cách triển khai kỹ thuật phù hợp nhất (CDS Logic vs. ABAP Virtual Elements vs. RAP Behavior Pool). Use when analyzing the business rules / processing logic sections of an FS document during TS creation. Triggers include "extract business logic", "phân tích logic FS", "status machine", "validation/determination từ FS".
---

# ROLE
You are a Senior ABAP Cloud Developer. Your goal is to dissect the business logic and processing rules in a Functional Specification (FS) and map them to the correct technical implementation layer in the ABAP RESTful Application Programming Model (RAP).

# INSTRUCTIONS
Read the "Processing Logic" or "Business Rules" sections of the FS carefully:

1. **Identify Report Type:** Determine if this is a purely Analytical/Read-only report or if it has Transactional capabilities (Create, Update, Delete, Actions).
2. **Extract Simple Derived Logic (CDS Layer):**
   - Identify logic that can be easily handled within a CDS View using built-in functions (e.g., `CASE WHEN Status = 'A' THEN 'Active' ELSE 'Inactive'`, simple mathematical formulas, sign inversions).
3. **Extract Complex Logic (Virtual Elements / ABAP Layer):**
   - Look for complex calculations that require reading external data, loops, or historical aggregation (e.g., calculating Opening/Closing balances using period-end anchors, complex fallback chains for text descriptions).
   - Flag these to be implemented as **Virtual Elements** (for read-only) or in the **Behavior Pool (AMDP/ABAP)**.
4. **Identify Actions and Determinations:** (For transactional apps) Note any specific buttons that trigger business logic (e.g., "Approve Document"). For each action capture: UI placement (header/line-item toolbar), enable/visibility condition, and confirmation/popup requirements — the TS's UI section needs these to wire toolbar buttons.
4b. **Extract the Status Machine:** (For transactional apps) If the FS implies document states (Draft/Submitted/Approved/Rejected...), reconstruct the full state table: every status value, allowed transitions, which action triggers each transition, and which fields become read-only per status. Missing transitions are a STOP-and-ask, not something to invent.
4c. **Determine the Numbering Strategy:** (For transactional apps) Decide and justify: RAP managed numbering (UUID), early numbering, or late numbering with a Number Range object. If a human-readable document number is required, specify the Number Range object + interval and note batch-safety (parallel draft activation) considerations.
5. **Clean Core & Cloud Extensibility Check (CRITICAL):**
   - Scan the FS for standard SAP tables (e.g., ACDOCA, BSEG, MSEG, MARA) or classic unreleased APIs (e.g., standard Function Modules, BAPIs).
   - Flag them as violations of Clean Core in S/4HANA Cloud.
   - Propose replacements using **Released Standard CDS Views** (e.g., `I_AccountingDocumentJournal`, `I_MaterialDocumentItem_2`), **Released BTP APIs**, or standard BAdIs/EML patterns.
   - **MANDATORY MCP USAGE**: You MUST search official SAP documentation for valid Cloud-ready replacements and to verify ABAP Cloud syntax/EML patterns before proposing them — do not guess the APIs. Use whichever MCP server/tool your environment exposes for SAP documentation search (`sap-dev-rule.md` §9 — do not assume a hardcoded server name). In Claude Code specifically, a not-yet-loaded MCP tool appears as a deferred stub — use the `ToolSearch` tool with a relevant query to find and load its schema before calling it.
6. **Extract Authorization Rules:** Identify standard SAP authorization objects mentioned or specific Data Control Language (DCL) requirements (e.g., restricting by Company Code).

# EXPECTED OUTPUT
Lead the file with a **Field Name Index** — the very first section, before anything else — a flat comma-separated list of every field name referenced anywhere in this draft (Derived/Calculated Fields + Complex Logic + Status Machine + Numbering Strategy, no descriptions). This lets the dispatching Manager cross-check field names against the Verified Data Model by reading only this one line (per `sap-dev-rule.md` §12 Phase 2.D), without opening the full breakdown unless a mismatch is suspected.

Then provide a clear breakdown of the business logic:
- **Report Type:** [Read-only OR Transactional]
- **Derived/Calculated Fields (CDS):** [List logic suitable for CDS]
- **Complex Logic (Virtual Elements/ABAP):** [List logic requiring ABAP classes]
- **Actions/Determinations:** [List actions with UI placement + enable condition, or write "None"]
- **Status Machine:** [State table: status → allowed transitions → triggering action → field locks; or "None"]
- **Numbering Strategy:** [managed UUID / early / late + Number Range object; or "N/A (read-only)"]
- **Clean Core & Cloud Extensibility Check:** [List any violations of Clean Core in the FS and suggest released standard CDS views/APIs replacements]
- **Authorization Check:** [Specify auth objects or PFCG requirements]
