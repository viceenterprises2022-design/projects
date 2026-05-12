"""
Tests for Crypto Options & Liquidation Dashboard.
"""

import pytest
from unittest.mock import patch, MagicMock
from crypto_dashboard import fetch_deribit_quotes

@patch('crypto_dashboard.requests.get')
def test_fetch_deribit_quotes_btc(mock_get):
    """Verify Deribit BTC options data fetching with mock."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": [{"instrument_name": "BTC-28MAR25-100000-C"}]}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_deribit_quotes("BTC")
    
    assert data is not None
    assert "result" in data
    assert isinstance(data["result"], list)
    assert data["result"][0]["instrument_name"] == "BTC-28MAR25-100000-C"
    mock_get.assert_called_with("https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option", timeout=5)

@patch('crypto_dashboard.requests.get')
def test_fetch_deribit_quotes_error(mock_get):
    """Verify error handling when API fails."""
    import requests
    mock_get.side_effect = requests.exceptions.RequestException("API Down")

    data = fetch_deribit_quotes("BTC")
    assert data is None

def test_calculate_pcr():
    from crypto_dashboard import calculate_pcr
    # Mock data with 10 Call OI and 20 Put OI
    options_data = [
        {"instrument_name": "BTC-30AUG24-60000-C", "open_interest": 10},
        {"instrument_name": "BTC-30AUG24-60000-P", "open_interest": 20},
    ]
    assert calculate_pcr(options_data) == 2.0

def test_calculate_max_pain():
    from crypto_dashboard import calculate_max_pain
    options_data = [
        {"instrument_name": "BTC-30AUG24-50000-C", "open_interest": 10},
        {"instrument_name": "BTC-30AUG24-60000-C", "open_interest": 10},
        {"instrument_name": "BTC-30AUG24-50000-P", "open_interest": 10},
        {"instrument_name": "BTC-30AUG24-60000-P", "open_interest": 10},
    ]
    # Both 50000 and 60000 result in same loss in this balanced mock
    assert calculate_max_pain(options_data) in [50000, 60000]

def test_aggregate_liquidation_bins_with_data():
    from crypto_dashboard import liq_collector, aggregate_liquidation_bins
    
    # Manually seed the global collector
    liq_collector.buffer["BTC"] = [
        {"price": 60001, "qty": 0.1, "timestamp": 123},
        {"price": 60049, "qty": 0.1, "timestamp": 123},
        {"price": 60099, "qty": 0.1, "timestamp": 123}
    ]
    
    # Result for BTC (bin size 100)
    # 60001 -> 60000
    # 60049 -> 60000
    # 60099 -> 60100
    result = aggregate_liquidation_bins("BTC")
    
    assert len(result) == 2
    assert result[0][0] == 60000
    assert result[0][1] == pytest.approx(12005.0)
    assert result[1][0] == 60100
    assert result[1][1] == pytest.approx(6009.9)

def test_aggregate_liquidation_bins_empty():
    from crypto_dashboard import liq_collector, aggregate_liquidation_bins
    liq_collector.buffer["SOL"] = []
    assert aggregate_liquidation_bins("SOL") == []
