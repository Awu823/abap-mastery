#!/usr/bin/env python3
"""Reference generator for a z.custom.excel.lib Excel template.

This is a worked example, not a library to import: copy it, rename it, and
reshape the layout for the report at hand. It produces a one-sheet template
with a logo box, a header block, a QR code, an item table with three row
layouts (group / detail / subtotal) and a vertical-merge column.

    python3 build_template.py out.xlsx
    python3 verify_template.py out.xlsx sample_payload.json

Engine rules baked into this file (see references/tag-reference.md):
  * EVERY worksheet of the file is a master template and is deleted from the
    output; a payload entry picks its master by name via "templateSheet",
    falling back to the first sheet. For several document types, run a layout
    routine like the one below once per master and name them TPL_*.
  * exactly ONE ${table:<array>.<field>} array per sheet
  * template rows must be contiguous; they are deleted after expansion
  * a cell that is exactly a tag keeps the cell's number format
  * an image/QR fills its merge box, so merge first and tag the top-left cell
"""
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# --------------------------------------------------------------------------
# Styles — keep every visual decision here so the layout below stays readable.
# --------------------------------------------------------------------------
FONT = "Calibri"
THIN = Side(style="thin", color="B0B0B0")
MED = Side(style="medium", color="404040")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BOX_TOP = Border(left=THIN, right=THIN, top=MED, bottom=THIN)

TITLE = Font(name=FONT, size=18, bold=True, color="1F3864")
LABEL = Font(name=FONT, size=10, bold=True, color="404040")
VALUE = Font(name=FONT, size=10)
TH = Font(name=FONT, size=10, bold=True, color="FFFFFF")
GROUP = Font(name=FONT, size=10, bold=True, color="1F3864")
TOTAL = Font(name=FONT, size=11, bold=True)

FILL_TH = PatternFill("solid", fgColor="1F3864")
FILL_GROUP = PatternFill("solid", fgColor="DDEBF7")
FILL_TOTAL = PatternFill("solid", fgColor="FFF2CC")

LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
RIGHT = Alignment(horizontal="right", vertical="center")

# Number formats live on the TEMPLATE cell and survive row cloning, which is
# why numeric values must stay numeric in the JSON payload.
FMT_QTY = "#,##0.000"
FMT_AMT = "#,##0.00"

# Column layout: (width, header text, item field, alignment, number format)
COLUMNS = [
    (6, "No.", None, CENTER, None),
    (18, "Store", "storeName", LEFT, None),          # gets |merge
    (16, "Material", "matId", LEFT, None),
    (34, "Description", "matName", LEFT, None),
    (12, "Qty", "quantity", RIGHT, FMT_QTY),
    (8, "UoM", "baseUnit", CENTER, None),
    (14, "Net Price", "netPrice", RIGHT, FMT_AMT),
    (16, "Amount", "netAmount", RIGHT, FMT_AMT),
]
MERGE_COLUMNS = {"storeName"}          # rendered as ${table:items.storeName|merge}
ARRAY = "items"                        # the ONE array of this sheet
LAST_COL = len(COLUMNS)


