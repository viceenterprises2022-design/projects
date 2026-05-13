
import websocket
import json
import time

def on_message(ws, message):
    print(f"MSG: {message[:100]}...")

def on_error(ws, error):
    print(f"ERR: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"CLOSED: {close_status_code} {close_msg}")

def test_binance():
    print("Testing Binance WebSocket (!forceOrder@arr)...")
    url = "wss://fstream.binance.com/ws/!forceOrder@arr"
    ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.run_forever(ping_interval=10)

def test_bybit():
    print("\nTesting Bybit WebSocket (allLiquidation.BTCUSDT)...")
    url = "wss://stream.bybit.com/v5/public/linear"
    def on_open(ws):
        print("Bybit Opened, subscribing...")
        ws.send(json.dumps({"op": "subscribe", "args": ["allLiquidation.BTCUSDT"]}))
    
    ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.run_forever(ping_interval=10)

if __name__ == "__main__":
    # Test Binance first, then Bybit after 20 seconds or Ctrl+C
    try:
        test_binance()
    except KeyboardInterrupt:
        pass
    
    try:
        test_bybit()
    except KeyboardInterrupt:
        pass
