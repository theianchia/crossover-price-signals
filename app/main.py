import tornado.ioloop
import tornado.web
import tornado.websocket

import asyncio
import websockets
import json
import csv
from datetime import datetime
from enum import Enum

TRADING_PAIR = "btcusdt"
SHORT_KLINE_INTERVAL = "1m"
SHORT_KLINE_DURATION = "5mins"
LONG_KLINE_INTERVAL = "5m"
LONG_KLINE_DURATION = "25mins"
PARTIAL_BOOK_INTERVAL = "1000ms"
NUMBER_OF_PERIODS = 5
SMOOTHING_FACTOR = 2
KLINE_COLUMN_HEADERS = ["Timestamp", "Open", "High", "Low", "Close", "Volume"]
PARTIAL_BOOK_COLUMN_HEADERS = [
    "Timestamp", 
    "Best Bid Price", 
    "Best Ask Price", 
    "Mid Price", 
    SHORT_KLINE_DURATION + " SMA", SHORT_KLINE_DURATION + " EMA", 
    LONG_KLINE_DURATION + " SMA", LONG_KLINE_DURATION + " EMA",
    SHORT_KLINE_DURATION + " SMA Crossover",
    LONG_KLINE_DURATION + " SMA Crossover"
]

close_price_short_window = []
total_close_price_short_window = 0
current_short_simple_moving_average = 0
current_short_exponential_moving_average = 0

close_price_long_window = []
total_close_price_long_window = 0
current_long_simple_moving_average = 0
current_long_exponential_moving_average = 0


class CrossoverIndicator(Enum):
    OVER = "Over"
    UNDER = "Under"
    NEUTRAL = "Neutral"


class BinanceShortKlineWebSocketHandler(tornado.websocket.WebSocketHandler):
    async def binance_short_kline_ws(self, uri):
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

                        print(f"Writing to CSV at {formatted_datetime}")

                        with open('binance_short_kline.csv', 'a', newline='') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=KLINE_COLUMN_HEADERS)

                            if csvfile.tell() == 0:
                                writer.writeheader()

                            csv_data = [formatted_datetime, open_price, high_price, low_price, close_price, volume]
                            writer.writerow(dict(zip(KLINE_COLUMN_HEADERS, csv_data)))

                        global close_price_short_window
                        global total_close_price_short_window
                        global current_short_simple_moving_average
                        global current_short_exponential_moving_average

                        close_price_short_window.append(float(close_price))
                        total_close_price_short_window += float(close_price)
                        if len(close_price_short_window) == NUMBER_OF_PERIODS:
                            current_short_simple_moving_average = total_close_price_short_window / NUMBER_OF_PERIODS
                            print(f"Current {SHORT_KLINE_DURATION} SMA: {current_short_simple_moving_average}")
                            current_short_exponential_moving_average = current_short_simple_moving_average
                            print(f"Current {SHORT_KLINE_DURATION} EMA: {current_short_exponential_moving_average}")

                        elif len(close_price_short_window) > NUMBER_OF_PERIODS:
                            total_close_price_short_window -= close_price_short_window.pop(0)
                            current_short_simple_moving_average = total_close_price_short_window / NUMBER_OF_PERIODS
                            print(f"Current {SHORT_KLINE_DURATION} SMA: {current_short_simple_moving_average}")

                            if current_short_exponential_moving_average == 0:
                                current_short_exponential_moving_average = current_short_simple_moving_average
                            else:
                                multiplier = (SMOOTHING_FACTOR / (1 + NUMBER_OF_PERIODS))
                                current_short_exponential_moving_average = float(close_price) * multiplier + current_short_exponential_moving_average * (1 - multiplier)
                                print(f"Current {SHORT_KLINE_DURATION} EMA: {current_short_exponential_moving_average}")


            except Exception as e:
                print(f"Error processing message: {e}")

    def open(self):
        print("Binance Short Kline WebSocket opened")
        binance_kline_uri = f"wss://stream.binance.com:9443/ws/{TRADING_PAIR}@kline_{SHORT_KLINE_INTERVAL}"
        asyncio.create_task(self.binance_short_kline_ws(binance_kline_uri))

    def on_close(self):
        print("Binance Short Kline WebSocket closed")


