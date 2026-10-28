# ABAP Backend Cookbook

Goal of the backend: turn the selected rows into **one JSON array of sheets** and name the template. Nothing else. No file is produced in ABAP.

## 1. Declare the static action (BDEF)

In the **interface** behavior definition of the BO whose list report carries the button:

```abap
static action printExcel parameter ZABS_EX_LIB_ACTION_INPUT
                         result [1] ZABS_EX_LIB_ACTION_RETURN;
```

In the **projection** behavior definition:

```abap
use action printExcel;
```

Rules:
- Name it exactly **`printExcel`** — the project standard and the library's zero-config default. OData action names are case-sensitive, so `PrintExcel` does not match; any other name forces the Fiori app to set `actionName` (see `fiori-setup.md`). BDEF names are case-insensitive, so `printExcel` cannot coexist with an existing `PrintExcel` action on the same BO.
- Declare it on the entity the List Report table is bound to — the frontend derives the entity set from the table binding.
- `static`, not instance-bound. The frontend calls it unbound and passes the keys itself as a JSON string.
- **No `@UI` annotation** on the action. The button is a Fiori custom action pointing at the library handler, not a generated action button. Annotating it produces a second, broken button.
- The two abstract entities are framework-owned — never copy or redefine them:

```abap
define abstract entity ZABS_EX_LIB_ACTION_INPUT {
  selected_keys : abap.string(0);   // JSON array of key objects, or empty
  app_id        : abap.char(30);
  custom_param  : abap.string(0);
}
define abstract entity ZABS_EX_LIB_ACTION_RETURN {
  excel_id     : abap.char(12);     // registered template id — 12 chars max
  filename     : abap.char(255);
  json_content : abap.string;
}
```

Handler declaration in the behavior pool's local handler class:

```abap
METHODS printexcel FOR MODIFY IMPORTING keys FOR ACTION r_order_h~printExcel RESULT result.
```

## 2. Parse the selected keys

`selected_keys` arrives as a JSON array of objects whose property names are the **OData key property names** of the projection (e.g. `[{"SoId":"SO0001"},{"SoId":"SO0002"}]`), unless the app overrides `idProperty` (manifest `sap.ui5/config/zExcelExport`, or a legacy `ExcelConfig.js`).

```abap
READ TABLE keys INTO DATA(ls_key) INDEX 1.
DATA(lv_keys_string) = ls_key-%param-selected_keys.

TYPES: BEGIN OF ty_so,
         soid TYPE yt1_de_so_id,        " component name must match the JSON property (case-insensitive)
       END OF ty_so.
DATA lt_filter TYPE TABLE OF ty_so.

zcl_ex_lib_utils=>parse_json_keys( EXPORTING iv_json_string = lv_keys_string
                                   CHANGING  ct_keys        = lt_filter ).
```

`parse_json_keys` is `xco_cp_json` under the hood and **swallows malformed JSON**: `ct_keys` comes back empty and the caller cannot tell that apart from "nothing selected". Treat empty as "export everything" only if that is the intended behaviour; otherwise guard explicitly.

Composite keys work the same way — declare all key components in `ty_*`.

## 3. Read the data

Read through CDS views, never physical tables (rule §3). Use one round trip per level, then assemble in memory:

```abap
IF lt_filter IS NOT INITIAL.
  SELECT * FROM yt1_r_order_h FOR ALL ENTRIES IN @lt_filter
    WHERE soid = @lt_filter-soid INTO TABLE @DATA(lt_head).
  SELECT * FROM yt1_r_order_i FOR ALL ENTRIES IN @lt_filter
    WHERE soid = @lt_filter-soid INTO TABLE @DATA(lt_item).
ELSE.
  SELECT * FROM yt1_r_order_h INTO TABLE @lt_head.
  SELECT * FROM yt1_r_order_i INTO TABLE @lt_item.
ENDIF.
```

`FOR ALL ENTRIES` on an empty table would read everything — that is why the `IS NOT INITIAL` guard is mandatory, and why an unguarded "export all" branch should be a conscious decision (it is an unbounded read).

## 4. Shape the payload

One local structure per sheet; the item table is a **component of it**, and its component name is the array name used in the template's `${table:<array>.<field>}` tags.

