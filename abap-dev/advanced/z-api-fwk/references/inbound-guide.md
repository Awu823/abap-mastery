# Z_API_FWK — Inbound API Guide (partner → SAP)

Everything needed to build, configure, and debug an inbound API on the framework. Source: live `Z_API_FWK` package source (`abap_bmw_dev`, Jul 2026).

## Runtime flow

```
Partner (Postman / external system)
  → HTTP request to service Z_API_INBOUND_HTTP        (ONE endpoint for ALL inbound APIs)
    header: x-api-id = <API_ID>                        (routing key — mandatory)
  → ZCL_API_INBOUND_HTTP (if_http_service_extension~handle_request)
  → NEW zcl_api_fwk( )->execute_inbound( io_request / io_response )
      1. read payload   (binary content-type → base64-encode; else get_text)
      2. read x-api-id  (missing → 400, stop)
      3. SELECT SINGLE zi_api_config_h WHERE ApiId = x-api-id   (validation matrix below)
      4. validate handler class via XCO (exists + implements ZIF_API_INBOUND_HANDLER)
      5. CREATE OBJECT (dynamic) → handler->handle_request( ... )
      6. set status/reason + Content-Type on response
      7. save_log if config log_enable ≠ space
```

Auth: the endpoint is exposed through communication scenario `ZCS_API_FWK` — the partner calls with a communication-arrangement user. Setting that up is [Skill: btp-abap-environment] territory.

## Build steps for a new inbound API

1. **DDIC request/response types** — abstract types/structures for the payloads ([Skill: naming-convention]).
2. **Handler class** `ZCL_IB_<NAME>` implementing `ZIF_API_INBOUND_HANDLER` (template below).
3. **Config row** in Fiori app **ZAPI_FWK_CONFIG**: `api_id`, `direction = 'I'`, `active = X`, `inbound_class = ZCL_IB_<NAME>`, `log_enable` (`X` full / `B` basic), `api_group`, description. Comm-scenario/method/uri fields are outbound-only — leave empty.
4. **Test** — unit tests on the handler (mock payload strings), then a real call (Postman) with header `x-api-id` against the `Z_API_INBOUND_HTTP` endpoint URL from the communication arrangement.

## Handler contract

```abap
INTERFACE zif_api_inbound_handler PUBLIC.
  METHODS handle_request
    IMPORTING
      iv_api_id           TYPE string
      iv_request_payload  TYPE string                              " raw text, or base64 when binary (see below)
      it_headers          TYPE zif_api_fwk_types=>tt_name_value OPTIONAL  " all HTTP request headers (name/value)
      it_params           TYPE zif_api_fwk_types=>tt_name_value OPTIONAL  " URL query/form fields (name/value)
    EXPORTING
      ev_response_payload   TYPE string
      ev_http_status        TYPE i
      ev_transaction_number TYPE string   " business key → log trans_num (optional)
    RAISING
      zcx_api_fwk.
ENDINTERFACE.
```

The handler owns the business result entirely: set `ev_http_status` explicitly for every path (200/201 success, 4xx business rejection with a JSON error body). Existing examples in the package: `ZCL_TEST_INBOUND_HANDLE_CLASS`, `ZCL_IB_RECEIVE_PDF_TEST`.

**LUW contract (mandatory)**: every EML modify the handler stages must be closed by the handler itself — `COMMIT ENTITIES` to persist, `ROLLBACK ENTITIES` to discard — **before returning** from `handle_request`. The business outcome then belongs 100% to the handler's logic; nothing the framework does afterwards can change it. Anything left uncommitted (forgotten commit, exception after staging) is **committed** by the framework's seal (see Logging notes) — never rolled back — so an error path that stages changes MUST roll them back explicitly. Direct-SQL writers should likewise `COMMIT WORK` themselves; if they don't, the seal secures their writes.

## Handler template

```abap
CLASS zcl_ib_my_api DEFINITION
  PUBLIC FINAL CREATE PUBLIC.
  PUBLIC SECTION.
    INTERFACES zif_api_inbound_handler.
  PRIVATE SECTION.
    TYPES: BEGIN OF ty_request,
             " request fields (underscore names when using camel mapping)
           END OF ty_request.
    TYPES: BEGIN OF ty_response,
             success TYPE abap_bool,
             message TYPE string,
           END OF ty_response.
ENDCLASS.

CLASS zcl_ib_my_api IMPLEMENTATION.
  METHOD zif_api_inbound_handler~handle_request.
    DATA ls_request  TYPE ty_request.
    DATA ls_response TYPE ty_response.

    TRY.
        " 1. Parse (JSON partner payload → ABAP; camel flag if partner sends camelCase)
        zcl_api_fwk=>json_to_abap( EXPORTING iv_json          = iv_request_payload
                                             iv_mapping_camel = abap_true
                                   CHANGING  c_abap           = ls_request ).

        " 2. Validate — business rejection is a 4xx set HERE, not an exception.
        "    Error bodies follow the OData V4 standard via zcl_api_error_util_v4:
        "    code = <msg_class>/<msg_number>, text resolved from the message class
        IF ls_request IS INITIAL.
          ev_http_status      = 400.
          ev_response_payload = zcl_api_error_util_v4=>build_error_json(
                                  iv_msg_class  = 'ZMC_MY_API'      " your message class
                                  iv_msg_number = '001'
                                  iv_target     = 'payload' ).      " optional; details via it_details
          RETURN.
        ENDIF.

        " 3. Business logic — EML / released APIs only (rule §3), never direct table writes

        " 4. Success response + business key for the API log (trans_num)
        ev_http_status        = 200.
        ev_response_payload   = zcl_api_fwk=>abap_to_json( ia_abap = ls_response iv_mapping_camel = abap_true ).
        ev_transaction_number = |{ lv_document_number }|.

      CATCH cx_root INTO DATA(lx_error).
        " Option A (explicit, preferred): map to a controlled 500 yourself —
        " main message from your message class, full exception text as a detail line
        ev_http_status      = 500.
        ev_response_payload = zcl_api_error_util_v4=>build_error_json(
          iv_msg_class  = 'ZMC_MY_API'
          iv_msg_number = '002'
          it_details    = VALUE #( ( code    = 'ZMC_MY_API/002'
                                     message = lx_error->get_text( ) ) ) ).
        " Option B: RAISE EXCEPTION TYPE zcx_api_fwk — framework returns a 500
        " OData V4 body whose code reuses the exception's own T100 key
    ENDTRY.
  ENDMETHOD.
ENDCLASS.
```

