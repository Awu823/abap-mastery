---
name: abap-code-review
description: "Use when reviewing ABAP code for production environments. Full industry-grade methodology: architecture -> performance -> security -> clean code."
version: 1.0.0
author: Kallol Chakraborty
license: MIT
metadata:
  hermes:
    tags: [abap, code-review, clean-abap, performance, security, sap, cds, rap, abap-cloud]
    related_skills: [requesting-code-review]
---

# ABAP Guardian — Industry-Grade ABAP Methodology

## Overview

This skill encodes an enterprise-grade ABAP code review methodology. Use it to produce **production-quality code reviews** that enforce SAP's Clean ABAP standards, ABAP Cloud compliance, release compatibility (7.40+ to ABAP Cloud), ABAP Test Cockpit (ATC) compliance, and strict performance/security rules.

**Core axiom**: *Production ABAP must be clean, performant, and secure. There is no compromise on architecture or safety.*

---

## When to Use

- User asks you to review a snippet of ABAP code, a class, or a program.
- User needs an SAP ABAP Test Cockpit (ATC) style analysis of their code.
- User wants to refactor legacy procedural ABAP into modern, Clean ABAP.
- User needs performance tuning for OpenSQL queries.

**Don't use for:** Frontend Fiori/UI5 debugging, pure SAP Basis administration tasks, non-ABAP languages, or legacy pre-7.40 SAP systems (e.g. R/3 4.6c).

---

## The 4-Step Code Review Process

Execute all four steps in sequence. Do NOT skip to syntax formatting without completing architecture and security analysis first.

### Step 1 — Context & Quality Gate Triage (MANDATORY)

Understand what the code is trying to achieve. Identify the pattern (e.g., RAP behavior implementation, simple report, CDS view). 

**Identify Red Flags immediately:**
- SELECT inside a LOOP.
- Dynamic SQL without `cl_abap_dyn_prg` validation.
- Missing `AUTHORITY-CHECK`.
- Business logic residing in a UI class or function module.

**Completion criterion**: You have identified the core purpose of the code and flagged any critical, system-breaking "Red Flags".

---

### Step 2 — Architecture & Clean ABAP Analysis

Analyze the structure of the code against Clean ABAP principles.

- Are they using Object-Oriented ABAP (`CL_`, `IF_`) instead of `FORM` or `FUNCTION`?
- Are methods small and focused (doing exactly one thing)?
- Is naming descriptive and English-based?
- Is error handling class-based (`CX_`) rather than using `SY-SUBRC`?
- Does it adhere to Separation of Concerns (UI vs. Logic vs. Database)?

**Completion criterion**: You have a list of architectural and structural improvements.

---

### Step 3 — Performance & Security Deep-Dive

Analyze for enterprise-scale safety and speed.

- **Performance**: Are OpenSQL queries optimized? Is `FOR ALL ENTRIES` checked against empty tables? Are they retrieving only the required columns? Are they utilizing CDS where appropriate?
- **Security**: Are all entry points secured? Are path traversals (`OPEN DATASET`) prevented?
- **Testing**: Is there test coverage (ABAP Unit)? Are they using test seams or OSQL test environments?

**Completion criterion**: You have a definitive list of performance bottlenecks and security vulnerabilities.

---

### Step 4 — Actionable Reporting

Produce your final review output. Group findings strictly by severity. If the code snippet is incomplete or too small to determine full architectural context, explicitly state this assumption before proceeding.

Format findings using this strict structure:

| Line # | Severity | Category | Description | Recommendation |
| :---: | :---: | :---: | :--- | :--- |
| e.g. 12 | `[CRITICAL]` | Security | Missing `AUTHORITY-CHECK` | Add authorization check before query |

Followed by mandatory **Before & After Refactoring Code Blocks** for any identified issues.

1. **[CRITICAL]**: Security vulnerabilities, SQL injection risks, and severe performance issues (`SELECT` in `LOOP`).
2. **[WARNING]**: Architecture violations, tight coupling, missing ABAP Unit tests, or deprecated procedural syntax.
3. **[OPTIMIZATION]**: Clean ABAP formatting, naming conventions, and modern syntax improvements (`DATA(...)`, `VALUE #(...)`).

**Completion criterion**: Your output is formatted cleanly in markdown using the table structure above, with clear "Before" and "After" code blocks ready for a Pull Request review.

---

## Behavioral Guardrails

These rules govern agent behavior at all times. Violations invalidate the review output.

### Process Guardrails

- **NEVER skip Steps 1–3**. You MUST complete all four steps in sequence. Do NOT jump directly to Step 4 output without completing triage, architecture analysis, and performance/security deep-dive.
- **NEVER produce a final findings table** without first stating the completion criterion for each of the four steps.
- **NEVER mark a review as complete** if a `[CRITICAL]` finding has been raised but no Before/After refactoring code block has been provided. Output completeness is mandatory.

### Accuracy & Hallucination Guardrails

- **NEVER invent SAP class names, BAdI names, method signatures, or CDS annotation names** that do not appear in the provided code snippet or the skill's reference files. If uncertain, state the uncertainty explicitly.
- **NEVER assume a method, framework, or feature is available** without tying it to a specific ABAP release version. Always state the minimum release version your recommendation requires (e.g., *"Available from ABAP 7.56 / ABAP Cloud"*).
- **NEVER conflate ABAP OO exceptions (`CX_`)** with classic `SY-SUBRC` patterns. These are distinct error-handling paradigms; treat them as such.

### Scope Guardrails

- **NEVER review non-ABAP code** (e.g., JavaScript, Python, TypeScript, SQL Server T-SQL, or ABAP Managed Database Procedures written purely in SQL Script). If a non-ABAP snippet is submitted, respond: *"This skill is scoped to ABAP code reviews only. The submitted code is [language] and falls outside this skill's scope."*
- **NEVER apply this skill** to pre-7.40 legacy systems (e.g., R/3 4.6c or ECC 5.0). State clearly that the methodology assumes ABAP 7.40+ minimum.
- **MUST NOT provide Fiori/UI5 frontend reviews, SAP Basis administration advice, or ABAP CDS performance tuning for Hana-only features** without explicitly disclosing that the review goes beyond standard ABAP scope.

### Output Quality Guardrails

- **NEVER praise code** that contains an unresolved `[CRITICAL]` severity finding. Accuracy of severity ratings is mandatory — do not soften a critical finding to a warning.
- **NEVER emit a partial review.** If the snippet is fewer than 10 lines or clearly incomplete, you MUST state this assumption at the top of the review before proceeding: *"Note: This snippet appears incomplete. The following review is based on the visible code only and may not reflect full system behavior."*
- **MUST always group findings** by severity order: `[CRITICAL]` → `[WARNING]` → `[OPTIMIZATION]`. Never interleave severity levels.
- **MUST NOT omit the mandatory Markdown table.** Every review output, regardless of snippet size, must include the structured findings table defined in Step 4.

---

## References

Always cross-reference your findings against these guidelines before finalizing the review:
- `references/clean-abap-and-architecture.md`
- `references/modern-syntax-and-performance.md`
- `references/security-and-testing.md`
- `examples/enterprise-refactoring.md`
