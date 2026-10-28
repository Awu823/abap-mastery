---
name: modern-abap-syntax
version: 1.0
description: Help with modern ABAP syntax for Cloud Development including constructor expressions, inline declarations, string processing, dynamic programming, and built-in functions. Use when users ask about ABAP syntax, VALUE, COND, SWITCH, REDUCE, FILTER, FOR loops, string templates, Field Symbols, Date and Time functions, built-in functions, or numeric operations. Triggers include "constructor expression", "string template", "REDUCE", "VALUE", "inline declaration", "cú pháp abap", "abap syntax". For SQL/SELECT/AMDP questions use abap-sql-amdp. Use even for quick one-off syntax questions or rewrites — Vietnamese triggers: "viết lại cho gọn", "chuyển sang VALUE/REDUCE", "refactor vòng LOOP", "cách viết ABAP hiện đại".
---

# Modern ABAP Syntax

Enforce modern ABAP in all generated code — workspace rule §3 mandates VALUE/COND/REDUCE-style constructs and rejects legacy procedural patterns. You already know the syntax; this skill exists to make the *choice* consistent, not to teach it.

## Rules of Thumb

| Instead of (legacy)                              | Write (modern)                                            |
| ------------------------------------------------ | ---------------------------------------------------------- |
| `DATA: lt_x TYPE ... . APPEND ... TO lt_x.` loops to build tables | `VALUE #( FOR ... ( ... ) )` / `FILTER #( ... )` |
| `IF/ELSEIF` chains assigning one variable        | `COND #( WHEN ... THEN ... ELSE ... )` or `SWITCH #( )`     |
| Accumulator loops (`ADD`, running totals)        | `REDUCE #( INIT ... FOR ... NEXT ... )`                     |
| `CONCATENATE ... INTO ...`                       | String templates `|{ lv_a } { lv_b }|`                      |
| Up-front `DATA:` blocks                          | Inline declarations `DATA(lv_x) = ...` / `FIELD-SYMBOL(<fs>)` at first use |
| `READ TABLE ... WITH KEY ... BINARY SEARCH`      | Table expressions `lt_tab[ key = val ]` (+ `OPTIONAL`/`DEFAULT`) or `line_exists( )` |
| `MOVE-CORRESPONDING` + manual fixes              | `CORRESPONDING #( ... MAPPING ... EXCEPT ... )`             |
| Helper variables for type conversion             | `CONV #( )`, `EXACT #( )`, `NEW #( )`                       |

Prefer functional/expression style when it stays readable; fall back to a classic LOOP when the expression version would nest more than ~2 levels deep — readability beats cleverness (Clean ABAP).

## Boundaries

- SQL expressions, SELECT syntax, window functions, CTE, AMDP → [Skill: abap-sql-amdp]
- Clean-code review of existing ABAP → [Skill: abap]
- EML (RAP entity manipulation) → [Skill: rap]

## Deep Dive

For the full `CORRESPONDING` addition reference (`BASE`/`MAPPING`/`EXCEPT`/`DEEP APPENDING`/...), which of these constructs are ever actually release-gated on a real ABAP Cloud target (most aren't — see the deep-dive for the ones that are), and a verified table-expression performance trade-off, read [references/deep-dive.md](references/deep-dive.md) — only when the rules-of-thumb table above isn't enough for the case at hand.

## Reference

Full syntax with examples: [SAP ABAP Cheat Sheets](https://github.com/SAP-samples/abap-cheat-sheets) — constructor expressions (05), string processing (07), internal tables (01), dynamic programming (06). Consult when unsure of an edge case rather than guessing.