Framework behavior if an exception escapes the handler (OData V4 bodies since Jul 2026): `zcx_api_fwk` → 500 with `{"error":{"code":"<t100key msgid/msgno>","message":"<text>"}}`; any other `cx_root` → 500 with the **generic** message `ZMC_API_FWK/014` ("Internal processing error…") — details deliberately not leaked to the partner. Working demo of all three `build_error_json` usage patterns: `ZCL_TEST_INBOUND_HANDLE_CLASS` (uses messages `ZMC_API_FWK 011–013`).

## Framework validation matrix (before the handler runs)

| Condition | HTTP | Message (`ZMC_API_FWK`) |
|---|---|---|
| Header `x-api-id` missing | 400 | 010 |
| No config row for the api_id | 404 | 000 |
| Config `active = false` | 500 | 001 |
| Config `direction ≠ 'I'` | 405 | 007 |
| Config `inbound_class` empty | 500 | 008 |
| Class doesn't exist or doesn't implement `ZIF_API_INBOUND_HANDLER` (XCO check) | 500 | 006 |
| `CREATE OBJECT` failed | 500 | 009 |

All framework error bodies follow the **OData V4 standard** (since Jul 2026): `{"error":{"code":"ZMC_API_FWK/<NNN>","message":"<text>"[,"target"][,"details"]}}` — built by `zcl_api_error_util_v4=>build_error_json`. Specifics: missing `x-api-id` adds `"target":"x-api-id"`; `CREATE OBJECT` failure (009) carries the original exception text in `details[]`; the generic `cx_root` path uses message `ZMC_API_FWK 014`. Messages `011–014` must exist in `ZMC_API_FWK` (added manually — the MCP tool cannot edit message classes).

## Payload & response mechanics

- **Binary uploads**: when the request `content-type` contains one of xlsx / xls / pdf / docx / zip / x-zip-compressed / octet-stream / image/, the framework reads binary and **base64-encodes** it — `iv_request_payload` arrives as a base64 string. Decode in the handler (e.g. `cl_web_http_utility=>decode_x_base64`). Everything else arrives as plain text via `get_text( )`.
- **Response Content-Type**: framework sets `application/json` when your `ev_response_payload` contains `{` or `[`, else `text/plain`. Reason phrase mapped from `ev_http_status` (200-299 OK, 400, 401, 403, 404, 405, 500).
- **Headers/params**: `it_headers` = every request header; `it_params` = form/query fields — read what you need by `name`.

## Logging notes (inbound specifics)

- **Persistence is deterministic (since Jul 2026)** — GET/POST/error alike. After the response is finalized, `execute_inbound` runs: `COMMIT WORK` (the **seal** — permanently closes whatever the handler intended to persist, incl. uncommitted direct-SQL writes) → `save_log` → long-form `COMMIT ENTITIES` for the log LUW → `ROLLBACK ENTITIES` only if that log save failed. The whole block is TRY/CATCH-wrapped: **logging is best-effort and can never dump or change the API response** (a dump here would turn a successful business call into a 500 and provoke partner retries).
- Because of the seal, a handler that stages EML and returns without commit/rollback gets its leftovers **committed** — see the LUW contract in the Handler contract section. Handler data can never be lost to a failed log save: the seal runs before anything touches the log.
- **Blind spots**: a failed log save is dropped silently (symptom: API works, **ZAPI_FWK_LOG** has no row). Phase-1 failures (`save_log`'s own `MODIFY` — e.g. a future BO authorization) are also silent (`ls_failed` is not evaluated). Debugging `save_log` is the only way to see them.
- Logged payload copies are **capped at 1 MB per direction** (truncation marker with original size appended, applied before pretty-printing) — protects the log save from multi-MB base64 binaries; the API payload itself is untouched. `ZBP_I_API_LOG_H` is empty — the BDEF declares authorization but no check is implemented (effectively always granted; verified Jul 2026).
- `execute_inbound` must only ever be called from the HTTP dispatcher (`ZCL_API_INBOUND_HTTP`) — it issues COMMITs, which dump inside a RAP handler context.
- Log written after the response is finalized; request `uri_path` is logged as the literal `'INBOUND'`.
- **Traceability by business key**: the handler exports `ev_transaction_number` (e.g. the created/read document number) — the dispatcher stores it as `trans_num` in the log (handler value wins over the dispatcher's own `iv_transaction_number` param). Handlers that don't set it leave `trans_num` empty. Framework-level errors (bad api_id, config errors) never reach the handler, so those log rows have no trans_num by design.
- `log_enable = 'B'` skips payloads and header/param items (log header row only).

## Test checklist (feeds the workflow's Verify Loop)

1. Unit test: handler with representative + broken payload strings (no HTTP involved).
2. Postman: success case → expect handler's 2xx + response body.
3. Postman: missing `x-api-id` → 400; unknown id → 404; config inactive → 500 (proves config wiring, not just class).
4. Check **ZAPI_FWK_LOG** app: log row exists with the expected HTTP code (evidence for rule §11).
