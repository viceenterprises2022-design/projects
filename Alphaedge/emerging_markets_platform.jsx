import { useState, useEffect, useCallback } from "react";

// ─── COMPREHENSIVE EMERGING MARKETS DATA ────────────────────────────────────

const EMERGING_MARKETS = {
  "South Asia": [
    { id:"IN", name:"India",       flag:"🇮🇳", index:"NIFTY 50",  indexVal:"21,345", chg:-0.31, mktCap:"$3.9T",  currency:"INR",  fxRate:"83.42",  fxChg:-0.21, uspxCorr:0.68, oilCorr:-0.42, usdCorr:-0.58, goldCorr:-0.22, chinaCorr:0.45, riskScore:38, gdpGrowth:6.8,  inflation:4.8,  interestRate:6.50, currentAccount:-1.2, debtGDP:83,  tier:"Frontier-Plus", color:"#f59e0b", drivers:["IT Exports","FII Flows","Oil Imports","Monsoon"],     keyRisk:"Oil Price Shock",    bondYield:7.10 },
    { id:"PK", name:"Pakistan",    flag:"🇵🇰", index:"KSE-100",   indexVal:"62,410", chg: 0.84, mktCap:"$52B",   currency:"PKR",  fxRate:"278.5",  fxChg:-0.82, uspxCorr:0.28, oilCorr:-0.55, usdCorr:-0.71, goldCorr: 0.21, chinaCorr:0.38, riskScore:78, gdpGrowth:1.8,  inflation:22.4, interestRate:22.0, currentAccount:-3.8, debtGDP:77,  tier:"Frontier",      color:"#22c55e", drivers:["IMF Program","Remittances","China CPEC","Agriculture"], keyRisk:"IMF Bailout Risk",   bondYield:22.5 },
    { id:"BD", name:"Bangladesh",  flag:"🇧🇩", index:"DSEX",      indexVal:"6,245",  chg:-0.42, mktCap:"$48B",   currency:"BDT",  fxRate:"110.2",  fxChg:-0.15, uspxCorr:0.31, oilCorr:-0.38, usdCorr:-0.48, goldCorr: 0.12, chinaCorr:0.42, riskScore:52, gdpGrowth:5.5,  inflation:9.2,  interestRate:8.75, currentAccount:-1.4, debtGDP:38,  tier:"Frontier",      color:"#3b82f6", drivers:["Garment Exports","Remittances","China FDI"],           keyRisk:"Political Instability", bondYield:9.2 },
    { id:"LK", name:"Sri Lanka",   flag:"🇱🇰", index:"CSE All",   indexVal:"8,912",  chg: 1.24, mktCap:"$7B",    currency:"LKR",  fxRate:"318.4",  fxChg: 0.34, uspxCorr:0.22, oilCorr:-0.48, usdCorr:-0.61, goldCorr: 0.18, chinaCorr:0.29, riskScore:72, gdpGrowth:2.8,  inflation:12.1, interestRate:9.00, currentAccount:-3.2, debtGDP:115, tier:"Frontier",      color:"#ef4444", drivers:["Tourism","Tea Exports","IMF Recovery"],               keyRisk:"Debt Restructuring",  bondYield:10.8 },
  ],
  "Southeast Asia": [
    { id:"ID", name:"Indonesia",   flag:"🇮🇩", index:"IDX Comp",  indexVal:"7,282",  chg: 0.18, mktCap:"$678B",  currency:"IDR",  fxRate:"15,820", fxChg:-0.12, uspxCorr:0.55, oilCorr: 0.42, usdCorr:-0.52, goldCorr: 0.18, chinaCorr:0.58, riskScore:42, gdpGrowth:5.0,  inflation:2.8,  interestRate:6.00, currentAccount:-0.4, debtGDP:39,  tier:"Emerging",      color:"#ef4444", drivers:["Coal Exports","Palm Oil","Nickel","China Demand"],     keyRisk:"Coal Demand Collapse",bondYield:6.85 },
    { id:"MY", name:"Malaysia",    flag:"🇲🇾", index:"KLCI",      indexVal:"1,524",  chg:-0.24, mktCap:"$384B",  currency:"MYR",  fxRate:"4.74",   fxChg:-0.18, uspxCorr:0.58, oilCorr: 0.35, usdCorr:-0.61, goldCorr: 0.14, chinaCorr:0.62, riskScore:36, gdpGrowth:4.4,  inflation:1.8,  interestRate:3.00, currentAccount: 1.8, debtGDP:66,  tier:"Emerging",      color:"#3b82f6", drivers:["Palm Oil","Semiconductor","LNG Exports","Tourism"],   keyRisk:"USD Strength",       bondYield:3.95 },
    { id:"TH", name:"Thailand",    flag:"🇹🇭", index:"SET",       indexVal:"1,415",  chg:-0.38, mktCap:"$488B",  currency:"THB",  fxRate:"35.2",   fxChg:-0.09, uspxCorr:0.52, oilCorr:-0.28, usdCorr:-0.55, goldCorr: 0.08, chinaCorr:0.55, riskScore:44, gdpGrowth:2.5,  inflation:0.8,  interestRate:2.50, currentAccount: 1.2, debtGDP:61,  tier:"Emerging",      color:"#8b5cf6", drivers:["Tourism","Auto Exports","Electronics","Agriculture"],  keyRisk:"Political Instability",bondYield:2.95 },
    { id:"PH", name:"Philippines", flag:"🇵🇭", index:"PSEi",      indexVal:"6,892",  chg: 0.52, mktCap:"$218B",  currency:"PHP",  fxRate:"57.8",   fxChg:-0.22, uspxCorr:0.51, oilCorr:-0.31, usdCorr:-0.62, goldCorr: 0.11, chinaCorr:0.44, riskScore:46, gdpGrowth:5.6,  inflation:3.2,  interestRate:6.50, currentAccount:-3.4, debtGDP:57,  tier:"Emerging",      color:"#22c55e", drivers:["Remittances","BPO Services","Real Estate","Consumption"],keyRisk:"Oil Imports",       bondYield:6.75 },
    { id:"VN", name:"Vietnam",     flag:"🇻🇳", index:"VN-Index",  indexVal:"1,248",  chg: 0.72, mktCap:"$182B",  currency:"VND",  fxRate:"25,420", fxChg:-0.08, uspxCorr:0.44, oilCorr:-0.18, usdCorr:-0.51, goldCorr: 0.22, chinaCorr:0.52, riskScore:39, gdpGrowth:6.2,  inflation:3.4,  interestRate:4.50, currentAccount: 2.8, debtGDP:37,  tier:"Frontier-Plus", color:"#f59e0b", drivers:["Manufacturing","Electronics Exports","FDI Inflows","Tourism"], keyRisk:"China Slowdown",   bondYield:4.85 },
    { id:"SG", name:"Singapore",   flag:"🇸🇬", index:"STI",       indexVal:"3,248",  chg:-0.18, mktCap:"$421B",  currency:"SGD",  fxRate:"1.345",  fxChg:-0.14, uspxCorr:0.61, oilCorr: 0.38, usdCorr:-0.52, goldCorr: 0.18, chinaCorr:0.58, riskScore:18, gdpGrowth:1.1,  inflation:3.2,  interestRate:3.86, currentAccount:17.0, debtGDP:168, tier:"Developed-EM",  color:"#22d3ee", drivers:["Trade Hub","REIT Yields","Finance","Tech"],            keyRisk:"Global Trade Slowdown", bondYield:3.28 },
  ],
  "East Asia": [
    { id:"CN", name:"China",       flag:"🇨🇳", index:"CSI 300",   indexVal:"3,412",  chg:-0.18, mktCap:"$9.4T",  currency:"CNY",  fxRate:"7.234",  fxChg: 0.04, uspxCorr:0.54, oilCorr: 0.12, usdCorr:-0.41, goldCorr: 0.05, chinaCorr:1.00, riskScore:55, gdpGrowth:4.8,  inflation:0.2,  interestRate:3.45, currentAccount: 1.8, debtGDP:288, tier:"Emerging",      color:"#ef4444", drivers:["Manufacturing PMI","Property Sector","Credit Impulse","Exports"], keyRisk:"Property Crisis",  bondYield:2.58 },
    { id:"KR", name:"South Korea", flag:"🇰🇷", index:"KOSPI",     indexVal:"2,584",  chg:-0.41, mktCap:"$1.6T",  currency:"KRW",  fxRate:"1,328",  fxChg:-0.18, uspxCorr:0.72, oilCorr:-0.22, usdCorr:-0.68, goldCorr:-0.12, chinaCorr:0.62, riskScore:28, gdpGrowth:2.5,  inflation:2.6,  interestRate:3.50, currentAccount: 1.4, debtGDP:54,  tier:"Emerging",      color:"#3b82f6", drivers:["Semiconductor","K-Pop/Tech","China Exports","Auto"],   keyRisk:"China Slowdown",     bondYield:3.62 },
    { id:"TW", name:"Taiwan",      flag:"🇹🇼", index:"TAIEX",     indexVal:"19,842", chg: 0.28, mktCap:"$1.9T",  currency:"TWD",  fxRate:"31.8",   fxChg:-0.12, uspxCorr:0.76, oilCorr:-0.18, usdCorr:-0.72, goldCorr:-0.15, chinaCorr:0.48, riskScore:58, gdpGrowth:2.6,  inflation:2.1,  interestRate:2.00, currentAccount:12.8, debtGDP:28,  tier:"Emerging",      color:"#22c55e", drivers:["TSMC/Semiconductors","USD Earnings","AI Demand"],     keyRisk:"Geopolitical Risk",  bondYield:1.54 },
    { id:"HK", name:"Hong Kong",   flag:"🇭🇰", index:"Hang Seng", indexVal:"16,284", chg:-0.54, mktCap:"$3.1T",  currency:"HKD",  fxRate:"7.822",  fxChg: 0.01, uspxCorr:0.62, oilCorr:-0.08, usdCorr:-0.18, goldCorr:-0.04, chinaCorr:0.78, riskScore:62, gdpGrowth:2.2,  inflation:2.4,  interestRate:5.75, currentAccount: 6.8, debtGDP:0,   tier:"Developed-EM",  color:"#f59e0b", drivers:["China Proxy","Finance Hub","Real Estate","USD Peg"],   keyRisk:"China Regulatory",   bondYield:4.28 },
  ],
  "Latin America": [
    { id:"BR", name:"Brazil",      flag:"🇧🇷", index:"Bovespa",   indexVal:"125,840",chg: 0.42, mktCap:"$841B",  currency:"BRL",  fxRate:"4.97",   fxChg:-0.28, uspxCorr:0.58, oilCorr: 0.52, usdCorr:-0.71, goldCorr: 0.32, chinaCorr:0.55, riskScore:55, gdpGrowth:2.1,  inflation:4.5,  interestRate:10.75,currentAccount:-1.5, debtGDP:89,  tier:"Emerging",      color:"#22c55e", drivers:["Commodities","Iron Ore","Soybean","Oil (Petrobras)"],  keyRisk:"Political Risk",     bondYield:10.92 },
    { id:"MX", name:"Mexico",      flag:"🇲🇽", index:"IPC BMV",   indexVal:"54,218", chg:-0.18, mktCap:"$421B",  currency:"MXN",  fxRate:"17.12",  fxChg:-0.14, uspxCorr:0.68, oilCorr: 0.42, usdCorr:-0.74, goldCorr: 0.15, chinaCorr:0.31, riskScore:48, gdpGrowth:2.4,  inflation:4.6,  interestRate:11.25,currentAccount:-0.4, debtGDP:49,  tier:"Emerging",      color:"#ef4444", drivers:["US Trade (USMCA)","Remittances","Oil","Nearshoring"],  keyRisk:"US Policy Risk",     bondYield:9.84 },
    { id:"CL", name:"Chile",       flag:"🇨🇱", index:"IPSA",      indexVal:"6,284",  chg: 0.31, mktCap:"$124B",  currency:"CLP",  fxRate:"952",    fxChg:-0.22, uspxCorr:0.52, oilCorr: 0.18, usdCorr:-0.65, goldCorr: 0.28, chinaCorr:0.71, riskScore:38, gdpGrowth:1.8,  inflation:3.8,  interestRate:7.25, currentAccount:-3.8, debtGDP:37,  tier:"Emerging",      color:"#3b82f6", drivers:["Copper (China demand)","Lithium","Agriculture"],       keyRisk:"Copper Price",       bondYield:5.82 },
    { id:"CO", name:"Colombia",    flag:"🇨🇴", index:"COLCAP",    indexVal:"1,248",  chg:-0.28, mktCap:"$56B",   currency:"COP",  fxRate:"3,940",  fxChg:-0.48, uspxCorr:0.44, oilCorr: 0.68, usdCorr:-0.72, goldCorr: 0.22, chinaCorr:0.28, riskScore:58, gdpGrowth:1.4,  inflation:7.2,  interestRate:12.75,currentAccount:-3.2, debtGDP:55,  tier:"Emerging",      color:"#f59e0b", drivers:["Oil Exports","Coal","Agriculture","Remittances"],      keyRisk:"Oil Price Fall",     bondYield:11.48 },
    { id:"PE", name:"Peru",        flag:"🇵🇪", index:"S&P/BVL",   indexVal:"12,841", chg: 0.18, mktCap:"$68B",   currency:"PEN",  fxRate:"3.78",   fxChg:-0.08, uspxCorr:0.48, oilCorr: 0.28, usdCorr:-0.62, goldCorr: 0.58, chinaCorr:0.61, riskScore:52, gdpGrowth:2.8,  inflation:3.2,  interestRate:6.75, currentAccount:-0.8, debtGDP:32,  tier:"Emerging",      color:"#ef4444", drivers:["Copper","Gold","Silver","Zinc (China demand)"],        keyRisk:"Political Instability",bondYield:6.42 },
    { id:"AR", name:"Argentina",   flag:"🇦🇷", index:"Merval",    indexVal:"1,482K", chg: 2.48, mktCap:"$41B",   currency:"ARS",  fxRate:"862",    fxChg:-2.14, uspxCorr:0.22, oilCorr: 0.18, usdCorr:-0.85, goldCorr: 0.42, chinaCorr:0.18, riskScore:88, gdpGrowth:-1.8, inflation:211.4,interestRate:60.0, currentAccount:-0.8, debtGDP:88,  tier:"Frontier",      color:"#22c55e", drivers:["IMF Program","Soybean","Lithium","Milei Reforms"],     keyRisk:"Hyperinflation",     bondYield:42.8 },
  ],
  "EMEA — Africa": [
    { id:"ZA", name:"South Africa",flag:"🇿🇦", index:"JSE All",   indexVal:"72,418", chg:-0.28, mktCap:"$748B",  currency:"ZAR",  fxRate:"18.82",  fxChg:-0.48, uspxCorr:0.55, oilCorr: 0.42, usdCorr:-0.72, goldCorr: 0.65, chinaCorr:0.44, riskScore:62, gdpGrowth:0.5,  inflation:5.4,  interestRate:8.25, currentAccount:-1.8, debtGDP:72,  tier:"Emerging",      color:"#22c55e", drivers:["Gold","Platinum","Coal","China Demand"],               keyRisk:"Power Crisis (Eskom)",bondYield:9.22 },
    { id:"NG", name:"Nigeria",     flag:"🇳🇬", index:"NGX All",   indexVal:"98,412", chg: 1.24, mktCap:"$38B",   currency:"NGN",  fxRate:"1,512",  fxChg:-1.82, uspxCorr:0.28, oilCorr: 0.82, usdCorr:-0.68, goldCorr: 0.12, chinaCorr:0.22, riskScore:72, gdpGrowth:2.9,  inflation:29.2, interestRate:26.25,currentAccount: 0.8, debtGDP:38,  tier:"Frontier",      color:"#ef4444", drivers:["Oil (NNPC)","Agriculture","Diaspora Remittances"],     keyRisk:"FX Volatility",      bondYield:18.5 },
    { id:"EG", name:"Egypt",       flag:"🇪🇬", index:"EGX 30",    indexVal:"28,412", chg: 0.82, mktCap:"$44B",   currency:"EGP",  fxRate:"48.2",   fxChg:-0.42, uspxCorr:0.31, oilCorr: 0.38, usdCorr:-0.71, goldCorr: 0.28, chinaCorr:0.28, riskScore:68, gdpGrowth:3.8,  inflation:31.8, interestRate:27.75,currentAccount:-4.8, debtGDP:92,  tier:"Frontier",      color:"#f59e0b", drivers:["Suez Canal","Tourism","Gas Exports","IMF Program"],   keyRisk:"Currency Devaluation",bondYield:28.4 },
    { id:"KE", name:"Kenya",       flag:"🇰🇪", index:"NSE 20",    indexVal:"1,842",  chg:-0.18, mktCap:"$12B",   currency:"KES",  fxRate:"128.4",  fxChg:-0.28, uspxCorr:0.24, oilCorr:-0.28, usdCorr:-0.58, goldCorr: 0.18, chinaCorr:0.32, riskScore:58, gdpGrowth:5.0,  inflation:5.8,  interestRate:13.0, currentAccount:-5.2, debtGDP:68,  tier:"Frontier",      color:"#22c55e", drivers:["Tea","Coffee","Fintech (M-Pesa)","Horticulture"],     keyRisk:"USD Debt Burden",    bondYield:16.2 },
    { id:"GH", name:"Ghana",       flag:"🇬🇭", index:"GSE Comp",  indexVal:"3,412",  chg: 0.48, mktCap:"$5B",    currency:"GHS",  fxRate:"12.8",   fxChg:-0.58, uspxCorr:0.21, oilCorr: 0.28, usdCorr:-0.72, goldCorr: 0.58, chinaCorr:0.18, riskScore:74, gdpGrowth:3.2,  inflation:24.2, interestRate:29.0, currentAccount:-3.8, debtGDP:88,  tier:"Frontier",      color:"#f59e0b", drivers:["Gold","Cocoa","Oil (Offshore)","IMF Recovery"],       keyRisk:"Debt Restructuring",  bondYield:28.8 },
    { id:"MA", name:"Morocco",     flag:"🇲🇦", index:"MASI",      indexVal:"12,841", chg: 0.22, mktCap:"$58B",   currency:"MAD",  fxRate:"9.98",   fxChg:-0.08, uspxCorr:0.34, oilCorr:-0.28, usdCorr:-0.48, goldCorr: 0.18, chinaCorr:0.24, riskScore:42, gdpGrowth:3.2,  inflation:5.2,  interestRate:3.00, currentAccount:-3.2, debtGDP:70,  tier:"Frontier",      color:"#3b82f6", drivers:["Phosphates","Tourism","Auto Exports","Remittances"],  keyRisk:"Europe Slowdown",    bondYield:5.12 },
    { id:"TZ", name:"Tanzania",    flag:"🇹🇿", index:"DSE",       indexVal:"2,184",  chg: 0.12, mktCap:"$4B",    currency:"TZS",  fxRate:"2,512",  fxChg:-0.18, uspxCorr:0.18, oilCorr:-0.12, usdCorr:-0.42, goldCorr: 0.42, chinaCorr:0.28, riskScore:48, gdpGrowth:5.1,  inflation:3.2,  interestRate:6.00, currentAccount:-4.8, debtGDP:42,  tier:"Frontier",      color:"#22c55e", drivers:["Gold","Tourism (Serengeti)","Agriculture","Gas (LNG)"],keyRisk:"Infrastructure Gap", bondYield:8.4 },
  ],
  "Middle East": [
    { id:"SA", name:"Saudi Arabia",flag:"🇸🇦", index:"Tadawul",   indexVal:"12,284", chg: 0.34, mktCap:"$2.9T",  currency:"SAR",  fxRate:"3.750",  fxChg: 0.00, uspxCorr:0.48, oilCorr: 0.82, usdCorr:-0.24, goldCorr: 0.28, chinaCorr:0.42, riskScore:32, gdpGrowth:0.8,  inflation:1.8,  interestRate:6.00, currentAccount: 3.8, debtGDP:24,  tier:"Emerging",      color:"#22c55e", drivers:["Oil (OPEC+)","Vision 2030","NEOM","Aramco"],          keyRisk:"Oil Price Fall",     bondYield:5.28 },
    { id:"AE", name:"UAE",         flag:"🇦🇪", index:"DFM",       indexVal:"4,182",  chg: 0.18, mktCap:"$358B",  currency:"AED",  fxRate:"3.673",  fxChg: 0.00, uspxCorr:0.44, oilCorr: 0.68, usdCorr:-0.18, goldCorr: 0.32, chinaCorr:0.38, riskScore:25, gdpGrowth:4.2,  inflation:2.2,  interestRate:5.40, currentAccount: 8.8, debtGDP:29,  tier:"Emerging",      color:"#f59e0b", drivers:["Oil","Tourism","Finance Hub","Real Estate"],           keyRisk:"Oil Dependency",     bondYield:4.82 },
    { id:"QA", name:"Qatar",       flag:"🇶🇦", index:"QSE",       indexVal:"10,284", chg:-0.12, mktCap:"$152B",  currency:"QAR",  fxRate:"3.641",  fxChg: 0.00, uspxCorr:0.38, oilCorr: 0.72, usdCorr:-0.18, goldCorr: 0.18, chinaCorr:0.44, riskScore:22, gdpGrowth:1.8,  inflation:2.8,  interestRate:5.75, currentAccount:12.4, debtGDP:42,  tier:"Emerging",      color:"#3b82f6", drivers:["LNG Exports","Finance","FIFA Legacy","Sovereign Fund"],keyRisk:"LNG Price Volatility",bondYield:4.52 },
    { id:"TR", name:"Turkey",      flag:"🇹🇷", index:"BIST 100",  indexVal:"8,284K", chg: 1.82, mktCap:"$142B",  currency:"TRY",  fxRate:"32.4",   fxChg:-0.84, uspxCorr:0.41, oilCorr:-0.18, usdCorr:-0.82, goldCorr: 0.52, chinaCorr:0.28, riskScore:72, gdpGrowth:3.2,  inflation:68.5, interestRate:50.0, currentAccount:-4.2, debtGDP:32,  tier:"Emerging",      color:"#ef4444", drivers:["Manufacturing","Tourism","Remittances","Defense"],     keyRisk:"Lira Depreciation",  bondYield:42.8 },
    { id:"IL", name:"Israel",      flag:"🇮🇱", index:"TA-125",    indexVal:"1,784",  chg:-0.82, mktCap:"$218B",  currency:"ILS",  fxRate:"3.68",   fxChg: 0.28, uspxCorr:0.55, oilCorr:-0.12, usdCorr:-0.48, goldCorr: 0.28, chinaCorr:0.22, riskScore:68, gdpGrowth:0.8,  inflation:2.8,  interestRate:4.75, currentAccount: 3.8, debtGDP:58,  tier:"Developed-EM",  color:"#3b82f6", drivers:["Tech/Cybersecurity","Pharma","Tourism","Defense"],     keyRisk:"Geopolitical Risk",  bondYield:4.82 },
    { id:"KW", name:"Kuwait",      flag:"🇰🇼", index:"Boursa KW", indexVal:"7,284",  chg: 0.12, mktCap:"$98B",   currency:"KWD",  fxRate:"0.307",  fxChg:-0.02, uspxCorr:0.38, oilCorr: 0.78, usdCorr:-0.18, goldCorr: 0.12, chinaCorr:0.38, riskScore:28, gdpGrowth:0.2,  inflation:3.2,  interestRate:4.25, currentAccount:18.2, debtGDP:3,   tier:"Emerging",      color:"#f59e0b", drivers:["Oil (KPC)","Sovereign Fund","Finance","Real Estate"],  keyRisk:"Oil Dependency",     bondYield:4.12 },
  ],
  "Emerging Europe": [
    { id:"PL", name:"Poland",      flag:"🇵🇱", index:"WIG20",     indexVal:"2,384",  chg:-0.18, mktCap:"$182B",  currency:"PLN",  fxRate:"4.02",   fxChg:-0.08, uspxCorr:0.62, oilCorr:-0.18, usdCorr:-0.68, goldCorr: 0.12, chinaCorr:0.38, riskScore:38, gdpGrowth:2.8,  inflation:3.8,  interestRate:5.75, currentAccount:-1.8, debtGDP:49,  tier:"Emerging",      color:"#3b82f6", drivers:["EU Funds","Manufacturing","Banking","Energy Transition"], keyRisk:"Russia Proximity",  bondYield:5.42 },
    { id:"CZ", name:"Czech Rep.",  flag:"🇨🇿", index:"PX",        indexVal:"1,484",  chg: 0.08, mktCap:"$42B",   currency:"CZK",  fxRate:"22.8",   fxChg:-0.04, uspxCorr:0.58, oilCorr:-0.14, usdCorr:-0.64, goldCorr: 0.08, chinaCorr:0.32, riskScore:28, gdpGrowth:1.2,  inflation:2.4,  interestRate:5.75, currentAccount: 0.8, debtGDP:44,  tier:"Emerging",      color:"#22c55e", drivers:["Auto Manufacturing","EU Trade","Finance"],             keyRisk:"Germany Recession",  bondYield:4.82 },
    { id:"HU", name:"Hungary",     flag:"🇭🇺", index:"BUX",       indexVal:"58,284", chg:-0.28, mktCap:"$32B",   currency:"HUF",  fxRate:"358",    fxChg:-0.22, uspxCorr:0.54, oilCorr:-0.22, usdCorr:-0.72, goldCorr: 0.18, chinaCorr:0.28, riskScore:52, gdpGrowth:0.5,  inflation:4.8,  interestRate:9.75, currentAccount:-3.4, debtGDP:73,  tier:"Emerging",      color:"#ef4444", drivers:["Auto/Manufacturing","EU Funds","Banking","Tourism"],   keyRisk:"Energy Costs",       bondYield:6.82 },
    { id:"RO", name:"Romania",     flag:"🇷🇴", index:"BET",       indexVal:"17,284", chg: 0.22, mktCap:"$28B",   currency:"RON",  fxRate:"4.97",   fxChg:-0.04, uspxCorr:0.52, oilCorr:-0.18, usdCorr:-0.62, goldCorr: 0.14, chinaCorr:0.24, riskScore:48, gdpGrowth:2.8,  inflation:5.8,  interestRate:7.00, currentAccount:-7.2, debtGDP:49,  tier:"Emerging",      color:"#f59e0b", drivers:["IT Services","Auto","Agriculture","EU Funds"],         keyRisk:"Large Deficit",      bondYield:6.42 },
    { id:"GR", name:"Greece",      flag:"🇬🇷", index:"Athens GE", indexVal:"1,484",  chg: 0.38, mktCap:"$52B",   currency:"EUR",  fxRate:"1.085",  fxChg:-0.08, uspxCorr:0.61, oilCorr:-0.22, usdCorr:-0.78, goldCorr: 0.18, chinaCorr:0.28, riskScore:44, gdpGrowth:2.1,  inflation:3.2,  interestRate:4.50, currentAccount:-7.8, debtGDP:161, tier:"Developed-EM",  color:"#3b82f6", drivers:["Tourism","Shipping","Agriculture","Real Estate"],      keyRisk:"Debt Level",         bondYield:3.58 },
  ],
};

