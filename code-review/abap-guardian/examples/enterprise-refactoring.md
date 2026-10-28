# Enterprise Refactoring Examples

## 1. SELECT inside a LOOP (Performance)

**[BAD] - Procedural & Slow**
```abap
LOOP AT lt_materials INTO ls_material.
  SELECT SINGLE maktx FROM makt 
    INTO ls_material-description
    WHERE matnr = ls_material-matnr 
      AND spras = sy-langu.
  MODIFY lt_materials FROM ls_material.
ENDLOOP.
```

**[GOOD] - Set-Based & Modern**
```abap
IF lt_materials IS NOT INITIAL.
  SELECT matnr, maktx 
    FROM makt 
    INTO TABLE @DATA(lt_descriptions)
    FOR ALL ENTRIES IN @lt_materials
    WHERE matnr = @lt_materials-matnr
      AND spras = @sy-langu.
      
  LOOP AT lt_materials ASSIGNING FIELD-SYMBOL(<ls_material>).
    <ls_material>-description = VALUE #( lt_descriptions[ matnr = <ls_material>-matnr ]-maktx OPTIONAL ).
  ENDLOOP.
ENDIF.
```

## 2. Legacy Error Handling (Architecture)

**[BAD] - SY-SUBRC checks**
```abap
CALL FUNCTION 'CALCULATE_TAX'
  EXPORTING
    amount = lv_amount
  IMPORTING
    tax    = lv_tax
  EXCEPTIONS
    error  = 1
    OTHERS = 2.
IF sy-subrc <> 0.
  " handle error
ENDIF.
```

**[GOOD] - Class-based exceptions**
```abap
TRY.
    DATA(lv_tax) = zcl_tax_calculator=>calculate( lv_amount ).
  CATCH zcx_tax_calculation_error INTO DATA(lx_error).
    " handle error properly, e.g., logging or re-raising
ENDTRY.
```

## 3. Dynamic SQL Injection Risk (Security)

**[BAD] - Unvalidated Dynamic SQL**
```abap
" Unsafe concatenation allowing SQL Injection vulnerability
DATA(lv_where) = |NAME = '{ iv_user_input }'|.
SELECT * FROM zusers INTO TABLE @DATA(lt_users) WHERE (lv_where).
```

**[GOOD] - Sanitized Dynamic SQL via CL_ABAP_DYN_PRG**
```abap
" Secure input sanitization preventing SQL Injection
TRY.
    DATA(lv_sanitized_input) = cl_abap_dyn_prg=>check_string_literal( iv_user_input ).
    DATA(lv_where) = |NAME = { lv_sanitized_input }|.
    SELECT * FROM zusers INTO TABLE @DATA(lt_users) WHERE (lv_where).
  CATCH cx_abap_dyn_prg_error INTO DATA(lx_sec_err).
    " Handle security validation error
ENDTRY.
```

## 4. Missing Authorization Check (Security)

**[BAD] - Direct Database Access Without Authority Validation**
```abap
METHOD get_financial_data.
  " CRITICAL SECURITY ISSUE: Missing AUTHORITY-CHECK
  SELECT * FROM sflight INTO TABLE @rt_flights WHERE carrid = @iv_carrid.
ENDMETHOD.
```

**[GOOD] - Explicit AUTHORITY-CHECK Before Execution**
```abap
METHOD get_financial_data.
  AUTHORITY-CHECK OBJECT 'S_TABU_DIS'
    ID 'DICBERCLS' FIELD 'FA'
    ID 'ACTVT'     FIELD '03'.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE zcx_auth_failed.
  ENDIF.

  SELECT * FROM sflight INTO TABLE @rt_flights WHERE carrid = @iv_carrid.
ENDMETHOD.
```

## 5. Legacy Procedural FORM to OO Method (Architecture)

**[BAD] - Subroutine with Global Variables**
```abap
FORM calculate_discount USING pv_price CHANGING cv_total.
  IF pv_price > 100.
    cv_total = pv_price * '0.9'.
  ENDIF.
ENDFORM.
```

**[GOOD] - Object-Oriented Single-Responsibility Method**
```abap
METHODS calculate_discount
  IMPORTING iv_price        TYPE mseg-dmbtr
  RETURNING VALUE(rv_total) TYPE mseg-dmbtr.

METHOD calculate_discount.
  rv_total = COND #( WHEN iv_price > 100 THEN iv_price * '0.90'
                     ELSE iv_price ).
ENDMETHOD.
```

## 6. Legacy Control Break (`AT NEW`) to Modern GROUP BY (Modern Syntax)

**[BAD] - Legacy Subroutine with Control Break AT NEW**
```abap
" Obsolete control break processing relying on table sorting and work area alignment
SORT lt_orders BY customer_id.
LOOP AT lt_orders INTO ls_order.
  AT NEW customer_id.
    CLEAR gv_customer_total.
  ENDAT.
  gv_customer_total += ls_order-amount.
ENDLOOP.
```

**[GOOD] - Modern Expression-Based GROUP BY Processing**
```abap
" Clean, modern group loop without global variables or side effects
LOOP AT lt_orders INTO DATA(ls_order)
  GROUP BY ( customer_id = ls_order-customer_id ) INTO DATA(group_key).
  
  DATA(lv_total) = REDUCE mseg-dmbtr( 
    INIT s = 0 
    FOR member IN GROUP group_key 
    NEXT s = s + member-amount ).
ENDLOOP.
```

## 7. Classic CDS View to Modern CDS View Entity (7.55+ / ABAP Cloud)

**[BAD] - Classic DEFINE VIEW (Generates Obsolete DB View)**
```sql
@AbapCatalog.sqlViewName: 'ZV_FLIGHT_OLD'
@AbapCatalog.compiler.CompareFilter: true
@AccessControl.authorizationCheck: #CHECK
@EndUserText.label: 'Legacy CDS View'
define view ZI_Flight_Legacy
  as select from sflight
{
  key carrid,
  key connid,
      price
}
```

**[GOOD] - Modern DEFINE VIEW ENTITY (ABAP Cloud Ready)**
```sql
@AccessControl.authorizationCheck: #CHECK
@EndUserText.label: 'Modern CDS View Entity'
define view entity ZI_Flight_Modern
  as select from sflight
{
  key carrid,
  key connid,
      price
}
```
