## Release Compatibility Matrix

Target system releases dictate allowed syntax. Flag incompatible syntax when reviewing for specific target releases:

| Feature / Syntax | 7.40 SP08 | 7.50 | 7.51 | 7.55+ | ABAP Cloud |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Inline Declarations `DATA(...)` / `FIELD-SYMBOL(...)` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Constructor Expressions (`VALUE`, `NEW`, `CONV`, `COND`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Table Expressions `itab[ ... ]` & `line_exists()` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Table Operators (`REDUCE`, `FILTER`, `BASE`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Inline Declaration `FINAL(...)` | ❌ | ✅ | ✅ | ✅ | ✅ |
| Host Expressions `@( expr )` in OpenSQL | ❌ | ✅ | ✅ | ✅ | ✅ |
| Common Table Expressions (`WITH`) | ❌ | ❌ | ✅ | ✅ | ✅ |
| CDS View Entities (`DEFINE VIEW ENTITY`) | ❌ | ❌ | ❌ | ✅ | ✅ |

## Advanced Table Operations & Refactoring
- **CORRESPONDING MAPPING**: Prefer `CORRESPONDING #( src MAPPING target_field = src_field )` over manual field-by-field assignments.
- **Table Reductions (REDUCE)**: Use `REDUCE` for aggregations, summations, and string concatenations over internal tables instead of explicit loop counters.
- **Table Filtering (FILTER)**: Use `FILTER #( itab WHERE status = 'A' )` on sorted/hashed tables instead of looping to populate a secondary table.
- **Group Loop Processing (GROUP BY)**: Replace legacy control break statements (`AT NEW`, `AT END OF`) with modern `LOOP AT itab INTO DATA(group) GROUP BY ( key = itab-key )`.

## Performance Optimization
- **Golden Rules of OpenSQL**:
  - Keep the result set small (use `WHERE` clauses effectively).
  - Minimize the amount of data transferred (select only required columns, avoid `SELECT *`).
  - Minimize the number of database accesses (use `JOIN` or `FOR ALL ENTRIES` instead of `SELECT` in a `LOOP`).
- **FOR ALL ENTRIES**: Always check if the driving table is not initial before executing a `SELECT ... FOR ALL ENTRIES`. Otherwise, it fetches the entire table.
- **Buffering**: Use SAP table buffering for configuration and customizing tables.
- **Memory Management**: Clear internal tables (`CLEAR`, `FREE`) when no longer needed in long-running background jobs to prevent memory leaks.
