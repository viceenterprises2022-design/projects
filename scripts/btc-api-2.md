<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# like the attached scripts, i want to develop for BTC, ETH, SOL Futures and spot. I want to get OHLC, OI data for the strikes. research and provide me the API links from where i can get this data. Binance, HYPERLIQUID or Bitget etc.. show me the links exactly.

Yes — for BTC, ETH, and SOL you can pull **spot OHLC**, **futures/perp OHLC**, and **open interest**, but **strike-level OI/OHLC is really options data**, not spot or standard futures data. Binance clearly exposes futures OI and has a dedicated options API/docs surface; Hyperliquid is strong for perp candles but does not offer listed options strikes like Binance options; Bitget supports futures market data and OI, but strike-based options coverage is not the same primary path as Binance’s listed options stack.[^1][^2][^3][^4]

## Best sources

For your use case, the cleanest split is:

- **Binance** for spot, USD-M futures/perps, and listed **options strikes** on BTC/ETH/SOL.[^2][^5][^1]
- **Hyperliquid** for perp OHLC and perp-related info, not exchange-listed options strikes.[^4][^6]
- **Bitget** for futures/perp OHLC and OI, with docs under its Mix/Futures API.[^3]


## Binance links

These are the exact Binance links most relevant to your build:


| Data type | Exact link | Notes |
| :-- | :-- | :-- |
| Binance API hub | [Binance APIs](https://www.binance.com/en/binance-api) | Binance states it offers Spot, Margin, Futures, and Options APIs. [^2] |
| USD-M futures open interest | [Open Interest](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest) | REST endpoint is `GET /fapi/v1/openInterest` with `symbol` required. [^1][^7] |
| Binance options docs surface | [Options API \& WebSocket overview](https://www.binance.com/en/support/faq/detail/fe0be251ac014a8082e702f83d089e54) | Entry point for options REST/WebSocket endpoints. [^5] |
| Options historical exercise records | [Historical Exercise Records](https://developers.binance.com/docs/derivatives/options-trading/market-data/Historical-Exercise-Records) | Shows option symbol and `strikePrice`; REST endpoint is `GET /eapi/v1/exerciseHistory`. [^8][^9] |
| Options OI by strike view | [BTC options OI \& volume](https://www.binance.com/en-IN/eoptions-data/btcusdt/oi-volume) | Public Binance page showing OI/volume by expiration and strike price. [^7] |
| Options OI by strike view | [ETH options OI \& volume](https://www.binance.com/markets/trading_data/eoptions-data/perpetual/trading-data/ETHUSDT/oi-volume) | Public Binance page for ETH options OI/volume by strike. [^10] |

For Binance specifically, your likely mapping is:

- **Spot OHLC:** Binance Spot market-data endpoints under the main API hub.[^2]
- **Futures OHLC:** USD-M futures market-data docs, alongside the open interest endpoint above.[^1]
- **Strike OI / strike candles:** use **Binance Options** endpoints and symbols like `BTC-220121-60000-P`; the exercise-history doc confirms option symbols carry strike price explicitly.[^9]


## Hyperliquid links

These are the most useful Hyperliquid references for your stack:


| Data type | Exact link | Notes |
| :-- | :-- | :-- |
| Hyperliquid candle reference | [Hyperliquid.Api.Info](https://hexdocs.pm/hyperliquid/Hyperliquid.Api.Info.html) | Documents `candle_snapshot(coin, interval, start_time, end_time)` for OHLCV candles. [^4] |
| Hyperliquid OI-cap info | [perpsAtOpenInterestCap](https://docs.chainstack.com/reference/hyperliquid-info-perps-at-open-interest-cap) | Chainstack docs for Hyperliquid `info` endpoint request type `perpsAtOpenInterestCap`. [^6] |

Important limitation: Hyperliquid documentation surfaced here is centered on **perpetuals**, including candle snapshots and OI-cap-related info, not listed option chains with strike-level OI like Binance options.[^6][^4]

## Bitget links

For Bitget, the main official developer entry in the results is:


| Data type | Exact link | Notes |
| :-- | :-- | :-- |
| Bitget futures/mix docs | [Bitget API Docs](https://bitgetlimited.github.io/apidoc/en/mix/) | Official Mix/Futures API documentation entry point. [^3] |

That is the right official docs root for:

- futures/perp OHLC,
- symbol metadata,
- open interest and related market data,
- WebSocket market streams under Bitget’s futures stack.[^3]


## What to use for your script

If your target is **BTC, ETH, SOL spot + futures + strike data**, I’d structure it this way:

- **Spot OHLC:** Binance spot first.[^2]
- **Perp/Futures OHLC + OI:** Binance USD-M futures, Hyperliquid perps, Bitget Mix/Futures.[^4][^1][^3]
- **Strike-level OI and option-symbol data:** Binance Options first, because the surfaced docs and pages explicitly show strike-based option symbols and OI-by-strike views.[^7][^5][^9]

Example instrument separation:

- `BTCUSDT`, `ETHUSDT`, `SOLUSDT` for spot/futures OHLC and futures OI on Binance.[^1]
- `BTC-YYMMDD-STRIKE-C/P` style option symbols for Binance strike data. The Binance options exercise doc explicitly includes symbols like `BTC-220121-60000-P` with `strikePrice`.[^9]

Would you like me to do the next step and turn this into a **developer-ready table of exact REST/WebSocket endpoints for Spot, Futures, OI, and Options strikes** for Binance, Hyperliquid, and Bitget?
<span style="display:none">[^11][^12][^13][^14][^15][^16]</span>

<div align="center">⁂</div>

[^1]: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest

[^2]: https://www.binance.com/en/binance-api

[^3]: https://bitgetlimited.github.io/apidoc/en/mix/

[^4]: https://hexdocs.pm/hyperliquid/Hyperliquid.Api.Info.html

[^5]: https://www.binance.com/en/support/faq/detail/fe0be251ac014a8082e702f83d089e54

[^6]: https://docs.chainstack.com/reference/hyperliquid-info-perps-at-open-interest-cap

[^7]: https://www.binance.com/en-IN/eoptions-data/btcusdt/oi-volume

[^8]: https://developers.binance.com/docs/derivatives/options-trading/market-data/Historical-Exercise-Records

[^9]: market_analysis_v3.py

[^10]: https://www.binance.com/markets/trading_data/eoptions-data/perpetual/trading-data/ETHUSDT/oi-volume

[^11]: https://www.binance.com/en/futures/funding-history/perpetual/trading-data

[^12]: https://www.binance.com/en-IN/blog/markets/510308467767700708

[^13]: https://www.dwellir.com/hyperliquid-ohlcv

[^14]: https://www.bitgetapp.com/support/articles/12560603819924

[^15]: https://www.coinglass.com/options/Binance

[^16]: https://coinalyze.net/hyperliquid/open-interest/

