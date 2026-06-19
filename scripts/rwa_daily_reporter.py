#!/usr/bin/env python3
import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from exa_py import Exa

# Load env variables
load_dotenv()

EXA_API_KEY = os.environ.get("EXA_API_KEY")
SLACK_WEBHOOK_RWA = os.environ.get("SLACK_WEBHOOK_RWA")
BRAIN_ARTIFACT_PATH = "/home/vreddy1/.gemini/antigravity-cli/brain/fbc9d0dd-21e4-4c02-b7f4-300d8d83e94a/rwa_stablecoin_deepdive_report.md"
WORKSPACE_REPORT_PATH = "/home/vreddy1/Desktop/Projects/scripts/rwa_stablecoin_deepdive_report.md"

if not EXA_API_KEY:
    print("Error: EXA_API_KEY not found in .env", file=sys.stderr)
    sys.exit(1)

if not SLACK_WEBHOOK_RWA:
    print("Error: SLACK_WEBHOOK_RWA not found in .env", file=sys.stderr)
    sys.exit(1)

# Initialize Exa
exa = Exa(api_key=EXA_API_KEY)

def fetch_latest_news():
    since = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
    queries = [
        "real world assets RWA tokenization AUM market updates 2026",
        "stablecoins Africa payment cross-border remittance Celo Stellar Base 2026"
    ]
    news_items = []
    
    for q in queries:
        try:
            resp = exa.search(
                q, 
                type="auto", 
                num_results=3, 
                start_published_date=since, 
                contents={"summary": {"query": "give me a 1-sentence summary of this article"}}
            )
            for r in resp.results:
                news_items.append({
                    "title": (r.title or "").strip(),
                    "url": r.url,
                    "summary": getattr(r, "summary", "") or ""
                })
        except Exception as e:
            print(f"Exa search failed for query '{q}': {e}", file=sys.stderr)
            
    # Deduplicate by URL
    seen_urls = set()
    deduped = []
    for item in news_items:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            deduped.append(item)
    return deduped

