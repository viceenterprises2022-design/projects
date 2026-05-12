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

@patch('crypto_dashboard.requests.get')
def test_fetch_binance_liquidations(mock_get):
    """Verify Binance liquidation data fetching."""
    from crypto_dashboard import fetch_binance_liquidations
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = [{"symbol": "BTCUSDT", "side": "SELL", "price": "60000"}]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_binance_liquidations("BTC")
    
    assert data is not None
    assert isinstance(data, list)
    assert data[0]["symbol"] == "BTCUSDT"
    mock_get.assert_called_with("https://fapi.binance.com/fapi/v1/allForceOrders?symbol=BTCUSDT&limit=100", timeout=10)

@patch('crypto_dashboard.requests.get')
def test_fetch_bybit_liquidations(mock_get):
    """Verify Bybit liquidation data fetching."""
    from crypto_dashboard import fetch_bybit_liquidations
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "retCode": 0,
        "result": {
            "list": [{"symbol": "BTCUSDT", "side": "Buy", "price": "61000"}]
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_bybit_liquidations("BTC")
    
    assert data is not None
    assert isinstance(data, list)
    assert data[0]["symbol"] == "BTCUSDT"
    mock_get.assert_called_with("https://api.bybit.com/v5/market/liquidation?category=linear&symbol=BTCUSDT&limit=50", timeout=10)

@patch('crypto_dashboard.requests.get')
def test_fetch_binance_liquidations_error(mock_get):
    """Verify Binance liquidation error handling."""
    from crypto_dashboard import fetch_binance_liquidations
    import requests
    mock_get.side_effect = requests.exceptions.RequestException("Binance Down")

    data = fetch_binance_liquidations("BTC")
    assert data is None

@patch('crypto_dashboard.requests.get')
def test_fetch_bybit_liquidations_error(mock_get):
    """Verify Bybit liquidation error handling."""
    from crypto_dashboard import fetch_bybit_liquidations
    import requests
    mock_get.side_effect = requests.exceptions.RequestException("Bybit Down")

    data = fetch_bybit_liquidations("BTC")
    assert data is None

@patch('crypto_dashboard.requests.get')
def test_fetch_bybit_liquidations_retcode_error(mock_get):
    """Verify Bybit liquidation handling when retCode is non-zero."""
    from crypto_dashboard import fetch_bybit_liquidations
    # Setup mock response with error code
    mock_response = MagicMock()
    mock_response.json.return_value = {"retCode": 10001, "retMsg": "Error"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_bybit_liquidations("BTC")
    assert data is None

@patch('crypto_dashboard.requests.get')
def test_fetch_deribit_quotes_invalid_json(mock_get):
    """Verify Deribit handling of invalid JSON."""
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_deribit_quotes("BTC")
    assert data is None

@patch('crypto_dashboard.requests.get')
def test_fetch_binance_liquidations_invalid_json(mock_get):
    """Verify Binance handling of invalid JSON."""
    from crypto_dashboard import fetch_binance_liquidations
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_binance_liquidations("BTC")
    assert data is None

@patch('crypto_dashboard.requests.get')
def test_fetch_binance_liquidations_not_list(mock_get):
    """Verify Binance handling when response is not a list."""
    from crypto_dashboard import fetch_binance_liquidations
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": "not a list"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_binance_liquidations("BTC")
    assert data is None

@patch('crypto_dashboard.requests.get')
def test_fetch_bybit_liquidations_invalid_json(mock_get):
    """Verify Bybit handling of invalid JSON."""
    from crypto_dashboard import fetch_bybit_liquidations
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_bybit_liquidations("BTC")
    assert data is None

def test_aggregate_liquidation_bins():
    from crypto_dashboard import aggregate_liquidation_bins
    
    # Binance data: price 60001, qty 0.1 -> bin 60000, vol 6000.1
    # price 60049, qty 0.1 -> bin 60000, vol 6004.9
    # total for bin 60000 = 12005.0
    binance_data = [
        {"price": "60001", "origQty": "0.1"},
        {"price": "60049", "origQty": "0.1"}
    ]
    
    # Bybit data: price 60099, size 0.1 -> bin 60100, vol 6009.9
    bybit_data = [
        {"price": "60099", "size": "0.1"}
    ]
    
    result = aggregate_liquidation_bins(binance_data, bybit_data, "BTC")
    
    # Expected: [(60000, 12005.0), (60100, 6009.9)]
    assert len(result) == 2
    assert result[0][0] == 60000
    assert result[0][1] == pytest.approx(12005.0)
    assert result[1][0] == 60100
    assert result[1][1] == pytest.approx(6009.9)

def test_aggregate_liquidation_bins_symbols():
    from crypto_dashboard import aggregate_liquidation_bins
    
    # ETH bin size 10
    eth_binance = [{"price": "2504", "origQty": "1.0"}] # bin 2500, vol 2504
    eth_bybit = [{"price": "2506", "size": "1.0"}]    # bin 2510, vol 2506
    result_eth = aggregate_liquidation_bins(eth_binance, eth_bybit, "ETH")
    assert (2500, 2504.0) in result_eth
    assert (2510, 2506.0) in result_eth

    # SOL bin size 1
    sol_binance = [{"price": "145.4", "origQty": "10.0"}] # bin 145, vol 1454
    sol_bybit = [{"price": "146.6", "size": "10.0"}]    # bin 147, vol 1466
    result_sol = aggregate_liquidation_bins(sol_binance, sol_bybit, "SOL")
    assert (145, 1454.0) in result_sol
    assert (147, 1466.0) in result_sol

def test_aggregate_liquidation_bins_empty():
    from crypto_dashboard import aggregate_liquidation_bins
    assert aggregate_liquidation_bins([], [], "BTC") == []
    assert aggregate_liquidation_bins(None, None, "BTC") == []
