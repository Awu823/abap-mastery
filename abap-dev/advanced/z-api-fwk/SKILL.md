---
name: z-api-fwk
version: 1.0
description: Usage guide for the custom Z_API_FWK integration framework (package Z_API_FWK) — how to build an INBOUND API (handler class implementing ZIF_API_INBOUND_HANDLER + config row + the single dispatcher endpoint Z_API_INBOUND_HTTP addressed via the x-api-id header) and an OUTBOUND API (config-driven ZCL_API_FWK->execute_api over a communication arrangement), plus the config/log data model, log levels, framework error matrices, and JSON/XML utility methods. Use this skill INSTEAD of reading the Z_API_FWK package source whenever a task touches a partner API on this framework — creating, reviewing, or debugging an inbound or outbound API, writing an inbound handler class, calling execute_api from a RAP action/report, configuring an API in the ZUI_API_CONFIG_O4 Fiori app, checking calls in the ZUI_API_LOG_O4 log app, or explaining framework behavior (HTTP status codes, logging, base64/binary payloads, camelCase mapping). Triggers include "Z_API_FWK", "API framework", "inbound API", "outbound API", "execute_api", "execute_inbound", "handler class", "x-api-id", "API config", "API log"; Vietnamese triggers "tạo API inbound/outbound", "gọi API ra ngoài", "nhận API từ đối tác", "cấu hình API framework", "xem log API". For creating the communication scenario/arrangement/system itself use btp-abap-environment; for OData services use odata; for analyzing an FS document's API requirements use fs-integration-api-analyzer.
---

# Z_API_FWK — Custom API Framework Usage

Config-driven framework for **inbound** (partner → SAP) and **outbound** (SAP → partner) HTTP APIs with automatic request/response logging and two Fiori admin apps. This skill is the canonical usage contract — **do not re-read the `Z_API_FWK` package source for routine build tasks**; everything a caller or handler author needs is here and in the two flow guides.

> **Source of truth**: extracted from the live source of package `Z_API_FWK` (system `abap_bmw_dev`, July 2026; `keep_session` multi-call support + fixed log time zone added Aug 2026; `DYNAMIC` method / content type + case-insensitive content-type header precedence Oct 2026). The framework may evolve — if observed system behavior contradicts this document, re-read the specific object (`SAP(action="read", target="CLAS ZCL_API_FWK")`) and trust the system, then propose a patch to this skill (rule §14).

## Object map

| Object | Type | Role |
|---|---|---|
| `ZCL_API_FWK` | Class | Engine: `execute_api` (outbound), `execute_inbound` (inbound dispatch), `save_log` (private), JSON/XML utils |
| `ZCL_API_INBOUND_HTTP` | Class | `IF_HTTP_SERVICE_EXTENSION` impl for HTTP service `Z_API_INBOUND_HTTP` — the ONE inbound endpoint for all APIs; delegates straight to `execute_inbound` |
| `ZIF_API_INBOUND_HANDLER` | Interface | Contract every inbound handler class implements (`handle_request`) |
| `ZIF_API_FWK_TYPES` | Interface | Shared types: `tt_name_value`, `ty_dynamic_request` (incl. `keep_session`, Aug 2026; `method` + `content_type`, Oct 2026), `ty_logger` (incl. `log_uuid`) |
| `ZIF_API_ERROR_TYPES_V4` | Interface | OData V4 standard error response types (`ty_error_v4`, `tt_error_detail_v4`, `ty_error_response_v4`) per OASIS OData JSON 4.01 |
| `ZCL_API_ERROR_UTIL_V4` | Class | Error-response toolkit (unit-tested): `build_error_json`/`build_detail` emit OData V4 error JSON from a T100 message (inbound side); `parse_error_json` extracts code/message/target/details from a partner's OData **V2 or V4** error body (outbound side) |
| `ZCX_API_FWK` | Exception | Textids `config_not_found`, `config_inactive`, `init_error`, `execute_error`, `method_required`, `content_type_required` (Oct 2026); messages in `ZMC_API_FWK` |
| `ZTB_API_CONFIG_H/_I/_P` | Tables | Config: header / HTTP headers / URL params (RAP BO `ZI_API_CONFIG_H`, draft-enabled) |
| `ZTB_API_LOG_H/_I_RQ/_I_RP/_P` | Tables | Log: header / request headers / response headers / params (RAP BO `ZI_API_LOG_H`) |
| `ZUI_API_CONFIG_O4` / `ZUI_API_LOG_O4` | SRVD+SRVB | OData V4 UI services behind Fiori apps `ZAPI_FWK_CONFIG` (maintain) / `ZAPI_FWK_LOG` (monitor) |
| `ZCS_API_FWK` | Comm scenario | Inbound communication scenario exposing `Z_API_INBOUND_HTTP` |
| `ZCL_API_LOG_CLEANUP_JOB` | Class | Application job (`IF_APJ_DT/RT_EXEC_OBJECT`): deletes log entries older than `P_DAYS` days (default 30) via the `ZI_API_LOG_H` BO, chunked 5000/LUW with composition cascade; scheduled through the Application Jobs Fiori app (job catalog entry + template created manually in ADT) |
| `ZTR_STRIP_ASX` | XSLT | Strips the `asx:abap` envelope for `abap_to_xml` |

