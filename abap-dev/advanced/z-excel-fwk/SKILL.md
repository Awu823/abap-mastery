---
name: z-excel-fwk
description: Usage guide for the custom Excel export-from-template framework (ABAP package Z_EXCEL_LIBRARY + SAPUI5 library z.custom.excel.lib) — how to build the ABAP side (static RAP action printExcel returning ZABS_EX_LIB_ACTION_RETURN with a camelCase JSON sheets payload), how to AUTHOR the .xlsx template itself with the engine's tag grammar (${var}, ${image:x}, ${table:arr.field|merge}, ${rowType:L1}, ${x|qrcode}), how to build a MULTI-TEMPLATE file where each output sheet picks its own master sheet via the `templateSheet` field, and how to wire the Fiori app in BAS (zero-config: manifest library dependency + custom action whose press is the library handler; optional overrides in manifest sap.ui5/config/zExcelExport; legacy ext/controller/ExcelConfig.js still honored). Use this skill INSTEAD of reading the framework source whenever a task touches Excel export on this framework — creating or debugging a PrintExcel action, designing or generating an Excel template with mapping tags, adding a summary/second-layout sheet to an existing report, registering an excel_id template version, embedding a logo/QR code, or explaining why a tag did not resolve. Triggers include "Z_EXCEL_LIBRARY", "z.custom.excel.lib", "excel library", "excel template", "PrintExcel", "printExcel action", "ExcelConfig.js", "zExcelExport", "PrintExcelHandler", "ExcelExportHelper", "excel_id", "mapping tag", "templateSheet", "multi-sheet template", "export excel from template"; Vietnamese triggers "xuất excel theo template", "in excel", "tạo template excel", "làm report excel", "in nhiều sheet", "sheet tổng hợp", "mỗi sheet một design", "tag không đổ dữ liệu", "nhúng logo/QR vào excel", "setup excel library trên BAS", "gắn nút Print Excel". For OData service definition/binding use odata; for RAP BO modeling use rap; for generic ABAP SQL use abap-sql-amdp.
---

# Z_EXCEL_LIBRARY — Excel Export from Template

Client-side templating engine. The browser downloads a registered `.xlsx` template, merges a JSON payload produced by an ABAP RAP action into it, and saves the result locally. **The SAP backend never writes an Excel file** — it only returns JSON + a template id.

Everything in this skill is verified against live source: ABAP package `Z_EXCEL_LIBRARY` on bmw-dev and the UI5 library source `ExcelExportHelper.js` / `PrintExcelHandler.js`. Where a statement is inference, it is marked `[unverified]`.

## 1. Runtime flow

```
User ticks rows → presses "Print Excel" (custom action on the table toolbar)
  → PrintExcelHandler.onPrintExcelPress
      1. resolves App Component → config, first hit wins:
           a. manifest  sap.ui5/config/zExcelExport          (optional overrides)
           b. <namespace>/ext/controller/ExcelConfig.js     (legacy, used as-is)
           c. nothing → zero-config defaults, action name "printExcel"
      2. collects key fields of selected rows → selected_keys = JSON array of key objects
      3. actionPath = config.actionPath if given (legacy: not pre-checked, diagnosed on failure)
         else derived: /<EntitySet of the table binding>/<$EntityContainer namespace>.<actionName>(...)
         and checked against $metadata — missing action → toast listing the service's actions
         POST OData action at that path
          ↓  ABAP: static action printExcel
             parameter ZABS_EX_LIB_ACTION_INPUT ( selected_keys, app_id, custom_param )
             result [1] ZABS_EX_LIB_ACTION_RETURN ( excel_id, filename, json_content )
      4. GET /sap/bc/http/sap/zib_ex_lib_template_content?excel_id=<excel_id>
         → latest version of the .xlsx from ZTB_EX_LIB_I
      5. ExcelExportHelper.generateExcel( excel_id, JSON.parse(json_content), filename )
         → for each element of the JSON array: resolve its master sheet (element.templateSheet
           by NAME, else the first sheet), clone it, resolve tags, copy that master's sheet-level
           print settings → then delete EVERY template sheet, save file
```

Three components, three owners:

