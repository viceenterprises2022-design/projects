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
    mock_get.assert_called_once()

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
    # PCR = Put OI / Call OI = 20 / 10 = 2.0
    assert calculate_pcr(options_data) == 2.0

def test_calculate_pcr_zero_calls():
    from crypto_dashboard import calculate_pcr
    options_data = [
        {"instrument_name": "BTC-30AUG24-60000-P", "open_interest": 20},
    ]
    # Should handle division by zero (return 0.0 if no calls)
    assert calculate_pcr(options_data) == 0.0

def test_calculate_max_pain():
    from crypto_dashboard import calculate_max_pain
    options_data = [
        {"instrument_name": "BTC-30AUG24-50000-C", "open_interest": 10},
        {"instrument_name": "BTC-30AUG24-60000-C", "open_interest": 10},
        {"instrument_name": "BTC-30AUG24-50000-P", "open_interest": 10},
        {"instrument_name": "BTC-30AUG24-60000-P", "open_interest": 10},
    ]
    # Simple case: 50k and 60k strikes. 
    # If 50k: Call 50k loss=0, Call 60k loss=0, Put 50k loss=0, Put 60k loss=(60-50)*10=100. Total=100.
    # If 60k: Call 50k loss=(60-50)*10=100, Call 60k loss=0, Put 50k loss=0, Put 60k loss=0. Total=100.
    # Both 50000 and 60000 result in 100 loss.
    assert calculate_max_pain(options_data) in [50000, 60000]
