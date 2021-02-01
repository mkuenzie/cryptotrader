from cryptotrader.cryptotrader import Cryptotrader
from cryptotrader.strategy import BbandsStrategy, BbandsDIStrategy
from datetime import timedelta, datetime

def write_markdown(trades, initial_wallet, usd_wallet, crypto_wallet):
    mdfile = trader.generate_markdown(trades, initial_wallet, usd_wallet, crypto_wallet)
    f = open('readme.md', 'w')
    f.write(mdfile)
    f.close()

proximity = 0.25

trader = Cryptotrader(market='BTC-USD', strategy=BbandsStrategy(proximity=proximity, stddevs=2), fee=0.0035, interval=timedelta(hours=1))
trader.refresh()
trades = trader.test2(start_at=datetime(2021, 1, 25, 12, 0, 0))
total = len(trades)
wallet = 100
for i in range(0, total-2, 2):
    buy = trades[i]
    sell = trades[i+1]
    buy_price = buy['price']
    sell_price = sell['price']
    if buy_price <= sell_price:
        gain = ((sell_price / buy_price) - 1) * 100
        wallet = wallet + (wallet * (gain/100))
        print(trades[i])
        print(trades[i+1])
        print('+ %.2f %%' % gain)
    else:
        loss = (1 - (sell_price / buy_price)) * 100
        wallet = wallet - (wallet * (loss/100))
        print(trades[i])
        print(trades[i + 1])
        print('- %.2f %%' % loss)
print(wallet)
