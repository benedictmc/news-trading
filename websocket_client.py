import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"Aggregated Trade Event: Price: {data['p']} Quantity: {data['q']}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    # No need to send a subscribe payload for single stream connections.
    # The subscription is implicit in the URL.
    pass

# Connect to the Binance WebSocket for aggregated trades on BNB/USDT futures
websocket_url = "wss://fstream.binance.com/ws/bnbusdt@aggTrade"
ws = websocket.WebSocketApp(
    websocket_url,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)
ws.on_open = on_open
ws.run_forever()