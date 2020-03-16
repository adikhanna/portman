import json
import asyncio
import argparse
import datetime

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from logger import Logger
from functools import partial

from thread_worker import Worker
from yahoo_stocks import YahooStocks
from yahoo_options import YahooOptions
from csv_exporter import CsvExporter
from stocks_feed import TopStocksFeed

from typing import Dict, Any, List


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, config: Dict[str, Any], *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.logger = Logger("ui.log").get_logger()
        self.exchanges_to_search: List[str] = []
        self.search_results: Dict[str, Dict[str, float]] = {}
        self.thread_pool = QtCore.QThreadPool()
        self.stats_to_compute = config["stats"]
        self.available_exchanges = config["exchanges"]
        self.yahoo_stocks = YahooStocks(self.logger, config)
        self.yahoo_options = YahooOptions(self.logger, config)
        self._initialize_window()

    def log(self, text: dict) -> None:
        self.logger.info(text)

    def _initialize_window(self) -> None:
        self.setWindowTitle("Volatile Stocks Finder")
        self.setGeometry(50, 50, 315, 1500)

        self.options_popup_layout = QtWidgets.QVBoxLayout()
        self.options_popup_frame = QtWidgets.QWidget()
        self.options_popup_frame.setLayout(self.options_popup_layout)

        self.layout = QtWidgets.QVBoxLayout()

        self._initialize_feeds()
        self._initialize_buttons()
        self._initialize_children_windows()

        widget = QtWidgets.QWidget()
        widget.setLayout(self.layout)

        self.setCentralWidget(widget)

    def _initialize_feeds(self) -> None:
        self.layout.addWidget(TopStocksFeed(self.yahoo_stocks))

    def _initialize_buttons(self) -> None:
        params_button = QtWidgets.QPushButton("Find Stocks")
        params_button.clicked.connect(self.show_search_params_window)
        self.layout.addWidget(params_button)

    def _initialize_children_windows(self) -> None:
        self.params_window = QtWidgets.QDialog()
        self.error_window = QtWidgets.QMessageBox()

    def _checkbox_toggle(self,
                        checkbox: QtWidgets.QCheckBox,
                        state: QtCore.Qt) -> None:
        if state == QtCore.Qt.Checked:
            self.exchanges_to_search.append(checkbox.text())
        else:
            self.exchanges_to_search.remove(checkbox.text())

    def _set_search_params_window(self) -> None:
        self.params_window = QtWidgets.QDialog()
        self.params_window.layout = QtWidgets.QVBoxLayout()
        self.params_window.setWindowTitle("Find Stocks")
        self.params_window.setGeometry(550, 50, 600, 400)

        self.exchange_layout = QtWidgets.QHBoxLayout()
        self.rest_layout = QtWidgets.QHBoxLayout()

        for exchange in self.available_exchanges:
            check_box = QtWidgets.QCheckBox(exchange)
            check_box.stateChanged.connect(partial(self._checkbox_toggle, check_box))
            self.exchange_layout.addWidget(check_box)

        beta_threshold = QtWidgets.QLabel("Beta Threshold:")
        lookback_period = QtWidgets.QLabel("Lookback Period (Days):")
        search_button = QtWidgets.QPushButton("Search")

        self.params_window.beta_threshold = QtWidgets.QLineEdit()
        self.rest_layout.addWidget(beta_threshold)
        self.rest_layout.addWidget(self.params_window.beta_threshold)
        self.params_window.lookback_period = QtWidgets.QLineEdit()
        self.rest_layout.addWidget(lookback_period)
        self.rest_layout.addWidget(self.params_window.lookback_period)

        self.params_window.layout.addLayout(self.exchange_layout)
        self.params_window.layout.addLayout(self.rest_layout)

        search_button.clicked.connect(self.check_fields)
        self.params_window.layout.addWidget(search_button)

    def show_search_params_window(self) -> None:
        self._set_search_params_window()
        self.params_window.setLayout(self.params_window.layout)
        self.params_window.show()

    def _validate_beta_threshold(self) -> bool:
        text = self.params_window.beta_threshold.text()
        if len(text) == 0:
            return False
        return True

    def _validate_lookback_period(self) -> bool:
        text = self.params_window.lookback_period.text()
        if len(text) == 0:
            return False
        return True

    def _show_error_window(self, error_text: str) -> None:
        self.error_window.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_window.setWindowTitle("Error")
        self.error_window.setText(error_text)
        self.error_window.show()

    def _dispatch(self,
                 fn,
                 res) -> None:
        worker = Worker(fn)
        worker.signals.result.connect(res)
        self.thread_pool.start(worker)

    def check_fields(self) -> None:
        if not self._validate_beta_threshold():
            self._show_error_window("Please enter a valid beta threshold")
        elif not self._validate_lookback_period():
            self._show_error_window("Please enter a valid lookback period")
        elif len(self.exchanges_to_search) == 0:
            self._show_error_window("Please select at least one exchange to search")
        else:
            self.beta_threshold = float(self.params_window.beta_threshold.text())
            self.lookback_period = int(self.params_window.lookback_period.text())
            self.params_window.close()
            self._dispatch(self.find_stocks, self.display_search_results)

    def display_search_results(self) -> None:
        if len(self.search_results) > 0:
            search_layout = QtWidgets.QVBoxLayout()
            search_frame = QtWidgets.QWidget()
            search_frame.setLayout(search_layout)

            w = QtWidgets.QTableWidget(0, len(self.search_results.keys())+1)
            w.setHorizontalHeaderLabels(["Statistic"] + list(self.search_results.keys()))

            for i, k in enumerate(self.stats_to_compute):
                w.insertRow(w.rowCount())
                it = QtWidgets.QTableWidgetItem()
                it.setData(QtCore.Qt.DisplayRole, str(k))
                w.setItem(i, 0, it)

            for i, (key, value) in enumerate(self.search_results.items()):
                rows = [value[k] for k in value.keys()]
                for j, v in enumerate(rows):
                    it = QtWidgets.QTableWidgetItem()
                    it.setData(QtCore.Qt.DisplayRole, str(v))
                    w.setItem(j, i+1, it)

            search_layout.addWidget(w)
            self._add_buttons_to_results(search_layout, search_frame)
            self.layout.addWidget(search_frame)
            search_frame.show()
        else:
            self._show_error_window("No stocks found")

    def _add_buttons_to_results(self, search_layout, search_frame) -> None:
        yahoo_stocks_csv = CsvExporter(self.search_results, self.yahoo_stocks)

        this_button = QtWidgets.QPushButton("Export this to csv...")
        this_button.clicked.connect(partial(self._dispatch,
                                            yahoo_stocks_csv.export_stats_to_csv,
                                            self.log))
        search_layout.addWidget(this_button)

        stats_button = QtWidgets.QPushButton("Export stats to csv...")
        stats_button.clicked.connect(partial(self._dispatch,
                                             yahoo_stocks_csv.export_ticker_stats_to_csv,
                                             self.log))
        search_layout.addWidget(stats_button)

        ops_button = QtWidgets.QPushButton("Get options data for these symbols...")
        ops_button.clicked.connect(self.show_options_data)
        search_layout.addWidget(ops_button)

        exit_button = QtWidgets.QPushButton("Close search")
        exit_button.clicked.connect(search_frame.close)
        search_layout.addWidget(exit_button)

    def show_options_data(self) -> None:
        combo_box = QtWidgets.QComboBox()
        combo_box.addItems(self.yahoo_options.get_expiration_dates(list(self.search_results.keys())))
        self.options_popup_layout.addWidget(combo_box)
        expiration_date = datetime.datetime.strptime(str(combo_box.currentText()), "%B %d, %Y")
        yahoo_options_csv = CsvExporter(self.search_results, self.yahoo_options, expiration_date)
        ops_button = QtWidgets.QPushButton("Export options data to csv...")
        ops_button.clicked.connect(partial(self._dispatch,
                                           yahoo_options_csv.export_options_chain_to_csv,
                                           self.log))
        self.options_popup_layout.addWidget(ops_button)
        self.options_popup_frame.show()

    def find_stocks(self) -> Dict[str, Dict[str, float]]:
        asyncio.set_event_loop(asyncio.new_event_loop())
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=self.lookback_period)
        vol_tickers = self.yahoo_stocks.get_volatile_tickers(self.yahoo_stocks.get_tickers(self.exchanges_to_search),
                                               self.beta_threshold)
        ticker_data = asyncio.get_event_loop().run_until_complete(self.yahoo_stocks.get_ticker_data(vol_tickers, start_date, end_date))
        self.search_results = self.yahoo_stocks.get_adjclose_stats(ticker_data)
        return self.search_results


def parse_args() -> str:
    parser = argparse.ArgumentParser(description="vsf")
    parser.add_argument("-config", type=str, required=True,
                        help="Config file")
    args = parser.parse_args()
    return args.config


def main():
    config = parse_args()

    with open(config) as conf:
        params = json.load(conf)

    app = QtWidgets.QApplication([])
    window = MainWindow(params)
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
