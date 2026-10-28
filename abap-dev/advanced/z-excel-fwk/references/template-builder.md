# Authoring the `.xlsx` Template

The template is the layout *and* the mapping spec. Build it with a Python/openpyxl script rather than by hand: the script is reviewable, re-runnable after a layout change, and diffable — a binary edited in Excel is none of those. Read `tag-reference.md` first; this file is about producing the file.

Tooling verified on this machine: **openpyxl 3.1.5**, **Pillow is not installed**. Consequence: `ws.add_image()` is unavailable, so never bake a static picture into the template — put a `${image:...}` tag in a merged box and let the engine insert the picture at runtime.

## Step 1 — pin the data contract before drawing anything

Whatever the input is (a JSON sample, an ABAP structure, a mockup screenshot, an existing Excel file), first write down the sheet's namespace:

- the flat scalar fields (camelCase, `[a-zA-Z0-9_]+`),
- **exactly one** item array and its fields,
- whether the array needs row variants (`row_type`) and which columns auto-merge.

If the input is an image or a PDF mockup, transcribe it to a grid table first (`[Skill: fs-vision-extractor]`) — region, cell range, label, source field — and get that table confirmed. Do not guess a field name; a tag that does not match the payload renders as empty and the bug only shows up at runtime.

If the input is an existing Excel file, read it with openpyxl and list its cells, merges, widths and number formats, then rebuild it as a script. `references/assets/*.xlsx` are three real production templates worth reading for conventions.

## Step 2 — decide the sheet split and the master sheets

One element of the sheets array = one output sheet. Each element names its master with `templateSheet` (by name); omitted → the file's first sheet. So a template file describes **one or more document types**, and the ABAP loop decides how many copies of each come out, in array order.

| Requirement | Design |
|---|---|
| one document per selected record (invoice, order) | one master, loop the records in ABAP, one sheet each, `sheetName` = the document id |
| one consolidated list | one master, one sheet, all rows in the single item array |
| N documents **plus** a summary page | two masters (`TPL_TRANSACTION`, `TPL_SUMMARY`); append the summary element **last** — array order is sheet order |
| two unrelated tables | two sheets, and since each can carry its own master they may have completely different layouts |
| grouped list with subtotals | one master, one flat array, `row_type` per row |

Naming and layout rules for a multi-master file:

- Prefix masters `TPL_*` and reference them **by name only** — `getWorksheet(<number>)` matches the internal id, not the tab order.
- **Every** sheet in the file is treated as a master and is deleted after rendering. Never leave an instruction sheet, a lookup sheet or a leftover `Sheet1` in the file expecting it to survive.
- Masters share nothing: column count, widths, orientation, fonts, row-variant sets, images and number formats are all per-master. A summary page can be portrait/5 columns next to a landscape/7-column document page.
- The one-item-array rule is **per master**, so two unrelated tables are now cleanly solved by two masters.
- No cross-sheet formulas — every master is gone by the time the file is saved (expected result: `#REF!`).

## Step 3 — lay out each master sheet

Copy `references/assets/build_template.py` and reshape it; in a multi-master file, run the same layout routine once per master with its own style/column table. The structure that file demonstrates:

1. **Style constants at the top** — fonts, fills, borders, number formats, column table. Keep every visual decision there so the layout code stays readable.
2. **Header block** — logo merge box with `${image:logo}`, company block, title, label/value grid. Keep labels and values in separate cells so a numeric value keeps its own number format.
3. **Table header row** — static, styled, frozen via `ws.freeze_panes`.
4. **Template block** — the contiguous rows carrying `${table:...}` / `${rowType:...}`.
5. **Footer** — grand totals from scalars, below the block (it shifts down automatically).
6. **Page setup** — `print_area`, orientation, fit-to-width, repeated title rows, frozen panes, tab colour. These are now genuinely honoured per master (see `tag-reference.md` §5), so set them deliberately instead of relying on the ExcelJS default.

