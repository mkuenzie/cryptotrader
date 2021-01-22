from cryptotrader.cryptotrader import Cryptotrader
from cryptotrader.strategy import Strategy, BbandsStrategy
from datetime import timedelta
from unittest import TestCase


trader = Cryptotrader(market='BTC-USD', strategy=BbandsStrategy(), fee=0.0025, interval=timedelta(hours=1))
trades = trader.test()
total = len(trades)
for i in range(0, total-2, 2):
    buy = trades[i]
    sell = trades[i+1]
    buy_price = buy['price']
    sell_price = sell['price']
    if buy_price <= sell_price:
        gain = ((sell_price / buy_price) -1) * 100
        print('+ %.2f' % gain)
    else:
        loss = ((buy_price / sell_price) -1) * 100
        print('- %.2f' % loss)