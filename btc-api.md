Here are the exact API endpoints you need, organized by exchange and data type. I've grouped them so you can drop them straight into your script.

---

## 1. Binance

### Spot OHLC (BTC, ETH, SOL)
```
GET https://api.binance.com/api/v3/klines
```
Params: `symbol=BTCUSDT&interval=1h&limit=1000` 

### USDT-M Futures OHLC
```
GET https://fapi.binance.com/fapi/v1/klines
```
Params: `symbol=BTCUSDT&interval=1h&limit=1000` 

### Options OHLC (strike-level candles)
```
GET https://eapi.binance.com/eapi/v1/klines
```
Params: `symbol=BTC-250620-90000-C&interval=1h&limit=1000` 

### Options Open Interest by Strike / Expiry
```
GET https://eapi.binance.com/eapi/v1/openInterest
```
Params: `underlyingAsset=BTC&expirationDate=250620`  

### Futures Open Interest (per symbol)
```
GET https://fapi.binance.com/fapi/v1/openInterest
```
Params: `symbol=BTCUSDT` 

### Futures OI History (time-series)
```
GET https://fapi.binance.com/futures/data/openInterestHist
```
Params: `symbol=BTCUSDT&period=1h&limit=500` 

---

## 2. Hyperliquid

Hyperliquid uses a **single JSON-RPC-style POST endpoint** for almost everything:

```
POST https://api.hyperliquid.xyz/info
Content-Type: application/json
```

### Perp OHLC (BTC, ETH, SOL)
Body:
```json
{
  "type": "candleSnapshot",
  "req": {
    "coin": "BTC",
    "interval": "1h",
    "startTime": 1715000000000,
    "endTime": 1716000000000
  }
}
```
 

### Spot OHLC
Body:
```json
{
  "type": "candleSnapshot",
  "req": {
    "coin": "@1",
    "interval": "1h",
    "startTime": 1715000000000,
    "endTime": 1716000000000
  }
}
```
Spot symbols use `@INDEX` format (discover via `spotMeta`) 

### Open Interest (perp)
Body:
```json
{
  "type": "openInterest",
  "coin": "BTC"
}
```
 

### Funding Rate
Body:
```json
{
  "type": "fundingHistory",
  "coin": "BTC",
  "startTime": 1715000000000,
  "endTime": 1716000000000
}
```


### Market Summary (price + OI + funding in one call)
Body:
```json
{
  "type": "metaAndAssetCtxs"
}
```
Returns an array where index `[1][n]` contains `openInterest`, `markPx`, `funding`, etc. 

---

## 3. Bitget

Base URL: `https://api.bitget.com`

### Spot OHLC
```
GET /api/v2/spot/market/candles
```
Params: `symbol=BTCUSDT&granularity=1h&limit=1000`  

### Spot Historic OHLC
```
GET /api/v2/spot/market/history-candles
```

### Futures (Mix) OHLC
```
GET /api/v2/mix/market/candles
```
Params: `symbol=BTCUSDT_UMCBL&granularity=1H&limit=1000` 

### Futures Historic OHLC
```
GET /api/v2/mix/market/history-candles
```
Params: `symbol=BTCUSDT_UMCBL&granularity=1H&startTime=...&endTime=...` 

### Futures Open Interest
```
GET /api/v2/mix/market/open-interest
```
Params: `symbol=BTCUSDT_UMCBL` 

### Futures Funding Rate
```
GET /api/v2/mix/market/current-fund-rate
```
Params: `symbol=BTCUSDT_UMCBL` 

---

## Quick Comparison Table

| Data Need | Best Source | Endpoint |
|---|---|---|
| Spot OHLC | Binance / Bitget | `api.binance.com/api/v3/klines` or `api.bitget.com/api/v2/spot/market/candles` |
| Futures OHLC | Binance / Bitget | `fapi.binance.com/fapi/v1/klines` or `api.bitget.com/api/v2/mix/market/candles` |
| Perp OHLC | Hyperliquid | `POST api.hyperliquid.xyz/info` → `candleSnapshot` |
| Options OHLC by Strike | Binance | `eapi.binance.com/eapi/v1/klines` |
| Options OI by Strike | Binance | `eapi.binance.com/eapi/v1/openInterest` |
| Futures OI | All three | `fapi.binance.com/fapi/v1/openInterest`, `api.hyperliquid.xyz/info`, `api.bitget.com/api/v2/mix/market/open-interest` |
| Funding Rate | Hyperliquid / Bitget | `api.hyperliquid.xyz/info`, `api.bitget.com/api/v2/mix/market/current-fund-rate` |

---

## One Important Note on Crypto Options OI

Unlike Indian index options (NIFTY/BANKNIFTY), **crypto options OI by individual strike is not freely available on most CEXs in a single chain query**. Binance Options gives you `openInterest` aggregated per expiry date , not per strike in one call. For true strike-level OI (like your Upstox option chain), **Deribit** is the gold standard:

```
GET https://www.deribit.com/api/v2/public/get_book_summary_by_currency
GET https://www.deribit.com/api/v2/public/get_instruments
GET https://www.deribit.com/api/v2/public/get_order_book
```

If you want the exact "Call/Put OI bars per strike" visualization like your `market_analysis_v3.py`, Deribit is your best bet. Binance Options is more limited in strike granularity.