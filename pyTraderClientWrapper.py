import asyncio
import json
import random
import time
from datetime import datetime, timedelta

import pytz
import requests
from binance.enums import HistoricalKlinesType

from strategy import log_error, log_general_error

# Open the JSON file
with open('environment.json', 'r') as f:
    # Load the data into a dictionary
    environment_data = json.load(f)

# Environment variables for the trading bot
TRAILING_STOP_LOSS_SIZE_MULTIPLIER = float(environment_data['TRAILING_STOP_LOSS_SIZE_MULTIPLIER']) or 0.5
TRADE_STOP_LOSS_SIZE_MULTIPLIER = float(environment_data['TRADE_STOP_LOSS_SIZE_MULTIPLIER']) or 0.5
CANDLE_PERIOD = environment_data['CANDLE_PERIOD'] or '15m'
RISK_AMOUNT = int(environment_data['RISK_AMOUNT']) or 100
ORDER_TYPE_BUY = "buy"
ORDER_TYPE_SELL = "sell"
DATA_ACCOUNT_TIME_ZONE = environment_data['DATA_ACCOUNT_TIME_ZONE'] or 'Europe/Tallinn'
TRADE_ACCOUNT_TIME_ZONE = environment_data['TRADE_ACCOUNT_TIME_ZONE'] or 'Europe/Tallinn'
DATA_ACCOUNT_TIME_DICT = environment_data['DATA_ACCOUNT_TIME_DICT'] or {'hours': 0, 'minutes': 0}
TRADE_ACCOUNT_TIME_DICT = environment_data['TRADE_ACCOUNT_TIME_DICT'] or {'hours': 0, 'minutes': 0}
MIN_MAX_CONTROLLER = environment_data['MIN_MAX_CONTROLLER'] or 'TRADE'
TELEGRAM_CHAT_ID = "-1002217857669"
TELEGRAM_BOT_TOKEN = "7427647021:AAFytDlcix4-Y5tqkJfkiAmoUF5Uw7XY4Z8"

# Valid trade intervals
if CANDLE_PERIOD == '15m':
    valid__trade_intervals = [(890, 900), (1790, 1800), (2690, 2700), (3590, 3600)]
