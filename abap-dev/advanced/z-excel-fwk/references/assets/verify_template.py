#!/usr/bin/env python3
"""Lint an Excel template against the z.custom.excel.lib rendering engine.

Usage:
    python3 verify_template.py TEMPLATE.xlsx [PAYLOAD.json]

PAYLOAD.json is the json_content the ABAP action returns: a list of
{"sheetName": ..., "templateSheet": ..., "data": {...}} objects. When supplied,
every entry is resolved to its master sheet (templateSheet by name, else the
first sheet of the workbook), each distinct master is linted against that
entry's data, and unused payload fields are reported.

Exit code 0 = no ERROR findings, 1 = at least one ERROR.
"""
import json
import re
import sys
from collections import defaultdict

from openpyxl import load_workbook

RE_IMG = re.compile(r"\$\{image:([a-zA-Z0-9_]+)\}")
RE_BARCODE = re.compile(r"\$\{([a-zA-Z0-9_]+)\|(barcode|qrcode|datamatrix)\}")
RE_TBL = re.compile(r"\$\{table:([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)(?:\|(merge))?\}")
RE_ROWTYPE = re.compile(r"\$\{(?:rowType|row_type):([a-zA-Z0-9_]+)\}", re.I)
RE_VAR = re.compile(r"\$\{([a-zA-Z0-9_]+)\}")
RE_ANY = re.compile(r"\$\{[^}]*\}")
RE_LEADING_ZERO = re.compile(r"^0[0-9]")
BAD_SHEET_CHARS = set("[]:*?/\\")

findings = []


def add(level, sheet, where, msg):
    findings.append((level, sheet, where, msg))


def looks_numeric(text):
    """Mirror the engine's coercion, including the leading-zero guard.

    Engine: /^0[0-9]/.test(v) ? v : (isNaN(v) ? v : Number(v))
    so "02" / "0101234567" stay text, while "0", "0.5", "1000" become numbers.
    """
    if not isinstance(text, str):
        return False
    if RE_LEADING_ZERO.match(text.strip()):
        return False
    try:
        float(text.strip())
        return True
    except (TypeError, ValueError):
        return False


