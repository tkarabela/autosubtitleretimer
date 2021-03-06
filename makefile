PYTHON = python2
PYQT4_PATH = $(shell $(PYTHON) -c 'from __future__ import print_function; import PyQt4, os.path; print(os.path.dirname(PyQt4.__file__))')
UI_FILES = $(shell find -type f -name '*.ui')
PY_FILES = $(shell find -type f -name '*.py')
TS_FILES = $(shell find -type f -name '*.ts')

.PHONY: test run

run:
	$(PYTHON) app.py

ui: $(UI_FILES)
	$(PYTHON) -c 'import PyQt4.uic; PyQt4.uic.compileUiDir(".", recurse=True, map=lambda d, fname: (d, "ui_"+fname))'

test:
	$(PYTHON) -m nose --with-doctest
