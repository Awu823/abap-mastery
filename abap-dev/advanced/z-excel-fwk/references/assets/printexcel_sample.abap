" Reference implementation of the printExcel static action.
" Source: live method LHC_R_ORDER_H->printexcel in class YT1_BP_R_ORDER (bmw-dev),
" paired with template sale_order_styled.xlsx / excel_id SALE_ORDER.
" Read references/abap-action-cookbook.md for the rules this code follows.
" NOTE: this is the live code as it stands and still serializes with /ui2/cl_json=>serialize.
" New actions use zcl_api_fwk=>abap_to_json( ia_abap = lt_sheets iv_mapping_camel = abap_true )
" instead — see the cookbook and SKILL.md §2 for the two behavioural deltas.

  METHOD printexcel.
    " =====================================================================
    " 1. ĐỌC THAM SỐ GỬI XUỐNG TỪ FRONTEND (Chuỗi các Order ID)
    " =====================================================================
    READ TABLE keys INTO DATA(ls_key) INDEX 1.
    DATA(lv_keys_string) = ls_key-%param-selected_keys.

    TYPES: BEGIN OF ty_so,
             soid TYPE yt1_de_so_id,
           END OF ty_so.
    DATA: lt_so_filter TYPE TABLE OF ty_so.

    zcl_ex_lib_utils=>parse_json_keys(
      EXPORTING
        iv_json_string = lv_keys_string
      CHANGING
        ct_keys        = lt_so_filter
    ).

    " =====================================================================
    " 2. QUERY DỮ LIỆU HEADER VÀ ITEM TỪ DATABASE
    " =====================================================================
    " (Lưu ý: Bạn nên select từ View Underlying YT1_R_... hoặc Table vật lý)
    IF lt_so_filter IS NOT INITIAL.
      " Lấy danh sách Header
      SELECT * FROM yt1_r_order_h
        FOR ALL ENTRIES IN @lt_so_filter
        WHERE soid = @lt_so_filter-soid
        INTO TABLE @DATA(lt_order_h).

      " Lấy danh sách Items của các Order trên
      SELECT * FROM yt1_r_order_i
        FOR ALL ENTRIES IN @lt_so_filter
        WHERE soid = @lt_so_filter-soid
        INTO TABLE @DATA(lt_order_i).
    ELSE.
      " Nếu không truyền xuống gì (vét toàn bộ DB)
      SELECT * FROM yt1_r_order_h INTO TABLE @lt_order_h.
      SELECT * FROM yt1_r_order_i INTO TABLE @lt_order_i.
    ENDIF.

    " =====================================================================
    " 3. KHAI BÁO CẤU TRÚC JSON NGHIỆP VỤ
    " =====================================================================
    " Cấu trúc Item
    TYPES: BEGIN OF ty_item,
             mat_id     TYPE string,
             mat_name   TYPE string,
             quantity   TYPE f,
             base_unit  TYPE string,
             net_price  TYPE f,
             net_amount TYPE f,
             currency   TYPE string,
           END OF ty_item,
           tt_items TYPE TABLE OF ty_item WITH DEFAULT KEY.

    " Cấu trúc Header (Đại diện cho 1 Sheet)
    TYPES: BEGIN OF ty_sheet_data,
             logo            TYPE string,
             company_name    TYPE string,
             company_address TYPE string,
             company_phone   TYPE string,
             company_tax     TYPE string,
             printed_user    TYPE string,
             printed_date    TYPE string,
             printed_time    TYPE string,
             company         TYPE string,
             sale_org        TYPE string,
             so_id           TYPE string,
             par_id          TYPE string,
             par_name        TYPE string,
             order_status    TYPE string,
             invoice_number  TYPE string,
             total_price     TYPE f,
             currency        TYPE string,
             store_id        TYPE string,
             store_name      TYPE string,
             items           TYPE tt_items, " <--- Bảng Items nằm lồng bên trong
           END OF ty_sheet_data.

    DATA: lt_final_sheets TYPE zif_ex_lib_types=>tt_sheets,
          ls_final_sheet  TYPE zif_ex_lib_types=>ty_sheet,
          ls_my_data      TYPE ty_sheet_data.

