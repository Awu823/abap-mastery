# Z_API_FWK — Outbound API Guide (SAP → partner)

Everything needed to call an external system through the framework. Source: live `Z_API_FWK` package source (`abap_bmw_dev`, Jul 2026).

## Runtime flow

```
Business code (RAP action / report / batch)
  → NEW zcl_api_fwk( )->execute_api( iv_api_id = '<API_ID>' ... )
      1. SELECT config header + headers(_I) + params(_P) by api_id
         (not found → zcx_api_fwk=>config_not_found; inactive → config_inactive)
      2. destination = cl_http_destination_provider=>create_by_comm_arrangement(
           comm_scenario / service_id / comm_system_id from config )     " init_error on failure
      3. build request: URI, method, query params, headers, payload
      4. lo_client->execute( )                                            " execute_error on failure (log saved first)
      5. 2xx + json → deserialize response into c_response_data
      6. save_log if log_enable ≠ space; client closed on all paths
```

## Prerequisites (once per target system)

1. Communication scenario + system + arrangement for the target endpoint — [Skill: btp-abap-environment].
2. Config row in Fiori app **ZAPI_FWK_CONFIG**: `api_id`, `direction = 'O'`, `active = X`, `comm_scenario`, `service_id`, `comm_system_id`, `method`, `content_type`, `mapping_camel`, `uri_path`, `log_enable`, `api_group`. Optional static HTTP headers → Headers item table; static URL params → Params item table.

Note: `execute_api` does not enforce `direction` (only inbound checks it) — set `'O'` anyway for correct log semantics. `timeout`/`batch_size` exist in the config table but are NOT consumed by `execute_api` (verified Jul 2026); [Inference] they are for caller-side use.

## Call pattern A — typed JSON request/response (the normal case)

```abap
DATA ls_request  TYPE zs_my_request.     " ABAP structure, underscore field names
DATA ls_response TYPE zs_my_response.

TRY.
    NEW zcl_api_fwk( )->execute_api(
      EXPORTING
        iv_api_id              = 'MY_API_ID'
        i_request_payload_data = ls_request       " serialized to JSON per config (camelCase if mapping_camel)
        iv_transaction_number  = |{ lv_document_number }|   " → log trans_num; ALWAYS pass the business key
      IMPORTING
        es_logger              = DATA(ls_logger)  " full request/response evidence (see below)
      CHANGING
        c_response_data        = ls_response ).   " filled only on 2xx + json config (camel→underscore)

  CATCH zcx_api_fwk INTO DATA(lx_api).
    " textids: config_not_found | config_inactive | init_error | execute_error
    " lx_api->previous holds the original HTTP/destination exception; failed call already logged
ENDTRY.
```

## Call pattern B — dynamic URI / headers / params / raw payload

```abap
NEW zcl_api_fwk( )->execute_api(
  EXPORTING
    iv_api_id                = 'MY_API_ID'
    is_dynamic_request_value = VALUE zif_api_fwk_types=>ty_dynamic_request(
        uri_path        = |/orders/{ lv_order_id }/confirm|          " overrides config uri_path
        request_payload = lv_raw_json                                 " pre-built string payload
        header          = VALUE #( ( name = 'x-correlation-id' value = lv_corr ) )
        param           = VALUE #( ( name = 'lang' value = 'EN' ) ) )
    iv_transaction_number    = lv_trans
  IMPORTING
    es_logger                = DATA(ls_logger) ).
```

## Call pattern C — multi-call same-session (`keep_session`, added Aug 2026)

One HTTP session across several `execute_api` calls — required whenever call N+1 must reuse call N's session cookies. Canonical case: **CSRF-protected POST** (fetch token with GET, POST with it) — a token is only valid inside the cookie session that fetched it, so two independent `execute_api` calls get 403. With a static config method this needs **TWO config rows**, e.g. `INTERNAL_GET_CSRF` (GET) + `INTERNAL_SALE_ORDER` (POST), both with the SAME `comm_scenario`/`service_id`/`comm_system_id`. Since Oct 2026 a single row with `method = DYNAMIC` can serve the whole chain instead — see pattern D below.

