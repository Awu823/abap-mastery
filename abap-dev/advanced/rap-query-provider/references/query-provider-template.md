# IF_RAP_QUERY_PROVIDER — Standard Class Template

Complete, Clean ABAP-compliant template. Replace `zcl_<entity>_query` / `zc_<entity>` with your object names per the naming-convention skill.

```abap
CLASS zcl_<entity>_query DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    INTERFACES if_rap_query_provider.
  PROTECTED SECTION.
  PRIVATE SECTION.
ENDCLASS.

CLASS zcl_<entity>_query IMPLEMENTATION.

  METHOD if_rap_query_provider~select.
    DATA lt_data TYPE TABLE OF zc_<entity>. " Target Custom Entity Type
    DATA(lv_entity_id) = io_request->get_entity_id( ).

    TRY.
        "---------------------------------------------------------------------
        " 1. Retrieve Request parameters (mandatory calls prevent runtime dumps)
        "---------------------------------------------------------------------
        " A. Filtering
        DATA(lo_filter) = io_request->get_filter( ).
        DATA(lt_filter_ranges) = lo_filter->get_as_ranges( ).

        " B. Sorting (mandatory retrieval)
        DATA(lt_sort_elements) = io_request->get_sort_elements( ).

        " C. Paging
        DATA(lo_paging) = io_request->get_paging( ).
        DATA(lv_offset) = lo_paging->get_offset( ).
        DATA(lv_page_size) = lo_paging->get_page_size( ).

        " D. Custom Parameters (if defined on Custom Entity)
        DATA(lt_parameters) = io_request->get_parameters( ).

        "---------------------------------------------------------------------
        " 2. Execute Business Logic & Data Retrieval
        "---------------------------------------------------------------------
        " Extract specific range values from filter, e.g. for a key field:
        DATA(lt_key_range) = VALUE rs_t_rrange( ).
        READ TABLE lt_filter_ranges WITH KEY name = '<ELEMENTNAME>' INTO DATA(ls_filter).
        IF sy-subrc = 0.
          lt_key_range = ls_filter-range.
        ENDIF.

        " Execute your custom analytical/business logic here
        " ... (populate lt_data with the FULL filtered dataset) ...

        "---------------------------------------------------------------------
        " 3. Apply Post-processing (Sorting & Paging)
        "---------------------------------------------------------------------
        " A. Apply dynamic sorting
        IF lt_sort_elements IS NOT INITIAL.
          DATA(lt_sort_order) = VALUE abap_sortorder_tab(
            FOR sort_el IN lt_sort_elements
            ( name = to_upper( sort_el-element_name )
              descending = sort_el-descending ) ).
          SORT lt_data BY (lt_sort_order).
        ELSE.
          " Fallback default sort: pick a stable, business-meaningful order
          " (usually the entity's semantic key fields). A deterministic order
          " matters because paging slices the table — an unstable order makes
          " pages overlap or skip rows between requests.
          " SORT lt_data BY <key_field_1> <key_field_2> ...
        ENDIF.

        " B. Calculate total records BEFORE paging is applied
        DATA(lv_total_count) = lines( lt_data ).

        " C. Apply paging (offset & page size)
        IF lv_page_size > 0.
          DATA(lv_from) = lv_offset + 1.
          DATA(lv_to)   = lv_offset + lv_page_size.

          IF lv_from <= lv_total_count.
            DATA lt_paged_data TYPE TABLE OF zc_<entity>.
            APPEND LINES OF lt_data FROM lv_from TO lv_to TO lt_paged_data.
            lt_data = lt_paged_data.
          ELSE.
            CLEAR lt_data.
          ENDIF.
        ENDIF.

        "---------------------------------------------------------------------
        " 4. Set Response Data & Metadata
        "---------------------------------------------------------------------
        io_response->set_data( lt_data ).

        IF io_request->is_total_numb_of_rec_requested( ).
          io_response->set_total_number_of_records( lv_total_count ).
        ENDIF.

      CATCH cx_rap_query_provider INTO DATA(lx_exc).
        RAISE EXCEPTION TYPE cx_rap_query_provider
          EXPORTING
            previous = lx_exc.
    ENDTRY.
  ENDMETHOD.

ENDCLASS.
```
