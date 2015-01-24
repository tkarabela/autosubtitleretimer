from __future__ import division

import random
import sys
import math
import traceback
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication, QMainWindow, QMessageBox, QFileDialog
import pysubs2
from retimer import Ui_MainWindow

# ----------------------------------------------------------------------------------------------------------------------

def get_clusters(subs, include_comments=False):
    lines = sorted(line for line in subs if not line.is_comment or include_comments)
    i = 0

    while i < len(lines):
        start = lines[i].start
        end = lines[i].end
        cluster_lines = [lines[i]]

        while True:
            i += 1
            if i < len(lines) and lines[i].start <= end:
                end = max(end, lines[i].end)
                cluster_lines.append(lines[i])
            else:
                break

        yield start, end, cluster_lines


def discretize(clusters, unit=100):
    times = []

    for start, end, _ in clusters:
        times.extend(range(start//unit, end//unit))

    return times

def simulated_annealing_solver(x0, move, objective, t0=1000, iterations=100, decay=0.97):
    t = t0
    x, fx = x0, objective(x0)
    bestx, bestfx = x, fx

    for _ in range(iterations):
        newx = move(x, t)
        newfx = objective(newx)
        delta = (newfx - fx)**2

        if newfx < fx or math.exp(-delta/t) > random.random():
            x, fx = newx, newfx # keep the new state

            if fx < bestfx:
                bestx, bestfx = x, fx

        t *= decay

    return bestx, bestfx

# ----------------------------------------------------------------------------------------------------------------------

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.settings = QSettings("autosubretimer", "autosubretimer")

        self.refLineEdit.setText(str(self.settings.value("refLine", type=str)))
        self.subsLineEdit.setText(str(self.settings.value("subsLine", type=str)))

        self.dryRunButton.clicked.connect(self.optimize)
        self.runButton.clicked.connect(self.run)
        self.refButton.clicked.connect(lambda: self.refLineEdit.setText(self.get_file()))
        self.subsButton.clicked.connect(lambda: self.subsLineEdit.setText(self.get_file()))

        self.refLineEdit.textChanged.connect(lambda s: self.settings.setValue("refLine", s))
        self.subsLineEdit.textChanged.connect(lambda s: self.settings.setValue("subsLine", s))

    def get_file(self):
        return QFileDialog.getOpenFileName(self,
            caption=self.tr("Select Subtitle File"),
            filter=self.tr("Subtitle files (*.ass *.srt);;All files (*.*)"))

    def optimize(self):
        try:
            ref_subs = pysubs2.load(str(self.refLineEdit.text()))
            subs = pysubs2.load(str(self.subsLineEdit.text()))

            unit = int(self.unitSpinBox.value())
            t0 = int(self.t0SpinBox.value())
            decay = float(self.decaySpinBox.value())
            iterations = int(self.iterationsSpinBox.value())

            ref_times = set(discretize(get_clusters(ref_subs), unit))
            times = set(discretize(get_clusters(subs), unit))

            x0 = 0
            move = lambda x, t: random.gauss(x, t)
            objective = lambda delta: len(ref_times ^ set(t+delta//unit for t in times))

            best_delta, e = simulated_annealing_solver(x0, move, objective, t0, iterations=iterations, decay=decay)
            self.logLabel.setText("shifted by %.2f s (error=%d)" % (best_delta/1000, e))
            return best_delta
        except Exception as exc:
            QMessageBox.critical(self, self.tr("Error"), traceback.format_exc(exc))

    def run(self):
        try:
            path = str(self.subsLineEdit.text())
            subs = pysubs2.load(path)
            delta = self.optimize()
            subs.shift(ms=delta)
            subs.save(path)
        except Exception as exc:
            QMessageBox.critical(self, self.tr("Error"), traceback.format_exc(exc))

# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
