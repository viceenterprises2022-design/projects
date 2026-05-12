"""
Tests for Crypto Options & Liquidation Dashboard.
"""

import pytest
from crypto_dashboard import fetch_deribit_quotes

def test_fetch_deribit_quotes_btc():
    """Verify Deribit BTC options data fetching."""
    data = fetch_deribit_quotes("BTC")
    assert "result" in data
    assert isinstance(data["result"], list)
