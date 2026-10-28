---
name: xdp-form-layout
description: Project-wide layout & format standard for Adobe Forms (XDP) on SAP — every form shares one A4 frame (margins, 5-area structure, Roboto typography, binding & FormCalc conventions) while each form carries its own data structure. Use whenever creating, reviewing, or modifying an XDP print form or its layout so the output stays uniform across the whole project. Triggers include "create form", "XDP", "Adobe Form", "print form", "form layout", "form template" — Vietnamese: "tạo form", "form in", "mẫu form", "chỉnh layout form", "review form", "quy chuẩn form".
---

# XDP Form Layout Standard

**Goal:** every XDP in the project is instantly recognizable as the same family — identical page frame, area structure, typography, and conventions. Only the **data structure inside the body differs per form**. Deviating from this standard requires explicit user approval, recorded in the TS.

This skill defines rules and a text skeleton only — it ships no binary `.xdp` sample file. When actually producing or reviewing an XDP, read [references/xdp-skeleton.md](references/xdp-skeleton.md) for the copy-paste XML frame; do not load it for consulting-only questions.

Form/interface object naming → [Skill: naming-convention].

## Prerequisites (check once per project)

- **Font Roboto** (Regular, Bold, Italic, Bold-Italic) must be uploaded/installed on the ADS instance serving this project. If not confirmed, flag it as an open prerequisite in the TS — do not silently assume.
- **Fallback font: Arial** — used only when Roboto is unavailable; never mix both in one form.
- Whatever font renders, it must support **Vietnamese Unicode (có dấu)**. Verify with a test render containing "ĐƯỜNG ưỡng ợ" before declaring the form done.

## 1. Page setup — A4 only

| | Portrait (dọc) | Landscape (ngang) |
|---|---|---|
| Page size | 210 × 297 mm | 297 × 210 mm |
| Margin top / bottom | **10 mm (1 cm)** / **10 mm (1 cm)** | 10 mm / 10 mm |
| Margin left / right | **10 mm (1 cm)** / **10 mm (1 cm)** | 10 mm / 10 mm |
| Content width | 190 mm | 277 mm |
| Content area (flowed) | x 10, y 35, w 190, h 244 mm | x 10, y 35, w 277, h 157 mm |
| Footer band | y 279, h 8 mm | y 192, h 8 mm |

All four margins are 1 cm in both orientations — no binding-edge offset. Pick orientation per form (wide tables → landscape); never a custom page size.

## 2. Area model (top → bottom)

**On the master page** (repeats on every page):

| Area | Position | Content |
|---|---|---|
| **Top** | y 10 mm, h 25 mm, full content width | Logo left, max 20 × 20 mm. Company info block immediately right of logo, left-aligned: company name 12 pt **bold**; address, tax code (MST) 12 pt regular, one line each. |
| **Footer** | footer band (see §1), full content width | **Mandatory, both elements:** page number `Trang X/Y` 12 pt **centered**; print info (printing user + print date/time, e.g. "In bởi: <user> – <date> <time>") 12 pt **right-aligned**. Print info comes display-ready from the backend (§5, §7). Nothing else. |

**In the flowed content area:**

| Area | Rules |
|---|---|
| **Header** | h ≈ 15 mm, first page only. Title **18–20 pt** **bold UPPERCASE**, centered. Optional detail line (e.g. "Từ ngày … đến ngày …") 12 pt *italic*, centered, directly under the title. |
| **Body** | The only per-form part. Item table full content width; header row set to **repeat on page break**. Group/summary/total blocks per §4. |
| **Signature** | Optional. ≥ 10 mm gap after body. Signature blocks distributed evenly across the width (2 blocks: left/right thirds). Role title 12 pt **bold** centered; optional "(Ký, họ tên)" 12 pt italic under it; ~20 mm empty signing space below. Must stay on one page (`keep intact`) — never split across a page break. |

## 3. Typography — Roboto everywhere

**Exactly two font sizes exist in a form:**

| Size class | Size | Applies to |
|---|---|---|
| **Normal text** | **12 pt** | Everything except the form title — set once on the root subform, inherited by every element |
| **Title** | **18–20 pt** | Form title only (default 18 pt; up to 20 pt when the title fits one line) |

Hierarchy is expressed by weight/posture/alignment only, never by size:

| Element | Style (all 12 pt unless stated) |
|---|---|
| Form title | **18–20 pt** bold, UPPERCASE, center |
| Header detail line | italic, center |
| Company name (top) | bold |
| Company address / MST | regular |
| Table header row | bold, center |
| Body data row | regular |
| Group / subtotal / total row | bold |
| Signature role title | bold, center |
| Signature note line | italic, center |
| Footer — page number | regular, center |
| Footer — print user + time | regular, right |

No third size without user approval. Line spacing: single; cell padding 1 mm top/bottom, 1.5 mm left/right.

## 4. Body table rules