def put(ws, row, col, value, font=VALUE, align=LEFT, border=None, fill=None, fmt=None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font
    c.alignment = align
    if border:
        c.border = border
    if fill:
        c.fill = fill
    if fmt:
        c.number_format = fmt
    return c


def style_span(ws, row, col_from, col_to, border=None, fill=None):
    """Apply border/fill to every cell of a range, including merged followers.

    openpyxl only styles the top-left cell of a merged range; the engine clones
    cell styles one by one, so the followers must be styled explicitly or the
    box loses its borders after expansion.
    """
    for col in range(col_from, col_to + 1):
        c = ws.cell(row=row, column=col)
        if border:
            c.border = border
        if fill:
            c.fill = fill


def build(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "TEMPLATE"                     # renamed per sheet at runtime anyway

    for idx, (width, *_rest) in enumerate(COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    # ---------------- header block -----------------------------------------
    # Logo: merge the box first, tag the top-left cell. The picture stretches
    # to the full merge range (editAs: twoCell).
    ws.merge_cells(start_row=1, start_column=1, end_row=4, end_column=2)
    put(ws, 1, 1, "${image:logo}", align=CENTER)
    ws.row_dimensions[1].height = 20

    put(ws, 1, 3, "${companyName}", font=Font(name=FONT, size=12, bold=True))
    put(ws, 2, 3, "${companyAddress}")
    put(ws, 3, 3, "Tel: ${companyPhone}")
    put(ws, 4, 3, "Tax code: ${conpanyTax}")

    # QR of the document id, same merge-box rule as the logo.
    ws.merge_cells(start_row=1, start_column=LAST_COL, end_row=4, end_column=LAST_COL)
    put(ws, 1, LAST_COL, "${soId|qrcode}", align=CENTER)

    ws.merge_cells(start_row=6, start_column=1, end_row=6, end_column=LAST_COL)
    put(ws, 6, 1, "SALES ORDER ${soId}", font=TITLE, align=CENTER)
    ws.row_dimensions[6].height = 26

    # Two-column label/value grid. Values are separate cells so that a numeric
    # value keeps its own format instead of being glued into a sentence.
    meta = [
        ("Customer", "${parId} - ${parName}", "Printed by", "${printedUser}"),
        ("Store", "${storeId} - ${storeName}", "Printed at", "${printedDate} ${printedTime}"),
        ("Status", "${orderStatus}", "Invoice", "${invoiceNumber}"),
    ]
    for i, (l1, v1, l2, v2) in enumerate(meta):
        r = 8 + i
        put(ws, r, 1, l1, font=LABEL)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        put(ws, r, 2, v1)
        put(ws, r, 5, l2, font=LABEL)
        ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=LAST_COL)
        put(ws, r, 6, v2)

    # ---------------- table header -----------------------------------------
    head_row = 12
    ws.row_dimensions[head_row].height = 22
    for idx, (_w, title, *_rest) in enumerate(COLUMNS, start=1):
        put(ws, head_row, idx, title, font=TH, align=CENTER, border=BOX, fill=FILL_TH)

    # ---------------- template rows ----------------------------------------
    # Contiguous block. Each row is one layout variant; items pick a variant
    # with item.row_type. Keep the DEFAULT (untagged) row — items whose
    # row_type matches nothing would otherwise be dropped silently.
    r = head_row + 1

    # L1 — group header: one wide merged cell, static text kept next to the tag.
    ws.row_dimensions[r].height = 20
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=LAST_COL)
    put(ws, r, 1, "${rowType:L1}${table:items.matType}", font=GROUP, align=LEFT,
        border=BOX, fill=FILL_GROUP)
    style_span(ws, r, 1, LAST_COL, border=BOX, fill=FILL_GROUP)
    r += 1

    # DEFAULT — detail row, no rowType tag.
    ws.row_dimensions[r].height = 18
    for idx, (_w, _t, field, align, fmt) in enumerate(COLUMNS, start=1):
        if field is None:
            put(ws, r, idx, None, align=align, border=BOX)
            continue
        suffix = "|merge" if field in MERGE_COLUMNS else ""
        put(ws, r, idx, f"${{table:{ARRAY}.{field}{suffix}}}",
            align=align, border=BOX, fmt=fmt)
    r += 1

    # L2 — subtotal row.
    ws.row_dimensions[r].height = 20
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=LAST_COL - 1)
    put(ws, r, 1, "${rowType:L2}Subtotal ${table:items.matType}", font=TOTAL,
        align=RIGHT, border=BOX_TOP, fill=FILL_TOTAL)
    style_span(ws, r, 1, LAST_COL - 1, border=BOX_TOP, fill=FILL_TOTAL)
    put(ws, r, LAST_COL, f"${{table:{ARRAY}.netAmount}}", font=TOTAL, align=RIGHT,
        border=BOX_TOP, fill=FILL_TOTAL, fmt=FMT_AMT)
    last_template_row = r

    # ---------------- footer (below the block) ------------------------------
    # Rows below the template block are shifted down automatically.
    foot = last_template_row + 2
    ws.merge_cells(start_row=foot, start_column=1, end_row=foot, end_column=LAST_COL - 1)
    put(ws, foot, 1, "TOTAL", font=TOTAL, align=RIGHT)
    put(ws, foot, LAST_COL, "${totalPrice}", font=TOTAL, align=RIGHT, fmt=FMT_AMT)
    put(ws, foot + 1, LAST_COL, "${currency}", font=LABEL, align=RIGHT)

    ws.print_area = f"A1:{get_column_letter(LAST_COL)}{foot + 1}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.freeze_panes = ws.cell(row=head_row + 1, column=1)

    wb.save(path)
    print(f"written {path}  (table block rows {head_row + 1}-{last_template_row})")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "template.xlsx")