## Config header fields (`ZTB_API_CONFIG_H`, key `api_id` char30)

| Field | Used by | Meaning |
|---|---|---|
| `api_id` | both | Key. Inbound: value the partner sends in header `x-api-id`. Outbound: value passed to `execute_api` |
| `active` | both | `abap_false` → inbound 500 / outbound raises `config_inactive` |
| `direction` | inbound | `'I'` enforced by `execute_inbound` (else HTTP 405). `execute_api` does NOT check direction — still set `'O'` for correct log/report semantics |
| `inbound_class` | inbound | Handler class name; must exist AND implement `ZIF_API_INBOUND_HANDLER` (validated via XCO before dynamic `CREATE OBJECT`) |
| `comm_scenario`, `service_id`, `comm_system_id` | outbound | Feed `cl_http_destination_provider=>create_by_comm_arrangement` — the only way the engine reaches a target |
| `method` | outbound | `GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS`; any other static value falls back to `GET`. **`DYNAMIC` (since Oct 2026)**: the caller supplies the verb per call in `is_dynamic_request_value-method` — mandatory then, else `zcx_api_fwk=>method_required` (ZMC_API_FWK 015) is raised before any destination/client/log. For every non-DYNAMIC config value the caller's `method` is ignored (config wins) |
| `content_type` | outbound | Static value (`application/json`, `application/pdf`, …): drives the request header `content-type` (added only when the caller sends no content-type header of its own, any letter case — Oct 2026), the XCO serialization of `i_request_payload_data` (contains `json`), the binary list (xlsx/xls/pdf/docx/zip/x-zip-compressed/octet-stream/image/ → `set_binary`) and the response deserialization. **`DYNAMIC` (since Oct 2026)**: the caller supplies the content type per call in `is_dynamic_request_value-content_type` — mandatory whenever the call has a body (else `zcx_api_fwk=>content_type_required`, ZMC_API_FWK 016, raised before any destination/client/log), optional on a bodiless call (CSRF HEAD); the resolved value then drives all of the above. For every static value the caller's `content_type` is ignored (config wins) — outbound guide pattern E |
| `mapping_camel` | outbound | `abap_true` → request ABAP→JSON uses underscore→camelCase. Response is ALWAYS deserialized camelCase→underscore regardless of this flag |
| `uri_path` | outbound | Default URI; a dynamic `uri_path` passed at call time wins |
| `log_enable` | both | `' '` = no log · `'B'` = basic (log header only — no payloads, no header/param items) · any other value (convention `'X'`) = full log |
| `timeout`, `batch_size` | — | Present in the table but NOT consumed by `execute_api`/`execute_inbound` source (verified Jul 2026). [Inference] intended for caller-side use |
| `api_group` | both | Grouping for config/log reporting (`ZVH_API_GROUP` value help) |

Config rows are maintained in Fiori app **ZAPI_FWK_CONFIG** (`ZUI_API_CONFIG_O4`) — never by direct table writes (rule §3).

## Logging (both flows)