elif CANDLE_PERIOD == '5m':
    valid__trade_intervals = [(290, 300), (590, 600), (890, 900), (1190, 1200), (1490, 1500), (1790, 1800),
                              (2090, 2100), (2390, 2400), (2690, 2700), (2990, 3000), (3290, 3300), (3590, 3600)]


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

    result = client.futures_orderbook_ticker(symbol=symbol)
    if result:
        result['date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        result['bid'] = float(result['bidPrice'])
        result['ask'] = float(result['askPrice'])
        return result
    else:
        return None


def placeTrade(client, symbol, action_type, volume, stop_loss, comment):
    """
        Function to place a trade on the market.

        Args:
            client (dwx_client): The dwx_client instance.
            symbol (str): The symbol to trade.
            action_type (str): The action type (buy or sell).
            volume (float): The volume of the trade.
            stop_loss (float): The stop loss for the trade.
            comment (str): A comment for the trade.

        Returns:
            dict: The last opened order.
        """

    # if TRADE_ACCOUNT_TYPE == 'MT5':
    #     result = mt5.order_send({
    #         "action": mt5.TRADE_ACTION_DEAL,
    #         "symbol": symbol,
    #         "volume": volume,
    #         "type": mt5.ORDER_TYPE_BUY if action_type == ORDER_TYPE_BUY else mt5.ORDER_TYPE_SELL,
    #         "sl": stop_loss,
    #         "comment": comment,
    #     })
    #     if result.retcode != mt5.TRADE_RETCODE_DONE:
    #         print(f"Failed to place trade: {result}")
    #         log_general_error(f"Failed to place trade: {result.retcode} | {mt5.last_error()}")
    #         return None
    #
    #     return {"positionId": result.order, "actionType": action_type, "volume": result.volume,
    #             "stopLoss": result.request.sl}
    # else:
    #     result = client.Open_order(instrument=symbol, ordertype=action_type, volume=volume, stoploss=stop_loss,
    #                                comment=comment)
    #     if result is not None:
    #         return {"positionId": result, "actionType": action_type, "volume": volume, "stopLoss": stop_loss}

    return {"positionId": random.randint(1, 1000), "actionType": action_type, "volume": volume, "stopLoss": stop_loss}


async def getHistoricalData(client, symbol, time_frame, limit=0):
    """
        Function to get the historical market data for a given symbol over a specified time frame.

        Args:
            client (dwx_client): The PyTrader instance.
            symbol (str): The symbol to get the historical data for.
            time_frame (str): The time frame to get the historical data for.
            limit (int): The limit for the historical data..

        Returns:
            list: The historical market data for the given symbol over the specified time frame.
        """
    if time_frame == "15m":
        time_frame = "15m"
    elif time_frame == "5m":
        time_frame = "5m"

    result = client.get_historical_klines(symbol, time_frame, limit=limit+1, klines_type=HistoricalKlinesType.FUTURES)
    temp_list = []
    if result is not None:
        for r in result:
            temp_dict = {
                "time": datetime.fromtimestamp(r[0]/1000).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
            }
            temp_list.append(temp_dict)

        return temp_list


async def get15MinHistoricalData(client, symbol, time_frame, data_account, limit=0, max_retries=7,
                                 return_partial_candle=False):
    """
        Function to get the historical market data for a given symbol over a specified time frame.

        Args:
            client (pyTraderClient): The pyTraderClient instance.
            symbol (str): The symbol to get the historical data for.
            time_frame (str): The time frame to get the historical data for.
            limit (int): The limit for the historical data
            max_retries (int): The maximum number of retries to fetch the historical data.
            return_partial_candle (bool): Whether to return the partial candle or not.

        Returns:
            list: The historical market data for the given symbol over the specified time frame.
        """
    retries = 0
    while retries < max_retries:
        try:
            pastData = await getHistoricalData(client, symbol, time_frame, limit)
            if pastData:
                lastCandleTime = datetime.strptime(pastData[-1]['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                    tzinfo=pytz.utc)

                if data_account:
                    currentSystemTime = get_data_account_time()
                else:
                    currentSystemTime = get_trade_account_time()
                # Check if the last candle is the latest one
                if time_frame == '15m':
                    temp_datetime = currentSystemTime - timedelta(minutes=currentSystemTime.minute % 15,
                                                                  seconds=currentSystemTime.second,
                                                                  microseconds=currentSystemTime.microsecond)
                    partial_candle_time = temp_datetime
                    if lastCandleTime.hour == partial_candle_time.hour and lastCandleTime.minute == partial_candle_time.minute:
                        if return_partial_candle:
                            return pastData
                        else:
                            return pastData[:-1]
                    else:
                        print(f"Last candle {pastData[-1]['time']} is not the latest one for {symbol}. Retrying...")
                        log_general_error(
                            f"Last candle {pastData[-1]['time']} is not the latest one for {symbol}. Retrying...")
                        time.sleep(1)
                        retries += 1
                        if retries == max_retries:
                            fifteen_minutes_ago = temp_datetime - timedelta(minutes=15)
                            if (lastCandleTime.hour == fifteen_minutes_ago.hour
                                    and lastCandleTime.minute == fifteen_minutes_ago.minute):

                                log_general_error(
                                    f"Candle has not been closed for {symbol} using partial candle. {str(pastData[-1])}")
                                return pastData
                            else:
                                log_general_error(f"Data is very old for {symbol}. {str(pastData[-1])}")

                elif time_frame == '5m':
                    temp_datetime = currentSystemTime - timedelta(minutes=currentSystemTime.minute % 5,
                                                                  seconds=currentSystemTime.second,
                                                                  microseconds=currentSystemTime.microsecond)
                    partial_candle_time = temp_datetime
                    if lastCandleTime.hour == partial_candle_time.hour and lastCandleTime.minute == partial_candle_time.minute:
                        if return_partial_candle:
                            return pastData
                        else:
                            return pastData[:-1]
                    else:
                        print(f"Last candle {pastData[-1]['time']} is not the latest one for {symbol}. Retrying...")
                        log_general_error(
                            f"Last candle {pastData[-1]['time']} is not the latest one for {symbol}. Retrying...")
                        time.sleep(1)
                        retries += 1
                        if retries == max_retries:
                            five_minutes_ago = temp_datetime - timedelta(minutes=5)
                            if (lastCandleTime.hour == five_minutes_ago.hour
                                    and lastCandleTime.minute == five_minutes_ago.minute):

                                log_general_error(
                                    f"Candle has not been closed for {symbol} using partial candle. {str(pastData[-1])}")
                                return pastData
                            else:
                                log_general_error(f"Data is very old for {symbol}. {str(pastData[-1])}")

            else:
                print(f"Failed to fetch past data for {symbol}")
                log_general_error(f"Failed to fetch past data for {symbol}")
                retries += 1

        except Exception as e:
            print(f"Error fetching past data for {symbol}: {e}")
            log_error(e, f"Error fetching past data for {symbol}")
            retries += 1
    print(f"Failed to fetch past data for {symbol} after {max_retries} attempts.")
    return []


async def get1MinHistoricalData(client, symbol, time_frame, data_account, limit=0, max_retries=7):
    """
        Function to get the historical market data for a given symbol over a specified time frame.

        Args:
            client (pyTraderClient): The pyTraderClient instance.
            symbol (str): The symbol to get the historical data for.
            time_frame (str): The time frame to get the historical data for.
            limit (int): The limit for the historical data
            max_retries (int): The maximum number of retries to fetch the historical data.

        Returns:
            list: The historical market data for the given symbol over the specified time frame.
        """
    retries = 0
    while retries < max_retries:
        try:
            pastData = await getHistoricalData(client, symbol, time_frame, limit)
            if pastData:
                lastCandleTime = datetime.strptime(pastData[-1]['time'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                    tzinfo=pytz.utc)
                if data_account:
                    currentSystemTime = get_data_account_time()
                else:
                    currentSystemTime = get_trade_account_time()
                # Check if the last candle is the latest one
                if lastCandleTime.hour == currentSystemTime.hour and lastCandleTime.minute == currentSystemTime.minute:
                    return pastData[:-1]
                else:
                    print(
                        f"Last candle {pastData[-1]['time']} is not the latest one for {symbol}. Retrying... {currentSystemTime}")
                    log_general_error(
                        f"Last candle {pastData[-1]['time']} is not the latest one for {symbol}. Retrying...")
                    time.sleep(1)
                    retries += 1

                    if retries == max_retries:
                        one_minute_ago = currentSystemTime - timedelta(minutes=1)
                        if (lastCandleTime.hour == one_minute_ago.hour
                                and lastCandleTime.minute == one_minute_ago.minute):

                            log_general_error(
                                f"Candle has not been closed for {symbol} using partial candle. {str(pastData[-1])}")
                            return pastData
                        else:
                            log_general_error(f"Data is very old for {symbol}. {str(pastData[-1])}")
            else:
                print(f"Failed to fetch past data for {symbol}")
                log_general_error(f"Failed to fetch past data for {symbol}")
                retries += 1

        except Exception as e:
            print(f"Error fetching past data for {symbol}: {e}")
            log_error(e, f"Error fetching past data for {symbol}")
            retries += 1
    print(f"Failed to fetch past data for {symbol} after {max_retries} attempts.")
    return []


async def doTradeScenario(client, dataAccountClient, symbol, actionType, contractSize, spread, comment, limit,
                          decimalPlaces):
    """
    Function to perform a trade scenario.

    Args:
        client (PyTrader): The PyTrader object.
        symbol (str): The symbol to trade.
        actionType (str): The action type (buy or sell).
        contractSize (int): The contract size.
        spread (float): The spread.
        comment (str): The comment for the trade.
        limit (int): The limit for the trade.
        decimalPlaces (int): The decimal places for the trade.

    Returns:
        dict: The response from the API as a dictionary.
    """
    is_data_account = False
    controller_client = client
    if MIN_MAX_CONTROLLER == 'DATA':
        is_data_account = True
        controller_client = dataAccountClient

    current_system_time = get_data_account_time()
    openPrice = await getPrice(client, symbol)
    openPrice = float(openPrice['bid'])
    pastData = await get15MinHistoricalData(controller_client, symbol, CANDLE_PERIOD, is_data_account, limit)
    if not isWithInTradeInterval(current_system_time):
        #     log that the trade is not valid in lost_trades.txt
        with open('lost_trades.txt', 'a') as f:
            f.write(
                f'Symbol: {symbol} | | Time: {current_system_time} |'
                f' Reason: Candle is not complete | pastData: {str(pastData[-1])}\n')
        return

    minPastData = min(candle['low'] for candle in pastData)
    maxPastData = max(candle['high'] for candle in pastData)
    diffPastData = maxPastData - minPastData
    stopLossSize = diffPastData * TRADE_STOP_LOSS_SIZE_MULTIPLIER
    stopLoss = openPrice - stopLossSize if actionType == ORDER_TYPE_BUY else openPrice + stopLossSize + spread
    stopLoss = round(stopLoss, decimalPlaces)
    volume = RISK_AMOUNT / stopLossSize / contractSize
    # make volumne 2 decimal places
    volume = round(volume, 2)
    trade = placeTrade(client, symbol, actionType, volume, stopLoss, comment)
    if trade['positionId'] != -1:
        # log the trade in trades.json
        trade_data = {
            'time': str(current_system_time),
            'trade': trade,
            'symbol': symbol,
            'actionType': actionType,
            'volume': volume,
            'openPrice': openPrice,
            'spread': spread,
            'comment': comment,
            'stopLoss': stopLoss,
            'stopLossSize': stopLossSize,
            'minPastData': minPastData,
            'maxPastData': maxPastData,
            'diffPastData': diffPastData,
            'lastCandle': str(pastData[-1]),
            'decimalPlaces': decimalPlaces
        }
        saveTradeData(trade_data)
        saveActiveTradeData(trade_data)
        # log the trade in trades.txt
        with open('trades.txt', 'a') as f:
            f.write(f'{trade_data}\n')

        message_signal_telegram = f"PositionID: {trade['positionId']} Signal: {actionType} {symbol} | Time: {current_system_time} | Open Price: {openPrice} | SL: {stopLoss} "
        await send_telegram_message(TELEGRAM_CHAT_ID, message_signal_telegram)

        return trade
    else:
        # log that the trade is not valid in lost_trades.txt
        with open('lost_trades.txt', 'a') as f:
            f.write(
                f'Symbol: {symbol} | | Time: {current_system_time} |'
                f' Reason: Trade not valid | pastData: {str(pastData[-1])}'
                f' Action: {actionType} | Vol: {volume} | SL: {stopLoss} | SL Size: {stopLossSize}'
                f'\n')


def saveTradeData(trade_data):
    """
    Function to save trade data to a JSON file.

    Args:
        trade_data (dict): The trade data to save.
    """
    try:
        # Load existing trade data from the JSON file
        with open('trades.json', 'r') as json_file:
            existing_trade_data = json.load(json_file)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty list
        existing_trade_data = []

        # Append the new trade_data to the existing data
    existing_trade_data.append(trade_data)

    # Save the updated data back to the JSON file
    with open('trades.json', 'w') as json_file:
        json.dump(existing_trade_data, json_file, indent=2)


def saveActiveTradeData(trade_data):
    """
    Function to save active trade data to a JSON file.

    Args:
        trade_data (dict): The active trade data to save.
    """
    try:
        # Load existing trade data from the JSON file
        with open('active_trades.json', 'r') as json_file:
            existing_trade_data = json.load(json_file)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty list
        existing_trade_data = []

        # Append the new trade_data to the existing data
    existing_trade_data.append(trade_data)

    # Save the updated data back to the JSON file
    with open('active_trades.json', 'w') as json_file:
        json.dump(existing_trade_data, json_file, indent=2)


def loadTradeData():
    """
    Function to load trade data from a JSON file.

    Returns:
        list: The existing trade data.
    """
    try:
        # Load existing trade data from the JSON file
        with open('trades.json', 'r') as json_file:
            existing_trade_data = json.load(json_file)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty list
        existing_trade_data = []
    return existing_trade_data


def loadActiveTradeData():
    """
    Function to load active trade data from a JSON file.

    Returns:
        list: The existing active trade data.
    """
    try:
        # Load existing trade data from the JSON file
        with open('active_trades.json', 'r') as json_file:
            existing_trade_data = json.load(json_file)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty list
        existing_trade_data = []
    return existing_trade_data


def isWithInTradeInterval(current_time):
    """
    Function to check if the current time is within the valid trade intervals.

    Args:
        current_time (datetime.time): The current time.

    Returns:
        bool: True if the current time is within the valid trade intervals, False otherwise.
    """
    total_seconds = current_time.second + current_time.minute * 60
    for interval in valid__trade_intervals:
        if interval[0] <= total_seconds <= interval[1]:
            return True
    return False


async def updatePosition(client, positionId, stopLoss, symbol, previousStopLoss):
    """
    Function to update the position of a trade.

    Args:
        client (DWXClient): The DWXClient object.
        positionId (str): The position ID of the trade.
        stopLoss (float): The stop loss for the trade.

    Returns:
        dict: The response from the API as a dictionary.
    """
    # send telegram message
    await send_telegram_message(TELEGRAM_CHAT_ID, f"Updating SL for {symbol} | PositionID: {positionId} | SL: {stopLoss} | Previous SL: {previousStopLoss} | Time: {get_trade_account_time()}")
    return True


async def getActivePositions(client) -> list:
    """
    Function to get the active positions.

    Args:
        client (DWXClient): The DWXClient object.

    Returns:
        dict: The response from the API as a dictionary.
    """
    active_trades_data = loadActiveTradeData()
    active_positions = []
    coroutines = [getPrice(client, symbol) for
                  symbol in
                  trading_pairs]
    results = await asyncio.gather(*coroutines)
    symbolPrices = dict(zip(trading_pairs, results))
    for active_trade_data in active_trades_data:
        symbol = active_trade_data['symbol']
        positionId = active_trade_data['trade']['positionId']
        stopLoss = active_trade_data['currentStopLoss']
        openPrice = active_trade_data['openPrice']
        temp_dict = {
            "positionId": positionId,
        }
        actionType = active_trade_data['actionType']
        if actionType == ORDER_TYPE_BUY:
            current_symbol_price = symbolPrices[symbol]['ask']
            if current_symbol_price > stopLoss:
                active_positions.append(temp_dict)
            else:
                calculate_profit = stopLoss - openPrice
                calculate_percent = (calculate_profit / openPrice) * 100
                message = f"Position Closed {positionId} | Time: {str(get_trade_account_time())} | Symbol: {symbol} | Open Price: {openPrice} | Stop Loss: {stopLoss} | Current Price: {current_symbol_price} | Profit Gained: {calculate_profit} | Profit Gain Percentage: {calculate_percent}"
                await send_telegram_message(TELEGRAM_CHAT_ID, message)
        else:
            current_symbol_price = symbolPrices[symbol]['bid']
            if current_symbol_price < stopLoss:
                active_positions.append(temp_dict)
            else:
                calculate_profit = openPrice - stopLoss
                calculate_percent = (calculate_profit / openPrice) * 100
                message = f"Position Closed {positionId} | Time: {str(get_trade_account_time())} | Symbol: {symbol} | Open Price: {openPrice} | Stop Loss: {stopLoss} | Current Price: {current_symbol_price} | Profit Gained: {calculate_profit} | Profit Gain Percentage: {calculate_percent}"
                await send_telegram_message(TELEGRAM_CHAT_ID, message)
    return active_positions


async def getAccountInfo(client):
    """
    Function to get the account information.

    Args:
        client (DWXClient): The DWXClient object.

    Returns:
        dict: The response from the API as a dictionary.
    """
    return client.MT.Get_static_account_info()


def get_utcplus2():
    """
    Function to get the current time in UTC+2.

    Returns:
        datetime: The current time in UTC+2.
    """
    return datetime.now(pytz.timezone('Europe/Tallinn')) + timedelta(hours=0)


def get_data_account_time():
    """
    Function to get the current time in the data account.

    Returns:
        datetime: The current time in the data account.
    """
    return datetime.now(pytz.timezone(DATA_ACCOUNT_TIME_ZONE)) + timedelta(hours=DATA_ACCOUNT_TIME_DICT['hours'],
                                                                           minutes=DATA_ACCOUNT_TIME_DICT['minutes'])


def get_trade_account_time():
    """
    Function to get the current time of the trade account.

    Returns:
        datetime: The current time of the trade account.
    """
    return datetime.now(pytz.timezone(TRADE_ACCOUNT_TIME_ZONE)) + timedelta(hours=TRADE_ACCOUNT_TIME_DICT['hours'],
                                                                            minutes=TRADE_ACCOUNT_TIME_DICT['minutes'])


def close_all_positions(client):
    """
    Function to close all open positions.

    Args:
        client (PyTrader): The PyTrader instance.

    Returns:
        dict: The response from the API as a dictionary.
    """
    # active_trades_data = loadActiveTradeData()
    # for active_trade_data in active_trades_data:
    #     if "positionId" in active_trade_data['trade']:
    #         action = client.Close_position_by_ticket(active_trade_data['trade']['positionId'])
    #         if action:
    #             print(f"Closed position {active_trade_data['trade']['positionId']}")
    #             with open('position_close_log.txt', 'a') as fx:
    #                 fx.write(
    #                     f"Position Closed {str(active_trade_data['trade']['positionId'])} | Time: {str(get_trade_account_time())} | response: {str(action)}\n")
    #         else:
    #             print(f"Failed to close position {active_trade_data['trade']['positionId']}")
    #             with open('position_close_log.txt', 'a') as f:
    #                 f.write(
    #                     f"Failed to close position {active_trade_data['trade']['positionId']} | Time: {str(get_trade_account_time())} | response: {str(client.command_return_error)}\n")
    #     else:
    #         print(f"Position ID not found for {active_trade_data}")
    #         with open('position_close_log.txt', 'a') as f:
    #             f.write(
    #                 f"Position ID not found for {active_trade_data} | Time: {str(get_trade_account_time())}\n")
    #
    #     try:
    #         os.remove('active_trades.json')
    #     except FileNotFoundError:
    #         pass

    return True


# Function to get the direction of the active trade for a symbol
async def get_active_trade_direction(symbol):
    positions = loadActiveTradeData()
    with open('direction_log.txt', 'a') as f:
        f.write(f"Active trades: {str(positions)}\n")
    for position in positions:
        if position['symbol'] == symbol:
            with open('direction_log.txt', 'a') as f:
                f.write(f"Active trade found for {symbol} | {str(position)}\n")
            return position['actionType']
    return None


async def send_telegram_message(chat_id, message):
    """
    Function to send a message to a Telegram chat.

    Args:
        chat_id (str): The chat ID of the Telegram chat.
        message (str): The message to send.

    Returns:
        dict: The response from the Telegram API as a dictionary.
    """
    # Replace 'your_bot_token' with the token you received from BotFather


    # Define the URL to send a message
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'

    # Define the message data
    data = {
        'chat_id': chat_id,
        'text': message
    }

    # Make a request to the URL
    response = requests.post(url, data=data)

    # Parse the JSON response
    return response.json()
