
import os
import pandas as pd
from bittrex.bittrex import Bittrex, CandleInterval
from datetime import datetime, timedelta


class Cryptotrader(object):

    def __init__(self, market, strategy, interval=timedelta(minutes=1), action='BUY', fee=0):
        self.exchange = Bittrex(api_key=os.environ.get("BITTREX_API_KEY"), api_secret=os.environ.get("BITTREX_API_SECRET"))
        self.market = market
        self.market_data = pd.DataFrame()
        self.market_start = datetime.now()
        self.strategy = strategy
        self.ticker = 0
        self.interval = interval
        self.refresh()
        self.action = action
        self.fee = fee

    def refresh(self):
        self.ticker = self.exchange.markets_ticker(self.market)
        market_data = self.exchange.markets_candle(self.market, self.interval)
        self.market_start = datetime.strptime((market_data[0])['startsAt'], '%Y-%m-%dT%H:%M:%SZ')
        data = {}
        for m_datum in market_data:
            if m_datum['startsAt'] not in self.market_data.index:
                for key in m_datum.keys():
                    if key not in data.keys():
                        data[key] = []
                    if key == 'startsAt':
                        data[key].append(datetime.strptime(m_datum[key], '%Y-%m-%dT%H:%M:%SZ'))
                    else:
                        data[key].append(float(m_datum[key]))
        df = pd.DataFrame(data=data)
        self.market_data = self.market_data.append(df)

    def eval(self):
        buy_price = self.strategy.enter(self.market_data)
        sell_price = self.strategy.exit(self.marker_data)
        return {'BUY': buy_price, 'SELL': sell_price}

    def test(self, action='BUY'):
        wallet = 100
        steps = len(self.market_data.index)
        curr_tick = self.market_start + (30 * self.interval)
        curr_action = action
        trades = []
        for i in range(30, steps):
            sliced_data = self.market_data.loc[self.market_data.startsAt <= curr_tick]
            tick_data = self.market_data.loc[self.market_data.startsAt == curr_tick]
            tick_high = tick_data.high.item()
            tick_low = tick_data.low.item()
            if curr_action == 'BUY':
                buy_price = self.strategy.enter(sliced_data, tick_data.close.item())
                if tick_low <= buy_price <= tick_high:
                    trades.append({'timestamp': curr_tick, 'action': curr_action,
                                   'price': buy_price, 'fee': (buy_price * self.fee)})
                    curr_action = 'SELL'
            else:
                sell_price = self.strategy.exit(sliced_data, tick_data.close.item())
                if tick_low <= sell_price <= tick_high:
                    trades.append({'timestamp': curr_tick, 'action': curr_action,
                                   'price': sell_price, 'fee': (sell_price * self.fee)})
                    curr_action = 'BUY'
            curr_tick = curr_tick + self.interval
        return trades




# init
# setup exchange, strategy, market data
#
# refresh
#update market & ticker data
#
# eval
# find buy/sell strike prices from set strategy
#
# test
#
# walk current market_data set and output trades strategy would make
#
# strike
# buy/sell at market
#
# trade
# action strategy on a market
#
#


