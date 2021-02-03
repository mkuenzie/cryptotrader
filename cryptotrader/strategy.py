#Takes DataFrame of market and returns a price to enter /exit market at
import pandas as pd
import talib
from talib import MA_Type
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import statistics

class Strategy(object):
    def __init__(self):
        pass

    def enter(self, market_data, ticker, now):
        last_candle = market_data.loc[len(market_data.index)-1]
        return last_candle.close.item()

    def exit(self, market_data, ticker, now, bought_at=0):
        last_candle = market_data.loc[len(market_data.index)-1]
        return last_candle.close.item()


class BbandsBearStrategy(Strategy):
    #if trending up, buy near middle, sell near upper
    #if tending down buy near lower, sell near middle
    # 'near' is 5% of the difference between either upper/middle or middle/lower
    def __init__(self, proximity=.05, stddevs=2):
        self.proximity = proximity
        self.stddevs = stddevs

    def enter(self, market_data, ticker, now):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=20, \
                                            nbdevup=self.stddevs, nbdevdn=self.stddevs)
        lower_spread = middle[i] - lower[i]
        enter_price = round(lower[i] - (lower_spread * self.proximity),8)
        return min(enter_price, ticker)

    def exit(self, market_data, ticker, now, bought_at=0):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=14, \
                                            nbdevup=self.stddevs, nbdevdn=self.stddevs)
        upper_spread = middle[i] - lower[i]
        exit_price = round(middle[i] - (upper_spread * self.proximity), 8)
        return exit_price


class BbandsStrategy(Strategy):
    #if trending up, buy near middle, sell near upper
    #if tending down buy near lower, sell near middle
    # 'near' is 5% of the difference between either upper/middle or middle/lower
    def __init__(self, proximity=.05, stddevs=2):
        self.proximity = proximity
        self.stddevs = stddevs

    def enter(self, market_data, ticker, now):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=20, \
                                            nbdevup=self.stddevs, nbdevdn=self.stddevs)
        lower_spread = middle[i] - lower[i]
        enter_price = round(lower[i] - (lower_spread * self.proximity),8)
        return min(enter_price, ticker)

    def exit(self, market_data, ticker, now, bought_at=0):
        i = len(market_data) - 1
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=14, \
                                            nbdevup=self.stddevs, nbdevdn=self.stddevs)
        upper_spread = upper[i] - middle[i]
        exit_price = round(upper[i] + (upper_spread * self.proximity), 8)
        return exit_price


class BBP_RSIStrategy(Strategy):
    def __init__(self, stddevs=2):
        self.stddevs = stddevs

    def bbp(self, market_data):
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=20, \
                                            nbdevup=self.stddevs, nbdevdn=self.stddevs)
        bbp = (market_data['close'] - lower) / (upper - lower)
        return bbp

    def enter(self, market_data, ticker, now):
        i = len(market_data) - 1
        bbp = self.bbp(market_data)
        rsi = talib.RSI(market_data['close'].values)
        if rsi[i] < 30 and bbp[i] < 0:
            return ticker
        else:
            return 0

    def exit(self, market_data, ticker, now, bought_at=0):
        i = len(market_data) - 1
        bbp = self.bbp(market_data)
        rsi = talib.RSI(market_data['close'].values)
        if rsi[i] > 70 and bbp[i] > 1:
            return ticker
        else:
            return ticker*2

def slope(x1, y1, x2, y2):
    m = (y2 - y1) / (x2 - x1)
    return m

class BbandsDIStrategy(Strategy):

    def __init__(self, proximity=.05, stddevs=2):
        self.proximity = proximity
        self.stddevs = stddevs

    def enter(self, market_data, ticker, now):
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
        up_enter_price = round(middle[i] + (upper_spread * up_proximity_mod), 8)
        lower_spread = middle[i] - lower[i]
        low_proximity_mod = self.proximity + (min_di[i]/1000)
        low_enter_price = round(lower[i] - (lower_spread * low_proximity_mod), 8)
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

    def exit(self, market_data, ticker, now, bought_at=0):
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
        up_exit_price = round(upper[i] + (upper_spread * up_proximity_mod), 8)
        lower_spread = middle[i] - lower[i]
        low_proximity_mod = self.proximity + (min_di[i] / 1000)
        low_exit_price = round(middle[i] - (lower_spread * low_proximity_mod), 8)
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

