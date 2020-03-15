from PyQt5 import QtCore
from typing import Callable, Any, Union


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
