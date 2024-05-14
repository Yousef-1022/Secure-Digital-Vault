from gui.ViewManager import WindowManager
from PyQt6 import QtWidgets

import sys

sys.argv += ['-platform', 'windows:darkmode=1'] # 1 = light Theme
app = QtWidgets.QApplication(sys.argv)
app.setStyle("Fusion")
MainWindow = WindowManager()
MainWindow.show()
sys.exit(app.exec())
