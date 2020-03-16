import json
import logging
import argparse
import pandas as pd
import yahoo_fin.options

from datetime import datetime
from yahoo_stocks import YahooStocks
from typing import List, Dict, Any
from logger import Logger


class YahooOptions:
    def __init__(self,
                 log: logging.Logger,
                 config: Dict[str, Any]) -> None:
        self.log = log
        self.config = config

    def get_expiration_dates(self,
                             tickers: List[str]) -> List[str]:
        expiration_dates: List[str] = []
        for ticker in tickers:
            try:
                expiration_dates += yahoo_fin.options.get_expiration_dates(
                    ticker)
            except Exception as error:
                self.log.error(str(error) + ticker)
                continue
        return expiration_dates

    def get_calls(self,
                  tickers: List[str],
                  option_expiration_date: datetime = None) -> Dict[str, pd.DataFrame]:
        expiry = option_expiration_date.strftime("%m/%d/%Y") \
            if option_expiration_date is not None else None
        calls: Dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            try:
                calls[ticker] = yahoo_fin.options.get_calls(ticker,
                                                            expiry)
            except Exception as error:
                self.log.error(str(error) + ticker)
                continue
        return calls

    def get_puts(self,
                 tickers: List[str],
                 option_expiration_date: datetime = None) -> Dict[str, pd.DataFrame]:
        expiry = option_expiration_date.strftime("%m/%d/%Y") \
            if option_expiration_date is not None else None
        puts: Dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            try:
                puts[ticker] = yahoo_fin.options.get_puts(ticker,
                                                          expiry)
            except Exception as error:
                self.log.error(str(error) + ticker)
                continue
        return puts

    def get_options_chain(self,
                          tickers: List[str],
                          option_expiration_date: datetime = None) -> Dict[str, Dict[str, pd.DataFrame]]:
        expiry = option_expiration_date.strftime("%m/%d/%Y") \
            if option_expiration_date is not None else None
        option_chains: Dict[str, Dict[str, pd.DataFrame]] = {}
        for ticker in tickers:
            try:
                option_chains[ticker] = yahoo_fin.options.get_options_chain(ticker,
                                                                            expiry)
            except Exception as error:
                self.log.error(str(error) + ticker)
                continue
        return option_chains

    def run(self):
        tickers = list(YahooStocks(self.log, self.config).get_tickers(
            self.config["exchanges"])[-1])
        print(self.get_expiration_dates(tickers))
        print(self.get_calls(tickers))
        print(self.get_puts(tickers))
        print(self.get_options_chain(tickers))


def parse_args() -> str:
    parser = argparse.ArgumentParser(description="Yahoo Options Data")
    parser.add_argument("-config", type=str, required=True,
                        help="Config file")
    args = parser.parse_args()
    return args.config


def main() -> None:
    config = parse_args()
    log = Logger("yahoo_options.log").get_logger()

    with open(config) as conf:
        params = json.load(conf)

    y_o = YahooOptions(log, params)
    y_o.run()


if __name__ == "__main__":
    main()
