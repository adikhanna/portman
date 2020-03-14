import json
import asyncio
import logging
import argparse
import yahoo_fin.options
import yahoo_fin.stock_info

from datetime import datetime, timedelta
from typing import List, Dict, Any


class VolStocksFilter:
    def __init__(self, log: logging.Logger, config: Dict[str, Any]) -> None:
        self.log = log
        self.end_date = datetime.now()
        self.stat_date = self.end_date - timedelta(days=config["lookback_duration_days"])
        self.option_expiration_date = config["option_expiration_date"]
        self.beta_threshold = config["beta_threshold"]
        self.exchanges = config["exchanges"]

    async def run(self) -> None:
        data = await self.get_price_data(self.get_volatile_tickers(self.get_tickers()))
        print(self.get_options_chain(data))
        print(self.compute_stats(data))

    def get_tickers(self) -> List[str]:
        all_tickers: List[str] = []
        for exchange in self.exchanges:
            try:
                exchange_tickers = eval("yahoo_fin.stock_info.tickers_" + exchange + "()")
                all_tickers += exchange_tickers
            except Exception as error:
                self.log.error(error, str(exchange))
                continue
        return all_tickers

    def get_volatile_tickers(self, tickers: List[str]) -> List[str]:
        vol_tickers: List[str] = []
        for ticker in tickers:
            try:
                data = yahoo_fin.stock_info.get_quote_table(ticker)
            except Exception as error:
                self.log.error(error, ticker)
                continue
            else:
                if float(data["Beta (5Y Monthly)"]) >= self.beta_threshold:
                    vol_tickers.append(ticker)
        return vol_tickers

    async def get_ticker_data(self, price_data: Dict[str, Any], ticker: str) -> None:
        try:
            price_data[ticker] = yahoo_fin.stock_info.get_data(ticker,
                                          start_date=self.stat_date.strftime("%m/%d/%Y"),
                                          end_date=self.end_date.strftime("%m/%d/%Y"))
        except Exception as error:
            self.log.error(error)

    async def get_price_data(self, tickers: List[str]) -> Dict[str, Any]:
        tasks: List[asyncio.Future] = []
        price_data: Dict[str, Any] = {}
        for ticker in tickers:
            task = asyncio.ensure_future(self.get_ticker_data(price_data, ticker))
            tasks.append(task)
        await asyncio.gather(*tasks)
        return price_data

    def get_options_chain(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        option_chains: Dict[str, Any] = {}
        for ticker in price_data.keys():
            try:
                option_chains[ticker] = yahoo_fin.options.get_options_chain(ticker, self.option_expiration_date)
            except Exception as error:
                self.log.error(error)
                continue
        return option_chains

    def compute_stats(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        price_stats: Dict[str, Any] = {}
        for ticker in price_data.keys():
            price_stats[ticker] = {
                "mean": price_data[ticker]["adjclose"].mean(),
                "median": price_data[ticker]["adjclose"].median(),
                "std_dev": price_data[ticker]["adjclose"].std(),
                "variance": price_data[ticker]["adjclose"].var()
            }
        return price_stats


def parse_args() -> str:
    parser = argparse.ArgumentParser(description="Volatile Stocks Filter")
    parser.add_argument("-config", type=str, required=True,
                        help="Config file")
    args = parser.parse_args()
    return args.config


def setup_logging() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    file_handle = logging.FileHandler("vol_stocks_filter.log")
    logger.addHandler(file_handle)
    return logger


async def main() -> None:
    log = setup_logging()
    config = parse_args()

    with open(config) as conf:
        params = json.load(conf)

    vsf = VolStocksFilter(log, params)
    await vsf.run()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
