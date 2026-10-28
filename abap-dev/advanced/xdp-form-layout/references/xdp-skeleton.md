# XDP Text Skeleton — project standard frame

Copy this frame for every new form; replace only `FORM_NAME`, the body tables' columns, and the data bindings. All measurements implement SKILL.md §1–§3; the structural patterns implement SKILL.md §8 (XFA hard rules) — **every one of them is traced to a real Acrobat/ADS render failure**, so do not "simplify" them away. Verified by render: this structure previewed clean in Acrobat with sample data (2026-09, form ZAF_CONSTR_CASHFLOW_DETAIL). **2026-09-28 standard update** — 1 cm margins on all sides (portrait content width 185 → 190 mm), only two font sizes (12 pt everything, 18–20 pt title), footer page number centered + print user/time right: the XFA structure is unchanged, but these new geometry/size values are **not yet render-verified** — the first form built on them must confirm via the §9 rendered preview.

## 1. Frame — A4 portrait

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xdp:xdp xmlns:xdp="http://ns.adobe.com/xdp/">
<template xmlns="http://www.xfa.org/schema/xfa-template/3.3/">
  <!-- access="protected": print form, no fillable-field highlight in Acrobat -->
  <subform name="FORM_NAME" layout="tb" locale="ambient" access="protected" restoreState="auto">
    <font typeface="Roboto" size="12pt"/>   <!-- form-wide default; elements override size/weight only -->

    <!-- ======================= MASTER PAGE ======================= -->
    <pageSet>
      <pageArea name="pmMain" id="pmMain">
        <medium stock="a4" short="210mm" long="297mm"/>
        <contentArea name="caMain" x="10mm" y="35mm" w="190mm" h="244mm"/>

        <!-- TOP: logo + company info, every page (positioned subform, fixed h is fine here) -->
        <subform name="sfTop" x="10mm" y="10mm" w="190mm" h="25mm">
          <field name="imgLogo" x="0mm" y="0mm" w="20mm" h="20mm">
            <ui><imageEdit/></ui>
            <bind match="dataRef" ref="$record.HEADER.LOGO"/>
          </field>
          <draw name="txtCompanyName" x="24mm" y="0mm" w="166mm" h="5mm">
            <font typeface="Roboto" size="12pt" weight="bold"/>
            <value><text>Công ty ...</text></value>
          </draw>
          <draw name="txtCompanyAddress" x="24mm" y="5mm" w="166mm" h="5mm">
            <font typeface="Roboto" size="12pt"/>
            <value><text>Số ..., Phường ..., TP..., Việt Nam</text></value>
          </draw>
          <draw name="txtCompanyTax" x="24mm" y="10mm" w="166mm" h="5mm">
            <font typeface="Roboto" size="12pt"/>
            <value><text>MST: ...</text></value>
          </draw>
        </subform>

        <!-- FOOTER (mandatory): page number CENTER, print user + time RIGHT, every page -->
        <subform name="sfFooter" x="10mm" y="279mm" w="190mm" h="8mm">
          <!-- Page number: activity MUST be "ready" ref="$layout" ("layout:ready" is an
               invalid enum), and the object ref MUST be wrapped in Ref() — FormCalc passes
               $ by VALUE, giving "Argument mismatch in property or function argument". -->
          <field name="txtPageNo" x="65mm" y="1.5mm" w="60mm" h="5mm">
            <ui><textEdit/></ui>
            <font typeface="Roboto" size="12pt"/><para hAlign="center"/>
            <event activity="ready" ref="$layout" name="event__ready">
              <script contentType="application/x-formcalc">
                $ = concat("Trang ", xfa.layout.page(Ref($)), "/", xfa.layout.pageCount())
              </script>
            </event>
          </field>
          <!-- Print info: display-ready string from backend (user + date/time per SAP
               user defaults, SKILL.md §7), e.g. "In bởi: <user> – <date> <time>" -->
          <field name="txtPrintInfo" x="130mm" y="1.5mm" w="60mm" h="5mm">
            <ui><textEdit/></ui>
            <font typeface="Roboto" size="12pt"/><para hAlign="right"/>
            <bind match="dataRef" ref="$record.HEADER.PRINT_INFO"/>
          </field>
        </subform>
      </pageArea>
    </pageSet>

    <!-- ======================= FLOWED CONTENT ======================= -->
    <subform name="sfContent" layout="tb" w="190mm">

      <!-- HEADER: title + detail line, first page only -->
      <subform name="sfHeader" layout="tb" w="190mm" h="15mm">
        <!-- title: 18-20pt (default 18pt; 20pt only when it still fits one line) -->
        <draw name="txtTitle" w="190mm" h="9mm">
          <font typeface="Roboto" size="18pt" weight="bold"/>
          <para hAlign="center"/>
          <value><text>TIÊU ĐỀ BÁO CÁO (UPPERCASE)</text></value>
        </draw>
        <field name="txtHeaderDetail" w="190mm" h="5.5mm">
          <ui><textEdit/></ui>
          <font typeface="Roboto" size="12pt" posture="italic"/>
          <para hAlign="center"/>
          <bind match="dataRef" ref="$record.HEADER.DATE_RANGE"/>
        </field>
      </subform>

      <!-- BODY: the only per-form part.
           HARD RULES (SKILL.md §8):
           - every row subform sits inside a layout="table" subform; bare rows render
             all cells overlapped at x=0
           - ALL tables of the report share ONE columnWidths grid (columns align)
           - rows/cells use minH (fixed h clips text); long-text cells multiLine="1"
           - amount columns sized for the longest formatted value (>=32mm for 13-char VND at 12pt)
           - column header repeats on page break via overflow leader on sfBody -->
      <subform name="sfBody" layout="tb" w="190mm">
        <overflow leader="tblHeader"/>

        <!-- column header: own table, re-rendered as leader after each break -->
        <subform name="tblHeader" layout="table" columnWidths="20mm 38mm 22mm 42mm 34mm 34mm" w="190mm">
          <bind match="none"/>
          <occur initial="1" min="1" max="-1"/>
          <subform name="rowTableHeader" layout="row" minH="6mm">
            <bind match="none"/>
            <!-- one draw per column: 12pt bold center, 10% grey fill, 0.5pt borders;
                 NO w attribute on cells - widths come from columnWidths -->
            <draw name="txtCol1" minH="6mm">
              <font typeface="Roboto" size="12pt" weight="bold"/>
              <para hAlign="center" vAlign="middle"/>
              <border><edge thickness="0.5pt"/><fill><color value="230,230,230"/></fill></border>
              <value><text>Cột 1</text></value>
            </draw>
            <!-- ... one draw per remaining column ... -->
          </subform>
        </subform>

        <!-- optional GROUP level: bound wrapper + its own table on the SAME grid -->
        <subform name="sfGroup" layout="tb" w="190mm">
          <occur min="0" max="-1"/>
          <bind match="dataRef" ref="$record.GROUPS.GROUP[*]"/>

          <subform name="tblGroup" layout="table" columnWidths="20mm 38mm 22mm 42mm 34mm 34mm" w="190mm">
            <bind match="none"/>   <!-- layout-only: pass the data context through -->

            <subform name="rowGroupHeader" layout="row" minH="6mm">
              <bind match="none"/>
              <!-- merged descriptive cell spans the text columns -->
              <field name="txtGroupLabel" colSpan="4" minH="6mm">
                <ui><textEdit multiLine="1"/></ui>
                <font typeface="Roboto" size="12pt" weight="bold"/>
                <para hAlign="left" vAlign="middle"/>
                <margin leftInset="1.5mm" rightInset="1.5mm" topInset="1mm" bottomInset="1mm"/>
                <border><edge thickness="0.5pt"/></border>
                <bind match="dataRef" ref="GROUP_LABEL"/>
              </field>
              <!-- group totals: display-ready from backend, no form-side math -->
              <field name="numGroupTotal1" minH="6mm">
                <ui><textEdit/></ui>
                <font typeface="Roboto" size="12pt" weight="bold"/>
                <para hAlign="right" vAlign="middle"/>
                <margin leftInset="1.5mm" rightInset="1.5mm" topInset="1mm" bottomInset="1mm"/>
                <border><edge thickness="0.5pt"/></border>
                <bind match="dataRef" ref="TOTAL_1"/>
              </field>
              <!-- ... second amount cell ... -->
            </subform>

            <subform name="rowItem" layout="row" minH="6mm">
              <occur min="0" max="-1"/>
              <bind match="dataRef" ref="ITEMS.ITEM[*]"/>
              <!-- cells: Roboto 12pt; numbers right / text left / dates center;
                   0.5pt borders; padding 1mm v / 1.5mm h;
                   long-text cells get <ui><textEdit multiLine="1"/></ui> -->
              <field name="txtItemText" minH="6mm">
                <ui><textEdit multiLine="1"/></ui>
                <font typeface="Roboto" size="12pt"/>
                <para hAlign="left" vAlign="middle"/>
                <margin leftInset="1.5mm" rightInset="1.5mm" topInset="1mm" bottomInset="1mm"/>
                <border><edge thickness="0.5pt"/></border>
                <bind match="dataRef" ref="TEXT_FIELD"/>
              </field>
              <field name="numItemAmount" minH="6mm">
                <ui><textEdit/></ui>
                <font typeface="Roboto" size="12pt"/>
                <para hAlign="right" vAlign="middle"/>
                <margin leftInset="1.5mm" rightInset="1.5mm" topInset="1mm" bottomInset="1mm"/>
                <border><edge thickness="0.5pt"/></border>
                <bind match="dataRef" ref="AMOUNT_FIELD"/>
              </field>
              <!-- ... remaining cells ... -->
            </subform>
          </subform>
        </subform>

        <!-- GRAND TOTAL: static structure => bind match="none" + occur min="1"
             (an unbound subform with min="0" is DROPPED by the data merge and
             silently vanishes from the output); hidden via presence when no data -->
        <subform name="tblTotal" layout="table" columnWidths="20mm 38mm 22mm 42mm 34mm 34mm" w="190mm">
          <bind match="none"/>
          <occur min="1" max="1"/>
          <event activity="initialize" name="event__initialize">
            <script contentType="application/x-formcalc">
              if (Count($record.GROUPS.GROUP[*]) == 0) then
                $.presence = "hidden"
              endif
            </script>
          </event>
          <subform name="rowGrandTotal" layout="row" minH="6mm">
            <bind match="none"/>
            <draw name="txtGrandTotalLabel" colSpan="4" minH="6mm">
              <font typeface="Roboto" size="12pt" weight="bold"/>
              <para hAlign="left" vAlign="middle"/>
              <margin leftInset="1.5mm" rightInset="1.5mm" topInset="1mm" bottomInset="1mm"/>
              <border><edge thickness="0.5pt"/></border>
              <value><text>Tổng cộng</text></value>
            </draw>
            <!-- amount cells bound to $record.TOTALS.* -->
          </subform>
        </subform>
      </subform>

      <!-- SIGNATURE: static => bind match="none" + occur min="1"; never splits -->
      <subform name="sfSignature" w="190mm" h="40mm">
        <bind match="none"/>
        <occur min="1" max="1"/>
        <keep intact="contentArea"/>
        <subform name="sfSignLeft" x="10mm" y="10mm" w="60mm" h="30mm">
          <draw name="txtSignRole1" x="0mm" y="0mm" w="60mm" h="5mm">
            <font typeface="Roboto" size="12pt" weight="bold"/><para hAlign="center"/>
            <value><text>Người lập</text></value>
          </draw>
          <draw name="txtSignNote1" x="0mm" y="5mm" w="60mm" h="5mm">
            <font typeface="Roboto" size="12pt" posture="italic"/><para hAlign="center"/>
            <value><text>(Ký, họ tên)</text></value>
          </draw>
          <!-- ~20mm empty signing space below -->
        </subform>
        <subform name="sfSignRight" x="120mm" y="10mm" w="60mm" h="30mm">
          <!-- same structure: e.g. Kế toán trưởng -->
        </subform>
      </subform>

    </subform>
  </subform>
