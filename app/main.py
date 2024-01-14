import tornado.ioloop
import tornado.web
import tornado.websocket

import asyncio
import websockets
import json
import csv
from datetime import datetime

COLUMN_HEADERS = ["Timestamp", "Open", "High", "Low", "Close", "Volume"]

current_total_close_price = 0
current_total_periods = 0
current_simple_moving_average = 0

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        print(f"Received message: {message}")
        self.write_message(f"You sent: {message}")

    def on_close(self):
        print("WebSocket closed")


class BinanceWebSocketHandler(tornado.websocket.WebSocketHandler):
    async def binance_klines_ws(self, uri):
        async with websockets.connect(uri) as ws:
            try:
                while True:
                    data = await ws.recv()
                    self.write_message(f"Received data: {data}")

                    kline_data = json.loads(data)
                    if kline_data.get('k', {}).get('x'):
                        timestamp = kline_data['k']['t'] // 1000
                        datetime_obj = datetime.utcfromtimestamp(timestamp)
                        formatted_datetime = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
                        open_price = kline_data['k']['o']
                        high_price = kline_data['k']['h']
                        low_price = kline_data['k']['l']
                        close_price = kline_data['k']['c']
                        volume = kline_data['k']['v']

                        current_total_close_price += close_price
                        current_total_periods += 1
                        if current_total_periods == 5:
                            current_simple_moving_average = current_total_close_price / current_total_periods
                            print(f"Current 5mins SMA: {current_simple_moving_average}")
                            current_total_close_price = 0
                            current_total_periods = 0

                        print(f"Writing to CSV at {formatted_datetime}")

                        with open('binance_klines.csv', 'a', newline='') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=COLUMN_HEADERS)

                            if csvfile.tell() == 0:
                                writer.writeheader()

                            csv_data = [formatted_datetime, open_price, high_price, low_price, close_price, volume]
                            writer.writerow(dict(zip(COLUMN_HEADERS, csv_data)))

            except Exception as e:
                print(f"Error processing message: {e}")

    def open(self):
        print("WebSocket opened")
        trading_pair = "btcusdt"
        interval = "1m"
        binance_kline_uri = f"wss://stream.binance.com:9443/ws/{trading_pair}@kline_{interval}"
        asyncio.create_task(self.binance_klines_ws(uri))

    def on_close(self):
        print("WebSocket closed")


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, Tornado!")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", WebSocketHandler),
        (r"/binance", BinanceWebSocketHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server listening on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
