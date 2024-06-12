import asyncio
import json

from binance import Client
from datetime import datetime
# credentials
api_key = "p5vVNIp8k9Kc4zoQb8dQFnlJPB8G12Tjs27BZz0NwwIV7s1QTJKoFTsUzH2H9v6O"
api_secret = "UQaxxDrfraKtuRbophOMwS9nvMNjTnuCuxYaJPbPldKLJrFn5Uo9QKEewE73ZCCs"

client = Client(api_key, api_secret)
# :return: list of OHLCV values (Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore)
# pastData = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_15MINUTE, limit=1)
# #
# print(pastData)

# price = client.get_ticker(symbol="ETHUSDT")
# print(price)
with open('environment.json', 'r') as f:
    # Load the data into a dictionary
    environment_data = json.load(f)
trading_pair_dict = environment_data['TRADING_PAIR_DICT']
trading_pairs = list(trading_pair_dict.keys())


async def getPrice(client, symbol):
    """
        Function to get the current market data for a given symbol.

        Args:
            client (dwx_client): The dwx_client instance.
            symbol (str): The symbol to get the market data for.

        Returns:
            dict: The market data for the given symbol.
        """

    result = client.get_orderbook_ticker(symbol=symbol)
    if result:
        result['date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        result['bid'] = float(result['bidPrice'])
        result['ask'] = float(result['askPrice'])
        return result
    else:
        return None

async def main():
    coroutines = [getPrice(client, symbol) for
                  symbol in
                  trading_pairs]
    results = await asyncio.gather(*coroutines)
    symbolPrices = dict(zip(trading_pairs, results))
    print(symbolPrices["ETHUSDT"]["ask"], symbolPrices["ETHUSDT"]["bid"], symbolPrices["ETHUSDT"]["date"])



if __name__ == "__main__":
    asyncio.run(main())