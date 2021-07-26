import pandas as pd
import time as time_true
import json
import pathlib

from td.client import TDClient
from td.utils import TDUtilities
milliseconds_since_epoch = TDUtilities().milliseconds_since_epoch
from datetime import datetime, timezone, timedelta

from typing import List, Dict, Optional, Union

from pythontradingbot.portfolio import Portfolio
from pythontradingbot.stock_frame import StockFrame
from pythontradingbot.trades import Trade


class PyRobot():

    def __init__(self, client_id: str, redirect_uri: str, credentials_path: str = None, 
                 trading_account: str = None, paper_trading: bool = True) -> None:
        """[summary]

        Args:
            client_id (str): [description]
            redirect_uri (str): [description]
            credentials_path (str, optional): [description]. Defaults to None.
            trading_account (str, optional): [description]. Defaults to None.
        """      

        self.trading_account: str = trading_account
        self.client_id: str = client_id
        self.redirect_uri: str = redirect_uri
        self.credentials_path: str = credentials_path
        self.sessions: TDClient = self._create_session()
        self.trades: dict = {}
        self.historical_prices: dict = {}
        self.stock_frame = None
        self.paper_trading = paper_trading

    def _create_session(self) -> TDClient:

        td_client = TDClient(
            client_id = self.client_id,
            redirect_uri = self.redirect_uri,
            credentials_path = self.credentials_path
        )

        #Login to the session 
        td_client.login()

        return td_client

    @property
    def pre_market_open(self) -> bool:
        
        pre_market_start_time = datetime.utcnow().replace(hour=12, minute=00, second=00).timestamp()
        market_start_time = datetime.utcnow().replace(hour=13, minute=30, second=00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if market_start_time >= right_now >= pre_market_start_time:
            return True
        else:
            return False

    @property
    def post_market_open(self) -> bool:
        
        post_market_end_time = datetime.utcnow().replace(hour=22, minute=30, second=00).timestamp()
        market_end_time = datetime.utcnow().replace(hour=20, minute=00, second=00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if post_market_end_time >= right_now >= market_end_time:
            return True
        else:
            return False

    @property
    def regular_market_open(self) -> bool:
        
        market_start_time = datetime.utcnow().replace(hour=13, minute=30, second=00).timestamp()
        market_end_time = datetime.utcnow().replace(hour=20, minute=00, second=00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if market_end_time >= right_now >= market_start_time:
            return True
        else:
            return False

    def create_portfolio(self):
        
        # Initialize a new Portfolio object
        self.portfolio = Portfolio(account_number=self.trading_account)

        # Assign the client 
        self.portfolio.td_client = self.sessions

        return self.portfolio

    def create_stock_frame(self, data: List[dict]) -> StockFrame:
        
        self.stock_frame = StockFrame(data=data)

        return self.stock_frame

    def create_trade(self, trade_id: str, enter_or_exit: str, long_or_short: str, order_type: str = 'mkt', 
                     price: float = 0.00, stop_limit_price: float = 0.00) -> Trade:
        
        # Initialize a new trade object
        trade = Trade()

        # Create a new trade
        trade.new_trade(
            trade_id=trade_id,
            order_type=order_type,
            enter_or_exit=enter_or_exit,
            long_or_short=long_or_short,
            price=price,
            stop_limit_price=stop_limit_price
        )

        self.trades[trade_id] = trade

        return trade

    def grab_current_quotes(self) -> dict:

        # First grab all the symbols.
        symbols = self.portfolio.positions.keys()

        # Grab the quotes.
        quotes = self.sessions.get_quotes(instruments=list(symbols))

        return quotes

    def grab_historical_prices(self, start: datetime, end: datetime, bar_size: int = 1, 
                               bar_type: str = 'minute', symbols: Optional[List[str]] = None) -> List[Dict]:
        
        self._bar_size = bar_size
        self._bar_type = bar_type

        start = str(milliseconds_since_epoch(dt_object=start))
        end = str(milliseconds_since_epoch(dt_object=end))

        new_prices = []

        if not symbols:
            symbols = self.portfolio.positions

        for symbol in symbols:
            historical_price_response = self.sessions.get_price_history(
                symbol=symbol,
                period_type='day',
                start_date=start,
                end_date=end,
                frequency_type=bar_type,
                frequency=bar_size,
                extended_hours=True
            )

            self.historical_prices[symbol] = {}
            self.historical_prices[symbol]['candles'] = historical_price_response['candles']

            for candle in historical_price_response['candles']:

                new_price_mini_dict = {}
                new_price_mini_dict['symbol'] = candle['symbol']
                new_price_mini_dict['open'] = candle['open']
                new_price_mini_dict['close'] = candle['close']
                new_price_mini_dict['high'] = candle['high']
                new_price_mini_dict['low'] = candle['low']
                new_price_mini_dict['volume'] = candle['volume']
                new_price_mini_dict['datetime'] = candle['datetime']
                new_prices.append(new_price_mini_dict)

            self.historical_prices['aggregated'] = new_prices

            return self.historical_prices

    def get_latest_bar(self) -> List[dict]:

        bar_size = self._bar_size
        bar_type = self._bar_type

        # Define our date range
        end_date = datetime.today()
        start_date = end_date - timedelta(minutes=15)

        start = str(milliseconds_since_epoch(dt_object=start_date))
        end = str(milliseconds_since_epoch(dt_object=end_date))

        latest_prices = []

        for symbol in self.portfolio.positions:

            try:

                # Grab the request.
                historical_prices_response = self.sessions.get_price_history(
                    symbol=symbol,
                    period_type='day',
                    start_date=start,
                    end_date=end,
                    frequency_type=bar_type,
                    frequency=bar_size,
                    extended_hours=True
                )

            except:

                time_true.sleep(2)

                # Grab the request.
                historical_prices_response = self.sessions.get_price_history(
                    symbol=symbol,
                    period_type='day',
                    start_date=start,
                    end_date=end,
                    frequency_type=bar_type,
                    frequency=bar_size,
                    extended_hours=True
                )

            # parse the candles.
            for candle in historical_prices_response['candles'][-1:]:

                new_price_mini_dict = {}
                new_price_mini_dict['symbol'] = symbol
                new_price_mini_dict['open'] = candle['open']
                new_price_mini_dict['close'] = candle['close']
                new_price_mini_dict['high'] = candle['high']
                new_price_mini_dict['low'] = candle['low']
                new_price_mini_dict['volume'] = candle['volume']
                new_price_mini_dict['datetime'] = candle['datetime']
                latest_prices.append(new_price_mini_dict)

        return latest_prices

    def wait_til_next_bar(self, last_bar_timestamp: pd.DatetimeIndex) -> None:

        last_bar_time = last_bar_timestamp.to_pydatetime()[0].replace(tzinfo=timezone.utc)
        next_bar_time = last_bar_time + timedelta(seconds=60)
        curr_bar_time = datetime.now(tz=timezone.utc)

        last_bar_timestamp = int(last_bar_time.timestamp())
        next_bar_timestamp = int(next_bar_time.timestamp())
        curr_bar_timestamp = int(curr_bar_time.timestamp())

        time_to_wait_now = next_bar_timestamp - curr_bar_timestamp
        
        if time_to_wait_now < 0:
            time_to_wait_now = 0

        print("=" * 80)
        print("Pausing for the next bar")
        print("-" * 80)
        print("Curr Time: {time_curr}".format(
            time_curr=curr_bar_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        )
        print("Next Time: {time_next}".format(
            time_next=next_bar_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        )
        print("Sleep Time: {seconds}".format(seconds=time_to_wait_now))
        print("-" * 80)
        print('')

        time_true.sleep(time_to_wait_now)