- Borders: 0.5 pt solid black, all cells; outer frame same weight (no thick/double borders).
- Header row: 10% grey shading; repeats on every page break.
- Alignment: **numbers right**, **text left**, **dates center** — always, in header and data rows alike.
- **Column sizing is data-driven**: size every column for its longest realistic formatted value, not for its header label. Amount columns ≥ 32 mm on the portrait grid (a 13-char VND amount `1.234.567.890` at 12 pt needs ~27–30 mm + 3 mm padding — scaled from the render-verified 11 pt figure, re-confirm on the first 12 pt render); code/key columns fixed to their content width; free-text columns (names, descriptions) take the remainder and **must wrap** (multiLine, §8) instead of clipping. `columnWidths` must sum exactly to the content width (190 / 277 mm).
- Group header row (e.g. "Mã công trình – Tên công trình"): bold, merged/spanning the descriptive columns, left-aligned; amount columns of the group row right-aligned like data.
- Subtotal per group directly under its items; grand total last row, bold; both rendered only when data exists (conditional presence, §5).
- No zebra striping, no color other than the grey header shading — print forms are B/W-safe.

## 5. Data binding rules

- Binding is explicit (`$record...`) — never rely on implicit name matching.
- Field names in the form mirror the interface/data-node names 1:1; subform prefixes: `sf` (subform), `row` (table row), `txt`/`num`/`dt` (draw/field by type), `img` (image).
- Repeating items: one row subform with `<occur min="0" max="-1"/>` bound to the repeating node. Group level = wrapping subform bound to the group node containing its own header row + item rows + subtotal row.
- Optional blocks (total, signature, header detail line) are dropped via **conditional presence** (`presence="hidden"` when the bound node is empty) — never by leaving blank space.
- Form receives display-ready business data; it never derives business values beyond simple sums/counters (§6).

## 6. Script rules — FormCalc-first

- **FormCalc** for: page numbering, `Sum()` of bound amounts, simple concatenation, presence toggles.
- **JavaScript** only where FormCalc genuinely can't (complex string/locale handling) — one language per script object, comment why JS was needed.
- No business logic in scripts: amounts, số tiền bằng chữ (amount-in-words), tax math come pre-computed from the backend interface.
- Standard snippets live in the skeleton reference.

## 7. Number / date / currency format

- **Follow the SAP user defaults** — do not hardcode locale separators or date patterns in picture clauses. Either bind backend-formatted strings, or use locale-driven `num{}`/`date{}` pictures without fixed separators.
- Alignment per §4 applies regardless of format.
- Currency amounts always carry their currency reference from the interface; never a hardcoded "VND".

## 8. XFA hard rules — each one traced to a real render failure

These are structural, not stylistic. Violating any of them produced a live Acrobat/ADS defect during this project (the error-to-fix mapping lives in the skeleton reference §4). Apply them to every form:

1. **Rows only inside tables.** Every `layout="row"` subform must be a child of a `layout="table"` subform with explicit `columnWidths`. A bare row is rendered as positioned content — all cells overlap at x=0. All tables of one report (header / groups / totals) share the **same** `columnWidths` grid so columns align; cells carry no `w` of their own; merged cells use `colSpan`.
2. **`minH`, never fixed `h`, on rows and cells** — fixed heights clip long content. Free-text cells additionally need `<ui><textEdit multiLine="1"/></ui>` so the row grows instead of truncating.
3. **Static/unbound blocks need `<bind match="none"/>` + `occur min="1"`.** An unbound subform with `min="0"` is silently dropped by the data merge — the block (signature, grand total, column header) just disappears from the output. Data-dependent hiding is done with a `presence = "hidden"` script, never with `min="0"`.
4. **Layout-only wrapper subforms get `<bind match="none"/>`** so the data context passes through to the bound rows inside them.
5. **Page numbering**: `<event activity="ready" ref="$layout">` (the value `layout:ready` is an invalid enum) with FormCalc `$ = concat("Trang ", xfa.layout.page(Ref($)), "/", xfa.layout.pageCount())` — the `Ref()` wrapper is mandatory; FormCalc passes `$` by value and fails with "Argument mismatch" without it.
6. **`access="protected"` on the root subform** — print forms must not render fillable-field highlights.
7. **Bold/italic only render if that font face exists** on the rendering side (design PC and ADS). `weight="bold"` degrades silently to regular when the Bold face is missing — verify via the output PDF's File > Properties > Fonts (no "substituted" entries).
8. **Field completeness against the mockup**: before handoff, walk the FS mockup element by element (logo, company block, title, header detail, every column, group rows, subtotals, grand total, every signature block, footer) and confirm each exists in the XDP — a mockup element with no counterpart is a defect, not an omission to mention later.

## 9. Compliance checklist (run before declaring any form done)

1. Page = A4, all four margins 1 cm (§1).
2. All areas present/positioned per §2 (signature optional but, if present, per spec); footer present with page number centered + print user/time right-aligned; every mockup element implemented (§8.8).
3. Every text element uses Roboto and exactly one of the two sizes in §3: 12 pt (everything) or 18–20 pt (form title only).
4. Table header repeats on page break; signature block does not split.
5. Numbers right / text left / dates center everywhere; columns sized per §4 (no clipped amounts).
6. Optional blocks use conditional presence, not blank space (and never `occur min="0"` on unbound blocks — §8.3).
7. No hardcoded locale format; no business logic in scripts.
8. **Rendered preview with sample data is mandatory evidence**: open the form with a sample-data XML (delivered alongside every form, node names mirroring the bindings 1:1) — zero script-error popups, long text wraps, bold renders bold, Vietnamese diacritics correct. "The XML looks right" is not a pass; only a clean render is.

A form failing any point is **not compliant** — fix or get explicit user sign-off on the deviation. Every form is delivered as a pair: the `.xdp` + its sample-data XML.
