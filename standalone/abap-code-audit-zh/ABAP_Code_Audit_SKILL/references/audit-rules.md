# ABAP审计规则详细说明

## 一、性能审计规则 (Performance Rules)

### P001: SELECT * 全字段查询 🔴 高

**问题代码:**
```abap
SELECT * FROM mara INTO TABLE lt_mara.
```

**推荐做法:**
```abap
SELECT matnr, ersda, ernam, mtart 
  FROM mara 
  INTO TABLE lt_mara.
```

**原因:** 减少数据库I/O和网络传输，提高查询性能

---

### P002: 嵌套SELECT查询 (N+1问题) 🔴 高

**问题代码:**
```abap
LOOP AT lt_mara INTO ls_mara.
  SELECT SINGLE * FROM marc 
    WHERE matnr = ls_mara-matnr 
    INTO ls_marc.
ENDLOOP.
```

**推荐做法:**
```abap
" 方案1: 使用FOR ALL ENTRIES
SELECT matnr, werks, lgort 
  FROM marc 
  INTO TABLE lt_marc 
  FOR ALL ENTRIES IN lt_mara 
  WHERE matnr = lt_mara-matnr.

" 方案2: 使用JOIN
SELECT a~matnr, a~mtart, b~werks 
  FROM mara AS a 
  INNER JOIN marc AS b ON a~matnr = b~matnr 
  INTO TABLE lt_result.
```

---

### P003: 全表扫描 ⚠️ 中

**问题代码:**
```abap
SELECT * FROM vbak INTO TABLE lt_vbak.
```

**推荐做法:**
```abap
SELECT vbeln, erdat, erzet, ernam 
  FROM vbak 
  INTO TABLE lt_vbak 
  WHERE erdat IN s_datum
    AND vkorg IN s_vkorg.
```

---

### P004: 循环内排序 🔴 高

**问题代码:**
```abap
LOOP AT lt_data INTO ls_data.
  SORT lt_result BY matnr.
ENDLOOP.
```

**推荐做法:**
```abap
" 将排序移到循环外部
LOOP AT lt_data INTO ls_data.
  " 处理逻辑
ENDLOOP.
SORT lt_result BY matnr.
```

---

## 二、安全审计规则 (Security Rules)

### S001: SQL注入风险 🔴 严重

**问题代码:**
```abap
CONCATENATE 'SELECT * FROM mara WHERE matnr = ''' 
            lv_matnr '''' INTO lv_sql.
EXECUTE IMMEDIATE lv_sql INTO TABLE lt_result.
```

**推荐做法:**
```abap
" 使用参数化查询
SELECT matnr, mtart FROM mara 
  INTO TABLE lt_result 
  WHERE matnr = iv_matnr.
```

### S002: 硬编码凭证 🔴 严重

**问题代码:**
```abap
DATA: lv_user TYPE string VALUE 'ADMIN',
      lv_pass TYPE string VALUE 'PASSWORD123'.
```

**推荐做法:**
```abap
" 使用SAP安全存储
CALL FUNCTION 'SSFC_BASE64_DECODE'
  EXPORTING
    bindata = lv_encoded_cred
  IMPORTING
    bindata = lv_decoded_cred.
```

### S003: 权限检查缺失 🔴 高

**问题代码:**
```abap
FORM delete_record USING p_vbeln.
  DELETE FROM vbak WHERE vbeln = p_vbeln.
ENDFORM.
```

**推荐做法:**
```abap
FORM delete_record USING p_vbeln.
  " 权限检查
  AUTHORITY-CHECK OBJECT 'V_VBAK_VKO'
    ID 'ACTVT' FIELD '06'
    ID 'VKORG' FIELD gs_vbak-vkorg.
  IF sy-subrc <> 0.
    MESSAGE e001(zmsg) WITH '无删除权限'.
  ENDIF.
  DELETE FROM vbak WHERE vbeln = p_vbeln.
ENDFORM.
```

---

## 三、代码质量规则 (Quality Rules)

### Q001: Z*命名规范 ⚠️ 中

**命名标准:**

| 对象类型 | 前缀 | 示例 |
|----------|------|------|
| 报告 | ZCL_ | ZCL_REPORT_SALES |
| 类 | ZCL_ | ZCL_CUSTOMER_MASTER |
| 函数组 | ZFG_ | ZFG_MATERIAL_DATA |
| 表 | Z* | ZCUSTOMER_MASTER |
| 数据元素 | ZDE_ | ZDE_CUSTOMER_ID |

### Q002: 错误处理缺失 ⚠️ 中

**问题代码:**
```abap
SELECT matnr FROM mara INTO ls_mara.
ENDSELECT.
```

**推荐做法:**
```abap
SELECT matnr FROM mara INTO ls_mara.
  APPEND ls_mara TO lt_result.
ENDSELECT.

IF sy-subrc <> 0.
  MESSAGE s001(zmsg) WITH '未找到数据'.
ENDIF.
```

### Q003: 魔法数字 ⚠️ 中

**问题代码:**
```abap
IF lv_amount > 100000.
  lv_discount = lv_amount * 0.1.
ENDIF.
```

**推荐做法:**
```abap
CONSTANTS: lc_discount_threshold TYPE p DECIMALS 2 VALUE 100000,
           lc_discount_rate TYPE p DECIMALS 2 VALUE 0.1.

IF lv_amount > lc_discount_threshold.
  lv_discount = lv_amount * lc_discount_rate.
ENDIF.
```

---

## 四、最佳实践规则 (Best Practices)

### B001: 使用NEW操作符 📝 低

**问题代码:**
```abap
CREATE OBJECT lo_helper.
```

**推荐做法:**
```abap
lo_helper = NEW #( ).
```

### B002: 使用内联声明 📝 低

**问题代码:**
```abap
DATA: lv_matnr TYPE matnr,
      ls_mara TYPE mara.

SELECT SINGLE matnr FROM mara INTO lv_matnr WHERE matnr = p_matnr.
```

**推荐做法:**
```abap
SELECT SINGLE matnr FROM mara INTO @DATA(lv_matnr) 
  WHERE matnr = @p_matnr.
```

### B003: 使用表表达式 📝 低

**问题代码:**
```abap
READ TABLE lt_mara INTO ls_mara INDEX 1.
IF sy-subrc = 0.
  lv_mtart = ls_mara-mtart.
ENDIF.
```

**推荐做法:**
```abap
DATA(ls_mara) = lt_mara[ 1 ].
lv_mtart = ls_mara-mtart.
```

---

## 五、复杂度计算

### 圈复杂度 (Cyclomatic Complexity)

每个IF、WHEN、CATCH增加1点复杂度：

| 分数 | 等级 | 建议 |
|------|------|------|
| 1-10 | 简单 | 无需重构 |
| 11-20 | 中等 | 考虑重构 |
| 21-50 | 复杂 | 需要重构 |
| 51+ | 不可维护 | 必须重构 |

---

*Last Updated: 2026-04-20*
