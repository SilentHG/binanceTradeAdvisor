import asyncio
import json
import os
import time
import traceback
from datetime import timedelta, datetime

import pytz
from binance import Client

import pyTraderClientWrapper as pWX

# Open the JSON file
with open('environment.json', 'r') as f:
    # Load the data into a dictionary
    environment_data = json.load(f)

trade_broker_name = environment_data['TRADING_BROKER_NAME'] or 'FTMO'
# Define a list of trading pairs
trading_pair_dict = environment_data['TRADING_PAIR_DICT']

pastCanldeCount = int(environment_data['PAST_CANDLE_COUNT']) or 35
thresholdPercent = float(environment_data['THRESHOLD_PERCENT']) or 0.05
CANDLE_PERIOD = environment_data['CANDLE_PERIOD'] or '15m'
TRADE_ENTRY_SECOND = int(environment_data['TRADE_ENTRY_SECOND']) or 5

if CANDLE_PERIOD == "15m":

    valid_intervals = [(890 + TRADE_ENTRY_SECOND, 890 + TRADE_ENTRY_SECOND + 1),
                       (1790 + TRADE_ENTRY_SECOND, 1790 + TRADE_ENTRY_SECOND + 1),
                       (2690 + TRADE_ENTRY_SECOND, 2690 + TRADE_ENTRY_SECOND + 1),
                       (3590 + TRADE_ENTRY_SECOND, 3590 + TRADE_ENTRY_SECOND + 1)]


    valid_calculation_intervals = [(870, 875), (1770, 1775), (2670, 2675), (3570, 3575)]
    valid_trailingstoploss_updating_intervals = [
        (910, 915),  # 15 minutes 10 seconds to 15 minutes 15 seconds
        (1810, 1815),  # 30 minutes 10 seconds to 30 minutes 15 seconds
        (2710, 2715),  # 45 minutes 10 seconds to 45 minutes 15 seconds
        (10, 15)  # 0 minutes 10 seconds to 0 minutes 15 seconds
    ]

elif CANDLE_PERIOD == "5m":
    valid_intervals = [
        (290 + TRADE_ENTRY_SECOND, 290 + TRADE_ENTRY_SECOND + 1),  # 5 minutes
        (590 + TRADE_ENTRY_SECOND, 590 + TRADE_ENTRY_SECOND + 1),  # 10 minutes
        (890 + TRADE_ENTRY_SECOND, 890 + TRADE_ENTRY_SECOND + 1),  # 15 minutes
        (1190 + TRADE_ENTRY_SECOND, 1190 + TRADE_ENTRY_SECOND + 1),  # 20 minutes
        (1490 + TRADE_ENTRY_SECOND, 1490 + TRADE_ENTRY_SECOND + 1),  # 25 minutes
        (1790 + TRADE_ENTRY_SECOND, 1790 + TRADE_ENTRY_SECOND + 1),  # 30 minutes
        (2090 + TRADE_ENTRY_SECOND, 2090 + TRADE_ENTRY_SECOND + 1),  # 35 minutes
        (2390 + TRADE_ENTRY_SECOND, 2390 + TRADE_ENTRY_SECOND + 1),  # 40 minutes
        (2690 + TRADE_ENTRY_SECOND, 2690 + TRADE_ENTRY_SECOND + 1),  # 45 minutes
        (2990 + TRADE_ENTRY_SECOND, 2990 + TRADE_ENTRY_SECOND + 1),  # 50 minutes
        (3290 + TRADE_ENTRY_SECOND, 3290 + TRADE_ENTRY_SECOND + 1),  # 55 minutes
        (50 + TRADE_ENTRY_SECOND, 50 + TRADE_ENTRY_SECOND + 1)  # 0 minutes
    ]

    valid_calculation_intervals = [
        (270, 275),  # 5 minutes
        (570, 575),  # 10 minutes
        (870, 875),  # 15 minutes
        (1170, 1175),  # 20 minutes
        (1470, 1475),  # 25 minutes
        (1770, 1775),  # 30 minutes
        (2070, 2075),  # 35 minutes
        (2370, 2375),  # 40 minutes
        (2670, 2675),  # 45 minutes
        (2970, 2975),  # 50 minutes
        (3270, 3275),  # 55 minutes
        (30, 35)  # 0 minutes
    ]

    valid_trailingstoploss_updating_intervals = [
        (310, 315),  # 5 minutes 10 seconds to 5 minutes 15 seconds
        (610, 615),  # 10 minutes 10 seconds to 10 minutes 15 seconds
        (910, 915),  # 15 minutes 10 seconds to 15 minutes 15 seconds
        (1210, 1215),  # 20 minutes 10 seconds to 20 minutes 15 seconds
        (1510, 1515),  # 25 minutes 10 seconds to 25 minutes 15 seconds
        (1810, 1815),  # 30 minutes 10 seconds to 30 minutes 15 seconds
        (2110, 2115),  # 35 minutes 10 seconds to 35 minutes 15 seconds
        (2410, 2415),  # 40 minutes 10 seconds to 40 minutes 15 seconds
        (2710, 2715),  # 45 minutes 10 seconds to 45 minutes 15 seconds
        (3010, 3015),  # 50 minutes 10 seconds to 50 minutes 15 seconds
        (3310, 3315),  # 55 minutes 10 seconds to 55 minutes 15 seconds
        (10, 15)  # 0 minutes 10 seconds to 0 minutes 15 seconds
    ]

BUY = 'buy'
SELL = 'sell'
PAST_DATA_FOR_TRAILING_STOP_LOSS = int(environment_data['PAST_DATA_FOR_TRAILING_STOP_LOSS']) or 50
BOT_TIME_START = environment_data['BOT_TIME_START'] or '00:00:00'
BOT_TIME_END = environment_data['BOT_TIME_END'] or '23:59:59'
TRADING_TIME_START = environment_data['TRADING_TIME_START'] or '00:00:00'
TRADING_TIME_END = environment_data['TRADING_TIME_END'] or '23:59:59'
BOT_STATUS = environment_data['BOT_STATUS'] or 'ON'
TIMEFRAME_1M = '1m'
TREND_UP_STRATEGY = environment_data['TREND_UP_STRATEGY'] or 'ON'
ORDER_COMMENT = environment_data['ORDER_COMMENT'] or 'Original Script'
FRIDAY_CLOSE = environment_data['FRIDAY_CLOSE'] or 'ON'
FRIDAY_CLOSE_TIME = environment_data['FRIDAY_CLOSE_TIME'] or '23:59:59'
DAILY_CLOSE = environment_data['DAILY_CLOSE'] or 'ON'
DAILY_CLOSE_TIME = environment_data['DAILY_CLOSE_TIME'] or '23:59:59'
NEWS_DICT_LIST = environment_data['NEWS_DICT'] or []
TREND_UP_INITIAL_CANDLES = int(environment_data['TREND_UP_INITIAL_CANDLES']) or 120
MIN_MAX_CONTROLLER = environment_data['MIN_MAX_CONTROLLER'] or 'TRADE'
THRESHOLD_CALCULATION_STRATEGY = environment_data['THRESHOLD_CALCULATION_STRATEGY'] or 'ON'
OUTSIDE_BAR_STRATEGY = environment_data['OUTSIDE_BAR_STRATEGY'] or 'ON'

if THRESHOLD_CALCULATION_STRATEGY == 'ON' and OUTSIDE_BAR_STRATEGY == 'ON':
    raise Exception("Both THRESHOLD_CALCULATION_STRATEGY and OUTSIDE_BAR_STRATEGY cannot be ON at the same time")

FRIDAY_CLOSE_DATETIME = datetime.strptime(FRIDAY_CLOSE_TIME, "%H:%M:%S").time()
DAILY_CLOSE_DATETIME = datetime.strptime(DAILY_CLOSE_TIME, "%H:%M:%S").time()

api_key = "p5vVNIp8k9Kc4zoQb8dQFnlJPB8G12Tjs27BZz0NwwIV7s1QTJKoFTsUzH2H9v6O"
api_secret = "UQaxxDrfraKtuRbophOMwS9nvMNjTnuCuxYaJPbPldKLJrFn5Uo9QKEewE73ZCCs"
TELEGRAM_CHAT_ID = "-1002217857669"


def get_universal_pair(symbol):
    return trading_pair_dict[symbol][trade_broker_name]


def log_general_error(message):
    with open('error_log.txt', 'a') as f:
        f.write(f'{message} | {str(pWX.get_trade_account_time())}\n')


