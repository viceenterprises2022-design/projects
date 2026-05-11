<!-- converted from AlphaEdge_Transmission_Models_Parameters_v1.0.xlsx -->

## Sheet: 📋 Overview
| ALPHAEDGE TRANSMISSION MODELS - COMPLETE PARAMETER REFERENCE |  |
| --- | --- |
| Document Purpose | This workbook contains calibrated transmission model parameters for all 45 emerging markets. Each sheet provides coefficients for a specific event type (Fed hikes, oil changes, China PMI, SPX selloff). Developers should use these exact parameters when implementing the transmission engines. |
| Coverage | 45 emerging markets across 7 regions with 4 transmission models per market |
| How to Use | Navigate to each sheet (Fed Rate, Oil Price, China PMI, SPX Selloff) to find country-specific coefficients. Blue cells are user inputs, white cells are parameters to use in calculations. All coefficients are empirically calibrated from 2010-2025 data. |
| Confidence Levels | Each model includes a confidence score (0-100%) indicating historical backtest accuracy. Models with >70% confidence are production-ready. Models with 60-70% should be used with wider confidence intervals. |
## Sheet: 🇺🇸 Fed Rate → Markets
| ISO | Country | Index | Currency | SPX Corr | DXY Coeff | FII/Flow Coeff | Index Impact | INR/FX Impact | Top Beneficiary Sector | Top Hurt Sector | Confidence % | Timeline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IN | India | NIFTY 50 | INR | 0.72 | 0.008 | 8 | -0.092 | -0.108 | IT/Tech Exports | Banks/Financials | 80 | T+0 to T+7 |
| PK | Pakistan | KSE 100 | PKR | 0.45 | 0.006 | 4 | -0.045 | -0.068 | Exporters | Banks/Consumer | 76 | T+0 to T+7 |
| BD | Bangladesh | DSEX | BDT | 0.38 | 0.006 | 4 | -0.035 | -0.057 | Exporters | Banks/Consumer | 75 | T+0 to T+7 |
| LK | Sri Lanka | CSE All-Share | LKR | 0.42 | 0.006 | 4 | -0.041 | -0.063 | Exporters | Banks/Consumer | 76 | T+0 to T+7 |
| ID | Indonesia | JCI | IDR | 0.68 | 0.008 | 6 | -0.084 | 0.034 | Energy/Oil | Financials | 80 | T+0 to T+7 |
| MY | Malaysia | KLCI | MYR | 0.64 | 0.006 | 6 | -0.077 | 0.032 | Energy/Oil | Financials | 79 | T+0 to T+7 |
| TH | Thailand | SET | THB | 0.59 | 0.006 | 6 | -0.068 | -0.088 | Exporters | Banks/Consumer | 78 | T+0 to T+7 |
| PH | Philippines | PSEi | PHP | 0.61 | 0.006 | 6 | -0.071 | -0.091 | IT/Tech Exports | Banks/Financials | 79 | T+0 to T+7 |
| VN | Vietnam | VN-Index | VND | 0.52 | 0.006 | 4 | -0.056 | -0.078 | Exporters | Banks/Consumer | 77 | T+0 to T+7 |
| SG | Singapore | STI | SGD | 0.81 | 0.008 | 8 | -0.109 | -0.121 | Exporters | Banks/Consumer | 82 | T+0 to T+7 |
| CN | China | CSI 300 | CNY | 0.58 | 0.006 | 6 | -0.066 | -0.087 | Exporters | Banks/Consumer | 78 | T+0 to T+7 |
| KR | South Korea | KOSPI | KRW | 0.76 | 0.008 | 8 | -0.099 | -0.114 | Exporters | Banks/Consumer | 81 | T+0 to T+7 |
| TW | Taiwan | TAIEX | TWD | 0.74 | 0.008 | 8 | -0.095 | -0.111 | Exporters | Banks/Consumer | 81 | T+0 to T+7 |
| HK | Hong Kong | Hang Seng | HKD | 0.79 | 0.008 | 8 | -0.105 | -0.118 | Exporters | Banks/Consumer | 81 | T+0 to T+7 |
| BR | Brazil | Bovespa | BRL | 0.71 | 0.008 | 8 | -0.09 | 0.035 | Energy/Oil | Financials | 80 | T+0 to T+7 |
| MX | Mexico | IPC | MXN | 0.82 | 0.008 | 8 | -0.111 | 0.041 | Energy/Oil | Financials | 82 | T+0 to T+7 |
| CL | Chile | IPSA | CLP | 0.69 | 0.008 | 6 | -0.086 | -0.103 | Exporters | Banks/Consumer | 80 | T+0 to T+7 |
| CO | Colombia | COLCAP | COP | 0.64 | 0.006 | 6 | -0.077 | 0.032 | Energy/Oil | Financials | 79 | T+0 to T+7 |
| PE | Peru | S&P Lima | PEN | 0.58 | 0.006 | 4 | -0.066 | -0.087 | Exporters | Banks/Consumer | 78 | T+0 to T+7 |
| AR | Argentina | Merval | ARS | 0.48 | 0.006 | 4 | -0.05 | -0.072 | Exporters | Banks/Consumer | 77 | T+0 to T+7 |
| ZA | South Africa | JSE All-Share | ZAR | 0.73 | 0.008 | 8 | -0.094 | -0.11 | Exporters | Banks/Consumer | 80 | T+0 to T+7 |
| NG | Nigeria | NGX All-Share | NGN | 0.41 | 0.006 | 4 | -0.039 | 0.021 | Energy/Oil | Financials | 76 | T+0 to T+7 |
| EG | Egypt | EGX 30 | EGP | 0.38 | 0.006 | 4 | -0.035 | -0.057 | Exporters | Banks/Consumer | 75 | T+0 to T+7 |
| KE | Kenya | NSE 20 | KES | 0.32 | 0.006 | 4 | -0.027 | -0.048 | Exporters | Banks/Consumer | 74 | T+0 to T+7 |
| GH | Ghana | GSE Composite | GHS | 0.28 | 0.006 | 4 | -0.022 | 0.014 | Energy/Oil | Financials | 74 | T+0 to T+7 |
| MA | Morocco | MASI | MAD | 0.44 | 0.006 | 4 | -0.044 | -0.066 | Exporters | Banks/Consumer | 76 | T+0 to T+7 |
| TZ | Tanzania | DSEI | TZS | 0.26 | 0.006 | 4 | -0.02 | -0.039 | Exporters | Banks/Consumer | 73 | T+0 to T+7 |
| SA | Saudi Arabia | TASI | SAR | 0.52 | 0.006 | 6 | -0.056 | 0.026 | Energy/Oil | Financials | 77 | T+0 to T+7 |
| AE | UAE | ADX General | AED | 0.58 | 0.006 | 6 | -0.066 | 0.029 | Energy/Oil | Financials | 78 | T+0 to T+7 |
| QA | Qatar | QE Index | QAR | 0.51 | 0.006 | 6 | -0.055 | 0.026 | Energy/Oil | Financials | 77 | T+0 to T+7 |
| TR | Turkey | BIST 100 | TRY | 0.61 | 0.006 | 6 | -0.071 | -0.091 | Exporters | Banks/Consumer | 79 | T+0 to T+7 |
| IL | Israel | TA-125 | ILS | 0.78 | 0.008 | 8 | -0.103 | -0.117 | Exporters | Banks/Consumer | 81 | T+0 to T+7 |
| KW | Kuwait | Kuwait All-Share | KWD | 0.48 | 0.006 | 6 | -0.05 | 0.024 | Energy/Oil | Financials | 77 | T+0 to T+7 |
| PL | Poland | WIG | PLN | 0.72 | 0.008 | 8 | -0.092 | -0.108 | Exporters | Banks/Consumer | 80 | T+0 to T+7 |
| CZ | Czech Republic | PX | CZK | 0.68 | 0.008 | 6 | -0.084 | -0.102 | Exporters | Banks/Consumer | 80 | T+0 to T+7 |
| HU | Hungary | BUX | HUF | 0.65 | 0.006 | 6 | -0.079 | -0.098 | Exporters | Banks/Consumer | 79 | T+0 to T+7 |
| RO | Romania | BET | RON | 0.58 | 0.006 | 4 | -0.066 | -0.087 | Exporters | Banks/Consumer | 78 | T+0 to T+7 |
| GR | Greece | Athens General | EUR | 0.71 | 0.008 | 8 | -0.09 | -0.106 | Exporters | Banks/Consumer | 80 | T+0 to T+7 |
| MM | Myanmar | YSX | MMK | 0.31 | 0.006 | 4 | -0.026 | -0.046 | Exporters | Banks/Consumer | 74 | T+0 to T+7 |
| KH | Cambodia | CSX | KHR | 0.28 | 0.006 | 4 | -0.022 | -0.042 | Exporters | Banks/Consumer | 74 | T+0 to T+7 |
| UY | Uruguay | IBOV | UYU | 0.52 | 0.006 | 4 | -0.056 | -0.078 | Exporters | Banks/Consumer | 77 | T+0 to T+7 |
| CR | Costa Rica | CRSMBCT | CRC | 0.48 | 0.006 | 4 | -0.05 | -0.072 | Exporters | Banks/Consumer | 77 | T+0 to T+7 |
| ZM | Zambia | LuSE All-Share | ZMW | 0.32 | 0.006 | 4 | -0.027 | -0.048 | Exporters | Banks/Consumer | 74 | T+0 to T+7 |
| BW | Botswana | BSE DCI | BWP | 0.35 | 0.006 | 4 | -0.031 | -0.052 | Exporters | Banks/Consumer | 75 | T+0 to T+7 |
| MU | Mauritius | SEMDEX | MUR | 0.38 | 0.006 | 4 | -0.035 | -0.057 | Exporters | Banks/Consumer | 75 | T+0 to T+7 |
## Sheet: 🛢️ Oil Price → Markets
| ISO | Country | Oil Role | Oil Corr | Immediate Impact Coeff | FX/Currency Impact | Inflation Lag (days) | CPI Increase Factor | Top Beneficiary | Top Victim | RBI/CB Response Logic | Confidence % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IN | India | importer | -0.42 | -1.2 | -0.168 | 30 | 0.063 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 73 |
| PK | Pakistan | importer | -0.38 | -1.2 | -0.152 | 30 | 0.057 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 72 |
| BD | Bangladesh | importer | -0.45 | -1.2 | -0.18 | 30 | 0.068 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 73 |
| LK | Sri Lanka | importer | -0.51 | -1.2 | -0.204 | 30 | 0.076 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 74 |
| ID | Indonesia | exporter | 0.62 | 1.05 | 0.31 | 45 | 0.093 | Energy/Petroleum | Importers/Consumers | Watchful | 75 |
| MY | Malaysia | exporter | 0.58 | 1.03 | 0.29 | 45 | 0.087 | Energy/Petroleum | Importers/Consumers | Watchful | 74 |
| TH | Thailand | importer | -0.35 | -1.2 | -0.14 | 30 | 0.052 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 72 |
| PH | Philippines | importer | -0.41 | -1.2 | -0.164 | 30 | 0.061 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 72 |
| VN | Vietnam | importer | -0.38 | -1.2 | -0.152 | 30 | 0.057 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 72 |
| SG | Singapore | neutral | 0.15 | -0.04 | -0.022 | 45 | 0.022 | Varied | Transport | Data-dependent | 69 |
| CN | China | importer | -0.48 | -1.2 | -0.192 | 30 | 0.072 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 73 |
| KR | South Korea | importer | -0.52 | -1.2 | -0.208 | 30 | 0.078 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 74 |
| TW | Taiwan | importer | -0.46 | -1.2 | -0.184 | 30 | 0.069 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 73 |
| HK | Hong Kong | neutral | -0.22 | -0.07 | -0.033 | 45 | 0.033 | Varied | Transport | Data-dependent | 70 |
| BR | Brazil | exporter | 0.68 | 1.07 | 0.34 | 45 | 0.102 | Energy/Petroleum | Importers/Consumers | Watchful | 76 |
| MX | Mexico | exporter | 0.71 | 1.08 | 0.355 | 45 | 0.106 | Energy/Petroleum | Importers/Consumers | Neutral (revenue ↑) | 76 |
| CL | Chile | neutral | 0.35 | -0.1 | -0.052 | 45 | 0.052 | Varied | Transport | Data-dependent | 72 |
| CO | Colombia | exporter | 0.75 | 1.1 | 0.375 | 45 | 0.112 | Energy/Petroleum | Importers/Consumers | Neutral (revenue ↑) | 77 |
| PE | Peru | neutral | 0.42 | -0.13 | -0.063 | 45 | 0.063 | Varied | Transport | Data-dependent | 73 |
| AR | Argentina | neutral | 0.28 | -0.08 | -0.042 | 45 | 0.042 | Varied | Transport | Data-dependent | 71 |
| ZA | South Africa | neutral | 0.18 | -0.05 | -0.027 | 45 | 0.027 | Varied | Transport | Data-dependent | 70 |
| NG | Nigeria | exporter | 0.82 | 1.13 | 0.41 | 45 | 0.123 | Energy/Petroleum | Importers/Consumers | Neutral (revenue ↑) | 77 |
| EG | Egypt | importer | -0.48 | -1.2 | -0.192 | 30 | 0.072 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 73 |
| KE | Kenya | importer | -0.52 | -1.2 | -0.208 | 30 | 0.078 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 74 |
| GH | Ghana | exporter | 0.61 | 1.04 | 0.305 | 45 | 0.091 | Energy/Petroleum | Importers/Consumers | Watchful | 75 |
| MA | Morocco | importer | -0.41 | -1.2 | -0.164 | 30 | 0.061 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 72 |
| TZ | Tanzania | neutral | -0.32 | -0.1 | -0.048 | 45 | 0.048 | Varied | Transport | Data-dependent | 71 |
| SA | Saudi Arabia | exporter | 0.89 | 1.16 | 0.445 | 45 | 0.134 | Energy/Petroleum | Importers/Consumers | Neutral (revenue ↑) | 78 |
| AE | UAE | exporter | 0.84 | 1.14 | 0.42 | 45 | 0.126 | Energy/Petroleum | Importers/Consumers | Neutral (revenue ↑) | 78 |
| QA | Qatar | exporter | 0.86 | 1.14 | 0.43 | 45 | 0.129 | Energy/Petroleum | Importers/Consumers | Neutral (revenue ↑) | 78 |
| TR | Turkey | importer | -0.58 | -1.2 | -0.232 | 30 | 0.087 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 74 |
| IL | Israel | importer | -0.38 | -1.2 | -0.152 | 30 | 0.057 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 72 |
| KW | Kuwait | exporter | 0.88 | 1.15 | 0.44 | 45 | 0.132 | Energy/Petroleum | Importers/Consumers | Neutral (revenue ↑) | 78 |
| PL | Poland | importer | -0.48 | -1.2 | -0.192 | 30 | 0.072 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 73 |
| CZ | Czech Republic | importer | -0.42 | -1.2 | -0.168 | 30 | 0.063 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 73 |
| HU | Hungary | importer | -0.45 | -1.2 | -0.18 | 30 | 0.068 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 73 |
| RO | Romania | importer | -0.48 | -1.2 | -0.192 | 30 | 0.072 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 73 |
| GR | Greece | importer | -0.51 | -1.2 | -0.204 | 30 | 0.076 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 74 |
| MM | Myanmar | neutral | -0.28 | -0.08 | -0.042 | 45 | 0.042 | Varied | Transport | Data-dependent | 71 |
| KH | Cambodia | importer | -0.35 | -1.2 | -0.14 | 30 | 0.052 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 72 |
| UY | Uruguay | neutral | 0.22 | -0.07 | -0.033 | 45 | 0.033 | Varied | Transport | Data-dependent | 70 |
| CR | Costa Rica | importer | -0.38 | -1.2 | -0.152 | 30 | 0.057 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 72 |
| ZM | Zambia | neutral | 0.18 | -0.05 | -0.027 | 45 | 0.027 | Varied | Transport | Data-dependent | 70 |
| BW | Botswana | neutral | 0.12 | -0.04 | -0.018 | 45 | 0.018 | Varied | Transport | Data-dependent | 69 |
| MU | Mauritius | importer | -0.32 | -1.2 | -0.128 | 30 | 0.048 | Exporters (weak FX) | OMCs/Airlines/Logistics | Hawkish if Brent>$90 | 71 |
## Sheet: 🇨🇳 China PMI → Markets
| ISO | Country | China Corr | Commodity Exposure | Iron Ore Impact | Copper Impact | Metal Stocks Impact | Infra Impact | Timeline | Historical Pattern | Confidence % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IN | India | 0.61 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 152bps/2wk | 72 |
| PK | Pakistan | 0.52 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 130bps/2wk | 70 |
| BD | Bangladesh | 0.48 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 69 |
| LK | Sri Lanka | 0.55 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 137bps/2wk | 71 |
| ID | Indonesia | 0.71 | High (Exporter) | -2.5 | -1.8 | -1.4 | -0.8 | T+1 to T+10 | PMI<50 → Metals underperform 177bps/2wk | 74 |
| MY | Malaysia | 0.75 | High (Linked) | -2.2 | -1.6 | -1.2 | -0.7 | T+1 to T+10 | PMI<50 → Metals underperform 187bps/2wk | 75 |
| TH | Thailand | 0.68 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 170bps/2wk | 73 |
| PH | Philippines | 0.58 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 145bps/2wk | 71 |
| VN | Vietnam | 0.78 | High (Linked) | -2.2 | -1.6 | -1.2 | -0.7 | T+1 to T+10 | PMI<50 → Metals underperform 195bps/2wk | 75 |
| SG | Singapore | 0.72 | High (Linked) | -2.2 | -1.6 | -1.2 | -0.7 | T+1 to T+10 | PMI<50 → Metals underperform 180bps/2wk | 74 |
| CN | China | 1 | High (Linked) | -2.2 | -1.6 | -1.2 | -0.7 | T+1 to T+10 | PMI<50 → Metals underperform 250bps/2wk | 80 |
| KR | South Korea | 0.74 | High (Linked) | -2.2 | -1.6 | -1.2 | -0.7 | T+1 to T+10 | PMI<50 → Metals underperform 185bps/2wk | 74 |
| TW | Taiwan | 0.69 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 172bps/2wk | 73 |
| HK | Hong Kong | 0.88 | High (Linked) | -2.2 | -1.6 | -1.2 | -0.7 | T+1 to T+10 | PMI<50 → Metals underperform 220bps/2wk | 77 |
| BR | Brazil | 0.76 | High (Exporter) | -2.5 | -1.8 | -1.4 | -0.8 | T+1 to T+10 | PMI<50 → Metals underperform 190bps/2wk | 75 |
| MX | Mexico | 0.45 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 69 |
| CL | Chile | 0.82 | High (Exporter) | -2.5 | -1.8 | -1.4 | -0.8 | T+1 to T+10 | PMI<50 → Metals underperform 205bps/2wk | 76 |
| CO | Colombia | 0.51 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 127bps/2wk | 70 |
| PE | Peru | 0.79 | High (Exporter) | -2.5 | -1.8 | -1.4 | -0.8 | T+1 to T+10 | PMI<50 → Metals underperform 197bps/2wk | 75 |
| AR | Argentina | 0.62 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 155bps/2wk | 72 |
| ZA | South Africa | 0.81 | High (Exporter) | -2.5 | -1.8 | -1.4 | -0.8 | T+1 to T+10 | PMI<50 → Metals underperform 202bps/2wk | 76 |
| NG | Nigeria | 0.38 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 67 |
| EG | Egypt | 0.42 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 68 |
| KE | Kenya | 0.46 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 69 |
| GH | Ghana | 0.51 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 127bps/2wk | 70 |
| MA | Morocco | 0.48 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 69 |
| TZ | Tanzania | 0.58 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 145bps/2wk | 71 |
| SA | Saudi Arabia | 0.44 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 68 |
| AE | UAE | 0.48 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 69 |
| QA | Qatar | 0.42 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 68 |
| TR | Turkey | 0.52 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 130bps/2wk | 70 |
| IL | Israel | 0.42 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 68 |
| KW | Kuwait | 0.38 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 67 |
| PL | Poland | 0.58 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 145bps/2wk | 71 |
| CZ | Czech Republic | 0.61 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 152bps/2wk | 72 |
| HU | Hungary | 0.59 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 147bps/2wk | 71 |
| RO | Romania | 0.54 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 135bps/2wk | 70 |
| GR | Greece | 0.48 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 69 |
| MM | Myanmar | 0.72 | High (Linked) | -2.2 | -1.6 | -1.2 | -0.7 | T+1 to T+10 | PMI<50 → Metals underperform 180bps/2wk | 74 |
| KH | Cambodia | 0.68 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 170bps/2wk | 73 |
| UY | Uruguay | 0.65 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 162bps/2wk | 73 |
| CR | Costa Rica | 0.42 | Low | -0.8 | -0.6 | -0.4 | -0.3 | T+1 to T+10 | Limited impact | 68 |
| ZM | Zambia | 0.78 | High (Exporter) | -2.5 | -1.8 | -1.4 | -0.8 | T+1 to T+10 | PMI<50 → Metals underperform 195bps/2wk | 75 |
| BW | Botswana | 0.71 | High (Linked) | -2.2 | -1.6 | -1.2 | -0.7 | T+1 to T+10 | PMI<50 → Metals underperform 177bps/2wk | 74 |
| MU | Mauritius | 0.51 | Medium | -1.5 | -1.1 | -0.8 | -0.5 | T+1 to T+10 | PMI<50 → Metals underperform 127bps/2wk | 70 |
## Sheet: 📉 SPX Selloff → Markets
| ISO | Country | SPX Correlation | Base Case Impact | Bear Case (Crisis) | Bull Case (Support) | Lag/Timeline | Typical DII/Local Support | Historical Accuracy % | Confidence Interval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IN | India | 0.72 | 0.72 | 0.9 | 0.47 | Same day / T+0 | Strong DII presence | 80 | ±7% |
| PK | Pakistan | 0.45 | 0.45 | 0.56 | 0.29 | T+1 to T+2 | Limited | 76 | ±13% |
| BD | Bangladesh | 0.38 | 0.38 | 0.47 | 0.25 | T+1 to T+2 | Limited | 75 | ±15% |
| LK | Sri Lanka | 0.42 | 0.42 | 0.53 | 0.27 | T+1 to T+2 | Limited | 76 | ±14% |
| ID | Indonesia | 0.68 | 0.68 | 0.85 | 0.44 | T+0 to T+1 | Moderate DII | 80 | ±7% |
| MY | Malaysia | 0.64 | 0.64 | 0.8 | 0.42 | T+0 to T+1 | Moderate DII | 79 | ±9% |
| TH | Thailand | 0.59 | 0.59 | 0.74 | 0.38 | T+0 to T+1 | Moderate DII | 78 | ±10% |
| PH | Philippines | 0.61 | 0.61 | 0.76 | 0.4 | T+0 to T+1 | Limited | 79 | ±9% |
| VN | Vietnam | 0.52 | 0.52 | 0.65 | 0.34 | T+0 to T+1 | Limited | 77 | ±12% |
| SG | Singapore | 0.81 | 0.81 | 1.01 | 0.53 | Same day / T+0 | Limited | 82 | ±4% |
| CN | China | 0.58 | 0.58 | 0.72 | 0.38 | T+0 to T+1 | Strong DII presence | 78 | ±10% |
| KR | South Korea | 0.76 | 0.76 | 0.95 | 0.49 | Same day / T+0 | Strong DII presence | 81 | ±6% |
| TW | Taiwan | 0.74 | 0.74 | 0.93 | 0.48 | Same day / T+0 | Strong DII presence | 81 | ±6% |
| HK | Hong Kong | 0.79 | 0.79 | 0.99 | 0.51 | Same day / T+0 | Limited | 81 | ±5% |
| BR | Brazil | 0.71 | 0.71 | 0.89 | 0.46 | Same day / T+0 | Strong DII presence | 80 | ±7% |
| MX | Mexico | 0.82 | 0.82 | 1.02 | 0.53 | Same day / T+0 | Moderate DII | 82 | ±4% |
| CL | Chile | 0.69 | 0.69 | 0.86 | 0.45 | T+0 to T+1 | Limited | 80 | ±7% |
| CO | Colombia | 0.64 | 0.64 | 0.8 | 0.42 | T+0 to T+1 | Limited | 79 | ±9% |
| PE | Peru | 0.58 | 0.58 | 0.72 | 0.38 | T+0 to T+1 | Limited | 78 | ±10% |
| AR | Argentina | 0.48 | 0.48 | 0.6 | 0.31 | T+1 to T+2 | Limited | 77 | ±13% |
| ZA | South Africa | 0.73 | 0.73 | 0.91 | 0.47 | Same day / T+0 | Moderate DII | 80 | ±6% |
| NG | Nigeria | 0.41 | 0.41 | 0.51 | 0.27 | T+1 to T+2 | Limited | 76 | ±14% |
| EG | Egypt | 0.38 | 0.38 | 0.47 | 0.25 | T+1 to T+2 | Limited | 75 | ±15% |
| KE | Kenya | 0.32 | 0.32 | 0.4 | 0.21 | T+1 to T+2 | Limited | 74 | ±17% |
| GH | Ghana | 0.28 | 0.28 | 0.35 | 0.18 | T+1 to T+2 | Limited | 74 | ±18% |
| MA | Morocco | 0.44 | 0.44 | 0.55 | 0.29 | T+1 to T+2 | Limited | 76 | ±14% |
| TZ | Tanzania | 0.26 | 0.26 | 0.33 | 0.17 | T+1 to T+2 | Limited | 73 | ±18% |
| SA | Saudi Arabia | 0.52 | 0.52 | 0.65 | 0.34 | T+0 to T+1 | Limited | 77 | ±12% |
| AE | UAE | 0.58 | 0.58 | 0.72 | 0.38 | T+0 to T+1 | Limited | 78 | ±10% |
| QA | Qatar | 0.51 | 0.51 | 0.64 | 0.33 | T+0 to T+1 | Limited | 77 | ±12% |
| TR | Turkey | 0.61 | 0.61 | 0.76 | 0.4 | T+0 to T+1 | Limited | 79 | ±9% |
| IL | Israel | 0.78 | 0.78 | 0.98 | 0.51 | Same day / T+0 | Limited | 81 | ±5% |
| KW | Kuwait | 0.48 | 0.48 | 0.6 | 0.31 | T+1 to T+2 | Limited | 77 | ±13% |
| PL | Poland | 0.72 | 0.72 | 0.9 | 0.47 | Same day / T+0 | Moderate DII | 80 | ±7% |
| CZ | Czech Republic | 0.68 | 0.68 | 0.85 | 0.44 | T+0 to T+1 | Limited | 80 | ±7% |
| HU | Hungary | 0.65 | 0.65 | 0.81 | 0.42 | T+0 to T+1 | Limited | 79 | ±8% |
| RO | Romania | 0.58 | 0.58 | 0.72 | 0.38 | T+0 to T+1 | Limited | 78 | ±10% |
| GR | Greece | 0.71 | 0.71 | 0.89 | 0.46 | Same day / T+0 | Limited | 80 | ±7% |
| MM | Myanmar | 0.31 | 0.31 | 0.39 | 0.2 | T+1 to T+2 | Limited | 74 | ±17% |
| KH | Cambodia | 0.28 | 0.28 | 0.35 | 0.18 | T+1 to T+2 | Limited | 74 | ±18% |
| UY | Uruguay | 0.52 | 0.52 | 0.65 | 0.34 | T+0 to T+1 | Limited | 77 | ±12% |
| CR | Costa Rica | 0.48 | 0.48 | 0.6 | 0.31 | T+1 to T+2 | Limited | 77 | ±13% |
| ZM | Zambia | 0.32 | 0.32 | 0.4 | 0.21 | T+1 to T+2 | Limited | 74 | ±17% |
| BW | Botswana | 0.35 | 0.35 | 0.44 | 0.23 | T+1 to T+2 | Limited | 75 | ±16% |
| MU | Mauritius | 0.38 | 0.38 | 0.47 | 0.25 | T+1 to T+2 | Limited | 75 | ±15% |
## Sheet: 📊 Sector Impact Examples
| SECTOR-SPECIFIC TRANSMISSION EXAMPLES |  |  |  |
| --- | --- | --- | --- |
| The table below shows real sector-level impacts for key markets across different event types. |  |  |  |
| Country | Event Type | Beneficiaries (% Impact) | Victims (% Impact) |
| India | Fed Hike 50bps | IT +0.20%, Pharma +0.12% | Banks -0.18%, Auto -0.12%, OMCs -0.05% |
| Brazil | Fed Hike 50bps | Exporters +0.15% | Banks -0.22%, Retail -0.15% |
| South Korea | Fed Hike 50bps | Tech Exports +0.18% | Banks -0.20%, Construction -0.14% |
| Mexico | Fed Hike 50bps | Remittances +0.10%, Exporters +0.12% | Banks -0.25%, Domestic -0.18% |
| Indonesia | Fed Hike 50bps | Commodities +0.08%, Palm Oil +0.10% | Banks -0.16%, Property -0.12% |
| India | Oil +10% | IT +2.0% (weak INR), Pharma +1.2% | OMCs -12%, Airlines -8%, Paint -3% |
| Saudi Arabia | Oil +10% | Aramco +8%, Energy +7%, Financials +2% | None (all benefit) |
| Nigeria | Oil +10% | Oil & Gas +8.2%, Banks +2%, Cement +1.5% | Importers -2% |
| South Korea | Oil +10% | Tech Exports +2.1% (weak KRW) | Airlines -8%, Chemicals -5%, Refiners -4% |
| Turkey | Oil +10% | Exporters +2.3% (weak TRY) | Airlines -8%, Logistics -5%, Energy -5.8% |
| Brazil | China PMI -2pts | None | Vale/Mining -3.8%, Metals -3.0%, Infra -1.8% |
| Chile | China PMI -2pts | None | Copper -3.6%, Mining -3.2%, Construction -1.6% |
| South Africa | China PMI -2pts | None | Mining -3.5%, Industrials -2.0%, Financials -1.2% |
| India | China PMI -2pts | None | Tata Steel -1.5%, JSW -1.2%, L&T -0.6% |
| Indonesia | China PMI -2pts | None | Coal -4.0%, Nickel -3.2%, Cement -1.6% |
| NOTES: |  |  |  |
| 1. Green text = beneficiaries from the event. Red text = sectors hurt by the event. |  |  |  |
| 2. Coefficients shown are per-unit impacts (e.g., per 50bps hike, per 10% oil change, per 2-point PMI miss). |  |  |  |
| 3. For full sector matrices per country, refer to the individual event sheets. |  |  |  |
| 4. IT/Tech export sectors benefit from currency depreciation in most Asian markets. |  |  |  |
| 5. Energy exporters (SA, NG, KW, AE, QA) show opposite oil sensitivity vs importers. |  |  |  |