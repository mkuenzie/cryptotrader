from cryptotrader.cryptotrader import Cryptotrader
from cryptotrader.strategy import BbandsStrategy, BbandsStrategy2, BbandsStrategy3
from datetime import timedelta, datetime
import daemon
from csv import DictWriter
import time

initial_wallet = 50
usd_wallet = 54.83
crypto_wallet = 0
trades = []
action = 'BUY'

trader = Cryptotrader(market='BTC-USD', strategy=BbandsStrategy3(proximity=0.25, stddevs=2), fee=0.0035, interval=timedelta(hours=1))
trades = trader.read_csv('trades.csv')

def write_markdown(trades, initial_wallet, usd_wallet, crypto_wallet):
    mdfile = trader.generate_markdown(trades, initial_wallet, usd_wallet, crypto_wallet)
    f = open('readme.md', 'w')
    f.write(mdfile)
    f.close()



def trade():
    session_start = datetime.utcnow()
    while True:
        global usd_wallet, crypto_wallet, action
        refresh_success = trader.refresh()
        if refresh_success:
            ticker = trader.get_ticker()
            plan = trader.eval()
            now = datetime.now()
            print("---------" + str(now) + "------------")
            print("Looking to " + action)
            print("Current Ticker:")
            print(ticker)
            print("Strategy Plan:")
            print(plan)
            buy_price = plan['BUY']
            sell_price = plan['SELL']
            if ticker <= buy_price and action == 'BUY':
                quantity = round((usd_wallet / ticker), 8)
                order = trader.strike(action, quantity)
                fill_quantity = float(order['fillQuantity'])
                proceeds = float(order['proceeds'])
                fee = float(order['commission'])
                price = round(proceeds / fill_quantity, 2)
                trade = {
                    'timestamp': datetime.strptime(order['closedAt'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                    'action': action,
                    'price': price,
                    'amount': fill_quantity,
                    'fee': fee
                }
                print(trade)
                trades.append(trade)
                usd_wallet = 0
                crypto_wallet = fill_quantity
                action = 'SELL'
            if ticker >= sell_price and action == 'SELL':
                quantity = crypto_wallet
                order = trader.strike(action, quantity)
                fill_quantity = float(order['fillQuantity'])
                proceeds = float(order['proceeds'])
                fee = float(order['commission'])
                price = round(proceeds / fill_quantity, 2)
                trade = {
                    'timestamp': datetime.strptime(order['closedAt'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                    'action': action,
                    'price': price,
                    'amount': fill_quantity,
                    'fee': fee
                }
                print(trade)
                trades.append(trade)
                usd_wallet = fill_quantity
                crypto_wallet = 0
                action = 'BUY'
            write_markdown(trades, initial_wallet, usd_wallet, crypto_wallet)
            new_trades = [d for d in trades if d['timestamp'] > session_start]
            if len(trades) > 0:
                trader.write_csv(new_trades, 'trades.csv', append=True)
        print("Wait 1 min...")
        time.sleep(60)


def run():
    with daemon.DaemonContext():
        trade()


if __name__ == "__main__":
    trade()


