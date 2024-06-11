from binance import Client

api_key = "p5vVNIp8k9Kc4zoQb8dQFnlJPB8G12Tjs27BZz0NwwIV7s1QTJKoFTsUzH2H9v6O"
api_secret = "UQaxxDrfraKtuRbophOMwS9nvMNjTnuCuxYaJPbPldKLJrFn5Uo9QKEewE73ZCCs"

client = Client(api_key, api_secret)
# :return: list of OHLCV values (Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore)
# pastData = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_15MINUTE, limit=1)
# #
# print(pastData)

price = client.get_ticker(symbol="ETHUSDT")
print(price)