def build_report_content(news):
    now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %I:%M %p IST")
    
    # Render latest news section
    news_md = ""
    if news:
        news_md = "\n## 6. Latest News & Market Developments (Exa Search)\n\n"
        for idx, item in enumerate(news, 1):
            news_md += f"**{idx}. [{item['title']}]({item['url']})**\n"
            if item["summary"]:
                news_md += f"*{item['summary'].strip()}*\n"
            news_md += "\n"
    else:
        news_md = "\n## 6. Latest News & Market Developments (Exa Search)\n\n*No new updates in the last 48 hours.*\n"

    report = f"""# Real-World Asset (RWA) & Stablecoin Market Intelligence Report: H1 2026 Global Synthesis

## Executive Summary

The tokenization of Real-World Assets (RWAs) and the deployment of stablecoins have transitioned from early-stage experimental phases into a core component of the global financial infrastructure. As of H1 2026, the aggregate on-chain value of tokenized RWAs has surpassed **$25–$30 billion**. 

This growth is driven by two parallel forces:
1. **Institutional Demand for Efficiency:** Major asset managers (e.g., BlackRock, Franklin Templeton) are leveraging public and private blockchains to optimize back-office operations, reduce settlement times, and unlock yield for treasury products.
2. **Emerging Market Economic Realities:** In frontier economies—specifically across Africa, Latin America (LATAM), and parts of Asia—stablecoins are serving as crucial alternatives to volatile local fiat currencies, enabling basic cross-border trade finance and protecting wealth against high inflation.

*Report generated at: {now_ist}*

---

## 1. RWA Sector Dynamics & AUM Metrics

The RWA tokenization space is dominated by tokenized government securities, private credit, and commodities. Below is a breakdown of the leading platforms, their flagship products, and estimated on-chain Assets Under Management (AUM) / Total Value Locked (TVL) as of H1 2026.

### Table 1: Major RWA Players and Asset Distribution

| Company / Protocol | Key Tokenized Product(s) | Primary Asset Class | Estimated AUM / TVL (H1 2026) | Primary Chains |
| :--- | :--- | :--- | :--- | :--- |
| **Ondo Finance** | USDY, OUSG | U.S. Treasuries, Global ETFs | ~$3.7B – $4.0B | Ethereum, Solana, Polygon, Arbitrum |
| **BlackRock** | BUIDL (Institutional Digital Liquidity Fund) | U.S. Treasuries, Repo Agreements | ~$2.3B – $2.5B | Ethereum (expanding to others) |
| **Franklin Templeton** | FOBXX (OnChain U.S. Government Money Fund) | U.S. Government Securities | ~$1.98B | Stellar, Polygon, Base, Arbitrum, Avalanche |
| **Centrifuge** | Anemoy Treasury, Private Credit Pools | Private Credit, Trade Receivables | ~$1.5B – $1.6B | Base, Ethereum, Centrifuge Chain |
| **Securitize** | Feeders for KKR, Hamilton Lane funds | Tokenized Private Equity/Credit | ~$1.2B | Ethereum, Avalanche |

### Critical Insights by Asset Class:
* **Tokenized Treasuries:** Yield-bearing U.S. Treasury tokens (like Ondo's USDY and BlackRock's BUIDL) are the fastest-growing sector. They serve as "on-chain cash equivalents" that allow crypto-native entities and treasury managers to earn low-risk, yield-bearing returns on their stable reserves.
* **Private Credit:** Protocols like Centrifuge utilize smart contracts to group real-world debts (such as commercial real estate loans, trade invoices, and structured finance) into pools. This offers higher yields than government securities but introduces underwriting and default risks.

---

## 2. Layer 1 (L1) & Layer 2 (L2) Selection Architecture

Issuers choose specific blockchains based on speed, transaction cost, security, compliance features, and existing liquidity pools. 

### Table 2: Blockchain Ecosystem Trade-offs for RWA

| Network | Type | Key Advantages | Major Limitations | Strategic Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Ethereum** | L1 | Maximum security, largest capital pool, deep DeFi composability, ERC-20 standardization. | High transaction fees, slow finality, lacks built-in compliance hooks. | High-value institutional funds (e.g., BlackRock BUIDL). |
| **Stellar** | L1 | Native compliance features (clawbacks, asset freezes), near-zero transaction fees, fast finality. | Limited smart contract flexibility compared to EVM, smaller retail DeFi ecosystem. | Interbank payments, government bond issuance (e.g., Franklin Templeton). |
| **Solana** | L1 | Sub-second finality, ultra-low fees, high throughput, native "Token Extensions". | Historically perceived liveness risks, complex custom Rust development. | Retail payment dApps, high-frequency RWA trading, tokenized assets needing embedded logic. |
| **Base** | L2 (Ethereum) | Coinbase ecosystem integration, low gas fees, EVM compatibility, access to Coinbase KYC rails. | Dependency on Ethereum L1 for final security, centralized sequencer concerns. | Capital-efficient DeFi yields, emerging market credit protocols (e.g., Mansa). |
| **Celo** | L2 (OP Stack) | Mobile-first architecture, gas payments using stablecoins (cUSD, cEUR), fast transactions. | Smaller capital pools compared to Arbitrum/Base, undergoing L1-to-L2 transition. | Micro-remittances, mobile-based savings apps (e.g., Kotani Pay). |

### Key Technical Feature Focus: Solana Token Extensions & Stellar Native Compliance
* **Solana Token Extensions:** Allow issuers to build complex compliance directly into the token standard. This includes permanent delegation (for custody), transfer hooks (triggering KYC checks before any transfer completes), interest-bearing metadata (for yield accrual), and confidential transfers.
* **Stellar Ledger-Level Controls:** Stellar's protocol has native flags like `AUTHORIZATION_REVOCABLE` and `AUTHORIZATION_CLAWBACK`. This enables regulated token issuers to freeze or claw back assets directly via ledger commands if required by a court order or regulatory audit, without deploying complex, buggy smart contracts.

---

## 3. High Focus: The African RWA & Stablecoin Landscape

Africa has become a primary real-world testing ground for stablecoin and RWA-driven financial products. Due to persistent foreign exchange (FX) illiquidity, high inflation rates (e.g., Nigeria, Egypt, Zimbabwe), and fragmented cross-border payment rails, decentralized infrastructure is moving from speculation to utility.

### Case Studies of African Innovators

#### 1. Zone (Nigeria)
* **Underlying Tech / Blockchain:** Proprietary private-permissioned Layer-1 blockchain protocol.
* **Role & Function:** Regulated by the Central Bank of Nigeria (CBN), Zone acts as a decentralized payment switch. By deploying nodes directly within commercial banks and fintechs, Zone clears interbank transactions directly without passing through a centralized clearinghouse.
* **Chain Selection Logic:** Zone chose a private-permissioned L1 framework because traditional public blockchains cannot meet the transaction speed (thousands of TPS), transaction privacy, and strict regulatory compliance required for national retail payment processing (ATMs and Point-of-Sale terminals).

#### 2. Mansa Finance (Pan-African / Global Emerging Markets)
* **Underlying Tech / Blockchain:** Built on **Base** (Ethereum Layer-2).
* **Role & Function:** A liquidity protocol that provides stablecoin liquidity (primarily USDT/USDC) to local payment companies, exporters, and fintechs. By providing revolving lines of credit, Mansa eliminates the need for businesses to hold expensive pre-funded local currency accounts.
* **Chain Selection Logic:** Mansa deployed on Base to leverage Ethereum's security alignment while maintaining low transaction fees. Base allows Mansa to connect easily with Coinbase's custodial services, institutional portals, and EVM-compatible DeFi liquidity sources.

#### 3. Kotani Pay (East Africa)
* **Underlying Tech / Blockchain:** Integrates with **Celo** (Ethereum Layer-2 transition).
* **Role & Function:** A middleware API and USSD (Unstructured Supplementary Service Data) gateway that connects blockchain stablecoins (such as Celo Dollar - cUSD) directly to local mobile money networks (like M-Pesa).
* **Chain Selection Logic:** Kotani Pay leverages Celo because Celo is optimized for mobile-first deployments, supports gas payments using stablecoins, and has light-client protocols designed for low-bandwidth cellular environments. The USSD menu allows users with basic feature phones (no internet required) to receive, save, and off-ramp digital dollars.

#### 4. Yellow Card (Pan-African)
* **Underlying Tech / Blockchain:** Multi-chain architecture (Stellar, Celo, Tron, Ethereum).
* **Role & Function:** The largest licensed stablecoin on/off ramp platform in Africa, operating in over 20 countries. It serves as B2B treasury infrastructure, allowing companies to buy/sell stablecoins (USDT, USDC, PYUSD) using local currencies.
* **Chain Selection Logic:** Yellow Card uses Stellar for cheap fiat-to-stablecoin cross-border corridors, Tron/USDT for high retail demand, and Celo/Base for mobile payments, matching the chain selection directly to regional market preferences.

---

## 4. Regional Global Market Updates (H1 2026)

### United States
* **Regulatory Climate:** Currently implementing the **GENIUS Act (Guiding and Establishing National Innovation for U.S. Stablecoins)**. The federal agencies (FDIC, Treasury, CFTC) are finalizing regulatory mandates, with the Treasury targeting July 2026 to enforce strict reserve backing rules (requiring 1:1 liquid U.S. Treasuries or cash).
* **Asset Growth:** Stablecoin issuers (Tether, Circle) remain the largest indirect purchasers of U.S. short-term debt, integrating traditional banking liquidity directly with on-chain systems.

### Europe
* **MiCA Enforced:** The transition grandfathering period for the **Markets in Crypto-Assets (MiCA)** regulation ends on **July 1, 2026**. All Crypto-Asset Service Providers (CASPs) must be fully authorized, and interest-bearing stablecoins are banned. Major exchanges are actively delisting non-compliant assets, consolidating liquidity toward regulated issuers.

### Asia
* **Hong Kong:** HKMA's stablecoin licensing framework went live in early 2026. High-volume B2B trade corridors are piloting tokenized HKD and USD stablecoins for cross-border settlement with ASEAN nations.
* **Singapore:** MAS DTSP rules enforce 100% reserve backing and 5-day redemption requirements for licensed issuers, securing Singapore's role as a low-risk institutional hub.

### Latin America (LATAM)
* **Brazil Leading:** The Central Bank of Brazil (BCB) resolutions 519–521 took effect in February 2026, establishing strict AML rules and minimum capital requirements for stablecoin operators.
* **Inflation Hedging:** In Argentina and Venezuela, USDT and USDC continue to dominate peer-to-peer commerce, serving as parallel shadow economies to protect against triple-digit local currency devaluations.

### Middle East (UAE)
* **Dubai (VARA):** Regulated frameworks under VARA and ADGM have attracted major institutional issuers seeking to establish regulatory-compliant pipelines between European capital and Asian trade networks.

---

## 5. Strategic Recommendations for African Product Development

If building a financial product targeting the African market, consider the following structural guidelines:

1. **Leverage Existing Rails (USSD + Mobile Money):** Smartphone penetration is growing, but basic feature phones remain critical in rural and low-income demographics. Incorporate USSD middleware (similar to Kotani Pay) to allow users to interact with stablecoin wallets without internet requirements.
2. **Prioritize Layer-2 Networks (Base or Celo):** High fees on Ethereum L1 make it completely unusable for retail micro-transactions. Base offers deep integration with institutional fiat corridors, while Celo provides native stablecoin gas payment features.
3. **Address FX Squeeze & Settlement Inefficiencies:** B2B trade finance and corporate treasury management represent higher-margin, lower-risk customer segments than retail crypto trading. Solutions providing stablecoin liquidity for import/export pre-funding (like Mansa) target immediate, severe market pain points.
4. **Partner with Regulated Switches:** For interbank settling and high-volume merchant networks, leveraging systems like Zone's private L1 allows compliant routing without bypassing Central Bank guidelines.
{news_md}"""
    return report