- Written by private `save_log` via EML `MODIFY ENTITIES OF zi_api_log_h` without its own commit. **Inbound (since Jul 2026)**: `execute_inbound` persists the log itself — it first seals the handler outcome (`COMMIT WORK`), then commits the log LUW (long-form `COMMIT ENTITIES`, TRY/CATCH-wrapped). Logging is best-effort: a failed log save can never dump or alter the API response, the row is silently dropped. Logged payload copies are capped at 1 MB per direction (truncation marker; the API payload itself is untouched). **Outbound**: unchanged — persistence rides on the caller's LUW commit; in a plain report/class context add `COMMIT ENTITIES`/`COMMIT WORK` after `execute_api` if log rows don't appear.
- **Inbound handler LUW contract**: any EML a handler stages must be COMMITted/ROLLBACKed by the handler itself before returning from `handle_request` — the handler fully owns its business outcome; anything left uncommitted is committed by the framework seal (never rolled back). Details in the inbound guide.
- Log header keys: `api_id` + `log_uuid`. Carries `trans_num` (= `iv_transaction_number` you pass — always pass the business document number for traceability), `correlation_id` (response header `x-correlation-id`, else `sap-message-id`), HTTP code/status, pretty-printed req/res payloads.
- Outbound on HTTP error: log is saved BEFORE `zcx_api_fwk` (`execute_error`) is raised — the failed attempt is always visible in **ZAPI_FWK_LOG**.
- **Log time zone (since Aug 2026)**: `ReqDate`/`ReqTime` are converted to the FIXED zone `UTC+7` (constant `lc_log_time_zone` inside `save_log`; fallback = system UTC if the zone were invalid). Rationale: the former `get_user_time_zone( )` depended on the executing user — inbound dispatch runs under a technical communication user (UTC), which made log times inconsistent with dialog users. One constant to change if the operations time zone ever moves.

## Utility class-methods on `ZCL_API_FWK` (usable anywhere)

| Method | Signature essence | Notes |
|---|---|---|
| `abap_to_json` | `ia_abap` any, `iv_mapping_camel` → `rv_json` | XCO-based |
| `json_to_abap` | `iv_json`, `iv_mapping_camel` → `CHANGING c_abap` | camelCase→underscore when flag set |
| `abap_to_xml` | `ia_abap` → `rv_xml` | `CALL TRANSFORMATION id` + `ZTR_STRIP_ASX` (no asx envelope) |
| `xml_to_abap` | `iv_xml` → `CHANGING c_abap` | swallows errors → clears `c_abap` |

## Error responses — OData V4 standard (both flows)

- **Inbound (emit)**: `execute_inbound` dispatcher errors AND handler business errors return OData V4 bodies `{"error":{"code":"<MSGID>/<MSGNO>","message":...[,target][,details]}}` — build them with `zcl_api_error_util_v4=>build_error_json` (optional members omitted per spec, JSON escaping handled). The dispatcher's generic `cx_root` path uses message `ZMC_API_FWK 014` — that message must exist.
- **Outbound (parse)**: partner/S4 standard-API error bodies (V2 or V4) → `zcl_api_error_util_v4=>parse_error_json( es_logger-response-payload )`. Do NOT use `json_to_abap` for this — real SAP V4 error bodies carry `@SAP__common.*` instance annotations that make XCO fail with "Non-canonical structure of element name" (unit-test verified Jul 2026).

## Which guide to read (progressive disclosure)

- Building/debugging an **inbound** API (partner calls SAP): read [references/inbound-guide.md](references/inbound-guide.md) — dispatcher flow, handler template, framework error matrix (400/404/405/500), binary/base64 behavior, config + test checklist.
- Building/debugging an **outbound** API (SAP calls partner): read [references/outbound-guide.md](references/outbound-guide.md) — `execute_api` call patterns (incl. multi-call same-session via `keep_session` — the CSRF fetch+POST case), dynamic-request precedence (incl. content type `DYNAMIC` per call for OData V4 `$batch` — pattern E), response deserialization rules, exception matrix, sharp edges.

Read only the guide for the flow actually being built.

## Boundaries

- Communication scenario/arrangement/system creation & auth setup → [Skill: btp-abap-environment]. New object names → [Skill: naming-convention] (inbound handlers observed as `ZCL_IB_*`). OData service work → [Skill: odata]. FS-document API extraction → [Skill: fs-integration-api-analyzer].
- Governance floor unchanged: TR+Package before creating objects (§2), [Skill: activation-guard] after every mutation (§5), evidence-based claims (§8). An in-system KTD document `Z_API_FWK_GUIDE` also exists in the package.
