import asyncio
from cryptotrader.cryptotrader import Cryptotrader
from cryptotrader.strategy import BbandsStrategy, BbandsDIStrategy
from datetime import timedelta, datetime
from bittrex import websocket
from bittrex.bittrex import CandleInterval
import os

initial_wallet = 150

LOCK = asyncio.Lock()

def write_markdown(markdown):
    f = open('cryptotrader/readme.md', 'w')
    f.write(markdown)
    f.close()


async def on_ticker(msg):
    async with LOCK:
        decoded_msg = await websocket.process_message(msg[0])
        await trader.update_ticker(decoded_msg)
        await trade()


async def on_candle(msg):
    async with LOCK:
        decoded_msg = await websocket.process_message(msg[0])
        await trader.update_candles(decoded_msg)
        await trade()


async def main():
    global action, trades, market, trader, usd_wallet, crypto_wallet
    usd_wallet = 147.4539334
    crypto_wallet = 0
    market = 'BTC-USD'
    interval = CandleInterval(timedelta(hours=1))

    trader = Cryptotrader(market=market, strategy=BbandsStrategy(proximity=0.25, stddevs=2), fee=0.0035,
                          interval=timedelta(hours=1))
    trader.refresh()
    trades = trader.read_csv('trades.csv')
    action = trader.get_action(trades)

    await websocket.connect()
    await websocket.authenticate(os.environ.get("BITTREX_API_KEY"), os.environ.get("BITTREX_API_SECRET"))
    #await websocket.subscribe("candle_" + "BTC-USD_MINUTE_1", on_candle)
    await websocket.subscribe("candle_" + market + "_" + interval.name, on_candle)
    await websocket.subscribe("ticker_" + market, on_ticker)
    #if trending up, buy near middle, sell near upper
    #if tending down buy near lower, sell near middle
    # 'near' is 5% of the difference between either upper/middle or middle/lower
    forever = asyncio.Event()
    await forever.wait()


async def trade():
    global action, usd_wallet, crypto_wallet, trader, trades, active_session
    session_start = datetime.utcnow()
    active_session = True
    ticker = trader.get_ticker()
    action = trader.get_action(trades)
    plan = trader.eval()
    now = datetime.now()
    os.system('clear')
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
        price = round(proceeds / fill_quantity, 8)
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
        price = round(proceeds / fill_quantity, 8)
        trade = {
            'timestamp': datetime.strptime(order['closedAt'], '%Y-%m-%dT%H:%M:%S.%fZ'),
            'action': action,
            'price': price,
            'amount': fill_quantity,
            'fee': fee
        }
        print(trade)
        trades.append(trade)
        usd_wallet = proceeds - fee
        crypto_wallet = 0
        action = 'BUY'
    markdown = trader.generate_markdown(trades, initial_wallet, usd_wallet, crypto_wallet)
    write_markdown(markdown)
    new_trades = [d for d in trades if d['timestamp'] > session_start]
    if len(new_trades) > 0:
        trader.write_csv(new_trades, 'trades.csv', append=True)
    active_session = False


if __name__ == "__main__":
    asyncio.run(main())