</template>
</xdp:xdp>
```

## 2. Landscape deltas (everything else identical)

| Element | Portrait | Landscape |
|---|---|---|
| `<medium>` | `short="210mm" long="297mm"` | `short="210mm" long="297mm" orientation="landscape"` |
| `caMain` | `x="10mm" y="35mm" w="190mm" h="244mm"` | `x="10mm" y="35mm" w="277mm" h="157mm"` |
| `sfTop` | `x="10mm" y="10mm" w="190mm"` | `x="10mm" y="10mm" w="277mm"` |
| `sfFooter` | `x="10mm" y="279mm" w="190mm"` | `x="10mm" y="192mm" w="277mm"` |
| `txtPageNo` x-offset (center) | `65mm` | `108.5mm` |
| `txtPrintInfo` x-offset (right) | `130mm` | `217mm` |
| Content subform / table widths | `190mm` | `277mm` |
| `sfSignRight` x | `120mm` | `207mm` |

`columnWidths` must sum exactly to the content width (190 / 277 mm).

## 3. Standard FormCalc snippets

```text
// Page numbering (event activity="ready" ref="$layout" on txtPageNo — already in the frame)
// Ref() is MANDATORY: FormCalc passes $ by value -> "Argument mismatch" without it
$ = concat("Trang ", xfa.layout.page(Ref($)), "/", xfa.layout.pageCount())

