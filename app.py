from __future__ import division

import sys
import traceback
from PyQt4.QtCore import QSettings, QThread, pyqtSignal
from PyQt4.QtGui import QApplication, QMainWindow, QMessageBox, QFileDialog
import pysubs2
from retimer import Ui_MainWindow
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
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.settings = QSettings("autosubretimer", "autosubretimer")

        self.refLineEdit.setText(str(self.settings.value("refLine", type=str)))
        self.subsLineEdit.setText(str(self.settings.value("subsLine", type=str)))

        self.dryRunButton.clicked.connect(self.start_processing)
        self.runButton.clicked.connect(self.start_processing)
        self.refButton.clicked.connect(lambda: self.refLineEdit.setText(self.get_file()))
        self.subsButton.clicked.connect(lambda: self.subsLineEdit.setText(self.get_file()))

        self.refLineEdit.textChanged.connect(lambda s: self.settings.setValue("refLine", s))
        self.subsLineEdit.textChanged.connect(lambda s: self.settings.setValue("subsLine", s))

        self.compute_decay()
        self.iterationsSpinBox.valueChanged.connect(self.compute_decay)
        self.unitSpinBox.valueChanged.connect(self.compute_decay)
        self.t0SpinBox.valueChanged.connect(self.compute_decay)

    def get_file(self):
        return QFileDialog.getOpenFileName(self,
            caption=self.tr("Select Subtitle File"),
            filter=self.tr("Subtitle files (*.ass *.srt);;All files (*.*)"))

    def start_processing(self):
        try:
            self.ref_subs = pysubs2.load(str(self.refLineEdit.text()))
            self.subs = pysubs2.load(str(self.subsLineEdit.text()))

            settings = {
                "unit": int(self.unitSpinBox.value()),
                "t0": int(self.t0SpinBox.value()),
                "decay": float(self.decaySpinBox.value()),
                "iterations": int(self.iterationsSpinBox.value()),
            }

            self.progressBar.setMaximum(settings["iterations"])

            self.thread = Worker(self, self.ref_subs, self.subs, settings)
            self.thread.updated.connect(self.updated)
            self.thread.done.connect(self.done)
            self.thread.start()
        except Exception as exc:
            QMessageBox.critical(self, self.tr("Error"), traceback.format_exc(exc))

    def updated(self, i, t, x, fx):
        if i % 2 > 0: return

        self.progressBar.setValue(i+1)
        self.tSpinBox.setValue(t)
        self.shiftLineEdit.setText(pysubs2.time.ms_to_str(x, fractions=True))
        self.errorSpinBox.setValue(fx)

    def done(self, x, fx):
        self.progressBar.setValue(self.progressBar.maximum())
        self.shiftLineEdit.setText(pysubs2.time.ms_to_str(x, fractions=True))
        self.errorSpinBox.setValue(fx)

    def compute_decay(self):
        n = int(self.iterationsSpinBox.value())
        unit = int(self.unitSpinBox.value())
        t0 = int(self.t0SpinBox.value())

        decay = (unit / t0)**(1/n)
        self.decaySpinBox.setValue(decay)

# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