*    DATA: lv_file_content TYPE xstring, " RAWSTRING trong DB
*          lv_file_name    TYPE string,
*          lv_mime_type    TYPE string.
*    SELECT SINGLE filecontent, filename, mimetype
*FROM zi_tb_ex_lib_i
*WHERE excelid = 'tet2'
* AND version = ( SELECT MAX( version )
*                   FROM zi_tb_ex_lib_i
*                   WHERE excelid = 'tet2' )
*INTO (@lv_file_content, @lv_file_name, @lv_mime_type).

    " =====================================================================
    " 4. MAPPING DỮ LIỆU THEO TỪNG SHEET (1 ORDER = 1 SHEET)
    " =====================================================================
    LOOP AT lt_order_h INTO DATA(ls_header).
      CLEAR ls_my_data.

      " --- 4.1 Đổ dữ liệu Header ---
*      ls_my_data-logo = |data:{ lv_mime_type };base64,{ cl_web_http_utility=>encode_x_base64( lv_file_content ) }|.
      ls_my_data-logo = zcl_image_lib=>get_latest_image_base64( iv_image_id = 'this_is_logo' ).

      ls_my_data-company_name     = 'Công ty TNHH ABC - Miền Bắc'.
      ls_my_data-company_address  = 'Tòa nhà Keangnam, Hà Nội'.
      ls_my_data-company_phone    = '024-1234-5678'.
      ls_my_data-company_tax      = '0101234567'.
      ls_my_data-printed_user     = sy-uname.
      ls_my_data-printed_date     = |{ cl_abap_context_info=>get_system_date( ) DATE = USER }|.
      ls_my_data-printed_time     = |{ cl_abap_context_info=>get_system_time( ) TIME = USER }|.
      ls_my_data-company          = '1000'.
      ls_my_data-sale_org         = '1000'.

      ls_my_data-so_id          = ls_header-soid.
      ls_my_data-par_id         = ls_header-parid.
      ls_my_data-par_name       = ls_header-parname.
      ls_my_data-order_status   = ls_header-orderstatus.
      ls_my_data-invoice_number = ls_header-invoicenumber.
      ls_my_data-total_price    = ls_header-totalprice.
      ls_my_data-currency       = ls_header-currency.
      ls_my_data-store_id       = ls_header-storeid.
      ls_my_data-store_name     = ls_header-storename.

      " --- 4.2 Đổ dữ liệu Item (Chỉ lấy item của Order đang lặp) ---
      LOOP AT lt_order_i INTO DATA(ls_item) WHERE soid = ls_header-soid.
        APPEND VALUE #(
           mat_id     = ls_item-matid
           mat_name   = ls_item-matname
           quantity   = ls_item-quantity
           base_unit  = ls_item-baseunit
           net_price  = ls_item-netprice
           net_amount = ls_item-netamount
           currency   = ls_item-currency
        ) TO ls_my_data-items.
      ENDLOOP.

      " --- 4.3 Đóng gói vào Sheet và Đặt tên Sheet ---
      " Tên sheet không được quá 31 ký tự theo chuẩn Excel. Ta lấy ID đơn hàng làm tên.
      ls_final_sheet-sheet_name = |Order_{ ls_header-soid }|.

      " Nhúng toàn bộ cục Data vào cấu trúc
      ls_final_sheet-data = NEW ty_sheet_data( ls_my_data ).

      " Gom vào danh sách các Sheets
      APPEND ls_final_sheet TO lt_final_sheets.
    ENDLOOP.

    " =====================================================================
    " 5. CONVERT JSON VÀ TRẢ KẾT QUẢ CHO FRONTEND
    " =====================================================================
    DATA(lv_json_string) = /ui2/cl_json=>serialize(
      data        = lt_final_sheets
      compress    = abap_true
      pretty_name = /ui2/cl_json=>pretty_mode-camel_case
    ).

    GET TIME STAMP FIELD DATA(lv_timestamp).

    DATA(v_name) = |SaleOrder_{ lv_timestamp }.xlsx|.

    " Đẩy kết quả ra Abstract Entity kèm theo %cid
    result = VALUE #( (
       %cid                = ls_key-%cid
       %param-excel_id     = 'SALE_ORDER' " ID Template bạn sẽ đăng ký
       %param-filename     = v_name
       %param-json_content = lv_json_string
    ) ).

  ENDMETHOD.
