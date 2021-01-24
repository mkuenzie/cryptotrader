from cryptotrader.cryptotrader import Cryptotrader
from cryptotrader.strategy import Strategy, BbandsStrategy
from datetime import timedelta
import csv


def generate_markdown(trades, initial_wallet, wallet):
    total = len(trades)
    markdown_text = "# Cryptotrader Stats\n\n"
    markdown_text += "Initial Wallet: $" + str(initial_wallet) + "\n"
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

def write_csv(trades):
    csv_columns = list(trades[0].keys())
    csv_file = 'trades.csv'
    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for trade in trades:
                for data in trade:
                    writer.writerow(data)
    except IOError:
        print("I/O error")


initial_wallet = 50
wallet = initial_wallet
trades = []

trader = Cryptotrader(market='BTC-USD', strategy=BbandsStrategy(0.1), fee=0.0035, interval=timedelta(hours=1))


mdfile = generate_markdown(trades, initial_wallet=initial_wallet, wallet=round(wallet,2))
F = open('readme.md', 'w')
F.write(mdfile)
F.close()
