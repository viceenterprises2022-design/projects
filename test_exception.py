import requests
from unittest.mock import MagicMock, patch

def fetch_binance_liquidations(symbol):
    url = f"https://fapi.binance.com/fapi/v1/allForceOrders?symbol={symbol}USDT&limit=100"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Binance liquidations for {symbol}: {e}")
        return None

@patch('requests.get')
def test_json_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response
    
    try:
        result = fetch_binance_liquidations("BTC")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Caught exception outside: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_json_error()