```abap
DATA(lo_fwk) = NEW zcl_api_fwk( ).          " ONE instance for the whole chain

" call 1 — keep_session: engine sets accept_cookies( abap_true ) and keeps
" the client open on this instance instead of closing it
lo_fwk->execute_api(
  EXPORTING iv_api_id                = 'INTERNAL_GET_CSRF'
            is_dynamic_request_value = VALUE #(
              uri_path     = '/sap/opu/odata/sap/API_SALES_ORDER_SRV/$metadata'
              header       = VALUE #( ( name = 'x-csrf-token' value = 'Fetch' ) )
              keep_session = abap_true )
            iv_transaction_number    = lv_trans
  IMPORTING es_logger                = DATA(ls_fetch) ).

DATA lv_token TYPE string.   " response header names: compare case-insensitively
LOOP AT ls_fetch-response-header INTO DATA(ls_h).
  IF to_lower( ls_h-name ) = 'x-csrf-token'.
    lv_token = ls_h-value.
    EXIT.
  ENDIF.
ENDLOOP.
" guard before POSTing: non-2xx, empty token, or literal 'Fetch' = no session

" call 2 — SAME instance reuses the kept client/cookies; flag left initial
" -> engine closes the session after this call
lo_fwk->execute_api(
  EXPORTING iv_api_id                = 'INTERNAL_SALE_ORDER'
            is_dynamic_request_value = VALUE #(
              uri_path        = '/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder'
              request_payload = lv_json
              header          = VALUE #( ( name = 'x-csrf-token' value = lv_token ) ) )
            iv_transaction_number    = lv_trans
  IMPORTING es_logger                = DATA(ls_post) ).
```

Engine rules (verified against source, Aug 2026):
- `keep_session = abap_true` → `accept_cookies( abap_true )` at client creation; after the call the client is stored on the INSTANCE (`mo_session_client`) instead of closed. The next `execute_api` on the SAME instance reuses it and skips destination creation.
- On reuse the engine deletes every header the previous call set and clears the query string before applying the new call's config/dynamic values — no cross-call leakage.
- A kept session must stay on ONE destination: a follow-up api_id with a different comm triple → `init_error`.
- ANY error path (config not found/inactive, init failure, HTTP execute failure) closes and clears the kept session.
- The chain's LAST call leaves the flag initial → engine closes the client. Aborting mid-chain (e.g. no usable token) abandons the kept client until the ABAP session ends — accepted rare-path leak; don't abort chains inside long-running loops.
- Each call stays one `execute_api` = one log row per call, unchanged. Recommend `log_enable = 'B'` on the fetch api_id — under full logging a `$metadata` body is logged for real (up to the 1 MB cap).
- Working reference: `ZCL_API_IB_CREATE_SO_DEMAND->CALL_SO_API_VIA_FWK` (package `Z_CUSTOMAPI_CREATE_SO`).

## Call pattern D — config `method = DYNAMIC`, verb chosen per call (added Oct 2026)

Set the config row's method to `DYNAMIC` (dropdown entry "Dynamic (set by caller)") when one API ID must serve several verbs — e.g. the CSRF chain above with ONE config row, or a REST resource that is read with GET and updated with PATCH. The caller then passes the verb in `is_dynamic_request_value-method`; it is **mandatory** and must be one of `GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS` (case-insensitive, blanks condensed).

```abap
DATA(lo_fwk) = NEW zcl_api_fwk( ).

lo_fwk->execute_api(                                   " call 1: GET on the same api_id
  EXPORTING iv_api_id                = 'S4_SALES_ORDER'   " config method = DYNAMIC
            is_dynamic_request_value = VALUE #(
              method       = 'GET'
              uri_path     = '/sap/opu/odata/sap/API_SALES_ORDER_SRV/$metadata'
              header       = VALUE #( ( name = 'x-csrf-token' value = 'Fetch' ) )
              keep_session = abap_true )
  IMPORTING es_logger                = DATA(ls_fetch) ).

lo_fwk->execute_api(                                   " call 2: POST, same row, same session
  EXPORTING iv_api_id                = 'S4_SALES_ORDER'
            is_dynamic_request_value = VALUE #(
              method          = 'POST'
              uri_path        = '/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder'
              request_payload = lv_json
              header          = VALUE #( ( name = 'x-csrf-token' value = lv_token ) ) )
  IMPORTING es_logger                = DATA(ls_post) ).
```