def log_error(e, message):
    with open('error_log.txt', 'a') as f:
        f.write(f'{message} | {str(e)} | Line: {traceback.format_exc()} | {str(pWX.get_trade_account_time())}\n')


async def GetPastCandleData(client, pair, count):
    try:
        pastData = await pWX.get15MinHistoricalData(client, pair, pWX.CANDLE_PERIOD, True, count)
        return pastData
    except Exception as e:
        print(f"Error fetching past data for {pair}: {e}")
        log_error(e, f"Error fetching past data for {pair}")
        return []


async def CalculateThresholds(pastData):
    prevCandle = pastData[-1] if len(pastData) >= 1 else None
    minPastData = min(candle['low'] for candle in pastData)
    maxPastData = max(candle['high'] for candle in pastData)
    diffPastData = maxPastData - minPastData

    closeMarginThreshold = diffPastData * thresholdPercent
    sellThreshold = prevCandle['low'] - closeMarginThreshold if prevCandle else None
    buyThreshold = prevCandle['high'] + closeMarginThreshold if prevCandle else None

    return {
        'minPastData': minPastData,
        'maxPastData': maxPastData,
        'closeMarginThreshold': closeMarginThreshold,
        'sellThreshold': sellThreshold,
        'buyThreshold': buyThreshold
    }


async def CreateSellSignal(pair, price, sellThreshold, price_time, current_system_time):
    try:
        print(
            f"Pair: {pair} - Price: {str(price)} - Sell Threshold: {str(sellThreshold)} - Time: {str(price_time)}"
            f" - Current System Time (UTC+2): {str(current_system_time)}")
        with open("sell_signal.txt", "a") as f:
            f.write(
                f"Pair: {pair} - Price: {str(price)} - Sell Threshold: {str(sellThreshold)} - Time: {str(price_time)}"
                f" - Current System Time (UTC+2): {str(current_system_time)}\n")

    except Exception as e:
        print(f"Error creating sell signal for {pair}: {e}")
        log_error(e, f"Error creating sell signal for {pair}")


async def CreateBuySignal(pair, price, buyThreshold, price_time, current_system_time):
    try:
        print(
            f"Pair: {pair} - Price: {str(price)} - Buy Threshold: {str(buyThreshold)} - Time: {str(price_time)}"
            f" - Current System Time (UTC+2): {str(current_system_time)}")
        with open("buy_signal.txt", "a") as f:
            f.write(
                f"Pair: {pair} - Price: {str(price)} - Buy Threshold: {str(buyThreshold)} - Time: {str(price_time)}"
                f" - Current System Time (UTC+2): {str(current_system_time)}\n")

    except Exception as e:
        print(f"Error creating buy signal for {pair}: {e}")
        log_error(e, f"Error creating buy signal for {pair}")


async def UpdateCalculations(account, pair):
    try:
        pastData = await GetPastCandleData(account, get_universal_pair(pair), pastCanldeCount)

        thresholds = await CalculateThresholds(pastData)

        # Update calculations in a JSON file
        calculations_data = {
            'pair': pair,
            'time': str(pWX.get_data_account_time()),
            'thresholds': thresholds,
            'prev_candle': str(pastData[-1])
        }

        # Read existing data from calculations_log.json
        # check if the file exists
        if not os.path.isfile("calculations_log.json"):
            with open("calculations_log.json", "w") as f:
                json.dump(calculations_data, f)
                f.write("\n")
            return

        with open("calculations_log.json", "r") as f:
            existing_data = [json.loads(line) for line in f if line.strip()]

        # Remove existing data for the current pair
        existing_data = [data for data in existing_data if data.get('pair') != pair]

        # Add the new data for the current pair
        existing_data.append(calculations_data)

        if len(existing_data) < 1:
            with open("calculations_log.json", "w") as f:
                json.dump(calculations_data, f)
                f.write("\n")

        else:
            with open("calculations_log.json", "w") as f:
                for data in existing_data:
                    json.dump(data, f)
                    f.write("\n")

        print(f"Updated calculations for {pair} at {str(pWX.get_data_account_time())}")

    except Exception as e:
        print(f"Error updating calculations for {pair}: {e}")
        log_error(e, f"Error updating calculations for {pair}")


async def GetStoredCalculations(pair):
    try:
        with open("calculations_log.json", "r") as f:
            calculations_data = [json.loads(line) for line in f if line.strip()]
            for data in reversed(calculations_data):
                if data['pair'] == pair:
                    return data
            return None
    except Exception as e:
        print(f"Error fetching stored calculations for {pair}: {e}")
        log_error(e, f"Error fetching stored calculations for {pair}")
        return None


async def UpdateStopLossofTrade(tradeAccount, current_datetime, dataAccount):
    try:
        # check if the file exists
        if not os.path.isfile("trades.json"):
            return

        trades_data = pWX.loadTradeData()
        active_trades_data = pWX.loadActiveTradeData()

        positions = await pWX.getActivePositions(tradeAccount)

        if positions is not None:
            # check if the position['id'] is in active_trades_data['trade']['positionId']
            active_trades_data = [active_trade_data for active_trade_data in active_trades_data if
                                  'positionId' in active_trade_data['trade'] and
                                  any(position['positionId'] == active_trade_data['trade']['positionId'] for position in
                                      positions
                                      if position is not None and 'positionId' in position)]

        processed_trades = []
        # TODO: make this loop async
        for trade_data in trades_data:
            try:
                if 'positionId' not in trade_data['trade']:
                    processed_trades.append(trade_data)
                    continue

                pastData = await pWX.get15MinHistoricalData(tradeAccount, trade_data['symbol'], pWX.CANDLE_PERIOD,
                                                            False, 1)

                closePrice = pastData[-1]['close']
                highestPrice = pastData[-1]['high']
                lowestPrice = pastData[-1]['low']
                valid = True
                if valid:
                    stopLoss = closePrice - trade_data['stopLossSize'] if trade_data[
                                                                              'actionType'] == BUY else closePrice + \
                                                                                                        trade_data[
                                                                                                            'stopLossSize'] + \
                                                                                                        trade_data[
                                                                                                            'spread']
                    stopLoss = round(stopLoss, trade_data['decimalPlaces'])
                    await pWX.updatePosition(tradeAccount, trade_data['trade']['positionId'], stopLoss,
                                             trade_data['symbol'], trade_data['stopLoss'])
                    print(f"Updated stop loss for {trade_data['symbol']} at {str(pWX.get_trade_account_time())}")
                    # log position modification in position_modification_log.txt
                    with open('position_modification_log.txt', 'a') as f:
                        f.write(
                            f"Position {trade_data['trade']['positionId']} Modified for Symbol: {trade_data['symbol']}"
                            f"|"
                            f"Time: {str(pWX.get_trade_account_time())} | Previous Stop Loss: {trade_data['stopLoss']} | "
                            f"New Stop Loss: {stopLoss} | Past 1 Candle: {str(pastData)}  \n")
                    # remove the trade from the trades.json file
                    processed_trades.append(trade_data)

                    for active_trade_data in active_trades_data:
                        if active_trade_data['trade']['positionId'] == trade_data['trade']['positionId']:
                            active_trade_data['initialStopLoss'] = stopLoss
                            active_trade_data['currentStopLoss'] = stopLoss
                            active_trade_data['highestPrice'] = highestPrice
                            active_trade_data['lowestPrice'] = lowestPrice
                            active_trade_data['didTrendChange'] = False
                            break

                else:
                    #         log in position_modification_log.txt
                    with open('position_modification_log.txt', 'a') as f:
                        f.write(
                            f"Position {trade_data['trade']['positionId']} Not Modified for Symbol: {trade_data['symbol']} | "
                            f"Time: {str(pWX.get_trade_account_time())} | Due to not getting the accurate past data\n")


            except Exception as ex:
                print(f"Error updating stop loss for {trade_data['trade']['positionId']} {trade_data['symbol']}", ex)
                log_error(ex,
                          f"Error updating stop loss for {trade_data['trade']['positionId']} {trade_data['symbol']}")
        with open("trades.json", "w") as file:
            unprocessed_trades = [trade_data for trade_data in trades_data if trade_data not in processed_trades]
            json.dump(unprocessed_trades, file, indent=2)

        with open("active_trades.json", "w") as file:
            json.dump(active_trades_data, file, indent=2)


    except Exception as e:
        print(f"Error updating stop loss")
        log_error(e, f"Error updating stop loss")