class BinanceLongKlineWebSocketHandler(tornado.websocket.WebSocketHandler):
    async def binance_long_kline_ws(self, uri):
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

                        print(f"Writing to CSV at {formatted_datetime}")

                        with open('binance_long_kline.csv', 'a', newline='') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=KLINE_COLUMN_HEADERS)

                            if csvfile.tell() == 0:
                                writer.writeheader()

                            csv_data = [formatted_datetime, open_price, high_price, low_price, close_price, volume]
                            writer.writerow(dict(zip(KLINE_COLUMN_HEADERS, csv_data)))

                        global close_price_long_window
                        global total_close_price_long_window
                        global current_long_simple_moving_average
                        global current_long_exponential_moving_average

                        close_price_long_window.append(float(close_price))
                        total_close_price_long_window += float(close_price)
                        if len(close_price_long_window) == NUMBER_OF_PERIODS:
                            current_long_simple_moving_average = total_close_price_long_window / NUMBER_OF_PERIODS
                            print(f"Current {LONG_KLINE_DURATION} SMA: {current_long_simple_moving_average}")
                            current_long_exponential_moving_average = current_long_simple_moving_average
                            print(f"Current {LONG_KLINE_DURATION} EMA: {current_long_exponential_moving_average}")

                        elif len(close_price_long_window) > NUMBER_OF_PERIODS:
                            total_close_price_long_window -= close_price_long_window.pop(0)
                            current_long_simple_moving_average = total_close_price_long_window / NUMBER_OF_PERIODS
                            print(f"Current {LONG_KLINE_DURATION} SMA: {current_long_simple_moving_average}")

                            if current_long_exponential_moving_average == 0:
                                current_long_exponential_moving_average = current_long_simple_moving_average
                            else:
                                multiplier = (SMOOTHING_FACTOR / (1 + NUMBER_OF_PERIODS))
                                current_long_exponential_moving_average = float(close_price) * multiplier + current_long_exponential_moving_average * (1 - multiplier)
                                print(f"Current {LONG_KLINE_DURATION} EMA: {current_long_exponential_moving_average}")


            except Exception as e:
                print(f"Error processing message: {e}")

    def open(self):
        print("Binance Long Kline WebSocket opened")
        binance_kline_uri = f"wss://stream.binance.com:9443/ws/{TRADING_PAIR}@kline_{LONG_KLINE_INTERVAL}"
        asyncio.create_task(self.binance_long_kline_ws(binance_kline_uri))

    def on_close(self):
        print("Binance Long Kline WebSocket closed")


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
                    if 'a' in partial_book_data and len(partial_book_data['a']) > 0:
                        best_ask_price, best_ask_quantity = partial_book_data['a'][0]

                    mid_price = (float(best_bid_price) + float(best_ask_price)) / 2
                    print(f"Current mid price at {formatted_datetime}: {mid_price}")

                    if current_long_simple_moving_average != 0:
                        with open('binance_partial_book.csv', 'a', newline='') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=PARTIAL_BOOK_COLUMN_HEADERS)

                            if csvfile.tell() == 0:
                                writer.writeheader()
                            
                            short_sma_crossover = CrossoverIndicator.UNDER.value
                            if mid_price > current_short_simple_moving_average:
                                short_sma_crossover = CrossoverIndicator.OVER.value
                            elif mid_price == current_short_simple_moving_average:
                                short_sma_crossover = CrossoverIndicator.NEUTRAL.value

                            long_sma_crossover = CrossoverIndicator.UNDER.value
                            if mid_price > current_long_simple_moving_average:
                                long_sma_crossover = CrossoverIndicator.OVER.value
                            elif mid_price == current_long_simple_moving_average:
                                long_sma_crossover = CrossoverIndicator.NEUTRAL.value

                            csv_data = [
                                formatted_datetime, 
                                best_bid_price, 
                                best_ask_price, 
                                mid_price, 
                                current_short_simple_moving_average, current_short_exponential_moving_average, 
                                current_long_simple_moving_average, current_long_exponential_moving_average,
                                short_sma_crossover,
                                long_sma_crossover
                            ]
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
        (r"/binance-short-kline", BinanceShortKlineWebSocketHandler),
        (r"/binance-long-kline", BinanceLongKlineWebSocketHandler),
        (r"/binance-partial-book", BinancePartialBookWebSocketHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server listening on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
