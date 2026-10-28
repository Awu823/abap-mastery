# Troubleshooting

Diagnose by layer first. The console log (F12) prints a line per phase; the **first missing line** names the failing layer.

| Last line seen | Failing layer |
|---|---|
| nothing at all | button not wired to `PrintExcelHandler.onPrintExcelPress`, or the library is not in `manifest.json` `libs` |
| toast `Service không có action 'printExcel'. Actions có sẵn: …` | zero-config could not find the action in `$metadata` — backend action missing, not exposed (`use action`), named differently (set `actionName` in `sap.ui5/config/zExcelExport`), or declared on another entity than the table's |
| toast `Lỗi thiết lập: Không xác định được Entity Set của bảng.` | zero-config found neither a selected row nor a table binding — no rows loaded; select a row or set `actionPath` |
| `🔗 Action Path: …` then `OData Action thất bại` | the action was called and failed in ABAP or on authorization — read the response in the Network tab; for a legacy `ExcelConfig.js` path the console also prints `Actions có trong service: …` to spot a wrong name |
| `🚀 Khởi động...` then `Thiếu file cấu hình` | old library version (no zero-config) — `ExcelConfig.js` missing/misplaced (`webapp/ext/controller/`); deploy the current `ZEX_LIB_CORE` or add the file |
| a legacy app suddenly calls `printExcel` instead of its own action | its `ExcelConfig.js` failed to load (syntax error, wrong folder) and the handler fell back to zero-config — the `ℹ️ Không có ExcelConfig.js` console line carries the load error |
| `📥 [1/4] tải Template` throws | `excel_id` not registered, or HTTP 404 from `zib_ex_lib_template_content` |
| `⚙️ [2/4] nạp Workbook` throws | the stored file is not a valid `.xlsx` |
| everything logs, file downloads, content wrong | a tag/payload mismatch — the table below |

## Symptom → cause

