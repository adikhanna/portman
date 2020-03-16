from PyQt5 import QtCore
from typing import Callable, Any


class WorkerSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(dict)


class Worker(QtCore.QRunnable):
    def __init__(self, func: Callable[[Any], Any], *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @QtCore.pyqtSlot()
    def run(self):
        result = self.fn(*self.args, **self.kwargs)
        self.signals.result.emit(result)


class UpdateThread(QtCore.QThread):
    updateData = QtCore.pyqtSignal(object)

    def __init__(self, record):
        QtCore.QTimer.__init__(self)
        self.data = record

    def run(self):
        self.updateData.emit(self.data)
