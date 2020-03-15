import csv
import asyncio
import datetime

from yahoo_stocks import YahooStocks
from yahoo_options import YahooOptions

from typing import Union, List, Any, Dict


class CsvExporter:
    def __init__(self,
                 data: Dict[str, Any],
                 yahoo_adapter):
        self.data = data
        self.yahoo_adapter = yahoo_adapter

    def export_stats_to_csv(self) -> Dict[str, bool]:
        if isinstance(self.yahoo_adapter, YahooStocks):
            with open("adjclose_stats.csv", "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                for key, value in self.data.items():
                    writer.writerow([key, value])
            return {"success": True}
        return {"success": False}

    def export_ticker_stats_to_csv(self) -> Dict[str, bool]:
        if isinstance(self.yahoo_adapter, YahooStocks):
            asyncio.set_event_loop(asyncio.new_event_loop())
            ticker_stats = asyncio.get_event_loop().run_until_complete(
                self.yahoo_adapter.get_ticker_stats(list(self.data.keys())))
            with open("ticker_stats.csv", "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                for key, value in ticker_stats.items():
                    writer.writerow([key, value])
            return {"success": True}
        return {"success": False}

    def export_options_chain_to_csv(
            self, expiration_date: datetime.datetime = None) -> Dict[str, bool]:
        if isinstance(self.yahoo_adapter, YahooOptions):
            options_chain = self.yahoo_adapter.get_options_chain(list(self.data.keys()),
                                                                 expiration_date)
            with open("option_chain.csv", "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                for key, value in options_chain.items():
                    writer.writerow([key, value])
            return {"success": True}
        return {"success": False}