// Global macro anchors
const MACRO_ANCHORS = {
  "SPX":    { val: "4,892",  chg: -0.45, label: "S&P 500",     color: "#3b82f6" },
  "DXY":    { val: "104.2",  chg:  0.38, label: "DXY Index",   color: "#f59e0b" },
  "BRENT":  { val: "$87.2",  chg:  1.82, label: "Brent Crude", color: "#ef4444" },
  "GOLD":   { val: "$2,042", chg:  0.82, label: "Gold",        color: "#eab308" },
  "VIX":    { val: "18.4",   chg:  8.24, label: "VIX",         color: "#8b5cf6" },
  "UST10Y": { val: "4.28%",  chg:  0.12, label: "US 10Y",      color: "#22c55e" },
};

const REGION_ORDER = ["South Asia","Southeast Asia","East Asia","Latin America","EMEA — Africa","Middle East","Emerging Europe"];

const ALL_MARKETS = REGION_ORDER.flatMap(r => EMERGING_MARKETS[r]);

// ─── UTILITY HELPERS ─────────────────────────────────────────────────────────

const corrColor = (v) => {
  if (v >= 0.7) return "#ef4444";
  if (v >= 0.4) return "#f59e0b";
  if (v >= 0.1) return "#22c55e";
  if (v >= -0.1) return "#64748b";
  if (v >= -0.4) return "#22d3ee";
  return "#3b82f6";
};

