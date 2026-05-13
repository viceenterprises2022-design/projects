
import websocket
import ssl
import json

def on_message(ws, message):
    print(f"MSG: {message[:100]}")

def on_error(ws, error):
    print(f"ERR: {error}")

def on_open(ws):
    print("OPEN")

def test_binance_insecure():
    url = "wss://fstream.binance.com/ws/!forceOrder@arr"
    ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_open=on_open)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    test_binance_insecure()