```abap
TYPES: BEGIN OF ty_item,
         mat_id     TYPE string,
         quantity   TYPE f,
         net_amount TYPE f,
       END OF ty_item,
       tt_items TYPE TABLE OF ty_item WITH DEFAULT KEY.

TYPES: BEGIN OF ty_sheet_data,
         logo         TYPE string,
         company_name TYPE string,
         printed_date TYPE string,
         so_id        TYPE string,
         total_price  TYPE f,
         items        TYPE tt_items,     " → ${table:items.matId}
       END OF ty_sheet_data.
```

Typing rules that matter downstream:

| Intent in the template | ABAP type | Why |
|---|---|---|
| number the template formats (amount, qty) | `f` / `p` / `decfloat34` | stays numeric in JSON → cell keeps its number format |
| code with a leading zero (status `02`, company code, tax id) | `string`, keep the zero | the engine keeps values matching `^0[0-9]` as text — do **not** strip the zero in ABAP |
| other identifier that must stay text | `string`, and make it non-numeric (prefix) or accept coercion | the engine coerces a numeric-looking whole-cell value with `Number()` |
| date / time | `string`, pre-formatted | no date type survives the JSON round trip |
| image / logo | `string` data URI | see below |

Header fields shared by every sheet (logo, company block, printed by/at) are repeated in each sheet's structure — there is no global namespace.

```abap
ls_data-logo         = zcl_image_lib=>get_latest_image_base64( iv_image_id = 'this_is_logo' ).
ls_data-printed_user = sy-uname.
ls_data-printed_date = |{ cl_abap_context_info=>get_system_date( ) DATE = USER }|.
ls_data-printed_time = |{ cl_abap_context_info=>get_system_time( ) TIME = USER }|.
```

`zcl_image_lib=>get_latest_image_base64` returns the latest version of an image from `ZI_IMG_I` already wrapped as `data:<mime>;base64,<...>`, and returns an empty string on any failure — a missing logo silently yields a blank cell, so verify it once during testing rather than trusting it.

### Multiple row layouts

When the template uses `${rowType:L1}` variants, emit **one flat array** and carry the variant on each item:

```abap
TYPES: BEGIN OF ty_item,
         row_type   TYPE string,    " → item.row_type, matched against the template's ${rowType:X}
         mat_name   TYPE string,
         amount     TYPE f,
       END OF ty_item.
```

Build the rows in display order (group header, details, subtotal, …) — the engine renders the array in sequence and does no sorting or grouping. The same applies to `|merge` columns: equal values must already be adjacent.

### Sheets with different layouts and different structures

Since `ty_sheet-template_sheet` exists, one export can mix document types. Declare **one local structure per master** — they share no fields and nothing is inherited:

```abap
" sheet type A — one per document, master TPL_TRANSACTION
TYPES: BEGIN OF ty_sheet_data,
         company_name TYPE string,
         so_id        TYPE string,
         items        TYPE tt_items,        " → ${table:items.matId}
       END OF ty_sheet_data.

" sheet type B — one summary page, master TPL_SUMMARY
TYPES: BEGIN OF ty_sum_line,
         row_type TYPE string,              " GROUP / ITEM / TOTAL variants in TPL_SUMMARY
         title    TYPE string,
         partner  TYPE string,
         amount   TYPE p LENGTH 15 DECIMALS 2,
         currency TYPE string,
       END OF ty_sum_line,
       tt_sum_lines TYPE TABLE OF ty_sum_line WITH DEFAULT KEY.

TYPES: BEGIN OF ty_summary_data,
         report_title   TYPE string,
         doc_count      TYPE i,
         amount_total   TYPE p LENGTH 15 DECIMALS 2,
         lines          TYPE tt_sum_lines,  " → ${table:lines.title}
       END OF ty_summary_data.
```

Rules for the summary block:

- **The engine never aggregates.** Every count, subtotal and grand total is computed in ABAP before serialization.
- Emit group/detail/total rows in display order into one flat array, each carrying its `row_type` — same mechanism as above, just a second master.
- Mixing currencies in one total is a silent wrong number; either group by currency or guard it explicitly.
- Shared header fields (logo, printed by/at) must be repeated in the summary structure — there is no global namespace.
- Keeping the new blocks marked (`" [MULTI-TEMPLATE]`, `" [SUMMARY]`) makes the feature removable by deletion, which is how the reference implementation `YT1_BP_R_ORDER` is written.

