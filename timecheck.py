import json
from datetime import datetime, timedelta

import pytz

with open('environment.json', 'r') as f:
    # Load the data into a dictionary
    environment_data = json.load(f)

DATA_ACCOUNT_TIME_ZONE = environment_data['DATA_ACCOUNT_TIME_ZONE'] or 'Europe/Tallinn'
TRADE_ACCOUNT_TIME_ZONE = environment_data['TRADE_ACCOUNT_TIME_ZONE'] or 'Europe/Tallinn'
DATA_ACCOUNT_TIME_DICT = environment_data['DATA_ACCOUNT_TIME_DICT'] or {'hours': 0, 'minutes': 0}
TRADE_ACCOUNT_TIME_DICT = environment_data['TRADE_ACCOUNT_TIME_DICT'] or {'hours': 0, 'minutes': 0}

print("CURRENT_TIME", datetime.now())

print("DATA_ACCOUNT_TIME",
      datetime.now(pytz.timezone(DATA_ACCOUNT_TIME_ZONE)) + timedelta(hours=DATA_ACCOUNT_TIME_DICT['hours'],
                                                                      minutes=DATA_ACCOUNT_TIME_DICT['minutes']))
print("TRADE_ACCOUNT_TIME",
        datetime.now(pytz.timezone(TRADE_ACCOUNT_TIME_ZONE)) + timedelta(hours=TRADE_ACCOUNT_TIME_DICT['hours'],
                                                                        minutes=TRADE_ACCOUNT_TIME_DICT['minutes']))