def findNewLowCandle(pastData, currentCandle):
    try:
        # Start from the current candle and go in reverse
        newLow = currentCandle['low']
        referenceCandle = currentCandle
        reversePastData = pastData[::-1]
        for i in range(len(reversePastData) - 1):
            data_time = datetime.strptime(reversePastData[i]['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
            current_time = datetime.strptime(currentCandle['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
            if data_time <= current_time:
                if reversePastData[i]['high'] < reversePastData[i + 1]['high']:
                    referenceCandle = reversePastData[i]
                    newLow = referenceCandle['low']
                    for data in pastData:
                        data_time = datetime.strptime(data['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
                        reference_time = datetime.strptime(referenceCandle['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                            tzinfo=pytz.utc)
                        if reference_time <= data_time <= current_time and data['low'] < newLow:
                            newLow = data['low']
                    return newLow, referenceCandle

        return newLow, referenceCandle
    except Exception as e:
        print(f"Error finding lowest price between candles: {e}")
        log_error(e, f"Error finding lowest price between candles")


def findNewHighCandle(pastData, currentCandle):
    try:
        # Start from the current candle and go in reverse
        newHigh = currentCandle['high']
        referenceCandle = currentCandle
        reversePastData = pastData[::-1]
        for i in range(len(reversePastData) - 1):
            data_time = datetime.strptime(reversePastData[i]['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
            current_time = datetime.strptime(currentCandle['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
            if data_time <= current_time:
                if reversePastData[i]['low'] > reversePastData[i + 1]['low']:
                    referenceCandle = reversePastData[i]
                    newHigh = referenceCandle['high']
                    for data in pastData:
                        data_time = datetime.strptime(data['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
                        reference_time = datetime.strptime(referenceCandle['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                            tzinfo=pytz.utc)
                        if reference_time <= data_time <= current_time and data['high'] > newHigh:
                            newHigh = data['high']
                    return newHigh, referenceCandle

        return newHigh, referenceCandle
    except Exception as e:
        print(f"Error finding highest price between candles: {e}")
        log_error(e, f"Error finding highest price between candles")


def findLowestBetweenCandles(allCandles, startingCandle, endingCandle):
    try:
        lowestPrice = startingCandle['low']
        for candle in allCandles:
            if startingCandle['time'] < candle['time'] <= endingCandle['time']:
                if candle['low'] < lowestPrice:
                    lowestPrice = candle['low']
        return lowestPrice
    except Exception as e:
        print(f"Error finding lowest price between candles: {e}")
        log_error(e, f"Error finding lowest price between candles")


def findHighestBetweenCandles(pastData, startingCandle, endingCandle):
    try:
        highestPrice = startingCandle['high']
        for candle in pastData:
            if candle['time'] > startingCandle['time'] and candle['time'] <= endingCandle['time']:
                if candle['high'] > highestPrice:
                    highestPrice = candle['high']
        return highestPrice
    except Exception as e:
        print(f"Error finding highest price between candles: {e}")
        log_error(e, f"Error finding highest price between candles")


def log_stoploss_trailing_update(prefix, active_trade_data, lastCandle):
    with open("trailing_stoploss_debug.txt", "a") as f:
        f.write(
            f"{prefix} | Position: {active_trade_data['trade']['positionId']} | {active_trade_data['symbol']} | Current Stop Loss: {active_trade_data['currentStopLoss']} | Highest Price: {active_trade_data['highestPrice']} | "
            f"Lowest Price: {active_trade_data['lowestPrice']} | Did Trend Change: {active_trade_data['didTrendChange']} |"
            f"Last Candle: {str(lastCandle)} |"
            f" Trend Change Candle: {active_trade_data['trendChangeCandle'] if 'trendChangeCandle' in active_trade_data else None}"
            f"System Time: {str(pWX.get_trade_account_time())}\n")


def log_one_minute_candle_update(prefix, active_trade_data, candleHighest, candleLowest):
    with open("one_minute_candle_debug.txt", "a") as f:
        f.write(
            f"{prefix} | Position: {active_trade_data['trade']['positionId']} | {active_trade_data['symbol']} | Current Stop Loss: {active_trade_data['currentStopLoss']} | Highest Price: {active_trade_data['highestPrice']} | "
            f"Lowest Price: {active_trade_data['lowestPrice']} | Did Trend Change: {active_trade_data['didTrendChange']} |"
            f"Past 1 Min Candle Highest: {str(candleHighest)} | Past 1 Min Candle Lowest: {str(candleLowest)} |"
            f" Trend Change Candle: {active_trade_data['trendChangeCandle'] if 'trendChangeCandle' in active_trade_data else None}"
            f"System Time: {str(pWX.get_trade_account_time())}\n")


def getDataAccountPair(pair):
    for key in trading_pair_dict:
        if trading_pair_dict[key][trade_broker_name] == pair:
            return key

async def UpdateTrailingStopLoss(dataAccountClient, tradeAccount, current_time, exception=False):
    try:

        if TREND_UP_STRATEGY == "ON":
            try:
                # get all keys of the trading_pair_dict
                trading_pairs = list(trading_pair_dict.keys())
                trading_account_pairs = [trading_pair_dict[tp][trade_broker_name] for tp in trading_pairs]
                await asyncio.gather(
                    *[TrendUpCandleLiveUpdate(dataAccountClient, symbol) for symbol in trading_account_pairs])
            except Exception as e:
                print(f"Error updating trend up candle: {e}")
                log_error(e, f"Error updating trend up candle")
        # check if the file exists
        if not os.path.isfile("active_trades.json"):
            return

        active_trades_data = pWX.loadActiveTradeData()

        trading_pairs = []
        trading_symbols = list(trading_pair_dict.keys())
        for tps in trading_symbols:
            trading_pairs.append(trading_pair_dict[tps][trade_broker_name])

        coroutines = [
            pWX.get15MinHistoricalData(tradeAccount, symbol, pWX.CANDLE_PERIOD, False, PAST_DATA_FOR_TRAILING_STOP_LOSS)
            for
            symbol in
            trading_pairs]
        results = await asyncio.gather(*coroutines)
        symbolPastData = dict(zip(trading_pairs, results))

        for active_trade_data in active_trades_data:
            try:
                if 'positionId' not in active_trade_data['trade']:
                    active_trades_data.remove(active_trade_data)
                    continue
                pastData = symbolPastData[active_trade_data['symbol']]
                highestPrice = active_trade_data['highestPrice']
                currentStopLoss = active_trade_data['currentStopLoss']
                didTrendChange = active_trade_data['didTrendChange']
                positionId = active_trade_data['trade']['positionId']
                symbol = active_trade_data['symbol']
                lowestPrice = active_trade_data['lowestPrice']


                isOneMinuteProcessedCandle = False

                if 'incompleteCandleStartTime' in active_trade_data:
                    incompleteCandleStartTime = datetime.strptime(active_trade_data['incompleteCandleStartTime'],
                                                                  "%Y-%m-%d %H:%M:%S%z").replace(
                        tzinfo=pytz.utc)

                    currentCandleTime = datetime.strptime(pastData[-1]['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                        tzinfo=pytz.utc)

                    mod_minute = 15 if pWX.CANDLE_PERIOD == "15m" else 5

                    past_minutes = currentCandleTime.minute % mod_minute
                    completedCandleTime = currentCandleTime - timedelta(minutes=past_minutes,
                                                                        seconds=currentCandleTime.second,
                                                                        microseconds=currentCandleTime.microsecond)

                    if incompleteCandleStartTime == completedCandleTime:
                        isOneMinuteProcessedCandle = True

                log_stoploss_trailing_update("Before", active_trade_data, pastData[-1])

                if active_trade_data['actionType'] == BUY:
                    if pastData[-1]['high'] > highestPrice:
                        highestPrice = pastData[-1]['high']
                        if didTrendChange is False:
                            active_trade_data['highestPrice'] = highestPrice
                        else:
                            validTrade = True
                            didTrendChange = False
                            errorCode = "A"
                            # Update stop loss
                            newStopLoss = findLowestBetweenCandles(pastData, active_trade_data['trendChangeCandle'],
                                                                   pastData[-1])
                            newStopLoss = newStopLoss - active_trade_data[
                                'stopLossSize'] * pWX.TRAILING_STOP_LOSS_SIZE_MULTIPLIER
                            newStopLoss = round(newStopLoss, active_trade_data['decimalPlaces'])
                            if newStopLoss < active_trade_data['initialStopLoss']:
                                validTrade = False

                            if newStopLoss == active_trade_data['currentStopLoss']:
                                errorCode = "B"
                                validTrade = False

                            active_trade_data['didTrendChange'] = didTrendChange
                            active_trade_data['highestPrice'] = highestPrice
                            # remove trend change candle
                            del active_trade_data['trendChangeCandle']

                            if validTrade:
                                active_trade_data['currentStopLoss'] = newStopLoss
                                response = await pWX.updatePosition(tradeAccount, positionId, newStopLoss, symbol, currentStopLoss)
                                if not response:
                                    active_trades_data.remove(active_trade_data)
                                    # log in unexpected_error_log.txt
                                    with open('position_close_log.txt', 'a') as f:
                                        f.write(
                                            f"Position {positionId} for Symbol: {symbol} | "
                                            f"Time: {str(pWX.get_trade_account_time())} | Error: \n")

                                else:
                                    # log position modification in buy_high_breakout_log.txt
                                    with open('buy_high_breakout_log.txt', 'a') as f:
                                        f.write(
                                            f"Position {positionId} Modified for Symbol: {symbol} | "
                                            f"Time: {str(pWX.get_trade_account_time())} | Previous Stop Loss: {currentStopLoss} | "
                                            f"New Stop Loss: {newStopLoss}\n| response: {response}\n")
                            else:
                                # log position modification in buy_high_breakout_log.txt
                                if errorCode == "A":
                                    with open('buy_high_breakout_log.txt', 'a') as f:
                                        f.write(
                                            f"Position {positionId} Not Modified for Symbol: {symbol} | "
                                            f"Time: {str(pWX.get_trade_account_time())} "
                                            f"| Due to Stop Loss: {newStopLoss} being less than Initial Stop Loss: {active_trade_data['initialStopLoss']}\n")
                                elif errorCode == "B":
                                    with open('buy_high_breakout_log.txt', 'a') as f:
                                        f.write(
                                            f"Position {positionId} Not Modified for Symbol: {symbol} | "
                                            f"Time: {str(pWX.get_trade_account_time())} "
                                            f"| Due to Stop Loss: {newStopLoss} being equal to Current Stop Loss: {active_trade_data['currentStopLoss']}\n")

                    elif ('trendChangeCandle' in active_trade_data and
                          pastData[-1]['high'] < pastData[-2]['high']):
                        didTrendChange = True
                        active_trade_data['didTrendChange'] = didTrendChange
                        active_trade_data['trendChangeCandle'] = pastData[-1]

                    elif 'trendChangeCandle' not in active_trade_data and pastData[-1]['high'] < highestPrice:
                        if isOneMinuteProcessedCandle is False:
                            didTrendChange = True
                            active_trade_data['didTrendChange'] = didTrendChange
                            active_trade_data['trendChangeCandle'] = pastData[-1]
                        else:
                            del active_trade_data['incompleteCandleStartTime']
                else:
                    if pastData[-1]['low'] < lowestPrice:
                        lowestPrice = pastData[-1]['low']
                        if didTrendChange is False:
                            active_trade_data['lowestPrice'] = lowestPrice
                        else:
                            validTrade = True
                            didTrendChange = False
                            errorCode = "A"
                            # Update stop loss
                            newStopLoss = findHighestBetweenCandles(pastData, active_trade_data['trendChangeCandle'],
                                                                    pastData[-1])
                            newStopLoss = newStopLoss + active_trade_data[
                                'stopLossSize'] * pWX.TRAILING_STOP_LOSS_SIZE_MULTIPLIER + active_trade_data[
                                              'spread']
                            newStopLoss = round(newStopLoss, active_trade_data['decimalPlaces'])
                            if newStopLoss > active_trade_data['initialStopLoss']:
                                validTrade = False

                            if newStopLoss == active_trade_data['currentStopLoss']:
                                errorCode = "B"
                                validTrade = False

                            active_trade_data['didTrendChange'] = didTrendChange
                            active_trade_data['lowestPrice'] = lowestPrice
                            # remove trend change candle
                            del active_trade_data['trendChangeCandle']

                            if validTrade:
                                active_trade_data['currentStopLoss'] = newStopLoss
                                response = await pWX.updatePosition(tradeAccount, positionId, newStopLoss, symbol, currentStopLoss)
                                if not response:
                                    active_trades_data.remove(active_trade_data)
                                    # log in unexpected_error_log.txt
                                    with open('position_close_log.txt', 'a') as f:
                                        f.write(
                                            f"Position {positionId} for Symbol: {symbol} | "
                                            f"Time: {str(pWX.get_trade_account_time())} | Error: \n")
                                else:
                                    # log position modification in sell_low_breakout_log.txt
                                    with open('sell_low_breakout_log.txt', 'a') as f:
                                        f.write(
                                            f"Position {positionId} Modified for Symbol: {symbol} | "
                                            f"Time: {str(pWX.get_trade_account_time())} | Previous Stop Loss: {currentStopLoss} | "
                                            f"New Stop Loss: {newStopLoss}\n| response: {response}\n")
                            else:
                                # log position modification in sell_low_breakout_log.txt
                                with open('sell_low_breakout_log.txt', 'a') as f:
                                    if errorCode == "A":
                                        f.write(
                                            f"Position {positionId} Not Modified for Symbol: {symbol} | "
                                            f"Time: {str(pWX.get_trade_account_time())} "
                                            f"| Due to Stop Loss: {newStopLoss} being greater than Initial Stop Loss: {active_trade_data['initialStopLoss']}\n")
                                    elif errorCode == "B":
                                        f.write(
                                            f"Position {positionId} Not Modified for Symbol: {symbol} | "
                                            f"Time: {str(pWX.get_trade_account_time())} "
                                            f"| Due to Stop Loss: {newStopLoss} being equal to Current Stop Loss: {active_trade_data['currentStopLoss']}\n")

                    elif ('trendChangeCandle' in active_trade_data and
                          pastData[-1]['low'] > pastData[-2]['low']):
                        didTrendChange = True
                        active_trade_data['didTrendChange'] = didTrendChange
                        active_trade_data['trendChangeCandle'] = pastData[-1]

                    elif 'trendChangeCandle' not in active_trade_data and pastData[-1]['low'] > lowestPrice:
                        if isOneMinuteProcessedCandle is False:
                            didTrendChange = True
                            active_trade_data['didTrendChange'] = didTrendChange
                            active_trade_data['trendChangeCandle'] = pastData[-1]
                        else:
                            del active_trade_data['incompleteCandleStartTime']

                # create a log file for debugging
                log_stoploss_trailing_update("After", active_trade_data, pastData[-1])

            except Exception as ex:
                log_error(ex,
                          f"Error updating trailing stop loss for {active_trade_data['trade']['positionId']} {active_trade_data['symbol']}")
                print(
                    f"Error updating trailing stop loss for {active_trade_data['trade']['positionId']} {active_trade_data['symbol']}: {ex}")

        with open("active_trades.json", "w") as file:
            json.dump(active_trades_data, file, indent=2)


    except Exception as e:
        print(f"Error updating trailing stop loss: {e}")
        log_error(e, f"Error updating trailing stop loss")


async def UpdateOneMinuteTrailingStopLoss(tradeAccount, current_datetime):
    #     This method is for checking if the minute candle is above the highest price for buy trades and below the lowest price for sell trades
    #     based on the minute of the time, get as many past 1 minute candles, and get lowest points and high point and see if High Breakout or Low Breakout

    try:
        # check if the file exists
        if not os.path.isfile("active_trades.json"):
            return

        active_trades_data = pWX.loadActiveTradeData()
        trading_pairs = []
        trading_symbols = list(trading_pair_dict.keys())
        for tps in trading_symbols:
            trading_pairs.append(trading_pair_dict[tps][trade_broker_name])


        mod_minute = 15 if pWX.CANDLE_PERIOD == "15m" else 5

        time_mod = current_datetime.minute % mod_minute
        # calculate the incomplete {mod_minute} minute candle start time
        incompleteCandleStartTime = current_datetime - timedelta(minutes=time_mod,
                                                                 seconds=current_datetime.second,
                                                                 microseconds=current_datetime.microsecond)
        incompleteCandleStartTime = str(incompleteCandleStartTime)
        symbolPastData = {}
        coroutines = [
            pWX.get1MinHistoricalData(tradeAccount, symbol, TIMEFRAME_1M, False, time_mod) for symbol in
            trading_pairs]

        results = await asyncio.gather(*coroutines)
        symbolPastData = dict(zip(trading_pairs, results))

        symbolsPast15MinData = {}
        coroutines = [
            pWX.get15MinHistoricalData(tradeAccount, symbol, pWX.CANDLE_PERIOD, False, PAST_DATA_FOR_TRAILING_STOP_LOSS)
            for
            symbol in
            trading_pairs]

        results = await asyncio.gather(*coroutines)
        symbolsPast15MinData = dict(zip(trading_pairs, results))

        for active_trade_data in active_trades_data:
            try:
                if 'positionId' not in active_trade_data['trade']:
                    active_trades_data.remove(active_trade_data)
                    continue
                pastData = symbolPastData[active_trade_data['symbol']]
                past15MinData = symbolsPast15MinData[active_trade_data['symbol']]
                highestPrice = active_trade_data['highestPrice']
                currentStopLoss = active_trade_data['currentStopLoss']
                didTrendChange = active_trade_data['didTrendChange']
                positionId = active_trade_data['trade']['positionId']
                symbol = active_trade_data['symbol']
                lowestPrice = active_trade_data['lowestPrice']

                #                get the highest point and lowest point
                candleHighestPrice = max(candle['high'] for candle in pastData)
                candleLowestPrice = min(candle['low'] for candle in pastData)

                log_one_minute_candle_update("Before", active_trade_data, candleHighestPrice, candleLowestPrice)

                if active_trade_data['actionType'] == BUY:
                    if candleHighestPrice > highestPrice and didTrendChange:
                        validTrade = True
                        didTrendChange = False
                        errorCode = "A"
                        # Get the lowest point between the trend change candle and the current candle
                        newStopLoss = findLowestBetweenCandles(past15MinData, active_trade_data['trendChangeCandle'],
                                                               past15MinData[-1])
                        if newStopLoss > candleLowestPrice:
                            newStopLoss = candleLowestPrice

                        newStopLoss = newStopLoss - active_trade_data[
                            'stopLossSize'] * pWX.TRAILING_STOP_LOSS_SIZE_MULTIPLIER
                        newStopLoss = round(newStopLoss, active_trade_data['decimalPlaces'])
                        if newStopLoss < active_trade_data['initialStopLoss']:
                            validTrade = False

                        if newStopLoss == active_trade_data['currentStopLoss']:
                            errorCode = "B"
                            validTrade = False

                        active_trade_data['didTrendChange'] = didTrendChange
                        active_trade_data['highestPrice'] = candleHighestPrice
                        active_trade_data['incompleteCandleStartTime'] = incompleteCandleStartTime
                        # remove trend change candle
                        del active_trade_data['trendChangeCandle']

                        if validTrade:
                            active_trade_data['currentStopLoss'] = newStopLoss
                            response = await pWX.updatePosition(tradeAccount, positionId, newStopLoss, symbol, currentStopLoss)
                            if not response:
                                active_trades_data.remove(active_trade_data)
                                # log in unexpected_error_log.txt
                                with open('position_close_log.txt', 'a') as f:
                                    f.write(
                                        f"Position {positionId} for Symbol: {symbol} | "
                                        f"Time: {str(pWX.get_trade_account_time())} | Error: \n")

                            else:
                                # log position modification in buy_high_breakout_log.txt
                                with open('buy_high_breakout_log_at_one_minute.txt', 'a') as f:
                                    f.write(
                                        f"Position {positionId} Modified for Symbol: {symbol} | "
                                        f"Time: {str(pWX.get_trade_account_time())} | Previous Stop Loss: {currentStopLoss} | "
                                        f"New Stop Loss: {newStopLoss}\n| response: {response}\n")

                        else:
                            # log position modification in buy_high_breakout_log.txt
                            if errorCode == "A":
                                with open('buy_high_breakout_log_at_one_minute.txt', 'a') as f:
                                    f.write(
                                        f"Position {positionId} Not Modified for Symbol: {symbol} | "
                                        f"Time: {str(pWX.get_trade_account_time())} "
                                        f"| Due to Stop Loss: {newStopLoss} being less than Initial Stop Loss: {active_trade_data['initialStopLoss']}\n")
                            elif errorCode == "B":
                                with open('buy_high_breakout_log_at_one_minute.txt', 'a') as f:
                                    f.write(
                                        f"Position {positionId} Not Modified for Symbol: {symbol} | "
                                        f"Time: {str(pWX.get_trade_account_time())} "
                                        f"| Due to Stop Loss: {newStopLoss} being equal to Current Stop Loss: {active_trade_data['currentStopLoss']}\n")

                else:
                    if candleLowestPrice < lowestPrice and didTrendChange:
                        validTrade = True
                        didTrendChange = False
                        errorCode = "A"
                        # Update stop loss
                        newStopLoss = findHighestBetweenCandles(past15MinData, active_trade_data['trendChangeCandle'],
                                                                past15MinData[-1])
                        if newStopLoss < candleHighestPrice:
                            newStopLoss = candleHighestPrice
                        newStopLoss = newStopLoss + active_trade_data[
                            'stopLossSize'] * pWX.TRAILING_STOP_LOSS_SIZE_MULTIPLIER + \
                                      active_trade_data[
                                          'spread']
                        newStopLoss = round(newStopLoss, active_trade_data['decimalPlaces'])
                        if newStopLoss > active_trade_data['initialStopLoss']:
                            validTrade = False

                        if newStopLoss == active_trade_data['currentStopLoss']:
                            errorCode = "B"
                            validTrade = False

                        active_trade_data['didTrendChange'] = didTrendChange
                        active_trade_data['lowestPrice'] = candleLowestPrice
                        active_trade_data['incompleteCandleStartTime'] = incompleteCandleStartTime
                        # remove trend change candle
                        del active_trade_data['trendChangeCandle']

                        if validTrade:
                            active_trade_data['currentStopLoss'] = newStopLoss
                            response = await pWX.updatePosition(tradeAccount, positionId, newStopLoss, symbol, currentStopLoss)
                            if not response:
                                active_trades_data.remove(active_trade_data)
                                # log in unexpected_error_log.txt
                                with open('position_close_log.txt', 'a') as f:
                                    f.write(
                                        f"Position {positionId} for Symbol: {symbol} | "
                                        f"Time: {str(pWX.get_trade_account_time())} | Error: \n")
                            else:
                                # log position modification in sell_low_breakout_log.txt
                                with open('sell_low_breakout_log_at_one_minute.txt', 'a') as f:
                                    f.write(
                                        f"Position {positionId} Modified for Symbol: {symbol} | "
                                        f"Time: {str(pWX.get_trade_account_time())} | Previous Stop Loss: {currentStopLoss} | "
                                        f"New Stop Loss: {newStopLoss}\n| response: {response}\n")
                        else:
                            # log position modification in sell_low_breakout_log.txt
                            if errorCode == "A":
                                with open('sell_low_breakout_log_at_one_minute.txt', 'a') as f:
                                    f.write(
                                        f"Position {positionId} Not Modified for Symbol: {symbol} | "
                                        f"Time: {str(pWX.get_trade_account_time())} "
                                        f"| Due to Stop Loss: {newStopLoss} being greater than Initial Stop Loss: {active_trade_data['initialStopLoss']}\n")
                            elif errorCode == "B":
                                with open('sell_low_breakout_log_at_one_minute.txt', 'a') as f:
                                    f.write(
                                        f"Position {positionId} Not Modified for Symbol: {symbol} | "
                                        f"Time: {str(pWX.get_trade_account_time())} "
                                        f"| Due to Stop Loss: {newStopLoss} being equal to Current Stop Loss: {active_trade_data['currentStopLoss']}\n")

                # create a log file for debugging
                log_one_minute_candle_update("After", active_trade_data, candleHighestPrice, candleLowestPrice)

            except Exception as ex:
                log_error(ex,
                          f"Error updating one minute trailing stop loss for {active_trade_data['trade']['positionId']} {active_trade_data['symbol']}")
                print(
                    f"Error updating one minute trailing stop loss for {active_trade_data['trade']['positionId']} {active_trade_data['symbol']}: {ex}")

        with open("active_trades.json", "w") as file:
            json.dump(active_trades_data, file, indent=2)

    except Exception as e:
        print(f"Error updating trailing stop loss: {e}")
        log_error(e, f"Error updating trailing stop loss")


def checkIfAllowedNumberOfTradesReached(pair, trading_broker_pair, actionType):
    # check if allowed number of sell trades is reached
    active_trades_data = pWX.loadActiveTradeData()
    active_sell_trades = [trade_data for trade_data in active_trades_data if
                          trade_data['actionType'] == actionType and trade_data[
                              'symbol'] == trading_broker_pair]

    if actionType == BUY:
        key = 'allowedNumberOfBuyTrades'
    else:
        key = 'allowedNumberOfSellTrades'

    if len(active_sell_trades) >= trading_pair_dict[pair][key]:
        # log in skip_signal_log.txt
        with open('skip_signal_log.txt', 'a') as f:
            f.write(
                f"Skipped {actionType} Signal for {trading_broker_pair} | "
                f"Time (UTC+2): {str(pWX.get_data_account_time())} | "
                f"Reason: Allowed Number of Trades reached\n")
        return True
    return False


async def checkIfOneDirectionTradeIsOn(pair, trading_broker_pair, actionTypeCheck):
    if trading_pair_dict[pair]['oneDirection'] == "ON":
        actionType = await pWX.get_active_trade_direction(trading_broker_pair)
        if actionType == actionTypeCheck:
            with open('skip_signal_log.txt', 'a') as f:
                f.write(
                    f"Skipped Buy Signal for {trading_broker_pair} | "
                    f"Time (UTC+2): {str(pWX.get_data_account_time())} | "
                    f"Reason: One Direction Trade is ON\n")
            return True
    return False


async def ProcessPair(account, tradeAccount, pair, dataAccount):
    trendUpData = None
    if TREND_UP_STRATEGY == "ON":
        trendUpData = await GetStoredTrendUpCalculations(get_universal_pair(pair))

        if trendUpData and trendUpData['isEntryCriteriaMet'] is False:
            return

    storedData = await GetStoredCalculations(pair)
    thresholds = storedData['thresholds'] if storedData else None
    prev_candle = storedData['prev_candle'] if storedData else None

    live_data = await pWX.getPrice(account, get_universal_pair(pair))
    trade_live_data = await pWX.getPrice(tradeAccount, get_universal_pair(pair))
    if 'bid' not in live_data:
        # log in error_log.txt
        with open('error_log.txt', 'a') as f:
            f.write(
                f'Error fetching live data for {pair} | Time: {str(pWX.get_data_account_time())} | Data: {str(live_data)}\n')
        return
    price = live_data['bid']
    price_time = live_data['date']

    current_system_time = pWX.get_data_account_time()
    with open("debuglog.txt", "a") as f:
        f.write("*********************************\n")
        f.write(f"Pair: {pair}\n")
        f.write(f"Price: {str(price)}\n")
        f.write(f"Price Time: {str(price_time)}\n")
        f.write(f"Current System Time (UTC+2): {str(current_system_time)}\n")
        f.write(f"Buy Threshold: {str(thresholds['buyThreshold'])}\n")
        f.write(f"Sell Threshold: {str(thresholds['sellThreshold'])}\n")
        f.write(f"Min Past Data: {str(thresholds['minPastData'])}\n")
        f.write(f"Max Past Data: {str(thresholds['maxPastData'])}\n")
        f.write(f"Close Margin Threshold: {str(thresholds['closeMarginThreshold'])}\n")
        f.write(f"Previous Candle: {str(prev_candle)}\n")
        f.write("*********************************\n")

    # recalculate spread
    current_spread = trade_live_data['ask'] - trade_live_data['bid']
    trading_pair_dict[pair]['spread'] = current_spread

    spread = trading_pair_dict[pair]['spread']
    contractSize = trading_pair_dict[pair]['contractSize']
    trading_broker_pair = get_universal_pair(pair)
    decimalPlaces = trading_pair_dict[pair]['decimalPlaces']

    if TREND_UP_STRATEGY == "ON":
        if THRESHOLD_CALCULATION_STRATEGY == "ON":
            if price < thresholds['sellThreshold'] and trendUpData['didTrendDownHappen']:
                # check if allowed number of sell trades is reached
                if checkIfAllowedNumberOfTradesReached(pair, trading_broker_pair, SELL):
                    return

                if await checkIfOneDirectionTradeIsOn(pair, trading_broker_pair, BUY):
                    return

                await CreateSellSignal(trading_broker_pair, price, thresholds['sellThreshold'], price_time,
                                       current_system_time)
                await pWX.doTradeScenario(tradeAccount,
                                          dataAccount,
                                          trading_broker_pair,
                                          SELL,
                                          contractSize,
                                          spread,
                                          ORDER_COMMENT,
                                          pastCanldeCount,
                                          decimalPlaces,
                                          )
            elif price > thresholds['buyThreshold'] and trendUpData['didTrendUpHappen']:
                # check if allowed number of buy trades is reached
                if checkIfAllowedNumberOfTradesReached(pair, trading_broker_pair, BUY):
                    return

                if await checkIfOneDirectionTradeIsOn(pair, trading_broker_pair, SELL):
                    return

                await CreateBuySignal(trading_broker_pair, price, thresholds['buyThreshold'], price_time,
                                      current_system_time)
                await pWX.doTradeScenario(tradeAccount,
                                          dataAccount,
                                          trading_broker_pair,
                                          BUY,
                                          contractSize,
                                          spread,
                                          ORDER_COMMENT,
                                          pastCanldeCount,
                                          decimalPlaces,
                                          )
        elif OUTSIDE_BAR_STRATEGY == "ON":
            pastData = await pWX.get15MinHistoricalData(dataAccount, trading_broker_pair, pWX.CANDLE_PERIOD, True,
                                                        2, return_partial_candle=True)
            if not pastData:
                return

            currentCandle = pastData[-1]
            previousCandle = pastData[-2]
            if currentCandle['high'] > previousCandle['high'] and currentCandle['low'] < previousCandle['low']:
                if price > previousCandle['close'] and trendUpData['didTrendUpHappen']:
                    # check if allowed number of buy trades is reached
                    if checkIfAllowedNumberOfTradesReached(pair, trading_broker_pair, BUY):
                        return
                    if await checkIfOneDirectionTradeIsOn(pair, trading_broker_pair, SELL):
                        return

                    await CreateBuySignal(trading_broker_pair, price, previousCandle['close'], price_time,
                                          current_system_time)
                    await pWX.doTradeScenario(tradeAccount,
                                              dataAccount,
                                              trading_broker_pair,
                                              BUY,
                                              contractSize,
                                              spread,
                                              ORDER_COMMENT,
                                              pastCanldeCount,
                                              decimalPlaces,
                                              )
                elif price < previousCandle['close'] and trendUpData['didTrendDownHappen']:
                    # check if allowed number of sell trades is reached
                    if checkIfAllowedNumberOfTradesReached(pair, trading_broker_pair, SELL):
                        return
                    if await checkIfOneDirectionTradeIsOn(pair, trading_broker_pair, BUY):
                        return

                    await CreateSellSignal(trading_broker_pair, price, previousCandle['close'], price_time,
                                           current_system_time)
                    await pWX.doTradeScenario(tradeAccount,
                                              dataAccount,
                                              trading_broker_pair,
                                              SELL,
                                              contractSize,
                                              spread,
                                              ORDER_COMMENT,
                                              pastCanldeCount,
                                              decimalPlaces,
                                              )
    elif THRESHOLD_CALCULATION_STRATEGY == "ON":
        if price < thresholds['sellThreshold']:
            # check if allowed number of sell trades is reached
            if checkIfAllowedNumberOfTradesReached(pair, trading_broker_pair, SELL):
                return
            if await checkIfOneDirectionTradeIsOn(pair, trading_broker_pair, BUY):
                return

            await CreateSellSignal(trading_broker_pair, price, thresholds['sellThreshold'], price_time,
                                   current_system_time)
            await pWX.doTradeScenario(tradeAccount,
                                      dataAccount,
                                      trading_broker_pair,
                                      SELL,
                                      contractSize,
                                      spread,
                                      ORDER_COMMENT,
                                      pastCanldeCount,
                                      decimalPlaces,
                                      )

        elif price > thresholds['buyThreshold']:
            # check if allowed number of buy trades is reached
            if checkIfAllowedNumberOfTradesReached(pair, trading_broker_pair, BUY):
                return
            if await checkIfOneDirectionTradeIsOn(pair, trading_broker_pair, SELL):
                return

            await CreateBuySignal(trading_broker_pair, price, thresholds['buyThreshold'], price_time,
                                  current_system_time)
            await pWX.doTradeScenario(tradeAccount,
                                      dataAccount,
                                      trading_broker_pair,
                                      BUY,
                                      contractSize,
                                      spread,
                                      ORDER_COMMENT,
                                      pastCanldeCount,
                                      decimalPlaces,
                                      )

    elif OUTSIDE_BAR_STRATEGY == "ON":
        pastData = await pWX.get15MinHistoricalData(dataAccount, trading_broker_pair, pWX.CANDLE_PERIOD, True,
                                                    2, return_partial_candle=True)
        if not pastData:
            return

        currentCandle = pastData[-1]
        previousCandle = pastData[-2]
        if currentCandle['high'] > previousCandle['high'] and currentCandle['low'] < previousCandle['low']:
            if price > previousCandle['close']:
                # check if allowed number of buy trades is reached
                if checkIfAllowedNumberOfTradesReached(pair, trading_broker_pair, BUY):
                    return
                if await checkIfOneDirectionTradeIsOn(pair, trading_broker_pair, SELL):
                    return

                await CreateBuySignal(trading_broker_pair, price, previousCandle['close'], price_time,
                                      current_system_time)
                await pWX.doTradeScenario(tradeAccount,
                                          dataAccount,
                                          trading_broker_pair,
                                          BUY,
                                          contractSize,
                                          spread,
                                          ORDER_COMMENT,
                                          pastCanldeCount,
                                          decimalPlaces,
                                          )

            elif price < previousCandle['close']:
                # check if allowed number of sell trades is reached
                if checkIfAllowedNumberOfTradesReached(pair, trading_broker_pair, SELL):
                    return
                if await checkIfOneDirectionTradeIsOn(pair, trading_broker_pair, BUY):
                    return

                await CreateSellSignal(trading_broker_pair, price, previousCandle['close'], price_time,
                                       current_system_time)
                await pWX.doTradeScenario(tradeAccount,
                                          dataAccount,
                                          trading_broker_pair,
                                          SELL,
                                          contractSize,
                                          spread,
                                          ORDER_COMMENT,
                                          pastCanldeCount,
                                          decimalPlaces,
                                          )


async def IsWithinValidTimeRange(current_time):
    total_seconds = current_time.second + current_time.minute * 60
    for valid_interval in valid_intervals:
        is_valid = valid_interval[0] <= total_seconds <= valid_interval[1]
        if is_valid:
            return True
    return False


async def IsWithinValidCalculationTimeRange(current_time):
    total_seconds = current_time.second + current_time.minute * 60
    for valid_interval in valid_calculation_intervals:
        is_valid = valid_interval[0] <= total_seconds <= valid_interval[1]
        if is_valid:
            return True
    return False


async def IsWithinValidStopLossUpdatingTimeRange(current_time):
    return 7 <= current_time.second <= 10


async def IsWithinValidTrailingStopLossUpdatingTimeRange(current_time):
    total_seconds = current_time.second + current_time.minute * 60
    for valid_interval in valid_trailingstoploss_updating_intervals:
        is_valid = valid_interval[0] <= total_seconds <= valid_interval[1]
        if is_valid:
            return True
    return False


async def IsWithinValidOneMinuteStopLossTrailingTimeRange(current_time):
    mod_minute = 15 if pWX.CANDLE_PERIOD == "15m" else 5
    valid_minutes = current_time.minute % mod_minute
    valid_seconds = current_time.second

    return valid_minutes > 1 and 15 < valid_seconds < 20


async def IsWithinExceptionStopLossTrailingTimeRange(current_time):
    valid_seconds = current_time.second

    return 15 < valid_seconds < 20


async def StoredTrendUpCalculations(symbol, storedData):
    # Check if the file exists
    if not os.path.isfile("stored_trend_up_calculations.json"):
        # If not, create it with an empty JSON object
        with open("stored_trend_up_calculations.json", "w") as file:
            json.dump({}, file)

    # Existing code
    with open("stored_trend_up_calculations.json", "r") as file:
        data = json.load(file)
        data[symbol] = storedData
    with open("stored_trend_up_calculations.json", "w") as file:
        json.dump(data, file, indent=2)


async def GetStoredTrendUpCalculations(symbol):
    # Check if the file exists
    if not os.path.isfile("stored_trend_up_calculations.json"):
        # If not, create it with an empty JSON object
        with open("stored_trend_up_calculations.json", "w") as file:
            json.dump({}, file)

    # Existing code
    with open("stored_trend_up_calculations.json", "r") as file:
        data = json.load(file)
        if symbol in data:
            return data[symbol]
        else:
            return None


def log_trend_up_candle_strategy_update(symbol, high, low, didTrendUpHappen,
                                        didTrendDownHappen, isEntryCriteriaMet, currentCandle):
    with open("trend_up_candle_strategy_debug.txt", "a") as f:
        f.write(
            f" {symbol} High: {str(high)} | Low: {str(low)} Did Trend Up Happen: {str(didTrendUpHappen)}"
            f" | Did Trend Down Happen: {str(didTrendDownHappen)} | Is Entry Criteria Met: {str(isEntryCriteriaMet)}"
            f" | Current Candle: {str(currentCandle)} | System Time: {str(pWX.get_data_account_time())}\n")


async def TrendUpCandleLiveUpdate(dataAccountClient, symbol):
    try:
        pastData = await pWX.get15MinHistoricalData(dataAccountClient, symbol, pWX.CANDLE_PERIOD, True,
                                                    PAST_DATA_FOR_TRAILING_STOP_LOSS)

        trendUpCandleData = await GetStoredTrendUpCalculations(symbol)
        high = trendUpCandleData['high']
        low = trendUpCandleData['low']
        highCandle = trendUpCandleData['highCandle']
        lowCandle = trendUpCandleData['lowCandle']
        didTrendUpHappen = trendUpCandleData['didTrendUpHappen']
        didTrendDownHappen = trendUpCandleData['didTrendDownHappen']
        isEntryCriteriaMet = trendUpCandleData['isEntryCriteriaMet']

        runHigh = True
        runLow = True
        currentCandle = pastData[-1]
        if currentCandle['high'] > high and currentCandle['low'] < low:
            print("Both high and low broke" + str(currentCandle) + " High: " + str(high) + " Low: " + str(low))
            if currentCandle['close'] > currentCandle['open']:
                runHigh = True
                runLow = False
            else:
                runHigh = False
                runLow = True

        if currentCandle['high'] > high and runHigh:
            high = currentCandle['high']
            highCandle = currentCandle
            # need to find new lowest point and lowest candle
            newLow, newLowCandle = findNewLowCandle(pastData, currentCandle)
            low = newLow
            lowCandle = newLowCandle
            if didTrendUpHappen and not didTrendDownHappen:
                isEntryCriteriaMet = True
            else:
                isEntryCriteriaMet = False

            didTrendUpHappen = True
            didTrendDownHappen = False

        elif currentCandle['low'] < low and runLow:
            low = currentCandle['low']
            lowCandle = currentCandle
            # need to find new highest point and highest candle
            newHigh, newHighCandle = findNewHighCandle(pastData, currentCandle)
            high = newHigh
            highCandle = newHighCandle
            if didTrendDownHappen and not didTrendUpHappen:
                isEntryCriteriaMet = True
            else:
                isEntryCriteriaMet = False

            didTrendDownHappen = True
            didTrendUpHappen = False
        else:
            isEntryCriteriaMet = False
            didTrendDownHappen = False
            didTrendUpHappen = False

        log_trend_up_candle_strategy_update(symbol, high, low, didTrendUpHappen,
                                            didTrendDownHappen, isEntryCriteriaMet, currentCandle)

        storedData = {
            'high': high,
            'low': low,
            'highCandle': highCandle,
            'lowCandle': lowCandle,
            'didTrendUpHappen': didTrendUpHappen,
            'didTrendDownHappen': didTrendDownHappen,
            'isEntryCriteriaMet': isEntryCriteriaMet
        }
        await StoredTrendUpCalculations(symbol, storedData)
    except Exception as e:
        print(f"Live Trend Up failed for {symbol}")
        log_error(e, "Live Trend Up failed for " + symbol)


async def TrendUpCandleStrategyInit(dataAccountClient, trading_account_pairs):
    for symbol in trading_account_pairs:
        pastData = await pWX.get15MinHistoricalData(dataAccountClient, symbol, pWX.CANDLE_PERIOD, True,
                                                    TREND_UP_INITIAL_CANDLES)
        high = pastData[0]['high']
        low = pastData[0]['low']
        highCandle = pastData[0]
        lowCandle = pastData[0]
        pastData.remove(pastData[0])
        didTrendUpHappen = False
        didTrendDownHappen = False
        isEntryCriteriaMet = False

        for candle in pastData:
            runHigh = True
            runLow = True

            if candle['high'] > high and candle['low'] < low:
                print("Both high and low broke" + str(candle) + " High: " + str(high) + " Low: " + str(low))
                if candle['close'] > candle['open']:
                    runHigh = True
                    runLow = False
                else:
                    runHigh = False
                    runLow = True

            if candle['high'] > high and runHigh:
                high = candle['high']
                highCandle = candle
                # need to find new lowest point and lowest candle
                newLow, newLowCandle = findNewLowCandle(pastData, candle)
                low = newLow
                lowCandle = newLowCandle
                if didTrendUpHappen and not didTrendDownHappen:
                    isEntryCriteriaMet = True

                didTrendUpHappen = True
                didTrendDownHappen = False

            elif candle['low'] < low and runLow:
                low = candle['low']
                lowCandle = candle
                # need to find new highest point and highest candle
                newHigh, newHighCandle = findNewHighCandle(pastData, candle)
                high = newHigh
                highCandle = newHighCandle
                if didTrendDownHappen and not didTrendUpHappen:
                    isEntryCriteriaMet = True

                didTrendDownHappen = True
                didTrendUpHappen = False
            else:
                isEntryCriteriaMet = False
                didTrendDownHappen = False
                didTrendUpHappen = False

            log_trend_up_candle_strategy_update(symbol, high, low, didTrendUpHappen,
                                                didTrendDownHappen, isEntryCriteriaMet, candle)

        storedData = {
            'high': high,
            'low': low,
            'highCandle': highCandle,
            'lowCandle': lowCandle,
            'didTrendUpHappen': didTrendUpHappen,
            'didTrendDownHappen': didTrendDownHappen,
            'isEntryCriteriaMet': isEntryCriteriaMet
        }
        await StoredTrendUpCalculations(symbol, storedData)


async def MainTradingLoop():
    # get all keys of the trading_pair_dict
    print("Trading Loop Started")
    trading_pairs = list(trading_pair_dict.keys())
    trading_account_pairs = [trading_pair_dict[tp][trade_broker_name] for tp in trading_pairs]
    dataAccountInstruments = {}
    for i in range(len(trading_pairs)):
        dataAccountInstruments[trading_account_pairs[i]] = trading_pairs[i]

    tradingAccountInstruments = {}
    for i in range(len(trading_pairs)):
        tradingAccountInstruments[trading_account_pairs[i]] = trading_account_pairs[i]

    print("Trying to connect to data account")

    dataAccountClient = Client(api_key, api_secret)
    tradeAccountClient = dataAccountClient

    print("Trade account connected")


    print("Data and Trade account connected")

    if TREND_UP_STRATEGY == "ON":
        print("Trend Up Strategy is ON")
        await TrendUpCandleStrategyInit(dataAccountClient, trading_account_pairs)

    print("Trading Loop Started")
    count = 0
    while count < 1:
        coroutines = [
            pWX.get1MinHistoricalData(dataAccountClient, symbol, TIMEFRAME_1M, True, PAST_DATA_FOR_TRAILING_STOP_LOSS)
            for
            symbol
            in
            trading_account_pairs]

        results = await asyncio.gather(*coroutines)
        print(results)

        coroutines = [
            pWX.get1MinHistoricalData(tradeAccountClient, symbol, TIMEFRAME_1M, False, PAST_DATA_FOR_TRAILING_STOP_LOSS)
            for
            symbol
            in
            trading_account_pairs]

        results = await asyncio.gather(*coroutines)
        print(results)

        coroutines = [
            pWX.get15MinHistoricalData(dataAccountClient, symbol, pWX.CANDLE_PERIOD, True,
                                       PAST_DATA_FOR_TRAILING_STOP_LOSS)
            for
            symbol in
            trading_account_pairs]

        results = await asyncio.gather(*coroutines)
        print(results)

        coroutines = [
            pWX.get15MinHistoricalData(tradeAccountClient, symbol, pWX.CANDLE_PERIOD, False,
                                       PAST_DATA_FOR_TRAILING_STOP_LOSS)
            for
            symbol in
            trading_account_pairs]

        results = await asyncio.gather(*coroutines)
        print(results)

        for symbol in trading_account_pairs:
            print(f"Price for {symbol} is {await pWX.getPrice(dataAccountClient, symbol)}")

        count += 1

    # for the first time, update calculations for all pairs
    await asyncio.gather(*[UpdateCalculations(dataAccountClient, pair) for pair in trading_pairs])

    current_datetime_temp = pWX.get_trade_account_time()
    is_news_day = False
    news_start_time = None
    news_end_time = None
    for news in NEWS_DICT_LIST:
        if current_datetime_temp.date() == datetime.strptime(news['NEWS_DATE'], '%d/%m/%Y').date():
            is_news_day = True
            news_start_time = datetime.strptime(news['NEWS_BLOCK_START'], '%H:%M:%S').time()
            news_end_time = datetime.strptime(news['NEWS_BLOCK_END'], '%H:%M:%S').time()
            break

    while True:
        try:
            current_datetime = pWX.get_trade_account_time()
            current_time = current_datetime.time()
            print(f"Current UTC+2 time: {current_time}")

            # if day is friday, close all trades
            if FRIDAY_CLOSE == "ON" and current_datetime.weekday() == 4 and current_time.hour == FRIDAY_CLOSE_DATETIME.hour and current_time.minute == FRIDAY_CLOSE_DATETIME.minute and current_time.second == FRIDAY_CLOSE_DATETIME.second:
                action = pWX.close_all_positions(tradeAccountClient)
                time.sleep(60)

            if DAILY_CLOSE == "ON" and current_time.hour == DAILY_CLOSE_DATETIME.hour and current_time.minute == DAILY_CLOSE_DATETIME.minute and current_time.second == DAILY_CLOSE_DATETIME.second:
                action = pWX.close_all_positions(tradeAccountClient)
                time.sleep(60)

            if is_news_day and news_start_time.hour == current_time.hour and news_start_time.minute == current_time.minute and news_start_time.second == current_time.second:
                action = pWX.close_all_positions(tradeAccountClient)
                time.sleep(1)

            if (datetime.strptime(BOT_TIME_START, '%H:%M:%S').time() <= current_time
                    <= datetime.strptime(BOT_TIME_END, '%H:%M:%S').time() and BOT_STATUS == 'ON'):
                is_valid = await IsWithinValidTimeRange(current_time)
                is_valid_calculation = await IsWithinValidCalculationTimeRange(current_time)
                is_valid_stoploss_updating = await IsWithinValidStopLossUpdatingTimeRange(current_time)
                is_valid_trailingstoploss_updating = await IsWithinValidTrailingStopLossUpdatingTimeRange(current_time)
                is_valid_one_minute_stoploss_trailing = await IsWithinValidOneMinuteStopLossTrailingTimeRange(
                    current_time)
                is_valid_exception_stoploss_trailing = await IsWithinExceptionStopLossTrailingTimeRange(
                    current_time)

                if is_valid and datetime.strptime(TRADING_TIME_START,
                                                  '%H:%M:%S').time() <= current_time <= datetime.strptime(
                    TRADING_TIME_END, '%H:%M:%S').time() and (
                        not is_news_day or (is_news_day and (news_end_time < current_time > news_start_time))
                        or (is_news_day and (news_end_time > current_time < news_start_time))):
                    print("We're within the desired Signal time range!" + str(current_time))
                    await asyncio.gather(
                        *[ProcessPair(dataAccountClient, tradeAccountClient, pair, dataAccountClient) for pair in
                          trading_pairs])
                    time.sleep(10)
                elif is_valid_calculation:
                    print("We're within the desired Calculation time range!" + str(current_time))
                    await asyncio.gather(*[UpdateCalculations(dataAccountClient, pair) for pair in trading_pairs])
                    time.sleep(5)
                elif is_valid_trailingstoploss_updating:
                    print("We're within the desired Trailing Stop Loss Updating time range!" + str(current_time))
                    await UpdateTrailingStopLoss(dataAccountClient, tradeAccountClient, current_time)
                    time.sleep(8)
                elif is_valid_stoploss_updating:
                    print("We're within the desired Stop Loss Updating time range!" + str(current_time))
                    await UpdateStopLossofTrade(tradeAccountClient, current_datetime, dataAccountClient)
                elif is_valid_one_minute_stoploss_trailing:
                    print("We're within the desired One Minute Stop Loss Trailing time range!" + str(current_time))
                    await UpdateOneMinuteTrailingStopLoss(tradeAccountClient, current_datetime)
                    time.sleep(5)

                time.sleep(0.5)
                print("Sleeping for 0.5 seconds")

        except Exception as e:
            print(f"Error in the main loop: {e}")
            log_error(e, f"Error in the main loop")
            await asyncio.sleep(60)


if __name__ == '__main__':
    asyncio.run(MainTradingLoop())
