from __future__ import division, unicode_literals

import sys
import traceback
from PyQt4.QtCore import QThread, pyqtSignal
from PyQt4.QtGui import QApplication, QMainWindow, QMessageBox
import pysubs2
from ui_mainwindow import Ui_MainWindow
from selectfilewidget import SelectFileWidget
from algorithms import solver_driver

# ----------------------------------------------------------------------------------------------------------------------

class Worker(QThread):
    updated = pyqtSignal(int, float, float, int)
    done = pyqtSignal(float, float)

    def __init__(self, parent, ref_subs, subs, settings):
        QThread.__init__(self, parent)
        self.ref_subs = ref_subs
        self.subs = subs
        self.settings = settings

    def run(self):
        for i, t, x, fx in solver_driver(self.ref_subs, self.subs, **self.settings):
            if i is None:
                self.done.emit(x, fx)
            else:
                self.updated.emit(i, t, x, fx)

# ----------------------------------------------------------------------------------------------------------------------

class MainWindow(QMainWindow, Ui_MainWindow):
    ENCODING = "latin-1"

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.refFile = SelectFileWidget(self, "*.ass *.srt *.mkv")
        self.refGroupBox.layout().addWidget(self.refFile)

        self.subsFile = SelectFileWidget(self, "*.ass *.srt")
        self.subsGroupBox.layout().addWidget(self.subsFile)

        self.dryRunButton.clicked.connect(lambda: self.start_processing(False))
        self.runButton.clicked.connect(lambda: self.start_processing(True))

        self.compute_decay()
        self.iterationsSpinBox.valueChanged.connect(self.compute_decay)
        self.unitSpinBox.valueChanged.connect(self.compute_decay)
        self.stepSizeSpinBox.valueChanged.connect(self.compute_decay)

    def get_t0(self):
        return int(self.stepSizeSpinBox.value()) * 1000

    def start_processing(self, write_file=True):
        try:
            self.ref_subs = pysubs2.load(self.refFile.path, self.ENCODING)
            self.subs = pysubs2.load(self.subsFile.path, self.ENCODING)

            settings = {
                "unit": int(self.unitSpinBox.value()),
                "t0": self.get_t0(),
                "decay": float(self.decaySpinBox.value()),
                "iterations": int(self.iterationsSpinBox.value()),
            }

            self.progressBar.setMaximum(settings["iterations"])

            self.thread = Worker(self, self.ref_subs, self.subs, settings)
            self.thread.updated.connect(self.updated)
            self.thread.done.connect(self.done)
            if write_file:
                self.thread.done.connect(self.shiftAndWrite)
            self.thread.start()
            self.enableButtons(False)
        except Exception as exc:
            QMessageBox.critical(self, self.tr("Error"), traceback.format_exc(exc))

    def getUnit(self):
        return self.unitSpinBox.value()

    def enableButtons(self, enabled):
        self.runButton.setEnabled(enabled)
        self.dryRunButton.setEnabled(enabled)
        self.refFile.setEnabled(enabled)
        self.subsFile.setEnabled(enabled)

    def updated(self, i, t, x, fx):
        if i % 2 > 0: return

        self.progressBar.setValue(i+1)
        self.stepSizeDisplay.setValue(t/1000)
        self.shiftDisplay.setText(pysubs2.time.ms_to_str(x, fractions=True))
        self.mismatchDisplay.setValue(fx/self.getUnit())

    def done(self, x, fx):
        self.progressBar.setValue(self.progressBar.maximum())
        self.shiftDisplay.setText(pysubs2.time.ms_to_str(x, fractions=True))
        self.mismatchDisplay.setValue(fx/self.getUnit())
        self.enableButtons(True)

    def shiftAndWrite(self, x, fx):
        try:
            self.subs.shift(ms=x)
            self.subs.save(self.subsFile.path, self.ENCODING)
        except Exception as exc:
            QMessageBox.critical(self, self.tr("Error"), traceback.format_exc(exc))

    def compute_decay(self):
        n = int(self.iterationsSpinBox.value())
        unit = int(self.unitSpinBox.value())
        t0 = self.get_t0()

        decay = (unit / t0)**(1/n)
        self.decaySpinBox.setValue(decay)
        if decay < 0.95:
            self.decaySpinBox.setStyleSheet("color: red")
        else:
            self.decaySpinBox.setStyleSheet("")

# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
