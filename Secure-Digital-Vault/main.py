from gui.Browser import VaultSearchWindow
from PyQt6 import QtWidgets
import sys

app = QtWidgets.QApplication(sys.argv)
MainWindow = VaultSearchWindow()
MainWindow.show()
sys.exit(app.exec())
