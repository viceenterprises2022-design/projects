import yfinance as yf
import ccxt
import pandas as pd
from datetime import datetime
import os

class EquityIngestion:
    """Ingest equity data from Yahoo Finance."""
    def __init__(self, ticker):
        self.ticker = ticker
        self.asset = yf.Ticker(ticker)

    def get_fundamentals(self):
        """Fetch fundamental data."""
        info = self.asset.info
        return {
            "ticker": self.ticker,
            "company_name": info.get("longName"),
            "data_date": datetime.now().strftime("%Y-%m-%d"),
            "financial_metrics": {
                "market_cap": info.get("marketCap"),
                "revenue_ttm": info.get("totalRevenue"),
                "gross_margin": info.get("grossMargins"),
                "operating_margin": info.get("operatingMargins"),
                "net_margin": info.get("profitMargins"),
                "roe": info.get("returnOnEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "free_cash_flow": info.get("freeCashflow"),
            }
        }

    def get_technical_data(self, period="1y"):
        """Fetch historical price data and compute indicators."""
        hist = self.asset.history(period=period)
        # Placeholder for technical indicator computation (SMA, RSI, etc.)
        return {
            "ticker": self.ticker,
            "current_price": hist['Close'].iloc[-1],
            "price_data": {
                "day_high": hist['High'].iloc[-1],
                "day_low": hist['Low'].iloc[-1],
                "week_52_high": hist['High'].max(),
                "week_52_low": hist['Low'].min(),
                "change_percent_1d": ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            }
        }

class CryptoIngestion:
    """Ingest crypto data from CCXT."""
    def __init__(self, symbol):
        self.symbol = symbol
        self.exchange = ccxt.binance()

    def get_market_data(self):
        """Fetch current price and volume."""
        ticker = self.exchange.fetch_ticker(self.symbol)
        return {
            "ticker": self.symbol,
            "current_price": ticker['last'],
            "volume_24h": ticker['quoteVolume'],
            "change_percent_24h": ticker['percentage']
        }

    def get_ohlcv(self, timeframe="1h", limit=100):
        """Fetch OHLCV data."""
        return self.exchange.fetch_ohlcv(self.symbol, timeframe=timeframe, limit=limit)

# Example usage pattern
if __name__ == "__main__":
    # Equity example
    equity = EquityIngestion("RELIANCE.NS")
    # print(equity.get_fundamentals())
    
    # Crypto example
    crypto = CryptoIngestion("BTC/USDT")
    # print(crypto.get_market_data())