### Rules that are easy to get wrong

- **Number formats belong on the template cell.** The cloned style carries them to every generated row. Send the value as a JSON number and the cell formats it; send it pre-formatted as a string and you get left-aligned text.
- **Style merged followers explicitly.** openpyxl only styles the top-left cell of a merge, but the engine clones cell styles one at a time — un-styled follower cells lose their borders after expansion. Use the `style_span()` helper.
- **Merge before tagging an image/QR.** The picture is anchored from the tag cell to the end of its merge range; an un-merged tag cell yields a tiny picture.
- **Keep the template block contiguous.** Any row between the first and last tagged row is part of the block and is deleted after expansion — including a blank spacer row.
- **Always keep one DEFAULT row** (a template row with no `${rowType:}`) unless every possible `row_type` value is declared. Items matching no variant are dropped without an error.
- **Static text inside a template row is cloned too.** `${rowType:L2}Subtotal` renders as `Subtotal` on every L2 row — that is the idiom for labelling variant rows.
- **Avoid formulas.** Cells whose formula errored, or whose formula contains `IMAGE`, are blanked by the engine, and formulas are not re-pointed when rows are inserted. Compute in ABAP instead.
- **Colour by value via conditional formatting**, not by hand — the engine copies conditional formatting rules and expands their ranges over the generated rows. (`material_report_styled.xlsx` uses this for criticality columns.)
- **Diacritics are fine in text**, not in tag names.
- **Do not indent a `${rowType:...}` row with leading spaces** — the engine trims them when it strips the tag. Use Excel's alignment/indent property instead.
- **Hide the masters if you like** (`ws.sheet_state = "hidden"`), it is safe: the engine deliberately does not copy `state`, so output sheets stay visible.
- **Set `print_area` to the pre-expansion range.** The engine widens it by the number of rows the table added, so a footer pushed below the block stays printable.

## Step 4 — verify before handing over

```bash
python3 build_my_template.py my_template.xlsx
python3 verify_template.py my_template.xlsx sample_payload.json
```

`sample_payload.json` is one serialized `tt_sheets` payload — either taken from a real action run or hand-written to match the ABAP structure. The linter resolves each payload entry to its master (`templateSheet` by name, else the first sheet) and checks: unknown tag syntax, more than one array per sheet, gaps in the template block, a missing DEFAULT row, tags with no matching payload field, `row_type` values the template does not declare, `|merge` columns whose sample data never repeats, sheet-name length / forbidden characters / duplicates, a `templateSheet` naming a sheet that does not exist, master sheets no entry references (they vanish from the output), and whole-cell scalar tags whose sample value is a numeric string that does **not** start `0[0-9]` (silent `Number()` coercion).

Exit code is non-zero when there is at least one ERROR. **A template is not "done" until this run is clean**, and the run output is the evidence to cite (rule §8).

Then re-open the produced file and read the tags back:

```python
from openpyxl import load_workbook
ws = load_workbook("my_template.xlsx").worksheets[0]
for row in ws.iter_rows():
    for c in row:
        if isinstance(c.value, str) and "${" in c.value:
            print(c.coordinate, repr(c.value))
```

Rendering itself is browser-side and cannot be reproduced locally — never claim the output "looks right" without a real export from the Fiori app (rule §11).

## Step 5 — register it

Upload through the Excel Library Fiori app under the `excel_id` the ABAP action returns (**max 12 characters**). When the change adds a new master sheet, **upload before importing the ABAP transport** — an action that names a master the stored file does not contain fails the export outright with `Không tìm thấy sheet mẫu`. Each upload creates a new `version` in `ZTB_EX_LIB_I`; both the HTTP endpoint and the backend read `MAX( version )`, so a re-upload takes effect immediately and no old version is ever served. There is no rollback other than uploading the previous file again — keep the generator script in the project repo, it *is* the source of truth.