Engine rules (verified against source + unit tests `ltc_resolve_http_method`, Oct 2026):
- Resolution happens right after the `active` check, BEFORE the destination/client is created: a missing or invalid caller verb raises `zcx_api_fwk` textid `method_required` (`ZMC_API_FWK 015`, `api_id` filled) — no HTTP call, **no log row**, a kept session is closed.
- Config wins: for any config method other than `DYNAMIC`, `is_dynamic_request_value-method` is ignored (100% backward compatible). An unknown static config value still falls back to `GET` as before.
- The resolved upper-case verb is what the log's `method` column shows.
- `ZVH_HTTP_METHOD` is a literal union — `OPTIONS` is accepted by the engine but not offered in the dropdown.

## Call pattern E — config `content_type = DYNAMIC`, content type chosen per call (added Oct 2026)

Set the config row's content type to `DYNAMIC` (dropdown entry "Dynamic (set by caller)") when one API ID must send bodies of different content types — the canonical case is an OData V4 **`$batch`** (`multipart/mixed; boundary=…`, a different boundary per call) behind a CSRF fetch, on one `DYNAMIC`-method row. The caller then passes the content type in `is_dynamic_request_value-content_type`; it is **mandatory whenever the call carries a body** and may stay empty on a bodiless call (the HEAD fetch).

| Config row (`INTERNAL_PROJDMND`-style) | Value | Why |
|---|---|---|
| `method` | `DYNAMIC` | HEAD (csrf) + POST on one row — pattern D |
| `content_type` | `DYNAMIC` | the caller decides per call; a static value (e.g. `application/json`) would win over the caller. Never pick a binary-list entry (pdf / xlsx) for a text body |
| `mapping_camel` | blank | only read by the `i_request_payload_data` / `c_response_data` XCO branches — both unused here |
| `uri_path` | empty | passed per call |

```abap
DATA(lo_fwk) = NEW zcl_api_fwk( ).

lo_fwk->execute_api(                                   " call 1: CSRF fetch, no body, no content_type
  EXPORTING iv_api_id                = 'INTERNAL_PROJDMND'
            is_dynamic_request_value = VALUE #(
              method       = zcl_api_fwk=>co_method-head
              uri_path     = lv_service_root               " e.g. /sap/opu/odata4/sap/<srv>/srvd_a2x/sap/<srv>/0001/ - confirm against $metadata
              header       = VALUE #( ( name = 'x-csrf-token' value = 'Fetch' ) )
              keep_session = abap_true )
  IMPORTING es_logger                = DATA(ls_fetch) ).
" ... take lv_token from ls_fetch-response-header (compare names case-insensitively) ...

lo_fwk->execute_api(                                   " call 2: the batch, same row, same session
  EXPORTING iv_api_id                = 'INTERNAL_PROJDMND'
            is_dynamic_request_value = VALUE #(
              method          = zcl_api_fwk=>co_method-post
              uri_path        = |{ lv_service_root }$batch|
              content_type    = |multipart/mixed; boundary={ lv_boundary }|
              request_payload = lv_batch_body             " pre-built multipart string, CRLF line ends
              header          = VALUE #( ( name = 'x-csrf-token' value = lv_token ) ) )
  IMPORTING es_logger                = DATA(ls_batch) ).
" ls_batch-response-payload = the multipart response text, untouched - parse it yourself.
" Do NOT pass c_response_data here (that would run the JSON deserializer on it).
```

