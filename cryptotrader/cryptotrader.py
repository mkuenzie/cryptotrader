
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
        self.ticker = {'lastTradeRate': 0}
        self.interval = interval
        self.action = action
        self.fee = fee
        self.refresh()

    def get_ticker(self):
        return float((self.ticker['lastTradeRate']))

    def refresh(self):
        try:
            self.exchange.ping()
        except Exception as e:
            print("Failed to refresh, exchange is unavailable.")
            return False
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
        return True

    def eval(self):
        buy_price = self.strategy.enter(self.market_data, self.get_ticker())
        sell_price = self.strategy.exit(self.market_data, self.get_ticker())
        return {'BUY': buy_price, 'SELL': sell_price}

    def test(self, start_at=''):
        usd_wallet = 100
        crypto_wallet = 0
        if start_at == '':
            test_data = self.market_data
        else:
            test_data = self.market_data.loc[self.market_data.startsAt >= start_at]
        steps = len(test_data.index)
        curr_tick = test_data.head(1).startsAt.item() + (30 * self.interval)
        curr_action = 'BUY'
        trades = []
        for i in range(30, steps):
            sliced_data = test_data.loc[test_data.startsAt <= curr_tick]
            tick_data = test_data.loc[test_data.startsAt == curr_tick]
            tick_high = tick_data.high.item()
            tick_low = tick_data.low.item()
            if curr_action == 'BUY':
                buy_price = self.strategy.enter(sliced_data, tick_data.close.item())
                if tick_low <= buy_price <= tick_high:
                    crypto_wallet = round(usd_wallet/buy_price, 6)
                    commission = round(usd_wallet * self.fee, 2)
                    usd_wallet = 0
                    trades.append({'timestamp': curr_tick, 'action': curr_action,
                                   'price': buy_price, 'amount': crypto_wallet, 'fee': commission})
                    curr_action = 'SELL'
            else:
                sell_price = self.strategy.exit(sliced_data, tick_data.close.item())
                if tick_low <= sell_price <= tick_high:
                    commission = round(crypto_wallet * sell_price * self.fee, 2)
                    trades.append({'timestamp': curr_tick, 'action': curr_action,
                                   'price': sell_price,  'amount': crypto_wallet, 'fee': commission})
                    usd_wallet = round(crypto_wallet * sell_price, 2)
                    crypto_wallet = 0
                    curr_action = 'BUY'
            curr_tick = curr_tick + self.interval
        return trades

    def strike(self, action, quantity):
        try:
            self.exchange.ping()
        except Exception as e:
            print("Failed to place order, exchange is unavailable.")
            return None
        if action == 'BUY':
            return self.exchange.buy(self.market, quantity)
        if action == 'SELL':
            return self.exchange.sell(self.market, quantity)
        raise ValueError('Invalid value for action')



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


