// LEGACY — only for apps set up before zero-config, or a system still running an old ZEX_LIB_CORE.
// New apps: no file needed (see ../fiori-setup.md); overrides go to manifest sap.ui5/config/zExcelExport.
// Location must be webapp/ext/controller/ExcelConfig.js.
sap.ui.define([], function () {
    "use strict";

    return {
        // 1. Mã định danh của App (Truyền xuống parameter app_id)
        appId: "",

        // 2. ID Template Excel đăng ký trên Node.js (Fallback nếu Backend không trả về)
        excelId: "",

        // 3. Đường dẫn Static Action OData V4 cấu hình trong BDEF
        // Copy EntitySet / Namespace / Action name from the service $metadata, e.g.
        // "/Orders/com.sap.gateway.srvd.zui_order.v0001.printExcel(...)"
        actionPath: "/{EntitySet}/{Schema Namespace}.{ActionName}(...)",

        // 4. Khóa chính của Business Object (TỰ ĐỘNG KHÔNG CẦN KHAI BÁO)
        // Nếu để trống (""), hệ thống sẽ tự động quét OData Metadata để lấy danh sách khóa (hỗ trợ cả khóa đơn và khóa kép).
        // Chỉ khai báo thủ công nếu muốn ghi đè (Ví dụ: "MaterialId" hoặc ["SalesOrderId", "SalesOrderItemId"])
        idProperty: "",

        // 5. Tham số mở rộng nếu có (Truyền xuống parameter custom_param)
        customParam: ""
    };
});