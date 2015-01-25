from __future__ import division, unicode_literals

from six import text_type as _str
import logging
import os.path
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QFileDialog, QWidget, QDropEvent, QDragEnterEvent
from ui_selectfilewidget import Ui_SelectFileWidget

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------------------------------------------------

class SelectFileWidget(QWidget, Ui_SelectFileWidget):
    def __init__(self, parent=None, filetypes="*.txt"):
        super(SelectFileWidget, self).__init__(parent)
        self.setupUi(self)

        self.filetypes = filetypes
        self.button.clicked.connect(self.selectFile)

    @property
    def path(self):
        return _str(self.lineEdit.text())

    @path.setter
    def path(self, x):
        x = _str(x)
        if os.path.isfile(x):
            self.lineEdit.setText(x)
        else:
            logger.error("Cannot set file to %r (not a file)", x)

    @pyqtSlot(QDropEvent)
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.path = url.toLocalFile()
            break

    @pyqtSlot(QDragEnterEvent)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def selectFile(self):
        if os.path.isfile(self.path):
            directory = os.path.dirname(self.path)
        else:
            directory = os.path.expanduser("~")

        new_path = QFileDialog.getOpenFileName(self,
            caption="Select File",
            filter="Files (%s);;All files (*.*)" % self.filetypes,
            directory=directory)

        self.path = new_path