| Component | Object | Who touches it |
|---|---|---|
| Template store + upload app | `ZTB_EX_LIB_H` / `ZTB_EX_LIB_I`, Fiori app on `ZUI_EX_LIB_O4` | BA / key user uploads the `.xlsx`, versioned per `excel_id` |
| Template delivery endpoint | HTTP service `ZIB_EX_LIB_TEMPLATE_CONTENT` (class `ZCL_IB_EX_LIB_TEMPLATE_CONTENT`) | nobody — fixed framework code |
| Rendering engine | UI5 library `z.custom.excel.lib` (`ExcelExportHelper`, `PrintExcelHandler`) | nobody — fixed framework code |

**Never modify the three framework pieces.** A new report = one ABAP action named `printExcel` + one template + two fixed manifest entries (library dependency, custom action `press`) — no `ExcelConfig.js`, nothing renamed per app (`references/fiori-setup.md`).

> Zero-config needs the library version whose `PrintExcelHandler.js` resolves config as in step 1 (source of truth: BMW repo `bmw.core.zex_lib_core`, `DEFAULT_ACTION_NAME = "printExcel"`). A system still running an older `ZEX_LIB_CORE` needs `ExcelConfig.js` with `actionPath` — check what is deployed before promising the 2-step setup.

## 2. The JSON contract (the one thing both sides must agree on)

`json_content` is the serialization of `zif_ex_lib_types=>tt_sheets`:

```abap
TYPES: BEGIN OF ty_sheet,
         sheet_name     TYPE zde_ex_lib_sheetname,
         template_sheet TYPE zde_ex_lib_sheetname,   " optional → ${templateSheet}
         data           TYPE REF TO data,   " any structure, becomes the sheet's tag namespace
       END OF ty_sheet,
       tt_sheets TYPE STANDARD TABLE OF ty_sheet WITH DEFAULT KEY.
```

Serialized with the Z_API_FWK utility `zcl_api_fwk=>abap_to_json( ia_abap = lt_sheets iv_mapping_camel = abap_true )` (XCO JSON under the hood — see `[Skill: z-api-fwk]`), so the payload is:

```json
[ { "sheetName": "Order_SO0001", "templateSheet": "TPL_TRANSACTION",
    "data": { "soId": "SO0001", "logo": "data:image/png;base64,...",
              "items": [ { "matId": "M1", "quantity": 3 } ] } },
  { "sheetName": "BAO_CAO_TONG_HOP", "templateSheet": "TPL_SUMMARY",
    "data": { "reportTitle": "...", "lines": [ { "rowType": "GROUP" } ] } } ]
```

Rules that follow directly from the engine source:

