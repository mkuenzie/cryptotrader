#Takes DataFrame of market and returns a price to enter /exit market at
import pandas as pd
import talib
from talib import MA_Type

class Strategy(object):
    def __init__(self):
        pass

    def enter(self, market_data, ticker):
        last_candle = market_data.loc[len(market_data.index)-1]
        return last_candle.close.item()

    def exit(self, market_data, ticker):
        last_candle = market_data.loc[len(market_data.index)-1]
        return last_candle.close.item()

class BbandsStrategy(Strategy):
    #if trending up, buy near middle, sell near upper
    #if tending down buy near lower, sell near middle
    # 'near' is 5% of the difference between either upper/middle or middle/lower
    def __init__(self, proximity=.05):
        self.proximity = proximity

    def enter(self, market_data, ticker):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3)
        plus_di = talib.PLUS_DI(market_data.high.values,
                                market_data.low.values,
                                market_data.close.values)
        min_di = talib.MINUS_DI(market_data.high.values,
                                market_data.low.values,
                                market_data.close.values)
        if plus_di[i] >= min_di[i]:
            upper_spread = upper[i] - middle[i]
            return round(middle[i] + (upper_spread * self.proximity),2)
        else:
            lower_spread = middle[i] - lower[i]
            return round(lower[i] + (lower_spread * self.proximity),2)

    def exit(self, market_data, ticker):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3)
        plus_di = talib.PLUS_DI(market_data.high.values,
                                market_data.low.values,
                                market_data.close.values)
        min_di = talib.MINUS_DI(market_data.high.values,
                                market_data.low.values,
                                market_data.close.values)
        if plus_di[i] >= min_di[i]:
            upper_spread = upper[i] - middle[i]
            return round(upper[i] - (upper_spread * self.proximity), 2)
        else:
            lower_spread = middle[i] - lower[i]
            return round(middle[i] - (lower_spread * self.proximity),2)