| Symptom | Cause | Fix |
|---|---|---|
| `${something}` printed literally in the output | tag name contains an illegal character (`.`, `-`, space, diacritic) so no regex matched | tag names are `[a-zA-Z0-9_]+`; flatten nested paths in ABAP |
| Cell is empty where a value was expected | the field is absent from the payload, or was never filled | fill it; a genuinely empty value rendering empty is correct behaviour |
| Cell shows `0` where blank was expected | `abap_to_json` (XCO) emits every component — an initial numeric field becomes `0` | type the field as `string`, or accept the zero and format it (`#,##0;;""`) |
| Whole sheet renders empty although the action returned JSON | `[unverified]` XCO may not dereference `ty_sheet-data` (`REF TO data`) — check whether the `data` node in `json_content` is populated | if it is empty, serialize that call with `/ui2/cl_json=>serialize( ... compress = abap_true pretty_name = camel_case )` instead |
| Export dies with `Không tìm thấy sheet mẫu "X" trong file template` | the action sent `template_sheet = 'X'` but the uploaded `.xlsx` has no sheet named `X` — typo, or the template was never re-uploaded after adding the master | fix the name or upload the template that contains it; no partial file is produced |
| A sheet that was in the template file is missing from the output | **every** sheet of the template file is a master and is deleted after rendering | declare it as its own payload entry with its own `templateSheet` |
| Sheets come out in the wrong order | array order is sheet order | reorder the `APPEND`s in ABAP (summary last) |
| One master's tags render with another sheet's data | the entry's `templateSheet` is missing/empty, so it fell back to the **first** sheet of the template file | set `template_sheet` explicitly on every entry once the file has more than one master |
| Cell shows a number where an ID was expected, leading zeros gone | whole-cell scalar tag + numeric-looking value → `Number()` coercion. Values matching `^0[0-9]` (`02`, `0101234567`) are kept as text since the leading-zero fix — if one is still mangled, ABAP stripped the zero before serialization | check the ABAP value first; otherwise keep static text in the cell (`SO ${soId}`), send a non-numeric value, or accept it and set a number format |
| Output prints portrait / with gridlines although the template is landscape | sheet-level print settings were not copied before commit `35ce9e5` | deploy the current UI5 library; `pageSetup`, `headerFooter`, `views` and `properties` are copied per master afterwards |
| Every output sheet is hidden | not caused by this engine — `state` is deliberately not copied from the master | look elsewhere (the produced file was post-processed, or the viewer) |
| Content at the bottom of the sheet is cut off in print preview | `printArea` is expanded by the number of rows the table added — if content moved further than that, the master's print area was too tight | widen `print_area` in the template |
| `autoFilter` from the template is gone | not copied — known gap | re-apply it manually, or drop the requirement |
| Export fails with `Worksheet name already exists: Sheet1` | `json_content` is not a JSON array and the template's first sheet is literally named `Sheet1` | return a proper array from the action; renaming the master away from `Sheet1` also avoids it |
| Indentation on a `${rowType:...}` row disappeared | leading spaces are trimmed when the tag is stripped | use Excel's alignment/indent instead of spaces |
| Totals are wrong / missing on a summary sheet | the engine never aggregates | compute every total in ABAP |
| Cell shows text where a number was expected, right-align/format lost | ABAP sent a formatted string, or the tag was embedded in other text | send a numeric ABAP type and make the tag the entire cell content |
| Date shows as a serial number or as raw `20260918` | dates are not converted by the engine | format in ABAP: `\|{ lv_date DATE = USER }\|` |
| Table does not repeat, only one row | `${table:...}` array name ≠ the payload's array field name, or the array is not a JSON array | align the ABAP component name with the tag's array name |
| Two tables in one sheet, one of them filled from the wrong data | the engine keeps a single array name per sheet — the last one scanned wins, the other loses its data with **no warning** | split into two sheets, each with its own `templateSheet` master, or one array with `row_type` |
| Some items silently missing from the output | their `row_type` matches no `${rowType:}` variant and there is no DEFAULT row | add a DEFAULT template row or fix the `row_type` values |
| Subtotal/group rows render with detail-row styling | the item's `row_type` is initial; `""` is falsy in `item.row_type \|\| item.rowType \|\| "DEFAULT"` → falls back to DEFAULT | set `row_type` explicitly on every item that needs a variant |
| `|merge` produced no merges | equal values are not adjacent | sort the array in ABAP; the engine never sorts |
| Borders missing on merged cells after expansion | only the merge master was styled in the template | style every cell of the range (`style_span()` in `build_template.py`) |
| A blank row disappeared from the middle of the table | it sat inside the template block and was deleted with it | move spacers outside the block |
| Logo/QR is tiny, one cell wide | the tag cell was not merged | merge the box, put the tag in its top-left cell |
| Logo missing entirely | `zcl_image_lib=>get_latest_image_base64` returned `''` — wrong `image_id`, no row in `ZI_IMG_I`, or an exception it swallowed | check the image id and that a version exists |
| QR/barcode missing, no error on screen | bwip-js threw; the engine logs to console and continues | read the `❌ [Barcode Generation Error]` line — usually an empty or over-long value |
| Rows below the table did not move down | they were inside the template block, or the array was empty | inspect the block boundaries with `verify_template.py` |
| Conditional formatting stops partway down the table | the rule's range did not overlap the template block, so it was not expanded | define the rule over the template rows themselves |
| Export dies on a large selection | the whole render is client-side; RAM is the limit (the log prints input JSON size and heap usage) | reduce the selection, or split into more sheets |
| HTTP 400 `Thiếu tham số excel_id` | `excel_id` came back empty from the action | the action must always set `%param-excel_id` |
| Nothing happens, no file, no error | `%cid` not returned by the action, so RAP could not correlate the response | `%cid = ls_key-%cid` |
| Right template, stale layout | a newer version was uploaded to a different `excel_id`, or the browser cached the fetch | check `MAX( version )` in `ZTB_EX_LIB_I` for that id; hard-reload |
| Works in DEV, empty template in QA/PROD | templates are client-dependent table data, not transported | upload the `.xlsx` in the target system |

## Reading the template store directly

```abap
SELECT excel_id, version, file_name, file_size, created_by, created_at
  FROM zi_tb_ex_lib_i
  WHERE excelid = @lv_id
  ORDER BY version DESCENDING
  INTO TABLE @DATA(lt_versions).
```

The endpoint serves `MAX( version )` — if that is not the file you expect, the upload landed under a different `excel_id`.
