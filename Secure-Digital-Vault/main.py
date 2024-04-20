from gui.ViewManager import WindowManager
from PyQt6 import QtWidgets

import sys

app = QtWidgets.QApplication(sys.argv)
MainWindow = WindowManager()
MainWindow.show()
sys.exit(app.exec())
