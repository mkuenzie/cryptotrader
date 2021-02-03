from cryptotrader.strategy import Strategy
from datetime import datetime, timedelta

class ChangeStrategy(Strategy):
    def __init__(self, pcnt_dn=.005, pcnt_up=.01, period=timedelta(hours=24), stop_loss=False):
        self.pcnt = pcnt_up
        self.pcnt_dn = pcnt_dn
        self.pcnt_up = pcnt_up
        self.period = period
        self.stop_loss = stop_loss

    def enter(self, market_data, ticker, now):
        then = now - self.period
        then_data = market_data.loc[market_data.index <= then]
        last_candle = then_data.tail(1)
        if last_candle.empty:
            return 0
        last_candle_close = last_candle.close.item()
        if last_candle_close >= ticker:
            pcnt_chg = -1 * (1 - (ticker / last_candle_close))
        else:
            pcnt_chg = (ticker/ last_candle_close) - 1
        if pcnt_chg <= (-1 * self.pcnt):
            return ticker
        else:
            return 0

    def exit(self, market_data, ticker, now, bought_at=0):
        if bought_at == 0:
            return ticker*2
        if bought_at >= ticker:
            pcnt_chg = -1 * (1 - (ticker / bought_at))
        else:
            pcnt_chg = (ticker / bought_at) - 1
        if pcnt_chg >= (2*self.pcnt):
            return ticker
        elif self.stop_loss and pcnt_chg <= -(2*self.pcnt):
            return ticker
        else:
            return ticker*2