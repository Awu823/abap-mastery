# Tag Reference — authoritative

Every rule below is read out of `z/custom/excel/lib/ExcelExportHelper.js`. Where the old HTML training deck disagrees, **this file wins** (the deck's `${:rowType:{value}}` form, for example, does not exist in the engine).

## 0. The five regexes

```js
REGEX_TAG_IMG     = /\$\{image:([a-zA-Z0-9_]+)\}/
REGEX_TAG_VAR     = /\$\{([a-zA-Z0-9_]+)\}/g
REGEX_TAG_TBL     = /\$\{table:([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)(?:\|(merge))?\}/
REGEX_TAG_BARCODE = /\$\{([a-zA-Z0-9_]+)\|(barcode|qrcode|datamatrix)\}/
ROW_TYPE          = /\$\{(?:rowType|row_type):([a-zA-Z0-9_]+)\}/i
```

Consequences: names are `[a-zA-Z0-9_]+` only — no dots, spaces, dashes or diacritics. Tag matching is case-sensitive except `rowType`.

A cell is only inspected when its ExcelJS type is **String** or **RichText**. A tag inside a formula cell, a number cell, or a date cell is never resolved.

## 1. `${varName}` — scalar

Resolved from `data[varName]` of the current sheet.

| Situation | Result |
|---|---|
| value present | tag replaced |
| whole cell was exactly the tag and value is numeric-looking | cell becomes a **real number** (`Number(value)`) — the template's number format applies |
| whole cell was exactly the tag and the value matches `/^0[0-9]/` | **stays text**, leading zero preserved (`"02"`, `"0101234567"`) |
| value missing / null / undefined | replaced with `""`; if the cell ends up empty the cell value is set to `null` |
| tag embedded in a sentence | string substitution, result stays text |
| cell also contains `table:` | **skipped** in this pass (the table pass handles it) |
| RichText cell | each run is substituted individually, formatting preserved |

**Numeric-coercion trap.** The coercion runs on the *whole resulting cell text*: a cell containing only `${soId}` with value `"1000"` becomes the number `1000`, right-aligned. Since the leading-zero fix the guard is

```js
/^0[0-9]/.test(newValue) ? newValue : (isNaN(newValue) ? newValue : Number(newValue))
```

so the SAP-typical codes that used to be mangled now survive as text:

| Value | Result | Note |
|---|---|---|
| `"02"`, `"0101234567"`, `"00"` | stays text | status / company code / tax id — the case the fix targets |
| `"0"`, `"0.5"`, `"1.50"`, `"99999.99"` | becomes a number | unchanged, decimals still format |
| `"1000"` | becomes a number | unchanged — no leading zero, so still coerced |

`${table:...}` cells never had this problem; before the fix the same status code printed correctly inside the table and wrongly in the header block.

If an identifier without a leading zero must stay text, still do one of:

- keep a prefix/suffix in the template cell (`SO ${soId}`), or
- send a value that cannot parse as a number (e.g. already formatted `SO-1000`), or
- accept the number and set an appropriate number format on the template cell.

Dates: send them as pre-formatted strings from ABAP (`|{ lv_date DATE = USER }|`). A date string like `2026-09-18` is not numeric, so it stays text.

## 2. `${image:varName}` — picture

- Value: a data URI (`data:image/png;base64,...`) or bare base64 — the engine prefixes `data:image/png;base64,` when `data:image` is absent, and always registers the image with `extension:'png'`.
- The tag cell is cleared, and the image is anchored `tl` = the tag cell, `br` = the **end of the merge range** when the tag sits on a merge master, otherwise the same single cell. `editAs:'twoCell'` — the image stretches to the box and follows row/column resizing.
- So: **merge the cells first, put the tag in the top-left of that merge**, and the logo fills that box exactly.
- A missing value leaves the cell empty and inserts nothing — no error.

ABAP side: use the released helper rather than encoding by hand.

```abap
ls_data-logo = zcl_image_lib=>get_latest_image_base64( iv_image_id = 'this_is_logo' ).
" returns |data:{ mime_type };base64,{ ... }| from ZI_IMG_I, latest version, '' on any failure
```

## 3. `${varName|barcode}` / `|qrcode` / `|datamatrix`

Rendered client-side with bwip-js onto a canvas, inserted as PNG, same anchoring/merge behaviour as `${image:}`.

| Suffix | bwip-js bcid | Extras |
|---|---|---|
| `barcode` | `code128` | height 12 mm, human-readable text printed underneath, centered |
| `qrcode` | `qrcode` | scale 3, padding 5 |
| `datamatrix` | `datamatrix` | scale 3, padding 5 |

The value is stringified. Empty/null → nothing drawn, cell cleared. A bwip-js failure is logged to the console and swallowed — the export still succeeds with a blank cell, so a missing barcode is a console-only symptom.

## 4. `${table:arrayName.fieldName}` — the item table

The engine scans the sheet for rows containing any `${table:...}` or `${rowType:...}` tag. Those rows form one contiguous **template block** from the first to the last such row. For each element of `data[arrayName]` it appends a copy of the matching template row, then deletes the whole template block.

Critical properties:

1. **One array per sheet.** `tableArrayName` is a single variable, overwritten by each match. Two different array names in one sheet means only the last one seen drives the loop, and the other's tags are filled from the wrong item. Design around it (see SKILL.md §4).
2. Everything in a template row is cloned: static text, borders, fills, fonts, number formats, row height, and horizontal merges.
3. If a cell's content is **exactly** the tag, the raw value is assigned (numbers stay numbers → number format applies). If the tag is embedded in text, a string replacement happens and the cell becomes text.
4. A missing field on an item becomes `""` — the tag is removed, never printed.
5. Rows are inserted in chunks of 10 000 to survive large payloads.

### `|merge` — vertical auto-merge

`${table:items.storeName|merge}` marks that column for post-processing: after expansion, vertically adjacent cells **with equal values** are merged into one. Comparison is on the cell value (objects compared via `JSON.stringify`). Sort the array in ABAP so equal values are adjacent — the engine does not sort.

### `${rowType:LEVEL}` — multiple row layouts

Put `${rowType:L1}` anywhere in a template row to register that row as the layout variant named `L1`. The tag text is stripped from the cell (the rest of the cell's text survives, so `Subtotal ${rowType:L2}` renders as `Subtotal`). A row carrying only a `rowType` tag and no `table:` tag still counts as part of the template block.

At render time each item picks its layout with `item.row_type || item.rowType || "DEFAULT"`, falling back to the `DEFAULT` variant (the template row that has no `rowType` tag). An item whose `rowType` matches nothing and where no `DEFAULT` row exists is **silently skipped**.

Typical use — `material_report_styled.xlsx` defines `L1`, `L2`, `L3` for group header / detail / subtotal rows; ABAP emits one flat array where each item carries `row_type`.

> `${table:items.rowType}` is something else entirely: it *prints* the field. Both can coexist (`store_revenue_tmp.xlsx` does this).

## 5. Layout features carried over automatically

Everything below is copied **from the master sheet that this output sheet was cloned from** — with multiple masters in play, sheet A can be landscape/7-column and sheet B portrait/5-column in the same file.

| Feature | Behaviour |
|---|---|
| Column widths / hidden columns / column styles | copied |
| Merged cells outside the table block | copied as-is |
| Horizontal merges inside a template row | re-applied to every generated row |
| Static images in the template | copied |
| Conditional formatting | copied, and ranges that overlap or sit below the table block are shifted/expanded by the number of generated rows |
| Formula cells | copied, but cells whose formula errored, or whose formula contains `IMAGE`, are blanked |
| `pageSetup` | copied — orientation, fit-to-page, paper size, margins, `printTitlesRow` (repeat header rows across printed pages), `printArea` |
| `headerFooter` | copied — print header/footer |
| `views` | copied — frozen rows/columns, `showGridLines`, zoom |
| `properties` | copied — tab colour, default row height / column width |
| `state` (hidden/visible) | **deliberately not copied** — masters are usually hidden in the template file, and copying it would hide every output sheet |
| `autoFilter` | **not copied** — known gap |

Conditional formatting is therefore the supported way to do data-dependent colouring (e.g. negative variance in red) — the engine does not colour by value on its own.

**`printArea` is re-expanded after the table grows.** The master's `printArea` is captured, then widened by the number of net rows the table added (`A1:E15` → `A1:E18` for +3 rows), so footer content pushed below the block stays inside the printed area.

> Sheet-level print settings were **not** copied before commit `35ce9e5`, so every output sheet fell back to ExcelJS defaults (portrait, gridlines on) regardless of the template. If an old report suddenly prints landscape without gridlines, that is this fix taking effect, not a regression — the template always declared it.

## 6. Multiple template sheets (`templateSheet`)

`templateSheet` is **not a tag** — it is a field of the sheets array element, resolved before any tag processing:

```
for each element of the payload array:
    master = element.templateSheet ? lookup BY NAME : first sheet of the template file
    if not found  → throw  'Không tìm thấy sheet mẫu "<name>" trong file template.'
    clone master → rename to element.sheetName → resolve tags → copy master's print settings
after the loop:
    delete every master sheet
```

What this changes for template design:

1. The template file holds **N masters, all of which disappear** from the output. A sheet that must appear in the result is an array element, never a sheet you leave lying in the file.
2. Masters are looked up **by name** — `getWorksheet(number)` in ExcelJS matches the internal id, not the tab position, so index-based reference is unreliable. Name them `TPL_*`.
3. Each master is an independent document: its own column count and widths, orientation, title styling, row-variant set, images and number formats. Two masters share nothing.
4. The engine's one-array-per-sheet limit is **per master**, so two unrelated tables now mean two masters rather than one shared layout.
5. Avoid cross-sheet formulas — the referenced master is gone by the time the file is saved.

## 7. Quick grammar card

```
${companyName}                      scalar
${image:logo}                       picture, fills its merge box
${soId|qrcode}                      QR, fills its merge box
${soId|barcode}                     Code128 + caption
${soId|datamatrix}                  DataMatrix
${table:items.matId}                item column
${table:items.storeName|merge}      item column + vertical auto-merge
${rowType:L2}                       marks this template row as layout "L2"
```
