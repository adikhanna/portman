from PyQt5 import QtWidgets
from PyQt5 import QtCore
from yahoo_stocks import YahooStocks


class TopStocksFeed(QtWidgets.QWidget):
    def __init__(self, feed_type: str,
                 yahoo_stocks: YahooStocks,
                 parent: QtWidgets.QWidget = None):
        QtWidgets.QWidget.__init__(self, parent)
        self.yahoo_stocks = yahoo_stocks
        self.feed = eval(
            "self.yahoo_stocks.get_day_" +
            feed_type +
            "()")["Symbol"]

        self.label = QtWidgets.QLabel("")
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.timeLine = QtCore.QTimeLine()
        self.timeLine.setCurveShape(QtCore.QTimeLine.LinearCurve)
        self.timeLine.frameChanged.connect(self.set_text)
        self.timeLine.finished.connect(self.next_news)
        self.signalMapper = QtCore.QSignalMapper(self)

        self.start_feed()

    def start_feed(self) -> None:
        self.rate = int(self.label.width() /
                        self.label.fontMetrics().averageCharWidth()) * 2
        self.news = "  +++  ".join([item for item in self.feed] +
                                   [" " * self.rate])
        self.timeLine.setDuration(len(self.news) * 1000 / 16)
        self.timeLine.setFrameRange(0, len(self.news))
        self.timeLine.start()

    def set_text(self, number_of_frame: int) -> None:
        if number_of_frame < self.rate:
            start = 0
        else:
            start = number_of_frame - self.rate
        text = "{}".format(self.news[start:number_of_frame])
        self.label.setText(text)

    def next_news(self) -> None:
        self.start_feed()