Engine rules (verified against source + unit tests `ltc_resolve_content_type`, `ltc_merge_request_headers`, Oct 2026):
- Resolution happens in step 1c, right after the method and BEFORE the destination/client is created. Config wins: for any static config value the caller's `content_type` is ignored (100% backward compatible). Config `DYNAMIC` (any letter case) → the caller's value, condensed.
- `DYNAMIC` + body (`i_request_payload_data` or `request_payload` filled) + empty caller value → `zcx_api_fwk` textid `content_type_required` (`ZMC_API_FWK 016`, `api_id` filled) — no HTTP call, **no log row**, a kept session is closed. `DYNAMIC` + no body + empty value → no header, nothing raised.
- The resolved content type drives everything the config value used to drive: the `content-type` request header, the XCO serialisation of `i_request_payload_data` (value contains `json`), the binary list (`set_binary`) and the JSON deserialisation into `c_response_data`. So `DYNAMIC` + `application/json` + an ABAP structure in `i_request_payload_data` serialises exactly like a static json row.
- Header merge order: caller headers, then ALL config `_I` rows, then — only when none of them is named `content-type` in **any letter case** and the resolved value is not empty — the resolved value as header `content-type`. A caller `content-type` / `Content-Type` header therefore still wins; sending one is no longer necessary. Before Oct 2026 only the exact lower-case spelling suppressed the config value.
- The body goes out byte-for-byte ONLY via `is_dynamic_request_value-request_payload`. A string handed to `i_request_payload_data` is XCO-serialised when the resolved content type contains `json` (it becomes a quoted JSON string) and templated otherwise — never use it for a ready-made body.
- `multipart/mixed` is not in the binary list → `set_text`. The response is always read with `get_text( )` and logged as-is (`format_json` only reformats payloads starting with `{` / `[`; 1 MB cap on the logged copy only).
- Reference caller: `ZCL_BCTC_POSTING` (package `ZBCTC`, project bmw-zbctc) once built; the HEAD+POST-JSON sibling today is `ZCL_API_IB_BCTC->import_finplan` (static `application/json` row, no caller content type).

## Merge & precedence rules (engine behavior, verified)

