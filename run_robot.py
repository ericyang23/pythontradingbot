import time as true_time
import pprint
import pathlib
import operator
import pandas as pd

from datetime import datetime, timedelta
from configparser import ConfigParser

from pythontradingbot.robot import PyRobot
from pythontradingbot.indicator import Indicators

# Grab the config file
config = ConfigParser()
config.read('config_setup/config.ini') 

CLIENT_ID = config.get('main', 'CLIENT_ID')
REDIRECT_URI = config.get('main', 'REDIRECT_URI')
CREDENTIALS_PATH = config.get('main', 'JSON_PATH')
ACCOUNT_NUMBER = config.get('main', 'ACCOUNT_NUMBER')

# Initialize the robot
trading_robot = PyRobot(
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    credentials_path=CREDENTIALS_PATH,
    trading_account=ACCOUNT_NUMBER,
    paper_trading=True
)