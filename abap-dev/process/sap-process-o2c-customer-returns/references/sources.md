# Sources — sap-process-o2c-customer-returns (BKP)

Read this file only when auditing a specific factual claim in `SKILL.md` — it is not needed for normal skill use.

- SAP Help — Customer Returns (BKP overview, scope-item derivation note): https://help.sap.com/docs/SAP_S4HANA_CLOUD/a376cd9ea00d476b96f18dea1247e6a5/a3d12e631d814c7cac20ef34f1eaab6d.html
- SAP Help — Customer Returns Processing (credit memo vs. replacement): https://help.sap.com/docs/SAP_S4HANA_CLOUD/a376cd9ea00d476b96f18dea1247e6a5/ef17554b70b946e588cf4fb378fa4622.html
- SAP Help — Lean Customer Returns Processing: https://help.sap.com/docs/SAP_S4HANA_CLOUD/a376cd9ea00d476b96f18dea1247e6a5/199070fbb7084b69a95e3d8b1ac16f35.html
- SAP Help — Customer Compensation (refund codes/percentages): https://help.sap.com/docs/SAP_S4HANA_CLOUD/a376cd9ea00d476b96f18dea1247e6a5/436368e8646443988837608bb121e92d.html
- SAP Help — Term Changes in Claims, Returns, and Refund Management (returns delivery type codes): https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/13293ba83c50476bbf3da12b6ef94f16.html
- SAP Help — Digital Payments in Customer Returns: Create Refunds Based on Invoices: https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/319ec2066d214d37b27f37c5538f2d6a.html
- SAP Help — No Refund for Customer Returns Involving Supplier Returns: https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/4860a35591ac4b65a72a82345d88c500.html
- SAP Help — Processing Returns of Sales Kits in Warehouse Management: https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/f76fd3fc5cd84d4da03078ac3109bbb0.html
- SAP Help — Configuration for Sales (BKP refund codes): https://help.sap.com/docs/SAP_S4HANA_CLOUD/085edb30fb3d413da552832f3d5c01c0/ce4e32b0266d487685cee64e698de3e9.html
- SAP API Release State repository (`sap_search_objects`, `public_cloud`, Clean Core Level A) — verified 2026-07-12: `I_CUSTOMERRETURN`, `I_CUSTOMERRETURNAPPROVALREASON`, `I_CUSTOMERRETURNDELIVERY`, `I_CUSTOMERRETURNDELIVERYITEM`.
- SAP API Release State repository — analytical/cube views, verified 2026-07-12 (added after the revenue/profit report test scenario surfaced this gap): `I_CUSTOMERRETURNITEMCUBE_2`, `I_CUSTOMERRETURNRATECUBE`, `I_CREDITMEMOREQUESTITEMCUBE`, `I_DEBITMEMOREQUESTITEMCUBE` (all SD-ANA-2CL).
