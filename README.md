<div align="center">
  <h3>Short-term Crossover Tracking with BTC/USDT</h3>
  <p>Identifying trends and signals using Crossovers on real-time BTC/USDT prices</p>
</div>

## About The Project
This project aims to gain insights into market dynamics by using
* Simple Moving Average (SMA) as a technical indicator to predict future price trends
* Bid-Ask Spread balance to understand buying and selling pressure and market sentiments

By comparing SMA and the current mid-price, we look for `crossovers` which might signal potential momentum as the price rises above or falls below the short-term historical average

##### Real-time BTC/USDT price data from Binance
* [KLine/Candlestick Stream](https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-streams)
* [Partial Book Depth Stream](https://binance-docs.github.io/apidocs/spot/en/#partial-book-depth-streams)

##### Technical Implementation
* Real-time, low latency `WebSocket` communication is used to consume highly-frequent market data from Binance, whilst minimising overhead when maintaining the persistent connection
* Data is instaneously processed and written into csv files for further post-analysis
* The closing price from the 1min KLine stream data is used to calculate the SMA using a 5mins timeframe
* The mid price is calculated by taking the average of the best bid and the best ask price from the Partial Book
* Spread Indicator
  * `BID`: Mid price is closer to the best bid price
  * `ASK`: Mid price is closer to the best ask price
  * `NEUTRAL`: Mid price is the equally close to the best bid and the best ask price

* Crossover Indicator
  * `OVER`: Mid price rises above the SMA
  * `UNDER`: Mid price falls below the SMA
  * `NEUTRAL`: Mid price is equal to the SMA

### What is Simple Moving Average (SMA)
* It is a calculation that represents the average over a set of prices within a certain timeframe
* It can act as a technical indicator that can aid in determining if an asset price will continue in its current trend and direction or not
* It smoothens out short-term price fluctuations and highlights the general direction of the trend

<div>
  <img src="assets/formula.png" width="350">
</div>

[Learn more](https://www.investopedia.com/terms/s/sma.asp)

## Built With
* [Python](https://www.python.org/doc/)
* [Tornado](https://www.tornadoweb.org/en/stable/guide.html)

## Getting Started
1. Install dependencies required
   `pip install -r requirements.txt`
2. Run the application
   ```
   cd app
   python main.py
   ```
3. WebSocket handler endpoints
   ```
   ws://127.0.0.1:8888/binance-klines
   ws://127.0.0.1:8888/binance-partial-book
   ```

## Results


## Improvements
