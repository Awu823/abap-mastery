# Modern ABAP Syntax — Deep Dive

Read this when the SKILL.md body's rules-of-thumb table isn't enough: full `CORRESPONDING` addition syntax, the version-safety framing for ABAP Cloud targets, and a verified performance trade-off for table expressions. Sources/citation trail: [references/sources-deep-dive.md](sources-deep-dive.md).

## Version Safety on ABAP Cloud Targets

**"Which release is `VALUE`/`COND`/`SWITCH`/`REDUCE`/`FILTER`/basic `CORRESPONDING`/inline `DATA(...)` available in?" is the wrong question for this workspace.** All of them originate in classic ABAP 7.40 (2013). Every real ABAP Cloud target (BTP ABAP Environment, S/4HANA Cloud Public/Private Edition) runs a kernel released 2017 or later — none of these 8 core constructs is ever a version risk here. Don't hedge or add a compatibility caveat when generating code that uses them.

What genuinely IS release-gated — check before relying on these if the target release is unusually old or unconfirmed:

| Feature | Introduced | Practical impact if unavailable |
|---|---|---|
| `FINAL(...)` inline declaration (immutable, distinct from `DATA(...)`) | Release 789 (2208 / 2022 Q3) | Fall back to `DATA(...)` — mutability just isn't enforced by the compiler |
| `CORRESPONDING #( ... MAPPING a = b DEFAULT ... )` | Release 791 (2302 / 2023 Q1) | Use plain `MAPPING` without `DEFAULT`; compute the default value separately before the assignment |
| Table expressions harmonized with `READ TABLE` (`TABLE KEY` variant) | Release 912 (2408 / 2024 Q3) | Use the older table-expression key syntax; behavior differences are edge-case (see source's syntax-warning note) |
| `CORRESPONDING`/`MOVE-CORRESPONDING` `APPENDING BASE DEEP` (nested-table-preserving deep copy) | Release 783 (2102 / 2021 Q1) | Without it, a deep `CORRESPONDING` on nested tables replaces rather than appends — write the nested-table merge manually |
| `REDUCE ... NEXT` accepting compound assignment (`+=`, `-=`, `*=`, `/=`, `&&=`) | Release 781 (2008 / 2020 Q3) | Use the older `NEXT var = var + ...` form instead of `NEXT var += ...` |

If you don't know the target system's release and one of these newer refinements would matter, ask rather than assume it's there — this table is the concrete list of what to ask about, not the 8 baseline constructs above it.

## `CORRESPONDING` — Full Addition Reference

The SKILL.md body shows only the plain form. Real TS-driven code (mapping a CDS projection to a DTO, merging admin fields, deep-copying a RAP composition tree) usually needs one of these additions:

| Addition | Effect |
|---|---|
| `BASE ( x )` | Keep `x`'s existing values, only overwrite matched components — note the extra parentheses around the base, unlike `VALUE`'s `BASE x`. |
| `MAPPING a = b [DEFAULT ...]` | Map a differently-named source component to a target component; never use `-` for nested-component mapping. `DEFAULT` (789+, see table above) supplies a value when the mapped source is unusable. |
| `EXCEPT b` | Exclude component `b` from the assignment — it stays initial. `EXCEPT *` combined with `MAPPING` means *only* the mapped components are populated, everything else stays initial. |
| `DISCARDING DUPLICATES` | For internal tables with a unique key — drop duplicate lines instead of raising an exception. |
| `DEEP` | Resolve nested tables at every hierarchy level, matched by name line-by-line — needed for composition-tree deep-copies. |
| `[DEEP] APPENDING` | Preserve the target's existing nested-table lines instead of replacing them (783+ for the `DEEP` variant, see table above). |
| `FROM tab USING` | Build a table by joining against a lookup table and comparing components — useful for enrichment-style transforms without a full ABAP SQL join. |

```abap
"Non-identical components in the target are initialized to blank/zero
s2 = CORRESPONDING #( s1 ).

"BASE: retain s2's existing values, only overwrite what s1 supplies
s2 = CORRESPONDING #( BASE ( s2 ) s1 ).

"MAPPING: source component c -> target component d
s2 = CORRESPONDING #( s1 MAPPING d = c ).

"EXCEPT: exclude b from the assignment (b stays initial in s2)
s2 = CORRESPONDING #( s1 EXCEPT b ).

"MAPPING + EXCEPT * : only d gets populated (from c), everything else initial
s2 = CORRESPONDING #( s1 MAPPING d = c EXCEPT * ).

"Internal tables: same rules apply per line
it2 = CORRESPONDING #( it1 ).
```

Decision cue: reach for `BASE` the moment you're updating an existing structure/table rather than building a fresh one — without it, every unmapped component silently resets to initial, which is a common source of "why did my other fields disappear" bugs when refactoring a manual field-by-field assignment into `CORRESPONDING`.

## Table Expressions — the Repeated-Access Performance Trap

Table expressions (`itab[ key = val ]`) are expressions, not statements — each occurrence re-resolves the table access. Multiple table expressions against the *same line* in a hot loop measurably cost more than resolving the line once via a field symbol or data reference and reusing it. Verified via the official performance cheat sheet's own benchmark (`references/sources-deep-dive.md`): a loop doing 6 field updates across 2 lines using table expressions directly (`it[ 1 ]-a = ...`, `it[ 1 ]-b = ...`, ...) ran measurably slower than the same 6 updates through cached field symbols:

```abap
"Slower: 6 separate table-expression resolutions per iteration
it[ 1 ]-a = sy-index.
it[ 1 ]-b = sy-index.
it[ 1 ]-c = sy-index.
it[ 2 ]-d = sy-index.
it[ 2 ]-e = sy-index.
it[ 2 ]-f = sy-index.

"Faster: resolve each line once, then reuse
ASSIGN it[ 1 ] TO FIELD-SYMBOL(<fs1>).
ASSIGN it[ 2 ] TO FIELD-SYMBOL(<fs2>).
<fs1>-a = sy-index.
<fs1>-b = sy-index.
<fs1>-c = sy-index.
<fs2>-d = sy-index.
<fs2>-e = sy-index.
<fs2>-f = sy-index.
```

Decision cue: a single table-expression read/write is fine and more readable than a `READ TABLE`/field-symbol pair — don't pre-optimize a one-off access. Reach for the field-symbol-caching form specifically when the same line is touched 3+ times in a loop that runs often (batch processing, RAP determination over many instances), not as a blanket rule.

## Decision Trade-offs (extends SKILL.md's readability boundary)

- **`FINAL(...)` vs `DATA(...)`**: prefer `FINAL(...)` for a value that's computed once and never reassigned (a lookup result, a derived total) — it documents the intent and the compiler enforces it. Use `DATA(...)` when the variable is genuinely reassigned later in the same scope (an accumulator outside a `REDUCE`, a loop-carried variable). Don't reflexively convert every `DATA(...)` to `FINAL(...)` in a review — that's churn, not a correctness fix.
- **Nesting depth**: the SKILL.md body already caps functional-style nesting at ~2 levels before falling back to a classic `LOOP`. The `CORRESPONDING`/table-expression content above doesn't change that boundary — a `CORRESPONDING` with 3+ stacked additions (`BASE` + `MAPPING` + `EXCEPT` + `DEEP APPENDING`) is exactly the kind of case where splitting into two statements with an intermediate variable reads better than a single dense expression.
