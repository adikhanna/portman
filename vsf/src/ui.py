import datetime
import asyncio
import threading
import json
import time
import csv

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
from functools import partial
from yahoo_stocks import YahooStocks
from yahoo_options import YahooOptions
from logger import Logger
from typing import List


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Volatile Stocks Finder")
        self.setGeometry(50, 50, 900, 900)
        self.exchanges_to_search = []
        self.threadpool = QtCore.QThreadPool()
        self.search_layout = QtWidgets.QVBoxLayout()
        self.search_frame = QtWidgets.QWidget()
        self.search_frame.setLayout(self.search_layout)

        self.options_layout = QtWidgets.QVBoxLayout()
        self.options_frame = QtWidgets.QWidget()
        self.options_frame.setLayout(self.options_layout)

        layout = QtWidgets.QVBoxLayout()

        gainer_label = QtWidgets.QLabel("Top 100 Gainers Today")
        layout.addWidget(gainer_label)
        gainer_feed = TopGainers()
        layout.addWidget(gainer_feed)

        active_label = QtWidgets.QLabel("Top 100 Most Active Today")
        layout.addWidget(active_label)
        active_feed = TopActive()
        layout.addWidget(active_feed)

        params_button = QtWidgets.QPushButton("Find Stocks")
        params_button.clicked.connect(self.search_params)
        layout.addWidget(params_button)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)
        self.show()

    def search_params(self):
        self.params_window = QtWidgets.QDialog()
        self.error_window = QtWidgets.QMessageBox()

        self.params_window.layout = QtWidgets.QVBoxLayout()
        self.params_window.setWindowTitle("Find Stocks")
        self.params_window.setGeometry(965, 50, 600, 400)
        self.lay = self.params_window.layout

        self.exchange_layout = QtWidgets.QGridLayout()
        self.rest_layout = QtWidgets.QHBoxLayout()

        self.dow = QtWidgets.QCheckBox("dow")
        self.dow.stateChanged.connect(partial(self.exchange_toggle, self.dow))
        self.exchange_layout.addWidget(self.dow, 0, 0)

        self.sp500 = QtWidgets.QCheckBox("sp500")
        self.sp500.stateChanged.connect(partial(self.exchange_toggle, self.sp500))
        self.exchange_layout.addWidget(self.sp500, 1, 0)

        self.nasdaq = QtWidgets.QCheckBox("nasdaq")
        self.nasdaq.stateChanged.connect(partial(self.exchange_toggle, self.nasdaq))
        self.exchange_layout.addWidget(self.nasdaq, 0, 1)

        self.other = QtWidgets.QCheckBox("other")
        self.other.stateChanged.connect(partial(self.exchange_toggle, self.other))
        self.exchange_layout.addWidget(self.other, 1, 1)

        beta_threshold = QtWidgets.QLabel("Beta Threshold:")
        self.params_window.beta_threshold = QtWidgets.QLineEdit()

        self.rest_layout.addWidget(beta_threshold)
        self.rest_layout.addWidget(self.params_window.beta_threshold)

        lookback_period = QtWidgets.QLabel("Lookback Period (Days):")
        self.params_window.lookback_period = QtWidgets.QLineEdit()

        self.rest_layout.addWidget(lookback_period)
        self.rest_layout.addWidget(self.params_window.lookback_period)

        search_button = QtWidgets.QPushButton("Search")
        search_button.clicked.connect(self.check_fields)

        self.lay.addLayout(self.exchange_layout)
        self.lay.addLayout(self.rest_layout)

        self.lay.addWidget(search_button)

        self.params_window.setLayout(self.lay)
        self.params_window.show()

    def exchange_toggle(self, exchange: QtWidgets.QCheckBox, state: QtCore.Qt):
        if state == QtCore.Qt.Checked:
            self.exchanges_to_search.append(exchange.text())
        else:
            self.exchanges_to_search.remove(exchange.text())

    def check_fields(self):
        if len(self.params_window.beta_threshold.text()) == 0:
            self.error_window.setIcon(QtWidgets.QMessageBox.Critical)
            self.error_window.setWindowTitle("Error")
            self.error_window.setText("Please enter a valid beta threshold!")
            self.error_window.show()
        elif len(self.params_window.lookback_period.text()) == 0:
            self.error_window.setIcon(QtWidgets.QMessageBox.Critical)
            self.error_window.setWindowTitle("Error")
            self.error_window.setText("Please enter a valid lookback period!")
            self.error_window.show()
        else:
            self.beta_threshold = float(self.params_window.beta_threshold.text())
            self.lookback_period = int(self.params_window.lookback_period.text())
            self.params_window.close()
            worker = Worker(self.find_stocks)
            worker.signals.result.connect(self.print_output)
            self.threadpool.start(worker)

    def print_output(self, s):
        print(s)

        w = QtWidgets.QTableWidget(0, len(s.keys())+1)
        w.setWindowTitle("Search Results")
        w.setHorizontalHeaderLabels(["Statistic"] + list(s.keys()))

        for i, k in enumerate(["mean", "median", "std_dev", "variance"]):
            w.insertRow(w.rowCount())
            it = QtWidgets.QTableWidgetItem()
            it.setData(QtCore.Qt.DisplayRole, str(k))
            w.setItem(i, 0, it)

        for i, (key, value) in enumerate(s.items()):
            rows = [value[k] for k in value.keys()]
            for j, v in enumerate(rows):
                it = QtWidgets.QTableWidgetItem()
                it.setData(QtCore.Qt.DisplayRole, str(v))
                w.setItem(j, i+1, it)

        self.search_layout.addWidget(w)
        this_button = QtWidgets.QPushButton("Export this to csv...")
        this_button.clicked.connect(partial(self.export_this_to_csv, s))
        self.search_layout.addWidget(this_button)
        stats_button = QtWidgets.QPushButton("Export stats to csv...")
        stats_button.clicked.connect(partial(self.export_stats_to_csv, list(s.keys())))
        self.search_layout.addWidget(stats_button)
        ops_button = QtWidgets.QPushButton("Get options data for these symbols...")
        ops_button.clicked.connect(partial(self.get_ops_data, list(s.keys())))
        self.search_layout.addWidget(ops_button)
        self.search_frame.show()

    def export_this_to_csv(self, s):
        with open('this.csv', 'w', newline="") as csv_file:
            writer = csv.writer(csv_file)
            for key, value in s.items():
                writer.writerow([key, value])

    def export_stats_to_csv(self, s):
        y_s = YahooStocks(Logger("ui.log").get_logger(), {})
        ticker_stats = asyncio.get_event_loop().run_until_complete(y_s.get_ticker_stats(s))
        with open('stats.csv', 'w', newline="") as csv_file:
            writer = csv.writer(csv_file)
            for key, value in ticker_stats.items():
                writer.writerow([key, value])

    def get_ops_data(self, s):
        y_o = YahooOptions(Logger("ui.log").get_logger(), {})
        cb = QtWidgets.QComboBox()
        cb.setWindowTitle("Select Expiration")
        cb.addItems(y_o.get_expiration_dates(s))
        self.options_layout.addWidget(cb)
        ops_button = QtWidgets.QPushButton("Export options data to csv...")
        ops_button.clicked.connect(partial(self.export_ops_to_csv, s, None, y_o))
        self.options_layout.addWidget(ops_button)
        self.options_frame.show()

    def export_ops_to_csv(self, s, expiry, y_o):
        options_chain = y_o.get_options_chain(s, expiry)
        with open('ops.csv', 'w', newline="") as csv_file:
            writer = csv.writer(csv_file)
            for key, value in options_chain.items():
                writer.writerow([key, value])

    def find_stocks(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        y_s = YahooStocks(Logger("ui.log").get_logger(), {})
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=self.lookback_period)
        vol_tickers = y_s.get_volatile_tickers(y_s.get_tickers(self.exchanges_to_search),
                                               self.beta_threshold)
        ticker_data = asyncio.get_event_loop().run_until_complete(y_s.get_ticker_data(vol_tickers, start_date, end_date))
        return y_s.get_adjclose_stats(ticker_data)