class PeaksTroughsStrategy(Strategy):
    def __init__(self, period=20, delay=timedelta(minutes=5), prominence_mod=.25):
        self.period = period
        self.delay = delay
        self.prominence_mod = prominence_mod

    def enter(self, market_data, ticker, now):
        cnt = len(market_data.index)
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=self.period)
        last_tick = market_data.iloc[cnt-1].name
        last_last_tick = market_data.iloc[cnt-2].name
        interval = last_tick - last_last_tick
        start = last_tick - ((self.period - 1) * interval)
        d = market_data.loc[market_data.index >= start]
        i = len(upper) - 1
        prom = (upper[i] - middle[i]) * self.prominence_mod * .25
        x = d['close'].values
        troughs, _ = find_peaks(-x, prominence=prom)
        if len(troughs) == 0:
            return 0
        last_trough = troughs[len(troughs) -1]
        last_op = d.iloc[last_trough]

        if now - self.delay <= last_op.name:
            return ticker
        else:
            return 0

    def exit(self, market_data, ticker, now, bought_at=0):
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=self.period)
        cnt = len(market_data.index)
        last_tick = market_data.iloc[cnt - 1].name
        last_last_tick = market_data.iloc[cnt - 2].name
        interval = last_tick - last_last_tick
        start = last_tick - ((self.period - 1) * interval)
        d = market_data.loc[market_data.index >= start]
        i = len(upper) - 1
        prom = (upper[i] - middle[i]) * self.prominence_mod
        x = d['close'].values
        peaks, _ = find_peaks(x, prominence=prom)
        if len(peaks) == 0:
            return ticker*2
        last_peak = peaks[len(peaks) - 1]
        last_op = d.iloc[last_peak]

        if now - self.delay <= last_op.name:
            return ticker
        else:
            return ticker*2


class PeaksTroughsMedianStrategy(Strategy):
    def __init__(self, period=20, prominence_mod=.25):
        self.period = period
        self.prominence_mod = prominence_mod

    def enter(self, market_data, ticker, now):
        cnt = len(market_data.index)
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=self.period)
        last_tick = market_data.iloc[cnt-1].name
        last_last_tick = market_data.iloc[cnt-2].name
        interval = last_tick - last_last_tick
        start = last_tick - ((self.period - 1) * interval)
        d = market_data.loc[market_data.index >= start]
        i = len(upper) - 1
        prom = (upper[i] - middle[i]) * self.prominence_mod * .25
        x = d['close'].values
        troughs, _ = find_peaks(-x, prominence=prom)
        if len(troughs) == 0:
            return 0
        trough_prices = []
        for trough in troughs:
            t = d.iloc[trough]
            trough_prices.append(t.close)
        return statistics.median(trough_prices)

    def exit(self, market_data, ticker, now, bought_at=0):
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=self.period)
        cnt = len(market_data.index)
        last_tick = market_data.iloc[cnt - 1].name
        last_last_tick = market_data.iloc[cnt - 2].name
        interval = last_tick - last_last_tick
        start = last_tick - ((self.period - 1) * interval)
        d = market_data.loc[market_data.index >= start]
        i = len(upper) - 1
        prom = (upper[i] - middle[i]) * self.prominence_mod
        x = d['close'].values
        peaks, _ = find_peaks(x, prominence=prom)
        if len(peaks) == 0:
            return ticker*2
        peak_prices = []
        for peak in peaks:
            p = d.iloc[peak]
            peak_prices.append(p.close)
        return statistics.median(peak_prices)


class PeaksTroughsMeanStrategy(Strategy):
    def __init__(self, period=20, prominence_mod=.25):
        self.period = period
        self.prominence_mod = prominence_mod

    def enter(self, market_data, ticker, now):
        cnt = len(market_data.index)
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=self.period)
        last_tick = market_data.iloc[cnt-1].name
        last_last_tick = market_data.iloc[cnt-2].name
        interval = last_tick - last_last_tick
        start = last_tick - ((self.period - 1) * interval)
        d = market_data.loc[market_data.index >= start]
        i = len(upper) - 1
        prom = (upper[i] - middle[i]) * self.prominence_mod * .25
        x = d['close'].values
        troughs, _ = find_peaks(-x, prominence=prom)
        if len(troughs) == 0:
            return 0
        trough_prices = []
        for trough in troughs:
            t = d.iloc[trough]
            trough_prices.append(t.close)
        return statistics.mean(trough_prices)

    def exit(self, market_data, ticker, now, bought_at=0):
        upper, middle, lower = talib.BBANDS(market_data.close.values, matype=MA_Type.T3, timeperiod=self.period)
        cnt = len(market_data.index)
        last_tick = market_data.iloc[cnt - 1].name
        last_last_tick = market_data.iloc[cnt - 2].name
        interval = last_tick - last_last_tick
        start = last_tick - ((self.period - 1) * interval)
        d = market_data.loc[market_data.index >= start]
        i = len(upper) - 1
        prom = (upper[i] - middle[i]) * self.prominence_mod
        x = d['close'].values
        peaks, _ = find_peaks(x, prominence=prom)
        if len(peaks) == 0:
            return ticker*2
        peak_prices = []
        for peak in peaks:
            p = d.iloc[peak]
            peak_prices.append(p.close)
        return statistics.mean(peak_prices)