## 5. Pack the sheets and return

```abap
DATA lt_sheets TYPE zif_ex_lib_types=>tt_sheets.

LOOP AT lt_head INTO DATA(ls_head).
  CLEAR ls_data.
  " ... fill ls_data, including ls_data-items ...
  APPEND VALUE #( sheet_name     = |Order_{ ls_head-soid }|  " <= 31 chars, no [ ] : * ? / \
                  template_sheet = 'TPL_TRANSACTION'         " master sheet BY NAME; omit → first sheet
                  data           = NEW ty_sheet_data( ls_data )
                ) TO lt_sheets.
ENDLOOP.

" optional extra page with its own layout and its own data structure —
" appended LAST because array order is sheet order
APPEND VALUE #( sheet_name     = 'BAO_CAO_TONG_HOP'
                template_sheet = 'TPL_SUMMARY'
                data           = NEW ty_summary_data( ls_summary )
              ) TO lt_sheets.

DATA(lv_json) = zcl_api_fwk=>abap_to_json( ia_abap          = lt_sheets
                                           iv_mapping_camel = abap_true ).

GET TIME STAMP FIELD DATA(lv_ts).

result = VALUE #( ( %cid                = ls_key-%cid
                    %param-excel_id     = 'SALE_ORDER'                 " registered id, max 12 chars
                    %param-filename     = |SaleOrder_{ lv_ts }.xlsx|
                    %param-json_content = lv_json ) ).
```

`zcl_api_fwk=>abap_to_json` is the shared Z_API_FWK utility (`CLASS-METHODS abap_to_json IMPORTING ia_abap TYPE any, iv_mapping_camel TYPE abap_bool DEFAULT abap_false RETURNING VALUE(rv_json) TYPE string`), implemented as `xco_cp_json=>data->from_abap( )` plus the `underscore_to_camel_case` transformation. Using it keeps this framework on the same JSON stack as the API framework — see `[Skill: z-api-fwk]`.

Non-negotiables:
- `iv_mapping_camel = abap_true` — the template's tag names are the camelCase ones.
- **XCO has no `compress`.** Every component is emitted, so an initial numeric field prints `0` instead of staying blank. If a cell must be empty when there is no value, type it as `string` and leave it initial, or do not place the tag at all.
- `%cid = ls_key-%cid`, otherwise the RAP response cannot be correlated and the frontend gets nothing.
- `excel_id` must exist in `ZTB_EX_LIB_H` / `ZTB_EX_LIB_I`, or step 4 of the flow returns HTTP 404 and the export dies with "Không thể tải Template".

## 6. Registering the template

`excel_id` is `char(12)`, the key of `ZTB_EX_LIB_H`; each upload adds a row to `ZTB_EX_LIB_I` with an incrementing `version`, and both the HTTP endpoint and any backend read take `MAX( version )`. Uploads happen through the Excel Library Fiori app (service binding `ZUI_EX_LIB_O4`) — do not INSERT into these tables from custom code.

The `.xlsx` lives in client-dependent table data, not in a transport. Promoting a report to QA/PROD means uploading the template there too; say so explicitly in any handover.

## 7. Checklist before claiming the backend is done

- [ ] Static action named exactly `printExcel`, on the entity the List Report table is bound to
- [ ] Static action declared in interface BDEF **and** `use action` in the projection BDEF, no `@UI` annotation
- [ ] `%cid` returned
- [ ] `excel_id` ≤ 12 chars and registered in the template app
- [ ] Sheet names ≤ 31 chars, no forbidden characters, unique per sheet
- [ ] Every `template_sheet` value exists as a sheet in the uploaded template file (a typo aborts the whole export)
- [ ] Sheet array built in the intended output order (summary page last)
- [ ] All totals computed in ABAP — the engine sums nothing
- [ ] Serialized with `zcl_api_fwk=>abap_to_json( ... iv_mapping_camel = abap_true )`
- [ ] Fields that must render blank are not numeric (XCO emits `0` for an initial number)
- [ ] First end-to-end export inspected — the `data` node is populated (XCO vs `REF TO data`, see SKILL.md §2)
- [ ] Item array component name == the array name in the template tags
- [ ] Every template tag has a matching JSON field (run `verify_template.py` against a serialized sample)
- [ ] Exactly one item array per sheet
- [ ] `[Skill: activation-guard]` run after each object change
