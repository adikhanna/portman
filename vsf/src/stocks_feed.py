import time

from PyQt5 import QtWidgets
from PyQt5 import QtCore, QtGui

from thread_worker import UpdateThread
from yahoo_stocks import YahooStocks


class TopStocksFeed(QtWidgets.QWidget):
    def __init__(self, yahoo_stocks: YahooStocks,
                 parent: QtWidgets.QWidget = None):
        QtWidgets.QWidget.__init__(self, parent)

        self.logView = QtWidgets.QTableWidget(0, 3)
        self.logView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.logView.setColumnCount(3)
        self.logView.setHorizontalHeaderLabels(["Top Gainers",
                                                "Top Losers",
                                                "Most Active"])

        header = self.logView.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh_tables)
        self.timer.start(120000)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.logView)
        self.setLayout(self.layout)
        self.yahoo_stocks = yahoo_stocks

        self.gainers = self.yahoo_stocks.get_day_gainers()
        self.losers = self.yahoo_stocks.get_day_losers()
        self.most_active = self.yahoo_stocks.get_day_most_active()

        for i in range(max(len(self.gainers), len(self.losers), len(self.most_active))):
            self.logView.insertRow(self.logView.rowCount())

        self.on_data_ready()

    def refresh_tables(self):
        self.gainers = self.yahoo_stocks.get_day_gainers()
        self.losers = self.yahoo_stocks.get_day_losers()
        self.most_active = self.yahoo_stocks.get_day_most_active()
        thread = UpdateThread(self.gainers)
        thread.updateData.connect(self.on_data_ready)
        thread.start()
        time.sleep(0.1)

    def on_data_ready(self):
        for index, (gainer, loser, most_active) in enumerate(zip(self.gainers["Symbol"],
                                                                 self.losers["Symbol"],
                                                                 self.most_active["Symbol"])):
            it = QtWidgets.QTableWidgetItem()
            it.setData(QtCore.Qt.DisplayRole, str(gainer))
            it.setBackground(QtGui.QColor("green"))
            self.logView.setItem(index, 0, it)
            it = QtWidgets.QTableWidgetItem()
            it.setData(QtCore.Qt.DisplayRole, str(loser))
            it.setBackground(QtGui.QColor("red"))
            self.logView.setItem(index, 1, it)
            it = QtWidgets.QTableWidgetItem()
            it.setData(QtCore.Qt.DisplayRole, str(most_active))
            it.setBackground(QtGui.QColor("blue"))
            self.logView.setItem(index, 2, it)