| Aspect | Rule |
|---|---|
| URI | dynamic `uri_path` wins; else config `uri_path` |
| Method | config wins (`GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS`, unknown static value → `GET`); config `DYNAMIC` → caller's `is_dynamic_request_value-method`, mandatory and validated (else `method_required`, raised before any HTTP/log) — pattern D. A multi-method chain = either one row per method (pattern C) or one `DYNAMIC` row |
| Content type | config wins (static value, caller's `content_type` ignored); config `DYNAMIC` → caller's `is_dynamic_request_value-content_type` (condensed), mandatory when the call has a body (else `content_type_required`, raised before any HTTP/log), optional on a bodiless call — pattern E. The resolved value drives the header, serialization, binary list and response deserialization rows below |
| Session | `keep_session = abap_true` keeps client + cookies on the instance for the next call (pattern C); initial (default) = client closed per call, exactly the pre-Aug-2026 behavior |
| Query params | dynamic params + ALL config `_P` rows appended; URL-escaped via `cl_web_http_utility=>escape_url` |
| Headers | caller (dynamic) headers, then ALL config `_I` rows; the resolved content type (row above) is appended as header `content-type` only when no merged header is named content-type in any letter case (case-insensitive since Oct 2026 — `merge_request_headers`) AND the resolved value is not empty |
| Payload | `i_request_payload_data` (when supplied and non-initial) WINS over `is_dynamic_request_value-request_payload` |
| Serialization | applies to `i_request_payload_data` only: resolved content type contains `json` → XCO JSON (+ camelCase if `mapping_camel`); binary list → `set_binary`; other content types fall back to `|{ data }|` string templating. A ready string belongs in `is_dynamic_request_value-request_payload` — sent untouched whatever the content type is |
| Response deserialize | only when HTTP 2xx AND `c_response_data` supplied AND payload non-empty AND the resolved content type contains `json`; transformation camelCase→underscore is ALWAYS applied — target ABAP structure must use underscore names |

## `es_logger` (`zif_api_fwk_types=>ty_logger`) — your §11 evidence

```
request : uri_path, method, header[], param[], payload
response: http_code, http_message, header[], payload
```

Always returned (also on non-2xx). Use it to: check `es_logger-response-http_code` for business success handling, quote real payloads in Verify Loops, and update BO status. Non-2xx without an HTTP-level exception does NOT raise — check the code yourself.

## Error handling matrix

| Situation | What happens |
|---|---|
| No config row | `zcx_api_fwk` textid `config_not_found` |
| Config inactive | `config_inactive` |
| Config `method = DYNAMIC` but caller `method` missing/invalid | `method_required` (ZMC_API_FWK 015) — raised before destination creation, nothing logged |
| Config `content_type = DYNAMIC`, call has a body, caller `content_type` empty | `content_type_required` (ZMC_API_FWK 016) — raised before destination creation, nothing logged (a bodiless call stays silent) |
| Destination/client creation failed | `init_error` (previous = root cause) |
| HTTP execute failed (network, TLS, timeout) | log saved first (if enabled), then `execute_error` (previous = root cause) |
| HTTP returned 4xx/5xx | NO exception — inspect `es_logger-response-http_code` |

## Parsing the partner's error body (OData V2 / V4)

On `http_code >= 400` from an OData service (S/4 standard APIs like `API_BILLINGDOCUMENT`, `API_OUTBOUND_DELIVERY_SRV`, or any partner following the OData error format), extract the business error with:

```abap
IF ls_logger-response-http_code >= 400.
  DATA(ls_error) = zcl_api_error_util_v4=>parse_error_json( ls_logger-response-payload ).
  " ls_error-code    e.g. 'VF/017'          ls_error-message  human-readable text
  " ls_error-target  optional               ls_error-details  table (code/message/target per line)
  " → update BO status / raise RAP message / log; never re-raise raw payload to the user
ENDIF.
```

Behavior (unit-test verified Jul 2026):
- Handles **both** formats with one call: V4 (`message` flat string, `details[]` under `error`) and V2 (`message` = `{lang, value}` object → `value` is taken; details read from `innererror/errordetails[]`).
- Tolerant of SAP instance annotations (`@SAP__common.ExceptionCategory`, `@SAP__common.numericSeverity`, …) and of `innererror` noise — they are skipped.
- Never raises; a non-JSON/unparseable payload returns an initial structure — check `ls_error-code IS INITIAL` before trusting it.
- **Do NOT use `zcl_api_fwk=>json_to_abap` for error bodies**: real SAP V4 error responses contain `@SAP__common.*` member names that XCO rejects (`CX_XCO_DEP_WRAPPED_EXCEPTION`, "Non-canonical structure of element name").

## Sharp edges (verified against source unless labeled)

- **Binary outbound**: when config `content_type` is in the binary list, the engine does `set_binary( CONV xstring( lv_payload ) )` — a character→byte conversion that treats the payload as a HEX string; it does NOT base64-decode. Binary outbound is effectively untested territory — verify with a real call before relying on it, or use text/JSON content types.
- **Log persistence**: `save_log` uses EML without `COMMIT ENTITIES` (intentional). [Inference] In a plain report/class context add `COMMIT ENTITIES`/`COMMIT WORK` after `execute_api` if log rows don't appear in **ZAPI_FWK_LOG**; inside RAP handlers the BO's own save sequence commits it.
- **Response camel mapping is unconditional** — even with `mapping_camel = false`, response JSON keys are converted camelCase→underscore before writing into `c_response_data`.
- **Correlation**: log `correlation_id` is taken from response header `x-correlation-id` (else `sap-message-id`) — ask the partner to echo one for cross-system tracing.

## Test checklist (feeds the workflow's Verify Loop)

1. Config row visible in **ZAPI_FWK_CONFIG**, `active = X`.
2. Trigger the real call (RAP action / report) → capture `es_logger` values as evidence.
3. Confirm target system received the request (partner log/screenshot) — rule §11: SAP-side success alone is not a PASS.
4. Check **ZAPI_FWK_LOG**: row with expected `trans_num`, HTTP code, payloads (full log) — and the error row exists when you force a failure.
