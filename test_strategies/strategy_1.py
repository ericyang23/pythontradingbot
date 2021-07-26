import json
import pprint
import pandas as pd
import operator

from datetime import datetime, timedelta
from configparser import ConfigParser

from pythontradingbot.robot import PyRobot
from pythontradingbot.indicator import Indicators
from pythontradingbot.trades import Trade

from td.client import TDClient

config = ConfigParser()
config.read("config/config.ini")

CLIENT_ID = config.get("main", "CLIENT_ID")
REDIRECT_URI = config.get("main", "REDIRECT_URI")
CREDENTIALS_PATH = config.get("main", "JSON_PATH")
ACCOUNT_NUMBER = config.get("main", "ACCOUNT_NUMBER")

trading_robot = PyRobot(
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    credentials_path=CREDENTIALS_PATH,
    trading_account=ACCOUNT_NUMBER,
    paper_trading=True
)

trading_robot_portfolio = trading_robot.create_portfolio()

trading_symbol = 'BB'

trading_robot_portfolio.add_position(
    symbol=trading_symbol,
    asset_type='equity'
)

start_date = datetime.today()
end_date = start_date - timedelta(days=30)

historical_prices = trading_robot.grab_historical_prices(
    start=end_date,
    end=start_date,
    bar_size=1,
    bar_type='minute'
)

# Create stock frame
stock_frame = trading_robot.create_stock_frame(
    data=historical_prices['aggregated']
)


trading_robot.portfolio.stock_frame = stock_frame
trading_robot.portfolio.historical_prices = historical_prices

# Create a new indicator object
indicator_client = Indicators(price_data_frame=stock_frame)

# Add the 200-day SMA
indicator_client.sma(period=200, column_name='sma_200')

# Add the 50-day SMA
indicator_client.sma(period=50, column_name='sma_50')

# Add the 50 day exponentials moving average.
indicator_client.ema(period=50)

# Add a signal check
indicator_client.set_indicator_signal_compare(
    indicator_1='sma_50',
    indicator_2='sma_200',
    condition_buy=operator.ge,
    condition_sell=operator.le
)

# Create a new trade object to enter
new_long_trade = trading_robot.create_trade(
    trade_id='long_enter',
    enter_or_exit='enter',
    long_or_short='long',
    order_type='mkt'
)

# Add an order leg
new_long_trade.instrument(
    symbol=trading_symbol,
    quantity=1,
    asset_type='EQUITY'
)

# Create a new trade object to exit
new_exit_trade = trading_robot.create_trade(
    trade_id='long_exit',
    enter_or_exit='exit',
    long_or_short='long',
    order_type='mkt'
)

# Add an order leg
new_exit_trade.instrument(
    symbol=trading_symbol,
    quantity=1,
    asset_type='EQUITY'
)


def default(obj):
    if isinstance(obj, TDClient):
        return str(obj)

# Save order
with open(file='order_strategies.json', mode='w+') as order_file:
    json.dump(
        obj=[new_long_trade.to_dict(), new_exit_trade.to_dict()],
        fp=order_file,
        default=default,
        indent=4
    )

# Define a trading dictionary
trade_dict = {
    trading_symbol: {
        'buy': {
            'trade_func': trading_robot.trades['long_enter'],
            'trade_id': trading_robot.trades['long_enter'].trade_id
        },
        'sell': {
            'trade_func': trading_robot.trades['long_exit'],
            'trade_id': trading_robot.trades['long_exit'].trade_id
        }
    }
}

# Define the ownership
ownership_dict = {
    trading_symbol: False
}

# Initialize an order variable
order = None