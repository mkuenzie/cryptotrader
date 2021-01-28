from cryptotrader.cryptotrader import Cryptotrader
from cryptotrader.strategy import BbandsStrategy
from datetime import timedelta, datetime
import daemon
from csv import DictWriter
import time

initial_wallet = 50
usd_wallet = 50
crypto_wallet = 0
trades = []
action = 'BUY'

trader = Cryptotrader(market='BTC-USD', strategy=BbandsStrategy(0.01), fee=0.0035, interval=timedelta(hours=1))


def generate_markdown():
    total = len(trades)
    markdown_text = "# Cryptotrader Stats\n\n"
    markdown_text += "Initial Wallet: $" + str(initial_wallet) + "\n"
    if usd_wallet == 0:
        wallet = round(crypto_wallet * trader.get_ticker(), 2)
    else:
        wallet = round(usd_wallet, 2)
    markdown_text += "Current Wallet: $" + str(wallet) + "\n\n"
    markdown_text += "Gain/Loss: "
    if wallet >= initial_wallet:
        markdown_text += '+ %.2f\n' % (((wallet / initial_wallet) - 1) * 100)
    else:
        markdown_text += '- %.2f\n' % ((1 - (wallet / initial_wallet)) * 100)
    markdown_text += "### Trades \n"
    markdown_text += "| Buy Date | Buy @ Price | Sell Date | Sell @ Price | Start/End Amount | Gain/Loss |\n"
    markdown_text += "| :------------- | :----------: | -----------: | :------------- | :----------: | -----------: |"
    for i in range(0, total - 2, 2):
        buy = trades[i]
        sell = trades[i + 1]
        buy_price = buy['price']
        buy_amnt = buy['amount']
        sell_price = sell['price']
        sell_amnt = sell['amount']
        buy_value = round(buy_price * buy_amnt, 2)
        sell_value = round(sell_price * sell_amnt, 2)
        markdown_text += "| " + str(buy['timestamp']) + " | " + str(buy_amnt) + '@' + str(buy_price) + " | " \
                         + str(sell['timestamp']) + " | " + str(sell_amnt) + ' @ ' + str(sell_price) + " | " \
                         + str(buy_value) + '/' + str(sell_value) + " | "
        if buy_price <= sell_price:
            gain = ((sell_price / buy_price) - 1) * 100
            markdown_text += ("+ %.2f" % gain) + " |\n"
            print('+ %.2f' % gain)
        else:
            loss = (1 - (sell_price / buy_price)) * 100
            markdown_text += ('- %.2f' % loss) + " |\n"
    return markdown_text


def write_csv():
    csv_columns = list(trades[0].keys())
    csv_file = 'trades.csv'
    try:
        with open(csv_file, 'a+', newline='') as csvfile:
            dict_writer = DictWriter(csvfile, fieldnames=csv_columns)
            for trade in trades:
                dict_writer.writerow(trade)
        csvfile.close()
    except IOError:
        print("I/O error")


def write_markdown():
    mdfile = generate_markdown()
    f = open('readme.md', 'w')
    f.write(mdfile)
    f.close()


def trade():
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
            write_markdown()
            if len(trades) > 0:
                write_csv()

        print("Wait 1 min...")
        time.sleep(60)


def run():
    with daemon.DaemonContext():
        trade()


if __name__ == "__main__":
    trade()


