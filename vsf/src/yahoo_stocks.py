import json
import asyncio
import logging
import argparse
import pandas as pd
import yahoo_fin.stock_info

from datetime import datetime, timedelta
from typing import List, Dict, Any
from logger import Logger


class YahooStocks:
    def __init__(self,
                 log: logging.Logger,
                 config: Dict[str, Any]) -> None:
        self.log = log
        self.config = config

    def get_tickers(self,
                    exchanges: List[str]) -> List[str]:
        tickers: List[str] = []
        for exchange in exchanges:
            try:
                exchange_tickers = eval(
                    "yahoo_fin.stock_info.tickers_" + exchange + "()")
                tickers += exchange_tickers
            except Exception as error:
                self.log.error(str(error) + exchange)
                continue
        return tickers

    def get_volatile_tickers(self,
                             tickers: List[str],
                             beta_threshold: float) -> List[str]:
        vol_tickers: List[str] = []
        for ticker in tickers:
            try:
                data = yahoo_fin.stock_info.get_quote_table(ticker)
            except Exception as error:
                self.log.error(str(error) + ticker)
                continue
            else:
                if float(data["Beta (5Y Monthly)"]) >= beta_threshold:
                    vol_tickers.append(ticker)
        return vol_tickers

    async def _get_data(self, ticker: str,
                        ticker_data: Dict[str, pd.DataFrame],
                        start_date: datetime,
                        end_date: datetime) -> None:
        try:
            ticker_data[ticker] = yahoo_fin.stock_info.get_data(ticker,
                                                                start_date=start_date.strftime(
                                                                    "%m/%d/%Y"),
                                                                end_date=end_date.strftime("%m/%d/%Y"))
        except Exception as error:
            self.log.error(str(error) + ticker)

    async def get_ticker_data(self, tickers: List[str],
                              start_date: datetime,
                              end_date: datetime) -> Dict[str, pd.DataFrame]:
        tasks: List[asyncio.Future] = []
        ticker_data: Dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            task = asyncio.ensure_future(
                self._get_data(
                    ticker,
                    ticker_data,
                    start_date,
                    end_date))
            tasks.append(task)
        await asyncio.gather(*tasks)
        return ticker_data

    def get_adjclose_stats(self,
                           ticker_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, float]]:
        ticker_stats: Dict[str, pd.DataFrame] = {}
        for ticker in ticker_data.keys():
            ticker_stats[ticker] = {
                "mean": ticker_data[ticker]["adjclose"].mean(),
                "median": ticker_data[ticker]["adjclose"].median(),
                "std_dev": ticker_data[ticker]["adjclose"].std(),
                "variance": ticker_data[ticker]["adjclose"].var()
            }
        return ticker_stats

    async def _get_stats(self,
                         ticker: str,
                         ticker_stats: Dict[str, pd.DataFrame]) -> None:
        try:
            ticker_stats[ticker] = yahoo_fin.stock_info.get_stats(ticker)
        except Exception as error:
            self.log.error(str(error) + ticker)

    async def get_ticker_stats(self,
                               tickers: List[str]) -> Dict[str, pd.DataFrame]:
        tasks: List[asyncio.Future] = []
        ticker_stats: Dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            task = asyncio.ensure_future(self._get_stats(ticker, ticker_stats))
            tasks.append(task)
        await asyncio.gather(*tasks)
        return ticker_stats

    def get_day_gainers(self) -> List[str]:
        day_gainers: List[str] = []
        try:
            day_gainers = yahoo_fin.stock_info.get_day_gainers()
        except Exception as error:
            self.log.error(str(error))
        return day_gainers

    def get_day_losers(self) -> List[str]:
        day_losers: List[str] = []
        try:
            day_losers = yahoo_fin.stock_info.get_day_losers()
        except Exception as error:
            self.log.error(str(error))
        return day_losers

    def get_day_most_active(self) -> List[str]:
        day_most_active: List[str] = []
        try:
            day_most_active = yahoo_fin.stock_info.get_day_most_active()
        except Exception as error:
            self.log.error(str(error))
        return day_most_active

    async def run(self) -> None:
        end_date = datetime.now()
        start_date = end_date - \
            timedelta(days=self.config["lookback_duration_days"])
        vol_tickers = self.get_volatile_tickers(self.get_tickers(self.config["exchanges"]),
                                                self.config["beta_threshold"])
        ticker_data = await self.get_ticker_data(vol_tickers, start_date, end_date)
        ticker_stats = await self.get_ticker_stats(vol_tickers)
        print(ticker_stats)
        print(self.get_adjclose_stats(ticker_data))
        print(self.get_day_gainers())
        print(self.get_day_losers())
        print(self.get_day_most_active())


def parse_args() -> str:
    parser = argparse.ArgumentParser(description="Yahoo Stocks Data")
    parser.add_argument("-config", type=str, required=True,
                        help="Config file")
    args = parser.parse_args()
    return args.config


async def main() -> None:
    config = parse_args()
    log = Logger("yahoo_stocks.log").get_logger()

    with open(config) as conf:
        params = json.load(conf)

    y_s = YahooStocks(log, params)
    await y_s.run()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
