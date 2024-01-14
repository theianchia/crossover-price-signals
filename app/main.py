import tornado.ioloop
import tornado.web
import tornado.websocket

import asyncio
import websockets
import json
import csv
from datetime import datetime

TRADING_PAIR = "btcusdt"
KLINES_INTERVAL = "1m"
PARTIAL_BOOK_INTERVAL = "1000ms"
KLINES_COLUMN_HEADERS = ["Timestamp", "Open", "High", "Low", "Close", "Volume"]
PARTIAL_BOOK_COLUMN_HEADERS = ["Timestamp", "Best Bid Price", "Best Ask Price", "Mid Price"]

current_total_close_price = 0
current_total_periods = 0
current_simple_moving_average = 0

current_mid_price = 0


class BinanceKlinesWebSocketHandler(tornado.websocket.WebSocketHandler):
    async def binance_klines_ws(self, uri):
        async with websockets.connect(uri) as ws:
            try:
                while True:
                    data = await ws.recv()
                    self.write_message(f"Received data: {data}")

                    klines_data = json.loads(data)
                    if klines_data.get('k', {}).get('x'):
                        timestamp = klines_data['k']['t'] // 1000
                        datetime_obj = datetime.utcfromtimestamp(timestamp)
                        formatted_datetime = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
                        open_price = klines_data['k']['o']
                        high_price = klines_data['k']['h']
                        low_price = klines_data['k']['l']
                        close_price = klines_data['k']['c']
                        volume = klines_data['k']['v']

                        print(f"Writing to CSV at {formatted_datetime}")

                        with open('binance_klines.csv', 'a', newline='') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=KLINES_COLUMN_HEADERS)

                            if csvfile.tell() == 0:
                                writer.writeheader()

                            csv_data = [formatted_datetime, open_price, high_price, low_price, close_price, volume]
                            writer.writerow(dict(zip(KLINES_COLUMN_HEADERS, csv_data)))

                        global current_total_close_price
                        global current_total_periods
                        global current_simple_moving_average
                        current_total_close_price += float(close_price)
                        current_total_periods += 1
                        if current_total_periods == 5:
                            current_simple_moving_average = current_total_close_price / current_total_periods
                            print(f"Current 5mins SMA: {current_simple_moving_average}")
                            current_total_close_price = 0
                            current_total_periods = 0

            except Exception as e:
                print(f"Error processing message: {e}")

    def open(self):
        print("Binance Klines WebSocket opened")
        binance_klines_uri = f"wss://stream.binance.com:9443/ws/{TRADING_PAIR}@kline_{KLINES_INTERVAL}"
        asyncio.create_task(self.binance_klines_ws(binance_klines_uri))

    def on_close(self):
        print("Binance Klines WebSocket closed")


class BinancePartialBookWebSocketHandler(tornado.websocket.WebSocketHandler):
    async def binance_partial_book_ws(self, uri):
        async with websockets.connect(uri) as ws:
            try:
                while True:
                    data = await ws.recv()
                    self.write_message(f"Received data: {data}")

                    partial_book_data = json.loads(data)
                    timestamp = partial_book_data['E'] // 1000
                    datetime_obj = datetime.utcfromtimestamp(timestamp)
                    formatted_datetime = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
                    best_bid_price, best_bid_quantity, best_ask_price, best_ask_quantity = 0, 0, 0, 0
                    if 'b' in partial_book_data and len(partial_book_data['b']) > 0:
                        best_bid_price, best_bid_quantity = partial_book_data['b'][0]
                        print(f"Best bid price: {best_bid_price}, best bid quantity: {best_bid_quantity}")
                    if 'a' in partial_book_data and len(partial_book_data['a']) > 0:
                        best_ask_price, best_ask_quantity = partial_book_data['a'][0]
                        print(f"Best ask price: {best_ask_price}, best ask quantity: {best_ask_quantity}")
                    
                    global current_mid_price
                    current_mid_price = (float(best_bid_price) + float(best_ask_price)) / 2
                    print(f"Current mid price: {current_mid_price}")

                    with open('binance_partial_book.csv', 'a', newline='') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=PARTIAL_BOOK_COLUMN_HEADERS)

                        if csvfile.tell() == 0:
                            writer.writeheader()

                        csv_data = [formatted_datetime, best_bid_price, best_ask_price, current_mid_price]
                        writer.writerow(dict(zip(PARTIAL_BOOK_COLUMN_HEADERS, csv_data)))

            except Exception as e:
                print(f"Error processing message: {e}")

    def open(self):
        print("Binance Partial Book WebSocket opened")
        binance_partial_book_uri = f"wss://stream.binance.com:9443/ws/{TRADING_PAIR}@depth@{PARTIAL_BOOK_INTERVAL}"
        asyncio.create_task(self.binance_partial_book_ws(binance_partial_book_uri))

    def on_close(self):
        print("Binance Partial Book WebSocket closed")


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, Tornado!")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/binance-klines", BinanceKlinesWebSocketHandler),
        (r"/binance-partial-book", BinancePartialBookWebSocketHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server listening on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
