from __future__ import division, unicode_literals

import sys
import traceback
from six import text_type as _str
from PyQt4.QtCore import QThread, pyqtSignal
from PyQt4.QtGui import QApplication, QMainWindow, QMessageBox
import pysubs2
from ui_mainwindow import Ui_MainWindow
from selectfilewidget import SelectFileWidget
from algorithms import solver_driver
from mkvhandler import extract_subtitle_track

# ----------------------------------------------------------------------------------------------------------------------

def time_to_str(ms):
    return pysubs2.time.ms_to_str(ms, fractions=True)

class Worker(QThread):
    ENCODING = "latin-1"

    updated = pyqtSignal(int, float, float, int)
    done = pyqtSignal(float, float)
    failed = pyqtSignal(_str)

    def __init__(self, parent, ref_path, subs_path, write_file, settings):
        QThread.__init__(self, parent)
        self.ref_path = ref_path
        self.subs_path = subs_path
        self.settings = settings
        self.write_file = write_file

    def run(self):
        try:
            if self.ref_path.lower().endswith(".mkv"):
                ref_subs = extract_subtitle_track(self.ref_path)
            else:
                ref_subs = pysubs2.load(self.ref_path, self.ENCODING)

            subs = pysubs2.load(self.subs_path, self.ENCODING)
            delta, error = None, None

            for i, t, x, fx in solver_driver(ref_subs, subs, **self.settings):
                if i is None:
                    delta, error = x, fx
                else:
                    self.updated.emit(i, t, x, fx)

            if self.write_file:
                subs.shift(ms=delta)
                subs.save(self.subs_path, self.ENCODING)

            self.done.emit(delta, error)
        except Exception as exc:
            self.failed.emit(traceback.format_exc(exc))

# ----------------------------------------------------------------------------------------------------------------------

class MainWindow(QMainWindow, Ui_MainWindow):
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
        if not self.refFile.path:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Please select reference subtitles or MKV file."))
            return
        elif not self.subsFile.path:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Please select subtitles to be retimed."))
            return

        try:
            self.enableButtons(False)

            settings = {
                "unit": int(self.unitSpinBox.value()),
                "t0": self.get_t0(),
                "decay": float(self.decaySpinBox.value()),
                "iterations": int(self.iterationsSpinBox.value()),
            }

            self.progressBar.setMaximum(0)

            self.thread = Worker(self, self.refFile.path, self.subsFile.path, write_file, settings)
            self.thread.updated.connect(self.updated)
            self.thread.done.connect(self.done)
            self.thread.failed.connect(self.failed)
            self.thread.start()
        except Exception as exc:
            QMessageBox.critical(self, self.tr("Error"), traceback.format_exc(exc))
            self.enableButtons(True)

    def getUnit(self):
        return self.unitSpinBox.value()

    def enableButtons(self, enabled):
        self.runButton.setEnabled(enabled)
        self.dryRunButton.setEnabled(enabled)
        self.refFile.setEnabled(enabled)
        self.subsFile.setEnabled(enabled)

    def updated(self, i, t, x, fx):
        if i % 2 > 0: return

        self.progressBar.setMaximum(int(self.iterationsSpinBox.value()))
        self.progressBar.setValue(i+1)
        self.stepSizeDisplay.setValue(t/1000)
        self.shiftDisplay.setText(time_to_str(x))
        self.mismatchDisplay.setValue(fx/self.getUnit())

    def failed(self, trace):
        self.enableButtons(True)
        self.progressBar.setMaximum(1)
        QMessageBox.critical(self, self.tr("Error"), trace)

    def done(self, x, fx):
        self.progressBar.setValue(self.progressBar.maximum())
        self.shiftDisplay.setText(time_to_str(x))
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
