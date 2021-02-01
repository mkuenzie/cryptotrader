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
    def __init__(self, proximity=.05, stddevs=2):
        self.proximity = proximity
        self.stddevs = stddevs

    def enter(self, market_data, ticker):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=20, \
                                            nbdevup=self.stddevs, nbdevdn=self.stddevs)
        lower_spread = middle[i] - lower[i]
        enter_price = round(lower[i] - (lower_spread * self.proximity),2)
        return min(enter_price, ticker)

    def exit(self, market_data, ticker):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=14, \
                                            nbdevup=self.stddevs, nbdevdn=self.stddevs)
        upper_spread = upper[i] - middle[i]
        exit_price = round(upper[i] + (upper_spread * self.proximity), 2)
        return exit_price


def slope(x1, y1, x2, y2):
    m = (y2 - y1) / (x2 - x1)
    return m

class BbandsDIStrategy(Strategy):

    def __init__(self, proximity=.05, stddevs=2):
        self.proximity = proximity
        self.stddevs = stddevs

    def enter(self, market_data, ticker):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.EMA, timeperiod=20, \
                                            nbdevup=self.stddevs, nbdevdn=self.stddevs)
        plus_di = talib.PLUS_DI(market_data.high.values,
                                market_data.low.values,
                                market_data.close.values, timeperiod=30)
        min_di = talib.MINUS_DI(market_data.high.values,
                                market_data.low.values,
                                market_data.close.values, timeperiod=30)
        adx = talib.ADX(market_data.high.values,
                        market_data.low.values,
                        market_data.close.values, timeperiod=24)
        upper_spread = upper[i] - middle[i]
        up_proximity_mod = self.proximity + (plus_di[i]/1000)
        up_enter_price = round(middle[i] + (upper_spread * up_proximity_mod), 2)
        lower_spread = middle[i] - lower[i]
        low_proximity_mod = self.proximity + (min_di[i]/1000)
        low_enter_price = round(lower[i] - (lower_spread * low_proximity_mod), 2)
        if plus_di[i] > min_di[i] and adx[i] >= 25:
            return min(up_enter_price, ticker)
        elif min_di[i] > plus_di[i] and adx[i] >= 25:
            return min(low_enter_price, ticker)
        else:
            plus_slope = slope(1, plus_di[i - 1], 2, plus_di[i])
            min_slope = slope(1, min_di[i - 1], 2, min_di[i])
            if plus_slope - min_slope > 1:
                return min(up_enter_price, ticker)
            else:
                return min(low_enter_price, ticker)

    def exit(self, market_data, ticker):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=20, \
                                            nbdevup=self.stddevs, nbdevdn=self.stddevs)
        plus_di = talib.PLUS_DI(market_data.high.values,
                                market_data.low.values,
                                market_data.close.values, timeperiod=24)
        min_di = talib.MINUS_DI(market_data.high.values,
                                market_data.low.values,
                                market_data.close.values, timeperiod=24)
        adx = talib.ADX(market_data.high.values,
                                market_data.low.values,
                                market_data.close.values, timeperiod=24)
        upper_spread = upper[i] - middle[i]
        up_proximity_mod = self.proximity + (plus_di[i] / 1000)
        up_exit_price = round(upper[i] + (upper_spread * up_proximity_mod), 2)
        lower_spread = middle[i] - lower[i]
        low_proximity_mod = self.proximity + (min_di[i] / 1000)
        low_exit_price = round(middle[i] - (lower_spread * low_proximity_mod), 2)
        if plus_di[i] > min_di[i] and adx[i] >= 25:
            return max(up_exit_price, ticker)
        elif min_di[i] > plus_di[i] and adx[i] >= 25:
            return max(low_exit_price, ticker)
        else:
            plus_slope = slope(1, plus_di[i - 1], 2, plus_di[i])
            min_slope = slope(1, min_di[i - 1], 2, min_di[i])
            if plus_slope - min_slope > 1:
                return max(up_exit_price, ticker)
            else:
                return max(low_exit_price, ticker)