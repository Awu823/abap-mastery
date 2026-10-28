# Sources — sap-process-o2c-sell-from-stock (BD9)

Read this file only when auditing a specific factual claim in `SKILL.md` — it is not needed for normal skill use.

- SAP Help — Configuration for Sales (BD9 config objects): https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/49d3f58cfcf84555b9042db16a33b2b8.html
- SAP Help — Configuration in Sales (BD9 rejection reasons): https://help.sap.com/docs/SAP_S4HANA_CLOUD/085edb30fb3d413da552832f3d5c01c0/89aa3bf2f8244a05b9f32e4687335a2b.html
- SAP Help — IAM Objects in Sales (business catalogs incl. `SAP_SD_BC_SO_ADV_PROC`): https://help.sap.com/docs/SAP_S4HANA_CLOUD/085edb30fb3d413da552832f3d5c01c0/27a1ec2307714e68abbeeb6f9fe65116.html
- SAP Help — SOAP API: Sales Order (A2A): https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/d23f57dcae19428c9e07c655d2a2d798.html
- SAP Help — SOAP API: Sales Order/Customer Return - Create, Update, Cancel (B2B): https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/4db2b25acc0c4a5e8160657fd6164a78.html
- SAP API Release State repository (`sap_search_objects`, `public_cloud`, Clean Core Level A) — verified 2026-07-12: `I_SALESORDER`, `I_SALESORDERITEM`, `I_OUTBOUNDDELIVERY`, `I_OUTBOUNDDELIVERYITEM`, `I_BILLINGDOCUMENT`, `I_BILLINGDOCUMENTITEM`.
- SAP API Release State repository — analytical/cube views, verified 2026-07-12 (added after the revenue/profit report test scenario surfaced this gap): `I_SALESORDERCUBE`, `I_SALESORDERITEMCUBE`, `I_BILLINGDOCUMENTITEMCUBE`, `I_SALESANALYTICSCUBE_1` (all SD-ANA-2CL), `I_SALESORDERITEMCOSTESTIMATE` (CO-PC-PCP-2CL), `I_PROFITABILITYSEGMENT` (CO-PA-2CL).