class TopGainers(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # self.setGeometry(50, 50, 50, 50)
        self.label = QtWidgets.QLabel("")  # label showing the news
        self.label.setAlignment(QtCore.Qt.AlignRight)  # text starts on the right
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.timeLine = QtCore.QTimeLine()
        self.timeLine.setCurveShape(QtCore.QTimeLine.LinearCurve)  # linear Timeline
        self.timeLine.frameChanged.connect(self.setText)
        self.timeLine.finished.connect(self.nextNews)
        self.signalMapper = QtCore.QSignalMapper(self)

        self.feed()

    def feed(self):
        fm = self.label.fontMetrics()
        self.nl = int(self.label.width() / fm.averageCharWidth())*2  # shown stringlength
        news = []

        y_s = YahooStocks(Logger("ui.log").get_logger(), {})
        gainers = y_s.get_day_gainers()["Symbol"]
        # ma = y_s.get_day_most_active()

        for gainer in gainers:
            news.append(gainer)

        appendix = ' ' * self.nl  # add some spaces at the end
        news.append(appendix)
        delimiter = '      +++      '  # shown between the messages
        self.news = delimiter.join(news)
        newsLength = len(self.news)  # number of letters in news = frameRange
        lps = 16  # letters per second
        dur = newsLength * 1000 / lps  # duration until the whole string is shown in milliseconds
        self.timeLine.setDuration(dur)
        self.timeLine.setFrameRange(0, newsLength)
        self.timeLine.start()

    def setText(self, number_of_frame):
        if number_of_frame < self.nl:
            start = 0
        else:
            start = number_of_frame - self.nl
        text = '{}'.format(self.news[start:number_of_frame])
        self.label.setText(text)

    def nextNews(self):
        self.feed()  # start again


class TopActive(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # self.setGeometry(50, 50, 50, 50)
        self.label = QtWidgets.QLabel("")  # label showing the news
        self.label.setAlignment(QtCore.Qt.AlignRight)  # text starts on the right
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.timeLine = QtCore.QTimeLine()
        self.timeLine.setCurveShape(QtCore.QTimeLine.LinearCurve)  # linear Timeline
        self.timeLine.frameChanged.connect(self.setText)
        self.timeLine.finished.connect(self.nextNews)
        self.signalMapper = QtCore.QSignalMapper(self)

        self.feed()

    def feed(self):
        fm = self.label.fontMetrics()
        self.nl = int(self.label.width() / fm.averageCharWidth())*2  # shown stringlength
        news = []

        y_s = YahooStocks(Logger("ui.log").get_logger(), {})
        active = y_s.get_day_most_active()["Symbol"]

        for act in active:
            news.append(act)

        appendix = ' ' * self.nl  # add some spaces at the end
        news.append(appendix)
        delimiter = '      ***      '  # shown between the messages
        self.news = delimiter.join(news)
        newsLength = len(self.news)  # number of letters in news = frameRange
        lps = 16  # letters per second
        dur = newsLength * 1000 / lps  # duration until the whole string is shown in milliseconds
        self.timeLine.setDuration(dur)
        self.timeLine.setFrameRange(0, newsLength)
        self.timeLine.start()

    def setText(self, number_of_frame):
        if number_of_frame < self.nl:
            start = 0
        else:
            start = number_of_frame - self.nl
        text = '{}'.format(self.news[start:number_of_frame])
        self.label.setText(text)

    def nextNews(self):
        self.feed()  # start again


class WorkerSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(dict)


class Worker(QtCore.QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @QtCore.pyqtSlot()
    def run(self):
        result = self.fn(*self.args, **self.kwargs)
        self.signals.result.emit(result)


def main():
    app = QtWidgets.QApplication([])
    window = MainWindow()
    app.exec_()


if __name__ == "__main__":
    main()