def main():
    print("Fetching latest news from Exa...")
    news = fetch_latest_news()
    print(f"Fetched {len(news)} stories.")
    
    report_content = build_report_content(news)
    
    # Save to workspace
    print(f"Saving to {WORKSPACE_REPORT_PATH}...")
    with open(WORKSPACE_REPORT_PATH, "w") as f:
        f.write(report_content)
        
    # Save to brain artifact directory if exists
    try:
        os.makedirs(os.path.dirname(BRAIN_ARTIFACT_PATH), exist_ok=True)
        print(f"Saving to brain artifact path {BRAIN_ARTIFACT_PATH}...")
        with open(BRAIN_ARTIFACT_PATH, "w") as f:
            f.write(report_content)
    except Exception as e:
        print(f"Warning: could not write to brain artifact path: {e}", file=sys.stderr)
        
    # Call send_slack.py to deliver
    print(f"Sending report to Slack webhook...")
    try:
        import subprocess
        cmd = [
            "/home/vreddy1/Desktop/Projects/scripts/venv/bin/python",
            "/home/vreddy1/Desktop/Projects/scripts/send_slack.py",
            "--webhook-url", SLACK_WEBHOOK_RWA,
            "--file", WORKSPACE_REPORT_PATH,
            "--header", "RWA & Stablecoin Daily Intelligence Brief",
            "--color", "info"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("Slack execution stdout:", result.stdout)
        if result.stderr:
            print("Slack execution stderr:", result.stderr, file=sys.stderr)
    except Exception as e:
        print(f"Failed to execute send_slack.py: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