const riskColor = (s) => s < 35 ? "#22c55e" : s < 55 ? "#f59e0b" : s < 70 ? "#f97316" : "#ef4444";
const riskLabel = (s) => s < 35 ? "LOW" : s < 55 ? "MEDIUM" : s < 70 ? "HIGH" : "CRITICAL";

const tierColor = {
  "Developed-EM": "#22d3ee", "Emerging": "#22c55e", "Frontier-Plus": "#f59e0b", "Frontier": "#f97316"
};

function MiniBar({ value, max = 1, color = "#f59e0b", h = 4, negative = false }) {
  const w = Math.min(Math.abs(value) / max, 1) * 100;
  return (
    <div style={{ background: "#1a2035", borderRadius: 2, height: h, width: "100%", overflow: "hidden" }}>
      <div style={{ width: `${w}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.6s ease" }} />
    </div>
  );
}

function CorrBadge({ value, size = 36 }) {
  const c = corrColor(value);
  return (
    <div style={{ width: size, height: size, borderRadius: 6, background: c + "22", border: `1px solid ${c}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: size * 0.28, fontFamily: "monospace", fontWeight: 700, color: c, flexShrink: 0 }}>
      {value.toFixed(2)}
    </div>
  );
}

function RiskPill({ score }) {
  const c = riskColor(score);
  return (
    <span style={{ fontSize: 9, padding: "2px 6px", borderRadius: 3, background: c + "22", color: c, fontWeight: 700, letterSpacing: 1, border: `1px solid ${c}44` }}>
      {riskLabel(score)}
    </span>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────

export default function EmergingMarketsEngine() {
  const [activeView, setActiveView] = useState("heatmap");
  const [selectedRegion, setSelectedRegion] = useState("All");
  const [selectedMarket, setSelectedMarket] = useState(null);
  const [sortBy, setSortBy] = useState("mktCap");
  const [filterTier, setFilterTier] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [corrDriver, setCorrDriver] = useState("uspxCorr");
  const [tick, setTick] = useState(0);
  const [crisisProb, setCrisisProb] = useState(0.63);

  useEffect(() => {
    const t = setInterval(() => {
      setTick(p => p + 1);
      setCrisisProb(p => Math.max(0.4, Math.min(0.88, p + (Math.random() - 0.5) * 0.015)));
    }, 2500);
    return () => clearInterval(t);
  }, []);

  const filteredMarkets = ALL_MARKETS.filter(m => {
    const regionOk = selectedRegion === "All" || REGION_ORDER.find(r => EMERGING_MARKETS[r]?.find(x => x.id === m.id) && r === selectedRegion);
    const tierOk = filterTier === "All" || m.tier === filterTier;
    const searchOk = !searchQuery || m.name.toLowerCase().includes(searchQuery.toLowerCase()) || m.id.toLowerCase().includes(searchQuery.toLowerCase());
    return regionOk && tierOk && searchOk;
  });

  const views = [
    { id: "heatmap", label: "World Heatmap", icon: "🌍" },
    { id: "grid", label: "Market Grid", icon: "⚡" },
    { id: "correlations", label: "Correlation Atlas", icon: "🔗" },
    { id: "risk", label: "Risk Radar", icon: "⚠" },
    { id: "macro", label: "Macro Flows", icon: "📊" },
    { id: "detail", label: "Market Deep Dive", icon: "🔬" },
  ];

  return (
    <div style={{ background: "#06090f", color: "#e2e8f0", fontFamily: "'IBM Plex Sans', sans-serif", minHeight: "100vh", fontSize: 12 }}>

      {/* ── HEADER ── */}
      <header style={{ background: "#080c16", borderBottom: "1px solid #0e1628", padding: "0 20px", display: "flex", alignItems: "center", gap: 16, height: 52, position: "sticky", top: 0, zIndex: 100, backdropFilter: "blur(12px)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 32, height: 32, background: "linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #8b5cf6 100%)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, boxShadow: "0 0 20px #f59e0b44" }}>⬡</div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 13, letterSpacing: 2, color: "#f8fafc" }}>ALPHA<span style={{ color: "#f59e0b" }}>EDGE</span> <span style={{ color: "#475569", fontWeight: 400 }}>|</span> <span style={{ color: "#22d3ee", fontSize: 11 }}>EMERGING MARKETS</span></div>
            <div style={{ fontSize: 9, color: "#334155", letterSpacing: 1.5, textTransform: "uppercase" }}>45 Markets · 7 Regions · Real-Time Intelligence</div>
          </div>
        </div>

        {/* LIVE ANCHORS */}
        <div style={{ display: "flex", gap: 16, fontSize: 10, fontFamily: "'IBM Plex Mono', monospace", overflow: "hidden" }}>
          {Object.entries(MACRO_ANCHORS).map(([k, v]) => (
            <div key={k} style={{ display: "flex", gap: 5, alignItems: "center", flexShrink: 0 }}>
              <div style={{ width: 3, height: 14, background: v.color, borderRadius: 1 }} />
              <span style={{ color: "#475569" }}>{v.label}</span>
              <span style={{ color: "#f8fafc", fontWeight: 700 }}>{v.val}</span>
              <span style={{ color: v.chg > 0 ? "#22c55e" : "#ef4444" }}>{v.chg > 0 ? "+" : ""}{v.chg.toFixed(2)}%</span>
            </div>
          ))}
        </div>

        <div style={{ marginLeft: "auto", display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{ background: crisisProb > 0.65 ? "#ef444422" : "#f59e0b22", border: `1px solid ${crisisProb > 0.65 ? "#ef4444" : "#f59e0b"}`, borderRadius: 4, padding: "3px 10px", fontSize: 10, color: crisisProb > 0.65 ? "#ef4444" : "#f59e0b", fontWeight: 700, letterSpacing: 1 }}>
            ⚡ CRISIS SIGNAL: {(crisisProb * 100).toFixed(0)}%
          </div>
          <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#22c55e", animation: "pulse 2s infinite", boxShadow: "0 0 8px #22c55e" }} />
            <span style={{ fontSize: 9, color: "#475569" }}>LIVE</span>
          </div>
        </div>
      </header>

      {/* ── NAVIGATION ── */}
      <nav style={{ background: "#080c16", borderBottom: "1px solid #0e1628", padding: "8px 20px", display: "flex", gap: 4, alignItems: "center", flexWrap: "wrap" }}>
        {views.map(v => (
          <button key={v.id} onClick={() => setActiveView(v.id)}
            style={{ padding: "6px 14px", borderRadius: 6, border: "none", cursor: "pointer", fontFamily: "inherit", fontSize: 11, fontWeight: activeView === v.id ? 700 : 400, transition: "all 0.15s",
              background: activeView === v.id ? "#f59e0b15" : "transparent",
              color: activeView === v.id ? "#f59e0b" : "#64748b",
              borderBottom: activeView === v.id ? "2px solid #f59e0b" : "2px solid transparent",
            }}>
            {v.icon} {v.label}
          </button>
        ))}

        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          {/* Search */}
          <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search market..." style={{ background: "#0e1628", border: "1px solid #1e2a3d", borderRadius: 6, padding: "5px 10px", color: "#f8fafc", fontSize: 11, fontFamily: "inherit", outline: "none", width: 140 }} />
          {/* Region filter */}
          <select value={selectedRegion} onChange={e => setSelectedRegion(e.target.value)} style={{ background: "#0e1628", border: "1px solid #1e2a3d", borderRadius: 6, padding: "5px 10px", color: "#94a3b8", fontSize: 11, fontFamily: "inherit", cursor: "pointer" }}>
            <option>All</option>
            {REGION_ORDER.map(r => <option key={r}>{r}</option>)}
          </select>
          {/* Tier filter */}
          <select value={filterTier} onChange={e => setFilterTier(e.target.value)} style={{ background: "#0e1628", border: "1px solid #1e2a3d", borderRadius: 6, padding: "5px 10px", color: "#94a3b8", fontSize: 11, fontFamily: "inherit", cursor: "pointer" }}>
            <option value="All">All Tiers</option>
            {["Developed-EM","Emerging","Frontier-Plus","Frontier"].map(t => <option key={t}>{t}</option>)}
          </select>
        </div>
      </nav>

      {/* ── CONTENT ── */}
      <div style={{ padding: "16px 20px" }}>
        {activeView === "heatmap"      && <HeatmapView markets={filteredMarkets} tick={tick} corrDriver={corrDriver} setCorrDriver={setCorrDriver} onSelect={m => { setSelectedMarket(m); setActiveView("detail"); }} />}
        {activeView === "grid"         && <GridView markets={filteredMarkets} tick={tick} onSelect={m => { setSelectedMarket(m); setActiveView("detail"); }} sortBy={sortBy} setSortBy={setSortBy} />}
        {activeView === "correlations" && <CorrelationAtlas markets={filteredMarkets} />}
        {activeView === "risk"         && <RiskRadar markets={filteredMarkets} tick={tick} />}
        {activeView === "macro"        && <MacroFlows markets={filteredMarkets} />}
        {activeView === "detail"       && <MarketDeepDive market={selectedMarket || ALL_MARKETS[0]} allMarkets={ALL_MARKETS} onBack={() => setActiveView("heatmap")} />}
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.2)} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
        * { box-sizing: border-box; scrollbar-width: thin; scrollbar-color: #1e2a3d #06090f; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #06090f; }
        ::-webkit-scrollbar-thumb { background: #1e2a3d; border-radius: 3px; }
      `}</style>
    </div>
  );
}

// ─── HEATMAP VIEW ─────────────────────────────────────────────────────────────

function HeatmapView({ markets, tick, corrDriver, setCorrDriver, onSelect }) {
  const driverOptions = [
    { id: "uspxCorr", label: "vs S&P 500" },
    { id: "oilCorr",  label: "vs Oil" },
    { id: "usdCorr",  label: "vs USD" },
    { id: "goldCorr", label: "vs Gold" },
    { id: "chinaCorr",label: "vs China PMI" },
  ];

  return (
    <div>
      {/* Controls */}
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
        <span style={{ fontSize: 11, color: "#64748b" }}>Correlation Driver:</span>
        {driverOptions.map(d => (
          <button key={d.id} onClick={() => setCorrDriver(d.id)}
            style={{ padding: "4px 12px", borderRadius: 5, border: "none", cursor: "pointer", fontFamily: "inherit", fontSize: 11, transition: "all 0.15s",
              background: corrDriver === d.id ? "#f59e0b22" : "#0e1628",
              color: corrDriver === d.id ? "#f59e0b" : "#64748b",
              outline: corrDriver === d.id ? "1px solid #f59e0b44" : "1px solid #1e2a3d",
            }}>{d.label}</button>
        ))}
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center", fontSize: 10 }}>
          {[[-1,"#3b82f6","Strong -ve"],[-0.3,"#22d3ee","Weak -ve"],[0.1,"#22c55e","Neutral"],[0.4,"#f59e0b","Weak +ve"],[0.7,"#ef4444","Strong +ve"]].map(([v,c,l]) => (
            <div key={l} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{ width: 10, height: 10, background: c + "44", border: `1px solid ${c}`, borderRadius: 2 }} />
              <span style={{ color: "#475569" }}>{l}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Region blocks */}
      {REGION_ORDER.map(region => {
        const regionMarkets = (EMERGING_MARKETS[region] || []).filter(m => markets.find(x => x.id === m.id));
        if (regionMarkets.length === 0) return null;
        return (
          <div key={region} style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 10, color: "#475569", textTransform: "uppercase", letterSpacing: 2, marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ height: 1, flex: 1, background: "#0e1628" }} />
              {region}
              <div style={{ height: 1, flex: 1, background: "#0e1628" }} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 8 }}>
              {regionMarkets.map(m => {
                const corrVal = m[corrDriver] || 0;
                const bc = corrColor(corrVal);
                return (
                  <div key={m.id} onClick={() => onSelect(m)}
                    style={{ background: bc + "0c", border: `1px solid ${bc}33`, borderRadius: 10, padding: 14, cursor: "pointer", transition: "all 0.2s", animation: "fadeIn 0.4s ease" }}
                    onMouseEnter={e => { e.currentTarget.style.background = bc + "22"; e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = `0 8px 24px ${bc}22`; }}
                    onMouseLeave={e => { e.currentTarget.style.background = bc + "0c"; e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = "none"; }}>
                    
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ fontSize: 18 }}>{m.flag}</span>
                        <div>
                          <div style={{ fontSize: 12, fontWeight: 700, color: "#f8fafc" }}>{m.name}</div>
                          <div style={{ fontSize: 9, color: "#475569" }}>{m.index}</div>
                        </div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: 14, fontWeight: 800, color: bc, fontFamily: "monospace" }}>{corrVal.toFixed(2)}</div>
                        <RiskPill score={m.riskScore} />
                      </div>
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                      <span style={{ fontFamily: "monospace", color: "#94a3b8", fontSize: 11 }}>{m.indexVal}</span>
                      <span style={{ fontFamily: "monospace", color: m.chg >= 0 ? "#22c55e" : "#ef4444", fontSize: 11, fontWeight: 600 }}>{m.chg >= 0 ? "+" : ""}{m.chg.toFixed(2)}%</span>
                    </div>

                    <MiniBar value={Math.abs(corrVal)} max={1} color={bc} h={3} />

                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 9, color: "#475569" }}>
                      <span>{m.currency} {m.fxRate}</span>
                      <span style={{ color: tierColor[m.tier] || "#f59e0b" }}>{m.tier}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── GRID VIEW ────────────────────────────────────────────────────────────────

function GridView({ markets, tick, onSelect, sortBy, setSortBy }) {
  const sorted = [...markets].sort((a, b) => {
    if (sortBy === "risk") return b.riskScore - a.riskScore;
    if (sortBy === "gdp") return b.gdpGrowth - a.gdpGrowth;
    if (sortBy === "inflation") return b.inflation - a.inflation;
    if (sortBy === "uspxCorr") return b.uspxCorr - a.uspxCorr;
    if (sortBy === "chg") return b.chg - a.chg;
    return b.riskScore - a.riskScore;
  });

  const cols = ["Market", "Index", "Change", "GDP %", "CPI %", "Rate %", "Corr SPX", "Corr Oil", "Corr USD", "Risk", "Tier"];
  const sortCols = { "GDP %": "gdp", "CPI %": "inflation", "Corr SPX": "uspxCorr", "Change": "chg", "Risk": "risk" };

  return (
    <div style={{ background: "#080c16", border: "1px solid #0e1628", borderRadius: 12, overflow: "hidden" }}>
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #0e1628", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5 }}>⚡ All Emerging Markets — Live Grid ({markets.length} markets)</div>
        <div style={{ fontSize: 10, color: "#475569" }}>Click column to sort · Click row for deep dive</div>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ background: "#0a0e1a" }}>
              {cols.map(c => (
                <th key={c} onClick={() => sortCols[c] && setSortBy(sortCols[c])}
                  style={{ padding: "8px 10px", textAlign: c === "Market" ? "left" : "center", color: sortBy === sortCols[c] ? "#f59e0b" : "#475569", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, cursor: sortCols[c] ? "pointer" : "default", whiteSpace: "nowrap", borderBottom: "1px solid #0e1628" }}>
                  {c} {sortCols[c] && sortBy === sortCols[c] ? "↓" : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((m, i) => (
              <tr key={m.id} onClick={() => onSelect(m)} style={{ borderBottom: "1px solid #0a0e1a", cursor: "pointer", transition: "background 0.15s", animationDelay: `${i * 0.02}s` }}
                onMouseEnter={e => e.currentTarget.style.background = "#0e162844"}
                onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                <td style={{ padding: "9px 10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 16 }}>{m.flag}</span>
                    <div>
                      <div style={{ fontWeight: 700, color: "#f8fafc" }}>{m.name}</div>
                      <div style={{ fontSize: 9, color: "#475569" }}>{m.id} · {m.currency}</div>
                    </div>
                  </div>
                </td>
                <td style={{ padding: "9px 10px", textAlign: "center", fontFamily: "monospace", color: "#94a3b8", fontSize: 10 }}>{m.indexVal}</td>
                <td style={{ padding: "9px 10px", textAlign: "center", fontFamily: "monospace", color: m.chg >= 0 ? "#22c55e" : "#ef4444", fontWeight: 700 }}>{m.chg >= 0 ? "+" : ""}{m.chg.toFixed(2)}%</td>
                <td style={{ padding: "9px 10px", textAlign: "center", fontFamily: "monospace", color: m.gdpGrowth >= 4 ? "#22c55e" : m.gdpGrowth >= 2 ? "#f59e0b" : "#ef4444", fontWeight: 600 }}>{m.gdpGrowth.toFixed(1)}%</td>
                <td style={{ padding: "9px 10px", textAlign: "center", fontFamily: "monospace", color: m.inflation > 20 ? "#ef4444" : m.inflation > 8 ? "#f97316" : m.inflation > 4 ? "#f59e0b" : "#22c55e", fontWeight: 600 }}>{m.inflation.toFixed(1)}%</td>
                <td style={{ padding: "9px 10px", textAlign: "center", fontFamily: "monospace", color: "#94a3b8" }}>{m.interestRate.toFixed(2)}%</td>
                <td style={{ padding: "9px 10px", textAlign: "center" }}><CorrBadge value={m.uspxCorr} size={32} /></td>
                <td style={{ padding: "9px 10px", textAlign: "center" }}><CorrBadge value={m.oilCorr} size={32} /></td>
                <td style={{ padding: "9px 10px", textAlign: "center" }}><CorrBadge value={m.usdCorr} size={32} /></td>
                <td style={{ padding: "9px 10px", textAlign: "center" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
                    <span style={{ fontFamily: "monospace", color: riskColor(m.riskScore), fontWeight: 700 }}>{m.riskScore}</span>
                    <MiniBar value={m.riskScore} max={100} color={riskColor(m.riskScore)} h={3} />
                  </div>
                </td>
                <td style={{ padding: "9px 10px", textAlign: "center" }}>
                  <span style={{ fontSize: 9, padding: "2px 7px", borderRadius: 3, background: (tierColor[m.tier] || "#f59e0b") + "22", color: tierColor[m.tier] || "#f59e0b", fontWeight: 700 }}>{m.tier}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── CORRELATION ATLAS ────────────────────────────────────────────────────────

function CorrelationAtlas({ markets }) {
  const [focusAsset, setFocusAsset] = useState("uspxCorr");
  const drivers = [
    { id: "uspxCorr", label: "S&P 500", icon: "🇺🇸", color: "#3b82f6" },
    { id: "oilCorr",  label: "Brent Oil", icon: "🛢️", color: "#ef4444" },
    { id: "usdCorr",  label: "USD Index", icon: "💵", color: "#f59e0b" },
    { id: "goldCorr", label: "Gold", icon: "🥇", color: "#eab308" },
    { id: "chinaCorr",label: "China PMI", icon: "🇨🇳", color: "#ef4444" },
  ];

  const sorted = [...markets].sort((a, b) => b[focusAsset] - a[focusAsset]);
  const driver = drivers.find(d => d.id === focusAsset);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 16 }}>
      {/* Driver selector */}
      <div style={{ background: "#080c16", border: "1px solid #0e1628", borderRadius: 12, padding: 16 }}>
        <div style={{ fontSize: 10, color: "#475569", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 12 }}>Focus Driver</div>
        {drivers.map(d => (
          <button key={d.id} onClick={() => setFocusAsset(d.id)}
            style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 8, border: "none", cursor: "pointer", fontFamily: "inherit", marginBottom: 6, transition: "all 0.15s",
              background: focusAsset === d.id ? d.color + "22" : "transparent",
              outline: focusAsset === d.id ? `1px solid ${d.color}44` : "1px solid transparent",
            }}>
            <span style={{ fontSize: 18 }}>{d.icon}</span>
            <div style={{ textAlign: "left" }}>
              <div style={{ fontSize: 12, fontWeight: focusAsset === d.id ? 700 : 400, color: focusAsset === d.id ? d.color : "#94a3b8" }}>{d.label}</div>
              <div style={{ fontSize: 9, color: "#475569" }}>Correlation ranking</div>
            </div>
          </button>
        ))}

        <div style={{ marginTop: 16, padding: 12, background: "#0a0e1a", borderRadius: 8 }}>
          <div style={{ fontSize: 10, color: "#475569", marginBottom: 8 }}>Legend</div>
          {[["≥0.7","Strong +ve","#ef4444"],["0.4–0.7","Moderate +ve","#f59e0b"],["0.1–0.4","Weak +ve","#22c55e"],["–0.1–0.1","Uncorrelated","#64748b"],["-0.4–-0.1","Weak -ve","#22d3ee"],["≤-0.4","Strong -ve","#3b82f6"]].map(([r,l,c]) => (
            <div key={r} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
              <div style={{ width: 10, height: 10, background: c + "44", border: `1px solid ${c}`, borderRadius: 2, flexShrink: 0 }} />
              <span style={{ fontSize: 9, color: "#64748b" }}>{r} &nbsp;{l}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Atlas chart */}
      <div style={{ background: "#080c16", border: "1px solid #0e1628", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 4 }}>
          Correlation Atlas: All {markets.length} Emerging Markets vs {driver?.label}
        </div>
        <div style={{ fontSize: 10, color: "#334155", marginBottom: 16 }}>
          Sorted strongest to weakest. Width = correlation magnitude.
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
          {sorted.map((m, i) => {
            const v = m[focusAsset];
            const c = corrColor(v);
            return (
              <div key={m.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 8px", borderRadius: 6, background: "#0a0e1a", border: `1px solid ${c}1a` }}>
                <span style={{ fontSize: 14, flexShrink: 0 }}>{m.flag}</span>
                <div style={{ fontSize: 10, color: "#94a3b8", minWidth: 80 }}>{m.name}</div>
                <div style={{ flex: 1, height: 8, background: "#0e1628", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{ width: `${Math.abs(v) * 100}%`, height: "100%", background: c, borderRadius: 4, transition: "width 0.8s" }} />
                </div>
                <div style={{ fontFamily: "monospace", color: c, fontWeight: 700, fontSize: 11, minWidth: 36, textAlign: "right" }}>{v.toFixed(2)}</div>
                <div style={{ fontSize: 9, color: m.chg >= 0 ? "#22c55e" : "#ef4444", minWidth: 40, textAlign: "right", fontFamily: "monospace" }}>{m.chg >= 0 ? "+" : ""}{m.chg.toFixed(1)}%</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── RISK RADAR ───────────────────────────────────────────────────────────────

function RiskRadar({ markets, tick }) {
  const critical = markets.filter(m => m.riskScore >= 70).sort((a, b) => b.riskScore - a.riskScore);
  const high = markets.filter(m => m.riskScore >= 55 && m.riskScore < 70);
  const medium = markets.filter(m => m.riskScore >= 35 && m.riskScore < 55);
  const low = markets.filter(m => m.riskScore < 35);

  const RiskGroup = ({ title, items, color, bg }) => (
    <div style={{ background: "#080c16", border: `1px solid ${color}33`, borderRadius: 12, padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{ fontSize: 10, color, textTransform: "uppercase", letterSpacing: 1.5, fontWeight: 700 }}>{title}</div>
        <span style={{ background: color + "22", color, fontSize: 10, padding: "2px 8px", borderRadius: 4, fontWeight: 700 }}>{items.length}</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {items.map(m => (
          <div key={m.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 8px", background: "#0a0e1a", borderRadius: 6 }}>
            <span style={{ fontSize: 14 }}>{m.flag}</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: "#f8fafc", fontWeight: 600 }}>{m.name}</div>
              <div style={{ fontSize: 9, color: "#475569", marginTop: 1 }}>{m.keyRisk}</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 14, fontWeight: 800, color, fontFamily: "monospace" }}>{m.riskScore}</div>
              <MiniBar value={m.riskScore} max={100} color={color} h={3} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16 }}>
      <RiskGroup title="🔴 Critical Risk" items={critical} color="#ef4444" />
      <RiskGroup title="🟠 High Risk" items={high} color="#f97316" />
      <RiskGroup title="🟡 Medium Risk" items={medium} color="#f59e0b" />
      <RiskGroup title="🟢 Low Risk" items={low} color="#22c55e" />

      {/* Summary strip */}
      <div style={{ gridColumn: "1 / -1", background: "#080c16", border: "1px solid #0e1628", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>📊 Key Risk Indicators — All Markets</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 10 }}>
          {markets.filter(m => m.inflation > 15).map(m => (
            <div key={m.id} style={{ background: "#0a0e1a", borderRadius: 8, padding: 12, border: "1px solid #ef444433" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                <span>{m.flag}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: "#f8fafc" }}>{m.name}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                <span style={{ color: "#64748b" }}>Inflation</span>
                <span style={{ color: "#ef4444", fontFamily: "monospace", fontWeight: 700 }}>{m.inflation.toFixed(1)}%</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                <span style={{ color: "#64748b" }}>Rate</span>
                <span style={{ color: "#f59e0b", fontFamily: "monospace" }}>{m.interestRate.toFixed(2)}%</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                <span style={{ color: "#64748b" }}>FX ({m.currency})</span>
                <span style={{ color: m.fxChg <= -0.5 ? "#ef4444" : "#94a3b8", fontFamily: "monospace" }}>{m.fxChg >= 0 ? "+" : ""}{m.fxChg.toFixed(2)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── MACRO FLOWS ──────────────────────────────────────────────────────────────

function MacroFlows({ markets }) {
  const oilBeneficiaries = markets.filter(m => m.oilCorr > 0.5).sort((a, b) => b.oilCorr - a.oilCorr);
  const oilVictims = markets.filter(m => m.oilCorr < -0.3).sort((a, b) => a.oilCorr - b.oilCorr);
  const usdStrengthWinners = markets.filter(m => m.usdCorr > 0).sort((a, b) => b.usdCorr - a.usdCorr);
  const usdStrengthLosers = markets.filter(m => m.usdCorr < -0.6).sort((a, b) => a.usdCorr - b.usdCorr);
  const chinaLinked = markets.filter(m => m.chinaCorr > 0.6).sort((a, b) => b.chinaCorr - a.chinaCorr);
  const highGrowth = markets.filter(m => m.gdpGrowth > 5).sort((a, b) => b.gdpGrowth - a.gdpGrowth);

  const FlowGroup = ({ title, subtitle, items, corrKey, color, icon }) => (
    <div style={{ background: "#080c16", border: `1px solid ${color}22`, borderRadius: 12, padding: 16 }}>
      <div style={{ fontSize: 10, color, textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 2, fontWeight: 700 }}>{icon} {title}</div>
      <div style={{ fontSize: 9, color: "#334155", marginBottom: 12 }}>{subtitle}</div>
      {items.slice(0, 8).map(m => (
        <div key={m.id} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
          <span style={{ fontSize: 13 }}>{m.flag}</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 11, color: "#f8fafc" }}>{m.name}</div>
            <MiniBar value={Math.abs(m[corrKey] || m.gdpGrowth || 0)} max={corrKey ? 1 : 10} color={color} h={3} />
          </div>
          <span style={{ fontFamily: "monospace", color, fontWeight: 700, fontSize: 11 }}>
            {corrKey ? (m[corrKey]).toFixed(2) : `${m.gdpGrowth.toFixed(1)}%`}
          </span>
        </div>
      ))}
    </div>
  );

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 14 }}>
        <FlowGroup title="Oil Price Winners" subtitle="If Brent rises, these gain" items={oilBeneficiaries} corrKey="oilCorr" color="#f97316" icon="🛢️" />
        <FlowGroup title="Oil Price Losers" subtitle="Net importers — hurt by oil" items={oilVictims} corrKey="oilCorr" color="#ef4444" icon="⛽" />
        <FlowGroup title="China PMI Leaders" subtitle="Highest commodity demand link" items={chinaLinked} corrKey="chinaCorr" color="#ef4444" icon="🇨🇳" />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
        <FlowGroup title="USD Strength Losers" subtitle="EM currencies that weaken most" items={usdStrengthLosers} corrKey="usdCorr" color="#3b82f6" icon="💵" />
        <FlowGroup title="High Growth Markets" subtitle="GDP growth leaders (>5%)" items={highGrowth} corrKey={null} color="#22c55e" icon="📈" />
        <div style={{ background: "#080c16", border: "1px solid #0e1628", borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 12, fontWeight: 700 }}>⚡ MACRO SNAPSHOT</div>
          {[
            { label: "Markets with CPI >15%", val: markets.filter(m => m.inflation > 15).length, color: "#ef4444" },
            { label: "Markets with +ve GDP growth", val: markets.filter(m => m.gdpGrowth > 3).length, color: "#22c55e" },
            { label: "High corr to SPX (>0.6)", val: markets.filter(m => m.uspxCorr > 0.6).length, color: "#3b82f6" },
            { label: "Oil-positive economies", val: markets.filter(m => m.oilCorr > 0.5).length, color: "#f97316" },
            { label: "China-linked (>0.5)", val: markets.filter(m => m.chinaCorr > 0.5).length, color: "#ef4444" },
            { label: "Critical risk score >70", val: markets.filter(m => m.riskScore > 70).length, color: "#ef4444" },
            { label: "Avg EM GDP growth", val: (markets.reduce((s,m) => s + m.gdpGrowth, 0) / markets.length).toFixed(1) + "%", color: "#22c55e" },
          ].map(item => (
            <div key={item.label} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #0a0e1a", fontSize: 11 }}>
              <span style={{ color: "#64748b" }}>{item.label}</span>
              <span style={{ fontFamily: "monospace", color: item.color, fontWeight: 700 }}>{item.val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── MARKET DEEP DIVE ─────────────────────────────────────────────────────────

function MarketDeepDive({ market, allMarkets, onBack }) {
  if (!market) return null;

  // Find most similar markets
  const peers = allMarkets.filter(m => m.id !== market.id).map(m => ({
    ...m,
    similarity: 1 - Math.abs(m.uspxCorr - market.uspxCorr) - Math.abs(m.oilCorr - market.oilCorr) - Math.abs(m.riskScore - market.riskScore) / 100
  })).sort((a, b) => b.similarity - a.similarity).slice(0, 5);

  const corrItems = [
    { label: "vs S&P 500", value: market.uspxCorr, icon: "🇺🇸", desc: market.uspxCorr > 0.6 ? "Highly US-dependent" : market.uspxCorr > 0.4 ? "Moderate US link" : "Low US dependence" },
    { label: "vs Brent Oil", value: market.oilCorr, icon: "🛢️", desc: market.oilCorr > 0.5 ? "Oil exporter — benefits from high oil" : market.oilCorr < -0.3 ? "Oil importer — hurt by high oil" : "Moderate oil sensitivity" },
    { label: "vs USD Index", value: market.usdCorr, icon: "💵", desc: market.usdCorr < -0.6 ? "Strong USD = currency pressure" : market.usdCorr < -0.3 ? "Moderate USD sensitivity" : "Low USD sensitivity" },
    { label: "vs Gold", value: market.goldCorr, icon: "🥇", desc: market.goldCorr > 0.5 ? "Gold producer / safe-haven link" : "Weak gold correlation" },
    { label: "vs China PMI", value: market.chinaCorr, icon: "🇨🇳", desc: market.chinaCorr > 0.6 ? "Heavily China commodity-linked" : market.chinaCorr > 0.4 ? "Moderate China link" : "Low China dependency" },
  ];

  return (
    <div>
      {/* Back + Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
        <button onClick={onBack} style={{ background: "#0e1628", border: "1px solid #1e2a3d", borderRadius: 6, padding: "6px 14px", color: "#94a3b8", cursor: "pointer", fontSize: 11, fontFamily: "inherit" }}>← Back</button>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 36 }}>{market.flag}</span>
          <div>
            <div style={{ fontSize: 22, fontWeight: 800, color: "#f8fafc" }}>{market.name}</div>
            <div style={{ fontSize: 11, color: "#64748b" }}>{market.index} · {market.currency} · {market.tier}</div>
          </div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 20 }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, color: "#64748b" }}>Index</div>
            <div style={{ fontSize: 20, fontFamily: "monospace", fontWeight: 800, color: "#f8fafc" }}>{market.indexVal}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, color: "#64748b" }}>Today</div>
            <div style={{ fontSize: 20, fontFamily: "monospace", fontWeight: 800, color: market.chg >= 0 ? "#22c55e" : "#ef4444" }}>{market.chg >= 0 ? "+" : ""}{market.chg.toFixed(2)}%</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, color: "#64748b" }}>Risk Score</div>
            <div style={{ fontSize: 20, fontFamily: "monospace", fontWeight: 800, color: riskColor(market.riskScore) }}>{market.riskScore}</div>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 2fr", gap: 16 }}>
        {/* Macro indicators */}
        <div style={{ background: "#080c16", border: "1px solid #0e1628", borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 10, color: "#475569", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>📊 Macro Indicators</div>
          {[
            { label: "GDP Growth", value: `${market.gdpGrowth.toFixed(1)}%`, color: market.gdpGrowth > 4 ? "#22c55e" : market.gdpGrowth > 2 ? "#f59e0b" : "#ef4444" },
            { label: "Inflation (CPI)", value: `${market.inflation.toFixed(1)}%`, color: market.inflation > 15 ? "#ef4444" : market.inflation > 8 ? "#f97316" : market.inflation > 4 ? "#f59e0b" : "#22c55e" },
            { label: "Interest Rate", value: `${market.interestRate.toFixed(2)}%`, color: "#94a3b8" },
            { label: "Bond Yield (10Y)", value: `${market.bondYield.toFixed(2)}%`, color: "#94a3b8" },
            { label: "Current Account", value: `${market.currentAccount >= 0 ? "+" : ""}${market.currentAccount.toFixed(1)}% GDP`, color: market.currentAccount >= 0 ? "#22c55e" : "#ef4444" },
            { label: "Debt / GDP", value: `${market.debtGDP}%`, color: market.debtGDP > 90 ? "#ef4444" : market.debtGDP > 60 ? "#f59e0b" : "#22c55e" },
            { label: "Market Cap", value: market.mktCap, color: "#94a3b8" },
            { label: "FX Rate", value: `${market.fxRate} ${market.currency}/USD`, color: "#94a3b8" },
            { label: "FX Change", value: `${market.fxChg >= 0 ? "+" : ""}${market.fxChg.toFixed(2)}%`, color: market.fxChg <= -0.5 ? "#ef4444" : market.fxChg >= 0.5 ? "#22c55e" : "#94a3b8" },
          ].map(row => (
            <div key={row.label} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #0a0e1a", fontSize: 11 }}>
              <span style={{ color: "#64748b" }}>{row.label}</span>
              <span style={{ fontFamily: "monospace", color: row.color, fontWeight: 600 }}>{row.value}</span>
            </div>
          ))}
        </div>

        {/* Correlations */}
        <div style={{ background: "#080c16", border: "1px solid #0e1628", borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 10, color: "#475569", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 14 }}>🔗 Global Correlations</div>
          {corrItems.map(c => {
            const bc = corrColor(c.value);
            return (
              <div key={c.label} style={{ marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: "#f8fafc", fontWeight: 600 }}>{c.icon} {c.label}</span>
                  <span style={{ fontFamily: "monospace", color: bc, fontWeight: 800, fontSize: 13 }}>{c.value.toFixed(2)}</span>
                </div>
                <div style={{ background: "#0a0e1a", borderRadius: 4, height: 8, overflow: "hidden", marginBottom: 4 }}>
                  <div style={{ width: `${Math.abs(c.value) * 100}%`, height: "100%", background: bc, borderRadius: 4, transition: "width 0.8s" }} />
                </div>
                <div style={{ fontSize: 9, color: "#475569" }}>{c.desc}</div>
              </div>
            );
          })}
        </div>

        {/* Key drivers + peer comparison */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Key drivers */}
          <div style={{ background: "#080c16", border: `1px solid ${market.color || "#f59e0b"}33`, borderRadius: 12, padding: 16 }}>
            <div style={{ fontSize: 10, color: market.color || "#f59e0b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 12 }}>⚡ KEY MARKET DRIVERS</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {market.drivers.map((d, i) => (
                <div key={d} style={{ background: "#0a0e1a", borderRadius: 6, padding: "8px 12px", border: "1px solid #0e1628", display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ width: 4, height: 4, borderRadius: "50%", background: market.color || "#f59e0b", flexShrink: 0 }} />
                  <span style={{ fontSize: 11, color: "#cbd5e1" }}>{d}</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12, padding: "10px 12px", background: "#ef444411", border: "1px solid #ef444422", borderRadius: 8 }}>
              <div style={{ fontSize: 10, color: "#64748b", marginBottom: 4 }}>⚠ KEY RISK</div>
              <div style={{ fontSize: 12, color: "#fca5a5", fontWeight: 600 }}>{market.keyRisk}</div>
            </div>
          </div>

          {/* Peer markets */}
          <div style={{ background: "#080c16", border: "1px solid #0e1628", borderRadius: 12, padding: 16 }}>
            <div style={{ fontSize: 10, color: "#475569", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 12 }}>🔄 Peer Markets</div>
            {peers.map(p => (
              <div key={p.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 0", borderBottom: "1px solid #0a0e1a" }}>
                <span style={{ fontSize: 14 }}>{p.flag}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: "#f8fafc", fontWeight: 600 }}>{p.name}</div>
                  <div style={{ fontSize: 9, color: "#475569" }}>SPX Corr: {p.uspxCorr.toFixed(2)} · Risk: {p.riskScore}</div>
                </div>
                <span style={{ fontSize: 11, fontFamily: "monospace", color: p.chg >= 0 ? "#22c55e" : "#ef4444" }}>{p.chg >= 0 ? "+" : ""}{p.chg.toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Transmission chain */}
      <div style={{ marginTop: 14, background: "#080c16", border: "1px solid #0e1628", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 16 }}>🌐 Macro Transmission: If US Fed Hikes 50bps → {market.name} Impact</div>
        <div style={{ display: "flex", alignItems: "center", gap: 4, overflowX: "auto", paddingBottom: 8 }}>
          {[
            { step: "Fed +50bps", color: "#ef4444", detail: "T+0" },
            { step: "DXY +" + (market.oilCorr > 0 ? "moderate" : "strong"), color: "#f59e0b", detail: "T+0" },
            { step: market.currentAccount < -2 ? "FX Pressure ↑" : "FX Moderate", color: "#f97316", detail: "T+1-3d" },
            { step: `${market.currency} ${market.usdCorr < -0.5 ? "weakens" : "stable"}`, color: "#3b82f6", detail: "T+2-5d" },
            { step: market.oilCorr < -0.3 ? "Oil cost ↑ hurts" : "Oil neutral", color: market.oilCorr < -0.3 ? "#ef4444" : "#22c55e", detail: "T+3-7d" },
            { step: `${market.name} equities ${market.uspxCorr > 0.6 ? "fall" : "minor move"}`, color: market.uspxCorr > 0.6 ? "#ef4444" : "#22c55e", detail: "T+5-10d" },
          ].map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 4, flexShrink: 0 }}>
              <div style={{ background: s.color + "22", border: `1px solid ${s.color}44`, borderRadius: 8, padding: "8px 14px", textAlign: "center" }}>
                <div style={{ fontSize: 12, color: "#f8fafc", fontWeight: 600, whiteSpace: "nowrap" }}>{s.step}</div>
                <div style={{ fontSize: 9, color: "#475569" }}>{s.detail}</div>
              </div>
              {i < 5 && <div style={{ color: "#334155", fontSize: 16 }}>→</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
