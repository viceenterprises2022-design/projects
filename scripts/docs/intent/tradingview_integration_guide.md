# TradingView Integration Guide

This guide details how to hook up TradingView alerts to trigger automated trades on the SaaS controller backend.

## 1. Webhook Settings

When creating a new alert on TradingView, check the **Webhook URL** box and enter:
```
http://<your-saas-server-ip>:8899/api/webhook/tradingview
```
*(Ensure port `8899` is open and accessible from TradingView IP addresses).*

## 2. Alert Payload Format

In the **Message** text box of your TradingView alert, construct a JSON payload using placeholders.

### Long Entry Signal (BUY)
```json
{
  "symbol": "BTC-PERP",
  "action": "BUY",
  "price": {{close}},
  "size": 0.02,
  "token": "supersecret_webhook_token"
}
```

### Short Entry Signal (SELL)
```json
{
  "symbol": "BTC-PERP",
  "action": "SELL",
  "price": {{close}},
  "size": 0.02,
  "token": "supersecret_webhook_token"
}
```

*Note: Replace `supersecret_webhook_token` with the value configured in your `.env` file under `WEBHOOK_SECRET_TOKEN`.*

## 3. Execution Scaling

When the webhook is received:
1. The backend locates all active users configured to trade `symbol`.
2. The user's risk multiplier is applied to the base `"size"` parameter. E.g., if a user has `risk_multiplier: 1.5`, their executed trade size will be `0.03 BTC-PERP`.
3. The trade is signed cryptographically via EIP-712 and submitted to Hyperliquid.
