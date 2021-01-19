
import os
from bittrex.bittrex import Bittrex

class Cryptotrader(object):

    def __init__(self):
        self.exchange = None

    def connect(self):
        self.exchange = Bittrex(api_key=os.environ.get("BITTREX_API_KEY"), api_secret=os.environ.get("BITTREX_API_SECRET"))

    def

class Candlestick(object):
    def __init__(self, start):
        self.start = start


trader = Cryptotrader()
trader.connect()

