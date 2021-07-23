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

# Create a new portfolio
trading_robot_portfolio = trading_robot.create_portfolio()

# Add multiple positions to our portfolio
multi_position = [
    {
        'asset_type': 'equity',
        'quantity': 2,
        'purchase_price': 4.00,
        'symbol': 'TSLA',
        'purchase_date': '2020-01-31'
    },
    {
        'asset_type': 'equity',
        'quantity': 2,
        'purchase_price': 4.00,
        'symbol': 'SQ',
        'purchase_date': '2020-01-31'
    }
]

# Add those positions to the portfolio
new_positions = trading_robot.portfolio.add_positions(positions=multi_position)
pprint.pprint(new_positions)

#Add a single position to the portfolio
trading_robot.portfolio.add_position(
    symbol='MSFT',
    quantity=10,
    purchase_price=10.00,
    assest_type='equity',
    purchase_date='2020-04-01'
)
pprint.pprint(trading_robot.portfolio.positions)

# Check to see if the regular market is open
if trading_robot.regular_market_open:
    print('Regular Market Open')
else:
    print('Regular Market Not Open')

# Check to see if the pre market is open
if trading_robot.pre_market_open:
    print('Pre Market Open')
else:
    print('Pre Market Not Open')

# Check to see if the post market is open
if trading_robot.post_market_open:
    print('Post Market Open')
else:
    print('Post Market Not Open')

# Grab the current quotes in our portfolio
current_quotes = trading_robot.grab_current_quotes()
pprint.pprint(current_quotes)

# Define our date range
end_date = datetime.today()
start_date = end_date - timedelta(days=30)

# Grab the historical prices
historical_prices = trading_robot.grab_historical_prices(
    start=start_date,
    end=end_date,
    bar_size=1,
    bar_type='minute'
)

# Convert the data into a StockFrame
stock_frame = trading_robot.create_stock_frame(data=historical_prices['aggregated'])

# Print the head of the StockFrame
pprint.pprint(stock_frame.frame.head(n=20))

# Create a new Trade object
new_trade = trading_robot.create_trade(
    trade_id='long_msft',
    enter_or_exit='enter',
    long_or_short='long',
    order_type='lmt',
    price=150.00
)

# Make it good til cancel
new_trade.good_til_cancel(cancel_time=datetime.now())

# Change the session
new_trade.modify_session(session='am')

# Add an order leg
new_trade.instrument(
    symbol='MSFT',
    quantity=2,
    asset_type='EQUITY'
)

# Add a stop loss
new_trade.add_stop_loss(
    stop_size=.10,
    percentage=False
)

# Print out the order
pprint,pprint(new_trade.order)

# Create a new indicator client
indicator_client = Indicators(price_data_frame=stock_frame)

# Add the RSI indicator
indicator_client.rsi(period=14)

# Add a 200 day simple moving average
indicator_client.sma(period=200)

# Add a 50 day exponential moving average
indicator_client.ema(period=50)

#Add a signal to check for 
indicator_client.set_indicator_signals(
    indicator='rsi',
    buy=40.0,
    sell=20.0,
    condiction_buy=operator.ge,
    condition_sell=operator.le
)

# Define a trade dictionary
trades_dict = {
    'MSFT': {
        'trade_func': trading_robot.trades['long_msft'],
        'trade_id': trading_robot.trades['long_msft'].trade_id
    }
}

while True:

    # Grab the latest bar
    latest_bars = trading_robot.get_latest_bar()

    # Add those bars to the StockFrame
    stock_frame.add_rows(data=latest_bars)

    # Refresh the indicators
    indicator_client.refresh()

    print("="*50)
    print("Current StockFrame")
    print("-"*50)
    print(stock_frame.symbol_groups.tail())
    print("-"*50)
    print("")

    # Check for signals.
    signals = indicator_client.check_signals()

    # Execute Trades.
    trading_robot.execute_signals(
        signals=signals,
        trades_to_execute=trades_dict
    )

    # Grab the last bar.
    last_bar_timestamp = trading_robot.stock_frame.frame.tail(
        n=1
    ).index.get_level_values(1)

    # Wait till the next bar.
    trading_robot.wait_till_next_bar(last_bar_timestamp=last_bar_timestamp)