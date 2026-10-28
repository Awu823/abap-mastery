# Sources — sap-process-supplychain-inventory-mgmt (BMC)

- SAP Help — Inventory Management (overview): https://help.sap.com/docs/SAP_S4HANA_CLOUD/64609d0ecac54654b0837cba34555b82/2bdcc4530b29b44ce10000000a174cb4.html
- SAP Help — Manage Stock (App F1062, scope item BMC): https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/9a4ffb3c08d74576a31a435b053778f3.html
- SAP Help — Analyze Stock in Date Range (App F6185, scope item BMC): https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/c69c194165ba4a9589c9e6babcdeb74f.html
- SAP Help — CDS Views for Inventory (Goods Movement Code/Reason Code): https://help.sap.com/docs/SAP_S4HANA_CLOUD/085edb30fb3d413da552832f3d5c01c0/7bf022a7a5d644ccb2b505662bbb45c5.html
- SAP Help — Support of Subcontracting for further Special Stocks in Goods Movement (BMC): https://help.sap.com/docs/SAP_S4HANA_CLOUD/ee9ee0ca4c3942068ea584d2f929b5b1/0d1320d664f6496f90bb5f131d2a7ada.html
- SAP API Release State repository (`sap_search_objects`, `public_cloud`, Clean Core Level A) — verified 2026-07-12: `I_MATERIALDOCUMENTHEADER_2`, `I_MATERIALDOCUMENTITEMTP`, `I_MATERIALSTOCK_2` (successor of deprecated `I_MATERIALSTOCK`), `I_MATERIALSTOCKTIMESERIES` — the stock-balance pair added after a test case (order-fulfillment dashboard FS) surfaced that movement-only views aren't enough for "current available stock" questions.
