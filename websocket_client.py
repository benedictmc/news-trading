import websocket
import time


def on_message(ws, message):
    print("Received:", message)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Closed")

def on_pong(ws, message):
    print("PONG:", message)

def on_open(ws):
    def ping_forever():
        # This loop will send a custom PING every 15 seconds
        while ws.keep_running:
            ws.ping("ping")
            time.sleep(15)

    # Starting the custom PING loop in its own thread



# Set up the basic configurations
websocket.enableTrace(True)
ws = websocket.WebSocketApp("wss://news.treeofalpha.com/ws",
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close,
                            on_pong=on_pong)
ws.on_open = on_open

# Start the main loop
ws.run_forever()