// Hide a static block when there is no data (initialize event)
if (Count($record.GROUPS.GROUP[*]) == 0) then
  $.presence = "hidden"
endif

// Simple sums are allowed (SKILL.md §6), but prefer backend-computed totals
$ = Sum(sfGroup.rowItem[*].numItemAmount)
```

## 4. Render-error quick reference (seen live, with the fix)

| Symptom (Acrobat/ADS) | Root cause | Fix |
|---|---|---|
| Popup `Invalid enumerated value: layout:ready` | `activity="layout:ready"` is not a valid XFA enum | `<event activity="ready" ref="$layout">` |
| Popup `Argument mismatch in property or function argument` on the page-number script | FormCalc passed `$` by value into `xfa.layout.page()` | wrap it: `xfa.layout.page(Ref($))` |
| All cells of a row drawn on top of each other at the left edge | `layout="row"` subform not inside a `layout="table"` subform | wrap rows in a table subform with `columnWidths` |
| Long text truncated mid-word | fixed `h` on row/cell; single-line field | use `minH` + `<ui><textEdit multiLine="1"/></ui>` on text cells |
| A whole block (signature, grand total) silently missing from output | unbound subform with `occur min="0"` dropped by data merge | `<bind match="none"/>` + `occur min="1"` (hide via `presence` script if data-dependent) |
| Amount shows clipped (`1.250.000.00`) | column narrower than longest formatted value | size amount columns ≥ 32 mm (portrait grid, 12 pt) for 13-char VND values |
| Bold/italic render as regular | that font face not installed (design PC) / not uploaded (ADS); Acrobat substitutes silently | install/upload all 4 Roboto faces; verify via PDF File > Properties > Fonts (no "substituted") |
| Blue fillable highlight on every bound cell | fields are interactive by default | `access="protected"` on the root subform |

## 5. Font declaration reminder

Default form font is set once on the root subform's `<font typeface="Roboto" size="12pt"/>`; every element only overrides size/weight/posture, never typeface. If ADS lacks Roboto, replace the typeface globally with `Arial` — never per element. `weight="bold"` renders bold **only if the Bold face actually exists** on the rendering side — it degrades silently otherwise (see §4 table).
