import os
from csv import DictWriter, DictReader

import pandas as pd
from bittrex.bittrex import Bittrex, CandleInterval
from bittrex import websocket
from datetime import datetime, timedelta


def _interval2max(interval):
    min_1 = timedelta(minutes=1)
    min_5 = timedelta(minutes=5)
    hour_1 = timedelta(hours=1)
    day_1 = timedelta(days=1)
    if interval == min_1:
        return 1440
    if interval == min_5:
        return 288
    if interval == hour_1:
        return 1440
    if interval == day_1:
        return 366

def _data2frame(rawdata):
    data = {}
    for m_datum in rawdata:
        for key in m_datum.keys():
            if key not in data.keys():
                data[key] = []
            if key == 'startsAt':
                data[key].append(datetime.strptime(m_datum[key], '%Y-%m-%dT%H:%M:%SZ'))
            else:
                data[key].append(float(m_datum[key]))
    df = pd.DataFrame(data=data, columns=data.keys())
    df = df.set_index('startsAt')
    return df


class Cryptotrader(object):

    def __init__(self, market, strategy, interval=timedelta(minutes=1), action='BUY', fee=0):
        self.exchange = Bittrex(api_key=os.environ.get("BITTREX_API_KEY"),
                                api_secret=os.environ.get("BITTREX_API_SECRET"))
        self.market = market
        self.market_sequence = 0
        self.market_data = pd.DataFrame()
        self.market_start = datetime.now()
        self.strategy = strategy
        self.ticker = {'lastTradeRate': 0}
        self.interval = interval
        self.action = action
        self.fee = fee

    async def update_candles(self, msg):
        sequence = msg['sequence']
        if sequence >= self.market_sequence:
            self.market_sequence = sequence
            delta = msg['delta']
            start = datetime.strptime(delta['startsAt'], '%Y-%m-%dT%H:%M:%SZ')
            df_raw = {
                'startsAt': [start]
            }
            for k in delta.keys():
                if k != 'startsAt':
                    df_raw[k] = [float(delta[k])]
            df = pd.DataFrame(data=df_raw, columns=df_raw.keys())
            df = df.set_index('startsAt')
            existing_f = self.market_data.loc[self.market_data.index == start]
            if existing_f.empty:
                self.market_data = self.market_data.append(df)
            else:
                self.market_data.update(df)

    async def update_ticker(self, msg):
        self.ticker = msg


    def get_ticker(self):
        return float((self.ticker['lastTradeRate']))

    def refresh(self):
        try:
            self.exchange.ping()
        except Exception as e:
            print("Failed to refresh, exchange is unavailable.")
            return False
        self.ticker = self.exchange.markets_ticker(self.market)
        response = self.exchange.markets_candle(self.market, self.interval)
        self.market_sequence = response['sequence']
        market_data = response['data']
        self.market_start = datetime.strptime((market_data[0])['startsAt'], '%Y-%m-%dT%H:%M:%SZ')
        self.market_data = _data2frame(market_data)
        return True

    def eval(self, bought_at=0):
        buy_price = self.strategy.enter(self.market_data, self.get_ticker(), datetime.utcnow())
        sell_price = self.strategy.exit(self.market_data, self.get_ticker(), datetime.utcnow(), bought_at)
        return {'BUY': buy_price, 'SELL': sell_price}

    def backtest(self, start_at=''):
        usd_wallet = 100
        crypto_wallet = 0
        signal_data = self.market_data

        if start_at == '':
            start = 30
            steps = len(signal_data.index)
            curr_tick = signal_data.head(1).index.item() + (30 * self.interval)
        else:
            check = start_at
            #Append earlier data from same day
            today = datetime(self.market_start.year, self.market_start.month, self.market_start.day, 0, 0)
            signal_data = signal_data.append(_data2frame( \
                self.exchange.markets_candle_history(self.market, today, self.interval)))
            while check not in signal_data.index:
                signal_data = signal_data.append(_data2frame(\
                    self.exchange.markets_candle_history(self.market, check, self.interval)))
                check = check + self.interval * _interval2max(self.interval)
            signal_data.sort_index(inplace=True)
            d = signal_data.loc[signal_data.index >= start_at]
            start = 0
            steps = len(d.index) - 1
            curr_tick = d.head(1).index.item()
        next_tick = curr_tick + self.interval
        tick_data = _data2frame(self.exchange.markets_candle_history(self.market, curr_tick))
        curr_action = 'BUY'
        trades = []
        bought_at = 0
        for i in range(start, steps):
            if curr_tick not in tick_data.index:
                if curr_tick <= today:
                    tick_data = tick_data.append(_data2frame(self.exchange.markets_candle_history(self.market, curr_tick)))
                else:
                    d = self.exchange.markets_candle(self.market)
                    tick_data = tick_data.append(_data2frame(d['data']))
            sliced_data = signal_data.loc[signal_data.index <= curr_tick]
            sliced_tick_data = tick_data.loc[(tick_data.index >= curr_tick) & (tick_data.index < next_tick)]
            for tick in sliced_tick_data.index:
                tick_close = sliced_tick_data.loc[sliced_tick_data.index == tick].close.item()
                tick_high = sliced_tick_data.loc[sliced_tick_data.index == tick].high.item()
                tick_low = sliced_tick_data.loc[sliced_tick_data.index == tick].low.item()
                sliced_data.loc[curr_tick]['high'] = tick_high
                sliced_data.loc[curr_tick]['close'] = tick_close
                sliced_data.loc[curr_tick]['low'] = tick_low
                if curr_action == 'BUY':
                    buy_price = self.strategy.enter(sliced_data, tick_close, tick)
                    if tick_low <= buy_price <= tick_high:
                        crypto_wallet = round(usd_wallet / buy_price, 8)
                        commission = round(usd_wallet * self.fee, 8)
                        usd_wallet = 0
                        bought_at =buy_price
                        trades.append({'timestamp': tick, 'action': curr_action,
                                       'price': buy_price, 'amount': crypto_wallet, 'fee': commission})
                        curr_action = 'SELL'
                else:
                    sell_price = self.strategy.exit(sliced_data, tick_close, tick, bought_at)
                    if tick_low <= sell_price <= tick_high:
                        commission = round(crypto_wallet * sell_price * self.fee, 8)
                        trades.append({'timestamp': tick, 'action': curr_action,
                                       'price': sell_price, 'amount': crypto_wallet, 'fee': commission})
                        usd_wallet = round(crypto_wallet * sell_price, 8)
                        crypto_wallet = 0
                        curr_action = 'BUY'
            curr_tick = curr_tick + self.interval
            next_tick = curr_tick + self.interval
        return trades

    def test(self, days=30, start_at=''):
        usd_wallet = 100
        crypto_wallet = 0
        if start_at == '':
            test_data = self.market_data
        else:
            test_data = self.market_data[self.market_data.index >= start_at]
        steps = len(test_data.index)
        curr_tick = test_data.head(1).index.item() + (30 * self.interval)
        curr_action = 'BUY'
        trades = []
        for i in range(30, steps):
            sliced_data = test_data.loc[test_data.index <= curr_tick]
            tick_data = test_data.loc[test_data.index == curr_tick]
            tick_high = tick_data.high.item()
            tick_low = tick_data.low.item()
            if curr_action == 'BUY':
                buy_price = self.strategy.enter(sliced_data, tick_data.close.item())
                if tick_low <= buy_price <= tick_high:
                    crypto_wallet = round(usd_wallet / buy_price, 8)
                    commission = round(usd_wallet * self.fee, 8)
                    usd_wallet = 0
                    trades.append({'timestamp': curr_tick, 'action': curr_action,
                                   'price': buy_price, 'amount': crypto_wallet, 'fee': commission})
                    curr_action = 'SELL'
            else:
                sell_price = self.strategy.exit(sliced_data, tick_data.close.item())
                if tick_low <= sell_price <= tick_high:
                    commission = round(crypto_wallet * sell_price * self.fee, 8)
                    trades.append({'timestamp': curr_tick, 'action': curr_action,
                                   'price': sell_price, 'amount': crypto_wallet, 'fee': commission})
                    usd_wallet = round(crypto_wallet * sell_price, 8)
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

    def write_csv(self, trades, filename, append=True):
        if len(trades) == 0:
            return
        csv_columns = list(trades[0].keys())
        csv_file = filename
        if append:
            mode = 'a+'
        else:
            mode = 'w'
        try:
            with open(csv_file, mode, newline='') as csvfile:
                dict_writer = DictWriter(csvfile, fieldnames=csv_columns)
                if not append:
                    dict_writer.writeheader()
                for trade in trades:
                    dict_writer.writerow(trade)
            csvfile.close()
        except IOError:
            print("I/O error")

    def read_csv(self, filename):
        trades = []
        with open(filename, 'r') as data:
            for line in DictReader(data):
                timestamp = datetime.strptime(line['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
                trade = {
                    'timestamp': timestamp,
                    'action': line['action'],
                    'price': float(line['price']),
                    'amount': float(line['amount']),
                    'fee': float(line['fee'])
                }
                trades.append(trade)
        return trades

    def generate_markdown(self, trades, initial_wallet, usd_wallet, crypto_wallet):
        total = len(trades)
        markdown_text = "# Cryptotrader Stats\n\n"
        markdown_text += "Initial Wallet: $" + str(initial_wallet) + "\n\n"
        if usd_wallet == 0:
            wallet = round(crypto_wallet * self.get_ticker(), 8)
        else:
            wallet = round(usd_wallet, 8)
        markdown_text += "Current Wallet: $" + str(wallet) + "\n\n"
        markdown_text += "Gain/Loss: "
        if wallet >= initial_wallet:
            markdown_text += '+ %.2f\n\n' % (((wallet / initial_wallet) - 1) * 100)
        else:
            markdown_text += '- %.2f\n\n' % ((1 - (wallet / initial_wallet)) * 100)
        markdown_text += "### Trades \n\n"
        markdown_text += "| Buy Date | Buy @ Price | Sell Date | Sell @ Price | Start/End Amount | Gain/Loss |\n"
        markdown_text += "| :------------- | :----------: | -----------: | :------------- | :----------: | -----------: |\n"
        for i in range(0, total - 1, 2):
            buy = trades[i]
            sell = trades[i + 1]
            buy_price = buy['price']
            buy_amnt = buy['amount']
            buy_fee = buy['fee']
            sell_price = sell['price']
            sell_amnt = sell['amount']
            sell_fee = sell['fee']
            buy_value = round(buy_price * buy_amnt, 8)
            sell_value = round(sell_price * sell_amnt, 8) - sell_fee
            buy_ts = buy['timestamp'].strftime("%m\-%d\-%Y %H:%M:%S")
            sell_ts = sell['timestamp'].strftime("%m\-%d\-%Y %H:%M:%S")
            markdown_text += "| " + buy_ts + " | " + str(buy_amnt) + '@' + str(buy_price) + " | " \
                             + sell_ts + " | " + str(sell_amnt) + ' @ ' + str(sell_price) + " | " \
                             + str(buy_value) + '/' + str(sell_value) + " | "
            if buy_price <= sell_price:
                gain = ((sell_price / buy_price) - 1) * 100
                markdown_text += ("+ %.2f" % gain) + " |\n"
            else:
                loss = (1 - (sell_price / buy_price)) * 100
                markdown_text += ('- %.2f' % loss) + " |\n"
        return markdown_text

    def get_action(self, trades):
        cnt = len(trades)
        last_trade = trades[cnt - 1]
        last_action = last_trade['action']
        if last_action == 'BUY':
            return 'SELL'
        elif last_action == 'SELL':
            return 'BUY'
        else:
            raise ValueError("Invalid action in trades")