def scan_sheet(ws, payload_data):
    name = ws.title
    if len(name) > 31:
        add("ERROR", name, "-", f"sheet name is {len(name)} chars (max 31)")
    if set(name) & BAD_SHEET_CHARS:
        add("ERROR", name, "-", "sheet name contains one of [ ] : * ? / \\")

    scalars, images, barcodes = {}, {}, {}
    arrays = defaultdict(dict)          # array -> {field: (cell, needs_merge)}
    row_types = {}                      # row number -> variant
    table_rows = set()
    exact_scalar_cells = []

    for row in ws.iter_rows():
        for cell in row:
            if not isinstance(cell.value, str) or "${" not in cell.value:
                continue
            text = cell.value
            ref = cell.coordinate

            for m in RE_ANY.finditer(text):
                tag = m.group(0)
                if not (
                    RE_IMG.fullmatch(tag)
                    or RE_BARCODE.fullmatch(tag)
                    or RE_TBL.fullmatch(tag)
                    or RE_ROWTYPE.fullmatch(tag)
                    or RE_VAR.fullmatch(tag)
                ):
                    add("ERROR", name, ref, f"{tag} matches no engine regex — it will be printed literally")

            rt = RE_ROWTYPE.search(text)
            if rt:
                row_types[cell.row] = rt.group(1)
                table_rows.add(cell.row)

            for m in RE_TBL.finditer(text):
                arrays[m.group(1)][m.group(2)] = (ref, m.group(3) == "merge")
                table_rows.add(cell.row)

            for m in RE_IMG.finditer(text):
                images[m.group(1)] = ref
            for m in RE_BARCODE.finditer(text):
                barcodes[m.group(1)] = (ref, m.group(2))

            if "table:" not in text:
                for m in RE_VAR.finditer(text):
                    scalars[m.group(1)] = ref
                    if text.strip() == m.group(0):
                        exact_scalar_cells.append((m.group(1), ref))

    if len(arrays) > 1:
        add(
            "ERROR",
            name,
            ", ".join(sorted(arrays)),
            "more than one item array in a sheet — the engine keeps only the last one seen; "
            "split into separate sheets or merge into one array with rowType",
        )

    if table_rows:
        lo, hi = min(table_rows), max(table_rows)
        gaps = [r for r in range(lo, hi + 1) if r not in table_rows]
        if gaps:
            add(
                "WARN",
                name,
                f"rows {lo}-{hi}",
                f"rows {gaps} sit inside the table block but carry no table/rowType tag — "
                "they are deleted together with the block",
            )
        if row_types and not [r for r in table_rows if r not in row_types]:
            add(
                "WARN",
                name,
                f"rows {lo}-{hi}",
                "every template row carries a rowType and none is the DEFAULT row — "
                "items whose rowType matches nothing are skipped silently",
            )

    if payload_data is None:
        if exact_scalar_cells:
            add(
                "INFO",
                name,
                "-",
                "whole-cell scalar tags (a numeric-looking value becomes a real number; "
                "values matching ^0[0-9] are kept as text by the engine): "
                f"{sorted({k for k, _ in exact_scalar_cells})}",
            )
        return

    # With a payload in hand, only flag the cells where the coercion actually bites:
    # a STRING value that Python can parse as a number.
    for key, ref in exact_scalar_cells:
        val = payload_data.get(key)
        if isinstance(val, str) and looks_numeric(val):
            add(
                "WARN",
                name,
                ref,
                f"${{{key}}} fills the whole cell and the sample value {val!r} is a numeric "
                "string — it will render as a number (leading zeros lost, right-aligned)",
            )

    data = payload_data
    for key, ref in scalars.items():
        if key not in data:
            add("ERROR", name, ref, f"${{{key}}} has no matching field in the payload")
    for key, ref in images.items():
        if key not in data:
            add("ERROR", name, ref, f"${{image:{key}}} has no matching field in the payload")
    for key, (ref, kind) in barcodes.items():
        if key not in data:
            add("ERROR", name, ref, f"${{{key}|{kind}}} has no matching field in the payload")

    for arr, fields in arrays.items():
        items = data.get(arr)
        if items is None:
            add("ERROR", name, "-", f"array '{arr}' is not in the payload")
            continue
        if not isinstance(items, list):
            add("ERROR", name, "-", f"payload field '{arr}' is not a JSON array")
            continue
        if not items:
            add("WARN", name, "-", f"array '{arr}' is empty in this sample — table rendering untested")
            continue
        seen = set()
        for it in items:
            seen.update(it.keys())
        for fld, (ref, needs_merge) in fields.items():
            if fld not in seen:
                add("ERROR", name, ref, f"${{table:{arr}.{fld}}} is on no item of '{arr}'")
            if needs_merge:
                vals = [it.get(fld) for it in items]
                runs = sum(1 for a, b in zip(vals, vals[1:]) if a != b) + 1
                if runs == len(vals) and len(vals) > 1:
                    add(
                        "WARN",
                        name,
                        ref,
                        f"|merge on '{fld}' but no two adjacent items share a value — "
                        "sort the array in ABAP or the merge does nothing",
                    )
        unused = seen - set(fields) - {"row_type", "rowType"}
        if unused:
            add("INFO", name, "-", f"item fields not placed in the template: {sorted(unused)}")

        variants = {it.get("row_type") or it.get("rowType") or "DEFAULT" for it in items}
        declared = set(row_types.values()) | {"DEFAULT"}
        missing = variants - declared
        if missing:
            add("ERROR", name, "-", f"items use rowType {sorted(missing)} but the template declares {sorted(declared)}")

    unused_scalar = set(data) - set(scalars) - set(images) - set(barcodes) - set(arrays)
    if unused_scalar:
        add("INFO", name, "-", f"payload fields not placed in the template: {sorted(unused_scalar)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    wb = load_workbook(sys.argv[1])
    payload = None
    if len(sys.argv) > 2:
        with open(sys.argv[2], encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, list):
            payload = [{"sheetName": "Sheet1", "data": payload}]

    # Every sheet of the workbook is a master template and is deleted from the
    # output; each payload entry picks its master BY NAME via templateSheet,
    # falling back to the first sheet.
    by_name = {ws.title: ws for ws in wb.worksheets}
    first = wb.worksheets[0]

    if not payload:
        for ws in wb.worksheets:
            scan_sheet(ws, None)
    else:
        seen_names = set()
        scanned = set()                     # master title -> scanned once
        for entry in payload:
            sn = entry.get("sheetName", "")
            if len(sn) > 31:
                add("ERROR", sn, "-", f"sheetName '{sn}' is {len(sn)} chars (max 31)")
            if set(sn) & BAD_SHEET_CHARS:
                add("ERROR", sn, "-", f"sheetName '{sn}' contains a forbidden character")
            if sn in seen_names:
                add("ERROR", sn, "-", f"sheetName '{sn}' is used by more than one entry")
            seen_names.add(sn)

            tpl = entry.get("templateSheet") or ""
            if tpl and tpl not in by_name:
                add("ERROR", sn, "-",
                    f"templateSheet '{tpl}' does not exist in the template file "
                    f"(available: {sorted(by_name)}) — the engine aborts the whole export")
                continue
            master = by_name[tpl] if tpl else first
            if master.title in scanned:
                continue                    # same master, already linted
            scanned.add(master.title)
            scan_sheet(master, entry.get("data"))

        unused = sorted(set(by_name) - scanned)
        if unused:
            add("WARN", "-", "-",
                f"template sheets never referenced by the payload: {unused} — "
                "they are deleted from the output, so a sheet meant to survive "
                "must be its own payload entry")

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: order[f[0]])
    errors = sum(1 for f in findings if f[0] == "ERROR")

    if not findings:
        print("OK — no findings.")
    for level, sheet, where, msg in findings:
        print(f"[{level:5}] {sheet}!{where}: {msg}")
    print(f"\n{errors} error(s), {sum(1 for f in findings if f[0]=='WARN')} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