- One array element = one output sheet, and **array order = sheet order** in the output file. A summary sheet is simply the last element.
- `templateSheet` picks that sheet's master **by name**. Absent, `null` or `""` → the template's first sheet (the pre-multi-template behaviour, unchanged). A name that matches no sheet in the template file **aborts the whole export** with `Không tìm thấy sheet mẫu "<name>" trong file template.` — no partial file is produced.
- **Every sheet in the template file is a master and every one of them is deleted from the result.** There is no way to ship a static sheet through: a sheet that must survive has to be declared as its own array element.
- Each element's `data` is an independent namespace — **nothing is inherited** between sheets. Shared header fields (logo, company block, printed by/at) must be repeated in every sheet's structure.
- `iv_mapping_camel = abap_true` applies XCO's `underscore_to_camel_case`, so `mat_id` → `matId` and `template_sheet` → `templateSheet`. **Tag names in the template are the camelCase names**, not the ABAP field names.
- XCO emits **every** component, including initial ones — `abap_to_json` has no `compress` equivalent. An initial `string` arrives as `""` and renders as an empty cell, but an initial numeric field arrives as `0` and **prints `0`, not blank**. Decide per field: either it is always filled, or the template must tolerate a zero.
- A tag whose field is absent from the payload resolves to empty and the tag is removed — that is intended behaviour, not an error.
- Tag names must match `[a-zA-Z0-9_]+`. No dots, no nesting: `${header.soId}` never resolves. Flatten everything into the sheet's `data` structure.
- `sheetName` ≤ 31 chars and must not contain `[ ] : * ? / \` — ExcelJS throws otherwise.

> Migrating from `/ui2/cl_json=>serialize( ... compress = abap_true pretty_name = camel_case )`: the JSON shape is identical, the two deltas are the initial-field behaviour above and `[unverified]` XCO's handling of the `data TYPE REF TO data` component of `ty_sheet` — `/ui2/cl_json` dereferences it, XCO's `from_abap` has not been confirmed to. Verify the first export end-to-end (a real file with real values) before relying on it, and keep `/ui2/cl_json=>serialize` as the fallback if the `data` node comes out empty.

## 3. What to read next

| Task | Read |
|---|---|
| Write / fix the ABAP `printExcel` action | `references/abap-action-cookbook.md` |
| Author or generate the `.xlsx` template | `references/template-builder.md` (how to build it with openpyxl) + `references/tag-reference.md` (the grammar) |
| Understand exactly how a tag behaves | `references/tag-reference.md` — authoritative, derived from `ExcelExportHelper.js` |
| Wire the Fiori app | `references/fiori-setup.md` — instructions for the Fiori developer, no coding done here |
| A tag did not render / file is wrong | `references/troubleshooting.md` |

Sample assets in `references/assets/`: three real templates (`sale_order_styled.xlsx`, `material_report_styled.xlsx`, `store_revenue_tmp.xlsx`), the reference ABAP action (`printexcel_sample.abap`), and two Python tools (`build_template.py`, `verify_template.py`).

## 4. Hard limits (check these before designing anything)

| Limit | Value | Source |
|---|---|---|
| `excel_id` length | **12 chars**, `abap.char(12)` | `ZTB_EX_LIB_I`, `ZABS_EX_LIB_ACTION_RETURN` |
| `filename` length | 255 | `ZABS_EX_LIB_ACTION_RETURN` |
| Item arrays per sheet | **exactly one** — `${table:a.x}` and `${table:b.y}` in the same sheet do NOT both work, and the loser loses its data **with no warning** | `ExcelExportHelper.js`: single `tableArrayName` variable |
| Template (master) sheets per file | unlimited; referenced **by name**, never by index | `fnResolveTemplate()` |
| Static (non-template) sheets in the template file | **none possible** — all masters are deleted | `ExcelExportHelper.js` cleanup loop |
| Sheet name | ≤31 chars (longer is truncated with a warning) | Excel / ExcelJS |
| Image formats | PNG / JPEG as data-URI or bare base64; the engine always declares `extension:'png'` | `ExcelExportHelper.js` |
| Barcode types | `barcode` (Code128), `qrcode`, `datamatrix` | `ExcelExportHelper.js` |
| Nesting depth of tags | flat only — one scalar namespace + one item array | tag regexes |

Need two independent item tables in one report → split them into **two sheets** (two elements of the sheets array). Since the multi-template update each of those sheets can have its **own master sheet**, so they no longer have to share a layout or an array name; folding them into one array distinguished by `rowType` remains the alternative when they belong on the same page.

## 5. Known gaps (not yet supported)

| Item | State |
|---|---|
| `autoFilter` | not copied from the template |
| Cross-sheet formulas | untested; expected to yield `#REF!` because every master sheet is deleted after rendering |
| A `json_content` that is not a JSON array | fails with `Worksheet name already exists: Sheet1` when the template's first sheet is literally named `Sheet1` — pre-existing bug, not fixed |
| Indentation written as leading spaces on a `${rowType:...}` row | trimmed away; use Excel's own alignment/indent instead |
| Aggregation | the engine never sums anything — **every total must be computed in ABAP** |

## 6. Governance floor

- New ABAP objects (action, behavior implementation, helper class): TR + Package required (rule §2); run `[Skill: activation-guard]` after every object change (rule §5).
- The template `.xlsx` is **data, not a transportable object** — it lives in `ZTB_EX_LIB_I` per client and is uploaded through the Fiori app. Moving a report to another system means re-uploading the template there. Say this explicitly when handing over.
- **ABAP and template ship together.** Adding a `template_sheet` value in the action without uploading a template file that contains that master sheet fails the export outright (`Không tìm thấy sheet mẫu`). Order of deployment: UI5 library → template upload → ABAP transport → test print.
- Business data stays read-only: the action only SELECTs. It is a `static action` with no `%key`, so it must never modify the BO.
