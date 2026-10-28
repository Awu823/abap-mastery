# Fiori Wiring — instructions for the Fiori developer (BAS)

Two fixed edits in the consuming Fiori Elements V4 List Report app, identical in every app — nothing is renamed per app. The coding happens in the UI5 project, outside this ABAP workspace.

Prerequisites (backend side, see `abap-action-cookbook.md`): a static action named exactly **`printExcel`** (case-sensitive in OData) on the entity the List Report table is bound to, exposed in the service. Verify once in the service `$metadata` (`<Action Name="printExcel">`) before touching BAS.

## 1. Declare the library dependency

`webapp/manifest.json` → `sap.ui5.dependencies.libs`:

```json
"z.custom.excel.lib": {}
```

## 2. Add the toolbar button

Create a custom action on the List Report table (Page Editor or by hand) and set its `press` to the library handler — this value is the only thing that matters:

```
z.custom.excel.lib.PrintExcelHandler.onPrintExcelPress
```

By hand it lands in the ListReport target → `options.settings.controlConfiguration` → the table's existing `LineItem` key (keep its qualifier, e.g. `#Main`; do not add a second key):

```json
"@com.sap.vocabularies.UI.v1.LineItem": {
  "actions": {
    "zPrintExcel": {
      "press": "z.custom.excel.lib.PrintExcelHandler.onPrintExcelPress",
      "requiresSelection": true,
      "text": "Print Excel"
    }
  }
}
```

`requiresSelection: true` is a UX choice, not a technical one — the handler falls back to the table's currently loaded contexts when nothing is selected, and the ABAP action receives an empty `selected_keys`. Decide deliberately, because "nothing selected" usually means an unbounded read in the backend.

No `ExcelConfig.js` and no controller code. The handler derives the action path itself:

```
/<EntitySet>/<Namespace>.<actionName>(...)
  EntitySet  ← binding path of the first selected row (or the table's row binding)
  Namespace  ← $EntityContainer of the service metadata, minus ".Container"
  actionName ← "printExcel" unless overridden
```

## 3. Optional overrides — only when needed

`webapp/manifest.json` → `sap.ui5.config.zExcelExport` (read via `getManifestEntry`; takes precedence over `ExcelConfig.js`):

```json
"config": {
  "zExcelExport": { "actionName": "printExcel", "appId": "SO_PRINT", "customParam": "" }
}
```

| Field | Set it when |
|---|---|
| `actionName` | the backend action is not named `printExcel` (e.g. legacy `PrintExcel_by_ex_lib` on `YT1_R_MAT_REPORT`, which cannot be renamed because `PrintExcel` already exists there and BDEF names are case-insensitive) |
| `actionPath` | full manual path — skips derivation and the metadata pre-check; avoid unless derivation cannot work |
| `appId` | the ABAP action branches on `app_id` (template choice, layout) — passed through as `app_id`, default `""` |
| `customParam` | the backend needs a filter the selection cannot express — passed through as `custom_param` |
| `idProperty` | string or array to send non-key fields instead of the metadata `$Key` (default: read `$Key`, works for composite keys) |
| `excelId` | legacy fallback only; the backend's returned `excel_id` always wins |

## 4. Legacy apps (`ExcelConfig.js`)

Apps set up before zero-config keep working unchanged: if `<namespace>/ext/controller/ExcelConfig.js` exists and the manifest has no `zExcelExport` entry, the handler uses that object **as-is** (no defaults merged, `actionPath` not pre-checked; on failure the console lists the service's actions).

Migrating a legacy app to zero-config: confirm the backend action is named `printExcel` (on bmw-dev 11 of 12 Excel actions already are — rule out `YT1_R_MAT_REPORT`), delete `webapp/ext/controller/ExcelConfig.js`, redeploy the app. Renaming a backend action and redeploying the app must happen together — a stale `actionPath` in `ExcelConfig.js` breaks the button immediately.

Sample of the legacy file: `assets/ExcelConfig.sample.js`.

## What the handler sends

Key values are collected per selected row into `[{"<KeyProp>":"<value>"}, ...]` and JSON-stringified into `selected_keys`. Property names are the **OData property names of the projection**, so the ABAP structure passed to `parse_json_keys` must use matching component names.

## Verifying an export

Open the app, select rows, press the button, and watch the browser console (F12) — the library logs every phase:

```
🚀 [Excel Core] Khởi động xuất Excel cho App: <namespace>
🔍 [Excel Core] Dùng cấu hình manifest: /sap.ui5/config/zExcelExport      (or)
🔍 [Excel Core] Đang nạp động file cấu hình: <path>/ExcelConfig.js
ℹ️ [Excel Core] Không có ExcelConfig.js → tự suy ra cấu hình (action mặc định: printExcel)
🔗 [Excel Core] Action Path: /<EntitySet>/<Namespace>.printExcel(...)
⏱ [Excel Core] Thời gian ABAP Backend xử lý: 1092.35 ms
📊 [Metrics] Input JSON Size: ~0.20 MB
📥 [1/4] Thời gian tải Template từ Backend: 191.64 ms
⚙ [2/4] Thời gian nạp Workbook ExcelJS: 54.60 ms
📄 [3/4] Bắt đầu xử lý 1 Sheet(s)...
📦 [4/4] Thời gian đóng gói nhị phân & Tải file: 29.38 ms
✔ [Excel Library] THÀNH CÔNG RỰC RỠ! Đã xuất file: ...
```

A zero-config app also logs a 404 for `ExcelConfig.js` before the `ℹ️` line — expected, it is the legacy probe.

Which line is missing tells you which layer failed — see `troubleshooting.md`. The whole render is client-side, so a slow export is the browser's CPU/RAM, not the backend; the backend time is printed separately.
